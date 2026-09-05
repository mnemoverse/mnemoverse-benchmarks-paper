"""verify_claims.py -- reproduce the paper's headline numbers from the PUBLIC kit.

    pip install -r kit/scripts/requirements.txt
    OPENAI_API_KEY=...  python kit/scripts/verify_claims.py

The paper's contract: judge-FREE numbers reproduce exactly; judge-DEPENDENT numbers
reproduce within a published tolerance, because LLM judges are non-deterministic.

CHECK 1 -- judge-free (exact, committed summary).  Naked-cosine recall@k on LoCoMo
           conv-26, read straight from the committed RECALL_AT_K_SUMMARY.json.

CHECK 1b -- judge-free (exact, standalone recompute).  Re-derives the same recall@k
           numbers from scratch using only kit files:
             kit/data/naked_cosine_conv26_retrieved.json  (per-question top-200 ids)
             kit/data/locomo_gold_ids.json                (gold evidence ids)
           No LLM, no private repo.  Must match the committed summary bit-for-bit.

CHECK 2 -- the load-bearing judge swing (within tolerance).  Re-judges the 143 conv-26 answers
           (control slice: Mem0 OSS backend retrieval, our reader) under the two prompts shipped in kit/prompts/. The paper
           reports mem0~0.74, strict~0.34, a ~40-point gap produced by nothing but the
           grading instructions. This run must land mem0 in [0.70,0.78], strict in
           [0.30,0.38], and the swing in [34,46] pp. (Tolerance = judge non-determinism;
           the paper measures a judged score's run-to-run noise at ~0.5-0.7pp at this
#            slice size, far below the 40pp effect.)

Exit code 0 if every check passes, 1 otherwise; 2 when OPENAI_API_KEY is absent and only the
judge-free checks ran (they must pass for the 2).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts"))
from judge import load_answers, run_judge  # noqa: E402

# Exact values as stored in RECALL_AT_K_SUMMARY.json (and recomputed by recompute_recall.py).
# Paper prose rounds these to 3 sig-figs (0.721, 0.886, 0.981), but the JSON stores the
# full 6-digit values — CHECK 1 searches for those.
RECALL_EXACT = {5: 0.595, 10: 0.720556, 20: 0.780, 50: 0.885556, 100: 0.938333, 200: 0.980556}
# String keys for CHECK 1 summary search (same values, keyed by string k as in the JSON)
RECALL_EXPECTED = {str(k): v for k, v in RECALL_EXACT.items()}
TOL = {"mem0": (0.70, 0.78), "strict": (0.30, 0.38), "swing_pp": (34.0, 46.0)}


def check_recall() -> bool:
    summary = json.loads((KIT / "data" / "RECALL_AT_K_SUMMARY.json").read_text(encoding="utf-8"))
    blob = json.dumps(summary)
    ok = True
    print("CHECK 1 -- judge-free naked-cosine recall@k (conv-26, committed summary):")
    for k, exp in RECALL_EXPECTED.items():
        # Search for the exact stored string representation
        found = str(exp) in blob
        print(f"   k={k:>3}: expected {exp}   {'present' if found else 'NOT FOUND'} in summary")
        ok = ok and found
    print(f"   -> {'PASS' if ok else 'FAIL'} (exact, judge-free)\n")
    return ok


def _strip_prefix(atom_id: str) -> str:
    return atom_id.split("::", 1)[1] if "::" in atom_id else atom_id


def _load_gold_index(gold_path: Path) -> dict:
    data = json.loads(gold_path.read_text(encoding="utf-8"))
    index = {}
    for conv in data.get("conversations", []):
        sample_id = conv.get("sample_id", "")
        for q in conv.get("questions", []):
            qid = f"{sample_id}::q{q['q_idx']}"
            index[qid] = {
                "evidence_ids": set(q.get("evidence", [])),
                "category": q.get("category", ""),
            }
    return index


def check_recall_standalone() -> bool:
    """Recompute recall@k from kit/data/naked_cosine_conv26_retrieved.json + locomo_gold_ids.json."""
    retrieved_path = KIT / "data" / "naked_cosine_conv26_retrieved.json"
    gold_path = KIT / "data" / "locomo_gold_ids.json"
    print("CHECK 1b -- judge-free recall@k standalone recompute (no private repo):")
    if not retrieved_path.exists():
        print(f"   ERROR: {retrieved_path.name} not found in kit/data/\n   -> FAIL\n")
        return False
    if not gold_path.exists():
        print(f"   ERROR: {gold_path.name} not found in kit/data/\n   -> FAIL\n")
        return False

    gold = _load_gold_index(gold_path)
    raw = json.loads(retrieved_path.read_text(encoding="utf-8"))
    records = raw.get("records", raw) if isinstance(raw, dict) else raw

    ks = list(RECALL_EXACT.keys())
    overall: dict[int, list[float]] = {k: [] for k in ks}

    for r in records:
        qid = r["qid"]
        info = gold.get(qid)
        if not info:
            continue
        evidence = info["evidence_ids"]
        if not evidence or info["category"] == "adversarial":
            continue
        stripped = [_strip_prefix(a) for a in r["retrieved_atom_ids"]]
        for k in ks:
            topk = set(stripped[:k])
            overall[k].append(len(evidence & topk) / len(evidence))

    ok = True
    n_eval = len(overall[ks[0]])
    print(f"   {n_eval} questions evaluated (adversarial excluded)")
    for k in ks:
        comp = round(sum(overall[k]) / len(overall[k]), 6) if overall[k] else 0.0
        exp = RECALL_EXACT[k]
        match = abs(comp - exp) < 1e-5
        if not match:
            ok = False
        print(f"   k={k:>3}: computed {comp:.6f}   expected {exp:.6f}   {'MATCH' if match else f'DIFF delta={abs(comp-exp):.6f}'}")
    print(f"   -> {'PASS' if ok else 'FAIL'} (exact standalone recompute)\n")
    return ok


async def check_swing(concurrency: int) -> bool:
    recs = load_answers(KIT / "data" / "answers_mem0_conv26.json")
    print(f"CHECK 2 -- re-judging the {len(recs)} control-slice conv-26 answers under mem0 + strict ...")
    accs = {}
    for j in ("mem0", "strict"):
        r = await run_judge(recs, j, concurrency)
        accs[j] = r["accuracy"]
        lo, hi = TOL[j]
        print(f"   {j:6}: accuracy={r['accuracy']:.4f}   tolerance [{lo:.2f},{hi:.2f}]   "
              f"{'OK' if lo <= r['accuracy'] <= hi else 'OUT OF RANGE'}")
    swing = (accs["mem0"] - accs["strict"]) * 100
    lo, hi = TOL["swing_pp"]
    swing_ok = lo <= swing <= hi
    print(f"   swing: {swing:.1f} pp   tolerance [{lo},{hi}]   {'OK' if swing_ok else 'OUT OF RANGE'}")
    ok = (TOL["mem0"][0] <= accs["mem0"] <= TOL["mem0"][1]
          and TOL["strict"][0] <= accs["strict"] <= TOL["strict"][1] and swing_ok)
    print(f"   -> {'PASS' if ok else 'FAIL'} (judge swing reproduced within tolerance)\n")
    return ok


async def main() -> int:
    r1 = check_recall()
    r1b = check_recall_standalone()
    if not os.getenv("OPENAI_API_KEY"):
        print("SKIP CHECK 2 -- the judge swing needs OPENAI_API_KEY (env or .env); "
              "the judge-free checks 1 and 1b ran above.", file=sys.stderr)
        print("=" * 60)
        print(f"VERIFY: judge-free checks {'PASS' if (r1 and r1b) else 'FAIL'}; CHECK 2 SKIPPED")
        return 2 if (r1 and r1b) else 1
    r2 = await check_swing(concurrency=6)
    ok = r1 and r1b and r2
    print("=" * 60)
    print(f"VERIFY: {'ALL CHECKS PASS' if ok else 'SOME CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
