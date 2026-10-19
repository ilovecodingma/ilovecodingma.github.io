# -*- coding: utf-8 -*-
"""자체 방문 집계(D1 hits) 주간 요약 — 비공개, PC에서만 실행. 관리자(uid 16) 방문 제외.
사용: python visits.py [일수=7]  → 일별 방문자·조회, 유입 도메인별, 많이 본 페이지
2026-10-19: 집계 4번(각각 hits 를 두 번 훑음)을 한 번 읽고 파이썬에서 묶는 방식으로 바꿨다 — D1 읽기 한도 때문."""
import sys, os, json, urllib.request, datetime
from collections import Counter, defaultdict
sys.path.insert(0, os.path.expanduser('~/remote_login')); import cf_token
DB = 'bad84d2c-a24e-4ba9-8de9-dad02f30e30e'


def q(sql, params=None):
    a, t = cf_token.get()
    r = urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{a}/d1/database/{DB}/query', method='POST',
        data=json.dumps({'sql': sql, **({'params': params} if params else {})}).encode(), headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json', 'User-Agent': 'wrangler/4.40.0'})
    return json.load(urllib.request.urlopen(r, timeout=60))['result'][0]['results']


n = int(sys.argv[1]) if len(sys.argv) > 1 else 7
since = (datetime.date.today() - datetime.timedelta(days=n - 1)).isoformat()

rows = q(f"SELECT day, ts, vid, uid, path, ref FROM hits WHERE day >= '{since}'")
mine = {r['vid'] for r in rows if r['uid'] == 16}          # vid 는 날짜별 해시라 기간 안에서만 봐도 같다
H = [r for r in rows if r['uid'] != 16 and r['vid'] not in mine]
print(f'== 최근 {n}일({since}~) 방문자 {len({r["vid"] for r in H}):,} · 조회 {len(H):,}   [hits {len(rows):,}줄 1회 읽음]')

byday = defaultdict(lambda: [set(), 0])
for r in H:
    byday[r['day']][0].add(r['vid']); byday[r['day']][1] += 1
for d in sorted(byday):
    print(f'  {d}  방문자 {len(byday[d][0]):>5}  조회 {byday[d][1]:>6}')

print('-- 유입(방문자별 첫 조회의 referrer · src:xx 는 링크 꼬리 ?src=xx)')
first = {}
for r in H:
    k = (r['vid'], r['day'])
    if k not in first or r['ts'] < first[k]['ts']:
        first[k] = r
for ref, v in Counter((r['ref'] or '(직접·앱)') for r in first.values()).most_common(25):
    print(f'  {ref:<28} {v:>5}')

print('-- 많이 본 페이지')
for path, v in Counter(r['path'] for r in H).most_common(20):
    print(f'  {v:>5}  {path}')
