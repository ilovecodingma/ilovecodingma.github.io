#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""루리의 줍줍(sungprofile.cloud) 정적 사이트 생성.
사용: python _gongmo/build.py [--push]
원본: 바탕화면 공모전_2026/주말큐_master.jsonl + _gongmo/txt/<id>.txt(공고 본문 캐시, 비공개)
"""
import json, os, re, sys, html, shutil, datetime, subprocess, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = r'C:\Users\k\Desktop\공모전_2026\data'  # 공모전 세션 정본 (2026-10-16 합의)
MASTER = os.path.join(DATA, 'master.jsonl')
if not os.path.exists(MASTER):
    MASTER = r'C:\Users\k\Desktop\공모전_2026\주말큐_master.jsonl'
SHOTS = os.path.join(DATA, 'shots')  # 공식 공고 캡처 <id>.webp 640x400
SITE = 'https://sungprofile.cloud'
NAME = '루리의 줍줍'
_CT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contact.json'), encoding='utf-8'))
MAIL, PARTNER = _CT['contact'], _CT['partner']
_CM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'community.json')
COMM_API = json.load(open(_CM, encoding='utf-8')).get('api', '') if os.path.exists(_CM) else ''  # 비어 있으면 게시판·로그인 숨김  # 에이전트채널 규약: 일반 문의 / 제휴·광고
TODAY = datetime.date.today()
KEEP_PAST = 0  # 마감 후 상세페이지 보존 일수 (2026-10-16 사용자: 마감된 건 내림)
TXT_SRC = [os.path.join(DATA, 'txt'),
           r'C:\Users\k\AppData\Local\Temp\claude\C--Users-k\4f3e089f-943b-4eb1-9e20-4a85afd47dac\scratchpad\collect\q\txt']
E = html.escape

CATS = [('literature', '문학'), ('idea', '아이디어·정책'), ('design', '디자인'), ('video', '영상'),
        ('paper', '논문'), ('it', 'IT·과학'), ('food', '요리·레시피'), ('global', '해외'), ('etc', '기타')]
SLUG = {n: s for s, n in CATS}
CAT_INTRO = {
 '요리·레시피': '레시피 공모전, 요리경연대회, 지역 특산물 요리대회처럼 음식으로 응모하는 공모전입니다. 레시피 서류 심사 후 본선에서 직접 조리하는 경우가 많아 재료비·조리 시간·인원 제한과 본선 날짜를 먼저 확인하세요. 지정 식재료(쌀, 과일, 계란 등)를 꼭 써야 하는 대회가 많습니다.',
 '문학': '시·소설·수필·수기·네이밍·슬로건처럼 글로 응모하는 공모전입니다. 분량과 형식(원고지 매수, 글자 수, 파일 형식)이 요강마다 달라 제출 전 반드시 확인해야 합니다. 수기 공모는 실제 경험을 구체적인 장면으로 쓰는 것이, 네이밍·슬로건은 주최 기관이 내세우려는 가치를 짧게 담는 것이 중요합니다.',
 '아이디어·정책': '지자체·공공기관·기업이 정책 제안, 사업 아이디어, 마케팅 기획을 받는 공모전입니다. 국민신문고·국민생각함 같은 공식 창구로 접수하는 경우가 많고, 현황·문제점·개선안·기대효과 순서의 제안서 형식이 일반적입니다. 실현 가능성과 예산 규모를 함께 적으면 심사에서 유리합니다.',
 '디자인': '캐릭터·포스터·일러스트·웹툰·건축·공예 등 시각 작품을 받는 공모전입니다. 해상도, 파일 형식(AI·PSD·PNG), 원본 파일 제출 여부, 저작권 귀속 조건을 꼭 확인하세요. 수상작의 저작권이 주최 측으로 넘어가는 경우가 많습니다.',
 '영상': '숏폼·UCC·사진·영화 공모전입니다. 영상 길이, 화면 비율(세로형 9:16 여부), 배경음악 저작권, 초상권 동의서 제출 여부가 자주 탈락 사유가 됩니다. 유튜브·인스타그램 업로드 후 링크를 제출하는 방식도 많습니다.',
 '논문': '학술 논문·리포트·연구 제안 공모입니다. 분량 기준, 인용 양식, 표절 검사(유사도) 기준과 공동 저자 허용 여부를 먼저 확인하세요. 학생부·일반부로 나뉘는 경우가 많습니다.',
 'IT·과학': '해커톤, SW 개발, AI 활용, 데이터 분석, 과학 탐구 공모전입니다. 팀 구성 인원, 개발 기간, 결과물 공개 여부(오픈소스), 사용 가능한 API·데이터 조건을 확인하세요.',
 '해외': '해외 기관이 주최하는 국제 공모전·해커톤입니다. 대부분 영어(일부 일본어)로 응모하며 국적 제한, 시차를 고려한 마감 시각(현지 시간 기준), 상금 송금 방식(해외 송금 수수료)을 확인해야 합니다.',
 '기타': '위 분야에 속하지 않는 다양한 공모전입니다. 요강의 응모 자격과 제출물을 꼼꼼히 읽어 보세요.',
}
TIPS = {
 '요리·레시피': ['지정 식재료(쌀·과일·계란 등)를 주재료로 썼는지 확인', '레시피는 재료 g·계량과 조리 순서를 사진과 함께', '본선 조리 시간·인원·재료 지참 여부 확인', '완성 사진은 밝은 자연광에서 위·45도 두 컷', '집에 있는 재료로 연습하려면 루리의 냉장고 파먹기 활용'],
 '문학': ['분량(글자 수·원고지 매수)과 파일 형식을 요강 그대로 맞추기', '주제어가 제목과 첫 문단에 드러나게 쓰기', '미발표 창작물 조건 확인(다른 공모전 중복 응모 금지가 흔함)'],
 '아이디어·정책': ['현황 → 문제점 → 개선안 → 기대효과 순서로 정리', '비슷한 기존 정책이 있는지 먼저 검색해 차별점 적기', '소요 예산과 실행 주체를 구체적으로 제시'],
 '디자인': ['요구 해상도·규격·파일 형식 확인', '원본 파일(AI·PSD) 제출 요구 여부 확인', '저작권 귀속·2차 활용 조건 읽기'],
 '영상': ['영상 길이와 화면 비율(가로·세로) 확인', '배경음악·폰트는 상업적 이용 가능한 것만 사용', '출연자 초상권 동의서 준비'],
 '논문': ['분량·인용 양식·유사도 기준 확인', '공동 저자 허용 여부와 소속 표기 방법 확인', '초록과 결론에 주최 측 주제 키워드 반영'],
 'IT·과학': ['팀 인원 제한과 개발 기간 확인', '사용 가능한 API·데이터·라이선스 확인', '시연 영상·README 등 제출물 형식 준비'],
 '해외': ['마감 시각의 기준 시간대(현지 시간) 확인', '국적·거주지 제한 여부 확인', '상금 수령 방식(해외 송금, 세금 서류) 확인'],
 '기타': ['응모 자격(나이·지역·학생 여부) 먼저 확인', '제출 방법(이메일·홈페이지·구글폼) 확인', '마감 당일 접속 폭주에 대비해 하루 전 제출'],
}
CH = {'mail': '이메일 접수', 'mail?': '이메일 접수(공고 확인)', 'web': '홈페이지 접수', 'gform': '구글폼 접수', 'nform': '네이버폼 접수',
      'ig': '인스타그램 참여', 'yt': '유튜브 참여'}
EV_KIND = {'event': '이벤트', 'sweepstakes': '추첨 경품', 'quiz': '퀴즈', 'survey': '설문', 'sns_comment': '댓글 이벤트',
           'sns_tag_required': '친구 태그', 'sns_story_required': '스토리 공유', 'sns_capture': '캡처 인증', 'sns_form_only': '폼 응모',
           'sns_comment+form': '댓글+폼', 'sns_purchase': '구매 인증', 'sns_region': '지역 한정', 'sns_other': 'SNS 이벤트'}

COMM_TAGS_TPL = '<link rel="stylesheet" href="/assets/community/comm.css?v=14"><script defer src="/assets/community/comm.js?v=21"></script><script defer src="/assets/community/crew.js?v=1"></script>'
GTAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4248498719773262" crossorigin="anonymous"></script>\n'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());if(location.hostname!=='sungprofile.cloud')window['ga-disable-G-G9BPFF95GY']=true;gtag('config','G-G9BPFF95GY');</script>")
THEMES = [  # (키, 이름, 아이콘, 테마색, 홈, [하위 메뉴], [이 테마에 속하는 주소 앞부분])
    ('issue', '이슈', '🕵️', '#b45309', '/news/', [('/news/', '이슈 감별'), ('/talk/', '커뮤니티 이슈'), ('/kw/', '인기 키워드'), ('/satire/', '루리 풍자'), ('/mag/', '매거진')],
     ['/news/', '/talk/', '/kw/', '/satire/', '/mag/']),
    ('money', '머니', '📊', '#047857', '/analyst/', [('/analyst/', '애널리스트 종합'), ('/money/experts/', '전문가 코멘트'), ('/money/policy/', '투자 정책'), ('/money/age/', '나이별 원칙'), ('/analyst/coin/btc/', '코인')], ['/analyst/', '/money/']),
    ('contest', '공모전', '🏆', '#6d28d9', '/contest/', [('/contest/', '추천 상담'), ('/cat/literature/', '분야별'), ('/prep/', '준비실'), ('/lab/', '수상 연구소'), ('/community/', '원정대'), ('/guide/', '가이드')],
     ['/contest/', '/c/', '/cat/', '/prep/', '/lab/', '/community/', '/guide/', '/v/', '/me/']),
    ('life', '생활', '🍳', '#0e7490', '/apply/', [('/apply/', '지원금·청약'), ('/apply/recommend/', '청약 추천'), ('/event/', '경품'), ('/fridge/', '냉장고 파먹기'), ('/qa/', '고민 해결')], ['/apply/', '/a/', '/event/', '/fridge/', '/qa/', '/ssul/']),
    ('ai', 'AI 로그', '🤖', '#0f172a', '/ailog/', [('/ailog/', 'AI 제작 로그')], ['/ailog/'])]


def theme_of(path):
    if path == '/':
        return None
    for th in THEMES:
        if any(path.startswith(px) for px in th[6]):
            return th
    return None


TABS = [('/news/', '🕵️ 이슈'), ('/analyst/', '📊 애널리스트'), ('/', '🏆 공모전'), ('/mag/', '📰 매거진'), ('/all/', '☰ 전체')]   # 2026-10-18 난잡함 정리: 5개만, 나머지는 /all/
NAV = [('apply', '청약·신청'), ('ssul', '썰'), ('event', '경품·용돈'), ('cat/literature', '문학'), ('cat/idea', '아이디어'), ('cat/design', '디자인'),
       ('cat/video', '영상'), ('cat/it', 'IT'), ('cat/global', '해외'), ('guide', '가이드')]


def page(path, title, desc, body, crumbs=None, ld=None, full_title=False):
    url = SITE + path
    TH = theme_of(path)
    COMM_TAGS = COMM_TAGS_TPL if COMM_API else ''
    t = title if full_title else f'{title} | {NAME}'
    lds = []
    if crumbs:
        lds.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]})
    if ld:
        lds.append(ld)
    ldh = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False).replace('</', '<\\/') for x in lds)
    nav = ''.join(f'<a href="/{s}/">{n}</a>' for s, n in NAV + ([('community', '원정대')] if COMM_API else []))
    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(t)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{E(t)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/ruri/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/assets/ruri/og.jpg">
<meta name="theme-color" content="{TH[3] if TH else '#5b21b6'}">
<link rel="icon" href="/favicon.ico?v=5" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png?v=5"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png?v=5"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://cdn.jsdelivr.net"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/gm.css?v=6">{('<link rel="stylesheet" href="/assets/chat/ruri-chat.css?v=7">') if not (TH and TH[0] == 'ai') else ''}{COMM_TAGS}{('<script type="module" src="/assets/chat/ruri-chat.js?v=11"></script>') if not (TH and TH[0] == 'ai') else ''}<script defer src="/assets/app/app.js?v=1"></script>
{ldh}
{GTAG}
</head><body data-th="{TH[0] if TH else 'hub'}"{(' data-api="' + COMM_API + '"') if COMM_API else ''}>
<header class="hd"><div class="w hd-in"><a class="logo" href="/"><img src="/assets/icons/logo.svg" width="30" height="30" alt=""><span>루리의 <b>줍줍</b></span></a>{('<span class="th-name">' + TH[2] + ' ' + TH[1] + '</span>') if TH else ''}</div>
<nav class="th-sw w" aria-label="테마">{"".join(f'<a href="{t[4]}" style="--tc:{t[3]}"{" class=on" if TH and TH[0] == t[0] else ""}>{t[2]} {t[1]}</a>' for t in THEMES)}</nav>
{('<nav class="tb w" aria-label="' + TH[1] + ' 메뉴">' + "".join(f'<a href="{u}"{" class=on" if (path == u or (u != TH[4] and path.startswith(u))) else ""}>{n}</a>' for u, n in TH[5]) + '</nav>') if TH else ''}</header>
<main class="w">
{body}
</main>
<footer class="ft"><div class="w ft-in"><div class="ft-b"><img class="av" src="/assets/ruri/avatar.webp" width="56" height="56" alt="루리" loading="lazy"><div><b>루리의 줍줍</b><p>마감 놓치지 마세요! 매일 아침 새 공모전을 정리해 둘게요.</p><p class="ft-m">문의 <a href="mailto:{MAIL}">{MAIL}</a>{"" if PARTNER == MAIL else f' · 제휴 <a href="mailto:{PARTNER}">{PARTNER}</a>'}</p></div></div>
<p class="ft-l"><a href="/about/">소개</a><a href="/ailog/">🤖 AI 제작 로그</a><a href="/news/">🕵️ 이슈 감별</a><a href="/app/">📲 앱·알림</a><a href="/prep/">준비실</a><a href="/qa/">고민 해결</a><a href="/guide/">응모 가이드</a><a href="/event/">경품 이벤트</a><a href="/privacy/">개인정보처리방침</a><a href="/terms/">이용약관</a><a href="/contact/">문의</a></p>
<p class="ft-n">공모전 정보는 각 주최 기관의 공고를 바탕으로 정리했으며, 정확한 요강은 반드시 공식 공고에서 확인하세요. © 2026 루리의 줍줍 · sungprofile.cloud</p></div></footer>
</body></html>'''
    d = os.path.join(ROOT, path.strip('/'))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(doc)


CAT_OUTFIT = {'요리·레시피': 'o_cook', '문학': 'o_cardigan', '아이디어·정책': 'o_present', '디자인': 'o_gray', '영상': 'o_anchor', '논문': 'o_vest', 'IT·과학': 'o_desk', '해외': 'o_trench', '기타': 'o_suit'}
CAT_ICON = {'요리·레시피': '🍳', '문학': '✍️', '아이디어·정책': '💡', '디자인': '🎨', '영상': '🎬', '논문': '📚', 'IT·과학': '💻', '해외': '🌏', '기타': '🧩'}


def say(expr, html_, cls=''):
    return (f'<div class="say {cls}"><img src="/assets/ruri/{expr}_s.webp" width="56" height="77" alt="루리" loading="lazy">'
            f'<div class="bub"><b>루리</b><div>{html_}</div></div></div>')


def dday(end):
    n = (datetime.date.fromisoformat(end) - TODAY).days
    return n, ('마감' if n < 0 else 'D-DAY' if n == 0 else f'D-{n}')


def ddot(s):
    return s.replace('-', '.') if s else ''


def sync_txt():
    """공모전 세션이 새로 받은 공고 본문을 _gongmo/txt 로 복사(없는 것·갱신된 것만)"""
    dst = os.path.join(HERE, 'txt')
    os.makedirs(dst, exist_ok=True)
    n = 0
    for src in TXT_SRC:
        if not os.path.isdir(src):
            continue
        for f in os.listdir(src):
            a, b = os.path.join(src, f), os.path.join(dst, f)
            if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
                shutil.copy2(a, b)
                n += 1
    return n


def sync_shots(live):
    """진행 중 공모전 캡처만 assets/shots 에 두고, 마감된 건 지움"""
    dst = os.path.join(ROOT, 'assets', 'shots')
    os.makedirs(dst, exist_ok=True)
    keep = {c['id'] + '.webp' for c in live if c.get('th')}
    for f in keep:
        a, b = os.path.join(SHOTS, f), os.path.join(dst, f)
        if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
            shutil.copy2(a, b)
    gone = [f for f in os.listdir(dst) if f not in keep]
    for f in gone:
        os.remove(os.path.join(dst, f))
    print('shots', len(keep), 'removed', len(gone))


def load():
    print('txt synced', sync_txt())
    rows = [json.loads(l) for l in open(MASTER, encoding='utf-8') if l.strip()]
    # 공모전 판정·추출은 parse.py 로직 그대로, 마감 후 KEEP_PAST 일까지 포함
    P.Q = HERE
    P.MASTER = MASTER
    P.TODAY = TODAY - datetime.timedelta(days=KEEP_PAST)
    tmp = os.path.join(HERE, '_c.json')
    P.OUT = tmp
    argv, sys.argv = sys.argv, ['x', '--no-push']
    P.main()
    sys.argv = argv
    contests = json.load(open(tmp, encoding='utf-8'))['items']
    os.remove(tmp)
    byid = {r['id']: r for r in rows}
    for c in contests:
        r = byid.get(c['id'], {})
        c['ch'] = CH.get(r.get('ch', ''), '공고 참조')
        c['th'] = 1 if os.path.exists(os.path.join(SHOTS, c['id'] + '.webp')) else 0
        # 공모전 세션 수집 필드(있으면 우선): quick, effort, region, fee
        c['quick'] = r.get('quick')
        c['effort'] = P.clean(r.get('effort', ''))[:12]
        c['region'] = P.clean(r.get('region', '') if isinstance(r.get('region'), str) else '')[:10]
        c['fee'] = r.get('fee') or 0
        c['submit'] = P.clean(r.get('submit', ''))[:10]
        if r.get('prize_first') and not c['pv']:
            c['pv'] = int(r['prize_first']); c['prize'] = f"1등 {int(r['prize_first']) // 10000:,}만원"
    seen, events = set(), []
    cids = {c['id'] for c in contests}
    for r in rows:
        k = r.get('kind', '')
        if k not in EV_KIND or r.get('end', '') < TODAY.isoformat() or r['id'] in cids:
            continue
        t = P.clean(r.get('title', ''))[:90]
        if not t or t == 'N/A':
            continue
        key = P.norm_title(t) + r.get('end', '')
        if key in seen:
            continue
        seen.add(key)
        events.append({'id': r['id'], 'title': t, 'org': P.clean(r.get('org', ''))[:40], 'end': r['end'],
                       'type': EV_KIND[k], 'ch': CH.get(r.get('ch', ''), ''), 'link': r.get('apply') or r['url'], 'effort': P.clean(r.get('effort', ''))[:12]})
    events.sort(key=lambda e: (e['end'], e['title']))
    return contests, events


def score(c):
    """추천순: 상금(로그) + 적당히 남은 기간(2~14일 최고) − 오늘 마감"""
    n = dday(c['end'])[0]
    import math
    s = (math.log10(c['pv']) - 4) * 1.2 if c['pv'] else 0
    s += 2 if 2 <= n <= 14 else 1 if n <= 30 else 0
    s -= 3 if n <= 0 else 0
    s += 1 if c.get('effort') or c.get('quick') else 0
    return s


def card(c):
    n, dd = dday(c['end'])
    cls = 'd off' if n < 0 else 'd u3' if n <= 3 else 'd hot' if n <= 7 else 'd'
    tg = ''.join(f'<span class="tg">{E(t)}</span>' for t in c['tags'])
    pz = (f'<span class="ez e0">{E(c["effort"])}</span>' if c.get('effort') else '') + (f'<span class="pz">🏆 {E(c["prize"])}</span>' if c['pv'] else '')
    th = f'<img class="th" src="/assets/shots/{c["id"]}.webp" width="640" height="400" alt="" loading="lazy">' if c.get('th') else ''
    return (f'<li><a class="card{" has-th" if th else ""}" data-c="{SLUG[c["tags"][0]]}" href="/c/{c["id"]}/">{th}<span class="ic">{CAT_ICON[c["tags"][0]]}</span><div class="cb"><div class="top"><h3 class="t">{E(c["title"])}</h3><span class="{cls}">{dd}</span></div>'
            f'<p class="o">{E(c["org"])}</p><p class="pd">접수 {(ddot(c["start"])[5:] + " ~ ") if c.get("start") else "~ "}{ddot(c["end"])[5:]}</p><div class="tags">{pz}{tg}</div></div></a></li>')


def detail(c, live):
    n, dd = dday(c['end'])
    main_tag = c['tags'][0]
    tips = ''.join(f'<li>{E(t)}</li>' for tag in c['tags'][:2] for t in TIPS[tag])
    sim = [x for x in live if x['id'] != c['id'] and main_tag in x['tags']][:6]
    simh = ''.join(card(x) for x in sim)
    status = ('<p class="warn">접수가 마감된 공모전입니다. 같은 분야의 진행 중 공모전을 아래에서 확인하세요.</p>' if n < 0
              else f'<p class="lead"><span class="{"d u3" if n <= 3 else "d hot" if n <= 7 else "d"}">{dd}</span> {ddot(c["end"])} 마감</p>')
    ruri = (say('sad', '아쉽지만 이건 마감됐어요. 아래 진행 중인 공모전을 봐 주세요!') if n < 0 else
            say('surprise', f'마감까지 <b>{dd}</b>! 오늘 바로 요강부터 확인해요.') if n <= 3 else
            say('thumbsup', f'상금 <b>{E(c["prize"])}</b>! 응모 자격만 맞으면 도전해 볼 만해요.') if c['pv'] else
            say('smile', '공식 공고에서 제출 양식과 파일 형식을 먼저 확인해 주세요!'))
    period = (ddot(c['start']) + ' ~ ' if c['start'] else '~ ') + ddot(c['end'])
    rows = [('주최·주관', c['org']), ('분야', c['field'] or ', '.join(c['tags'])), ('접수 기간', period), ('상금', c['prize']),
            ('응모 자격', c['elig']), ('접수 방법', c['ch'])]
    tb = ''.join(f'<tr><th>{k}</th><td>{E(v)}</td></tr>' for k, v in rows)
    catl = ' · '.join(f'<a href="/cat/{SLUG[t]}/">{E(t)}</a>' for t in c['tags'])
    org = c['org'] if c['org'] != '공고 참조' else '주최 기관'
    summary = (f'「{c["title"]}」은 {org}에서 진행하는 {", ".join(c["tags"])} 분야 공모전으로 {ddot(c["end"])}까지 접수합니다. '
               f'응모 자격은 "{c["elig"]}"이고 상금은 {c["prize"]}입니다. '
               f'접수 방법은 {c["ch"]}이므로 공식 공고에서 제출 양식과 파일 형식을 먼저 확인하세요.')
    body = f'''<p class="bc"><a href="/">홈</a> › <a href="/cat/{SLUG[main_tag]}/">{E(main_tag)}</a></p>
<section class="dh" data-c="{SLUG[main_tag]}"><span class="ic big">{CAT_ICON[main_tag]}</span><h1>{E(c["title"])}</h1>{status}</section>
{ruri}
<a class="shot" href="{E(c["link"])}" target="_blank" rel="noopener nofollow">{f'<img src="/assets/shots/{c["id"]}.webp" width="640" height="400" alt="{E(c["title"])} 공식 공고 화면">' if c.get('th') else f'<img class="ruri" src="/assets/ruri/thumbsup.webp" width="300" height="415" alt="루리">'}<span>공식 공고 페이지 열기 →</span></a>
<div class="panel"><table class="info">{tb}</table>
<a class="btn" href="{E(c["link"])}" target="_blank" rel="noopener nofollow">공식 공고 보러 가기 →</a></div>
<div class="my-acts" data-id="c:{c["id"]}" data-title="{E(c["title"])}" data-end="{c["end"]}"></div>
<h2>한눈에 보기</h2><p>{E(summary)}</p>
<h2>응모 전 체크리스트</h2><ul class="chk">{tips}</ul>
{'<a class="lab-cta" href="/lab/#diag"><b>🏆 이런 공모전 수상작은 어떻게 생겼을까?</b><span>수상작 300여 개를 분석한 당선 공식과 내 문구 진단 →</span></a>' if re.search(r'슬로건|표어|네이밍|명칭|캐치프레이즈|삼행시|N행시|이행시|애칭', c['title']) else ''}
<p class="note">분야: {catl}. 상금·자격·기간은 공고 원문에서 자동으로 정리한 값이라 오차가 있을 수 있습니다. 최종 기준은 주최 측 공식 공고입니다.</p>
{f'<section id="cm-crew" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section><section id="cm-teams" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section><section id="cm-board" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section>' if COMM_API else ''}
<h2>같은 분야 진행 중 공모전</h2><ul class="list">{simh or '<li class="empty">진행 중인 같은 분야 공모전이 없어요.</li>'}</ul>'''
    ld = {'@context': 'https://schema.org', '@type': 'Event', 'name': c['title'], 'eventStatus': 'https://schema.org/EventScheduled',
          'eventAttendanceMode': 'https://schema.org/OnlineEventAttendanceMode', 'startDate': c['start'] or c['end'], 'endDate': c['end'],
          'location': {'@type': 'VirtualLocation', 'url': c['link']}, 'organizer': {'@type': 'Organization', 'name': c['org']},
          'description': summary}
    desc = f'{c["title"]} — {org} 주최, {ddot(c["end"])} 마감, 상금 {c["prize"]}. 응모 자격·접수 방법·체크리스트 정리.'
    page(f'/c/{c["id"]}/', c['title'], desc[:155], body,
         [('루리의 줍줍', '/'), (main_tag, f'/cat/{SLUG[main_tag]}/'), (c['title'], f'/c/{c["id"]}/')], ld)


def listing_js(cat=''):
    return '''<script>
(function(){var IC=%s,SL=%s;var $=function(i){return document.getElementById(i)};var items=[],cat=%s,PAGE=40,shown=PAGE;
var n=new Date(),LATE=n.getHours()>=18,T=Math.round(Date.UTC(n.getFullYear(),n.getMonth(),n.getDate())/864e5);
function dn(s){var p=s.split('-');return Math.round(Date.UTC(+p[0],p[1]-1,+p[2])/864e5)}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function render(){var q=$('q').value.trim().toLowerCase(),due=+$('due').value||0,s=$('sort').value;
function sc(i){var s=i.pv?(Math.log(i.pv)/Math.LN10-4)*1.2:0;s+=(i.left>=2&&i.left<=14)?2:i.left<=30?1:0;if(i.left<=0)s-=3;if(i.effort)s+=1;return s}
var r=items.filter(function(i){return i.left>=(LATE?1:0)&&(!cat||i.tags.indexOf(cat)>=0)&&(!due||i.left<=due)&&(!q||i.hay.indexOf(q)>=0)});
r.sort(s==='prize'?function(a,b){return b.pv-a.pv||a.left-b.left}:s==='end'?function(a,b){return a.left-b.left||b.pv-a.pv}:function(a,b){return sc(b)-sc(a)||a.left-b.left});
$('cnt').textContent='진행 중 공모전 '+r.length+'건';var ul=$('list');ul.textContent='';
if(!r.length){var li=el('li','empty');li.innerHTML='<img src="/assets/ruri/sad_s.webp" width="56" height="77" alt=""><p>조건에 맞는 공모전이 없어요. 검색어를 바꿔 볼까요?</p>';ul.appendChild(li)}
r.slice(0,shown).forEach(function(i){var li=el('li'),a=el('a','card');a.href='/c/'+i.id+'/';a.dataset.c=SL[i.tags[0]]||'etc';if(i.th){a.className+=' has-th';var im=el('img','th');im.src='/assets/shots/'+i.id+'.webp';im.loading='lazy';im.alt='';a.appendChild(im)}a.appendChild(el('span','ic',IC[i.tags[0]]||'🧩'));var cb=el('div','cb'),top=el('div','top');top.appendChild(el('h3','t',i.title));
top.appendChild(el('span','d'+(i.left<=3?' u3':i.left<=7?' hot':''),i.left?'D-'+i.left:'D-DAY'));cb.appendChild(top);cb.appendChild(el('p','o',i.org));cb.appendChild(el('p','pd','접수 '+(i.start?i.start.slice(5).replace('-','.')+' ~ ':'~ ')+i.end.slice(5).replace('-','.')));
var tg=el('div','tags');if(i.effort)tg.appendChild(el('span','ez e0',i.effort));if(i.pv)tg.appendChild(el('span','pz','🏆 '+i.prize));i.tags.forEach(function(x){tg.appendChild(el('span','tg',x))});cb.appendChild(tg);a.appendChild(cb);li.appendChild(a);ul.appendChild(li)});
$('more').hidden=r.length<=shown}
['q','due','sort'].forEach(function(i){$(i).addEventListener('input',function(){shown=PAGE;render()})});$('more').onclick=function(){shown+=PAGE;render()};
fetch('/data.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(d){items=d.items.map(function(i){i.left=dn(i.end)-T;i.hay=(i.title+' '+i.org+' '+i.field+' '+i.tags.join(' ')).toLowerCase();return i});render()});
})();</script>''' % (json.dumps(CAT_ICON, ensure_ascii=False), json.dumps(SLUG, ensure_ascii=False), json.dumps(cat, ensure_ascii=False))


TOOLBAR = '''<div class="bar"><input type="search" id="q" placeholder="공모전, 주최, 키워드 검색" aria-label="검색">
<select id="due" aria-label="마감"><option value="">마감 전체</option><option value="7">7일 이내</option><option value="30">30일 이내</option></select>
<select id="sort" aria-label="정렬"><option value="rec">추천순</option><option value="end">마감 임박순</option><option value="prize">상금 큰 순</option></select></div>
<p class="cnt" id="cnt"></p>'''


# 참여 난이도 배지 (공모전 세션 합의: "설문 5분", "댓글 1줄" 처럼 쉬운 정도를 앞에)
EASY = {'댓글 이벤트': '댓글 1줄', '설문': '설문 5분', '퀴즈': '퀴즈 풀기', '폼 응모': '폼 1분', '댓글+폼': '댓글+폼', '추첨 경품': '응모만',
        '친구 태그': '친구 태그', '스토리 공유': '스토리 공유', '캡처 인증': '캡처 인증', '구매 인증': '구매 필요', '지역 한정': '지역 한정',
        '이벤트': '참여형', 'SNS 이벤트': 'SNS 참여'}
EASY_RANK = {'댓글 1줄': 0, '폼 1분': 0, '응모만': 0, '설문 5분': 1, '퀴즈 풀기': 1, '댓글+폼': 1, '참여형': 2, 'SNS 참여': 2,
             '친구 태그': 2, '스토리 공유': 3, '캡처 인증': 3, '지역 한정': 4, '구매 필요': 5}


def ev_card(e):
    n, dd = dday(e['end'])
    ch = f'<span class="tg">{E(e["ch"])}</span>' if e['ch'] else ''
    ez = e.get('effort') or EASY.get(e['type'], e['type'])
    return (f'<li><a class="card" data-c="event" href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><span class="ic">🎁</span><div class="cb"><div class="top"><h3 class="t">{E(e["title"])}</h3>'
            f'<span class="d{" u3" if n <= 3 else ""}">{dd}</span></div><p class="o">{E(e["org"] or "공식 계정")} · ~{ddot(e["end"])}</p>'
            f'<div class="tags"><span class="ez e{EASY_RANK.get(ez, 2)}">{E(ez)}</span>{ch}</div></div></a></li>')


# ---- 청약·신청 (공모전 세션이 data/apply.jsonl 에 쌓음: title, org, kind, start, end, url, source, verified) ----
APPLY_KIND = {'apt': ('아파트 청약', '🏠'), 'rent': ('공공임대', '🏘️'), 'ipo': ('공모주', '📈'), 'grant': ('지원금 신청', '💰')}


def apply_kind(k):
    k = (k or '').lower()
    for key, v in APPLY_KIND.items():
        if key in k or v[0] in k:
            return v
    if any(w in k for w in ('청약', '분양')):
        return APPLY_KIND['apt']
    if any(w in k for w in ('임대', '행복주택', '매입')):
        return APPLY_KIND['rent']
    if '공모주' in k or '상장' in k:
        return APPLY_KIND['ipo']
    return ('신청', '📝')


def load_apply():
    fp = os.path.join(DATA, 'apply.jsonl')
    mp = os.path.join(HERE, 'manual_apply.jsonl')  # 사이트 쪽 확인분(정본은 공모전 세션 apply.jsonl)
    lines = (open(fp, encoding='utf-8').readlines() if os.path.exists(fp) else []) + (open(mp, encoding='utf-8').readlines() if os.path.exists(mp) else [])
    out, seen = [], set()
    for l in lines:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if not r.get('title') or not (r.get('end') or r.get('always')) or r.get('closed'):
            continue
        end = r.get('end_override') or r.get('end') or '2099-12-31'  # always: 상시 신청
        try:
            if dday(end)[0] < 0:
                continue
        except ValueError:
            continue
        aid = str(r['id']) if r.get('id') else 'A' + hashlib.md5((r['title'] + '|' + r.get('url', '')).encode('utf-8')).hexdigest()[:8]
        if aid in seen:
            continue
        seen.add(aid)
        nm, ic = apply_kind(r.get('kind'))
        out.append({'id': aid, 'title': P.clean(r['title'])[:90], 'org': P.clean(r.get('org', ''))[:40] or '공고 참조', 'kind': nm, 'icon': ic, 'kk': r.get('kind') or ('apt' if re.search(r'아파트|분양|자이|힐스테이트|푸르지오|래미안|e편한|롯데캐슬|하늘채|더샵|아이파크|위브|포레나|센트레빌|리슈빌|공공분양', r['title']) else 'rent' if re.search(r'임대|전세|월세|행복주택|매입', r['title']) else 'grant'),
                    'start': r.get('start', ''), 'end': end, 'url': r.get('url', ''), 'source': r.get('source', ''), 'verified': bool(r.get('verified')),
                    'always': bool(r.get('always')), 'region': P.clean(r.get('region', ''))[:20], 'target': P.clean(r.get('target', ''))[:80], 'benefit': P.clean(r.get('benefit', ''))[:80],
                    'how': P.clean(r.get('how', ''))[:60], 'income': P.clean(r.get('income', ''))[:30], 'age_min': r.get('age_min'), 'age_max': r.get('age_max')})
    out.sort(key=lambda a: (a['end'], a['title']))
    return out


def ap_card(a):
    n, dd = dday(a['end'])
    v = '<span class="tg">확인됨</span>' if a['verified'] else ''
    return (f'<li><a class="card" data-c="apply" href="/a/{a["id"]}/"><span class="ic">{a["icon"]}</span><div class="cb"><div class="top"><h3 class="t">{E(a["title"])}</h3>'
            f'<span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span></div><p class="o">{E(a["org"])} · ~{ddot(a["end"])}</p>'
            f'<div class="tags"><span class="ez e1">{E(a["kind"])}</span>{v}</div></div></a></li>')


APPLY_INTRO = '''<p>아파트 청약, 공공임대, 공모주 청약, 지원금 신청처럼 <b>기간 안에 신청만 하면 되는 기회</b>를 모았어요. 신청은 반드시 공식 사이트에서 하세요.</p>
<h2>어디서 신청하나요?</h2><ul class="chk"><li><b>아파트 청약</b>: 한국부동산원 청약홈(applyhome.co.kr). 청약통장 가입 기간·납입 횟수가 순위를 가릅니다.</li>
<li><b>공공임대</b>: LH청약플러스(apply.lh.or.kr), SH·GH 등 지역 공사. 소득·자산 기준을 먼저 확인하세요.</li>
<li><b>공모주</b>: 증권사 앱에서 청약. 증거금(신청금액의 50% 안팎)이 필요하고, 배정 후 남은 돈은 환불됩니다.</li>
<li><b>지원금</b>: 정부24·복지로·지자체 홈페이지. 대부분 본인인증 후 온라인으로 신청합니다.</li></ul>
<p class="note">정보는 공고를 바탕으로 정리했으며, 자격·일정은 바뀔 수 있으니 공식 공고를 기준으로 하세요. 투자·청약 결과에 대한 판단은 본인 책임입니다.</p>'''


def build_apply(aps):
    # 메인 루리 상담(청약·지원금)용 데이터 (2026-10-17)
    with open(os.path.join(ROOT, 'apply.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{k: a[k] for k in ('id', 'title', 'org', 'kind', 'icon', 'kk', 'start', 'end', 'always', 'region', 'target', 'benefit', 'how', 'income', 'age_min', 'age_max') if a.get(k) not in (None, '', False)} for a in aps], f, ensure_ascii=False, separators=(',', ':'))
    for a in aps:
        n, dd = dday(a['end'])
        period = (ddot(a['start']) + ' ~ ' if a['start'] else '~ ') + ddot(a['end'])
        tb = ''.join(f'<tr><th>{k}</th><td>{E(v)}</td></tr>' for k, v in
                     [x for x in [('구분', a['kind']), ('대상', a.get('target')), ('혜택', a.get('benefit')), ('지역', a.get('region')), ('나이', (f"만 {a['age_min'] or ''}~{a['age_max'] or ''}세" if a.get('age_min') or a.get('age_max') else '')),
                      ('소득 조건', a.get('income')), ('신청 방법', a.get('how')), ('주관', a['org']), ('신청 기간', '상시 신청' if a.get('always') else period), ('출처', a['source'] or '공식 공고')] if x[1]])
        btn = (f'<a class="btn" href="{E(a["url"])}" target="_blank" rel="noopener nofollow">공식 사이트에서 신청하기 →</a>' if a['url'] else '')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">청약·신청</a></p>
<section class="dh" data-c="apply"><span class="ic big">{a["icon"]}</span><h1>{E(a["title"])}</h1><p class="lead">{'<span class="d">상시</span> 지금 신청할 수 있어요' if a.get('always') else f'<span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span> {ddot(a["end"])} 마감'}</p></section>
<div class="my-acts" data-id="a:{E(a['id'])}" data-title="{E(a['title'])}" data-end="{'' if a.get('always') else a['end']}"></div>
{say('o_suit', f'신청 기간을 놓치지 마세요! 자격 조건은 <b>공식 공고</b>에서 꼭 확인해 주세요.')}
<div class="panel"><table class="info">{tb}</table>{btn}</div>
<h2>신청 전 확인할 것</h2><ul class="chk"><li>신청 자격(나이·소득·자산·거주지·무주택 여부)</li><li>필요 서류와 본인인증 수단</li><li>발표일과 계약·납부 일정</li></ul>'''
        page(f'/a/{a["id"]}/', a['title'], f'{a["title"]} — {a["kind"]}, {ddot(a["end"])} 마감. 신청 기간과 공식 신청처 정리.', body,
             [('루리의 줍줍', '/'), ('청약·신청', '/apply/'), (a['title'], f'/a/{a["id"]}/')])
    lst = ''.join(ap_card(a) for a in aps) or '<li class="empty"><img src="/assets/ruri/o_desk_s.webp" width="64" height="88" alt=""><p>지금 정리 중이에요. 곧 청약·신청 일정을 올릴게요!</p></li>'
    page('/apply/', f'청약·신청 일정 모음', '아파트 청약, 공공임대, 공모주, 지원금 신청 일정을 마감 순서로 정리했어요.',
         f'''<p class="bc"><a href="/">홈</a> › 청약·신청</p><section class="dh" data-c="apply"><span class="ic big">📝</span><h1>청약·신청</h1><p class="lead">진행 중 <b>{len(aps)}건</b> · 마감 임박순</p></section>
{say('o_desk', '신청만 하면 되는 기회들이에요. 기간이 짧으니 미리 챙겨요!')}{APPLY_INTRO}<h2>진행 중 청약·신청</h2><ul class="list">{lst}</ul>''',
         [('루리의 줍줍', '/'), ('청약·신청', '/apply/')])


HERO_JS = '''<script>(function(){var o=[['smile','오늘도 마감 임박 공모전 챙겨 왔어요 ✨'],['o_suit','오늘의 공모전 브리핑 시작할게요!'],['o_gray','상금 큰 공모전부터 정리해 뒀어요.'],['o_present','이번 주 마감, 같이 확인해 볼까요?'],['o_desk','새 공모전을 방금 업데이트했어요.'],['o_cardigan','글쓰기 공모전도 많아요. 천천히 골라 보세요.'],['o_trench','해외 공모전도 챙겨 왔어요.'],['o_anchor','마감 소식 전해 드릴게요!'],['o_vest','응모 전 체크리스트도 잊지 마세요.']];
try{var p=o[Math.floor(Math.random()*o.length)],i=document.getElementById('hero-ruri'),b=document.querySelector('.hb');if(i){i.src='/assets/ruri/'+p[0]+'.webp'}if(b){b.innerHTML='안녕하세요, <b>루리</b>예요!<br>'+p[1]}}catch(e){}})();</script>'''


def build():
    contests, events = load()
    late = datetime.datetime.now().hour >= 18  # 대부분 18시·업무시간 마감 → 저녁 빌드부터 오늘 마감은 내림
    live = [c for c in contests if dday(c['end'])[0] >= (1 if late else 0)]
    events = [e for e in events if dday(e['end'])[0] >= (1 if late else 0)]
    for d in ('c', 'cat', 'event', 'guide'):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    for c in contests:
        detail(c, live)
    sync_shots(live)
    keys = ('id', 'title', 'org', 'start', 'end', 'prize', 'pv', 'field', 'tags', 'th', 'elig', 'effort', 'region')
    with open(os.path.join(ROOT, 'data.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'items': [{k: c[k] for k in keys} for c in live]},
                  f, ensure_ascii=False, separators=(',', ':'))
    # 챗봇 추천용 경품 이벤트 목록 (진행 중만)
    with open(os.path.join(ROOT, 'events.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{'title': e['title'], 'org': e['org'], 'end': e['end'], 'ez': e.get('effort') or EASY.get(e['type'], e['type']), 'link': e['link']} for e in events],
                  f, ensure_ascii=False, separators=(',', ':'))
    live_rec = sorted(live, key=lambda c: -score(c))
    pre = ''.join(card(c) for c in live_rec[:60])  # 크롤러용 서버 렌더, JS 가 전체 목록으로 교체
    big = sorted(live, key=lambda c: -c['pv'])[:6]
    aps = load_apply()
    wk = [c for c in live if 1 <= dday(c['end'])[0] <= 7]
    quick = sorted([e for e in events if EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2) <= 1],
                   key=lambda e: (e['end'], EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2)))
    SHORT = re.compile(r'슬로건|네이밍|명칭|표어|캐치프레이즈|아이디어|사진|한\s*줄|삼행시|사행시|디카시|짧은\s*글|문구|애칭|이름\s*짓기|BI|캐릭터\s*이름')
    short = [c for c in live if not c.get('fee') and not re.search('우편|방문', c.get('submit') or '') and (c.get('quick') is True or (c.get('quick') is None and SHORT.search(c['title'] + ' ' + (c['field'] or ''))))]
    short = [c for c in short if dday(c['end'])[0] >= 2]
    short.sort(key=lambda c: -score(c))
    LOCAL = re.compile(r'(시민|도민|군민|구민|주민|거주|재학|재직|소재|관내|출신)')
    SMALLORG = re.compile(r'(군|구|읍|면|동)(청|청장|의회)?$|문화재단|복지관|도서관|센터$')
    hidden = sorted([c for c in live if c not in short and not c.get('fee') and (c.get('region') or LOCAL.search(c['elig'] or '') or SMALLORG.search((c['org'] or '').strip()))],
                    key=lambda c: -score(c))
    hidden = [c for c in hidden if dday(c['end'])[0] >= 2]
    cats = ''.join(f'<a class="cat" data-c="{s_}" href="/cat/{s_}/"><span class="ic">{CAT_ICON[n]}</span><b>{n}</b><span class="n">{sum(1 for c in live if n in c["tags"])}건</span></a>' for s_, n in CATS)
    # 2026-10-18 사용자: "메인이 너무 난잡 → 테마를 정하고 테마별 맞춤 UI, AI 로그 등 분리, 기획부터 다시"
    # → 메인(/)은 테마 입구(허브)만, 공모전 상담은 /contest/ 로. 유입(src·referrer)에 맞는 테마 입구를 맨 위로 + 루리 안내
    contest_home = f'''<h1 class="cs-h1">🏆 루리 공모전 추천 상담 — 이 공모전이나 해 볼까?</h1>
<section id="consult" aria-label="루리 공모전 추천 상담"><noscript><p>루리 상담은 자바스크립트가 필요해요. 진행 중 공모전 {len(live)}건이 있어요.</p></noscript></section>
{qa_home()}<p class="cs-foot">진행 중 공모전 {len(live)}건의 마감일·상금·응모 자격·접수 방법과 공식 공고 캡처를 정리해 두고, 루리가 상황에 맞는 것만 골라 드려요.</p>
<link rel="stylesheet" href="/assets/home/consult.css?v=12"><script defer src="/assets/home/consult.js?v=10"></script>'''
    page('/contest/', '루리 공모전 추천 상담 — 진행 중 공모전 ' + str(len(live)) + '건', f'진행 중인 공모전 {len(live)}건을 마감 임박순·상금순으로. 질문 몇 개면 루리가 딱 맞는 공모전을 골라 드려요.',
         contest_home, [('루리의 줍줍', '/'), ('공모전', '/contest/')])
    nw, an, tk = _rd('news/data.json'), _rd('analyst/data.json'), _rd('talk/data.json')
    i0 = (nw.get('issues') or [{}])[0]
    btc = next((c for c in an.get('coins', []) if c['sym'] == 'BTC'), None)
    d3 = sum(1 for c in live if 0 <= dday(c['end'])[0] <= 3)
    newap = sum(1 for a in aps if a.get('start') and a['start'] >= (TODAY - datetime.timedelta(days=2)).isoformat())
    doors = [
        ('issue', '/news/', '🕵️', '이슈', '오늘 많이 보도된 이슈와 기사 팩트 채점', (f'1위 · {i0.get("t", "")}' if i0 else '언론사 15곳 기사 매시간 채점'), ['커뮤니티 이슈', '인기 키워드', '풍자', '매거진']),
        ('money', '/analyst/', '📊', '머니', '증권사 목표가·코인 전망을 노드로 다시 정리', (f'비트코인 {btc["price"]["p"]:,.0f}원 · 강세 {btc["bull"]} / 약세 {btc["bear"]}' if btc and btc.get('price') else '증권사 리포트 종합'),
         [f'목표가 상향 {sum(s["up"] for s in an.get("stocks", []))}건', f'하향 {sum(s["down"] for s in an.get("stocks", []))}건']),
        ('contest', '/contest/', '🏆', '공모전', '질문 몇 개면 딱 맞는 공모전 추천', f'진행 중 {len(live)}건 · 사흘 안 마감 {d3}건', ['준비실', '수상 연구소', '원정대']),
        ('life', '/apply/', '🍳', '생활', '지원금·청약·경품·오늘 메뉴', f'지원금·청약 {len(aps)}건 · 새로 열린 것 {newap}건', ['경품', '냉장고 파먹기', '고민 해결'])]
    cards = ''.join(f'<a class="dr dr-{k}" data-k="{k}" href="{u}"><span class="dr-ic">{ic}</span><div><b>{E(n)}</b><small>{E(sub)}</small><p>{E(live_)}</p><i>{" · ".join(E(x) for x in tags)}</i></div></a>'
                    for k, u, ic, n, sub, live_, tags in doors)
    home = f'''<h1 class="hub-h">루리의 줍줍 <small>오늘 필요한 정보만 골라 드려요</small></h1>
<div id="hm-in" hidden></div>
<nav id="doors" class="doors" aria-label="테마">{cards}</nav>
{satire_top()}
<p class="hub-ai"><a href="/ailog/">🤖 이 사이트는 사람 1명 + AI로 만들었어요 — AI 제작 로그</a></p>
<script>(function(){{try{{
var q=(new URLSearchParams(location.search).get('src')||'').toLowerCase(),r=(document.referrer||'').toLowerCase(),k='jj_in',v=sessionStorage.getItem(k);
if(!v){{var s=r+' '+q;
v=/okky|geeknews|news\\.hada|velog|disquiet|github|(^| )(dev|gn|dq|velog)$/.test(s)?'dev'
:/kin\\.naver|blog\\.naver|cafe\\.naver|tistory|search\\.naver|(^| )(blog|cafe|kin)$/.test(s)?'contest'
:/(^| )(an|stock|coin|money)$/.test(s)?'money'
:/youtube|youtu\\.be|instagram|threads|dcinside|twitter|x\\.com|facebook|(^| )(yt|ig|th|dc|reel|shorts|news|sns)$/.test(s)?'issue':'-';
sessionStorage.setItem(k,v)}}
var M={{contest:['찾던 공모전·지원금부터 보여 드릴게요!','contest','/contest/'],issue:['오늘 이슈랑 팩트 채점부터 보여 드릴게요!','issue','/news/'],
money:['증권사 목표가·코인 전망 종합부터 보여 드릴게요!','money','/analyst/'],dev:['이 사이트는 사람 1명 + AI로 서버비 0원에 만들었어요.','ai','/ailog/']}},m=M[v];
if(!m)return;var h=document.getElementById('doors'),c=h.querySelector('[data-k='+m[1]+']');if(c){{h.insertBefore(c,h.firstChild);c.classList.add('pick')}}
var b=document.getElementById('hm-in');b.innerHTML='<img src="/assets/ruri/o_det_wave_s.webp" width="44" height="61" alt=""><p><b>루리</b>'+m[0]+' <a href="'+m[2]+'">바로 가기 →</a></p>';b.hidden=false;
window.gtag&&gtag('event','home_route',{{route:v}})}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="/assets/home/consult.css?v=12">'''
    page('/', '루리의 줍줍 — 이슈 · 머니 · 공모전 · 생활 정보',
         f'오늘의 이슈 팩트 채점, 증권사 목표가·코인 전망 종합, 공모전 {len(live)}건 추천, 지원금·청약·경품까지 — 테마별로 골라 보는 루리의 줍줍.',
         home, full_title=True, ld={'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'alternateName': ['루리의줍줍', 'sungprofile', '루리 줍줍'], 'url': SITE + '/'})
    for s, n in CATS:
        cl = [c for c in live if n in c['tags']]
        tips = ''.join(f'<li>{E(t)}</li>' for t in TIPS[n])
        body = f'''<p class="bc"><a href="/">홈</a> › {n}</p><section class="dh" data-c="{s}"><span class="ic big">{CAT_ICON[n]}</span><h1>{n} 공모전</h1><p class="lead">진행 중 <b>{len(cl)}건</b> · 마감 임박순</p></section>
<p>{CAT_INTRO[n]}</p>
{say(CAT_OUTFIT[n], f'<b>{n} 공모전 응모 팁</b><ul class="chk">{tips}</ul>')}{'<a class="lab-cta" href="/fridge/"><b>🍳 루리의 냉장고 파먹기</b><span>집에 있는 재료로 만들 수 있는 레시피 77개 · 요리대회 연습용으로 딱 →</span></a>' if s == 'food' else ''}
<h2>진행 중 {n} 공모전</h2>{TOOLBAR}<ul class="list" id="list">{''.join(card(c) for c in cl[:60])}</ul><button class="more" id="more" hidden>더 보기</button>'''
        page(f'/cat/{s}/', f'{n} 공모전 모음 (진행 중 {len(cl)}건)', f'{n} 분야 진행 중 공모전 {len(cl)}건 마감 임박순 정리. {CAT_INTRO[n][:70]}',
             body + listing_js(n), [('루리의 줍줍', '/'), (n, f'/cat/{s}/')])
    # 2026-10-18 사용자: "경품 이벤트도 좀 적당히 보이게, 갱신도 자동으로" — 1,300여 건 통째 나열 대신 '오늘·내일 마감 + 쉬운 것' 12개만 크게, 나머지는 종류·검색으로(events.json 매시 빌드 갱신)
    EZT = ('댓글 1줄', '퀴즈 1분', '설문 5분', '응모만', '폼 1분')
    tidy_ev = lambda t: re.sub(r'^\s*\((?:중복|\d+회 중복)[^)]*\)\s*', '', t).strip()
    top = sorted([e for e in events if dday(e['end'])[0] <= 1 and (e.get('effort') or EASY.get(e['type'], '')) in EZT and (e.get('org') or '').strip()],
                 key=lambda e: (e['end'], EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2)))[:12]
    if len(top) < 12:
        top += [e for e in sorted(events, key=lambda e: e['end']) if e not in top and (e.get('effort') or EASY.get(e['type'], '')) in EZT][:12 - len(top)]
    tcards = ''.join(f'<li><a href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><b>{E(tidy_ev(e["title"]))}</b><span><em class="{"u" if dday(e["end"])[0] <= 1 else ""}">{dday(e["end"])[1]}</em>{E(e["org"] or "공식 계정")} · <i>{E(e.get("effort") or EASY.get(e["type"], e["type"]))}</i></span></a></li>' for e in top)
    page('/event/', f'경품 이벤트 — 오늘 마감·쉬운 것부터 (진행 중 {len(events)}건)', f'댓글 1줄·퀴즈·설문·응모만 하면 되는 경품 이벤트 {len(events)}건. 오늘·내일 마감하는 쉬운 이벤트부터, 종류별·검색으로 골라 보세요. 매시간 갱신.',
         f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">생활</a> › 경품 이벤트</p><h1>🎁 경품 이벤트</h1>
{say('excited', f'오늘·내일 마감하는 쉬운 이벤트부터 골랐어요! 지금 진행 중인 이벤트는 {len(events):,}건이고, 매시간 새로 정리돼요.')}
<section class="ev-top"><h2>⚡ 오늘·내일 마감 · 쉬운 것 {len(top)}</h2><ul class="ev-ul">{tcards}</ul></section>
<h2 class="ev-h">🔎 종류별로 골라 보기</h2><section id="evl" aria-label="경품 이벤트 목록"><noscript>자바스크립트가 필요해요.</noscript></section>
<p class="note">마지막 갱신 {datetime.datetime.now().strftime('%m/%d %H:%M')} · 참여 조건(팔로우·태그·공유)과 당첨자 발표는 이벤트마다 달라요. 당첨 연락을 사칭해 개인정보나 송금을 요구하면 사기예요.</p>
<link rel="stylesheet" href="/assets/event/ev.css?v=1"><script defer src="/assets/event/ev.js?v=1"></script>''', [('루리의 줍줍', '/'), ('생활', '/apply/'), ('경품 이벤트', '/event/')])
    shutil.rmtree(os.path.join(ROOT, 'a'), ignore_errors=True)
    build_apply(aps)
    ss = load_ssul()
    build_ssul(ss, live, aps)
    guides(live)
    qa_pages(live)
    prep_page()
    fridge_page()
    app_page()
    news_page()
    extra_urls = talk_pages() + mag_pages(live, aps) + analyst_pages() + satire_pages() + kw_pages() + money_pages() + apply_rec_page()
    extra_urls += ailog_page(live, len(extra_urls)) + all_page()
    community(live)
    lab_urls = lab() or []
    me_pages()
    statics(len(live), len(events))
    urls = ['/', '/apply/', '/event/', '/guide/', '/ssul/'] + lab_urls + [f'/ssul/{x["slug"]}/' for x in ss] + [f'/a/{a["id"]}/' for a in aps] + [f'/cat/{s}/' for s, _ in CATS] + [f'/guide/{g[0]}/' for g in GUIDES] + ['/qa/', '/prep/', '/fridge/', '/app/', '/news/'] + extra_urls + [f'/guide/{q["slug"]}/' for q in QA] + \
           ['/about/', '/privacy/', '/terms/', '/contact/'] + [f'/c/{c["id"]}/' for c in contests] + sorted((f'/v/{d}/' for d in os.listdir(os.path.join(ROOT, 'v')) if os.path.isfile(os.path.join(ROOT, 'v', d, 'index.html'))), key=lambda u: int(u.split('/')[2]) if u.split('/')[2].isdigit() else 0)
    global NEW_URLS
    sm = os.path.join(ROOT, 'sitemap.xml')
    old = set(re.findall(r'<loc>([^<]+)</loc>', open(sm, encoding='utf-8').read())) if os.path.exists(sm) else set()
    NEW_URLS = [SITE + u for u in urls if SITE + u not in old]
    with open(sm, 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.writelines(f'<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls)
        f.write('</urlset>\n')
    print('contests', len(contests), 'live', len(live), 'events', len(events), 'urls', len(urls))


GUIDES = [
 ('first', '공모전 처음 응모할 때 꼭 확인할 7가지', '처음 공모전에 응모할 때 요강에서 놓치기 쉬운 응모 자격, 제출 형식, 저작권, 중복 응모, 마감 시각 등 7가지를 정리했습니다.', '''
<p>공모전은 요강을 얼마나 꼼꼼히 읽었는지에서 결과가 갈리는 경우가 많습니다. 작품이 좋아도 형식 미달로 심사에 오르지 못하는 일이 생각보다 흔합니다. 처음 응모한다면 아래 일곱 가지를 순서대로 확인해 보세요.</p>
<h2>1. 응모 자격</h2><p>나이, 거주 지역, 학생 여부, 개인·팀 여부를 먼저 봅니다. 지자체 공모전은 해당 지역 거주자나 생활권 주민만 받는 경우가 많고, 대학생 공모전은 재학 증명서를 요구하기도 합니다.</p>
<h2>2. 제출물 형식</h2><p>분량(글자 수, 원고지 매수, 영상 길이), 파일 형식(HWP·PDF·JPG·MP4), 파일명 규칙을 확인합니다. 지정 양식이 있다면 반드시 그 양식에 작성해야 합니다.</p>
<h2>3. 접수 방법</h2><p>이메일, 홈페이지, 구글폼·네이버폼, SNS 해시태그 등 방식이 다양합니다. 이메일 접수라면 제목 형식을 지정하는 경우가 많고, 첨부 용량 제한도 확인하세요.</p>
<h2>4. 마감 시각</h2><p>마감일 자정이 아니라 오후 6시나 업무 시간 기준인 경우가 있습니다. 해외 공모전은 현지 시간 기준이라 한국 시간으로 바꿔 계산해야 합니다.</p>
<h2>5. 저작권과 활용 조건</h2><p>수상작의 저작권이 주최 측에 귀속되거나, 응모작 전체를 홍보에 활용할 수 있다는 조건이 붙기도 합니다. 내 작품을 다른 곳에 다시 쓰고 싶다면 꼭 읽어 보세요.</p>
<h2>6. 중복 응모·미발표 조건</h2><p>다른 공모전 수상작이나 이미 공개한 작품은 받지 않는 경우가 대부분입니다. 수상 후에도 결격 사유가 밝혀지면 수상이 취소될 수 있습니다.</p>
<h2>7. 생성형 AI 사용 규정</h2><p>최근에는 생성형 AI 사용을 금지하거나, 사용 시 표기를 요구하는 공모전이 늘고 있습니다. 규정이 없더라도 애매하면 주최 측에 문의하는 것이 안전합니다.</p>'''),
 ('proposal', '정책·아이디어 제안서 쓰는 법', '지자체·공공기관 정책 제안과 아이디어 공모전에서 쓰는 제안서 구조(현황, 문제점, 개선안, 기대효과)와 작성 요령을 정리했습니다.', '''
<p>정책 제안·아이디어 공모전은 글솜씨보다 <b>구조</b>가 중요합니다. 심사위원은 많은 제안서를 짧은 시간에 읽기 때문에, 무엇이 문제이고 무엇을 바꾸자는 것인지가 첫 페이지에서 보여야 합니다.</p>
<h2>기본 구조</h2><ul class="chk"><li><b>제목</b>: 제안 내용을 한 줄로. 예) "버스정류장 도착 안내를 마을버스까지 확대"</li><li><b>현황</b>: 지금 어떻게 운영되고 있는지 사실 위주로</li><li><b>문제점</b>: 누가, 언제, 어떤 불편을 겪는지 구체적으로</li><li><b>개선안</b>: 무엇을 어떻게 바꿀지, 실행 주체와 단계</li><li><b>기대효과</b>: 수혜 대상과 효과(가능하면 숫자로)</li><li><b>소요 예산·추진 일정</b>: 대략이라도 제시하면 실현 가능성 평가에 유리</li></ul>
<h2>좋은 제안의 조건</h2><p>이미 시행 중인 정책과 겹치지 않아야 합니다. 제안 전에 해당 기관 홈페이지와 보도자료를 검색해 비슷한 사업이 있는지 확인하고, 있다면 그것과 무엇이 다른지 적으세요. 다른 지자체의 성공 사례를 근거로 들면 설득력이 높아집니다.</p>
<h2>접수 창구</h2><p>국민신문고(국민제안), 국민생각함, 각 지자체 홈페이지 제안 게시판으로 받는 경우가 많습니다. 본인인증이 필요한 창구가 많으니 마감 직전보다 여유 있게 제출하세요.</p>'''),
 ('writing', '수기·문학 공모전에서 눈에 띄는 글 쓰기', '수기, 수필, 시, 네이밍·슬로건 공모전에서 심사위원 눈에 띄는 글의 공통점과 분량·형식 맞추는 요령.', '''
<p>수기·문학 공모전은 응모작이 많아 첫 문단에서 인상이 결정되는 경우가 많습니다. 다음 원칙을 기억해 두세요.</p>
<h2>수기·수필</h2><p>주제를 설명하기보다 <b>장면</b>으로 보여 주세요. "도움을 받아 감사했다"보다 그날의 날씨, 들은 말, 손에 쥐고 있던 물건을 쓰는 편이 훨씬 오래 기억됩니다. 주최 기관의 사업(예: 장기요양, 안전, 환경)과 내 경험이 만나는 지점을 분명히 하세요.</p>
<h2>시</h2><p>주제어를 그대로 반복하기보다 구체적인 사물과 이미지로 바꿔 보세요. 분량 제한(편수, 행 수)을 지키는 것이 기본입니다.</p>
<h2>네이밍·슬로건</h2><p>짧고, 소리 내어 읽기 쉽고, 주최 측이 내세우려는 가치를 담아야 합니다. 후보를 여러 개 만든 뒤 기존 상표·슬로건과 겹치는지 검색해 보세요. 의미 설명을 한두 줄 붙이게 하는 공모전이 많습니다.</p>
<h2>형식</h2><p>원고지 매수 기준이라면 200자 원고지 환산 분량을, 글자 수 기준이라면 공백 포함 여부를 확인하세요. 지정 서식(HWP)이 있으면 글꼴과 줄 간격까지 그대로 두는 것이 안전합니다.</p>'''),
 ('prize', '공모전 상금 수령과 당첨 연락 확인법', '공모전 상금을 받을 때 필요한 서류, 제세공과금 공제, 당첨 사칭 연락을 구별하는 방법을 정리했습니다.', '''
<h2>상금 지급 절차</h2><p>수상자로 선정되면 주최 측이 신분증 사본, 통장 사본, 개인정보 동의서 등을 요청하는 것이 일반적입니다. 상금은 대개 제세공과금(기타소득세 등)을 원천징수한 뒤 지급되므로 공고에 적힌 금액보다 적게 입금될 수 있습니다. 공제 기준은 주최 측과 상금 성격에 따라 다르니 안내를 확인하세요.</p>
<h2>팀 수상</h2><p>팀으로 수상하면 대표자 계좌로 한 번에 지급하는 경우가 많습니다. 미리 팀원끼리 배분 방식을 정해 두면 분쟁을 줄일 수 있습니다.</p>
<h2>당첨 사칭 주의</h2><p>"당첨되었으니 수수료나 세금을 먼저 입금하라"는 연락은 사기일 가능성이 높습니다. 정상적인 공모전은 상금에서 세금을 공제하고 지급하며, 응모자에게 먼저 돈을 보내라고 하지 않습니다. 발표는 반드시 주최 기관의 공식 홈페이지나 공식 SNS 계정에서 다시 확인하세요.</p>
<h2>발표 확인</h2><p>발표일을 메모해 두고, 발표 방법(홈페이지 게시, 개별 연락, SNS 댓글)을 확인해 두세요. 연락이 닿지 않으면 수상이 취소되는 공모전도 있습니다.</p>'''),
]
_GX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guides_extra.json')  # 지식인 고민 해결 글(연구 세션이 추가)
# 고민 해결(/qa/ 목록, 글은 /guide/<slug>/ 유지 — 지식인 답변 링크). 항목: [slug, 제목, 요약, 본문HTML] 또는 {slug,title,desc,body,icon,tag}
QA = []
if os.path.exists(_GX):
    for g in json.load(open(_GX, encoding='utf-8')):
        g = g if isinstance(g, dict) else dict(zip(('slug', 'title', 'desc', 'body'), g))
        QA.append({'slug': g['slug'], 'title': g['title'], 'desc': g.get('desc', ''), 'body': g.get('body', ''), 'icon': g.get('icon') or '💬', 'tag': g.get('tag', '')})
    QA.reverse()  # 새 글이 위로


# ---- 썰 코너 (본문은 공모전 세션이 바탕화면 공모전_2026\daily\ssul\<slug>.md 로 씀) ----
# md 맨 위 머리말:  ---\ntitle: 제목\ndate: 2026-10-17\nsummary: 한 줄 요약\nfacts: Q00123, Q00456\nexpr: o_cardigan\n---\n본문(마크다운)
SSUL_DIR = r'C:\Users\k\Desktop\공모전_2026\daily\ssul'


def load_ssul():
    import markdown
    out = []
    if not os.path.isdir(SSUL_DIR):
        return out
    for f in sorted(os.listdir(SSUL_DIR)):
        if not f.endswith('.md'):
            continue
        slug = re.sub(r'[^0-9A-Za-z가-힣_-]', '', f[:-3])[:60]
        raw = open(os.path.join(SSUL_DIR, f), encoding='utf-8').read().replace('\r\n', '\n')
        meta, body = {}, raw
        m = re.match(r'---\n(.*?)\n---\n', raw, re.S)
        if m:
            for line in m.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1); meta[k.strip()] = v.strip()
            body = raw[m.end():]
        if not meta.get('title') or meta.get('draft') in ('true', '1'):
            continue
        html_ = markdown.markdown(html.escape(body, quote=False), extensions=['extra', 'nl2br'])
        out.append({'slug': slug, 'title': meta['title'][:80], 'date': meta.get('date', ''), 'summary': meta.get('summary', '')[:140],
                    'facts': [x.strip() for x in re.split(r'[,\s]+', meta.get('facts', '')) if x.strip()],
                    'expr': meta.get('expr', 'o_cardigan') if re.fullmatch(r'[a-z_]+', meta.get('expr', 'x')) else 'o_cardigan', 'html': html_})
    out.sort(key=lambda x: x['date'], reverse=True)
    return out


def build_ssul(ss, live, aps):
    shutil.rmtree(os.path.join(ROOT, 'ssul'), ignore_errors=True)
    byc = {c['id']: c for c in live}; bya = {a['id']: a for a in aps}
    for x in ss:
        rel = ''.join(card(byc[i]) for i in x['facts'] if i in byc) + ''.join(ap_card(bya[i]) for i in x['facts'] if i in bya)
        tail = (f'<h2>루리가 골라 둔 진짜 기회</h2><ul class="list">{rel}</ul>' if rel else
                '<h2>지금 낼 수 있는 대회</h2><p><a href="/">바로 낼 수 있는 대회 보러 가기 →</a></p>')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/ssul/">썰</a></p>
<article class="ssul"><p class="note">{E(x["date"])}</p><h1>{E(x["title"])}</h1>{say(x["expr"], E(x["summary"]) or "루리가 들려주는 이야기예요.")}{x["html"]}</article>{tail}'''
        page(f'/ssul/{x["slug"]}/', x['title'], x['summary'] or x['title'], body,
             [('루리의 줍줍', '/'), ('썰', '/ssul/'), (x['title'], f'/ssul/{x["slug"]}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': x['title'], 'datePublished': x['date'] or str(TODAY),
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})
    li = ''.join(f'<li><a class="card" data-c="guide" href="/ssul/{x["slug"]}/"><span class="ic">💬</span><div class="cb"><h3 class="t">{E(x["title"])}</h3><p class="o">{E(x["summary"])}</p></div></a></li>' for x in ss) \
        or '<li class="empty"><img src="/assets/ruri/o_cardigan_s.webp" width="64" height="88" alt=""><p>루리가 첫 이야기를 준비하고 있어요!</p></li>'
    page('/ssul/', '루리의 썰', '루리가 들려주는 용돈·공모전 이야기. 이야기 끝에 실제로 낼 수 있는 대회를 이어 드려요.',
         f'''<p class="bc"><a href="/">홈</a> › 썰</p><section class="dh" data-c="guide"><span class="ic big">💬</span><h1>루리의 썰</h1><p class="lead">이야기 끝에 진짜 낼 수 있는 대회가 이어져요</p></section>
{say("o_cardigan", "오늘은 무슨 얘기 해 볼까요? 재밌게 읽고, 마음에 드는 대회는 바로 넣어 봐요!")}<ul class="list">{li}</ul>''',
         [('루리의 줍줍', '/'), ('썰', '/ssul/')])


def prep_page():
    # 루리의 준비실 (2026-10-18 사용자: 공모전 준비할 사람들이 더 편하게 준비할 공간 + 꿀팁 공유)
    G = json.load(open(os.path.join(ROOT, 'assets', 'prep', 'data.json'), encoding='utf-8'))['genres']
    seed = ''.join(f'<li class="tp-ruri"><span class="tp-who">{g["icon"]} {E(g["name"])}</span><p>{E(x)}</p></li>' for g in G for x in g['tips'][:2])
    body = f'''<p class="bc"><a href="/">홈</a> › 준비실</p><h1>📋 루리의 공모전 준비실</h1>
{say("o_desk", "공모전 하나 고르면 마감일에 맞춰 할 일을 날짜별로 짜 드릴게요. 체크하면서 따라오기만 하면 돼요!")}
<section id="prep" aria-label="공모전 준비 보드">
<h2>🧰 준비 도구</h2><div class="pp-tools"><div class="pp-tool"><h3>📏 분량 계산기 <small>글자 수·원고지 매수·A4 쪽수</small></h3><div id="pp-count"><noscript>자바스크립트가 필요해요.</noscript></div></div>
<div class="pp-links"><a href="/lab/#diag"><b>🏆 내 문구 진단</b>슬로건·네이밍을 수상작 공식과 비교</a><a href="/lab/"><b>🔬 수상 연구소</b>실제 수상작과 분석</a><a href="/community/"><b>🚩 원정대</b>같이 할 팀원 찾기</a><a href="/qa/"><b>💬 고민 해결</b>준비하다 막힌 것들</a></div></div>
<section id="tips"><h2>🍯 장르별 공모전 꿀팁 <small>루리 팁 + 회원들이 직접 나눈 팁</small></h2><div class="tp-chips"></div><ul class="tp-list">{seed}</ul><div class="tp-form"></div></section>
</section><link rel="stylesheet" href="/assets/prep/prep.css?v=3"><script defer src="/assets/prep/prep.js?v=3"></script>'''
    page('/prep/', '루리의 공모전 준비실 — 마감 역산 일정·체크리스트·꿀팁', '공모전을 고르면 마감일에 맞춘 준비 일정과 장르별 체크리스트를 만들어 줘요. 슬로건·수기·디자인·영상·사진·정책 제안 꿀팁과 분량 계산기까지.',
         body, [('루리의 줍줍', '/'), ('준비실', '/prep/')])


KDAY = '월화수목금토일'
GRADE = {'ok': ('✅', '믿을 만함'), 'warn': ('🟡', '확인 필요'), 'bad': ('🔴', '의심')}


def kdate(d):
    d = datetime.date.fromisoformat(d) if isinstance(d, str) else d
    return f'{d.month}월 {d.day}일({KDAY[d.weekday()]})'


TALK_NOTE = '<p class="tk-warn">💬 커뮤니티 반응을 정리한 것이며 사실 확인 전이에요. 원문은 각 커뮤니티 글이고, 언론 보도 여부를 함께 표시해요.</p>'


def talk_issue(x, day):
    n = x.get('news')
    if n and day == TODAY.isoformat():
        g = GRADE.get(n.get('g'), ('', ''))[0]
        sc = n.get('s') if n.get('s') is not None else ''
        nw = f'<a class="tk-news" href="/news/#is{n["n"]}">📰 언론 {n["on"]}곳 보도 · 감별 {g} {sc}점 →</a>'
    elif n:
        nw = '<span class="tk-news">📰 언론에도 보도됨</span>'
    else:
        nw = '<span class="tk-nn">📰 언론 미확인 · 커뮤니티에서만 도는 이야기</span>'
    pr = ''.join(f'<a href="{E(p["u"])}"><em>{E(p["k"])}</em><b>{E(p["t"])}</b></a>' for p in x.get('pr') or [])
    prh = f'<div class="nw-pr"><small>📌 관련 있는 줍줍</small>{pr}</div>' if pr else ''
    posts = ''.join(f'<li><a href="{E(p["u"])}" target="_blank" rel="noopener nofollow ugc"><em>{E(p["s"])}</em>{E(p["t"])}</a><small>💬 {p["nc"]}</small></li>' for p in x['posts'])
    kw = ''.join(f'<span>#{E(k)}</span>' for k in x['kw'][:5])
    sm = '<br>'.join(E(l) for l in x['sum'])
    return (f'<article class="tk-is" id="t{x["n"]}"><div class="tk-r">{x["n"] + 1}</div><div class="tk-b"><p class="tk-m"><span class="tk-hot">🔥 {x["nsite"]}개 커뮤니티</span><span>댓글 {x["nc"]:,}</span></p>'
            f'<h2>{E(x["t"])}</h2><p class="tk-s">{sm}</p><p class="tk-kw">{kw}</p>{nw}{prh}'
            f'<details><summary>커뮤니티 원문 {len(x["posts"])}건</summary><ul class="tk-ps">{posts}</ul></details></div></article>')


def talk_pages():
    # 루리의 커뮤니티 이슈 (2026-10-18 사용자 승인: "서로 이야기하면서 만들어, 매거진이랑", "정보성으로") — 매시 talk.py, 날짜별 아카이브
    ad = os.path.join(ROOT, 'talk', 'archive')
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True) if os.path.isdir(ad) else []
    if not days:
        return []
    arch = '<section class="tk-arch"><h2>📅 날짜별 커뮤니티 이슈</h2><p>' + ''.join(f'<a href="/talk/{d}/">{kdate(d)}</a>' for d in days[:60]) + '</p></section>'
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=9"><link rel="stylesheet" href="/assets/news/news.css?v=3">'
    note = '<p class="note">순위는 여러 커뮤니티에 동시에 뜬 정도·댓글 수·인기글에 머문 시간으로 매겨요. 성·혐오·개인 신상·비방·사생활 폭로성 글은 모으지 않아요. 요약은 루리가 제목과 수치만 보고 정리했어요.</p>'
    urls = ['/talk/']
    for i, d in enumerate(days):
        x = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        iss = x.get('issues', [])
        st = ' · 매시간 갱신' if i == 0 else ' · 확정'
        head = (f'<div class="tk-hero"><img src="/assets/ruri/o_det_think.webp" width="300" height="415" alt="커뮤니티 이슈를 정리하는 루리"><div><small>{E(x["updated"])} 기준{st}</small>'
                f'<b>{kdate(d)} 커뮤니티 이슈 TOP{len(iss)}</b><p>커뮤니티 {x.get("sites", 0)}곳 인기글 {x.get("npost", 0):,}건을 같은 화제끼리 묶어, 몇 곳에서 동시에 떴는지로 순위를 매겼어요.</p></div></div>')
        body = head + TALK_NOTE + ''.join(talk_issue(y, d) for y in iss) + arch + note + css
        dsc = f'{kdate(d)} 커뮤니티 13곳 인기글을 화제별로 묶은 이슈 순위: ' + ', '.join(y['t'] for y in iss[:3])
        if i == 0:
            page('/talk/', '루리의 커뮤니티 이슈 — 지금 여러 커뮤니티에서 동시에 뜨는 화제', dsc,
                 '<p class="bc"><a href="/">홈</a> › 커뮤니티 이슈</p><h1>💬 루리의 커뮤니티 이슈</h1>' + body, [('루리의 줍줍', '/'), ('커뮤니티 이슈', '/talk/')])
        page(f'/talk/{d}/', f'{kdate(d)} 커뮤니티 이슈 TOP{len(iss)} — 더쿠·클리앙·디시 등 지금 뜨는 화제', dsc,
             f'<p class="bc"><a href="/">홈</a> › <a href="/talk/">커뮤니티 이슈</a> › {kdate(d)}</p><h1>💬 {kdate(d)} 커뮤니티 이슈</h1>' + body,
             [('루리의 줍줍', '/'), ('커뮤니티 이슈', '/talk/'), (kdate(d), f'/talk/{d}/')])
        urls.append(f'/talk/{d}/')
    return urls


MAG0 = datetime.date(2026, 10, 18)


def _rd(p):
    try:
        return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
    except Exception:
        return {}


def mag_snapshot(live, aps):
    """오늘 호 재료를 mag/archive/YYYY-MM-DD.json 에 저장(매 빌드 갱신, 자정 지나면 그날 호 확정)."""
    md = os.path.join(ROOT, 'mag', 'archive')
    os.makedirs(md, exist_ok=True)
    nw, tk = _rd('news/data.json'), _rd('talk/data.json')
    I = {a['id']: a for a in nw.get('items', [])}
    pol = []
    for x in nw.get('issues', []):
        if x.get('c') != '정치':
            continue
        a0 = I.get(x['a'][0]) or {}
        pol.append({'t': x['t'], 'on': x['on'], 's': x.get('s'), 'g': x.get('g'), 'claim': x.get('claim', 0), 'cf': x.get('cf') or [], 'u': a0.get('u', ''), 'o': a0.get('o', ''), 'n': x['n']})
    pol = pol[:3]
    talk = [{'t': x['t'], 'nsite': x['nsite'], 'nc': x['nc'], 'sum': x['sum'][0], 'n': x['n'], 'news': bool(x.get('news'))} for x in tk.get('issues', [])][:5]
    soon = sorted([c for c in live if 1 <= dday(c['end'])[0] <= 3], key=lambda c: -(c.get('pv') or 0))[:3]
    con = [{'id': c['id'], 't': c['title'], 'p': c.get('prize', ''), 'e': c['end']} for c in soon]
    new = []
    for a in aps:
        try:
            if a.get('start') and (TODAY - datetime.date.fromisoformat(a['start'])).days in (0, 1, 2):
                new.append(a)
        except Exception:
            pass
    new = sorted(new, key=lambda a: a['start'], reverse=True)[:5]
    apl = [{'id': a['id'], 't': a['title'], 'k': a.get('kind', ''), 'e': a.get('end', '')} for a in new]
    R = _rd('assets/fridge/recipes.json').get('recipes', [])
    mn = R[(TODAY - MAG0).days * 7 % len(R)] if R else None
    snap = {'date': TODAY.isoformat(), 'no': (TODAY - MAG0).days + 1, 'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'pol': pol, 'talk': talk, 'con': con, 'apl': apl,
            'menu': {'n': mn['n'], 'e': mn['e'], 'm': mn['m'], 'need': mn['need'], 's': mn['s']} if mn else None}
    json.dump(snap, open(os.path.join(md, TODAY.isoformat() + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))


LEAD_DIR = r'C:\Users\k\Desktop\공모전_2026\이슈리딩'


def lead_html(d):
    """홍보 세션(연구 ⑂)이 쓰는 「루리의 이슈 리딩」 원고 mag.json + 카드 10장을 매거진 호 맨 위에 그대로 싣는다(2026-10-18 합의)."""
    dd = datetime.date.fromisoformat(d)
    src = os.path.join(LEAD_DIR, f'{dd:%m%d}')
    mj = os.path.join(src, 'mag.json')
    if not os.path.exists(mj):
        return '', None
    try:
        m = json.load(open(mj, encoding='utf-8'))
    except Exception:
        return '', None
    out_dir = os.path.join(ROOT, 'mag', d, 'cards')
    os.makedirs(out_dir, exist_ok=True)
    from PIL import Image
    secs = []
    for i, pg in enumerate(m.get('pages', [])):
        png = os.path.join(src, 'cards', f'{i + 1:02d}.png')
        img = ''
        if os.path.exists(png):
            wp = os.path.join(out_dir, f'{i + 1:02d}.webp')
            if not os.path.exists(wp) or os.path.getmtime(wp) < os.path.getmtime(png):
                Image.open(png).convert('RGB').resize((720, 900), Image.LANCZOS).save(wp, quality=82)
            img = f'<img src="/mag/{d}/cards/{i + 1:02d}.webp" width="720" height="900" alt="{E(pg.get("title", ""))}" loading="{"eager" if i == 0 else "lazy"}">'
        rows = ''.join(f'<li>{E(r)}</li>' for r in pg.get('rows', []))
        say_ = ' '.join(pg.get('say', []))
        secs.append(f'<section class="ld-p">{img}<div class="ld-t">{("<small>" + E(pg["kicker"]) + "</small>") if pg.get("kicker") else ""}<h2>{E(pg.get("title", ""))}</h2>'
                    f'{("<p class=ld-big>" + E(pg["big"]) + "</p>") if pg.get("big") else ""}<ul>{rows}</ul>{("<p class=ld-say>💬 " + E(say_) + "</p>") if say_ else ""}'
                    f'{("<p class=ld-src>출처: " + E(pg["src"]) + "</p>") if pg.get("src") else ""}</div></section>')
    first = (m.get('pages') or [{}])[0].get('title', '')
    return f'<div class="ld">{"".join(secs)}</div><h2 class="ld-more">📌 오늘의 줍줍 모음</h2>', first


def mag_issue_html(m, d):
    is_today = d == TODAY.isoformat()
    sec = []
    if m['pol']:
        li = ''
        for i, x in enumerate(m['pol']):
            g = GRADE.get('bad' if x['cf'] else x['g'], ('', ''))[0]
            sc = x['s'] if x['s'] is not None else ''
            cl = ' · 🗣️ 발언·주장' if x['claim'] else ''
            href = f'/news/#is{x["n"]}' if is_today else E(x['u'])
            ext = '' if is_today else ' target="_blank" rel="noopener nofollow"'
            li += f'<li><a href="{href}"{ext}><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["on"]}곳 보도 · {g} {sc}점{cl}</span></a></li>'
        sec.append(f'<section class="mg-s"><h2>🕵️ 오늘의 정치 이슈 TOP{len(m["pol"])}</h2>' + say('o_det_think', '여러 언론사가 가장 많이 다룬 정치 이슈예요. 점수는 교차 보도·출처·제목-본문 일치로 매긴 확인 신호예요.')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/news/">이슈 감별 전체 보기 →</a></section>')
    if m['talk']:
        li = ''
        for i, x in enumerate(m['talk']):
            nb = ' · 📰 언론 보도' if x['news'] else ' · 언론 미확인'
            li += f'<li><a href="/talk/{d}/#t{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["nsite"]}개 커뮤니티 · 댓글 {x["nc"]:,}{nb}</span></a></li>'
        sec.append(f'<section class="mg-s"><h2>💬 커뮤니티 이슈 TOP{len(m["talk"])}</h2>' + say('o_det_wave', '여러 커뮤니티에 동시에 뜬 화제예요. 커뮤니티 반응이라 사실 확인 전이에요!')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/talk/{d}/">커뮤니티 이슈 전체 보기 →</a></section>')
    if m['con']:
        li = ''.join(f'<li><a href="/c/{x["id"]}/"><em>🏆</em><b>{E(x["t"])}</b><span>{E(x["p"] or "상금 공고 확인")} · {x["e"][5:].replace("-", "/")} 마감</span></a></li>' for x in m['con'])
        sec.append('<section class="mg-s"><h2>⏰ 마감 임박 공모전</h2>' + say('o_present', '사흘 안에 마감하는 공모전 중 상금이 큰 것만 골랐어요. 지금 넣어도 늦지 않아요!')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/">공모전 전체 보기 →</a></section>')
    if m['apl']:
        li = ''
        for x in m['apl']:
            e = (' · ~' + x['e'][5:].replace('-', '/')) if x['e'] else ''
            li += f'<li><a href="/a/{x["id"]}/"><em>💰</em><b>{E(x["t"])}</b><span>{E(x["k"])}{e}</span></a></li>'
        sec.append('<section class="mg-s"><h2>💰 새로 열린 지원금·청약</h2>' + say('o_cardigan', '이틀 안에 새로 접수를 시작한 지원금·청약이에요. 조건이 맞는지 확인해 보세요.')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/apply/">지원금·청약 전체 보기 →</a></section>')
    if m.get('menu'):
        mn = m['menu']
        steps = ''.join(f'<li>{E(x)}</li>' for x in mn['s'])
        sec.append('<section class="mg-s"><h2>🍳 루리의 오늘 메뉴</h2>' + say('o_cook', f'오늘은 {E(mn["n"])} 어때요? {mn["m"]}분이면 돼요!')
                   + f'<div class="mg-menu"><b>{mn["e"]} {E(mn["n"])}</b><span>필요한 재료: {E(", ".join(mn["need"]))}</span><ol>{steps}</ol></div><a class="mg-more" href="/fridge/">냉장고 재료로 다른 메뉴 찾기 →</a></section>')
    st = '기준 · 오늘 하루 계속 갱신' if is_today else '확정'
    head = (f'<div class="mg-hero"><small>루리의 줍줍 데일리 · 제{m["no"]}호</small><b>{kdate(d)}</b><p>오늘의 정치 이슈 · 커뮤니티 화제 · 마감 임박 공모전 · 새 지원금 · 오늘 메뉴를 한 장에 모았어요.</p>'
            f'<span>{E(m["updated"])} {st}</span></div>')
    lead, _ = lead_html(d)
    return head + lead + ''.join(sec)


def mag_pages(live, aps):
    # 루리의 줍줍 데일리 (2026-10-18 사용자: "매거진이랑 등등으로", "정보성으로") — 하루 한 호, 정적 페이지 + 아카이브
    mag_snapshot(live, aps)
    md = os.path.join(ROOT, 'mag', 'archive')
    days = sorted([f[:-5] for f in os.listdir(md) if f.endswith('.json')], reverse=True)
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=9">'
    urls, cards = ['/mag/'], []
    for d in days:
        m = json.load(open(os.path.join(md, d + '.json'), encoding='utf-8'))
        _, lt = lead_html(d)
        tops = ([lt] if lt else []) + [x['t'] for x in m['pol'][:1]] + [x['t'] for x in m['talk'][:1]]
        nm = '루리의 이슈 리딩' if lt else '루리의 줍줍 데일리'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/mag/">매거진</a> › {kdate(d)}</p><h1>📰 {nm} {kdate(d)}</h1>' + mag_issue_html(m, d)
                + '<p class="mg-nav"><a href="/mag/">📚 지난 호 모두 보기</a></p>' + css)
        page(f'/mag/{d}/', f'{nm} {kdate(d)} — ' + (lt or '정치 이슈·커뮤니티 화제·마감 공모전'), (f'{kdate(d)} 하루 정보 모음: ' + ' / '.join(tops))[:150], body,
             [('루리의 줍줍', '/'), ('매거진', '/mag/'), (kdate(d), f'/mag/{d}/')])
        urls.append(f'/mag/{d}/')
        cards.append(f'<li><a href="/mag/{d}/"><small>제{m["no"]}호</small><b>{kdate(d)}</b><span>{E(" · ".join(tops))}</span></a></li>')
    page('/mag/', '루리의 줍줍 데일리 — 매일 정보 매거진', '매일 한 장으로 보는 정치 이슈 팩트 감별, 커뮤니티 화제, 마감 임박 공모전, 새 지원금·청약, 오늘 메뉴. 루리의 줍줍 데일리 매거진 전체 호.',
         '<p class="bc"><a href="/">홈</a> › 매거진</p><h1>📰 루리의 줍줍 데일리</h1>' + say('o_present', '매일 한 장으로 정리해 드려요. 오늘 호는 하루 동안 계속 새 소식으로 바뀌어요!')
         + f'<ul class="mg-idx">{"".join(cards)}</ul>' + css, [('루리의 줍줍', '/'), ('매거진', '/mag/')])
    return urls


DIRN = {'up': ('🔺', '목표가 상향'), 'down': ('🔻', '목표가 하향'), 'keep': ('➖', '의견 유지'), 'bull': ('🟢', '강세 전망'), 'bear': ('🔴', '약세 전망'), 'neutral': ('⚪', '중립·혼조')}
AN_NOTE = ('<p class="an-warn">📊 증권사 리포트·전문가 전망을 다룬 기사를 모아 다시 정리한 정보예요. 루리의 줍줍이 직접 주가를 예측하거나 매수·매도를 권하지 않아요. '
           '투자 판단과 책임은 본인에게 있어요. 목표가·의견은 각 증권사·기관의 것이며 원문 기사에서 확인해 주세요.</p>')


def won_txt(v):
    if not v:
        return '-'
    return f'{v // 10000:,}만{(" " + format(v % 10000, ",")) if v % 10000 else ""}원' if v >= 10000 else f'{v:,}원'


def an_tree(tree, keys):
    out = ''
    for d in keys:
        rows = tree.get(d) or []
        if not rows:
            continue
        li = ''.join(f'<li><b>{E(r[0])}</b><span>{E(", ".join(r[1]))}{(" 외 " + str(r[2] - len(r[1])) + "건") if len(r) > 2 and r[2] > len(r[1]) else ""}</span></li>' for r in rows[:6])
        out += f'<div class="an-br {d}"><p>{DIRN[d][0]} {DIRN[d][1]} 근거</p><ul>{li}</ul></div>'
    return f'<div class="an-tree">{out}</div>' if out else ''


def an_nodes(nodes, coin=False):
    li = ''
    for n in nodes[:12]:
        dt = datetime.datetime.fromtimestamp(n['ts']).strftime('%m/%d')
        if coin:
            meta = f'{E(n.get("who") or n["o"])}{(" · 목표 " + format(n["tgt"], "g") + "만 달러") if n.get("tgt") else ""}'
        else:
            tp = (f'{won_txt(n["tp0"])} → {won_txt(n["tp"])}' if n.get('tp0') else won_txt(n['tp'])) if n.get('tp') else ''
            meta = f'{E(n["br"])}{(" · " + E(n["op"])) if n.get("op") else ""}{(" · " + tp) if tp else ""}{" · ⚠️ 숫자 확인 필요(평균 제외)" if n.get("chk") else ""}'
        li += (f'<li class="{n["dir"]}"><span class="an-d">{DIRN[n["dir"]][0]}</span><div><small>{dt} · {meta}</small>'
               f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["t"])}</a><em>{E(n["o"])}</em></div></li>')
    return f'<ul class="an-nodes">{li}</ul>'


DCOL = {'up': '#ef4444', 'bull': '#ef4444', 'down': '#3b82f6', 'bear': '#3b82f6', 'keep': '#94a3b8', 'neutral': '#94a3b8'}


def kdate_of(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')


def coin_svg(c):
    """30일 종가 선 + 전망 기사가 나온 날 강세(빨강)·약세(파랑)·혼조(회색) 점을 겹친다."""
    h = c.get('hist') or []
    if len(h) < 5:
        return ''
    W, H, L, R, T, B = 640, 250, 70, 14, 16, 34
    ps = [v for _, v in h]
    lo, hi = min(ps), max(ps)
    pad = (hi - lo) * 0.08 or hi * 0.01
    lo, hi = lo - pad, hi + pad
    X = lambda i: L + (W - L - R) * i / (len(h) - 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    pts = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, (_, v) in enumerate(h))
    area = f'{X(0):.1f},{H - B} ' + pts + f' {X(len(h) - 1):.1f},{H - B}'
    idx = {d: i for i, (d, _) in enumerate(h)}
    dots, stack = '', {}
    for n in c.get('nodes', []):
        i = idx.get(kdate_of(n['ts']))
        if i is None:
            continue
        k = stack[i] = stack.get(i, 0) + 1
        if k > 6:
            continue
        y = Y(h[i][1]) - 11 * k
        dots += f'<circle cx="{X(i):.1f}" cy="{y:.1f}" r="4.5" fill="{DCOL[n["dir"]]}" stroke="#fff" stroke-width="1.5"><title>{E(n["t"])}</title></circle>'
    dots += ''.join(f'<text x="{X(i) - 8:.1f}" y="{Y(h[i][1]) - 80:.1f}" text-anchor="end" class="lb">+{k - 6}</text>' for i, k in stack.items() if k > 6)
    fmt = (lambda v: f'{v / 1e8:.2f}억') if hi >= 1e8 else (lambda v: f'{v / 1e4:,.0f}만') if hi >= 1e5 else (lambda v: f'{v:,.0f}')
    ax = ''.join(f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{fmt(v)}</text><line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="g"/>' for v in (lo + pad, (lo + hi) / 2, hi - pad))
    xs = ''.join(f'<text x="{X(i):.1f}" y="{H - 10}" text-anchor="middle">{h[i][0][5:].replace("-", "/")}</text>' for i in (0, len(h) // 2, len(h) - 1))
    return (f'<figure class="an-ch"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(c["name"])} 30일 가격과 전망 기사"><defs><linearGradient id="ga{c["sym"]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".25"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></linearGradient></defs>'
            f'{ax}<polygon points="{area}" fill="url(#ga{c["sym"]})"/><polyline points="{pts}" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linejoin="round"/>{dots}{xs}</svg>'
            f'<figcaption>업비트 일봉 종가(원) · 점 = 그날 나온 전망 기사 <i style="color:#ef4444">● 강세</i> <i style="color:#3b82f6">● 약세</i> <i style="color:#94a3b8">● 혼조</i></figcaption></figure>')


def stock_svg(s):
    """증권사별 목표가: 점(새 목표가) + 이전 목표가에서 이어지는 선, 평균 목표가 점선."""
    ns = [n for n in s.get('nodes', []) if n.get('tp') and not n.get('chk')]
    if not ns:
        return ''
    W, H, L, R, T, B = 640, 240, 86, 16, 20, 34
    now = time.time()
    t0 = min(min(n['ts'] for n in ns), now - 7 * 86400)
    vals = [n['tp'] for n in ns] + [n['tp0'] for n in ns if n.get('tp0')]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or hi * 0.1
    lo, hi = lo - pad, hi + pad
    X = lambda ts: L + (W - L - R) * (ts - t0) / max(1, now - t0)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    g = ''
    for n in ns:
        x = X(n['ts'])
        if n.get('tp0'):
            g += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y(n["tp0"]):.1f}" y2="{Y(n["tp"]):.1f}" stroke="{DCOL[n["dir"]]}" stroke-width="3" stroke-opacity=".45"/><circle cx="{x:.1f}" cy="{Y(n["tp0"]):.1f}" r="3.5" fill="#fff" stroke="{DCOL[n["dir"]]}" stroke-width="2"/>'
        g += f'<circle cx="{x:.1f}" cy="{Y(n["tp"]):.1f}" r="6" fill="{DCOL[n["dir"]]}" stroke="#fff" stroke-width="2"><title>{E(n["br"])} {won_txt(n["tp"])}</title></circle><text x="{x + 9:.1f}" y="{Y(n["tp"]) + 4:.1f}" class="lb">{E(n["br"].replace("투자증권", "").replace("증권", "").replace("금융투자", ""))}</text>'
    avg = s.get('tp_avg')
    av = f'<line x1="{L}" x2="{W - R}" y1="{Y(avg):.1f}" y2="{Y(avg):.1f}" stroke="#10b981" stroke-dasharray="6 4" stroke-width="2"/><text x="{W - R}" y="{Y(avg) - 6:.1f}" text-anchor="end" class="lb" fill="#047857">평균 {won_txt(avg)}</text>' if avg else ''
    ax = ''.join(f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{won_txt(int(v))}</text><line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="g"/>' for v in (lo + pad, hi - pad) if v > 0)
    xs = f'<text x="{L}" y="{H - 10}">{kdate_of(t0)[5:].replace("-", "/")}</text><text x="{W - R}" y="{H - 10}" text-anchor="end">오늘</text>'
    return (f'<figure class="an-ch"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(s["name"])} 증권사별 목표가">{ax}{av}{g}{xs}</svg>'
            f'<figcaption>증권사별 목표가(원) · <i style="color:#ef4444">● 상향</i> <i style="color:#3b82f6">● 하향</i> <i style="color:#94a3b8">● 유지</i> · 흰 점 = 이전 목표가</figcaption></figure>')


def stock_card(s, full=False):
    tot = s['up'] + s['down'] + s['keep']
    bar = ''.join(f'<i class="{d}" style="width:{round(100 * s[d] / tot)}%"></i>' for d in ('up', 'keep', 'down') if tot and s[d])
    rng = f'{won_txt(s["tp_min"])} ~ {won_txt(s["tp_max"])}' if s['tp_min'] and s['tp_max'] and s['tp_min'] != s['tp_max'] else ''
    head = (f'<div class="an-h"><h3><a href="/analyst/s/{s["id"]}/">{E(s["name"])}</a></h3>{"<span class=an-mix>⚖️ 의견 엇갈림</span>" if s["mixed"] else ""}</div>'
            f'<p class="an-st">증권사 {s["nb"]}곳 · 🔺{s["up"]} ➖{s["keep"]} 🔻{s["down"]}{(" · 평균 목표가 " + won_txt(s["tp_avg"])) if s["tp_avg"] else ""}{(" (" + rng + ")") if rng else ""}{(" · 기사 속 상승여력 평균 " + str(s["upside"]) + "%") if s.get("upside") is not None else ""}</p>'
            f'<div class="an-bar">{bar}</div>')
    return f'<article class="an-c">{head}{stock_svg(s)}{an_tree(s["tree"], ("up", "down", "keep"))}' + (an_nodes(s['nodes']) if full else f'<a class="an-more" href="/analyst/s/{s["id"]}/">리포트 노드 {s["nn"]}개 자세히 →</a>') + '</article>'


def coin_card(c, full=False):
    p = c.get('price') or {}
    pr = f'<span class="an-p">{p["p"]:,.0f}원 <b class="{"up" if p["chg"] >= 0 else "down"}">{p["chg"]:+.2f}%</b> <small>업비트</small></span>' if p else ''
    tot = c['bull'] + c['bear'] + c['neutral']
    bar = ''.join(f'<i class="{d}" style="width:{round(100 * c[d] / tot)}%"></i>' for d in ('bull', 'neutral', 'bear') if tot and c[d])
    tg = f' · 기사 속 목표 {format(c["tgt"][0], "g")}~{format(c["tgt"][1], "g")}만 달러' if c.get('tgt') else ''
    return (f'<article class="an-c"><div class="an-h"><h3><a href="/analyst/coin/{c["sym"].lower()}/">{E(c["name"])} <small>{c["sym"]}</small></a></h3>{pr}</div>'
            f'<p class="an-st">최근 7일 전망 기사 {c["n"]}건 · 🟢 강세 {c["bull"]} · ⚪ 혼조 {c["neutral"]} · 🔴 약세 {c["bear"]}{tg}</p><div class="an-bar">{bar}</div>'
            + coin_svg(c) + an_tree(c['tree'], ('bull', 'bear', 'neutral')) + (an_nodes(c['nodes'], True) if full else f'<a class="an-more" href="/analyst/coin/{c["sym"].lower()}/">전망 노드 {c["n"]}개 자세히 →</a>') + '</article>')


def analyst_pages():
    # 애널리스트 분석의 분석 (2026-10-18 사용자: 애널리스트 발언을 노드로 나눠 2차 가공, 비트코인·이더리움 등, 사이트 비중 40%)
    d = _rd('analyst/data.json')
    if not d:
        return []
    S, C = d.get('stocks', []), d.get('coins', [])
    css = '<link rel="stylesheet" href="/assets/analyst/analyst.css?v=4">'
    ups = sorted([s for s in S if s['up'] > s['down']], key=lambda s: (-s['up'], -s['last']))[:10]
    dns = sorted([s for s in S if s['down'] > s['up']], key=lambda s: (-s['down'], -s['last']))[:10]
    mix = [s for s in S if s['mixed']][:10]
    nn = sum(s['nn'] for s in S)
    hero = (f'<div class="an-hero"><img src="/assets/ruri/o_present.webp" width="300" height="415" alt="애널리스트 분석을 정리하는 루리"><div><small>{E(d["updated"])} 기준 · 매시간 갱신</small>'
            f'<b>리포트 노드 {nn}개 · 종목 {len(S)}개 · 코인 {len(C)}개</b><p>증권사 리포트 기사 속 발언을 「상향·하향·유지」 노드로 쪼개고, 근거별로 어느 증권사가 말했는지 다시 묶었어요.</p></div></div>')
    how = ('<details class="an-how"><summary>노드 분석은 이렇게 해요</summary><ol><li>증권 기사 RSS에서 「목표가」「투자의견」이 나온 기사만 골라요.</li><li>기사 1건 = 노드 1개: 증권사·종목·방향(상향/하향/유지)·투자의견·목표가(이전→새)·근거 태그를 뽑아요.</li>'
           '<li>근거 태그(실적 개선·업황 호조·수주·주주환원·저평가 / 실적 부진·업황 둔화·고평가·규제·심리 악화)는 노드 방향과 맞는 것만 붙여요.</li><li>종목별로 증권사마다 최신 노드 하나만 남겨 상향·하향·유지 수, 평균 목표가, 의견 엇갈림을 계산해요.</li>'
           '<li>코인은 전문가·기관 발언 기사를 강세·약세·혼조 노드로 나누고 근거(ETF 자금·금리·규제·기관 매수·거래소 유입 등)별로 묶어요.</li></ol></details>')
    sec = ''
    if C:
        sec += '<h2>🪙 코인 전망 종합</h2>' + ''.join(coin_card(c) for c in C if c['n'])
    if ups:
        sec += '<h2>🔺 목표가 상향이 많은 종목</h2>' + ''.join(stock_card(s) for s in ups)
    if dns:
        sec += '<h2>🔻 목표가 하향이 많은 종목</h2>' + ''.join(stock_card(s) for s in dns)
    if mix:
        sec += '<h2>⚖️ 증권사 의견이 엇갈린 종목</h2>' + ''.join(stock_card(s) for s in mix)
    rest = [s for s in S if s not in ups and s not in dns and s not in mix]
    if rest:
        sec += '<h2>📋 최근 리포트가 나온 종목</h2><ul class="an-all">' + ''.join(f'<li><a href="/analyst/s/{s["id"]}/">{E(s["name"])}<small>{"🔺" * min(3, s["up"])}{"🔻" * min(3, s["down"])}{"➖" * min(3, s["keep"])}</small></a></li>' for s in rest) + '</ul>'
    page('/analyst/', '루리의 애널리스트 분석 종합 — 증권사 목표가 상향·하향, 코인 전망 노드 분석',
         f'증권사 리포트 기사 속 목표가·투자의견을 노드로 쪼개 종목별로 다시 정리했어요. 상향 {sum(s["up"] for s in S)}건 · 하향 {sum(s["down"] for s in S)}건, 비트코인·이더리움 전망 강세·약세 근거까지.',
         '<p class="bc"><a href="/">홈</a> › 애널리스트 분석</p><h1>📊 루리의 애널리스트 분석 종합</h1>' + hero + AN_NOTE + sec + how + css, [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/')])
    urls = ['/analyst/']
    for s in S:
        page(f'/analyst/s/{s["id"]}/', f'{s["name"]} 목표가·투자의견 종합 — 증권사 {s["nb"]}곳 리포트 노드 분석',
             f'{s["name"]} 최근 30일 증권사 리포트: 상향 {s["up"]} · 유지 {s["keep"]} · 하향 {s["down"]}' + (f', 평균 목표가 {won_txt(s["tp_avg"])}' if s['tp_avg'] else '') + '. 상승·하락 근거별로 어느 증권사가 말했는지 정리.',
             f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">애널리스트 분석</a> › {E(s["name"])}</p><h1>📊 {E(s["name"])} 애널리스트 의견 종합</h1>' + AN_NOTE + stock_card(s, True) + '<p class="mg-nav"><a href="/analyst/">다른 종목 보기 →</a></p>' + css,
             [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/'), (s['name'], f'/analyst/s/{s["id"]}/')])
        urls.append(f'/analyst/s/{s["id"]}/')
    for c in C:
        if not c['n']:
            continue
        page(f'/analyst/coin/{c["sym"].lower()}/', f'{c["name"]}({c["sym"]}) 전망 종합 — 강세·약세 의견 노드 분석', f'{c["name"]} 최근 7일 전망 기사 {c["n"]}건: 강세 {c["bull"]} · 약세 {c["bear"]} · 혼조 {c["neutral"]}. 근거별 정리와 업비트 현재가.',
             f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">애널리스트 분석</a> › {E(c["name"])}</p><h1>🪙 {E(c["name"])} 전망 종합</h1>' + AN_NOTE + coin_card(c, True) + '<p class="mg-nav"><a href="/analyst/">다른 코인·종목 보기 →</a></p>' + css,
             [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/'), (c['name'], f'/analyst/coin/{c["sym"].lower()}/')])
        urls.append(f'/analyst/coin/{c["sym"].lower()}/')
    return urls


def analyst_top():
    d = _rd('analyst/data.json')
    if not d:
        return ''
    S, C = d.get('stocks', []), d.get('coins', [])
    li = ''
    for c in [c for c in C if c['n']][:2]:
        p = c.get('price') or {}
        li += f'<li><a href="/analyst/coin/{c["sym"].lower()}/"><em>🪙</em><b>{E(c["name"])}{(" " + format(p["p"], ",.0f") + "원") if p else ""}</b><span>🟢{c["bull"]} 🔴{c["bear"]}</span></a></li>'
    for s in sorted(S, key=lambda s: (-s['nb'], -s['last']))[:3]:
        li += f'<li><a href="/analyst/s/{s["id"]}/"><em>📈</em><b>{E(s["name"])}</b><span>🔺{s["up"]} 🔻{s["down"]}{(" · " + won_txt(s["tp_avg"])) if s["tp_avg"] else ""}</span></a></li>'
    return f'<section class="nw-home an-home"><h2>📊 애널리스트 분석 종합 <a href="/analyst/">전체 →</a></h2><ol>{li}</ol></section>' if li else ''


def talk_top():
    d = _rd('talk/data.json')
    li = ''.join(f'<li><a href="/talk/#t{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["nsite"]}곳 · 💬{x["nc"]:,}</span></a></li>' for i, x in enumerate(d.get('issues', [])[:3]))
    return f'<section class="nw-home tk-home"><h2>💬 지금 커뮤니티 이슈 <a href="/talk/">TOP30 →</a></h2><ol>{li}</ol></section>' if li else ''


SAT_DIR = r'C:\Users\k\Desktop\공모전_2026\풍자툰'


def satire_days():
    """풍자툰 폴더의 satire_MMDD.png(만평)·toon_MMDD.png(4컷)·cap_MMDD.txt → [(YYYY-MM-DD, {'imgs': [...], 'cap': [...]})], 최신 먼저."""
    if not os.path.isdir(SAT_DIR):
        return []
    days = {}
    for f in os.listdir(SAT_DIR):
        m = re.match(r'(satire|toon)_(\d{2})(\d{2})\.png$', f)
        if not m:
            continue
        y = TODAY.year if (int(m.group(2)), int(m.group(3))) <= (TODAY.month, TODAY.day) else TODAY.year - 1
        d = f'{y}-{m.group(2)}-{m.group(3)}'
        days.setdefault(d, {'imgs': [], 'mmdd': m.group(2) + m.group(3)})['imgs'].append((0 if m.group(1) == 'satire' else 1, f))
    out = []
    for d, v in days.items():
        v['imgs'] = [f for _, f in sorted(v['imgs'])]
        cp = os.path.join(SAT_DIR, f'cap_{v["mmdd"]}.txt')
        lines = []
        if os.path.exists(cp):
            for l in open(cp, encoding='utf-8-sig').read().splitlines():
                l = l.strip()
                if l and not l.startswith('#') and '프로필 링크' not in l and '캐릭터 이미지' not in l:
                    lines.append(l)
        v['cap'] = lines
        out.append((d, v))
    return sorted(out, reverse=True)


def satire_img(d, f):
    od = os.path.join(ROOT, 'satire', d)
    os.makedirs(od, exist_ok=True)
    src, dst = os.path.join(SAT_DIR, f), os.path.join(od, f[:-4] + '.webp')
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        from PIL import Image
        Image.open(src).convert('RGB').resize((864, 1080), Image.LANCZOS).save(dst, quality=84)
    return f'/satire/{d}/{f[:-4]}.webp'


def satire_pages():
    # 루리 풍자 (2026-10-18 사용자: "루리 풍자도 메인에 올리고 매일매일 하나씩 나오게 하고 이전꺼도 보게") — 원고·그림은 홍보 세션이 풍자툰 폴더에 매일 둔다
    days = satire_days()
    if not days:
        return []
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=9">'
    note = '<p class="note">풍자 만화예요. 특정 종목·인물을 비방하거나 투자를 권하려는 게 아니에요. 숫자는 그날 보도 기준이에요.</p>'
    urls = ['/satire/']
    def one(d, v, h='h2'):
        imgs = ''.join(f'<img src="{satire_img(d, f)}" width="864" height="1080" alt="{kdate(d)} 루리 풍자 {"만평" if f.startswith("satire") else "4컷"}" loading="lazy">' for f in v['imgs'])
        cap = ''.join(f'<p>{E(l)}</p>' for l in v['cap'])
        return f'<article class="st-d"><{h}>🎨 {kdate(d)} 루리 풍자</{h}><div class="st-imgs">{imgs}</div>{("<div class=st-cap>" + cap + "</div>") if cap else ""}</article>'
    arch = '<section class="tk-arch"><h2>📅 지난 풍자 모아 보기</h2><p>' + ''.join(f'<a href="/satire/{d}/">{kdate(d)}</a>' for d, _ in days[:90]) + '</p></section>'
    d0, v0 = days[0]
    title0 = (v0['cap'][0] if v0['cap'] else '오늘의 풍자')
    page('/satire/', '루리 풍자 — 매일 한 컷, 증시·뉴스 만평', f'루리가 매일 그리는 풍자 만화. 오늘: {title0}. 지난 풍자도 날짜별로 모아 봐요.',
         '<p class="bc"><a href="/">홈</a> › 루리 풍자</p><h1>🎨 루리 풍자</h1>' + one(d0, v0) + note + arch + css, [('루리의 줍줍', '/'), ('루리 풍자', '/satire/')])
    for i, (d, v) in enumerate(days):
        od = os.path.join(ROOT, 'satire', d)  # 원본이 빠진 그림(사용자가 뺀 컷)은 사이트에서도 지움
        keep = {f[:-4] + '.webp' for f in v['imgs']}
        for f in (os.listdir(od) if os.path.isdir(od) else []):
            if f.endswith('.webp') and f not in keep:
                os.remove(os.path.join(od, f))
        nav = ''
        if i + 1 < len(days):
            nav += f'<a href="/satire/{days[i + 1][0]}/">← {kdate(days[i + 1][0])}</a>'
        if i > 0:
            nav += f'<a href="/satire/{days[i - 1][0]}/">{kdate(days[i - 1][0])} →</a>'
        page(f'/satire/{d}/', f'{kdate(d)} 루리 풍자 — ' + (v['cap'][0] if v['cap'] else '증시·뉴스 만평'), f'{kdate(d)} 루리 풍자 만화. ' + ' '.join(v['cap'][:2])[:120],
             f'<p class="bc"><a href="/">홈</a> › <a href="/satire/">루리 풍자</a> › {kdate(d)}</p>' + one(d, v, 'h1') + f'<p class="st-nav">{nav}</p>' + note + arch + css,
             [('루리의 줍줍', '/'), ('루리 풍자', '/satire/'), (kdate(d), f'/satire/{d}/')])
        urls.append(f'/satire/{d}/')
    return urls


def satire_top():
    days = satire_days()
    if not days:
        return ''
    d, v = days[0]
    img = satire_img(d, v['imgs'][0])
    t = v['cap'][0] if v['cap'] else '오늘의 풍자'
    return (f'<section class="nw-home st-home"><h2>🎨 오늘의 루리 풍자 <a href="/satire/">지난 풍자 →</a></h2><a class="st-hm" href="/satire/{d}/"><img src="{img}" width="864" height="1080" alt="{E(t)}">'
            f'<span><b>{E(t)}</b>{E(" ".join(v["cap"][1:3]))[:90]}</span></a></section>')


def josa_ga(w):
    c = w[-1]
    return '이' if '가' <= c <= '힣' and (ord(c) - 0xAC00) % 28 else '가'


def kw_pages():
    # 인기 키워드 상세 (2026-10-18 사용자: 구글 등 인기 키워드로 블로그 + 사이트 상세 정보, 홍보 세션 연구 ⑂ 요청) — 매시 kw.py
    db = _rd('kw/db.json')
    ad = os.path.join(ROOT, 'kw', 'archive')
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True) if os.path.isdir(ad) else []
    if not db or not days:
        return []
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=9">'
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    note = '<p class="note">구글 트렌드 한국 급상승 검색어를 바탕으로 루리가 관련 보도와 사이트 정보를 모은 페이지예요. 연예인 사생활·사건사고·비방성 키워드는 다루지 않아요.</p>'
    urls = ['/kw/']
    kd = os.path.join(ROOT, 'kw')  # 제외된 키워드 페이지는 지움
    for f in os.listdir(kd):
        if os.path.isdir(os.path.join(kd, f)) and f != 'archive' and not re.match(r'\d{4}-\d{2}-\d{2}$', f) and f not in db:
            shutil.rmtree(os.path.join(kd, f), ignore_errors=True)
    SRCB = lambda r: ('<span class="kw-b both">구글+네이버 동시</span>' if len(r.get('src') or []) > 1 else '<span class="kw-b n">실시간 검색어</span>' if (r.get('src') or ['google']) == ['naver'] else '<span class="kw-b g">구글 트렌드</span>')
    for sl, r in db.items():
        k = r['k']
        lines = [f'「{E(k)}」{josa_ga(k)} {kdate(r["days"][-1])} ' + ('구글 급상승과 실시간 검색어에 동시에' if len(r.get('src') or []) > 1 else '실시간 검색어에' if (r.get('src') or ['google']) == ['naver'] else '구글 검색 급상승 키워드에') + f' 올랐어요({E(r.get("traffic") or "-")}).']
        if r.get('srcs'):
            lines.append(f'관련 보도는 {len(r["srcs"])}곳({E(", ".join(r["srcs"][:5]))}{" 등" if len(r["srcs"]) > 5 else ""})에서 나왔어요.')
        if r.get('issue'):
            x = r['issue']
            lines.append(f'루리 이슈 감별에서는 언론사 {x["on"]}곳이 보도한 이슈로 묶였고, 확인 신호 점수는 {G.get(x.get("g"), "")} {x.get("s") if x.get("s") is not None else "-"}점이에요.')
        if len(r['days']) > 1:
            lines.append(f'최근 {len(r["days"])}일 동안 급상승에 올랐어요({", ".join(d[5:].replace("-", "/") for d in r["days"][-5:])}).')
        why = ''.join(f'<li><a href="{E(n["u"])}" target="_blank" rel="noopener nofollow"><em>{E(n["o"])}</em>{E(n["t"])}</a></li>' for n in r.get('news', []))
        ours = ''.join(f'<li><a href="{E(a["u"])}" target="_blank" rel="noopener nofollow"><em>{E(a["o"])} {G.get(a.get("g"), "")} {a["s"] if a.get("s") is not None else ""}</em>{E(a["t"])}</a></li>' for a in r.get('ours', []))
        links = []
        if r.get('issue'):
            links.append(f'<a href="/news/#is{r["issue"]["n"]}"><em>🕵️ 이슈 감별</em><b>{E(r["issue"]["t"])}</b></a>')
        links += [f'<a href="/talk/#t{x["n"]}"><em>💬 커뮤니티</em><b>{E(x["t"])}</b></a>' for x in r.get('talk', [])]
        links += [f'<a href="/analyst/s/{x["id"]}/"><em>📊 애널리스트</em><b>{E(x["name"])} 목표가 의견</b></a>' for x in r.get('stocks', [])]
        links += [f'<a href="/analyst/coin/{x["sym"].lower()}/"><em>🪙 코인</em><b>{E(x["name"])} 전망 종합</b></a>' for x in r.get('coins', [])]
        links += [f'<a href="{E(p_["u"])}"><em>{E(p_["k"])}</em><b>{E(p_["t"])}</b></a>' for p_ in r.get('pr', [])]
        trs = r.get('trend') or []
        if len(trs) >= 5:
            W_, H_ = 600, 140; mx = max(v for _, v in trs) or 1
            pts = ' '.join(f'{10 + (W_ - 20) * i / (len(trs) - 1):.1f},{H_ - 22 - (H_ - 40) * v / mx:.1f}' for i, (_, v) in enumerate(trs))
            trend_html = (f'<section class="mg-s"><h2>📈 최근 30일 네이버 검색량 추이</h2><figure class="an-ch"><svg viewBox="0 0 {W_} {H_}" role="img" aria-label="{E(k)} 검색량 추이">'
                          f'<polyline points="{pts}" fill="none" stroke="#16a34a" stroke-width="3"/><text x="10" y="{H_ - 4}">{trs[0][0][5:]}</text><text x="{W_ - 10}" y="{H_ - 4}" text-anchor="end">{trs[-1][0][5:]}</text></svg>'
                          '<figcaption>네이버 데이터랩 검색어 트렌드(기간 중 최댓값 = 100인 상대값)</figcaption></figure></section>')
        else:
            trend_html = ''
        post = f'<section class="mg-s"><h2>✍️ 루리의 정리 글</h2><div class="nw-pr"><a href="{E(r["post"])}" target="_blank" rel="noopener"><em>블로그</em><b>{E(k)} 자세히 정리한 글 보기</b></a></div></section>' if r.get('post') else ''
        css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=9"><link rel="stylesheet" href="/assets/analyst/analyst.css?v=4">'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/kw/">인기 키워드</a> › {E(k)}</p><h1>🔎 {E(k)} — 왜 검색이 늘었나</h1><p>{SRCB(r)}</p>'
                + say('o_det_think', ' '.join(lines)) + trend_html + post
                + (f'<section class="mg-s"><h2>📰 왜 떴나: 관련 보도</h2><ul class="kw-l">{why}</ul></section>' if why else '')
                + (f'<section class="mg-s"><h2>🕵️ 루리가 채점한 관련 기사</h2><ul class="kw-l">{ours}</ul></section>' if ours else '')
                + (f'<section class="mg-s"><h2>📌 루리의 줍줍에서 더 보기</h2><div class="nw-pr">{"".join(links)}</div></section>' if links else '')
                + f'<p class="mg-nav"><a href="/kw/">오늘의 인기 키워드 전체 →</a> · <a href="/mag/">매거진 →</a></p>' + note + css)
        page(f'/kw/{sl}/', f'{k} 검색 급상승 이유 — 관련 보도·정리', f'{k}{josa_ga(k)} 검색 급상승 키워드에 오른 이유: ' + ' / '.join(n['t'] for n in r.get('news', [])[:2])[:140], body,
             [('루리의 줍줍', '/'), ('인기 키워드', '/kw/'), (k, f'/kw/{sl}/')])
        urls.append(f'/kw/{sl}/')
    arch = '<section class="tk-arch"><h2>📅 날짜별 인기 키워드</h2><p>' + ''.join(f'<a href="/kw/{d}/">{kdate(d)}</a>' for d in days[:90]) + '</p></section>'
    for i, d in enumerate(days):
        L = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        li = ''.join(f'<li><a href="/kw/{x["slug"]}/"><em>{j + 1}</em><b>{E(x["k"])}</b><span>{SRCB(x)} {E(x.get("traffic") or "-")} · {E(x.get("first", ""))} 첫 등장</span></a></li>' for j, x in enumerate([y for y in L if y['slug'] in db]))
        bd = f'<ol class="mg-l">{li}</ol>' + arch + note + css
        if i == 0:
            page('/kw/', '오늘의 인기 키워드 — 검색 급상승 이유 정리', f'{kdate(d)} 구글 검색 급상승 키워드와 왜 떴는지: ' + ', '.join(x['k'] for x in L[:6]),
                 f'<p class="bc"><a href="/">홈</a> › 인기 키워드</p><h1>🔎 오늘의 인기 키워드</h1>' + say('o_det_wave', '지금 검색이 확 늘어난 키워드를 모아, 왜 떴는지 관련 보도와 함께 정리했어요.') + bd,
                 [('루리의 줍줍', '/'), ('인기 키워드', '/kw/')])
        page(f'/kw/{d}/', f'{kdate(d)} 인기 키워드 — 검색 급상승 정리', f'{kdate(d)} 구글 검색 급상승 키워드: ' + ', '.join(x['k'] for x in L[:8]),
             f'<p class="bc"><a href="/">홈</a> › <a href="/kw/">인기 키워드</a> › {kdate(d)}</p><h1>🔎 {kdate(d)} 인기 키워드</h1>' + bd, [('루리의 줍줍', '/'), ('인기 키워드', '/kw/'), (kdate(d), f'/kw/{d}/')])
        urls.append(f'/kw/{d}/')
    return urls


def ailog_page(live, nurls):
    # AI 제작 로그 (2026-10-18 사용자: "AI로 이 사이트 어케 만들었는지 다 공개", "홍보 마케팅은 기밀, 사이트 쪽만", "핵심은 비용 0원으로 그럴듯한 운영")
    a = json.load(open(os.path.join(HERE, 'ailog.json'), encoding='utf-8'))
    first = a.get('start', '2026-10-17')   # 2026-10-18 사용자: "2일이야" — 루리의 줍줍 제작 시작일 기준
    try:
        commits = int(subprocess.run(['git', 'rev-list', '--count', f'--since={first}T00:00', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() or 0)
    except Exception:
        commits = 0
    npage = sum(1 for _r, _d, fs in os.walk(ROOT) if 'index.html' in fs and '.git' not in _r)
    days = (TODAY - datetime.date.fromisoformat(first)).days + 1
    stat = [('제작 기간', f'{days}일', f'{first[5:].replace("-", "/")} 시작'), ('코드 변경(커밋)', f'{commits:,}번', 'AI가 고치고 올린 횟수'),
            ('페이지', f'{npage:,}개', '매시간 다시 만들어요'), ('진행 중 공모전', f'{len(live):,}건', '상세 페이지 자동 생성'),
            ('매시간 자동 작업', '6가지', '뉴스·커뮤니티·애널리스트·키워드·빌드·배포'), ('서버·API 비용', '0원', '무료 한도 + 내 PC')]
    st = ''.join(f'<div><small>{E(k)}</small><b>{E(v)}</b><span>{E(d)}</span></div>' for k, v, d in stat)
    cost = ''.join(f'<tr><td>{E(x)}</td><td>{E(y)}</td><td><b>{E(z)}</b></td></tr>' for x, y, z in a['costs'])
    arch = ''.join(f'<li><b>{E(x)}</b><span>{E(y)}</span></li>' for x, y in a['arch'])
    chat = ''.join(f'<li><p class="al-u">🙋 {E(u)}</p><p class="al-a">🤖 {E(r)}</p></li>' for u, r in a['chat'])
    fixes = ''.join(f'<li><b>❌ {E(x)}</b><span>✅ {E(y)}</span></li>' for x, y in a['fixes'])
    rules = ''.join(f'<li>{E(x)}</li>' for x in a['rules'])
    tl = ''.join(f'<li><em>{E(d)}</em><span>{E(t)}</span></li>' for d, t in a['timeline'])
    body = (f'<p class="bc"><a href="/">홈</a> › AI 제작 로그</p><h1>🤖 AI 제작 로그 — 서버비 0원으로 이 사이트를 만든 방법</h1>'
            + say('o_desk', E(a['lead']))
            + f'<div class="al-st">{st}</div>'
            + f'<section class="mg-s"><h2>💸 비용표: 어디에 얼마 드나</h2><table class="al-t"><tr><th>무엇</th><th>쓰는 것</th><th>비용</th></tr>{cost}</table><p class="note">{E(a["cost_note"])}</p></section>'
            + f'<section class="mg-s"><h2>🧩 구조: 매시간 이렇게 돌아가요</h2><ol class="al-ar">{arch}</ol></section>'
            + f'<section class="mg-s"><h2>💬 사람이 한 말 → AI가 만든 것</h2><p class="note">실제 지시를 그대로 옮겼어요. 사람은 방향만 말하고, 코드·디자인·배포·검사는 AI가 했어요.</p><ul class="al-c">{chat}</ul></section>'
            + f'<section class="mg-s"><h2>🛠️ AI가 틀린 것과 고친 것</h2><ul class="al-f">{fixes}</ul></section>'
            + f'<section class="mg-s"><h2>📏 지킨 원칙</h2><ul class="al-r">{rules}</ul></section>'
            + f'<section class="mg-s"><h2>🗓️ 날짜별 기록</h2><ul class="al-tl">{tl}</ul></section>'
            + '<p class="note">이 페이지는 사이트 개발 과정만 공개해요. 숫자는 빌드할 때마다 자동으로 갱신돼요.</p><link rel="stylesheet" href="/assets/mag/mag.css?v=9">')
    page('/ailog/', 'AI 제작 로그 — 서버비 0원으로 정보 사이트 만들기(Claude Code)',
         f'사람 한 명의 말과 AI(Claude Code)로 {days}일 동안 페이지 {npage:,}개짜리 정보 사이트를 만든 기록. 무료 호스팅·무료 서버리스·공개 RSS로 서버비 0원, 매시간 자동 갱신.',
         body, [('루리의 줍줍', '/'), ('AI 제작 로그', '/ailog/')])
    return ['/ailog/']


def all_page():
    # 전체 메뉴 (2026-10-18 홈 단순화로 빠진 기능 모음)
    G = [('🕵️ 이슈', [('/news/', '이슈 감별', '언론사 기사 묶음·팩트 채점'), ('/talk/', '커뮤니티 이슈', '여러 커뮤니티에 동시에 뜬 화제'), ('/kw/', '인기 키워드', '검색 급상승 이유'),
                       ('/satire/', '루리 풍자', '매일 한 컷 만평'), ('/mag/', '데일리 매거진', '이슈 리딩·하루 정보 한 장')]),
         ('📊 투자 정보', [('/analyst/', '애널리스트 분석', '목표가 상향·하향 노드 트리'), ('/analyst/coin/btc/', '코인 전망', '비트코인·이더리움 강세·약세')]),
         ('🏆 공모전', [('/', '공모전 추천 상담', '질문 몇 개로 딱 맞는 공모전'), ('/cat/literature/', '분야별 공모전', '문학·아이디어·디자인·영상·IT·요리'), ('/prep/', '준비실', '마감 역산 일정·체크리스트·꿀팁'),
                       ('/lab/', '수상 연구소', '수상작 분석·당선 공식'), ('/community/', '원정대', '같이 나갈 팀 모으기'), ('/guide/', '응모 가이드', '공모전 처음이라면')]),
         ('💰 생활 정보', [('/apply/', '지원금·청약', '청년 지원금·청약 일정'), ('/event/', '경품 이벤트', '응모만 하면 되는 이벤트'), ('/fridge/', '냉장고 파먹기', '있는 재료로 오늘 메뉴'), ('/qa/', '고민 해결', '실제 고민에 답 정리')]),
         ('⚙️ 더 보기', [('/app/', '앱·알림', '홈 화면 설치·폰 알림'), ('/me/', '내 공간', '찜·응모 기록'), ('/ailog/', 'AI 제작 로그', '이 사이트를 만든 방법')])]
    body = '<p class="bc"><a href="/">홈</a> › 전체 메뉴</p><h1>☰ 루리의 줍줍 전체 메뉴</h1>' + ''.join(
        f'<section class="mg-s"><h2>{E(g)}</h2><ul class="al-menu">' + ''.join(f'<li><a href="{u}"><b>{E(n)}</b><span>{E(d)}</span></a></li>' for u, n, d in items) + '</ul></section>' for g, items in G) + '<link rel="stylesheet" href="/assets/mag/mag.css?v=9">'
    page('/all/', '전체 메뉴', '루리의 줍줍 전체 메뉴: 이슈 감별, 커뮤니티 이슈, 인기 키워드, 풍자, 매거진, 애널리스트 분석, 공모전, 지원금·청약, 경품, 냉장고 파먹기, 앱·알림.', body, [('루리의 줍줍', '/'), ('전체 메뉴', '/all/')])
    return ['/all/']


MONEY_NOTE = ('<p class="an-warn">📊 공개된 기사·공식 자료를 정리한 일반 정보예요. 루리의 줍줍이 특정 종목·상품을 권하거나 수익을 약속하지 않아요. '
              '개인 상황에 따라 맞는 답이 다르고, 투자 판단과 책임은 본인에게 있어요.</p>')
ECOL = {'bull': ('🟢', '긍정'), 'bear': ('🔴', '신중'), 'neutral': ('⚪', '중립')}


def exp_li(n):
    dt = datetime.datetime.fromtimestamp(n['ts']).strftime('%m/%d')
    return (f'<li class="{n["dir"]}"><span class="an-d">{ECOL[n["dir"]][0]}</span><div><small>{dt} · {E(n["who"])} · {E(n["cat"])}</small>'
            f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["t"])}</a><em>{E(n["o"])}</em></div></li>')


def experts_html(ex, cats=None, limit=None):
    out = ''
    for e in ex[:limit]:
        ns = [n for n in e['nodes'] if not cats or n['cat'] in cats]
        if not ns:
            continue
        if e['mixed']:
            b = [n for n in ns if n['dir'] == 'bull'][:4]
            r = [n for n in ns if n['dir'] == 'bear'][:4]
            body = (f'<div class="ex-vs"><div><p>🟢 긍정적으로 본 쪽</p><ul class="an-nodes">{"".join(exp_li(n) for n in b)}</ul></div>'
                    f'<div><p>🔴 신중하게 본 쪽</p><ul class="an-nodes">{"".join(exp_li(n) for n in r)}</ul></div></div>')
        else:
            body = f'<ul class="an-nodes">{"".join(exp_li(n) for n in ns[:6])}</ul>'
        cc = ' · '.join(f'{k} {v}' for k, v in e['cats'].items() if v)
        out += (f'<article class="an-c"><div class="an-h"><h3>{E(e["topic"])}</h3>{"<span class=an-mix>⚖️ 의견 엇갈림</span>" if e["mixed"] else ""}</div>'
                f'<p class="an-st">최근 14일 전문가 발언 {e["n"]}건 · 🟢 {e["bull"]} · 🔴 {e["bear"]} · {E(cc)}</p>{body}</article>')
    return out


def money_pages():
    # 머니 테마 정보 섹션 (2026-10-18 사용자: "주식 관련해서도 정책 등, 나이별 포트폴리오 전략 등을 넣고 전문가들 이야기도 넣어서" — 연구 ⑂ 기획)
    an = _rd('analyst/data.json')
    ex = an.get('experts', [])
    css = '<link rel="stylesheet" href="/assets/analyst/analyst.css?v=4"><link rel="stylesheet" href="/assets/mag/mag.css?v=9">'
    urls = []
    how = ('<details class="an-how"><summary>어떻게 모았나요?</summary><ol><li>증권·경제 기사 RSS에서 리서치센터장·CIO·이코노미스트·한국은행·KDI·IMF·월가 기관 등 실명 기관·인물의 발언이 제목에 나온 기사만 골라요.</li>'
           '<li>주제(코스피·미국 증시·금리·환율·반도체·부동산·경기·코인·원자재)와 성격(시장 전망·자산배분 조언·리스크 경고)으로 나눠요.</li><li>발언(따옴표) 부분으로 긍정·신중을 가려, 같은 주제에서 둘 다 있으면 나란히 보여 줘요.</li>'
           '<li>기사 본문은 옮기지 않고 제목(발언 요지)과 원문 링크만 실어요.</li></ol></details>')
    page('/money/experts/', '전문가 코멘트 종합 — 리서치센터장·CIO·한은·IMF 시장 전망 비교',
         '증권사 리서치센터장, 운용사 CIO, 한국은행·KDI·IMF 등 실명 전문가 발언을 주제별로 모으고, 같은 주제에서 의견이 엇갈리면 나란히 비교했어요.',
         '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 전문가 코멘트</p><h1>🎙️ 전문가 코멘트 종합</h1>' + MONEY_NOTE
         + (experts_html(ex) or '<p class="nw-empty">아직 모인 발언이 없어요. 매시간 새로 모아요.</p>') + how + css,
         [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('전문가 코멘트', '/money/experts/')])
    urls.append('/money/experts/')
    a = json.load(open(os.path.join(HERE, 'money_age.json'), encoding='utf-8'))
    common = ''.join(f'<li><b>{E(k)}</b><span>{E(v)}</span></li>' for k, v in a['common'])
    rule = f'<section class="mg-s"><h2>📏 {E(a["rule"]["title"])}</h2><p>{E(a["rule"]["body"])}</p><ul class="al-r">{"".join(f"<li>{E(x)}</li>" for x in a["rule"]["limits"])}</ul></section>'
    ages = ''.join(f'<section class="mg-s ag-{x["k"]}" id="{x["k"]}"><h2>{E(x["t"])} <small>— {E(x["focus"])}</small></h2><ul class="ag-l">{"".join(f"<li>{E(i)}</li>" for i in x["items"])}</ul></section>' for x in a['ages'])
    jump = ''.join(f'<a href="#{x["k"]}">{E(x["t"].split(" · ")[0])}</a>' for x in a['ages'])
    adv = experts_html(ex, cats=('자산배분 조언', '리스크 경고'), limit=4)
    page('/money/age/', '나이별 자산관리 일반 원칙 — 20대부터 은퇴 후까지',
         '20대 사회초년생, 30대 결혼·내 집 마련, 40대, 50대 은퇴 준비, 60대 이상 인출기까지 흔히 쓰이는 자산관리 원칙: 비상금, 세제 혜택 계좌 순서, 100−나이 규칙과 한계, 분산·리밸런싱.',
         '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 나이별 원칙</p><h1>🧭 나이별 자산관리 일반 원칙</h1>'
         + f'<p class="an-warn">⚠️ {E(a["note"])}</p><p class="hm-links">{jump}<a href="/money/policy/">투자 정책 정리 →</a></p>'
         + f'<section class="mg-s"><h2>🧱 나이와 상관없는 공통 원칙</h2><ul class="ag-c">{common}</ul></section>' + rule + ages
         + (f'<h2>🎙️ 요즘 전문가들의 자산배분·리스크 이야기</h2>{adv}' if adv else '') + css,
         [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('나이별 원칙', '/money/age/')])
    urls.append('/money/age/')
    pol = os.path.join(HERE, 'money_policy.json')
    if os.path.exists(pol):
        P = json.load(open(pol, encoding='utf-8'))
        secs = ''
        for it in P.get('items', []):
            rows = ''.join(f'<tr><th>{E(r[0])}</th><td>{E(r[1])}</td></tr>' for r in it.get('rows', []) if len(r) >= 2)
            src = ''.join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">{E(x["title"])}</a>{(" · " + E(x["date"])) if x.get("date") else ""}</li>' for x in it.get('sources', []))
            ver = '' if it.get('verified', True) else '<p class="an-warn">🔎 공식 자료를 찾지 못해 보도 기준으로 정리했어요. 가입 전 공식 안내를 꼭 확인하세요.</p>'
            secs += (f'<section class="mg-s" id="{E(it["key"])}"><h2>{E(it["name"])}</h2>{ver}<table class="pl-t">{rows}</table>'
                     + (f'<p class="pl-ch">🆕 {E(it["changes"])}</p>' if it.get('changes') else '') + (f'<details class="pl-src"><summary>출처</summary><ul>{src}</ul></details>' if src else '') + '</section>')
        jump = ''.join(f'<a href="#{E(it["key"])}">{E(it["name"].split("(")[0])}</a>' for it in P.get('items', []))
        rel = experts_html([e for e in ex if e['topic'] in ('금리', '코스피·국내 증시', '경기·성장률')], limit=2)
        page('/money/policy/', '투자 관련 정책·제도 정리 — ISA·연금저축·IRP·청년도약계좌·공모주·세제·공매도',
             'ISA, 연금저축·IRP 세액공제, 청년도약계좌, 공모주 청약 배정, 금투세·배당소득 과세, 공매도 제도를 공식 자료 기준으로 표로 정리했어요(기준일·출처 표시).',
             '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 투자 정책</p><h1>🏛️ 투자 관련 정책·제도 정리</h1>' + MONEY_NOTE
             + f'<p class="pl-asof">기준일 {E(P.get("asof", ""))} · 금융위원회·기획재정부·국세청 등 공식 자료 기준. 제도는 바뀔 수 있으니 가입 전 공식 안내를 확인하세요.</p><p class="hm-links">{jump}</p>'
             + secs + '<p class="hm-links"><a href="/apply/">💰 지원금·청약 데이터 보기</a><a href="/money/age/">🧭 나이별 원칙</a></p>' + (f'<h2>🎙️ 관련 전문가 코멘트</h2>{rel}' if rel else '') + css,
             [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('투자 정책', '/money/policy/')])
        urls.append('/money/policy/')
    return urls


def apply_rec_page():
    # 루리의 청약 추천 (2026-10-18 사용자: "청약 추천도 만들어") — 생활 테마
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/apply/">생활</a> › 청약 추천</p><h1>🏠 루리의 청약 추천</h1>'
            + say('o_cardigan', '내 상황을 고르면 청약 가점이랑 노려볼 만한 공급 유형, 지금 접수 중인 공고 중 맞는 걸 골라 드려요. 입력한 내용은 이 폰에만 저장돼요.')
            + '<section id="aprec" aria-label="청약 추천"><noscript>자바스크립트가 필요해요.</noscript></section>'
            + '<p class="note">청약 가점은 대략 계산이며, 특별공급 자격(소득·자산·거주 기간 등)은 단지마다 달라요. 신청 전 공고문과 청약홈에서 꼭 확인하세요.</p>'
            + '<link rel="stylesheet" href="/assets/apply/rec.css?v=1"><script defer src="/assets/apply/rec.js?v=1"></script>')
    page('/apply/recommend/', '청약 추천 — 내 가점·노려볼 공급 유형·지금 접수 중인 공고', '지역·나이·결혼·자녀·무주택 기간·부양가족·통장 기간을 고르면 청약 가점(84점)과 신혼·생애최초·다자녀·청년·공공임대 등 노려볼 공급 유형, 지금 접수 중인 공고를 골라 드려요.',
         body, [('루리의 줍줍', '/'), ('생활', '/apply/'), ('청약 추천', '/apply/recommend/')])
    return ['/apply/recommend/']


def news_top():
    # 홈 투트랙(2026-10-18 사용자: 공모전과 투트랙) — 이슈 감별 상위 3개
    try:
        d = json.load(open(os.path.join(ROOT, 'news', 'data.json'), encoding='utf-8'))
    except Exception:
        return ''
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    li = ''.join(f'<li><a href="/news/#is{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{G.get("bad" if x.get("cf") else x.get("g"), "")} {x["s"] if x.get("s") is not None else ""}점 · {x["on"]}곳</span></a></li>' for i, x in enumerate([y for y in d.get('issues', []) if y.get('c') == '정치'][:3] or d.get('issues', [])[:3]))
    return f'<section class="nw-home"><h2>🕵️ 오늘의 정치 이슈 감별 <a href="/news/">이슈 순위 전체 →</a></h2><ol>{li}</ol></section>' if li else ''


def news_page():
    # 루리 탐정의 이슈 감별 (2026-10-18 사용자: RSS 기사 수집 → 주제별 묶음 → 팩트체크 기반 채점, 피드, 탐정 루리, 기사 관련 줍줍)
    body = f'''<p class="bc"><a href="/">홈</a> › 이슈 감별</p><h1>🕵️ 루리 탐정의 이슈 감별</h1>
<section id="news" aria-label="이슈 순위와 기사 채점"><noscript>자바스크립트가 필요해요.</noscript></section>
<details class="nw-how"><summary>채점은 이렇게 해요</summary><ul><li><b>교차 보도</b> — 같은 사건을 여러 언론사가 보도하면 가점, 한 곳뿐이면 표시만 해요.</li><li><b>출처</b> — 실명 기관·인물 출처는 가점, 익명 관계자뿐이거나 온라인 커뮤니티·SNS 글이 출처면 감점.</li><li><b>제목-본문 일치</b> — 제목의 숫자·인용문이 본문에 없으면 감점.</li><li><b>숫자 엇갈림</b> — 같은 사건인데 언론사마다 사망·부상자 수가 다르면 따로 표시해요.</li><li><b>낚시·홍보</b> — 「충격」「결국」「이것」 같은 낚시 표현, 기업 홍보성 기사는 감점.</li></ul><p>기사 본문은 채점에만 쓰고 이 사이트에 옮겨 싣지 않아요. 제목을 누르면 원래 언론사 기사로 이동해요.</p></details>
<link rel="stylesheet" href="/assets/news/news.css?v=3"><script defer src="/assets/news/news.js?v=3"></script>'''
    page('/news/', '루리 탐정의 이슈 감별 — 오늘의 이슈 순위·기사 팩트 채점', '언론사 15곳 기사를 매시간 모아 같은 사건끼리 묶고, 교차 보도·출처·제목-본문 일치·숫자 엇갈림·낚시 표현으로 기사마다 점수를 매겨요. 지금 가장 많이 보도된 이슈 순위.',
         body, [('루리의 줍줍', '/'), ('이슈 감별', '/news/')])


def app_page():
    # 루리의 줍줍 앱(PWA) 설치 + 공모전 알림 (2026-10-18 사용자: 앱도 사이트 안에서 배포, 공모전 알림, 웹푸시, 메일)
    cats = json.dumps([[sl, n, CAT_ICON.get(n, '🧩')] for sl, n in CATS], ensure_ascii=False)
    faq = [('앱은 어디서 받아요?', '이 페이지에서 바로 설치돼요. 플레이스토어·앱스토어를 거치지 않는 웹앱이라 용량이 거의 없고, 늘 최신 공모전이 보여요.'),
           ('알림은 얼마나 자주 와요?', '하루 최대 2번이에요. 저녁 7시쯤 관심 분야 새 공모전을 한 번에 모아서, 아침 9시쯤 인기 공모전 마감 3일 전 소식을 보내요. 새 공모전이 없는 날은 안 와요.'),
           ('가입해야 해요?', '폰 알림은 가입 없이 바로 켤 수 있어요. 찜한 공모전 마감 메일은 회원만 받을 수 있어요.'),
           ('아이폰도 돼요?', 'iOS 16.4 이상 사파리에서 홈 화면에 추가한 뒤, 홈 화면의 루리의 줍줍 앱을 열어 알림을 켜면 돼요.'),
           ('알림을 끄고 싶어요.', '이 페이지에서 「알림 끄기」를 누르거나, 폰 설정 → 알림에서 루리의 줍줍(또는 sungprofile.cloud)을 끄면 돼요.')]
    body = f'''<p class="bc"><a href="/">홈</a> › 앱·알림</p><h1>📲 루리의 줍줍 앱 · 공모전 알림</h1>
{say("o_present", "홈 화면에 앱을 깔고 관심 분야만 골라 두면, 새 공모전이랑 마감 임박을 제가 폰으로 알려 드릴게요!")}
<section id="app-page" data-cats='{E(cats)}'>
<div class="ap-hero"><img src="/assets/icons/icon-192.png" alt="루리의 줍줍 앱 아이콘" width="72" height="72"><div><b>루리의 줍줍</b><span>공모전·청약·지원금·경품 이벤트 · 무료 · 광고 클릭 강요 없음</span></div></div>
<h2>1. 앱 설치</h2><div class="ap-card ap-inst"><p class="ap-sm">불러오는 중…</p></div>
<h2>2. 공모전 폰 알림 (웹푸시)</h2><div class="ap-card ap-push"><p class="ap-sm">불러오는 중…</p></div>
<h2>3. 메일 알림</h2><div class="ap-card ap-mail"><p class="ap-sm">불러오는 중…</p></div>
<h2>자주 묻는 질문</h2><div class="ap-card ap-faq">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in faq)}</div>
</section><p class="note">알림을 켜면 브라우저가 만든 알림 주소와 고른 분야만 저장해요. 이름·전화번호는 받지 않아요. 알림을 끄면 바로 지워져요.</p>
<link rel="stylesheet" href="/assets/app/app.css?v=1">'''
    page('/app/', '루리의 줍줍 앱 설치 · 공모전 알림 받기', '루리의 줍줍 앱을 홈 화면에 설치하고, 관심 분야 새 공모전과 마감 임박 소식을 폰 알림(웹푸시)·메일로 받아 보세요. 무료, 가입 없이 폰 알림 가능.',
         body, [('루리의 줍줍', '/'), ('앱·알림', '/app/')])


def fridge_page():
    # 루리의 냉장고 파먹기 (2026-10-18 사용자: 냉장고 사진 찍어서 오늘 메뉴 추천, Claude API)
    page('/fridge/', '루리의 냉장고 파먹기 — 있는 재료로 오늘 메뉴 추천', '냉장고에 있는 재료만 고르면 집밥 레시피 77개 중 지금 바로 만들 수 있는 오늘 메뉴와 만드는 법, 하나만 사면 되는 메뉴까지 알려 줘요.',
         f'''<p class="bc"><a href="/">홈</a> › 냉장고 파먹기</p><h1>🍳 루리의 냉장고 파먹기</h1>
{say("o_cook", "냉장고 사진을 찍거나 있는 재료를 눌러 주세요. 집밥 레시피 77개 중에 지금 바로 만들 수 있는 걸 골라 드릴게요!")}
<section id="fridge" aria-label="냉장고 재료로 메뉴 추천"><noscript>자바스크립트가 필요해요.</noscript></section>
<a class="lab-cta" href="/cat/food/"><b>🏆 요리·레시피 공모전</b><span>레시피 공모전·요리경연대회 모아 보기 · 상금 받고 요리 실력 뽐내기 →</span></a><p class="note">사진은 재료를 찾는 데만 쓰고 저장하지 않아요. 고른 재료는 이 폰에만 저장돼요. 알레르기가 있으면 재료를 꼭 다시 확인해 주세요.</p>
<link rel="stylesheet" href="/assets/fridge/fridge.css?v=4"><script defer src="/assets/fridge/fridge.js?v=4"></script>''', [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/')])


def qa_card(q):
    return f'<li><a class="card" data-c="guide" href="/guide/{q["slug"]}/"><span class="ic">{q["icon"]}</span><div class="cb"><h3 class="t">{E(q["title"])}</h3><p class="o">{(E(q["tag"]) + " · ") if q["tag"] else ""}{E(q["desc"])}</p></div></a></li>'


def qa_home():
    if not QA: return ''
    return f'<section class="qa-home"><h2>💬 루리의 고민 해결 <a href="/qa/">전체 {len(QA)}편 →</a></h2><ul class="list">{"".join(qa_card(q) for q in QA[:4])}</ul></section>'


def qa_pages(live):
    page('/qa/', '루리의 고민 해결', '청년 지원금, 진로, 공모전 준비까지 실제로 받은 고민에 루리가 답을 정리했어요.',
         f'<p class="bc"><a href="/">홈</a> › 고민 해결</p><section class="dh" data-c="guide"><span class="ic big">💬</span><h1>루리의 고민 해결</h1></section>{say("o_cardigan", "실제로 받은 고민에 하나씩 답을 정리했어요. 비슷한 고민이면 골라 읽어 보세요!")}<ul class="list">{"".join(qa_card(q) for q in QA)}</ul>',
         [('루리의 줍줍', '/'), ('고민 해결', '/qa/')])
    rel = ''.join(card(c) for c in live[:4])
    for i, q in enumerate(QA):
        page(f'/guide/{q["slug"]}/', q['title'], q['desc'], f'<p class="bc"><a href="/">홈</a> › <a href="/qa/">고민 해결</a></p><article><h1>{E(q["title"])}</h1>{say(["o_suit", "o_cardigan", "o_desk", "o_present"][i % 4], E(q["desc"]))}{q["body"]}</article><p class="qa-more"><a href="/qa/">💬 다른 고민 보기</a> · <a href="/">🎯 루리에게 추천 상담 받기</a></p><h2>마감 임박 공모전</h2><ul class="list">{rel}</ul>',
             [('루리의 줍줍', '/'), ('고민 해결', '/qa/'), (q['title'], f'/guide/{q["slug"]}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': q['title'], 'description': q['desc'], 'datePublished': '2026-10-17',
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})


def guides(live):
    li = ''.join(f'<li><a class="card" data-c="guide" href="/guide/{s}/"><span class="ic">📖</span><div class="cb"><h3 class="t">{E(t)}</h3><p class="o">{E(d)}</p></div></a></li>' for s, t, d, _ in GUIDES)
    page('/guide/', '공모전 응모 가이드', '공모전 처음 응모하는 법, 제안서 쓰는 법, 수기·문학 공모 요령, 상금 수령과 사칭 주의까지.',
         f'<p class="bc"><a href="/">홈</a> › 응모 가이드</p><section class="dh" data-c="guide"><span class="ic big">📖</span><h1>공모전 응모 가이드</h1></section>{say("o_vest", "처음 응모한다면 1번부터 차근차근 읽어 보세요. 실수로 탈락하는 일이 확 줄어요!")}<ul class="list">{li}</ul>', [('루리의 줍줍', '/'), ('응모 가이드', '/guide/')])
    rel = ''.join(card(c) for c in live[:4])
    for s, t, d, b in GUIDES:
        page(f'/guide/{s}/', t, d, f'<p class="bc"><a href="/">홈</a> › <a href="/guide/">응모 가이드</a></p><article><h1>{E(t)}</h1>{say(["o_suit", "o_cardigan", "o_desk", "o_present"][GUIDES.index((s, t, d, b)) % 4], E(d))}{b}</article><h2>마감 임박 공모전</h2><ul class="list">{rel}</ul>',
             [('루리의 줍줍', '/'), ('응모 가이드', '/guide/'), (t, f'/guide/{s}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': t, 'description': d, 'datePublished': '2026-10-16',
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})


PRIV_MEMBER = ('<p>루리의 줍줍(sungprofile.cloud)은 커뮤니티(후기·질문 게시판)를 쓰려는 회원에게서 <b>이메일 주소 한 가지</b>만 받습니다. 이름·전화번호·주소 등 다른 정보는 받지 않습니다.</p>'
               '<h2>회원 정보</h2><ul class="chk"><li>수집 항목: 이메일 주소(필수). 비밀번호는 복원할 수 없는 암호화 값(PBKDF2)으로만 저장합니다.</li>'
               '<li>이용 목적: 로그인, 게시글·댓글 작성자 구분, 부정 이용 방지</li><li>표시: 글쓴이 이름은 이메일 앞부분을 가린 값(예: sun***)으로만 보입니다.</li>'
               '<li>보관: 회원 탈퇴 시 즉시 삭제하며, 작성한 글·댓글은 비공개 처리합니다. 탈퇴·삭제 요청은 문의 메일로도 받습니다.</li>'
               '<li>처리 위탁: 회원·게시판 데이터는 Cloudflare(Workers, D1)에 저장됩니다.</li></ul>'
               '<p>회원이 아닌 방문자의 개인정보는 수집하지 않습니다.</p>') if COMM_API else               '<p>루리의 줍줍(sungprofile.cloud)은 회원가입·로그인 기능이 없으며 이용자의 이름, 이메일, 연락처 등 개인정보를 수집·저장하지 않습니다.</p>'


def community(live=()):
    if not COMM_API:
        shutil.rmtree(os.path.join(ROOT, 'community'), ignore_errors=True)
        return
    # 팀 만들 때 고르는 공모전 목록 (진행 중만)
    with open(os.path.join(ROOT, 'assets', 'community', 'contests.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{'id': c['id'], 't': c['title'], 'e': c['end'], 'p': c.get('prize', ''), 'pv': c.get('pv', 0), 'g': (c.get('tags') or [''])[0], 'i': CAT_ICON.get((c.get('tags') or ['기타'])[0], '💗'), 'th': c.get('th', 0)} for c in live], f, ensure_ascii=False, separators=(',', ':'))
    page('/community/', '공모전 원정대 · 커뮤니티', '공모전에 같이 나갈 사람을 찾는 루리의 줍줍 원정대. 원정대를 꾸리고 대원을 모아요.',
         f'''<p class="bc"><a href="/">홈</a> › 커뮤니티</p><h1 class="vn-h1">🚩 공모전 원정대</h1>
<section id="vn" aria-label="루리와 공모전 원정대 찾기"></section>
<button class="btn2 cm-join-cta" hidden>무료 가입 · 로그인 (이메일만 있으면 돼요)</button>
<div class="cm-tabs"><button data-k="team">🚩 전체 원정대</button><button data-k="crew">🙋 동료 찾기</button><button data-k="board">💬 후기·질문</button></div>
<section id="cm-teams" data-all data-tab="team"></section>
<section id="cm-crew" data-all data-tab="crew" hidden></section><section id="cm-board" data-all data-tab="board" hidden></section>
<script defer src="/assets/community/vn.js?v=7"></script>''', [('루리의 줍줍', '/'), ('커뮤니티', '/community/')])


def me_pages():
    """내 공간(가입 혜택 모음) · 관리자 (2026-10-17)"""
    page('/me/', '내 공간 — 찜·응모 기록·마감 알림', '찜한 공모전·청약, 응모 기록, 마감 알림 메일, 자격 프로필, 청약 가점 계산기를 한곳에서.',
         '''<section id="me" aria-label="내 공간"></section><link rel="stylesheet" href="/assets/me/me.css?v=2"><script defer src="/assets/me/me.js?v=2"></script>''', [('루리의 줍줍', '/'), ('내 공간', '/me/')])
    page('/admin/', '관리자', '관리자', '''<section id="admin"></section><link rel="stylesheet" href="/assets/me/me.css?v=2"><script defer src="/assets/me/admin.js?v=3"></script>''')


def lab():
    """루리의 수상 연구소 — 실제 수상작 + 작품 해설 (2026-10-17 사용자: 공모전 실제 작품과 분석 형식, 장르별)"""
    import lab_pages
    r = lab_pages.build(ROOT, page, say)
    if not r:
        return []
    cards, urls, D = r
    page('/lab/', '루리의 수상 연구소 — 공모전 수상작 해설', f'슬로건·표어·네이밍 공모전 실제 수상작 {D["count"]}개를 한 편씩 구조·기법으로 해설했어요. 내 문구 진단도 해 드려요.',
         lab_pages.index_html(cards, D), [('루리의 줍줍', '/'), ('수상 연구소', '/lab/')])
    return ['/lab/'] + urls


def statics(nl, ne):
    page('/about/', '소개', '루리의 줍줍은 흩어진 공모전·지원금·경품 이벤트 공고를 마감일·상금·자격 기준으로 정리하는 개인 운영 사이트입니다.',
         f'''<h1>소개</h1><p>루리의 줍줍은 개인 개발자 Seongsang Park이 운영하는 "일단 넣고 보는" 용돈 정보 사이트입니다. 응모만 하면 되는 경품, 1분이면 끝나는 댓글·설문 이벤트, 청약·지원금 신청, 슬로건 한 줄로 낼 수 있는 공모전처럼 그냥 넣으면 되는 기회를 주워 모읍니다. 여러 사이트와 기관 홈페이지에 흩어진 공모전·경품 이벤트 공고를 모아 <b>마감일, 상금, 응모 자격, 접수 방법</b>을 같은 형식으로 정리합니다. 현재 진행 중인 공모전 {nl}건, 경품 이벤트 {ne}건을 소개하고 있습니다.</p>
<h2>정보 정리 방식</h2><p>공개된 공고를 수집해 마감일과 상금, 자격을 자동으로 추출하고, 분야별 응모 체크리스트를 붙입니다. 자동 정리 과정에서 오류가 생길 수 있으므로 공모전 페이지마다 공식 공고 링크를 함께 제공합니다. 정확한 요강은 항상 주최 측 공식 공고를 기준으로 해 주세요.</p>
<h2>잘못된 정보 제보</h2><p>마감일이나 상금이 틀렸거나 종료된 공모전이 보이면 <a href="/contact/">문의</a>로 알려 주세요.</p>''', [('루리의 줍줍', '/'), ('소개', '/about/')])
    page('/contact/', '문의', '루리의 줍줍 정보 오류 제보, 공모전 등록 요청, 삭제 요청 안내.',
         f'''<h1>문의</h1><p>정보 오류 제보, 공모전 등록 요청, 삭제 요청은 이메일 <a href="mailto:{MAIL}">{MAIL}</a>, 제휴·광고 문의는 <a href="mailto:{PARTNER}">{PARTNER}</a> 로 보내 주세요. <a href="https://github.com/ilovecodingma/ilovecodingma.github.io/issues" rel="noopener">GitHub Issues</a>에 남기셔도 됩니다. 공모전 등록을 요청할 때는 공식 공고 주소를 함께 적어 주시면 확인 후 반영합니다.</p><p class="note">개인정보(이름·연락처)는 공개 게시판에 올리지 마세요.</p>''', [('루리의 줍줍', '/'), ('문의', '/contact/')])
    page('/privacy/', '개인정보처리방침', '루리의 줍줍은 이용자의 개인정보를 수집하지 않습니다. 광고 쿠키와 방문 통계 안내.',
         f'''<h1>개인정보처리방침</h1>{PRIV_MEMBER}
<h2>1. 광고와 쿠키</h2><p>이 사이트는 Google AdSense 광고를 게재하며, Google 등 제3자 광고 사업자는 쿠키를 사용해 이용자의 이전 방문 기록에 기반한 광고를 표시할 수 있습니다. 이용자는 <a href="https://adssettings.google.com" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 해제할 수 있으며, 자세한 내용은 <a href="https://policies.google.com/technologies/ads" rel="noopener">Google 광고 정책</a>을 참고하세요.</p>
<h2>2. 방문 통계</h2><p>서비스 개선을 위해 Google Analytics로 방문 통계(페이지 조회, 유입 경로, 기기 종류)를 수집합니다. 브라우저 설정이나 <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">차단 부가기능</a>으로 거부할 수 있습니다.</p>
<h2>3. 접속 로그</h2><p>사이트는 GitHub Pages로 호스팅되며, 호스팅 제공자가 보안 목적으로 접속 로그(IP 주소 등)를 처리할 수 있습니다.</p>
<h2>4. 외부 링크</h2><p>공모전 공식 공고 링크를 누르면 주최 기관 사이트로 이동하며, 해당 사이트의 개인정보처리방침이 적용됩니다.</p>
<h2>5. 문의</h2><p><a href="/contact/">문의</a> 페이지를 이용해 주세요.</p><p class="note">시행일: 2026-10-16</p>''', [('루리의 줍줍', '/'), ('개인정보처리방침', '/privacy/')])
    page('/terms/', '이용약관', '루리의 줍줍 이용약관과 정보 정확성에 관한 면책 안내.',
         '''<h1>이용약관</h1><h2>1. 서비스 내용</h2><p>루리의 줍줍은 공개된 공모전·지원사업·이벤트 공고를 정리해 소개하는 무료 정보 서비스입니다. 공모전의 주최·심사·시상에는 관여하지 않습니다.</p>
<h2>2. 정보의 정확성</h2><p>마감일·상금·응모 자격 등은 공고 원문에서 자동으로 정리한 값으로 오류가 있을 수 있습니다. 응모 전 반드시 주최 측 공식 공고를 확인해야 하며, 사이트 정보만 믿고 응모해 생긴 불이익에 대해 운영자는 책임지지 않습니다.</p>
<h2>3. 저작권</h2><p>각 공모전 공고의 저작권은 주최 기관에 있습니다. 루리의 줍줍은 요약 정보와 공식 공고 링크만 제공합니다. 게재를 원하지 않는 주최 측은 <a href="/contact/">문의</a>로 요청하시면 삭제합니다.</p>
<h2>4. 광고</h2><p>사이트 운영을 위해 Google AdSense 광고를 게재합니다.</p><p class="note">시행일: 2026-10-16</p>''', [('루리의 줍줍', '/'), ('이용약관', '/terms/')])


NEW_URLS = []
INDEXNOW_KEY = '5d0b54e7778c4d46a6de43d65f168163'


def indexnow(urls):
    """새로 생긴 주소만 Bing·네이버·Yandex 에 알림 (키 파일은 사이트 루트)"""
    import urllib.request
    body = json.dumps({'host': 'sungprofile.cloud', 'key': INDEXNOW_KEY, 'keyLocation': f'{SITE}/{INDEXNOW_KEY}.txt', 'urlList': urls}).encode()
    for ep in ('https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow'):
        try:
            r = urllib.request.urlopen(urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'}), timeout=30)
            print('indexnow', ep, r.status, len(urls))
        except Exception as e:
            print('indexnow', ep, 'fail', e)


def take_lock():
    """수집기 호출과 1시간 예약이 겹치지 않게: 20분 안의 잠금이 있으면 이번 실행은 건너뜀"""
    import time
    lk = os.path.join(HERE, '.lock')
    if os.path.exists(lk) and time.time() - os.path.getmtime(lk) < 1200:
        print('다른 생성이 진행 중이라 건너뜀')
        sys.exit(0)
    open(lk, 'w').write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(lk) and os.remove(lk))


if __name__ == '__main__':
    take_lock()
    build()
    if '--push' in sys.argv:
        def git(*a):
            r = subprocess.run(['git', '-C', ROOT] + list(a), capture_output=True, text=True, encoding='utf-8')
            print('git', a[0], r.returncode, (r.stdout + r.stderr).strip()[:200])
            return r
        git('add', '-A')
        if git('diff', '--cached', '--quiet').returncode:
            git('commit', '-q', '-m', f'사이트 데이터 갱신 {datetime.datetime.now():%m-%d %H:%M}')
            git('pull', '-q', '--rebase', '-X', 'ours')
            if git('push', '-q').returncode == 0 and NEW_URLS:
                indexnow([SITE + '/'] + NEW_URLS)
