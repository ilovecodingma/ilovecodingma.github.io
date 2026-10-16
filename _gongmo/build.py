#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공모왕(sungprofile.cloud) 정적 사이트 생성.
사용: python _gongmo/build.py [--push]
원본: 바탕화면 공모전_2026/주말큐_master.jsonl + _gongmo/txt/<id>.txt(공고 본문 캐시, 비공개)
"""
import json, os, re, sys, html, shutil, datetime, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MASTER = r'C:\Users\k\Desktop\공모전_2026\주말큐_master.jsonl'
SITE = 'https://sungprofile.cloud'
NAME = '공모왕'
TODAY = datetime.date.today()
KEEP_PAST = 45  # 마감 후 상세페이지 보존 일수
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

GTAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4248498719773262" crossorigin="anonymous"></script>\n'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-G9BPFF95GY');</script>")
NAV = [('cat/literature', '문학'), ('cat/idea', '아이디어'), ('cat/design', '디자인'), ('cat/video', '영상'),
       ('cat/it', 'IT'), ('cat/global', '해외'), ('event', '경품'), ('guide', '가이드')]


def page(path, title, desc, body, crumbs=None, ld=None, full_title=False):
    url = SITE + path
    t = title if full_title else f'{title} | {NAME}'
    lds = []
    if crumbs:
        lds.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]})
    if ld:
        lds.append(ld)
    ldh = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False).replace('</', '<\\/') for x in lds)
    nav = ''.join(f'<a href="/{s}/">{n}</a>' for s, n in NAV)
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
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://cdn.jsdelivr.net"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/gm.css?v=2">
{ldh}
{GTAG}
</head><body>
<header class="hd"><div class="w hd-in"><a class="logo" href="/"><img src="/assets/icons/logo.svg" width="30" height="30" alt="">공모왕</a><nav>{nav}</nav></div></header>
<main class="w">
{body}
</main>
<footer class="ft"><div class="w ft-in"><div class="ft-b"><img src="/assets/ruri/wink_s.webp" width="56" height="77" alt="" loading="lazy"><div><b>공모왕</b><p>마감 놓치지 마세요! 매일 아침 새 공모전을 정리해 둘게요.</p></div></div>
<p class="ft-l"><a href="/about/">소개</a><a href="/guide/">응모 가이드</a><a href="/event/">경품 이벤트</a><a href="/privacy/">개인정보처리방침</a><a href="/terms/">이용약관</a><a href="/contact/">문의</a></p>
<p class="ft-n">공모전 정보는 각 주최 기관의 공고를 바탕으로 정리했으며, 정확한 요강은 반드시 공식 공고에서 확인하세요. © 2026 공모왕 · sungprofile.cloud</p></div></footer>
</body></html>'''
    d = os.path.join(ROOT, path.strip('/'))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(doc)


CAT_ICON = {'문학': '✍️', '아이디어·정책': '💡', '디자인': '🎨', '영상': '🎬', '논문': '📚', 'IT·과학': '💻', '해외': '🌏', '기타': '🧩'}


def say(expr, html_, cls=''):
    return (f'<div class="say {cls}"><img src="/assets/ruri/{expr}_s.webp" width="56" height="77" alt="공모왕 루리" loading="lazy">'
            f'<div class="bub"><b>루리</b><div>{html_}</div></div></div>')


def dday(end):
    n = (datetime.date.fromisoformat(end) - TODAY).days
    return n, ('마감' if n < 0 else 'D-DAY' if n == 0 else f'D-{n}')


def ddot(s):
    return s.replace('-', '.') if s else ''


def load():
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
                       'type': EV_KIND[k], 'ch': CH.get(r.get('ch', ''), ''), 'link': r.get('apply') or r['url']})
    events.sort(key=lambda e: (e['end'], e['title']))
    return contests, events


def card(c):
    n, dd = dday(c['end'])
    cls = 'd off' if n < 0 else 'd u3' if n <= 3 else 'd hot' if n <= 7 else 'd'
    tg = ''.join(f'<span class="tg">{E(t)}</span>' for t in c['tags'])
    pz = f'<span class="pz">🏆 {E(c["prize"])}</span>' if c['pv'] else ''
    return (f'<li><a class="card" data-c="{SLUG[c["tags"][0]]}" href="/c/{c["id"]}/"><span class="ic">{CAT_ICON[c["tags"][0]]}</span><div class="cb"><div class="top"><h3 class="t">{E(c["title"])}</h3><span class="{cls}">{dd}</span></div>'
            f'<p class="o">{E(c["org"])} · ~{ddot(c["end"])}</p><div class="tags">{pz}{tg}</div></div></a></li>')


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
<div class="panel"><table class="info">{tb}</table>
<a class="btn" href="{E(c["link"])}" target="_blank" rel="noopener nofollow">공식 공고 보러 가기 →</a></div>
<h2>한눈에 보기</h2><p>{E(summary)}</p>
<h2>응모 전 체크리스트</h2><ul class="chk">{tips}</ul>
<p class="note">분야: {catl}. 상금·자격·기간은 공고 원문에서 자동으로 정리한 값이라 오차가 있을 수 있습니다. 최종 기준은 주최 측 공식 공고입니다.</p>
<h2>같은 분야 진행 중 공모전</h2><ul class="list">{simh or '<li class="empty">진행 중인 같은 분야 공모전이 없어요.</li>'}</ul>'''
    ld = {'@context': 'https://schema.org', '@type': 'Event', 'name': c['title'], 'eventStatus': 'https://schema.org/EventScheduled',
          'eventAttendanceMode': 'https://schema.org/OnlineEventAttendanceMode', 'startDate': c['start'] or c['end'], 'endDate': c['end'],
          'location': {'@type': 'VirtualLocation', 'url': c['link']}, 'organizer': {'@type': 'Organization', 'name': c['org']},
          'description': summary}
    desc = f'{c["title"]} — {org} 주최, {ddot(c["end"])} 마감, 상금 {c["prize"]}. 응모 자격·접수 방법·체크리스트 정리.'
    page(f'/c/{c["id"]}/', c['title'], desc[:155], body,
         [('공모왕', '/'), (main_tag, f'/cat/{SLUG[main_tag]}/'), (c['title'], f'/c/{c["id"]}/')], ld)


def listing_js(cat=''):
    return '''<script>
(function(){var IC=%s,SL=%s;var $=function(i){return document.getElementById(i)};var items=[],cat=%s,PAGE=40,shown=PAGE;
var n=new Date(),T=Math.round(Date.UTC(n.getFullYear(),n.getMonth(),n.getDate())/864e5);
function dn(s){var p=s.split('-');return Math.round(Date.UTC(+p[0],p[1]-1,+p[2])/864e5)}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function render(){var q=$('q').value.trim().toLowerCase(),due=+$('due').value||0,s=$('sort').value;
var r=items.filter(function(i){return i.left>=0&&(!cat||i.tags.indexOf(cat)>=0)&&(!due||i.left<=due)&&(!q||i.hay.indexOf(q)>=0)});
r.sort(s==='prize'?function(a,b){return b.pv-a.pv||a.left-b.left}:function(a,b){return a.left-b.left||b.pv-a.pv});
$('cnt').textContent='진행 중 공모전 '+r.length+'건';var ul=$('list');ul.textContent='';
if(!r.length){var li=el('li','empty');li.innerHTML='<img src="/assets/ruri/sad_s.webp" width="56" height="77" alt=""><p>조건에 맞는 공모전이 없어요. 검색어를 바꿔 볼까요?</p>';ul.appendChild(li)}
r.slice(0,shown).forEach(function(i){var li=el('li'),a=el('a','card');a.href='/c/'+i.id+'/';a.dataset.c=SL[i.tags[0]]||'etc';a.appendChild(el('span','ic',IC[i.tags[0]]||'🧩'));var cb=el('div','cb'),top=el('div','top');top.appendChild(el('h3','t',i.title));
top.appendChild(el('span','d'+(i.left<=3?' u3':i.left<=7?' hot':''),i.left?'D-'+i.left:'D-DAY'));cb.appendChild(top);cb.appendChild(el('p','o',i.org+' · ~'+i.end.replace(/-/g,'.')));
var tg=el('div','tags');if(i.pv)tg.appendChild(el('span','pz','🏆 '+i.prize));i.tags.forEach(function(x){tg.appendChild(el('span','tg',x))});cb.appendChild(tg);a.appendChild(cb);li.appendChild(a);ul.appendChild(li)});
$('more').hidden=r.length<=shown}
['q','due','sort'].forEach(function(i){$(i).addEventListener('input',function(){shown=PAGE;render()})});$('more').onclick=function(){shown+=PAGE;render()};
fetch('/data.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(d){items=d.items.map(function(i){i.left=dn(i.end)-T;i.hay=(i.title+' '+i.org+' '+i.field+' '+i.tags.join(' ')).toLowerCase();return i});render()});
})();</script>''' % (json.dumps(CAT_ICON, ensure_ascii=False), json.dumps(SLUG, ensure_ascii=False), json.dumps(cat, ensure_ascii=False))


TOOLBAR = '''<div class="bar"><input type="search" id="q" placeholder="공모전, 주최, 키워드 검색" aria-label="검색">
<select id="due" aria-label="마감"><option value="">마감 전체</option><option value="7">7일 이내</option><option value="30">30일 이내</option></select>
<select id="sort" aria-label="정렬"><option value="end">마감 임박순</option><option value="prize">상금 큰 순</option></select></div>
<p class="cnt" id="cnt"></p>'''


def ev_card(e):
    n, dd = dday(e['end'])
    ch = f'<span class="tg">{E(e["ch"])}</span>' if e['ch'] else ''
    return (f'<li><a class="card" data-c="event" href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><span class="ic">🎁</span><div class="cb"><div class="top"><h3 class="t">{E(e["title"])}</h3>'
            f'<span class="d{" u3" if n <= 3 else ""}">{dd}</span></div><p class="o">{E(e["org"] or "공식 계정")} · ~{ddot(e["end"])}</p>'
            f'<div class="tags"><span class="tg">{E(e["type"])}</span>{ch}</div></div></a></li>')


def build():
    contests, events = load()
    live = [c for c in contests if dday(c['end'])[0] >= 0]
    for d in ('c', 'cat', 'event', 'guide'):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    for c in contests:
        detail(c, live)
    keys = ('id', 'title', 'org', 'end', 'prize', 'pv', 'field', 'tags')
    with open(os.path.join(ROOT, 'data.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'items': [{k: c[k] for k in keys} for c in live]},
                  f, ensure_ascii=False, separators=(',', ':'))
    pre = ''.join(card(c) for c in live[:60])  # 크롤러용 서버 렌더, JS 가 전체 목록으로 교체
    big = sorted(live, key=lambda c: -c['pv'])[:6]
    wk = [c for c in live if dday(c['end'])[0] <= 7]
    cats = ''.join(f'<a class="cat" data-c="{s_}" href="/cat/{s_}/"><span class="ic">{CAT_ICON[n]}</span><b>{n}</b><span class="n">{sum(1 for c in live if n in c["tags"])}건</span></a>' for s_, n in CATS)
    home = f'''<section class="hero"><div class="hero-t"><p class="kick">{TODAY.month}월 {TODAY.day}일 업데이트</p><h1>마감 임박 공모전,<br><em>공모왕</em>이 골라 드려요</h1>
<p class="sub">문학·아이디어·디자인·영상·논문·IT·해외 공모전과 경품 이벤트를 마감 순서로 정리했어요.</p>
<form class="hs" onsubmit="var q=document.getElementById('q');q.value=this.k.value;q.dispatchEvent(new Event('input'));document.getElementById('all').scrollIntoView();return false"><input name="k" type="search" placeholder="예) 슬로건, 숏폼, 해커톤" aria-label="공모전 검색"><button>검색</button></form>
<div class="stat"><span><b>{len(live)}</b>진행 중</span><span><b>{len(wk)}</b>이번 주 마감</span><span><b>{len(events)}</b>경품 이벤트</span></div></div>
<div class="hero-r"><div class="hb">안녕하세요, <b>공모왕 루리</b>예요!<br>오늘도 마감 임박 공모전 챙겨 왔어요 ✨</div><img src="/assets/ruri/smile.webp" width="300" height="415" alt="공모왕 루리"></div></section>
<div class="cats">{cats}<a class="cat" data-c="event" href="/event/"><span class="ic">🎁</span><b>경품 이벤트</b><span class="n">{len(events)}건</span></a></div>
<div class="sec"><h2>⏰ 이번 주 마감</h2><a href="#all">전체 보기 →</a></div><ul class="list row">{''.join(card(c) for c in wk[:10])}</ul>
<div class="sec"><h2>🏆 상금 큰 공모전</h2></div><ul class="list grid">{''.join(card(c) for c in big)}</ul>
<div class="sec" id="all"><h2>📋 전체 공모전</h2></div>{TOOLBAR}<ul class="list" id="list">{pre}</ul><button class="more" id="more" hidden>더 보기</button>
<section class="intro">{say('think', '공모전 정보는 여러 사이트에 흩어져 있어서 마감을 놓치기 쉬워요. 그래서 제가 <b>마감일·상금·응모 자격·접수 방법</b>을 같은 형식으로 정리하고, 공모전마다 응모 전 체크리스트를 붙였어요. 처음이라면 <a href="/guide/">응모 가이드</a>부터 읽어 보세요!')}</section>'''
    page('/', '공모왕 — 마감 임박 공모전·상금 정보 모음',
         f'진행 중인 공모전 {len(live)}건을 마감 임박순·상금순으로. 문학, 아이디어·정책, 디자인, 영상, 논문, IT, 해외 공모전과 경품 이벤트 정리.',
         home + listing_js(), full_title=True, ld={'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': SITE + '/'})
    for s, n in CATS:
        cl = [c for c in live if n in c['tags']]
        tips = ''.join(f'<li>{E(t)}</li>' for t in TIPS[n])
        body = f'''<p class="bc"><a href="/">홈</a> › {n}</p><section class="dh" data-c="{s}"><span class="ic big">{CAT_ICON[n]}</span><h1>{n} 공모전</h1><p class="lead">진행 중 <b>{len(cl)}건</b> · 마감 임박순</p></section>
<p>{CAT_INTRO[n]}</p>
{say('serious', f'<b>{n} 공모전 응모 팁</b><ul class="chk">{tips}</ul>')}
<h2>진행 중 {n} 공모전</h2>{TOOLBAR}<ul class="list" id="list">{''.join(card(c) for c in cl[:60])}</ul><button class="more" id="more" hidden>더 보기</button>'''
        page(f'/cat/{s}/', f'{n} 공모전 모음 (진행 중 {len(cl)}건)', f'{n} 분야 진행 중 공모전 {len(cl)}건 마감 임박순 정리. {CAT_INTRO[n][:70]}',
             body + listing_js(n), [('공모왕', '/'), (n, f'/cat/{s}/')])
    page('/event/', f'경품 이벤트 모음 (진행 중 {len(events)}건)', f'댓글·퀴즈·설문·SNS 경품 이벤트 {len(events)}건을 마감 임박순으로 정리했어요.',
         f'''<p class="bc"><a href="/">홈</a> › 경품 이벤트</p><section class="dh" data-c="event"><span class="ic big">🎁</span><h1>경품 이벤트</h1><p class="lead">진행 중 <b>{len(events)}건</b> · 마감 임박순</p></section>
{say('excited', '댓글·퀴즈·설문만으로 응모할 수 있는 이벤트가 이렇게 많아요! 당첨 발표는 꼭 공식 계정에서 확인해요.')}
<p>공공기관·기업이 진행하는 댓글, 퀴즈, 설문, SNS 경품 이벤트입니다. 참여 조건(팔로우, 친구 태그, 스토리 공유 등)과 당첨자 발표 방법은 이벤트마다 달라요. 당첨 연락을 사칭해 개인정보나 송금을 요구하는 경우가 있으니 발표는 주최 측 공식 계정에서 확인하세요.</p>
<ul class="list">{''.join(ev_card(e) for e in events)}</ul>''', [('공모왕', '/'), ('경품 이벤트', '/event/')])
    guides(live)
    statics(len(live), len(events))
    urls = ['/', '/event/', '/guide/'] + [f'/cat/{s}/' for s, _ in CATS] + [f'/guide/{g[0]}/' for g in GUIDES] + \
           ['/about/', '/privacy/', '/terms/', '/contact/'] + [f'/c/{c["id"]}/' for c in contests] + sorted((f'/v/{d}/' for d in os.listdir(os.path.join(ROOT, 'v')) if os.path.isfile(os.path.join(ROOT, 'v', d, 'index.html'))), key=lambda u: int(u.split('/')[2]) if u.split('/')[2].isdigit() else 0)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as f:
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


def guides(live):
    li = ''.join(f'<li><a class="card" data-c="guide" href="/guide/{s}/"><span class="ic">📖</span><div class="cb"><h3 class="t">{E(t)}</h3><p class="o">{E(d)}</p></div></a></li>' for s, t, d, _ in GUIDES)
    page('/guide/', '공모전 응모 가이드', '공모전 처음 응모하는 법, 제안서 쓰는 법, 수기·문학 공모 요령, 상금 수령과 사칭 주의까지.',
         f'<p class="bc"><a href="/">홈</a> › 응모 가이드</p><section class="dh" data-c="guide"><span class="ic big">📖</span><h1>공모전 응모 가이드</h1></section>{say("wink", "처음 응모한다면 1번부터 차근차근 읽어 보세요. 실수로 탈락하는 일이 확 줄어요!")}<ul class="list">{li}</ul>', [('공모왕', '/'), ('응모 가이드', '/guide/')])
    rel = ''.join(card(c) for c in live[:4])
    for s, t, d, b in GUIDES:
        page(f'/guide/{s}/', t, d, f'<p class="bc"><a href="/">홈</a> › <a href="/guide/">응모 가이드</a></p><article><h1>{E(t)}</h1>{say("thumbsup", E(d))}{b}</article><h2>마감 임박 공모전</h2><ul class="list">{rel}</ul>',
             [('공모왕', '/'), ('응모 가이드', '/guide/'), (t, f'/guide/{s}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': t, 'description': d, 'datePublished': '2026-10-16',
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})


def statics(nl, ne):
    page('/about/', '소개', '공모왕은 흩어진 공모전·경품 이벤트 공고를 마감일·상금·자격 기준으로 정리하는 개인 운영 사이트입니다.',
         f'''<h1>소개</h1><p>공모왕은 개인 개발자 Seongsang Park이 운영하는 공모전 정보 사이트입니다. 여러 사이트와 기관 홈페이지에 흩어진 공모전·경품 이벤트 공고를 모아 <b>마감일, 상금, 응모 자격, 접수 방법</b>을 같은 형식으로 정리합니다. 현재 진행 중인 공모전 {nl}건, 경품 이벤트 {ne}건을 소개하고 있습니다.</p>
<h2>정보 정리 방식</h2><p>공개된 공고를 수집해 마감일과 상금, 자격을 자동으로 추출하고, 분야별 응모 체크리스트를 붙입니다. 자동 정리 과정에서 오류가 생길 수 있으므로 공모전 페이지마다 공식 공고 링크를 함께 제공합니다. 정확한 요강은 항상 주최 측 공식 공고를 기준으로 해 주세요.</p>
<h2>잘못된 정보 제보</h2><p>마감일이나 상금이 틀렸거나 종료된 공모전이 보이면 <a href="/contact/">문의</a>로 알려 주세요.</p>''', [('공모왕', '/'), ('소개', '/about/')])
    page('/contact/', '문의', '공모왕 정보 오류 제보, 공모전 등록 요청, 삭제 요청 안내.',
         '''<h1>문의</h1><p>정보 오류 제보, 공모전 등록 요청, 삭제 요청은 <a href="https://github.com/ilovecodingma/ilovecodingma.github.io/issues" rel="noopener">GitHub Issues</a>에 남겨 주세요. 공모전 등록을 요청할 때는 공식 공고 주소를 함께 적어 주시면 확인 후 반영합니다.</p><p class="note">개인정보(이름·연락처)는 공개 게시판에 올리지 마세요.</p>''', [('공모왕', '/'), ('문의', '/contact/')])
    page('/privacy/', '개인정보처리방침', '공모왕은 이용자의 개인정보를 수집하지 않습니다. 광고 쿠키와 방문 통계 안내.',
         '''<h1>개인정보처리방침</h1><p>공모왕(sungprofile.cloud)은 회원가입·로그인 기능이 없으며 이용자의 이름, 이메일, 연락처 등 개인정보를 수집·저장하지 않습니다.</p>
<h2>1. 광고와 쿠키</h2><p>이 사이트는 Google AdSense 광고를 게재하며, Google 등 제3자 광고 사업자는 쿠키를 사용해 이용자의 이전 방문 기록에 기반한 광고를 표시할 수 있습니다. 이용자는 <a href="https://adssettings.google.com" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 해제할 수 있으며, 자세한 내용은 <a href="https://policies.google.com/technologies/ads" rel="noopener">Google 광고 정책</a>을 참고하세요.</p>
<h2>2. 방문 통계</h2><p>서비스 개선을 위해 Google Analytics로 방문 통계(페이지 조회, 유입 경로, 기기 종류)를 수집합니다. 브라우저 설정이나 <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">차단 부가기능</a>으로 거부할 수 있습니다.</p>
<h2>3. 접속 로그</h2><p>사이트는 GitHub Pages로 호스팅되며, 호스팅 제공자가 보안 목적으로 접속 로그(IP 주소 등)를 처리할 수 있습니다.</p>
<h2>4. 외부 링크</h2><p>공모전 공식 공고 링크를 누르면 주최 기관 사이트로 이동하며, 해당 사이트의 개인정보처리방침이 적용됩니다.</p>
<h2>5. 문의</h2><p><a href="/contact/">문의</a> 페이지를 이용해 주세요.</p><p class="note">시행일: 2026-10-16</p>''', [('공모왕', '/'), ('개인정보처리방침', '/privacy/')])
    page('/terms/', '이용약관', '공모왕 이용약관과 정보 정확성에 관한 면책 안내.',
         '''<h1>이용약관</h1><h2>1. 서비스 내용</h2><p>공모왕은 공개된 공모전·이벤트 공고를 정리해 소개하는 무료 정보 서비스입니다. 공모전의 주최·심사·시상에는 관여하지 않습니다.</p>
<h2>2. 정보의 정확성</h2><p>마감일·상금·응모 자격 등은 공고 원문에서 자동으로 정리한 값으로 오류가 있을 수 있습니다. 응모 전 반드시 주최 측 공식 공고를 확인해야 하며, 사이트 정보만 믿고 응모해 생긴 불이익에 대해 운영자는 책임지지 않습니다.</p>
<h2>3. 저작권</h2><p>각 공모전 공고의 저작권은 주최 기관에 있습니다. 공모왕은 요약 정보와 공식 공고 링크만 제공합니다. 게재를 원하지 않는 주최 측은 <a href="/contact/">문의</a>로 요청하시면 삭제합니다.</p>
<h2>4. 광고</h2><p>사이트 운영을 위해 Google AdSense 광고를 게재합니다.</p><p class="note">시행일: 2026-10-16</p>''', [('공모왕', '/'), ('이용약관', '/terms/')])


if __name__ == '__main__':
    build()
    if '--push' in sys.argv:
        def git(*a):
            r = subprocess.run(['git', '-C', ROOT] + list(a), capture_output=True, text=True, encoding='utf-8')
            print('git', a[0], r.returncode, (r.stdout + r.stderr).strip()[:200])
            return r
        git('add', '-A')
        if git('diff', '--cached', '--quiet').returncode:
            git('commit', '-q', '-m', f'공모왕 데이터 갱신 {datetime.datetime.now():%m-%d %H:%M}')
            git('pull', '-q', '--rebase', '-X', 'ours')
            git('push', '-q')
