#!/usr/bin/env python3
"""Check that the summary is written in its own words.

Every file of the summary is compared with the part of the LaTeX edition (latex/) it summarizes.
Reported per file:

  * the share of the summary's six-word sequences that also occur in the book;
  * the longest run of consecutive words shared with the book outside quotation marks
    (titles and headings, which are the book's own by design, are not counted);
  * the longest shared run inside quotation marks (sayings of historical persons and
    short phrases of the author that the summary quotes as such).

Usage:  python3 tools/summary_overlap.py [options]
  --max-run N     fail (exit status 1) if an unquoted shared run is longer than N words (default 9)
  --max-quote N   fail if a quoted shared run is longer than N words (default 45)
  --list N        list every unquoted shared run of at least N words with its sentence
  --quotes N      list every quoted shared run of at least N words
  --only NAME     restrict the report to files whose name contains NAME (e.g. ch41)

The list of popes is a table of names and years taken over in full and is not part of this check.
"""
import re, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 6

STRUCT = [r'\\summarychapter\{\d+\}\{(?P<a>[^{}]*)\}\{(?P<b>[^{}]*)\}',
          r'\\ssection\{(?P<a>(?:[^{}]|\{[^{}]*\})*)\}',
          r'\\begin\{sidebox\}\{(?P<a>(?:[^{}]|\{[^{}]*\})*)\}',
          r'\\pch\{\d+\}\{(?P<a>[^{}]*)\}\{(?P<b>[^{}]*)\}',
          r'\\summarypart\{\w+\}\{(?P<a>[^{}]*)\}\{(?P<b>[^{}]*)\}',
          r'\\age\{\d+\}\{(?P<a>[^{}]*)\}\{(?P<b>[^{}]*)\}',
          r'\\(?:front|back)chapter\{(?P<a>[^{}]*)\}']

def tokens(tex):
    """List of (word, kind, start, end); kind is '' (plain), 'q' (in quotation marks) or 's' (title)."""
    blank = lambda m: ' ' * len(m.group(0))
    spans = []
    for pat in STRUCT:
        for m in re.finditer(pat, tex):
            for g in ('a', 'b'):
                if g in m.groupdict() and m.group(g) is not None:
                    spans.append(m.span(g))
    t = re.sub(r'(?<!\\)%[^\n]*', blank, tex)
    t = t.replace("``", '\x01 ').replace("''", '\x02 ').replace('\u201c', '\x01').replace('\u201d', '\x02')
    t = re.sub(r'\n[ \t]*\n', lambda m: '\x03' + ' ' * (len(m.group(0)) - 1), t)
    t = re.sub(r"\\['`^\"~=.]", '  ', t)
    t = re.sub(r'\\(?:begin|end)\{[^}]*\}', blank, t)
    t = re.sub(r'\\[a-zA-Z@]+\*?', blank, t)
    out, quoted = [], False
    for m in re.finditer(r"[\x01\x02\x03]|[A-Za-z0-9]+(?:['\u2019][a-z]+)?", t):
        tok = m.group(0)
        if tok == '\x01':
            quoted = True
        elif tok in '\x02\x03':
            quoted = False
        else:
            kind = 'q' if quoted else ''
            if any(a <= m.start() < b for a, b in spans):
                kind = 's'
            out.append((tok.lower().replace('\u2019', "'"), kind, m.start(), m.end()))
    return out

def shared_runs(stoks, btoks):
    """Maximal runs of summary tokens (i, j) that occur as consecutive words in the book."""
    sw = [t[0] for t in stoks]
    bw = [t[0] for t in btoks]
    index = {}
    for j in range(len(bw) - N + 1):
        index.setdefault(tuple(bw[j:j + N]), []).append(j)
    reach = [0] * len(sw)                 # reach[i]: end of the longest shared run starting at i
    hits = 0
    for i in range(len(sw) - N + 1):
        cands = index.get(tuple(sw[i:i + N]))
        if not cands:
            continue
        hits += 1
        best = N
        for j in cands:
            k = N
            while i + k < len(sw) and j + k < len(bw) and sw[i + k] == bw[j + k]:
                k += 1
            best = max(best, k)
        reach[i] = i + best
    runs, i = [], 0
    while i < len(sw):
        if reach[i]:
            end = reach[i]
            j = i + 1
            while j < end:                # runs that overlap are merged
                end = max(end, reach[j])
                j += 1
            runs.append((i, end))
            i = end
        else:
            i += 1
    return runs, 100.0 * hits / max(1, len(sw) - N + 1)

def pieces(stoks, runs, kind_wanted):
    """Split the shared runs into stretches of plain ('') or quoted ('q') words."""
    out = []
    for a, b in runs:
        i = a
        while i < b:
            if stoks[i][1] == kind_wanted:
                j = i
                while j < b and stoks[j][1] == kind_wanted:
                    j += 1
                out.append((i, j))
                i = j
            else:
                i += 1
    return out

def sentence(tex, start, end):
    a = start
    while a > 0 and not re.match(r'[.?!]["\')\u201d]*\s|\n[ \t]*\n|\}\s*\n', tex[a - 1:a + 3]) and start - a < 400:
        a -= 1
    b = end
    while b < len(tex) and not re.match(r'[.?!]', tex[b]) and tex[b:b + 2] != '\n\n' and b - end < 400:
        b += 1
    text = tex[a:start] + '[[' + tex[start:end] + ']]' + tex[end:b + 1]
    return re.sub(r'\s+', ' ', text).strip()

def pairs():
    j = os.path.join
    out = []
    for f in sorted(glob.glob(j(ROOT, 'summary', 'chapters', 'ch*.tex'))):
        num = int(re.search(r'ch(\d+)\.tex$', f).group(1))
        out.append((f, [j(ROOT, 'latex', 'chapters', 'chapter%02d.tex' % num)]))
    for f in sorted(glob.glob(j(ROOT, 'summary', 'parts', 'part*.tex'))):
        out.append((f, [j(ROOT, 'latex', 'parts', os.path.basename(f))]))
    front = [j(ROOT, 'latex', 'frontmatter', n) for n in ('foreword.tex', 'prologue.tex')]
    parts = sorted(glob.glob(j(ROOT, 'latex', 'parts', 'part*.tex')))
    out.append((j(ROOT, 'summary', 'front', 'foreword-prologue.tex'), front))
    out.append((j(ROOT, 'summary', 'front', 'glance.tex'), front + parts))
    out.append((j(ROOT, 'summary', 'front', 'about.tex'), front))
    out.append((j(ROOT, 'summary', 'back', 'epilogue.tex'), [j(ROOT, 'latex', 'backmatter', 'epilogue.tex')]))
    out.append((j(ROOT, 'summary', 'back', 'notes.tex'), [j(ROOT, 'latex', 'backmatter', 'notes.tex')]))
    return [(f, s) for f, s in out if os.path.exists(f)]

def opt(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

def main():
    max_run, max_quote = opt('--max-run', 9), opt('--max-quote', 45)
    list_n, quote_n = opt('--list', 0), opt('--quotes', 0)
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''
    worst = worst_q = 0
    tot_s = tot_b = tot_run = 0
    print('file                     summary    book  ratio  shared 6-grams  longest run  in quotes')
    for f, sources in pairs():
        name = os.path.basename(f)
        if only and only not in name:
            continue
        tex = open(f, encoding='utf-8').read()
        stoks = tokens(tex)
        btoks = []
        for s in sources:
            btoks += tokens(open(s, encoding='utf-8').read()) + [('\x00', '', 0, 0)]
        runs, pct = shared_runs(stoks, btoks)
        plain = pieces(stoks, runs, '')
        quoted = pieces(stoks, runs, 'q')
        lp = max([b - a for a, b in plain], default=0)
        lq = max([b - a for a, b in quoted], default=0)
        worst, worst_q = max(worst, lp), max(worst_q, lq)
        tot_s += len(stoks); tot_b += len(btoks)
        tot_run += sum(b - a for a, b in plain if b - a >= 8)
        flag = '  <--' if lp > max_run or lq > max_quote else ''
        print(f'{name:24s} {len(stoks):7d} {len(btoks):7d}  {100*len(stoks)/max(1,len(btoks)):4.0f}%     {pct:5.1f}%'
              f'         {lp:3d}        {lq:3d}{flag}')
        if list_n:
            for a, b in plain:
                if b - a >= list_n:
                    print(f'   {b - a:2d}: ' + sentence(tex, stoks[a][2], stoks[b - 1][3]))
        if quote_n:
            for a, b in quoted:
                if b - a >= quote_n:
                    print(f'   q{b - a:2d}: ' + sentence(tex, stoks[a][2], stoks[b - 1][3]))
    print(f'total {tot_s} words against {tot_b}; words in unquoted shared runs of 8 or more: {tot_run}')
    print(f'longest unquoted shared run: {worst} words (limit {max_run}); longest quoted: {worst_q} (limit {max_quote})')
    sys.exit(1 if worst > max_run or worst_q > max_quote else 0)

if __name__ == '__main__':
    main()
