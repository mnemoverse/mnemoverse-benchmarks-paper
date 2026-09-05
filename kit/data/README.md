# kit/data — what's here

## Files

| File | Description | Source |
|------|-------------|--------|
| `answers_mem0_conv26.json` | Control-slice answers for conv-26 (Mem0 v2 OSS backend retrieval + our reader — see `ATTRIBUTION.md`): 143 scored records with `{qid, question, gold, answer, category}` schema. The load-bearing answer set for `verify_claims.py` CHECK 2 (judge-swing reproduction). | Control run: mem0ai backend @4b61c5d (Apache-2.0 code) + our reader (answer text = our output, MIT); question/gold = LoCoMo CC BY-NC 4.0 |
| `mem0_oss_answers/conv0.json`–`conv9.json` | Mem0 Platform's generated answers (gpt-5/azure, top_200 cutoff) for all 10 LoCoMo conversations. 1,539 answers total; conv0 = paper's "conv-26". Used by `run_experiments.py` part B (cross-conversation swing). | mem0ai/memory-benchmarks@4b61c5d (Apache-2.0) |
| `mem0_oss_answers/SOURCE.md` | Attribution and schema documentation for the 10-conversation answer set. | — |
| `rejudge_q8_20260531T201308Z.json` | Per-question judge verdicts (mem0 + strict) on the conv-26 control-slice answers (Mem0 v2 OSS backend retrieval + our reader). 152 questions, 143 scored (9 skipped: null/empty answers). | Mnemoverse harness run 2026-05-31 |
| `rejudge_20260521_235650.json` | Per-judge score arrays for our engine's answers on conv-26, 4 judges (mem0, mem0-4o, strict, mnemoverse). | Mnemoverse harness run 2026-05-21 |
| `RECALL_AT_K_SUMMARY.json` | Judge-free recall@k results across all benchmark cells. Primary metric for the paper's #1 claim. Checked by `verify_claims.py` CHECK 1. | Mnemoverse night-runs 2026-06 |
| `variance_study_20260603_2300.json` | 3-repeat variance study on 20 questions × 4 judges for conv-26 (seeds 42/43/44). Quantifies judge stochasticity. | Mnemoverse harness run 2026-06-03 |
| `locomo_gold_ids.json` | **Derived file** — gold evidence IDs and category labels for all 10 LoCoMo conversations. See note below. | Derived from Maharana et al. 2024 |
| `naked_cosine_conv26_retrieved.json` | **Minimal extract** — per-question `{qid, retrieved_atom_ids}` (top-200) for naked-cosine on LoCoMo conv-26 (152 questions). Enables standalone recall@k recomputation. See note below. | Extracted from mnemoverse-core (MIT) |
| `answers_engine_conv26.json` | Our engine's 152 conv-26 answers `{records: [{qid, question, gold, answer, category}]}`, index-aligned with `rejudge_20260521_235650.json`; read by `kit/scripts/recompute_judge_error.py`. `answer` MIT; `question`/`gold` LoCoMo CC BY-NC 4.0 (see `ATTRIBUTION.md`). | Mnemoverse run 2026-05-21 |
| `beam_answers_10m.json` | 200 BEAM-10M probing questions with the rubric nuggets joined as `gold`, plus our engine's answers; read by `scripts/run_beam_rescore.py` (paper §7). `question`/`gold` CC BY-SA 4.0 (BEAM, Tavakoli et al. 2025); `answer` MIT. | HF dataset `Mohammadta/BEAM-10M`, split 10M; Mnemoverse BEAM run |
| `matrix_conv26_answers.json` | Six answer sets (five harness pipelines + naked cosine) × 152 conv-26 questions, canonical order; the fixed answers behind the matrix. Mixed license (LoCoMo fields CC BY-NC 4.0). | Mnemoverse harness sweep (see `kit/MANIFEST.md` §F) |
| `matrix_conv26_multijudge.json` | Released aggregates of the five-pipeline × four-judge matrix (what `scripts/rank_bootstrap.py` gates against). | Mnemoverse harness sweep |
| `matrix_conv26_perq.json` | Per-question verdicts of that matrix (input of the rank bootstrap, paper Table 3). | Mnemoverse harness sweep |
| `ATTRIBUTION.md` | License and attribution for all files in this directory. | — |

## Note on locomo_gold_ids.json

`locomo_gold_ids.json` is a minimal derivative of the LoCoMo benchmark dataset
(Maharana et al., ACL 2024). It contains **only** the per-question fields needed
to recompute recall@k without the judge:

- `sample_id` — which conversation (e.g. "conv-26")
- `q_idx` — question index within that conversation
- `evidence` — list of dialogue-turn IDs (e.g. `["D1:3", "D2:12"]`) that are
  the gold evidence for that question
- `category` — question category (`single_hop`, `temporal`, `multi_hop`,
  `open_domain`, `adversarial`)

It does **not** include question text, gold answers, or conversation content.
To run with the full dataset, download it from:
https://github.com/snap-research/locomo

Category labels are derived from the integer category codes in locomo10.json
using the canonical map: `{1→multi_hop, 2→temporal, 3→open_domain, 4→single_hop,
5→adversarial}`.

## Note on naked_cosine_conv26_retrieved.json

This file contains per-question ranked retrieval results for the naked-cosine
system on LoCoMo conv-26, extracted (read-only) from the private mnemoverse-core
experiment cell `cell_0b_naked_locomo_conv26_full.json`. It stores only:

- `qid` — question ID (e.g. `"conv-26::q0"`)
- `retrieved_atom_ids` — ranked list of top-200 retrieved dialogue-turn IDs

No answer text, no reader output, no judge scores.

Together with `locomo_gold_ids.json`, this file enables **fully standalone**
bit-for-bit recomputation of the paper's published recall@k numbers:

```bash
python kit/scripts/recompute_recall.py
```

The provenance block in the file (`_provenance`) records the source cell,
system name, embed model, and private-repo path for auditability.

## Note on mem0_oss_answers/

These files contain Mem0 Platform's **published answers** for all 10 LoCoMo
conversations, extracted from `mem0ai/memory-benchmarks` (Apache-2.0, commit
`4b61c5d`). Each JSON file is a list of `{qid, question, gold, answer, category}`
records (1,539 total across 10 conversations). See `mem0_oss_answers/SOURCE.md`
for full provenance, schema details, and the per-conversation question counts.

`conv0.json` corresponds to conv-26 in the paper (conv_idx=0 in the upstream file).
`answers_mem0_conv26.json` is a different, smaller set — the 143-record control
slice (Mem0 OSS backend retrieval + our reader, ~74% under the lenient judge),
not Mem0's published answers.

## Judge error outputs

Judge-error outputs live in `kit/scripts/judge_error/` (`RESULTS.md`, `judge_error_results.json`,
and the reference implementation `compute_judge_error.py`); the offline recompute is
`kit/scripts/recompute_judge_error.py`. See `kit/MANIFEST.md` for the full path map.
