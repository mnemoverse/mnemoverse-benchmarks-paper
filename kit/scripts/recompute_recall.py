"""Standalone recall recompute — bit-for-bit from kit files only.

Recomputes naked-cosine recall@k for LoCoMo conv-26 from the two kit data files:
  - kit/data/naked_cosine_conv26_retrieved.json  (per-question top-200 retrieved IDs)
  - kit/data/locomo_gold_ids.json                (gold evidence IDs, no question text)

No dependency on mnemoverse-core or any private repository.

Usage (run from the repo root or any directory):
    python kit/scripts/recompute_recall.py

Expected output:
    k=  5: 0.595000   MATCH
    k= 10: 0.720556   MATCH
    k= 20: 0.780000   MATCH
    k= 50: 0.885556   MATCH
    k=100: 0.938333   MATCH
    k=200: 0.980556   MATCH
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]   # .../kit/
DATA = KIT / "data"

KS = [5, 10, 20, 50, 100, 200]

# Published overall recall@k values (from RECALL_AT_K_SUMMARY.json, cell_0b)
EXPECTED = {5: 0.595, 10: 0.720556, 20: 0.780, 50: 0.885556, 100: 0.938333, 200: 0.980556}

# note: verify_claims.py uses 3-digit rounded strings; we use exact 6-digit here.


def strip_prefix(atom_id: str) -> str:
    """'conv-26::D1:3' -> 'D1:3'."""
    return atom_id.split("::", 1)[1] if "::" in atom_id else atom_id


def load_gold(gold_path: Path) -> dict[str, dict]:
    """Build qid -> {evidence_ids: set, category: str} for all conversations."""
    data = json.loads(gold_path.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for conv in data.get("conversations", []):
        sample_id = conv.get("sample_id", "")
        for q in conv.get("questions", []):
            qid = f"{sample_id}::q{q['q_idx']}"
            index[qid] = {
                "evidence_ids": set(q.get("evidence", [])),
                "category": q.get("category", ""),
            }
    return index


def compute_recall(records: list[dict], gold: dict[str, dict]) -> dict:
    """Compute recall@k from retrieved ids + gold.  Adversarial questions excluded."""
    overall: dict[int, list[float]] = {k: [] for k in KS}
    by_cat: dict[str, dict[int, list[float]]] = defaultdict(lambda: {k: [] for k in KS})

    for r in records:
        qid = r["qid"]
        info = gold.get(qid)
        if not info:
            continue
        evidence = info["evidence_ids"]
        if not evidence:
            continue
        cat = info["category"]
        if cat == "adversarial":
            continue
        stripped = [strip_prefix(a) for a in r["retrieved_atom_ids"]]
        for k in KS:
            topk = set(stripped[:k])
            recall = len(evidence & topk) / len(evidence)
            overall[k].append(recall)
            by_cat[cat][k].append(recall)

    return {
        "overall_recall_at_k": {k: round(sum(v) / len(v), 6) if v else 0.0 for k, v in overall.items()},
        "by_category_recall_at_k": {
            cat: {
                "n": len(per_k[KS[0]]),
                "recall_at_k": {k: round(sum(v) / len(v), 6) if v else 0.0 for k, v in per_k.items()},
            }
            for cat, per_k in by_cat.items()
        },
        "n_questions_evaluated": sum(len(v) for v in list(overall.values())[:1]),
    }


def main() -> int:
    gold_path = DATA / "locomo_gold_ids.json"
    retrieved_path = DATA / "naked_cosine_conv26_retrieved.json"

    if not gold_path.exists():
        print(f"ERROR: {gold_path} not found")
        return 1
    if not retrieved_path.exists():
        print(f"ERROR: {retrieved_path} not found")
        return 1

    gold = load_gold(gold_path)
    data = json.loads(retrieved_path.read_text(encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data

    result = compute_recall(records, gold)
    overall = result["overall_recall_at_k"]
    by_cat = result["by_category_recall_at_k"]

    print(f"Standalone recall recompute — {result['n_questions_evaluated']} questions evaluated (adversarial excluded)\n")
    print(f"{'k':>5}  {'computed':>10}  {'expected':>10}  match")
    print("-" * 42)

    all_ok = True
    for k in KS:
        comp = overall.get(k, None)
        exp = EXPECTED.get(k)
        if comp is None:
            print(f"{k:>5}  {'N/A':>10}  {exp:>10.6f}  MISSING")
            all_ok = False
            continue
        match = abs(comp - exp) < 1e-5
        if not match:
            all_ok = False
        print(f"{k:>5}  {comp:>10.6f}  {exp:>10.6f}  {'MATCH' if match else f'DIFF delta={abs(comp-exp):.6f}'}")

    print("\nPer-category recall@k=200:")
    for cat in sorted(by_cat.keys()):
        n = by_cat[cat]["n"]
        v = by_cat[cat]["recall_at_k"].get(200, 0.0)
        print(f"  {cat:<12} n={n:>3}  recall@200={v:.6f}")

    print()
    print(f"{'PASS — all recall@k values reproduced exactly' if all_ok else 'FAIL — discrepancy detected (see above)'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
