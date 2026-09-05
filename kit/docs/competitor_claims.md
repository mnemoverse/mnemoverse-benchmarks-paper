# Competitor Claims — Public Provenance

The paper cites two findings about Mem0's published benchmark numbers.
This note records the public sources for each.

## Finding 1 — Two different published BEAM-10M average-score values: 48.6 and 45.0

Mem0's public surfaces show two different average scores for BEAM-10M
(200 questions, 10 conversations at 10M-token scale):

- **48.6** (average score × 100) — reported in the April 2026 blog post:
  https://mem0.ai/blog/ai-memory-benchmarks-in-2026 (published 2026-04-16)

- **45.0** (average score × 100) — reported on the research page updated in
  May 2026:
  https://mem0.ai/research (accessed 2026-06-01)

Both values appeared on the same vendor's pages, with the aggregation method
(judge, prompt, reader configuration) unspecified in both places. Without
dated archival snapshots of each surface we do not claim a temporal
regression — we cannot establish which configuration produced which number.
The April blog post also reports a pass-rate of 50.5% (questions scoring
≥ 0.5) alongside the 48.6 average score; the narrative accompanying the May
update discusses improvements on LoCoMo and LongMemEval and does not mention
or annotate the differing BEAM value.

Both numbers are self-reported by Mem0. The paper cites the April number
(48.6) as the primary reference because it corresponds to the same blog post
that introduced the BEAM numbers publicly and is the version other
independent analyses have cited; the differing May value (45.0) is disclosed
for full context. The point is not a score change over time — it is that an
un-pinned configuration lets two different numbers for the same benchmark
coexist with no way to reconcile them.

## Finding 2 — a "~84%" LoCoMo self-claim vs a 66.0% independent re-evaluation, same system (Zep)

Three different LoCoMo accuracy numbers circulate for the **same** system, Zep:

- **~84%** — a self-claim that appears in circulated materials but is **not
  traceable** to Zep's own paper or to any published harness with a
  held-constant judge. Zep's paper (Rasmussen et al., arXiv:2501.13956)
  reports Zep on the **DMR** benchmark at 94.8% (vs MemGPT 93.4%), not a
  LoCoMo figure of ~84%. The ~84% LoCoMo number has no locatable primary
  source.
- **66.0%** — an **independent** re-evaluation of Zep, reported in the Mem0
  paper:

  > Chhikara et al., *Mem0: Building Production-Ready AI Agents with Scalable
  > Long-Term Memory*, arXiv:2504.19413, Table 2 (Zep row, LoCoMo Score
  > column): **66.0%** (gpt-4o reader, gpt-4o judge, Mem0's harness).

The ~18-point gap between the untraceable self-claim (~84%) and the
independent measurement (66.0%) is on the **same** system, and is exactly the
leniency / protocol-mismatch range the paper measures directly elsewhere. The
point is not that either number is "right": it is that the most-circulated
figure has no published, reproducible source, while the one number with a
traceable harness and a named judge sits ~18 points lower. (A third figure,
75.1%, comes from a separate third-party "Backboard" harness — underscoring
that a bare "Zep on LoCoMo" citation is unusable without specifying which
harness and judge produced it.)

## Finding 3 — Mem0's own LoCoMo headline: 92.5% (gpt-5 judge)

The paper compares the full-run lenient re-score (91.0%, n-weighted over all ten
LoCoMo conversations) against **92.5%**, Mem0's own published LoCoMo accuracy under
its gpt-5 judge.

- **92.5%** is recorded verbatim in the kit's ported prompt header,
  `kit/prompts/judge_mem0_generous.txt` line 6 ("comparable with Mem0's published
  92.5% on LoCoMo (gpt-5 judge)"), taken from `mem0ai/memory-benchmarks` @ `4b61c5d`
  (Apache-2.0). It is Mem0's gpt-5-judge figure — the same judge configuration whose
  published answers the kit re-scores.
- The kit reproduces it at **91.0%** (n-weighted mean of the ten per-conversation
  cells, `experiments/hardening/summary.json` → `B_cross_conversation`), i.e. within
  ~1.5 points — the point being that our "lenient" judge **is** the field's judge,
  not a softball of our own.

Note: 92.5% is Mem0's *gpt-5-judge* LoCoMo headline, distinct from the 66.0 / ~84 /
75.1 figures in Finding 2, which are all **Zep** (different system, different judge).

**Primary source:** the official README of `mem0ai/memory-benchmarks`, which reports
**92.5% (1425/1540)** overall at the Top-200 cutoff for the LoCoMo run whose per-answer
outputs this kit re-scores. Independently confirmed against the live README on
2026-07-04 by two external validation reviews. Re-checked against the live README on 2026-09-04 and 2026-09-05: the table still
reports **92.5** on LoCoMo; the surrounding sentence now reads "92.5 on LoCoMo -- +21 points
over the previous algorithm" (earlier wording: "+26% over OpenAI Memory"). The figure the kit
relies on is unchanged. The quoted wording above is the dated record; the release tag `arxiv-v1` pins this file.
