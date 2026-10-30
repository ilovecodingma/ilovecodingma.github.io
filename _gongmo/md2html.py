# -*- coding: utf-8 -*-
"""작가 납품 마크다운 → guides_extra.json 항목 [slug, title, desc, html] 변환 (코드만, AI 호출 없음)."""
import re, json, html, sys, os
E = html.escape

def inline(t):
    t = E(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)
    t = re.sub(r'(?<![">])(https?://[^\s<)]+)', lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener nofollow">{m.group(1)}</a>', t)
    return t

def convert(md, slug):
    lines = md.replace('\r', '').split('\n')
    title = next(l[2:].strip() for l in lines if l.startswith('# '))
    summ = next((re.sub(r'^\*\*한 줄 요약:\*\*\s*', '', l).strip() for l in lines if l.startswith('**한 줄 요약')), '')
    out, i, ul, tb, faq = [], 0, False, [], False
    def close_ul():
        nonlocal ul
        if ul: out.append('</ul>'); ul = False
    def flush_tb():
        nonlocal tb
        if tb:
            rows = [r for r in tb if not re.fullmatch(r'\|[\s:\-|]+\|?', r)]
            h = [c.strip() for c in rows[0].strip('|').split('|')]
            s = '<table class="info"><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in h) + '</tr>'
            for r in rows[1:]:
                s += '<tr>' + ''.join(f'<td>{inline(c.strip())}</td>' for c in r.strip('|').split('|')) + '</tr>'
            out.append(s + '</table>'); tb = []
    body = [l for l in lines if not l.startswith('# ') and not l.startswith('**한 줄 요약')]
    for l in body:
        s = l.strip()
        if s.startswith('|'):
            close_ul(); tb.append(s); continue
        flush_tb()
        if not s:
            close_ul(); continue
        if s.startswith('## '):
            close_ul(); out.append(f'<h2>{inline(s[3:])}</h2>'); continue
        if s.startswith('### '):
            close_ul(); out.append(f'<h3>{inline(s[4:])}</h3>'); continue
        if s.startswith('> '):
            close_ul(); out.append(f'<p class="note">{inline(s[2:])}</p>'); continue
        m = re.match(r'^(?:[-*]|\d+\.)\s+(?:\[[ x]\]\s*)?(.*)$', s)
        if m:
            if not ul: out.append('<ul>'); ul = True
            out.append(f'<li>{inline(m.group(1))}</li>'); continue
        close_ul()
        out.append(f'<p>{inline(s)}</p>')
    close_ul(); flush_tb()
    intro = f'<p>{inline(summ)}</p>' if summ else ''
    return [slug, title, summ[:200], intro + ''.join(out)]

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    res = []
    for f in sorted(os.listdir(here)):
        if f.endswith('.md'):
            res.append(convert(open(os.path.join(here, f), encoding='utf-8').read(), f[:-3]))
    json.dump(res, open(os.path.join(here, '_converted.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in res: print(r[0], '|', r[1][:40], '| html', len(r[3]), '| h2', r[3].count('<h2>'), '| table', r[3].count('<table'), '| li', r[3].count('<li>'))
