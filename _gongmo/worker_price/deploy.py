# -*- coding: utf-8 -*-
"""최저가 찾기 API 배포 (Cloudflare REST, 커뮤니티 API 와 따로 둔 Worker — 여기가 죽어도 로그인·댓글에 영향 없음)
사용: python -X utf8 deploy.py   → Worker 업로드 → workers.dev 공개 → _gongmo/price_api.json 기록
"""
import json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'jupjup-price'
sys.path.insert(0, os.path.expanduser('~/remote_login'))
import cf_token
ACC, TOKEN = cf_token.get()
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


bd = '----jupjup' + os.urandom(6).hex()
meta = {'main_module': 'worker.js', 'compatibility_date': '2026-10-01', 'bindings': []}
parts = [
    f'--{bd}\r\nContent-Disposition: form-data; name="metadata"; filename="metadata.json"\r\nContent-Type: application/json\r\n\r\n'.encode() + json.dumps(meta).encode() + b'\r\n',
    f'--{bd}\r\nContent-Disposition: form-data; name="worker.js"; filename="worker.js"\r\nContent-Type: application/javascript+module\r\n\r\n'.encode()
    + open(os.path.join(HERE, 'worker.js'), 'rb').read() + b'\r\n',
    f'--{bd}--\r\n'.encode()]
r = call('PUT', f'/workers/scripts/{NAME}', raw=b''.join(parts), ctype=f'multipart/form-data; boundary={bd}')
print('worker', r.get('success'))
sub = (call('GET', '/workers/subdomain').get('result') or {}).get('subdomain')
call('POST', f'/workers/scripts/{NAME}/subdomain', {'enabled': True})
api = f'https://{NAME}.{sub}.workers.dev'
json.dump({'api': api}, open(os.path.join(os.path.dirname(HERE), 'price_api.json'), 'w', encoding='utf-8'))
print('API', api)
try:
    print('health', urllib.request.urlopen(urllib.request.Request(api + '/api/price/health', headers={'User-Agent': 'jupjup-deploy'}), timeout=30).read().decode())
except Exception as e:
    print('health 확인 실패(전파 대기 중일 수 있음)', e)
