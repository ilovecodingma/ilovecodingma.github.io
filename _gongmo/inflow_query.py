# -*- coding: utf-8 -*-
"""검색엔진 유입 검색어 요약 → inflow_query.json (워커가 2026-11-19 부터 ref_q 에 쌓음). 사용: python -X utf8 inflow_query.py [--days 14]
   q='' 는 리퍼러에 검색어가 안 붙어 온 방문. 엔진별로 「검색어 있음/없음」 비율도 함께 낸다."""
import json, os, sys, datetime, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inflow_report import query
days = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 14
since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
rows = query('SELECT day, eng, q, path, n FROM ref_q WHERE day >= ? ORDER BY day DESC, n DESC', [since])
have, none = collections.Counter(), collections.Counter()
for r in rows:
    (have if r['q'] else none)[r['eng']] += r['n']
out = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'note': '날짜, 검색엔진, 검색어, 도착 주소, 수. 검색어 없음(q 빈칸)은 리퍼러에 검색어가 안 붙은 방문.',
       'coverage': {e: {'검색어 있음': have[e], '없음': none[e]} for e in set(have) | set(none)}, 'rows': [r for r in rows if r['q']][:500]}
json.dump(out, open(os.path.join(HERE, 'inflow_query.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out['coverage'], ensure_ascii=False))
