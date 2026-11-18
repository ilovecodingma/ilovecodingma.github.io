# -*- coding: utf-8 -*-
"""책 「가난한 박과장과 퇴근 후 나만의 팀 운영하기」 읽기 화면(/book/park/): 원고 마크다운을 장별 페이지로, 그림은 줄여서 붙인다.
2026-11-19 사장님 지시(작가 전달). 원본(조판 폴더)은 읽기만 한다. 검색 제외(noindex)로 둔다 — 판매와 겹치므로 색인은 사장님 결정 후.
원고 규칙: `# ` 장 제목, `## ` 소제목(「하네스 실습」으로 시작하면 실습 절), `> ` 인용(첫 줄이 [에이전트] 면 에이전트 발화), [[그림 ID]] 는 그림 자리."""
import html
import json
import os
import re

E = html.escape
SRC = r'C:\Users\k\Desktop\퇴근후팀_조판'
MS = os.path.join(SRC, '_최종_1118', '원고')
FIGS = os.path.join(SRC, 'figs')
TITLE = '가난한 박과장과 퇴근 후 나만의 팀 운영하기'
BASE = '/book/park/'
PARTS = [(1, 12, '1부'), (13, 24, '2부'), (25, 36, '3부')]
CSS = ('<style>.bkp{max-width:760px;margin:0 auto;line-height:1.85;font-size:17px}.bkp h1{font-size:26px;line-height:1.35;margin:18px 0 8px}.bkp h2{font-size:21px;margin:34px 0 8px}'
       '.bkp h2.sil{border-left:4px solid var(--tc,#2563eb);padding-left:10px}.bkp p{margin:0 0 14px;word-break:keep-all}.bkp figure{margin:22px 0;text-align:center}.bkp figure img{max-width:100%;height:auto;border:1px solid #e2e8f0;border-radius:8px}'
       '.bkp figcaption{font-size:14px;color:#64748b;margin-top:6px}.bkp blockquote{margin:14px 0;padding:10px 14px;border-left:4px solid #94a3b8;background:#f8fafc;border-radius:0 8px 8px 0}.bkp blockquote.ag{border-left-color:#2563eb;background:#eff6ff}'
       '.bkp blockquote small{display:block;color:#64748b;font-size:12px;margin-bottom:2px}.bkp blockquote p{margin:0 0 8px}.bkp .bkn{display:flex;justify-content:space-between;gap:10px;margin:30px 0}.bkp .bkn a{flex:1;padding:12px;border:1px solid #e2e8f0;border-radius:8px;text-decoration:none}'
       '.bkp .bkt{list-style:none;padding:0}.bkp .bkt li{margin:6px 0}.bkp .bkt b{display:inline-block;min-width:54px}.bkp h3.pt{margin:26px 0 6px;color:#475569}.bkp .cv{padding:22px;border-radius:12px;background:linear-gradient(160deg,#1e293b,#334155);color:#fff;margin:10px 0 22px}.bkp .cv h1{color:#fff;margin:0 0 6px}'
       '@media (prefers-color-scheme:dark){.bkp blockquote{background:#1e293b}.bkp blockquote.ag{background:#172554}.bkp figure img,.bkp .bkn a{border-color:#334155}}</style>')


def _inline(s):
    s = E(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def _fig(fid, imgdir, made):
    """그림 한 장: 줄인 JPG 를 만들어 두고(이미 있으면 재사용) <figure> 를 돌려준다. 원본 PNG 는 읽기만 한다."""
    png = os.path.join(FIGS, fid + '.png')
    if not os.path.exists(png):
        return ''
    out = os.path.join(imgdir, fid + '.jpg')
    if not os.path.exists(out):
        try:
            from PIL import Image
            im = Image.open(png)
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA')
                bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert('RGB')
            if im.width > 1100:
                im = im.resize((1100, round(im.height * 1100 / im.width)))
            im.save(out, 'JPEG', quality=80, optimize=True)
        except Exception as e:
            print('그림 변환 실패', fid, repr(e)[:80])
            return ''
    made.append(fid)
    cap = ''
    jp = os.path.join(FIGS, fid + '.json')
    if os.path.exists(jp):
        try:
            cap = json.load(open(jp, encoding='utf-8')).get('caption', '')
        except Exception:
            cap = ''
    return f'<figure><img src="{BASE}img/{fid}.jpg" alt="{E(cap or "그림")}" loading="lazy">' + (f'<figcaption>{E(cap)}</figcaption>' if cap else '') + '</figure>'


def _render(md, imgdir, made):
    out, para, quote = [], [], []

    def flush_p():
        if para:
            out.append('<p>' + _inline(' '.join(para)) + '</p>')
            para.clear()

    def flush_q():
        if quote:
            ps, cur = [], []
            for l in quote:
                if l.strip() == '':
                    if cur:
                        ps.append(' '.join(cur)); cur = []
                else:
                    cur.append(l.strip())
            if cur:
                ps.append(' '.join(cur))
            ag = bool(ps) and ps[0].startswith('[에이전트] ')
            if ag:
                ps[0] = ps[0][len('[에이전트] '):]
            out.append(f'<blockquote class="{"ag" if ag else "au"}"><small>{"에이전트" if ag else "저자"}</small>' + ''.join('<p>' + _inline(p) + '</p>' for p in ps) + '</blockquote>')
            quote.clear()

    title = ''
    for line in md.split('\n'):
        if line.startswith('> ') or line == '>':
            flush_p(); quote.append(line[2:] if line.startswith('> ') else '')
            continue
        flush_q()
        m = re.match(r'^\[\[그림 ([^\]]+)\]\]\s*$', line.strip())
        if m:
            flush_p(); out.append(_fig(m.group(1).strip(), imgdir, made)); continue
        if line.startswith('# '):
            flush_p(); title = line[2:].strip(); continue
        if line.startswith('## '):
            flush_p(); h = line[3:].strip()
            cls = ' class="sil"' if h.startswith('하네스 실습') else ''
            out.append('<h2' + cls + '>' + _inline(h) + '</h2>'); continue
        if line.strip() == '':
            flush_p(); continue
        para.append(line.strip())
    flush_p(); flush_q()
    return title, ''.join(out)


def pages(page, root):
    if not os.path.isdir(MS):
        return []
    files = [('ch00', '서론')] + [(f'ch{n:02d}', None) for n in range(1, 37)] + [('ch99', '맺는글')]
    imgdir = os.path.join(root, 'book', 'park', 'img')
    os.makedirs(imgdir, exist_ok=True)
    chs, made = [], []
    for key, fixed in files:
        fp = os.path.join(MS, key + '.md')
        if not os.path.exists(fp):
            continue
        t, body = _render(open(fp, encoding='utf-8').read(), imgdir, made)
        chs.append(dict(key=key, title=t or fixed or key, body=body, n=int(key[2:]) if key not in ('ch00', 'ch99') else 0))
    if not chs:
        return []
    urls = []
    crumbs0 = [('홈', '/'), ('책', BASE)]

    def nav(i):
        p = chs[i - 1] if i > 0 else None
        n = chs[i + 1] if i + 1 < len(chs) else None
        return ('<div class="bkn">' + (f'<a href="{BASE}{p["key"]}/">← {E(p["title"])}</a>' if p else '<span></span>')
                + (f'<a href="{BASE}{n["key"]}/" style="text-align:right">{E(n["title"])} →</a>' if n else '<span></span>') + '</div>')

    for i, c in enumerate(chs):
        body = (f'<div class="bkp"><p class="bc"><a href="/">홈</a> › <a href="{BASE}">{E(TITLE)}</a></p><h1>{E(c["title"])}</h1>' + c['body'] + nav(i)
                + f'<p><a href="{BASE}">차례로 돌아가기</a></p></div>' + CSS)
        page(f'{BASE}{c["key"]}/', f'{c["title"]} — {TITLE}', f'{TITLE}의 {c["title"]} 읽기 화면입니다.', body, crumbs0 + [(c['title'], f'{BASE}{c["key"]}/')], noindex=True)
        urls.append(f'{BASE}{c["key"]}/')
    toc = ''
    for c in chs:
        if c['n'] in (1, 13, 25):
            nm = [x[2] for x in PARTS if x[0] == c['n']][0]
            toc += f'</ul><h3 class="pt">{nm}</h3><ul class="bkt">'
        toc += f'<li><a href="{BASE}{c["key"]}/"><b>{"" if c["n"] == 0 else str(c["n"]) + "장"}</b> {E(c["title"])}</a></li>'
    toc = '<ul class="bkt">' + toc + '</ul>'
    cover = (f'<div class="bkp"><p class="bc"><a href="/">홈</a> › {E(TITLE)}</p><div class="cv"><h1>{E(TITLE)}</h1><p>지은이 가난한 박과장</p></div>'
             '<p>근로소득만으로는 답이 없다는 것을 깨닫고 새로운 도전을 꿈꾸는 당신에게. 퇴근 후 AI 에이전트 팀과 서비스를 만들고 운영한 두 달의 기록입니다.</p>'
             '<h2>차례</h2>' + toc + '</div>' + CSS)
    page(BASE, f'{TITLE} — 읽기', f'{TITLE} 전문 읽기 화면. 지은이 가난한 박과장.', cover, crumbs0, noindex=True)
    urls.append(BASE)
    print('책 읽기 화면', len(chs), '장 / 그림', len(made), '장')
    return urls
