# -*- coding: utf-8 -*-
"""구글 색인 요청 후보 (2026-11-06 마케터 요청 · 일 방문 1,000 전략 1순위). 읽기 전용 — 색인 요청 자체는 홍보 세션이 서치 콘솔 화면에서 한다.
「다음·빙·네이버 검색으로는 들어오는데 구글에는 색인되지 않은 글」을 찾는다:
  ① D1 hit_daily 에서 최근 14일 채널별 첫 페이지 방문 수 ② 사이트맵에 있는 주소만 ③ 서치 콘솔 URL 검사 API 로 구글 색인 상태 조회(3일 안에 본 주소는 다시 묻지 않음)
  ④ 색인 안 된 주소를 다른 검색엔진 방문 수 순으로 정렬 → 최근 7일 안에 넘긴 적 없는 10건을 홍보 outbox 에 저장
사용: python -X utf8 index_candidates.py [--days 14] [--n 10] [--check 80]"""
import os, re, sys, json, time, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SITE = 'https://sungprofile.cloud'
STATE = os.path.join(HERE, 'index_state_all.json')      # 주소별 구글 색인 상태(조회 시각 포함)
LOG = os.path.join(HERE, 'index_req_log.json')          # 홍보에 넘긴 주소와 날짜
OUTBOX = r'C:\Users\k\tools\promo_share\outbox\index_req'
OTHER = ('다음', '빙', '네이버 검색')


def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    import inflow_report as IR
    from gsc import session, PROP
    days, n_out, n_check = arg('--days', 14), arg('--n', 10), arg('--check', 80)
    now = datetime.datetime.now(); today = now.strftime('%Y-%m-%d')
    since = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9) - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    rows = IR.query('SELECT ch, path, SUM(v) AS v FROM hit_daily WHERE day >= ? GROUP BY ch, path', [since])
    other, google = collections.Counter(), collections.Counter()
    for r in rows:
        p = r['path'].split('?')[0]
        if any(k in r['ch'] for k in OTHER):
            other[p] += r['v']
        elif '구글' in r['ch']:
            google[p] += r['v']
    smap = set()
    for fn in os.listdir(ROOT):
        if fn.startswith('sitemap') and fn.endswith('.xml') and fn != 'sitemap_index.xml':
            smap |= {u.replace(SITE, '') for u in re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, fn), encoding='utf-8').read())}
    short = set()   # 곧 내려가는 단기 이슈(보관 14일 미만)는 색인 요청을 쓰지 않는다
    idir = os.path.join(HERE, 'issues')
    for fn in os.listdir(idir) if os.path.isdir(idir) else []:
        if fn.endswith('.json'):
            try:
                c = json.load(open(os.path.join(idir, fn), encoding='utf-8'))
                if int(c.get('keep_days', 4)) < 14:
                    short.add(f'/issue/{c["slug"]}/')
            except Exception:
                pass
    cand = [(v, p) for p, v in other.most_common() if p in smap and p != '/' and p not in short][:n_check]
    st = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    try:   # /money/ 구역은 index_state.py 가 이미 조회한 값이 있으면 이어 쓴다
        for u, v in json.load(open(os.path.join(HERE, 'index_state.json'), encoding='utf-8')).get('urls', {}).items():
            p = u.replace(SITE, '')
            if p not in st or st[p].get('at', '') < v.get('at', ''):
                st[p] = v
    except Exception:
        pass
    fresh = (now - datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
    S = session(); asked = err = 0
    for _v, p in cand:
        if st.get(p, {}).get('at', '') >= fresh:
            continue
        try:
            r = S.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect', json={'inspectionUrl': SITE + p, 'siteUrl': PROP}, timeout=40)
            if r.status_code == 429:
                print('조회 한도 도달'); break
            if r.status_code != 200:
                err += 1; continue
            ix = r.json().get('inspectionResult', {}).get('indexStatusResult', {})
            cs = ix.get('coverageState') or ix.get('verdict') or '알 수 없음'
            st[p] = {'state': cs, 'indexed': 'indexed' in cs.lower() and 'not indexed' not in cs.lower(), 'crawl': ix.get('lastCrawlTime', ''), 'at': now.strftime('%Y-%m-%d %H:%M')}
            asked += 1
        except Exception:
            err += 1
        time.sleep(0.35)
    json.dump(st, open(STATE, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=1)
    log = json.load(open(LOG, encoding='utf-8')) if os.path.exists(LOG) else {}
    recent = (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    notidx = [(v, p, st[p]['state']) for v, p in cand if p in st and not st[p]['indexed']]
    pick = [(v, p, s) for v, p, s in notidx if log.get(p, '') < recent][:n_out]
    os.makedirs(OUTBOX, exist_ok=True)
    f = os.path.join(OUTBOX, f'색인요청_{now:%m%d}_타검색유입.txt')
    if os.path.exists(f) and '--force' not in sys.argv:   # 같은 날 두 번 돌면 먼저 만든 10건을 덮어쓰지 않는다(2026-11-06: 06시 자동 실행이 새벽에 만든 목록을 바꿔 버렸음)
        print(f'오늘 목록이 이미 있음 → 그대로 둠: {f}')
        return
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(f'# {today} 구글 색인 요청 후보 {len(pick)}건 — 최근 {days}일 다음·빙·네이버 검색 유입이 있는데 구글에 색인되지 않은 글(방문 많은 순). 서치 콘솔 URL 검사 → 색인 생성 요청\n')
        for v, p, s in pick:
            fh.write(f'{SITE}{p}\n')
        fh.write('\n# 참고(주소 · 타 검색엔진 방문 수 · 구글 상태)\n')
        for v, p, s in pick:
            fh.write(f'# {p} · {v}명 · {s}\n')
    for v, p, s in pick:
        log[p] = today
    json.dump(log, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 구역별 색인율(조회한 주소 기준)
    sec = collections.defaultdict(lambda: [0, 0])
    for p, v in st.items():
        k = '/' + p.strip('/').split('/')[0] + '/'
        sec[k][0] += 1; sec[k][1] += 1 if v.get('indexed') else 0
    rep = [f'# 구글 색인 상태 — {today} (URL 검사 API 로 조회한 주소 기준, 전체 주소가 아님)', '', '구역|조회한 주소|색인됨|색인율', '---|---:|---:|---:']
    for k, (a, b) in sorted(sec.items(), key=lambda x: -x[1][0]):
        rep.append(f'{k}|{a}|{b}|{round(100 * b / a)}%')
    rep += ['', f'## 다른 검색엔진 유입 상위 {len(cand)}쪽 중 구글 미색인 {len(notidx)}쪽', '', '주소|다음·빙·네이버 방문(최근 {0}일)|구글 방문|구글 상태'.format(days), '---|---:|---:|---']
    rep += [f'{p}|{v}|{google.get(p, 0)}|{s}' for v, p, s in notidx]
    open(os.path.join(HERE, 'index_candidates.md'), 'w', encoding='utf-8').write('\n'.join(rep))
    print(f'유입 주소 {len(other)} · 후보 {len(cand)} · 새로 조회 {asked}(오류 {err}) · 미색인 {len(notidx)} · 이번에 넘김 {len(pick)} → {f}')
    for v, p, s in pick:
        print(f'  {v:>3}명  {p}  [{s}]')


if __name__ == '__main__':
    main()
