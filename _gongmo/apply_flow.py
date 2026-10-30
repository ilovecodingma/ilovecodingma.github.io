# -*- coding: utf-8 -*-
"""가이드의 「신청·절차·방법」 번호 목록을 단계 흐름(ol.flow)으로 바꾼다. 작가 마크다운에서 번호 목록과 앞 제목을 읽어,
guides_extra.json 의 <ul> 에서 같은 항목을 찾아 교체한다(이미 바뀐 건 건너뜀). 사용: python -X utf8 _gongmo/apply_flow.py"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\k\Desktop\공모전_2026\작가_납품'
sys.path.insert(0, SRC)
import md2guide as M
HEAD = re.compile(r'신청|절차|방법|순서|단계|따라|하는 법|발급|진행|처리|대응|접수|해지|변경|제출|확인하는|이의|취소|환급|등록|이용')
LI = re.compile(r'^(?:[-*]|\d+\.)\s+(?:\[[ x]\]\s*)?(.*)$')
R = os.path.join(HERE, 'guides_extra.json')
g = json.load(open(R, encoding='utf-8'))
by = {x[0]: x for x in g if isinstance(x, list)}
n_l = n_g = 0
for slug, x in by.items():
    p = os.path.join(SRC, slug + '.md')
    if not os.path.exists(p):
        continue
    lines = open(p, encoding='utf-8').read().replace('\r', '').split('\n')
    head, cur, lists = '', [], []
    for l in lines + ['']:
        s = l.strip()
        if s.startswith('## ') or s.startswith('### '):
            head = s
        m = re.match(r'^\d+\.\s+(.*)$', s)
        if m:
            cur.append(LI.match(s).group(1))
        else:
            if len(cur) >= 3 and HEAD.search(head):
                lists.append(cur)
            cur = []
    h, hit = x[3], 0
    for items in lists:
        old = '<ul>' + ''.join(f'<li>{M.inline(i)}</li>' for i in items) + '</ul>'
        if old in h:
            h = h.replace(old, '<ol class="flow">' + ''.join(f'<li>{M.inline(i)}</li>' for i in items) + '</ol>', 1)
            hit += 1
    if hit:
        x[3] = h; n_l += hit; n_g += 1
json.dump(g, open(R, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('흐름으로 바꾼 목록', n_l, '개 /', n_g, '편')
