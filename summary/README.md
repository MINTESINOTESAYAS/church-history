# Summary volume

`church-history-summary.pdf` is a complete summary of the book: every chapter is summarized
section by section, under the section headings of the original.

## Files

```
summary.tex          main file (pdfLaTeX; run twice)
summarybook.sty      design: page, fonts, colours, all commands
front/               title page, note on the summary, the book at a glance, foreword and prologue
parts/part1..9.tex   the nine part pages with their overviews
chapters/ch01..48.tex
back/                epilogue, notes, chronology (generated), list of popes (generated)
```

Build:

```
python3 tools/summary_extras.py      # writes back/chronology.tex and back/popes.tex
cd summary && pdflatex summary && pdflatex summary
```

`python3 tools/summary_check.py` checks that every chapter is present with the right title and
that each section heading and sidebar of the original has its counterpart, in the same order.

## How a chapter file is built

```latex
\summarychapter{1}{Title}{Subtitle}
\begin{inbrief} two or three sentences \question{the question the chapter asks} \end{inbrief}
opening paragraph (the anecdote the chapter starts with)
\ssection{Heading of the original, in title case}  ...one per original section, same order...
\begin{sidebox}{Title of the sidebar} ... \end{sidebox}
\begin{keyfacts}
\keypeople{...}
\keydates{\kd{312}{event} \kd{c. 30}{event}}
\keyterms{...}
\end{keyfacts}
```

Conventions: the summary is written in new words and reports what the book says (author's
judgments are marked as such: "Shelley argues ..."); nothing is added from outside the book.
Plain TeX input is used for punctuation (``quotes'', `--` in ranges, unspaced `---` dashes).
The `\kd` entries of all chapters are collected into the chronology at the back.
