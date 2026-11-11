#!/usr/bin/env python3
"""Print a compact plain-text reading view of files of the LaTeX edition.

    python3 tools/reading_view.py chapters/chapter01.tex [more files under latex/ ...]

Markup is reduced to a few markers (## heading, [SIDEBAR: ...], [QUOTE] ...), paragraphs are put
on one line each and the reading list is replaced by its length.  Used for writing the summary.
"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'latex') + os.sep


def view(rel):
    s = open(ROOT + rel, encoding='utf-8').read()
    s = re.sub(r'^% Source:.*\n', '', s)
    # reading list: keep only the count
    m = re.search(r'\\readinghead\{[^}]*\}\s*\\begin\{readinglist\}(.*?)\\end\{readinglist\}', s, re.S)
    if m:
        n = m.group(1).count('\\entry')
        s = s[:m.start()] + '\n\n(READING LIST: %d entries omitted)\n' % n + s[m.end():]
    s = re.sub(r'\\bookchapter\[[^\]]*\]\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}', r'### \1 | \2 | \3\n', s)
    s = re.sub(r'\\bookpart\[[^\]]*\]\{([^}]*)\}\{([^}]*)\}', r'### PART: \1 | \2\n', s)
    s = re.sub(r'\\(?:front|back)chapter\[[^\]]*\]\{([^}]*)\}\{[^}]*\}', r'### \1\n', s)
    s = re.sub(r'\\(?:front|back)chapter\{([^}]*)\}\{[^}]*\}', r'### \1\n', s)
    s = re.sub(r'\\leadin\{([^}]*)\}\{([^}]*)\}', r'\1\2', s)
    s = re.sub(r'\\section\{([^}]*)\}', r'\n## \1\n', s)
    s = re.sub(r'\\begin\{sidebar\}\{([^}]*)\}', r'\n[SIDEBAR: \1]\n', s)
    s = re.sub(r'\\end\{sidebar\}', r'\n[/SIDEBAR]\n', s)
    s = re.sub(r'\\sidebarhead\{([^}]*)\}', r'\n# \1\n', s)
    s = re.sub(r'\\begin\{blockquote\}', r'\n[QUOTE]\n', s)
    s = re.sub(r'\\end\{blockquote\}', r'\n[/QUOTE]\n', s)
    s = re.sub(r'\\begin\{(poem|plainlines|centerlines)\}', r'\n[VERSE]\n', s)
    s = re.sub(r'\\end\{(poem|plainlines|centerlines)\}', r'\n[/VERSE]\n', s)
    s = re.sub(r'\\begin\{numlist\}', r'\n[LIST]\n', s)
    s = re.sub(r'\\end\{numlist\}', r'\n[/LIST]\n', s)
    s = re.sub(r'\\item\[([^\]]*)\]', r'\n\1', s)
    s = re.sub(r'\\(figcaption|figtitle|tabletitle|timelinetitle|byline|noteshead|readinghead|popesintro)\{([^}]*)\}', r'\n[\1: \2]\n', s)
    s = re.sub(r'\\begin\{booktable\}\{[^\n]*\}\n', '\n[TABLE]\n', s)
    s = re.sub(r'\\end\{booktable\}', '\n[/TABLE]\n', s)
    s = re.sub(r'\\(toprule|midrule|bottomrule)', '', s)
    s = re.sub(r'\\addlinespace(\[[^\]]*\])?', '', s)
    s = re.sub(r'\\begin\{[a-z]+\}|\\end\{[a-z]+\}', '\n', s)
    s = re.sub(r'\\epigraphsource\{([^}]*)\}\{([^}]*)\}', r'\n-- \1, \2\n', s)
    s = re.sub(r'\\url\{([^}]*)\}', r'\1', s)
    s = s.replace('\\noindent', '').replace('\\entry', '\n*').replace('\\,', '').replace('~', ' ')
    s = s.replace('\\&', '&').replace('\\$', '$').replace('\\\\', ' / ')
    # unwrap paragraphs
    paras = [re.sub(r'\s*\n\s*', ' ', p).strip() for p in re.split(r'\n\s*\n', s)]
    out = '\n'.join(p for p in paras if p)
    out = re.sub(r'\n(## |\[SIDEBAR|### )', r'\n\n\1', out)
    return out


for rel in sys.argv[1:]:
    t = view(rel)
    print(t)
    print('\n[%s: %d words]' % (rel, len(t.split())))
