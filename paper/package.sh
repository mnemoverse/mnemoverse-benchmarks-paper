#!/usr/bin/env bash
# Package the paper into a SELF-CONTAINED bundle that compiles with nothing above
# its own root. Two consumers, one bundle:
#   1. Overleaf  -- drag-drop paper/dist/arxiv/ into a new project, set main.tex as
#      the main document, and it compiles. (main.tex in git reaches ../refs and
#      ../../figures; an Overleaf/arXiv project has no parent, so we flatten.)
#   2. arXiv     -- `paper/dist/judge-benchmark.zip` includes the generated main.bbl,
#      which is what arXiv wants (it does not run bibtex).
#
# The git repo stays the source of truth: this bundle is a DERIVED artifact, like the
# frozen PDFs. main.tex in git keeps its ../ paths untouched; only the bundled copy is
# rewritten. Round-trip (pulling co-author edits back) is kept in the maintainers' internal docs.
#
#   bash paper/package.sh
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1                 # repo root
PYBIN="${PYTHON:-$(command -v python3 || command -v python || true)}"
[ -n "$PYBIN" ] || { echo "FAIL: no python3/python on PATH (set PYTHON=/path/to/python3)"; exit 1; }

SRC=paper/current
OUT=paper/dist/arxiv
mkdir -p "$OUT/figures"

# --- copy inputs into a flat, parent-free tree -------------------------------
cp "$SRC/main.tex"                       "$OUT/main.tex"
cp paper/refs.bib                        "$OUT/refs.bib"
cp figures/crossconv_swing.pdf           "$OUT/figures/"
cp figures/recall_k_curve.pdf            "$OUT/figures/"
cp figures/table_judge_swing.tex         "$OUT/figures/"

# --- rewrite the four out-of-dir paths (and NOTHING else) --------------------
#   ../../figures/  -> figures/      (keep a figures/ subdir; arXiv + Overleaf allow it)
#   ../refs         -> refs
"${PYBIN}" - "$OUT/main.tex" <<'PY'
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
before = s
s = s.replace("../../figures/", "figures/")
s = s.replace(r"\bibliography{../refs}", r"\bibliography{refs}")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
# fail loudly if a parent-reaching path survives in a COMPILED (non-comment) line --
# a stray "../" inside a % comment is inert and left as-is.
def code(ln):
    return ln.split("%", 1)[0]
leftover = [ln for ln in s.splitlines() if "../" in code(ln)]
if leftover:
    sys.exit("path rewrite incomplete, '../' remains in code:\n  " + "\n  ".join(leftover))
print(f"rewrote parent-reaching paths -> self-contained (comment-only '../' left inert)")
PY

# --- compile IN the bundle to prove it is self-contained + emit main.bbl -----
( cd "$OUT"
  pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true
  bibtex   main                          >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true )

log="$OUT/main.log"
fail=0
[ -f "$OUT/main.pdf" ] || { echo "FAIL: bundle did not produce main.pdf"; fail=1; }
[ -f "$OUT/main.bbl" ] || { echo "FAIL: no main.bbl (arXiv needs it)"; fail=1; }
grep -aq "Output written on main.pdf"      "$log" 2>/dev/null || { echo "FAIL: no output line"; fail=1; }
grep -aq "Citation.*undefined"             "$log" 2>/dev/null && { echo "FAIL: undefined citations"; fail=1; }
grep -aq "There were undefined references" "$log" 2>/dev/null && { echo "FAIL: undefined references"; fail=1; }
[ "$fail" -eq 0 ] || { echo "BUNDLE BUILD FAILED"; exit 1; }

pages=$(grep -aoE "Output written on main.pdf \(([0-9]+) page" "$log" | grep -oE "[0-9]+" | head -1)
echo "BUNDLE OK: $OUT/main.pdf ($pages pages), main.bbl present"

# --- arXiv tarball: sources + .bbl, no build litter --------------------------
zip=paper/dist/judge-benchmark.zip
rm -f "$zip"
( cd "$OUT" && zip -q -r "../../../$zip" main.tex refs.bib main.bbl figures )
echo "arXiv bundle: $zip"
echo
echo "Overleaf: New Project -> Upload Project -> $zip  (or drag paper/dist/arxiv/*)."
echo "          Set main.tex as the Main document. It compiles as-is."
