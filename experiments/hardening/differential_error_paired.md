# Is the judge's leniency system-dependent? (question-clustered)

The two answer sets are the same conv-26 questions answered by two systems: 110 rule-decidable questions join on question text (engine set 117, control slice 110). A two-proportion test would treat them as independent samples; these do not. Seeded, B=10000. Rerun: `python scripts/differential_error_paired.py`.

**Full sets (the paper's figures):** engine FP 78.3% (n=60 proxy-wrong answers), control slice FP 58.8% (n=68); difference +19.5 pp.

## (a) Cluster bootstrap over the shared question frame

Difference in FP rate (engine − slice): median +17.9 pp, central 95% [+4.4, +31.7]; the difference is ≤ 0 in 0.5% of resamples.

## (b) Paired permutation (questions both systems answer proxy-wrong)

n = 46 such questions; the judge credits **34 from the engine and 34 from the slice** (difference +0); two-sided permutation p = 1.000 (system label exchanged within each question).

## (c) Where the aggregate gap lives: the singleton-wrong strata

Only the engine proxy-wrong: **10 questions, 9 credited**. Only the slice proxy-wrong: **22 questions, 6 credited**. The gap is localized here, not in the matched stratum -- but these are different questions, so this localizes the effect rather than identifying its mechanism.

Both (a) and (b) respect the shared question frame that a two-proportion test ignores.
