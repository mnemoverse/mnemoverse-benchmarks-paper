# Multi-annotator relabeling campaign (inter-annotator agreement)

**Status: campaign complete.** Two raters returned full 180-case streams
(`returned/cases_OI_labels.json`, exported 2026-07-05; `returned/cases_NS_labels.json`,
exported 2026-07-14); both passed all five attention checks. Results:
`experiments/hardening/golden_vs_externals.md`, `experiments/hardening/validation_54_all_judges.md`,
and the paper's threats section. With the campaign over, the unblinding key is public, as the
pre-registered plan foresaw; the "never sent to annotators" wording below records the rule that
applied while it ran.

The paper's primary human labels were produced by a single annotator who is also the
lead author (disclosed in the paper). This directory is the campaign that addressed it: two
further hypothesis-blind annotators relabeled all adjudicated and validation cases; agreement is
reported with a pre-registered analysis plan.

## Files

| File | What it is |
|---|---|
| `label-annotator.html` | The exact tool annotators receive: ONE shuffled stream of 180 masked cases (q001–q180), ack-gated instructions screen (v2), per-verdict `first_ts`/`ts` timestamps, offline, localStorage autosave. |
| `annotator_key_mapping.json` | **Unblinding key** — masked id → source set/qid + catch flags. Withheld from annotators for the whole campaign; public since it closed. |
| `build_external_package.py` | Reproducible generator (seed=42). Its inputs (the author's session-labeling tools) are not in this repository; rebuilding is a maintainer operation (`BENCH_LABELING_DIR`). |
| `analyze_kappa.py` | The analysis. Its docstring is the **pre-registered plan** (fixed before any labels arrived; the pre-release commit that timestamps it lives in the maintainers' private history archive, since the public history starts at the release): primary = Fleiss' κ on the validation subset; Landis–Koch labels attached to the bootstrap-CI lower bound; catch-gate-only exclusion; the paper's "97 of 121" moves to the 3-rater majority. Also: Gwet's AC1 for the skewed subsets, timing forensics, per-annotator "X of 121" reconstruction. |
| `returned/` | Annotator submissions (`cases_<CODE>_labels.json`), codes `OI` and `NS`; the paper reports them as raters O.T. and A.S. |
| `submit-worker/` | Optional Cloudflare Worker for one-click submission from the tool (deploy gated). |

## Stream composition

54 out-of-sample validation cases + 5 attention catches + 57 control-slice
adjudication cases + 64 engine-side adjudication cases, shuffled into one
neutral stream so that set sizes and ordering reveal nothing.

## Protocol invariants

- The grading rule shown to annotators is character-identical to the one the
  author labeled under; instructions v2 adds only a neutral purpose frame
  ("an assistant will act on this answer"), the 2023 timeline of the
  conversations, and the gold-answer-is-the-only-truth-standard clarification.
- Annotators are blind to machine verdicts, to set provenance, and to which
  system produced which answer; there is no vendor or hypothesis language
  anywhere in the shipped tool (leak-checked at build time, fail-closed).
- Exclusion of an annotator is possible only via the catch gate (≥2 of 5),
  decided before any agreement statistic is seen.
- Results are published whatever they are.

Run: `python analyze_kappa.py returned/cases_*.json`
