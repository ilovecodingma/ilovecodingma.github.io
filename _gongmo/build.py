#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""루리의 줍줍(sungprofile.cloud) 정적 사이트 생성.
사용: python _gongmo/build.py [--push]
원본: 바탕화면 공모전_2026/주말큐_master.jsonl + _gongmo/txt/<id>.txt(공고 본문 캐시, 비공개)
"""
import json, os, re, sys, html, shutil, datetime, subprocess, hashlib
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
        ('paper', '논문'), ('it', 'IT·과학'), ('global', '해외'), ('etc', '기타')]
SLUG = {n: s for s, n in CATS}
CAT_INTRO = {
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

COMM_TAGS_TPL = '<link rel="stylesheet" href="/assets/community/comm.css?v=6"><script defer src="/assets/community/comm.js?v=5"></script>'
GTAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4248498719773262" crossorigin="anonymous"></script>\n'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-G9BPFF95GY');</script>")
NAV = [('apply', '청약·신청'), ('ssul', '썰'), ('event', '경품·용돈'), ('cat/literature', '문학'), ('cat/idea', '아이디어'), ('cat/design', '디자인'),
       ('cat/video', '영상'), ('cat/it', 'IT'), ('cat/global', '해외'), ('guide', '가이드')]


def page(path, title, desc, body, crumbs=None, ld=None, full_title=False):
    url = SITE + path
    COMM_TAGS = COMM_TAGS_TPL if COMM_API else ''
    t = title if full_title else f'{title} | {NAME}'
    lds = []
    if crumbs:
        lds.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]})
    if ld:
        lds.append(ld)
    ldh = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False).replace('</', '<\\/') for x in lds)
    nav = ''.join(f'<a href="/{s}/">{n}</a>' for s, n in NAV + ([('community', '공략 파티')] if COMM_API else []))
    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(t)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{E(t)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/ruri/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/assets/ruri/og.jpg">
<meta name="theme-color" content="#5b21b6">
<link rel="icon" href="/favicon.ico?v=5" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png?v=5"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png?v=5"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://cdn.jsdelivr.net"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/gm.css?v=4"><link rel="stylesheet" href="/assets/chat/ruri-chat.css?v=3">{COMM_TAGS}<script type="module" src="/assets/chat/ruri-chat.js?v=5"></script>
{ldh}
{GTAG}
</head><body{(' data-api="' + COMM_API + '"') if COMM_API else ''}>
<header class="hd"><div class="w hd-in"><a class="logo" href="/"><img src="/assets/icons/logo.svg" width="30" height="30" alt=""><span>루리의 <b>줍줍</b></span></a><nav>{nav}</nav></div></header>
<main class="w">
{body}
</main>
<footer class="ft"><div class="w ft-in"><div class="ft-b"><img class="av" src="/assets/ruri/avatar.webp" width="56" height="56" alt="루리" loading="lazy"><div><b>루리의 줍줍</b><p>마감 놓치지 마세요! 매일 아침 새 공모전을 정리해 둘게요.</p><p class="ft-m">문의 <a href="mailto:{MAIL}">{MAIL}</a>{"" if PARTNER == MAIL else f' · 제휴 <a href="mailto:{PARTNER}">{PARTNER}</a>'}</p></div></div>
<p class="ft-l"><a href="/about/">소개</a><a href="/guide/">응모 가이드</a><a href="/event/">경품 이벤트</a><a href="/privacy/">개인정보처리방침</a><a href="/terms/">이용약관</a><a href="/contact/">문의</a></p>
<p class="ft-n">공모전 정보는 각 주최 기관의 공고를 바탕으로 정리했으며, 정확한 요강은 반드시 공식 공고에서 확인하세요. © 2026 루리의 줍줍 · sungprofile.cloud</p></div></footer>
</body></html>'''
    d = os.path.join(ROOT, path.strip('/'))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(doc)


CAT_OUTFIT = {'문학': 'o_cardigan', '아이디어·정책': 'o_present', '디자인': 'o_gray', '영상': 'o_anchor', '논문': 'o_vest', 'IT·과학': 'o_desk', '해외': 'o_trench', '기타': 'o_suit'}
CAT_ICON = {'문학': '✍️', '아이디어·정책': '💡', '디자인': '🎨', '영상': '🎬', '논문': '📚', 'IT·과학': '💻', '해외': '🌏', '기타': '🧩'}


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
    for r in rows:
        k = r.get('kind', '')
        if k not in EV_KIND or r.get('end', '') < TODAY.isoformat():
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
<h2>한눈에 보기</h2><p>{E(summary)}</p>
<h2>응모 전 체크리스트</h2><ul class="chk">{tips}</ul>
<p class="note">분야: {catl}. 상금·자격·기간은 공고 원문에서 자동으로 정리한 값이라 오차가 있을 수 있습니다. 최종 기준은 주최 측 공식 공고입니다.</p>
{f'<section id="cm-teams" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section><section id="cm-board" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section>' if COMM_API else ''}
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
    if not os.path.exists(fp):
        return []
    out, seen = [], set()
    for l in open(fp, encoding='utf-8'):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if not r.get('title') or not r.get('end') or r.get('closed'):
            continue
        end = r.get('end_override') or r['end']
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
        out.append({'id': aid, 'title': P.clean(r['title'])[:90], 'org': P.clean(r.get('org', ''))[:40] or '공고 참조', 'kind': nm, 'icon': ic,
                    'start': r.get('start', ''), 'end': end, 'url': r.get('url', ''), 'source': r.get('source', ''), 'verified': bool(r.get('verified'))})
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
    for a in aps:
        n, dd = dday(a['end'])
        period = (ddot(a['start']) + ' ~ ' if a['start'] else '~ ') + ddot(a['end'])
        tb = ''.join(f'<tr><th>{k}</th><td>{E(v)}</td></tr>' for k, v in
                     [('구분', a['kind']), ('주관', a['org']), ('신청 기간', period), ('출처', a['source'] or '공식 공고')])
        btn = (f'<a class="btn" href="{E(a["url"])}" target="_blank" rel="noopener nofollow">공식 사이트에서 신청하기 →</a>' if a['url'] else '')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">청약·신청</a></p>
<section class="dh" data-c="apply"><span class="ic big">{a["icon"]}</span><h1>{E(a["title"])}</h1><p class="lead"><span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span> {ddot(a["end"])} 마감</p></section>
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
    home = f'''<section class="hero"><div class="hero-t"><p class="kick">{TODAY.month}월 {TODAY.day}일 업데이트</p><h1>그냥 넣으면 되는 용돈 기회,<br><em>루리</em>가 주워 왔어요</h1>
<p class="sub">슬로건 한 줄, 사진 한 장으로 내는 대회부터 경쟁 적은 숨은 대회, 청약·지원금 신청까지. 일단 넣고 보세요!</p>
<form class="hs" onsubmit="var q=document.getElementById('q');q.value=this.k.value;q.dispatchEvent(new Event('input'));document.getElementById('all').scrollIntoView();return false"><input name="k" type="search" placeholder="예) 슬로건, 숏폼, 해커톤" aria-label="공모전 검색"><button>검색</button></form>
<div class="stat"><span><b>{len(live)}</b>공모전</span><span><b>{len(wk)}</b>이번 주 마감</span><span><b>{len(events)}</b>경품·용돈</span></div></div>
<div class="hero-r"><div class="hb">안녕하세요, <b>루리</b>예요!<br>오늘도 마감 임박 공모전 챙겨 왔어요 ✨</div><img id="hero-ruri" src="/assets/ruri/smile.webp" width="300" height="415" alt="루리"></div></section>
<div class="sec"><h2>✍️ 바로 낼 수 있는 대회</h2><a href="#all">전체 보기 →</a></div><p class="note" style="margin:-6px 0 10px">슬로건·네이밍·짧은 글·아이디어·사진처럼 오늘 바로 낼 수 있는 대회</p><ul class="list row">{''.join(card(c) for c in short[:12])}</ul>
<div class="sec"><h2>🔍 참가자 적은 숨은 대회</h2><a href="#all">전체 보기 →</a></div><p class="note" style="margin:-6px 0 10px">지역·재학·재직 같은 자격 제한이 있거나 시·군·구 단위로 열려 경쟁이 덜할 만한 대회</p><ul class="list row">{''.join(card(c) for c in hidden[:12])}</ul>
{'<div class="sec"><h2>📝 청약·신청 일정</h2><a href="/apply/">전체 보기 →</a></div><ul class="list row">' + ''.join(ap_card(a) for a in aps[:10]) + '</ul>' if aps else ''}
<div class="cats">{cats}<a class="cat" data-c="event" href="/event/"><span class="ic">🎁</span><b>경품·용돈</b><span class="n">{len(events)}건</span></a><a class="cat" data-c="apply" href="/apply/"><span class="ic">📝</span><b>청약·신청</b><span class="n">{len(aps)}건</span></a></div>
<div class="sec"><h2>⏰ 이번 주 마감</h2><a href="#all">전체 보기 →</a></div><ul class="list row">{''.join(card(c) for c in wk[:10])}</ul>
<div class="sec"><h2>🏆 상금 큰 공모전</h2></div><ul class="list grid">{''.join(card(c) for c in big)}</ul>
<div class="sec" id="all"><h2>📋 전체 공모전</h2></div>{TOOLBAR}<ul class="list" id="list">{pre}</ul><button class="more" id="more" hidden>더 보기</button>
<section class="intro">{say('think', '공모전 정보는 여러 사이트에 흩어져 있어서 마감을 놓치기 쉬워요. 그래서 제가 <b>마감일·상금·응모 자격·접수 방법</b>을 같은 형식으로 정리하고, 공모전마다 응모 전 체크리스트를 붙였어요. 처음이라면 <a href="/guide/">응모 가이드</a>부터 읽어 보세요!')}</section>'''
    page('/', '루리의 줍줍 — 일단 넣고 보는 용돈 정보',
         f'진행 중인 공모전 {len(live)}건을 마감 임박순·상금순으로. 문학, 아이디어·정책, 디자인, 영상, 논문, IT, 해외 공모전과 경품 이벤트 정리.',
         home + HERO_JS + listing_js(), full_title=True, ld={'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': SITE + '/'})
    for s, n in CATS:
        cl = [c for c in live if n in c['tags']]
        tips = ''.join(f'<li>{E(t)}</li>' for t in TIPS[n])
        body = f'''<p class="bc"><a href="/">홈</a> › {n}</p><section class="dh" data-c="{s}"><span class="ic big">{CAT_ICON[n]}</span><h1>{n} 공모전</h1><p class="lead">진행 중 <b>{len(cl)}건</b> · 마감 임박순</p></section>
<p>{CAT_INTRO[n]}</p>
{say(CAT_OUTFIT[n], f'<b>{n} 공모전 응모 팁</b><ul class="chk">{tips}</ul>')}
<h2>진행 중 {n} 공모전</h2>{TOOLBAR}<ul class="list" id="list">{''.join(card(c) for c in cl[:60])}</ul><button class="more" id="more" hidden>더 보기</button>'''
        page(f'/cat/{s}/', f'{n} 공모전 모음 (진행 중 {len(cl)}건)', f'{n} 분야 진행 중 공모전 {len(cl)}건 마감 임박순 정리. {CAT_INTRO[n][:70]}',
             body + listing_js(n), [('루리의 줍줍', '/'), (n, f'/cat/{s}/')])
    page('/event/', f'경품 이벤트 모음 (진행 중 {len(events)}건)', f'댓글·퀴즈·설문·SNS 경품 이벤트 {len(events)}건을 마감 임박순으로 정리했어요.',
         f'''<p class="bc"><a href="/">홈</a> › 경품 이벤트</p><section class="dh" data-c="event"><span class="ic big">🎁</span><h1>경품 이벤트</h1><p class="lead">진행 중 <b>{len(events)}건</b> · 마감 임박순</p></section>
{say('excited', '댓글·퀴즈·설문만으로 응모할 수 있는 이벤트가 이렇게 많아요! 당첨 발표는 꼭 공식 계정에서 확인해요.')}
<p>공공기관·기업이 진행하는 댓글, 퀴즈, 설문, SNS 경품 이벤트입니다. 참여 조건(팔로우, 친구 태그, 스토리 공유 등)과 당첨자 발표 방법은 이벤트마다 달라요. 당첨 연락을 사칭해 개인정보나 송금을 요구하는 경우가 있으니 발표는 주최 측 공식 계정에서 확인하세요.</p>
<ul class="list">{''.join(ev_card(e) for e in sorted(events, key=lambda e: (min(dday(e['end'])[0], 7) // 4, EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2), e['end'])))}</ul>''', [('루리의 줍줍', '/'), ('경품 이벤트', '/event/')])
    shutil.rmtree(os.path.join(ROOT, 'a'), ignore_errors=True)
    build_apply(aps)
    ss = load_ssul()
    build_ssul(ss, live, aps)
    guides(live)
    community(live)
    statics(len(live), len(events))
    urls = ['/', '/apply/', '/event/', '/guide/', '/ssul/'] + [f'/ssul/{x["slug"]}/' for x in ss] + [f'/a/{a["id"]}/' for a in aps] + [f'/cat/{s}/' for s, _ in CATS] + [f'/guide/{g[0]}/' for g in GUIDES] + \
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
    page('/community/', '공모전 공략 파티 · 커뮤니티', '공모전이라는 히로인을 같이 공략할 파티원을 찾는 루리의 줍줍 커뮤니티. 파티를 결성하고 합류 신청을 받아요.',
         f'''<p class="bc"><a href="/">홈</a> › 커뮤니티</p><h1 class="vn-h1">💘 공모전 공략 파티</h1>
<section id="vn" aria-label="루리와 공모전 공략 파티 찾기"></section>
<button class="btn2 cm-join-cta" hidden>무료 가입 · 로그인 (이메일만 있으면 돼요)</button>
<div class="cm-tabs"><button data-k="team">💘 전체 파티 목록</button><button data-k="board">💬 후기·질문</button></div>
<section id="cm-teams" data-all data-tab="team"></section>
<section id="cm-board" data-all data-tab="board" hidden></section>
<script defer src="/assets/community/vn.js?v=4"></script>''', [('루리의 줍줍', '/'), ('커뮤니티', '/community/')])


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
