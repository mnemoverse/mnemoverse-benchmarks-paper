# Reproducibility Kit — *The Judge Is the Benchmark*

This kit is **self-contained**: it depends on no internal repository. With Python,
`pip install -r kit/scripts/requirements.txt`, and an `OPENAI_API_KEY`, you can
reproduce the paper's judge-free numbers exactly and the control-slice swing within tolerance (the full-run verdicts ship as committed artifacts in experiments/hardening/).

The whole thesis in one sentence: **the answers are fixed; only the grading prompt
changes — and the score moves ~40 points.** This kit lets you watch that happen.

## Quick start — one-command verification

```bash
pip install -r kit/scripts/requirements.txt
export OPENAI_API_KEY=sk-...
python kit/scripts/verify_claims.py
```

`verify_claims.py` runs three checks and exits non-zero if any fail:

1. **Judge-free recall@k, committed summary** (exact) — the naked-cosine recall numbers are read
   from `data/RECALL_AT_K_SUMMARY.json`; no LLM.
1b. **Judge-free recall@k, standalone recompute** (exact, no LLM) — the same numbers re-derived
   from `data/naked_cosine_conv26_retrieved.json` + `data/locomo_gold_ids.json`, the logic of
   `recompute_recall.py`; must match the summary bit-for-bit.
2. **The load-bearing swing** (within tolerance) — re-judges the 143 conv-26 control-slice
   answers (Mem0 OSS backend retrieval, our reader — see `data/ATTRIBUTION.md`) under the
   two prompts in `kit/prompts/`. Expect `mem0`≈0.74, `strict`≈0.34, a ~40-point gap
   (tolerance: mem0 in [0.70, 0.78], strict in [0.30, 0.38], swing in [34, 46] points). The
   tolerance absorbs LLM-judge non-determinism: a judged score moves ~0.5–0.7 pp between runs
   at this slice size, far below the 40 pp effect. Without `OPENAI_API_KEY` the script runs
   checks 1 and 1b and skips check 2 (exit code 2).

The judge-error table (Table 4 in the paper) has its own offline recompute,
`recompute_judge_error.py` (no API key); see `REPRODUCING.md`.

## Run any judge on any answer set

```bash
python kit/scripts/judge.py \
  --answers kit/data/answers_mem0_conv26.json \
  --judge mem0 --judge strict \
  --out out/verdicts.json
```

`--answers` is a list of `{qid, question, gold, answer}` records (answer = the system's
output, gold = the LoCoMo reference). `--judge` may be any of `mem0`, `strict`, `mnemoverse`, `mem0-4o`, `strict-4o`, `lme`, `lme-temporal`, `abl-no-partial`, `abl-no-paraphrase`, `abl-no-datetol`, `abl-no-extradetail`, `mem0-claude`, `strict-claude`, `golden` (see the table at the top of `judge.py` for the prompt file and model behind each id). Output records carry
`label`, `score`, and the judge's `reasoning`.

## Reproduce the hardening experiments

```bash
python kit/scripts/run_experiments.py --repeats 3
```

- **(A) Judge variance on the control slice** — re-judges the 143 conv-26 control-slice
  answers three times under `mem0`+`strict`: the swing is stable across repeats and the
  within-judge stdev is small.
- **(B) Cross-conversation swing on the vendor's own answers** — re-judges Mem0's OWN
  published answers for all ten LoCoMo conversations (`kit/data/mem0_oss_answers/`): the
  ~40-point swing is not specific to conv-26.

Outputs (verdicts with reasoning + a summary) land in `experiments/hardening/`.

## Standalone recall recompute (no API key needed)

```bash
python kit/scripts/recompute_recall.py
```

Reads two files that ship in this repo — no private repository, no LLM:

- `kit/data/naked_cosine_conv26_retrieved.json` — per-question top-200 retrieved IDs
  for the naked-cosine system on LoCoMo conv-26 (152 questions, extracted from the
  private experiment cell read-only).
- `kit/data/locomo_gold_ids.json` — gold evidence IDs and category labels for all
  10 LoCoMo conversations (derived; no question text, no answers).

Expected output: exact bit-for-bit match at k=5/10/20/50/100/200 against the paper's
published recall values (0.595/0.721/0.780/0.886/0.938/0.981).

`verify_claims.py` runs this recompute automatically as CHECK 1b before the judge checks.

## What's in the kit

```
kit/
  MANIFEST.md                        ← provenance map for every artifact
  README.md                          ← this file
  scripts/
    anti_cheat_audit.py                ← reference copy of gold-label leakage scanner
    compute_recall.py                  ← reference copy from harness (has private-repo imports)
    judge.py                           ← self-contained LLM-judge runner (the lever)
    judge_error/RESULTS.md             ← FP/FN judge-error analysis (paper Table 4)
    judge_error/compute_judge_error.py ← reference implementation of the proxy rule
    judge_error/judge_error_results.json ← its committed output
    recompute_judge_error.py           ← standalone judge-error table recompute (no API key)
    recompute_recall.py                ← standalone bit-for-bit recall@k recompute (no API key)
    requirements.txt                   ← openai + python-dotenv
    run_experiments.py                 ← the hardening experiments (variance, cross-conversation swing)
    verify_claims.py                   ← one-command reproduction (checks 1, 1b, 2)
  prompts/
    judge_abl_no_datetol.txt           ← lenient prompt with the date-tolerance rule tightened
    judge_abl_no_extradetail.txt       ← lenient prompt with the extra-detail rule tightened
    judge_abl_no_paraphrase.txt        ← lenient prompt with the paraphrase rule tightened
    judge_abl_no_partial.txt           ← lenient prompt with the partial-credit rule tightened
    judge_golden_v1.txt                ← human-calibrated judge, first version
    judge_golden_v2.txt                ← human-calibrated judge, the version the paper uses
    judge_longmemeval_default.txt      ← verbatim LongMemEval rubric (default categories)
    judge_longmemeval_temporal.txt     ← verbatim LongMemEval rubric (temporal categories)
    judge_mem0_generous.txt            ← the field's de-facto lenient prompt (Apache-2.0, mem0ai)
    judge_mnemoverse.txt               ← our default binary prompt
    judge_strict_ours.txt              ← our strict/adversarial prompt
  data/
    ATTRIBUTION.md                     ← licensing for every file
    README.md                          ← per-file descriptions and provenance notes
    RECALL_AT_K_SUMMARY.json           ← judge-free recall@k, all cells (committed summary)
    answers_engine_conv26.json         ← our engine's 152 conv-26 answers (judge-error table)
    answers_mem0_conv26.json           ← the 143 conv-26 control-slice answers (Mem0 OSS retrieval + our reader; check 2)
    beam_answers_10m.json              ← BEAM-10M questions, rubric text and our answers (200; CC BY-SA 4.0 fields)
    locomo_gold_ids.json               ← gold evidence ids + category labels, all 10 convs (no dialogue text)
    matrix_conv26_answers.json         ← six answer sets behind the five-pipeline matrix
    matrix_conv26_multijudge.json      ← released matrix aggregates (five pipelines × four judges)
    matrix_conv26_perq.json            ← per-question matrix verdicts (rank bootstrap)
    mem0_oss_answers/SOURCE.md         ← attribution + schema of Mem0's published answers
    mem0_oss_answers/conv0-9.json      ← Mem0's OWN published answers, all 10 LoCoMo convs (Apache-2.0, mem0ai/memory-benchmarks @4b61c5d)
    naked_cosine_conv26_retrieved.json ← per-question top-200 retrieved ids (standalone recall recompute)
    rejudge_20260521_235650.json       ← our engine's answers, 4-judge score arrays
    rejudge_q8_20260531T201308Z.json   ← committed mem0+strict verdicts on the control slice
    variance_study_20260603_2300.json  ← judge variance (3 repeats × 4 judges)
  docs/
    PROVENANCE_NOTES.md                ← the P1–P9 register the paper's footnotes cite
    asymmetry_inventory.md             ← full disclosure of the evaluation asymmetries
    beam_integrity.md                  ← BEAM integrity rules (μ=0, anti-cheat, reader budget)
    competitor_claims.md               ← public-sourced competitor-number provenance
    provenance.md                      ← the four-artifact provenance contract
  judge_audit/
    human_labels_control_slice.json    ← the author's blind labels, 57 control-slice disagreements
    human_labels_engine_side.json      ← the author's blind labels, engine-side disagreements
    human_labels_validation_set.json   ← the author's labels on the 54-answer validation set
    label_sheet.csv                    ← the label sheet used for adjudication
  annotation/
    README.md                          ← the two-annotator relabeling campaign
    analyze_kappa.py                   ← pre-registered agreement analysis
    annotator_key_mapping.json         ← unblinding key (public since the campaign closed)
    build_external_package.py          ← generator of the tool and key (maintainer-only inputs)
    label-annotator.html               ← the tool the annotators received (180 masked cases)
    returned/cases_NS_labels.json      ← returned labels, annotator NS
    returned/cases_OI_labels.json      ← returned labels, annotator OI
    submit-worker/worker.js            ← optional submission worker
    submit-worker/wrangler.toml        ← its config
```

We do **not** redistribute the raw LoCoMo dialogues (third-party license). For the full
dataset see <https://github.com/snap-research/locomo>; the per-question
(question, gold, answer) tuples needed to re-judge are included here under their
respective licenses (see `data/ATTRIBUTION.md`).
