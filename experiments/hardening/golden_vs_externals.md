# Calibrated judge vs the two additional annotators (validation set)

Decided = annotator labeled CORRECT or WRONG (non-catch, set_a). Golden verdicts were sealed before any annotator labels existed. Rerun: `python scripts/golden_vs_externals.py` (offline, no API).

**OI: 46 of 49 decided cases (93.9%)**
- q018 (c9_qconv9_q82): human WRONG, golden CORRECT
- q110 (c1_qconv1_q33): human CORRECT, golden WRONG
- q119 (c3_qconv3_q140): human CORRECT, golden WRONG

**NS: 47 of 50 decided cases (94.0%)**
- q019 (c3_qconv3_q114): human WRONG, golden CORRECT
- q119 (c3_qconv3_q140): human CORRECT, golden WRONG
- q153 (c4_qconv4_q4): human CORRECT, golden WRONG

