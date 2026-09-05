#!/usr/bin/env python3
"""Is the judge's leniency system-dependent? -- question-clustered, not two-proportion.

The paper reports the mem0 judge's false-positive rate as 78.3% on our engine's
answers vs 58.8% on the Mem0-backed control slice, with a two-proportion test at
p ~ 0.02. A subagent panel flagged that test, correctly: the two answer sets are
the SAME conv-26 questions answered by two systems (verified here by joining on
question text), so the samples are not independent -- the question frame is
shared, and a two-proportion test ignores that clustering.

This redoes the comparison respecting the design, twice:

  (a) CLUSTER BOOTSTRAP over the shared question frame: resample questions with
      replacement, recompute both FP rates on the resample, take the difference.
  (b) PAIRED PERMUTATION over the questions where BOTH systems' answers are
      proxy-wrong: under the null "the judge's leniency does not depend on whose
      answer it is", the two systems' verdicts are exchangeable within a
      question, so permuting the system label per question gives an exact null.

Both use the verbatim proxy rule and rule-decidable filter from
kit/scripts/judge_error/compute_judge_error.py -- the same functions behind the
committed judge_error_results.json -- so there is no reimplementation drift.

    python scripts/differential_error_paired.py   (offline, no API)
Writes experiments/hardening/differential_error_paired.md.
"""
from __future__ import annotations
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "scripts" / "judge_error"))
from compute_judge_error import (  # noqa: E402  (verbatim rule functions)
    INCLUDE_CATS_WITH_MULTI_HOP,
    is_correct_by_proxy,
    is_discrete_gold,
)

OUT = REPO / "experiments" / "hardening" / "differential_error_paired.md"
B = 10000
random.seed(20260715)


def in_subset(category, gold) -> bool:
    return category in INCLUDE_CATS_WITH_MULTI_HOP and is_discrete_gold(str(gold))


def norm_q(q: str) -> str:
    return " ".join((q or "").lower().split())


def load():
    """-> {question_text: (proxy_ok, judge_credited)} per answer set."""
    eng_ans = json.loads((KIT / "data" / "answers_engine_conv26.json").read_text(encoding="utf-8"))["records"]
    eng_rj = json.loads((KIT / "data" / "rejudge_20260521_235650.json").read_text(encoding="utf-8"))
    eng_scores = {j["judge"]: j["scores"] for j in eng_rj["judges"]}["mem0"]
    engine = {}
    for r in eng_ans:
        if not in_subset(r["category"], r["gold"]):
            continue
        v = eng_scores[r["idx"]]
        if v not in (0.0, 1.0):
            continue
        engine[norm_q(r["question"])] = (is_correct_by_proxy(r["gold"], r["answer"]), v == 1.0)

    # The control slice's re-judge carries answers AND verdicts in one per_question
    # block (schema: {qid, category, question, answer, ground_truth, mem0_score, ...}).
    sl_rj = json.loads((KIT / "data" / "rejudge_q8_20260531T201308Z.json").read_text(encoding="utf-8"))
    slice_ = {}
    for r in sl_rj["per_question"]:
        gold = r["ground_truth"]
        if not in_subset(r["category"], gold):
            continue
        v = r.get("mem0_score")
        if v not in (0.0, 1.0):
            continue
        slice_[norm_q(r["question"])] = (is_correct_by_proxy(gold, r["answer"]), v == 1.0)
    return engine, slice_


def fp_rate(pairs):
    wrong = [cred for ok, cred in pairs if not ok]
    return (sum(wrong) / len(wrong)) if wrong else float("nan"), len(wrong)


def main() -> int:
    engine, slice_ = load()
    shared = sorted(set(engine) & set(slice_))
    if len(shared) < 50:
        OUT.write_text(f"# Paired differential-error check\n\nOnly {len(shared)} shared "
                       f"questions joined (engine {len(engine)}, slice {len(slice_)}) -- "
                       f"join failed, not reporting.\n", encoding="utf-8")
        print(f"join failed: {len(shared)} shared")
        return 1

    L = ["# Is the judge's leniency system-dependent? (question-clustered)", "",
         f"The two answer sets are the same conv-26 questions answered by two systems: "
         f"{len(shared)} rule-decidable questions join on question text (engine set "
         f"{len(engine)}, control slice {len(slice_)}). A two-proportion test would treat "
         f"them as independent samples; these do not. Seeded, B={B}. "
         f"Rerun: `python scripts/differential_error_paired.py`.", ""]

    e_all, e_n = fp_rate(list(engine.values()))
    s_all, s_n = fp_rate(list(slice_.values()))
    L.append(f"**Full sets (the paper's figures):** engine FP {100*e_all:.1f}% (n={e_n} proxy-wrong "
             f"answers), control slice FP {100*s_all:.1f}% (n={s_n}); difference "
             f"{100*(e_all-s_all):+.1f} pp.")
    L.append("")

    diffs = []
    for _ in range(B):
        pick = [shared[random.randrange(len(shared))] for _ in shared]
        e, _ = fp_rate([engine[q] for q in pick])
        s, _ = fp_rate([slice_[q] for q in pick])
        if e == e and s == s:
            diffs.append(100 * (e - s))
    diffs.sort()
    lo, hi = diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))]
    le0 = sum(1 for d in diffs if d <= 0) / len(diffs)
    L.append("## (a) Cluster bootstrap over the shared question frame")
    L.append("")
    L.append(f"Difference in FP rate (engine − slice): median {diffs[len(diffs)//2]:+.1f} pp, "
             f"central 95% [{lo:+.1f}, {hi:+.1f}]; the difference is ≤ 0 in "
             f"{100*le0:.1f}% of resamples.")
    L.append("")

    both_wrong = [q for q in shared if not engine[q][0] and not slice_[q][0]]
    e_cred = sum(engine[q][1] for q in both_wrong)
    s_cred = sum(slice_[q][1] for q in both_wrong)
    obs = e_cred - s_cred
    # The singleton strata are where the aggregate gap actually lives -- the paper quotes
    # these counts, so the script that certifies them must emit them (REPRODUCING.md's
    # registry names this command's expected check).
    only_e = [q for q in shared if not engine[q][0] and slice_[q][0]]
    only_s = [q for q in shared if engine[q][0] and not slice_[q][0]]
    ge = 0
    for _ in range(B):
        stat = 0
        for q in both_wrong:
            a, b = engine[q][1], slice_[q][1]
            if random.random() < 0.5:
                a, b = b, a
            stat += a - b
        if abs(stat) >= abs(obs):
            ge += 1
    L.append("## (b) Paired permutation (questions both systems answer proxy-wrong)")
    L.append("")
    L.append(f"n = {len(both_wrong)} such questions; the judge credits **{e_cred} from the engine "
             f"and {s_cred} from the slice** (difference {obs:+d}); two-sided permutation "
             f"p = {ge/B:.3f} (system label exchanged within each question).")
    L.append("")
    L.append("## (c) Where the aggregate gap lives: the singleton-wrong strata")
    L.append("")
    L.append(f"Only the engine proxy-wrong: **{len(only_e)} questions, {sum(engine[q][1] for q in only_e)} credited**. "
             f"Only the slice proxy-wrong: **{len(only_s)} questions, {sum(slice_[q][1] for q in only_s)} credited**. "
             "The gap is localized here, not in the matched stratum -- but these are different "
             "questions, so this localizes the effect rather than identifying its mechanism.")
    L.append("")
    L.append("Both (a) and (b) respect the shared question frame that a two-proportion test ignores.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
