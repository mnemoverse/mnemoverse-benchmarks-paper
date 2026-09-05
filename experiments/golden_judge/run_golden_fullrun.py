"""M4: golden v2 over Mem0's FULL published run (all 10 conversations, 1,539 answers).

Produces the calibrated-inflation estimate: how far the field's lenient prompt sits
from the human-band-validated judge on the vendor's own full run — reported beside
the 56pp lenient-vs-naive-strict sensitivity bound.

Saves per-conversation verdicts (B-style) + a summary with per-conv and n-weighted
aggregates, plus the mem0-vs-golden delta per conversation (mem0 accuracies read
from the committed experiments/hardening/summary.json).

    OPENAI_API_KEY=... python experiments/golden_judge/run_golden_fullrun.py
"""
from __future__ import annotations

import asyncio
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "kit" / "scripts"))
import judge  # noqa: E402

judge.JUDGE_PROMPT["golden2"] = "judge_golden_v2.txt"
judge.JUDGE_MODEL["golden2"] = "gpt-5"

VERDICTS = HERE / "fullrun_verdicts"


async def main() -> int:
    VERDICTS.mkdir(exist_ok=True)
    baseline = json.loads((REPO / "experiments" / "hardening" / "summary.json").read_text(encoding="utf-8"))
    mem0_by_conv = {r["conv"]: r for r in baseline["B_cross_conversation"]["per_conversation"]}

    convs = sorted((REPO / "kit" / "data" / "mem0_oss_answers").glob("conv*.json"),
                   key=lambda p: int(p.stem.replace("conv", "")))
    rows = []
    for cp in convs:
        recs = judge.load_answers(cp)
        r = await judge.run_judge(recs, "golden2", 8)
        (VERDICTS / f"{cp.stem}_golden2.json").write_text(
            json.dumps(r["records"], indent=1), encoding="utf-8")
        g = r["accuracy"]
        m = mem0_by_conv[cp.stem]["mem0_acc"]
        s = mem0_by_conv[cp.stem]["strict_acc"]
        rows.append({"conv": cp.stem, "n": r["n"], "n_total": r["n_total"],
                     "golden_acc": round(g, 4), "mem0_acc": m, "strict_acc": s,
                     "inflation_mem0_minus_golden_pp": round((m - g) * 100, 1)})
        print(f"{cp.stem}: golden={g:.4f} mem0={m:.4f} inflation={ (m-g)*100:+.1f}pp "
              f"(n={r['n']}/{r['n_total']})", flush=True)

    N = sum(r["n"] for r in rows)
    gw = sum(r["golden_acc"] * r["n"] for r in rows) / N
    mw = sum(r["mem0_acc"] * r["n"] for r in rows) / N
    sw = sum(r["strict_acc"] * r["n"] for r in rows) / N
    infl = [r["inflation_mem0_minus_golden_pp"] for r in rows]
    out = {
        "_note": "Golden v2 (human-calibrated, validated 97.7% OOS) over Mem0's full published run. "
                 "calibrated inflation = mem0-lenient minus golden, i.e. how much the field prompt "
                 "inflates the vendor's own headline relative to a human-band-validated judge.",
        "n_total": N,
        "weighted": {"golden": round(gw, 4), "mem0": round(mw, 4), "strict_naive": round(sw, 4),
                     "calibrated_inflation_pp": round((mw - gw) * 100, 1),
                     "sensitivity_bound_pp": round((mw - sw) * 100, 1)},
        "per_conversation": rows,
        "inflation_range_pp": [min(infl), max(infl)],
        "inflation_mean_pp": round(st.mean(infl), 1),
        "inflation_stdev_pp": round(st.pstdev(infl), 2),
    }
    (HERE / "FULLRUN_GOLDEN_RESULTS.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out["weighted"], indent=2))
    print(f"inflation per conv: {infl}  range {min(infl)}..{max(infl)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
