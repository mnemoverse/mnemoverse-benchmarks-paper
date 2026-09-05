> **SUPERSEDED (2026-07-15) -- not cited by the paper.** This analysis pools six
> pipelines, but `naked_cosine` ran on a different runner path from the other five
> (answers ~105 chars vs 43-70; its `mnemoverse` judge is the binary-text prompt,
> not the JSON one the harness cells use -- core ASYM-004). Its 4/15 and 4/10 flip
> counts therefore mix two answer paths and two judge prompts under one label, and
> its Spearman values run over 5-6 points (5% critical value 0.90). The paper reports
> the five-pipeline single-sweep matrix with a paired bootstrap instead:
> `experiments/hardening/rank_bootstrap.md` -- 2 of 10 pairs flip, 95% interval [0, 4].

# Multi-system rank stability under judge variation (conv-26, historic six-pipeline pooling)

Six pipelines x four judges as originally pooled -- NOT a symmetric comparison; see banner. Source artifact `kit/data/matrix_conv26_multijudge.json`; rerun `python scripts/multi_system_rank.py`.

## k = 10  (6 systems)

| system | mnemoverse | mem0 | mem0-4o | strict |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.572 | 0.684 | 0.711 | 0.257 |
| mnemoverse_engine | 0.691 | 0.803 | 0.822 | 0.375 |
| mnemoverse_http | 0.296 | 0.428 | 0.454 | 0.125 |
| naked_cosine | 0.592 | 0.770 | 0.816 | 0.283 |
| supermemory | 0.342 | 0.421 | 0.474 | 0.191 |
| zep | 0.217 | 0.296 | 0.329 | 0.086 |

**Rank reversals: 1 of 15 system pairs flip order between judges.**
- mnemoverse_http vs supermemory -> winner by judge: mnemoverse: supermemory, mem0: mnemoverse_http, mem0-4o: supermemory, strict: supermemory

Spearman rank correlation between judges: mnemoverse~mem0: 0.94; mnemoverse~mem0-4o: 1.00; mnemoverse~strict: 1.00; mem0~mem0-4o: 0.94; mem0~strict: 0.94; mem0-4o~strict: 1.00

## k = 20  (6 systems)

| system | mnemoverse | mem0 | mem0-4o | strict |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.625 | 0.717 | 0.737 | 0.283 |
| mnemoverse_engine | 0.684 | 0.809 | 0.849 | 0.362 |
| mnemoverse_http | 0.362 | 0.507 | 0.566 | 0.151 |
| naked_cosine | 0.599 | 0.776 | 0.855 | 0.336 |
| supermemory | 0.421 | 0.533 | 0.546 | 0.237 |
| zep | 0.355 | 0.480 | 0.546 | 0.125 |

**Rank reversals: 4 of 15 system pairs flip order between judges.**
- mem0_v3_cloud vs naked_cosine -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: naked_cosine, mem0-4o: naked_cosine, strict: naked_cosine
- mnemoverse_engine vs naked_cosine -> winner by judge: mnemoverse: mnemoverse_engine, mem0: mnemoverse_engine, mem0-4o: naked_cosine, strict: mnemoverse_engine
- mnemoverse_http vs supermemory -> winner by judge: mnemoverse: supermemory, mem0: supermemory, mem0-4o: mnemoverse_http, strict: supermemory
- supermemory vs zep -> winner by judge: mnemoverse: supermemory, mem0: supermemory, mem0-4o: zep, strict: supermemory

Spearman rank correlation between judges: mnemoverse~mem0: 0.94; mnemoverse~mem0-4o: 0.72; mnemoverse~strict: 0.94; mem0~mem0-4o: 0.84; mem0~strict: 1.00; mem0-4o~strict: 0.84

## k = 50  (6 systems)

| system | mnemoverse | mem0 | mem0-4o | strict |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.625 | 0.704 | 0.724 | 0.270 |
| mnemoverse_engine | 0.711 | 0.770 | 0.822 | 0.388 |
| mnemoverse_http | 0.408 | 0.579 | 0.658 | 0.217 |
| naked_cosine | 0.632 | 0.809 | 0.882 | 0.362 |
| supermemory | 0.651 | 0.789 | 0.822 | 0.349 |
| zep | 0.480 | 0.638 | 0.684 | 0.191 |

**Rank reversals: 4 of 15 system pairs flip order between judges.**
- mnemoverse_engine vs naked_cosine -> winner by judge: mnemoverse: mnemoverse_engine, mem0: naked_cosine, mem0-4o: naked_cosine, strict: mnemoverse_engine
- mnemoverse_engine vs supermemory -> winner by judge: mnemoverse: mnemoverse_engine, mem0: supermemory, mem0-4o: supermemory, strict: mnemoverse_engine
- mnemoverse_http vs zep -> winner by judge: mnemoverse: zep, mem0: zep, mem0-4o: zep, strict: mnemoverse_http
- naked_cosine vs supermemory -> winner by judge: mnemoverse: supermemory, mem0: naked_cosine, mem0-4o: naked_cosine, strict: naked_cosine

Spearman rank correlation between judges: mnemoverse~mem0: 0.77; mnemoverse~mem0-4o: 0.81; mnemoverse~strict: 0.89; mem0~mem0-4o: 0.99; mem0~strict: 0.77; mem0-4o~strict: 0.84

## k = 100  (5 systems)

| system | mnemoverse | mem0 | mem0-4o | strict |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.664 | 0.711 | 0.750 | 0.276 |
| mnemoverse_engine | 0.664 | 0.750 | 0.803 | 0.362 |
| mnemoverse_http | 0.526 | 0.697 | 0.783 | 0.283 |
| naked_cosine | 0.664 | 0.809 | 0.882 | 0.408 |
| supermemory | 0.638 | 0.770 | 0.829 | 0.336 |

**Rank reversals: 3 of 10 system pairs flip order between judges.**
- mem0_v3_cloud vs mnemoverse_http -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: mem0_v3_cloud, mem0-4o: mnemoverse_http, strict: mnemoverse_http
- mem0_v3_cloud vs supermemory -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: supermemory, mem0-4o: supermemory, strict: supermemory
- mnemoverse_engine vs supermemory -> winner by judge: mnemoverse: mnemoverse_engine, mem0: supermemory, mem0-4o: supermemory, strict: mnemoverse_engine

Spearman rank correlation between judges: mnemoverse~mem0: 0.45; mnemoverse~mem0-4o: 0.11; mnemoverse~strict: 0.34; mem0~mem0-4o: 0.90; mem0~strict: 0.80; mem0-4o~strict: 0.90

## k = 200  (5 systems)

| system | mnemoverse | mem0 | mem0-4o | strict |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.664 | 0.730 | 0.743 | 0.270 |
| mnemoverse_engine | 0.638 | 0.743 | 0.809 | 0.375 |
| mnemoverse_http | 0.539 | 0.717 | 0.789 | 0.316 |
| naked_cosine | 0.704 | 0.842 | 0.901 | 0.375 |
| supermemory | 0.645 | 0.796 | 0.836 | 0.349 |

**Rank reversals: 4 of 10 system pairs flip order between judges.**
- mem0_v3_cloud vs mnemoverse_engine -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: mnemoverse_engine, mem0-4o: mnemoverse_engine, strict: mnemoverse_engine
- mem0_v3_cloud vs mnemoverse_http -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: mem0_v3_cloud, mem0-4o: mnemoverse_http, strict: mnemoverse_http
- mem0_v3_cloud vs supermemory -> winner by judge: mnemoverse: mem0_v3_cloud, mem0: supermemory, mem0-4o: supermemory, strict: supermemory
- mnemoverse_engine vs supermemory -> winner by judge: mnemoverse: supermemory, mem0: supermemory, mem0-4o: supermemory, strict: mnemoverse_engine

Spearman rank correlation between judges: mnemoverse~mem0: 0.70; mnemoverse~mem0-4o: 0.40; mnemoverse~strict: 0.15; mem0~mem0-4o: 0.90; mem0~strict: 0.72; mem0-4o~strict: 0.82

Reproduction gate: k=200 -> (4, 10, 0.15389675281277312), k=50 -> (4, 15, 0.7714285714285715) (expected reversals 4/10 and 4/15) => PASS
