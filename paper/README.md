# paper/

- `current/` — live LaTeX source (arXiv target): `main.tex`, `build.sh` (fail-closed
  pdflatex+bibtex; use this on Windows), `Makefile`. Build artifacts are untracked.
- `refs.bib` — shared bibliography (every entry field-verified against arXiv).
- Release-candidate PDFs and the review archive (three external rounds, an adversarial
  audit, a citation-fit pass) are kept outside the public tree; the released state of the
  paper is the git tag `arxiv-v1`, created at the arXiv v1 release (see the repository's Releases page).
