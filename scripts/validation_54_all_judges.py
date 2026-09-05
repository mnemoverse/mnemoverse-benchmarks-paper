#!/usr/bin/env python3
"""All five graders on the SAME 54 validation items (review B-R2 fix: the human
band [70.4, 88.9] is a 54-item aggregate, so every judge compared to it must be
scored on those same 54 items -- the full-run 81.7 is a different denominator).

Offline: joins committed per-answer verdicts to the validation qids.
  - golden / lenient / strict: experiments/golden_judge/VALIDATION_RESULTS.json
    (recomputed here independently from the verdict files where available)
  - LongMemEval: experiments/hardening/verdicts/LME_conv*.json (full-run verdicts,
    subset to the 54)
Four graders are scored: calibrated (golden), lenient (mem0), strict, LongMemEval.
Also reports, per grader, agreement with the lead annotator's 44 decided cases, with
each additional annotator's decided cases, and with the 3-rater majority -- plus the
score band each human standard implies on the same 54 (ambiguous cases resolved both
ways), which is the only denominator on which a grader's score is comparable to a band.

    python scripts/validation_54_all_judges.py
Writes experiments/hardening/validation_54_all_judges.md.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "experiments" / "hardening" / "validation_54_all_judges.md"


def load_verdicts(path, key="label"):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    return {r["qid"]: r[key] for r in recs}


def main():
    val = json.loads((REPO / "kit/judge_audit/human_labels_validation_set.json")
                     .read_text(encoding="utf-8"))["labels"]
    # qid: c9_qconv9_q72 -> conv file conv9, verdict qid conv9_q72
    items = []
    for r in val:
        c, rest = r["qid"].split("_", 1)          # c9, qconv9_q72
        items.append({"vqid": r["qid"], "conv": c[1:], "fq": rest[1:],
                      "human": r["human_verdict"]})

    # LME full-run verdicts, subsetted
    lme = {}
    for conv in {it["conv"] for it in items}:
        lme.update(load_verdicts(REPO / f"experiments/hardening/verdicts/LME_conv{conv}.json"))

    # golden / lenient(mem0) / strict on the validation set (sealed verdict files)
    golden = load_verdicts(REPO / "experiments/golden_judge/verdicts_golden2_validation_set.json")

    # lenient + strict full-run verdicts, subsetted (same files as the 91.0/35.0)
    lenient, strict = {}, {}
    for conv in {it["conv"] for it in items}:
        lenient.update(load_verdicts(REPO / f"experiments/hardening/verdicts/B_conv{conv}_mem0.json"))
        strict.update(load_verdicts(REPO / f"experiments/hardening/verdicts/B_conv{conv}_strict.json"))

    # additional annotators via masked ids
    mapping = json.loads((REPO / "kit/annotation/annotator_key_mapping.json").read_text(encoding="utf-8"))
    # A dict wrapping an EMPTY 'cases' list means an empty campaign, not "fall
    # back to the dict's values" -- test for the key, never for truthiness.
    if isinstance(mapping, list):
        mitems = mapping
    elif "cases" in mapping:
        mitems = mapping["cases"]
    else:
        mitems = list(mapping.values())
    mask_of = {m["source_qid"]: m["masked_id"] for m in mitems
               if m.get("source_set") == "set_a" and not m.get("is_catch")}
    ann = {}
    for code in ("OI", "NS"):
        lab = json.loads((REPO / f"kit/annotation/returned/cases_{code}_labels.json")
                         .read_text(encoding="utf-8"))["labels"]
        by_mask = {r["id"]: r["verdict"] for r in lab}
        ann[code] = {vq: by_mask.get(mask_of.get(vq)) for vq in (it["vqid"] for it in items)}

    judges = {"golden": lambda it: golden.get(it["vqid"]),
              "lenient": lambda it: lenient.get(it["fq"]),
              "strict": lambda it: strict.get(it["fq"]),
              "longmemeval": lambda it: lme.get(it["fq"])}

    # 3-rater majority per item (CORRECT/WRONG/AMBIGUOUS; majority of decided verdicts)
    def majority(it):
        votes = [it["human"], ann["OI"].get(it["vqid"]), ann["NS"].get(it["vqid"])]
        cc = votes.count("CORRECT"); ww = votes.count("WRONG")
        if cc >= 2: return "CORRECT"
        if ww >= 2: return "WRONG"
        return None

    L = ["# All graders on the same 54 validation items", "",
         "Offline join of committed verdicts; rerun `python scripts/validation_54_all_judges.py`.", ""]

    # human-implied score band per rater standard: [all ambiguous WRONG, all ambiguous CORRECT]
    L.append("## Human-implied score band on the 54, per rater standard")
    L.append("")
    L.append("| standard | CORRECT | WRONG | ambiguous | band |")
    L.append("|---|---:|---:|---:|---:|")
    std_votes = {"lead annotator": [it["human"] for it in items],
                 "O.T.": [ann["OI"].get(it["vqid"]) for it in items],
                 "A.S.": [ann["NS"].get(it["vqid"]) for it in items],
                 "3-rater majority": [majority(it) for it in items]}
    for name, votes in std_votes.items():
        c = sum(1 for v in votes if v == "CORRECT")
        w = sum(1 for v in votes if v == "WRONG")
        amb = len(votes) - c - w
        lo, hi = 100 * c / len(votes), 100 * (c + amb) / len(votes)
        L.append(f"| {name} | {c} | {w} | {amb} | [{lo:.1f}, {hi:.1f}] |")
    L.append("")
    L.append("The lead annotator marks the most cases ambiguous, so that band is the widest; the two "
             "additional raters decide more cases toward credit, so their bands sit higher. A claim "
             "that a judge scores above 'the human band' must name the standard.")
    L.append("")
    L.append("## Grader scores and agreement")
    L.append("")
    L.append("| grader | score on the 54 | vs lead annotator (44 decided) | vs OI decided | vs NS decided | vs 3-rater majority (decided) |")
    L.append("|---|---:|---:|---:|---:|---:|")

    for name, get in judges.items():
        scored = [(it, get(it)) for it in items]
        missing = [it["vqid"] for it, v in scored if v not in ("CORRECT", "WRONG")]
        n = len([1 for _, v in scored if v in ("CORRECT", "WRONG")])
        score = 100 * sum(1 for _, v in scored if v == "CORRECT") / n if n else float("nan")
        cells = [f"{score:.1f}\\% (n={n})"]
        for std_name, std in [("lead", lambda it: it["human"]),
                              ("OI", lambda it: ann["OI"].get(it["vqid"])),
                              ("NS", lambda it: ann["NS"].get(it["vqid"])),
                              ("maj", majority)]:
            a = d = 0
            for it, v in scored:
                hv = std(it)
                if hv in ("CORRECT", "WRONG") and v in ("CORRECT", "WRONG"):
                    d += 1
                    if hv == v: a += 1
            cells.append(f"{a}/{d}")
        L.append(f"| {name} | " + " | ".join(cells) + " |")
        if missing:
            L.append(f"|  | _{name}: {len(missing)} unparseable/missing: {', '.join(missing[:6])}_ | | | | |")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
