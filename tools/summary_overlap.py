#!/usr/bin/env python3
"""Check that the summary is written in its own words.

For every summary chapter the script compares the wording with the corresponding chapter of the
LaTeX edition (latex/chapters) and reports

  * the share of the summary's six-word sequences that also occur in the book, and
  * the longest run of consecutive words shared with the book, once overall and once
    outside quotation marks (quoted sayings of historical persons are expected to agree).

Usage:  python3 tools/summary_overlap.py [--max-run N] [--show]
        --max-run N   exit with status 1 if an unquoted shared run is longer than N words (default 9)
        --show        print the longest shared run of every chapter
"""
import re, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def tokens(tex):
    """(word, in_quotes) pairs of a LaTeX text."""
    tex = re.sub(r'(?<!\\)%.*', '', tex)
    tex = tex.replace("``", ' \x01 ').replace("''", ' \x02 ').replace('\u201c', ' \x01 ').replace('\u201d', ' \x02 ')
    tex = re.sub(r"\\['`^\"~=.]\s*\{?([A-Za-z])\}?", r'\1', tex)          # accents
    tex = re.sub(r'\\(begin|end)\{[^}]*\}', ' ', tex)
    tex = re.sub(r'\\[a-zA-Z@]+\*?', ' ', tex)
    tex = re.sub(r'[{}~\\]', ' ', tex)
    out, quoted = [], False
    for tok in re.findall(r"[\x01\x02]|[A-Za-z0-9]+(?:['\u2019][a-z]+)?", tex):
        if tok == '\x01':
            quoted = True
        elif tok == '\x02':
            quoted = False
        else:
            out.append((tok.lower().replace('\u2019', "'"), quoted))
    return out

def compare(summary, source, n=6):
    s = tokens(summary)
    sw = [w for w, q in s]
    bw = [w for w, q in tokens(source)]
    index = {}
    for j in range(len(bw) - n + 1):
        index.setdefault(tuple(bw[j:j + n]), []).append(j)
    grams = max(1, len(sw) - n + 1)
    shared = sum(1 for i in range(len(sw) - n + 1) if tuple(sw[i:i + n]) in index)
    best = (0, 0); best_unq = (0, 0)
    for i in range(len(sw) - n + 1):
        for j in index.get(tuple(sw[i:i + n]), ()):
            k = n
            while i + k < len(sw) and j + k < len(bw) and sw[i + k] == bw[j + k]:
                k += 1
            if k > best[0]:
                best = (k, i)
            # longest stretch inside this run that lies outside quotation marks
            run = 0
            for t in range(i, i + k):
                run = 0 if s[t][1] else run + 1
                if run > best_unq[0]:
                    best_unq = (run, t - run + 1)
    return len(sw), len(bw), 100.0 * shared / grams, best, best_unq, sw

def main():
    limit = 9
    if '--max-run' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--max-run') + 1])
    show = '--show' in sys.argv
    worst = 0; total_s = total_b = 0
    print('chapter  summary    book  shared 6-grams  longest run  outside quotes')
    for f in sorted(glob.glob(os.path.join(ROOT, 'summary', 'chapters', 'ch*.tex'))):
        num = int(re.search(r'ch(\d+)\.tex$', f).group(1))
        src = os.path.join(ROOT, 'latex', 'chapters', 'chapter%02d.tex' % num)
        ns, nb, pct, best, unq, sw = compare(open(f, encoding='utf-8').read(), open(src, encoding='utf-8').read())
        total_s += ns; total_b += nb; worst = max(worst, unq[0])
        flag = '  <-- over the limit' if unq[0] > limit else ''
        print(f'  {num:2d}    {ns:6d}  {nb:6d}      {pct:5.1f}%        {best[0]:3d}          {unq[0]:3d}{flag}')
        if show or unq[0] > limit:
            print('         overall :', ' '.join(sw[best[1]:best[1] + best[0]]))
            print('         unquoted:', ' '.join(sw[unq[1]:unq[1] + unq[0]]))
    print(f'total   {total_s:6d}  {total_b:6d}   longest unquoted shared run: {worst} words (limit {limit})')
    sys.exit(1 if worst > limit else 0)

if __name__ == '__main__':
    main()
