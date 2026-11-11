# Summary volume

`church-history-summary.pdf` is a complete summary of the book: every chapter is summarized
section by section, under the section headings of the original. It has 381 pages in a 6 × 9 inch
format, with a linked table of contents and PDF bookmarks down to the section headings.

| Part of the volume | What it holds |
| --- | --- |
| Front matter | title page, note on the summary, contents, "The Book at a Glance", foreword and prologue |
| Nine parts, 48 chapters | part overview and chapter list; per chapter an "In brief" box with the chapter's question, one section per original heading (216 in all), the 30 sidebars, the 3 tables, and key people, dates and terms |
| Back matter | epilogue (both authors), a description of the book's notes, a chronology of all 378 chapter dates, the list of popes in full |

The reading lists and the text of the source notes are described but not reproduced; the
pictures and timelines of the printed book are left out.

## Files

```
summary.tex          main file (pdfLaTeX; run three times)
summarybook.sty      design: page, fonts, colours, all commands and placement rules
front/               title page, note on the summary, the book at a glance, foreword and prologue
parts/part1..9.tex   the nine part pages with their overviews and chapter lists
chapters/ch01..48.tex
back/                epilogue.tex, notes.tex (written by hand)
                     chronology.tex, popes.tex (generated, do not edit)
church-history-summary.pdf   the compiled volume
```

Build:

```
python3 tools/summary_extras.py      # writes back/chronology.tex and back/popes.tex
cd summary && pdflatex summary && pdflatex summary && pdflatex summary
```

Three runs are needed: the second settles the contents and the links, the third the dates that
are repeated in the chronology after a page break. The packages used are in every TeX Live
(`mathpazo`, `helvet`, `microtype`, `mdframed`, `booktabs`, `multicol`, `hyperref`, ...).
The last build ends with no overfull or underfull boxes, no warnings and no errors.

## Checks

| Command | What it checks |
| --- | --- |
| `python3 tools/summary_check.py` | every chapter is present with the book's title and subtitle, and every section heading and sidebar of the original has its counterpart, in the same order |
| `python3 tools/summary_overlap.py` | the wording is the summary's own: no stretch of more than 8 consecutive words is shared with the book outside quotation marks (titles and headings excepted); `--list 8` shows the stretches, `--quotes 25` the long quotations |
| `python3 tools/summary_extras.py --check` | chronology and list of popes are up to date with the chapters |
| `python3 tools/summary_dashes.py --check` | no spaced em dashes |

Current state: 48 of 48 chapters, about 96,000 words in the chapters (the book has about
196,000); six-word sequences shared with the book make up between 0.5 and 6.2 percent per
chapter, most of them names, dates and quoted sayings.

## How a chapter file is built

```latex
\summarychapter{1}{Title}{Subtitle}
\begin{inbrief} two or three sentences \question{the question the chapter asks} \end{inbrief}
opening paragraph (the anecdote the chapter starts with)
\ssection{Heading of the original, in title case}  ...one per original section, same order...
\begin{sidebox}{Title of the sidebar} ... \end{sidebox}
\begin{sumtable}[Caption]{L{0.47\linewidth}L{0.47\linewidth}}
\sumhead{Column} & \sumhead{Column} \\ \midrule
cell & cell \\
\end{sumtable}
\begin{keyfacts}
\keypeople{...}
\keydates{\kd{312}{event} \kd{c. 30}{event}}
\keyterms{...}
\end{keyfacts}
```

Other commands: `\summarypart{ONE}{Title}{dates}`, `partoverview`, `\partchapters{\pch{n}{Title}{Subtitle}...}`
for the part pages; `\frontchapter{Title}` and `\backchapter{Title}` for unnumbered chapters;
`chronology` (`\chronhead`, `\chron`, `\chronmore`) and `popecolumns` (`\pope`) in the generated files.

## Conventions

- The summary is written in new words and reports what the book says. Judgments of the author
  are marked as his ("Shelley argues ..."); nothing is added from outside the book. Words taken
  over from the book stand in quotation marks.
- Titles, subtitles and section headings are the book's own, in the book's order.
- Plain TeX input is used for punctuation: ``` ``quotes'' ```, `--` in ranges, unspaced `---` dashes.
- Every `\kd` entry must read on its own, because all of them are collected into the chronology:
  name the person, country or body ("Luther posts the Ninety-five Theses", not "The theses posted").
  Date forms: `381`, `c. 140`, `374--383`, `AD 70`, `332 BC`, `2nd century`, `1960s`.
- A sentence that introduces a table must not depend on the table following at once (see below).

## Placement rules (in `summarybook.sty`)

- **Sidebars** stand where they are written if the page has room. Otherwise they go, in one
  piece, to the top of the next page while the text runs on. Only a sidebar longer than 0.6 of a
  page may run over a page break, and then with several lines on each side.
- **Tables** are never divided; a table that does not fit goes to the top of the next page.
- **Key facts** close the chapter. The block stays in one piece where it fits; otherwise it
  breaks between two entries, and the last three dates stay with the key terms.
- **Part pages**: the chapter list is never divided, and the heading block moves up a little
  when that lets the list stay on the part page.
- **Chronology**: when a page break falls among several events of one year, the year is printed
  again at the top of the new page.
