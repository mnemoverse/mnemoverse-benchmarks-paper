"""Run the paper's hardening experiments, fully self-contained (kit only, no
internal-repo dependency). Uses kit/scripts/judge.py + kit/data/.

A) JUDGE VARIANCE ON THE CONTROL SLICE
   Re-judge q8 (the 143 conv-26 control-slice answers: Mem0 OSS backend retrieval,
   our reader) K times under {mem0, strict}:
   per-repeat accuracy + swing (is the 0.74->0.34 gap stable across repeats?),
   and within-case stdev across repeats (judge non-determinism on the fixed answer set).

B) CROSS-CONVERSATION SWING ON THE VENDOR'S OWN ANSWERS
   Re-judge Mem0's OWN published answers for all 10 LoCoMo conversations under
   {mem0, strict} -> per-conversation mem0->strict swing (does the 40-pt gap
   depend on conv-26?). Mem0's answers, both prompts public in the kit.

Saves per-(set,judge,repeat) verdicts (with judge REASONING -> the hall-of-shame)
plus a summary, into experiments/hardening/ in the paper repo.

    OPENAI_API_KEY=... python kit/scripts/run_experiments.py [--concurrency 8] [--repeats 3]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics as st
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
PAPER = KIT.parent
sys.path.insert(0, str(KIT / "scripts"))
from judge import run_judge, load_answers  # noqa: E402

OUTDIR = PAPER / "experiments" / "hardening"
VERDICTS = OUTDIR / "verdicts"


def _acc(recs) -> float:
    s = [r["score"] for r in recs if r["score"] in (0.0, 1.0)]
    return sum(s) / len(s) if s else float("nan")


def _save(name: str, obj) -> None:
    VERDICTS.mkdir(parents=True, exist_ok=True)
    (VERDICTS / f"{name}.json").write_text(json.dumps(obj, indent=1), encoding="utf-8")


async def part_a(concurrency: int, repeats: int) -> dict:
    recs = load_answers(KIT / "data" / "answers_mem0_conv26.json")
    print(f"[A] variance: q8 = the {len(recs)} conv-26 control-slice answers, {repeats} repeats x mem0+strict", flush=True)
    per = {"mem0": [], "strict": []}
    verds = {"mem0": [], "strict": []}
    for j in ("mem0", "strict"):
        for rep in range(repeats):
            r = await run_judge(recs, j, concurrency)
            per[j].append(round(r["accuracy"], 4))
            verds[j].append({x["qid"]: x["score"] for x in r["records"]})
            _save(f"A_{j}_rep{rep}", r["records"])
            print(f"[A]   {j} rep{rep}: acc={r['accuracy']:.4f}", flush=True)
    # within-case stdev across repeats
    within = {}
    for j in ("mem0", "strict"):
        qids = verds[j][0].keys()
        sds = []
        for q in qids:
            vals = [verds[j][rep][q] for rep in range(repeats) if verds[j][rep].get(q) in (0.0, 1.0)]
            if len(vals) >= 2:
                sds.append(st.pstdev(vals))
        within[j] = round(st.mean(sds), 4) if sds else 0.0
    swing = [round(per["mem0"][rep] - per["strict"][rep], 4) for rep in range(repeats)]
    return {
        "n": len(recs),
        "per_repeat_acc": per,
        "within_judge_stdev": within,
        "swing_per_repeat_pp": [round(s * 100, 1) for s in swing],
        "mean_swing_pp": round(st.mean(swing) * 100, 1),
        "swing_stdev_pp": round(st.pstdev(swing) * 100, 2) if repeats >= 2 else 0.0,
    }


async def part_b(concurrency: int) -> dict:
    convs = sorted((KIT / "data" / "mem0_oss_answers").glob("conv*.json"),
                   key=lambda p: int(p.stem.replace("conv", "")))
    print(f"[B] cross-conv: Mem0's own answers, {len(convs)} conversations x mem0+strict", flush=True)
    rows = []
    for cp in convs:
        recs = load_answers(cp)
        res = {}
        for j in ("mem0", "strict"):
            r = await run_judge(recs, j, concurrency)
            res[j] = r
            _save(f"B_{cp.stem}_{j}", r["records"])
        m, s = _acc(res["mem0"]["records"]), _acc(res["strict"]["records"])
        rows.append({"conv": cp.stem, "n": len(recs),
                     "mem0_acc": round(m, 4), "strict_acc": round(s, 4),
                     "swing_pp": round((m - s) * 100, 1)})
        print(f"[B]   {cp.stem}: mem0={m:.3f} strict={s:.3f} swing={ (m-s)*100:.1f}pp", flush=True)
    sw = [r["swing_pp"] for r in rows]
    return {
        "n_conversations": len(rows),
        "n_total": sum(r["n"] for r in rows),
        "per_conversation": rows,
        "swing_min_pp": min(sw), "swing_max_pp": max(sw),
        "swing_mean_pp": round(st.mean(sw), 1),
        "swing_stdev_pp": round(st.pstdev(sw), 2),
    }


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--skip-a", action="store_true")
    ap.add_argument("--skip-b", action="store_true")
    args = ap.parse_args()

    t0 = time.perf_counter()
    out = {"kind": "paper_hardening_selfcontained", "concurrency": args.concurrency, "repeats": args.repeats}
    if not args.skip_a:
        out["A_variance"] = await part_a(args.concurrency, args.repeats)
    if not args.skip_b:
        out["B_cross_conversation"] = await part_b(args.concurrency)
    out["elapsed_s"] = round(time.perf_counter() - t0, 1)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps({k: v for k, v in out.items() if k.startswith(("A_", "B_", "elapsed"))}, indent=2)[:2500], flush=True)
    print(f"\nwrote {OUTDIR/'summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
