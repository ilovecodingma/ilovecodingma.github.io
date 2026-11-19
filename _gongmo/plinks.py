# -*- coding: utf-8 -*-
"""내부 링크 보강(2026-11-19 마케터 「구글을 뚫어야 해」 전술, 개발 몫): 빌드가 끝난 HTML 에 링크 블록을 끼워 넣는다(prune_1116 과 같은 사후 처리, 매 빌드 멱등).
 A. 지금 많이 찾는 가이드(우선 10편): 홈·가이드·이슈·공모전·돈 허브와 방문이 많은 글 4곳
 B. 링크를 2개 미만 받는 글: /more/ 모음 페이지 + 같은 분야 허브의 「이 분야의 다른 글」 (글마다 인바운드 2개 이상이 되게)
 블록은 <!--pl-->…<!--/pl--> 로 감싸고, 인바운드 계산에서는 이 블록을 뺀다(없애도 다음 빌드에서 같은 결과가 나오게)."""
import html
import json
import os
import re
import urllib.parse as up

E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRIORITY = ['/guide/employment-support-target-veterans-apply/', '/guide/conditional-recipient-self-support-work-duty/', '/money/guide/suneung-2027-admit-card-reissue/',
            '/money/guide/teacher-pay-2027-salary-table/', '/money/guide/industrial-accident-insurance-rate-2027/', '/contest/deadline-11/',
            '/guide/ulsan-youth-rent-support-2026-apply/', '/guide/daily-worker-short-job-wage-tax-insurance/', '/money/guide/civil-servant-pay-2027-schedule/',
            '/guide/national-technical-qualification-exam-fee-refund/']
HOSTS_A = ['/', '/money/guide/', '/guide/', '/issue/', '/contest/', '/money/guide/insurance-rates-2027-table/', '/money/guide/teacher-exam-2027-schedule/',
           '/issue/suneung-day-checklist-1104/', '/issue/insurance-rates-2027-1104/']
AREA_HUBS = {'/lab/': '/lab/', '/issue/': '/issue/', '/analyst/': '/analyst/', '/money/': '/money/guide/', '/hot/': '/hot/', '/pick/': '/pick/', '/fridge/': '/fridge/', '/ssul/': '/ssul/'}
MARK = re.compile(r'<!--pl-->.*?<!--/pl-->', re.S)
CSS = '<style>.pl{margin:28px 0;padding:14px 16px;border:1px solid #e2e8f0;border-radius:10px}.pl h2{font-size:18px;margin:0 0 8px}.pl ul{margin:0;padding-left:18px}.pl li{margin:4px 0;line-height:1.6}</style>'


def _f(u):
    return os.path.join(ROOT, u.strip('/'), 'index.html') if u != '/' else os.path.join(ROOT, 'index.html')


def _read(u):
    try:
        return open(_f(u), encoding='utf-8', errors='ignore').read()
    except OSError:
        return ''


def _title(u):
    h = _read(u)
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) or re.search(r'<title>(.*?)</title>', h, re.S)
    t = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
    return html.unescape(t.split(' | ')[0])[:60]


def _inject(u, block):
    p = _f(u)
    if not os.path.exists(p):
        return False
    h = open(p, encoding='utf-8').read()
    h = MARK.sub('', h)
    b = '<!--pl-->' + block + '<!--/pl-->'
    for tag in ('</main>', '<footer', '</body>'):
        if tag in h:
            h = h.replace(tag, b + tag, 1)
            open(p, 'w', encoding='utf-8', newline='\n').write(h)
            return True
    return False


def fix_ld(urls):
    """Article 구조화 데이터에 dateModified 가 없는 /guide/ 글에 넣는다(값은 사이트맵 lastmod.json 의 지난 빌드 날짜, 없으면 게시일)."""
    try:
        lm = json.load(open(os.path.join(HERE, 'lastmod.json'), encoding='utf-8'))
    except Exception:
        lm = {}
    n = 0
    for u in urls:
        if not u.startswith('/guide/') or not u.endswith('/'):
            continue
        p = _f(u)
        if not os.path.exists(p):
            continue
        h = open(p, encoding='utf-8').read()
        changed = False

        def sub(m):
            nonlocal changed
            try:
                j = json.loads(m.group(1))
            except Exception:
                return m.group(0)
            if isinstance(j, dict) and j.get('@type') == 'Article' and not j.get('dateModified') and j.get('datePublished'):
                j['dateModified'] = (lm.get(u) or [None, j['datePublished']])[1] or j['datePublished']
                changed = True
                return '<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False).replace('</', '<' + chr(92) + '/') + '</script>'
            return m.group(0)
        h2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', sub, h, flags=re.S)
        if changed:
            open(p, 'w', encoding='utf-8', newline=chr(10)).write(h2)
            n += 1
    return n


def run(urls, page):
    sm = {u for u in urls if u.endswith('/')}
    # 인바운드 계산(우리가 끼운 블록은 뺀다)
    inb = {}
    for u in sm:
        if u == '/more/':
            continue   # 모음 페이지의 링크는 세지 않는다(세면 다음 빌드에서 목록이 비어 오락가락한다)
        h = MARK.sub('', _read(u))
        for m in set(re.findall(r'href="(/[^"#?]*)', h)):
            m = up.unquote(m)
            if not m.endswith('/') and '.' not in m.rsplit('/', 1)[-1]:
                m += '/'
            if m in sm and m != u:
                inb[m] = inb.get(m, 0) + 1
    low = sorted(u for u in sm if inb.get(u, 0) < 2 and not u.startswith(('/book/', '/c/', '/a/', '/devlog/', '/more/')) and os.path.exists(_f(u)))
    # /more/ 모음 페이지(분야별 전체 목록)
    by0 = {}
    for u in low:
        by0.setdefault(next((a for a in AREA_HUBS if u.startswith(a)), '기타'), []).append(u)
    NM = {'/lab/': '수상작·분석', '/issue/': '이슈', '/analyst/': '분석', '/money/': '돈·생활 가이드', '/hot/': '요즘 뜨는 주제', '/pick/': '추천', '/fridge/': '냉장고', '/ssul/': '이야기', '기타': '기타'}
    secs = ''.join(f'<h2>{E(NM.get(k, k))}</h2><ul>' + ''.join(f'<li><a href="{E(u)}">{E(_title(u) or u)}</a></li>' for u in lst) + '</ul>' for k, lst in by0.items())
    page('/more/', '놓치기 쉬운 글 모음 — 루리 줍줍', '검색이나 목록에서 놓치기 쉬운 가이드·이슈·분석 글을 분야별로 모았습니다.',
         '<div class="sk"><p class="bc"><a href="/">홈</a> › 놓치기 쉬운 글</p><h1>놓치기 쉬운 글 모음</h1><p>목록 깊숙이 있어 잘 보이지 않는 글을 분야별로 모았습니다.</p>' + secs + '</div>', [('홈', '/'), ('놓치기 쉬운 글', '/more/')])
    sm.add('/more/')
    # A
    pri = [(u, _title(u)) for u in PRIORITY if os.path.exists(_f(u))]
    blockA = ('<section class="pl"><h2>지금 많이 찾는 가이드</h2><ul>' + ''.join(f'<li><a href="{E(u)}">{E(t)}</a></li>' for u, t in pri) + '<li><a href="/more/">놓치기 쉬운 글 모음 →</a></li></ul></section>' + CSS)
    nA = sum(_inject(u, blockA) for u in HOSTS_A if u in sm)
    # B: /more/ 모음(분야별) + 분야 허브 블록
    by = {}
    for u in low:
        k = next((a for a in AREA_HUBS if u.startswith(a)), '기타')
        by.setdefault(k, []).append(u)
    nB = 0
    for k, lst in by.items():
        hub = AREA_HUBS.get(k)
        if not hub or hub not in sm:
            continue
        blk = ('<section class="pl"><h2>이 분야의 다른 글</h2><ul>' + ''.join(f'<li><a href="{E(u)}">{E(_title(u) or u)}</a></li>' for u in lst[:60]) + '</ul></section>' + CSS)
        nB += _inject(hub, blk)
    return dict(ld_fixed=fix_ld(urls), low=len(low), hosts_a=nA, hubs_b=nB, by={k: len(v) for k, v in by.items()}), low
