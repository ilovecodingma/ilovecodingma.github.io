# -*- coding: utf-8 -*-
"""「잠이 오냐」 관심 분야 공통 모듈 (2026-11-27). exam_push.py(푸시)와 digest.py(메일)가 같이 쓴다. 발송·D1 접근 없음, 사이트 데이터 파일만 읽는다.

구독 항목은 두 종류다.
  exams  = 시험 계열 키 (FAMILIES) → 일정(접수·시험일 D-7/3/1/0) + 오늘의 문제(문제은행) + 시험 새 글
  topics = 분야 키 (FIELDS)       → 마감 임박(돈·주거·공모전) + 새 소식(전 분야)
알림 종류는 sch(일정·마감) / qz(오늘의 문제, 시험 한정) / nw(새 소식), 분야는 켜고 끄는 방식(목록에 있으면 켬)."""
import os, re, json, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
EXD = os.path.join(HERE, 'exam_data')

# ── 시험 id ↔ 문제은행 매핑표 ─────────────────────────────────────────────
# 키: (표시 이름, exams_2027.json 의 id 앞머리 목록, 문제은행 파일 이름(bank/*.json, hold:true 는 자동 제외))
# exams_2027.json 은 회차마다 id 가 따로(toeic-584 …)라 계열로 묶는다. 일정이 없는 계열(prefix 빈 목록)은 문제만 온다.
FAMILIES = {
    'toeic': ('토익', ['toeic-'], ['toeic-grammar-basic', 'toeic-vocab-basic']),
    'korhist': ('한국사능력검정', ['korean-history-'], ['korean-history-basic', 'korean-history-advanced']),
    'csat': ('수능', ['csat-'], ['csat-math-1', 'csat-math-2', 'csat-english-vocab']),
    'jeongsi': ('정시·수시 입시', ['jeongsi-', 'susi-'], []),
    'civil': ('공무원 5·7·9급·PSAT', ['civil-', 'psat-', 'diplomat-'], ['civil-servant-law-basic']),
    'fire': ('소방공무원', ['fire-'], ['fire-science-basic']),
    'police': ('경찰공무원', ['police-'], []),
    'teacher': ('교원임용', ['teacher-'], []),
    'mma': ('병무청·군 채용', ['mma-', 'military-'], []),
    'gisa': ('기사(Q-net)', ['qnet-gisa-'], ['engineer-info-processing-basic']),
    'gineungsa': ('기능사(Q-net)', ['qnet-gineungsa-', 'qnet-gineungjang-'], ['electric-basic', 'heavy-equipment-safety-basic']),
    'gisulsa': ('기술사(Q-net)', ['qnet-gisulsa-'], []),
    'realtor': ('공인중개사', ['qnet-realtor-'], ['realtor-law-basic']),
    'socialw': ('사회복지사 1급', ['qnet-social-worker-'], ['social-worker-law-basic']),
    'kuksiwon': ('보건의료 국가시험', ['kuksiwon-'], []),
    'carework': ('요양보호사', ['care-worker-'], []),
    'korcham': ('컴퓨터활용능력', ['korcham-'], ['korcham-computer-2']),
    'gumjeong': ('검정고시', ['gumjeong-'], ['gumjeong-social-basic']),
    'itcert': ('ADsP·SQLD·AWS·리눅스', [], ['adsp-basic', 'sqld-basic', 'aws-clf-basic', 'linux-network-basic']),
    'ncs': ('NCS·GSAT 취업시험', [], ['ncs-communication', 'ncs-numerical', 'gsat-style-reasoning']),
    'driver': ('운전면허 필기', [], ['driver-license-written', 'driver-road-traffic-law', 'driver-safe-driving-first-aid', 'driver-signs-markings', 'driver-class1-extra']),
    'laborexam': ('근로기준법·노무', [], ['labor-standards-basic']),
    'transfer': ('편입 영어', [], ['transfer-english-basic']),
}
# 분야: 키 → (이름, 한 줄). 사이트에 실제 데이터가 있는 것만(apply.json·data.json·selfdev_data/items.json·news/brief.json·diet).
FIELDS = {
    'dev': ('자기개발·스킬', '개발·AI·어학·강좌·자격 새 정보 (selfdev 수집)'),
    'money': ('돈·세금·지원금', '지원금 신청 마감, 새 지원금, 재테크 소식 (apply.json)'),
    'house': ('주거·전월세·청약', '아파트 청약·공공임대 접수 마감 (apply.json)'),
    'job': ('취업·노동·이직', '노동·일자리 정책 새 소식 (selfdev 수집)'),
    'contest': ('공모전·스펙', '공모전 마감 임박·새 공모전 (data.json)'),
    'health': ('식단·건강', '오늘 뭐 먹을지·운동 잔소리 (fridge·diet)'),
    'issue': ('이슈', '오늘 알고나 있어야 할 사건·제도 변화 (news/brief.json)'),
}
APPLY_KIND = {'money': ('지원금 신청', '공모주'), 'house': ('아파트 청약', '공공임대')}
SD_KIND = {'dev': ('IT', '강좌', '자격'), 'job': ('노동',), 'money': ('재테크',)}   # selfdev items.json 의 kind
HOLD_SD_SRC = ('서울도서관',)


def rd(p):
    f = p if os.path.isabs(p) else os.path.join(ROOT, p)
    try:
        return json.load(open(f, encoding='utf-8'))
    except Exception:
        return None


def h(*a):
    return int(hashlib.md5('|'.join(map(str, a)).encode()).hexdigest(), 16)


def pick(lst, *seed):
    return lst[h(*seed) % len(lst)]


def pdate(s):
    m = re.search(r'\d{4}-\d{2}-\d{2}', str(s or ''))
    try:
        return datetime.date.fromisoformat(m.group(0)) if m else None
    except Exception:
        return None


def short(t, n=34):
    t = re.sub(r'\s*NEW$', '', t or '').strip()
    return t if len(t) <= n else t[:n - 1] + '…'


def csv(s):
    return [x for x in (s or '').split(',') if x]


_EX = []


def exams():
    if not _EX:
        _EX.append(rd(os.path.join(EXD, 'exams_2027.json')) or [])
    return _EX[0]


def family_of(exam_id):
    if isinstance(exam_id, (list, tuple)):
        return next((f for f in map(family_of, exam_id) if f), None)
    for k, (_, pre, _) in FAMILIES.items():
        if any(exam_id.startswith(p) for p in pre):
            return k
    return None


def uncovered():
    return [e['id'] for e in exams() if not family_of(e['id'])]


# ── 시험 일정 ─────────────────────────────────────────────────────────────
_ED = {'reg_start': ('접수', '시작'), 'reg_end': ('접수', '마감'), 'exam_date': ('시험', '')}


def exam_copy(kind, n, name, date):
    if kind == 'reg_start':
        return ('접수 오늘 열린다' if n == 0 else f'접수 시작까지 {n}일', f'{name}. 원서는 냈냐? 남들은 이미 넣었다더라.' if n == 0 else f'{name}. 준비 안 해 놓고 열리면 또 늦는다.')
    if kind == 'reg_end':
        return {7: ('접수 마감 7일 남았다', f'{name}. 원서 아직이면 오늘 해라.'), 3: ('원서는 냈냐? 3일 남았다', f'{name}. 마감 날 접속 폭주하면 니 책임이다.'),
                1: ('내일 접수 끝이다', f'{name}. 또 미루면 다음 회차까지 기다려라.'), 0: ('오늘이 접수 마감이다', f'{name}. 지금 안 내면 올해는 구경만 해라.')}[n]
    return {7: ('시험 7일 남았다. 잠이 오냐?', f'{name} · {date}. 아직도 책 안 폈지?'), 3: ('3일 남았다. 니 점수에 잠이 오냐?', f'{name} · {date}. 남들은 이미 마무리 중이다.'),
            1: ('내일이 시험이다', f'{name} · {date}. 지금 놀 때가 아니다.'), 0: ('오늘 시험이다', f'{name}. 일어나라. 신분증은 챙겼냐.')}[n]


def exam_events(fams, day, offs=(7, 3, 1, 0)):
    out = []
    for e in exams():
        f = family_of(e['id'])
        if f not in fams:
            continue
        for k in ('reg_start', 'reg_end', 'exam_date'):
            d = pdate(e.get(k))
            if not d:
                continue
            n = (d - day).days
            if n in offs if k != 'reg_start' else n in (0, 1, 3):
                t, b = exam_copy(k, n, short(e['name'], 30), d.strftime('%m.%d'))
                out.append({'n': n, 'k': k, 'name': e['name'], 'title': t, 'body': b, 'url': f'/exam/{e["id"]}/?src=push_sch', 'fam': f})
    uniq = {}
    for x in sorted(out, key=lambda x: (x['n'], x['k'])):
        uniq.setdefault((x['fam'], x['k'], x['n']), x)   # 같은 계열 같은 종류는 가장 가까운 회차 하나만
    return list(uniq.values())


def exam_upcoming(fams, day, within=14):
    """메일용: within 일 안의 접수 시작·마감·시험일."""
    out = []
    for e in exams():
        if family_of(e['id']) not in fams:
            continue
        for k, lab in (('reg_start', '접수 시작'), ('reg_end', '접수 마감'), ('exam_date', '시험')):
            d = pdate(e.get(k))
            if d and 0 <= (d - day).days <= within:
                out.append(((d - day).days, f'{lab} · {short(e["name"], 36)} ({d:%m.%d})', f'/exam/{e["id"]}/'))
    return sorted(out)


# ── 문제은행 ──────────────────────────────────────────────────────────────
_BK = {}


def bank(slug):
    if slug not in _BK:
        b = rd(os.path.join(EXD, 'bank', slug + '.json'))
        _BK[slug] = None if (not b or b.get('hold') or not b.get('questions')) else b
    return _BK[slug]


def pick_quiz(fams, *seed):
    slugs = [s for f in fams if f in FAMILIES for s in FAMILIES[f][2] if bank(s)]
    if not slugs:
        return None
    s = pick(sorted(set(slugs)), *seed); b = bank(s)
    qs = [(i, q) for i, q in enumerate(b['questions']) if not q.get('fig')] or list(enumerate(b['questions']))
    i, q = pick(qs, *seed, s)
    fam = next(f for f in fams if s in FAMILIES[f][2])
    return {'slug': s, 'name': b.get('name') or FAMILIES[fam][0], 'fam': FAMILIES[fam][0], 'q': q['q'], 'choices': q['choices'], 'i': i}


def quiz_msg(z, *seed):
    mk = '①②③④⑤'
    body = short(z['q'].replace('\n', ' '), 120) + '\n' + ' '.join(f'{mk[i]} {short(c, 22)}' for i, c in enumerate(z['choices'][:5]))
    ti = pick(['오늘의 문제. 풀 수 있냐?', '니 점수에 잠이 오냐? 이거나 풀어라', '이것도 모르면서 원서를 냈냐', '1문제만 풀어라. 그것도 귀찮냐?', '남들은 이미 풀었다더라'], *seed)
    return {'title': f'{z["fam"]} · {ti}', 'body': body, 'url': f'/exam/bank/{z["slug"]}/?src=push_qz', 'tag': 'jam-qz'}


# ── 분야: 마감 임박 ───────────────────────────────────────────────────────
def _live_end(a):
    return a.get('end') and not (a.get('always') or str(a['end']).startswith('2099'))


def field_deadlines(topics, day, offs=(3, 1, 0)):
    out = []
    for t in topics:
        if t in APPLY_KIND:
            for a in rd('apply.json') or []:
                if a.get('kind') in APPLY_KIND[t] and _live_end(a):
                    d = pdate(a['end'])
                    if d and (d - day).days in offs:
                        n = (d - day).days
                        ti = {'money': {3: '지원금 마감 3일 남았다. 또 놓칠래', 1: '내일 마감이다. 또 놓칠래', 0: '오늘 마감이다. 안 받아 가면 니 손해다'},
                              'house': {3: '청약 마감 3일 남았다. 월세 계속 낼 거냐', 1: '청약 내일 마감이다. 구경만 할 거냐', 0: '오늘 청약 마감이다. 내 집은 남의 얘기냐'}}[t].get(n, f'마감 {n}일 남았다. 놓치면 니 손해다')
                        out.append({'n': n, 'k': t, 'title': ti, 'body': short(a['title'], 60), 'url': f'/a/{a["id"]}/?src=push_sch', 'pv': 0})
        elif t == 'contest':
            for c in (rd('data.json') or {}).get('items') or []:
                d = pdate(c.get('end'))
                if d and (d - day).days in offs:
                    n = (d - day).days
                    out.append({'n': n, 'k': t, 'title': {3: '공모전 마감 3일 남았다. 스펙 한 줄 비었지?', 1: '내일 공모전 마감이다. 또 구경만 할래', 0: '오늘 공모전 마감이다. 안 내면 아무 일도 안 생긴다'}.get(n, f'공모전 마감 {n}일 남았다. 스펙 한 줄 비었지?'),
                                'body': short(c['title'], 50) + (f' · {c["prize"]}' if c.get('prize') else ''), 'url': f'/c/{c["id"]}/?src=push_sch', 'pv': c.get('pv') or 0})
    return sorted(out, key=lambda x: (x['n'], -x['pv']))


# ── 분야: 새 소식 ─────────────────────────────────────────────────────────
def sd_items(t):
    ks = SD_KIND.get(t)
    its = (rd('_gongmo/selfdev_data/items.json') or [])
    out = []
    for i in its:
        lib = i.get('source') in HOLD_SD_SRC
        if t == 'dev' and (lib or i['kind'] in ks):
            out.append(i)
        elif t != 'dev' and ks and i['kind'] in ks and not lib:
            out.append(i)
    return out


def field_news_all(t, day):
    """분야별 지금 올라와 있는 항목 [(key, 제목, url)]. '새 것'은 호출 쪽이 본 목록(seen)과 비교해 가린다."""
    if t in APPLY_KIND:
        L = [(a['id'], a['title'], f'/a/{a["id"]}/?src=push_nw') for a in (rd('apply.json') or []) if a.get('kind') in APPLY_KIND[t] and (not a.get('end') or str(a['end']) >= day.isoformat())]
        if t == 'money':
            L += [(i['id'], i['title'], i['url']) for i in sd_items('money')]
        return L
    if t == 'contest':
        return [(c['id'], c['title'], f'/c/{c["id"]}/?src=push_nw') for c in sorted((rd('data.json') or {}).get('items') or [], key=lambda c: -(c.get('pv') or 0)) if not c.get('end') or c['end'] >= day.isoformat()]
    if t in SD_KIND:
        seen, L = set(), []
        for i in sd_items(t):
            k = short(i['title'], 200)
            if k not in seen:
                seen.add(k); L.append((i['id'], i['title'], i['url']))
        return L
    return []


NEWS_TITLE = {'dev': '새 강좌·자격·IT 소식 {n}건. 남들은 이미 듣고 있다', 'money': '새 지원금·돈 소식 {n}건. 또 모르고 지나갈래', 'house': '새 청약·공공임대 {n}건. 월세 올랐는데 구경만 할래',
              'job': '노동·일자리 새 소식 {n}건. 모르고 일하면 호구다', 'contest': '새 공모전 {n}건. 스펙 한 줄 추가할 기회다'}


def news_msg(t, new):
    top = new[0]
    return {'title': NEWS_TITLE[t].format(n=len(new)), 'body': short(top[1], 60) + (f' 외 {len(new) - 1}건' if len(new) > 1 else ''), 'url': top[2], 'tag': 'jam-nw-' + t}


def issue_today():
    b = rd('news/brief.json') or {}
    it = b.get('items') or []
    if not it:
        return None
    import html
    hd = html.unescape(html.unescape(it[0]['headline']))
    return {'date': b.get('date') or '', 'n': len(it), 'head': hd}


def issue_msg(z):
    return {'title': f'오늘 이슈 {z["n"]}건. 뉴스도 안 보고 사냐', 'body': short(z['head'], 70), 'url': '/news/?src=push_nw#brief', 'tag': 'jam-nw-issue'}


def article_new(fams):
    L = []
    for a in rd(os.path.join(EXD, 'exam_articles.json')) or []:
        f = family_of(a.get('exam_id') or '')
        if f in fams:
            L.append((a['url'], a['title'], a['url'] + '?src=push_nw', f))
    return L


def article_msg(new):
    return {'title': '시험 새 글 올라왔다. 읽고나 지원해라', 'body': short(new[0][1], 60) + (f' 외 {len(new) - 1}건' if len(new) > 1 else ''), 'url': new[0][2], 'tag': 'jam-nw-art'}


def sched_msg(evs):
    """하루 한 통: 가장 급한 것 + 나머지 건수."""
    t = evs[0]
    return {'title': t['title'], 'body': t['body'] + (f' (외 {len(evs) - 1}건)' if len(evs) > 1 else ''), 'url': t['url'], 'tag': 'jam-sch'}


def catalog(day=None):
    """앱·/me/ 화면용 목록(assets/app/jam.json). 일정이 있으면 가장 가까운 날짜, 문제은행 수도 같이."""
    day = day or datetime.date.today()
    fams = []
    for k, (name, pre, banks) in FAMILIES.items():
        ex = [e for e in exams() if family_of(e['id']) == k]
        nxt = sorted(d for e in ex for d in (pdate(e.get(x)) for x in ('reg_start', 'reg_end', 'exam_date')) if d and d >= day)
        nb = sum(len(bank(s)['questions']) for s in banks if bank(s))
        if ex or nb:
            fams.append({'k': k, 'n': name, 'e': len(ex), 'q': nb, 'nx': nxt[0].isoformat() if nxt else ''})
    return {'fams': fams, 'fields': [{'k': k, 'n': n, 'd': d} for k, (n, d) in FIELDS.items()]}
