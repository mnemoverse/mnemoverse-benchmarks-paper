#!/usr/bin/env python3
"""Full-set model-vs-prompt decomposition (Andrey-review B1; open-work B1/R11).

Re-judges Mem0's full published run (all 10 conversations, 1,539 answers) under
gpt-4o with BOTH prompts (mem0-4o, strict-4o). Together with the committed gpt-5
verdicts (experiments/hardening/verdicts/B_conv*_{mem0,strict}.json) this yields,
on the FULL SET rather than conv-26 alone:

  prompt effect  = mem0 - strict          (within each model)
  model  effect  = gpt-5 - gpt-4o         (within each prompt)

computed on jointly-scored answers per comparison, per conversation and overall.

    OPENAI_API_KEY=... python scripts/run_model_vs_prompt_fullset.py [--concurrency 12]

Writes per-answer verdicts to experiments/hardening/verdicts/MV_conv{N}_{judge}.json
and the summary+markdown to experiments/hardening/model_vs_prompt_fullset.{json,md}.
Resumable: conversations whose verdict files already exist are skipped.
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
OUT_JSON = REPO / "experiments" / "hardening" / "model_vs_prompt_fullset.json"
OUT_MD = REPO / "experiments" / "hardening" / "model_vs_prompt_fullset.md"

CONVS = [f"conv{i}" for i in range(10)]
NEW_JUDGES = ("mem0-4o", "strict-4o")


def scored_map(path: Path) -> dict[str, float]:
    recs = json.loads(path.read_text(encoding="utf-8"))
    return {r["qid"]: float(r["score"]) for r in recs
            if isinstance(r.get("score"), (int, float)) and r["score"] in (0.0, 1.0)}


def acc_joint(a: dict[str, float], b: dict[str, float]) -> tuple[float, float, int]:
    joint = sorted(set(a) & set(b))
    if not joint:
        return float("nan"), float("nan"), 0
    return (sum(a[q] for q in joint) / len(joint),
            sum(b[q] for q in joint) / len(joint), len(joint))


async def rejudge(concurrency: int) -> None:
    for conv in CONVS:
        recs = load_answers(DATA / f"{conv}.json")
        for judge in NEW_JUDGES:
            out = VERDICTS / f"MV_{conv}_{judge}.json"
            if out.exists():
                print(f"[skip] {out.name} exists", flush=True)
                continue
            t0 = time.time()
            r = await run_judge(recs, judge, concurrency)
            out.write_text(json.dumps(r["records"], indent=1), encoding="utf-8")
            print(f"[done] {conv} {judge}: acc={r['accuracy']:.4f} n={r['n']}/{r['n_total']} "
                  f"({time.time()-t0:.0f}s)", flush=True)


def analyze() -> None:
    rows = []
    agg: dict[str, dict[str, float]] = {}
    pools: dict[str, dict[str, float]] = {j: {} for j in
        ("mem0_g5", "strict_g5", "mem0_4o", "strict_4o")}
    for conv in CONVS:
        maps = {
            "mem0_g5": scored_map(VERDICTS / f"B_{conv}_mem0.json"),
            "strict_g5": scored_map(VERDICTS / f"B_{conv}_strict.json"),
            "mem0_4o": scored_map(VERDICTS / f"MV_{conv}_mem0-4o.json"),
            "strict_4o": scored_map(VERDICTS / f"MV_{conv}_strict-4o.json"),
        }
        for k, m in maps.items():
            pools[k].update({f"{conv}:{q}": s for q, s in m.items()})
        p5a, p5b, n5 = acc_joint(maps["mem0_g5"], maps["strict_g5"])
        p4a, p4b, n4 = acc_joint(maps["mem0_4o"], maps["strict_4o"])
        mma, mmb, nmm = acc_joint(maps["mem0_g5"], maps["mem0_4o"])
        msa, msb, nms = acc_joint(maps["strict_g5"], maps["strict_4o"])
        rows.append({
            "conv": conv,
            "prompt_effect_gpt5_pp": (p5a - p5b) * 100, "n_p5": n5,
            "prompt_effect_gpt4o_pp": (p4a - p4b) * 100, "n_p4": n4,
            "model_effect_mem0_pp": (mma - mmb) * 100, "n_mm": nmm,
            "model_effect_strict_pp": (msa - msb) * 100, "n_ms": nms,
        })

    def overall(a_key: str, b_key: str) -> tuple[float, int]:
        a, b = pools[a_key], pools[b_key]
        j = sorted(set(a) & set(b))
        return (sum(a[q] for q in j) / len(j) - sum(b[q] for q in j) / len(j)) * 100, len(j)

    o_p5, n_p5 = overall("mem0_g5", "strict_g5")
    o_p4, n_p4 = overall("mem0_4o", "strict_4o")
    o_mm, n_mm = overall("mem0_g5", "mem0_4o")
    o_ms, n_ms = overall("strict_g5", "strict_4o")

    # 2x2 identity: prompt-effect difference must equal model-effect difference
    ident = (o_p5 - o_p4) - (o_mm - o_ms)
    assert abs(ident) < 1e-9, f"2x2 identity violated: {ident}"

    summary = {"per_conversation": rows, "overall": {
        "prompt_effect_gpt5_pp": o_p5, "n": n_p5,
        "prompt_effect_gpt4o_pp": o_p4, "n_4o": n_p4,
        "model_effect_mem0_prompt_pp": o_mm, "n_mem0": n_mm,
        "model_effect_strict_prompt_pp": o_ms, "n_strict": n_ms,
    }}
    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")

    L = []
    L.append("# Full-set model-vs-prompt decomposition (all 10 conversations, Mem0 published answers)")
    L.append("")
    L.append("Provenance: gpt-5 verdicts = committed `experiments/hardening/verdicts/B_conv*_{mem0,strict}.json`; "
             "gpt-4o verdicts = `MV_conv*_{mem0-4o,strict-4o}.json` produced by this script "
             "(`scripts/run_model_vs_prompt_fullset.py`); effects computed on jointly-scored answers per comparison. "
             "Sign convention: model effect = gpt-5 minus gpt-4o (negative = gpt-4o more generous). "
             "The 2x2 identity (prompt-effect difference == model-effect difference) is asserted at build time.")
    L.append("")
    L.append("| conv | prompt effect (gpt-5) | prompt effect (gpt-4o) | model effect (mem0 prompt) | model effect (strict prompt) |")
    L.append("|------|----------------------|------------------------|----------------------------|------------------------------|")
    for r in rows:
        L.append(f"| {r['conv']} | {r['prompt_effect_gpt5_pp']:+.1f} (n={r['n_p5']}) "
                 f"| {r['prompt_effect_gpt4o_pp']:+.1f} (n={r['n_p4']}) "
                 f"| {r['model_effect_mem0_pp']:+.1f} (n={r['n_mm']}) "
                 f"| {r['model_effect_strict_pp']:+.1f} (n={r['n_ms']}) |")
    L.append(f"| **all** | **{o_p5:+.1f}** (n={n_p5}) | **{o_p4:+.1f}** (n={n_p4}) "
             f"| **{o_mm:+.1f}** (n={n_mm}) | **{o_ms:+.1f}** (n={n_ms}) |")
    L.append("")
    L.append(f"Ratio of mean |prompt effect| to mean |model effect| (overall): "
             f"{(abs(o_p5)+abs(o_p4))/2:.1f} / {(abs(o_mm)+abs(o_ms))/2:.1f} = "
             f"{((abs(o_p5)+abs(o_p4))/2) / max(0.05,(abs(o_mm)+abs(o_ms))/2):.1f}x")
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
