"""Source loading and the line-width model used to recover the book's structure.

The .txt files are a line-by-line dump of a typeset edition: every text line is one
typeset line and blank lines are page breaks.  Paragraph breaks, block quotations,
sidebars and so on are therefore not marked explicitly, but they can be recovered
from line widths, because the original was set with greedy line breaking in a
Times-like face.  Widths below are in em, from the Times-Roman AFM metrics.
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)                      # repository root (the .txt files)
_W = json.load(open(os.path.join(HERE, 'times_widths.json'), encoding='utf-8'))
SP = 0.25                                        # width of a normal space


def src_files():
    """The unique source files in reading order (the two '(1)' copies are duplicates)."""
    return sorted(f for f in glob.glob(os.path.join(SRC, '*.txt')) if '(1)' not in f)


def find_file(prefix):
    return next(f for f in src_files() if os.path.basename(f).startswith(prefix))


def short_name(path):
    return os.path.basename(path)[:3]


def sw(s):
    """Width of a string in em (Times-Roman, no kerning)."""
    return sum(_W.get(c, 0.5) for c in s)


def first_unit(s):
    """Text up to the first line-break opportunity."""
    m = re.match(r'\S+', s)
    tok = m.group(0) if m else ''
    for p in range(1, len(tok)):
        a, b = tok[p - 1], tok[p]
        if a in '-–' and b.isalnum():
            return tok[:p]
        if a == '—' and b != '—':
            return tok[:p]
        if b == '—' and a != '—':
            return tok[:p]
    return tok


# One-word lines with a trailing space that are NOT fragments of an exploded line.
NOT_EXPLODED = {('43_', 102), ('63_', 70)}
# Multi-word lines with a trailing space that ARE the head of an exploded line.
EXTRA_EXPLODED = {('40_', 316)}


class Line:
    __slots__ = ('text', 'n0', 'n1', 'pb', 'trail', 'w', 'u', 'merged')

    def __init__(self, text, n0, n1, pb, trail, merged=False):
        self.text, self.n0, self.n1, self.pb, self.trail, self.merged = text, n0, n1, pb, trail, merged

    def __repr__(self):
        return f"<{self.n0}:{self.text[:40]!r}>"


def load(path):
    """Read a source file into Line objects.

    Blank lines are dropped (pb=True marks a page break before the line).  A few
    lines were 'exploded' into one word per line (each with a trailing space) by
    the extraction; they are merged back.  For every line, w is its natural width
    and u the width it would have had with the first breakable unit of the next
    line appended: a line break is 'natural' at measure M when w <= M < u.
    """
    key = short_name(path)
    raw = open(path, encoding='utf-8').read().split('\n')
    out = []
    pb = False
    i = 0
    n = len(raw)
    while i < n:
        l = raw[i]
        if not l.strip():
            pb = True
            i += 1
            continue
        trail = l.endswith(' ')
        s = l.rstrip()
        exploded = trail and ((' ' not in s and (key, i + 1) not in NOT_EXPLODED) or (key, i + 1) in EXTRA_EXPLODED)
        if exploded:
            parts = [s]
            j = i + 1
            while j < n and raw[j].endswith(' ') and ' ' not in raw[j].rstrip() and raw[j].strip():
                parts.append(raw[j].rstrip())
                j += 1
            assert j < n and raw[j].strip(), (path, i + 1)
            parts.append(raw[j].rstrip())
            out.append(Line(' '.join(parts), i + 1, j + 1, pb, False, merged=True))
            pb = False
            i = j + 1
            continue
        out.append(Line(s, i + 1, i + 1, pb, trail))
        pb = False
        i += 1
    for k, ln in enumerate(out):
        ln.w = sw(ln.text)
        if k + 1 < len(out):
            nx = out[k + 1].text
            nosp = ln.text[-1] in '-–—' or nx.startswith('—')
            ln.u = ln.w + (0 if nosp else SP) + sw(first_unit(nx))
        else:
            ln.u = 1e9
    return out


def join_texts(texts):
    """Join typeset lines into running text.

    Every line-end hyphen in the source is a real hyphen (no word is hyphenated
    across lines), so hyphens and dashes are joined without a space.
    """
    out = texts[0]
    for t in texts[1:]:
        if out.endswith(('-', '–', '—')) or (t.startswith('—') and not t.startswith('———')):
            out += t
        else:
            out += ' ' + t
    return out


def join_lines(lines):
    return join_texts([ln.text for ln in lines])
