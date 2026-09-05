#!/usr/bin/env python3
"""Inter-annotator agreement for the external-annotation campaign (single-stream protocol).

Usage:
  python analyze_kappa.py returned/cases_AU_labels.json [returned/cases_OI_labels.json ...]

Feed it the FINAL returned JSON per annotator (partial files are for backup only).
It reconstructs the three sets via annotator_key_mapping.json (source_set) and prints:
  - catch-case report (>=2 fails = the pre-registered rejection gate)
  - speed report (median seconds between consecutive verdicts; first_ts preferred)
  - per set: % agreement, Cohen's kappa (3-way) with bootstrap 95% CI,
    both-decided binary kappa, Gwet's AC1 (standard companion for skewed B/C),
    every disagreement listed
  - with 2+ externals: pairwise external kappas and Fleiss' kappa (incl. the author)
  - the load-bearing reconstruction: per-annotator and majority "X of 121"
    (B+C CORRECT = strict false rejection), plus shared-question B/C pairs for eyes

=== PRE-REGISTERED ANALYSIS PLAN (fixed before any labels arrive; the git commit
=== of this file is the timestamp):
  PRIMARY: Fleiss' kappa over all available raters (author + externals) on the
           validation set (set_a, non-catch, n=54), 3 categories.
  Reported unconditionally alongside: each pairwise Cohen's kappa (3-way, with
  bootstrap 95% CI), both-decided binary kappa, % agreement, AC1 for set_b/set_c,
  per-annotator and majority "X of 121".
  Landis-Koch labels are attached to the CI LOWER BOUND, not the point estimate.
  ANNOTATOR EXCLUSION: only via the catch gate (>=2 of 5 catches failed), decided
  before looking at any agreement statistic. Remedy for a failed gate with known
  annotators: calibration call + relabel, not silent drop.
  HEADLINE RECONCILIATION: the paper's "97 of 121" moves to the 3-rater majority;
  the author-only number is retained beside it for comparison. Golden-judge
  validation is recomputed against majority AND against each annotator separately.
  SENSITIVITY: kappa for annotator AU recomputed excluding EXCLUDE_AU_CONTAMINATED
  (cases whose author-verdicts are quoted in the paper draft AU reviewed).

No third-party deps. Thresholds (Landis & Koch): >=0.61 substantial, 0.41-0.60 moderate.
"""
import json, sys, random, statistics
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations

HERE = Path(__file__).resolve().parent
KIT_AUDIT = HERE.parent / "judge_audit"

MAPPING = json.loads((HERE / "annotator_key_mapping.json").read_text(encoding="utf-8"))["cases"]
SETS = ("set_a", "set_b", "set_c")

# masked_ids (q###) whose author-verdicts are quoted/identifiable in the paper draft
# that annotator AU reviewed. FILL BEFORE ANALYZING AU (grep the draft for quoted
# examples: "trans"/"transgender woman", "last year"/2022, etc.), then commit.
EXCLUDE_AU_CONTAMINATED: set = set()

BOOT_N = 2000
random.seed(20260705)

def author_labels():
    """source_set -> {source_qid(str): verdict}"""
    out = {}
    v = json.loads((KIT_AUDIT / "human_labels_validation_set.json").read_text(encoding="utf-8"))
    out["set_a"] = {str(l["qid"]): l["human_verdict"] for l in v["labels"]}
    c = json.loads((KIT_AUDIT / "human_labels_control_slice.json").read_text(encoding="utf-8"))
    out["set_b"] = {str(l["qid"]): l["human_verdict"] for l in c["labels"]}
    e = json.loads((KIT_AUDIT / "human_labels_engine_side.json").read_text(encoding="utf-8"))
    out["set_c"] = {str(l["exhibit_id"]): l["human_verdict"] for l in e["labels"]}
    return out

# ---------- statistics ----------------------------------------------------------

def cohen_kappa(pairs):
    """pairs: list of (label1, label2). Returns (kappa|None, n). None = undefined
    (degenerate marginals), NOT perfect agreement."""
    n = len(pairs)
    if n == 0:
        return None, 0
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(1 for a, b in pairs if a == b) / n
    m1, m2 = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((m1[c] / n) * (m2[c] / n) for c in cats)
    if pe >= 1.0 - 1e-12:
        return None, n
    return (po - pe) / (1 - pe), n

def boot_ci(pairs, stat=cohen_kappa):
    """Percentile bootstrap 95% CI for a pair statistic. Returns (lo, hi) or None."""
    n = len(pairs)
    if n < 10:
        return None
    vals = []
    for _ in range(BOOT_N):
        sample = [pairs[random.randrange(n)] for _ in range(n)]
        k, _ = stat(sample)
        if k is not None:
            vals.append(k)
    if len(vals) < BOOT_N * 0.5:
        return None
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))]

def gwet_ac1(pairs):
    """Gwet's AC1 for two raters, multi-category. Robust to skewed prevalence."""
    n = len(pairs)
    if n == 0:
        return None
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    if len(cats) < 2:
        return None
    pa = sum(1 for a, b in pairs if a == b) / n
    m1, m2 = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pi = {c: (m1[c] + m2[c]) / (2 * n) for c in cats}
    pe = sum(p * (1 - p) for p in pi.values()) / (len(cats) - 1)
    if pe >= 1.0 - 1e-12:
        return None
    return (pa - pe) / (1 - pe)

def fleiss_kappa(rows, cats):
    """rows: list of Counter(category -> votes), same total raters per row."""
    rows = [r for r in rows if sum(r.values()) >= 2]
    if not rows:
        return None, 0
    n_raters = sum(rows[0].values())
    rows = [r for r in rows if sum(r.values()) == n_raters]
    N = len(rows)
    P_i = [(sum(v * v for v in r.values()) - n_raters) / (n_raters * (n_raters - 1)) for r in rows]
    P_bar = sum(P_i) / N
    p_j = [sum(r[c] for r in rows) / (N * n_raters) for c in cats]
    P_e = sum(p * p for p in p_j)
    if P_e >= 1.0 - 1e-12:
        return None, N
    return (P_bar - P_e) / (1 - P_e), N

def interp(k):
    if k is None: return "undefined (degenerate marginals)"
    return ("almost perfect" if k >= 0.81 else "substantial" if k >= 0.61 else
            "moderate" if k >= 0.41 else "fair" if k >= 0.21 else "slight/poor")

def fmt_k(k, ci=None):
    if k is None:
        return "undefined (degenerate marginals)"
    s = f"{k:.3f}"
    if ci:
        s += f" [95% CI {ci[0]:.3f}, {ci[1]:.3f}] -> label by lower bound: {interp(ci[0])}"
    else:
        s += f" ({interp(k)})"
    return s

# ---------- main -----------------------------------------------------------------

def main(paths):
    ed = author_labels()
    by_id = {m["masked_id"]: m for m in MAPPING}
    catch_ids = {m["masked_id"] for m in MAPPING if m["is_catch"]}

    # external[annotator] = {masked_id: label-record}
    external = {}
    for p in paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        ann = str(d.get("annotator", "unknown")).strip().upper()
        got = {l["id"]: l for l in d["labels"] if l.get("verdict")}
        if ann in external:
            print(f"WARNING: duplicate annotator '{ann}' — merging {p} over earlier file")
            external[ann].update(got)
        else:
            external[ann] = got
        ack = d.get("instructions_ack")
        ack_s = (f"ack={ack.get('version')}@{ack.get('ts')}" if isinstance(ack, dict)
                 else "ack=NONE (pre-v2 export — instruction-regime split applies, see TZ)")
        print(f"loaded {p}: annotator={ann} labeled={len(got)}/180  {ack_s}")

    for ann, got in external.items():
        print(f"\n{'='*72}\nANNOTATOR {ann}\n{'='*72}")
        # --- catch gate (pre-registered exclusion path) ---
        fails = []
        for m in MAPPING:
            if not m["is_catch"]:
                continue
            v = got.get(m["masked_id"], {}).get("verdict", "(missing)")
            if v != m["catch_expected"]:
                fails.append((m["masked_id"], m["source_qid"], m["catch_expected"], v))
        print(f"CATCH GATE: {5-len(fails)}/5 passed" + ("" if not fails else f"  FAILED: {fails}"))
        if len(fails) >= 2:
            print("  *** >=2 catch failures: PRE-REGISTERED GATE TRIPPED -> calibration call + relabel ***")
        # --- speed report ---
        ts = sorted((l.get("first_ts") or l.get("ts")) for l in got.values() if l.get("ts") or l.get("first_ts"))
        gaps = [(b - a) / 1000 for a, b in zip(ts, ts[1:]) if 0 < (b - a) < 600_000]
        if gaps:
            med = statistics.median(gaps)
            q1, q3 = statistics.quantiles(gaps, n=4)[0], statistics.quantiles(gaps, n=4)[2]
            print(f"SPEED: median {med:.0f}s/case (IQR {q1:.0f}-{q3:.0f}) over {len(gaps)} gaps"
                  + ("  *** <10s median: speed-run flag ***" if med < 10 else ""))
        # --- agreement vs the author, per reconstructed set ---
        for set_key in SETS:
            pairs, disagreements = [], []
            for m in MAPPING:
                if m["source_set"] != set_key or m["is_catch"]:
                    continue
                e_v = ed[set_key].get(m["source_qid"])
                x = got.get(m["masked_id"], {})
                if e_v and x.get("verdict"):
                    pairs.append((e_v, x["verdict"]))
                    if e_v != x["verdict"]:
                        disagreements.append((m["masked_id"], m["source_qid"], e_v, x["verdict"], x.get("note", "")))
            if not pairs:
                print(f"[{set_key}] no overlap yet"); continue
            k3, n3 = cohen_kappa(pairs)
            agree = sum(1 for a, b in pairs if a == b)
            print(f"[{set_key}] vs author: n={n3}  agreement={agree}/{n3} ({100*agree/n3:.1f}%)"
                  f"  kappa_3way={fmt_k(k3, boot_ci(pairs))}")
            if set_key in ("set_b", "set_c"):
                print(f"[{set_key}] Gwet's AC1 (skew-robust companion): "
                      + (f"{gwet_ac1(pairs):.3f}" if gwet_ac1(pairs) is not None else "undefined"))
            dec = [(a, b) for a, b in pairs if a != "AMBIGUOUS" and b != "AMBIGUOUS"]
            k2, n2 = cohen_kappa(dec)
            if n2:
                print(f"[{set_key}] both-decided binary: n={n2}  kappa={fmt_k(k2)}")
            for d_ in disagreements:
                print(f"    DISAGREE {d_[0]} (src {d_[1]}): author={d_[2]}  {ann}={d_[3]}  note='{d_[4]}'")
        # --- sensitivity: AU minus paper-contaminated items ---
        if ann == "AU" and EXCLUDE_AU_CONTAMINATED:
            pairs = []
            for m in MAPPING:
                if m["is_catch"] or m["masked_id"] in EXCLUDE_AU_CONTAMINATED:
                    continue
                e_v = ed[m["source_set"]].get(m["source_qid"])
                x = got.get(m["masked_id"], {})
                if e_v and x.get("verdict"):
                    pairs.append((e_v, x["verdict"]))
            k, n = cohen_kappa(pairs)
            print(f"SENSITIVITY (AU, minus {len(EXCLUDE_AU_CONTAMINATED)} paper-quoted cases): "
                  f"n={n} kappa={fmt_k(k, boot_ci(pairs))}")

    # ---- multi-rater ----
    anns = sorted(external)
    if len(anns) >= 2:
        print(f"\n{'='*72}\nPAIRWISE EXTERNAL + FLEISS (PRIMARY on set_a)\n{'='*72}")
        for set_key in SETS:
            ids = [m["masked_id"] for m in MAPPING if m["source_set"] == set_key and not m["is_catch"]]
            for a1, a2 in combinations(anns, 2):
                pairs = [(external[a1][i]["verdict"], external[a2][i]["verdict"])
                         for i in ids if i in external[a1] and i in external[a2]]
                k, n = cohen_kappa(pairs)
                if n:
                    print(f"[{set_key}] {a1} vs {a2}: n={n} kappa={fmt_k(k, boot_ci(pairs))}")
            rows = []
            for m in MAPPING:
                if m["source_set"] != set_key or m["is_catch"]:
                    continue
                votes = Counter()
                e_v = ed[set_key].get(m["source_qid"])
                if e_v:
                    votes[e_v] += 1
                for a in anns:
                    v = external[a].get(m["masked_id"], {}).get("verdict")
                    if v:
                        votes[v] += 1
                if sum(votes.values()) == len(anns) + 1:
                    rows.append(votes)
            fk, fn = fleiss_kappa(rows, ["CORRECT", "WRONG", "AMBIGUOUS"])
            tag = "  <<< PRIMARY (pre-registered)" if set_key == "set_a" else ""
            if fn:
                print(f"[{set_key}] Fleiss (author + {len(anns)} externals): n={fn} kappa={fmt_k(fk)}{tag}")

    # ---- the load-bearing reconstruction: "X of 121" ----
    print(f"\n{'='*72}\n'X of 121' RECONSTRUCTION (set_b + set_c; CORRECT = strict false rejection)\n{'='*72}")
    pool = [m for m in MAPPING if m["source_set"] in ("set_b", "set_c") and not m["is_catch"]]
    def dist(fn_v):
        c = Counter(fn_v(m) for m in pool)
        return f"CORRECT={c['CORRECT']}  WRONG={c['WRONG']}  AMBIGUOUS={c['AMBIGUOUS']}  (missing={c[None]})"
    print(f"author : {dist(lambda m: ed[m['source_set']].get(m['source_qid']))}")
    for a in anns:
        print(f"{a:7s}: {dist(lambda m: external[a].get(m['masked_id'], {}).get('verdict'))}")
    if len(anns) >= 1:
        def majority(m):
            votes = Counter()
            e_v = ed[m["source_set"]].get(m["source_qid"])
            if e_v: votes[e_v] += 1
            for a in anns:
                v = external[a].get(m["masked_id"], {}).get("verdict")
                if v: votes[v] += 1
            if not votes: return None
            top, cnt = votes.most_common(1)[0]
            return top if cnt > sum(votes.values()) / 2 else "AMBIGUOUS"  # no majority -> ambiguous
        print(f"MAJORITY (no-majority -> AMBIGUOUS): {dist(majority)}")
        print("Pre-registered rule: the paper's headline '97 of 121' moves to the majority "
              "CORRECT count; the author-only number is retained beside it.")

    # ---- shared-question B/C pairs: within-annotator consistency, for eyes ----
    print(f"\n{'='*72}\nSHARED-QUESTION B/C PAIRS (consistency probe, informational)\n{'='*72}")
    import re as _re
    def nq(s): return _re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    src = {}
    for m in MAPPING:
        if m["is_catch"]: continue
        src.setdefault(m["source_set"], {})[m["masked_id"]] = m
    # need questions: pull from the shipped tool's data via mapping order
    tool = json.loads(_re.search(r"const DATA = (\{.*?\});\n",
             (HERE / "label-annotator.html").read_text(encoding="utf-8"), _re.S).group(1))
    qtext = {c["qid"]: c["question"] for c in tool["cases"]["cases"]}
    b_ids = {nq(qtext[i]): i for i in src.get("set_b", {})}
    n_pairs = 0
    for ci_ in src.get("set_c", {}):
        key = nq(qtext[ci_])
        if key in b_ids:
            n_pairs += 1
            bi = b_ids[key]
            row = " | ".join(f"{a}: B={external[a].get(bi, {}).get('verdict', '-')}"
                             f"/C={external[a].get(ci_, {}).get('verdict', '-')}" for a in anns)
            print(f"  {bi}<->{ci_}  {row}")
    print(f"({n_pairs} shared-question pairs)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
