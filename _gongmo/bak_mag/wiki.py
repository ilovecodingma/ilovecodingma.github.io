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


def _trim(t, n=100):
    """요약은 완결된 문장으로. 첫 문장이 길면 마지막 공백에서 자르고, 금액·단위 중간(숫자 바로 뒤)에서는 끊지 않는다."""
    t = re.sub(r'\s+', ' ', t).strip()
    m = re.match(r'(.+?[요다])\.(?:\s|$)', t)
    if m and len(m.group(1)) + 1 <= n:
        return m.group(1) + '.'
    if len(t) <= n:
        return t
    cut = t[:n]
    sp = cut.rfind(' ')
    cut = cut[:sp] if sp > n * 0.5 else cut
    cut = re.sub(r'[\s·,(\[]+$', '', cut)
    while re.search(r'[\d,]$', cut):
        sp = cut.rfind(' ')
        if sp < 20:
            break
        cut = cut[:sp]
    return cut + '…'


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
        desc, fb = '', ''
        LAW = re.compile(r'시행규칙|시행령|별표|제\d+조|제\d+항|법률|조문')   # 법령 문장은 카드 요약으로 쓰지 않는다(2026-10-23 UI 2차 10번)
        for p in re.findall(r'<(?:p|li)[^>]*>(.*?)</(?:p|li)>', mh[mh.find('</h1>'):], re.S):
            t = _clean(p)
            if len(t) >= 40 and not t.startswith(('기준', '홈 ›')) and not LAW.search(t):
                c = _trim(t, 72)
                if not c.endswith('…'):
                    desc = c
                    break
                fb = fb or c
        desc = desc or fb
        # id 가 h2 에 있거나(공용 글), h2 를 감싸는 section 에 있는(생활 돈 가이드) 두 경우를 모두 읽는다
        heads = [(i, re.sub(r'^[\d?]+\s*', '', _clean(t))) for _tg, i, t in re.findall(r'<(section|h2)\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', mh, re.S) if len(_clean(t)) < 120]
        dt = (re.search(r'확인일\s*(\d{4}-\d{2}-\d{2})', mh) or [0, ''])[1]
        seen.add(u)
        arts.append({'u': u, 'g': g[0], 'title': title, 'desc': desc, 'heads': heads, 'dt': dt})
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
                 '<link rel="stylesheet" href="/assets/wiki/wiki.css?v=2"><script defer src="/assets/wiki/wiki.js?v=2"></script></main>')
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
    start = sorted([a for a in arts if a['g'] == 'money' and a.get('dt')], key=lambda a: a['dt'], reverse=True)[:5]
    st = ''.join(f'<a href="{E(a["u"])}"><b>{E(a["title"][:44])}</b><span>{E(a["desc"])}</span><small>확인일 {E(a["dt"])}</small></a>' for a in start)
    chips = ''.join(f'<a href="#g-{k}">{ic} {E(lb)} <small>{len(byg[k])}</small></a>' for k, lb, ic, _ in GROUPS if k in byg)
    body = (f'<p class="bc"><a href="/">홈</a> › 루리 위키</p>'
            '<header class="wk-hero"><h1>📚 루리 위키</h1><p>공식 출처로 확인한 생활 돈·응모·개발 지식을 한곳에 모았어요. 글마다 확인일과 출처를 적고, 확인하지 못한 값은 비워 둡니다.</p>'
            '<input class="wk-hq" type="search" placeholder="예: 에너지바우처, 근로장려금, 퇴직금" aria-label="위키 검색" autocomplete="off"><div class="wk-sc" role="group" aria-label="검색 범위"><button type="button" class="on" data-s="">전체</button><button type="button" data-s="money">생활 돈</button><button type="button" data-s="guide">가이드</button><button type="button" data-s="dev">개발·기타</button></div><div class="wk-res" aria-live="polite"></div>'
            f'<div class="wk-chips">{chips}</div></header>'
            + (f'<section class="wk-start"><h2>최근 확인한 가이드 <small>확인일이 가장 최근인 5편</small></h2><div class="wk-sgrid">{st}</div></section>' if st else '')
            + cards + '<link rel="stylesheet" href="/assets/wiki/wiki.css?v=2"><script defer src="/assets/wiki/wiki.js?v=2"></script>')
    page_fn('/wiki/', '루리 위키 — 생활 돈 가이드·응모 가이드·개발 지식 한곳에', f'공식 출처로 확인한 생활 돈 가이드 {len(byg.get("money", []))}편과 응모·고민 해결 가이드, 개발 지식, 평론을 한곳에서 검색하고 읽어요.',
            body, [('루리의 줍줍', '/'), ('루리 위키', '/wiki/')])


def build_wiki(urls, noindex, page_fn, root, site):
    arts = collect(urls, noindex, root)
    os.makedirs(os.path.join(root, 'assets', 'wiki'), exist_ok=True)
    json.dump([{'u': a['u'], 't': a['title'], 'g': a['g'], 'd': a['desc'], 'dt': a.get('dt', '')} for a in arts],
              open(os.path.join(root, 'assets', 'wiki', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    hub(arts, page_fn, site)
    return len(arts), inject(arts, root)
