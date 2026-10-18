"""애드센스 사전 점검 (비공개, 2026-10-18). 사이트맵 URL 마다 <main> 안 「우리가 쓴 고유 본문」 글자 수를 센다.
고유 본문 = main 글자 − 링크 글자 − 여러 페이지에 똑같이 나오는 틀 문장(숫자는 지우고 비교, 5쪽 이상 반복이면 틀로 봄).
사용: python -X utf8 _gongmo/adsense_audit.py [--all]   (--all 이면 noindex 페이지까지 포함해 셈)"""
import os, re, sys, json, statistics, collections, html as H
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://sungprofile.cloud'

def urls():
    sm = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
    return [u.replace(SITE, '') for u in re.findall(r'<loc>([^<]+)', sm)]

def kind(u):
    p = u.strip('/').split('/')
    if not p[0]: return '홈'
    if p[0] in ('c', 'a', 'kw', 'hot', 'satire', 'mag', 'talk', 'analyst', 'lab', 'guide', 'money', 'cat'):
        return f'/{p[0]}/' + ('목록' if len(p) == 1 else '상세')
    return f'/{p[0]}/'

BLK = re.compile(r'</?(p|li|h[1-6]|div|section|tr|td|th|br|table|ul|ol|figcaption|blockquote|dd|dt)\b[^>]*>', re.I)

def parts(doc):
    m = re.search(r'<main[^>]*>(.*)</main>', doc, re.S)
    s = m.group(1) if m else ''
    s = re.sub(r'<(script|style|noscript|svg)\b.*?</\1>', ' ', s, flags=re.S | re.I)
    links = re.findall(r'<a\b([^>]*)>(.*?)</a>', s, re.S | re.I)
    ext = sum(len(re.sub(r'<[^>]+>|\s', '', t)) for a, t in links if re.search(r'href="https?://(?!sungprofile)', a))
    lk = sum(len(re.sub(r'<[^>]+>|\s', '', t)) for a, t in links)
    s2 = re.sub(r'<a\b.*?</a>', ' ', s, flags=re.S | re.I)
    s2 = BLK.sub('\n', s2)
    s2 = H.unescape(re.sub(r'<[^>]+>', ' ', s2))
    lines = [re.sub(r'\s+', ' ', l).strip() for l in s2.split('\n')]
    lines = [l for l in lines if len(l) >= 2]
    alltext = len(re.sub(r'\s', '', H.unescape(re.sub(r'<[^>]+>', '', s))))
    return lines, lk, ext, alltext

def main():
    us = urls()
    inc_all = '--all' in sys.argv
    rows, freq = [], collections.Counter()
    for u in us:
        f = os.path.join(ROOT, u.strip('/'), 'index.html')
        if not os.path.exists(f):
            rows.append((u, None)); continue
        doc = open(f, encoding='utf-8').read()
        if not inc_all and 'name="robots" content="noindex' in doc: continue
        lines, lk, ext, tot = parts(doc)
        keys = {re.sub(r'[\d,.]+', '#', l) for l in lines}
        freq.update(keys)
        rows.append((u, (lines, lk, ext, tot)))
    out, by = [], collections.defaultdict(list)
    missing = [u for u, r in rows if r is None]
    for u, r in rows:
        if r is None: continue
        lines, lk, ext, tot = r
        own = sum(len(l.replace(' ', '')) for l in lines if freq[re.sub(r'[\d,.]+', '#', l)] < 5)
        thin = own < 300 or (tot and lk / tot > .6)
        by[kind(u)].append((own, u, lk, ext, tot, thin))
    return by, missing

def report(by, missing, path=None):
    L = ['# 애드센스 사전 점검 (비공개)', '', '고유 본문 = `<main>` 글자 − 링크 글자 − 5쪽 이상 반복되는 틀 문장. 메뉴·푸터는 `<main>` 밖이라 처음부터 빠짐.', '',
         '| 유형 | 페이지 | 고유 본문 중앙값 | 하위 25% | 얇은 페이지 |', '|---|---:|---:|---:|---:|']
    tot = thin = 0
    for k in sorted(by, key=lambda k: -len(by[k])):
        v = by[k]; o = sorted(x[0] for x in v)
        q1 = o[len(o) // 4]; n_thin = sum(1 for x in v if x[5])
        tot += len(v); thin += n_thin
        L.append(f'| {k} | {len(v)} | {int(statistics.median(o))} | {q1} | {n_thin} |')
    L += ['', f'**합계 {tot}쪽 중 얇은 페이지 {thin}쪽 ({thin * 100 // max(tot, 1)}%)** — 기준: 고유 본문 300자 미만 또는 링크 글자가 본문의 60% 넘음', '']
    if missing: L += ['## 사이트맵에 있는데 파일이 없는 주소', ''] + [f'- {u}' for u in missing] + ['']
    L += ['## 얇은 페이지 목록', '']
    for k in sorted(by):
        t = sorted([x for x in by[k] if x[5]])
        if not t: continue
        L.append(f'### {k} ({len(t)})')
        L += [f'- {u} — 고유 {o}자 · 링크 {lk}자(외부 {ex}) / 전체 {tt}자' for o, u, lk, ex, tt, _ in t[:40]]
        if len(t) > 40: L.append(f'- … 외 {len(t) - 40}쪽')
        L.append('')
    s = '\n'.join(L)
    if path: open(path, 'w', encoding='utf-8').write(s)
    return s, tot, thin

if __name__ == '__main__':
    by, miss = main()
    s, tot, thin = report(by, miss)
    print(s[:6000])
