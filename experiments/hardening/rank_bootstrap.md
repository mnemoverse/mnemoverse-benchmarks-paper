# Rank-flip uncertainty (conv-26, k=50): five harness pipelines x four judges

Headline matrix = the five pipelines from the single 2026-06-07 harness sweep (identical reader gpt-5-mini, identical judge prompt hashes, identical cat!=5 filter). naked_cosine ran on the other runner path (category hints, relevance-formatted context, binary-text `mnemoverse` judge per ASYM-004, and answers ~2x longer) and is reported separately below, never inside the matrix. Paired bootstrap B=10000, seed 20260715. Tie rule: ties are not flips. Rerun: `python scripts/rank_bootstrap.py` (offline).

Gate vs committed aggregates: PASS

## Cell table (accuracy, x/152)
| pipeline | mem0 | mem0-4o | strict | mnemoverse |
|---|---:|---:|---:|---:|
| mem0_v3_cloud | 0.704 (107/152) | 0.724 (110/152) | 0.270 (41/152) | 0.625 (95/152) |
| mnemoverse_engine | 0.770 (117/152) | 0.822 (125/152) | 0.388 (59/152) | 0.711 (108/152) |
| mnemoverse_http | 0.579 (88/152) | 0.658 (100/152) | 0.217 (33/152) | 0.408 (62/152) |
| supermemory | 0.789 (120/152) | 0.822 (125/152) | 0.349 (53/152) | 0.651 (99/152) |
| zep | 0.638 (97/152) | 0.684 (104/152) | 0.191 (29/152) | 0.480 (73/152) |

## Observed (four judges, five harness pipelines): 2 of 10 pairs flip
- mnemoverse_engine vs supermemory: mem0: 0.770 vs 0.789 (margin 3 answers); mem0-4o: 0.822 vs 0.822 (margin 0 answers); strict: 0.388 vs 0.349 (margin 6 answers); mnemoverse: 0.711 vs 0.651 (margin 9 answers)
- mnemoverse_http vs zep: mem0: 0.579 vs 0.638 (margin 9 answers); mem0-4o: 0.658 vs 0.684 (margin 4 answers); strict: 0.217 vs 0.191 (margin 4 answers); mnemoverse: 0.408 vs 0.480 (margin 11 answers)

Same-backbone (mem0 vs strict, both gpt-5): 2 of 10 pairs flip: mnemoverse_engine~supermemory, mnemoverse_http~zep

Separately, naked_cosine (other runner path -- NOT part of the matrix above): mem0 0.809, mem0-4o 0.882, strict 0.362, mnemoverse 0.632. Its answers average ~105 characters against 43--70 for the harness pipelines, exactly the padded-answer shape the lenient prompt is measured to over-credit (+25.4pp extra-detail rule), so a lenient-judge win for it is not evidence about memory quality.
Top pipeline by judge (full argmax set; ties shown): mem0: supermemory; mem0-4o: mnemoverse_engine/supermemory; strict: mnemoverse_engine; mnemoverse: mnemoverse_engine

## Bootstrap (B=10000, paired question resampling)
- flip-count distribution (4 judges): median 2, 95% interval [0, 4]
- same-backbone flip count: median 1, 95% interval [0, 3]
- winner differs between judges in 66.6% of resamples
- observed flip mnemoverse_engine ~ supermemory: reproduces in 65.8% of resamples
- observed flip mnemoverse_http ~ zep: reproduces in 76.1% of resamples

## P(A>B) per judge (bootstrap), pairs involved in observed flips
- P(mnemoverse_engine > supermemory): mem0: 0.29, mem0-4o: 0.45, strict: 0.83, mnemoverse: 0.91
- P(mnemoverse_http > zep): mem0: 0.07, mem0-4o: 0.27, strict: 0.75, mnemoverse: 0.03
