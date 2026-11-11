"""Turn the recovered structure into LaTeX source."""
import re
import textwrap

import structure_data as SD

WIDTH = 100
MOJIBAKE = '¬†'                    # a mis-decoded no-break space in the source (twice, in the Epilogue)
_ELL = re.compile(r'( ?)(\.(?: \.){2,})( ?)')
_URL = re.compile(r'https?://[^\s]+|\b[\w-]+(?:\.[\w-]+)+\.(?:com|org|net)\b')


def clean(s):
    """Source text -> the text that is typeset (only repairs the mojibake)."""
    return s.replace(MOJIBAKE, ' ')


def tex(s):
    """Escape running text for LaTeX.  The words are untouched; only spacing glue is added:
    ties inside ellipses, a thin space between nested closing quotes, \\url for web addresses."""
    s = clean(s)
    if re.search(r'[%#_~^\\{}]', s):
        raise ValueError('unexpected TeX special in: ' + s)
    s = s.replace('&', r'\&').replace('$', r'\$')
    s = s.replace('’ ”', r'’\,”')

    def ell(m):
        lead, dots, trail = m.groups()
        out = ('~' if lead and m.start() > 0 else lead) + dots.replace(' ', '~')
        if trail:
            out += '~' if s[m.end():m.end() + 1] in tuple('?!.,;:”’)') and m.end() < len(s) else ' '
        return out

    s = _ELL.sub(ell, s)
    s = _URL.sub(lambda m: r'\url{' + m.group(0) + '}', s)
    return s


def wrap(s, first='', rest=''):
    return textwrap.fill(s, width=WIDTH, initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False)


def guard(line):
    """Protect a line that follows \\\\ and starts with * or [ (they would be read as arguments)."""
    return '{}' + line if line[:1] in '*[' else line


def leadin(text):
    """The first four words of an opening paragraph are capitals in the source: \\leadin{W}{HAT ...}."""
    words = text.split(' ')
    lead = ' '.join(words[:4])
    m = re.match(r'^([“‘]?.)(.*)$', lead)
    return r'\leadin{%s}{%s}' % (tex(m.group(1)), tex(m.group(2))) + tex(text[len(lead):])


def para(p, noindent_ok=True):
    if p.get('opener'):
        return wrap(leadin(p['text']))
    t = tex(p['text'])
    if not p['indent'] and noindent_ok:
        t = r'\noindent ' + t
    return wrap(t)


def lines_env(env, lines):
    body = '\\\\\n'.join(guard(tex(l)) for l in lines)
    return '\\begin{%s}\n%s\n\\end{%s}' % (env, body, env)


def table(el):
    spec = SD.TABLES[(el['key'], el['n0'])]
    # check that the table is made of exactly the words of the source lines
    src = ' '.join(el['lines']).split()
    words = ([spec['title']] if spec['title'] else []) + spec['header'] + [c for r in spec['rows'] for c in r]
    assert ' '.join(words).split() == src, (el['key'], el['n0'])
    n = spec['cols']
    cols = {2: '@{}L{0.47}L{0.47}@{}', 3: '@{}L{0.30}C{0.31}C{0.31}@{}', 4: '@{}L{0.16}L{0.24}L{0.24}L{0.24}@{}'}[n]
    out = []
    if spec['title']:
        out.append(r'\tabletitle{%s}' % tex(spec['title']))
    out.append(r'\begin{booktable}{%s}' % cols)
    out.append(r'\toprule')
    out.append(' & '.join(tex(c) for c in spec['header']) + r' \\')
    out.append(r'\midrule')
    for i, r in enumerate(spec['rows']):
        if i:
            out.append(r'\addlinespace[2pt]')
        out.append(' & '.join(tex(c) for c in r) + r' \\')
    out.append(r'\bottomrule')
    out.append(r'\end{booktable}')
    return '\n'.join(out)


def blocks(els, in_sidebar=False):
    """Body elements -> list of LaTeX chunks (joined with blank lines by the caller)."""
    out = []
    prev = None
    for el in els:
        t = el['t']
        if t == 'p':
            # after a heading LaTeX suppresses the indent by itself
            out.append(para(el, noindent_ok=prev not in ('h', 'subhead', 'title', None) or el.get('opener')))
        elif t == 'h':
            out.append(r'\section{%s}' % tex(el['text']))
        elif t == 'quote':
            body = '\n\n'.join(wrap(tex(p['text'])) for p in el['paras'])
            out.append('\\begin{blockquote}\n%s\n\\end{blockquote}' % body)
        elif t == 'verse':
            out.append(lines_env('poem', el['lines']))
        elif t == 'display':
            out.append(lines_env('centerlines', el['lines']))
        elif t == 'lines':
            out.append(lines_env('plainlines', el['lines']))
        elif t == 'list':
            items = []
            for it in el['items']:
                ps = [wrap(r'\item[%s] ' % tex(it['label']) + tex(it['paras'][0]['text']), rest='  ')]
                ps += [wrap(tex(p['text']), first='  ', rest='  ') for p in it['paras'][1:]]
                items.append('\n\n'.join(ps))
            out.append('\\begin{numlist}\n%s\n\\end{numlist}' % '\n'.join(items))
        elif t == 'caption':
            out.append(wrap(r'\figcaption{%s}' % tex(el['text'])))
        elif t == 'figtitle':
            out.append(r'\figtitle{%s}' % tex(el['text']))
        elif t == 'subhead':
            out.append(r'\sidebarhead{%s}' % tex(el['text']))
        elif t == 'table':
            out.append(table(el))
        elif t == 'sidebar':
            inner = '\n\n'.join(blocks(el['body'], in_sidebar=True))
            out.append('\\begin{sidebar}{%s}\n%s\n\\end{sidebar}' % (tex(el['title']), inner))
        elif t == 'byline':
            out.append(r'\byline{%s}' % tex(el['text']))
        elif t == 'epigraph':
            out.append('\\begin{epigraphblock}\n%s\n\\epigraphsource{%s}{%s}\n\\end{epigraphblock}'
                       % (wrap(tex(el['text'])), tex(el['by']), tex(el['work'])))
        elif t == 'signature':
            out.append(lines_env('signature', el['lines']))
        else:
            raise ValueError(t)
        prev = t
    return out


def entries_env(env, entries):
    return '\\begin{%s}\n%s\n\\end{%s}' % (env, '\n'.join(wrap(r'\entry ' + tex(e['text']), rest='  ') for e in entries), env)
