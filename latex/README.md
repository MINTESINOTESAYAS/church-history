# LaTeX edition

This directory is a LaTeX version of the plain-text files in the repository root.
The text itself is unchanged; structure (paragraphs, headings, quotations, sidebars,
lists, tables, reading lists, notes) was reconstructed and marked up.

## Building

```
cd latex
pdflatex main && pdflatex main      # two runs for the page numbers in the contents
```

`latexmk -pdf main` works as well. On Overleaf, set `latex/main.tex` as the main document.

| Engine   | Status                          | Result                                         |
|----------|---------------------------------|------------------------------------------------|
| pdfLaTeX | tested (TeX Live 2022)          | 608 pages, Palatino, no overfull boxes         |
| XeLaTeX  | tested (TeX Live 2022)          | 581 pages with the Latin Modern fallback font  |
| LuaLaTeX | supported in the style, untested | —                                              |

Packages used: `geometry`, `microtype`, `fancyhdr`, `array`, `booktabs`, `multicol`,
`hyperref`, `iftex`, plus `mathpazo` (pdfLaTeX) or `fontspec` (XeLaTeX/LuaLaTeX; TeX Gyre
Pagella is used when it is installed).

To typeset only part of the book while editing, uncomment the `\includeonly` line in `main.tex`.

## Layout of the project

```
main.tex              document skeleton: one \include per source file, in book order
churchhistory.sty     page size, fonts and every structural command (the only style file)
frontmatter/          dedication, contents, foreword, prologue
parts/part1..9.tex    the nine part dividers
chapters/chapter01..48.tex
backmatter/           epilogue, notes, list of popes
```

The first line of every file names the `.txt` file it was made from.

## Markup

All formatting lives in `churchhistory.sty`; the content files only use these commands.

| Markup | Meaning |
|---|---|
| `\bookpart[Short]{TITLE}{DATES}`, `partsummary`, `\timelinetitle{…}` | part divider page |
| `\bookchapter[Short]{CHAPTER N}{TITLE}{Subtitle}` | chapter opening; the short title feeds the running head and PDF outline |
| `\frontchapter[Short]{TITLE}{label}`, `\backchapter…` | unnumbered chapters |
| `\leadin{W}{ORDS IN CAPITALS}` | the capitalised opening words of a chapter |
| `\section{…}` | section heading (capitals as in the source) |
| `blockquote` | block quotation |
| `poem` | verse and creeds, one source line per line |
| `sidebar` + `\sidebarhead{…}` | boxed aside ("text box") |
| `numlist` with `\item[1.]` | numbered list, labels as in the source |
| `booktable` + `\tabletitle{…}` | the three tables |
| `\figcaption{…}`, `\figtitle{…}` | caption or title of a picture, chart, map or timeline |
| `readinglist`, `notelist` with `\entry` | reading lists and notes (hanging entries) |
| `popelist` with `\pope{dates}{name}` | list of popes |

Change the page size in the `geometry` line of the style file. For chapters that always
start on a right-hand page, see the comment at `\ch@openchapter`.

## How the text was converted

The `.txt` files are a line-by-line dump of a typeset edition: one typeset line per text
line, blank lines only at page breaks. Paragraphs and blocks are therefore not marked.
They were recovered from line widths (the original used greedy line breaking, so the last
line of a paragraph, an indented first line, or a narrower block can be recognised by
measuring the line) and from a hand-checked table of block positions. See `../tools/`.

Verification: `python3 tools/verify_text.py` strips the LaTeX markup again and compares
the result with the `.txt` files character by character. Result: 64 files, 195,608 words,
identical. The text extracted from the compiled PDFs was compared with the sources in the
same way.

### What is inferred, and what is missing

* **Paragraph breaks.** Most are certain. Where the last line of a paragraph happened to
  fill the full width, the layout shows nothing: 81 such breaks were proven by the indent
  of the next line, 89 were decided by reading, and at about 350 further places a hidden
  break is possible but none was made. `python3 tools/build_latex.py --report` lists them;
  add an entry to `BREAK_AFTER` in `tools/structure_data.py` to split one.
* **Italics** are not recorded in the source, so book titles and emphasis are upright.
* **Pictures, charts, maps and timelines** are not in the source. Their captions and
  titles are kept (`\figcaption`, `\figtitle`, `\timelinetitle`) at the place where they occur.
* **Indexes** are listed in the contents but there is no source file for them.
* The three **tables** were rebuilt by hand from their cell text.
* There is **no title page**: the source files begin with the dedication.
* Two files in the repository root are byte-identical duplicates (`… (1).txt`) and were skipped.

### Deliberate departures from the source characters

* `¬†` (a mis-decoded no-break space, twice in the Epilogue) is typeset as a normal space.
* Spacing only: non-breaking spaces inside spaced ellipses (`. . .`), a thin space between
  adjacent closing quotation marks, and `\url{…}` around the two web addresses.
* Everything else is kept as it is, including apparent typos, a footnote mark `[1]`
  without a note, and a web address that carries a line-break hyphen.

## Regenerating

```
python3 tools/build_latex.py     # rewrites latex/**/*.tex and main.tex (not the .sty)
python3 tools/verify_text.py
```

Only the Python standard library is needed. The generated files can also simply be edited
by hand; just do not run the converter again afterwards.
