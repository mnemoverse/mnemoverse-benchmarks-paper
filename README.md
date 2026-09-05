# The Judge Is the Benchmark

> The Same Answers Score 91% or 35%, Depending on the Grading Prompt

**Edward Izgorodin, Olga Timoshina, Andrey Ustyuzhanin** — arXiv: TBA · DOI: [10.5281/zenodo.22348527](https://doi.org/10.5281/zenodo.22348527) (release tag `arxiv-v1`)

This repository is the public reproduction kit for the methodology paper **"The Judge Is the
Benchmark."** A memory vendor published its complete LoCoMo benchmark run — 1,539 answers across
all ten conversations. We re-scored those *identical* answers under different LLM-judge grading
prompts and measured how far the headline number moves when nothing but the grading instruction
changes. Every load-bearing number traces to a committed artifact in this repository — the self-contained
[`kit/`](kit/), the full-run outputs under [`experiments/`](experiments/), and the recompute scripts
under [`scripts/`](scripts/): the judge-free
recall recomputes exactly offline, the control-slice swing re-judges in one command, and the
full-run per-answer verdicts ship alongside the paper. No private repository is needed.

## Headline results

- **91.0% vs 35.0% on identical answers.** The vendor's own distributed judge prompt scores its
  1,539 published answers at 91.0% (within 1.5 points of its 92.5% headline); a deliberately strict
  prompt of our own construction, on the same answers and the same gpt-5 backbone, scores 35.0%.
  The 56-point span is a constructed stress test, not a pair of truth bounds. The two prompts
  disagree on 863 answers, all in one direction (the lenient prompt credits what the strict one
  rejects, never the reverse), partly by construction: the strict rubric is near-nested inside the
  lenient one. Eight of the 863 are strict-side formatting pedantry; the remaining 855 were not
  hand-adjudicated, so the count is not a tally of verified over-credits. The swing is 48–61 points
  in every one of the ten conversations.
- **Calibrated judge: 85.3% — a provisional 5.7-point inflation estimate.** A judge calibrated on
  blind human adjudication by one author (also the lead annotator; disclosed) and validated out of
  sample on 54 held-back answers (43 of 44 decided cases; 94% against two independent raters)
  scores the same 1,534 jointly scored answers at 85.3%, 5.7 points below the field's prompt,
  positive in all ten conversations (floor +3.3). This is a provisional plug-in estimate, not a
  human-labeled full-run measurement: its interval excludes calibration uncertainty.
- **A third, independently sourced rubric lands at 81.7%.** The unmodified LongMemEval grading
  prompt, on its pinned `gpt-4o-2024-08-06` judge, scores the identical run at 81.7% — 9.4 points
  below the field's prompt on gpt-5 and 10.3 points below the same lenient prompt within the
  gpt-4o family (91.9%; differences taken before rounding). The 10.3 is a configuration contrast,
  not a rubric-only effect: one judge calls the mutable `gpt-4o` alias, the other a pinned
  snapshot. It corroborates the direction of the calibrated estimate, not its magnitude.
- **Prompt dominates model by an order of magnitude.** Holding the model fixed, the prompt moves
  the run-level score by **+56.1 pp** (gpt-5) / **+48.8 pp** (gpt-4o); holding the prompt fixed, the
  gpt-5−gpt-4o difference is only **−0.9 pp** (lenient) / **−8.2 pp** (strict).

## Reproduce in three commands

```bash
pip install -r kit/scripts/requirements.txt

python kit/scripts/recompute_recall.py           # judge-free recall@k (no API key)
python kit/scripts/recompute_judge_error.py       # judge-free judge-error table recompute (no API key)
OPENAI_API_KEY=sk-... python kit/scripts/verify_claims.py   # re-judges the control slice
```

The two recompute commands use no API key, hit no network, and finish in seconds — they reproduce
the judge-free numbers bit-for-bit (`recompute_judge_error.py` ends with `ALL TABLE-2 NUMBERS
REPRODUCE`; TABLE-2 is that table's original numbering, Table 4 in the paper). `verify_claims.py`
runs the same two judge-free checks and then adds the load-bearing judge swing: it re-judges the
143-answer conv-26 control slice under both prompts (2 × 143 = 286 gpt-5 judge calls before
retries) and checks that the ~40-point gap reproduces within the published tolerance (mem0 in
[0.70, 0.78], strict in [0.30, 0.38], swing in [34, 46] points; LLM judges are non-deterministic,
and a judged score moves ~0.5–0.7 pp between runs at this slice size, far below the effect).
Without a key it runs the judge-free checks and skips the swing.

## Artifact map

| Path | What it is |
| --- | --- |
| [`kit/`](kit/) | Self-contained public reproducibility kit: `scripts/` (judge runner, recomputes, verifier), `prompts/` (the two grading prompts + LongMemEval), `data/` (answers, gold IDs, committed verdicts), `docs/` (asymmetry inventory, provenance contract). See [`kit/README.md`](kit/README.md) and [`kit/MANIFEST.md`](kit/MANIFEST.md). |
| `experiments/` | Full-run outputs behind the headline: per-answer verdicts, the cross-conversation swing (`hardening/`), and the calibrated golden-judge run (`golden_judge/`). |
| `scripts/` | Figure regeneration (`make_recall_curve.py`, `make_crossconv_figure.py`; matplotlib needed) and provenance scripts (e.g. `count_disagreements.py`, `stats_ci.py`, `per_conv_calibrated.py`, `rank_bootstrap.py`, `run_model_vs_prompt_fullset.py`, `run_third_rubric_longmemeval.py`). `make_judge_ranking.py` and `multi_system_rank.py` are superseded and kept for provenance only; they do not run (see [REPRODUCING.md](REPRODUCING.md)). |
| `paper/` | The paper itself — `paper/current/main.tex`; build with `bash paper/current/build.sh` → `main.pdf`. |

See [`REPRODUCING.md`](REPRODUCING.md) for the per-claim source-of-truth table and
[`NAVIGATION.md`](NAVIGATION.md) for the full repo map.

## Licensing

The kit mixes licenses; [`kit/data/ATTRIBUTION.md`](kit/data/ATTRIBUTION.md) gives the file-by-file
detail. In summary:

- **LoCoMo-derived fields** (`question` / `gold` text and evidence IDs): **CC BY-NC 4.0**
  (attribution, non-commercial) — Maharana et al., ACL 2024,
  <https://github.com/snap-research/locomo>. Raw dialogues are *not* redistributed here.
- **Mem0's published answers** (`kit/data/mem0_oss_answers/`): **Apache-2.0**, from
  `mem0ai/memory-benchmarks@4b61c5d`. The ported `mem0` judge prompt carries the same license.
- **Our code, computed outputs, and judge verdicts** (recompute scripts, `RECALL_AT_K_SUMMARY.json`,
  `rejudge_*.json`, `variance_study_*.json`, `naked_cosine_conv26_retrieved.json`, our reader's
  answer text): **MIT**.
- **Paper text and figures**: **CC BY 4.0** (see [`LICENSE`](LICENSE)).

## Citation

```bibtex
@misc{izgorodin2026judge,
  title         = {The Judge Is the Benchmark: The Same Answers Score 91\% or 35\%,
                   Depending on the Grading Prompt},
  author        = {Izgorodin, Edward and Timoshina, Olga and Ustyuzhanin, Andrey},
  year          = {2026},
  eprint        = {TBA},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  note          = {Reproduction kit: https://github.com/mnemoverse/mnemoverse-benchmarks-paper.
                   Zenodo DOI: 10.5281/zenodo.22348527 (release tag arxiv-v1).}
}
```
