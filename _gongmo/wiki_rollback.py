# -*- coding: utf-8 -*-
"""잘못 올라간 위키 문서를 이전 개정으로 되돌린다.
사용: python wiki_rollback.py <slug>        → 개정 목록 보기
      python wiki_rollback.py <slug> <번호>  → 그 개정 내용을 현재 문서로 복원(새 개정으로 기록됨). 이어서 build.py --push 로 올린다.
"""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'wiki_data')
if len(sys.argv) < 2:
    sys.exit(__doc__)
slug = sys.argv[1]
rd = os.path.join(D, '_rev', slug)
fs = sorted(f for f in os.listdir(rd) if f.endswith('.json'))
if len(sys.argv) == 2:
    for f in fs:
        r = json.load(open(os.path.join(rd, f), encoding='utf-8'))
        print(f[:4], r.get('_ts'), r.get('_note'))
    sys.exit()
n = int(sys.argv[2])
src = json.load(open(os.path.join(rd, f'{n:04d}.json'), encoding='utf-8'))
cur = json.load(open(os.path.join(D, slug + '.json'), encoding='utf-8'))
for k in ('title', 'summary', 'sections', 'notes'):
    cur[k] = src[k]
cur['updated'] = datetime.date.today().isoformat()
cur['rev_note'] = f'r{n} 로 되돌림'
json.dump(cur, open(os.path.join(D, slug + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('복원 완료 → build.py --push')
