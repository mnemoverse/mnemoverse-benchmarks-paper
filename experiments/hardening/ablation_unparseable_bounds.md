# Date-tolerance (and all) ablation: unparseable-row bounds

Drop from lenient (91.0 on its own scored set) under three handlings of each variant's unparseable rows. Paper convention = excluded. Rerun: `python scripts/ablation_unparseable_bounds.py`.

| variant | unparseable | drop (excluded) | drop (all correct) | drop (all wrong) |
|---|---:|---:|---:|---:|
| abl-no-paraphrase | 1 | +3.1 | +3.1 | +3.1 |
| abl-no-datetol | 158 | +4.3 | +3.3 | +13.6 |
| abl-no-partial | 0 | +7.1 | +7.1 | +7.1 |
| abl-no-extradetail | 12 | +25.4 | +25.2 | +26.0 |

Ordering under excluded: extradetail > partial > datetol > paraphrase
Ordering under all-correct: extradetail > partial > datetol > paraphrase
Ordering under all-wrong: extradetail > datetol > partial > paraphrase
