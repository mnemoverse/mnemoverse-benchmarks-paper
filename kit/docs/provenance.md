# Benchmark Run Provenance — Public Contract

Every number published from this benchmark project must satisfy a
**four-artifact provenance chain**. A number that cannot be traced through
all four links is not publishable.

## The four-artifact chain

```
               run_id  (the join key — present in every artifact)
                 │
  ┌──────────────┼───────────────┬──────────────────┐
  ▼              ▼               ▼                  ▼
protocol.md  →  result.json  →  registry entry  →  git SHA
(frozen        (the data)      (the index)       (the code
 pre-run)                                          version)
```

**Artifact A — `<run_id>.protocol.md`** (written before any work begins):
captures the verbatim CLI command, fully resolved config, all prompts
verbatim, provider and model IDs, git SHA + dirty flag, and timestamp.
A run with no `protocol.md` is provenance-incomplete and must not be cited.

**Artifact B — `result.json`** (the measurements): per-question results plus
aggregated metrics. Must carry `run_id` as the join key back to A and
forward to C.

**Artifact C — registry entry** (the index): one entry in `registry.json`
per run, produced either by self-registration on completion or by a
deterministic full rescan. Carries paradigm, integrity classification, and
a `visibility.public_dashboard` flag. The registry is what a number-audit
resolves against — if a number on a public surface does not trace to a
registry entry, it is untraceable.

**Artifact D — git SHA / tag** (the code version): captured in `protocol.md`
and ideally inside `result.json`. Deliberately pinned baselines also carry
an annotated git tag.

## The invariant

> For any published number **N**: there exists a `run_id` such that
> `N ∈ result.json(run_id).results`, `protocol.md(run_id)` exists and froze
> the config+prompts, `registry[run_id]` indexes it with a paradigm +
> integrity classification, and `git SHA` pins the code. Break any link →
> **not publishable**.

## Principle

A number is *provenanced* only when all four links exist and resolve. Numbers
that predate run-id discipline, or that were produced from a dirty working
tree without an archived diff, are marked `provenance lost` and kept
registry-only; they are never placed on public surfaces. Honesty about a gap
beats a fabricated chain.
