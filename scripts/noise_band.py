#!/usr/bin/env python3
"""What is the judge's noise on a SLICE-LEVEL score? (round-2 cold read, item 3)

The variance study repeats each judge 3x on 20 questions. Its headline field
`mean_within_qid_stdev` (0.014) is the average standard deviation of a SINGLE
QUESTION's verdict across repeats -- it is NOT the standard deviation of a
slice-level accuracy, and it must not be compared to the cross-judge spread of
judge MEANS (0.107) or propagated to a 152-question score.

This script computes the quantity the paper actually needs, three ways:
  (a) run-to-run sd of the 20-question MEAN, per judge (from the repeat scores);
  (b) the same rescaled to n=152 (sd_mean scales as 1/sqrt(n));
  (c) the direct empirical check: three repeats of the lenient-minus-strict
      difference on the 143-answer control slice (kit/data variance record in
      experiments/hardening/summary.json A_variance) -- the sd of a DIFFERENCE
      of two prompt-judged scores, which is what a rank flip actually turns on.

    python scripts/noise_band.py     (offline)
Writes experiments/hardening/noise_band.md.
"""
from __future__ import annotations
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VS = REPO / "kit" / "data" / "variance_study_20260603_2300.json"
SUM = REPO / "experiments" / "hardening" / "summary.json"
OUT = REPO / "experiments" / "hardening" / "noise_band.md"


def main():
    vs = json.loads(VS.read_text(encoding="utf-8"))
    per = vs["per_cell_judge"]          # one record per (qid, judge) with .scores = 3 repeats
    by_judge = {}
    for r in per:
        by_judge.setdefault(r["judge"], []).append(r["scores"])

    L = ["# What the judge's noise actually is, at slice level", "",
         "The variance study is 3 repeats x 20 questions x 4 judges "
         f"(`{VS.name}`). All standard deviations here are SAMPLE sd (n-1), the convention "
         "the source artifact's own `stdev` field uses -- mixing conventions is how the "
         "0.014 figure got misquoted in the first place. Rerun: `python scripts/noise_band.py`.", ""]
    L.append("| judge | mean per-question sd (the 0.014 figure) | sd of the 20-question mean across repeats | implied sd at n=152 |")
    L.append("|---|---:|---:|---:|")
    means_at_152 = []
    for j, rows in sorted(by_judge.items()):
        n_rep = len(rows[0])
        per_q_sd = st.mean(st.stdev(s) for s in rows)
        # run-level means: repeat r's mean over the 20 questions
        run_means = [st.mean(s[r] for s in rows) for r in range(n_rep)]
        sd_mean_20 = st.stdev(run_means)
        sd_at_152 = sd_mean_20 * (20 / 152) ** 0.5
        means_at_152.append(sd_at_152)
        L.append(f"| {j} | {per_q_sd:.4f} | {sd_mean_20:.4f} (n=20) | {sd_at_152:.4f} |")
    L.append("")
    L.append(f"Mean sd of a slice-level score at n=152: **{100*st.mean(means_at_152):.2f} pp** "
             f"(vs the {100*st.mean(st.mean(st.stdev(s) for s in rows) for rows in by_judge.values()):.1f} pp "
             "per-question figure the paper has been quoting as if it were a slice-level band).")
    L.append("")

    # (c) direct: three repeats of the lenient-strict DIFFERENCE on the 143-answer slice
    summ = json.loads(SUM.read_text(encoding="utf-8"))
    a = summ.get("A_variance", {})
    swings = a.get("swings_pp") or a.get("swing_pp_per_repeat")
    if swings is None:  # dig
        swings = [v for k, v in a.items() if "swing" in k and isinstance(v, list)]
        swings = swings[0] if swings else None
    if swings:
        L.append("## Direct measurement (what a flip actually turns on)")
        L.append("")
        L.append(f"Three repeats of the lenient-minus-strict difference on the 143-answer control "
                 f"slice: {' / '.join(f'{x}' for x in swings)} pp -> sample sd "
                 f"**{st.stdev(swings):.2f} pp** (population sd {st.pstdev(swings):.2f}). "
                 "This is the sd of a DIFFERENCE of two prompt-judged scores -- the quantity a "
                 "rank flip between two pipelines turns on -- and it agrees with the rescaled "
                 "estimate above, not with the per-question figure.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
