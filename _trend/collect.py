"""커뮤니티 니즈·트렌드 수집 분석기.

인기글 게시판과 질문·창업 게시판의 글을 모아 제목·본문·댓글에서
"하고 싶다 / 불편하다 / 있었으면 / 추천해 달라" 같은 니즈 문장을 뽑고 키워드로 묶는다.

  python collect.py               평소 실행(20분마다): 각 목록 첫 페이지
  python collect.py --backfill 7  지난 7일 치를 페이지를 넘겨 한꺼번에 받기

공개 파일은 trend/data/latest.json(집계·제목·링크)뿐이다. 글 상태와 니즈 문장 원문은
_trend/state/ 에만 두고, 운영자용 보고서 _trend/needs_report.html 을 따로 만든다.
"""
import html, json, os, re, sys, time, collections
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import money_private as MP           # 비공개 확장: 공개 저장소에 올리지 않는다(.gitignore)
except ImportError:
    MP = None
ROOT = os.path.dirname(HERE)
STATE = os.path.join(HERE, 'state')
POSTS_F = os.path.join(STATE, 'posts.json')
NEEDS_F = os.path.join(STATE, 'needs.json')
REPORT_F = os.path.join(HERE, 'needs_report.html')
LATEST_F = os.path.join(ROOT, 'trend', 'data', 'latest.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36',
      'Accept-Language': 'ko-KR,ko;q=0.9'}

# g: hot(인기글) / ask(질문·창업). key: 글 번호 정규식. sel: 제목 링크. row: 글 한 줄. date: 날짜 칸.
# cmt: 정적 댓글. body: 본문(질문·창업 게시판만). page: 지난 페이지 주소({n}). bf: 백필 최대 요청 수, stride: 페이지 건너뛰기.
SITES = [
    dict(id='pann', g='hot', name='네이트판', url='https://pann.nate.com/talk/ranking', key=r'/talk/(\d+)$',
         sel='div.mainarea div.cntList a', cmt='dl.cmt_item dd.usertxt', pann_day=True),
    dict(id='clien', g='hot', name='클리앙', url='https://www.clien.net/service/group/clien_all?&od=T33', key=r'/service/board/(\w+)/(\d+)',
         sel='div.list_item.symph_row a.list_subject', row='div.list_item', date='span.timestamp', cmt='div.comment_row div.comment_view',
         page='https://www.clien.net/service/group/clien_all?&od=T33&po={n0}', bf=40, stride=5),
    dict(id='theqoo', g='hot', name='더쿠', url='https://theqoo.net/hot', key=r'/hot/(\d+)',
         sel='table.theqoo_board_table tr:not(.notice) td.title a:not(.replyNum)', row='tr', date='td.time',
         page='https://theqoo.net/hot?page={n}', bf=100),
    dict(id='instiz', g='hot', name='인스티즈', url='https://www.instiz.net/pt?srt=3', key=r'/pt/(\d+)', sel='td.listsubject a', tail_num=True,
         row='tr', cmt='td.comment_memo span[id^=n]'),
    dict(id='bobae', g='hot', name='보배드림', url='https://www.bobaedream.co.kr/list?code=best', key=r'code=best.*No=(\d+)',
         sel='table#boardlist a.bsubject', row='tr', date='td.date', cmt='div.commentlistbox dd[id^=bepl_small_cmt]',
         page='https://www.bobaedream.co.kr/list?code=best&page={n}', bf=60),
    dict(id='ruliweb', g='hot', name='루리웹', url='https://bbs.ruliweb.com/best/all/now', key=r'/read/(\d+)',
         sel='table.board_list_table tr.table_body:not(.notice) td.subject a.subject_link', row='tr', date='td.time',
         page='https://bbs.ruliweb.com/best/all/now?page={n}', bf=30),
    dict(id='dc', g='hot', name='디시인사이드', url='https://gall.dcinside.com/board/lists/?id=dcbest', key=r'id=dcbest&no=(\d+)',
         sel='section.left_content tr.us-post td.gall_tit a:not(.reply_numbox)', row='tr', date='td.gall_date',
         page='https://gall.dcinside.com/board/lists/?id=dcbest&page={n}', bf=60),
    dict(id='mlbpark', g='hot', name='MLB파크', url='https://mlbpark.donga.com/mp/b.php?b=bullpen&m=bbs&p=1&order=hit', key=r'b=bullpen.*id=(\d+)',
         sel='li.items div.title a', cmt='span.re_txt'),
    dict(id='todayhumor', g='hot', name='오늘의유머', url='https://www.todayhumor.co.kr/board/list.php?table=bestofbest', key=r'table=bestofbest.*no=(\d+)',
         sel='table.table_list td.subject a', row='tr', date='td.date',
         page='https://www.todayhumor.co.kr/board/list.php?table=bestofbest&page={n}', bf=10),
    dict(id='slr', g='hot', name='SLR클럽', url='https://www.slrclub.com/bbs/zboard.php?id=best_article', key=r'id=best_article.*no=(\d+)',
         sel='td.sbj a', row='tr'),
    dict(id='cook82', g='hot', name='82쿡', url='https://www.82cook.com/entiz/enti.php?bn=15', key=r'num=(\d+)',
         sel='div#list_table tr:not(.noticeList) td.title a', row='tr', date='td.regdate', cmt='ul.reples li p',
         page='https://www.82cook.com/entiz/enti.php?bn=15&page={n}', bf=50, stride=8),
    dict(id='dogdrip', g='hot', name='개드립', url='https://www.dogdrip.net/dogdrip?sort_index=popular', key=r'/dogdrip/(\d+)',
         sel='a.title-link', row='li', cmt='div.comment-content .xe_content',
         page='https://www.dogdrip.net/dogdrip?sort_index=popular&page={n}', bf=40),
    dict(id='arca', g='hot', name='아카라이브', url='https://arca.live/b/live', key=r'/b/live/(\d+)',
         sel='div.list-table a.title.hybrid-title', row='div.vrow', cmt='div.comment-item div.message div.text'),
    # 질문·창업 게시판: 무언가 하고 싶거나 막힌 사람이 직접 묻는 곳
    dict(id='clien_venture', g='ask', name='클리앙 창업한당', url='https://www.clien.net/service/board/cm_venture', key=r'/cm_venture/(\d+)',
         sel='div.list_item.symph_row a.list_subject', row='div.list_item', date='span.timestamp', cmt='div.comment_row div.comment_view',
         body='div.post_article', page='https://www.clien.net/service/board/cm_venture?&od=T31&category=0&po={n0}', bf=6),
    dict(id='clien_kin', g='ask', name='클리앙 아무거나질문', url='https://www.clien.net/service/board/kin', key=r'/kin/(\d+)',
         sel='div.list_item.symph_row a.list_subject', row='div.list_item', date='span.timestamp', cmt='div.comment_row div.comment_view',
         body='div.post_article', page='https://www.clien.net/service/board/kin?&od=T31&category=0&po={n0}', bf=6),
    dict(id='dc_startup', g='ask', name='디시 스타트업 갤러리', url='https://gall.dcinside.com/mgallery/board/lists/?id=startup', key=r'id=startup&no=(\d+)',
         sel='tr.us-post td.gall_tit a:not(.reply_numbox)', row='tr', date='td.gall_date', body='div.write_div',
         page='https://gall.dcinside.com/mgallery/board/lists/?id=startup&page={n}', bf=5),
    dict(id='cook82_q', g='ask', name='82쿡 이런글저런질문', url='https://www.82cook.com/entiz/enti.php?bn=16', key=r'num=(\d+)',
         sel='div#list_table tr:not(.noticeList) td.title a', row='tr', date='td.regdate', cmt='ul.reples li p', body='#articleBody',
         page='https://www.82cook.com/entiz/enti.php?bn=16&page={n}', bf=3),
    dict(id='kin', g='ask', name='지식iN 경제', url='https://kin.naver.com/qna/list.naver?dirId=4', key=r'docId=(\d+)',
         sel='td.title a', row='tr', body='div.questionDetail',
         page='https://kin.naver.com/qna/list.naver?dirId=4&page={n}', bf=40, stride=10),
]
if MP:
    SITES += MP.SITES                     # 비공개 수집처(돈 신호)
SITE_NAME = {s['id']: s['name'] for s in SITES}
SITE_GROUP = {s['id']: s['g'] for s in SITES}

KEEP_DAYS = 8             # 글 상태 보관(오늘 + 지난 7일)
DETAIL_LIVE = {'hot': 15, 'ask': 30, 'money': 20}   # 평소 실행 때 사이트당 본문·댓글 수집 수
DETAIL_BACKFILL = 300     # 백필 때 사이트당 본문·댓글 수집 상한
REFRESH_MIN = 60          # 댓글 재수집 간격
REFRESH_AGE_H = 24        # 처음 본 뒤 이 시간까지만 재수집
SLEEP = 0.6

STOP = set('''
진짜 정말 사람 오늘 생각 이거 그거 저거 지금 정도 하나 사진 얘기 이유 경우 우리 자기 이번 시간 때문 이상 근데 그냥 그래서
그런데 게시물 게시글 댓글 추천 반대 비추 펼쳐보기 이미지 동영상 영상 베스트 링크 출처 기사 내용 본문 제목 글쓴이 작성자
자체 부분 느낌 수준 요즘 최근 하루 이제 다음 이후 처음 마지막 진심 레전드 근황 상황 모습 의미 결과 이야기 대박 실화
가지 사실 자신 누구 무엇 어디 언제 거기 여기 저기 이것 그것 저것 뭔가 같은 모두 다른 무슨 이런 그런 저런 제일 가장
인증 공지 이용 규칙 운영 회원 유머 개드립 더쿠 인스티즈 루리웹 클리앙 보배 네이트 디시 아카 오유 엠팍 펌글
경험 상태 일반 방법 문제 이건 그게 뭐가 정말로 완전 계속 그동안 무조건 바로 혹시 아마 역시 별로 자꾸
JPG GIF PNG MP4 조회 댓글수정 수정 삭제 가능 소리 짤방 스압 브금 싱갤 분들 형님 님들 원글 본인 상대 개인 사용 발생
관련 대한 대해 위해 통해 동안 사이 정보 내외 전체 기준 질문 답변 궁금 고민 문의 부탁 감사 안녕 조언 도움
필요 마음 얼마 비용 가격 추가 확인 해결 진행 시작 준비 계획
'''.split())

# 니즈 분류: 문장 하나에 여러 종류가 붙을 수 있다. 순서는 화면 표시 순서.
NEED_TYPES = [
    ('창업·부업', r'창업|사업(을|하|자|체|계획|아이템)|부업|가게|매장|장사|프랜차이즈|자영업|스마트스토어|쇼핑몰|오픈(하려|준비|예정)|차리(려|고|는|면)|퇴사 ?(후|하고)|1인 ?(기업|사업)|외주|수익화'),
    ('하고 싶음', r'하고 ?싶|해보고 ?싶|배우고 ?싶|시작하려|시작해 ?보|도전|준비 ?중|알아보(는|고) ?(중|있)|고려 ?중|하려고|해볼까|할까 ?(하|고민)|계획 ?중|만들고 ?싶|되고 ?싶'),
    ('바람', r'있었으면|있으면 ?좋겠|생겼으면|해 ?줬으면|해 ?주면 ?좋|누가 ?(좀 )?만들|나왔으면|좋겠(다|어|네|습)|왜 ?없|없나요|없을까요'),
    ('불편·불만', r'불편|귀찮|짜증|답답|번거|스트레스|너무 ?(비싸|어렵|오래|힘들|많)|비싸(서|다|요|네)|최악|불만|못 ?하겠|어려워|힘들어|힘드네|막막|빡치|열받'),
    ('찾음·추천', r'추천|어디서|어디가 ?(좋|싸)|뭐 ?사|뭘 ?사|찾고 ?있|찾습니다|아시는 ?분|괜찮은 ?(곳|데|거|제품)|골라|구합니다|구해요'),
    ('방법 질문', r'어떻게|방법|하는 ?법|알려 ?주|가능한가|가능할까|되나요|해야 ?(하나|할까|되나|하는지)|맞나요|괜찮을까|어떤가요'),
    ('비용', r'얼마(?!나)|비용|가격|견적|시세|월세|권리금|수수료|단가|예산'),
]
NEED_RX = [(n, re.compile(r)) for n, r in NEED_TYPES]
# 니즈를 가리키는 말 자체(불편·짜증 등)는 '무엇을' 원하는지가 아니므로 니즈 키워드에서 뺀다
NEED_WORDS = set('''불편 짜증 최악 불만 스트레스 도전 답답 귀찮 막막 걱정 후회 정신 번거 불만족 열받 빡침 고생 힘듦 어려움
시작 준비 계획 고민 방법 질문 추천 비용 가격 견적 시세 단가 예산 수수료 구매 선택 생각 이해 필요 정도 상담'''.split())
# 창업 주제 키워드에서 뺄 창업 일반어(무슨 창업인지를 보려고)
BIZ_WORDS = set('창업 사업 사업자 자영업 자영업자 가게 매장 장사 부업 프랜차이즈 오픈 퇴사 수익 수익화 외주 개업 폐업 기업 1인'.split())
NEED_ORDER = [n for n, _ in NEED_TYPES]

MONEY_RX = MP.MONEY_RX if MP else []     # 비공개 확장이 없으면 돈 신호 분류도 없다


def now_kst():
    return datetime.now(KST).replace(microsecond=0)


def load(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    m = re.search(r'charset=([\w-]+)', r.headers.get('content-type', ''), re.I)
    return BeautifulSoup(r.content, 'html.parser', from_encoding=m.group(1) if m else None)


# ---------- 날짜 ----------

def safe_dt(y, mo, d, h, mi):
    try:
        return datetime(y, mo, d, h, mi, tzinfo=KST)
    except ValueError:
        return None


def parse_dt(text, now):
    """목록에 찍힌 여러 날짜 표기를 KST datetime 으로. 못 읽으면 None."""
    text = text.strip()
    m = re.search(r'(20\d{2})[-./](\d{1,2})[-./](\d{1,2})\.?(?:[T\s]+(\d{1,2}):(\d{2}))?', text)
    if m:
        h, mi = (int(m[4]), int(m[5])) if m[4] else (12, 0)
        return safe_dt(int(m[1]), int(m[2]), int(m[3]), h, mi)
    m = re.search(r'\b(\d{2})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})', text)       # 26/10/14 17:12
    if m:
        return safe_dt(2000 + int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]))
    m = re.search(r'(?<![\d.])(\d{2})\.(\d{2})\.(\d{2})\s+(\d{1,2}):(\d{2})', text)  # 26.10.14 22:41
    if m:
        return safe_dt(2000 + int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]))
    m = re.search(r'(?<![\d.])(\d{2})\.(\d{2})\.(\d{2})(?![\d.])', text)        # 20.03.25
    if m:
        return safe_dt(2000 + int(m[1]), int(m[2]), int(m[3]), 12, 0)
    m = re.search(r'(\d+)\s*(초|분|시간|일)\s*전', text)
    if m:
        n = int(m[1])
        return now - {'초': timedelta(seconds=n), '분': timedelta(minutes=n), '시간': timedelta(hours=n), '일': timedelta(days=n)}[m[2]]
    m = re.search(r'(?<![\d.:])(\d{1,2}):(\d{2})(?::\d{2})?(?!\d)', text)       # 오늘 HH:MM
    if m and int(m[1]) < 24:
        dt = now.replace(hour=int(m[1]), minute=int(m[2]), second=0)
        return dt - timedelta(days=1) if dt > now + timedelta(minutes=10) else dt
    m = re.search(r'(?<![\d.])(\d{1,2})[./-](\d{1,2})(?![\d.])', text)           # 10.13, 10/12
    if m:
        dt = safe_dt(now.year, int(m[1]), int(m[2]), 12, 0)
        if dt and dt > now + timedelta(days=1):
            dt = safe_dt(now.year - 1, int(m[1]), int(m[2]), 12, 0)
        return dt
    return None


def row_dt(a, site, now):
    if not site.get('row'):
        return None
    tag, _, cls = site['row'].partition('.')
    row = a.find_parent(tag, class_=cls) if cls else a.find_parent(tag)
    if row is None:
        return None
    for e in row.find_all(attrs={'datetime': True}):
        try:
            return datetime.fromisoformat(e['datetime'].replace('Z', '+00:00')).astimezone(KST)
        except ValueError:
            pass
    for c in row.select(site['date']) if site.get('date') else []:
        for t in (c.get('title') or '', c.get_text(' ', strip=True)):
            dt = parse_dt(t, now) if t else None
            if dt:
                return dt
    rest = row.get_text(' ', strip=True).replace(a.get_text(' ', strip=True), ' ')
    return parse_dt(rest, now)


# ---------- 목록 ----------

def clean_title(t, tail_num=False):
    t = ' '.join(t.split())
    t = re.sub(r'^\d{1,3}\s+', '', t)
    t = re.sub(r'^(모공|새로운소식|사진|아무거나|알뜰구매|팁과강좌)\s+', '', t)
    t = re.sub(r'^\[\S{1,6}갤\]\s*', '', t)
    t = re.sub(r'\s*[\(\[]\d{1,5}[\)\]]\s*$', '', t)
    if tail_num:
        t = re.sub(r'\s+\d{1,5}$', '', t)
    return t.strip()


def bad_title(t):
    if len(t) < 4 or len(t) > 150 or re.fullmatch(r'[\d\s\(\)\[\],.]+', t):
        return True
    return bool(re.search(r'^(공지|\[공지\])|이용\s?(규칙|안내)|운영\s?원칙|필독|서버 작업', t))


def parse_list(site, soup, now, base):
    """[(키, 제목, 주소, 작성시각 ISO 또는 None)]"""
    rx = re.compile(site['key'])
    found = {}
    for a in soup.select(site['sel']):
        href = (a.get('href') or '').split('#')[0]
        m = rx.search(href)
        if not m:
            continue
        key = site['id'] + ':' + '_'.join(m.groups())
        sub = a.select_one('span.subject_fixed')      # 클리앙: 말머리 빼고 제목만
        t = clean_title((sub or a).get_text(' ', strip=True), site.get('tail_num'))
        if bad_title(t):
            continue
        cur = found.get(key)
        if not cur or len(t) > len(cur[0]):
            dt = row_dt(a, site, now)
            found[key] = (t, urljoin(base, href), dt.isoformat() if dt else (cur[2] if cur else None))
    return [(k, *v) for k, v in found.items()]


def list_backfill(site, now, days):
    cutoff = now - timedelta(days=days)
    out = {}
    if site.get('pann_day'):
        # 네이트판은 날짜별 랭킹 주소가 따로 있다. 작성 시각 대신 랭킹 날짜 정오로 둔다.
        for i in range(days + 1):
            d = now - timedelta(days=i)
            u = f'https://pann.nate.com/talk/ranking/d?stdt={d:%Y%m%d}&page=1'
            try:
                for k, t, url, _ in parse_list(site, fetch(u), now, u):
                    out.setdefault(k, (k, t, url, d.replace(hour=12, minute=0, second=0).isoformat() if i else None))
            except Exception:
                pass
            time.sleep(SLEEP)
        return list(out.values())
    if not site.get('page'):
        return []
    stride, n, old_streak = site.get('stride', 1), 1, 0
    for _ in range(site.get('bf', 10)):
        u = site['page'].format(n=n, n0=n - 1)
        try:
            items = parse_list(site, fetch(u), now, u)
        except Exception:
            break
        time.sleep(SLEEP)
        if not items:
            break
        fresh = [it for it in items if not it[3] or datetime.fromisoformat(it[3]) >= cutoff]
        for it in fresh:
            out.setdefault(it[0], it)
        old_streak = 0 if fresh else old_streak + 1
        if old_streak >= 2:
            break
        n += stride
    return list(out.values())


# ---------- 본문·댓글 ----------

def collect_detail(site, url):
    soup = fetch(url)
    for x in soup.select('span.name_re'):
        x.decompose()
    seen, cmts = set(), []
    for e in soup.select(site['cmt']) if site.get('cmt') else []:
        t = ' '.join(e.get_text(' ', strip=True).split())
        t = re.sub(r'펼쳐보기▼?$|댓글수정|답글쓰기', '', t).strip()
        if len(t) < 2 or t in seen or re.fullmatch(r'(답글|추천|반대)\s*\d*', t):
            continue
        seen.add(t)
        cmts.append(t)
    body = ''
    if site.get('body'):
        e = soup.select_one(site['body'])
        if e:
            body = ' '.join(e.get_text(' ', strip=True).split())[:3000]
    return cmts, body


# ---------- 분석 도구 ----------

class Tok:
    def __init__(self):
        from kiwipiepy import Kiwi
        self.kiwi = Kiwi()

    def nouns(self, text):
        text = re.sub(r'\.?(jpe?g|gif|png|webp|mp4|avi)\b', ' ', text, flags=re.I)
        out = []
        for tk in self.kiwi.tokenize(text):
            if tk.tag not in ('NNG', 'NNP', 'SL'):
                continue
            w = tk.form
            if tk.tag == 'SL' and len(w) <= 5:
                w = w.upper()
            if len(w) < 2 or w in STOP:
                continue
            out.append(w)
        return out


def sentences(text):
    parts = re.split(r'(?<=[.!?。])\s+|\n+|[ㅋㅎ]{3,}|[ㅠㅜ]{2,}|(?<=[요다죠네])\s+(?=[가-힣])', text)
    return [p.strip() for p in parts if p and 6 <= len(p.strip()) <= 220]


def extract_needs(texts, tok):
    """[(출처 t/b/c, 글)] → [[출처, [니즈 종류], 문장, [명사]]]"""
    out, seen = [], set()
    for src, text in texts:
        for s in ([text] if src == 't' else sentences(text)):
            ty = [n for n, rx in NEED_RX if rx.search(s)]
            mty = [n for n, _, rx in MONEY_RX if rx.search(s)]
            if not (ty or mty) or s in seen:
                continue
            seen.add(s)
            kws = sorted(set(tok.nouns(s)))
            if kws:
                out.append([src, ty, s[:220], kws, mty])
    return out


# ---------- 수집 실행 ----------

def run_site(site, posts, now, backfill_days):
    res = dict(site=site['id'], ok=False, n=0, err=None, items=[], detail={})
    try:
        items = parse_list(site, fetch(site['url']), now, site['url'])
        if site['g'] == 'ask' and site.get('page') and not backfill_days:
            u = site['page'].format(n=2, n0=1)
            time.sleep(SLEEP)
            items += parse_list(site, fetch(u), now, u)
        if backfill_days:
            items += list_backfill(site, now, backfill_days)
    except Exception as e:
        res['err'] = f'{type(e).__name__}: {str(e)[:120]}'
        return res
    uniq = {}
    for it in items:
        if it[0] not in uniq or (it[3] and not uniq[it[0]][3]):
            uniq[it[0]] = it
    items = list(uniq.values())
    res.update(items=items, n=len(items), ok=bool(items))
    if not items:
        res['err'] = '글 링크 0개(구조 변경 또는 차단 의심)'
    if not (site.get('cmt') or site.get('body')):
        return res
    cands = []
    for key, _, url, _ in items:
        p = posts.get(key)
        if p is None or 'cf' not in p:
            cands.append((0, key, url))
            continue
        age = (now - datetime.fromisoformat(p['fs'])).total_seconds() / 3600
        since = (now - datetime.fromisoformat(p['cf'])).total_seconds() / 60
        if site.get('cmt') and age <= REFRESH_AGE_H and since >= REFRESH_MIN:
            cands.append((1, key, url))
    cands.sort(key=lambda x: x[0])
    cap = DETAIL_BACKFILL if backfill_days else DETAIL_LIVE[site['g']]
    for _, key, url in cands[:cap]:
        try:
            time.sleep(SLEEP)
            res['detail'][key] = collect_detail(site, url)
        except Exception:
            pass
    return res


def update(posts, needs, results, tok, now):
    hk, iso = now.strftime('%Y%m%d%H'), now.isoformat()
    for res in results:
        for rank, (key, title, url, pt) in enumerate(res['items'], 1):
            p = posts.get(key)
            if p is None:
                p = posts[key] = dict(s=res['site'], t=title, u=url, fs=iso, br=rank, h=[])
            if p.get('t') != title or p.get('tv') != 2:
                p['t'], p['tk'], p['tv'] = title, sorted(set(tok.nouns(title))), 2
                p['tn'] = extract_needs([('t', title)], tok)
            if pt and not p.get('pt'):
                p['pt'] = pt
            p['ls'], p['r'] = iso, rank
            p['br'] = min(p.get('br', rank), rank)
            if hk not in p['h']:
                p['h'].append(hk)
        for key, (cmts, body) in res['detail'].items():
            p = posts.get(key)
            if p is None:
                continue
            c = collections.Counter()
            for t in cmts:
                c.update(set(tok.nouns(t)))
            p['nc'], p['ck'], p['cf'] = len(cmts), dict(c.most_common(40)), iso
            needs[key] = extract_needs([('b', body)] + [('c', t) for t in cmts], tok)
    cut = now - timedelta(days=KEEP_DAYS)
    for key in [k for k, p in posts.items() if post_time(p) < cut and datetime.fromisoformat(p['ls']) < cut]:
        del posts[key]
    for key in [k for k in needs if k not in posts]:
        del needs[key]


def post_time(p):
    return datetime.fromisoformat(p.get('pt') or p['fs'])


# ---------- 집계 ----------

def mention_kws(p):
    s = set(p.get('tk', []))
    s.update(k for k, v in p.get('ck', {}).items() if v >= 2)
    return s - STOP


def analyze(posts, needs, site_stat, now):
    today0 = now.replace(hour=0, minute=0, second=0)
    day_keys = [(today0 - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, -1, -1)]   # 지난 7일 + 오늘
    periods = {'today': today0, '24': now - timedelta(hours=24), '7d': today0 - timedelta(days=7),
               'week': today0 - timedelta(days=7)}                    # week: 오늘을 뺀 지난 7일
    ends = {'week': today0}

    plist = []
    for k, p in posts.items():
        if SITE_GROUP.get(p['s']) not in ('hot', 'ask'):
            continue                                        # 돈 신호 수집처는 공개 집계에서 뺀다
        pt = post_time(p)
        nd = [x[:4] for x in (p.get('tn') or []) + needs.get(k, []) if x[1]]
        nkw, ntype = set(), collections.Counter()
        for _, ty, _, kws in nd:
            nkw.update(w for w in kws if w not in STOP and w not in NEED_WORDS)
            ntype.update(ty)
        plist.append(dict(k=k, p=p, pt=pt, day=pt.strftime('%Y-%m-%d'), mk=mention_kws(p), nd=nd, nkw=nkw, ntype=ntype))

    top = lambda c, n=50: [[k, v] for k, v in c.most_common(n)]
    out_p, need_p = {}, {}
    for name, start in periods.items():
        act = [x for x in plist if x['pt'] >= start and (name not in ends or x['pt'] < ends[name])]
        mention, per_site, site_posts = collections.Counter(), collections.defaultdict(collections.Counter), collections.Counter()
        nk_posts, nk_type, ntype, nsent = collections.Counter(), collections.defaultdict(collections.Counter), collections.Counter(), 0
        for x in act:
            mention.update(x['mk'])
            per_site[x['p']['s']].update(x['mk'])
            site_posts[x['p']['s']] += 1
            nsent += len(x['nd'])
            for _, ty, _, kws in x['nd']:
                ntype.update(ty)
                for w in set(kws) - STOP - NEED_WORDS:
                    nk_type[w].update(ty)
            nk_posts.update(x['nkw'])
        out_p[name] = dict(posts=len(act), mention=top(mention, 80),
                           sites={s: dict(posts=site_posts[s], top=top(per_site[s], 10)) for s in site_posts})
        need_p[name] = dict(
            posts=sum(1 for x in act if x['nd']), sentences=nsent,
            types=[[t, ntype[t]] for t in NEED_ORDER],
            keywords=[[w, n, {t: nk_type[w][t] for t in NEED_ORDER if nk_type[w][t]}] for w, n in nk_posts.most_common(60)],
        )

    def share_cmp(field, min_today):
        """오늘 vs 지난 7일: 사이트별 수집량 차이를 줄이려고 같은 기간 글 대비 비율로 비교."""
        t_posts = [x for x in plist if x['pt'] >= today0]
        w_posts = [x for x in plist if periods['7d'] <= x['pt'] < today0]
        tc, wc = collections.Counter(), collections.Counter()
        for x in t_posts:
            tc.update(x[field])
        for x in w_posts:
            wc.update(x[field])
        nt, nw = max(len(t_posts), 1), max(len(w_posts), 1)
        rows = []
        for w, v in tc.items():
            if v >= min_today:
                ts, ws = v / nt, wc[w] / nw
                rows.append([w, v, round(wc[w] / 7, 1), round(ts * 100, 2), round(ws * 100, 2), round((ts + 0.002) / (ws + 0.002), 2)])
        rows.sort(key=lambda r: (-r[5], -r[1]))
        return dict(today_posts=len(t_posts), week_posts=len(w_posts), rows=rows[:25])

    tvw, tvw_need = share_cmp('mk', 3), share_cmp('nkw', 2)

    post_ref, refs = {}, []

    def ref(x):
        if x['k'] not in post_ref:
            p = x['p']
            post_ref[x['k']] = len(refs)
            refs.append([p['s'], p['t'], p['u'], x['pt'].strftime('%m-%d %H:%M'), p.get('nc', 0), len(x['nd']),
                         [t for t in NEED_ORDER if x['ntype'][t]]])
        return post_ref[x['k']]

    focus = [w for n in periods for w, _ in out_p[n]['mention'][:60]]
    focus += [w for n in periods for w, _, _ in need_p[n]['keywords'][:60]]
    focus += [r[0] for r in tvw['rows']] + [r[0] for r in tvw_need['rows']]
    by_kw = collections.defaultdict(list)
    for x in plist:
        for w in x['mk'] | x['nkw']:
            by_kw[w].append(x)
    detail = {}
    for w in dict.fromkeys(focus):
        xs = sorted(by_kw.get(w, []), key=lambda x: (w in x['nkw'], x['pt']), reverse=True)
        md, ndd, co, types = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
        for x in xs:
            if w in x['mk']:
                md[x['day']] += 1
            if w in x['nkw']:
                ndd[x['day']] += 1
                for _, ty, _, kws in x['nd']:
                    if w in kws:
                        types.update(ty)
            co.update((x['mk'] | x['nkw']) - {w})
        detail[w] = dict(days=[md[d] for d in day_keys], need_days=[ndd[d] for d in day_keys],
                         sites=dict(collections.Counter(x['p']['s'] for x in xs)),
                         types={t: types[t] for t in NEED_ORDER if types[t]},
                         posts=[ref(x) for x in xs[:15]], co=top(co, 8))

    # 창업·하고 싶은 일: 니즈 중 창업·부업 / 하고 싶음 이 붙은 글(최근 7일 + 오늘)
    st = [x for x in plist if x['pt'] >= periods['7d'] and (x['ntype']['창업·부업'] or x['ntype']['하고 싶음'])]
    def own(x, t):   # 글쓴이 본인(제목·본문)이 말한 니즈인지
        return sum(1 for src, ty, _, _ in x['nd'] if src in 'tb' and t in ty)
    st.sort(key=lambda x: (own(x, '창업·부업') > 0, own(x, '하고 싶음') > 0, x['ntype']['창업·부업'] * 2 + x['ntype']['하고 싶음'], x['pt']), reverse=True)
    sk = collections.Counter()
    for x in st:
        for _, ty, _, kws in x['nd']:
            if '창업·부업' in ty:
                sk.update(set(kws) - STOP - NEED_WORDS - BIZ_WORDS)
    startup = dict(posts=len(st), keywords=top(sk, 30), list=[ref(x) for x in st[:40]])

    latest = dict(
        updated=now.isoformat(), days=day_keys,
        day_posts=[sum(1 for x in plist if x['day'] == d) for d in day_keys],
        sites={k: v for k, v in SITE_NAME.items() if SITE_GROUP[k] != 'money'},
        groups={k: v for k, v in SITE_GROUP.items() if v != 'money'},
        site_status={k: v for k, v in site_stat.items() if SITE_GROUP.get(k) != 'money'},
        need_types=NEED_ORDER, periods=out_p, needs=need_p, today_vs_week=tvw, needs_today_vs_week=tvw_need,
        startup=startup, detail=detail, posts=refs,
    )
    latest['summary'] = make_summary(latest)
    return latest, plist


def make_summary(d):
    n7, nt = d['needs']['7d'], d['needs']['today']
    ok = sum(1 for s in d['site_status'].values() if s['ok'])
    lines = [f"지난 7일과 오늘, {ok}개 게시판 글 {d['periods']['7d']['posts']:,}건에서 무언가를 원하거나 막혀 있는 문장 "
             f"{n7['sentences']:,}개를 찾았습니다(오늘 {nt['sentences']:,}개)."]
    kws = [w for w, _, _ in n7['keywords'][:6]]
    if kws:
        lines.append(f"이번 주 사람들이 가장 많이 원하거나 묻는 주제는 {', '.join(kws)}입니다.")
    if d['startup']['keywords']:
        sk = [w for w, _ in d['startup']['keywords'][:5]]
        lines.append(f"창업·부업이나 새로 해 보고 싶은 일을 말한 글은 {d['startup']['posts']:,}건이고, 주로 {', '.join(sk)} 이야기입니다.")
    rows = d['needs_today_vs_week']['rows'][:4] or d['today_vs_week']['rows'][:4]
    if rows:
        lines.append(f"지난주보다 오늘 눈에 띄게 늘어난 키워드는 {', '.join(r[0] for r in rows)}입니다.")
    return lines


# ---------- 운영자용 보고서(비공개, git 에 올리지 않음) ----------

def write_report(d, plist, now):
    e = html.escape
    week = [x for x in plist if x['pt'] >= now - timedelta(days=8)]
    by_type, by_kw = collections.defaultdict(list), collections.defaultdict(list)
    for x in week:
        for src, ty, s, kws in x['nd']:
            for t in ty:
                by_type[t].append((x, src, s, ty))
            for w in kws:
                by_kw[w].append((x, src, s, ty))
    srcname = {'t': '제목', 'b': '본문', 'c': '댓글'}

    def li(x, src, s, ty, tags=False):
        p = x['p']
        tg = ''.join(f"<span class=t>{e(t)}</span>" for t in ty) if tags else ''
        return (f"<li>{tg}{e(s)} <span class=m>— {srcname[src]} · {e(SITE_NAME[p['s']])} · {x['pt']:%m-%d} · "
                f"<a href='{e(p['u'])}' target=_blank rel=noopener>{e(p['t'][:40])}</a></span></li>")

    def section(title, rows, n, tags=False):
        rows = sorted(rows, key=lambda r: r[0]['pt'], reverse=True)
        return f"<h3>{title} ({len(rows)}문장)</h3><ul>" + ''.join(li(*r, tags=tags) for r in rows[:n]) + '</ul>'

    parts = [f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
             f"<title>니즈 보고서 {now:%m-%d %H:%M}</title>",
             "<style>body{font:15px/1.6 'Malgun Gothic',sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#222;background:#fff}"
             "h2{margin-top:36px;border-bottom:2px solid #333}h3{margin:22px 0 6px}li{margin:3px 0}.m{color:#888;font-size:12px}"
             "a{color:#1c5cab}.t{display:inline-block;font-size:11px;border:1px solid #bbb;border-radius:4px;padding:0 4px;margin-right:4px;color:#555}</style>",
             f"<h1>니즈 보고서 (비공개) · {now:%Y-%m-%d %H:%M} 기준 최근 8일</h1>",
             '<p>' + '<br>'.join(e(s) for s in d['summary']) + '</p>',
             '<h2>창업·부업 / 하고 싶은 일</h2>',
             section('창업·부업', by_type['창업·부업'], 200), section('하고 싶음', by_type['하고 싶음'], 200),
             '<h2>니즈 키워드별 문장 (최근 7일 상위 40)</h2>']
    for w, n, types in d['needs']['7d']['keywords']:
        parts.append(f"<h3>{e(w)} · 글 {n}건 · " + ', '.join(f'{e(k)} {v}' for k, v in types.items()) + '</h3><ul>'
                     + ''.join(li(*r, tags=True) for r in sorted(by_kw[w], key=lambda r: r[0]['pt'], reverse=True)[:20]) + '</ul>')
    parts.append('<h2>바람 · 불편·불만 · 찾음</h2>')
    for t in ('바람', '불편·불만', '찾음·추천'):
        parts.append(section(t, by_type[t], 200))
    with open(REPORT_F, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    now = now_kst()
    if '--if-stale' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--if-stale') + 1])
        upd = load(LATEST_F, {}).get('updated')
        if upd and (now - datetime.fromisoformat(upd)).total_seconds() < limit * 60:
            print(f'최근 갱신 {upd} - {limit}분 이내라 건너뜀')
            return 0
    bf = int(sys.argv[sys.argv.index('--backfill') + 1]) if '--backfill' in sys.argv else 0
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    posts, needs = load(POSTS_F, {}), load(NEEDS_F, {})
    if '--analyze-only' in sys.argv:
        # 수집 없이 저장된 상태로 집계만 다시(분류 규칙을 고친 뒤 쓰기)
        latest, plist = analyze(posts, needs, load(LATEST_F, {}).get('site_status', {}), now)
        dump(LATEST_F, latest)
        write_report(latest, plist, now)
        rows = MP.money_analyze(sys.modules[__name__], posts, needs, now) if MP else []
        print('돈 신호', [(r[0], r[1]) for r in rows[:25]])
        n7 = latest['needs']['7d']
        print('니즈 키워드', [w for w, _, _ in n7['keywords'][:25]])
        print('창업', latest['startup']['keywords'][:20])
        return 0
    tok = Tok()
    sites = [s for s in SITES if not only or s['id'] in only]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=len(sites)) as ex:
        results = list(ex.map(lambda s: run_site(s, posts, now, bf), sites))
    site_stat = load(LATEST_F, {}).get('site_status', {}) if only else {}
    for r in results:
        site_stat[r['site']] = dict(ok=r['ok'], n=r['n'], cmt=len(r['detail']), err=r['err'])
        print(f"{r['site']:<14} {'OK ' if r['ok'] else 'ERR'} 목록 {r['n']:>4} 본문·댓글 {len(r['detail']):>4} {r['err'] or ''}")
    if not any(r['ok'] for r in results):
        print('모든 사이트 실패 - 저장하지 않음')
        return 1
    update(posts, needs, results, tok, now)
    latest, plist = analyze(posts, needs, site_stat, now)
    dump(POSTS_F, posts)
    dump(NEEDS_F, needs)
    dump(LATEST_F, latest)
    write_report(latest, plist, now)
    rows = MP.money_analyze(sys.modules[__name__], posts, needs, now) if MP else []
    print('돈 신호', [(r[0], r[1]) for r in rows[:20]])
    n7 = latest['needs']['7d']
    print(f"보관 글 {len(posts)} | 7일 니즈 문장 {n7['sentences']} | {time.time() - t0:.0f}초")
    print('니즈 키워드', [w for w, _, _ in n7['keywords'][:20]])
    print('창업', latest['startup']['keywords'][:15])
    return 0


if __name__ == '__main__':
    sys.exit(main())
