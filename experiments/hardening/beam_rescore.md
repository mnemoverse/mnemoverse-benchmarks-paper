# BEAM controlled re-score (P1): same answers, two prompts, 10M-token scale

Our engine's generated answers to the 200 BEAM-10M questions (nugget rubric as gold), re-scored under the SAME mem0 lenient and strict prompts on gpt-5. Answers committed at `kit/data/beam_answers_10m.json`; verdicts `experiments/hardening/verdicts/BEAM_*.json`; runner `scripts/run_beam_rescore.py`.

**Overall (n=197): lenient 74.1% vs strict 7.6% -- a 66.5-point swing on identical answers.**

| question type | n | lenient % | strict % | swing (pp) |
|---------------|---|-----------|----------|------------|
| abstention | 20 | 65.0 | 20.0 | +45.0 |
| contradiction_resolution | 20 | 85.0 | 0.0 | +85.0 |
| event_ordering | 19 | 78.9 | 0.0 | +78.9 |
| information_extraction | 20 | 65.0 | 0.0 | +65.0 |
| instruction_following | 20 | 95.0 | 30.0 | +65.0 |
| knowledge_update | 20 | 80.0 | 5.0 | +75.0 |
| multi_session_reasoning | 20 | 35.0 | 0.0 | +35.0 |
| preference_following | 20 | 75.0 | 5.0 | +70.0 |
| summarization | 20 | 100.0 | 0.0 | +100.0 |
| temporal_reasoning | 18 | 61.1 | 16.7 | +44.4 |

The prompt-sensitivity phenomenon of \S3 is not specific to LoCoMo or its scale: the same two grading prompts move BEAM-10M pass-rates by tens of points on a fixed set of answers scored against a per-claim nugget rubric.
