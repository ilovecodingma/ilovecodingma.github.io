# -*- coding: utf-8 -*-
"""일별 유입 경로 보고 (2026-11-02 마케터 요청 6번): D1 hit_daily(워커가 매시 7분에 채움)를 읽어
날짜별 채널 → 첫 페이지 방문자 수를 _gongmo/inflow_daily.json 으로 저장하고 표로 찍는다. 읽기 전용.
사용: python -X utf8 inflow_report.py [--days 14]"""
import json, os, sys, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DB = 'bad84d2c-a24e-4ba9-8de9-dad02f30e30e'
OUT = os.path.join(HERE, 'inflow_daily.json')


def query(sql, params):
    sys.path.insert(0, os.path.expanduser('~/remote_login'))
    import cf_token
    acc, tok = cf_token.get()
    req = urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{acc}/d1/database/{DB}/query',
                                 data=json.dumps({'sql': sql, 'params': params}).encode(), method='POST',
                                 headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json', 'User-Agent': 'jupjup-report/1'})
    r = json.load(urllib.request.urlopen(req, timeout=60))
    if not r.get('success'):
        raise RuntimeError(r.get('errors'))
    return r['result'][0].get('results') or []


def main():
    days = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 14
    import datetime
    since = (datetime.datetime.utcnow() + datetime.timedelta(hours=9) - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    rows = query('SELECT day, ch, path, v FROM hit_daily WHERE day >= ? ORDER BY day DESC, v DESC', [since])
    by = collections.OrderedDict()
    for r in rows:
        d = by.setdefault(r['day'], {'total': 0, 'ch': collections.Counter(), 'land': collections.Counter(), 'ch_land': collections.defaultdict(collections.Counter)})
        d['total'] += r['v']; d['ch'][r['ch']] += r['v']; d['land'][r['path']] += r['v']; d['ch_land'][r['ch']][r['path']] += r['v']
    out = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'note': '그날 처음 들어온 방문자 기준(관리자·자동 점검 제외). 채널 → 첫 페이지별 방문자 수.', 'days': []}
    for day, d in by.items():
        out['days'].append({'day': day, 'visitors': d['total'], 'channels': d['ch'].most_common(),
                            'landing': d['land'].most_common(15),
                            'by_channel': {c: l.most_common(5) for c, l in d['ch_land'].items()}})
    json.dump(out, open(OUT, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=1)
    for x in out['days']:
        print(x['day'], '방문자', x['visitors'])
        for c, v in x['channels'][:6]:
            print('   ', v, c, '→', ', '.join(f'{p}({n})' for p, n in x['by_channel'][c][:3]))


if __name__ == '__main__':
    main()
