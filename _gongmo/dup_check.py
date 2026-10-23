# -*- coding: utf-8 -*-
"""공모전 중복 검사 (2026-10-19 SEO·홍보 지침 3.3). parse.py 가 이미 「정규화 제목이 같은 것」은 합쳐 두었고,
여기서는 남은 것 중 ① 공식 공고 주소가 같은 것 ② 제목 2글자 묶음 유사도 0.72 이상 + 마감일 같음 ③ 같은 주최 + 유사도 0.6 이상 + 마감 3일 이내 를 같은 공고로 본다.
dups(items) → {중복 id: 대표 id}. 대표는 정보(상금·자격·시작일·제출물)가 더 많이 채워진 쪽, 같으면 id 가 작은 쪽."""
import re, urllib.parse as up


def _bg(t):
    t = re.sub(r'\[[^\]]*\]|\([^)]*\)|20\d\d년?|제?\d+회|[^0-9A-Za-z가-힣]', '', t).lower()
    return {t[i:i + 2] for i in range(len(t) - 1)}


def _jac(a, b):
    return len(a & b) / max(1, len(a | b))


def _flat(t):
    """대괄호 안 글자는 지우지 않고 기호·공백만 걷어 낸 제목(제목 전체가 대괄호 안에 있어도 남는다)."""
    return re.sub(r'[^0-9A-Za-z가-힣]', '', t or '').lower()


def _url(u):
    u = (u or '').strip().split('#')[0]
    p = up.urlparse(u)
    q = '&'.join(x for x in p.query.split('&') if x and not re.match(r'(utm_|ref=|from=)', x))
    return (p.netloc.replace('www.', '') + p.path.rstrip('/') + ('?' + q if q else '')).lower()


def _fill(c):
    return sum(1 for k in ('pv', 'elig', 'start', 'effort', 'submit', 'region') if c.get(k)) + (1 if c.get('th') else 0)


PLACE = re.compile(r'([가-힣]{2,4}?)(?:특별자치도|특별자치시|특별시|광역시|도|시|군|구)(?=[\s\]」)]|$|[가-힣])')


def _places(t):
    return {m.group(1) for m in PLACE.finditer(re.sub(r'\[[^\]]*\]', ' ', t)) if m.group(1) not in ('공모', '도시', '시민', '군민', '구민', '도민', '지구', '연구', '청소', '부산대')}

GENERIC = re.compile(r'공모전|공모|콘테스트|경연|대회|영상|사진|숏폼|아이디어|디자인|캐릭터|포스터|슬로건|네이밍|전국|대국민|국제|함께하는|개최|모집|주최|주관|한국|대한민국')


def _core(t):
    """일반어·괄호·연도·회차를 걷어 낸 핵심 이름(고유명사 위주)."""
    t = re.sub(r'\[[^\]]*\]|\([^)]*\)|20\d\d년?|제?\d+회', '', t)
    t = GENERIC.sub('', t)
    return re.sub(r'[^0-9A-Za-z가-힣]', '', t).lower()


def _lcs(a, b):
    """가장 긴 공통 부분 문자열 길이."""
    best, prev = 0, [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def _org_compat(a, b):
    """주최가 비어 있거나 한쪽이 다른 쪽을 포함하면 같은 주최로 본다(공동 주최 표기 차이 허용)."""
    x, y = re.sub(r'\s', '', a or ''), re.sub(r'\s', '', b or '')
    return (not x) or (not y) or x in y or y in x or bool(set(re.split(r'[/,·]', a or '')) & set(re.split(r'[/,·]', b or '')) - {''})


def _latin_tokens(t):
    return {w.lower() for w in re.findall(r'[A-Za-z]{3,}', re.sub(r'\[[^\]]*\]', ' ', t))} - {'the', 'and', 'for', 'contest', 'award', 'awards', 'korea', 'seoul', 'photo', 'video', 'year', 'with'}


def same_event_by_core(a, b, min_len=5):
    """높은 확신 신호만 자동 합침(서로 다른 부문을 잘못 통합하지 않기 위해 좁게):
    마감일이 같고 주최가 호환되며, ① 일반어를 뺀 핵심 이름이 한쪽이 다른 쪽에 통째로 들어 있거나(짧은 쪽 min_len 이상)
    ② 제목에 같은 영문 고유어(KOBC, LAW REVIEW 같은 약어)가 있는 경우.
    부문이 다른 같은 주최 공모전(탄소중립 미술 ≠ 탄소중립 숏폼)은 핵심 이름이 서로 들어 있지 않아 걸리지 않는다. 나머지는 candidates() 로 사람 검토."""
    if a['end'] != b['end'] or not _org_compat(a.get('org'), b.get('org')):
        return False
    ea, eb = re.search(r'제\s?(\d+)\s?회', a['title']), re.search(r'제\s?(\d+)\s?회', b['title'])
    if ea and eb and ea.group(1) != eb.group(1):
        return False   # 회차가 다르면 다른 공모전(같은 대회의 다른 회차)
    ca, cb = _core(a['title']), _core(b['title'])
    if min(len(ca), len(cb)) >= min_len and (ca in cb or cb in ca):
        return True
    return bool(_latin_tokens(a['title']) & _latin_tokens(b['title']))


def candidates(items):
    """자동 합침은 아니지만 사람이 확인할 가치가 있는 쌍: 마감일 같음 + 주최 호환 + 핵심 이름 5글자 이상 겹침."""
    out, L = [], sorted(items, key=lambda c: c['end'])
    for i, a in enumerate(L):
        for b in L[i + 1:]:
            if b['end'] != a['end']:
                break
            if _org_compat(a.get('org'), b.get('org')) and _lcs(_core(a['title']), _core(b['title'])) >= 5:
                out.append((a['id'], b['id']))
    return out


def _first_prize(c):
    m = re.search(r'1등\s*([\d,\.]+\s*(?:억|천만|백만|만)?\s*원)', c.get('prize') or '')
    return re.sub(r'\s', '', m.group(1)) if m else ''


def _same_run(a, b):
    """2026-10-23 재심사 지침 2번: 유사 제목·동일 주최·동일 일정. 주최(공백·괄호 표기 차이 허용)와 마감이 같고 시작일 차이 1일 이하,
    1등 상금이 같으며(둘 다 있을 때) 회차가 충돌하지 않고 제목 유사도 0.6 이상이면 같은 공모전으로 본다(월간 캐릭터 제20회·팔공산 케이블카 사진 공모전)."""
    from difflib import SequenceMatcher
    if a['end'] != b['end'] or not (a.get('org') and b.get('org')):
        return False
    n = lambda t: re.sub(r'주식회사|\(주\)|[^0-9A-Za-z가-힣]', '', t or '').lower()
    oa, ob = n(a['org']), n(b['org'])
    if not (oa == ob or (min(len(oa), len(ob)) >= 4 and (oa in ob or ob in oa))):
        return False
    try:
        import datetime as dt
        if a.get('start') and b.get('start') and abs((dt.date.fromisoformat(a['start']) - dt.date.fromisoformat(b['start'])).days) > 1:
            return False
    except ValueError:
        return False
    ea, eb = re.search(r'제\s?(\d+)\s?회', a['title']), re.search(r'제\s?(\d+)\s?회', b['title'])
    if ea and eb and ea.group(1) != eb.group(1):
        return False
    pa, pb = _first_prize(a), _first_prize(b)
    if pa and pb and pa != pb:
        return False
    if not (pa or pb) and not (a.get('start') and a.get('start') == b.get('start')):
        return False
    ta = re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'\[[^\]]*\]|20\d\d년?|제?\d+회|공모전', '', a['title']))
    tb = re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'\[[^\]]*\]|20\d\d년?|제?\d+회|공모전', '', b['title']))
    CATW = re.compile(r'숏폼|숏츠|영상|사진|캐릭터|논문|슬로건|디자인|미술|포스터|웹툰|애니메이션|축제|작곡|문학|아이디어|제안|수기|공예')
    ca, cb = {x.replace('숏츠', '숏폼') for x in CATW.findall(a['title'])}, {x.replace('숏츠', '숏폼') for x in CATW.findall(b['title'])}
    r = SequenceMatcher(None, ta, tb).ratio()
    if ca and cb and not (ca <= cb or cb <= ca):
        return False   # 부문 낱말이 서로 어긋나면 다른 공모전(숏폼 영상 ≠ 미술)
    if bool(ca) != bool(cb) or not (pa or pb):
        return r >= 0.75   # 한쪽만 부문이 적혀 있거나 둘 다 1등 상금이 없으면 제목이 아주 비슷해야 한다
    return r >= (0.45 if pa and pa == pb else 0.6)   # 주최·기간·1등 상금이 모두 같으면 제목은 느슨하게


MANUAL_DUP = {'Q01475': 'Q01474'}   # 대구국제디자인어워드(DIDA) — dida.biz 접수개요 확인

AGG = re.compile(r'contestkorea|wevity|thinkyou|all-con|linkareer|campuspick|detizen|allforyoung')


def dups(items):
    by_url, out, why = {}, {}, {}
    B = {c['id']: _bg(c['title']) for c in items}
    for c in items:
        k = _url(c.get('link'))
        if k and not AGG.search(k) and len(k) > 15:   # 모음 사이트 주소는 공고마다 달라도 같은 틀이라 제외
            by_url.setdefault(k, []).append(c)
    pairs = [(g[0], x, '공고 주소 같음') for g in by_url.values() if len(g) > 1 for x in g[1:]]
    L = sorted(items, key=lambda c: c['end'])
    for i, a in enumerate(L):
        for b in L[i + 1:]:
            if b['end'] > a['end'] and (int(b['end'][8:]) - int(a['end'][8:]) > 3 or b['end'][:7] != a['end'][:7]):
                break
            pa, pb = _places(a['title']), _places(b['title'])
            if pa and pb and not (pa & pb):
                continue   # 지역 이름이 서로 다르면 다른 공모전(경남 드론 ≠ 충남 드론)
            if a['end'] == b['end'] and a.get('start') and a.get('start') == b.get('start') and _flat(a['title']) == _flat(b['title']) and len(_flat(a['title'])) >= 6:
                pairs.append((a, b, '제목 동일(대괄호·기호 차이) · 접수 기간 같음')); continue   # 「[제2회 CBS 숏폼 공모전]」 ↔ 「제2회 CBS 숏폼 공모전」(2026-10-23 P0)
            j = _jac(B[a['id']], B[b['id']])
            na, nb = re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'총상금[^｜|]*[｜|]|\[[^\]]*\]', '', a['title'])), re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'총상금[^｜|]*[｜|]|\[[^\]]*\]', '', b['title']))
            if a['end'] == b['end'] and min(len(na), len(nb)) >= 10 and (na in nb or nb in na):
                pairs.append((a, b, '제목 포함 · 마감일 같음')); continue
            if _same_run(a, b):
                pairs.append((a, b, '같은 주최 · 같은 접수 기간 · 같은 1등 상금 · 제목 유사')); continue
            if same_event_by_core(a, b):
                pairs.append((a, b, '핵심 이름 겹침 · 마감일 같음 · 주최 호환')); continue
            if (j >= 0.72 and a['end'] == b['end']) or (j >= 0.6 and a.get('org') and a.get('org') == b.get('org')):
                pairs.append((a, b, f'제목 유사도 {j:.2f}' + (' · 마감일 같음' if a['end'] == b['end'] else ' · 같은 주최')))
    ids = {c['id']: c for c in items}
    for d_, r_ in MANUAL_DUP.items():   # 공식 페이지로 같은 공모전임을 확인한 쌍(2026-10-23)
        if d_ in ids and r_ in ids:
            pairs.insert(0, (ids[r_], ids[d_], '공식 페이지 확인 — 같은 공모전'))
    for a, b, w in pairs:
        if a['id'] in out or b['id'] in out:
            continue
        rep, dup = (a, b) if (_fill(a), -int(re.sub(r'\D', '', a['id']) or 0)) >= (_fill(b), -int(re.sub(r'\D', '', b['id']) or 0)) else (b, a)
        out[dup['id']] = rep['id']; why[dup['id']] = w
    return out, why


if __name__ == '__main__':
    import json, os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    items = json.load(open(os.path.join(R, 'data.json'), encoding='utf-8'))['items']
    rows = {json.loads(l)['id']: json.loads(l) for l in open(r'C:\Users\k\Desktop\공모전_2026\data\master.jsonl', encoding='utf-8') if l.strip()}
    for c in items:
        r = rows.get(c['id'], {}); c['link'] = r.get('apply') or r.get('url')
    m, w = dups(items)
    I = {c['id']: c for c in items}
    lines = [f'# 공모전 중복 검사 — 진행 중 {len(items)}건 중 중복 {len(m)}건', '']
    for d, r in m.items():
        lines.append(f'- {w[d]}: 「{I[d]["title"]}」({d}, {I[d]["end"]}) → 대표 「{I[r]["title"]}」({r}, {I[r]["end"]})')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dup_report.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines[:40]))
