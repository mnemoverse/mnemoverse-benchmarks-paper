"""Golden-judge calibration loop.

Runs the experimental human-calibrated judge (kit/prompts/judge_golden_v1.txt)
on the q8 answer set and evaluates it against the human adjudication of the 57
judge-disputed cases (blind labels, 2026-07-02).

Reuses kit/scripts/judge.py wholesale (same call parameters as mem0/strict —
the prompt is the only variable), registering the extra judge id at runtime.

Usage:
    python experiments/golden_judge/run_golden.py [--limit 0] [--concurrency 6]
                                                  [--judge golden]

Requires OPENAI_API_KEY in env.

Calibration targets (NOT to be overfit — validate out-of-sample later on the
control set the maintainers will label; see feedback: tune for quality, not benchmark):
  - the 40 human-CORRECT disputed cases: golden should say CORRECT (strict's FNs)
  - the 3 human-WRONG disputed cases: golden should say WRONG (lenient's FPs)
  - the 14 AMBIGUOUS: report where they fall (no target)
  - the 86 agreed cases: report disagreement with the mem0/strict consensus
"""
from __future__ import annotations

import argparse
import os
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "kit" / "scripts"))
import judge  # noqa: E402  (kit/scripts/judge.py)

# Register the experimental judges (same machinery, same model family).
judge.JUDGE_PROMPT["golden"] = "judge_golden_v1.txt"
judge.JUDGE_MODEL["golden"] = "gpt-5"
judge.JUDGE_PROMPT["golden2"] = "judge_golden_v2.txt"
judge.JUDGE_MODEL["golden2"] = "gpt-5"

ANSWERS = REPO / "kit" / "data" / "answers_mem0_conv26.json"
REJUDGE = REPO / "kit" / "data" / "rejudge_q8_20260531T201308Z.json"
# The 57 blind human adjudications of the control-slice disagreements ship in the
# kit: kit/judge_audit/human_labels_control_slice.json, schema
# {"_note", "_date", "labels": [{qid, category, human_verdict}]}; qids match
# kit/data/rejudge_q8_20260531T201308Z.json. JUDGE_HUMAN_LABELS may point at an
# alternative file with either that schema or a bare list of {qid, verdict}.
HUMAN = Path(os.environ.get(
    "JUDGE_HUMAN_LABELS",
    str(REPO / "kit" / "judge_audit" / "human_labels_control_slice.json"),
))


def load_human_labels(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw["labels"] if isinstance(raw, dict) else raw
    return {str(r["qid"]): r.get("human_verdict", r.get("verdict")) for r in rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="golden")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=6)
    args = ap.parse_args()
    if not args.limit and not HUMAN.exists():
        sys.exit(f"human labels not found at {HUMAN}; set JUDGE_HUMAN_LABELS to override")

    records = judge.load_answers(ANSWERS)
    if args.limit:
        records = records[: args.limit]
    print(f"[golden] scoring {len(records)} answers with judge={args.judge} "
          f"(model {judge.JUDGE_MODEL[args.judge]})", flush=True)

    result = asyncio.run(judge.run_judge(records, args.judge, args.concurrency))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = HERE / f"verdicts_{args.judge}_{stamp}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[golden] accuracy={result['accuracy']:.4f} n={result['n']}/{result['n_total']}")
    print(f"[golden] verdicts -> {out_path}")

    if args.limit:  # smoke run: skip eval
        for r in result["records"]:
            print(f"  qid {r['qid']}: {r['label']} — {r['reasoning'][:90]}")
        return

    # ---- eval vs human labels + old judges ----
    golden = {str(r["qid"]): r for r in result["records"]}
    q8 = json.loads(REJUDGE.read_text(encoding="utf-8"))["per_question"]
    human = load_human_labels(HUMAN)

    tgt_c = [q for q, v in human.items() if v == "CORRECT"]
    tgt_w = [q for q, v in human.items() if v == "WRONG"]
    amb = [q for q, v in human.items() if v == "AMBIGUOUS"]

    def hits(qids, want):
        have = [q for q in qids if golden.get(q, {}).get("label")]
        ok = [q for q in have if golden[q]["label"] == want]
        return ok, have

    ok_c, have_c = hits(tgt_c, "CORRECT")
    ok_w, have_w = hits(tgt_w, "WRONG")
    amb_c, have_a = hits(amb, "CORRECT")

    print("\n==== calibration vs human (57 disputed) ====")
    print(f"human-CORRECT recovered: {len(ok_c)}/{len(have_c)}  "
          f"(misses: {[q for q in have_c if q not in ok_c]})")
    print(f"human-WRONG   recovered: {len(ok_w)}/{len(have_w)}  "
          f"(misses: {[q for q in have_w if q not in ok_w]})")
    print(f"ambiguous -> CORRECT on {len(amb_c)}/{len(have_a)}: {amb_c}")

    agreed = [r for r in q8 if r["agree"]]
    dis_ag = [r for r in agreed
              if golden.get(str(r["qid"]), {}).get("label")
              and (golden[str(r["qid"])]["label"] == "CORRECT") != r["mem0_correct"]]
    print(f"\nagreed-86 cases where golden disagrees with the mem0+strict consensus: "
          f"{len(dis_ag)} -> {[r['qid'] for r in dis_ag]}")

    n_scored = [r for r in result["records"] if r["label"]]
    print(f"\ngolden overall accuracy on q8: "
          f"{sum(1 for r in n_scored if r['label'] == 'CORRECT') / len(n_scored):.4f} "
          f"(mem0 0.7413, strict 0.3427)")


if __name__ == "__main__":
    main()
