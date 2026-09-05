# NOTE (kit excerpt): This script is excerpted from
# experiments/benchmarks/_harness/compute_recall.py in the mnemoverse-core
# repository for reference. It has two internal dependencies that will not
# resolve in a standalone environment:
#   1. The sys.path insert at line ~32 assumes the script lives four
#      directories deep inside the repo (parents[3] points to the repo root).
#   2. The deferred imports of `experiments.benchmarks._harness.normalize_cell`
#      (functions `_infer_benchmark_scope` and `_infer_system`) are used only
#      in `find_normalized_path()` and the summary-print block of `main()`.
#      Remove or stub those imports if running this script outside the repo.
# The core logic (`load_locomo_evidence`, `compute_recall_for_cell`,
# `RECALL_PROVENANCE`, `strip_sample_prefix`) is self-contained and
# does not require the internal modules.

"""Compute recall@k from evidence_dia_ids vs retrieved_atom_ids.

LoCoMo gold labels: each qa item has `evidence: ["D1:3", "D2:12", ...]` (dialogue:turn IDs).
Our retrieved_atom_ids: ["conv-26::D1:3", "conv-26::D2:12", ...] (sample_id::dia_id).

For each cell:
- For each question, intersect evidence with first-k retrieved atom IDs (modulo sample prefix)
- recall@k = |intersection| / |evidence|
- aggregate: mean across questions, per-category breakdown

This is the JUDGE-FREE primary metric per MATRIX_DASHBOARD_BRIEF.md §3.3 (`recall_at_k`).
Updates normalized cells in-place with the recall_at_k field.

Usage:
  python compute_recall.py --dataset experiments/data/locomo10.json \\
                            --cells-dir experiments/benchmarks/matrix/cells \\
                            [--also-process-raw experiments/results/night-runs/]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# Add repo root to sys.path so the sibling normalize_cell module is importable
# whether the script is launched from anywhere (CLI, IDE, CI).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

LOCOMO_CATEGORY_MAP = {
    1: "multi_hop",
    2: "temporal",
    3: "open_domain",
    4: "single_hop",
    5: "adversarial",
}


def load_locomo_evidence(dataset_path: Path) -> dict[str, dict]:
    """Build qid -> {evidence: set(dia_ids), category_name, n_evidence} for LoCoMo."""
    with dataset_path.open("r", encoding="utf-8") as f:
        locomo = json.load(f)
    qid_info: dict[str, dict] = {}
    for conv in locomo:
        sample_id = conv.get("sample_id", "")
        for q_idx, qa in enumerate(conv.get("qa", [])):
            qid = f"{sample_id}::q{q_idx}"
            evidence = qa.get("evidence", [])
            cat_int = qa.get("category", 0)
            qid_info[qid] = {
                "evidence_ids": set(evidence),  # ["D1:3", ...]
                "category_name": LOCOMO_CATEGORY_MAP.get(cat_int, "unknown"),
                "n_evidence": len(evidence),
            }
    return qid_info


def strip_sample_prefix(atom_id: str) -> str:
    """Convert 'conv-26::D1:3' -> 'D1:3'. If no '::' present, return as-is."""
    return atom_id.split("::", 1)[1] if "::" in atom_id else atom_id


def compute_recall_for_cell(
    raw_cell_path: Path,
    qid_info: dict[str, dict],
    ks: list[int] | None = None,
) -> dict:
    """Compute recall@k for a raw runner cell JSON.

    Returns:
      {
        "overall_recall_at_k": {k: float},
        "by_category_recall_at_k": {category: {k: float}},
        "n_questions": int,
        "n_questions_with_evidence": int,
      }
    """
    with raw_cell_path.open("r", encoding="utf-8") as f:
        cell = json.load(f)

    cfg = cell.get("config", {})
    cell_k_raw = cfg.get("top_k") or cfg.get("k") or 0
    try:
        cell_k = int(cell_k_raw)
    except (TypeError, ValueError):
        cell_k = 0
    if cell_k <= 0:
        raise ValueError(
            f"compute_recall_for_cell: cell {raw_cell_path.name} has invalid k "
            f"(top_k={cfg.get('top_k')!r}, k={cfg.get('k')!r}). Recall@k requires k > 0."
        )
    if ks is None:
        # By default compute recall at the cell's own k, plus standard breakpoints below it
        ks = sorted(set([cell_k] + [k for k in (5, 10, 20, 50, 100, 200) if k <= cell_k]))

    results = cell.get("results", [])
    overall_per_k: dict[int, list[float]] = {k: [] for k in ks}
    by_cat_per_k: dict[str, dict[int, list[float]]] = defaultdict(lambda: {k: [] for k in ks})
    n_with_evidence_eval = 0
    n_with_placeholder = 0

    for r in results:
        qid = r.get("qid", "")
        info = qid_info.get(qid)
        if not info:
            continue
        evidence = info["evidence_ids"]
        if not evidence:
            continue
        cat = info["category_name"]
        # Adversarial questions are excluded from BOTH per-category recall AND
        # the count of evaluable questions. Counting them in n_with_evidence
        # would inflate the reported denominator vs. what was actually scored.
        if cat == "adversarial":
            continue
        n_with_evidence_eval += 1

        retrieved = r.get("retrieved_atom_ids", [])
        stripped_retrieved = [strip_sample_prefix(a) for a in retrieved]
        # Surface engine "?" placeholder atoms (engine emits them as padding
        # when its strategy returns fewer than top_k real atoms). They deflate
        # recall vs. naked-cosine artifactually, see RECALL_VS_JUDGE_ANALYSIS.md.
        if any(a == "?" for a in stripped_retrieved):
            n_with_placeholder += 1

        for k in ks:
            top_k_set = set(stripped_retrieved[:k])
            hits = len(evidence & top_k_set)
            recall = hits / len(evidence)
            overall_per_k[k].append(recall)
            by_cat_per_k[cat][k].append(recall)

    overall = {k: round(sum(v) / len(v), 6) if v else 0.0 for k, v in overall_per_k.items()}
    by_cat = {
        cat: {
            "n": len(per_k[ks[0]]),
            "recall_at_k": {k: round(sum(v) / len(v), 6) if v else 0.0 for k, v in per_k.items()},
        }
        for cat, per_k in by_cat_per_k.items()
    }

    return {
        "overall_recall_at_k": overall,
        "by_category_recall_at_k": by_cat,
        "n_questions": len(results),
        "n_questions_with_evidence_eval": n_with_evidence_eval,
        "n_questions_with_placeholder_retrieval": n_with_placeholder,
        "ks_computed": ks,
        "cell_native_k": cell_k,
    }


def _atomic_write_json(path: Path, payload: dict, *, indent: int = 2) -> None:
    """Write JSON via temp file + os.replace so a Ctrl-C / OOM mid-write does
    not corrupt the destination. Mandatory for load-bearing artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


# recall provenance by system (executor-plan ask #3, 2026-06-12): recall is
# NOT one metric across systems — naked stores turns 1:1 (exact); the http
# adapter maps atoms back to turns but consolidation products have no dia
# mapping (lower bound); text-only competitor adapters return rewritten
# snippets (not computable). Consumers MUST render n_a as "n/a", never 0.
RECALL_PROVENANCE = {
    "naked_cosine": "exact",
    "mnemoverse_http": "lower_bound",
    "mnemoverse": "n_a",
    "mnemoverse_engine": "n_a",
    "mem0_v3_cloud": "n_a",
    "mem0_v2_oss": "n_a",
    "supermemory": "n_a",
    "zep": "n_a",
    "letta": "n_a",
    "qdrant": "n_a",
}


def update_normalized_cell(normalized_path: Path, recall_data: dict) -> None:
    """Add recall_at_k + recall_provenance to a normalized cell. Atomic."""
    with normalized_path.open("r", encoding="utf-8") as f:
        cell = json.load(f)
    agg = cell.setdefault("aggregates", {})
    agg["recall_at_k"] = recall_data
    system = cell.get("system", "")
    if system not in RECALL_PROVENANCE:
        raise ValueError(
            f"update_normalized_cell: unknown system {system!r} for recall "
            "provenance — add it to RECALL_PROVENANCE explicitly (fail-on-"
            "unknown is the contract; silent defaults would mislabel data)."
        )
    agg["recall_provenance"] = RECALL_PROVENANCE[system]
    _atomic_write_json(normalized_path, cell)


def find_normalized_path(raw_path: Path, normalized_dir: Path) -> Path | None:
    """Map raw cell path to its normalized counterpart by config inspection.

    Mirrors normalize_cell.py's `_infer_benchmark_scope` filename heuristic so
    naked cells (which lack cfg.conv_id) still resolve to the conv26_* scope
    when their raw filename carries the conv label. Without this mirror,
    recall data silently never lands on naked cells.

    System inference is delegated to normalize_cell._infer_system so future
    competitor cells (mem0_v2_oss / supermemory / letta / zep / qdrant)
    resolve to their own normalized filenames rather than being silently
    misclassified as naked_cosine.
    """
    # Defer the import so this module stays runnable without the harness
    # entrypoint loading dotenv / sys.path side effects.
    from experiments.benchmarks._harness.normalize_cell import (
        _infer_benchmark_scope,
        _infer_system,
    )

    with raw_path.open("r", encoding="utf-8") as f:
        cell = json.load(f)
    cfg = cell.get("config", {})
    k = cfg.get("top_k") or cfg.get("k") or 0
    n = cell.get("n_questions", 0)

    try:
        system = _infer_system(cfg, raw_path)
    except ValueError:
        # Same fail-soft as the rest of compute_recall's batch loop —
        # caller's print path will note the cell was not back-written.
        return None
    # DELEGATE scope inference — this used to be a hand-mirrored copy of
    # normalize_cell's heuristic, and it drifted exactly as mirrors do:
    # PR #313 generalized conv-N in normalize_cell while this copy stayed
    # conv-26-only, so every conv-47 cell silently lost its recall
    # back-write (recall_at_k stayed None on all 27 v2 cells).
    bench, scope, _ = _infer_benchmark_scope(cfg, n, raw_path=raw_path)

    target = f"cell_{system}_{bench}_{scope}_k{k}.json"
    candidate = normalized_dir / target
    return candidate if candidate.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="experiments/data/locomo10.json")
    parser.add_argument(
        "--cells-dir",
        default="experiments/benchmarks/matrix/cells",
        help="Directory of normalized cells to update with recall@k",
    )
    parser.add_argument(
        "--raw-dir",
        default="experiments/results/night-runs",
        help="Directory of raw runner JSONs to compute recall from",
    )
    parser.add_argument(
        "--summary-out",
        default=None,
        help="Path to write RECALL_AT_K_SUMMARY.json (default: <raw-dir>/RECALL_AT_K_SUMMARY.json)",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    qid_info = load_locomo_evidence(dataset_path)
    print(f"Loaded {len(qid_info)} qid → evidence mappings")

    raw_dir = Path(args.raw_dir)
    normalized_dir = Path(args.cells_dir)
    raw_files = sorted(raw_dir.glob("cell_*_locomo*.json"))
    if not raw_files:
        print(f"No raw cell files at {raw_dir}", file=sys.stderr)
        return 1

    print(f"\n{'cell':50} {'sys':18} {'k':>4} {'n':>4} {'recall@cell_k':>14}")
    print("-" * 100)
    summary = []
    for raw_path in raw_files:
        try:
            recall_data = compute_recall_for_cell(raw_path, qid_info)
        except Exception as e:
            print(f"FAIL {raw_path.name}: {e}", file=sys.stderr)
            continue

        normalized_path = find_normalized_path(raw_path, normalized_dir)
        if normalized_path:
            update_normalized_cell(normalized_path, recall_data)
        else:
            # SURFACE the back-write miss instead of swallowing it. Without
            # this, competitor cells (mem0_v2_oss / supermemory / letta /
            # zep / qdrant) silently fail to receive their recall data and
            # the dashboard renders "—" for recall on those rows forever.
            print(
                f"WARN: no normalized cell found for {raw_path.name} — "
                f"recall data NOT written. Make sure normalize_cell.py was "
                f"run first against the same raw cell.",
                file=sys.stderr,
            )

        # Print compact summary
        with raw_path.open("r", encoding="utf-8") as f:
            c = json.load(f)
        cfg = c.get("config", {})
        # Delegate to normalize_cell._infer_system so future competitor cells
        # (mem0_v2_oss / supermemory / letta / zep / qdrant) are labelled
        # correctly in RECALL_AT_K_SUMMARY.json, not all bucketed as 'naked'.
        try:
            from experiments.benchmarks._harness.normalize_cell import _infer_system

            sys_name = _infer_system(cfg, raw_path)
        except (ValueError, ImportError):
            sys_name = "engine" if cfg.get("engine") == "mnemoverse" else "naked"
        k = recall_data["cell_native_k"]
        recall_at_native = recall_data["overall_recall_at_k"].get(k, 0.0)
        print(
            f"{raw_path.name:50} {sys_name:18} {k:>4} {recall_data['n_questions']:>4} {recall_at_native:>14.4f}"
        )
        summary.append(
            {
                "cell": raw_path.name,
                "system": sys_name,
                "k": k,
                "n": recall_data["n_questions"],
                "recall_at_native_k": recall_at_native,
                "overall_recall_at_k": recall_data["overall_recall_at_k"],
                "by_category_recall_at_k": recall_data["by_category_recall_at_k"],
                "normalized_updated": normalized_path is not None,
            }
        )

    n_missing = sum(1 for s in summary if not s["normalized_updated"])
    if n_missing:
        print(
            f"\nWARN: {n_missing} of {len(summary)} cells did not get a "
            f"recall back-write (no normalized counterpart found).",
            file=sys.stderr,
        )

    out_path = Path(args.summary_out) if args.summary_out else raw_dir / "RECALL_AT_K_SUMMARY.json"
    _atomic_write_json(out_path, summary)
    print(f"\nSaved summary to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
