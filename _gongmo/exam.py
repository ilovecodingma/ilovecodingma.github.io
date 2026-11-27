# -*- coding: utf-8 -*-
"""시험 허브(/exam/): 시험(회차)별 접수·시험일·발표일 + 예측 컷. 2026-11-20 사장님 지시(한국 모든 시험), 마케터가 원자료를 만든다.
 데이터(저장소 안): _gongmo/exam_data/exams_2027.json (리스트), _gongmo/exam_data/cuts/<exam_id>.json (컷, 예상과 공식 분리).
 원자료는 마케터 폴더(tools/marketer/calendar)에 있고 exam_sync.py 가 저장소로 복사한다(빌드는 저장소 안 파일만 읽는다).
 날짜 값이 공고 전의 작년 기준이면(status 작년 시기·basis_year<2027) 「작년 기준」 배지, 컷의 예상 값에는 기관·시각·주소와 「예상(기관 추정)」 배지를 붙인다."""
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, 'exam_data')
E = html.escape
CATS = ['입시', '공무원', '국가자격', '전문자격', '어학', '병역', '기타']
CSS = ('<style>.ex{max-width:920px;margin:0 auto}.ex h2{margin:26px 0 8px}.ex table{width:100%;border-collapse:collapse;font-size:15px}.ex th,.ex td{border-bottom:1px solid #e2e8f0;padding:8px 6px;text-align:left;vertical-align:top}'
       '.ex .tw{overflow-x:auto}.ex .bd{display:inline-block;font-size:12px;padding:1px 7px;border-radius:999px;background:#fef3c7;color:#92400e;margin-left:4px;white-space:nowrap}.ex .bd.ok{background:#dcfce7;color:#166534}.ex .bd.fc{background:#dbeafe;color:#1e40af}'
       '.ex .nt{font-size:13px;color:#64748b;margin:6px 0}.ex .ex-g{margin:14px 0}</style>')


def _load():
    p = os.path.join(DATA, 'exams_2027.json')
    if not os.path.exists(p):
        return []
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return []
    d = d.get('exams', d) if isinstance(d, dict) else d
    return [x for x in d if isinstance(x, dict) and x.get('id') and x.get('name')]


def _cut(eid):
    p = os.path.join(DATA, 'cuts', eid + '.json')
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def _d(s):
    return E(str(s)) if s else '-'


def _period(x, note=True):
    a, b = x.get('reg_start'), x.get('reg_end')
    t = f'{a} ~ {b}' if a and b else (a or b or '')
    return (E(t) + (f' <small>({E(x["reg_note"])})</small>' if (note and x.get('reg_note')) else '')) if t else '-'


def _badge(x):
    try:
        by = int(str(x.get('basis_year') or 0)[:4])
    except ValueError:
        by = 0
    if x.get('status') == '작년 시기' or (by and by < 2027):
        return '<span class="bd" title="2027년 공고 전이라 작년 일정이야">작년 기준</span>'
    if x.get('status') == '확정':
        return '<span class="bd ok">확정</span>'
    return f'<span class="bd">{E(x["status"])}</span>' if x.get('status') else ''


def _key(x):
    return (x.get('exam_date') or '9999', x.get('name'))


def _cut_html(c):
    oc = c.get('official_cut') or {}
    fr = c.get('forecast_rows') or []
    cs = '<h2>컷</h2>'
    if oc.get('rows'):
        cs += '<h3>공식 확정 컷</h3><div class="tw"><table><thead><tr><th>영역</th><th>등급</th><th>값</th></tr></thead><tbody>' + ''.join(
            f'<tr><td>{E(str(r.get("subject", "")))} {E(str(r.get("option", "")))}</td><td>{E(str(r.get("grade", "")))}</td><td>{E(str(r.get("value", "")))}</td></tr>' for r in oc['rows']) + '</tbody></table></div>'
    else:
        cs += f'<p><span class="bd fc">공식 컷 {E(oc.get("status", "미공개"))}</span> ' + (f'공개 예정일 {E(oc["release_date"])}' if oc.get('release_date') else '') + '</p>'
    if fr:
        cs += ('<h3>예상 컷 <span class="bd">예상(기관 추정)</span></h3><p class="nt">입시기관 추정이야. 확정 아니야. 기관마다 달라서 평균 안 내고 따로 적었어.</p>'
               '<div class="tw"><table><thead><tr><th>영역</th><th>등급</th><th>구분</th><th>예상 값</th><th>출처·시각</th></tr></thead><tbody>')
        for r in fr:
            src = (f'<a href="{E(r["source_url"])}" target="_blank" rel="noopener nofollow">{E(r.get("source_name", "출처"))}</a>' if r.get('source_url') else E(r.get('source_name', '')))
            cs += (f'<tr><td>{E(str(r.get("subject", "")))} {E(str(r.get("option", "")))}</td><td>{E(str(r.get("grade", "")))}</td><td>{E(str(r.get("score_type", "")))}</td>'
                   f'<td><b>{E(str(r.get("value", "")))}</b></td><td>{src}<br><small>{E(str(r.get("published_at", "")))}</small></td></tr>')
        cs += '</tbody></table></div>'
    if c.get('notes'):
        cs += '<ul class="nt">' + ''.join(f'<li>{E(n)}</li>' for n in c['notes']) + '</ul>'
    if c.get('updated_at'):
        cs += f'<p class="nt">갱신 {E(c["updated_at"])} (한국시간)</p>'
    return cs


def _rows(nm):
    p = os.path.join(DATA, nm)
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return []
    return d if isinstance(d, list) else []


def _src(r):
    return f'<a href="{E(r["source_url"])}" target="_blank" rel="noopener nofollow">공식</a>' if r.get('source_url') else '-'


def table_pages(page):
    urls = []

    def guide_ok(s):
        return bool(s) and os.path.exists(os.path.join(ROOT, 'money', 'guide', s, 'index.html'))
    js = _rows('jeongsi_2027_universities.json')
    if js:
        tr = ''.join(f'<tr><td><b>{E(r.get("university", ""))}</b></td><td>{E(str(r.get("군") or "-"))}</td><td>{_d(r.get("announce_date"))} <small>{E(str(r.get("announce_time") or ""))}</small></td>'
                     f'<td>{_d(r.get("register_start"))} ~ {_d(r.get("register_end"))}</td><td><small>{E(str(r.get("note") or ""))}</small></td><td>{_src(r)}</td></tr>' for r in js)
        g = next((r['guide_slug'] for r in js if guide_ok(r.get('guide_slug'))), '')
        body = ('<div class="ex"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험 일정</a> › 2027학년도 정시</p><h1>2027학년도 정시 대학별 합격자 발표일·등록 기간</h1>'
                '<p>대학별 정시 합격자 발표일이랑 등록 기간. 「○월 ○일 이전」으로만 밝힌 곳은 비워 뒀어. 접수 전에 입학처 공고 다시 확인해.</p>'
                '<div class="tw"><table><thead><tr><th>대학</th><th>군</th><th>합격자 발표</th><th>등록 기간</th><th>비고</th><th>출처</th></tr></thead><tbody>' + tr + '</tbody></table></div>'
                + (f'<p><a href="/money/guide/{E(g)}/">정시 발표일 가이드 자세히 보기 →</a></p>' if g else '') + '<p><a href="/exam/">← 시험 일정 전체</a></p></div>' + CSS)
        page('/exam/jeongsi-univ-2027/', '2027학년도 정시 대학별 합격자 발표일·등록 기간 — 가난한 박과장', '2027학년도 정시 30개 대학의 합격자 발표일과 등록 기간을 공식 입학처 출처와 함께 정리했어.', body, [('홈', '/'), ('시험 일정', '/exam/'), ('2027학년도 정시', '/exam/jeongsi-univ-2027/')])
        urls.append('/exam/jeongsi-univ-2027/')
    ns = _rows('nonsul_2026_2027.json')
    if ns:
        ns = sorted(ns, key=lambda r: (r.get('exam_date') or '9999', r.get('university') or ''))
        tr = ''.join(f'<tr><td><b>{E(r.get("university", ""))}</b></td><td>{_d(r.get("exam_date"))} <small>{E(str(r.get("exam_time") or ""))}</small></td><td>{E(str(r.get("target") or "-"))}</td><td>{_src(r)}</td></tr>' for r in ns)
        g = next((r['guide_slug'] for r in ns if guide_ok(r.get('guide_slug'))), '')
        body = ('<div class="ex"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험 일정</a> › 논술 시험일</p><h1>2027학년도 대학별 논술 시험일</h1>'
                '<p>대학별 논술 날짜, 날짜순. 계열마다 날짜 다른 대학은 줄 나눴어. 모집요강으로 다시 확인해.</p>'
                '<div class="tw"><table><thead><tr><th>대학</th><th>시험일</th><th>대상</th><th>출처</th></tr></thead><tbody>' + tr + '</tbody></table></div>'
                + (f'<p><a href="/money/guide/{E(g)}/">논술 일정 가이드 자세히 보기 →</a></p>' if g else '') + '<p><a href="/exam/">← 시험 일정 전체</a></p></div>' + CSS)
        page('/exam/nonsul-2027/', '2027학년도 대학별 논술 시험일 모음 — 가난한 박과장', '2027학년도 대학별 논술고사 시험일을 날짜순으로 모아 공식 출처와 함께 정리했어.', body, [('홈', '/'), ('시험 일정', '/exam/'), ('논술 시험일', '/exam/nonsul-2027/')])
        urls.append('/exam/nonsul-2027/')
    return urls


def pages(page):
    ex = _load()
    if not ex:
        return []
    today = datetime.date.today().isoformat()
    urls = []

    def guide_ok(s):
        return bool(s) and os.path.exists(os.path.join(ROOT, 'money', 'guide', s, 'index.html'))
    for x in ex:
        eid = x['id']
        c = _cut(eid)
        rows = [('접수', _period(x)), ('시험일', _d(x.get('exam_date')) + (f' <small>({E(x["exam_note"])})</small>' if x.get('exam_note') else '')),
                ('발표일', _d(x.get('result_date')) + (f' <small>({E(x["result_note"])})</small>' if x.get('result_note') else '')),
                ('응시료', _d(x.get('fee'))), ('시행 기관', _d(x.get('organizer')))]
        tb = '<div class="tw"><table><tbody>' + ''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows) + '</tbody></table></div>'
        off = f'<p><a href="{E(x["official_url"])}" target="_blank" rel="noopener nofollow">공식 사이트에서 확인하기 →</a></p>' if x.get('official_url') else ''
        gl = f'<p class="ex-g"><a href="/money/guide/{E(x["guide_slug"])}/">이 시험 일정 가이드 자세히 보기 →</a></p>' if guide_ok(x.get('guide_slug')) else ''
        body = (f'<div class="ex"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험 일정</a> › {E(x["name"])}</p><h1>{E(x["name"])} {_badge(x)}</h1>'
                f'<p>{E(x["name"])}의 접수 기간, 시험일, 발표일. 공식 공고로 확인한 날짜야. 공고 바뀌면 달라지니까 접수 전에 공식 사이트에서 다시 확인해.</p>'
                + tb + off + gl + (_cut_html(c) if c else '') + '<p><a href="/exam/">← 시험 일정 전체</a></p></div>' + CSS)
        page(f'/exam/{eid}/', f'{x["name"]} 일정·접수·발표일' + (' · 컷' if c else '') + ' — 가난한 박과장',
             f'{x["name"]}의 접수 기간, 시험일, 발표일' + (', 예상 컷' if c else '') + '을 공식 출처와 함께 정리했어.', body,
             [('홈', '/'), ('시험 일정', '/exam/'), (x['name'], f'/exam/{eid}/')])
        urls.append(f'/exam/{eid}/')
    ex_s = sorted(ex, key=_key)
    up = [x for x in ex_s if (x.get('exam_date') or '') >= today][:12]

    def li(x):
        return f'<tr><td><a href="/exam/{E(x["id"])}/">{E(x["name"])}</a> {_badge(x)}</td><td>{_period(x, False)}</td><td>{_d(x.get("exam_date"))}</td><td>{_d(x.get("result_date"))}</td></tr>'
    head = '<thead><tr><th>시험</th><th>접수</th><th>시험일</th><th>발표일</th></tr></thead>'
    sec = ''
    if up:
        sec += '<h2>다가오는 시험</h2><div class="tw"><table>' + head + '<tbody>' + ''.join(li(x) for x in up) + '</tbody></table></div>'
    sec = ('<h2>입시 일정표</h2><ul><li><a href="/exam/jeongsi-univ-2027/">2027학년도 정시 대학별 합격자 발표일·등록 기간</a></li><li><a href="/exam/nonsul-2027/">2027학년도 대학별 논술 시험일</a></li></ul>' if (_rows('jeongsi_2027_universities.json') or _rows('nonsul_2026_2027.json')) else '') + sec
    if os.path.isdir(os.path.join(DATA, 'bank')) and any(f.endswith('.json') for f in os.listdir(os.path.join(DATA, 'bank'))):
        sec = '<h2>문제은행</h2><ul><li><a href="/exam/bank/">시험별 연습문제 풀어 보기(운전면허·근로기준법·한국사 등)</a></li></ul>' + sec
    for cat in CATS + sorted({x.get('category', '기타') for x in ex} - set(CATS)):
        L = [x for x in ex_s if x.get('category', '기타') == cat]
        if L:
            sec += f'<h2>{E(cat)}</h2><div class="tw"><table>{head}<tbody>' + ''.join(li(x) for x in L) + '</tbody></table></div>'
    hub = ('<div class="ex"><p class="bc"><a href="/">홈</a> › 시험 일정</p><h1>시험 일정·접수·발표일·컷 모음</h1>'
           f'<p>접수·시험일·발표일을 한곳에 모았어. 지금 {len(ex)}개, 계속 늘려. '
           '「작년 기준」은 올해 공고 전이라 작년 일정을 적은 거야. 공고 나오면 바뀌어.</p>' + sec + '</div>' + CSS)
    page('/exam/', '시험 일정·접수·발표일·컷 모음 — 수능·공무원·자격증 — 가난한 박과장', '수능, 공무원, 국가자격, 전문자격, 어학시험의 접수 기간·시험일·발표일과 예상 컷을 공식 출처와 함께 모았어.', hub, [('홈', '/'), ('시험 일정', '/exam/')])
    urls += table_pages(page)
    urls.append('/exam/')
    print('시험 허브', len(ex), '건')
    return urls
