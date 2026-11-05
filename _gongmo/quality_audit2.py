# -*- coding: utf-8 -*-
"""전체 URL 품질 감사 2판 (2026-11-05 「애드센스 승인 대비 전면 품질 개선 지침」 P0). 읽기 전용 — 사이트·URL·색인은 건드리지 않는다.
quality_audit.py(10/23)의 본문 분리(adsense_audit.parts)를 재사용하고 지침 1절의 속성을 더한다:
  유형·본문 분량·생성일/수정일·출처 수·공식 1차 출처·검증 수준·중복(문장 공유/제목 유사)·독자 가치(도구·표·고유 본문)·색인 상태·내부 링크 수·만료·미확인 개수·검색 노출/클릭
  + 기술 SEO(8절): canonical·H1·title/description 중복·JSON-LD·noindex∩사이트맵·깨진 내부 링크·광고 코드
등급 A/B/C/D 는 「자동 1차 분류」다. 사람이 원문을 대조한 결과가 아니므로 보고서에 그렇게 적는다.
결과: 바탕화면 루리줍줍_품질개편\\1105\\ (저장소 밖). 사용: python -X utf8 quality_audit2.py"""
import os, re, sys, json, csv, collections, statistics, datetime, subprocess, html as H
import urllib.parse as up
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import adsense_audit as A

SITE = 'https://sungprofile.cloud'
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', '루리줍줍_품질개편', '1105'); os.makedirs(OUT, exist_ok=True)
TODAY = datetime.date.today()
SKIP_DIRS = ('_', '.git', 'assets', 'og', 'pdf', 'node_modules')
PRIVATE = ('/admin/', '/me/')

# 출처 도메인 분류
PRIMARY_SFX = ('.go.kr', 'korea.kr', '.gov', '.gov.uk', 'europa.eu', '.mil.kr')
PRIMARY_HOSTS = ('nhis.or.kr', 'nps.or.kr', 'comwel.or.kr', 'lh.or.kr', 'khug.or.kr', 'fss.or.kr', 'kinfa.or.kr', 'hrdkorea.or.kr', 'kca.go.kr', 'kosaf.go.kr', 'hf.go.kr',
                 'kdic.or.kr', 'kamco.or.kr', 'hira.or.kr', 'kcomwel.or.kr', 'bok.or.kr', 'krx.co.kr', 'sec.gov', 'kofia.or.kr', 'ccourt.go.kr', 'scourt.go.kr', 'kbo.or.kr', 'kleague.com',
                 'kice.re.kr', 'suneung.re.kr', 'ebsi.co.kr', 'kcue.or.kr', 'adiga.kr', 'work24.go.kr', 'bokjiro.go.kr', 'gov.kr', 'hometax.go.kr', 'wetax.go.kr', 'law.go.kr')
PUBLIC_SFX = ('.or.kr', '.ac.kr', '.re.kr', '.edu', '.org')
AGG_HOSTS = ('wevity.com', 'contestkorea.com', 'all-con.co.kr', 'thinkyou.co.kr', 'linkareer.com', 'campuspick.com', 'allforyoung.com', 'detizen.com')
SOCIAL = ('youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'x.com', 'twitter.com', 'band.us', 'kakao.com', 'naver.me', 'blog.naver.com', 'cafe.naver.com', 't.me', 'open.kakao.com', 'story.kakao.com', 'pf.kakao.com', 'threads.net', 'tiktok.com')

UNVER_RX = re.compile(r'미확인|확인 필요|확인하지 못|확인 못|확인되지 않|원문 대조 전|공식 공고 확인')
ANOM = [('나이 범위 시작=끝', re.compile(r'만\s?(\d{1,2})\s?[~∼\-]\s?\1\s?세')),
        ('자리표시자 노출', re.compile(r'(?<![=A-Za-z.])\bundefined\b(?![A-Za-z(])|(?<![=A-Za-z.])\bNaN\b|@@\w+@@|\{\{[^}]{0,40}\}\}|null원|Traceback \(most')),
        ('빈 금액·날짜', re.compile(r'(?<![\d,])0원\s?지원|~\s?마감|0000-00-00|1970-01-01'))]
YMYL_KIND = ('가이드', '지원금 상세', '고민 해결', '이슈', '계산기·도구')
STOP_T = re.compile(r'20\d\d(?:년|학년도)?|정리|총정리|방법|안내|기준|확인|가이드|루리 ?줍줍|\(.*?\)|[|·,:—\-「」?!]')


def pages():
    for r, ds, fs in os.walk(ROOT):
        rel = os.path.relpath(r, ROOT).replace(os.sep, '/')
        ds[:] = [d for d in ds if not d.startswith(SKIP_DIRS)]
        if 'index.html' in fs:
            yield ('/' if rel == '.' else '/' + rel + '/'), os.path.join(r, 'index.html')


def ptype(u):
    p = u.strip('/').split('/')
    if not p[0]: return '홈'
    n = len(p); h = p[0]
    if h in ('en', 'ja', 'zh', 'es', 'vi', 'id', 'th'): return '다국어' if n > 2 else '목록·허브'
    if h == 'c': return '공모전 상세' if n > 1 else '목록·허브'
    if h == 'a': return '지원금 상세' if n > 1 else '목록·허브'
    if h == 'issue': return '이슈' if n > 1 else '목록·허브'
    if h == 'guide': return '고민 해결' if n > 1 else '목록·허브'
    if h == 'money':
        if n >= 3 and p[1] == 'guide': return '목록·허브' if p[2] in ('hub', 'journey') else '가이드'
        if n >= 3 and p[1] == 'tools': return '계산기·도구'
        return '목록·허브'
    if h == 'fridge': return '레시피' if (n >= 3 and p[1] == 'r') else '목록·허브'
    if h == 'game': return '게임' if n > 1 else '목록·허브'
    if h == 'dev' and n > 1 and p[1] == 'tag': return '태그 모음'
    if h in ('class', 'dev', 'lab', 'review', 'ssul', 'satire', 'diet', 'ref', 'pick', 'play', 'v', 'w', 'hot', 'mag', 'talk', 'analyst', 'kw'): return ({'class': 'AI 교실', 'dev': '개발 지식', 'lab': '실험실', 'w': '위키', 'hot': '급상승', 'analyst': '애널리스트', 'v': '영상', 'play': '놀이'}.get(h, h)) if n > 1 else '목록·허브'
    if h in ('about', 'privacy', 'terms', 'contact'): return '정책·소개'
    if h in ('contest', 'cat', 'apply', 'event', 'today', 'all', 'qa', 'wiki', 'map', 'trend', 'watch', 'widget'): return '목록·허브'
    return h


def host_class(hs):
    hs = hs.lower().split(':')[0]
    if hs.startswith('www.'): hs = hs[4:]
    if hs.endswith(AGG_HOSTS): return 'agg'
    if hs.endswith(SOCIAL): return 'social'
    if hs.endswith(PRIMARY_SFX) or hs.endswith(PRIMARY_HOSTS): return 'primary'
    if hs.endswith(PUBLIC_SFX): return 'public'
    return 'other'


def norm_link(base, href):
    href = H.unescape(href).split('#')[0].split('?')[0]
    if not href or href.startswith(('mailto:', 'tel:', 'javascript:', 'data:')): return None
    if href.startswith(SITE): href = href[len(SITE):] or '/'
    if href.startswith('//') or re.match(r'https?://', href): return None
    if not href.startswith('/'): href = up.urljoin(base, href)
    return href


def exists(path):
    path = up.unquote(path)
    f = os.path.join(ROOT, path.strip('/').replace('/', os.sep))
    return os.path.isfile(f) or os.path.isfile(os.path.join(f, 'index.html')) or path == '/'


def git_created():
    out = {}
    try:
        r = subprocess.run(['git', '-C', ROOT, '-c', 'core.quotepath=false', 'log', '--diff-filter=A', '--format=@%cs', '--name-only', '--', '*.html'], capture_output=True, text=True, encoding='utf-8', timeout=180)
        day = ''
        for l in r.stdout.splitlines():
            if l.startswith('@'): day = l[1:]
            elif l.endswith('index.html'):
                u = '/' + l[:-len('index.html')]
                out[u] = day   # log 는 최신→과거 순이라 마지막에 덮어쓴 값이 가장 이른 추가일
    except Exception as e:
        print('git 생성일 조회 실패', e)
    return out


def main():
    smap, sm_last = set(), {}
    for f in os.listdir(ROOT):
        if f.startswith('sitemap') and f.endswith('.xml') and f != 'sitemap_index.xml':
            t = open(os.path.join(ROOT, f), encoding='utf-8').read()
            for loc, lm in re.findall(r'<loc>([^<]+)</loc>(?:\s*<lastmod>([^<]+)</lastmod>)?', t):
                u = up.unquote(loc.replace(SITE, '')); smap.add(u)
                if lm: sm_last[u] = lm[:10]
    lastmod = {}
    try: lastmod = {k: v[1] for k, v in json.load(open(os.path.join(HERE, 'lastmod.json'), encoding='utf-8')).items()}
    except Exception: pass
    gsc, insp, land = {}, {}, collections.Counter()
    try:
        for p in json.load(open(os.path.join(HERE, 'gsc_daily.json'), encoding='utf-8')).get('pages', []): gsc[up.unquote(p['page'].replace(SITE, ''))] = (p.get('impr', 0), p.get('clicks', 0))
    except Exception: pass
    try:
        for k, v in json.load(open(os.path.join(HERE, 'index_state.json'), encoding='utf-8')).get('urls', {}).items(): insp[up.unquote(k.replace(SITE, ''))] = v.get('state', '')
    except Exception: pass
    try:
        for d in json.load(open(os.path.join(HERE, 'inflow_daily.json'), encoding='utf-8')).get('days', []):
            for u, n in d.get('landing', []): land[u] += n
    except Exception: pass
    live_c, live_a = set(), set()
    try: live_c = {i['id'] for i in json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))['items']}
    except Exception: pass
    try: live_a = {i['id'] for i in json.load(open(os.path.join(ROOT, 'apply.json'), encoding='utf-8'))}
    except Exception: pass
    created = git_created()

    recs, freq = [], collections.Counter()
    inlinks, inlinks_main = collections.Counter(), collections.Counter()
    broken = collections.defaultdict(set)
    titles, descs = collections.defaultdict(list), collections.defaultdict(list)
    for u, f in pages():
        if u.startswith(PRIVATE): continue
        doc = open(f, encoding='utf-8', errors='replace').read()
        m = re.search(r'<main[^>]*>(.*)</main>', doc, re.S); mh = m.group(1) if m else ''
        lines, lk, ext, tot = A.parts(doc)
        freq.update({re.sub(r'[\d,.]+', '#', l) for l in lines})
        title = H.unescape((re.search(r'<title>(.*?)</title>', doc, re.S) or [0, ''])[1]).strip()
        desc = H.unescape((re.search(r'<meta name="description" content="([^"]*)"', doc) or [0, ''])[1]).strip()
        canon = (re.search(r'<link rel="canonical" href="([^"]*)"', doc) or [0, ''])[1]
        noindex = bool(re.search(r'<meta name="robots" content="[^"]*noindex', doc))
        h1 = len(re.findall(r'<h1\b', doc))
        ld_bad = 0; ld_n = 0
        for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
            ld_n += 1
            try: json.loads(j)
            except Exception: ld_bad += 1
        # 링크
        hosts = collections.Counter()
        for a in re.findall(r'<a\b[^>]*href="([^"]+)"', mh):
            mm = re.match(r'https?://([^/]+)', a)
            if mm and 'sungprofile.cloud' not in mm.group(1): hosts[host_class(mm.group(1))] += 1
        seen_all, seen_main = set(), set()
        doc_ns = re.sub(r'<script\b.*?</script>', ' ', doc, flags=re.S | re.I)
        mh_ns = re.sub(r'<script\b.*?</script>', ' ', mh, flags=re.S | re.I)
        for a in re.findall(r'<a\b[^>]*href="([^"]+)"', doc_ns):
            t = norm_link(u, a)
            if t is None: continue
            if t.startswith(('/admin', '/me', '/api', '/cdn-cgi')): continue
            if not exists(t): broken[up.unquote(t)].add(u)
            t2 = up.unquote(t if t.endswith('/') or '.' in t.rsplit('/', 1)[-1] else t + '/')
            if t2 != u: seen_all.add(t2)
        for a in re.findall(r'<a\b[^>]*href="([^"]+)"', mh_ns):
            t = norm_link(u, a)
            if t:
                t2 = up.unquote(t if t.endswith('/') or '.' in t.rsplit('/', 1)[-1] else t + '/')
                if t2 != u: seen_main.add(t2)
        for t in seen_all: inlinks[t] += 1
        for t in seen_main: inlinks_main[t] += 1
        mtext = H.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style|noscript|svg)\b.*?</\1>', ' ', mh, flags=re.S | re.I)))
        anom = [n for n, rx in ANOM if rx.search(mtext)]
        ctrl = len([t for t in re.findall(r'<(input|select|textarea)([^>]*)>', mh) if not re.search(r'type="?(hidden|submit|checkbox)', t[1])])
        stage = (re.search(r'현재 「([^」]+)」', mtext) or [0, ''])[1]
        recs.append(dict(u=u, lines=lines, lk=lk, tot=tot, title=title, desc=desc, canon=canon, noindex=noindex, h1=h1, ld_n=ld_n, ld_bad=ld_bad, hosts=hosts,
                         unver=len(UNVER_RX.findall(mtext)), anom=anom, ctrl=ctrl, tables=mh.count('<table'), lis=mh.count('<li'), stage=stage,
                         agg_only=('수집처 공고 페이지' in mtext), has_date=bool(re.search(r'기준|갱신|확인일|업데이트|20\d\d[-.년 ]\s?\d{1,2}[-.월 ]', mtext)),
                         ads=('adsbygoogle' in doc or 'pagead2.googlesyndication' in doc), out_main=len(seen_main), mlen=len(re.sub(r'\s', '', mtext))))
        if not noindex:
            titles[title].append(u); descs[desc].append(u)

    # 문장 공유 기반 중복: 20자 이상·사이트 전체 2~30쪽에만 나오는 줄을 「틀이 아닌 공유 문장」으로 보고, 한 상대와 공유한 글자 비율의 최댓값
    key = lambda l: re.sub(r'[\d,.]+', '#', l)
    inv = collections.defaultdict(list)
    for i, r in enumerate(recs):
        r['body'] = [l for l in r['lines'] if len(l) >= 20 and freq[key(l)] <= 30]
        for k in {key(l) for l in r['body']}:
            if freq[k] >= 2: inv[k].append(i)
    for i, r in enumerate(recs):
        share = collections.Counter(); base = sum(len(l) for l in r['body'])
        for l in r['body']:
            k = key(l)
            if freq[k] >= 2:
                for j in inv[k]:
                    if j != i: share[j] += len(l)
        if share and base:
            j, n = share.most_common(1)[0]
            r['dup_ratio'] = round(min(n / base, 1), 2); r['dup_with'] = recs[j]['u']
        else:
            r['dup_ratio'] = 0; r['dup_with'] = ''
    # 제목 유사(같은 유형 안, 글자 2-gram 자카드 ≥ 0.75) — 표현만 다른 같은 주제 후보
    def grams(t):
        t = re.sub(r'\s+', '', STOP_T.sub(' ', t.split(' | ')[0]))
        return {t[i:i + 2] for i in range(len(t) - 1)}
    bytype = collections.defaultdict(list)
    for i, r in enumerate(recs):
        r['type'] = ptype(r['u']); r['tg'] = grams(r['title'])
        if not r['noindex'] and r['type'] in ('가이드', '고민 해결', '이슈', '공모전 상세', '지원금 상세', '게임', 'AI 교실', '개발 지식', '위키'): bytype[r['type']].append(i)
    for r in recs: r['title_sim'] = 0; r['title_sim_with'] = ''
    for tp, idx in bytype.items():
        for a in range(len(idx)):
            ga = recs[idx[a]]['tg']
            if len(ga) < 5: continue
            for b in range(a + 1, len(idx)):
                gb = recs[idx[b]]['tg']
                if len(gb) < 5: continue
                inter = len(ga & gb)
                if inter * 4 < len(ga) * 3 and inter * 4 < len(gb) * 3: continue
                s = inter / len(ga | gb)
                if s >= 0.75:
                    for x, y in ((idx[a], idx[b]), (idx[b], idx[a])):
                        if s > recs[x]['title_sim']: recs[x]['title_sim'] = round(s, 2); recs[x]['title_sim_with'] = recs[y]['u']

    rows = []
    for r in recs:
        u = r['u']; tp = r['type']
        own = sum(len(l.replace(' ', '')) for l in r['lines'] if freq[key(l)] < 5)
        hs = r['hosts']; src_n = hs['primary'] + hs['public'] + hs['other'] + hs['agg']
        expired = (tp == '공모전 상세' and u.strip('/').split('/')[-1] not in live_c) or (tp == '지원금 상세' and u.strip('/').split('/')[-1] not in live_a)
        stale_title = bool(re.search(r'202[0-5]', r['title'])) and not re.search(r'202[6-9]', r['title'])
        if tp == '공모전 상세':
            ver = r['stage'] or ('수집처 기준' if r['agg_only'] else '표기 없음')
        else:
            ver = 'PRIMARY_LINKED(공식 1차 출처 링크 있음·대조 기록 없음)' if hs['primary'] else ('PUBLIC_LINKED(공공·단체 출처 링크)' if hs['public'] else ('SECONDARY_LINKED(언론 등 2차 출처 링크)' if hs['other'] else 'NO_SOURCE(출처 링크 없음)'))
        functional = r['ctrl'] >= 1 or tp in ('계산기·도구',)
        canon_ok = (not r['canon']) or up.unquote(r['canon'].replace(SITE, '')) == u
        # ---- 등급(자동 1차 분류) ----
        why = []
        g = 'B'
        hub = tp in ('목록·허브', '홈', '정책·소개', '태그 모음')
        if r['mlen'] < 150 and not functional: g = 'D'; why.append('본문 거의 없음')
        if not r['title'] or r['h1'] == 0: g = 'D'; why.append('제목/H1 없음')
        if '자리표시자 노출' in r['anom'] and tp not in ('개발 지식', '다국어', 'AI 교실'): g = 'D'; why.append('자리표시자 노출')
        if expired and not r['noindex']: g = 'D'; why.append('만료됐는데 색인 대상')
        if g != 'D':
            c = []
            if not hub and not functional and own < 400 and r['tables'] == 0: c.append(f'고유 본문 {own}자')
            if tp == '태그 모음' and r['out_main'] < 5: c.append(f'글 {r["out_main"]}개뿐인 태그 모음')
            if r['dup_ratio'] >= 0.5 and (not hub or sum(len(l) for l in r['body']) >= 300): c.append(f'문장 공유 {int(r["dup_ratio"] * 100)}%')
            if r['title_sim'] >= 0.85: c.append('제목이 거의 같은 글 있음')
            if tp == '이슈':
                if src_n == 0: c.append('출처 링크 없음')
            elif tp in YMYL_KIND and not hs['primary'] and not hs['public'] and not functional: c.append('공식·공공 출처 링크 없음')
            if tp == '공모전 상세' and (r['agg_only'] or r['stage'] in ('', '수집 완료')): c.append('공식 원문 대조 전')
            if not hub and tp != '이슈' and r['unver'] >= (10 if tp in ('가이드', '고민 해결') else 6): c.append(f'미확인 표기 {r["unver"]}곳')
            if '나이 범위 시작=끝' in r['anom'] or '빈 금액·날짜' in r['anom']: c.append('수치 이상 의심(원문 대조 필요)')
            if expired: c.append('만료(색인 제외 상태)')
            if c: g = 'C'; why += c
            else:
                a_ok = (own >= 1200 or functional or (hub and (r['ctrl'] or own >= 300))) and r['dup_ratio'] < 0.25 and (r['unver'] <= 2 or tp == '이슈' or hub) and (hs['primary'] or hs['public'] or tp in ('레시피', '게임', 'AI 교실', '개발 지식', '목록·허브', '홈', '정책·소개', '계산기·도구')) and (r['has_date'] or hub)
                if a_ok: g = 'A'
                else:
                    if own < 1200 and not functional and not hub: why.append(f'고유 본문 {own}자(1,200자 미만)')
                    if r['dup_ratio'] >= 0.25: why.append(f'문장 공유 {int(r["dup_ratio"] * 100)}%')
                    if r['unver'] > 2 and tp != '이슈' and not hub: why.append(f'미확인 표기 {r["unver"]}곳')
                    if not (hs['primary'] or hs['public']) and tp not in ('레시피', '게임', 'AI 교실', '개발 지식', '목록·허브', '홈', '정책·소개', '계산기·도구'): why.append('공식·공공 출처 링크 없음')
                    if not r['has_date'] and not hub: why.append('기준일 표기 없음')
        rows.append(dict(url=u, type=tp, section=u.strip('/').split('/')[0] or '(홈)', title=r['title'], grade=g, why=' / '.join(why),
                         indexable=not r['noindex'], in_sitemap=u in smap, gsc_inspect=insp.get(u, ''), created=created.get(u, ''), modified=sm_last.get(u) or lastmod.get(u, ''),
                         main_chars=r['mlen'], unique_chars=own, tool=functional, tables=r['tables'],
                         src_total=src_n, src_primary=hs['primary'], src_public=hs['public'], src_agg=hs['agg'], src_other=hs['other'], verify=ver,
                         unverified_marks=r['unver'], anomalies=','.join(r['anom']), expired=expired, stale_title=stale_title,
                         dup_ratio=r['dup_ratio'], dup_with=r['dup_with'], title_sim=r['title_sim'], title_sim_with=r['title_sim_with'],
                         inlinks=inlinks[u], inlinks_body=inlinks_main[u], outlinks_body=r['out_main'],
                         gsc_impr=gsc.get(u, (0, 0))[0], gsc_clicks=gsc.get(u, (0, 0))[1], landing_visits=land.get(u, 0),
                         h1=r['h1'], canonical_ok=canon_ok, has_canonical=bool(r['canon']), jsonld=r['ld_n'], jsonld_bad=r['ld_bad'], ads_code=r['ads'], desc_len=len(r['desc'])))
    with open(os.path.join(OUT, 'pages_audit2.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(os.path.join(OUT, 'pages_audit2.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    # ---- 기술 SEO 요약 ----
    idx = [x for x in rows if x['indexable']]
    tech = {
        '전체 페이지(비공개 제외)': len(rows), '색인 대상': len(idx), 'noindex': len(rows) - len(idx),
        '사이트맵 주소': len(smap), 'noindex 인데 사이트맵에 있음': [x['url'] for x in rows if not x['indexable'] and x['in_sitemap']],
        '사이트맵에 있는데 파일 없음': sorted(u for u in smap if not exists(u)),
        '색인 대상인데 사이트맵에 없음': len([x for x in idx if not x['in_sitemap']]),
        'canonical 없음(색인 대상)': [x['url'] for x in idx if not x['has_canonical']][:50],
        'canonical 불일치': [x['url'] for x in idx if not x['canonical_ok']][:50],
        'H1 없음': [x['url'] for x in idx if x['h1'] == 0][:50], 'H1 2개 이상': len([x for x in idx if x['h1'] > 1]),
        'JSON-LD 파싱 오류': [x['url'] for x in rows if x['jsonld_bad']][:50],
        '중복 title 묶음': len([t for t, v in titles.items() if len(v) > 1]), '중복 description 묶음': len([t for t, v in descs.items() if len(v) > 1 and t]),
        'description 없음(색인 대상)': len([x for x in idx if x['desc_len'] == 0]),
        '광고 코드 없음(색인 대상)': len([x for x in idx if not x['ads_code']]),
        '깨진 내부 링크 대상 수': len(broken),
    }
    json.dump({'tech': tech, 'dup_titles': {t: v for t, v in titles.items() if len(v) > 1}, 'dup_descs': {t: v for t, v in descs.items() if len(v) > 1 and t},
               'broken': {k: sorted(v)[:10] for k, v in broken.items()}}, open(os.path.join(OUT, 'tech_seo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 요약 ----
    L = [f'# 전체 URL 품질 감사 (자동 1차 분류) — {TODAY}', '',
         f'- 페이지 {len(rows)}쪽(비공개 /admin/·/me/ 제외) · 색인 대상 {len(idx)}쪽 · 사이트맵 {len(smap)}건',
         '- 등급은 규칙으로 매긴 1차 분류이고, 사람이 원문을 대조한 결과가 아닙니다.', '',
         '## 유형별 분포와 등급 (색인 대상만)', '', '유형|쪽수|A|B|C|D|고유 본문 중앙값|공식 1차 출처 있음|검색 노출 있음', '---|---:|---:|---:|---:|---:|---:|---:|---:']
    T = collections.defaultdict(list)
    for x in idx: T[x['type']].append(x)
    for tp, v in sorted(T.items(), key=lambda kv: -len(kv[1])):
        c = collections.Counter(x['grade'] for x in v)
        L.append(f"{tp}|{len(v)}|{c['A']}|{c['B']}|{c['C']}|{c['D']}|{int(statistics.median([x['unique_chars'] for x in v]))}|{sum(1 for x in v if x['src_primary'])}|{sum(1 for x in v if x['gsc_impr'])}")
    ca = collections.Counter(x['grade'] for x in idx); cn = collections.Counter(x['grade'] for x in rows if not x['indexable'])
    L += ['', f"**색인 대상 합계** A {ca['A']} · B {ca['B']} · C {ca['C']} · D {ca['D']}", f"**noindex 페이지** A {cn['A']} · B {cn['B']} · C {cn['C']} · D {cn['D']} (참고)", '',
          '## C·D 사유 상위 (색인 대상)', '']
    wc = collections.Counter()
    for x in idx:
        if x['grade'] in 'CD':
            for w_ in x['why'].split(' / '): wc[re.sub(r'\d+', '#', w_)] += 1
    L += [f'- {k}: {n}쪽' for k, n in wc.most_common(15)]
    L += ['', '## 기술 SEO', ''] + [f'- {k}: {v if not isinstance(v, list) else str(len(v)) + "건 " + ", ".join(v[:8])}' for k, v in tech.items()]
    open(os.path.join(OUT, '00_감사요약.md'), 'w', encoding='utf-8').write('\n'.join(L))
    print('\n'.join(L))


if __name__ == '__main__':
    main()
