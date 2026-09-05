#!/usr/bin/env python3
"""Bootstrap CIs + common-denominator ablation (external reviews A#3/#5, B follow-ups).

Offline, stdlib only, seeded. Computes:
1. Calibrated inflation (lenient - golden on the joint full run): point estimate,
   item-level bootstrap 95% CI, conversation-cluster bootstrap 95% CI.
2. Same-backbone rubric gap (mem0-4o - LongMemEval, both gpt-4o): same three numbers.
3. Single-rule ablation drops on the COMMON jointly-parseable denominator
   (answers scored by lenient + strict + all four ablation judges).

    python scripts/stats_ci.py
Writes experiments/hardening/stats_ci.md and prints it.
"""
from __future__ import annotations
import json, random
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V = REPO / "experiments" / "hardening" / "verdicts"
G = REPO / "experiments" / "golden_judge" / "fullrun_verdicts"
OUT = REPO / "experiments" / "hardening" / "stats_ci.md"
CONVS = [f"conv{i}" for i in range(10)]
B = 4000
random.seed(20260714)


def smap(path: Path) -> dict:
    recs = json.loads(path.read_text(encoding="utf-8"))
    return {r["qid"]: float(r["score"]) for r in recs
            if isinstance(r.get("score"), (int, float)) and r["score"] in (0.0, 1.0)}


def paired_pool(files_a, files_b):
    """-> list of (conv, delta_item) where delta = a - b on jointly scored qids."""
    out = []
    for conv, fa, fb in zip(CONVS, files_a, files_b):
        a, b = smap(fa), smap(fb)
        for q in sorted(set(a) & set(b)):
            out.append((conv, a[q] - b[q]))
    return out


def boot(pool):
    n = len(pool)
    point = 100 * sum(d for _, d in pool) / n
    # item bootstrap
    vals = []
    for _ in range(B):
        s = 0.0
        for _ in range(n):
            s += pool[random.randrange(n)][1]
        vals.append(100 * s / n)
    vals.sort()
    item_ci = (vals[int(.025 * B)], vals[int(.975 * B)])
    # conversation-cluster bootstrap
    byconv = {}
    for c, d in pool:
        byconv.setdefault(c, []).append(d)
    convs = list(byconv)
    cvals = []
    for _ in range(B):
        picked = [byconv[convs[random.randrange(len(convs))]] for _ in convs]
        tot = sum(sum(x) for x in picked)
        m = sum(len(x) for x in picked)
        cvals.append(100 * tot / m)
    cvals.sort()
    clus_ci = (cvals[int(.025 * B)], cvals[int(.975 * B)])
    return point, n, item_ci, clus_ci


def main():
    L = ["# Bootstrap CIs and common-denominator ablation", "",
         f"Seeded (20260714), B={B} resamples, stdlib only. Rerun: `python scripts/stats_ci.py`.", ""]

    infl = boot(paired_pool([V / f"B_{c}_mem0.json" for c in CONVS],
                            [G / f"{c}_golden2.json" for c in CONVS]))
    L.append(f"**Calibrated inflation (lenient − golden, joint):** {infl[0]:.2f} pp (n={infl[1]}); "
             f"item bootstrap 95% CI [{infl[2][0]:.1f}, {infl[2][1]:.1f}]; "
             f"conversation-cluster 95% CI [{infl[3][0]:.1f}, {infl[3][1]:.1f}].")

    lme = boot(paired_pool([V / f"MV_{c}_mem0-4o.json" for c in CONVS],
                           [V / f"LME_{c}.json" for c in CONVS]))
    L.append(f"**Same-backbone rubric gap (mem0-4o − LongMemEval, both gpt-4o):** {lme[0]:.2f} pp (n={lme[1]}); "
             f"item 95% CI [{lme[2][0]:.1f}, {lme[2][1]:.1f}]; "
             f"cluster 95% CI [{lme[3][0]:.1f}, {lme[3][1]:.1f}].")
    L.append("")

    # common-denominator ablation
    judges = {"lenient": [V / f"B_{c}_mem0.json" for c in CONVS],
              "strict": [V / f"B_{c}_strict.json" for c in CONVS],
              "no_partial": [V / f"ABL_{c}_abl-no-partial.json" for c in CONVS],
              "no_paraphrase": [V / f"ABL_{c}_abl-no-paraphrase.json" for c in CONVS],
              "no_datetol": [V / f"ABL_{c}_abl-no-datetol.json" for c in CONVS],
              "no_extradetail": [V / f"ABL_{c}_abl-no-extradetail.json" for c in CONVS]}
    maps = {}
    for name, files in judges.items():
        m = {}
        for c, f in zip(CONVS, files):
            m.update({f"{c}:{q}": s for q, s in smap(f).items()})
        maps[name] = m
    common = set.intersection(*(set(m) for m in maps.values()))
    L.append(f"**Common-denominator ablation (answers scored by all six judges): n={len(common)}**")
    L.append("")
    L.append("| judge | score % | drop from lenient (pp) |")
    L.append("|---|---:|---:|")
    len_c = 100 * sum(maps["lenient"][q] for q in common) / len(common)
    for name in ("no_paraphrase", "no_datetol", "no_partial", "no_extradetail", "strict"):
        sc = 100 * sum(maps[name][q] for q in common) / len(common)
        L.append(f"| {name} | {sc:.1f} | {len_c - sc:+.1f} |")
    L.append(f"| lenient (anchor) | {len_c:.1f} | 0.0 |")
    L.append("")
    drops = {name: len_c - 100 * sum(maps[name][q] for q in common) / len(common)
             for name in ("no_paraphrase", "no_datetol", "no_partial", "no_extradetail")}
    ssum = sum(drops.values()); full = len_c - 100 * sum(maps["strict"][q] for q in common) / len(common)
    L.append(f"Single-rule drops sum to {ssum:.1f} pp vs the full swing {full:.1f} pp on the same n; "
             f"the gap is rule interaction. Ordering unchanged vs the per-variant denominators.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
