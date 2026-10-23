# -*- coding: utf-8 -*-
"""콘텐츠 품질 감사 (2026-10-23, 애드센스 재심사 준비 PHASE 1).  읽기 전용 — 사이트·URL·색인은 건드리지 않는다.
adsense_audit.py 의 본문 분리(parts)·분류(kind)를 재사용하고, 기능·출처·갱신일·중복(simhash)·유입(GSC)을 더해 페이지별 점수와 분류를 낸다.
결과는 저장소 밖(바탕화면 루리줍줍_품질개편)에 쓴다. 사용: python -X utf8 quality_audit.py"""
import os, re, sys, json, csv, hashlib, collections, statistics, html as H
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import adsense_audit as A

OUT = os.path.expanduser(r'~\Desktop\루리줍줍_품질개편'); os.makedirs(OUT, exist_ok=True)
SKIP = ('_', '.git', 'assets', 'og', 'pdf')


def pages():
    for r, ds, fs in os.walk(ROOT):
        rel = os.path.relpath(r, ROOT).replace(os.sep, '/')
        ds[:] = [d for d in ds if not d.startswith(SKIP) or d in ('og',) and False]
        if 'index.html' in fs and rel != '.' and not rel.startswith(('_', '.git', 'assets')):
            yield '/' + rel + '/', os.path.join(r, 'index.html')
        elif 'index.html' in fs and rel == '.':
            yield '/', os.path.join(r, 'index.html')


def sitemap_set():
    s = set()
    for f in os.listdir(ROOT):
        if f.startswith('sitemap') and f.endswith('.xml'):
            s |= {u.replace(A.SITE, '') for u in re.findall(r'<loc>([^<]+)', open(os.path.join(ROOT, f), encoding='utf-8').read())}
    return s


def simhash(tokens):
    v = [0] * 64
    for t in tokens:
        h = int(hashlib.md5(t.encode('utf-8')).hexdigest()[:16], 16)
        for i in range(64): v[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(64) if v[i] > 0)


def main():
    smap = sitemap_set()
    gsc = {}
    try:
        g = json.load(open(os.path.join(HERE, 'gsc_daily.json'), encoding='utf-8'))
        for p in g.get('pages', []): gsc[p['page'].replace(A.SITE, '')] = (p.get('impr', 0), p.get('clicks', 0))
    except Exception: pass
    recs, freq = [], collections.Counter()
    for u, f in pages():
        doc = open(f, encoding='utf-8').read()
        m = re.search(r'<main[^>]*>(.*)</main>', doc, re.S); mh = m.group(1) if m else ''
        lines, lk, ext, tot = A.parts(doc)
        freq.update({re.sub(r'[\d,.]+', '#', l) for l in lines})
        title = (re.search(r'<title>(.*?)</title>', doc, re.S) or [0, ''])[1]
        recs.append(dict(u=u, doc=doc, mh=mh, lines=lines, lk=lk, ext=ext, tot=tot, title=H.unescape(title).strip(), noindex='name="robots" content="noindex' in doc))
    rows = []
    for r in recs:
        uniq_lines = [l for l in r['lines'] if freq[re.sub(r'[\d,.]+', '#', l)] < 5]
        own = sum(len(l.replace(' ', '')) for l in uniq_lines); text = ' '.join(uniq_lines)
        ctrl = len([t for t in re.findall(r'<(input|select|textarea)([^>]*)>', r['mh']) if 'type="hidden"' not in t[1] and 'type=hidden' not in t[1] and 'type="submit"' not in t[1]])   # 실제 입력 요소만(찜·공유 버튼은 도구로 세지 않는다)
        tables = r['mh'].count('<table'); lis = r['mh'].count('<li')
        mtext = re.sub(r'<[^>]+>', ' ', r['mh'])
        has_date = bool(re.search(r'기준|갱신|확인일|업데이트|20\d\d[-.년 ]\s?\d{1,2}[-.월 ]', mtext))
        digits = len(re.findall(r'\d', text)); dens = digits * 1000 / max(len(text), 1)
        sec = r['u'].strip('/').split('/')[0] or '(홈)'
        toks = [text[i:i + 3] for i in range(0, max(len(text) - 2, 0), 2)] if own >= 60 else []
        rows.append(dict(u=r['u'], section=sec, kind=A.kind(r['u']), title=r['title'], noindex=r['noindex'], in_sitemap=r['u'] in smap,
                         main_chars=r['tot'], unique_chars=own, link_ratio=round(r['lk'] / r['tot'], 2) if r['tot'] else 1, tool=ctrl >= 1, tables=tables, lists=lis,
                         ext_links=r['ext'] > 0, has_date=has_date, num_density=round(dens, 1), sh=simhash(toks) if toks else None,
                         gsc_impr=gsc.get(r['u'], (0, 0))[0], gsc_clicks=gsc.get(r['u'], (0, 0))[1]))
    # 중복 묶음: 같은 구역 안에서 simhash 해밍거리 ≤ 4 (본문 유사). 앞 16비트 버킷으로 후보를 좁힌다
    bysec = collections.defaultdict(list)
    for i, x in enumerate(rows):
        if x['sh'] is not None and not x['noindex']: bysec[x['section']].append(i)
    parent = list(range(len(rows)))
    find = lambda a: a if parent[a] == a else find(parent[a])
    for sec, idx in bysec.items():
        for ai in range(len(idx)):
            for bi in range(ai + 1, len(idx)):
                a, b = idx[ai], idx[bi]
                if bin(rows[a]['sh'] ^ rows[b]['sh']).count('1') <= 4: parent[find(a)] = find(b)
    grp = collections.defaultdict(list)
    for i in range(len(rows)): grp[find(i)].append(i)
    for g, idx in grp.items():
        for i in idx: rows[i]['dup_group'] = ('D%04d' % g) if len(idx) > 1 and not rows[i]['noindex'] else ''; rows[i]['dup_size'] = len(idx) if len(idx) > 1 and not rows[i]['noindex'] else 1
    for x in rows:
        s = min(x['unique_chars'], 1200) / 1200 * 40
        s += 20 if x['tool'] else (10 if x['tables'] else (5 if x['lists'] >= 3 else 0))
        s += (10 if x['ext_links'] else 0) + (10 if x['has_date'] else 0) + (10 if x['num_density'] >= 10 else 0)
        s -= 25 if x['dup_size'] > 1 else 0
        s -= 10 if x['link_ratio'] > .6 else 0
        x['score'] = round(max(0, min(100, s)))
        thin = x['unique_chars'] < 250 and not x['tool'] and x['tables'] == 0
        if x['noindex']: x['verdict'] = '색인 제외 유지(현행 noindex)'
        elif x['dup_size'] > 1: x['verdict'] = '통합 검토'
        elif thin: x['verdict'] = '색인 제외 검토'
        elif x['score'] < 55: x['verdict'] = '개선'
        else: x['verdict'] = '유지'
        x['traffic'] = x['gsc_impr'] > 0 or x['gsc_clicks'] > 0
    for x in rows: x.pop('sh', None)
    with open(os.path.join(OUT, 'pages_audit.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(os.path.join(OUT, 'pages_audit.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    # 요약
    S = collections.defaultdict(list)
    for x in rows: S[x['section']].append(x)
    L = ['구역|쪽수|색인대상|유지|개선|통합|제외검토|현행noindex|고유본문 중앙값|도구있음|출처링크|갱신일표기|유입있음', '---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:']
    for sec, v in sorted(S.items(), key=lambda kv: -len(kv[1])):
        idx = [x for x in v if not x['noindex']]; c = collections.Counter(x['verdict'] for x in v)
        med = int(statistics.median([x['unique_chars'] for x in idx])) if idx else 0
        L.append(f"{sec}|{len(v)}|{len(idx)}|{c['유지']}|{c['개선']}|{c['통합 검토']}|{c['색인 제외 검토']}|{c['색인 제외 유지(현행 noindex)']}|{med}|{sum(x['tool'] for x in idx)}|{sum(x['ext_links'] for x in idx)}|{sum(x['has_date'] for x in idx)}|{sum(x['traffic'] for x in v)}")
    open(os.path.join(OUT, 'section_summary.md'), 'w', encoding='utf-8').write('\n'.join(L))
    tot = collections.Counter(x['verdict'] for x in rows)
    print('전체', len(rows), '쪽 / 색인대상', sum(not x['noindex'] for x in rows), '/ 사이트맵', sum(x['in_sitemap'] for x in rows))
    print(dict(tot)); print(); print('\n'.join(L[:24]))


if __name__ == '__main__':
    main()
