# -*- coding: utf-8 -*-
"""커뮤니티 API 배포 (Cloudflare REST API, wrangler·node 불필요)
준비: 금고 ~/.cloudflare.xml (PSCredential: UserName=계정 ID, Password=API 토큰[Workers Scripts:Edit, D1:Edit, Workers Subdomain:Edit])
사용: python -X utf8 deploy.py   → D1 생성/재사용 → 스키마 적용 → Worker 업로드 → workers.dev 공개 → _gongmo/community.json 기록
"""
import json, os, subprocess, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
NAME, DBNAME = 'jupjup-api', 'jupjup'


def cred():
    ps = ("$c = Import-Clixml \"$env:USERPROFILE\\.cloudflare.xml\"; "
          "Write-Output $c.UserName; Write-Output $c.GetNetworkCredential().Password")
    out = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.split()
    return out[0], out[1]


ACC, TOKEN = cred()
API = f'https://api.cloudflare.com/client/v4/accounts/{ACC}'


def call(method, path, data=None, ctype='application/json', raw=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(API + path, data=body, method=method, headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': ctype})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        r = json.loads(e.read() or b'{}')
    if not r.get('success', False):
        print('API 실패', method, path, r.get('errors'))
    return r


# 1) D1
dbs = call('GET', '/d1/database?name=' + DBNAME).get('result') or []
db = next((d for d in dbs if d['name'] == DBNAME), None) or call('POST', '/d1/database', {'name': DBNAME}).get('result')
DBID = db['uuid']
print('D1', DBID)
# 2) 스키마
call('POST', f'/d1/database/{DBID}/query', {'sql': open(os.path.join(HERE, 'schema.sql'), encoding='utf-8').read()})
# 3) Worker 업로드 (ES 모듈 + D1 바인딩)
bd = '----jupjup' + os.urandom(6).hex()
meta = {'main_module': 'worker.js', 'compatibility_date': '2026-10-01', 'bindings': [{'type': 'd1', 'name': 'DB', 'id': DBID}]}
parts = [
    f'--{bd}\r\nContent-Disposition: form-data; name="metadata"; filename="metadata.json"\r\nContent-Type: application/json\r\n\r\n'.encode() + json.dumps(meta).encode() + b'\r\n',
    f'--{bd}\r\nContent-Disposition: form-data; name="worker.js"; filename="worker.js"\r\nContent-Type: application/javascript+module\r\n\r\n'.encode()
    + open(os.path.join(HERE, 'worker.js'), 'rb').read() + b'\r\n',
    f'--{bd}--\r\n'.encode()]
r = call('PUT', f'/workers/scripts/{NAME}', raw=b''.join(parts), ctype=f'multipart/form-data; boundary={bd}')
print('worker', r.get('success'))
# 4) workers.dev 공개
sub = (call('GET', '/workers/subdomain').get('result') or {}).get('subdomain')
if not sub:
    sub = (call('PUT', '/workers/subdomain', {'subdomain': 'jupjup' + os.urandom(2).hex()}).get('result') or {}).get('subdomain')
call('POST', f'/workers/scripts/{NAME}/subdomain', {'enabled': True})
api = f'https://{NAME}.{sub}.workers.dev'
json.dump({'api': api}, open(os.path.join(os.path.dirname(HERE), 'community.json'), 'w', encoding='utf-8'))
print('API', api)
try:
    print('health', urllib.request.urlopen(api + '/api/health', timeout=30).read().decode())
except Exception as e:
    print('health 확인 실패(전파 대기 중일 수 있음)', e)
