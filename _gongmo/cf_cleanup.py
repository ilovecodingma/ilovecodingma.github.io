# -*- coding: utf-8 -*-
"""Cloudflare 계정 정리 (2026-10-27 사용자 지시: 줍줍 빼고 다 삭제). 사용자가 직접 실행한다.
  python -X utf8 cf_cleanup.py          → 지울 대상만 보여 줌(아무것도 안 지움)
  python -X utf8 cf_cleanup.py --yes    → 실제 삭제
남기는 것: Worker jupjup-api, D1 jupjup.   지우는 것: Worker life-notes-kr, KV noz_lab_kv, R2 news-crawler-data / test / test1 / total"""
import sys, json, urllib.request, urllib.parse, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.expanduser('~/remote_login')); import cf_token
YES = '--yes' in sys.argv
a, t = cf_token.get()
H = {'Authorization': 'Bearer ' + t, 'User-Agent': 'wrangler/4.40.0', 'Content-Type': 'application/json'}
B = f'https://api.cloudflare.com/client/v4/accounts/{a}'


def call(method, path):
    r = urllib.request.Request(B + path, method=method, headers=H)
    try:
        return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except Exception: return {'success': False, 'http': e.code}


def do(label, method, path):
    if not YES:
        print('[대상]', label); return
    r = call(method, path)
    print('삭제' if r.get('success') else '실패', label, '' if r.get('success') else json.dumps(r.get('errors'), ensure_ascii=False)[:200])


do('Worker life-notes-kr', 'DELETE', '/workers/scripts/life-notes-kr?force=true')
ns = [x for x in call('GET', '/storage/kv/namespaces').get('result', []) if x['title'] == 'noz_lab_kv']
for x in ns: do('KV noz_lab_kv', 'DELETE', f"/storage/kv/namespaces/{x['id']}")
for b in ('news-crawler-data', 'test', 'test1', 'total'):
    cur = None
    while True:   # 버킷이 비어 있어야 지울 수 있어서 개체를 먼저 지운다
        r = call('GET', f'/r2/buckets/{b}/objects' + (f'?cursor={urllib.parse.quote(cur)}' if cur else ''))
        objs = r.get('result') or []
        if not objs: break
        for o in objs:
            do(f"R2 {b}/{o['key']}", 'DELETE', f"/r2/buckets/{b}/objects/{urllib.parse.quote(o['key'], safe='')}")
        cur = (r.get('result_info') or {}).get('cursor')
        if not YES or not cur: break
    do(f'R2 버킷 {b}', 'DELETE', f'/r2/buckets/{b}')
print('끝' if YES else '위 대상이 지워질 예정입니다. 실제로 지우려면 --yes 를 붙여 다시 실행하세요.')
