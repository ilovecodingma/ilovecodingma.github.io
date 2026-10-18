"""매 빌드 건강 점검 (2026-10-18 연구 세션 요청: 사람이 손 안 대도 유지).
깨진 내부 링크·빈 페이지·중복 제목·noindex 비율·사이트맵 수·고아 페이지를 세어
/admin/health.json(관리자 화면용, 숫자만)과 _gongmo/health_log.txt(비공개)에 남긴다."""
import os, re, json, datetime, collections

SKIP = ('.git', '_gongmo', '_trend', 'assets', 'w')


def run(root, sitemap_urls, noindex):
    pages, titles, links, inbound = {}, collections.defaultdict(list), collections.Counter(), collections.Counter()
    broken = collections.Counter()
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP]
        if 'index.html' not in fs:
            continue
        u = '/' + os.path.relpath(d, root).replace('\\', '/').strip('.').strip('/') + '/'
        u = '/' if u == '//' else u
        s = open(os.path.join(d, 'index.html'), encoding='utf-8', errors='ignore').read()
        m = re.search(r'<main[^>]*>(.*)</main>', s, re.S)
        txt = len(re.sub(r'\s', '', re.sub(r'<[^>]+>', '', re.sub(r'<(script|style)\b.*?</\1>', '', m.group(1) if m else '', flags=re.S))))
        pages[u] = txt
        t = re.search(r'<title>([^<]*)', s)
        if t and 'noindex' not in s[:3000]:
            titles[t.group(1)].append(u)
        for h in set(re.findall(r'href="(/[^"#?]*)', s)):
            if h.startswith('//') or h.startswith('/assets/') or h.startswith('/w/') or '.' in h.rsplit('/', 1)[-1]:
                continue
            hh = h if h.endswith('/') else h + '/'
            inbound[hh] += 1
            if not os.path.exists(os.path.join(root, hh.strip('/'), 'index.html')) and hh != '/':
                broken[hh] += 1
    empty = [u for u, n in pages.items() if n < 50 and not u.startswith(('/admin/', '/me/', '/community/'))]
    dup = {t: us for t, us in titles.items() if len(us) > 1}
    orphan = [u for u in sitemap_urls if u not in noindex and inbound[u] == 0 and u != '/']
    r = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'pages': len(pages), 'sitemap': len([u for u in sitemap_urls if u not in noindex]),
         'noindex': len(noindex), 'noindex_pct': round(len(noindex) * 100 / max(1, len(sitemap_urls))),
         'broken': len(broken), 'broken_top': broken.most_common(5), 'empty': len(empty), 'empty_top': empty[:5],
         'dup_titles': len(dup), 'dup_top': list(dup.items())[:3], 'orphans': len(orphan), 'orphan_top': orphan[:5]}
    warn = []
    if r['broken']: warn.append(f'깨진 내부 링크 {r["broken"]}개')
    if r['empty']: warn.append(f'빈 페이지 {r["empty"]}개')
    if r['dup_titles'] > 5: warn.append(f'중복 제목 {r["dup_titles"]}개')
    if r['orphans']: warn.append(f'고아 페이지 {r["orphans"]}개')
    if r['sitemap'] < 300: warn.append(f'사이트맵 {r["sitemap"]}쪽으로 줄었어요')
    if r['noindex_pct'] > 75: warn.append(f'검색 제외 비율 {r["noindex_pct"]}%')
    r['warn'] = warn
    os.makedirs(os.path.join(root, 'admin'), exist_ok=True)
    json.dump(r, open(os.path.join(root, 'admin', 'health.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'health_log.txt'), 'a', encoding='utf-8') as f:
        f.write(f'{r["at"]} 사이트맵 {r["sitemap"]} noindex {r["noindex_pct"]}% 깨짐 {r["broken"]} 빈 {r["empty"]} 중복제목 {r["dup_titles"]} 고아 {r["orphans"]} {"⚠️ " + ", ".join(warn) if warn else "정상"}\n')
    return r
