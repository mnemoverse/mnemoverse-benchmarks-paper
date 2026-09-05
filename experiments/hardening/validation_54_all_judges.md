# All graders on the same 54 validation items

Offline join of committed verdicts; rerun `python scripts/validation_54_all_judges.py`.

## Human-implied score band on the 54, per rater standard

| standard | CORRECT | WRONG | ambiguous | band |
|---|---:|---:|---:|---:|
| lead annotator | 38 | 6 | 10 | [70.4, 88.9] |
| O.T. | 45 | 4 | 5 | [83.3, 92.6] |
| A.S. | 46 | 4 | 4 | [85.2, 92.6] |
| 3-rater majority | 45 | 4 | 5 | [83.3, 92.6] |

The lead annotator marks the most cases ambiguous, so that band is the widest; the two additional raters decide more cases toward credit, so their bands sit higher. A claim that a judge scores above 'the human band' must name the standard.

## Grader scores and agreement

| grader | score on the 54 | vs lead annotator (44 decided) | vs OI decided | vs NS decided | vs 3-rater majority (decided) |
|---|---:|---:|---:|---:|---:|
| golden | 85.2\% (n=54) | 43/44 | 46/49 | 47/50 | 47/49 |
| lenient | 94.4\% (n=54) | 41/44 | 47/49 | 48/50 | 48/49 |
| strict | 33.3\% (n=54) | 24/44 | 21/49 | 22/50 | 22/49 |
| longmemeval | 83.3\% (n=54) | 38/44 | 44/49 | 43/50 | 44/49 |
