"""방문 기록으로 「많이 찾는 글」 순위를 만든다 (2026-11-10 사용자 「접근 기록들 기반으로 개편」).

- D1 hits 에서 최근 7일만 읽어(색인 hits_day, 한 번에 4천 행 안팎) 주소별 방문자 수를 pop.json 에 적는다.
- 관리 화면(worker.js)과 같은 기준으로 뺀다: 운영자 계정, 데이터센터 접속, 해외에서 링크 없이만 온 방문(자동 점검 프로그램).
- 6시간 안에 만든 pop.json 이 있으면 다시 읽지 않는다(D1 읽기 한도 보호). 실패하면 예전 파일을 그대로 둔다.
- pop.json 에는 주소와 방문자 수만 들어간다(방문자 식별값·주소·기기 정보는 넣지 않는다).

쓰기:  python pop_fetch.py [--force]      불러 쓰기:  import pop_fetch; pop_fetch.load()
"""
import collections
import datetime
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'pop.json')
DAYS = 7
MAX_AGE = 6 * 3600
ADMINS = {16}


def _clean(p):
    p = (p or '/').split('?')[0].split('#')[0]
    return p if p.endswith('/') or '.' in p.rsplit('/', 1)[-1] else p + '/'


def fetch():
    sys.path.insert(0, os.path.expanduser('~/remote_login'))
    import cf_token
    acc, tok = cf_token.get()
    hd = {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}

    def req(u, body=None):
        r = urllib.request.Request(u, data=json.dumps(body).encode() if body else None, headers=hd)
        return json.load(urllib.request.urlopen(r, timeout=40))
    base = f'https://api.cloudflare.com/client/v4/accounts/{acc}/d1/database'
    db = [d for d in req(base)['result'] if d['name'] == 'jupjup'][0]['uuid']
    today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()
    d0 = (today - datetime.timedelta(days=DAYS - 1)).isoformat()
    rows, read = [], 0
    for i in range(DAYS):   # 하루씩 같다(=)로 물어야 날짜 색인을 탄다(범위+id 조건으로 물으면 표 전체를 읽었다 — 11/10 확인)
        day = (today - datetime.timedelta(days=i)).isoformat(); off = 0
        while True:
            res = req(f'{base}/{db}/query', {'sql': 'SELECT vid, uid, path, ref, country, dc FROM hits WHERE day = ? LIMIT 3000 OFFSET ?', 'params': [day, off]})['result'][0]
            part = res['results']; read += (res.get('meta') or {}).get('rows_read') or 0
            rows += part; off += len(part)
            if len(part) < 3000:
                break
    own = {h['vid'] for h in rows if h['uid'] in ADMINS}
    mx = {}
    for h in rows:
        c = h['country'] or ''
        if c in ('KR', ''):
            continue
        r0 = h['ref'] or ''
        if h['vid'] not in mx or r0 > mx[h['vid']]:
            mx[h['vid']] = r0
    bot = {v for v, m in mx.items() if m == ''}
    uv = collections.defaultdict(set)
    for h in rows:
        if h['dc'] or h['vid'] in own or h['vid'] in bot:
            continue
        uv[_clean(h['path'])].add(h['vid'])
    paths = {p: len(s) for p, s in uv.items() if len(s) >= 2}
    return {'gen': int(time.time()), 'from': d0, 'days': DAYS, 'rows_read': read, 'visitors': len({v for s in uv.values() for v in s}),
            'paths': dict(sorted(paths.items(), key=lambda x: (-x[1], x[0])))}


def refresh(force=False):
    """필요할 때만 다시 받는다. 성공하면 True. 어떤 실패도 밖으로 던지지 않는다(빌드를 멈추지 않는다)."""
    try:
        if not force and os.path.exists(OUT) and time.time() - os.path.getmtime(OUT) < MAX_AGE:
            return False
        d = fetch()
        if len(d['paths']) < 10:   # 기록이 비정상적으로 적으면(집계 오류·한도) 예전 순위를 지우지 않는다
            return False
        tmp = OUT + '.tmp'
        json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        os.replace(tmp, OUT)
        return True
    except Exception as e:
        print('pop_fetch 실패(예전 순위 유지)', repr(e)[:160])
        return False


def load():
    """{주소: 최근 7일 방문자 수}. 파일이 없거나 14일 넘게 묵었으면 빈 값(오래된 순위를 계속 보여 주지 않는다)."""
    try:
        d = json.load(open(OUT, encoding='utf-8'))
        if time.time() - d.get('gen', 0) > 14 * 86400:
            return {}
        return d.get('paths') or {}
    except Exception:
        return {}


if __name__ == '__main__':
    ok = refresh(force='--force' in sys.argv)
    d = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    print('새로 받음' if ok else '그대로', '| 기간', d.get('from'), '| 읽은 행', d.get('rows_read'), '| 방문자', d.get('visitors'), '| 주소', len(d.get('paths') or {}))
    for p, v in list((d.get('paths') or {}).items())[:15]:
        print(v, p)
