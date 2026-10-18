# -*- coding: utf-8 -*-
"""루리의 커뮤니티 이슈 (/talk/) — 커뮤니티 인기글 제목을 같은 화제끼리 묶어 "몇 개 커뮤니티에서 동시에 떴나"로 순위를 매긴다.
2026-10-18 사용자: 커뮤니티 이슈 공개 승인("서로 이야기하면서 만들어, 매거진이랑 등등으로", "정보성으로"). 홍보 세션(연구 ⑂) 기획:
  이슈마다 우리 요약(제목·수치만 근거) + 커뮤니티 원문 링크 + /news/ 언론 이슈 연결(없으면 '언론 미확인') + 관련 줍줍, '사실 확인 전' 문구 상시.
  제외: 성·혐오·일반인 신상·정치인 비방·연예 사생활 폭로·욕설.
재료: _trend/state/posts.json(수집기 CommunityTrendCollect 20분)의 제목·토큰·댓글 수·인기글 체류 시간만. 본문·댓글 원문·니즈 문장·money 는 쓰지 않는다.
결과: root/talk/data.json + root/talk/archive/YYYY-MM-DD.json(그날 마지막 실행이 자정에 확정)."""
import os, re, sys, json, datetime
from kiwipiepy import Kiwi

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
POSTS = os.path.join(ROOT, '_trend', 'state', 'posts.json')
OUT = os.path.join(ROOT, 'talk', 'data.json')
ARCH = os.path.join(ROOT, 'talk', 'archive')
KST = datetime.timezone(datetime.timedelta(hours=9))
HOT = {'pann': '네이트판', 'clien': '클리앙', 'theqoo': '더쿠', 'instiz': '인스티즈', 'bobae': '보배드림', 'ruliweb': '루리웹', 'dc': '디시인사이드',
       'mlbpark': 'MLB파크', 'todayhumor': '오늘의유머', 'slr': 'SLR클럽', 'cook82': '82쿡', 'dogdrip': '개드립', 'arca': '아카라이브'}
BLOCK = re.compile(r'성관계|섹스|야동|\bAV\b|가슴|노출|몸매|19금|성병|자궁|음란|불륜|외도|바람핀|바람난|강간|성폭|성추행|몰카|도촬|한남|한녀|김치녀|틀딱|짱깨|쪽바리|흑형|급식충|맘충|좌빨|수꼴|일베|메갈|화짱조|매국노|'
                   r'신상|얼굴 공개|실명 공개|전화번호|주소 공개|폭로|저격|사생활|열애|이혼|결별|스캔들|루머|찌라시|지라시|ㅅㅂ|시발|씨발|병신|존나|개새|좆|미친놈|미친년|새끼|련|놈들|혐오|자살|살인|시체')
POL_INSULT = re.compile(r'(대통령|의원|장관|대표|총리|당대표|정부|민주당|국민의힘|국힘|여당|야당|[가-힣]{2,3}(?:명|석|열|훈)).{0,12}(쓰레기|미친|구속|감옥|사형|역적|매국|탄핵하라|꺼져|죽어|빨갱이|토착왜구|개돼지|선동|간첩)')
STOP = set('오늘 진짜 근데 이거 그냥 사람 생각 우리 지금 요즘 최근 정말 너무 이번 하나 그거 저거 이건 뭐 왜 나 너 저 글 사진 영상 후기 질문 근황 레전드 반응 이유 상황 정리 모음 ㄷㄷ ㅋㅋ ㅎㅎ jpg gif mp4 webp 유머 펌'.split())
kiwi = Kiwi()


def toks(p):
    tk = [w for w in (p.get('tk') or []) if len(w) >= 2 and w not in STOP]
    if not tk:
        tk = [w.form for w in kiwi.tokenize(p['t']) if w.tag in ('NNP', 'NNG', 'SL') and len(w.form) >= 2 and w.form not in STOP]
    return set(tk)


def tidy(t, mx=60):
    t = re.sub(r'\.(jpg|jpeg|gif|png|mp4|webp)\b', '', t, flags=re.I)
    t = re.sub(r'\s*\[\d+\]\s*$|\(\d+\)$', '', t)
    t = re.sub(r'\s+\d+\s+\d{1,2}\.\d{1,2}\s+\d{1,2}:\d{2}.*$', '', t)            # 더쿠 등 제목 뒤 조회수·시각 꼬리
    t = re.sub('[\U0001F000-\U0001FAFF☀-➿️]', '', t)                 # 이모지
    t = re.sub(r'^\s*[a-zA-Z가-힣]{1,3}x?\)\s*', '', t)                                # '솦x)' 같은 말머리
    t = re.sub(r'\s+', ' ', t).strip()
    return t if len(t) <= mx else t[:mx - 1] + '…'


def main():
    now = datetime.datetime.now(KST)
    P = json.load(open(POSTS, encoding='utf-8'))
    since = now - datetime.timedelta(hours=24)
    posts = []
    for k, p in P.items():
        if p.get('s') not in HOT:
            continue
        try:
            ls = datetime.datetime.fromisoformat(p.get('ls') or p.get('fs'))
        except Exception:
            continue
        if ls < since:
            continue
        t = p.get('t') or ''
        if BLOCK.search(t) or POL_INSULT.search(t):
            continue
        p = dict(p, tks=toks(p), hrs=len(p.get('h') or []), nc=int(p.get('nc') or 0))
        if len(p['tks']) < 2:
            continue
        posts.append(p)
    # 씨앗 기준 묶기(고리처럼 번지지 않게)
    posts.sort(key=lambda p: -(p['nc'] + 10 * p['hrs']))
    seeds, groups = [], []
    for p in posts:
        best, bs = None, 0
        for gi, sd in enumerate(seeds):
            sh = len(p['tks'] & sd['tks']); jac = sh / max(1, len(p['tks'] | sd['tks']))
            if sh >= 2 and jac >= 0.3 and jac > bs:
                best, bs = gi, jac
        if best is None:
            seeds.append(p); groups.append([p])
        else:
            groups[best].append(p)
    # 언론 이슈 연결
    news = {}
    try:
        news = json.load(open(os.path.join(ROOT, 'news', 'data.json'), encoding='utf-8'))
    except Exception:
        pass
    nis = [(x, {w.form for w in kiwi.tokenize(x['t']) if w.tag in ('NNP', 'NNG', 'SL') and len(w.form) >= 2}) for x in news.get('issues', [])]
    sys.path.insert(0, HERE)
    import news as NW
    C = json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))['items']
    A = json.load(open(os.path.join(ROOT, 'apply.json'), encoding='utf-8'))
    today = now.date().isoformat()
    out = []
    for g in groups:
        sites = sorted({p['s'] for p in g}, key=lambda s: -sum(q['nc'] for q in g if q['s'] == s))
        nc, hrs = sum(p['nc'] for p in g), max(p['hrs'] for p in g)
        if len(sites) < 2 and not (nc >= 80 or hrs >= 6):
            continue
        cnt = {}
        for p in g:
            for w in p['tks']:
                cnt[w] = cnt.get(w, 0) + 1
        kw = [w for w, c in sorted(cnt.items(), key=lambda x: -x[1]) if c >= 2][:5] or [w for w, _ in sorted(cnt.items(), key=lambda x: -x[1])][:3]
        rep = max(g, key=lambda p: p['nc'] + 5 * p['hrs'])
        allw = set(cnt)
        nm = next(((x, len(allw & ns)) for x, ns in nis if len(allw & ns) >= 2), None)
        names = [HOT[s] for s in sites]
        lines = [f'{len(sites)}개 커뮤니티({", ".join(names[:4])}{" 등" if len(names) > 4 else ""})에서 글 {len(g)}건, 댓글 {nc:,}개가 올라온 화제예요.' if len(sites) >= 2
                 else f'{names[0]} 인기글에 {hrs}시간 머물며 댓글 {nc:,}개가 달린 화제예요.',
                 '자주 나온 말: ' + ', '.join(kw[:4]) + '.']
        out.append({'t': tidy(rep['t']), 'kw': kw, 'cs': names, 'nsite': len(sites), 'np': len(g), 'nc': nc, 'hrs': hrs, 'sum': lines,
                    'news': {'n': nm[0]['n'], 'on': nm[0]['on'], 't': nm[0]['t'], 's': nm[0].get('s'), 'g': nm[0].get('g')} if nm else None,
                    'pr': NW.promos({'t': ' '.join(kw) + ' ' + rep['t'], 'd': ''}, C, A, today),
                    'posts': [{'s': HOT[p['s']], 't': tidy(p['t'], 80), 'u': p['u'], 'nc': p['nc']} for p in sorted(g, key=lambda p: -p['nc'])[:6]]})
    out.sort(key=lambda x: (-x['nsite'], -x['nc'], -x['hrs']))
    out = out[:30]
    for i, x in enumerate(out):
        x['n'] = i
    d = {'updated': now.strftime('%Y-%m-%d %H:%M'), 'date': today, 'npost': len(posts), 'sites': len({p['s'] for p in posts}), 'issues': out}
    os.makedirs(ARCH, exist_ok=True)
    for f in (OUT, os.path.join(ARCH, f'{today}.json')):
        json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('글', len(posts), '이슈', len(out), '언론 연결', sum(1 for x in out if x['news']))


if __name__ == '__main__':
    main()
