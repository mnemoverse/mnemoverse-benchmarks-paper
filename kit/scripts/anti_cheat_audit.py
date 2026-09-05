# NOTE (kit excerpt): This script is excerpted from scripts/anti_cheat_audit.py
# in the mnemoverse-core repository for reference. It is self-contained with
# no internal imports, but two things to be aware of when running it outside
# the original repo:
#   1. `REPO_ROOT` (line ~36) is inferred as `Path(__file__).resolve().parent.parent`.
#      When running from a different repo, pass `--root <repo-root>` to point
#      the scanner at the correct directory tree.
#   2. `SCOPE_GLOBS` (line ~38-44) targets `src/mnemo/**/*.py` and
#      `experiments/benchmarks/competitors/**/*.py`. Adjust these globs to
#      match your own codebase layout when adapting the gate.
# The detection patterns (gold-label field names + allow-marker convention)
# are fully portable and require no modification.

"""Anti-cheat gate — gold-label leakage detector.

Scans engine code, competitor adapters, and SDK prompts for any reference to
LoCoMo gold-label fields that must NEVER reach inference time:

    qa.category           # cat=5 hint (used by symmetric filter pre-run only)
    qa.evidence           # gold support list
    adversarial_answer    # ground-truth contrast
    qa_adversarial        # ground-truth contrast (alt key)
    dia_id                # dialogue-id leak (positional alignment)

Plan reference: SYMMETRIC_V1_PLAN_DRAFT.md §3-4 (G1 — gold-label leakage gate).
Scope: src/mnemo/**, experiments/benchmarks/competitors/*,
       docs/sdk-prompts/*.
Allow-marker: a `# anti-cheat-allow: <reason>` comment on the SAME line
(or the line directly above) suppresses one match. Required for fixture
builders, the symmetric pre-filter, and disclosure-doc snippets.

Usage:
    python scripts/anti_cheat_audit.py             # human report
    python scripts/anti_cheat_audit.py --json      # machine-readable
    python scripts/anti_cheat_audit.py --root .    # override repo root

Exit codes: 0 = clean, 1 = violations, 2 = setup error (no scope dirs).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCOPE_GLOBS = [
    "src/mnemo/**/*.py",
    "experiments/benchmarks/competitors/**/*.py",
    # docs/sdk-prompts/** scope is reserved for the SDK prompts artifact —
    # re-add (with the *.md / *.txt suffixes) once that directory lands.
    # Glob is excluded for now to avoid silent drift; the path didn't exist
    # as of 2026-06-10.
]

# Exempted-by-design paths (documented to prevent drift):
#   experiments/benchmarks/locomo/**       — LoCoMo dataset loader + grader.
#     dataset.py constructs gold-label structs; evaluate.py runs judges on
#     engine output. Reading qa.evidence / qa.category is THE JOB of the
#     grading harness. The leakage gate protects engine + competitor adapter
#     code paths only — never the grading harness itself.
#   experiments/benchmarks/shared/**       — judge / scoring utilities; same
#     reasoning as locomo/ (grading-side, never reaches engine inference).
#   experiments/benchmarks/_harness/compute_recall.py
#                                          — recall@k metric; needs
#     evidence_dia_ids to compute the metric. Grading-side.

# Tuple of (pattern_regex, human_label, suggestion).
PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        # \b so `qa.category` matches but `qa.category_name` does not — the
        # category_name token is the human label the judge prompt uses for
        # rubric assembly, not a gold signal the engine is allowed to read.
        re.compile(r"qa\.category\b"),
        "qa.category",
        "qa.answer",  # the reference answer itself (F-L3: reader-path bypass)
        "Use the pre-run symmetric filter; engine MUST NOT branch on category at inference.",
    ),
    (
        re.compile(r"qa\.evidence\b"),
        "qa.evidence",
        "Gold support is for grading only. Never read evidence in retrieval/reader code.",
    ),
    (
        re.compile(r"adversarial_answer"),
        "adversarial_answer",
        "Ground-truth contrast — judge-only. Never reference in engine/competitor adapter.",
    ),
    (
        re.compile(r"qa_adversarial"),
        "qa_adversarial",
        "Ground-truth contrast (alt key) — judge-only.",
    ),
    (
        re.compile(r"\bdia_id\b"),
        "dia_id",
        "Dialogue id leak; positional qids only. Use qid scheme per GAP-001.",
    ),
]

ALLOW_MARKER = re.compile(r"#\s*anti-cheat-allow\s*:\s*(?P<reason>.+?)\s*$")


@dataclass
class Violation:
    file: str
    line: int
    pattern: str
    match: str  # the matched substring (truncated)
    suggestion: str


def _iter_scope_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for g in SCOPE_GLOBS:
        files.extend(root.glob(g))
    # de-dup, deterministic order
    return sorted({f.resolve() for f in files if f.is_file()})


_COMMENT_LINE = re.compile(r"^\s*#")


def _line_is_allowed(
    line: str,
    prev_line: str | None,
    prev_block: list[str] | None = None,
) -> bool:
    """Allow if the SAME line carries the marker, OR a contiguous '#'-comment
    block immediately above the violation contains the marker.

    Prev-block form (introduced 2026-06-10, R1 fix) closes the window=1
    blind-spot: a multi-line disclosure comment placed above a violation
    used to suppress only its last line. Now any line in the contiguous
    comment block (read backward until the first non-comment line) counts.

    `prev_line` is kept for backward compatibility with the synthetic
    fixture tests; `prev_block` (when supplied) is the canonical path.
    """
    if ALLOW_MARKER.search(line):
        return True
    if prev_block:
        return any(ALLOW_MARKER.search(b) for b in prev_block)
    return bool(prev_line and ALLOW_MARKER.search(prev_line))


def scan_file(path: Path, root: Path) -> list[Violation]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    out: list[Violation] = []
    lines = text.splitlines()
    rel = str(path.relative_to(root)).replace("\\", "/")
    for i, line in enumerate(lines, start=1):
        prev = lines[i - 2] if i >= 2 else None
        # Walk back over a contiguous '#'-comment block above the violation
        # so a multi-line disclosure header can carry the allow-marker.
        # When the violating line is itself a comment (multi-line disclosure
        # that happens to mention `dia_id` etc.), keep walking back through
        # the comment block to find the marker — every comment line in a
        # block belongs to the same disclosure.
        prev_block: list[str] = []
        j = i - 2  # zero-based index of the line above
        while j >= 0 and _COMMENT_LINE.match(lines[j]):
            prev_block.append(lines[j])
            j -= 1
        if _line_is_allowed(line, prev, prev_block):
            continue
        for pat_re, label, suggestion in PATTERNS:
            m = pat_re.search(line)
            if m:
                out.append(
                    Violation(
                        file=rel,
                        line=i,
                        pattern=label,
                        match=line.strip()[:200],
                        suggestion=suggestion,
                    )
                )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="anti_cheat_audit",
        description="Gold-label leakage gate (SYMMETRIC_V1_PLAN_DRAFT.md G1).",
    )
    p.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help=f"Repo root (default: {REPO_ROOT}).",
    )
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output.")
    args = p.parse_args(argv)

    files = _iter_scope_files(args.root)
    if not files:
        print(f"anti_cheat_audit: no files under {SCOPE_GLOBS}", file=sys.stderr)
        return 2
    violations: list[Violation] = []
    for f in files:
        violations.extend(scan_file(f, args.root))

    if args.json:
        print(
            json.dumps(
                {
                    "scanned": len(files),
                    "violations": [asdict(v) for v in violations],
                    "exit_code": 1 if violations else 0,
                },
                indent=2,
            )
        )
        return 1 if violations else 0

    if not violations:
        print(f"anti_cheat_audit: clean ({len(files)} files scanned).")
        return 0
    print(f"anti_cheat_audit: {len(violations)} violations across {len(files)} files\n")
    for v in violations:
        print(f"  {v.file}:{v.line}: matched `{v.pattern}`")
        print(f"    > {v.match}")
        print(f"    hint: {v.suggestion}")
        print(
            "    suppress: append `# anti-cheat-allow: <reason>` to the line above or end-of-line.\n"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
