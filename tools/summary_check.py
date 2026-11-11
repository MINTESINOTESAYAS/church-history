#!/usr/bin/env python3
"""Check the summary volume against the structure of the book.

    python3 tools/summary_check.py

For every chapter of the LaTeX edition the summary chapter must exist, carry the same number,
title and subtitle, and contain one \\ssection for every section heading and one sidebox for every
sidebar of the original, in the same order.  Also prints the length of each summary chapter.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    s = s.replace('``', '"').replace("''", '"').replace('`', "'")
    s = re.sub(r'[“”]', '"', s)
    s = re.sub(r'[‘’]', "'", s)
    s = s.replace('---', '—').replace('--', '–').replace('\\&', '&').replace('~', ' ')
    s = re.sub(r'\\[a-zA-Z]+\s*', '', s).replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', s).strip().lower()


def words(tex):
    t = re.sub(r'\\[a-zA-Z@]+', ' ', tex)
    return len(re.sub(r'[{}\[\]%]', ' ', t).split())


def main():
    bad, total, done = 0, 0, 0
    report = []
    for n in range(1, 49):
        src = open(os.path.join(ROOT, 'latex', 'chapters', 'chapter%02d.tex' % n), encoding='utf-8').read()
        m = re.search(r'\\bookchapter\[[^\]]*\]\{CHAPTER (\d+)\}\{([^}]*)\}\{([^}]*)\}', src)
        want = [('sec', norm(x)) for x in []]
        want = [(k, norm(v)) for k, v in re.findall(r'\\(section|begin\{sidebar\})\{([^}]*)\}', src)]
        want = [('side' if k.startswith('begin') else 'sec', v) for k, v in want]
        path = os.path.join(ROOT, 'summary', 'chapters', 'ch%02d.tex' % n)
        if not os.path.exists(path):
            report.append('ch%02d  MISSING' % n)
            continue
        done += 1
        s = open(path, encoding='utf-8').read()
        h = re.search(r'\\summarychapter\{(\d+)\}\{([^}]*)\}\{([^}]*)\}', s)
        problems = []
        if not h or int(h.group(1)) != n:
            problems.append('chapter number')
        else:
            if norm(h.group(2)) != norm(m.group(2)):
                problems.append('title %r vs %r' % (h.group(2), m.group(2)))
            if norm(h.group(3)) != norm(m.group(3)):
                problems.append('subtitle %r vs %r' % (h.group(3), m.group(3)))
        got = [('side' if k.startswith('begin') else 'sec', norm(v))
               for k, v in re.findall(r'\\(ssection|begin\{sidebox\})\{((?:[^{}]|\{[^{}]*\})*)\}', s)]
        if got != want:
            missing = [w for w in want if w not in got]
            extra = [g for g in got if g not in want]
            if missing:
                problems.append('missing: ' + '; '.join('%s "%s"' % w for w in missing))
            if extra:
                problems.append('not in the book: ' + '; '.join('%s "%s"' % g for g in extra))
            if not missing and not extra:
                problems.append('sections in a different order')
        for need in ('\\begin{inbrief}', '\\question{', '\\begin{keyfacts}', '\\keypeople{', '\\keydates{'):
            if need not in s:
                problems.append('no ' + need)
        w = words(s)
        total += w
        report.append('ch%02d  %4d words  %2d sections  %s' % (n, w, len(want), 'ok' if not problems else 'PROBLEM: ' + ' | '.join(problems)))
        bad += bool(problems)
    print('\n'.join(report))
    print('%d of 48 chapters written, %d words, %d with problems' % (done, total, bad))
    return 1 if bad or done < 48 else 0


if __name__ == '__main__':
    sys.exit(main())
