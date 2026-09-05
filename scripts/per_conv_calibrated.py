"""per_conv_calibrated.py -- per-conversation lenient-vs-calibrated table on the full Mem0 run.

Implements the external-review [Nice-to-have]: report the calibrated ("golden v2")
judge's score PER CONVERSATION on the full 1,539-answer Mem0 published run, beside
the lenient (mem0) prompt's score, so readers can see whether the ~5.7pp calibrated
inflation is uniform or concentrated in specific conversations.

Inputs (committed artifacts, no API calls):
    experiments/hardening/verdicts/B_conv{0..9}_mem0.json        per-answer lenient verdicts
    experiments/golden_judge/fullrun_verdicts/conv{0..9}_golden2.json  per-answer calibrated verdicts
Cross-checks against the committed aggregates:
    experiments/hardening/summary.json            (B_cross_conversation.per_conversation)
    experiments/golden_judge/FULLRUN_GOLDEN_RESULTS.json

Counting conventions follow kit/scripts/judge.py::run_judge exactly:
    - a record is SCORED iff its score is exactly 0.0 or 1.0
      (unparseable judge output -> NaN, API error -> null; both excluded);
    - accuracy = mean(score) over scored records (CORRECT=1.0, WRONG=0.0;
      there is no AMBIGUOUS label in this pipeline).
The paper's headline convention (main.tex, golden-judge footnote): the 91.0 / 85.3 / 5.7pp
numbers are computed on the JOINTLY-scored answers (both judges parseable, n=1534).
Robustness handlings also reported: lenient over all its 1,539 scored answers (-> 5.8pp)
and unparseable-counted-as-wrong (-> 6.0pp).

Run (stdlib only, offline):
    python scripts/per_conv_calibrated.py
Writes scripts/per_conv_calibrated_output.md and prints the same table.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LENIENT_DIR = REPO / "experiments" / "hardening" / "verdicts"
GOLDEN_DIR = REPO / "experiments" / "golden_judge" / "fullrun_verdicts"
HARDENING_SUMMARY = REPO / "experiments" / "hardening" / "summary.json"
FULLRUN_SUMMARY = REPO / "experiments" / "golden_judge" / "FULLRUN_GOLDEN_RESULTS.json"
OUT_MD = REPO / "scripts" / "per_conv_calibrated_output.md"

CONVS = [f"conv{i}" for i in range(10)]


def is_scored(score) -> bool:
    """kit/scripts/judge.py convention: scored iff score is exactly 0.0 or 1.0.

    Unparseable judge output is stored as NaN (NaN != NaN, so it fails the check);
    API errors are stored as null (None). Both are excluded from the denominator.
    """
    return isinstance(score, (int, float)) and score in (0.0, 1.0)


def load_verdicts(path: Path) -> dict[str, float]:
    """qid -> score for SCORED records only."""
    records = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for r in records:
        if is_scored(r.get("score")):
            out[r["qid"]] = float(r["score"])
    return out


def pct(x: float) -> float:
    return round(x * 100, 1)


def main() -> int:
    hardening = json.loads(HARDENING_SUMMARY.read_text(encoding="utf-8"))
    fullrun = json.loads(FULLRUN_SUMMARY.read_text(encoding="utf-8"))
    mem0_committed = {r["conv"]: r for r in hardening["B_cross_conversation"]["per_conversation"]}
    golden_committed = {r["conv"]: r for r in fullrun["per_conversation"]}

    rows = []
    joint_len_scores: list[float] = []
    joint_gold_scores: list[float] = []
    all_len_scores: list[float] = []
    n_unparseable_golden = 0
    n_total_all = 0
    unparseable_ids: list[str] = []

    for conv in CONVS:
        lenient_path = LENIENT_DIR / f"B_{conv}_mem0.json"
        golden_path = GOLDEN_DIR / f"{conv}_golden2.json"
        lenient = load_verdicts(lenient_path)
        golden = load_verdicts(golden_path)
        golden_records = json.loads(golden_path.read_text(encoding="utf-8"))
        n_records = len(golden_records)
        n_total_all += n_records
        n_unparseable_golden += n_records - len(golden)
        unparseable_ids += [f"{conv}:{r['qid']}" for r in golden_records
                            if not is_scored(r.get("score"))]

        joint_qids = sorted(set(lenient) & set(golden))
        l_scores = [lenient[q] for q in joint_qids]
        g_scores = [golden[q] for q in joint_qids]
        joint_len_scores += l_scores
        joint_gold_scores += g_scores
        all_len_scores += list(lenient.values())

        l_acc = sum(l_scores) / len(l_scores)
        g_acc = sum(g_scores) / len(g_scores)
        # cross-checks against the committed aggregates
        l_acc_full = sum(lenient.values()) / len(lenient)  # lenient over ALL its scored answers
        chk_mem0 = abs(round(l_acc_full, 4) - mem0_committed[conv]["mem0_acc"]) < 5e-5
        chk_gold = abs(round(g_acc, 4) - golden_committed[conv]["golden_acc"]) < 5e-5
        rows.append({
            "conv": conv,
            "n_joint": len(joint_qids),
            "n_total": n_records,
            "lenient_acc": l_acc,
            "calibrated_acc": g_acc,
            "delta_pp": (l_acc - g_acc) * 100,
            "chk_mem0_committed": chk_mem0,
            "chk_golden_committed": chk_gold,
        })

    # sensitivity: exclude conv0 (= LoCoMo conv-26, whose questions fed the
    # judge's calibration signal via the control slice)
    excl = [r for r in rows if r["conv"] != "conv0"]
    n_j_x = sum(r["n_joint"] for r in excl)
    len_j_x = sum(r["lenient_acc"] * r["n_joint"] for r in excl) / n_j_x
    gold_j_x = sum(r["calibrated_acc"] * r["n_joint"] for r in excl) / n_j_x

    n_joint = len(joint_len_scores)
    len_joint = sum(joint_len_scores) / n_joint
    gold_joint = sum(joint_gold_scores) / n_joint
    delta_joint = (len_joint - gold_joint) * 100
    len_all = sum(all_len_scores) / len(all_len_scores)
    # robustness: count golden's unparseable answers as WRONG (denominator = all records)
    gold_unparse_wrong = sum(joint_gold_scores) / n_total_all
    delta_all1539 = (len_all - gold_joint) * 100
    delta_unparse_wrong = (len_all - gold_unparse_wrong) * 100

    # ---- console + markdown ----
    lines = []
    lines.append("# Per-conversation lenient vs calibrated (golden v2) — full Mem0 published run")
    lines.append("")
    lines.append(
        "Provenance: computed offline (stdlib only) from the committed per-answer verdicts "
        "`experiments/hardening/verdicts/B_conv{0..9}_mem0.json` (lenient) and "
        "`experiments/golden_judge/fullrun_verdicts/conv{0..9}_golden2.json` (calibrated); "
        "counting conventions of `kit/scripts/judge.py::run_judge` (scored iff score is exactly 0/1); "
        "headline row = jointly-scored answers (paper convention, main.tex golden-judge footnote). "
        "Rerun: `python scripts/per_conv_calibrated.py`.")
    lines.append("")
    lines.append("| conv | n (joint) | n (total) | lenient % | calibrated % | inflation (pp) |")
    lines.append("|------|-----------|-----------|-----------|--------------|----------------|")
    for r in rows:
        lines.append(
            f"| {r['conv']} | {r['n_joint']} | {r['n_total']} | {pct(r['lenient_acc']):.1f} "
            f"| {pct(r['calibrated_acc']):.1f} | +{r['delta_pp']:.1f} |")
    lines.append(
        f"| **all** | **{n_joint}** | **{n_total_all}** | **{len_joint*100:.1f}** "
        f"| **{gold_joint*100:.1f}** | **+{delta_joint:.1f}** |")
    lines.append("")
    lines.append(
        f"Aggregate (jointly-scored, n={n_joint}): lenient {len_joint:.4f}, "
        f"calibrated {gold_joint:.4f}, inflation {delta_joint:.2f} pp.")
    lines.append(
        f"Robustness: lenient over all its {len(all_len_scores)} scored answers = {len_all:.4f} "
        f"(inflation {delta_all1539:.2f} pp); counting the {n_unparseable_golden} calibrated-unparseable "
        f"answers as wrong = calibrated {gold_unparse_wrong:.4f} (inflation {delta_unparse_wrong:.2f} pp).")
    lines.append(
        f"Sensitivity, excluding conv0 (= LoCoMo conv-26; its questions fed the judge's "
        f"calibration signal via the control slice): joint-denominator inflation "
        f"{(len_j_x-gold_j_x)*100:.2f} pp on n={n_j_x} -- i.e. 5.6-5.7 depending on handling.")
    lines.append(
        f"The {n_unparseable_golden} calibrated-unparseable answers (excluded from the joint "
        f"denominator; inflation is computed at full precision before rounding, so a table row may "
        f"differ from the subtraction of its rounded columns by 0.1): "
        + ", ".join(f"`{u}`" for u in unparseable_ids) + ".")
    lines.append("")

    # honesty gate: must reproduce the paper's published aggregates
    ok_len = round(len_joint * 100, 1) == 91.0
    ok_gold = round(gold_joint * 100, 1) == 85.3
    ok_delta = round(delta_joint, 1) == 5.7
    ok_committed = all(r["chk_mem0_committed"] and r["chk_golden_committed"] for r in rows)
    lines.append(
        f"Reproduction check vs paper: lenient 91.0 -> {'PASS' if ok_len else 'FAIL'} "
        f"({len_joint*100:.4f}); calibrated 85.3 -> {'PASS' if ok_gold else 'FAIL'} "
        f"({gold_joint*100:.4f}); inflation 5.7 pp -> {'PASS' if ok_delta else 'FAIL'} "
        f"({delta_joint:.4f}); per-conv cells match committed summaries -> "
        f"{'PASS' if ok_committed else 'FAIL'}.")
    md = "\n".join(lines) + "\n"
    OUT_MD.write_text(md, encoding="utf-8")
    print(md)
    print(f"wrote {OUT_MD}")
    if not (ok_len and ok_gold and ok_delta and ok_committed):
        print("REPRODUCTION FAILURE — do not use these numbers; investigate first.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
