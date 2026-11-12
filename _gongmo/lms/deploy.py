# -*- coding: utf-8 -*-
"""하네스 학습 사이트(LMS) 워커 배포 — 별도 워커 jupjup-lms + 별도 D1 jupjup-lms (운영 중인 jupjup-api 는 건드리지 않는다).
사용: python -X utf8 deploy.py   (토큰은 ~/remote_login/cf_token.py 가 갱신) → D1 만들기/재사용 → 스키마 → 워커 올리기 → workers.dev 켜기 → _gongmo/lms.json 에 주소 기록"""
import json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
NAME, DBNAME = 'jupjup-lms', 'jupjup-lms'
sys.path.insert(0, os.path.expanduser('~/remote_login'))
import cf_token
ACC, TOKEN = cf_token.get()
API = f'https://api.cloudflare.com/client/v4/accounts/{ACC}'


def call(method, path, data=None, ctype='application/json', raw=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(API + path, data=body, method=method, headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': ctype, 'User-Agent': 'jupjup-lms-deploy/1'})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        r = json.loads(e.read() or b'{}')
    if not r.get('success', False):
        print('API 실패', method, path, r.get('errors'))
    return r


dbs = call('GET', '/d1/database?name=' + DBNAME).get('result') or []
db = next((d for d in dbs if d['name'] == DBNAME), None) or call('POST', '/d1/database', {'name': DBNAME}).get('result')
DBID = db['uuid']; print('D1', DBID)
for stmt in [s.strip() for s in open(os.path.join(HERE, 'schema.sql'), encoding='utf-8').read().split(';') if s.strip()]:
    call('POST', f'/d1/database/{DBID}/query', {'sql': stmt})
bd = '----lms' + os.urandom(6).hex()
meta = {'main_module': 'worker.js', 'compatibility_date': '2026-10-01', 'bindings': [{'type': 'd1', 'name': 'DB', 'id': DBID}]}
parts = [f'--{bd}\r\nContent-Disposition: form-data; name="metadata"; filename="metadata.json"\r\nContent-Type: application/json\r\n\r\n'.encode() + json.dumps(meta).encode() + b'\r\n',
         f'--{bd}\r\nContent-Disposition: form-data; name="worker.js"; filename="worker.js"\r\nContent-Type: application/javascript+module\r\n\r\n'.encode() + open(os.path.join(HERE, 'worker.js'), 'rb').read() + b'\r\n',
         f'--{bd}--\r\n'.encode()]
r = call('PUT', f'/workers/scripts/{NAME}', raw=b''.join(parts), ctype=f'multipart/form-data; boundary={bd}')
print('worker', r.get('success'))
sub = (call('GET', '/workers/subdomain').get('result') or {}).get('subdomain')
call('POST', f'/workers/scripts/{NAME}/subdomain', {'enabled': True})
api = f'https://{NAME}.{sub}.workers.dev'
json.dump({'api': api}, open(os.path.join(os.path.dirname(HERE), 'lms.json'), 'w', encoding='utf-8'))
print('API', api)
try:
    print('health', urllib.request.urlopen(api + '/lms/health', timeout=30).read().decode())
except Exception as e:
    print('health 확인 실패(전파 대기 중일 수 있음)', repr(e)[:100])
