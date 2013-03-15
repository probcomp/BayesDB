# Makefile for LaTeX files
# (c) 2002 Hanna Wallach

FILENAME = predictiveTabularDatabases

all: pdf

.PHONY: clean

pdf: $(FILENAME).pdf

experimental: $(FILENAME)_experimental.pdf

%.pdf: %.tex
	pdflatex $<

clean:
	rm -f *.aux *.log *.pdf *.dvi *.blg *.bbl *~
