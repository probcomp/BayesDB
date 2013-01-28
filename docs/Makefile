# Makefile for LaTeX files
# (c) 2002 Hanna Wallach

FILENAME = predictiveTabularDatabases

all: pdf

.PHONY: clean

pdf: $(FILENAME).pdf

$(FILENAME).pdf: $(FILENAME).tex
	pdflatex $(FILENAME)

clean:
	rm -f *.aux *.log *.pdf *.dvi *.blg *.bbl *~
