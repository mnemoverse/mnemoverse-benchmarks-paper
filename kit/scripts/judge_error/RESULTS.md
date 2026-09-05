# Judge Error Analysis — conv-26 (LoCoMo)

## Data provenance

| Private source (mnemoverse-core path, not in this repo) | Public copy in this repo | Role |
|---|---|---|
| `experiments/results/rejudge_20260521_235650.json` | `kit/data/rejudge_20260521_235650.json` | 4-judge verdicts on **our engine's** answers (n=152) |
| `experiments/results/rejudge_q8_20260531T201308Z.json` | `kit/data/rejudge_q8_20260531T201308Z.json` | 2-judge verdicts on the **control-slice** answers (Mem0 OSS retrieval, our reader; n_scored=143) |
| `experiments/results/locomo_20260521_230400.json` | `kit/data/answers_engine_conv26.json` | Our engine's per-question answers + metadata |
| `experiments/results/comparison_20260530_024828.json` | `kit/data/answers_mem0_conv26.json` | The control-slice answers |
| `experiments/data/locomo10.json` | `kit/data/locomo_gold_ids.json` (ids/categories) + the `gold` fields of the answer files | Gold answers + evidence + categories |


## Objective subset (rule-based ground truth)

Ground-truth proxy: an answer is TRUE-correct iff the normalised gold token
(or any date-format variant) appears in the normalised system answer.

**Included categories:** `single_hop`, `temporal`, `multi_hop` (only discrete golds).
**Excluded:** `open_domain` (subjective), `adversarial` (not in run).

### Caveat on proxy strictness

> This proxy is **strict by design**: it can under-credit a correct paraphrase
> (e.g. 'trans woman' for gold 'Transgender woman'). That systematic bias means
> the proxy itself has a FN tendency — judges that agree with correct paraphrases
> will look _more lenient_ here than they truly are. The human label sheet
> (`kit/judge_audit/label_sheet.csv`) exists to calibrate this.

### Our engine — objective subset size

Total questions in run: **152**  
Objective subset: **117** questions

| Category | n in subset | proxy-TRUE | proxy-FALSE |
|----------|-------------|------------|-------------|
| multi_hop | 31 | 12 | 19 |
| single_hop | 49 | 26 | 23 |
| temporal | 37 | 19 | 18 |

## Judge error metrics — our engine's answers

### Overall

| Judge | Model | n | Accuracy vs proxy | FP rate (leniency error) | FN rate (strictness error) |
|-------|-------|---|-------------------|--------------------------|----------------------------|
| mem0 | gpt-5 | 117 | 59.8% | 78.3% | 0.0% |
| mem0-4o | gpt-4o | 117 | 57.3% | 83.3% | 0.0% |
| strict | gpt-5 | 117 | 74.4% | 28.3% | 22.8% |
| mnemoverse | gpt-5-mini | 117 | 70.1% | 53.3% | 5.3% |

### Per category

| Judge | Category | n | Accuracy | FP rate | FN rate |
|-------|----------|---|----------|---------|---------|
| mem0 | multi_hop | 31 | 51.6% | 79.0% | 0.0% |
| mem0 | single_hop | 49 | 67.3% | 69.6% | 0.0% |
| mem0 | temporal | 37 | 56.8% | 88.9% | 0.0% |
| mem0-4o | multi_hop | 31 | 51.6% | 79.0% | 0.0% |
| mem0-4o | single_hop | 49 | 63.3% | 78.3% | 0.0% |
| mem0-4o | temporal | 37 | 54.0% | 94.4% | 0.0% |
| strict | multi_hop | 31 | 77.4% | 10.5% | 41.7% |
| strict | single_hop | 49 | 79.6% | 30.4% | 11.5% |
| strict | temporal | 37 | 64.9% | 44.4% | 26.3% |
| mnemoverse | multi_hop | 31 | 83.9% | 26.3% | 0.0% |
| mnemoverse | single_hop | 49 | 69.4% | 65.2% | 0.0% |
| mnemoverse | temporal | 37 | 59.5% | 66.7% | 15.8% |

## Judge error metrics — Mem0 OSS answers

Total questions scored: **143** (9 skipped due to empty/null answers in source)  
Objective subset: **110** questions

| Category | n in subset | proxy-TRUE | proxy-FALSE |
|----------|-------------|------------|-------------|
| multi_hop | 25 | 8 | 17 |
| single_hop | 49 | 25 | 24 |
| temporal | 36 | 9 | 27 |

### Overall

| Judge | Model | n | Accuracy vs proxy | FP rate (leniency error) | FN rate (strictness error) |
|-------|-------|---|-------------------|--------------------------|----------------------------|
| mem0 | gpt-5 | 110 | 63.6% | 58.8% | 0.0% |
| strict | gpt-5 | 110 | 75.4% | 19.1% | 33.3% |

### Per category

| Judge | Category | n | Accuracy | FP rate | FN rate |
|-------|----------|---|----------|---------|---------|
| mem0 | multi_hop | 25 | 60.0% | 58.8% | 0.0% |
| mem0 | single_hop | 49 | 69.4% | 62.5% | 0.0% |
| mem0 | temporal | 36 | 58.3% | 55.6% | 0.0% |
| strict | multi_hop | 25 | 84.0% | 5.9% | 37.5% |
| strict | single_hop | 49 | 75.5% | 25.0% | 24.0% |
| strict | temporal | 36 | 69.4% | 22.2% | 55.6% |

## Key findings

_(These findings are computed from the numbers above; no LLM adjudication.)_

**1. Most accurate judge (our engine answers):** `strict` at 74.4% accuracy vs proxy truth. `mem0-4o` is least accurate at 57.3%.

**2. mem0 judge error direction (our engine):** FP rate = 78.3%, FN rate = 0.0% — FP-dominant (over-credits).

**3. strict judge error direction (our engine):** FP rate = 28.3%, FN rate = 22.8% — balanced (both modes present; neither dominates strongly).

**4. mem0 judge on the control slice's answers (Mem0 OSS backend retrieval, our reader):** FP rate = 58.8%, FN rate = 0.0%. strict judge on the same answers: FP = 19.1%, FN = 33.3%.

## Caveats

1. **Proxy strictness:** The substring match under-credits paraphrases.  Any judge that accepts correct paraphrases will appear more lenient (higher FP rate) than it truly is.  The human label sheet is the antidote.

2. **Relative-date golds excluded:** Golds like 'The week before 9 June 2023' or 'The sunday before 25 May 2023' are excluded from the objective subset because no substring rule can reliably evaluate them without calendar arithmetic.

3. **multi_hop coverage:** multi_hop questions often have multi-part golds ('pottery, camping, painting, swimming') — the substring rule may partially credit a correct-but-incomplete answer as FALSE, inflating FN for lenient judges.

4. **n=152 (our engine) / n=143 (Mem0) on one conversation (conv-26):** Results are single-conversation; generalisation to other LoCoMo conversations should be tested before publishing cross-system claims.

5. **The 9 skipped questions (Mem0):** qids 143–151 had empty/null answers in the comparison file at rejudge time and were excluded from q8 scoring. All are single_hop. Their absence does not affect category-level conclusions since the single_hop subset remains well-powered.

---

_Generated by `scripts/judge_error/compute_judge_error.py` — all numbers trace to committed JSON files._
