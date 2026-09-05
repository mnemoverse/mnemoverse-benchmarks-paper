#!/usr/bin/env bash
# Local build (Windows Git Bash / machines without `make`).
#
# Runs the pdflatex -> bibtex -> pdflatex x2 cycle TOLERANTLY (the first pdflatex
# pass legitimately returns non-zero on undefined-cite warnings before bibtex runs,
# and MiKTeX's bibtex "check for updates" is a harmless nag), then FAILS CLOSED:
# exits non-zero if the final PDF is missing or the final log still shows undefined
# citations/references or asks for a rerun. A reproducibility gate must not report
# success on a broken build.
cd "$(dirname "$0")" || exit 1

pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true
bibtex   main                          >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main >/dev/null 2>&1 || true

fail=0
[ -f main.pdf ] || { echo "FAIL: main.pdf was not produced"; fail=1; }
grep -aq "Output written on main.pdf" main.log 2>/dev/null \
  || { echo "FAIL: no 'Output written on main.pdf' in main.log"; fail=1; }
grep -aq "Citation.*undefined"            main.log 2>/dev/null && { echo "FAIL: undefined citations remain"; fail=1; }
grep -aq "There were undefined references" main.log 2>/dev/null && { echo "FAIL: undefined references"; fail=1; }
grep -aq "Rerun to get"                    main.log 2>/dev/null && { echo "FAIL: labels changed, rerun needed"; fail=1; }
grep -aq "^! "                             main.log 2>/dev/null && { echo "FAIL: TeX error in final pass:"; grep -a -m3 "^! " main.log; fail=1; }

grep -aoE "Output written on main.pdf \([0-9]+ pages?, [0-9]+ bytes\)" main.log | tail -1

if [ "$fail" -ne 0 ]; then
  echo "BUILD FAILED"
  exit 1
fi
echo "BUILD OK"
exit 0
