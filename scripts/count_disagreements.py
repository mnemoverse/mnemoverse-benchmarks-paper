"""Provenance for the cross-conversation disagreement counts in the paper (S3 footnote).

Recomputes, from the committed verdicts, the claim that the mem0->strict swing on
Mem0's own answers is ENTIRELY ONE-DIRECTIONAL:
  - lenient credits / strict rejects   (the leniency)
  - counter-directional (strict credits / mem0 rejects)  -- expected 0
  - strict pedantry: cases where Mem0's answer equals the gold modulo case/punctuation
    yet the strict prompt still rejected it (the ~1% that makes strict not ground truth).

    python scripts/count_disagreements.py
"""
import json
import re
from pathlib import Path

V = Path(__file__).resolve().parents[1] / "experiments/hardening/verdicts"
KIT = Path(__file__).resolve().parents[1] / "kit/data/mem0_oss_answers"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def main() -> None:
    lenient_credits = counter = 0
    pedantic = []
    for mp in sorted(V.glob("B_conv*_mem0.json")):
        conv = mp.name.replace("B_", "").replace("_mem0.json", "")
        strict = {str(r["qid"]): r for r in json.loads(mp.with_name(mp.name.replace("_mem0", "_strict")).read_text())}
        mem0 = {str(r["qid"]): r for r in json.loads(mp.read_text())}
        ans = {str(r["qid"]): r for r in json.loads((KIT / f"{conv}.json").read_text())}
        for q, mv in mem0.items():
            sv, a = strict.get(q), ans.get(q)
            if not sv:
                continue
            if mv["score"] == 1.0 and sv["score"] == 0.0:
                lenient_credits += 1
                if a and norm(a["answer"]) == norm(a["gold"]):
                    pedantic.append((conv, a["answer"], a["gold"]))
            elif mv["score"] == 0.0 and sv["score"] == 1.0:
                counter += 1
    print(f"lenient credits / strict rejects : {lenient_credits}")
    print(f"counter-directional              : {counter}   (entirely one-directional iff 0)")
    print(f"total disagreements              : {lenient_credits + counter}")
    print(f"strict pedantry (==gold mod case/punct): {len(pedantic)}")
    for c, a, g in pedantic:
        print(f"    {c}: {a!r} vs gold {g!r}")


if __name__ == "__main__":
    main()
