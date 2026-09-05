#!/usr/bin/env python3
"""Calibrated-judge agreement with the two additional annotators (offline).

The paper quotes the calibrated (golden-v2) judge's agreement with the two
additional annotators' labels on decided validation cases. This script makes
that number recompute from committed artifacts alone:

  - experiments/golden_judge/verdicts_golden2_validation_set.json (sealed verdicts)
  - kit/annotation/annotator_key_mapping.json (masked-id -> validation ex-id)
  - kit/annotation/returned/cases_{OI,NS}_labels.json (annotator labels)

Agreement is computed on the cases the annotator DECIDED (CORRECT or WRONG,
non-catch, set_a only); AMBIGUOUS cases carry no verdict to agree with.

    python scripts/golden_vs_externals.py
Writes experiments/hardening/golden_vs_externals.md and prints it.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "experiments" / "hardening" / "golden_vs_externals.md"


def unwrap_mapping(mapping):
    """The key mapping ships as a list, or as a dict wrapping one under 'cases'.
    An empty 'cases' means an empty campaign, not 'try the dict's values' -- so
    test for the key, never for truthiness."""
    if isinstance(mapping, list):
        return mapping
    if "cases" in mapping:
        return mapping["cases"]
    return list(mapping.values())


def main():
    golden = {r["qid"]: r["label"] for r in json.loads(
        (REPO / "experiments/golden_judge/verdicts_golden2_validation_set.json")
        .read_text(encoding="utf-8"))["records"]}
    mapping = json.loads((REPO / "kit/annotation/annotator_key_mapping.json")
                         .read_text(encoding="utf-8"))
    items = unwrap_mapping(mapping)
    val_of = {m["masked_id"]: m["source_qid"] for m in items
              if m.get("source_set") == "set_a" and not m.get("is_catch")}
    if not val_of:
        raise SystemExit("no set_a non-catch cases in the key mapping -- artifact drift?")

    L = ["# Calibrated judge vs the two additional annotators (validation set)", "",
         "Decided = annotator labeled CORRECT or WRONG (non-catch, set_a). "
         "Golden verdicts were sealed before any annotator labels existed. "
         "Rerun: `python scripts/golden_vs_externals.py` (offline, no API).", ""]
    for code in ("OI", "NS"):
        labels = json.loads((REPO / f"kit/annotation/returned/cases_{code}_labels.json")
                            .read_text(encoding="utf-8"))
        lab = {r["id"]: r["verdict"] for r in labels["labels"]}
        agree = n = 0
        misses = []
        for mid, ex in val_of.items():
            hv = lab.get(mid)
            if hv not in ("CORRECT", "WRONG"):
                continue
            gv = golden.get(ex)
            if gv not in ("CORRECT", "WRONG"):
                continue
            n += 1
            if gv == hv:
                agree += 1
            else:
                misses.append((mid, ex, hv, gv))
        if n == 0:
            raise SystemExit(f"{code}: no jointly-decided cases -- labels or verdicts drifted")
        L.append(f"**{code}: {agree} of {n} decided cases ({100*agree/n:.1f}%)**")
        for mid, ex, hv, gv in misses:
            L.append(f"- {mid} ({ex}): human {hv}, golden {gv}")
        L.append("")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
