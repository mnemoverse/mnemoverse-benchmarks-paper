#!/usr/bin/env python3
"""BEAM controlled re-score (P1 / review 'Important' B2): the prompt-swing at 10M-token scale.

Answers fixed, judge varied -- exactly the LoCoMo demonstration, on BEAM. Takes our
engine's generated answers to the 200 BEAM-10M questions (nugget rubric as the gold),
re-scores them under the SAME two headline prompts (mem0 lenient, strict) on gpt-5,
and reports the pass-rate swing overall and by question type. Upgrades the paper's
BEAM section from qualitative inference to a measured controlled re-score.

Step 1 (one-time) extracts a committed answer artifact from the private core run so
the re-score reproduces offline without core:
    kit/data/beam_answers_10m.json   (question, gold=rubric, answer, question_type, conv_idx)

    OPENAI_API_KEY=... python scripts/run_beam_rescore.py [--extract-from <core_result.json>]

Writes verdicts to experiments/hardening/verdicts/BEAM_{mem0,strict}.json and a summary
to experiments/hardening/beam_rescore.{json,md}. Resumable per judge.
"""
from __future__ import annotations
import argparse, asyncio, json, sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "scripts"))
from judge import run_judge  # noqa: E402

ANSWERS = KIT / "data" / "beam_answers_10m.json"
VERDICTS = REPO / "experiments" / "hardening" / "verdicts"
CUTOFF = "top_100"


def extract(core_path: str):
    d = json.loads(Path(core_path).read_text(encoding="utf-8"))
    out = []
    for e in d["evaluations"]:
        cr = e["cutoff_results"].get(CUTOFF, {})
        ans = cr.get("generated_answer")
        if not ans:
            continue
        gold = "; ".join(e["rubric"]) if isinstance(e["rubric"], list) else str(e["rubric"])
        out.append({"qid": e["question_id"], "question": e["question"], "gold": gold,
                    "answer": ans, "category": e["question_type"], "conv_idx": e["conv_idx"]})
    ANSWERS.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"extracted {len(out)} BEAM answers -> {ANSWERS} (source: {Path(core_path).name})")


def load():
    recs = json.loads(ANSWERS.read_text(encoding="utf-8"))
    return [{"qid": r["qid"], "question": r["question"], "gold": r["gold"],
             "answer": r["answer"], "category": r["category"]} for r in recs]


async def run(concurrency):
    recs = load()
    verds = {}
    for j in ("mem0", "strict"):
        out = VERDICTS / f"BEAM_{j}.json"
        if out.exists():
            print(f"[skip] {out.name}", flush=True)
            verds[j] = json.loads(out.read_text(encoding="utf-8"))
            continue
        r = await run_judge(recs, j, concurrency)
        out.write_text(json.dumps(r["records"], indent=1), encoding="utf-8")
        verds[j] = r["records"]
        print(f"[done] BEAM {j}: acc={r['accuracy']:.4f} n={r['n']}/{r['n_total']}", flush=True)
    return verds


def analyze(verds):
    def smap(recs):
        return {r["qid"]: float(r["score"]) for r in recs
                if isinstance(r.get("score"), (int, float)) and r["score"] in (0.0, 1.0)}
    cat = {r["qid"]: r.get("category") for r in verds["mem0"]}
    m, s = smap(verds["mem0"]), smap(verds["strict"])
    joint = sorted(set(m) & set(s))
    lm = sum(m[q] for q in joint) / len(joint) * 100
    ss = sum(s[q] for q in joint) / len(joint) * 100
    by = defaultdict(lambda: [0, 0, 0])
    for q in joint:
        by[cat[q]][0] += m[q]; by[cat[q]][1] += s[q]; by[cat[q]][2] += 1
    L = ["# BEAM controlled re-score (P1): same answers, two prompts, 10M-token scale", "",
         "Our engine's generated answers to the 200 BEAM-10M questions (nugget rubric as gold), "
         "re-scored under the SAME mem0 lenient and strict prompts on gpt-5. Answers committed at "
         "`kit/data/beam_answers_10m.json`; verdicts `experiments/hardening/verdicts/BEAM_*.json`; "
         "runner `scripts/run_beam_rescore.py`.", "",
         f"**Overall (n={len(joint)}): lenient {lm:.1f}% vs strict {ss:.1f}% -- a {lm-ss:.1f}-point swing on identical answers.**", "",
         "| question type | n | lenient % | strict % | swing (pp) |",
         "|---------------|---|-----------|----------|------------|"]
    for c in sorted(by):
        a, b, n = by[c]
        L.append(f"| {c} | {n} | {a/n*100:.1f} | {b/n*100:.1f} | {(a-b)/n*100:+.1f} |")
    L.append("")
    L.append("The prompt-sensitivity phenomenon of \\S3 is not specific to LoCoMo or its scale: the same two "
             "grading prompts move BEAM-10M pass-rates by tens of points on a fixed set of answers scored against "
             "a per-claim nugget rubric.")
    (REPO / "experiments" / "hardening" / "beam_rescore.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (REPO / "experiments" / "hardening" / "beam_rescore.json").write_text(
        json.dumps({"n": len(joint), "lenient_pct": lm, "strict_pct": ss, "swing_pp": lm - ss,
                    "by_type": {c: {"n": by[c][2], "lenient_pct": by[c][0]/by[c][2]*100,
                                    "strict_pct": by[c][1]/by[c][2]*100} for c in by}}, indent=1),
        encoding="utf-8")
    print("\n".join(L))


async def main(args):
    if args.extract_from:
        extract(args.extract_from)
    if not ANSWERS.exists():
        sys.exit("No beam_answers_10m.json; run once with --extract-from <core beam result json>")
    verds = await run(args.concurrency)
    analyze(verds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-from", default=None)
    ap.add_argument("--concurrency", type=int, default=10)
    asyncio.run(main(ap.parse_args()))
