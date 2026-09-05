#!/usr/bin/env python3
"""SUPERSEDED by scripts/rank_bootstrap.py -- kept for provenance, not cited by the paper.

WHY: this script pools six pipelines, but naked_cosine ran on a different runner
path from the other five (its answers average 105 characters against 43-70, and
its `mnemoverse` judge is the binary-text prompt, not the JSON one the harness
cells use -- core ASYM-004). Its 4/15 and 4/10 flip counts therefore mix two
answer paths and two judge prompts under one label, and its Spearman values are
computed over five or six points, where the 5% critical value is 0.90. The paper
reports instead the five-pipeline single-sweep matrix with a paired bootstrap
(scripts/rank_bootstrap.py): 2 of 10 pairs flip, 95% interval [0, 4].
The aggregates artifact this reads (kit/data/matrix_conv26_multijudge.json) is
still live -- rank_bootstrap.py gates its per-question extraction against it.

Original docstring follows.

Multi-system rank stability under judge variation (external-review #1 / Q1).

Reads the committed matrix artifact kit/data/matrix_conv26_multijudge.json
(six memory systems x four judges on LoCoMo conv-26, symmetric harness:
same gpt-5-mini reader, same text-embedding-3-small embeddings, same n=152
questions; extracted from the private core matrix cells -- see _provenance)
and reports, per k:

  - the full system x judge accuracy table,
  - every PAIRWISE RANK REVERSAL (a pair of systems whose order flips
    between judges),
  - Spearman rank correlation between judges' system rankings.

Run offline, no API:  python scripts/multi_system_rank.py

One-time extraction from a core checkout (maintainers only):
  python scripts/multi_system_rank.py --extract-from <core>/experiments/benchmarks/matrix/cells
"""
from __future__ import annotations
import argparse, itertools, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ART = REPO / "kit" / "data" / "matrix_conv26_multijudge.json"
OUT_MD = REPO / "experiments" / "hardening" / "multi_system_rank.md"

SYSTEMS = ["mem0_v3_cloud", "mnemoverse_engine", "mnemoverse_http",
           "naked_cosine", "supermemory", "zep"]
JUDGES = ["mnemoverse", "mem0", "mem0-4o", "strict"]
KS = [10, 20, 50, 100, 200]


def extract(cells_dir: str) -> None:
    cells = {}
    src = Path(cells_dir)
    for s in SYSTEMS:
        for k in KS:
            p = src / f"cell_{s}_locomo_conv26_n152_k{k}.json"
            if not p.exists():
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            cells[f"{s}|k{k}"] = {
                "system": s, "k": k,
                "judge_accuracy_by_judge": d["aggregates"]["judge_accuracy_by_judge"],
                "reader_model": d.get("reader_model"),
                "embedding_model": (d.get("config") or {}).get("embedding_model"),
                "n": d.get("benchmark_scope_n", 152),
            }
    art = {"_provenance": {
        "source": "mnemoverse-core experiments/benchmarks/matrix/cells (baseline-2026-06-08, symmetric harness)",
        "note": "Same gpt-5-mini reader and text-embedding-3-small embeddings for every system "
                "(naked_cosine is the reader-free retrieval baseline scored on extractive answers); "
                "judges as in kit/prompts (mnemoverse=gpt-5-mini, mem0=gpt-5, mem0-4o=gpt-4o, strict=gpt-5). "
                "zep cells exist for k in {10,20,50} only.",
        "extracted": "2026-07-14",
    }, "cells": cells}
    ART.write_text(json.dumps(art, indent=1), encoding="utf-8")
    print(f"extracted {len(cells)} cells -> {ART}")


def spearman(x, y):
    n = len(x)
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for t in range(i, j + 1):
                r[order[t]] = avg
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def analyze() -> int:
    art = json.loads(ART.read_text(encoding="utf-8"))
    cells = art["cells"]
    L = ["> **SUPERSEDED (2026-07-15) -- not cited by the paper.** This analysis pools six",
         "> pipelines, but `naked_cosine` ran on a different runner path from the other five",
         "> (answers ~105 chars vs 43-70; its `mnemoverse` judge is the binary-text prompt,",
         "> not the JSON one the harness cells use -- core ASYM-004). Its 4/15 and 4/10 flip",
         "> counts therefore mix two answer paths and two judge prompts under one label, and",
         "> its Spearman values run over 5-6 points (5% critical value 0.90). The paper reports",
         "> the five-pipeline single-sweep matrix with a paired bootstrap instead:",
         "> `experiments/hardening/rank_bootstrap.md` -- 2 of 10 pairs flip, 95% interval [0, 4].",
         "",
         "# Multi-system rank stability under judge variation (conv-26, historic six-pipeline pooling)", "",
         "Six pipelines x four judges as originally pooled -- NOT a symmetric comparison; see banner. "
         "Source artifact `kit/data/matrix_conv26_multijudge.json`; rerun `python scripts/multi_system_rank.py`.", ""]
    headline = {}
    for K in KS:
        tab = {s: cells[f"{s}|k{K}"]["judge_accuracy_by_judge"]
               for s in SYSTEMS if f"{s}|k{K}" in cells}
        if len(tab) < 3:
            continue
        L.append(f"## k = {K}  ({len(tab)} systems)")
        L.append("")
        L.append("| system | " + " | ".join(JUDGES) + " |")
        L.append("|---|" + "---:|" * len(JUDGES))
        for s, j in tab.items():
            L.append(f"| {s} | " + " | ".join(f"{j.get(x, float('nan')):.3f}" for x in JUDGES) + " |")
        systems = list(tab)
        revs = []
        for a, b in itertools.combinations(systems, 2):
            orders = {tab[a][jd] > tab[b][jd] for jd in JUDGES if jd in tab[a] and jd in tab[b]}
            if len(orders) > 1:
                revs.append((a, b))
        pairs = len(list(itertools.combinations(systems, 2)))
        L.append("")
        L.append(f"**Rank reversals: {len(revs)} of {pairs} system pairs flip order between judges.**")
        for a, b in revs:
            detail = ", ".join(f"{jd}: {a if tab[a][jd] > tab[b][jd] else b}"
                               for jd in JUDGES if jd in tab[a] and jd in tab[b])
            L.append(f"- {a} vs {b} -> winner by judge: {detail}")
        L.append("")
        rhos = []
        for j1, j2 in itertools.combinations(JUDGES, 2):
            rho = spearman([tab[s][j1] for s in systems], [tab[s][j2] for s in systems])
            rhos.append((j1, j2, rho))
        L.append("Spearman rank correlation between judges: " +
                 "; ".join(f"{a}~{b}: {r:.2f}" for a, b, r in rhos))
        L.append("")
        headline[K] = (len(revs), pairs, min(r for _, _, r in rhos))
    # headline assertions (fail-closed reproduction gate)
    ok = headline.get(200, (0, 0, 1))[:2] == (4, 10) and headline.get(50, (0, 0, 1))[:2] == (4, 15)
    L.append(f"Reproduction gate: k=200 -> {headline.get(200)}, k=50 -> {headline.get(50)} "
             f"(expected reversals 4/10 and 4/15) => {'PASS' if ok else 'FAIL'}")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-from", default=None)
    a = ap.parse_args()
    if a.extract_from:
        extract(a.extract_from)
    if not ART.exists():
        sys.exit("no artifact; run with --extract-from <core cells dir>")
    raise SystemExit(analyze())
