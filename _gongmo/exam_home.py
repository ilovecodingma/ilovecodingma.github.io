# -*- coding: utf-8 -*-
"""홈(/) 시험 정보·평생교육 홈 — 짙은 남색 스킨(assets/home/ct.css), 레퍼런스 certoday 느낌 (2026-11-25).
구성: 히어로(큰 제목+검색+칩+루리) · 바로가기 · 12개 대분류 · 다가오는 시험 · 이어 보기(노드) · 문제은행 · 시험 글 · 공모전 · 식단 · 위키."""
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = html.escape

# 사용자 확정 12개 대분류(2026-11-25). (이름, 대표 시험, 데이터상 category 값들)
CATS12 = [
    ('대학 입시', '수능·모의고사·논술·편입', ('입시',)),
    ('대학원·전문대학원', 'LEET·GRE·GMAT', ()),
    ('공무원', '국가직·지방직·경찰·소방·군무원', ('공무원',)),
    ('전문직', '변호사·회계사·세무사·노무사·감정평가사', ()),
    ('국가기술자격', '기사·산업기사·기능사·기술사', ('국가자격',)),
    ('국가전문자격', '공인중개사·주택관리사·행정사·관세사', ('전문자격',)),
    ('어학', 'TOEIC·TOEFL·IELTS·JLPT·HSK', ('어학',)),
    ('금융·투자', '투자자산운용사·AFPK·CFA', ()),
    ('IT', '정보처리기사·SQLD·ADsP·AWS', ()),
    ('의료·보건', '의사·간호사·약사 국가시험', ()),
    ('취업', 'NCS·GSAT·SKCT·인적성', ()),
    ('기타', '검정고시·한국사능력검정·운전면허', ('기타',)),
    ('자기개발', '시험과 상관없이 배우는 AI·코딩·글쓰기·습관', ()),
]
CHIPS = [('수능', 'csat-2028'), ('한능검', 'korean-history-81'), ('토익', 'toeic-585'), ('컴활', 'korcham-computer-skills'),
         ('공인중개사', 'qnet-realtor-38'), ('9급 공무원', 'civil-9-2027')]


def _exists(u):
    return os.path.exists(os.path.join(ROOT, u.strip('/'), 'index.html'))


def _exams():
    try:
        import exam
        return exam._load()
    except Exception:
        return []


def _upcoming(ex, n=8):
    today = datetime.date.today()
    out, seen = [], set()
    for x in ex:
        d = (x.get('exam_date') or '')[:10]
        try:
            dd = datetime.date.fromisoformat(d)
        except ValueError:
            continue
        key = x['name'].split(' 제')[0].split('(')[0]
        if dd >= today and _exists(f'/exam/{x["id"]}/') and key not in seen:
            seen.add(key)       # 같은 시험의 여러 회차는 가장 가까운 1개만
            out.append(((dd - today).days, x))
    out.sort(key=lambda t: (t[0], t[1]['name']))
    return out[:n]


def _banks(n=4):
    d = os.path.join(HERE, 'exam_data', 'bank')
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.json'):
                try:
                    b = json.load(open(os.path.join(d, f), encoding='utf-8'))
                except Exception:
                    continue
                u = f'/exam/bank/{b.get("id")}/'
                if _exists(u):
                    out.append((u, b.get('name', ''), len(b.get('questions', []))))
    return out[:n]


def _articles(n=6):
    try:
        import exam_articles
        return [(x['url'], x['title']) for x in exam_articles._items()[:n]]
    except Exception:
        return []


def _stats():
    ex = _exams()
    up = _upcoming(ex, 1)
    nq = 0
    for _u, _n, q in _banks(99):
        nq += q
    nxt = (f'D-{up[0][0]}' if up[0][0] else '오늘') if up else '-'
    return ('<ul class="ct-stats"><li><b>' + str(len(ex)) + '</b><span>시험 일정</span></li><li><b>' + nxt + '</b><span>가장 가까운 시험</span></li>'
            '<li><b>' + str(nq) + '</b><span>풀어 볼 문제</span></li></ul>')


def hero(ic):
    stats = _stats()
    chips = ''.join(f'<a href="/exam/{i}/">{E(n)}</a>' for n, i in CHIPS if _exists(f'/exam/{i}/'))
    return ('<div class="ct"><div class="ct-tick" aria-hidden="true"><div class="ct-tick-in"><span>지금 자면 내일은 라면 한 봉지가 2,000원인 시대일지도 몰라</span><span>학점도 월급도 그 모양인데, 잠이 오냐?</span><span>남들 다 하나씩 더 배우는데 혼자 가만히 있을 거냐?</span><span>오늘 아무것도 안 하면 내일도 오늘이랑 똑같아</span><span>지금 자면 내일은 라면 한 봉지가 2,000원인 시대일지도 몰라</span><span>학점도 월급도 그 모양인데, 잠이 오냐?</span><span>남들 다 하나씩 더 배우는데 혼자 가만히 있을 거냐?</span><span>오늘 아무것도 안 하면 내일도 오늘이랑 똑같아</span></div></div><canvas id="ct-bg" aria-hidden="true"></canvas><section class="ct-hero" aria-labelledby="h2-t"><div>'
            '<h1 id="h2-t">가난한 박과장과 <b>헬조선 <mark>살아남기</mark></b></h1>'
            '<p class="lead">뭐라도 해. 안 하면 도태.</p>'

            '<form class="h2-s" role="search" action="/wiki/"><div class="row"><label class="sr" for="hs">검색 범위</label><select id="hs"><option value="">전체</option><option value="c">공모전</option><option value="a">지원금</option><option value="w">가이드</option><option value="r">식단</option></select>'
            '<label class="sr" for="hq">검색어</label><input id="hq" type="search" placeholder="시험 이름 검색 (예: 한능검, 토익, 컴활)" autocomplete="off" enterkeyhint="search"><button type="submit" class="go">검색</button></div>'
            '<div class="res" id="hr" aria-live="polite"></div></form>'
            f'<div class="ct-chips"><small>자주 찾는 시험</small>{chips}</div>{stats}</div>'
            '<div class="ct-ruri"><img src="/assets/ruri/o_sn_point.webp" width="260" height="360" alt="박과장의 전속 비서 루리"><span class="ct-stamp">아직도<br>안 배움?</span></div></section>'
            '<div class="ct-paths"><a href="/park/"><b>자기개발</b><span>시사·요리·바이브 코딩</span></a>'
            '<a href="/exam/"><b>자격증·시험</b><span>따야 산다</span></a></div>'

            '<nav class="ct-tabs" aria-label="바로가기"><a href="/park/">자기개발</a><a href="/exam/">전체 시험 일정</a><a href="/exam/bank/">문제은행</a><a href="/exam/articles/">시험 글</a>'
            '<a href="/issue/">시험 뉴스</a><a href="/contest/">공모전</a><a href="/diet/">식단</a><a href="/plaza/">이야기방</a><a href="/wiki/">위키</a></nav>')


WEIRD = {'자기개발': '일단 뭐라도 배워라', '분야별로 찾기': '뭘 따야 하는지도 모르지?', '다가오는 시험': '곧 터진다',
         '문제은행': '틀리면 루리가 웃는다', '시험 뉴스·글': '알고나 있어라', '공모전': '상금 먹을 시간'}


def _hd(t, more):
    w = WEIRD.get(t)
    h = f'{E(w)} <small>{t}</small>' if w else t
    return f'<div class="ct-hd"><h2>{h}</h2><a href="{more[0]}">{more[1]} →</a></div>'


def sections(ctx, ic):
    ex = _exams()
    cnt = {}
    for x in ex:
        cnt[x.get('category')] = cnt.get(x.get('category'), 0) + 1
    out = hero(ic)
    out += ('<section class="ct-sec">' + _hd('자기개발', ('/park/', '전체 보기')) + '<ul class="ct-grid">'
            '<li><a class="ct-card" href="/park/"><span class="d far">시작</span><h3>AI 에이전트로 내 서비스 만들기</h3><p>퇴근하고 3시간</p></a></li>'
            '<li><a class="ct-card" href="/ailog/"><span class="d far">지식</span><h3>개발 지식 · 제작 로그</h3><p>만들면서 배운 것</p></a></li>'
            '<li><a class="ct-card" href="/dev/"><span class="d far">블로그</span><h3>기술 블로그</h3><p>개발·AI 글</p></a></li></ul></section>')
    tiles = ''
    for nm, sub, keys in CATS12:
        n = sum(cnt.get(k, 0) for k in keys)
        href = '/park/' if nm == '자기개발' else '/exam/'
        n = n or (1 if nm == '자기개발' else 0)
        tiles += (f'<a class="ct-cat{"" if n else " off"}" href="{href}"><b>{E(nm)}</b><span>{E(sub)}</span>'
                  f'<em>{("배울 거리 보기" if nm == "자기개발" else f"{n}개 시험 일정") if n else "준비 중"}</em></a>')
    out += '<section class="ct-sec">' + _hd('분야별로 찾기', ('/exam/', '전체 일정')) + f'<div class="ct-cats">{tiles}</div></section>'
    out += '<div class="ct-tape" aria-hidden="true"><span>경고 · 정신 차려 · 경고 · 정신 차려 · 경고 · 정신 차려 · 경고 · 정신 차려 · 경고 · 정신 차려 · </span></div>'
    up = _upcoming(ex)
    if up:
        li = ''
        for dday, x in up:
            tag = '오늘' if dday == 0 else f'D-{dday}'
            far = '' if dday <= 30 else ' far'
            li += (f'<li><a class="ct-card" href="/exam/{E(x["id"])}/"><span class="d{far}">{tag}</span>'
                   f'<h3>{E(x["name"])}</h3><p>{E(x.get("exam_date") or "")} · {E(x.get("category") or "")}</p></a></li>')
        out += '<section class="ct-sec">' + _hd('다가오는 시험', ('/exam/', '시험 일정 전체')) + f'<ul class="ct-grid">{li}</ul></section>'
    bk = _banks()
    ar = _articles()
    left = right = ''
    if bk:
        left = '<div>' + _hd('문제은행', ('/exam/bank/', '전체')) + '<ul class="ct-list">' + ''.join(
            f'<li><a href="{u}">{E(nm)} <small style="color:#9aa4c4">· 유사문제 {n}문항</small></a></li>' for u, nm, n in bk) + '</ul></div>'
    if ar:
        right = '<div>' + _hd('시험 뉴스·글', ('/exam/articles/', '전체')) + '<ul class="ct-list">' + ''.join(
            f'<li><a href="{E(u)}">{E(t)}</a></li>' for u, t in ar) + '</ul></div>'
    if left or right:
        out += f'<section class="ct-sec"><div class="ct-two">{left}{right}</div></section>'
    n_c = ctx.get('n_contest')
    out += ('<section class="ct-sec">' + _hd('공모전', ('/contest/', '공모전 찾기'))
            + '<div class="ct-ban"><img src="/assets/ruri/o_sn_point.webp" alt="" width="84" height="116"><div><b>학생·취준생이 낼 수 있는 공모전'
            + (f' {n_c}건' if n_c else '') + '</b><span>마감 임박순.</span></div></div></section>')
    out += ('<section class="ct-sec"><div class="ct-two"><a class="ct-ban" href="/diet/"><div><b>식단</b><span>먹어야 공부한다.</span></div></a>'
            '<a class="ct-ban" href="/wiki/"><div><b>위키 · 생활 정보</b><span>세금·보험·지원금처럼 나머지 잡다한 건 위키.</span></div></a></div></section></div>')
    out += '<link rel="stylesheet" href="/assets/home/home2.css?v=11"><link rel="stylesheet" href="/assets/home/ct.css?v=6"><script defer src="/assets/home/ct-bg.js?v=4"></script><script defer src="/assets/home/home2.js?v=3"></script>'
    return out
