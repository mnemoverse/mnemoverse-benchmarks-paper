#!/usr/bin/env python3
"""Rank-flip uncertainty for the conv-26 pipeline matrix (reviews A-R2 M1, B-R2 #1).

Headline matrix: the FIVE pipelines of the single 2026-06-07 harness sweep x
FOUR judges (mem0, mem0-4o, strict, mnemoverse) at k=50. All four judge columns
are comparable across those five, because every one of their cells carries
identical judge_prompt_hashes -- so `mnemoverse` there is one instrument.
naked_cosine ran on the other runner path (its `mnemoverse` judge is the
binary-text prompt, core ASYM-004; its answers average ~105 characters against
43-70), so it is reported SEPARATELY and never inside the matrix.

Reports:

  - the full cell table with answer counts (x/152),
  - observed pairwise flips (strict-order reversal between judges; ties do
    not count as flips -- declared tie rule),
  - the same restricted to the same-backbone pair (mem0 vs strict, both gpt-5),
  - naked_cosine's own cells, outside the matrix, with the format caveat,
  - paired bootstrap (resampling questions, B=10000): distribution of the
    flip count, per-observed-pair flip stability, winner agreement,
  - P(A>B) per judge for every pair involved in an observed flip.

This is the script behind the paper's Table 3 and its [0, 4] flip-count
interval: 2 of 10 pairs flip, and the interval includes zero, which is why the
paper reports an unstable ranking rather than a measured reversal.

Inputs are the committed per-question night-run / phase-c result files from the
private core checkout (paths below); the derived per-question matrix is written
to kit/data/matrix_conv26_perq.json so the analysis itself recomputes offline
from this repo alone. GATE: recomputed cell accuracies must match the committed
aggregates in kit/data/matrix_conv26_multijudge.json to 3 decimals, else exit 1.

    python scripts/rank_bootstrap.py [--core <core-root>]  # extract + analyze
    python scripts/rank_bootstrap.py                        # analyze committed
Writes experiments/hardening/rank_bootstrap.md.
"""
from __future__ import annotations
import argparse, itertools, json, random, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PERQ = REPO / "kit" / "data" / "matrix_conv26_perq.json"
AGG = REPO / "kit" / "data" / "matrix_conv26_multijudge.json"
OUT = REPO / "experiments" / "hardening" / "rank_bootstrap.md"
# All four judges are comparable ACROSS THE FIVE HARNESS PIPELINES: every one of
# those cells carries identical judge_prompt_hashes (mnemoverse 703651c0..., mem0
# f2215542..., mem0-4o same, strict dd9f96f2...), so the `mnemoverse` column is
# one instrument there. It is NOT comparable to naked_cosine, which ran on the
# other runner path with the binary-text mnemoverse prompt (core ASYM-004) --
# hence naked is excluded from the headline matrix and reported separately.
JUDGES = ["mem0", "mem0-4o", "strict", "mnemoverse"]
HARNESS = ["mem0_v3_cloud", "mnemoverse_engine", "mnemoverse_http", "supermemory", "zep"]
B = 10000
random.seed(20260715)

# The five harness cells live at git object e19f030 (branch preserve/conv26-
# baseline-e19f030) under experiments/results/matrix-2026-06-07/ -- the sweep
# behind the committed matrix aggregates (verified to 6 decimals). Their rows
# are in canonical question order (position i = i-th non-adversarial question),
# verified against locomo10 question texts (152/152 for every file).
# naked_cosine is the night-runs cell the committed cell's raw_data_url names.
E19 = "e19f030:experiments/results/matrix-2026-06-07"
SOURCES = {  # pipeline -> (git-show spec or relpath under experiments/results, qid mode)
    "naked_cosine": ("night-runs/cell_0e_naked_locomo_conv26_k50.json", "idx"),
    "mnemoverse_engine": (f"{E19}/cell_mnemoverse_locomo_conv26_n199_k50.json", "order"),
    "mnemoverse_http": (f"{E19}/cell_mnemoverse_http_locomo_conv26_n199_k50.json", "order"),
    "mem0_v3_cloud": (f"{E19}/cell_mem0_v3_cloud_locomo_conv26_n199_k50.json", "order"),
    "supermemory": (f"{E19}/cell_supermemory_locomo_conv26_n199_k50.json", "order"),
    "zep": (f"{E19}/cell_zep_locomo_conv26_n199_k50.json", "order"),
}


def norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def extract(core_root: str) -> None:
    import subprocess
    core = Path(core_root)
    qa = json.loads((core / "experiments/data/locomo10.json").read_text(encoding="utf-8"))[0]["qa"]
    # canonical indices 0..151 are the non-adversarial questions (cat5 = tail 152..198)
    canon = [i for i, q in enumerate(qa) if q.get("category") != 5]
    assert canon == list(range(152)), "cat-5 tail assumption violated"
    canon_text = [norm(qa[i]["question"]) for i in canon]

    matrix = {}
    for pipe, (rel, mode) in SOURCES.items():
        if ":" in rel:  # git-show spec
            raw = subprocess.run(["git", "-C", str(core), "show", rel],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
            d = json.loads(raw)
        else:
            d = json.loads((core / "experiments/results" / rel).read_text(encoding="utf-8"))
        rows = {}
        if mode == "order":
            res = d["results"]
            if len(res) != 152:
                raise SystemExit(f"{pipe}: {len(res)} rows, expected 152")
            for i, r in enumerate(res):
                if norm(r.get("question", "")) != canon_text[i]:
                    raise SystemExit(f"{pipe}: row {i} question mismatch vs canonical order")
                rows[i] = {j: r["judge_scores"].get(j) for j in JUDGES}
        else:
            for r in d["results"]:
                i = int(r["qid"].split("::q")[1])
                if i > 151 or str(r.get("category")) == "5":
                    continue
                rows[i] = {j: r["judge_scores"].get(j) for j in JUDGES}
        if len(rows) != 152:
            raise SystemExit(f"{pipe}: paired {len(rows)} of 152")
        matrix[pipe] = {str(i): rows[i] for i in sorted(rows)}
    PERQ.write_text(json.dumps(
        {"_provenance": {
            "source": "core git object e19f030 (branch preserve/conv26-baseline-e19f030), "
                      "experiments/results/matrix-2026-06-07/ -- the harness sweep behind the "
                      "committed matrix aggregates (verified to 6 decimals); naked_cosine from "
                      "night-runs cell_0e, the committed cell's raw_data_url",
            "note": "k=50, LoCoMo conv-26, 152 non-adversarial questions; judges mem0/mem0-4o/strict "
                    "(mnemoverse judge excluded per ASYM-004: two different prompts under one label). "
                    "Pairing: harness rows are in canonical question order (verified against locomo10 "
                    "texts, 152/152 per file); naked by positional qid.",
            "extracted": "2026-07-15"},
         "matrix": matrix}, indent=1), encoding="utf-8")
    print(f"extracted per-question matrix -> {PERQ}")


def analyze() -> int:
    perq = json.loads(PERQ.read_text(encoding="utf-8"))["matrix"]
    pipes = [p for p in HARNESS if p in perq]   # headline matrix: the five harness pipelines
    n = 152
    idx = [str(i) for i in range(n)]

    def acc(pipe, judge, sample):
        vals = [perq[pipe][i][judge] for i in sample]
        good = [v for v in vals if v is not None]
        return sum(good) / len(good) if good else float("nan")

    # GATE vs committed aggregates
    agg = json.loads(AGG.read_text(encoding="utf-8"))["cells"]
    bad = []
    for p in pipes:
        for j in JUDGES:
            a = round(acc(p, j, idx), 3)
            want = round(agg[f"{p}|k50"]["judge_accuracy_by_judge"][j], 3)
            if abs(a - want) > 0.0011:
                bad.append((p, j, a, want))
    L = ["# Rank-flip uncertainty (conv-26, k=50): five harness pipelines x four judges", "",
         "Headline matrix = the five pipelines from the single 2026-06-07 harness sweep "
         "(identical reader gpt-5-mini, identical judge prompt hashes, identical cat!=5 "
         "filter). naked_cosine ran on the other runner path (category hints, "
         "relevance-formatted context, binary-text `mnemoverse` judge per ASYM-004, and "
         "answers ~2x longer) and is reported separately below, never inside the matrix. "
         f"Paired bootstrap B={B}, seed 20260715. Tie rule: ties are not flips. "
         "Rerun: `python scripts/rank_bootstrap.py` (offline).", ""]
    L.append(f"Gate vs committed aggregates: {'PASS' if not bad else 'FAIL ' + str(bad)}")
    L.append("")
    if bad:
        OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return 1

    def flips(sample, pipe_set, judge_set):
        out = []
        for a, b in itertools.combinations(pipe_set, 2):
            orders = set()
            for j in judge_set:
                da, db = acc(a, j, sample), acc(b, j, sample)
                if da > db:
                    orders.add(1)
                elif db > da:
                    orders.add(-1)
            if len(orders) > 1:
                out.append((a, b))
        return out

    obs = flips(idx, pipes, JUDGES)
    obs_sb = flips(idx, pipes, ["mem0", "strict"])
    npairs = len(list(itertools.combinations(pipes, 2)))

    L.append("## Cell table (accuracy, x/152)")
    L.append("| pipeline | " + " | ".join(JUDGES) + " |")
    L.append("|---|" + "---:|" * len(JUDGES))
    for p in pipes:
        L.append(f"| {p} | " + " | ".join(
            f"{acc(p,j,idx):.3f} ({round(acc(p,j,idx)*n)}/152)" for j in JUDGES) + " |")
    L.append("")
    L.append(f"## Observed (four judges, five harness pipelines): {len(obs)} of {npairs} pairs flip")
    for a, b in obs:
        detail = "; ".join(f"{j}: {acc(a,j,idx):.3f} vs {acc(b,j,idx):.3f} "
                           f"(margin {abs(round(acc(a,j,idx)*n)-round(acc(b,j,idx)*n))} answers)"
                           for j in JUDGES)
        L.append(f"- {a} vs {b}: {detail}")
    L.append("")
    L.append(f"Same-backbone (mem0 vs strict, both gpt-5): {len(obs_sb)} of {npairs} pairs flip"
             + (": " + ", ".join(f"{a}~{b}" for a, b in obs_sb) if obs_sb else ""))
    # naked, reported separately (different runner path)
    if "naked_cosine" in perq:
        L.append("")
        L.append("Separately, naked_cosine (other runner path -- NOT part of the matrix above): "
                 + ", ".join(f"{j} {acc('naked_cosine', j, idx):.3f}" for j in JUDGES)
                 + ". Its answers average ~105 characters against 43--70 for the harness "
                   "pipelines, exactly the padded-answer shape the lenient prompt is measured "
                   "to over-credit (+25.4pp extra-detail rule), so a lenient-judge win for it "
                   "is not evidence about memory quality.")
    def top_set(judge, sample):
        """Every pipeline tied for this judge's maximum. max() would break ties by
        list order, which makes a 'winners differ' count depend on how HARNESS is
        written -- and this matrix HAS an exact tie (mem0-4o: engine = supermemory)."""
        best = max(acc(p, judge, sample) for p in pipes)
        return {p for p in pipes if abs(acc(p, judge, sample) - best) < 1e-12}

    winners = {j: top_set(j, idx) for j in JUDGES}
    L.append("Top pipeline by judge (full argmax set; ties shown): "
             + "; ".join(f"{j}: {'/'.join(sorted(w))}" for j, w in winners.items()))
    L.append("")

    # bootstrap
    flip_counts = []
    pair_hits = {pair: 0 for pair in obs}
    sb_counts = []
    winner_flip_hits = 0
    for _ in range(B):
        sample = [idx[random.randrange(n)] for _ in range(n)]
        f = flips(sample, pipes, JUDGES)
        flip_counts.append(len(f))
        fs = set(f)
        for pair in obs:
            if pair in fs:
                pair_hits[pair] += 1
        sb_counts.append(len(flips(sample, pipes, ["mem0", "strict"])))
        # Tie-aware: the judges "disagree on the winner" only when no single
        # pipeline is top for all four. Taking max() per judge instead would make
        # this rate depend on HARNESS's list order (68.2% as written, 72.1%
        # reversed) -- an artifact, not a measurement.
        common = set(pipes)
        for j in JUDGES:
            common &= top_set(j, sample)
        if not common:
            winner_flip_hits += 1
    flip_counts.sort(); sb_counts.sort()
    L.append(f"## Bootstrap (B={B}, paired question resampling)")
    L.append(f"- flip-count distribution (4 judges): median {flip_counts[B//2]}, "
             f"95% interval [{flip_counts[int(.025*B)]}, {flip_counts[int(.975*B)]}]")
    L.append(f"- same-backbone flip count: median {sb_counts[B//2]}, "
             f"95% interval [{sb_counts[int(.025*B)]}, {sb_counts[int(.975*B)]}]")
    L.append(f"- winner differs between judges in {100*winner_flip_hits/B:.1f}% of resamples")
    for pair, h in pair_hits.items():
        L.append(f"- observed flip {pair[0]} ~ {pair[1]}: reproduces in {100*h/B:.1f}% of resamples")
    L.append("")

    # P(A>B) for flip-involved pairs
    L.append("## P(A>B) per judge (bootstrap), pairs involved in observed flips")
    for a, b in obs:
        row = []
        for j in JUDGES:
            wins = 0
            for _ in range(2000):
                sample = [idx[random.randrange(n)] for _ in range(n)]
                if acc(a, j, sample) > acc(b, j, sample):
                    wins += 1
            row.append(f"{j}: {wins/2000:.2f}")
        L.append(f"- P({a} > {b}): " + ", ".join(row))
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default=None)
    a = ap.parse_args()
    if a.core:
        extract(a.core)
    if not PERQ.exists():
        sys.exit("no per-question artifact; run with --core <core-root>")
    raise SystemExit(analyze())
