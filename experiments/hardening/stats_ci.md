# Bootstrap CIs and common-denominator ablation

Seeded (20260714), B=4000 resamples, stdlib only. Rerun: `python scripts/stats_ci.py`.

**Calibrated inflation (lenient − golden, joint):** 5.74 pp (n=1534); item bootstrap 95% CI [4.6, 6.9]; conversation-cluster 95% CI [4.9, 6.5].
**Same-backbone rubric gap (mem0-4o − LongMemEval, both gpt-4o):** 10.27 pp (n=1539); item 95% CI [8.8, 11.8]; cluster 95% CI [8.9, 11.8].

**Common-denominator ablation (answers scored by all six judges): n=1371**

| judge | score % | drop from lenient (pp) |
|---|---:|---:|
| no_paraphrase | 87.4 | +3.2 |
| no_datetol | 86.5 | +4.1 |
| no_partial | 83.8 | +6.8 |
| no_extradetail | 65.0 | +25.6 |
| strict | 34.7 | +55.9 |
| lenient (anchor) | 90.6 | 0.0 |

Single-rule drops sum to 39.7 pp vs the full swing 55.9 pp on the same n; the gap is rule interaction. Ordering unchanged vs the per-variant denominators.
