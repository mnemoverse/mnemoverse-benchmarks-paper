#!/usr/bin/env python3
"""Extra full-run re-judges added after external review (answers fixed): the single-rule
ablation and the Claude backbone.

Single-rule ablation: re-judge Mem0's full published run (1,539 answers)
    under four ablation prompts, each = the lenient prompt with ONE leniency rule
    tightened to strict. score(lenient) - score(ablation_i) isolates how much of
    the lenient->strict swing rule i carries.
Non-OpenAI backbone: re-judge the same run under the lenient and strict
    prompts on a Claude backbone (claude-sonnet-4-5). Gives prompt- and model-axis
    effects against a truly distant judge model.

    OPENAI_API_KEY=... ANTHROPIC_API_KEY=... python scripts/run_extra_judges.py

Writes per-answer verdicts to experiments/hardening/verdicts/{ABL_,XB_}conv{N}_{judge}.json
and summaries to experiments/hardening/{ablation,third_backbone}.{json,md}.
Resumable per (conversation, judge). gpt-5 judges run at concurrency 12, Claude at 5.
"""
from __future__ import annotations
import argparse, asyncio, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "scripts"))
from judge import run_judge, load_answers  # noqa: E402

DATA = KIT / "data" / "mem0_oss_answers"
VERDICTS = REPO / "experiments" / "hardening" / "verdicts"
CONVS = [f"conv{i}" for i in range(10)]

ABL_JUDGES = ["abl-no-partial", "abl-no-paraphrase", "abl-no-datetol", "abl-no-extradetail"]
CLAUDE_JUDGES = ["mem0-claude", "strict-claude"]


def scored_map(path: Path) -> dict:
    recs = json.loads(path.read_text(encoding="utf-8"))
    return {r["qid"]: float(r["score"]) for r in recs
            if isinstance(r.get("score"), (int, float)) and r["score"] in (0.0, 1.0)}


async def rejudge(judges, prefix, concurrency):
    for conv in CONVS:
        recs = load_answers(DATA / f"{conv}.json")
        for j in judges:
            out = VERDICTS / f"{prefix}{conv}_{j}.json"
            if out.exists():
                print(f"[skip] {out.name}", flush=True); continue
            r = await run_judge(recs, j, concurrency)
            out.write_text(json.dumps(r["records"], indent=1), encoding="utf-8")
            print(f"[done] {conv} {j}: acc={r['accuracy']:.4f} n={r['n']}/{r['n_total']}", flush=True)


def pool(prefix, judge):
    m = {}
    for conv in CONVS:
        p = VERDICTS / f"{prefix}{conv}_{judge}.json"
        if p.exists():
            m.update({f"{conv}:{q}": s for q, s in scored_map(p).items()})
    return m


def joint(a, b):
    j = sorted(set(a) & set(b))
    return (sum(a[q] for q in j) / len(j), sum(b[q] for q in j) / len(j), len(j)) if j else (float("nan"),)*2 + (0,)


def analyze_ablation():
    lenient = {}
    for conv in CONVS:
        lenient.update({f"{conv}:{q}": s for q, s in scored_map(VERDICTS / f"B_{conv}_mem0.json").items()})
    strict = {}
    for conv in CONVS:
        strict.update({f"{conv}:{q}": s for q, s in scored_map(VERDICTS / f"B_{conv}_strict.json").items()})
    L = ["# Single-rule ablation of the lenient prompt (P4 / F-S8)", "",
         "Each variant is the mem0 lenient prompt with exactly ONE rule tightened to strict; "
         "`drop` = lenient score minus the variant's score on the jointly-scored answers = the swing that rule carries. "
         "Prompts: `kit/prompts/judge_abl_*.txt`; verdicts `experiments/hardening/verdicts/ABL_conv*.json`. "
         "Runner `scripts/run_extra_judges.py`.", "",
         "| variant (rule tightened) | score % | drop from lenient (pp) |",
         "|--------------------------|---------|------------------------|"]
    len_all = sum(lenient.values()) / len(lenient) * 100
    rows = []
    for j, label in [("abl-no-partial", "partial credit"), ("abl-no-paraphrase", "paraphrase / semantic"),
                     ("abl-no-datetol", "date / duration tolerance"), ("abl-no-extradetail", "extra detail / referent")]:
        pj = pool("ABL_", j)
        la, va, n = joint(lenient, pj)
        drop = (la - va) * 100
        rows.append((label, va * 100, drop, n))
        L.append(f"| {label} | {va*100:.1f} | {drop:+.1f} (n={n}) |")
    sa, _, _ = joint(lenient, strict)
    strict_all = sum(strict.values()) / len(strict) * 100
    L.append(f"| **lenient (anchor)** | **{len_all:.1f}** | 0.0 |")
    L.append(f"| **strict (all rules)** | **{strict_all:.1f}** | **{len_all-strict_all:+.1f}** |")
    L.append("")
    L.append(f"Sum of single-rule drops = {sum(r[2] for r in rows):.1f} pp vs the full lenient->strict swing "
             f"{len_all-strict_all:.1f} pp; the difference is rule interaction (an answer can be caught by more "
             f"than one tightened rule, so single-rule drops overlap).")
    (REPO / "experiments" / "hardening" / "ablation.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (REPO / "experiments" / "hardening" / "ablation.json").write_text(
        json.dumps({"lenient_pct": len_all, "strict_pct": strict_all,
                    "drops": [{"rule": r[0], "score_pct": r[1], "drop_pp": r[2], "n": r[3]} for r in rows]}, indent=1),
        encoding="utf-8")
    print("\n".join(L))


def analyze_backbone():
    g5_mem, g5_str = pool("B_", "mem0"), pool("B_", "strict")
    # committed lenient/strict use B_conv{N}_{mem0,strict}.json
    g5_mem = {}; g5_str = {}
    for conv in CONVS:
        g5_mem.update({f"{conv}:{q}": s for q, s in scored_map(VERDICTS / f"B_{conv}_mem0.json").items()})
        g5_str.update({f"{conv}:{q}": s for q, s in scored_map(VERDICTS / f"B_{conv}_strict.json").items()})
    cl_mem, cl_str = pool("XB_", "mem0-claude"), pool("XB_", "strict-claude")
    pm_a, pm_b, npm = joint(cl_mem, cl_str)          # prompt effect on Claude
    mm_a, mm_b, nmm = joint(g5_mem, cl_mem)          # model effect (gpt-5 - claude), lenient
    ms_a, ms_b, nms = joint(g5_str, cl_str)          # model effect, strict
    lenient_claude = sum(cl_mem.values()) / len(cl_mem) * 100
    strict_claude = sum(cl_str.values()) / len(cl_str) * 100
    L = ["# Third judge backbone: Claude (P6 / F-S7)", "",
         "The two headline prompts re-scored on `claude-sonnet-4-5` (a non-OpenAI backbone), same 1,539 answers. "
         "Verdicts `experiments/hardening/verdicts/XB_conv*.json`; runner `scripts/run_extra_judges.py`.", "",
         f"- Prompt effect on Claude (lenient - strict): **{(pm_a-pm_b)*100:+.1f} pp** (n={npm}); "
         f"lenient {lenient_claude:.1f}%, strict {strict_claude:.1f}%.",
         f"- Model effect, lenient prompt (gpt-5 - Claude): **{(mm_a-mm_b)*100:+.1f} pp** (n={nmm}).",
         f"- Model effect, strict prompt (gpt-5 - Claude): **{(ms_a-ms_b)*100:+.1f} pp** (n={nms}).", "",
         "Read against the gpt-5/gpt-4o decomposition: the prompt axis remains an order of magnitude larger than "
         "the model axis even against a distant backbone if the prompt effect here is tens of points and the model "
         "effects are single digits."]
    (REPO / "experiments" / "hardening" / "third_backbone.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (REPO / "experiments" / "hardening" / "third_backbone.json").write_text(
        json.dumps({"prompt_effect_claude_pp": (pm_a-pm_b)*100, "lenient_claude_pct": lenient_claude,
                    "strict_claude_pct": strict_claude, "model_effect_lenient_pp": (mm_a-mm_b)*100,
                    "model_effect_strict_pp": (ms_a-ms_b)*100}, indent=1), encoding="utf-8")
    print("\n".join(L))


async def main(args):
    if not args.analyze_only:
        await rejudge(ABL_JUDGES, "ABL_", 12)
        await rejudge(CLAUDE_JUDGES, "XB_", 5)
    analyze_ablation()
    print()
    analyze_backbone()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyze-only", action="store_true")
    asyncio.run(main(ap.parse_args()))
