#!/usr/bin/env python3
"""Convert the plain-text book in the repository root into the LaTeX project in latex/.

    python3 tools/build_latex.py            # (re)write latex/*.tex
    python3 tools/build_latex.py --report   # also list the places decided by hand or left open

The text of the book is never retyped: every word comes from the .txt files.  What this
script adds is structure (paragraphs, headings, quotations, sidebars, lists ...), which
is recovered from the typeset line widths (see textmodel.py and segment.py) together with
the hand-checked annotations in structure_data.py.
"""
import os
import sys

import emit
from emit import tex, wrap
import segment as S
from textmodel import SRC, join_texts, short_name, src_files

OUT = os.path.join(SRC, 'latex')


def header(srcname):
    return '%% Source: %s\n' % srcname


def build():
    ctx = S.Ctx()
    files = {}          # relative path -> content
    order = []          # (relative path without .tex, source file name)
    contents = S.parse_contents()
    ch_short = {c['num']: c for c in contents if c['t'] == 'chapter'}
    part_lines = [c['text'] for c in contents if c['t'] == 'part']
    simple = [c['text'] for c in contents if c['t'] == 'entry']   # Foreword, Prologue, Epilogue, Notes, Popes, Indexes

    def put(rel, srcpath, body):
        name = os.path.basename(srcpath)
        files[rel + '.tex'] = header(name) + body.rstrip('\n') + '\n'
        order.append((rel, name))

    npart = 0
    for path in src_files():
        key = short_name(path)
        base = os.path.basename(path)
        if key == '02_':
            put('frontmatter/dedication', path, emit.lines_env('dedication', S.parse_dedication()))
        elif key == '03_':
            out = [r'\frontchapter[Contents]{%s}{fm:contents}' % tex(contents[0]['text'])]
            labels = {'Foreword': 'fm:foreword', 'Prologue': 'fm:prologue', 'Epilogue': 'bm:epilogue',
                      'Notes': 'bm:notes', 'List of Popes from Leo I to the Present': 'bm:popes'}
            np = 0
            for c in contents[1:]:
                if c['t'] == 'chapter':
                    out.append(r'\tocchapter{%s}{%s}{%s}{ch:%d}' % (tex(c['label']), tex(c['title']), tex(c['subtitle']), c['num']))
                elif c['t'] == 'part':
                    np += 1
                    out.append('')
                    out.append(r'\tocpart{%s}{part:%d}' % (tex(c['text']), np))
                elif c['text'] in labels:
                    if c['text'] == 'Epilogue':
                        out.append('')
                    out.append(r'\tocentry{%s}{%s}' % (tex(c['text']), labels[c['text']]))
                else:                                   # "Indexes ...": listed, but not part of the text source
                    out.append(r'\tocentryplain{%s}' % tex(c['text']))
            put('frontmatter/contents', path, '\n'.join(out))
        elif key in ('04_', '05_'):
            els = S.parse_front(key, ctx, [1, 2, 1] if key == '04_' else [1])
            short, label = ('Foreword', 'fm:foreword') if key == '04_' else ('Prologue', 'fm:prologue')
            assert short in simple
            out = [r'\frontchapter[%s]{%s}{%s}' % (short, tex(els[0]['text']), label)] + emit.blocks(els[1:])
            put('frontmatter/' + short.lower(), path, '\n\n'.join(out))
        elif 'Chapter_' in base:
            els = S.parse_chapter(path, ctx)
            h = els[0]
            c = ch_short[h['num']]
            out = [r'\bookchapter[%s]{%s}{%s}{%s}' % (tex(c['title']), tex(h['label']), tex(join_texts(h['title'])), tex(h['subtitle']))]
            body = [e for e in els[1:] if e['t'] not in ('bibhead', 'biblines')]
            out += emit.blocks(body)
            bh = next(e for e in els if e['t'] == 'bibhead')
            bl = next(e for e in els if e['t'] == 'biblines')
            out.append(r'\readinghead{%s}' % tex(bh['text']) + '\n' + emit.entries_env('readinglist', S.seg_bib(bl['key'], bl['lines'], ctx)))
            put('chapters/chapter%02d' % h['num'], path, '\n\n'.join(out))
        elif key == '63_':
            els = S.parse_epilogue(ctx)
            out = [r'\backchapter[Epilogue]{%s}{bm:epilogue}' % tex(els[0]['text'])] + emit.blocks(els[1:])
            put('backmatter/epilogue', path, '\n\n'.join(out))
        elif key == '64_':
            nt = S.parse_notes(ctx)
            out = [r'\backchapter[Notes]{%s}{bm:notes}' % tex(nt['title'])]
            for g in nt['groups']:
                out.append(r'\noteshead{%s}' % tex(g['head']) + '\n' + emit.entries_env('notelist', g['entries']))
            put('backmatter/notes', path, '\n\n'.join(out))
        elif key == '65_':
            pp = S.parse_popes()
            out = [r'\backchapter[List of Popes from Leo I to the Present]{%s}{bm:popes}' % tex(pp['title']),
                   wrap(r'\popesintro{%s}' % tex(pp['intro'])),
                   '\\begin{popelist}\n%s\n\\end{popelist}' % '\n'.join(r'\pope{%s}{%s}' % (tex(d), tex(n)) for d, n in pp['pairs']),
                   emit.lines_env('popelegend', pp['legend'])]
            put('backmatter/popes', path, '\n\n'.join(out))
        else:                                           # part divider
            d = S.parse_divider(key)
            npart += 1
            line = part_lines[npart - 1]
            assert line.endswith(d['dates']), (line, d['dates'])
            short = line[:-len(d['dates'])].strip()
            out = [r'\bookpart[%s]{%s}{%s}' % (tex(short), tex(d['title']), tex(d['dates'])),
                   '\\begin{partsummary}\n%s\n\\end{partsummary}' % wrap(tex(d['summary'])),
                   r'\timelinetitle{%s}' % tex(d['timeline'])]
            put('parts/part%d' % npart, path, '\n\n'.join(out))

    # main file
    m = [r'% A LaTeX edition of the plain-text book in this repository.',
         r'% Compile with pdflatex (recommended), xelatex or lualatex; run twice for page references.',
         r'\documentclass[11pt,twoside,openany]{book}',
         r'\usepackage{churchhistory}',
         '',
         r'% To typeset only a few files while editing, e.g.:',
         r'% \includeonly{chapters/chapter01,chapters/chapter02}',
         '',
         r'\begin{document}', '', r'\frontmatter']
    state = 'front'
    for rel, name in order:
        if state == 'front' and (rel.startswith('parts/') or rel.startswith('chapters/')):
            m += ['', r'\mainmatter']
            state = 'main'
        if state == 'main' and rel.startswith('backmatter/'):
            m += ['', r'\backmatter']
            state = 'back'
        if rel.startswith('parts/'):
            m.append('')
        m.append(r'\include{%s}' % rel)
    m += ['', r'\end{document}']
    files['main.tex'] = '\n'.join(m) + '\n'
    return files, order, ctx


def main():
    files, order, ctx = build()
    for rel, content in files.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
    print('wrote %d files to %s' % (len(files), OUT))
    unused = (ctx.breaks | ctx.joins) - ctx.used
    if unused:
        print('WARNING: unused overrides:', sorted(unused))
    for a in ctx.anom:
        print('note: %s line %d: %s | %s' % (a[0], a[1], a[2], a[3][:70]))
    if '--report' in sys.argv:
        print('%d paragraph ends were proven by the indent of the following line' % len(ctx.auto))
        print('%d places where a hidden paragraph or entry break is possible but was not made:' % len(ctx.ambig))
        for a in ctx.ambig:
            print('   %s line %d (%s): ...%s || %s...' % (a[0], a[1], a[2], a[3].text[-40:], a[4].text[:40]))


if __name__ == '__main__':
    main()
