#!/usr/bin/env python3
"""Normalize em dashes in the summary volume: `word --- word` (also across a line end) -> `word---word`.

The summary follows the book's own style (unspaced em dashes).  Lines that grow too long through
the joining are wrapped again.  Run from the repository root:
    python3 tools/summary_dashes.py          # rewrite files in place
    python3 tools/summary_dashes.py --check  # only report
"""
import glob
import re
import sys

CHECK = '--check' in sys.argv
WIDTH = 104
SPACED = re.compile(r'[ \t]*\n?[ \t]*(?<!-)---(?!-)[ \t]*\n?[ \t]*')


def wrap(line):
    """Break a long source line at spaces (a line end is a space for TeX)."""
    out = []
    while len(line) > WIDTH:
        cut = line.rfind(' ', 0, WIDTH + 1)
        if cut <= 0:
            break
        out.append(line[:cut])
        line = line[cut + 1:]
    out.append(line)
    return '\n'.join(out)


total = 0
files = sorted(glob.glob('summary/chapters/*.tex') + glob.glob('summary/back/*.tex')
               + glob.glob('summary/front/*.tex') + glob.glob('summary/parts/*.tex'))
for path in files:
    text = open(path, encoding='utf-8').read()
    count = 0
    pieces = re.split(r'(?m)(^%.*$)', text)          # comment lines stay as they are
    for k, piece in enumerate(pieces):
        if piece.startswith('%'):
            continue

        def fix(m):
            global count
            if m.group(0) != '---':
                count += 1
            return '---'

        piece = SPACED.sub(fix, piece)
        pieces[k] = '\n'.join(wrap(ln) if len(ln) > WIDTH + 6 else ln for ln in piece.split('\n'))
    if count:
        total += count
        print(f'{path}: {count}')
        if not CHECK:
            open(path, 'w', encoding='utf-8').write(''.join(pieces))
print('spaced em dashes', 'found' if CHECK else 'fixed', total)
