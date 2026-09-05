#!/usr/bin/env python3
"""Independent rubrics over the conv-26 pipeline matrix (reviewer-requested check).

The four-judge matrix opposes two field-style prompts to two author-written
prompts, and the author-written pair crowns the author's engine. This run adds
two rubrics NEITHER of which favors the strict prompt's author: the
human-calibrated judge (golden, gpt-5) and the verbatim LongMemEval port
(gpt-4o-2024-08-06, default + temporal variants routed by category) -- over the
same six fixed answer sets behind the committed matrix cells (k=50).

One-time answer extraction (maintainers, private core checkout):
    python scripts/run_matrix_extra_judges.py --extract-from <core-root>
writes kit/data/matrix_conv26_answers.json (6 x 152 answers, canonical order).

Paid re-judge (resumable per pipeline x judge; ~1.9k calls):
    OPENAI_API_KEY=... python scripts/run_matrix_extra_judges.py

Paid path output (NOT run for the released paper; nothing in the paper depends on it):
    experiments/hardening/verdicts/MX_{pipeline}_{golden|lme}.json and
    experiments/hardening/matrix_extra_judges.md are written only if you run it yourself.
Only the --extract-from step was executed; its artifact kit/data/matrix_conv26_answers.json ships.
"""
from __future__ import annotations
import argparse, asyncio, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "scripts"))
from judge import run_judge  # noqa: E402

ANSWERS = KIT / "data" / "matrix_conv26_answers.json"
VERDICTS = REPO / "experiments" / "hardening" / "verdicts"
OUT_MD = REPO / "experiments" / "hardening" / "matrix_extra_judges.md"
CAT_NAME = {1: "multi-hop", 2: "temporal", 3: "open-domain", 4: "single-hop"}

E19 = "e19f030:experiments/results/matrix-2026-06-07"
SOURCES = {
    "naked_cosine": "night-runs/cell_0e_naked_locomo_conv26_k50.json",
    "mnemoverse_engine": f"{E19}/cell_mnemoverse_locomo_conv26_n199_k50.json",
    "mnemoverse_http": f"{E19}/cell_mnemoverse_http_locomo_conv26_n199_k50.json",
    "mem0_v3_cloud": f"{E19}/cell_mem0_v3_cloud_locomo_conv26_n199_k50.json",
    "supermemory": f"{E19}/cell_supermemory_locomo_conv26_n199_k50.json",
    "zep": f"{E19}/cell_zep_locomo_conv26_n199_k50.json",
}


def norm(s):
    return " ".join((s or "").lower().split())


def extract(core_root: str) -> None:
    core = Path(core_root)
    qa = json.loads((core / "experiments/data/locomo10.json").read_text(encoding="utf-8"))[0]["qa"]
    canon = [q for q in qa if q.get("category") != 5]
    assert len(canon) == 152
    out = {}
    for pipe, rel in SOURCES.items():
        if ":" in rel:
            raw = subprocess.run(["git", "-C", str(core), "show", rel],
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
            d = json.loads(raw)
        else:
            d = json.loads((core / "experiments/results" / rel).read_text(encoding="utf-8"))
        res = d["results"]
        recs = []
        if pipe == "naked_cosine":  # positional qids, no question/gold fields
            by_idx = {int(r["qid"].split("::q")[1]): r for r in res}
            for i, q in enumerate(canon):
                r = by_idx[i]
                recs.append({"qid": f"p{i}", "question": q["question"],
                             "gold": str(q["answer"]), "answer": r["reader_answer"],
                             "category": CAT_NAME[q["category"]]})
        else:  # canonical row order (verified)
            assert len(res) == 152, f"{pipe}: {len(res)} rows"
            for i, (r, q) in enumerate(zip(res, canon)):
                assert norm(r["question"]) == norm(q["question"]), f"{pipe} row {i} order mismatch"
                recs.append({"qid": f"p{i}", "question": q["question"],
                             "gold": str(q["answer"]), "answer": r["reader_answer"],
                             "category": CAT_NAME[q["category"]]})
        out[pipe] = recs
    ANSWERS.write_text(json.dumps(
        {"_provenance": {
            "source": "core git object e19f030 (branch preserve/conv26-baseline-e19f030), "
                      "matrix-2026-06-07 sweep; naked_cosine from night-runs cell_0e",
            "note": "reader answers behind the committed k=50 matrix cells; canonical question "
                    "order (qid p<i> = i-th non-adversarial conv-26 question); gold/category "
                    "from the locomo10 release",
            "extracted": "2026-07-15"},
         "answers": out}, indent=1), encoding="utf-8")
    print(f"extracted 6x152 answers -> {ANSWERS}")


def is_temporal(rec):
    return rec.get("category") == "temporal"


async def main():
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))["answers"]
    VERDICTS.mkdir(parents=True, exist_ok=True)
    for pipe, recs in answers.items():
        for judge in ("golden", "lme"):
            out = VERDICTS / f"MX_{pipe}_{judge}.json"
            if out.exists():
                print(f"[skip] {out.name}", flush=True)
                continue
            t0 = time.time()
            if judge == "lme":
                temporal = [r for r in recs if is_temporal(r)]
                rest = [r for r in recs if not is_temporal(r)]
                r1 = await run_judge(rest, "lme", 8)
                r2 = await run_judge(temporal, "lme-temporal", 8) if temporal else {"records": []}
                by_qid = {r["qid"]: r for r in r1["records"] + r2["records"]}
                records = [by_qid[rec["qid"]] for rec in recs]
            else:
                records = (await run_judge(recs, "golden", 8))["records"]
            out.write_text(json.dumps(records, indent=1), encoding="utf-8")
            scored = [r for r in records if r["score"] in (0.0, 1.0)]
            acc = sum(r["score"] for r in scored) / len(scored)
            print(f"[done] {pipe} {judge}: acc={acc:.4f} n={len(scored)}/{len(records)} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # summary table
    L = ["# Independent rubrics over the conv-26 pipeline matrix (k=50)", "",
         "golden = human-calibrated judge (gpt-5); lme = verbatim LongMemEval port "
         "(gpt-4o-2024-08-06, default+temporal routed by category). Answers: "
         "kit/data/matrix_conv26_answers.json. Rerun: scripts/run_matrix_extra_judges.py.", ""]
    def row_for(pipe):
        row = [pipe]
        for judge in ("golden", "lme"):
            recs = json.loads((VERDICTS / f"MX_{pipe}_{judge}.json").read_text(encoding="utf-8"))
            scored = [r for r in recs if r["score"] in (0.0, 1.0)]
            if not scored:
                raise SystemExit(f"{pipe}/{judge}: no parseable verdicts -- purge and re-run")
            row.append(f"{sum(r['score'] for r in scored)/len(scored):.3f} (n={len(scored)})")
        return row

    # naked_cosine ran on the other runner path (answers ~105 chars against 43-70)
    # and is NOT comparable to the harness five -- same separation the paper keeps.
    L.append("## Headline: the five harness pipelines")
    L.append("")
    L.append("| pipeline | golden | lme |")
    L.append("|---|---:|---:|")
    for pipe in (p for p in answers if p != "naked_cosine"):
        L.append("| " + " | ".join(row_for(pipe)) + " |")
    if "naked_cosine" in answers:
        L.append("")
        L.append("## Separately: naked_cosine (other runner path, not part of the matrix)")
        L.append("")
        L.append("| pipeline | golden | lme |")
        L.append("|---|---:|---:|")
        L.append("| " + " | ".join(row_for("naked_cosine")) + " |")
        L.append("")
        L.append("Its answers average ~105 characters against 43-70 for the harness pipelines, "
                 "so any lenient-rubric edge is confounded with answer format (the extra-detail "
                 "rule is worth +25.4pp). Reported for completeness, never inside the comparison.")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-from", default=None)
    a = ap.parse_args()
    if a.extract_from:
        extract(a.extract_from)
        sys.exit(0)
    if not ANSWERS.exists():
        sys.exit("no answers artifact; run with --extract-from <core-root>")
    asyncio.run(main())
