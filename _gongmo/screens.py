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
        (3, '작성', '공식 출처와 기준일을 단 분석 글'), (4, '노출·정리', '기간이 지난 글은 자동으로 내림')))
    return (f'<section class="cp"><p class="cp-k">LURI ANALYST</p><h2 class="cp-h">사람들이 궁금해하는 것,<br><em>근거와 숫자</em>로 분석합니다</h2>'
            f'<p class="cp-s">루리 애널리스트는 지금 사람들이 무엇을 궁금해하는지 신호로 찾아내고, 그 질문에 공식 출처 기준으로 답하는 분석 사이트입니다. 현재 <b>{tot}개</b>의 질문이 정리되어 있습니다.</p>'
            f'<div class="cp-g">{cards}</div><ol class="cp-f">{flow}</ol></section>')


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


def home_html(ctx):
    now = ctx['now']; items = due_items(ctx)
    new_c = [c for c in ctx['new_contests'] if ctx['elig_short'](c) not in ('미확인', '확인 필요') and (c.get('effort') or c.get('medium')) and (c['id'] in (ctx.get('VER') or {}) or ctx['prize_short'](c) != '확인 필요')]
    new_c = sorted(new_c, key=lambda c: 0 if c['id'] in (ctx.get('VER') or {}) else 1)[:5]
    # 오늘 마감 미리보기(공모전·지원금 우선 5개)
    order = {'공모전': 0, '지원금': 1, '주거 청약': 2, '공모주': 3, '이벤트': 4}
    _ver = ctx.get('VER') or {}
    prev = sorted([x for x in items if x['target'] != '확인 필요' and (x.get('cid') in _ver or x['type'] != '공모전' or x['benefit'] not in ('확인 필요',))], key=lambda x: (0 if x.get('cid') in _ver else 1, order.get(x['type'], 9), x['title']))[:5]   # 공식 원문 대조된 항목 먼저   # 대표 영역에는 핵심 조건이 확인된 항목만
    prev_h = ''.join(_card(i) for i in prev) or '<li class="td-empty">오늘 마감하는 항목이 없어요.</li>'
    new_h = ''.join(f'<li><a href="/c/{c["id"]}/"><b>{E(_short(c["title"], 46))}</b><span>{E(ctx["elig_short"](c))} · {E(ctx["prize_short"](c))} · {E(c["end"][5:].replace("-", "."))} 마감</span></a></li>' for c in new_c) or '<li class="td-empty">오늘 새로 확인한 공모전은 아직 없어요.</li>'
    guides = ''.join(f'<a href="{E(g["u"])}"><b>{E(_short(g["title"], 38))}</b><span>{E(_short(g["desc"], 60))}</span></a>' for g in ctx['guides'][:3])
    main = [('📰', '오늘의 이슈', '단기 이슈 · 매일 갱신', '/hot/'), ('💰', '돈·생활 가이드', '지원금·세금·일자리·집', '/money/guide/'), ('📈', '지표·시세', 'RSI 현황표', '/analyst/rsi/'), ('🍳', '레시피', '오늘 뭐 먹지 · 재료로 찾기', '/fridge/'), ('🏆', '공모전·이벤트', f'{ctx["n_contest"]}건 진행 중', '/contest/'), ('🧮', '계산기', '연봉 실수령액 · 퇴직금', '/money/tools/salary/')]
    mh = ''.join(f'<a class="hm-a" href="{u}"><i>{ic}</i><b>{E(t)}</b><span>{E(s)}</span></a>' for ic, t, s, u in main)
    sub = ''.join(f'<a href="{u}">{ic} {E(t)}</a>' for ic, t, u in (('⏰', '오늘 마감', '/today/'), ('📋', '지원금·청약', '/apply/'), ('🎁', '경품 이벤트', '/event/'), ('📚', '루리 위키', '/wiki/'), ('📺', '뉴스', '/news/')))
    allsv = ''.join(f'<a href="{E(t["path"])}"><i>{t["icon"]}</i>{E(t["name"])}</a>' for t in ctx['topics'])
    feats = ''.join(f'<li><b>{E(a)}</b><span>{E(b)}</span></li>' for a, b in (('루리 위키', '정보성 글을 문서처럼 묶어 검색·이전/다음으로 읽어요 (10/23)'), ('재료 → 최저가', '레시피에서 없는 재료를 쇼핑몰 가격순 검색으로 바로 연결해요 (10/23)'), ('공식 원문 대조', '확인한 공모전은 확인일과 달랐던 점을 함께 보여 줘요 (10/23)')))
    _shown = {x.get('cid') for x in prev if x.get('cid')}   # 위 「오늘 마감」에 이미 나온 공고는 다시 보여 주지 않는다
    _vi = [i for i in ver_items(ctx, 12) if i['cid'] not in _shown][:4]
    ver_h = ''.join(_card(i) for i in _vi)
    ver_sec = (f'<section class="hm-sec"><div class="hm-h"><h2>공식 원문까지 확인한 공모전</h2><a href="/contest/">공모전 찾기 →</a></div>'
               f'<p class="note">주최 측 공고와 첨부 서류를 직접 열어 자격·제출 규격·접수 방법을 대조한 공모전이에요(확인일은 각 상세에).</p><ul class="td-l hm-td">{ver_h}</ul></section>') if _vi else ''
    return (_concept_sec() + f'<section class="hm-hero"><h1>궁금한 것을 바로 찾아보세요.</h1>'
            '<p>이슈, 제도, 공모전, 지원금을 한 번에 검색합니다. 공식 공고와 대조한 곳에는 표시를 달고, 확인하지 못한 값은 「확인 필요」로 남깁니다.</p>'
            '<form class="hm-s" role="search" action="/wiki/" onsubmit="return false"><input id="hq" type="search" placeholder="예: 청년 월세, 영상 공모전, 김치볶음밥, 근로장려금" aria-label="통합 검색" autocomplete="off">'
            '<div class="hm-sc" role="group" aria-label="검색 범위"><button type="button" class="on" data-s="">전체</button><button type="button" data-s="c">공모전</button><button type="button" data-s="a">지원금</button><button type="button" data-s="e">이벤트</button><button type="button" data-s="r">레시피</button><button type="button" data-s="w">가이드</button></div>'
            '<div class="hm-r" id="hr" aria-live="polite"></div></form></section>'
            f'<nav class="hm-act" aria-label="주요 바로가기">{mh}</nav><nav class="hm-sub" aria-label="더 보기">{sub}</nav>'
            + _today_hot_sec() + _kwmap_sec() + _tier_sec() + _indicator_sec() + _field_sections()
            + (f'<section class="hm-sec"><div class="hm-h"><h2>추천 가이드</h2><a href="/wiki/">루리 위키 →</a></div><div class="hm-g">{guides}</div></section>' if guides else '')
            + f'<section class="hm-ai" aria-label="AI 수집 현황"><b>🤖 AI 수집기</b><span>마지막 수집 <b>{now:%H:%M}</b></span><span>오늘 새로 확인 <b>{ctx["n_new"]}건</b></span><span>수집 완료 <b>{ctx["n_live"]}건</b></span><span>공식 원문 확보 <b>{ctx["n_ver"]}건</b></span><span>핵심 조건 대조 <b>{ctx["n_core"]}건</b> <small>(AI 대조)</small></span><span>운영자 직접 검토 <b>{ctx["n_op"]}건</b></span><span>확인 못한 값은 「확인 필요」</span><a href="/corrections/">정정 기록</a> · <a href="/about/">제작 원칙</a></section>'
            + f'<section class="hm-sec"><div class="hm-h"><h2>오늘 마감</h2><a href="/today/">전체 {len(items)}건 →</a></div><ul class="td-l hm-td">{prev_h}</ul></section>'
            + ver_sec +
            f'<section class="hm-sec"><div class="hm-h"><h2>새로 확인한 공모전</h2><a href="/contest/">공모전 찾기 →</a></div><ul class="hm-nl">{new_h}</ul></section>'
            + f'<section class="hm-sec"><div class="hm-h"><h2>새로 생긴 기능</h2></div><ul class="hm-f">{feats}</ul></section>'
            + (f'<section class="hm-sec"><div class="hm-h"><h2>더 읽을거리</h2></div><ul class="hm-nl">' + ''.join(f'<li><a href="{E(r["u"])}"><b>{E(_short(r["title"], 60))}</b><span>{E(r["sub"])}</span></a></li>' for r in ctx.get('reads', [])) + '</ul></section>' if ctx.get('reads') else '')
            + f'<section class="hm-sec" id="all"><div class="hm-h"><h2>전체 서비스</h2></div><nav class="hm-all" aria-label="전체 서비스">{allsv}</nav></section>'
            '<p class="hm-about">루리 애널리스트은 요즘 사람들이 궁금해하는 이슈와 생활 속 돈 정보를 공식 출처 기준으로 분석해 정리하는 온라인 미디어입니다. 확인일과 출처를 적고, 확인하지 못한 내용은 표시해 둡니다. 편집 원칙은 <a href="/about/">소개</a>에 있습니다.</p>'
            '<link rel="stylesheet" href="/assets/home/screens.css?v=5"><script defer src="/assets/home/screens.js?v=1"></script>')
