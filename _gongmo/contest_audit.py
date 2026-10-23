# -*- coding: utf-8 -*-
"""공모전 데이터 감사 (2026-10-23 공모전 2.0 Sprint 0). 읽기 전용: 원본 master.jsonl 과 사이트 산출물만 읽고 결과는 바탕화면 루리줍줍_품질개편 에 쓴다.
검사: 중복 후보 묶음(주최·시작일·제목 특징·접수처), 사진/영상 분류·제출물 불일치, 출처 유형(공식/수집처), 마감 시각 정보, 상금 일관성."""
import os, re, sys, json, csv, collections, datetime, html as H
import urllib.parse as up
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = r'C:\Users\k\Desktop\공모전_2026\data'
OUT = os.path.expanduser(r'~\Desktop\루리줍줍_품질개편'); os.makedirs(OUT, exist_ok=True)
TODAY = datetime.date.today().isoformat()
AGG = ('wevity', 'contestkorea', 'all-con', 'thinkyou', 'linkareer', 'campuspick', 'allcon', 'detizen', 'cafe.naver', 'blog.naver', 'instagram', 'forms.gle', 'form.naver', 'docs.google')
STOP = set('공모전 공모 모집 개최 제회 회 년 년도 대회 한국 주최 주관 함께하는 와 과 및 의 2026 2025 2027 사진 영상 포스터 아이디어 콘테스트 contest'.split())


def host(u):
    try: return up.urlparse(u or '').netloc.lower()
    except Exception: return ''


def src_type(u):
    h = host(u)
    if not h: return 'NONE'
    if any(a in h for a in ('wevity', 'contestkorea', 'all-con', 'allcon', 'thinkyou', 'linkareer', 'campuspick', 'detizen')): return 'SECONDARY_AGGREGATOR'
    if any(a in h for a in ('forms.gle', 'form.naver', 'docs.google', 'google.com/forms')): return 'APPLICATION_FORM'
    if any(a in h for a in ('blog.naver', 'cafe.naver', 'instagram', 'facebook', 'tistory')): return 'SOCIAL_OR_BLOG'
    return 'OFFICIAL_CANDIDATE'   # 주최 기관 도메인일 가능성(자동 판정, 검증 전)


def toks(title):
    t = re.sub(r'\[[^\]]*\]|\([^)]*\)|【[^】]*】|[「」『』“”‘’\'"<>]', ' ', title or '')
    t = re.sub(r'20\d\d|제\s?\d+\s?회', ' ', t)
    out = set()
    for w in re.findall(r'[A-Za-z]{2,}|[가-힣]{2,}', t):
        w = w.lower()
        if w in STOP: continue
        out.add(w)
        if re.match(r'[가-힣]{4,}', w): out |= {w[i:i + 2] for i in range(len(w) - 1)}   # 붙여 쓴 한글 낱말은 2글자 조각도 비교(해양사진공모전 ↔ 해양 사진 공모전)
    return out


def subtype(r):
    s = ' '.join(str(r.get(k) or '') for k in ('title', 'field', 'effort'))
    if re.search(r'사진|포토|photo', s, re.I): return '사진'
    if re.search(r'영상|숏폼|쇼츠|UCC|동영상|영화', s): return '영상'
    return ''


def main():
    rows = [json.loads(l) for l in open(os.path.join(DATA, 'master.jsonl'), encoding='utf-8') if l.strip()]
    live = [r for r in rows if r.get('kind') == 'contest' and not r.get('closed') and (r.get('end_override') or r.get('end') or '') >= TODAY and r.get('verified') is not False]
    print('원본', len(rows), '진행 중 공모전', len(live))
    # 1) 중복 후보: 시작일 같음 + 제목 특징 겹침(자카드 ≥0.35) 또는 접수처·공고 URL 동일. 다른 부문은 제목 차이로 남기므로 자동 병합하지 않고 「검토 후보」로만 낸다
    parent = {r['id']: r['id'] for r in live}
    find = lambda a: a if parent[a] == a else find(parent[a])
    T = {r['id']: toks(r['title']) for r in live}; why = collections.defaultdict(list)
    byst = collections.defaultdict(list)
    for r in live: byst[r.get('start') or ''].append(r)
    for st, g in byst.items():
        if not st: continue
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]; ta, tb = T[a['id']], T[b['id']]
                jac = len(ta & tb) / max(1, len(ta | tb))
                same_apply = a.get('apply') and a.get('apply') == b.get('apply')
                if jac >= .35 or same_apply:
                    parent[find(a['id'])] = find(b['id']); why[a['id']].append((b['id'], round(jac, 2), 'same_apply' if same_apply else '')); why[b['id']].append((a['id'], round(jac, 2), ''))
    groups = collections.defaultdict(list)
    for r in live: groups[find(r['id'])].append(r)
    dups = [g for g in groups.values() if len(g) > 1]
    # 2) 분류·제출물 불일치
    mism = []
    for r in live:
        st = subtype(r); tags_txt = ' '.join(str(r.get(k) or '') for k in ('field',))
        if st == '사진': mism.append((r['id'], r['title'][:50], '사진 공모전이나 분류는 영상/기타 (사진 분류 없음)' if re.search('영상', tags_txt) else '사진 공모전(분류 확인)'))
    # 3) 출처 유형
    st_cnt = collections.Counter(src_type(r.get('apply') or r.get('url')) for r in live)
    only_agg = [r['id'] for r in live if src_type(r.get('apply') or r.get('url')) in ('SECONDARY_AGGREGATOR', 'NONE')]
    # 4) 마감 시각 정보: 공고 원문 캐시에서 「마감/접수 … N시」
    tdir = os.path.join(DATA, 'txt'); with_time = no_txt = 0
    for r in live:
        f = os.path.join(tdir, r['id'] + '.txt')
        if not os.path.exists(f): no_txt += 1; continue
        t = open(f, encoding='utf-8', errors='ignore').read()
        if re.search(r'(마감|접수|까지|~)[^\n]{0,40}?(\d{1,2}\s?시|\d{1,2}:\d{2})', t): with_time += 1
    # 5) 상금 일관성: krw 가 있는데 제목/본문 총상금과 다를 가능성은 샘플 검증 필요 → 여기선 그룹 내 불일치만
    conflicts = []
    for g in dups:
        ends = {x.get('end_override') or x.get('end') for x in g}; krws = {x.get('krw') for x in g if x.get('krw')}
        if len(ends) > 1 or len(krws) > 1: conflicts.append((g[0]['id'], [x['id'] for x in g], sorted(ends), sorted(krws)))
    with open(os.path.join(OUT, 'contest_dup_candidates.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['group', 'id', 'title', 'org', 'start', 'end', 'krw', 'apply_type', 'apply', 'url'])
        for n, g in enumerate(sorted(dups, key=lambda g: -len(g)), 1):
            for x in g: w.writerow([f'G{n:03d}', x['id'], x['title'], x.get('org', ''), x.get('start'), x.get('end_override') or x.get('end'), x.get('krw'), src_type(x.get('apply') or x.get('url')), x.get('apply'), x.get('url')])
    with open(os.path.join(OUT, 'contest_subtype_mismatch.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['id', 'title', 'issue']); w.writerows(mism)
    summ = {'live': len(live), 'dup_groups': len(dups), 'dup_contests': sum(len(g) for g in dups), 'dup_conflicts': len(conflicts), 'photo_contests': len(mism),
            'src_types': dict(st_cnt), 'notice_text_cached': len(live) - no_txt, 'notice_mentions_time': with_time}
    json.dump(summ, open(os.path.join(OUT, 'contest_audit_summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    print('\n중복 후보 묶음(상위 12):')
    for g in sorted(dups, key=lambda g: -len(g))[:12]:
        print(' -', ' | '.join(f"{x['id']} {x['title'][:26]} ({x.get('end_override') or x.get('end')})" for x in g))
    print('\n값이 서로 다른 묶음:', len(conflicts))
    for c in conflicts[:6]: print('  ', c)


if __name__ == '__main__':
    main()
