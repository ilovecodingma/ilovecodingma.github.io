# -*- coding: utf-8 -*-
"""시험 글 모음(/exam/articles/): 기존 글 주소는 그대로 두고 시험별로 묶어 보여 준다.
입력 _gongmo/exam_data/exam_articles.json = [{"url","title","date","exam_id"(선택)}] (마케터 작성, exam_sync.py 가 복사).
 - 주소가 실제로 빌드된 글만 보여 준다(없는 주소는 건너뜀). 날짜는 신뢰도가 낮아 화면에 쓰지 않고 제목순으로 정렬한다.
 - 시험 페이지(/exam/<id>/)에 붙이는 관련 글은 related(eid) 로 가져간다."""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = html.escape


def _items():
    p = os.path.join(HERE, 'exam_data', 'exam_articles.json')
    if not os.path.exists(p):
        return []
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return []
    d = d.get('articles', d) if isinstance(d, dict) else d
    out, seen = [], set()
    for x in d:
        u = (x or {}).get('url', '')
        if not u.startswith('/') or u in seen or not x.get('title'):
            continue
        if not os.path.exists(os.path.join(ROOT, u.strip('/'), 'index.html')):
            continue
        seen.add(u)
        out.append(x)
    return out


def _ids(x):
    """exam_id 는 문자열 하나 또는 목록(글 하나가 시험 둘 이상일 때)."""
    v = x.get('exam_id') or []
    return [v] if isinstance(v, str) else [i for i in v if isinstance(i, str)]


def related(eid, limit=6):
    return [(x['url'], x['title']) for x in _items() if eid in _ids(x)][:limit]


def pages(page):
    items = _items()
    if not items:
        return []
    try:
        import exam
        names = {e['id']: e['name'] for e in exam._load()}
    except Exception:
        names = {}
    groups = {}
    for x in items:
        for i in (_ids(x) or ['']):
            groups.setdefault(i, []).append(x)
    order = sorted(groups, key=lambda k: (k == '', -len(groups[k]), k))
    secs = ''
    for k in order:
        lst = sorted(groups[k], key=lambda x: x['title'])
        nm = names.get(k) or ('기타 시험 글' if not k else k)
        head = f'<a href="/exam/{E(k)}/">{E(nm)}</a>' if k in names and os.path.exists(os.path.join(ROOT, 'exam', k, 'index.html')) else E(nm)
        secs += f'<h2>{head} <small>({len(lst)}편)</small></h2><ul>' + ''.join(f'<li><a href="{E(x["url"])}">{E(x["title"])}</a></li>' for x in lst) + '</ul>'
    body = ('<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › 시험 글 모음</p><h1>시험 글 모음</h1>'
            f'<p>수능·정시·자격증·공무원 등 시험 관련 글 {len(items)}편을 시험별로 모았어요. 일정과 예상 컷은 <a href="/exam/">시험 허브</a>, 연습문제는 <a href="/exam/bank/">문제은행</a>에서 볼 수 있어요.</p>'
            + secs + '</div>')
    page('/exam/articles/', '시험 글 모음 — 수능·정시·자격증 가이드 한곳에 — 가난한 박과장', f'시험 관련 가이드·이슈 글 {len(items)}편을 시험별로 모았습니다. 일정·접수·합격 기준을 한곳에서 찾아보세요.', body,
         [('홈', '/'), ('시험', '/exam/'), ('시험 글 모음', '/exam/articles/')])
    print('시험 글 모음', len(items), '편')
    return ['/exam/articles/']
