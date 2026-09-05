#!/usr/bin/env python3
"""Best/worst-case bounds for the date-tolerance ablation's unparseable verdicts
(review B-R2 #3: 158 unparseable rows could hide non-random selection bias).

For each ablation judge, recompute its drop-from-lenient under three handlings
of its unparseable rows: excluded (the paper's convention), all-counted-correct
(best case for the variant), all-counted-wrong (worst case). If the ordering of
the four single-rule drops is unchanged under every handling, the 158 rows
cannot be driving the conclusion.

    python scripts/ablation_unparseable_bounds.py   (offline)
Writes experiments/hardening/ablation_unparseable_bounds.md.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V = REPO / "experiments" / "hardening" / "verdicts"
OUT = REPO / "experiments" / "hardening" / "ablation_unparseable_bounds.md"
CONVS = [f"conv{i}" for i in range(10)]
ABL = ["abl-no-paraphrase", "abl-no-datetol", "abl-no-partial", "abl-no-extradetail"]


def rows(name):
    out = {}
    for c in CONVS:
        for r in json.loads((V / f"{('ABL_' if name.startswith('abl') else 'B_')}{c}_{name}.json")
                            .read_text(encoding="utf-8")):
            s = r.get("score")
            out[f"{c}:{r['qid']}"] = float(s) if isinstance(s, (int, float)) and s in (0.0, 1.0) else None
    return out


def main():
    lenient = rows("mem0")
    len_scored = {q: s for q, s in lenient.items() if s is not None}
    len_acc = 100 * sum(len_scored.values()) / len(len_scored)
    L = ["# Date-tolerance (and all) ablation: unparseable-row bounds", "",
         "Drop from lenient (91.0 on its own scored set) under three handlings of each "
         "variant's unparseable rows. Paper convention = excluded. "
         "Rerun: `python scripts/ablation_unparseable_bounds.py`.", ""]
    L.append("| variant | unparseable | drop (excluded) | drop (all correct) | drop (all wrong) |")
    L.append("|---|---:|---:|---:|---:|")
    table = {}
    for name in ABL:
        r = rows(name)
        n_un = sum(1 for s in r.values() if s is None)
        joint = {q: s for q, s in r.items() if q in len_scored}
        scored = {q: s for q, s in joint.items() if s is not None}
        acc_ex = 100 * sum(scored.values()) / len(scored)
        len_ex = 100 * sum(len_scored[q] for q in scored) / len(scored)
        acc_hi = 100 * (sum(scored.values()) + (len(joint) - len(scored))) / len(joint)
        acc_lo = 100 * sum(scored.values()) / len(joint)
        len_all = 100 * sum(len_scored[q] for q in joint) / len(joint)
        table[name] = (n_un, len_ex - acc_ex, len_all - acc_hi, len_all - acc_lo)
        L.append(f"| {name} | {n_un} | {len_ex-acc_ex:+.1f} | {len_all-acc_hi:+.1f} | {len_all-acc_lo:+.1f} |")
    L.append("")
    for handling, i in (("excluded", 1), ("all-correct", 2), ("all-wrong", 3)):
        order = sorted(table, key=lambda k: -table[k][i])
        L.append(f"Ordering under {handling}: " + " > ".join(o.replace('abl-no-', '') for o in order))
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
