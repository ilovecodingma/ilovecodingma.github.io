# -*- coding: utf-8 -*-
"""루리 위키 (2026-10-23 사용자 「docs 수준 퀄리티 · 루리 위키」).
이미 만들어진 정보성 글(생활 돈 가이드·가이드·개발 지식·평론·English)을 문서 사이트처럼 묶는다.
  - /wiki/ 허브: 검색 + 묶음별 글 목록 + 처음 읽는다면
  - 각 글: 왼쪽 글 목록(묶음별·현재 글 강조·검색) / 오른쪽 「이 페이지에서」 목차 / 아래 이전·다음 글
글 본문과 주소는 건드리지 않는다. 빌드 마지막(auto_thin 이후)에 한 번 호출: build_wiki(urls, noindex, page_fn, root, site).
"""
import os, re, json, html as H

GROUPS = [
    ('money', '생활 돈 가이드', '💰', re.compile(r'^/money/guide/[^/]+/$')),
    ('guide', '가이드 · 고민 해결', '📘', re.compile(r'^/guide/[^/]+/$')),
    ('dev', '개발 지식', '🧑‍💻', re.compile(r'^/dev/[^/]+/$')),
    ('review', '평론', '🖋️', re.compile(r'^/review/[^/]+/$')),
    ('en', 'English guides', '🌐', re.compile(r'^/en/guide/[^/]+/$')),
]
START = ['/money/guide/energy-voucher/', '/money/guide/eitc/', '/money/guide/naeil-card/', '/money/guide/first-meeting-voucher/', '/money/guide/severance/']
E = lambda t: H.escape(str(t), quote=True)


def _clean(t):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', t))).strip()


def _read(root, u):
    f = os.path.join(root, u.strip('/'), 'index.html')
    return open(f, encoding='utf-8').read() if os.path.exists(f) else None


def collect(urls, noindex, root):
    arts = []
    seen = set()
    for u in urls:
        if u in seen or u in noindex:
            continue
        g = next((g for g in GROUPS if g[3].match(u)), None)
        if not g:
            continue
        doc = _read(root, u)
        if not doc or 'location.replace' in doc or 'name="robots" content="noindex' in doc:
            continue
        m = re.search(r'<main[^>]*>(.*)</main>', doc, re.S)
        if not m:
            continue
        mh = m.group(1)
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', mh, re.S)
        if not h1:
            continue
        title = re.sub(r'^[^\w가-힣]+', '', _clean(h1.group(1)))
        desc = ''
        for p in re.findall(r'<(?:p|li)[^>]*>(.*?)</(?:p|li)>', mh[mh.find('</h1>'):], re.S):
            t = _clean(p)
            if len(t) >= 40 and not t.startswith(('기준', '홈 ›')):
                desc = t[:96] + ('…' if len(t) > 96 else '')
                break
        # id 가 h2 에 있거나(공용 글), h2 를 감싸는 section 에 있는(생활 돈 가이드) 두 경우를 모두 읽는다
        heads = [(i, re.sub(r'^[\d?]+\s*', '', _clean(t))) for _tg, i, t in re.findall(r'<(section|h2)\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', mh, re.S) if len(_clean(t)) < 120]
        seen.add(u)
        arts.append({'u': u, 'g': g[0], 'title': title, 'desc': desc, 'heads': heads})
    return arts


def _side(arts, cur):
    groups = []
    for key, label, ic, _rx in GROUPS:
        L = [a for a in arts if a['g'] == key]
        if not L:
            continue
        op = ' open' if cur and cur['g'] == key else ''
        li = ''.join(f'<li><a href="{E(a["u"])}"{" class=on aria-current=page" if cur and a["u"] == cur["u"] else ""}>{E(a["title"][:44])}</a></li>' for a in L)
        groups.append(f'<details class="wk-g"{op}><summary><span>{ic} {E(label)}</span><small>{len(L)}</small></summary><ul>{li}</ul></details>')
    return ('<aside class="wk-side"><button type="button" class="wk-toggle" aria-expanded="false">📚 위키 목록</button><div class="wk-nav">'
            '<a class="wk-home" href="/wiki/">📚 루리 위키</a><input class="wk-q" type="search" placeholder="글 찾기" aria-label="위키에서 글 찾기" autocomplete="off">'
            + ''.join(groups) + '</div></aside>')


def _toc(a):
    if len(a['heads']) < 2:
        return '<aside class="wk-toc" aria-hidden="true"></aside>'
    return ('<aside class="wk-toc"><nav aria-label="이 페이지에서"><b>이 페이지에서</b>'
            + ''.join(f'<a href="#{E(i)}">{E(t[:28])}</a>' for i, t in a['heads']) + '</nav></aside>')


def _pn(arts, a):
    L = [x for x in arts if x['g'] == a['g']]
    i = L.index(a)
    prev = f'<a class="pv" rel="prev" href="{E(L[i - 1]["u"])}"><small>← 이전 글</small>{E(L[i - 1]["title"][:40])}</a>' if i > 0 else '<span></span>'
    nxt = f'<a class="nx" rel="next" href="{E(L[i + 1]["u"])}"><small>다음 글 →</small>{E(L[i + 1]["title"][:40])}</a>' if i + 1 < len(L) else '<span></span>'
    return f'<nav class="wk-pn" aria-label="이전·다음 글">{prev}{nxt}</nav>'


def inject(arts, root):
    n = 0
    label = {k: (lb, ic) for k, lb, ic, _ in GROUPS}
    for a in arts:
        f = os.path.join(root, a['u'].strip('/'), 'index.html')
        doc = open(f, encoding='utf-8').read()
        if 'wk-grid' in doc:
            continue
        m = re.search(r'<main class="w">(.*?)</main>', doc, re.S)
        if not m:
            continue
        lb, ic = label[a['g']]
        top = f'<div class="wk-top"><a href="/wiki/">📚 루리 위키</a><span>›</span><span>{ic} {E(lb)}</span></div>'
        shell = ('<main class="w wk"><div class="wk-grid">' + _side(arts, a) + '<article class="wk-art">' + top + m.group(1) + _pn(arts, a) + '</article>' + _toc(a) + '</div>'
                 '<link rel="stylesheet" href="/assets/wiki/wiki.css?v=1"><script defer src="/assets/wiki/wiki.js?v=1"></script></main>')
        doc = doc[:m.start()] + shell + doc[m.end():]
        open(f, 'w', encoding='utf-8', newline='\n').write(doc)
        n += 1
    return n


def hub(arts, page_fn, site):
    cards, byg = '', {}
    for key, label, ic, _ in GROUPS:
        L = [a for a in arts if a['g'] == key]
        if not L:
            continue
        byg[key] = L
        li = ''.join(f'<li><a href="{E(a["u"])}"><b>{E(a["title"][:48])}</b><span>{E(a["desc"])}</span></a></li>' for a in L)
        cards += (f'<section class="wk-card" id="g-{key}"><h2>{ic} {E(label)} <small>{len(L)}편</small></h2>'
                  f'<ul class="wk-list">{li}</ul></section>')
    start = [a for u in START for a in arts if a['u'] == u]
    st = ''.join(f'<a href="{E(a["u"])}"><b>{E(a["title"][:40])}</b><span>{E(a["desc"][:70])}</span></a>' for a in start[:5])
    chips = ''.join(f'<a href="#g-{k}">{ic} {E(lb)} <small>{len(byg[k])}</small></a>' for k, lb, ic, _ in GROUPS if k in byg)
    body = (f'<p class="bc"><a href="/">홈</a> › 루리 위키</p>'
            '<header class="wk-hero"><h1>📚 루리 위키</h1><p>공식 출처로 확인한 생활 돈·응모·개발 지식을 한곳에 모았어요. 글마다 확인일과 출처를 적고, 확인하지 못한 값은 비워 둡니다.</p>'
            '<input class="wk-hq" type="search" placeholder="예: 에너지바우처, 근로장려금, 퇴직금, D1" aria-label="위키 검색" autocomplete="off"><div class="wk-res" aria-live="polite"></div>'
            f'<div class="wk-chips">{chips}</div></header>'
            + (f'<section class="wk-start"><h2>처음 읽는다면</h2><div class="wk-sgrid">{st}</div></section>' if st else '')
            + cards + '<link rel="stylesheet" href="/assets/wiki/wiki.css?v=1"><script defer src="/assets/wiki/wiki.js?v=1"></script>')
    page_fn('/wiki/', '루리 위키 — 생활 돈 가이드·응모 가이드·개발 지식 한곳에', f'공식 출처로 확인한 생활 돈 가이드 {len(byg.get("money", []))}편과 응모·고민 해결 가이드, 개발 지식, 평론을 한곳에서 검색하고 읽어요.',
            body, [('루리의 줍줍', '/'), ('루리 위키', '/wiki/')])


def build_wiki(urls, noindex, page_fn, root, site):
    arts = collect(urls, noindex, root)
    os.makedirs(os.path.join(root, 'assets', 'wiki'), exist_ok=True)
    json.dump([{'u': a['u'], 't': a['title'], 'g': a['g'], 'd': a['desc']} for a in arts],
              open(os.path.join(root, 'assets', 'wiki', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    hub(arts, page_fn, site)
    return len(arts), inject(arts, root)
