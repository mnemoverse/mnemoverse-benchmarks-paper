# Source Attribution — mem0_oss_answers/

## Origin

These files contain Mem0 Platform's **generated answers** for LoCoMo conversations,
extracted verbatim from the mem0ai/memory-benchmarks public repository.

> Note on the name: the `_oss_` in this directory refers to the **open-source
> license** under which Mem0 released these answers, not to an OSS-library run.
> The answers are outputs of Mem0's **hosted Platform**, published open-source
> (Apache-2.0) in the benchmarks repo. (The separate `answers_mem0_conv26.json`
> set used for the q8 result was, by contrast, produced by us running Mem0's
> open-source benchmark pipeline locally — see `kit/data/ATTRIBUTION.md`.)

| Field         | Value |
|---------------|-------|
| Repo URL      | https://github.com/mem0ai/memory-benchmarks |
| License       | Apache-2.0 |
| Commit SHA    | `4b61c5d31b9c668a12b4f5e78064248a02c82d2b` |
| Upstream file | `results/platform/locomo_results.json` |
| Run timestamp | `20260406_170942` (from `metadata.timestamp`) |
| Answerer model | `gpt-5` (from `metadata.answerer_model`) |
| Judge model   | `gpt-5` (from `metadata.judge_model`) |
| Provider      | `azure` |
| Retrieval cutoff used | `top_200` |

## Conversations extracted

All ten LoCoMo conversations from the upstream run are extracted (one file each,
`conv0.json`–`conv9.json`), **1,539 answers total**:

| File | Upstream conv_idx | Questions |
|------|-------------------|-----------|
| `conv0.json` | 0 | 152 |
| `conv1.json` | 1 | 81 |
| `conv2.json` | 2 | 152 |
| `conv3.json` | 3 | 198 |
| `conv4.json` | 4 | 178 |
| `conv5.json` | 5 | 123 |
| `conv6.json` | 6 | 150 |
| `conv7.json` | 7 | 191 |
| `conv8.json` | 8 | 156 |
| `conv9.json` | 9 | 158 |
| **total** | | **1,539** |

**Note on `conv0`:** this is "conv-26" in the paper. These are Mem0's published
*platform* answers — the `gpt-5`/azure run behind Mem0's reported ~92% LoCoMo
headline — and are a **different Mem0 answer set** from
`kit/data/rejudge_q8_20260531T201308Z.json` (the q8 comparison run, ~74% under the
lenient judge). Re-judging `conv0` is therefore a useful consistency check against q8,
not a duplicate of it.

## Record schema

Each file is a JSON array of objects:

```json
{
  "qid":      "conv1_q0",          // upstream question_id
  "question": "...",               // question text from LoCoMo
  "gold":     "...",               // ground-truth answer from LoCoMo
  "answer":   "...",               // Mem0 Platform's generated answer (top_200 cutoff)
  "category": "temporal"           // LoCoMo category: temporal / single-hop / multi-hop / open-domain
}
```

`answer` is taken from `cutoff_results.top_200.generated_answer` in the upstream file.
No records have `null` answers across these ten conversations (verified at extraction time).

## What is NOT redistributed

These files do NOT include:
- The raw LoCoMo dialogue/conversation text
- Mem0's internal memory representations
- Latency or retrieval metadata

Only the (question, gold, Mem0-generated-answer, category) tuples needed for
re-judging are included. This minimises reproduction of the LoCoMo dataset content
while preserving everything needed to run the strict-vs-generous judge comparison.

## LoCoMo dataset credit

The question text and gold answers originate from the LoCoMo dataset:

> Maharana, A., Lee, D., Tulyakov, S., Bansal, M., Barbieri, F., & Fang, Y. (2024).
> Evaluating Very Long-Term Conversational Memory of LLM Agents.
> ACL 2024. https://arxiv.org/abs/2402.17753

See the LoCoMo repository (https://github.com/snap-research/locomo) for dataset terms.
