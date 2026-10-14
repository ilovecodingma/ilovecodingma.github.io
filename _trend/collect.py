"""커뮤니티 인기글 수집·키워드 분석기.

실행할 때마다 각 커뮤니티 인기 목록을 읽고, 정적 댓글 사이트는 본문 댓글도 받아
키워드를 센 뒤 trend/data/*.json 을 갱신한다. 댓글 원문은 저장하지 않는다.
"""
import json, os, re, sys, time, collections
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'trend', 'data')
POSTS_F = os.path.join(DATA, 'posts.json')
HOURLY_F = os.path.join(DATA, 'hourly.json')
LATEST_F = os.path.join(DATA, 'latest.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36',
      'Accept-Language': 'ko-KR,ko;q=0.9'}

# key: 글 고유번호를 뽑는 정규식(그룹을 이어 붙여 키로 씀). cmt: 정적 HTML 댓글 선택자.
SITES = [
    dict(id='pann', name='네이트판', url='https://pann.nate.com/talk/ranking', key=r'/talk/(\d+)$', sel='div.mainarea div.cntList a', cmt='dl.cmt_item dd.usertxt'),
    dict(id='clien', name='클리앙', url='https://www.clien.net/service/group/clien_all?&od=T33', key=r'/service/board/(\w+)/(\d+)', sel='div.list_item.symph_row a.list_subject', cmt='div.comment_row div.comment_view'),
    dict(id='theqoo', name='더쿠', url='https://theqoo.net/hot', key=r'/hot/(\d+)', sel='table.theqoo_board_table tr:not(.notice) td.title a:not(.replyNum)'),
    dict(id='instiz', name='인스티즈', url='https://www.instiz.net/pt?srt=3', key=r'/pt/(\d+)', sel='td.listsubject a', tail_num=True, cmt='td.comment_memo span[id^=n]'),
    dict(id='bobae', name='보배드림', url='https://www.bobaedream.co.kr/list?code=best', key=r'code=best.*No=(\d+)', sel='table#boardlist a.bsubject', cmt='div.commentlistbox dd[id^=bepl_small_cmt]'),
    dict(id='ruliweb', name='루리웹', url='https://bbs.ruliweb.com/best/all/now', key=r'/read/(\d+)', sel='table.board_list_table tr.table_body:not(.notice) td.subject a.subject_link'),
    dict(id='dc', name='디시인사이드', url='https://gall.dcinside.com/board/lists/?id=dcbest', key=r'id=dcbest&no=(\d+)', sel='section.left_content tr.us-post td.gall_tit a:not(.reply_numbox)'),
    dict(id='mlbpark', name='MLB파크', url='https://mlbpark.donga.com/mp/b.php?b=bullpen&m=bbs&p=1&order=hit', key=r'b=bullpen.*id=(\d+)', sel='li.items div.title a', cmt='span.re_txt'),
    dict(id='todayhumor', name='오늘의유머', url='https://www.todayhumor.co.kr/board/list.php?table=bestofbest', key=r'table=bestofbest.*no=(\d+)', sel='table.table_list td.subject a'),
    dict(id='slr', name='SLR클럽', url='https://www.slrclub.com/bbs/zboard.php?id=best_article', key=r'id=best_article.*no=(\d+)', sel='td.sbj a'),
    dict(id='cook82', name='82쿡', url='https://www.82cook.com/entiz/enti.php?bn=15', key=r'num=(\d+)', sel='div#list_table tr:not(.noticeList) td.title a', cmt='ul.reples li p'),
    dict(id='dogdrip', name='개드립', url='https://www.dogdrip.net/dogdrip?sort_index=popular', key=r'/dogdrip/(\d+)', sel='a.title-link', cmt='div.comment-content .xe_content'),
    dict(id='arca', name='아카라이브', url='https://arca.live/b/live', key=r'/b/live/(\d+)', sel='div.list-table a.title.hybrid-title', cmt='div.comment-item div.message div.text'),
]
SITE_NAME = {s['id']: s['name'] for s in SITES}

KEEP_HOURS = 72           # 글 메타 보관 기간
HOURLY_KEEP_DAYS = 30     # 시간별 키워드 집계 보관 기간
CMT_PER_SITE = 15         # 한 번 실행에 사이트당 받을 본문 수
CMT_REFRESH_MIN = 60      # 댓글 재수집 간격
CMT_REFRESH_AGE_H = 24    # 처음 본 뒤 이 시간까지만 댓글 재수집
WINDOWS = [1, 6, 24, 72]

STOP = set('''
진짜 정말 사람 오늘 생각 이거 그거 저거 지금 정도 하나 사진 얘기 이유 경우 우리 자기 이번 시간 때문 이상 근데 그냥 그래서
그런데 게시물 게시글 댓글 추천 반대 비추 펼쳐보기 이미지 동영상 영상 베스트 링크 출처 기사 내용 본문 제목 글쓴이 작성자
자체 부분 느낌 수준 요즘 최근 하루 이제 다음 이후 처음 마지막 진심 레전드 근황 상황 모습 의미 결과 이야기 대박 실화
가지 사실 자신 누구 무엇 어디 언제 거기 여기 저기 이것 그것 저것 뭔가 같은 모두 다른 무슨 이런 그런 저런 제일 가장
인증 공지 이용 규칙 운영 회원 유머 개드립 더쿠 인스티즈 루리웹 클리앙 보배 네이트 디시 아카 오유 엠팍 펌글
경험 상태 일반 방법 문제 이건 그게 뭐가 정말로 완전 계속 그동안 무조건 바로 혹시 아마 역시 별로 자꾸
JPG GIF PNG MP4 조회 댓글수정 수정 삭제 가능 소리 짤방 스압 브금 ㄷㄷ ㅋㅋ ㅎㄷㄷ 싱갤 펌 분들 형님 님들 원글 본인 상대 개인 사용 발생 관련 대한 대해 위해 통해 동안 사이 정보 내외 전체 기준
'''.split())

NEED_RX = [
    ('추천 요청', r'추천|골라|뭐 ?살까|뭐가 ?(좋|나)|어떤 ?게'),
    ('방법 질문', r'어떻게|방법|하는 ?법|알려|가능한가|가능할까|되나요|있나요|어디서|어디에'),
    ('고민·상담', r'고민|조언|할까요|해야 ?(하나|할까|되나)|어쩌죠|어떡|망설|후회'),
    ('비교', r'비교|\bvs\b|VS|차이|어느 ?쪽'),
    ('가격·비용', r'얼마(?!나)|가격|비용|가성비|최저가'),
]


def now_kst():
    return datetime.now(KST).replace(microsecond=0)


def hour_key(dt):
    return dt.strftime('%Y%m%d%H')


def load(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def dump(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    m = re.search(r'charset=([\w-]+)', r.headers.get('content-type', ''), re.I)
    return BeautifulSoup(r.content, 'html.parser', from_encoding=m.group(1) if m else None)


def clean_title(t, tail_num=False):
    t = ' '.join(t.split())
    t = re.sub(r'^\d{1,3}\s+', '', t)                       # 앞 순위 숫자
    t = re.sub(r'^(모공|새로운소식|사진|아무거나|알뜰구매|팁과강좌)\s+', '', t)  # 클리앙 말머리
    t = re.sub(r'^\[\S{1,6}갤\]\s*', '', t)                # 디시 갤러리 말머리
    t = re.sub(r'\s*[\(\[]\d{1,5}[\)\]]\s*$', '', t)        # 뒤 댓글 수
    if tail_num:
        t = re.sub(r'\s+\d{1,5}$', '', t)                   # 괄호 없는 댓글 수(인스티즈)
    return t.strip()


def bad_title(t):
    if len(t) < 4 or len(t) > 150:
        return True
    if re.fullmatch(r'[\d\s\(\)\[\],.]+', t):
        return True
    return bool(re.search(r'^(공지|\[공지\])|이용\s?(규칙|안내)|운영\s?원칙|필독', t))


def collect_list(site):
    soup = fetch(site['url'])
    rx = re.compile(site['key'])
    found = {}
    for a in soup.select(site['sel']):
        href = (a.get('href') or '').split('#')[0]
        m = rx.search(href)
        if not m:
            continue
        key = site['id'] + ':' + '_'.join(m.groups())
        t = clean_title(a.get_text(' ', strip=True), site.get('tail_num'))
        if bad_title(t):
            found.setdefault(key, None)
            continue
        cur = found.get(key)
        if not cur or len(t) > len(cur[0]):
            found[key] = (t, urljoin(site['url'], href))
    return [(k, v[0], v[1]) for k, v in found.items() if v]


def collect_comments(site, url):
    soup = fetch(url)
    for x in soup.select('span.name_re'):
        x.decompose()
    seen, out = set(), []
    for e in soup.select(site['cmt']):
        t = ' '.join(e.get_text(' ', strip=True).split())
        t = re.sub(r'펼쳐보기▼?$|댓글수정|답글쓰기', '', t).strip()
        if len(t) < 2 or t in seen or re.fullmatch(r'(답글|추천|반대)\s*\d*', t):
            continue
        seen.add(t)
        out.append(t)
    return out


class Tok:
    def __init__(self):
        from kiwipiepy import Kiwi
        self.kiwi = Kiwi()

    def nouns(self, text):
        text = re.sub(r'\.?(jpe?g|gif|png|webp|mp4|avi)', ' ', text, flags=re.I)
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


def need_type(title):
    for name, rx in NEED_RX:
        if re.search(rx, title):
            return name
    if title.rstrip().endswith('?'):
        return '방법 질문'
    return None


def run_site(site, posts, now):
    """한 사이트를 수집한다. posts 는 읽기만 하고 변경분은 결과로 돌려준다."""
    res = dict(site=site['id'], ok=False, n=0, err=None, items=[], comments={})
    try:
        items = collect_list(site)
    except Exception as e:
        res['err'] = f'{type(e).__name__}: {str(e)[:120]}'
        return res
    res.update(items=items, n=len(items), ok=bool(items))
    if not items:
        res['err'] = '글 링크 0개(구조 변경 또는 차단 의심)'
    if not site.get('cmt'):
        return res
    cands = []
    for key, _, url in items:
        p = posts.get(key)
        if p is None or 'cf' not in p:
            cands.append((0, key, url))
            continue
        age = (now - datetime.fromisoformat(p['fs'])).total_seconds() / 3600
        since = (now - datetime.fromisoformat(p['cf'])).total_seconds() / 60
        if age <= CMT_REFRESH_AGE_H and since >= CMT_REFRESH_MIN:
            cands.append((1, key, url))
    cands.sort(key=lambda x: x[0])
    for _, key, url in cands[:CMT_PER_SITE]:
        try:
            time.sleep(0.6)
            res['comments'][key] = collect_comments(site, url)
        except Exception:
            pass
    return res


def update(posts, results, tok, now):
    hk, iso = hour_key(now), now.isoformat()
    for res in results:
        for rank, (key, title, url) in enumerate(res['items'], 1):
            p = posts.get(key)
            if p is None:
                p = posts[key] = dict(s=res['site'], t=title, u=url, fs=iso, br=rank, h=[])
            if p.get('t') != title or 'tk' not in p:
                p['t'] = title
            p['tk'] = sorted(set(tok.nouns(title)))
            p['nd'] = need_type(title)
            p['ls'], p['r'] = iso, rank
            p['br'] = min(p.get('br', rank), rank)
            if hk not in p['h']:
                p['h'].append(hk)
        for key, cmts in res['comments'].items():
            p = posts.get(key)
            if p is None:
                continue
            c = collections.Counter()
            for t in cmts:
                c.update(set(tok.nouns(t)))   # 댓글 하나에서 같은 낱말은 1회만 센다
            p['nc'], p['ck'], p['cf'] = len(cmts), dict(c.most_common(40)), iso
    cut = now - timedelta(hours=KEEP_HOURS)
    for key in [k for k, p in posts.items() if datetime.fromisoformat(p['ls']) < cut]:
        del posts[key]


def post_kws(p):
    """글 하나가 '언급'한 키워드: 제목 낱말 + 댓글 2개 이상에서 나온 낱말."""
    s = set(p.get('tk', []))
    s.update(k for k, v in p.get('ck', {}).items() if v >= 2)
    return s - STOP


def analyze(posts, site_stat, now, hourly):
    def hours_back(n):
        return {hour_key(now - timedelta(hours=i)) for i in range(n)}

    def active(p, hs):
        return any(h in hs for h in p['h'])

    plist = list(posts.items())
    kws_of = {k: post_kws(p) for k, p in plist}
    top = lambda c, n=50: [[k, v] for k, v in c.most_common(n)]

    windows = {}
    for w in WINDOWS:
        hs = hours_back(w)
        act = [(k, p) for k, p in plist if active(p, hs)]
        mention, title_c, cmt_c = collections.Counter(), collections.Counter(), collections.Counter()
        per_site, site_posts = collections.defaultdict(collections.Counter), collections.Counter()
        for k, p in act:
            mention.update(kws_of[k])
            title_c.update(set(p.get('tk', [])))
            cmt_c.update({w: v for w, v in p.get('ck', {}).items() if w not in STOP})
            per_site[p['s']].update(kws_of[k])
            site_posts[p['s']] += 1
        windows[str(w)] = dict(
            posts=len(act), mention=top(mention), title=top(title_c), comment=top(cmt_c),
            sites={s: dict(posts=site_posts[s], top=top(per_site[s], 12)) for s in site_posts},
        )

    # 급상승: 최근 3시간 언급 글 수 vs 그 앞 6시간의 3시간당 평균
    cur_h, prev_h = hours_back(3), hours_back(9) - hours_back(3)
    cur, prev = collections.Counter(), collections.Counter()
    for k, p in plist:
        if active(p, cur_h):
            cur.update(kws_of[k])
        if active(p, prev_h):
            prev.update(kws_of[k])
    rising = []
    if sum(prev.values()):
        for k, v in cur.items():
            pv = prev[k] / 2
            if v >= 3 and v > pv:
                rising.append([k, v, round(pv, 1), round((v + 1) / (pv + 1), 2)])
        rising.sort(key=lambda x: (-x[3], -x[1]))
        rising = rising[:20]

    # 시간별 키워드 글 수(보관 중인 72시간 버킷은 매번 다시 계산)
    by_hour = collections.defaultdict(collections.Counter)
    for k, p in plist:
        for h in p['h']:
            by_hour[h].update(kws_of[k])
    for h, c in by_hour.items():
        hourly[h] = dict(c.most_common(150))
    cutoff = hour_key(now - timedelta(days=HOURLY_KEEP_DAYS))
    for h in [h for h in hourly if h < cutoff]:
        del hourly[h]

    # 키워드 상세: 시간 추이·커뮤니티 분포·관련 글·함께 나온 키워드
    hours72 = [hour_key(now - timedelta(hours=i)) for i in range(71, -1, -1)]
    focus = [k for w in ('1', '6', '24', '72') for k, _ in windows[w]['mention'][:40]]
    focus += [k for w in ('6', '24') for k, _ in windows[w]['title'][:30] + windows[w]['comment'][:30]]
    focus = list(dict.fromkeys(focus + [r[0] for r in rising]))
    post_ref, refs = {}, []

    def ref(key):
        if key not in post_ref:
            p = posts[key]
            post_ref[key] = len(refs)
            refs.append([p['s'], p['t'], p['u'], p['ls'][5:16].replace('T', ' '), p.get('nc', 0), p.get('br', 0)])
        return post_ref[key]

    kw_posts = collections.defaultdict(list)
    for k, p in plist:
        for w in kws_of[k]:
            kw_posts[w].append(k)
    detail = {}
    for w in focus:
        keys = sorted(kw_posts.get(w, []), key=lambda x: posts[x]['ls'], reverse=True)
        co = collections.Counter()
        for key in keys:
            co.update(kws_of[key] - {w})
        detail[w] = dict(
            series=[hourly.get(h, {}).get(w, 0) for h in hours72],
            sites=dict(collections.Counter(posts[x]['s'] for x in keys)),
            posts=[ref(x) for x in keys[:15]],
            co=top(co, 8),
        )

    # 니즈 글(24시간)
    hs24 = hours_back(24)
    needs = sorted([(k, p) for k, p in plist if p.get('nd') and active(p, hs24)], key=lambda kp: kp[1]['ls'], reverse=True)
    need_kw, need_type_c = collections.Counter(), collections.Counter()
    for _, p in needs:
        need_kw.update(set(p.get('tk', [])))
        need_type_c[p['nd']] += 1
    need_out = dict(count=len(needs), types=need_type_c.most_common(), keywords=top(need_kw, 30),
                    posts=[[p['nd'], ref(k)] for k, p in needs[:80]])

    return dict(
        updated=now.isoformat(), hours=hours72, sites=SITE_NAME, site_status=site_stat,
        windows=windows, rising=rising, detail=detail, needs=need_out, posts=refs,
        summary=make_summary(windows, rising, need_out, site_stat),
    )


def josa(word, a, b):
    """받침 여부로 조사를 고른다(은/는, 이/가 등). 한글이 아니면 b."""
    ch = word[-1]
    if '가' <= ch <= '힣':
        return a if (ord(ch) - 0xAC00) % 28 else b
    return b


def make_summary(windows, rising, needs, site_stat):
    w = windows['24']
    ok = sum(1 for s in site_stat.values() if s['ok'])
    lines = []
    top5 = [k for k, _ in w['mention'][:5]]
    if top5:
        lines.append(f"지난 24시간 동안 {ok}개 커뮤니티의 인기글 {w['posts']:,}건을 분석했습니다. "
                     f"가장 많이 언급된 키워드는 {', '.join(top5)}입니다.")
    if rising:
        lines.append(f"최근 3시간 사이 언급이 빠르게 늘어난 키워드는 {', '.join(r[0] for r in rising[:5])}입니다.")
    parts = []
    for s, v in sorted(w['sites'].items(), key=lambda x: -x[1]['posts'])[:6]:
        ks = [k for k, _ in v['top'][:3]]
        if ks:
            n = SITE_NAME[s]
            parts.append(f"{n}{josa(n, '은', '는')} {'·'.join(ks)}")
    if parts:
        lines.append('커뮤니티별로 보면 ' + ', '.join(parts) + ' 이야기가 많았습니다.')
    if needs['count']:
        nk = [k for k, _ in needs['keywords'][:5]]
        lines.append(f"추천·방법·고민을 묻는 글은 {needs['count']}건이었고, 주로 {', '.join(nk)}에 관한 질문이었습니다.")
    return lines


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(DATA, exist_ok=True)
    now = now_kst()
    if '--if-stale' in sys.argv:
        # 예비 실행: 집 PC 수집이 멈춰 데이터가 오래됐을 때만 돈다(해외 IP는 일부 사이트가 막힘)
        limit = int(sys.argv[sys.argv.index('--if-stale') + 1])
        upd = load(LATEST_F, {}).get('updated')
        if upd and (now - datetime.fromisoformat(upd)).total_seconds() < limit * 60:
            print(f'최근 갱신 {upd} - {limit}분 이내라 건너뜀')
            return 0
    posts = load(POSTS_F, {})
    hourly = load(HOURLY_F, {})
    tok = Tok()
    with ThreadPoolExecutor(max_workers=7) as ex:
        results = list(ex.map(lambda s: run_site(s, posts, now), SITES))
    site_stat = {}
    for r in results:
        site_stat[r['site']] = dict(ok=r['ok'], n=r['n'], cmt=len(r['comments']), err=r['err'])
        print(f"{r['site']:<11} {'OK ' if r['ok'] else 'ERR'} 목록 {r['n']:>3} 댓글수집 {len(r['comments']):>3} {r['err'] or ''}")
    if not any(r['ok'] for r in results):
        print('모든 사이트 실패 - 저장하지 않음')
        return 1
    update(posts, results, tok, now)
    latest = analyze(posts, site_stat, now, hourly)
    dump(POSTS_F, posts)
    dump(HOURLY_F, hourly)
    dump(LATEST_F, latest)
    print('보관 글', len(posts), '| 24h 상위', latest['windows']['24']['mention'][:20])
    return 0


if __name__ == '__main__':
    sys.exit(main())
