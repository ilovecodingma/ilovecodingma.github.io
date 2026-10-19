# -*- coding: utf-8 -*-
"""루리 탐정의 기사 확인 신호 (/news/) — 언론사 RSS 기사를 모아 진실성 신호로 점수를 매기고, 기사 주제와 관련된 줍줍(공모전·지원금·청약)을 붙인다.
2026-10-18 사용자: "RSS 뉴스 중 기레기 판별" → "팩트체크로, 프로모션은 그 기사 관련 쪽으로" → "기사 수집해서 진실성 평가로" → "피드로, 루리 탐정 복장으로".
점수는 사실 여부 판정이 아니라 '확인 신호'다:
  ① 교차 보도: 같은 사건을 몇 개 언론사가 썼나   ② 출처: 실명 기관·인물 / 익명 관계자 / 커뮤니티·SNS
  ③ 제목-본문 일치: 제목의 숫자·인용이 본문에 실제로 있나   ④ 낚시 표현   ⑤ 기업 홍보성
본문은 분석에만 쓰고 저장·게시하지 않는다(제목·언론사·링크·판정만 data.json 에).
사용: python news.py [--no-push]   결과 root/news/data.json (작업 스케줄러 JupJup_News 매시 50분, 배포는 매시 빌드가 함께 올림)"""
import os, re, sys, json, time, html, math, datetime, hashlib, email.utils, collections, concurrent.futures as cf
import requests, trafilatura
from kiwipiepy import Kiwi

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'news', 'data.json')
CACHE = os.path.join(HERE, 'news_cache.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'}
FEEDS = {
    '연합뉴스': 'https://www.yna.co.kr/rss/news.xml', '한겨레': 'https://www.hani.co.kr/rss/', '경향신문': 'https://www.khan.co.kr/rss/rssdata/total_news.xml',
    '조선일보': 'https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml', '동아일보': 'https://rss.donga.com/total.xml', 'SBS': 'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01',
    '한국경제': 'https://www.hankyung.com/feed/all-news', '머니투데이': 'https://rss.mt.co.kr/mt_news.xml', '국민일보': 'https://www.kmib.co.kr/rss/data/kmibRssAll.xml',
    '뉴시스': 'https://newsis.com/RSS/sokbo.xml', '아시아경제': 'https://www.asiae.co.kr/rss/all.htm', '파이낸셜뉴스': 'https://www.fnnews.com/rss/r20/fn_realnews_all.xml',
    '세계일보': 'https://www.segye.com/Articles/RSSList/segye_recent.xml', '이데일리': 'http://rss.edaily.co.kr/edaily_news.xml', '오마이뉴스': 'http://rss.ohmynews.com/rss/ohmynews.xml',
}
ENT = [('연합뉴스', 'https://www.yna.co.kr/rss/entertainment.xml'), ('조선일보', 'https://www.chosun.com/arc/outboundfeeds/rss/category/entertainments/?outputType=xml'),
       ('동아일보', 'https://rss.donga.com/entertainment.xml'), ('뉴시스', 'https://newsis.com/RSS/entertain.xml'), ('한국경제', 'https://www.hankyung.com/feed/entertainment'),
       ('세계일보', 'https://www.segye.com/Articles/RSSList/segye_entertainment.xml'), ('SBS', 'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14'), ('국민일보', 'https://www.kmib.co.kr/rss/data/kmibEntRss.xml')]
SRC = [(k, v, 0) for k, v in FEEDS.items()] + [(k, v, 1) for k, v in ENT]
ENT_BAIT = ['♥', '열애', '결별', '파격', '과감', '아찔', '몸매', '비키니', '오열', '저격', '누구?', '이 배우', '이 가수', '못 알아볼', '확 달라진', '이게 무슨', '눈길', '시선 강탈', '깜짝 근황', '충격 고백', '심경', '의미심장']
SNSRE = re.compile(r'자신의 SNS|자신의 인스타그램|인스타그램에|개인 (?:SNS|계정)|라이브 방송에서|유튜브 채널에|스토리에|팬 커뮤니티|게시물을 올렸|사진을 게재|근황을 공개')
ACC = re.compile(r'사고|숨져|숨진|사망|화재|참사|추락|실종|부상|흉기|살해|변사|폭행|끼임|붕괴|익사|사상자|중상|순직')
POL_QUOTE = re.compile(r"^[“\"‘'][^”\"’']{4,}[”\"’']|[가-힣]{2,4}(?: 대통령| 총리| 장관| 대표| 의원| 위원장| 대변인| 시장| 지사)?[,\s]*[“\"][^”\"]{6,}[”\"]")
WINDOW_H = 36
DEBUG = "--debug" in sys.argv
MAX_ITEMS = 300
KST = datetime.timezone(datetime.timedelta(hours=9))
kiwi = Kiwi()

SKIP = re.compile(r'^\s*[\[［(]\s*(포토|사진|영상|화보|인사|부고|날씨|오늘의 운세|운세|그래픽|표|게시판|모집)\s*[\]］)]|^\s*\d{4}년 \d+월 \d+일 .*뉴스$')
OPINION = re.compile(r'^\s*[\[［(]\s*(사설|칼럼|시론|기고|오피니언|데스크|기자수첩|논설|사이언스카페|특파원 칼럼|여적|만물상|횡설수설|광화문|분수대)[^\]］)]*[\]］)]|/opinion|/column', re.I)
BAIT = ['충격', '경악', '헉', '발칵', '난리', '대박', '알고 보니', '알고보니', '이럴 수가', '깜짝', '소름', '맙소사', '화들짝', '민낯', '실체', '근황', '반전', '숨겨진', '정체는', '무슨 일', '어쩌다', '결국', '뒤집어', '초토화', '날벼락', '아찔', '역대급', '참담', '폭발', '이것', '이 사람', '이 연예인', '이 회사', '…왜', '왜?', '?']
ANON = re.compile(r'관계자|소식통|익명을 요구|한 인사|측근|업계에 따르면|정치권에 따르면|알려졌다|전해졌다')
COMMU = re.compile(r'온라인 커뮤니티|커뮤니티에|누리꾼|네티즌|SNS에|게시글|X\(옛 트위터\)|틱톡에서|스레드에|인스타그램에|유튜브 채널|블라인드에')
NAMED = re.compile(r'(?:[가-힣A-Za-z]{2,}(?:부|처|청|원|위원회|공사|공단|연구원|연구소|협회|은행|대학교|대학|경찰서|경찰청|검찰|법원|시|군|구|도|정부|대통령실|국회|당|센터|재단|통계청|한국은행|기획재정부)|[가-힣]{2,4} (?:장관|대표|의원|교수|청장|원장|총재|시장|지사|대변인|위원장|대통령|총리|회장|사장|박사|연구원))(?:은|는|이|가|측은)?[^.]{0,60}?(?:밝혔다|말했다|발표했다|설명했다|강조했다|덧붙였다|답했다|전했다|따르면)')
PROMO_T = re.compile(r'출시|선보|론칭|오픈|할인|프로모션|이벤트 진행|사은품|기획전|신제품|[\[［]PR[\]］]|[\[［]광고[\]］]')
NUM = re.compile(r'\d[\d,.]*\s?(?:%|퍼센트|만|억|조|명|원|배|세|건|년|개|위|채|가구|곳|대)?')
QUOTE = re.compile(r'[“"‘\']([^”"’\']{4,40})[”"’\']')
STOPN = set('기자 뉴스 오늘 내일 올해 지난해 이번 관련 사진 영상 단독 속보 종합 대한 위해 통해 가운데 이후 이날 지난 최근 등 것 수 때 중 전 후 내 외'.split())


def log(*a):
    print(*a, flush=True)


def decode(r):
    head = r.content[:300].decode('ascii', 'ignore').lower()
    for enc in ('euc-kr', 'cp949', 'ks_c_5601'):
        if enc in head:
            return r.content.decode('cp949', 'ignore')
    return r.content.decode('utf-8', 'ignore')


def clean(s):
    s = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', s or '', flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(html.unescape(s))).strip()


def feed(src):
    name, url, ent = src
    try:
        r = requests.get(url, headers=UA, timeout=20)
        x = decode(r)
    except Exception as e:
        log('피드 실패', name, repr(e)[:80]); return []
    out = []
    for it in re.findall(r'<item[\s>](.*?)</item>', x, re.S):
        g = lambda tag: (re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', it, re.S) or [None, ''])[1]
        t, link = clean(g('title')), clean(g('link'))
        if not t or not link.startswith('http'):
            continue
        ds = clean(g('pubDate') or g('dc:date'))
        try:
            ts = email.utils.parsedate_to_datetime(ds).timestamp() if ',' in ds or 'GMT' in ds or '+' in ds[-6:] else datetime.datetime.fromisoformat(ds.replace('Z', '+00:00')).timestamp()
        except Exception:
            ts = time.time()
        out.append(dict(o=name, t=t, u=link, ts=int(ts), d=clean(g('description'))[:400], ent=ent))
    return out


def body_of(u):
    try:
        r = requests.get(u, headers=UA, timeout=15)
        txt = trafilatura.extract(decode(r), include_comments=False, include_tables=False) or ''
        return txt[:12000]
    except Exception:
        return ''


def nouns(t):
    t = re.sub(r'[\[［(][^\]］)]{0,12}[\]］)]', ' ', t)
    return {w.form for w in kiwi.tokenize(t) if (w.tag in ('NNP', 'NNG', 'SL') and len(w.form) >= 2 and w.form not in STOPN)}


def ents(t):
    """고유명사(인물·기관·나라). 다른 사건을 합치지 않는 근거로 쓴다."""
    t = re.sub(r'[\[［(][^\]］)]{0,12}[\]］)]', ' ', t)
    return {w.form for w in kiwi.tokenize(t) if w.tag == 'NNP' and len(w.form) >= 2 and w.form not in STOPN}


# ---- 중복 제거 (2026-10-19 사용자: 같은 사건을 제목만 바꿔 중복 노출하지 않게)
TRACK = re.compile(r'(?<=[?&])(?:utm_[^=&]*|fbclid|gclid|from|ref|rss|feed|cid|sns|share)=[^&]*&?', re.I)


def norm_url(u):
    u = u.strip().split('#')[0]
    u = re.sub(r'^http://', 'https://', u)
    u = re.sub(r'^https://(?:www|m)\.', 'https://', u)
    u = TRACK.sub('', u)
    return re.sub(r'[?&]+$', '', u).rstrip('/')


def norm_title(t):
    t = re.sub(r'[\[［(【<〈][^\]］)】>〉]{0,14}[\]］)】>〉]', ' ', t)   # [단독] (종합) 【속보】 같은 머리표
    t = re.sub(r'\(?\d보\)?|종합\d?보?$', ' ', t)
    return re.sub(r'[^0-9A-Za-z가-힣]', '', t).lower()


def dedup(arts):
    """① 같은 주소(추적 꼬리표 무시) ② 같은 언론사의 같은 제목(머리표·문장부호 무시) → 최신 1건만."""
    by_u, by_t = {}, {}
    for a in sorted(arts, key=lambda a: -a['ts']):
        k = norm_url(a['u'])
        if k in by_u:
            continue
        by_u[k] = a
        kt = (a['o'], norm_title(a['t']))
        if kt[1] and kt in by_t:
            continue
        by_t[kt] = a
    return sorted(by_t.values(), key=lambda a: -a['ts'])


def group(arts):
    """같은 사건 묶기. 1단계: 씨앗 기사와 제목 명사가 3개 이상·자카드 0.3 이상 겹치면 같은 묶음(고리처럼 번지지 않게 씨앗 기준).
    2단계: 묶음끼리 핵심 명사(묶음 기사 절반 이상에 나오는 말)가 희귀어 가중치로 절반 이상 겹치면 합친다.
    단, 서로 상대 묶음에 없는 고유명사(인물·기관·나라)가 양쪽 모두에 있으면 다른 사건으로 보고 합치지 않는다."""
    N = [nouns(a['t']) for a in arts]
    P = [ents(a['t']) for a in arts]
    df = collections.Counter(w for n in N for w in n)
    idf = {w: math.log((len(N) + 1) / (c + 0.5)) for w, c in df.items()}
    W = lambda ws: sum(idf[t] for t in ws)
    seeds, gid = [], [0] * len(arts)
    for i in sorted(range(len(arts)), key=lambda k: arts[k]['ts']):
        best, bs = None, 0
        for g_, sd in enumerate(seeds):
            if abs(arts[sd]['ts'] - arts[i]['ts']) > 30 * 3600:
                continue
            sh = len(N[i] & N[sd]); jac = sh / max(1, len(N[i] | N[sd]))
            if sh >= 3 and jac >= 0.3 and jac > bs and W(N[i] & N[sd]) >= 0.45 * min(W(N[i]), W(N[sd])):
                best, bs = g_, jac
        if best is None:
            seeds.append(i); best = len(seeds) - 1
        gid[i] = best
    mem = collections.defaultdict(list)
    for i, g_ in enumerate(gid):
        mem[g_].append(i)
    core, allw, ent, tsr = {}, {}, {}, {}
    for g_, L in mem.items():
        c = collections.Counter(w for i in L for w in N[i])
        core[g_] = {w for w, n in c.items() if n * 2 >= len(L)}
        allw[g_] = set(c)
        ent[g_] = {w for i in L for w in P[i]} & core[g_]
        tsr[g_] = (min(arts[i]['ts'] for i in L), max(arts[i]['ts'] for i in L))
    par = {g_: g_ for g_ in mem}
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    G = sorted(mem, key=lambda g_: -len(mem[g_]))
    for x, a in enumerate(G):
        for b in G[x + 1:]:
            if tsr[a][0] - tsr[b][1] > 30 * 3600 or tsr[b][0] - tsr[a][1] > 30 * 3600:
                continue
            sh = core[a] & core[b]
            if len(sh) < 3:
                continue
            w = sum(idf[t] for t in sh) / max(1e-9, min(sum(idf[t] for t in core[a]), sum(idf[t] for t in core[b])))
            if w < 0.5:
                continue
            if (ent[a] - allw[b]) and (ent[b] - allw[a]):
                continue
            if DEBUG:
                log("합침", round(w, 2), sorted(sh), "|", arts[mem[a][0]]["t"][:40], "<-", arts[mem[b][0]]["t"][:40])
            par[find(b)] = find(a)
    return [find(g_) for g_ in gid]


def signals(a, body):
    """본문 기반 신호(캐시됨): 출처 종류, 제목 숫자·인용 일치."""
    s = {'body': bool(body and len(body) > 200)}
    if not s['body']:
        return s
    s['named'] = len(NAMED.findall(body))
    s['anon'] = len(ANON.findall(body))
    s['commu'] = len(COMMU.findall(body))
    s['sns'] = len(SNSRE.findall(body))
    bd = re.sub(r'[\s,]', '', body)
    miss_n = [n.strip() for n in NUM.findall(a['t']) if re.sub(r'[\s,]', '', n.strip()) and re.sub(r'[\s,]', '', n.strip()) not in bd and re.sub(r'\D', '', n) not in re.sub(r'\D', ' ', body).split()]
    s['miss_num'] = [n for n in miss_n if len(re.sub(r'\D', '', n)) >= 1][:3]
    s['miss_q'] = [q for q in QUOTE.findall(a['t']) if (lambda ws: bool(ws) and sum(1 for w in ws if w[:2] in body) / len(ws) < 0.6)(re.findall(r'[가-힣A-Za-z0-9]{2,}', q))][:2]
    return s


def judge(a, sig, cl_n, cl_out, cat=''):
    """0~100 확인 신호 점수(높을수록 확인할 근거가 많음 — 사실 판정 아님)와 이유 목록."""
    why, sc = [], 65
    t = a['t']
    if OPINION.search(t) or OPINION.search(a['u']):
        return None, 'opinion', ['🗣️ 사설·칼럼 같은 의견 글이라 확인 신호 점수를 매기지 않아요']
    excl = '단독' in t[:8]
    if cl_n >= 4:
        sc += 20; why.append(f'✅ {cl_n}개 언론사가 같은 사건을 보도했어요')
    elif cl_n >= 2:
        sc += 10; why.append(f'✅ {cl_n}개 언론사가 같은 사건을 보도했어요')
    elif excl:
        why.append('🔎 단독 보도라 아직 다른 언론사 확인 전이에요')
    else:
        why.append('🔎 아직 이 언론사만 보도했어요')
    if sig.get('body'):
        if sig['commu']:
            sc -= 20; why.append('⚠️ 온라인 커뮤니티·SNS 글을 출처로 썼어요')
        if sig['named'] >= 2:
            sc += 10; why.append('✅ 실명 기관·인물 출처가 있어요')
        elif sig['named'] == 0 and sig['anon']:
            sc -= 10; why.append('⚠️ 출처가 익명(관계자·알려졌다)뿐이에요')
        elif sig['named'] == 0:
            why.append('🔎 말한 사람·기관이 따로 없는 기사예요')
        if sig.get('miss_num'):
            sc -= min(30, 15 * len(sig['miss_num'])); why.append(f'❌ 제목 숫자({", ".join(sig["miss_num"])})가 본문에 없어요')
        if sig.get('miss_q'):
            sc -= 10; why.append('❌ 제목의 인용문이 본문 내용과 달라요')
    else:
        why.append('🔎 본문을 가져오지 못해 출처·제목-본문 일치는 확인 불가예요(허위라는 뜻 아님)')
    bait = [w for w in BAIT if w in t and not (w == '?' and t.rstrip().endswith('?') is False)]
    if t.rstrip().endswith('?'):
        bait = [w for w in bait if w not in ('?',)] + ['물음표 제목']
    else:
        bait = [w for w in bait if w != '?']
    if bait:
        sc -= min(30, 10 * len(bait)); why.append('🎣 낚시 표현: ' + ', '.join(dict.fromkeys(bait)))
    if a.get('ent') or cat == '연예·문화':
        eb = [w for w in ENT_BAIT if w in t]
        if eb:
            sc -= min(30, 10 * len(eb)); why.append('🎣 연예 낚시 표현: ' + ', '.join(eb))
        if sig.get('sns'):
            sc -= 15; why.append('📱 연예인 SNS 글·사진을 옮겨 쓴 기사예요')
    if cat == '정치' and POL_QUOTE.search(t):
        why.append('🗣️ 발언 전달 기사: 따옴표 안은 말한 사람의 주장이에요. 말한 내용이 맞는지는 따로 확인이 필요해요')
    if PROMO_T.search(t) and cl_n <= 1:
        sc -= 10; why.append('📢 기업·상품 홍보성 기사로 보여요')
    sc = max(0, min(100, sc))
    g = 'ok' if sc >= 75 else ('warn' if sc >= 50 else 'bad')
    if not sig.get('body') and g == 'ok':
        g = 'warn'   # 본문을 못 읽었으면 「확인 신호 많음」으로 올리지 않는다
    return sc, g, why


def checks(a, sig, cl_n, cat=''):
    """항목별 확인 표: [항목, 상태, 근거]. 상태 = 확인 / 주의 / 확인 불가 / 해당 없음 / 참고.
    2026-10-19 사용자: 무엇을 확인했고 무엇을 확인 못 했는지, 확인 실패를 허위로 처리하지 말 것."""
    t, body = a['t'], sig.get('body')
    C = [['같은 사건 보도', '참고', f'언론사 {cl_n}곳(같은 언론사 기사는 1곳으로 셈). 보도한 곳이 많아도 내용이 사실이라는 뜻은 아니에요.']]
    if not body:
        C.append(['출처(말한 사람·기관)', '확인 불가', '본문을 가져오지 못했어요.'])
    elif sig.get('commu'):
        C.append(['출처(말한 사람·기관)', '주의', '본문이 온라인 커뮤니티·SNS 글을 출처로 들었어요.'])
    elif sig.get('named', 0) >= 2:
        C.append(['출처(말한 사람·기관)', '확인', f'실명 기관·인물이 말한 문장 {sig["named"]}곳.'])
    elif sig.get('anon'):
        C.append(['출처(말한 사람·기관)', '주의', '「관계자」「알려졌다」 같은 익명 출처만 있어요.'])
    else:
        C.append(['출처(말한 사람·기관)', '참고', '말한 사람·기관이 따로 나오지 않는 기사예요.'])
    nums = [n.strip() for n in NUM.findall(t) if re.sub(r'\D', '', n)]
    if not nums:
        C.append(['제목 숫자 ↔ 본문', '해당 없음', '제목에 숫자가 없어요.'])
    elif not body:
        C.append(['제목 숫자 ↔ 본문', '확인 불가', '본문을 가져오지 못해 비교하지 못했어요.'])
    elif sig.get('miss_num'):
        C.append(['제목 숫자 ↔ 본문', '주의', '본문에서 찾지 못한 숫자: ' + ', '.join(sig['miss_num'])])
    else:
        C.append(['제목 숫자 ↔ 본문', '확인', '제목의 숫자가 본문에 있어요: ' + ', '.join(nums[:3])])
    if not QUOTE.findall(t):
        C.append(['제목 인용문 ↔ 본문', '해당 없음', '제목에 따옴표 인용이 없어요.'])
    elif not body:
        C.append(['제목 인용문 ↔ 본문', '확인 불가', '본문을 가져오지 못해 비교하지 못했어요.'])
    elif sig.get('miss_q'):
        C.append(['제목 인용문 ↔ 본문', '주의', '본문과 표현이 많이 다른 인용: ' + ', '.join(sig['miss_q'])])
    else:
        C.append(['제목 인용문 ↔ 본문', '확인', '제목의 인용 표현이 본문에도 있어요.'])
    bait = [w for w in BAIT if w in t and w != '?'] + (['물음표 제목'] if t.rstrip().endswith('?') else [])
    if a.get('ent') or cat == '연예·문화':
        bait += [w for w in ENT_BAIT if w in t]
    C.append(['낚시 표현(제목)', '주의' if bait else '확인', ('있음: ' + ', '.join(dict.fromkeys(bait))) if bait else '없음'])
    if OPINION.search(t) or OPINION.search(a['u']):
        C.append(['글 종류', '참고', '사설·칼럼 같은 의견 글이에요.'])
    return C


# ---------------- 기사 주제와 관련된 줍줍(사이트 내부 페이지만)
REGIONS = ['서울', '부산', '인천', '대구', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
TOPICS = [
    (r'청약|분양|아파트|전세|월세|임대|주택|부동산|집값', 'a', lambda x: x.get('kind') in ('아파트 청약', '공공임대')),
    (r'공모주|IPO|상장|증시|코스피|코스닥', 'a', lambda x: x.get('kind') == '공모주'),
    (r'청년|취업|일자리|구직|대학생|사회초년|취준', 'a', lambda x: '청년' in x['title']),
    (r'출산|육아|저출생|저출산|보육|임신|어린이집', 'a', lambda x: re.search(r'출산|육아|아동|임신|보육', x['title'])),
    (r'소상공인|자영업|창업|폐업', 'a', lambda x: re.search(r'소상공인|창업|자영업', x['title'])),
    (r'노인|어르신|고령|노후', 'a', lambda x: re.search(r'노인|어르신|고령', x['title'])),
    (r'AI|인공지능|챗GPT|생성형|반도체|로봇|디지털|SW|소프트웨어', 'c', lambda x: re.search(r'AI|인공지능|디지털|SW|소프트웨어|로봇', x['title'])),
    (r'환경|기후|탄소|재활용|미세먼지|에너지|폭염', 'c', lambda x: re.search(r'환경|기후|탄소|에너지|업사이클', x['title'])),
    (r'음식|요리|식품|물가|장바구니|맛집|농산물|김장|외식|급식', 'f', None),
    (r'영화|드라마|유튜브|웹툰|숏폼|영상 콘텐츠', 'c', lambda x: '영상' in (x.get('tags') or [])),
    (r'독서|문학|작가|글쓰기|도서관|소설|시집|출판', 'c', lambda x: '문학' in (x.get('tags') or [])),
    (r'관광|여행|축제|명소|여행지', 'c', lambda x: re.search(r'관광|여행|축제', x['title'])),
    (r'재난|소방|교통사고|화재|지진|안전사고', 'c', lambda x: re.search(r'(?<!행정)안전|재난|소방|교통안전', x['title'])),
    (r'디자인|브랜드|로고|패션', 'c', lambda x: '디자인' in (x.get('tags') or [])),
]


def promos(a, C, A, today):
    t = a['t'] + ' ' + a.get('d', '')[:120]
    reg = next((r for r in REGIONS if r in a['t']), None)
    out = []
    for rx, src, f in TOPICS:
        if not re.search(rx, t):
            continue
        if src == 'f':
            out.append({'t': '냉장고 재료로 오늘 메뉴 추천 · 루리의 냉장고 파먹기', 'u': '/fridge/', 'k': '🍳 집밥'})
            fc = [x for x in C if '요리·레시피' in (x.get('tags') or [])]
            fc.sort(key=lambda x: -(x.get('pv') or 0))
            out += [{'t': x['title'], 'u': f'/c/{x["id"]}/', 'k': '🏆 공모전', 'e': x['end']} for x in fc[:1]]
            continue
        pool = [x for x in (A if src == 'a' else C) if f(x) and x.get('end', '9999') >= today]
        if reg:
            pool.sort(key=lambda x: (reg not in (x['title'] + x.get('org', '') + x.get('region', '')), x.get('end', '9999')))
        else:
            pool.sort(key=lambda x: (-(x.get('pv') or 0), x.get('end', '9999')) if src == 'c' else x.get('end', '9999'))
        for x in pool[:2]:
            out.append({'t': x['title'], 'u': (f'/a/{x["id"]}/' if src == 'a' else f'/c/{x["id"]}/'), 'k': ('💰 ' + x.get('kind', '지원')) if src == 'a' else '🏆 공모전', 'e': x.get('end', '')})
        if len(out) >= 2:
            break
    seen, res = set(), []
    for p in out:
        if p['u'] not in seen:
            seen.add(p['u']); res.append(p)
    return res[:2]


CATS = [('정치', r'대통령|국회|여당|야당|민주당|국민의힘|장관|총리|선거|의원|탄핵|외교|북한|대통령실|청와대'),
        ('경제', r'코스피|코스닥|주가|금리|환율|증시|매출|실적|부동산|아파트|물가|수출|은행|투자|경제|기업|무역|관세|채권'),
        ('국제', r'미국|중국|일본|트럼프|러시아|우크라이나|이스라엘|EU|유엔|백악관|美|中|日'),
        ('IT·과학', r'AI|인공지능|챗GPT|반도체|과학|우주|로봇|플랫폼|게임|앤스로픽|오픈AI|엔비디아'),
        ('스포츠', r'야구|축구|농구|배구|골프|올림픽|감독|선수|리그|홈런|우승|MLB|EPL|KBO|월드컵|멀티골'),
        ('연예·문화', r'배우|가수|드라마|영화|아이돌|공연|예능|콘서트|전시|뮤지컬|작가'),
        ('사회', r'경찰|검찰|법원|사고|화재|사건|학교|교육|의료|병원|소방|재판|노동|숨져|사망|실종|부상')]


def cat_of(ts):
    t = ' '.join(ts)
    sc = [(len(re.findall(rx, t)), n) for n, rx in CATS]
    sc.sort(key=lambda x: -x[0])
    return sc[0][1] if sc[0][0] else '사회'


UNIT = re.compile(r'(\d[\d,.]*)\s?(명|원|억원|조원|만원|%|채|가구|건|곳|대|배)')


def conflict(titles):
    """같은 이슈 제목들에서 같은 단위 숫자가 언론사마다 다르면 엇갈림."""
    by = {}
    for o, t in titles:
        if not re.search(r'사망|숨|부상|사상|실종|희생|사상자|확진|피해', t):
            continue
        if re.search(r'\d\s?여\s?명|약\s?\d|이상', t):
            continue
        for v, u in UNIT.findall(t):
            by.setdefault(u, {}).setdefault(v.replace(',', ''), set()).add(o)
    out = []
    for u, vs in by.items():
        if u == '명' and len(vs) >= 2 and len({o for os_ in vs.values() for o in os_}) >= 2:
            out.append(' vs '.join(f'{v}{u}' for v in list(vs)[:3]))
    return out[:2]


def main():
    t0 = time.time()
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    with cf.ThreadPoolExecutor(8) as ex:
        arts = [a for lst in ex.map(feed, SRC) for a in lst]
    now = time.time()
    arts = [a for a in arts if now - a['ts'] < WINDOW_H * 3600 and not SKIP.search(a['t'])]
    n0 = len(arts)
    arts = dedup(arts)
    log('기사', len(arts), f'(중복 {n0 - len(arts)}건 제거)', '언론사', len({a['o'] for a in arts}))
    todo = [a for a in arts if a['u'] not in cache][:400]
    log('본문 새로 읽기', len(todo))
    with cf.ThreadPoolExecutor(8) as ex:
        for a, body in zip(todo, ex.map(lambda a: body_of(a['u']), todo)):
            cache[a['u']] = {'sig': signals(a, body), 'ts': a['ts'], 'at': datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M')}
            try:   # 경쟁 지표 A: 공모전 기사의 「총 N편 접수」 문장만 쌓기(본문은 저장 안 함)
                import compete
                compete.appl_sentences(a['t'], body, a['u'], a['ts'])
            except Exception:
                pass
    cache = {k: v for k, v in cache.items() if now - v.get('ts', now) < 72 * 3600}
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    # 같은 사건 묶기(제목 명사 겹침 + 묶음끼리 합치기, group() 설명 참고)
    gid = group(arts)
    fd = lambda i: gid[i]
    groups = {}
    for i in range(len(arts)):
        groups.setdefault(gid[i], []).append(i)
    data = json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))['items']
    apply_ = json.load(open(os.path.join(ROOT, 'apply.json'), encoding='utf-8'))
    today = datetime.datetime.now(KST).date().isoformat()
    issues = []
    for root_, g in groups.items():
        outs = sorted({arts[k]['o'] for k in g})
        if len(outs) < 2 or sum(1 for k in g if ACC.search(arts[k]['t'])) * 2 >= len(g):
            continue
        issues.append({'g': g, 'outs': outs, 'ts': max(arts[k]['ts'] for k in g)})
    issues.sort(key=lambda x: (-len(x['outs']), -x['ts']))
    iss_of = {}
    for n_, x in enumerate(issues[:60]):
        for k in x['g']:
            iss_of[k] = n_
    items, by_o = [], {}
    for i, a in enumerate(arts):
        g = groups[fd(i)]
        outs = sorted({arts[k]['o'] for k in g})
        ct = '연예·문화' if a.get('ent') and not re.search(CATS[0][1], a['t']) else cat_of([a['t']])
        sig_ = cache.get(a['u'], {}).get('sig', {})
        sc, grade, why = judge(a, sig_, len(outs), outs, ct)
        it = {'id': hashlib.md5(a['u'].encode()).hexdigest()[:10], 't': a['t'], 'o': a['o'], 'u': a['u'], 'ts': a['ts'], 's': sc, 'g': grade, 'why': why,
              'cl': [o for o in outs if o != a['o']][:6], 'pr': promos(a, data, apply_, today), 'c': ct, 'is': iss_of.get(i), 'ent': a.get('ent', 0), 'acc': 1 if ACC.search(a['t']) else 0,
              'ck': checks(a, sig_, len(outs), ct), 'at': cache.get(a['u'], {}).get('at')}
        items.append(it)
        if sc is not None:
            by_o.setdefault(a['o'], []).append(sc)
    ISS = []
    for n_, x in enumerate(issues[:60]):
        arts_ = sorted([items[k] for k in x['g']], key=lambda it: -(it['s'] or 0))
        sc = [it['s'] for it in arts_ if it['s'] is not None]
        best = arts_[0]
        cf_ = conflict([(it['o'], it['t']) for it in arts_])
        avg = round(sum(sc) / len(sc)) if sc else None
        if cf_ and avg is not None:
            avg = max(0, avg - 10)
        prs = next((it['pr'] for it in arts_ if it['pr']), [])
        cc = cat_of([it['t'] for it in arts_])
        claim = cc == '정치' and sum(1 for it in arts_ if POL_QUOTE.search(it['t'])) * 2 >= len(arts_)
        ISS.append({'claim': 1 if claim else 0, 'n': n_, 't': re.sub(r'\s*[\[［][^\]］]{1,14}[\]］]\s*$', '', best['t']), 'c': cc, 'on': len(x['outs']), 'ts': x['ts'], 's': avg,
                    'g': None if avg is None else ('ok' if avg >= 75 else 'warn' if avg >= 50 else 'bad'), 'cf': cf_, 'a': [it['id'] for it in arts_], 'pr': prs})
    keep = {i for x in ISS for i in x['a']}
    ENTW = [it['id'] for it in sorted([it for it in items if it.get('ent') and it['s'] is not None and it['s'] < 60], key=lambda it: it['s'])[:25]]
    keep |= set(ENTW)
    items = [it for it in items if it['id'] in keep] + [it for it in items if it['id'] not in keep][:MAX_ITEMS]
    outlets = sorted([{'o': o, 'n': len(v), 'avg': round(sum(v) / len(v)), 'bad': round(100 * sum(1 for x in v if x < 50) / len(v))} for o, v in by_o.items() if len(v) >= 10], key=lambda x: -x['avg'])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({'updated': datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M'), 'issues': ISS, 'ent': ENTW, 'items': items, 'outlets': outlets}, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    cnt = {k: sum(1 for x in items if x['g'] == k) for k in ('ok', 'warn', 'bad', 'opinion')}
    log('이슈', len(ISS), '최대', ISS[0]['on'] if ISS else 0, '곳')
    log('완료', len(items), cnt, f'{time.time() - t0:.0f}초')


if __name__ == '__main__':
    main()
    try:  # 커뮤니티 이슈도 같은 주기로(언론 이슈 연결 때문에 뉴스 다음)
        import talk
        talk.main()
        import analyst
        analyst.main()
        import kw
        kw.main()
        import hot
        hot.main()
    except Exception as e:
        log('talk 실패', repr(e)[:200])
