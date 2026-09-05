#!/usr/bin/env python3
"""Third, independently-sourced strict rubric (reviewer-requested triangulation for the threats section).

Re-judges Mem0's full published run (10 conversations, 1,539 answers) under the
LongMemEval judge prompt (Wu et al., ICLR 2025) ported VERBATIM into
kit/prompts/judge_longmemeval_{default,temporal}.txt, on their pinned judge
model gpt-4o-2024-08-06. Category routing mirrors their per-task routing:
LoCoMo `temporal` -> their temporal-reasoning variant; all other categories ->
their default template.

This triangulates the paper's swing: the 91.0/35.0 endpoints came from the
field's lenient prompt and OUR strict prompt; this rubric is a published,
widely-used grading prompt none of whose words we wrote.

    OPENAI_API_KEY=... python scripts/run_third_rubric_longmemeval.py [--concurrency 12]

Writes experiments/hardening/verdicts/LME_conv{N}.json and
experiments/hardening/third_rubric_longmemeval.{json,md}. Resumable per conversation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "scripts"))
from judge import run_judge, load_answers  # noqa: E402

DATA = KIT / "data" / "mem0_oss_answers"
VERDICTS = REPO / "experiments" / "hardening" / "verdicts"
OUT_JSON = REPO / "experiments" / "hardening" / "third_rubric_longmemeval.json"
OUT_MD = REPO / "experiments" / "hardening" / "third_rubric_longmemeval.md"

CONVS = [f"conv{i}" for i in range(10)]


def is_temporal(rec: dict) -> bool:
    return (rec.get("category") or "").replace("_", "-").strip().lower() == "temporal"


async def rejudge(concurrency: int) -> None:
    for conv in CONVS:
        out = VERDICTS / f"LME_{conv}.json"
        if out.exists():
            print(f"[skip] {out.name} exists", flush=True)
            continue
        recs = load_answers(DATA / f"{conv}.json")
        temporal = [r for r in recs if is_temporal(r)]
        rest = [r for r in recs if not is_temporal(r)]
        t0 = time.time()
        results = []
        if rest:
            r = await run_judge(rest, "lme", concurrency)
            results += r["records"]
        if temporal:
            r = await run_judge(temporal, "lme-temporal", concurrency)
            results += r["records"]
        out.write_text(json.dumps(results, indent=1), encoding="utf-8")
        scored = [x["score"] for x in results if x["score"] in (0.0, 1.0)]
        print(f"[done] {conv}: acc={sum(scored)/len(scored):.4f} n={len(scored)}/{len(results)} "
              f"(temporal via variant: {len(temporal)}) ({time.time()-t0:.0f}s)", flush=True)


def scored_map(path: Path) -> dict[str, float]:
    recs = json.loads(path.read_text(encoding="utf-8"))
    return {r["qid"]: float(r["score"]) for r in recs
            if isinstance(r.get("score"), (int, float)) and r["score"] in (0.0, 1.0)}


def analyze() -> None:
    rows, pool_lme, pool_mem0, pool_strict = [], {}, {}, {}
    for conv in CONVS:
        lme = scored_map(VERDICTS / f"LME_{conv}.json")
        mem0 = scored_map(VERDICTS / f"B_{conv}_mem0.json")
        strict = scored_map(VERDICTS / f"B_{conv}_strict.json")
        pool_lme.update({f"{conv}:{q}": s for q, s in lme.items()})
        pool_mem0.update({f"{conv}:{q}": s for q, s in mem0.items()})
        pool_strict.update({f"{conv}:{q}": s for q, s in strict.items()})
        rows.append({"conv": conv, "n": len(lme),
                     "lme_acc": sum(lme.values()) / len(lme) if lme else float("nan"),
                     "mem0_acc": sum(mem0.values()) / len(mem0),
                     "strict_acc": sum(strict.values()) / len(strict)})

    def j3(a: dict, b: dict) -> tuple[float, float, int]:
        j = sorted(set(a) & set(b))
        return (sum(a[q] for q in j) / len(j), sum(b[q] for q in j) / len(j), len(j))

    lme_v_mem0 = j3(pool_mem0, pool_lme)
    lme_v_strict = j3(pool_lme, pool_strict)
    summary = {"per_conversation": rows,
               "overall": {"lme_acc": sum(pool_lme.values()) / len(pool_lme), "n_lme": len(pool_lme),
                           "mem0_minus_lme_pp": (lme_v_mem0[0] - lme_v_mem0[1]) * 100, "n_joint_mem0": lme_v_mem0[2],
                           "lme_minus_strict_pp": (lme_v_strict[0] - lme_v_strict[1]) * 100, "n_joint_strict": lme_v_strict[2]}}
    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")

    o = summary["overall"]
    L = []
    L.append("# Third rubric: LongMemEval judge prompt over Mem0's full published run")
    L.append("")
    L.append("Provenance: prompts = verbatim port of LongMemEval `evaluate_qa.py::get_anscheck_prompt` "
             "(default + temporal variants; kit/prompts/judge_longmemeval_*.txt), judge model "
             "gpt-4o-2024-08-06 (their pinned snapshot), temperature 0; answers = the same committed "
             "Mem0 published run; lenient/strict columns = the committed gpt-5 verdicts. "
             "Rerun: `python scripts/run_third_rubric_longmemeval.py`.")
    L.append("")
    L.append("| conv | n | LongMemEval rubric % | lenient (mem0) % | strict (ours) % |")
    L.append("|------|---|----------------------|------------------|-----------------|")
    for r in rows:
        L.append(f"| {r['conv']} | {r['n']} | {r['lme_acc']*100:.1f} | {r['mem0_acc']*100:.1f} | {r['strict_acc']*100:.1f} |")
    L.append(f"| **all** | **{o['n_lme']}** | **{o['lme_acc']*100:.1f}** | | |")
    L.append("")
    L.append(f"Overall: LongMemEval rubric scores the run at {o['lme_acc']*100:.1f}%; "
             f"the lenient prompt sits {o['mem0_minus_lme_pp']:+.1f} pp above it (n={o['n_joint_mem0']} joint), "
             f"and it sits {o['lme_minus_strict_pp']:+.1f} pp above our strict prompt (n={o['n_joint_strict']} joint).")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    if not args.analyze_only:
        asyncio.run(rejudge(args.concurrency))
    analyze()
