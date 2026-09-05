# Third rubric: LongMemEval judge prompt over Mem0's full published run

Provenance: prompts = verbatim port of LongMemEval `evaluate_qa.py::get_anscheck_prompt` (default + temporal variants; kit/prompts/judge_longmemeval_*.txt), judge model gpt-4o-2024-08-06 (their pinned snapshot), temperature 0; answers = the same committed Mem0 published run; lenient/strict columns = the committed gpt-5 verdicts. Rerun: `python scripts/run_third_rubric_longmemeval.py`.

| conv | n | LongMemEval rubric % | lenient (mem0) % | strict (ours) % |
|------|---|----------------------|------------------|-----------------|
| conv0 | 152 | 81.6 | 92.1 | 30.9 |
| conv1 | 81 | 75.3 | 86.4 | 28.4 |
| conv2 | 152 | 88.2 | 96.1 | 35.5 |
| conv3 | 198 | 72.7 | 85.4 | 30.3 |
| conv4 | 178 | 80.3 | 87.1 | 34.3 |
| conv5 | 123 | 82.9 | 89.4 | 35.8 |
| conv6 | 150 | 86.0 | 92.0 | 44.0 |
| conv7 | 191 | 84.8 | 95.3 | 38.2 |
| conv8 | 156 | 78.2 | 91.7 | 37.2 |
| conv9 | 158 | 86.1 | 93.7 | 32.9 |
| **all** | **1539** | **81.7** | | |

Overall: LongMemEval rubric scores the run at 81.7%; the lenient prompt sits +9.4 pp above it (n=1539 joint), and it sits +46.7 pp above our strict prompt (n=1539 joint).
