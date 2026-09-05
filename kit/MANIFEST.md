# Kit Manifest — provenance of every shipped artifact

This manifest records the provenance of every file shipped in the kit: where
each artifact came from and how to reproduce or inspect it.

---

## A. Copied verbatim (already in kit/)

| Private path (mnemoverse-core) | Public kit path | Notes |
|---|---|---|
| `experiments/results/rejudge_q8_20260531T201308Z.json` | `kit/data/rejudge_q8_20260531T201308Z.json` | Re-judge (mem0 + strict judges) of the 143 conv-26 control-slice answers (Mem0 v2 OSS backend retrieval + our reader — see `kit/data/ATTRIBUTION.md`). Embedded answer text and verdicts are our output (MIT); question/gold fields are LoCoMo CC BY-NC 4.0. |
| `experiments/results/rejudge_20260521_235650.json` | `kit/data/rejudge_20260521_235650.json` | Our engine answers, 4 judges. MIT. |
| `experiments/results/night-runs/RECALL_AT_K_SUMMARY.json` | `kit/data/RECALL_AT_K_SUMMARY.json` | Judge-free recall@k, all cells. MIT. |
| `experiments/results/night-runs/variance_study_20260603_2300.json` | `kit/data/variance_study_20260603_2300.json` | Variance study, 4 judges × 3 repeats. MIT. |
| `experiments/results/night-runs/cell_0b_naked_locomo_conv26_full.json` → extracted | `kit/data/naked_cosine_conv26_retrieved.json` | **Minimal extract** — per-question `{qid, retrieved_atom_ids}` only (top-200, 152 questions). No answer text, no judge scores. Enables standalone recall@k recomputation without the private repo. MIT. |

## B. Already in repo (referenced from kit, not duplicated)

| Path in mnemoverse-benchmarks-paper | Status |
|---|---|
| `kit/scripts/judge_error/judge_error_results.json` | Lives inside the kit; listed in the `kit/README.md` tree |
| `kit/scripts/judge_error/RESULTS.md` | Lives inside the kit; the paper's judge-error table (Table 4) |
| `kit/scripts/judge_error/compute_judge_error.py` | Lives inside the kit; its rule functions are imported verbatim by `kit/scripts/recompute_judge_error.py` and `scripts/differential_error_paired.py` |
| `scripts/count_disagreements.py` | Already committed; provenance for the 863-count one-directional disagreements claim (S3 footnote). Reads `experiments/hardening/verdicts/` (output of `run_experiments.py`) and `kit/data/mem0_oss_answers/`. |

## C. Judge prompts extracted (kit/prompts/)

| Source (judges.py symbol) | Public kit path | License | Notes |
|---|---|---|---|
| `_MEM0_SYSTEM` + `_MEM0_USER` | `kit/prompts/judge_mem0_generous.txt` | Apache-2.0 (ported from mem0ai/memory-benchmarks@4b61c5d) | Header comment attributes source + license |
| `_STRICT_SYSTEM` + `_STRICT_USER` | `kit/prompts/judge_strict_ours.txt` | MIT (Mnemoverse original) | Adversarial prompt for leniency quantification |
| `_MNEMO_SYSTEM` + `_MNEMO_USER` | `kit/prompts/judge_mnemoverse.txt` | MIT (Mnemoverse original) | ASYM-004 note included: dual-prompt issue disclosed |

## D. LoCoMo dataset — derived only, full not copied

| Original | Status | Public artifact |
|---|---|---|
| `experiments/data/locomo10.json` | NOT COPIED — third-party dataset (Maharana et al., snap-research/locomo) | `kit/data/locomo_gold_ids.json` — derived: evidence IDs + categories only (no question text, no answers). Category labels regenerated from integer codes in locomo10.json using the canonical map {1→multi_hop, 2→temporal, 3→open_domain, 4→single_hop, 5→adversarial}. |

## E. Self-contained scripts (new, no private-repo dependency)

These scripts live in the kit and require nothing outside this repository.

| Script | Location | What it does |
|---|---|---|
| `judge.py` | `kit/scripts/judge.py` | Self-contained LLM-judge runner. Reads prompts from `kit/prompts/`, calls OpenAI API. No internal imports. |
| `verify_claims.py` | `kit/scripts/verify_claims.py` | One-command headline reproduction. CHECK 1: reads committed RECALL_AT_K_SUMMARY.json. CHECK 1b: recomputes recall@k from scratch using `naked_cosine_conv26_retrieved.json` + `locomo_gold_ids.json`. CHECK 2: re-runs the judge swing (requires OPENAI_API_KEY). |
| `recompute_recall.py` | `kit/scripts/recompute_recall.py` | Standalone bit-for-bit recall@k recompute from `naked_cosine_conv26_retrieved.json` + `locomo_gold_ids.json`. No LLM, no API key needed. |
| `run_experiments.py` | `kit/scripts/run_experiments.py` | Runs the two hardening experiments (A: judge variance; B: cross-conversation swing on Mem0's own 10-conv answers). Requires OPENAI_API_KEY. |
| `compute_recall.py` | `kit/scripts/compute_recall.py` | *(Reference copy from mnemoverse-core harness.)* Full recall@k harness with normalized-cell update logic; has internal imports that won't resolve outside the private repo. For standalone use, use `recompute_recall.py` instead. |
| `anti_cheat_audit.py` | `kit/scripts/anti_cheat_audit.py` | *(Reference copy from mnemoverse-core.)* Gold-label leakage scanner; portable detection patterns, but path defaults to src/mnemo/ in the original repo. |
| `requirements.txt` | `kit/scripts/requirements.txt` | `openai>=1.40, python-dotenv>=1.0` — covers all judge-running scripts. |

## F. Five-pipeline conv-26 matrix (rank-stability analysis, §3)

Extracted 2026-07-15 from the private core sweep behind the released matrix cells
(git object `e19f030`, branch `preserve/conv26-baseline-e19f030`,
`experiments/results/matrix-2026-06-07/`; `naked_cosine` from
`experiments/results/night-runs/cell_0e_naked_locomo_conv26_k50.json`, the file the
released naked cell names as its `raw_data_url`). Recomputed cell accuracies match the
released aggregates to six decimals; row order is canonical question order, verified
152/152 against the locomo10 question texts.

| Upstream path | Public kit path | License | Notes |
|---|---|---|---|
| `experiments/benchmarks/matrix/cells/cell_*_locomo_conv26_n152_k50.json` @ core | `kit/data/matrix_conv26_multijudge.json` | MIT | The released per-cell aggregates (six pipelines × four judges × k∈{10..200}). Used as the fail-closed gate for the per-question extraction. |
| `matrix-2026-06-07/cell_*_locomo_conv26_n199_k50.json` @ `e19f030` (+ night-runs cell_0e) | `kit/data/matrix_conv26_perq.json` | MIT | Per-question verdicts, six pipelines × 152 questions × four judges. The five harness pipelines share identical `judge_prompt_hashes`, so all four judge columns are one instrument across them; `naked_cosine` ran on the other runner path (binary-text `mnemoverse` prompt, core ASYM-004) and is reported outside the matrix. Consumed by `scripts/rank_bootstrap.py`. |
| same | `kit/data/matrix_conv26_answers.json` | MIT (answer text = our reader output) + CC BY-NC 4.0 (LoCoMo question/gold fields) | The six pipelines' reader answers, 152 each, canonical order, with gold and category. Lets any judge be re-run over the same fixed answers (`scripts/run_matrix_extra_judges.py`). |

## G. Mem0 OSS published answers (cross-conversation hardening) + control slice

| Upstream path | Public kit path | License | Notes |
|---|---|---|---|
| `results/platform/locomo_results.json` @ mem0ai/memory-benchmarks@4b61c5d | `kit/data/mem0_oss_answers/conv0.json`–`conv9.json` | Apache-2.0 | Mem0 Platform's generated answers (gpt-5/azure, top_200 cutoff) for all 10 LoCoMo conversations. 1,539 answers total. conv0 = paper's "conv-26". Schema: `{qid, question, gold, answer, category}`. |
| — | `kit/data/answers_mem0_conv26.json` | MIT (answer text = our reader output) + CC BY-NC 4.0 (LoCoMo question/gold fields) | Control-slice answers (Mem0 v2 OSS backend retrieval + our reader) — see ATTRIBUTION.md. 143 scored records, standard `{qid, question, gold, answer, category}` schema. This is the load-bearing set for CHECK 2 in `verify_claims.py`. |
| — | `kit/data/mem0_oss_answers/SOURCE.md` | — | Attribution and schema documentation for the 10-conversation set. |

## H. Internal methodology docs (distilled into kit/docs/)

The following internal documents from `mnemoverse-core/experiments/benchmarks/`
were the upstream source material for the public methodology docs in `kit/docs/`.
They are not reproduced here; the public `kit/docs/` versions are the citable
artifacts shipped with this repository.

| Internal file | Public kit/docs/ equivalent |
|---|---|
| `experiments/benchmarks/ASYMMETRY_INVENTORY.md` | `kit/docs/asymmetry_inventory.md` |
| `experiments/benchmarks/BENCHMARK_PROVENANCE.md` | `kit/docs/provenance.md` |
| `experiments/benchmarks/competitors/COMPETITOR_CLAIMS_TRACKER.md` | `kit/docs/competitor_claims.md` |
| `experiments/benchmarks/beam/BEAM_PROTOCOL.md` | `kit/docs/beam_integrity.md` |

## I. BEAM-10M controlled re-score (§7, scale prompt-swing)

| Upstream source | Public kit path | License | Notes |
|---|---|---|---|
| HuggingFace dataset `Mohammadta/BEAM-10M`, split `10M` (Tavakoli et al. 2025, arXiv:2510.27246), loaded through the private harness's BEAM adapter | `kit/data/beam_answers_10m.json` | `question` and `gold` (the rubric nuggets joined with "; "): **CC BY-SA 4.0** (the dataset card's license); `answer`: our engine's output, MIT | 200 records `{qid, question, gold, answer, category, conv_idx}`; read by `scripts/run_beam_rescore.py`; verdicts in `experiments/hardening/verdicts/BEAM_*` and the summary in `experiments/hardening/beam_rescore.md`. The BEAM source conversations (~656 MB) are not redistributed. |
