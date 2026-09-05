"""SUPERSEDED -- not cited by the paper; kept for provenance only. DO NOT paste its caption.

WHY: this figure plots six pipelines, but naked_cosine ran on a different runner path
from the other five (answers ~105 chars against 43-70), and its `mnemoverse` column uses
the binary-text prompt rather than the harness JSON prompt (core ASYM-004). Its "rank
instability is real but modest" reading is the framing the paper WITHDREW: the
five-pipeline paired bootstrap (scripts/rank_bootstrap.py) finds 2 of 10 pairs flip with
a 95% interval of [0, 4] -- includes zero, so the rank-reversal claim is reported only as
a scoped observation. The old caption also cited ASYM-023 (zep effective k=30), which is
FALSE for these cells: zep returned 50 atoms per query in this sweep. The paper includes
no rank figure; the matrix is reported in text and in Table 3.

Its input artifact (scripts/figdata/system_by_judge_matrix.json) and its rendered outputs
were removed for the same reason -- a rendered PDF asserts the withdrawn ranking visually,
where no banner can reach a reader. This file no longer runs; it is a record of what was
tried.
"""
import json
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
HERE = pathlib.Path(__file__).parent
DATA = HERE / "figdata" / "system_by_judge_matrix.json"
OUT_DIR = HERE.parent / "figures"
OUT_DIR.mkdir(exist_ok=True)
OUT_PDF = OUT_DIR / "judge_ranking_instability.pdf"
OUT_PNG = OUT_DIR / "judge_ranking_instability.png"

# ── data ───────────────────────────────────────────────────────────────────
with open(DATA) as f:
    d = json.load(f)

# Build score dict  {system: {judge: score}}
scores = {}
for row in d["rows"]:
    scores[row["system"]] = row["judge_accuracy"]

# Display labels (shorter, publication-friendly)
sys_labels = {
    "naked_cosine":      "naked\ncosine",
    "supermemory":       "super-\nmemory",
    "mnemoverse_engine": "mnemo-\nverse\nengine",
    "mnemoverse_http":   "mnemo-\nverse\nhttp",
    "mem0_v3_cloud":     "mem0\nv3",
    "zep":               "zep",
}

judge_labels = {
    "mem0-4o":    "mem0-4o\n(lenient, gpt-4o)",
    "mem0":       "mem0\n(lenient, gpt-5)",
    "mnemoverse": "mnemoverse\n(binary, gpt-5-mini)",
    "strict":     "strict\n(strict, gpt-5)",
}

# Order: systems by mem0-4o score desc
judge_order = ["mem0-4o", "mem0", "mnemoverse", "strict"]
sys_order = sorted(scores.keys(), key=lambda s: scores[s]["mem0-4o"], reverse=True)

# Build matrix [n_judges x n_sys]
n_j = len(judge_order)
n_s = len(sys_order)
mat = np.zeros((n_j, n_s))
for ji, j in enumerate(judge_order):
    for si, s in enumerate(sys_order):
        mat[ji, si] = scores[s][j]

# ── style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8.5,
    "axes.linewidth": 0.7,
    "figure.dpi": 150,
})

fig, ax = plt.subplots(figsize=(6.5, 2.6))

# Grayscale colormap, reversed so high score = light, low = dark
# (white = best, dark = worst) — intentionally "neutral" direction so
# no system looks like a winner by colour.
cmap = matplotlib.colormaps["gray_r"]  # dark = low, light = high
im = ax.imshow(mat, cmap=cmap, vmin=0.10, vmax=1.0, aspect="auto")

# Annotate cells with score values
for ji in range(n_j):
    for si in range(n_s):
        val = mat[ji, si]
        # Use white text on dark cells, black on light
        text_color = "white" if val < 0.55 else "black"
        ax.text(si, ji, f"{val:.2f}", ha="center", va="center",
                fontsize=7.5, color=text_color, fontweight="normal")

# Axes labels
ax.set_xticks(range(n_s))
ax.set_xticklabels([sys_labels[s] for s in sys_order],
                   fontsize=7.5, linespacing=1.2)
ax.set_yticks(range(n_j))
ax.set_yticklabels([judge_labels[j] for j in judge_order],
                   fontsize=7.5, linespacing=1.2)

ax.set_title(
    "Accuracy of the same answer set under four judges\n"
    "(columns sorted by most lenient judge, mem0-4o)",
    fontsize=8.5, pad=6,
)

# Add a thin rank-order annotation above the cells
for si, s in enumerate(sys_order):
    # Rank under strict judge
    strict_rank = sorted(sys_order, key=lambda x: scores[x]["strict"], reverse=True).index(s) + 1
    # Rank under mnemoverse judge
    mnem_rank = sorted(sys_order, key=lambda x: scores[x]["mnemoverse"], reverse=True).index(s) + 1
    # Mark systems that swap rank vs mem0-4o (rank 1 = leftmost)
    mem4o_rank = si + 1  # already sorted by mem0-4o
    if strict_rank != mem4o_rank:
        ax.text(si, -0.7, f"→{strict_rank}", ha="center", va="bottom",
                fontsize=6, color="#888888", style="italic")

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label("Accuracy", fontsize=7.5)
cbar.ax.tick_params(labelsize=7)

# Annotation: prompt swap vs model swap arrow
# Draw a bracket-style note pointing at the strict row
ax.annotate(
    "42 pp prompt-swap\n(same gpt-5, mem0→strict)",
    xy=(0, 3), xytext=(1.5, 3.55),
    fontsize=6.5, color="#333333",
    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.7),
    ha="center",
)

fig.tight_layout(pad=0.6)
fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=200)
print(f"Saved: {OUT_PDF}")
print(f"Saved: {OUT_PNG}")
