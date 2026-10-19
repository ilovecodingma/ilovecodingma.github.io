# -*- coding: utf-8 -*-
"""애널리스트 분석의 분석 (/analyst/) — 증권사 리포트·전망 기사를 노드로 쪼개 종목·코인별로 다시 가공한다.
2026-10-18 사용자: "다양한 주식 애널리스트 말들을 종합해서 주가 예측 서비스", "비트코인 이더리움 등등",
"애널리스트들의 발언을 따라 노드를 나눠서 분석 들어가는 알고리즘", "분석을 모아 분석하는 사이트", "쇼츠로".
원천: 수집을 허용한 언론사 증권·코인 RSS만(네이버 금융·한경 컨센서스·구글 뉴스·야후는 robots.txt 금지라 쓰지 않음). 코인 시세는 업비트 공개 API.
노드 1개 = 기사 1건 속 발언 1개: {종목, 증권사/기관, 방향(상향·하향·유지 / 강세·약세), 의견, 목표가, 근거 태그, 날짜, 출처 링크}.
종목 트리 = 상승 근거 / 하락 근거 / 유지 가지 아래 근거 태그별로 어느 증권사가 말했는지 모은다. 우리가 직접 예측하거나 매수를 권하지 않는다.
누적: _gongmo/analyst_db.json(노드, 90일 보관). 결과: root/analyst/data.json. news.py 뒤에 매시 실행."""
import os, re, json, time, hashlib, datetime, concurrent.futures as cf
import requests, trafilatura

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DB = os.path.join(HERE, 'analyst_db.json')
OUT = os.path.join(ROOT, 'analyst', 'data.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'}
STOCK_FEEDS = [('머니투데이', 'https://rss.mt.co.kr/mt_news_stock.xml'), ('이데일리', 'http://rss.edaily.co.kr/stock_news.xml'), ('인포스탁데일리', 'https://www.infostockdaily.co.kr/rss/allArticle.xml'),
               ('아시아경제', 'https://www.asiae.co.kr/rss/stock.htm'), ('연합뉴스', 'https://www.yna.co.kr/rss/market.xml'), ('한국경제', 'https://www.hankyung.com/feed/finance'),
               ('뉴시스', 'https://newsis.com/RSS/economy.xml'), ('파이낸셜뉴스', 'https://www.fnnews.com/rss/r20/fn_realnews_stock.xml'),
               # 2026-10-20 전문가 코멘트 수집량 보강(하루 1~4건 → 늘림). robots.txt 허용 확인. 매경(403)·뉴스1(RSS 없음)·구글뉴스(금지)는 뺌
               ('연합인포맥스', 'https://news.einfomax.co.kr/rss/allArticle.xml'), ('한국경제', 'https://www.hankyung.com/feed/economy'), ('이데일리', 'http://rss.edaily.co.kr/edaily_news.xml'),
               ('서울경제', 'https://www.sedaily.com/rss/finance'), ('서울경제', 'https://www.sedaily.com/rss/market'), ('서울경제', 'https://www.sedaily.com/rss/economy'),
               ('연합뉴스', 'https://www.yna.co.kr/rss/economy.xml')]   # 맨 끝은 코인 기사에도 씀
COIN_FEEDS = [('블록미디어', 'https://www.blockmedia.co.kr/feed'), ('토큰포스트', 'https://www.tokenpost.kr/rss')]
COINS = {'BTC': ('비트코인', r'비트코인|BTC|Bitcoin'), 'ETH': ('이더리움', r'이더리움|ETH\b|Ethereum'), 'XRP': ('리플', r'리플|XRP'), 'SOL': ('솔라나', r'솔라나|\bSOL\b|Solana'), 'DOGE': ('도지코인', r'도지코인|DOGE')}
BROKERS = {'한투': '한국투자증권', '한국투자': '한국투자증권', '한화': '한화투자증권', '대신': '대신증권', '신한': '신한투자증권', 'KB': 'KB증권', '키움': '키움증권', 'NH': 'NH투자증권', '미래에셋': '미래에셋증권',
           '삼성': '삼성증권', '하나': '하나증권', '메리츠': '메리츠증권', '유안타': '유안타증권', '교보': '교보증권', '현대차': '현대차증권', 'DB': 'DB금융투자', '하이': '하이투자증권', 'IBK': 'IBK투자증권',
           '신영': '신영증권', '유진': '유진투자증권', 'LS': 'LS증권', '이베스트': 'LS증권', 'SK': 'SK증권', '다올': '다올투자증권', '상상인': '상상인증권', 'BNK': 'BNK투자증권', 'iM': 'iM증권', '부국': '부국증권',
           '한양': '한양증권', '케이프': '케이프투자증권', '흥국': '흥국증권', '모건스탠리': '모건스탠리', '골드만삭스': '골드만삭스', 'JP모건': 'JP모건', '씨티': '씨티', 'BoA': '뱅크오브아메리카', 'UBS': 'UBS',
           '맥쿼리': '맥쿼리', '노무라': '노무라', 'CLSA': 'CLSA', '번스타인': '번스타인', '웰스파고': '웰스파고', '바클레이즈': '바클레이즈', '제프리스': '제프리스', '도이치': '도이치방크', 'HSBC': 'HSBC', '캔터': '캔터피츠제럴드'}
BRX = '|'.join(sorted(map(re.escape, BROKERS), key=len, reverse=True))
UP = re.compile(r'목표(?:주)?가\s?(?:↑|상향|올려|높여|인상|31%↑|\d+%↑)|투자의견\s?(?:↑|상향)|매수로 상향|목표가.{0,12}상향')
DOWN = re.compile(r'목표(?:주)?가\s?(?:↓|하향|낮춰|내려|인하|\d+%↓)|투자의견\s?(?:↓|하향)|중립으로 하향|매도로|목표가.{0,12}하향|줄하향')
KEEP = re.compile(r'매수 유지|투자의견 유지|목표가 유지|비중확대 유지|Buy 유지')
OPIN = [('매수', r'매수|Buy|BUY|비중확대|Outperform|Overweight'), ('중립', r'중립|Hold|HOLD|보유|Neutral|시장수익률'), ('매도', r'매도|Sell|SELL|비중축소|Underweight|Underperform')]
REASONS = [  # (태그, 정규식, +1 상승 근거 / -1 하락 근거)
    ('실적 개선', r'실적 개선|영업이익 증가|어닝 서프라이즈|호실적|최대 실적|실적 성장|이익 개선|흑자 전환|컨센서스 상회', 1),
    ('실적 부진', r'실적 부진|어닝 쇼크|영업이익 감소|적자|추정치 하향|실적 둔화|컨센서스 하회|이익 감소', -1),
    ('업황 호조', r'빅사이클|업사이클|호황|수요 증가|가격 상승|업황 개선|공급 부족|슈퍼사이클', 1),
    ('업황 둔화', r'수요 둔화|업황 부진|재고 부담|공급 과잉|가격 하락|업황 악화|피크아웃', -1),
    ('수주·신사업', r'수주|공급 계약|신사업|신제품|출시|로봇|데이터센터|AI 수요|HBM|신약|기술 수출', 1),
    ('주주환원', r'자사주|배당 확대|소각|주주환원|밸류업', 1),
    ('저평가', r'저평가|밸류에이션 매력|할인 해소|리레이팅|재평가', 1),
    ('고평가 부담', r'고평가|밸류에이션 부담|과열|주가 선반영|상승 여력 제한', -1),
    ('환율·금리', r'환율|원화 강세|원화 약세|금리 인하|금리 인상|달러', 0),
    ('규제·정책', r'규제|관세|정책 리스크|법안|제재', -1),
    ('투자심리 악화', r'투자심리 훼손|불확실성|우려|리스크 확대|소송', -1)]
CR = [('ETF 자금', r'ETF|현물 ETF|자금 유입|자금 유출', 0), ('금리·연준', r'금리|연준|Fed|FOMC|파월', 0), ('규제', r'규제|SEC|소송|제재|법안', -1),
      ('기관·기업 매수', r'매입|매수|보유량|트레저리|Strategy|스트래티지|기관', 1), ('거래소 유입·고래', r'거래소 유입|고래|순유입|매도 물량', -1),
      ('기술·업그레이드', r'업그레이드|하드포크|네트워크|스테이킹', 1), ('거시·위험자산', r'나스닥|증시|위험자산|버블|AI 버블|경기', 0)]
BULL = re.compile(r'상승|돌파|강세|낙관|반등|신고가|랠리|오른다|급등|목표가 상향|\d+만\s?달러.{0,6}(?:간다|전망|예상|도달)|불장')
BEAR = re.compile(r'하락|약세|비관|매도|조정|폭락|경고|버블|붕괴|급락|떨어|하방|찬바람|지지선')
PERSON = re.compile(r'([가-힣A-Za-z]{2,12}(?: CEO| 회장| 창업자| 전략가| 애널리스트| 리서치| 캐피털| 증권| 은행|인베스트먼트|자산운용)?)\s?(?:은|는|이|가)?\s?["“]')


def clean(s):
    import html as H
    s = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', s or '', flags=re.S)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def feed(src):
    name, url = src
    try:
        r = requests.get(url, headers=UA, timeout=20)
        x = r.content.decode('cp949', 'ignore') if 'euc-kr' in r.content[:300].decode('ascii', 'ignore').lower() else r.content.decode('utf-8', 'ignore')
    except Exception:
        return []
    out = []
    for it in re.findall(r'<item[\s>](.*?)</item>', x, re.S):
        g = lambda tag: (re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', it, re.S) or [None, ''])[1]
        t, u = clean(g('title')), clean(g('link'))
        if t and u.startswith('http'):
            out.append({'o': name, 't': t, 'u': u, 'd': clean(g('description'))[:300], 'pd': clean(g('pubDate'))})
    return out


BDATE = {}


def body(u):
    try:
        r = requests.get(u, headers=UA, timeout=15)
        x = r.content.decode('cp949', 'ignore') if 'euc-kr' in r.content[:2000].decode('ascii', 'ignore').lower() else r.content.decode('utf-8', 'ignore')
        try:  # 기사 작성일(메타데이터) — RSS 날짜가 없을 때 옛 기사가 오늘 것으로 들어오지 않게
            md = trafilatura.extract_metadata(x)
            if md and md.date:
                BDATE[u] = md.date
        except Exception:
            pass
        return (trafilatura.extract(x) or '')[:8000]
    except Exception:
        return ''


def url_date(u):
    m = re.search(r'(20[12]\d)[-/]?(0[1-9]|1[0-2])[-/]?(0[1-9]|[12]\d|3[01])', u)
    if m:
        try:
            return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, tzinfo=KST).timestamp()
        except Exception:
            return None
    return None


def broker_of(t, b):
    m = re.search(rf'-\s?({BRX})\s*$', t) or re.search(rf'^(?:\[[^\]]+\]\s*)?({BRX})(?:증권|투자증권|금융투자)?[,\s"“]', t) or re.search(rf'({BRX})(?:증권|투자증권|금융투자|은행)?\s?(?:은|는|이|가)?\s', t + ' ' + b[:300])
    return BROKERS.get(m.group(1)) if m else None


def stock_of(t, br):
    t0 = re.sub(r'^\s*\[[^\]]{1,12}\]\s*', '', t)
    t0 = re.sub(r'[“”"\'‘’]', '', t0)
    if br:
        for k, v in BROKERS.items():
            if v == br:
                t0 = re.sub(rf'^{re.escape(k)}(?:증권|투자증권|금융투자)?[,\s]+', '', t0)
    m = re.match(r'^([가-힣A-Za-z0-9&·]{2,16}?)(?:[,…]|\s(?:목표|투자의견|실적|주가|\d))', t0)
    if not m:
        return None
    s = m.group(1)
    if re.search(r'증권$|^美|특징주|증시|코스피|코스닥|외국인|기관|개미|업종|주말|오늘|급등|급락|전망', s):
        return None
    return s


def num(s):
    try:
        return int(s.replace(',', ''))
    except Exception:
        return None


WON = r'(\d{1,3}(?:,\d{3})+|\d+)\s?(?:만\s?(\d{1,4})?\s?)?원'


def won(m1, m2, man):
    v = num(m1)
    if v is None:
        return None
    return v * 10000 + (num(m2) or 0) if man else v


def tp_of(text):
    """'목표주가를 기존 8만4000원에서 11만원으로', '목표가를 4만2000원으로' → (새 목표가, 이전 목표가)."""
    rx = r'(\d{1,3}(?:,\d{3})+|\d+)\s?(만)?\s?(\d{1,4})?\s?원'
    m = re.search(r'목표(?:주)?가(?:를|는|도)?\s?(?:기존\s?)?' + rx + r'\s?(?:에서|→)\s?' + rx, text)
    if m:
        g = m.groups()
        return won(g[3], g[4] and g[5], g[4]), won(g[0], g[1] and g[2], g[1])
    m = re.search(r'목표(?:주)?가(?:를|는|도|로)?\s?' + rx, text)
    if m:
        g = m.groups()
        return won(g[0], g[1] and g[2], g[1]), None
    return None, None


def tags_dir(text, table, d):
    """근거 태그 중 방향과 맞는 것만(상향 노드엔 +·중립 근거, 하향 노드엔 −·중립 근거)."""
    sg = {'up': 1, 'bull': 1, 'down': -1, 'bear': -1}.get(d, 0)
    return [(n, s) for n, rx, s in table if re.search(rx, text) and (sg == 0 or s == 0 or s == sg)]


def tags(text, table):
    return [(n, sgn) for n, rx, sgn in table if re.search(rx, text)]


def stock_nodes(arts, bodies):
    nodes = []
    for a in arts:
        t, b = a['t'], bodies.get(a['u'], '')
        if not re.search(r'목표(?:주)?가|투자의견', t):
            continue
        br = broker_of(t, b)
        st = stock_of(t, br)
        if not st:
            continue
        d = 'up' if UP.search(t) else 'down' if DOWN.search(t) else 'keep' if KEEP.search(t + b[:400]) else None
        if not d:
            continue
        op = next((n for n, rx in OPIN if re.search(rx, t + ' ' + b[:600])), None)
        tp, prev = tp_of(t + ' ' + b[:1500])
        up = re.search(r'상승\s?여력(?:은|이)?\s?(?:약\s)?(\d{1,3}(?:\.\d)?)\s?%', b)
        # 숫자 검증: 이전→새 목표가 변화가 60% 넘거나, 방향(상향/하향)과 반대거나, 제목의 %와 크게 다르면 '확인 필요'
        chk = 0
        if tp and prev:
            r_ = tp / prev - 1
            pct = re.search(r'(\d{1,3})%\s?[↑↓]', t)
            if abs(r_) > 0.6 or (d == 'up' and r_ < 0) or (d == 'down' and r_ > 0) or (pct and abs(abs(r_) * 100 - int(pct.group(1))) > 8):
                chk = 1
        if up and float(up.group(1)) > 150:
            chk = 1
        rs = tags_dir(t + ' ' + b[:1500], REASONS, d)
        nodes.append({'k': 'stock', 'id': hashlib.md5(a['u'].encode()).hexdigest()[:10], 'name': st, 'br': br or '증권사 미상', 'dir': d, 'op': op, 'tp': tp, 'tp0': prev,
                      'chk': chk, 'upside': float(up.group(1)) if up else None, 'rs': [n for n, s in rs], 'rsg': {n: s for n, s in rs}, 't': t, 'u': a['u'], 'o': a['o'], 'ts': a['ts']})
    return nodes


def coin_nodes(arts, bodies):
    nodes = []
    for a in arts:
        t, b = a['t'], bodies.get(a['u'], '')
        txt = t + ' ' + a.get('d', '')
        for sym, (kn, rx) in COINS.items():
            if not re.search(rx, t):
                continue
            bu, be = len(BULL.findall(txt)), len(BEAR.findall(txt))
            if bu == be:
                d = 'neutral'
            else:
                d = 'bull' if bu > be else 'bear'
            who = PERSON.search(t)
            tgt = re.search(r'(\d+(?:\.\d+)?)\s?만\s?달러\s?(?:간다|전망|예상|도달|돌파|목표|갈|까지)', t) if sym == 'BTC' else None
            rs = tags_dir(t + ' ' + b[:1500], CR, d)
            nodes.append({'k': 'coin', 'id': hashlib.md5((a['u'] + sym).encode()).hexdigest()[:10], 'sym': sym, 'name': kn, 'dir': d, 'who': who.group(1).strip() if who else None,
                          'tgt': float(tgt.group(1)) if tgt else None, 'rs': [n for n, s in rs], 't': t, 'u': a['u'], 'o': a['o'], 'ts': a['ts']})
    return nodes


EXP_ROLE = re.compile(r'리서치센터장|센터장|본부장|수석연구위원|수석연구원|수석\s?전략가|연구위원|금융위원장|금감원장|금융감독원장|기재부 장관|기획재정부 장관|경제부총리|자본시장연구원|금융연구원|씨티|BofA|뱅크오브아메리카|노무라|최고투자책임자|CIO|수석\s?이코노미스트|이코노미스트|전략가|스트래티지스트|투자전략팀장|운용역|펀드매니저|한국은행|한은 총재|총재|KDI|한국개발연구원|IMF|OECD|국제통화기금|연준|파월|월가|골드만삭스|JP모건|모건스탠리|블랙록|자산운용|버핏|다이먼')
EXP_SAY = re.compile(r'전망|예상|경고|우려|조언|분석|진단|관측|내다|점쳤|권고|제시|"|“')
EXP_CAT = [('리스크 경고', r'경고|우려|위험|버블|거품|폭락|급락|경계|하방|침체|위기|리스크'), ('자산배분 조언', r'비중|분산|채권|현금|포트폴리오|자산배분|담아|줄여|늘려|매수 기회|분할 매수|리밸런싱|배당주')]
EXP_TOPIC = [('코스피·국내 증시', r'코스피|코스닥|국내 증시|韓 증시|한국 증시|K-?증시'), ('미국 증시', r'S&P|나스닥|뉴욕증시|미 증시|미국 증시|다우'), ('금리', r'금리|기준금리|연준|Fed|FOMC|한은'),
             ('환율', r'환율|원·달러|원달러|달러|엔화'), ('반도체·AI', r'반도체|HBM|AI|엔비디아|삼성전자|하이닉스'), ('부동산', r'부동산|집값|아파트|주택'), ('경기·성장률', r'성장률|경기|GDP|침체|물가|인플레'),
             ('코인', r'비트코인|이더리움|가상자산|암호화폐'), ('원자재', r'유가|금값|원자재|구리'), ('기타 시장', r'(?!)')]   # 위 주제에 안 맞으면 기타 시장(2026-10-20, 버리지 않음)


EXP_NOT = re.compile(r'접견|개소|취임|선임|인사|출범|MOU|업무협약|협약 체결|IMF급|IMF 외환위기|IMF 때|부고|별세|수상|시상')   # 2026-10-20 발언 아닌 행사·인사·비유


def expert_nodes(arts):
    out = []
    for a in arts:
        t = a['t'] + ' ' + a.get('d', '')[:160]
        if not (EXP_ROLE.search(a['t']) and EXP_SAY.search(t)) or re.search(r'목표(?:주)?가|투자의견', a['t']) or EXP_NOT.search(a['t']):
            continue
        tp = next((n for n, rx in EXP_TOPIC if re.search(rx, t)), '기타 시장')
        if tp == '기타 시장' and not re.search(r'[“"]', a['t']):   # 기타 시장은 따옴표 발언이 제목에 있을 때만
            continue
        who = EXP_ROLE.search(a['t']).group(0)
        m = re.search(r'([가-힣A-Za-z&·]{2,12}(?:증권|자산운용|운용|은행|연구원|캐피털|인베스트먼트)?)\s?(?:' + re.escape(who) + ')', a['t'])
        who_full = (m.group(0) if m else who).strip()
        cat = next((n for n, rx in EXP_CAT if re.search(rx, t)), '시장 전망')
        qt = ' '.join(re.findall(r'[“"]([^”"]{3,})[”"]', a['t'])) or a['t']   # 발언(따옴표) 부분으로 방향 판단
        bu = len(BULL.findall(qt)) + len(re.findall(r'사라|매수|기회|저평가|낙관|반등|과도|기대', qt))
        be = len(BEAR.findall(qt)) + len(re.findall(r'팔아|매도|고평가|비관|경고|조심|위험', qt))
        d = 'bull' if bu > be else 'bear' if be > bu else 'neutral'
        cat = next((n for n, rx in EXP_CAT if re.search(rx, qt)), '시장 전망')
        out.append({'k': 'expert', 'id': hashlib.md5(('e' + a['u']).encode()).hexdigest()[:10], 'who': who_full, 'topic': tp, 'cat': cat, 'dir': d,
                    't': a['t'], 'u': a['u'], 'o': a['o'], 'ts': a['ts']})
    return out


def tree_stock(ns):
    """종목 노드들 → 상승/하락/유지 가지, 가지 아래 근거 태그별 증권사 목록."""
    br = {}
    for d in ('up', 'down', 'keep'):
        reasons = {}
        for n in ns:
            if n['dir'] != d:
                continue
            for r in (n['rs'] or ['근거 기사 본문 확인 필요']):
                reasons.setdefault(r, set()).add(n['br'])
        br[d] = sorted([[r, sorted(b)] for r, b in reasons.items()], key=lambda x: -len(x[1]))
    return br


def main():
    now = time.time()
    db = json.load(open(DB, encoding='utf-8')) if os.path.exists(DB) else {'nodes': {}, 'seen': {}}
    with cf.ThreadPoolExecutor(8) as ex:
        sa = [a for L in ex.map(feed, STOCK_FEEDS) for a in L]
        ca = [a for L in ex.map(feed, COIN_FEEDS + STOCK_FEEDS[-1:]) for a in L]
    import email.utils
    for a in sa + ca:
        try:
            a['ts'] = int(email.utils.parsedate_to_datetime(a['pd']).timestamp())
        except Exception:
            try:
                a['ts'] = int(datetime.datetime.fromisoformat(a['pd'].replace('Z', '+00:00')).timestamp())
            except Exception:
                a['ts'] = None
    ea = [a for a in sa if EXP_ROLE.search(a['t']) and a['u'] not in db['seen']]
    sa = [a for a in sa if re.search(r'목표(?:주)?가|투자의견', a['t']) and a['u'] not in db['seen']]
    ca = [a for a in ca if any(re.search(rx, a['t']) for _, rx in COINS.values()) and a['u'] not in db['seen']]
    need = {a['u'] for a in sa + ca}
    for a in ea:
        if a['ts'] is None:
            ud = url_date(a['u']); a['ts'] = int(ud) if ud else None
    ea = [a for a in ea if a['ts'] and now - a['ts'] < 7 * 86400]
    with cf.ThreadPoolExecutor(8) as ex:
        bodies = dict(zip(need, ex.map(body, need)))
    for a in sa + ca:  # 날짜 확정: RSS → 주소 속 날짜 → 기사 메타데이터. 모르면 버림. 주소 날짜가 RSS보다 3일 넘게 이르면 옛 기사
        ud = url_date(a['u'])
        if a['ts'] is None and a['u'] in BDATE:
            try:
                a['ts'] = int(datetime.datetime.fromisoformat(BDATE[a['u']]).replace(tzinfo=KST).timestamp())
            except Exception:
                pass
        if a['ts'] is None:
            a['ts'] = int(ud) if ud else None
        elif ud and a['ts'] - ud > 3 * 86400:
            a['ts'] = int(ud)
    sa = [a for a in sa if a['ts'] and now - a['ts'] < 7 * 86400]
    ca = [a for a in ca if a['ts'] and now - a['ts'] < 7 * 86400]
    new = stock_nodes(sa, bodies) + coin_nodes(ca, bodies) + expert_nodes(ea)
    for n in new:
        db['nodes'][n['id']] = n
    for u in need | {a['u'] for a in ea}:
        db['seen'][u] = int(now)
    cut = now - 90 * 86400
    db['nodes'] = {k: v for k, v in db['nodes'].items() if v['ts'] >= cut}
    db['seen'] = {k: v for k, v in db['seen'].items() if v >= cut}
    json.dump(db, open(DB, 'w', encoding='utf-8'), ensure_ascii=False)
    # ---- 종목 집계(최근 30일)
    N = [n for n in db['nodes'].values() if n['k'] == 'stock' and n['ts'] >= now - 30 * 86400]
    by = {}
    for n in N:
        by.setdefault(n['name'], []).append(n)
    stocks = []
    for name, ns in by.items():
        ns.sort(key=lambda n: -n['ts'])
        latest = {}
        for n in ns:  # 증권사별 최신 의견만 집계
            latest.setdefault(n['br'], n)
        L = list(latest.values())
        tps = [n['tp'] for n in L if n['tp'] and not n.get('chk')]
        up, dn, kp = (sum(1 for n in L if n['dir'] == d) for d in ('up', 'down', 'keep'))
        tot = up + dn + kp
        agree = round(100 * max(up, dn, kp) / tot) if tot else 0
        ups = [n['upside'] for n in L if n.get('upside') is not None]
        stocks.append({'id': hashlib.md5(name.encode()).hexdigest()[:8], 'name': name, 'nb': len(L), 'nn': len(ns), 'up': up, 'down': dn, 'keep': kp, 'agree': agree,
                       'mixed': 1 if up and dn else 0, 'tp_avg': round(sum(tps) / len(tps)) if tps else None, 'tp_min': min(tps) if tps else None, 'tp_max': max(tps) if tps else None,
                       'upside': round(sum(ups) / len(ups), 1) if ups else None, 'last': ns[0]['ts'], 'tree': tree_stock(L),
                       'nodes': [{k: n.get(k) for k in ('br', 'dir', 'op', 'tp', 'tp0', 'upside', 'rs', 't', 'u', 'o', 'ts', 'chk')} for n in ns[:20]]})
    stocks.sort(key=lambda s: (-s['nb'], -s['last']))
    # ---- 코인 집계(최근 7일) + 업비트 시세
    C = [n for n in db['nodes'].values() if n['k'] == 'coin' and n['ts'] >= now - 7 * 86400]
    price = {}
    try:
        r = requests.get('https://api.upbit.com/v1/ticker', params={'markets': ','.join('KRW-' + s for s in COINS)}, timeout=15).json()
        price = {x['market'][4:]: {'p': x['trade_price'], 'chg': round(x['signed_change_rate'] * 100, 2)} for x in r}
    except Exception:
        pass
    hist = {}
    for sym in COINS:  # 업비트 공개 API 일봉 30일(차트용)
        try:
            r = requests.get('https://api.upbit.com/v1/candles/days', params={'market': 'KRW-' + sym, 'count': 30}, timeout=15).json()
            hist[sym] = [[x['candle_date_time_kst'][:10], x['trade_price']] for x in reversed(r)]
            time.sleep(0.15)
        except Exception:
            pass
    coins = []
    for sym, (kn, _) in COINS.items():
        ns = sorted([n for n in C if n['sym'] == sym], key=lambda n: -n['ts'])
        bu, be, ne = (sum(1 for n in ns if n['dir'] == d) for d in ('bull', 'bear', 'neutral'))
        tree = {}
        for d in ('bull', 'bear', 'neutral'):
            rs = {}
            for n in ns:
                if n['dir'] == d:
                    for r in n['rs']:
                        rs.setdefault(r, []).append(n['who'] or n['o'])
            tree[d] = sorted([[r, sorted(set(w))[:6], len(w)] for r, w in rs.items()], key=lambda x: -x[2])
        tg = [n['tgt'] for n in ns if n.get('tgt')]
        coins.append({'hist': hist.get(sym, []), 'sym': sym, 'name': kn, 'bull': bu, 'bear': be, 'neutral': ne, 'n': len(ns), 'price': price.get(sym), 'tgt': [min(tg), max(tg)] if tg else None, 'tree': tree,
                      'nodes': [{k: n.get(k) for k in ('dir', 'who', 'tgt', 'rs', 't', 'u', 'o', 'ts')} for n in ns[:20]]})
    E_ = sorted([n for n in db['nodes'].values() if n['k'] == 'expert' and n['ts'] >= now - 14 * 86400], key=lambda n: -n['ts'])
    experts = []
    for tp, _ in EXP_TOPIC:
        ns = [n for n in E_ if n['topic'] == tp]
        ns = [n for i, n in enumerate(ns) if n['t'] not in [x['t'] for x in ns[:i]]]   # 같은 제목(여러 피드) 한 번
        if not ns:
            continue
        bu, be = sum(1 for n in ns if n['dir'] == 'bull'), sum(1 for n in ns if n['dir'] == 'bear')
        experts.append({'topic': tp, 'n': len(ns), 'last': ns[0]['ts'], 'bull': bu, 'bear': be, 'mixed': 1 if bu and be else 0,
                        'cats': {c: sum(1 for n in ns if n['cat'] == c) for c in ('시장 전망', '자산배분 조언', '리스크 경고')},
                        'nodes': [{k: n.get(k) for k in ('who', 'cat', 'dir', 't', 'u', 'o', 'ts')} for n in ns[:12]]})
    experts.sort(key=lambda x: (-x['mixed'], -x['n']))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    experts.sort(key=lambda e: -e['last'])   # 새 발언이 나온 주제부터
    exp_meta = {'n24': sum(1 for n in E_ if n['ts'] >= now - 86400), 'n14': len(E_)}
    json.dump({'experts': experts, 'exp_meta': exp_meta, 'updated': datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M'), 'stocks': stocks, 'coins': coins},
              open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('새 노드', len(new), '종목', len(stocks), '코인 노드', len(C), '시세', bool(price))


if __name__ == '__main__':
    main()
