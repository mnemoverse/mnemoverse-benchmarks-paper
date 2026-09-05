# BEAM Benchmark — Integrity Rules (Public)

The following integrity rules govern every BEAM evaluation run that
produces numbers cited in the paper. They are extracted from the internal
BEAM Protocol and cover the three invariants the paper's claims depend on.

## Rule 1 — μ=0 zero-LLM-ingest invariant

`llm_calls_during_ingest == 0` across the entire run, for every
conversation at every token-budget scale (100K / 500K / 1M / 10M).

The runner asserts this after every conversation. If a single LLM call
fires during the ingest phase, **the run aborts with a non-zero exit code**
and prints the call-site stack. Any result file produced from a run where
this assertion was not met is invalid and must not be cited.

This is the central architectural claim for our own engine: Mnemoverse
ingests without LLM calls. Memory systems that perform LLM-based extraction
or summarization during ingest incur an ingest-time LLM cost; a μ=0 protocol
makes that cost an explicit, checkable property of a run rather than a hidden
variable in the headline.

## Rule 2 — Anti-cheat: gold evidence forbidden in read requests

The `ReadRequest` sent to the memory engine during evaluation **must not
contain** any of the following gold-label fields from the BEAM dataset:

- `rubric`
- `nuggets`
- `source_chat_ids`
- `difficulty`
- `ground_truth_answer`

Only `question_text` (the probing question itself) reaches the engine —
identical to what a real user would type. Passing any gold field to the
engine would trivially inflate scores and is forbidden.

The same rule applies to feedback: `outcome` must be the constant `0.5`
(neutral / blind). It must never be derived from nugget scores or judge
verdicts.

## Rule 3 — Reader-input token budget caveat

The BEAM headline score (average nugget score across questions) depends on
how many retrieved memories are fed to the reader. The paper's headline
numbers use Mem0's reference retrieval settings (`top_k=200`, reader
context capped at `cutoff=100`) with `gpt-5` reader and `gpt-5` judge —
matching Mem0's published protocol for apples-to-apples comparison.

**Cross-reader rows are not directly comparable.** A run with a different
reader model, a different token budget, or a different top-k produces a
number on a different axis. Track A (validation, non-gpt-5 reader) and
Track B (publication, gpt-5 reader) are not interchangeable: Track B vs
Mem0 isolates memory engine; Track A vs Mem0 is confounded by the LLM.
Each cited number must declare its reader model and token budget.
