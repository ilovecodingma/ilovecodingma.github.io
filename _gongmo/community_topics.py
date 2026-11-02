# -*- coding: utf-8 -*-
"""커뮤니티별(출처별) 오늘의 화제 집계 (2026-11-02 마케터 요청).
talk/archive/<날짜>.json(매시 talk.py)의 이슈별 원글(posts)을 커뮤니티 이름으로 다시 묶어 _gongmo/community_topics.json 으로 쓴다.
집계만 하고 작성자·연령·성별 정보는 만들지 않는다(원자료에도 없다). 사용: python -X utf8 community_topics.py"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'community_topics.json')


def run():
    ad = os.path.join(ROOT, 'talk', 'archive')
    if not os.path.isdir(ad):
        return None
    days = sorted(f[:-5] for f in os.listdir(ad) if f.endswith('.json'))
    if not days:
        return None
    day = days[-1]
    d = json.load(open(os.path.join(ad, day + '.json'), encoding='utf-8'))
    src = collections.defaultdict(lambda: {'np': 0, 'nc': 0, 'topics': []})
    for iss in d.get('issues', []):
        by = collections.defaultdict(list)
        for p in iss.get('posts', []):
            by[p.get('s') or '기타'].append(p)
        for c, ps in by.items():
            nc = sum(int(p.get('nc') or 0) for p in ps)
            top = max(ps, key=lambda p: int(p.get('nc') or 0))
            src[c]['np'] += len(ps); src[c]['nc'] += nc
            src[c]['topics'].append({'t': iss.get('t', ''), 'nsite': iss.get('nsite', 0), 'np_here': len(ps), 'nc_here': nc,
                                     'issue_np': iss.get('np', 0), 'issue_nc': iss.get('nc', 0), 'kw': iss.get('kw', [])[:4],
                                     'top_post': {'t': top.get('t', ''), 'u': top.get('u', ''), 'nc': int(top.get('nc') or 0)}})
    out = {'date': day, 'updated': d.get('updated', ''), 'sites': d.get('sites', 0), 'npost': d.get('npost', 0),
           'note': '출처(커뮤니티)별 집계예요. 작성자·연령·성별 정보는 수집하지 않아요. posts 는 이슈별로 뽑힌 일부라 전체 글 수가 아니에요.',
           'sources': []}
    for c, v in sorted(src.items(), key=lambda kv: -kv[1]['nc']):
        v['topics'].sort(key=lambda t: (-t['nc_here'], -t['nsite']))
        out['sources'].append({'name': c, 'np': v['np'], 'nc': v['nc'], 'topics': v['topics'][:8]})
    json.dump(out, open(OUT, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=1)
    return out


if __name__ == '__main__':
    r = run()
    if r:
        print(r['date'], '커뮤니티', len(r['sources']), '곳')
        for s in r['sources']:
            print('  ', s['name'], '글', s['np'], '댓글', s['nc'], '| 1위:', s['topics'][0]['t'][:30])
