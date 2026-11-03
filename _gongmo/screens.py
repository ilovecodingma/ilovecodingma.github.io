# -*- coding: utf-8 -*-
"""홈(/)과 오늘 마감(/today/) 화면 (2026-10-23 화면별 UI 개선 지침 P1).
홈: 사이트 가치 한 문장 → 통합 검색 → 목적별 바로가기 → AI 수집 현황 → 실제 콘텐츠(오늘 마감·새로 확인·추천 가이드) → 전체 서비스 → 짧은 소개.
오늘 마감: 오늘 끝나는 기회만, 필터(전체/공모전/이벤트/지원금/주거 청약/공모주), 통일된 카드(제목·대상·혜택·마감·이동), 시각을 모르면 「시각 미확인」.
build.py 의 함수는 ctx 로 받는다(순환 import 방지)."""
import re, json, datetime, html as H
import contest_quality as CQ
import shorten as SH

E = lambda t: H.escape(str(t if t is not None else ''), quote=True)


def _short(t, n):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


def due_items(ctx, today_only=True):
    """오늘 마감 항목(공모전·이벤트·지원금·청약·공모주)을 같은 모양의 dict 로 모은다."""
    T = ctx['today'].isoformat(); out = []
    for c in ctx['contests']:
        if c['id'] in ctx['DUP'] or c['end'] != T:
            continue
        dr = ctx['deadline_row'](c, '')
        tm = re.match(r'(\d{1,2}(?::\d{2}|시))', dr)
        out.append({'type': '공모전', 'title': c['title'], 'target': ctx['elig_short'](c), 'benefit': ctx['prize_short'](c),
                    'time': tm.group(1) if tm else '', 'href': f'/c/{c["id"]}/', 'ext': c.get('link') or '', 'org': c.get('org') or '', 'cid': c['id'], 'end': c['end'], 'dleft': 0, 'tstate': ctx['deadline_state'](c), 'ver': c['id'] in (ctx.get('VER') or {})})
    for e in ctx['events']:
        if e['end'] != T:
            continue
        out.append({'type': '이벤트', 'title': ctx['tidy_ev'](e['title']), 'target': None, 'benefit': '경품 이벤트 · ' + (e.get('effort') or ctx['EASY'].get(e['type'], e['type'])),
                    'time': '', 'href': '', 'ext': e.get('link') or '', 'org': e.get('org') or ''})
    for a in ctx['aps']:
        if a.get('always') or a['end'] != T or a['id'] in ctx['AP_DUP']:
            continue
        kk = a.get('kk') or ''
        typ = '공모주' if kk == 'ipo' else '주거 청약' if kk in ('apt', 'rent', 'lh') else '지원금'
        tg = None if typ == '공모주' else (SH.clip(re.sub(r'^\([^)]{1,6}\)\s*', '', a.get('target') or ''), 22) or ('확인 필요' if typ == '지원금' else None))
        out.append({'type': typ, 'title': a['title'], 'target': tg, 'benefit': (SH.clip(a.get('benefit') or '', 26) or a.get('kind') or '확인 필요') if typ != '공모주' else '청약 ' + a['start'][5:].replace('-', '.') + ' ~ ' + a['end'][5:].replace('-', '.'),
                    'time': '', 'href': f'/a/{a["id"]}/', 'ext': a.get('url') or '', 'org': a.get('org') or ''})
    return out


def _dl(it):
    day = '오늘' if it.get('dleft', 0) == 0 else f'{it["end"][5:].replace("-", ".")}(D-{it["dleft"]})'
    st = it.get('tstate', 'unknown')
    tm = f'{day} <b>{E(it["time"])}</b>' if it['time'] else (f'{day} · <span class="nu">시각 명시 없음</span>' if st == 'absent' else f'{day} · <span class="nu">시각 확인 필요</span>')
    rows = []
    if it['target'] is not None:
        rows.append(('대상', it['target']))
    rows.append(('혜택', it['benefit']))
    return ''.join(f'<div><dt>{k}</dt><dd{" class=nu" if v == "확인 필요" else ""}>{E(v)}</dd></div>' for k, v in rows) + f'<div><dt>마감</dt><dd>{tm}</dd></div>'


def _card(it):
    tm = f'오늘 <b>{E(it["time"])}</b>' if it['time'] else '오늘 · <span class="nu">시각 미확인</span>'
    btns = ''
    if it['href']:
        btns += f'<a class="b1" href="{E(it["href"])}">상세 보기</a>'
    if it['ext']:
        btns += f'<a class="b2" href="{E(it["ext"])}" target="_blank" rel="noopener nofollow">{E('공식 공고·접수' if it.get('ver') else CQ.link_label(it["ext"]))} ↗</a>' if it['type'] != '이벤트' else f'<a class="b1" href="{E(it["ext"])}" target="_blank" rel="noopener nofollow">이벤트 보기 ↗</a>'
    return (f'<li class="td-c" data-t="{E(it["type"])}"><span class="td-t">{E(it["type"])}</span><h3>{E(_short(it["title"], 60))}</h3>'
            f'<dl>{_dl(it)}</dl>'
            f'<div class="td-b">{btns}</div></li>')


def today_html(ctx):
    items = due_items(ctx)
    order = {'공모전': 0, '지원금': 1, '주거 청약': 2, '공모주': 3, '이벤트': 4}
    items.sort(key=lambda x: (order.get(x['type'], 9), x['title']))
    cnt = {k: sum(1 for i in items if i['type'] == k) for k in order}
    chips = f'<button type="button" class="on" data-f="">전체 <small>{len(items)}</small></button>' + ''.join(f'<button type="button" data-f="{k}">{k} <small>{v}</small></button>' for k, v in cnt.items())
    now = ctx['now']
    lst = ''.join(_card(i) for i in items) or '<li class="td-empty">오늘 마감하는 항목이 없어요. 내일 마감하는 공모전은 <a href="/contest/">공모전 목록</a>에서 마감순으로 볼 수 있어요.</li>'
    return (f'<p class="bc"><a href="/">홈</a> › 오늘 마감</p><h1 class="td-h1">오늘 마감하는 기회</h1>'
            f'<p class="td-sub">{now:%Y년 %m월 %d일}(한국 시간) 마감 · {now:%H:%M} 갱신 · 마감 시각을 알 수 없으면 「시각 미확인」으로 표시해요</p>'
            f'<div class="td-f" role="group" aria-label="유형 필터">{chips}</div>'
            f'<ul class="td-l" id="tdl">{lst}</ul><p class="td-n" id="tdn" hidden>이 유형은 오늘 마감하는 항목이 없어요.</p>'
            '<p class="note">뉴스·웹툰·레시피 등 다른 주제는 <a href="/">홈</a>에서 찾아보세요. 마감 정보는 자동 수집 값이라 신청 전에 공식 사이트에서 다시 확인하세요.</p>'
            '<link rel="stylesheet" href="/assets/home/screens.css?v=5"><script defer src="/assets/home/screens.js?v=1"></script>')


def ver_items(ctx, limit=6):
    """공식 원문까지 대조한 진행 중 공모전(마감 임박순). 홈에서 확인 수준이 높은 콘텐츠를 먼저 보여 주기 위한 목록."""
    T = ctx['today'].isoformat(); V = ctx.get('VER') or {}; out = []
    for c in sorted(ctx['contests'], key=lambda c: c['end']):
        if c['id'] not in V or c['id'] in ctx['DUP'] or c['end'] < T or ctx['elig_short'](c) == '확인 필요':   # 대상이 비어 있는 공고는 홈 대표 영역에 올리지 않는다
            continue
        lv = V[c['id']].get('level')
        dr = ctx['deadline_row'](c, '')
        tm = re.match(r'(\d{1,2}(?::\d{2}|시))', dr)
        out.append({'type': '공모전', 'title': c['title'], 'target': ctx['elig_short'](c), 'benefit': ctx['prize_short'](c), 'time': tm.group(1) if tm else '',
                    'href': f'/c/{c["id"]}/', 'ext': c.get('link') or '', 'org': c.get('org') or '', 'cid': c['id'], 'end': c['end'], 'dleft': (datetime.date.fromisoformat(c['end']) - ctx['today']).days, 'tstate': ctx['deadline_state'](c), 'ver': True, 'full': lv != 'partial'})
    out.sort(key=lambda x: (0 if x['full'] else 1, x['end']))
    return out[:limit]


def _new_guides_sec():
    """홈에서 새로 올라온 돈 가이드로 가는 링크(2026-11-02 색인 경로: kin_guides.json 은 새 글이 뒤에 붙는다)"""
    import os
    try:
        g = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kin_guides.json'), encoding='utf-8'))['guides'][-8:][::-1]
    except Exception:
        return ''
    li = ''.join(f'<li><a href="/money/guide/{x["slug"]}/"><b>{E(_short(x["title"], 60))}</b><span>{E(x["name"])}</span></a></li>' for x in g)
    return f'<section class="hm-sec"><div class="hm-h"><h2>새로 올라온 생활 가이드</h2><a href="/money/guide/">전체 보기 →</a></div><ul class="hm-nl">{li}</ul></section>'


def _today_hot_sec():
    """홈 「오늘 많이 찾는 것」: 마케터 이슈 원고(issues/*.json, 보관 기간 안) 먼저, 그다음 지금 뜨는 핫이슈(48시간 안, 언론사 많은 순). 잡지 커버스토리 칸(2026-11-02)."""
    import os, datetime
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    today = datetime.date.today()
    cards = []
    idir = os.path.join(here, 'issues')
    if os.path.isdir(idir):
        _lst = []
        for fn in os.listdir(idir):
            if not fn.endswith('.json'):
                continue
            try:
                c = json.load(open(os.path.join(idir, fn), encoding='utf-8'))
                d0 = datetime.date.fromisoformat(c['date'])
            except Exception:
                continue
            _lst.append((d0.isoformat(), int(c.get('priority', 0)), os.path.getmtime(os.path.join(idir, fn)), c, d0))
        for _dd, _pr, _mt, c, d0 in sorted(_lst, key=lambda x: (x[0], x[1], x[2]), reverse=True):   # 최신 날짜 → priority(마케터 지정, 클수록 위) → 최근 수정 순
            if (today - d0).days > int(c.get('keep_days', 4)) or not os.path.exists(os.path.join(root, 'issue', c['slug'], 'index.html')):
                continue
            cards.append((d0.isoformat(), f'/issue/{c["slug"]}/', c['h1'], f'{c["date"][5:].replace("-", "/")} 기준 · 이슈 정리'))
    try:
        db = json.load(open(os.path.join(root, 'hot', 'db.json'), encoding='utf-8'))
        cut = (datetime.datetime.now() - datetime.timedelta(hours=48)).strftime('%Y-%m-%d %H:%M')
        hot = sorted([v for v in db.values() if not v.get('dup') and v['last'] >= cut and os.path.exists(os.path.join(root, 'hot', v['slug'], 'index.html'))],
                     key=lambda v: (-len(v['outs']), v['last']))
        for v in hot:
            cards.append((v['last'], f'/hot/{v["slug"]}/', v['title'], f'언론사 {len(v["outs"])}곳 보도 · {v["last"][5:10].replace("-", "/")}'))
    except Exception:
        pass
    cards = cards[:5]
    if not cards:
        return ''
    li = ''.join(f'<li><a href="{E(u)}"><b>{E(_short(t, 60))}</b><span>{E(sub)}</span></a></li>' for _d, u, t, sub in cards)
    return f'<section class="hm-sec"><div class="hm-h"><h2>오늘 많이 찾는 것</h2><a href="/issue/">이슈 전체 →</a></div><ul class="hm-nl">{li}</ul></section>'


def _tier_sec():
    """홈 「궁금증 3단」: keywords.json(마케터 키워드 장부)에서 상태=작성·페이지 있음·만료 전인 항목을 단기/중기/장기로 나눠 보여 준다(2026-11-03 사이트 컨셉 전환)."""
    import os, datetime, hashlib
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    try:
        items = json.load(open(os.path.join(here, 'keywords.json'), encoding='utf-8'))['items']
    except Exception:
        return ''
    today = datetime.date.today().isoformat()
    by = {'단기': [], '중기': [], '장기': []}
    for i in items:
        p = i.get('page') or ''
        if i.get('status') != '작성' or not p or i.get('tier') not in by:
            continue
        if i.get('expires') and i['expires'] < today:
            continue
        if not os.path.exists(os.path.join(root, p.strip('/'), 'index.html')):
            continue
        by[i['tier']].append(i)
    def pick(t, n):
        L = by[t]
        if t == '장기':   # 장기는 날마다 다른 묶음이 보이도록 날짜로 돌린다
            L = sorted(L, key=lambda i: hashlib.md5((today + i['query']).encode()).hexdigest())
        else:
            L = sorted(L, key=lambda i: (i.get('registered', ''), i.get('score', 0)), reverse=True)
        return L[:n]
    cols = (('단기', '지금 급상승', '며칠 안에 내려가는 이슈', 5, '/issue/'), ('중기', '이번 달 관심사', '2주 안팎 이어지는 주제', 4, '/issue/'), ('장기', '오래 찾는 것', '해마다 다시 찾는 제도·방법', 6, '/money/guide/'))
    out = ''
    for t, h, sub, n, more in cols:
        L = pick(t, n)
        if not L:
            continue
        li = ''.join(f'<li><a href="{E(i["page"])}"><b>{E(_short(i["query"], 54))}</b></a></li>' for i in L)
        out += f'<div class="hm-tc"><h3>{h}</h3><p>{sub}</p><ul class="hm-nl">{li}</ul><a class="hm-tm" href="{more}">더 보기 →</a></div>'
    if not out:
        return ''
    return f'<section class="hm-sec hm-tier"><div class="hm-h"><h2>사람들이 궁금해하는 것</h2></div><div class="hm-tg">{out}</div></section>'


def _kwmap_sec(full=False):
    """홈 「키워드 3D 지도」(2026-11-03 사용자: 키워드 노드를 따라가는 형식·3D): keywords.json 의 작성된 글을 노드로, 겹치는 단어를 선으로 보여 준다."""
    import os, re, datetime
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    try:
        items = json.load(open(os.path.join(here, 'keywords.json'), encoding='utf-8'))['items']
    except Exception:
        return ''
    today = datetime.date.today().isoformat()
    ok = []
    for i in items:
        p = i.get('page') or ''
        if i.get('status') != '작성' or not p or (i.get('expires') and i['expires'] < today):
            continue
        if not os.path.exists(os.path.join(root, p.strip('/'), 'index.html')):
            continue
        ok.append(i)
    tier = {'단기': 0, '중기': 1, '장기': 2}
    lim = {0: 40, 1: 40, 2: 70 if not full else 400}
    nodes, cnt = [], {0: 0, 1: 0, 2: 0}
    for i in sorted(ok, key=lambda i: (tier[i['tier']], -(i.get('score') or 0), i.get('query', ''))):
        t = tier[i['tier']]
        if cnt[t] >= lim[t]:
            continue
        cnt[t] += 1
        nodes.append({'q': i['query'], 't': t, 'u': i['page']})
    if len(nodes) < 8:
        return ''
    stop = {'방법', '신청', '조건', '대상', '기준', '정리', '언제', '확인', '계산', '가이드', '지원금', '2026', '2027'}
    toks = [{w for w in re.findall(r'[가-힣A-Za-z0-9]{2,}', n['q']) if w not in stop} for n in nodes]
    edges, deg = [], [0] * len(nodes)
    for a in range(len(nodes)):
        for b in range(a + 1, len(nodes)):
            if deg[a] >= 3 or deg[b] >= 3:
                continue
            if toks[a] & toks[b]:
                edges.append([a, b]); deg[a] += 1; deg[b] += 1
    data = json.dumps({'n': nodes, 'e': edges}, ensure_ascii=False).replace('</', '<' + chr(92) + '/')
    head = '' if full else '<div class="hm-h"><h2>키워드 지도</h2><a href="/map/">크게 보기 →</a></div>'
    return (f'<section class="hm-sec hm-kw">{head}<p class="note"><i class="kd" style="background:#e5484d"></i>단기 · <i class="kd" style="background:#d97706"></i>중기 · <i class="kd" style="background:#2563eb"></i>장기 — 끌어서 돌리고, 점을 누르면 해당 글로 이동합니다. 선은 겹치는 단어로 이어집니다.</p>'
            f'<div id="kwmap" class="kw-box"></div><script type="application/json" id="kwdata">{data}</script><script defer src="/assets/home/kwmap.js?v=1"></script></section>')


def _concept_sec():
    """홈 첫 화면 설명 띠(2026-11-03 사용자: 메인에서 화려하게 설명): 컨셉 3단계와 장부 숫자, 작동 순서."""
    import os, datetime
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    c = {'단기': 0, '중기': 0, '장기': 0}; tot = 0
    try:
        today = datetime.date.today().isoformat()
        for i in json.load(open(os.path.join(here, 'keywords.json'), encoding='utf-8'))['items']:
            if i.get('status') == '작성' and not (i.get('expires') and i['expires'] < today) and i.get('tier') in c:
                c[i['tier']] += 1; tot += 1
    except Exception:
        pass
    def card(cls, tag, h, p, n, unit):
        return f'<div class="cp-c {cls}"><span class="cp-t">{tag}</span><b class="cp-n">{n}<small>{unit}</small></b><h3>{h}</h3><p>{p}</p></div>'
    cards = (card('s', '단기 · 3~4일', '지금 급상승', '뉴스·트렌드에서 갑자기 뜬 질문을 빠르게 확인해 정리하고, 며칠 뒤 내립니다.', c['단기'], '건')
             + card('m', '중기 · 약 2주', '이번 달 관심사', '시즌과 검색 흐름이 이어지는 주제를 2주 단위로 다룹니다.', c['중기'], '건')
             + card('l', '장기 · 계속', '오래 찾는 것', '해마다 반복되는 제도와 방법을 공식 자료로 깊게 정리해 유지합니다.', c['장기'], '건'))
    flow = ''.join(f'<li><i>{n}</i><b>{a}</b><span>{b}</span></li>' for n, a, b in (
        (1, '신호 수집', '자동완성·검색 콘솔·지식인·커뮤니티·뉴스'), (2, '분석', '겹침 대조, 점수화, 단기·중기·장기 분류'),
        (3, '작성', '공식 출처와 기준일을 단 분석 글'), (4, '루리 위키에 기록', '검색으로 찾아오는 문서, 기간 지난 단기 글은 정리')))
    return (f'<section class="cp"><p class="cp-k">LURI ANALYST · LIVE ARCHIVE</p><h2 class="cp-h">사람들이 궁금해하는 것을<br><em>실시간으로 찾아 기록</em>합니다</h2>'
            f'<p class="cp-s">루리 애널리스트는 검색어·자동완성·커뮤니티·뉴스 신호를 매시간 수집하고 분석해, 사람들이 궁금해하는 질문을 찾아냅니다. 찾아낸 질문은 공식 출처 기준의 문서로 <b>루리 위키</b>에 기록하고, 현재 <b>{tot}개</b>의 질문이 쌓여 있습니다.</p>'
            f'<div class="cp-g">{cards}</div><ol class="cp-f">{flow}</ol><p class="cp-a"><a class="cp-btn" href="/wiki/">루리 위키 열기 →</a><a class="cp-btn o" href="/map/">키워드 지도 보기</a></p></section>')


def _indicator_sec():
    """홈 「지표 현황」: rsi_daily.json(마케터가 매일 갱신)에서 RSI 낮은 순을 보여 주는 지표 칸. 추천이 아니라 현황이다(2026-11-02)."""
    import os
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rsi_daily.json')
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        return ''
    its = [x for x in d.get('items', []) if x.get('rsi') is not None]
    if not its:
        return ''
    os_n = sum(1 for x in its if x['rsi'] <= 30)
    ob_n = sum(1 for x in its if x['rsi'] >= 70)
    pick = []
    for g in ('국내 대형주', '업비트 원화'):
        pick += sorted([x for x in its if x.get('market') == g], key=lambda x: x['rsi'])[:3]
    li = ''.join(f'<li><a href="/analyst/rsi/"><b>{E(x["name"])} · RSI {x["rsi"]:.1f}</b><span>{E(x.get("market", ""))}'
                 + (f' · 52주 고점 대비 {x["from_high"]:+.1f}%' if x.get('from_high') is not None else '') + '</span></a></li>' for x in pick)
    return (f'<section class="hm-sec"><div class="hm-h"><h2>지표 현황</h2><a href="/analyst/rsi/">RSI 현황표 →</a></div>'
            f'<p class="note">{E(d.get("asof", ""))} 기준 RSI(14일) 30 이하 {os_n}개 · 70 이상 {ob_n}개. RSI가 낮은 순으로 보여 주는 지표 현황이고, 투자 권유가 아니에요.</p>'
            f'<ul class="hm-nl">{li}</ul></section>')


def _field_sections():
    """홈 분야별 최신 3개(2026-11-02 마케터 분류표 guide_sections.json). 새 글일수록 kin_guides.json 뒤쪽이라 목록 순서로 최신을 고른다."""
    import os
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    try:
        gs = json.load(open(os.path.join(here, 'guide_sections.json'), encoding='utf-8'))
        kin = json.load(open(os.path.join(here, 'kin_guides.json'), encoding='utf-8'))['guides']
    except Exception:
        return ''
    pos = {g['slug']: i for i, g in enumerate(kin)}
    gm = {g['slug']: g for g in kin}
    icon = {'돈·지원금': '💰', '일·직장': '💼', '집·부동산': '🏠', '세금': '🧾', '건강·복지': '🩺', '생활': '🧺'}
    blocks = ''
    for f, L in gs.items():
        L = [x for x in L if x in pos and os.path.exists(os.path.join(root, 'money', 'guide', x, 'index.html'))]
        top = sorted(L, key=lambda x: -pos[x])[:3]
        if not top:
            continue
        li = ''.join(f'<li><a href="/money/guide/{x}/"><b>{E(_short(gm[x]["title"], 46))}</b></a></li>' for x in top)
        blocks += f'<div class="hm-fb"><h3>{icon.get(f, "📌")} {E(f)}</h3><ul>{li}</ul></div>'
    if not blocks:
        return ''
    return f'<section class="hm-sec"><div class="hm-h"><h2>분야별 새 글</h2><a href="/money/guide/">가이드 전체 →</a></div><div class="hm-fld">{blocks}</div></section>'


# ───────── 홈 개편 (2026-11-03): 검색 하나 → 지금 읽을 글 → 마감 임박 → 생활 가이드 → 주제 탐색 ─────────
_IC = {  # 같은 선 굵기·크기의 아이콘 한 벌
    'issue': '<path d="M4 5h13v14H6a2 2 0 0 1-2-2V5Zm13 3h3v9a2 2 0 0 1-2 2M8 9h5M8 13h5"/>',
    'apply': '<path d="M12 3v18M16 7.5c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.8 2.6 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3"/>',
    'contest': '<path d="M8 4h8v5a4 4 0 0 1-8 0V4ZM8 6H5v1a3 3 0 0 0 3 3M16 6h3v1a3 3 0 0 1-3 3M12 13v4M8 20h8"/>',
    'guide': '<path d="M5 4h9a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Zm3 4h6M8 12h6"/>',
    'recipe': '<path d="M6 3v7a2 2 0 0 0 2 2v9M10 3v7M8 3v7M17 3c-2 2-2 6 0 8v10"/>',
    'calc': '<path d="M6 3h12v18H6V3Zm3 4h6M9 11h.01M12 11h.01M15 11h.01M9 15h.01M12 15h.01M15 15h.01"/>',
    'wiki': '<path d="M4 6c3-1.5 5-1.5 8 0 3-1.5 5-1.5 8 0v13c-3-1.5-5-1.5-8 0-3-1.5-5-1.5-8 0V6Zm8 0v13"/>',
    'map': '<circle cx="6" cy="7" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><path d="m8 7.5 8-1M7 9l4 7M17 8l-4 8"/>',
    'chart': '<path d="M4 20V4M4 20h16M8 16l4-5 3 3 5-7"/>',
    'event': '<path d="M4 9h16v11H4V9Zm0 0V6h16v3M12 9v11"/>',
    'game': '<path d="M7 8h10a4 4 0 0 1 4 4v1a3 3 0 0 1-5.5 1.7L15 14H9l-.5.7A3 3 0 0 1 3 13v-1a4 4 0 0 1 4-4Zm1 3v3M6.5 12.5h3"/>',
    'search': '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/>',
    'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    'ext': '<path d="M14 4h6v6M20 4l-9 9M18 14v5H5V6h5"/>',
}


def _ic(k, cls='sv'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_IC[k]}</svg>'


def _dstr(iso):
    return iso[5:7].lstrip('0') + '.' + iso[8:10].lstrip('0') if iso else ''


def _first_sentences(t, n):
    t = re.sub(r'\s+', ' ', t or '').strip()
    if len(t) <= n:
        return t
    cut = t[:n]
    k = max(cut.rfind('다. '), cut.rfind('요. '), cut.rfind('. '))
    return cut[:k + 1].strip() if k > n * .5 else cut.rstrip() + '…'


def _read_candidates(ctx):
    """지금 읽을 글 후보: 마케터 이슈 원고(보관 기간 안, 최신·priority 순) → 최근 생활 가이드. (url, 주제, 제목, 요약, 날짜)"""
    import os
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    today = datetime.date.today(); out = []
    idir = os.path.join(here, 'issues'); L = []
    if os.path.isdir(idir):
        for fn in os.listdir(idir):
            if not fn.endswith('.json'):
                continue
            try:
                c = json.load(open(os.path.join(idir, fn), encoding='utf-8')); d0 = datetime.date.fromisoformat(c['date'])
            except Exception:
                continue
            if (today - d0).days > int(c.get('keep_days', 4)) or not os.path.exists(os.path.join(root, 'issue', c['slug'], 'index.html')):
                continue
            L.append((d0.isoformat(), int(c.get('priority', 0)), c))
    for d0, _p, c in sorted(L, key=lambda x: (x[0], x[1]), reverse=True):
        out.append((f'/issue/{c["slug"]}/', '이슈', c['h1'], c.get('summary') or c.get('desc') or '', d0))
    try:
        kin = json.load(open(os.path.join(here, 'kin_guides.json'), encoding='utf-8'))['guides']
    except Exception:
        kin = []
    for g in kin[::-1]:
        if not os.path.exists(os.path.join(root, 'money', 'guide', g['slug'], 'index.html')):
            continue
        m = re.search(r'확인일\s*(\d{4}-\d{2}-\d{2})', g.get('basis') or '')
        out.append((f'/money/guide/{g["slug"]}/', g.get('name') or '생활 가이드', g.get('h1') or g['title'], g.get('lead') or g.get('desc') or '', m.group(1) if m else ''))
    return out


def _dt(t):
    """화면 표시용 제목: 검색 노출용 긴 제목에서 기준일·연월·보조 설명을 덜어낸다(원제는 상세 페이지와 title 태그에 그대로)."""
    t = re.sub(r'\s+', ' ', t or '').strip()
    t = re.sub(r'\s*\((?:\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\s*기준\)\s*$', '', t)
    t = re.sub(r'\s*20\d\d년\s*\d{1,2}월\s*$', '', t)
    t = re.sub(r'\s*확인된 (?:내용|사실)(?: 정리| 총정리)?\s*$', '', t)
    for sep in (' — ', ': ', ' - '):
        if sep in t:
            a = t.split(sep)[0].strip()
            if len(a) >= 8:
                t = a
                break
    t = re.sub(r'\s*20\d\d\s*$', '', t).strip(' ?·,')
    return t + ('?' if re.search(r'(?:나요|까요|가요|할까)$', t) else '')


def _sec_read(cands, seen):
    pick = []
    for c in cands:
        if c[0] in seen:
            continue
        pick.append(c); seen.add(c[0])
        if len(pick) == 5:
            break
    if not pick:
        return ''
    f, rest = pick[0], pick[1:]
    dt = lambda c: f'<time datetime="{c[4]}">{_dstr(c[4])} 업데이트</time>' if c[4] else ''
    big = (f'<article class="rd-f"><p class="kk">{E(f[1])}</p><h3><a href="{E(f[0])}">{E(_dt(f[2]))}</a></h3><p class="sm">{E(_first_sentences(f[3], 150))}</p><p class="mt">{dt(f)}</p></article>')
    li = ''.join(f'<li><p class="kk">{E(c[1])}</p><h3><a href="{E(c[0])}">{E(_short(_dt(c[2]), 60))}</a></h3><p class="sm">{E(_first_sentences(c[3], 60))}</p><p class="mt">{dt(c)}</p></li>' for c in rest)
    return (f'<section class="h2-sec" aria-labelledby="s-read"><div class="h2-hd"><h2 id="s-read">지금 읽을 글</h2><a href="/issue/">이슈 전체 {_ic("arrow", "sv s")}</a></div>'
            f'<div class="rd-g">{big}<ul class="rd-l">{li}</ul></div></section>')


def _badge(ctx, cid):
    if cid in (ctx.get('OP') or ()):
        return '<span class="vb op" title="운영자가 직접 확인해 날짜를 남긴 공고">운영자 검토</span>'
    if cid in (ctx.get('VER') or {}):
        return '<span class="vb" title="AI가 공식 원문과 대조했고 운영자 검토는 아직 없음">AI 대조</span>'
    return ''


def _opp_cards(ctx, seen, limit=6):
    """마감 임박 공모전(4) + 지원금(2): 마감 빠른 순, 핵심 조건이 확인된 것만."""
    T = ctx['today']; Ti = T.isoformat(); out = []
    for c in sorted(ctx['contests'], key=lambda c: c['end']):
        if c['id'] in ctx['DUP'] or c['end'] < Ti or ctx['elig_short'](c) in ('확인 필요', '미확인') or ctx['prize_short'](c) == '확인 필요':
            continue
        if f'/c/{c["id"]}/' in seen:
            continue
        d = (datetime.date.fromisoformat(c['end']) - T).days
        if d > 21:
            continue
        out.append(('공모전', c['end'], d, c['title'], [('대상', ctx['elig_short'](c)), ('혜택', ctx['prize_short'](c))], f'/c/{c["id"]}/', c.get('link') or '', _badge(ctx, c['id']), c['id']))
    cs = out[:4]
    ap = []
    for a in sorted(ctx['aps'], key=lambda a: a['end']):
        if a.get('always') or a['end'] < Ti or a['id'] in ctx['AP_DUP'] or f'/a/{a["id"]}/' in seen:
            continue
        kk = a.get('kk') or ''
        if kk == 'ipo':
            continue
        tg = SH.clip(re.sub(r'^\([^)]{1,6}\)\s*', '', a.get('target') or ''), 24)
        bn = SH.clip(a.get('benefit') or '', 28)
        if not tg or not bn or '확인 필요' in tg or '상이' in tg or '확인 필요' in bn:
            continue
        d = (datetime.date.fromisoformat(a['end']) - T).days
        if d > 30:
            continue
        ap.append(('주거 청약' if kk in ('apt', 'rent', 'lh') else '지원금', a['end'], d, a['title'], [('대상', tg), ('내용', bn)], f'/a/{a["id"]}/', a.get('url') or '', '', a['id']))
        if len(ap) >= limit - len(cs):
            break
    cards = sorted(cs + ap, key=lambda x: x[1])[:limit]
    li = ''
    for typ, end, d, title, rows, href, ext, vb, _id in cards:
        seen.add(href)
        dd = '오늘 마감' if d == 0 else f'D-{d}'
        urgent = ' u' if d <= 3 else ''
        dl = ''.join(f'<div><dt>{k}</dt><dd>{E(v)}</dd></div>' for k, v in rows) + f'<div><dt>마감</dt><dd>{_dstr(end)}</dd></div>'
        ex = f'<a class="b2" href="{E(ext)}" target="_blank" rel="noopener nofollow">원문 {_ic("ext", "sv s")}</a>' if ext else ''
        li += (f'<li class="op"><div class="op-t"><span class="kk">{E(typ)}</span><span class="dd{urgent}">{dd}</span></div><h3>{E(_short(title, 60))}</h3><dl>{dl}</dl>'
               f'<div class="op-b"><a class="b1" href="{E(href)}">상세 보기</a>{ex}{vb}</div></li>')
    if not li:
        return ''
    return (f'<section class="h2-sec" aria-labelledby="s-opp"><div class="h2-hd"><h2 id="s-opp">마감 임박 공모전·지원 기회</h2><a href="/today/">오늘 마감 {_ic("arrow", "sv s")}</a></div>'
            f'<ul class="op-g">{li}</ul><p class="h2-nt">마감 빠른 순입니다. 핵심 조건을 확인하지 못한 공고는 제외했고, 신청 전 공식 공고를 다시 확인해 주세요. <a href="/contest/">공모전 전체</a> · <a href="/apply/">지원금·청약 전체</a></p></section>')


def _sec_guides(seen):
    import os
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    try:
        kin = json.load(open(os.path.join(here, 'kin_guides.json'), encoding='utf-8'))['guides']
    except Exception:
        return ''
    li = ''; n = 0
    for g in kin[::-1]:
        u = f'/money/guide/{g["slug"]}/'
        if u in seen or not os.path.exists(os.path.join(root, 'money', 'guide', g['slug'], 'index.html')):
            continue
        seen.add(u); n += 1
        m = re.search(r'확인일\s*(\d{4}-\d{2}-\d{2})', g.get('basis') or '')
        dt = f'<time datetime="{m.group(1)}">{_dstr(m.group(1))} 업데이트</time>' if m else ''
        li += f'<li><p class="kk">{E(g.get("name") or "생활 가이드")}</p><h3><a href="{u}">{E(_short(_dt(g.get("h1") or g["title"]), 60))}</a></h3><p class="sm">{E(_first_sentences(g.get("lead") or g.get("desc") or "", 70))}</p><p class="mt">{dt}</p></li>'
        if n == 6:
            break
    if not li:
        return ''
    return f'<section class="h2-sec" aria-labelledby="s-gd"><div class="h2-hd"><h2 id="s-gd">생활 가이드</h2><a href="/money/guide/">가이드 전체 {_ic("arrow", "sv s")}</a></div><ul class="gd-l">{li}</ul></section>'


def _kw_chips(seen, n=10):
    """읽을 수 있는 주요 주제: 작성 완료된 키워드 글(단기→중기 순, 점수순)을 글자 칩으로."""
    import os
    here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
    try:
        items = json.load(open(os.path.join(here, 'keywords.json'), encoding='utf-8'))['items']
    except Exception:
        return ''
    today = datetime.date.today().isoformat(); tier = {'단기': 0, '중기': 1, '장기': 2}; ok = []
    for i in items:
        p = i.get('page') or ''
        if i.get('status') != '작성' or not p or i.get('tier') not in tier or (i.get('expires') and i['expires'] < today) or p in seen or len(i.get('query', '')) > 18 or not os.path.exists(os.path.join(root, p.strip('/'), 'index.html')):
            continue
        ok.append(i)
    ok.sort(key=lambda i: (tier[i['tier']], -(i.get('score') or 0)))
    return ''.join(f'<a href="{E(i["page"])}">{E(_short(i["query"], 20))}</a>' for i in ok[:n])


def _sec_topics(ctx, seen):
    tp = [('이슈', '/issue/', 'issue', '요즘 화제를 출처와 함께'), ('지원금·청약', '/apply/', 'apply', '신청 기간·대상 정리'), ('공모전', '/contest/', 'contest', f'진행 중 {ctx["n_contest"]}건'),
          ('생활 가이드', '/money/guide/', 'guide', '세금·일·집·건강'), ('경품 이벤트', '/event/', 'event', '마감순 정리'), ('레시피', '/fridge/', 'recipe', '재료로 찾는 집밥'),
          ('계산기', '/money/tools/salary/', 'calc', '실수령액·퇴직금'), ('지표·RSI', '/analyst/rsi/', 'chart', '시세 현황표'), ('루리 위키', '/wiki/', 'wiki', '문서로 묶은 정보'), ('게임', '/game/', 'game', '출시·세일 일정')]
    cards = ''.join(f'<li><a href="{u}">{_ic(ic)}<span><b>{E(n)}</b><small>{E(s)}</small></span></a></li>' for n, u, ic, s in tp)
    ch = _kw_chips(seen)
    mp = f'<a class="mp" href="/map/">{_ic("map", "sv s")}키워드 지도에서 탐색</a>'
    kw = f'<div class="kw-row"><h3>키워드로 찾기</h3><div class="chips">{ch}</div>{mp}</div>' if ch else f'<div class="kw-row">{mp}</div>'
    return f'<section class="h2-sec" id="all" aria-labelledby="s-all"><div class="h2-hd"><h2 id="s-all">전체 주제 탐색</h2></div><ul class="tp-g">{cards}</ul>{kw}</section>'


def home_html(ctx):
    seen = set()
    cands = _read_candidates(ctx)
    top = ('<section class="h2-top" aria-labelledby="h2-t"><h1 id="h2-t">지금 궁금한 것, 루리에서 찾아보세요.</h1>'
           '<p class="lead">이슈부터 지원금·공모전까지, 출처와 함께 정리합니다. 자료는 AI로 수집·정리합니다. <a href="/about/#method">만드는 방식</a></p>'
           f'<form class="h2-s" role="search" action="/wiki/"><div class="row"><label class="sr" for="hs">검색 범위</label><select id="hs"><option value="">전체</option><option value="c">공모전</option><option value="a">지원금</option><option value="w">가이드</option><option value="r">레시피</option></select>'
           '<label class="sr" for="hq">검색어</label><input id="hq" type="search" placeholder="예: 청년 월세, 영상 공모전, 근로장려금" autocomplete="off" enterkeyhint="search"><button type="submit" class="go">검색</button></div>'
           '<div class="res" id="hr" aria-live="polite"></div></form></section>')
    return (top + _sec_read(cands, seen) + _opp_cards(ctx, seen) + _sec_guides(seen) + _sec_topics(ctx, seen)
            + '<link rel="stylesheet" href="/assets/home/home2.css?v=5"><script defer src="/assets/home/home2.js?v=2"></script>')


def kwmap_page_html():
    """/map/ 별도 탐색 화면(2026-11-03): 검색·분류 필터·확대/초기화 + 같은 내용의 목록."""
    h = _kwmap_sec(full=True)
    m = re.search(r'<script type="application/json" id="kwdata">(.*?)</script>', h or '', re.S)
    if not m:
        return ''
    raw = m.group(1)
    d = json.loads(raw.replace('<' + chr(92) + '/', '</'))
    TN = ['단기', '중기', '장기']
    lis = {0: '', 1: '', 2: ''}
    for i, n in enumerate(d['n']):
        lis[n['t']] += f'<li data-i="{i}"><a href="{E(n["u"])}">{E(n["q"])}</a><button type="button" aria-label="{E(n["q"])} 지도에서 보기">지도에서 보기</button></li>'
    cnt = {t: sum(1 for n in d['n'] if n['t'] == t) for t in range(3)}
    desc = ('단기 · 3~4일 안에 갑자기 많이 찾는 질문', '중기 · 약 2주 동안 이어지는 관심사', '장기 · 해마다 반복해 찾는 제도와 방법')
    lists = ''.join(f'<h3 class="kw-lh"><i class="dot t{t}"></i>{desc[t]} <small>{cnt[t]}건</small></h3><ul class="kw-l">{lis[t]}</ul>' for t in range(3) if lis[t])
    filt = ''.join(f'<button type="button" data-t="{t}" aria-pressed="true"><i class="dot t{t}"></i>{TN[t]} {cnt[t]}</button>' for t in range(3))
    return ('<div class="kw-pg"><div class="kw-bar"><form role="search" class="kw-s"><label class="sr" for="kw-q">키워드 검색</label>'
            '<input id="kw-q" type="search" placeholder="키워드 검색 (예: 월세, 연말정산)" autocomplete="off"></form>'
            f'<div class="kw-f" role="group" aria-label="기간 분류">{filt}</div>'
            '<div class="kw-z" role="group" aria-label="지도 조작"><button type="button" id="kw-in" aria-label="확대">＋</button><button type="button" id="kw-out" aria-label="축소">－</button><button type="button" id="kw-reset">초기화</button></div></div>'
            '<div class="kw-main"><div id="kwmap" class="kw-box"><canvas tabindex="0" role="img" aria-label="키워드 지도. 방향키로 돌리고 플러스·마이너스로 확대합니다. 같은 내용은 아래 목록에 있습니다."></canvas></div>'
            '<aside id="kw-info" class="kw-info" aria-live="polite"></aside></div>'
            '<p class="kw-hint"><b>보는 법</b> · 점 하나가 질문(글) 하나입니다. 안쪽 점이 단기, 바깥쪽 점이 장기입니다. 두 점을 잇는 선은 <b>제목에 같은 핵심 단어가 들어 있다</b>는 뜻이며, 의미가 비슷하다는 판단은 아닙니다. 끌어서 돌리고, 점을 누르면 연결된 질문이 강조됩니다.</p>'
            f'<h2 class="kw-h2">목록으로 보기</h2><p id="kw-empty" class="kw-empty" hidden>조건에 맞는 키워드가 없어요. 검색어를 줄이거나 분류를 다시 켜 보세요.</p>{lists}</div>'
            f'<script type="application/json" id="kwdata">{raw}</script><link rel="stylesheet" href="/assets/home/kwmap.css?v=1"><script defer src="/assets/home/kwmap.js?v=4"></script>')
