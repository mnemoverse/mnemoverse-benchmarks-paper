"""Standalone public recompute of the paper's Table 2 (judge-error vs the lexical proxy).

No private repository, no API key. Inputs (all committed in this repo):
  kit/data/answers_engine_conv26.json        -- our engine's 152 conv-26 answers
                                                (question/gold/answer/category, index-aligned)
  kit/data/rejudge_20260521_235650.json      -- four judges' per-question score arrays
                                                (same index order)
  kit/data/answers_mem0_conv26.json          -- the control slice's 143 answers
  kit/data/rejudge_q8_20260531T201308Z.json  -- mem0/strict verdicts on the control slice

The lexical-containment proxy (normalise + substring + date variants) and the
rule-decidable subset filter are imported VERBATIM from the reference implementation
in kit/scripts/judge_error/compute_judge_error.py -- the same functions that produced
the committed judge_error_results.json -- so there is no reimplementation drift. Only
that module's data-loading requires the private harness; its rule functions do not.

Expected values (the paper's Table 2 + control-slice note); exits non-zero on mismatch:
  engine side, n=117:  mem0 59.8/78.3/0.0  mem0-4o 57.3/83.3/0.0
                       strict 74.4/28.3/22.8  mnemoverse 70.1/53.3/5.3
                       (and the "credits 47 of 60" mem0 false positives)
  control slice, n=110: mem0 FP 58.8, strict FN 33.3

    python kit/scripts/recompute_judge_error.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts" / "judge_error"))
from compute_judge_error import (  # noqa: E402  (verbatim rule functions)
    INCLUDE_CATS_WITH_MULTI_HOP,
    is_correct_by_proxy,
    is_discrete_gold,
)

EXPECTED_ENGINE = {  # judge -> (acc%, FP%, FN%)
    "mem0": (59.8, 78.3, 0.0),
    "mem0-4o": (57.3, 83.3, 0.0),
    "strict": (74.4, 28.3, 22.8),
    "mnemoverse": (70.1, 53.3, 5.3),
}
EXPECTED_ENGINE_N = 117
EXPECTED_MEM0_FP_COUNT = (47, 60)          # credits 47 of 60 proxy-wrong
EXPECTED_CONTROL = {"mem0_fp": 58.8, "strict_fn": 33.3}
EXPECTED_CONTROL_N = 110


def in_subset(category: str, gold: str) -> bool:
    return category in INCLUDE_CATS_WITH_MULTI_HOP and is_discrete_gold(str(gold))


def metrics(pairs):
    """pairs: list of (truth: bool, verdict: 0/1). Returns acc%, FP%, FN%."""
    n = len(pairs)
    n_wrong = sum(1 for t, _ in pairs if not t)
    n_right = n - n_wrong
    fp = sum(1 for t, v in pairs if not t and v == 1.0)
    fn = sum(1 for t, v in pairs if t and v == 0.0)
    agree = sum(1 for t, v in pairs if (v == 1.0) == t)
    return (100 * agree / n,
            100 * fp / n_wrong if n_wrong else 0.0,
            100 * fn / n_right if n_right else 0.0,
            fp, n_wrong)


def close(a: float, b: float, tol: float = 0.06) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    ok = True

    # ---- engine side (Table 2) ----
    ans = json.loads((KIT / "data" / "answers_engine_conv26.json").read_text(encoding="utf-8"))["records"]
    rj = json.loads((KIT / "data" / "rejudge_20260521_235650.json").read_text(encoding="utf-8"))
    judges = {j["judge"]: j["scores"] for j in rj["judges"]}

    idxs = [r["idx"] for r in ans if in_subset(r["category"], r["gold"])]
    truth = {r["idx"]: is_correct_by_proxy(r["gold"], r["answer"]) for r in ans}
    print(f"ENGINE SIDE -- rule-decidable subset: n={len(idxs)} (expected {EXPECTED_ENGINE_N})")
    ok &= len(idxs) == EXPECTED_ENGINE_N

    for name, exp in EXPECTED_ENGINE.items():
        scores = judges[name]
        pairs = [(truth[i], scores[i]) for i in idxs if scores[i] in (0.0, 1.0)]
        acc, fp, fn, fp_cnt, n_wrong = metrics(pairs)
        match = close(acc, exp[0]) and close(fp, exp[1]) and close(fn, exp[2])
        ok &= match
        print(f"  {name:10s}: acc {acc:5.1f} (exp {exp[0]})  FP {fp:5.1f} (exp {exp[1]})  "
              f"FN {fn:5.1f} (exp {exp[2]})  {'MATCH' if match else 'MISMATCH'}")
        if name == "mem0":
            cnt_ok = (fp_cnt, n_wrong) == EXPECTED_MEM0_FP_COUNT
            ok &= cnt_ok
            print(f"             credits {fp_cnt} of {n_wrong} proxy-wrong "
                  f"(expected {EXPECTED_MEM0_FP_COUNT[0]} of {EXPECTED_MEM0_FP_COUNT[1]}) "
                  f"{'MATCH' if cnt_ok else 'MISMATCH'}")

    # ---- control slice side ----
    q8 = json.loads((KIT / "data" / "rejudge_q8_20260531T201308Z.json").read_text(encoding="utf-8"))["per_question"]
    sub = [r for r in q8 if in_subset(r["category"], r["ground_truth"])]
    print(f"\nCONTROL SLICE -- rule-decidable subset: n={len(sub)} (expected {EXPECTED_CONTROL_N})")
    ok &= len(sub) == EXPECTED_CONTROL_N
    pairs_m = [(is_correct_by_proxy(r["ground_truth"], r["answer"]), r["mem0_score"]) for r in sub]
    pairs_s = [(is_correct_by_proxy(r["ground_truth"], r["answer"]), r["strict_score"]) for r in sub]
    _, fp_m, _, _, _ = metrics(pairs_m)
    _, _, fn_s, _, _ = metrics(pairs_s)
    m_ok = close(fp_m, EXPECTED_CONTROL["mem0_fp"]) and close(fn_s, EXPECTED_CONTROL["strict_fn"])
    ok &= m_ok
    print(f"  mem0 FP {fp_m:5.1f} (exp {EXPECTED_CONTROL['mem0_fp']})  "
          f"strict FN {fn_s:5.1f} (exp {EXPECTED_CONTROL['strict_fn']})  "
          f"{'MATCH' if m_ok else 'MISMATCH'}")

    print("\n" + ("ALL TABLE-2 NUMBERS REPRODUCE" if ok else "MISMATCH -- see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
