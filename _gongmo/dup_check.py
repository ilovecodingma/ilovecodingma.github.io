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
            j = _jac(B[a['id']], B[b['id']])
            na, nb = re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'총상금[^｜|]*[｜|]|\[[^\]]*\]', '', a['title'])), re.sub(r'[^0-9A-Za-z가-힣]', '', re.sub(r'총상금[^｜|]*[｜|]|\[[^\]]*\]', '', b['title']))
            if a['end'] == b['end'] and min(len(na), len(nb)) >= 10 and (na in nb or nb in na):
                pairs.append((a, b, '제목 포함 · 마감일 같음')); continue
            if (j >= 0.72 and a['end'] == b['end']) or (j >= 0.6 and a.get('org') and a.get('org') == b.get('org')):
                pairs.append((a, b, f'제목 유사도 {j:.2f}' + (' · 마감일 같음' if a['end'] == b['end'] else ' · 같은 주최')))
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
