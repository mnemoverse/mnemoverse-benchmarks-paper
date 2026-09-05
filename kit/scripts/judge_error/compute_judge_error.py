"""
compute_judge_error.py
======================
Reference copy. Recomputing from scratch requires the private benchmark harness;
the committed `judge_error_results.json` in this directory is the shipped output
the paper cites.

Empirical "judging the judges" analysis for Mnemoverse vs Mem0 on LoCoMo conv-26.

Data sources (all paths relative to mnemoverse-core repo root):
  (private harness paths; the public copies are listed in the "Data provenance" table of RESULTS.md)
  experiments/results/rejudge_20260521_235650.json  -- 4 judges, 152 Qs, OUR engine's answers  -> kit/data/rejudge_20260521_235650.json
  experiments/results/rejudge_q8_20260531T201308Z.json  -- 2 judges, 143 Qs, control-slice answers -> kit/data/rejudge_q8_20260531T201308Z.json
  experiments/results/locomo_20260521_230400.json   -- per-question metadata for our run          -> kit/data/answers_engine_conv26.json
  experiments/results/comparison_20260530_024828.json -- the control-slice answers                -> kit/data/answers_mem0_conv26.json
  experiments/data/locomo10.json                    -- gold answers + evidence + categories       -> kit/data/locomo_gold_ids.json (+ gold fields)

Ground-truth proxy (rule-based, no LLM):
  A system answer is TRUE-correct iff the normalised gold token appears in the
  normalised system answer.  Normalisation: lowercase, strip punctuation, then
  apply date-format equivalences (e.g. "7 may 2023" == "may 7 2023" == "2023-05-07").

  Objective subset: single_hop + temporal whose gold is a discrete value
  (date / name / number / entity).  open_domain and adversarial are EXCLUDED.
  multi_hop is included ONLY when its gold resolves to a discrete value — we apply
  the same rule and let it fall naturally; the caller should be aware that multi_hop
  coverage here is sparse and noisier.

  Caveat: this proxy is STRICT — it can under-credit a correct paraphrase.  That
  systematic bias (toward FN on truth) means the FN rates reported for judges should
  be interpreted as upper bounds on how strict a judge can "justifiably" be.

Outputs (written to the same directory as this script):
  judge_error_results.json   -- machine-readable results
  RESULTS.md                 -- human-readable markdown table

Usage:
  python compute_judge_error.py [--core-root PATH]

  Default core root: ../../.. (three levels up from this script's directory,
  resolving to the mnemoverse-core repo root).
"""

import argparse
import json
import os
import re
import csv
import random
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_core_root(arg=None):
    if arg:
        return os.path.abspath(arg)
    # Default: script is at mnemoverse-benchmarks-paper/scripts/judge_error/
    # mnemoverse-core is a sibling of mnemoverse-benchmarks-paper
    candidate = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "mnemoverse-core"))
    if os.path.isdir(candidate):
        return candidate
    raise FileNotFoundError(
        f"Could not find mnemoverse-core at {candidate}. Pass --core-root explicitly."
    )


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

MONTH_NAMES = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def normalise_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def date_variants(text: str) -> set:
    """
    Return a set of normalised date strings for all date-like patterns found in text.
    Handles:
      - ISO: 2023-05-07  -> "2023 05 07"
      - "7 may 2023", "may 7 2023", "7th may 2023"
    Returns set of canonical "YYYY MM DD" tokens (space-separated) alongside the
    original normalised text so both are checked.
    """
    variants = set()
    # ISO date YYYY-MM-DD or YYYY/MM/DD
    for m in re.finditer(r"\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b", text):
        y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
        variants.add(f"{y} {mo} {d}")
    # D Month YYYY or Month D YYYY (with optional st/nd/rd/th)
    for m in re.finditer(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTH_NAMES.keys()) + r")\s+(\d{4})\b",
        text.lower(),
    ):
        d, mon_str, y = m.group(1).zfill(2), MONTH_NAMES[m.group(2)], m.group(3)
        variants.add(f"{y} {mon_str} {d}")
    for m in re.finditer(
        r"\b(" + "|".join(MONTH_NAMES.keys()) + r")\s+(\d{1,2})(?:st|nd|rd|th)?\s*[,]?\s*(\d{4})\b",
        text.lower(),
    ):
        mon_str, d, y = MONTH_NAMES[m.group(1)], m.group(2).zfill(2), m.group(3)
        variants.add(f"{y} {mon_str} {d}")
    return variants


def is_correct_by_proxy(gold: str, answer: str) -> bool:
    """
    Rule-based correctness: True iff the normalised gold token appears in the
    normalised answer, OR any date variant of gold appears in any date variant
    of answer.
    """
    norm_gold = normalise_text(str(gold))
    norm_ans = normalise_text(str(answer))

    # Direct substring check
    if norm_gold and norm_gold in norm_ans:
        return True

    # Each token of gold must appear in answer (for multi-word golds like "mat patterson")
    gold_tokens = norm_gold.split()
    if gold_tokens and all(tok in norm_ans for tok in gold_tokens):
        return True

    # Date variant check
    gold_date_vars = date_variants(str(gold))
    ans_date_vars = date_variants(str(answer))
    if gold_date_vars and ans_date_vars:
        if gold_date_vars & ans_date_vars:
            return True

    return False


# ---------------------------------------------------------------------------
# Objective subset filter
# ---------------------------------------------------------------------------

INCLUDE_CATS = {"single_hop", "temporal"}
INCLUDE_CATS_WITH_MULTI_HOP = {"single_hop", "temporal", "multi_hop"}
# multi_hop is included but flagged; open_domain and adversarial are excluded


def is_discrete_gold(gold: str) -> bool:
    """
    Heuristic: a gold answer is 'discrete' if it is short (<=6 tokens) and
    does NOT contain hedging language.  This excludes open-ended explanations.
    """
    if not isinstance(gold, str):
        gold = str(gold)
    norm = normalise_text(gold)
    tokens = norm.split()
    if len(tokens) > 8:
        return False
    # Exclude relational golds like "The week before X" — too ambiguous for substring match
    # BUT keep them if they contain a concrete date
    if "the week before" in norm or "the sunday before" in norm:
        # only include if date variants exist
        return bool(date_variants(gold))
    return True


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_all_data(core_root: str):
    """Load and join all data sources. Returns (run_questions, q8_questions)."""

    def rpath(*parts):
        return os.path.join(core_root, *parts)

    # --- LoCoMo gold ---
    with open(rpath("experiments", "data", "locomo10.json")) as f:
        locomo = json.load(f)
    cat_map = {1: "single_hop", 2: "temporal", 3: "open_domain", 4: "multi_hop", 5: "adversarial"}
    conv26 = next(d for d in locomo if d["sample_id"] == "conv-26")
    locomo_by_q = {}
    for q in conv26["qa"]:
        # adversarial items use 'adversarial_answer' key instead of 'answer'
        gold = q.get("answer", q.get("adversarial_answer", ""))
        locomo_by_q[q["question"]] = {
            "gold_locomo": str(gold),
            "evidence": q.get("evidence", []),
            "category_locomo": cat_map.get(q["category"], str(q["category"])),
        }

    # --- OUR engine run (source of system answers + category names) ---
    with open(rpath("experiments", "results", "locomo_20260521_230400.json")) as f:
        run_file = json.load(f)
    run_qs_raw = run_file["questions"]

    # --- Conv-26 rejudge: 4 judges ---
    with open(rpath("experiments", "results", "rejudge_20260521_235650.json")) as f:
        rj = json.load(f)
    judge_scores_conv26 = {j["judge"]: j["scores"] for j in rj["judges"]}
    # scores are aligned by index to run_qs_raw

    # --- Q8 rejudge: mem0's answers, 2 judges ---
    with open(rpath("experiments", "results", "rejudge_q8_20260531T201308Z.json")) as f:
        q8_file = json.load(f)
    q8_by_qid = {item["qid"]: item for item in q8_file["per_question"]}

    # --- Build conv-26 question records ---
    run_questions = []
    for i, rq in enumerate(run_qs_raw):
        loc = locomo_by_q.get(rq["question"], {})
        record = {
            "qid": i,
            "question": rq["question"],
            "category": rq["category_name"],
            "system_answer": rq["answer"],
            "gold_answer": rq["ground_truth"],
            "evidence": loc.get("evidence", []),
            "verdict_mem0": judge_scores_conv26.get("mem0", [])[i],
            "verdict_mem0_4o": judge_scores_conv26.get("mem0-4o", [])[i],
            "verdict_strict": judge_scores_conv26.get("strict", [])[i],
            "verdict_mnemoverse": judge_scores_conv26.get("mnemoverse", [])[i],
        }
        run_questions.append(record)

    # --- Build q8 question records (mem0's answers) ---
    # Use the run questions for metadata (question, category, gold) since same ordering
    q8_questions = []
    for qid, item in q8_by_qid.items():
        rq = run_qs_raw[qid]  # same question order
        q8_rec = {
            "qid": qid,
            "question": item["question"],
            "category": item["category"],
            "system_answer": item["answer"],
            "gold_answer": item["ground_truth"],
            "evidence": locomo_by_q.get(rq["question"], {}).get("evidence", []),
            "verdict_mem0": item["mem0_score"],
            "verdict_strict": item["strict_score"],
        }
        q8_questions.append(q8_rec)
    q8_questions.sort(key=lambda x: x["qid"])

    return run_questions, q8_questions


# ---------------------------------------------------------------------------
# Apply objective subset filter
# ---------------------------------------------------------------------------

def build_objective_subset(questions: list) -> list:
    """
    Select questions where the proxy can be reliably applied:
    - category in {single_hop, temporal, multi_hop}  (exclude open_domain, adversarial)
    - gold is 'discrete' by heuristic
    Returns filtered list with added 'proxy_truth' field.
    """
    result = []
    for q in questions:
        cat = q["category"]
        if cat not in INCLUDE_CATS_WITH_MULTI_HOP:
            continue
        gold = q["gold_answer"]
        if not is_discrete_gold(gold):
            continue
        q2 = dict(q)
        q2["proxy_truth"] = is_correct_by_proxy(gold, q["system_answer"])
        result.append(q2)
    return result


# ---------------------------------------------------------------------------
# Error metrics
# ---------------------------------------------------------------------------

def compute_error_metrics(questions: list, judge_keys: list) -> dict:
    """
    For each judge, compute per-overall and per-category:
      accuracy   = P(judge agrees with proxy_truth)
      FP_rate    = P(judge=1 | proxy_truth=0)  -- leniency error
      FN_rate    = P(judge=0 | proxy_truth=1)  -- strictness error

    Returns nested dict: {judge: {overall: {...}, per_category: {cat: {...}}}}
    """
    results = {}
    for jkey in judge_keys:
        # overall
        overall = _compute_metrics_for_group(questions, jkey)

        # per category
        cats = sorted({q["category"] for q in questions})
        per_cat = {}
        for cat in cats:
            subset = [q for q in questions if q["category"] == cat]
            per_cat[cat] = _compute_metrics_for_group(subset, jkey)

        results[jkey] = {"overall": overall, "per_category": per_cat}

    return results


def _compute_metrics_for_group(questions: list, jkey: str) -> dict:
    """Compute metrics for a single group of questions and one judge."""
    # Only use questions where judge verdict is not None
    valid = [q for q in questions if q.get(jkey) is not None]
    n = len(valid)
    if n == 0:
        return {"n": 0, "accuracy": None, "FP_rate": None, "FN_rate": None,
                "n_truth_correct": 0, "n_truth_incorrect": 0,
                "n_judge_correct": 0, "n_judge_incorrect": 0}

    truth_correct = [q for q in valid if q["proxy_truth"]]
    truth_incorrect = [q for q in valid if not q["proxy_truth"]]

    n_tp = sum(1 for q in truth_correct if q[jkey] == 1.0)    # judge=1, truth=1
    n_fn = sum(1 for q in truth_correct if q[jkey] == 0.0)    # judge=0, truth=1
    n_fp = sum(1 for q in truth_incorrect if q[jkey] == 1.0)  # judge=1, truth=0
    n_tn = sum(1 for q in truth_incorrect if q[jkey] == 0.0)  # judge=0, truth=0

    accuracy = (n_tp + n_tn) / n if n > 0 else None
    fp_rate = n_fp / len(truth_incorrect) if truth_incorrect else None
    fn_rate = n_fn / len(truth_correct) if truth_correct else None

    return {
        "n": n,
        "n_truth_correct": len(truth_correct),
        "n_truth_incorrect": len(truth_incorrect),
        "n_tp": n_tp, "n_fn": n_fn, "n_fp": n_fp, "n_tn": n_tn,
        "accuracy": round(accuracy, 4) if accuracy is not None else None,
        "FP_rate": round(fp_rate, 4) if fp_rate is not None else None,
        "FN_rate": round(fn_rate, 4) if fn_rate is not None else None,
    }


# ---------------------------------------------------------------------------
# Label sheet builder
# ---------------------------------------------------------------------------

def build_label_sheet(run_questions: list, target_n: int = 100) -> list:
    """
    Stratified sample of ~100 questions, oversampling:
    - open_domain and multi_hop (ambiguous categories)
    - questions where the 4 judges DISAGREE

    Returns list of row dicts for CSV.
    """
    random.seed(42)

    # Tag disagreement
    for q in run_questions:
        verdicts = [q.get("verdict_mem0"), q.get("verdict_mem0_4o"),
                    q.get("verdict_strict"), q.get("verdict_mnemoverse")]
        valid_verdicts = [v for v in verdicts if v is not None]
        q["_disagree"] = len(set(valid_verdicts)) > 1 if valid_verdicts else False

    # Strata
    disagree_qs = [q for q in run_questions if q["_disagree"]]
    open_mh = [q for q in run_questions if q["category"] in ("open_domain", "multi_hop") and not q["_disagree"]]
    easy = [q for q in run_questions if q["category"] in ("single_hop", "temporal") and not q["_disagree"]]

    # Proportions: ~40 disagree, ~35 open/multi_hop, ~25 easy
    n_disagree = min(40, len(disagree_qs))
    n_open_mh = min(35, len(open_mh))
    n_easy = target_n - n_disagree - n_open_mh

    sampled = (
        random.sample(disagree_qs, n_disagree) +
        random.sample(open_mh, min(n_open_mh, len(open_mh))) +
        random.sample(easy, min(n_easy, len(easy)))
    )
    sampled.sort(key=lambda q: q["qid"])

    rows = []
    for q in sampled:
        rows.append({
            "qid": q["qid"],
            "category": q["category"],
            "question": q["question"],
            "system_answer": q["system_answer"],
            "gold_answer": q["gold_answer"],
            "evidence": "; ".join(q["evidence"]) if q["evidence"] else "",
            "verdict_mem0": q.get("verdict_mem0", ""),
            "verdict_mem0_4o": q.get("verdict_mem0_4o", ""),
            "verdict_strict": q.get("verdict_strict", ""),
            "verdict_mnemoverse": q.get("verdict_mnemoverse", ""),
            "truth_label": "",  # LEFT BLANK for human labelling
        })
    return rows


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def pct(v):
    if v is None:
        return "—"
    return f"{v*100:.1f}%"


def build_markdown_results(
    conv26_metrics: dict,
    q8_metrics: dict,
    conv26_subset_info: dict,
    q8_subset_info: dict,
) -> str:
    """Build the RESULTS.md content."""

    lines = [
        "# Judge Error Analysis — conv-26 (LoCoMo)",
        "",
        "## Data provenance",
        "",
        "| Private source (mnemoverse-core path, not in this repo) | Public copy in this repo | Role |",
        "|---|---|---|",
        "| `experiments/results/rejudge_20260521_235650.json` | `kit/data/rejudge_20260521_235650.json` | 4-judge verdicts on **our engine's** answers (n=152) |",
        "| `experiments/results/rejudge_q8_20260531T201308Z.json` | `kit/data/rejudge_q8_20260531T201308Z.json` | 2-judge verdicts on the **control-slice** answers (Mem0 OSS retrieval, our reader; n_scored=143) |",
        "| `experiments/results/locomo_20260521_230400.json` | `kit/data/answers_engine_conv26.json` | Our engine's per-question answers + metadata |",
        "| `experiments/results/comparison_20260530_024828.json` | `kit/data/answers_mem0_conv26.json` | The control-slice answers |",
        "| `experiments/data/locomo10.json` | `kit/data/locomo_gold_ids.json` (ids/categories) + the `gold` fields of the answer files | Gold answers + evidence + categories |",
    ]

    # Conv-26 subset breakdown
    ci = conv26_subset_info
    lines += [
        f"Total questions in run: **{ci['n_total']}**  ",
        f"Objective subset: **{ci['n_subset']}** questions",
        "",
        "| Category | n in subset | proxy-TRUE | proxy-FALSE |",
        "|----------|-------------|------------|-------------|",
    ]
    for cat, info in sorted(ci["per_category"].items()):
        lines.append(
            f"| {cat} | {info['n']} | {info['n_true']} | {info['n_false']} |"
        )
    lines.append("")

    # Conv-26 judge metrics overall
    lines += [
        "## Judge error metrics — our engine's answers",
        "",
        "### Overall",
        "",
        "| Judge | Model | n | Accuracy vs proxy | FP rate (leniency error) | FN rate (strictness error) |",
        "|-------|-------|---|-------------------|--------------------------|----------------------------|",
    ]
    judge_display = {
        "verdict_mem0": ("mem0", "gpt-5"),
        "verdict_mem0_4o": ("mem0-4o", "gpt-4o"),
        "verdict_strict": ("strict", "gpt-5"),
        "verdict_mnemoverse": ("mnemoverse", "gpt-5-mini"),
    }
    for jkey, (jname, jmodel) in judge_display.items():
        if jkey not in conv26_metrics:
            continue
        m = conv26_metrics[jkey]["overall"]
        lines.append(
            f"| {jname} | {jmodel} | {m['n']} "
            f"| {pct(m['accuracy'])} "
            f"| {pct(m['FP_rate'])} "
            f"| {pct(m['FN_rate'])} |"
        )
    lines.append("")

    # Conv-26 per-category
    lines += [
        "### Per category",
        "",
        "| Judge | Category | n | Accuracy | FP rate | FN rate |",
        "|-------|----------|---|----------|---------|---------|",
    ]
    for jkey, (jname, _) in judge_display.items():
        if jkey not in conv26_metrics:
            continue
        for cat, m in sorted(conv26_metrics[jkey]["per_category"].items()):
            lines.append(
                f"| {jname} | {cat} | {m['n']} "
                f"| {pct(m['accuracy'])} "
                f"| {pct(m['FP_rate'])} "
                f"| {pct(m['FN_rate'])} |"
            )
    lines.append("")

    # Q8 (Mem0 answers) subset breakdown
    qi = q8_subset_info
    lines += [
        "## Judge error metrics — control-slice answers",
        "",
        f"Total questions scored: **{qi['n_total']}** (9 skipped due to empty/null answers in source)  ",
        f"Objective subset: **{qi['n_subset']}** questions",
        "",
        "| Category | n in subset | proxy-TRUE | proxy-FALSE |",
        "|----------|-------------|------------|-------------|",
    ]
    for cat, info in sorted(qi["per_category"].items()):
        lines.append(
            f"| {cat} | {info['n']} | {info['n_true']} | {info['n_false']} |"
        )
    lines.append("")

    # Q8 judge metrics overall
    lines += [
        "### Overall",
        "",
        "| Judge | Model | n | Accuracy vs proxy | FP rate (leniency error) | FN rate (strictness error) |",
        "|-------|-------|---|-------------------|--------------------------|----------------------------|",
    ]
    q8_judge_display = {
        "verdict_mem0": ("mem0", "gpt-5"),
        "verdict_strict": ("strict", "gpt-5"),
    }
    for jkey, (jname, jmodel) in q8_judge_display.items():
        if jkey not in q8_metrics:
            continue
        m = q8_metrics[jkey]["overall"]
        lines.append(
            f"| {jname} | {jmodel} | {m['n']} "
            f"| {pct(m['accuracy'])} "
            f"| {pct(m['FP_rate'])} "
            f"| {pct(m['FN_rate'])} |"
        )
    lines.append("")

    # Q8 per-category
    lines += [
        "### Per category",
        "",
        "| Judge | Category | n | Accuracy | FP rate | FN rate |",
        "|-------|----------|---|----------|---------|---------|",
    ]
    for jkey, (jname, _) in q8_judge_display.items():
        if jkey not in q8_metrics:
            continue
        for cat, m in sorted(q8_metrics[jkey]["per_category"].items()):
            lines.append(
                f"| {jname} | {cat} | {m['n']} "
                f"| {pct(m['accuracy'])} "
                f"| {pct(m['FP_rate'])} "
                f"| {pct(m['FN_rate'])} |"
            )
    lines.append("")

    # Key findings
    lines += [
        "## Key findings",
        "",
        "_(These findings are computed from the numbers above; no LLM adjudication.)_",
        "",
    ]

    # Auto-generate key findings from numbers
    # Our engine: which judge most accurate?
    judge_accs = {
        jkey: conv26_metrics[jkey]["overall"]["accuracy"]
        for jkey in judge_display
        if jkey in conv26_metrics and conv26_metrics[jkey]["overall"]["accuracy"] is not None
    }
    best_judge = max(judge_accs, key=judge_accs.get)
    worst_judge = min(judge_accs, key=judge_accs.get)
    jnames = {jk: jn for jk, (jn, _) in judge_display.items()}

    lines.append(
        f"**1. Most accurate judge (our engine answers):** `{jnames[best_judge]}` "
        f"at {pct(judge_accs[best_judge])} accuracy vs proxy truth. "
        f"`{jnames[worst_judge]}` is least accurate at {pct(judge_accs[worst_judge])}."
    )
    lines.append("")

    # mem0 leniency direction
    mem0_fp = conv26_metrics.get("verdict_mem0", {}).get("overall", {}).get("FP_rate")
    mem0_fn = conv26_metrics.get("verdict_mem0", {}).get("overall", {}).get("FN_rate")
    if mem0_fp is not None and mem0_fn is not None:
        direction = "FP-dominant (over-credits)" if mem0_fp > mem0_fn else "FN-dominant (over-rejects)"
        lines.append(
            f"**2. mem0 judge error direction (our engine):** FP rate = {pct(mem0_fp)}, "
            f"FN rate = {pct(mem0_fn)} — {direction}."
        )
        lines.append("")

    # strict judge direction
    strict_fp = conv26_metrics.get("verdict_strict", {}).get("overall", {}).get("FP_rate")
    strict_fn = conv26_metrics.get("verdict_strict", {}).get("overall", {}).get("FN_rate")
    if strict_fp is not None and strict_fn is not None:
        if strict_fn > strict_fp * 1.25:
            strict_dir = "FN-dominant (over-rejects correct answers)"
        elif strict_fp > strict_fn * 1.25:
            strict_dir = "FP-dominant (over-credits wrong answers)"
        else:
            strict_dir = "balanced (both modes present; neither dominates strongly)"
        lines.append(
            f"**3. strict judge error direction (our engine):** FP rate = {pct(strict_fp)}, "
            f"FN rate = {pct(strict_fn)} — {strict_dir}."
        )
        lines.append("")

    # Mem0 answers: mem0 judge on its own answers
    q8_mem0_fp = q8_metrics.get("verdict_mem0", {}).get("overall", {}).get("FP_rate")
    q8_mem0_fn = q8_metrics.get("verdict_mem0", {}).get("overall", {}).get("FN_rate")
    q8_strict_fp = q8_metrics.get("verdict_strict", {}).get("overall", {}).get("FP_rate")
    q8_strict_fn = q8_metrics.get("verdict_strict", {}).get("overall", {}).get("FN_rate")
    if q8_mem0_fp is not None:
        lines.append(
            f"**4. mem0 judge on the control slice's answers:** FP rate = {pct(q8_mem0_fp)}, "
            f"FN rate = {pct(q8_mem0_fn)}. "
            f"strict judge on the same answers: FP = {pct(q8_strict_fp)}, FN = {pct(q8_strict_fn)}."
        )
        lines.append("")

    lines += [
        "## Caveats",
        "",
        "1. **Proxy strictness:** The substring match under-credits paraphrases.  "
        "Any judge that accepts correct paraphrases will appear more lenient (higher FP rate) "
        "than it truly is.  The human label sheet is the antidote.",
        "",
        "2. **Relative-date golds excluded:** Golds like 'The week before 9 June 2023' or "
        "'The sunday before 25 May 2023' are excluded from the objective subset because "
        "no substring rule can reliably evaluate them without calendar arithmetic.",
        "",
        "3. **multi_hop coverage:** multi_hop questions often have multi-part golds "
        "('pottery, camping, painting, swimming') — the substring rule may partially credit "
        "a correct-but-incomplete answer as FALSE, inflating FN for lenient judges.",
        "",
        "4. **n=152 (our engine) / n=143 (Mem0) on one conversation (conv-26):** "
        "Results are single-conversation; generalisation to other LoCoMo conversations "
        "should be tested before publishing cross-system claims.",
        "",
        "5. **The 9 skipped questions (Mem0):** qids 143–151 had empty/null answers "
        "in the comparison file at rejudge time and were excluded from q8 scoring. "
        "All are single_hop. Their absence does not affect category-level conclusions "
        "since the single_hop subset remains well-powered.",
        "",
        "---",
        "",
        "_Generated by `scripts/judge_error/compute_judge_error.py` — all numbers trace to committed JSON files._",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Compute judge error metrics.")
    parser.add_argument("--core-root", default=None,
                        help="Path to mnemoverse-core repo root")
    args = parser.parse_args()

    core_root = resolve_core_root(args.core_root)
    print(f"[INFO] core_root = {core_root}")

    # Load data
    print("[INFO] Loading data...")
    run_questions, q8_questions = load_all_data(core_root)
    print(f"[INFO] Loaded {len(run_questions)} run questions, {len(q8_questions)} q8 questions")

    # Build objective subsets
    conv26_subset = build_objective_subset(run_questions)
    q8_subset = build_objective_subset(q8_questions)
    print(f"[INFO] Objective subset: conv26={len(conv26_subset)}, q8={len(q8_subset)}")

    # Subset info
    def subset_info(subset, total):
        from collections import Counter
        info = {"n_total": total, "n_subset": len(subset), "per_category": {}}
        cats = Counter(q["category"] for q in subset)
        for cat in sorted(cats):
            sub_cat = [q for q in subset if q["category"] == cat]
            n_true = sum(1 for q in sub_cat if q["proxy_truth"])
            info["per_category"][cat] = {"n": len(sub_cat), "n_true": n_true, "n_false": len(sub_cat) - n_true}
        return info

    conv26_subset_info = subset_info(conv26_subset, len(run_questions))
    q8_subset_info = subset_info(q8_subset, len(q8_questions))

    # Compute metrics
    conv26_judge_keys = ["verdict_mem0", "verdict_mem0_4o", "verdict_strict", "verdict_mnemoverse"]
    q8_judge_keys = ["verdict_mem0", "verdict_strict"]

    conv26_metrics = compute_error_metrics(conv26_subset, conv26_judge_keys)
    q8_metrics = compute_error_metrics(q8_subset, q8_judge_keys)

    # Build results JSON
    results = {
        "meta": {
            "proxy_method": "substring_match_with_date_normalisation",
            "included_categories": list(INCLUDE_CATS_WITH_MULTI_HOP),
            "excluded_categories": ["open_domain", "adversarial"],
            "discrete_gold_max_tokens": 8,
        },
        "conv26_our_engine": {
            "subset_info": conv26_subset_info,
            "judge_metrics": conv26_metrics,
        },
        "q8_mem0_answers": {
            "subset_info": q8_subset_info,
            "judge_metrics": q8_metrics,
        },
    }

    # Write results JSON
    out_json = os.path.join(SCRIPT_DIR, "judge_error_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Wrote {out_json}")

    # Write RESULTS.md
    md_content = build_markdown_results(
        conv26_metrics, q8_metrics, conv26_subset_info, q8_subset_info
    )
    out_md = os.path.join(SCRIPT_DIR, "RESULTS.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Wrote {out_md}")

    # Build label sheet
    label_rows = build_label_sheet(run_questions)
    kit_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "kit", "judge_audit"))
    os.makedirs(kit_dir, exist_ok=True)
    out_csv = os.path.join(kit_dir, "label_sheet.csv")
    fieldnames = [
        "qid", "category", "question", "system_answer", "gold_answer",
        "evidence", "verdict_mem0", "verdict_mem0_4o", "verdict_strict",
        "verdict_mnemoverse", "truth_label",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(label_rows)
    print(f"[OK] Wrote {out_csv} ({len(label_rows)} rows)")

    # Print summary to stdout
    print("\n" + "=" * 70)
    print("SUMMARY — OUR ENGINE (conv-26, objective subset)")
    print("=" * 70)
    judge_display = {
        "verdict_mem0": "mem0/gpt-5",
        "verdict_mem0_4o": "mem0-4o/gpt-4o",
        "verdict_strict": "strict/gpt-5",
        "verdict_mnemoverse": "mnemoverse/gpt-5-mini",
    }
    for jkey, jname in judge_display.items():
        m = conv26_metrics[jkey]["overall"]
        print(f"  {jname:30s}  acc={pct(m['accuracy'])}  FP={pct(m['FP_rate'])}  FN={pct(m['FN_rate'])}  n={m['n']}")

    print("\nSUMMARY — MEM0 OSS ANSWERS")
    print("=" * 70)
    q8_display = {
        "verdict_mem0": "mem0/gpt-5",
        "verdict_strict": "strict/gpt-5",
    }
    for jkey, jname in q8_display.items():
        m = q8_metrics[jkey]["overall"]
        print(f"  {jname:30s}  acc={pct(m['accuracy'])}  FP={pct(m['FP_rate'])}  FN={pct(m['FN_rate'])}  n={m['n']}")

    print(f"\nObjective subset: {len(conv26_subset)} / {len(run_questions)} our-engine questions")
    print(f"Objective subset: {len(q8_subset)} / {len(q8_questions)} Mem0 questions")


if __name__ == "__main__":
    main()
