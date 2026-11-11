#!/usr/bin/env python3
"""Check that the LaTeX edition contains exactly the text of the source files.

    python3 tools/verify_text.py

Every latex/*/*.tex file names its source file in its first line.  The LaTeX markup is
stripped again and the remaining characters are compared, in order, with the characters
of the .txt file.  The single-file edition (latex/church-history-single-file.tex), if it
exists, is checked in the same way, block by block.  Only two things are allowed to differ:

  * white space next to a hyphen or dash (the source breaks lines there, and such
    lines are joined without a space), and
  * the two occurrences of a mis-decoded no-break space in the Epilogue, which
    are typeset as a normal space.

A second test closes the first loophole: inside running text the LaTeX files must have
a space next to a hyphen or dash exactly as often as the source has one inside a line.

This script deliberately does not use the converter's code.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SINGLE = os.path.join(ROOT, 'latex', 'church-history-single-file.tex')
MOJIBAKE = '¬†'

# command -> (optional arguments to drop, mandatory arguments, indexes kept, joiner)
MACROS = {
    'bookchapter': (1, 3, (0, 1, 2), ' '), 'frontchapter': (1, 2, (0,), ' '), 'backchapter': (1, 2, (0,), ' '),
    'bookpart': (1, 2, (0, 1), ' '), 'timelinetitle': (0, 1, (0,), ' '), 'leadin': (0, 2, (0, 1), ''),
    'section': (0, 1, (0,), ' '), 'byline': (0, 1, (0,), ' '), 'sidebarhead': (0, 1, (0,), ' '),
    'figcaption': (0, 1, (0,), ' '), 'figtitle': (0, 1, (0,), ' '), 'tabletitle': (0, 1, (0,), ' '),
    'readinghead': (0, 1, (0,), ' '), 'noteshead': (0, 1, (0,), ' '), 'popesintro': (0, 1, (0,), ' '),
    'tocentryplain': (0, 1, (0,), ' '), 'tocentry': (0, 2, (0,), ' '), 'tocpart': (0, 2, (0,), ' '),
    'tocchapter': (0, 4, (0, 1, 2), ' '), 'pope': (0, 2, (0, 1), ' '), 'epigraphsource': (0, 2, (0, 1), ' '),
    'url': (0, 1, (0,), ' '), 'entry': (0, 0, (), ''), 'noindent': (0, 0, (), ''), 'toprule': (0, 0, (), ''),
    'midrule': (0, 0, (), ''), 'bottomrule': (0, 0, (), ''), 'addlinespace': (1, 0, (), ''),
}
ENV_ARGS = {'sidebar': 'keep', 'booktable': 'drop'}      # environments with one mandatory argument
SEP = '\x01'                 # a word separator that comes from markup, not from running text
DASH_SPACE = re.compile(r'[-–—][ \n]+(?!\x01)(?=\S)|(?<=[^\x01\s])[ \n]+—')


class Parser:
    def __init__(self, s):
        self.s, self.i = s, 0

    def group(self):
        """Read {...} at the current position and return its de-TeXed content."""
        assert self.s[self.i] == '{', self.s[self.i:self.i + 40]
        self.i += 1
        out = self.run(stop='}')
        self.i += 1
        return out

    def raw_group(self):
        depth, j = 0, self.i
        while True:
            c = self.s[j]
            depth += (c == '{') - (c == '}')
            j += 1
            if depth == 0:
                break
        out = self.s[self.i + 1:j - 1]
        self.i = j
        return out

    def optional(self, keep=False):
        if self.s[self.i:self.i + 1] != '[':
            return ''
        j = self.s.index(']', self.i)
        out = self.s[self.i + 1:j]
        self.i = j + 1
        return out if keep else ''

    def run(self, stop=None):
        s, out = self.s, []
        while self.i < len(s):
            c = s[self.i]
            if c == stop:
                break
            if c == '%':
                self.i = s.index('\n', self.i) + 1 if '\n' in s[self.i:] else len(s)
            elif c == '\\':
                m = re.match(r'\\([A-Za-z]+) ?', s[self.i:])
                if not m:                                    # control symbol
                    sym = s[self.i + 1]
                    out.append({'\\': SEP, ',': ' ', '&': '&', '$': '$'}[sym])
                    self.i += 2
                    continue
                name = m.group(1)
                self.i += len(m.group(0))
                if name == 'begin':
                    env = self.raw_group()
                    if env in ENV_ARGS:
                        arg = self.group() if ENV_ARGS[env] == 'keep' else (self.raw_group() and '')
                        out.append(SEP + arg + SEP)
                    else:
                        out.append(SEP)
                elif name == 'end':
                    self.raw_group()
                    out.append(SEP)
                elif name == 'item':
                    out.append(SEP + self.optional(keep=True) + ' ')
                else:
                    nopt, nmand, keep, joiner = MACROS[name]         # unknown commands are an error
                    for _ in range(nopt):
                        self.optional()
                    args = [self.group() for _ in range(nmand)]
                    kept = (joiner if joiner == '' else SEP).join(args[k] for k in keep)
                    out.append(kept if name in ('leadin', 'url') else SEP + kept + SEP)
            elif c == '{':
                out.append(self.group())
            elif c == '~':
                out.append(' ')
                self.i += 1
            elif c == '&':                                   # table cell separator
                out.append(SEP)
                self.i += 1
            elif c == '\n' and s[self.i + 1:self.i + 2] == '\n':    # blank line: paragraph break
                out.append(SEP)
                self.i += 1
            else:
                out.append(c)
                self.i += 1
        return ''.join(out)


def canon(s):
    s = re.sub(r'\s+', ' ', s.replace(SEP, ' ')).strip()
    s = re.sub(r'([-–—]) ', r'\1', s)           # no space after a hyphen or dash ...
    return re.sub(r' —', '—', s)                 # ... or before an em dash


def source_text(path):
    lines = [l.strip() for l in open(path, encoding='utf-8').read().split('\n')]
    return canon(' '.join(l for l in lines if l).replace(MOJIBAKE, ' '))


def check(units, what):
    """units: [(label, LaTeX text starting with '% Source: <file>')].  Returns the number of problems."""
    seen, bad, nchar, nword = set(), 0, 0, 0
    for label, body in units:
        m = re.match(r'% Source: (.+)\n', body)
        if not m:
            print('NO SOURCE LINE:', label)
            bad += 1
            continue
        src = os.path.join(ROOT, m.group(1))
        seen.add(m.group(1))
        a = source_text(src)
        detexed = Parser(body).run()
        b = canon(detexed)
        nchar += len(a)
        nword += len(a.split())
        if a != b:
            bad += 1
            k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print('MISMATCH %s\n   source: ...%s\n   latex:  ...%s' % (label, a[max(0, k - 50):k + 50], b[max(0, k - 50):k + 50]))
        # spaces next to hyphens and dashes inside running text
        lines = [l.strip().replace(MOJIBAKE, ' ') for l in open(src, encoding='utf-8').read().split('\n')]
        in_source = sum(len(re.findall(r'[-–—] +(?=\S)|(?<=\S) +—', l)) for l in lines)
        in_latex = len(DASH_SPACE.findall(detexed))
        if in_source != in_latex:
            bad += 1
            print('LINE JOIN %s: %d spaces next to a dash in the source lines, %d in the LaTeX text'
                  % (label, in_source, in_latex))
    expected = {os.path.basename(f) for f in glob.glob(os.path.join(ROOT, '*.txt')) if '(1)' not in f}
    for name in sorted(expected - seen):
        print('SOURCE FILE NOT CONVERTED (%s): %s' % (what, name))
        bad += 1
    print('%s checked against %d source files: %d words, %d characters; %s'
          % (what, len(seen), nword, nchar, 'ALL IDENTICAL' if not bad else '%d PROBLEM(S)' % bad))
    return bad


def split_single(path):
    """The blocks of the single-file edition: one per '% Source:' line, without the lines of main.tex."""
    text = open(path, encoding='utf-8').read()
    text = text[re.search(r'(?m)^\\begin\{document\}', text).start():]
    units = []
    for block in re.split(r'(?m)^(?=% Source: )', text)[1:]:
        lines = block.rstrip('\n').split('\n')
        while re.fullmatch(r'\\(frontmatter|mainmatter|backmatter|end\{document\})|%.*|\s*', lines[-1]):
            lines.pop()
        units.append('\n'.join(lines) + '\n')
    return units


def main():
    texs = sorted(glob.glob(os.path.join(ROOT, 'latex', '*', '*.tex')))
    files = [(os.path.relpath(t, ROOT), open(t, encoding='utf-8').read()) for t in texs]
    bad = check(files, '%d LaTeX files' % len(files))
    if os.path.exists(SINGLE):
        name = os.path.basename(SINGLE)
        blocks = split_single(SINGLE)
        bad += check([('%s, block %d' % (name, i + 1), b) for i, b in enumerate(blocks)],
                     '%s (%d blocks)' % (name, len(blocks)))
        if sorted(b.rstrip() for b in blocks) != sorted(body.rstrip() for _, body in files):
            print('NOTE: %s is not up to date with the separate files; run tools/single_file.py' % name)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
