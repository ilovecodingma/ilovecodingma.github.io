# -*- coding: utf-8 -*-
"""검색엔진별 첫 방문자 수(다음/빙/줌 갈라서): D1 hits 의 ref 호스트 기준, 그날 처음 들어온 방문(vid)만. 출력 inflow_engine.json = {day: {엔진: 수}}
   검색어는 남지 않는다: 워커가 ref 를 호스트 이름까지만 저장하고, 브라우저도 검색 사이트에서 넘어올 때 주소의 검색어 부분은 보통 떼어 보낸다."""
import json, os, sys, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inflow_report import query


def eng(r):
    if 'daum.net' in r: return '다음(모바일)' if r.startswith('m.') else '다음(PC)'
    if 'bing.com' in r: return '빙'
    if 'zum.com' in r: return '줌'
    if 'naver.com' in r: return '네이버'
    if 'google.' in r: return '구글'
    return None


def main(days=14):
    since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    rows = query('SELECT day, ts, vid, ref, country FROM hits WHERE day >= ? ORDER BY ts', [since])
    first = {}
    for h in rows:
        k = (h['day'], h['vid'])
        if k not in first:
            first[k] = h
    out = collections.defaultdict(collections.Counter)
    for (day, _v), h in first.items():
        e = eng(h.get('ref') or '')
        if e:
            out[day][e] += 1
    p = os.path.join(HERE, 'inflow_engine.json')
    try:
        old = json.load(open(p, encoding='utf-8'))
    except Exception:
        old = {}
    old.update({d: dict(c) for d, c in out.items()})
    json.dump(dict(sorted(old.items())), open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for d in sorted(out):
        print(d, dict(out[d]))


if __name__ == '__main__':
    main()
