# Single-rule ablation of the lenient prompt

Each variant is the mem0 lenient prompt with exactly ONE rule tightened to strict; `drop` = lenient score minus the variant's score on the jointly-scored answers = the swing that rule carries. Prompts: `kit/prompts/judge_abl_*.txt`; verdicts `experiments/hardening/verdicts/ABL_conv*.json`. Runner `scripts/run_extra_judges.py`.

| variant (rule tightened) | score % | drop from lenient (pp) |
|--------------------------|---------|------------------------|
| partial credit | 83.9 | +7.1 (n=1539) |
| paraphrase / semantic | 88.0 | +3.1 (n=1538) |
| date / duration tolerance | 86.3 | +4.3 (n=1381) |
| extra detail / referent | 65.6 | +25.4 (n=1527) |
| **lenient (anchor)** | **91.0** | 0.0 |
| **strict (all rules)** | **35.0** | **+56.1** |

Sum of single-rule drops = 40.0 pp vs the full lenient->strict swing 56.1 pp; the difference is rule interaction (an answer can be caught by more than one tightened rule, so single-rule drops overlap).
