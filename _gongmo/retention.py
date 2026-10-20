# -*- coding: utf-8 -*-
"""재방문율 요약 (2026-10-20 홍보 세션 요청: 같은 방문자가 2일 이상 방문한 비율). 주 1회, D1 읽기 한도 때문에 일별·방문자별 쌍만 한 번 읽어 retention.json 에 요약표로 둔다.
vid 는 2026-10-20 부터 브라우저가 저장한 익명 번호로 만들어서(이전 기록은 날마다 바뀌는 번호라 비교 불가) 그 날 이후만 재방문으로 셈한다.
사용: python retention.py [--days 14]   → _gongmo/retention.json"""
import os, sys, json, datetime, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from alerts import q   # 같은 D1 조회

STABLE_SINCE = '2026-10-20'   # 안정적인 방문 번호를 쓰기 시작한 날(그 전 hits 는 날마다 다른 번호)


def main():
    days = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 14
    today = datetime.date.today()
    since = max((today - datetime.timedelta(days=days)).isoformat(), STABLE_SINCE)
    rows = q("SELECT day, vid FROM hits WHERE day >= ? AND vid != '' GROUP BY day, vid", [since])   # (날, 방문자) 쌍만 — 행 수가 방문자×일수라 적어요
    by = collections.defaultdict(set)
    for r in rows:
        by[r['vid']].add(r['day'])
    ndays = sorted({r['day'] for r in rows})
    first = {v: min(d) for v, d in by.items()}
    daily = []
    for d in ndays:
        vs = [r['vid'] for r in rows if r['day'] == d]
        daily.append({'day': d, 'visitors': len(vs), 'returning': sum(1 for v in vs if first[v] < d)})
    out = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'since': since, 'stable_since': STABLE_SINCE, 'days_observed': len(ndays),
           'visitors': len(by), 'returning_2plus_days': sum(1 for d in by.values() if len(d) >= 2), 'daily': daily,
           'note': '같은 방문 번호가 2일 이상 방문한 비율. 번호는 브라우저 저장소 기준이라 브라우저·기기를 바꾸거나 저장소를 지우면 새 방문자로 셈해요.'}
    out['rate'] = round(out['returning_2plus_days'] / out['visitors'] * 100, 1) if out['visitors'] else None
    json.dump(out, open(os.path.join(HERE, 'retention.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'daily'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
