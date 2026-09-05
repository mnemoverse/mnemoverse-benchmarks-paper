# Disclosed Asymmetries — cross-system comparison inventory

This paper proposes a measurement contract for memory-system benchmarks.
One element of that contract is **disclosed asymmetries**: any place where
the two sides of a comparison are not measured under identical conditions
should be named, with the direction it tilts the result stated plainly. We
hold ourselves to that element here.

Below is the full set of asymmetries we found in our own cross-system
comparisons (Mnemoverse vs. external memory systems on a conversational-QA
benchmark) and the direction each one tilts. Each is described in terms of
the **experiment** — the retrieval path, the prompt, the question set, the
judge, the timing — not in terms of any system's internals. We do not drop,
merge, or soften the ones that favour us; the honesty value of this table is
precisely that we admit them.

Direction tags:

- **FAVORS_MNEMOVERSE** — tilts the result toward our system (inflates our
  score or depresses a competitor's relative to a fair comparison).
- **FAVORS_COMPETITOR** — tilts the result toward a competitor / against us.
- **BOTH** — two-sided or net-direction genuinely ambiguous.
- **UNKNOWN** — direction not determined.

Some asymmetries were closed in later harness work; where so, the "Status"
column says **closed** (it still tilts any historical cell produced before the
fix) and the direction column records the direction it *had*. Active items
are marked **active**.

The `ASYM-NNN` ids are opaque labels carried over from our internal tracking,
kept so individual findings can be cited stably.

## Inventory

| id | Asymmetry (plain language) | Direction | Status |
|---|---|---|---|
| ASYM-001 | Our system was scored on a smaller question set — the adversarial / unanswerable question subset was dropped on our side but kept for competitors. Competitors score near-zero on that subset, so excluding it from our side narrows the gap in our favour. | FAVORS_MNEMOVERSE | active |
| ASYM-002 | The reader (the LLM that writes the final answer from retrieved context) received per-question answer-format hints on our path but not on the competitor path, so our reader was told the expected shape of the answer (list / date / multi-fact) and the competitor's was not. | FAVORS_MNEMOVERSE | active |
| ASYM-003 | Some competitor cells were published with a 100% retrieval-failure rate (every query hit a quota/rate-limit error and returned nothing), yet the resulting judge scores were presented as real measurements rather than as scores against an empty context. | FAVORS_MNEMOVERSE | active |
| ASYM-004 | The same judge column name referred to two *different* judge prompts depending on the path — a binary-text-output prompt on our side and a JSON-label prompt on the competitor side — so the column being compared across systems was not one comparable metric. | FAVORS_MNEMOVERSE | active |
| ASYM-005 | The retrieved context was formatted differently for the two readers: our reader saw per-item relevance scores plus a chronological sort; the competitor reader saw only a positional index. These extra signals aid the reader, especially on temporal questions. | FAVORS_MNEMOVERSE | active |
| ASYM-006 | Judge token-usage was never recorded on the competitor path (the counter was initialised but never incremented), so every competitor cell reported zero judge cost while our cells carried real judge cost — biasing any cost comparison. | FAVORS_MNEMOVERSE | active |
| ASYM-007 | When the reader LLM call failed, our path silently substituted the top retrieved item as the "answer" (which can still pass the judge), while the competitor path returned an empty string (which always scores zero). | FAVORS_MNEMOVERSE | active |
| ASYM-008 | At large retrieval depths, our reader's effective context was capped per question-type while the competitor reader received the full retrieved list. This both withholds context (a disadvantage) and reduces noise (an advantage), so the net direction is genuinely two-sided. | BOTH | active |
| ASYM-009 | The reader answer-length / thinking budget was smaller on our path than on the competitor path. This clearly disadvantages us (small in practice). | FAVORS_COMPETITOR | active |
| ASYM-010 | Empty-answer rows were handled inconsistently across the two scoring paths — scored as zero on one path, skipped on the other — producing different per-judge denominators with no disclosure. Direction depends on which side has empty answers in a given cell. | BOTH | active |
| ASYM-011 | When a per-row judge call failed, the failure was silently dropped and the aggregate was computed over a smaller denominator with no field recording how many rows were actually judged. Direction depends on which rows failed. | BOTH | active |
| ASYM-012 | Our system applied an in-evaluation memory update (an adaptive learning step) between questions within the same cell, so later questions saw an evolving retrieval state driven by the very query distribution being evaluated. Competitor systems were frozen after ingestion and received no equivalent step. | FAVORS_MNEMOVERSE | active |
| ASYM-013 | Recall-against-evidence was computable for our cells (which carried real memory ids) but not for competitor cells (which returned only snippet text with positional placeholder ids), so any recall comparison structurally favours our side. | FAVORS_MNEMOVERSE | active |
| ASYM-014 | A query-failure-rate field was present on competitor cells but absent on ours; its absence on our side reads as "zero failures" but actually conflates that with "the run crashed before publishing," a survivorship effect in our favour. | FAVORS_MNEMOVERSE | active |
| ASYM-015 | Provenance (the code-version stamp) on our cells was applied at a later normalization step rather than captured at run time, while competitor cells carried a real run-time stamp — so our headline numbers reference a version the run itself did not record. | FAVORS_MNEMOVERSE | active |
| ASYM-016 | A competitor ingestion path could swallow per-unit write failures and report zero failed units downstream, making a partially-failed ingestion look like a clean one and understating the competitor only when reported as a ratio. | FAVORS_MNEMOVERSE | active |
| ASYM-017 | Points along a single competitor depth-curve were produced under two different code versions, so curve shape cannot be cleanly attributed to retrieval depth vs. code drift. The drift direction is unattributable. | BOTH | active |
| ASYM-018 | Our cells and the competitor cells were produced under different code versions, and re-running the competitor harness at our version would re-introduce a since-fixed bug — so the cross-version mismatch makes the gap impossible to validate at a single shared version. | BOTH | active |
| ASYM-019 | A secondary code path used to run our system through the competitor harness drifts from our main ingestion plumbing, so re-running our system that way would not reproduce the headline numbers. Direction depends on which ingestion setting dominates. | UNKNOWN | active |
| ASYM-020 | A competitor's ingestion counts were reported in mismatched units (documents vs. conversation turns), so a naive stored/total ratio reads as a catastrophic ingestion failure when the system actually ingested everything — distorting downstream per-unit comparisons. | FAVORS_MNEMOVERSE | active |
| ASYM-021 | Because judge token-usage was zero on the competitor path (see ASYM-006), the derived competitor judge-cost was structurally zero while ours reflected real tokens — so cross-system cost comparisons are not apples-to-apples. | BOTH | active |
| ASYM-022 | Two of the judges in the panel replicate a published, deliberately lenient evaluation prompt (accepting paraphrase, partial credit, and a wide temporal tolerance) that inflates every system's score and compresses the gap between strong and weak systems. The net effect on cross-system ranking is two-sided, but the inflation is real and must be disclosed whenever such a number is cited. | BOTH | active |
| ASYM-023 | One competitor's retrieval was internally capped, so its cells labelled with deep retrieval depths actually measured a much shallower depth — putting it at a structural retrieval-depth disadvantage at those labels. Fixed in later harness work; historical deep-depth cells for that system remain affected. | FAVORS_MNEMOVERSE | closed (historical cells affected) |
| ASYM-026 | An ingestion "settle" check on our HTTP path read an org-wide count rather than a per-conversation count, which is safe for sequential ingestion but would mis-settle under parallel ingestion into the same workspace. No run to date does parallel ingestion, so it is a latent risk, not a live bias. | UNKNOWN | active |
| ASYM-024 | Our HTTP retrieval path omitted a retrieval feature that our in-process baseline used by default, so HTTP cells under-represented our own engine and read as "the API is worse than local" when the real difference was the missing feature flag. Closed in later harness work; pre-fix cells remain affected. | FAVORS_COMPETITOR | closed (historical cells affected) |
| ASYM-027 | After the ASYM-024 fix, our HTTP retrieval path applies a query-strategy preset (selected by a server-side classifier) that the in-process baseline does not, giving the HTTP row a structurally stronger retrieval pipeline. This is intra-Mnemoverse (it decides which of our own rows leads), disclosed as a kept, named advantage rather than hidden. | FAVORS_MNEMOVERSE | active (disclosed kept advantage) |
| ASYM-025 | Our HTTP ingestion path stored raw turn text and relied on server-side concept extraction, while the in-process baseline stored timestamp-and-speaker-prefixed text and extracted concepts client-side — so the two paths differ in both stored content and extraction trigger, plausibly affecting temporal retrieval. Closed in later harness work; historical HTTP cells remain affected. | UNKNOWN | closed (historical cells affected) |
| ASYM-028 | The shared reader prompt was tuned against a development conversation (anti-abstain, list-format, brevity rules matching the benchmark's failure modes). It is applied identically to every system, so it is not a row-vs-row bias, but it bakes benchmark knowledge into the harness and means absolute scores overstate out-of-box performance for every system. | BOTH (symmetric across systems) | active |
| ASYM-029 | Some competitors index asynchronously: ingestion returning is not the same as the store being queryable. In one run, an async competitor was queried before its index settled (or its response shape had drifted), so the harness measured an empty/partial index and published it as the system's score — understating the competitor, the same dishonesty class as inflating our own numbers. Mitigated by a quarantine gate plus a re-query mode; a settle-poll is pending. | FAVORS_MNEMOVERSE | active (mitigated) |
| ASYM-030 | Our in-process reference row ran with a much larger per-read time budget than the production default, so it could answer reads a production-budget engine would refuse. This is intra-Mnemoverse (it concerns the in-process reference row only; the headline HTTP row hits the production server with the production budget); the asymmetry is availability, not latency, and per-read latency is still recorded honestly. | FAVORS_MNEMOVERSE | active (in-proc reference row only) |

## Count summary

Thirty asymmetries are catalogued. By the direction each one tilts:

| Direction | Count |
|---|---|
| FAVORS_MNEMOVERSE | 17 |
| FAVORS_COMPETITOR | 2 |
| BOTH (two-sided / ambiguous) | 8 |
| UNKNOWN | 3 |
| **Total** | **30** |

Seventeen of the thirty findings tilt in our favour. One of those seventeen
(ASYM-023) is closed for new runs and tilts only historical cells, so
**sixteen actively favour us on current runs**. Two findings clearly
disadvantage us (ASYM-009; ASYM-024, the latter now closed). The remaining
eleven are two-sided or undetermined.

On current runs alone---excluding the three findings closed for new runs
(ASYM-023, ASYM-024, ASYM-025)---the active breakdown is **sixteen favouring
us, one a competitor, and ten two-sided or undetermined**. Those are the counts
the paper cites ("sixteen of the thirty findings favour us").

The honest headline is the one we want a reader to take away: the bias in our
raw comparisons skews toward our own system, and any cross-system claim drawn
from these cells must account for that directional skew — not just the count
of findings.
