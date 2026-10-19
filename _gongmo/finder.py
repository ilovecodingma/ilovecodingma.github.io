# -*- coding: utf-8 -*-
"""공모전 자동 자료 찾기 (2026-10-19 사용자 아이디어 「공모전 고르면 맞는 자료를 자동으로 찾아 주는 검색엔진」, 모델 없음).
빌드 끝에서 ① 사이트 안 문서 색인 /assets/finder/index.json (수상작·가이드·준비실·핫이슈·키워드·공모전·평론 페이지의 제목·설명 + 최근 기사 제목)
② 공모전마다 자동 질의 /assets/finder/q.json (제목·공고 원문 주제·제출물·분야에서 명사만, 불용어 제외) 를 만든다.
검색(BM25)은 브라우저(assets/finder/finder.js)에서 돌린다 — 서버 비용 0원."""
import collections, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KINDS = [('/lab/', 'lab', '🏆 수상작·분석'), ('/guide/', 'guide', '📘 가이드'), ('/qa/', 'guide', '📘 가이드'), ('/prep/', 'guide', '📘 가이드'), ('/hot/', 'issue', '🔥 핫이슈'),
         ('/kw/', 'issue', '🔎 인기 키워드'), ('/review/', 'issue', '🖋️ 평론'), ('/c/', 'contest', '🏆 비슷한 공모전'), ('/contest/', 'hub', '📚 공모전 모음'), ('/cat/', 'hub', '📚 공모전 모음'),
         ('/money/tools/', 'tool', '🧮 계산기'), ('/fridge/r/', 'recipe', '🍳 레시피')]
STOP = set('공모전 공모 모집 안내 공고 대회 경진대회 경연대회 개최 참가자 참가 접수 신청 제출 응모 작품 시상 수상 기간 전국 대한민국 국민 누구 일반 이상 이하 관련 활용 위한 대한 통한 기념 주년 제회 신규 연장 재공고 마감 공식 포함 가능 진행 내용 분야 주제 형식 기타 이번 올해 시민 도민 군민 구민 행사 사업 프로젝트 챌린지 이벤트 참여 최소 최대 세로 가로 기반 대국민 사업단 해상도 이내 제작 작성 개인 단체 학생 일반부 만원 상금 총상금'.split())


def _meta(doc, name, attr='name'):
    m = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', doc[:12000])
    return html.unescape(m.group(1)) if m else ''


def build_index(urls, noindex, live_ids):
    docs = []
    for u in urls:
        k = next(((kd, lab) for px, kd, lab in KINDS if u.startswith(px) and u != px), None)
        if not k:
            continue
        if k[0] == 'contest' and u not in {f'/c/{i}/' for i in live_ids}:
            continue   # 마감·중복 안내 페이지는 자료에서 뺌
        f = os.path.join(ROOT, u.strip('/'), 'index.html')
        if not os.path.exists(f):
            continue
        doc = open(f, encoding='utf-8', errors='ignore').read()
        t = re.sub(r'\s*\|\s*루리의 줍줍\s*$', '', html.unescape((re.search(r'<title>([^<]*)', doc) or [None, ''])[1])).strip()
        if not t:
            continue
        docs.append({'k': k[0], 'l': k[1], 't': t[:90], 'x': _meta(doc, 'description')[:140], 'u': u})
    nw = os.path.join(ROOT, 'news', 'data.json')
    if os.path.exists(nw):
        for a in json.load(open(nw, encoding='utf-8')).get('items', [])[:400]:
            if a.get('s') is None or a.get('ent'):
                continue
            docs.append({'k': 'news', 'l': f'📰 기사 · {a["o"]}', 't': a['t'][:90], 'x': '', 'u': a['u'], 'ext': 1})
    os.makedirs(os.path.join(ROOT, 'assets', 'finder'), exist_ok=True)
    json.dump({'docs': docs}, open(os.path.join(ROOT, 'assets', 'finder', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return len(docs)


_kiwi = None


def nouns(t):
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()
    t = re.sub(r'[\[［(「『][^\]］)」』]{0,20}[\]］)」』]', lambda m: ' ' + m.group(0)[1:-1] + ' ', t)
    return [w.form for w in _kiwi.tokenize(t) if w.tag in ('NNP', 'NNG', 'SL') and len(w.form) >= 2 and w.form not in STOP and not re.fullmatch(r'\d+|[A-Za-z]', w.form)]


def build_queries(live, notice_points):
    Q = {}
    for c in live:
        sc = collections.Counter()
        for w in nouns(c['title']):
            sc[w] += 3
        for lab, v in notice_points(c['id']):
            if lab in ('공모 주제', '제출물·규격'):
                for w in nouns(v)[:12]:
                    sc[w] += 1
        for tg in c['tags'][:2]:
            for w in re.split(r'[·\s]', tg):
                if len(w) >= 2 and w not in STOP:
                    sc[w] += 1
        if c.get('effort'):
            sc[c['effort']] += 1
        org = c.get('org') or ''
        for w in nouns(org):
            sc.pop(w, None)   # 주최 기관 이름은 자료 찾기에 잡음이라 뺌
        Q[c['id']] = [w for w, _ in sc.most_common(8)]
    json.dump(Q, open(os.path.join(ROOT, 'assets', 'finder', 'q.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return Q
