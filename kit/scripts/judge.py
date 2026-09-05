"""Self-contained LLM-judge runner — the reproducibility centerpiece of the
"The Judge Is the Benchmark" kit.

Zero dependency on any internal repository: this script reads the judge prompts
from ``kit/prompts/*.txt`` and calls the OpenAI API directly. Anyone with an
``OPENAI_API_KEY`` can re-run any shipped judge on the shipped answers and
reproduce the headline swing within the published tolerance. The answers are
FIXED; the grading prompt is the only thing that changes between judges.

    pip install openai python-dotenv      # kit/scripts/requirements.txt

    python kit/scripts/judge.py \
        --answers kit/data/answers_mem0_conv26.json \
        --judge mem0 --judge strict \
        --out  out/verdicts.json [--repeats 1] [--concurrency 6] [--limit 0]

answers.json schema: a list of records ``{qid, question, gold, answer[, category]}``
where ``answer`` is the system's generated answer and ``gold`` is the LoCoMo gold.

Judges (id -> prompt file -> model):
    mem0       judge_mem0_generous.txt   gpt-5      (the field's de-facto lenient prompt)
    strict     judge_strict_ours.txt     gpt-5      (our adversarial strict prompt)
    mnemoverse judge_mnemoverse.txt       gpt-5-mini (our default binary prompt)
    mem0-4o    judge_mem0_generous.txt   gpt-4o     (mem0 prompt, different model)

Output: ``{judge: {records: [{qid, label, score, reasoning}], accuracy, n}}``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import dotenv

KIT = Path(__file__).resolve().parents[1]          # .../kit
PROMPTS = KIT / "prompts"
dotenv.load_dotenv()                                # OPENAI_API_KEY from env or .env

JUDGE_PROMPT = {
    "mem0": "judge_mem0_generous.txt",
    "strict": "judge_strict_ours.txt",
    "mnemoverse": "judge_mnemoverse.txt",
    "mem0-4o": "judge_mem0_generous.txt",
    "strict-4o": "judge_strict_ours.txt",
    "lme": "judge_longmemeval_default.txt",
    "lme-temporal": "judge_longmemeval_temporal.txt",
    # single-rule ablation of the lenient prompt (P4/F-S8): each tightens ONE rule
    "abl-no-partial": "judge_abl_no_partial.txt",
    "abl-no-paraphrase": "judge_abl_no_paraphrase.txt",
    "abl-no-datetol": "judge_abl_no_datetol.txt",
    "abl-no-extradetail": "judge_abl_no_extradetail.txt",
    # non-OpenAI backbone (P6/F-S7): the two headline prompts on Claude
    "mem0-claude": "judge_mem0_generous.txt",
    "strict-claude": "judge_strict_ours.txt",
    # human-calibrated judge (paper term: "calibrated"; artifact term: "golden")
    "golden": "judge_golden_v2.txt",
}
JUDGE_MODEL = {"mem0": "gpt-5", "strict": "gpt-5", "mnemoverse": "gpt-5-mini",
               "mem0-4o": "gpt-4o", "strict-4o": "gpt-4o",
               # LongMemEval pins its judge snapshot (model_zoo in their evaluate_qa.py)
               "lme": "gpt-4o-2024-08-06", "lme-temporal": "gpt-4o-2024-08-06",
               "abl-no-partial": "gpt-5", "abl-no-paraphrase": "gpt-5",
               "abl-no-datetol": "gpt-5", "abl-no-extradetail": "gpt-5",
               "mem0-claude": "claude-sonnet-4-5", "strict-claude": "claude-sonnet-4-5",
               "golden": "gpt-5"}


def parse_prompt(judge_id: str) -> tuple[str, str]:
    """Return (system, user_template) parsed from kit/prompts/<file>."""
    text = (PROMPTS / JUDGE_PROMPT[judge_id]).read_text(encoding="utf-8")
    # Files are: optional '# comment' header, '--- SYSTEM ---', system text,
    # '--- USER TEMPLATE ---', user template (with {question}{answer}{response}).
    sys_marker, usr_marker = "--- SYSTEM ---", "--- USER TEMPLATE ---"
    if sys_marker not in text or usr_marker not in text:
        raise ValueError(f"prompt {JUDGE_PROMPT[judge_id]} missing SYSTEM/USER markers")
    system = text.split(sys_marker, 1)[1].split(usr_marker, 1)[0].strip()
    user = text.split(usr_marker, 1)[1].strip()
    return system, user


_LABEL_RE = re.compile(r'"?label"?\s*[:=]?\s*"?\s*(CORRECT|WRONG)', re.IGNORECASE)


def parse_label(raw: str) -> tuple[float, str]:
    """Extract (score, reasoning) from a judge response. Robust to non-JSON."""
    reasoning = ""
    try:
        obj = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        lbl = str(obj.get("label", "")).upper()
        reasoning = str(obj.get("reasoning", ""))
        if "CORRECT" in lbl and "WRONG" not in lbl:
            return 1.0, reasoning
        if "WRONG" in lbl:
            return 0.0, reasoning
    except Exception:
        pass
    m = _LABEL_RE.search(raw)
    if m:
        return (1.0 if m.group(1).upper() == "CORRECT" else 0.0), reasoning or raw[:200]
    # Last resort: a bare CORRECT/WRONG token (count WRONG first — "not correct").
    up = raw.upper()
    if "WRONG" in up:
        return 0.0, reasoning or raw[:200]
    if "CORRECT" in up:
        return 1.0, reasoning or raw[:200]
    # yes/no-style judges (the ported LongMemEval rubric answers "yes or no only")
    first = up.strip().split()[0].strip(".,!\"'") if up.strip() else ""
    if first == "YES":
        return 1.0, reasoning or raw[:200]
    if first == "NO":
        return 0.0, reasoning or raw[:200]
    return float("nan"), f"UNPARSEABLE: {raw[:200]}"


async def _call(client, model: str, system: str, user: str) -> str:
    if model.startswith("claude"):
        # Anthropic SDK: system is a top-level arg, temperature 0 for determinism.
        resp = await client.messages.create(
            model=model, system=system, max_tokens=512, temperature=0,
            messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    # OpenAI. gpt-5 is a reasoning model: no temperature, use max_completion_tokens.
    kwargs = {"model": model, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]}
    if model.startswith("gpt-5"):
        kwargs["max_completion_tokens"] = 2000
    else:
        kwargs["temperature"] = 0
        kwargs["max_tokens"] = 512
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def score_one(client, judge_id, system, user_tmpl, rec, sem) -> dict:
    async with sem:
        user = user_tmpl.format(question=rec["question"], answer=rec["gold"], response=rec["answer"])
        raw = None
        last_err = None
        for attempt in range(6):
            try:
                raw = await _call(client, JUDGE_MODEL[judge_id], system, user)
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e).lower()
                transient = "429" in msg or "rate" in msg or "quota" in msg or "overloaded" in msg or "timeout" in msg
                if not transient or attempt == 5:
                    return {"qid": rec.get("qid"), "score": None, "label": None,
                            "reasoning": f"ERROR: {e}", "category": rec.get("category")}
                await asyncio.sleep(min(2 ** attempt + 1, 45))
        score, reasoning = parse_label(raw)
        return {"qid": rec.get("qid"), "score": score,
                "label": "CORRECT" if score == 1.0 else ("WRONG" if score == 0.0 else None),
                "reasoning": reasoning, "category": rec.get("category")}


async def run_judge(records, judge_id, concurrency) -> dict:
    system, user_tmpl = parse_prompt(judge_id)
    if JUDGE_MODEL[judge_id].startswith("claude"):
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
    else:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
    sem = asyncio.Semaphore(concurrency)
    out = await asyncio.gather(*[score_one(client, judge_id, system, user_tmpl, r, sem) for r in records])
    scored = [r for r in out if r["score"] in (0.0, 1.0)]
    acc = sum(r["score"] for r in scored) / len(scored) if scored else float("nan")
    return {"records": out, "n": len(scored), "n_total": len(records), "accuracy": acc}


def load_answers(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    recs = data if isinstance(data, list) else (data.get("records") or data.get("answers") or [])
    norm = []
    for r in recs:
        ans = r.get("answer")
        if ans in (None, "", "null"):
            continue
        norm.append({
            "qid": r.get("qid"),
            "question": r["question"],
            "gold": r.get("gold", r.get("ground_truth")),
            "answer": ans,
            "category": r.get("category") or r.get("category_name"),
        })
    return norm


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--answers", required=True, type=Path)
    ap.add_argument("--judge", action="append", required=True, choices=list(JUDGE_PROMPT))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set (env or .env).", file=sys.stderr)
        return 2

    records = load_answers(args.answers)
    if args.limit:
        records = records[: args.limit]
    print(f"answers: {args.answers.name}  n={len(records)}  judges={args.judge}  repeats={args.repeats}", flush=True)

    result = {"answers_file": str(args.answers), "n_records": len(records), "judges": {}}
    for j in args.judge:
        reps = []
        for rep in range(args.repeats):
            r = await run_judge(records, j, args.concurrency)
            reps.append(r)
            print(f"  {j} repeat {rep}: accuracy={r['accuracy']:.4f}  (n={r['n']}/{r['n_total']})", flush=True)
        result["judges"][j] = reps if args.repeats > 1 else reps[0]

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
