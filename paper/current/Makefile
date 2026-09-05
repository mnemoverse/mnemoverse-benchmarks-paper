LATEX = pdflatex
LATEX_FLAGS = -interaction=nonstopmode -halt-on-error
BIBTEX = bibtex
MAIN = main

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex ../refs.bib
	$(LATEX) $(LATEX_FLAGS) $(MAIN)
	-$(BIBTEX) $(MAIN)
	$(LATEX) $(LATEX_FLAGS) $(MAIN)
	$(LATEX) $(LATEX_FLAGS) $(MAIN)

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out $(MAIN).toc

.PHONY: all clean
