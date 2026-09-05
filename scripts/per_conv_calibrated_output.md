# Per-conversation lenient vs calibrated (golden v2) — full Mem0 published run

Provenance: computed offline (stdlib only) from the committed per-answer verdicts `experiments/hardening/verdicts/B_conv{0..9}_mem0.json` (lenient) and `experiments/golden_judge/fullrun_verdicts/conv{0..9}_golden2.json` (calibrated); counting conventions of `kit/scripts/judge.py::run_judge` (scored iff score is exactly 0/1); headline row = jointly-scored answers (paper convention, main.tex golden-judge footnote). Rerun: `python scripts/per_conv_calibrated.py`.

| conv | n (joint) | n (total) | lenient % | calibrated % | inflation (pp) |
|------|-----------|-----------|-----------|--------------|----------------|
| conv0 | 151 | 152 | 92.1 | 85.4 | +6.6 |
| conv1 | 81 | 81 | 86.4 | 77.8 | +8.6 |
| conv2 | 152 | 152 | 96.1 | 91.4 | +4.6 |
| conv3 | 196 | 198 | 85.2 | 78.6 | +6.6 |
| conv4 | 177 | 178 | 87.0 | 80.2 | +6.8 |
| conv5 | 123 | 123 | 89.4 | 86.2 | +3.3 |
| conv6 | 150 | 150 | 92.0 | 86.7 | +5.3 |
| conv7 | 191 | 191 | 95.3 | 91.1 | +4.2 |
| conv8 | 156 | 156 | 91.7 | 85.9 | +5.8 |
| conv9 | 157 | 158 | 93.6 | 87.3 | +6.4 |
| **all** | **1534** | **1539** | **91.0** | **85.3** | **+5.7** |

Aggregate (jointly-scored, n=1534): lenient 0.9100, calibrated 0.8527, inflation 5.74 pp.
Robustness: lenient over all its 1539 scored answers = 0.9103 (inflation 5.77 pp); counting the 5 calibrated-unparseable answers as wrong = calibrated 0.8499 (inflation 6.04 pp).
Sensitivity, excluding conv0 (= LoCoMo conv-26; its questions fed the judge's calibration signal via the control slice): joint-denominator inflation 5.64 pp on n=1383 -- i.e. 5.6-5.7 depending on handling.
The 5 calibrated-unparseable answers (excluded from the joint denominator; inflation is computed at full precision before rounding, so a table row may differ from the subtraction of its rounded columns by 0.1): `conv0:conv0_q70`, `conv3:conv3_q81`, `conv3:conv3_q83`, `conv4:conv4_q9`, `conv9:conv9_q12`.

Reproduction check vs paper: lenient 91.0 -> PASS (91.0039); calibrated 85.3 -> PASS (85.2673); inflation 5.7 pp -> PASS (5.7366); per-conv cells match committed summaries -> PASS.
