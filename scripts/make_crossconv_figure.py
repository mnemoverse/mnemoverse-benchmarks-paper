"""Figure -- mem0->strict judge swing per LoCoMo conversation, on MEM0'S OWN answers.
Reads experiments/hardening/summary.json (produced by kit/scripts/run_experiments.py).
Shows the ~40-point swing is not specific to conv-26: it holds in every conversation.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPER = Path(__file__).resolve().parents[1]
summary = json.loads((PAPER / "experiments/hardening/summary.json").read_text(encoding="utf-8"))
B = summary["B_cross_conversation"]
rows = sorted(B["per_conversation"], key=lambda r: -r["swing_pp"])
labels = [r["conv"].replace("conv", "c") for r in rows]
swings = [r["swing_pp"] for r in rows]
mean = B["swing_mean_pp"]

fig, ax = plt.subplots(figsize=(6.2, 3.2))
ax.bar(range(len(rows)), swings, color="0.30", width=0.66)
ax.axhline(mean, color="black", lw=1.0, ls="--")
ax.text(len(rows) - 0.4, mean + 0.8, f"mean {mean:.1f} pp", ha="right", va="bottom", fontsize=8)
ax.set_xticks(range(len(rows)))
ax.set_xticklabels([f"{l}\n(n={r['n']})" for l, r in zip(labels, rows)], fontsize=7.5)
ax.set_ylabel("mem0$\\to$strict swing (pp)")
ax.set_title("Judge-prompt swing on Mem0's own answers, per LoCoMo conversation", fontsize=9)
ax.set_ylim(0, max(swings) * 1.15)
for i, s in enumerate(swings):
    ax.text(i, s + 0.5, f"{s:.0f}", ha="center", va="bottom", fontsize=7)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.tight_layout()
out = PAPER / "figures"
fig.savefig(out / "crossconv_swing.pdf")
fig.savefig(out / "crossconv_swing.png", dpi=140)
print(f"saved crossconv_swing.pdf  (min {B['swing_min_pp']} / mean {mean} / max {B['swing_max_pp']} pp across {B['n_conversations']} convs)")
