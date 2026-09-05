"""Figure 1 -- naked-cosine recall@k on LoCoMo conv-26 (n=152).
Naked only: compute_recall.py certifies naked recall 'exact' but flags the learned
engine's recall 'n_a' (consolidated atoms lack a 1:1 gold-id map), so we anchor on
the naked floor and do not plot an engine-vs-naked delta. Numbers verified from
kit/data/RECALL_AT_K_SUMMARY.json."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

k = [5, 10, 20, 50, 100, 200]
overall = [0.595, 0.721, 0.780, 0.886, 0.938, 0.981]
multihop = [0.242, 0.424, 0.531, 0.714, 0.846, 0.951]

fig, ax = plt.subplots(figsize=(5.4, 3.4))
ax.plot(k, overall, "o-", color="black", lw=1.4, label="naked cosine, overall")
ax.plot(k, multihop, "s--", color="0.45", lw=1.4, label="naked cosine, multi-hop")
ax.axhline(1.0, color="0.8", lw=0.6, ls=":")
ax.set_xscale("log")
ax.set_xticks(k); ax.set_xticklabels(k)
ax.set_xlabel(r"retrieval depth $k$ (log scale)")
ax.set_ylabel(r"recall@$k$")
ax.set_ylim(0, 1.03)
ax.annotate("0.98, not 1.0:\n$k\\,{=}\\,200$ is a real cutoff", xy=(200, 0.981),
            xytext=(34, 0.60), fontsize=7.5, color="0.30",
            arrowprops=dict(arrowstyle="->", color="0.55", lw=0.6))
ax.annotate("multi-hop 0.24 at $k\\,{=}\\,5$:\nretrieval unsolved at deployment depth",
            xy=(5, 0.242), xytext=(5.4, 0.04), fontsize=7.5, color="0.30")
ax.legend(fontsize=8, frameon=False, loc="lower right")
ax.grid(True, which="both", axis="y", color="0.93", lw=0.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
out = Path(__file__).parent.parent / "figures"
fig.savefig(out / "recall_k_curve.pdf")
fig.savefig(out / "recall_k_curve.png", dpi=140)
print("saved", out / "recall_k_curve.pdf")
