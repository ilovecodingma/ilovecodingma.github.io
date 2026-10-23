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
                    'time': tm.group(1) if tm else '', 'href': f'/c/{c["id"]}/', 'ext': c.get('link') or '', 'org': c.get('org') or '', 'cid': c['id']})
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
    tm = f'오늘 <b>{E(it["time"])}</b>' if it['time'] else '오늘 · <span class="nu">시각 확인 필요</span>'
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
        btns += f'<a class="b2" href="{E(it["ext"])}" target="_blank" rel="noopener nofollow">{E(CQ.link_label(it["ext"]))} ↗</a>' if it['type'] != '이벤트' else f'<a class="b1" href="{E(it["ext"])}" target="_blank" rel="noopener nofollow">이벤트 보기 ↗</a>'
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
            '<link rel="stylesheet" href="/assets/home/screens.css?v=1"><script defer src="/assets/home/screens.js?v=1"></script>')


def home_html(ctx):
    now = ctx['now']; items = due_items(ctx)
    new_c = [c for c in ctx['new_contests'] if ctx['elig_short'](c) not in ('미확인', '확인 필요') and (c.get('effort') or c.get('medium'))]
    new_c = sorted(new_c, key=lambda c: 0 if c['id'] in (ctx.get('VER') or {}) else 1)[:5]
    # 오늘 마감 미리보기(공모전·지원금 우선 5개)
    order = {'공모전': 0, '지원금': 1, '주거 청약': 2, '공모주': 3, '이벤트': 4}
    _ver = ctx.get('VER') or {}
    prev = sorted([x for x in items if x['target'] != '확인 필요'], key=lambda x: (0 if x.get('cid') in _ver else 1, order.get(x['type'], 9), x['title']))[:5]   # 공식 원문 대조된 항목 먼저   # 대표 영역에는 핵심 조건이 확인된 항목만
    prev_h = ''.join(_card(i) for i in prev) or '<li class="td-empty">오늘 마감하는 항목이 없어요.</li>'
    new_h = ''.join(f'<li><a href="/c/{c["id"]}/"><b>{E(_short(c["title"], 46))}</b><span>{E(ctx["elig_short"](c))} · {E(ctx["prize_short"](c))} · {E(c["end"][5:].replace("-", "."))} 마감</span></a></li>' for c in new_c) or '<li class="td-empty">오늘 새로 확인한 공모전은 아직 없어요.</li>'
    guides = ''.join(f'<a href="{E(g["u"])}"><b>{E(_short(g["title"], 38))}</b><span>{E(_short(g["desc"], 60))}</span></a>' for g in ctx['guides'][:3])
    main = [('⏰', '오늘 마감하는 기회', f'{len(items)}건', '/today/'), ('🏆', '공모전 찾기', f'{ctx["n_contest"]}건 진행 중', '/contest/'), ('📋', '지원금·청약 찾기', f'{ctx["n_apply"]}건', '/apply/'), ('🍳', '오늘 뭐 먹지', '재료로도 찾기', '/fridge/')]
    mh = ''.join(f'<a class="hm-a" href="{u}"><i>{ic}</i><b>{E(t)}</b><span>{E(s)}</span></a>' for ic, t, s, u in main)
    sub = ''.join(f'<a href="{u}">{ic} {E(t)}</a>' for ic, t, u in (('🎁', '경품 이벤트', '/event/'), ('📚', '루리 위키', '/wiki/'), ('💰', '생활 돈 가이드', '/money/guide/'), ('📺', '뉴스', '/news/')))
    allsv = ''.join(f'<a href="{E(t["path"])}"><i>{t["icon"]}</i>{E(t["name"])}</a>' for t in ctx['topics'])
    feats = ''.join(f'<li><b>{E(a)}</b><span>{E(b)}</span></li>' for a, b in (('루리 위키', '정보성 글을 문서처럼 묶어 검색·이전/다음으로 읽어요 (10/23)'), ('재료 → 최저가', '레시피에서 없는 재료를 쇼핑몰 가격순 검색으로 바로 연결해요 (10/23)'), ('공식 원문 대조', '확인한 공모전은 확인일과 달랐던 점을 함께 보여 줘요 (10/23)')))
    return (f'<section class="hm-hero"><h1>오늘 필요한 생활 정보,<br>조건에 맞게 골라보세요.</h1>'
            '<p>공모전·지원금·이벤트·레시피를 AI가 매시간 모아 정리하고, 확인하지 못한 값은 「미확인」으로 남겨요.</p>'
            '<form class="hm-s" role="search" action="/wiki/" onsubmit="return false"><input id="hq" type="search" placeholder="예: 청년 월세, 영상 공모전, 김치볶음밥, 근로장려금" aria-label="통합 검색" autocomplete="off">'
            '<div class="hm-sc" role="group" aria-label="검색 범위"><button type="button" class="on" data-s="">전체</button><button type="button" data-s="c">공모전</button><button type="button" data-s="a">지원금</button><button type="button" data-s="e">이벤트</button><button type="button" data-s="r">레시피</button><button type="button" data-s="w">가이드</button></div>'
            '<div class="hm-r" id="hr" aria-live="polite"></div></form></section>'
            f'<nav class="hm-act" aria-label="주요 바로가기">{mh}</nav><nav class="hm-sub" aria-label="더 보기">{sub}</nav>'
            f'<section class="hm-ai" aria-label="AI 수집 현황"><b>🤖 AI 수집기</b><span>마지막 수집 <b>{now:%H:%M}</b></span><span>오늘 새로 확인 <b>{ctx["n_new"]}건</b></span><span>진행 중 공모전 수집 <b>{ctx["n_live"]}건</b></span><span>공식 원문 확인 <b>{ctx["n_ver"]}건</b> <small>(핵심 조건까지 대조 {ctx["n_core"]}건 · 누적)</small></span><span>확인 못한 값은 「확인 필요」</span><a href="/about/">제작 원칙·로그</a></section>'
            f'<section class="hm-sec"><div class="hm-h"><h2>오늘 마감</h2><a href="/today/">전체 {len(items)}건 →</a></div><ul class="td-l hm-td">{prev_h}</ul></section>'
            f'<section class="hm-sec"><div class="hm-h"><h2>새로 확인한 공모전</h2><a href="/contest/">공모전 찾기 →</a></div><ul class="hm-nl">{new_h}</ul></section>'
            + (f'<section class="hm-sec"><div class="hm-h"><h2>추천 가이드</h2><a href="/wiki/">루리 위키 →</a></div><div class="hm-g">{guides}</div></section>' if guides else '')
            + f'<section class="hm-sec"><div class="hm-h"><h2>새로 생긴 기능</h2></div><ul class="hm-f">{feats}</ul></section>'
            + (f'<section class="hm-sec"><div class="hm-h"><h2>더 읽을거리</h2></div><ul class="hm-nl">' + ''.join(f'<li><a href="{E(r["u"])}"><b>{E(_short(r["title"], 60))}</b><span>{E(r["sub"])}</span></a></li>' for r in ctx.get('reads', [])) + '</ul></section>' if ctx.get('reads') else '')
            + f'<section class="hm-sec" id="all"><div class="hm-h"><h2>전체 서비스</h2></div><nav class="hm-all" aria-label="전체 서비스">{allsv}</nav></section>'
            '<p class="hm-about">루리의 줍줍은 개인 개발자가 AI 수집기로 공개 공고를 모아 정리하는 생활 정보 사이트예요. 공식 출처와 확인일을 적고, 확인하지 못한 값은 비워 둡니다. 자세한 제작 원칙은 <a href="/about/">소개</a>와 <a href="/ailog/">제작 로그</a>에 있어요.</p>'
            '<link rel="stylesheet" href="/assets/home/screens.css?v=1"><script defer src="/assets/home/screens.js?v=1"></script>')
