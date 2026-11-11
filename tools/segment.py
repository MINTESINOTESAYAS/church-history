"""Recover paragraphs and block structure from the typeset lines."""
import re

from textmodel import find_file, join_lines, join_texts, load, short_name, sw
import structure_data as SD

MEAS = {            # class -> (measure, paragraph indent), in em
    'body':    (31.19, 1.28),
    'sidebar': (29.23, 1.45),
    'quote':   (28.12, 1.28),
    'list':    (28.73, 1.28),
    'slist':   (28.12, 1.28),   # list inside a sidebar
}
TOL = 0.06
PARA_END = re.compile(r'([.?!:]|\. \.)[”’)\]]*$')
LABEL = re.compile(r'^(\d{1,2})\. ')
SUGG = 'Suggestions for Further Reading'


def is_caps(s):
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


class Ctx:
    """Overrides going in, review material coming out."""

    def __init__(self):
        self.breaks = set(SD.BREAK_AFTER)
        self.joins = set(SD.JOIN_AFTER)
        self.ambig = []       # undecidable paragraph ends (default: no break)
        self.anom = []        # things the model cannot explain
        self.auto = []        # breaks proven by the indent of the following line
        self.used = set()


def seg_paras(key, lines, cls, ctx, first_flush=None, first_extra=0.0, opener=False):
    """Split a run of lines of one prose class into paragraphs.

    Returns [{'lines': [...], 'flush': bool}, ...].  first_flush: True / False /
    None (decide from the width of the first line).  first_extra: extra room on the
    very first line (a hanging list label).  opener: the first line starts with the
    chapter's lead-in, whose width cannot be modelled.
    """
    M, I = MEAS[cls]
    paras = []
    k, n, first = 0, len(lines), True
    while k < n:
        ln = lines[k]
        if first:
            flush = (ln.w > M - I + 0.10) if first_flush is None else first_flush
        else:
            flush = False
            if ln.w > M - I + 0.30:
                ctx.anom.append((key, ln.n0, f'first line too wide for an indented paragraph ({cls})', ln.text))
        avail = (M if flush else M - I) + (first_extra if first else 0.0)
        j = k
        while True:
            lj = lines[j]
            m_eff = avail if j == k else M
            is_op = opener and first and j == k
            if not is_op and lj.w > m_eff + (0.45 if cls == 'body' else 0.30):
                ctx.anom.append((key, lj.n0, f'line wider than measure ({cls}, {lj.w:.2f} > {m_eff:.2f})', lj.text))
            if j == n - 1:
                break
            site = (key, lj.n0)
            forced = (not is_op) and lj.u <= m_eff - TOL and site not in ctx.joins
            if forced:
                if not PARA_END.search(lj.text):
                    ctx.anom.append((key, lj.n0, f'forced break without sentence end ({cls}, u={lj.u:.2f})', lj.text))
                break
            if site in ctx.breaks:
                ctx.used.add(site)
                break
            nx = lines[j + 1]
            if PARA_END.search(lj.text) and nx.w <= M - I + 0.10 and site not in ctx.joins:
                # The next line could be an indented first line.  It certainly is one if, read as a
                # continuation line, it would have been broken early without ending the paragraph.
                short_as_cont = nx.u <= M - TOL
                natural_as_first = nx.u > M - I - TOL
                auto = False
                if short_as_cont and natural_as_first and j + 1 < n - 1:
                    if not PARA_END.search(nx.text) or lines[j + 2].w > M - I + 0.10:
                        auto = True
                if auto:
                    ctx.auto.append(site)
                    break
                ctx.ambig.append((key, lj.n0, cls, lj, nx, j - k + 1, lines, j))
            elif site in ctx.joins:
                ctx.used.add(site)
            j += 1
        paras.append({'lines': lines[k:j + 1], 'flush': flush})
        k, first = j + 1, False
    return paras


def mk_p(par, **kw):
    d = {'t': 'p', 'text': join_lines(par['lines']), 'indent': not par['flush'],
         'n0': par['lines'][0].n0, 'n1': par['lines'][-1].n1, 'nlines': len(par['lines'])}
    d.update(kw)
    return d


def build_list(key, lines, cls, ctx):
    groups = []
    for ln in lines:
        if LABEL.match(ln.text):
            groups.append([ln])
        else:
            groups[-1].append(ln)
    items = []
    for g in groups:
        m = LABEL.match(g[0].text)
        paras = seg_paras(key, g, cls, ctx, first_flush=True, first_extra=sw(m.group(0)))
        ps = []
        for pi, par in enumerate(paras):
            p = mk_p(par)
            if pi == 0:
                p['text'] = p['text'][len(m.group(0)):]
                p['indent'] = False
            ps.append(p)
        items.append({'label': m.group(0).strip(), 'paras': ps})
    return {'t': 'list', 'items': items}


def build_block(key, blk, lines, inner, ctx, in_sidebar=False):
    kind = blk[2]
    extra = blk[3] if len(blk) > 3 else None
    n0, n1 = lines[0].n0, lines[-1].n1
    if kind == 'quote':
        return {'t': 'quote', 'paras': [mk_p(p) for p in seg_paras(key, lines, 'quote', ctx, first_flush=True)]}
    if kind == 'narrow':
        return {'t': 'quote', 'paras': [{'t': 'p', 'text': join_lines(lines), 'indent': False, 'n0': n0, 'n1': n1,
                                         'nlines': len(lines)}]}
    if kind == 'verse':
        if extra:
            out, cur = [], []
            for ln in lines:
                cur.append(ln)
                if not ln.u > extra:
                    out.append(join_lines(cur))
                    cur = []
            if cur:
                out.append(join_lines(cur))
            return {'t': 'verse', 'lines': out}
        return {'t': 'verse', 'lines': [ln.text for ln in lines]}
    if kind in ('display', 'lines'):
        return {'t': kind, 'lines': [ln.text for ln in lines]}
    if kind == 'caption':
        return {'t': 'caption', 'text': join_lines(lines)}
    if kind in ('figtitle', 'subhead'):
        return {'t': kind, 'text': join_lines(lines)}
    if kind == 'table':
        return {'t': 'table', 'key': key, 'n0': n0, 'n1': n1, 'lines': [ln.text for ln in lines]}
    if kind == 'list':
        return build_list(key, lines, 'slist' if in_sidebar else 'list', ctx)
    if kind == 'sidebar':
        return {'t': 'sidebar', 'title': lines[0].text,
                'body': build_run(key, lines[1:], inner, ctx, 'sidebar', after='title')}
    raise ValueError(kind)


def build_run(key, lines, blocks, ctx, cls, after='heading', opener=False):
    """Turn a region (body text, or the inside of a sidebar) into elements."""
    blocks = sorted(blocks, key=lambda b: (b[0], -b[1]))
    top = []
    for b in blocks:
        if top and b[0] >= top[-1][0] and b[1] <= top[-1][1]:
            continue
        top.append(b)
    out = []
    state = {'prev': after, 'first': True}

    def flush_prose(buf):
        if not buf:
            return
        op = opener and state['first']
        ff = True if (op or state['prev'] in ('heading', 'title')) else None
        for pi, par in enumerate(seg_paras(key, buf, cls, ctx, first_flush=ff, opener=op)):
            out.append(mk_p(par, opener=(op and pi == 0)))
        state['first'] = False

    buf = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        blk = next((b for b in top if b[0] <= ln.n0 <= b[1]), None)
        if blk is not None:
            flush_prose(buf)
            buf = []
            j = i
            while j < n and lines[j].n0 <= blk[1]:
                j += 1
            inner = [b for b in blocks if b is not blk and b[0] >= blk[0] and b[1] <= blk[1]]
            out.append(build_block(key, blk, lines[i:j], inner, ctx, in_sidebar=(cls == 'sidebar')))
            state['prev'] = 'title' if blk[2] == 'subhead' else 'block'
            state['first'] = False
            i = j
            continue
        if cls == 'body' and is_caps(ln.text) and (key, ln.n0) not in SD.NOT_HEADING:
            flush_prose(buf)
            buf = []
            j, hl = i, []
            while j < n and is_caps(lines[j].text) and not any(b[0] <= lines[j].n0 <= b[1] for b in top):
                hl.append(lines[j].text)
                j += 1
            out.append({'t': 'h', 'text': join_texts(hl), 'n0': ln.n0})
            state['prev'] = 'heading'
            state['first'] = False
            i = j
            continue
        buf.append(ln)
        i += 1
    flush_prose(buf)
    return out


def opener_index(L):
    """Index of the chapter's first text line: its first words are set in capitals."""
    for k in range(2, 12):
        t = L[k].text
        words = t.split()
        if (L[k].w > 24 and len(words) >= 4 and all(not re.search(r'[a-z]', w) for w in words[:3])
                and re.search(r'[a-z]', t)):
            return k
    raise ValueError('no opener')


def parse_chapter(path, ctx):
    key = short_name(path)
    L = load(path)
    assert re.match(r'^CHAPTER \d+$', L[0].text), L[0].text
    num = int(L[0].text.split()[1])
    op = opener_index(L)
    blocks = SD.BLOCKS.get(key, [])
    title, rest = [], []
    for ln in L[1:op]:
        if is_caps(ln.text) and not rest:
            title.append(ln.text)
        else:
            rest.append(ln)
    els = [{'t': 'chapterhead', 'num': num, 'label': L[0].text, 'title': title, 'subtitle': rest[0].text}]
    pre = rest[1:]                       # an epigraph between the chapter head and the text (chapter 37)
    if pre:
        pb = [b for b in blocks if b[0] >= pre[0].n0 and b[1] <= pre[-1].n1]
        els += build_run(key, pre, pb, ctx, 'body')
    end = next(k for k, ln in enumerate(L) if ln.text == SUGG)
    body = L[op:end]
    els += build_run(key, body, [b for b in blocks if b[0] >= body[0].n0], ctx, 'body', after='heading', opener=True)
    els.append({'t': 'bibhead', 'text': SUGG})
    els.append({'t': 'biblines', 'lines': L[end + 1:], 'key': key})
    return els


# ---- hanging-indent entries (reading lists, notes) --------------------------------------

BIB_START = re.compile(r"^\*?(———\.|(?:[A-Z][a-z]+ )?[A-ZÀ-Ý][A-Za-zÀ-ÿ’'\-]+, (?:[A-Z][a-z]+[,. ]|[A-Z]\.))")
M_FIRST, M_CONT = 31.19, 29.91
TOL_ITALIC = 0.35     # titles are set in italics, whose widths the roman metrics only approximate


def seg_bib(key, lines, ctx):
    """Split a reading list into entries.  Entries hang: the first line is full measure and
    the rest are indented, so a new entry normally shows by its shape ("Surname, Name ...")."""
    entries = []
    k, n = 0, len(lines)
    while k < n:
        j = k
        while j < n - 1:
            lj, nx = lines[j], lines[j + 1]
            avail = M_FIRST if j == k else M_CONT
            site = (key, lj.n0)
            if site in ctx.joins:
                ctx.used.add(site)
                j += 1
                continue
            if site in ctx.breaks:
                ctx.used.add(site)
                break
            if BIB_START.search(nx.text):
                break
            if lj.u <= avail - TOL_ITALIC or nx.w > M_CONT + TOL_ITALIC:
                ctx.anom.append((key, nx.n0, 'reading list: entry with an unusual start', nx.text))
                break
            j += 1
        entries.append({'text': join_lines(lines[k:j + 1]), 'n0': lines[k].n0, 'n1': lines[j].n1})
        k = j + 1
    return entries


def seg_notes(key, lines, ctx):
    """Split the notes of one chapter into entries (same hanging layout, free-form text)."""
    entries = []
    k, n = 0, len(lines)
    while k < n:
        j = k
        while j < n - 1:
            lj, nx = lines[j], lines[j + 1]
            avail = M_FIRST if j == k else M_CONT
            site = (key, lj.n0)
            if site in ctx.joins:
                ctx.used.add(site)
                j += 1
                continue
            if site in ctx.breaks:
                ctx.used.add(site)
                break
            if lj.u <= avail - TOL_ITALIC or nx.w > M_CONT + TOL_ITALIC:
                break
            if lj.u <= avail - TOL:                      # probably broken early; italics make it uncertain
                ctx.ambig.append((key, lj.n0, 'note-break', lj, nx, j - k + 1, lines, j))
                break
            if re.search(r'[.)”’]$', lj.text) and re.match(r'[“‘(]?[A-Z]', nx.text):
                ctx.ambig.append((key, lj.n0, 'note-join', lj, nx, j - k + 1, lines, j))
            j += 1
        entries.append({'text': join_lines(lines[k:j + 1]), 'n0': lines[k].n0, 'n1': lines[j].n1})
        k = j + 1
    return entries


# ---- front and back matter ---------------------------------------------------------------

def parse_front(prefix, ctx, sig_groups):
    """Foreword / Prologue: title, text with a lead-in, signature.  sig_groups: for each
    signature line, how many source lines it spans (counted from the end of the file)."""
    L = load(find_file(prefix))
    nsig = sum(sig_groups)
    body, sig = L[1:len(L) - nsig], L[len(L) - nsig:]
    els = [{'t': 'fronthead', 'text': L[0].text}]
    els += build_run(prefix, body, [], ctx, 'body', after='heading', opener=True)
    lines, i = [], 0
    for g in sig_groups:
        lines.append(join_lines(sig[i:i + g]))
        i += g
    els.append({'t': 'signature', 'lines': lines})
    return els


def parse_epilogue(ctx):
    key = '63_'
    L = load(find_file(key))
    E = SD.EPILOGUE

    def rng(a, b):
        return [ln for ln in L if a <= ln.n0 <= b]

    els = [{'t': 'fronthead', 'text': L[0].text},
           {'t': 'byline', 'text': rng(E['byline1'], E['byline1'])[0].text},
           {'t': 'epigraph', 'text': join_lines(rng(*E['epigraph'])),
            'by': rng(E['epigraph_by'], E['epigraph_by'])[0].text,
            'work': join_lines(rng(*E['epigraph_work']))}]
    els += build_run(key, rng(*E['body1']), SD.BLOCKS[key], ctx, 'body', after='heading')
    els.append({'t': 'byline', 'text': rng(E['byline2'], E['byline2'])[0].text})
    els += build_run(key, rng(*E['body2']), [], ctx, 'body', after='heading', opener=True)
    return els


def parse_divider(prefix):
    """Part divider: title lines, date line, one summary paragraph and, on the next page,
    the title of a timeline graphic that is not in the text source."""
    L = load(find_file(prefix))
    k = next(i for i, ln in enumerate(L) if any(ch.isdigit() for ch in ln.text) and ln.w < 12)
    summ = []
    for ln in L[k + 1:]:
        if ln.pb:
            break
        summ.append(ln)
    rest = L[k + 1 + len(summ):]
    return {'title': join_lines(L[:k]), 'dates': L[k].text,
            'summary': join_lines(summ), 'timeline': join_lines(rest)}


def parse_notes(ctx):
    key = '64_'
    L = load(find_file(key))
    groups, cur = [], None
    for ln in L[1:]:
        if re.match(r'^Chapter \d+$', ln.text) or ln.text == 'For Further Study':
            cur = {'head': ln.text, 'lines': []}
            groups.append(cur)
        else:
            cur['lines'].append(ln)
    for g in groups:
        g['entries'] = seg_notes(key, g.pop('lines'), ctx)
    return {'title': L[0].text, 'groups': groups}


def parse_popes():
    L = load(find_file('65_'))
    title = join_lines(L[:2])
    intro = join_lines(L[2:4])
    rows = L[4:]
    k = next(i for i, ln in enumerate(rows) if not re.match(r'^\d', ln.text) and i % 2 == 0)
    pairs = [(rows[i].text, rows[i + 1].text) for i in range(0, k, 2)]
    legend = [ln.text for ln in rows[k:]]
    return {'title': title, 'intro': intro, 'pairs': pairs, 'legend': legend}


def parse_contents():
    L = [ln.text for ln in load(find_file('03_'))]
    out = [{'t': 'head', 'text': L[0]}]
    i = 1
    while i < len(L):
        t = L[i]
        m = re.match(r'^(CHAPTER (\d+)) (.*)$', t)
        if m:
            out.append({'t': 'chapter', 'label': m.group(1), 'num': int(m.group(2)), 'title': m.group(3), 'subtitle': L[i + 1]})
            i += 2
            continue
        if re.search(r'(\d|BC)–(\d+|AD \d+)?$', t) and t.startswith('The '):
            out.append({'t': 'part', 'text': t})
        else:
            out.append({'t': 'entry', 'text': t})
        i += 1
    return out


def parse_dedication():
    return [ln.text for ln in load(find_file('02_'))]
