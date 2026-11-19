# -*- coding: utf-8 -*-
"""글 A 를 본 뒤 같은 방문자가 글 B 를 본 수. 사용: python -X utf8 transit.py A경로 B경로 [--days 7]  (D1 hits 에서 두 주소만 읽음, 주 1회 정도만)"""
import sys, datetime, collections
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from inflow_report import query
a, b = sys.argv[1], sys.argv[2]
days = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 7
since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
rows = query('SELECT day, vid, ts, path FROM hits WHERE day >= ? AND path IN (?, ?)', [since, a, b])
by = collections.defaultdict(list)
for r in rows:
    by[(r['day'], r['vid'])].append((r['ts'], r['path']))
sa = sum(1 for v in by.values() if any(p == a for _t, p in v))
ab = 0
for v in by.values():
    v.sort(); ta = [t for t, p in v if p == a]
    if ta and any(p == b and t > ta[0] for t, p in v):
        ab += 1
print(f'{a} 본 방문자 {sa}명 중 이어서 {b} 본 사람 {ab}명 (최근 {days}일, 같은 날 기준)')
