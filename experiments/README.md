# experiments/

Full-run outputs behind the paper's headline numbers. Everything here is a committed result; the
scripts that produced it are named per row, and `REPRODUCING.md` says which rows are certified
offline-exact.

## hardening/verdicts/ — per-answer judge verdicts, by file prefix

| Prefix | Experiment | Answers judged | Produced by | Summary |
|---|---|---|---|---|
| `A_{mem0,strict}_rep{0,1,2}` | Judge variance: three repeats per prompt | 143 control-slice answers (conv-26; Mem0 OSS retrieval, our reader) | `kit/scripts/run_experiments.py` | `hardening/summary.json` (`A_variance`), `hardening/noise_band.md` |
| `B_conv{0..9}_{mem0,strict}` | Cross-conversation swing: lenient vs strict prompt, gpt-5 | Mem0's full published run, 1,539 answers | `kit/scripts/run_experiments.py` | `hardening/summary.json` (`B_cross_conversation`), `hardening/per_category_swing.json`, `hardening/disagreement_exhibits.{json,md}` (863 cases; count by `scripts/count_disagreements.py`) |
| `MV_conv{0..9}_{mem0-4o,strict-4o}` | Model-vs-prompt decomposition on a gpt-4o backbone | same 1,539 answers | `scripts/run_model_vs_prompt_fullset.py` | `hardening/model_vs_prompt_fullset.{json,md}` |
| `LME_conv{0..9}` | Third rubric: verbatim LongMemEval judge (gpt-4o-2024-08-06, default + temporal routing) | same 1,539 answers | `scripts/run_third_rubric_longmemeval.py` | `hardening/third_rubric_longmemeval.{json,md}` |
| `ABL_conv{0..9}_abl-no-{partial,paraphrase,datetol,extradetail}` | Single-rule ablations of the lenient prompt | same 1,539 answers | `scripts/run_extra_judges.py` | `hardening/ablation.{json,md}`, `hardening/ablation_unparseable_bounds.md` |
| `XB_conv{0..9}_{mem0,strict}-claude` | Third judge backbone (Claude) under both prompts | same 1,539 answers | `scripts/run_extra_judges.py` | `hardening/third_backbone.{json,md}` |
| `BEAM_{mem0,strict}` | BEAM-10M controlled re-score: same answers, two prompts | 200 BEAM-10M answers (`kit/data/beam_answers_10m.json`) | `scripts/run_beam_rescore.py` | `hardening/beam_rescore.{json,md}` |

Other files in `hardening/`: `stats_ci.md` (bootstrap intervals for the 5.7 and 10.3 contrasts;
`scripts/stats_ci.py`), `rank_bootstrap.md` (five-pipeline matrix, rank-flip uncertainty;
`scripts/rank_bootstrap.py`), `differential_error_paired.md` (question-clustered leniency test;
`scripts/differential_error_paired.py`), `validation_54_all_judges.md` and `golden_vs_externals.md`
(every grader against every human standard on the 54 validation answers;
`scripts/validation_54_all_judges.py`), `multi_system_rank.md` (superseded, not cited; kept for provenance).

## golden_judge/ — the human-calibrated judge

| File | What it is |
|---|---|
| `run_golden.py` | Runs a judge over the 143 control-slice answers and scores it against the 57 blind human adjudications in `kit/judge_audit/human_labels_control_slice.json` (calibration loop for the golden prompts). |
| `run_golden_fullrun.py` | Runs the calibrated judge (`golden`, prompt `kit/prompts/judge_golden_v2.txt`) over Mem0's full published run. |
| `fullrun_verdicts/` | Its per-conversation verdicts. |
| `FULLRUN_GOLDEN_RESULTS.json` | Aggregate of that run: 85.3% against the lenient prompt's 91.0% on the 1,534 jointly scored answers, per-conversation inflation, its range and mean. |
| `verdicts_golden_20260702T195250Z.json`, `verdicts_golden_20260702T195458Z.json` | Calibration runs of the first golden prompt (v1) on the control slice. |
| `verdicts_golden2_20260702T195900Z.json` | Calibration run of the prompt the paper uses (v2) on the control slice. |
| `verdicts_golden2_engine_conv26.json` | Golden v2 over our engine's 152 conv-26 answers. |
| `validation_set_answers.json`, `verdicts_golden2_validation_set.json`, `VALIDATION_RESULTS.json` | The 54-answer out-of-sample validation set, golden v2's verdicts on it, and the agreement with the blind human labels (43 of 44 decided cases). |
| `mem0_audit_sample.json` | 90 Mem0 answers (question, gold, answer, category) sampled for manual inspection during calibration; not a scored artifact. |
