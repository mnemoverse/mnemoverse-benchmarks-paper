# What the judge's noise actually is, at slice level

The variance study is 3 repeats x 20 questions x 4 judges (`variance_study_20260603_2300.json`). All standard deviations here are SAMPLE sd (n-1), the convention the source artifact's own `stdev` field uses -- mixing conventions is how the 0.014 figure got misquoted in the first place. Rerun: `python scripts/noise_band.py`.

| judge | mean per-question sd (the 0.014 figure) | sd of the 20-question mean across repeats | implied sd at n=152 |
|---|---:|---:|---:|
| mem0 | 0.0289 | 0.0289 (n=20) | 0.0105 |
| mem0-4o | 0.0000 | 0.0000 (n=20) | 0.0000 |
| mnemoverse | 0.0000 | 0.0000 (n=20) | 0.0000 |
| strict | 0.0289 | 0.0289 (n=20) | 0.0105 |

Mean sd of a slice-level score at n=152: **0.52 pp** (vs the 1.4 pp per-question figure the paper has been quoting as if it were a slice-level band).

## Direct measurement (what a flip actually turns on)

Three repeats of the lenient-minus-strict difference on the 143-answer control slice: 41.3 / 40.6 / 39.9 pp -> sample sd **0.70 pp** (population sd 0.57). This is the sd of a DIFFERENCE of two prompt-judged scores -- the quantity a rank flip between two pipelines turns on -- and it agrees with the rescaled estimate above, not with the per-question figure.
