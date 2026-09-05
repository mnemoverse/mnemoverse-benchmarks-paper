# Reproducing the paper's numbers and figures

Every load-bearing number in the paper traces to a committed **public** artifact in
**this** repository's [`kit/`](./kit/). Nothing is needed from the private
`mnemoverse-core` repo. The map from each artifact to its provenance is
[`kit/MANIFEST.md`](./kit/MANIFEST.md).

## One-command verification

```bash
pip install -r kit/scripts/requirements.txt
export OPENAI_API_KEY=sk-...        # only the judge-swing check needs this
python kit/scripts/verify_claims.py
```

`verify_claims.py` runs three checks and exits non-zero if any fail:

1. **Committed recall summary (judge-free, exact).** Reads the naked-cosine
   recall@k values straight from `kit/data/RECALL_AT_K_SUMMARY.json`.
2. **Standalone recall recompute (judge-free, exact, no API).** Re-derives those
   same recall@k numbers from scratch from `kit/data/naked_cosine_conv26_retrieved.json`
   (per-question top-200 retrieved IDs) and `kit/data/locomo_gold_ids.json` (gold
   evidence IDs). Must match the committed summary bit-for-bit.
3. **The judge swing (within tolerance).** Re-judges the 143 conv-26 control-slice answers
   (`kit/data/answers_mem0_conv26.json` — Mem0 OSS backend retrieval, our reader; see
   `kit/data/ATTRIBUTION.md`) under the two prompts in `kit/prompts/`. The
   only thing that changes is the grading instruction; the score moves ~40 points
   (mem0 ≈ 0.74, strict ≈ 0.34). Reproduces within the published tolerance, because
   LLM judges are non-deterministic (a judged score moves ~0.5-0.7 pp between runs at
   this slice size -- see `scripts/noise_band.py` -- far below the 40 pp effect).

## Recall without an API key

The two judge-free recall checks can be run on their own — no `OPENAI_API_KEY`,
no LLM, nothing outside this repo:

```bash
python kit/scripts/recompute_recall.py
```

Expected bit-for-bit match at k=5/10/20/50/100/200 against the published values
(0.595 / 0.721 / 0.780 / 0.886 / 0.938 / 0.981).

## Offline recomputes (no API key, no private repo)

Each script reads committed artifacts only, prints its table, and writes it to
`experiments/hardening/`. These cover every statistic added during the round-2 review
cycle:

```bash
python scripts/rank_bootstrap.py              # five-pipeline x four-judge matrix (§3):
                                              # cells, flips, margins, paired bootstrap.
                                              # Fail-closed: asserts every recomputed cell
                                              # against kit/data/matrix_conv26_multijudge.json
python scripts/stats_ci.py                    # bootstrap CIs for the 5.7 and 10.3 estimates,
                                              # common-denominator ablation (n=1371)
python scripts/validation_54_all_judges.py    # every grader and every rater band on the
                                              # same 54 validation answers (Table 5)
python scripts/golden_vs_externals.py         # calibrated judge vs the two additional raters
python scripts/ablation_unparseable_bounds.py # best/worst bounds for unparseable verdicts
python scripts/per_conv_calibrated.py         # per-conversation calibrated inflation (Table 6)
python scripts/differential_error_paired.py   # paired/cluster analysis of proxy errors
python scripts/noise_band.py                  # limited three-repeat noise diagnostics
```

## Claim-to-command registry

Only rows in this table are certified as offline-recomputable. “Exact” means exact from
the committed derived artifacts; it does not mean that private answer generation can be
re-run or that a mutable provider alias will reproduce old verdicts.

| Paper result | Inputs | Command | Expected check | Tier |
| --- | --- | --- | --- | --- |
| Naked-cosine recall curve | `kit/data/naked_cosine_conv26_retrieved.json`, `kit/data/locomo_gold_ids.json` | `python kit/scripts/recompute_recall.py` | k=5/10/20/50/100/200 = 0.595/0.721/0.780/0.886/0.938/0.981 | offline exact from retrieved IDs |
| Judge-error table (Table 4) and control-slice FP/FN note | `kit/data/answers_engine_conv26.json`, `kit/data/rejudge_20260521_235650.json`, `kit/data/rejudge_q8_20260531T201308Z.json`; proxy rule imported from `kit/scripts/judge_error/compute_judge_error.py` | `python kit/scripts/recompute_judge_error.py` | n=117 / n=110; every acc/FP/FN cell reproduces; ends with `ALL TABLE-2 NUMBERS REPRODUCE` | offline exact from committed artifacts |
| Five-pipeline judge matrix and rank stability | `kit/data/matrix_conv26_perq.json`, `matrix_conv26_multijudge.json` | `python scripts/rank_bootstrap.py` | aggregate cells assert; flip-count stability range `[0,4]` | offline exact from verdicts |
| 5.7/10.3-point model contrasts | committed full-run verdicts | `python scripts/stats_ci.py` | script exits zero and prints registered intervals | offline exact from verdicts; calibration uncertainty excluded |
| 54-item rater-implied ambiguity intervals | validation verdicts and labels | `python scripts/validation_54_all_judges.py` | Table 5 counts | offline exact from labels |
| Differential-error localization | proxy decisions and paired answers | `python scripts/differential_error_paired.py` | +17.9 pp; both-wrong credits 34/34 | offline exact from derived decisions; no mechanism claim |
| Per-conversation `golden-v2` contrast | full-run verdicts | `python scripts/per_conv_calibrated.py` | ten rows; aggregate 5.7 pp on joint denominator | offline exact from verdicts |
| Repeat-variability diagnostic | `kit/data/variance_study_20260603_2300.json` and control repeats | `python scripts/noise_band.py` | approximately 0.5--0.7 pp | descriptive; three repeats only |
| Control-slice prompt swing | fixed answers and two prompts | `python kit/scripts/verify_claims.py` | within published tolerance | paid re-judge; mutable alias |

The full paid re-judge is currently **script-by-script**, not one-command. Relevant
entry points include `kit/scripts/run_experiments.py`,
`scripts/run_model_vs_prompt_fullset.py`, `scripts/run_extra_judges.py`,
`scripts/run_third_rubric_longmemeval.py`, and `scripts/run_beam_rescore.py`.
Each requires the provider credentials used by that runner. Provider aliases may have
changed or been retired, so this tier reconstructs the protocol where available; it is
not guaranteed verdict identity. A unified 9,200-call orchestrator is not currently
claimed.

## Prospective-lock and missing-verdict policy

Future benchmark runs use the following lifecycle: protocol/prompt/parser/analysis files
and their hashes are committed first; a run ID binds that lock before API execution; raw
responses are immutable; derived results and the registry are written afterward. Any
rule change creates a new protocol version and run ID.

Judge calls use `kit/scripts/judge.py`: at most six attempts with exponential backoff;
unparseable responses remain explicit. Paired headline comparisons use the joint
parseable denominator as the primary estimand and report best/worst bounds when failures
could affect interpretation. Table-specific departures must be stated beside the table.

The published 54-item validation sample is artifact-auditable but not reconstructible
from the paper alone: its candidate frame, seed/PRNG, strata, ambiguity rules, and label
timestamps live under `kit/judge_audit/` and `kit/annotation/`. Until those are consolidated
into one prospectively locked sampling protocol, treat this as auditability of the shipped
sample, not independent regeneration of sample selection.

`scripts/multi_system_rank.py` and `scripts/make_judge_ranking.py` are **superseded** and
not cited by the paper; their headers explain why (both pooled two runner paths under one
label, and the figure's caption carried a zep k=30 note that is false for these cells).
`scripts/rank_bootstrap.py` replaces the analysis and gates against the committed
aggregates; the paper reports the matrix in text and Table 3, with no rank figure.

Two scripts need inputs that are not in this repo and are documented as such:
`scripts/rank_bootstrap.py --core <path>` and `scripts/run_matrix_extra_judges.py
--extract-from <path>` re-derive their committed artifacts from a private
`mnemoverse-core` checkout. **Neither is needed to reproduce anything** — the extracted
artifacts (`kit/data/matrix_conv26_perq.json`, `kit/data/matrix_conv26_answers.json`)
ship here, and the analyses run from them. The paid re-judge path of `run_matrix_extra_judges.py` (`MX_*` verdicts,
`matrix_extra_judges.md`) was not run for the released paper and nothing in the paper depends on it;
only its `--extract-from` step was executed.

## Source-of-truth artifacts (all in `kit/data/`)

| Paper claim | Public kit artifact |
| --- | --- |
| Naked-cosine recall@k curve (§4) | `RECALL_AT_K_SUMMARY.json`; recomputable from `naked_cosine_conv26_retrieved.json` + `locomo_gold_ids.json` |
| Judge-prompt swing (control slice) (§3) | `answers_mem0_conv26.json`, `rejudge_q8_20260531T201308Z.json`; prompts in `kit/prompts/` |
| Our engine's 4-judge scores (§3) | `rejudge_20260521_235650.json` |
| Judge variance (§8) | `variance_study_20260603_2300.json` |
| Cross-conversation swing (full run) — Mem0's own published answers | `mem0_oss_answers/conv0.json`–`conv9.json` |
| Five-pipeline × four-judge matrix, per question (§3) | `matrix_conv26_perq.json` (verdicts) + `matrix_conv26_multijudge.json` (the released aggregates it is gated against) |
| Reader answers behind the matrix (§3) | `matrix_conv26_answers.json` — 6 × 152, canonical question order: the five harness pipelines **plus** `naked_cosine`, which the paper reports separately and outside the matrix (different runner path). Consumers comparing the five must exclude it. |
| Human labels: validation set, adjudications, campaign | `kit/judge_audit/`, `kit/annotation/` (labels, timestamps, analysis script) |

See [`kit/MANIFEST.md`](./kit/MANIFEST.md) for the full per-file provenance,
licensing, and what was deliberately left out (e.g. the raw LoCoMo dialogues —
third-party license; we ship only derived gold IDs).

## Figures

`scripts/make_*.py` emit the paper's figures into `figures/`:

The figure scripts are outside the kit and need matplotlib in addition to the kit requirements
(`pip install 'matplotlib>=3.8'`). Regenerating rewrites the committed `figures/*.pdf` and `.png`;
bytes differ across matplotlib versions, the content does not.

- `scripts/make_recall_curve.py` → `figures/recall_k_curve.pdf` (recall@k, §4).
- `scripts/make_crossconv_figure.py` → `figures/crossconv_swing.pdf` (per-conversation
  mem0→strict swing; reads `experiments/hardening/summary.json`, produced by
  `kit/scripts/run_experiments.py`).

## Build the PDF

```bash
cd paper/current && bash build.sh
```

`build.sh` runs the full pdflatex → bibtex → pdflatex → pdflatex cycle and is robust
to MiKTeX warnings; it writes `paper/current/main.pdf`. (No `make` required — a
`Makefile` exists for `make`-equipped machines, but `bash build.sh` is the portable
path, including Windows Git Bash.)
