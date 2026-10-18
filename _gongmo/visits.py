# -*- coding: utf-8 -*-
"""자체 방문 집계(D1 hits) 주간 요약 — 비공개, PC에서만 실행. 관리자(uid 16) 방문 제외.
사용: python visits.py [일수=7]  → 일별 방문자·조회, 유입 도메인별, 많이 본 페이지"""
import sys, os, json, urllib.request, datetime
sys.path.insert(0, os.path.expanduser('~/remote_login')); import cf_token
DB = 'bad84d2c-a24e-4ba9-8de9-dad02f30e30e'


def q(sql, params=None):
    a, t = cf_token.get()
    r = urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{a}/d1/database/{DB}/query', method='POST',
        data=json.dumps({'sql': sql, **({'params': params} if params else {})}).encode(), headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json', 'User-Agent': 'wrangler/4.40.0'})
    return json.load(urllib.request.urlopen(r, timeout=60))['result'][0]['results']


n = int(sys.argv[1]) if len(sys.argv) > 1 else 7
since = (datetime.date.today() - datetime.timedelta(days=n - 1)).isoformat()
W = f"day >= '{since}' AND uid != 16 AND vid NOT IN (SELECT DISTINCT vid FROM hits WHERE uid = 16)"
tot = q(f"SELECT COUNT(DISTINCT vid) v, COUNT(*) pv FROM hits WHERE {W}")[0]
print(f'== 최근 {n}일({since}~) 방문자 {tot["v"]:,} · 조회 {tot["pv"]:,}')
for r in q(f"SELECT day, COUNT(DISTINCT vid) v, COUNT(*) pv FROM hits WHERE {W} GROUP BY day ORDER BY day"):
    print(f'  {r["day"]}  방문자 {r["v"]:>5}  조회 {r["pv"]:>6}')
print('-- 유입(방문자별 첫 조회의 referrer · src:xx 는 링크 꼬리 ?src=xx)')
for r in q(f"SELECT COALESCE(NULLIF(h.ref,''),'(직접·앱)') r, COUNT(*) v FROM hits h JOIN (SELECT vid, day, MIN(ts) t FROM hits WHERE {W} GROUP BY vid, day) f ON h.vid = f.vid AND h.ts = f.t AND h.day = f.day GROUP BY r ORDER BY v DESC LIMIT 25"):
    print(f'  {r["r"]:<28} {r["v"]:>5}')
print('-- 많이 본 페이지')
for r in q(f"SELECT path, COUNT(*) n FROM hits WHERE {W} GROUP BY path ORDER BY n DESC LIMIT 20"):
    print(f'  {r["n"]:>5}  {r["path"]}')
