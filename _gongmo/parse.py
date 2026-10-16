#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공모왕 data.json 생성 + commit/push.
사용: python gongmo_build.py [--no-push]
master.jsonl + collect/q/txt/<id>.txt 에서 gongmo/data.json 을 다시 만들고 git pull --rebase, commit, push 한다.
"""
import json, os, re, sys, html, subprocess, datetime, urllib.parse as up

SCR = os.path.dirname(os.path.abspath(__file__))
Q = os.path.join(SCR, 'collect', 'q')
MASTER = os.path.join(Q, 'master.jsonl')
REPO = r'C:\Users\k\Desktop\adsense_sites\root'
OUT = os.path.join(REPO, 'gongmo', 'data.json')
TODAY = datetime.date.today()
KINDS = ('contest', 'writing', 'idea', 'hackathon')
AGG = ('contestkorea.com', 'wevity.com', 'all-con.co.kr', 'thinkyou.co.kr', 'linkareer.com')
DATE = r'(\d{2,4})[-.](\d{1,2})[-.](\d{1,2})'


def clean(s):
    s = html.unescape(html.unescape(s or ''))
    s = s.replace('\ufeff', '').replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def to_date(y, m, d):
    y = int(y)
    if y < 100:
        y += 2000
    try:
        return datetime.date(y, int(m), int(d))
    except ValueError:
        return None


def amount_won(s):
    """'1,300만원' '3천만원' '1억 2천만원' '100만 원' -> 원. 못 읽으면 None"""
    s = s.replace(',', '').replace(' ', '')
    m = re.fullmatch(r'(?:(\d+(?:\.\d+)?)억)?(?:(\d+)천만)?(?:(\d+(?:\.\d+)?)백만)?(?:(\d+(?:\.\d+)?)만)?(?:(\d+))?원?', s)
    if not m or not any(m.groups()):
        return None
    eok, chm, bm, man, won = m.groups()
    v = 0
    if eok: v += float(eok) * 1e8
    if chm: v += int(chm) * 1e7
    if bm: v += float(bm) * 1e6
    if man: v += float(man) * 1e4
    if won: v += int(won)
    return int(v)


AMT = r'((?:\d[\d,\.]*\s*억\s*)?(?:\d[\d,]*\s*천\s*만\s*)?(?:\d[\d,\.]*\s*백\s*만\s*)?(?:\d[\d,\.]*\s*만\s*)?(?:\d[\d,]*)?\s*원)'
AMT_RE = re.compile(AMT)


def fmt_amt(txt):
    return re.sub(r'\s+', '', txt)


def find_amount_after(label_re, text, span=24):
    for m in re.finditer(label_re, text):
        seg = text[m.end(): m.end() + span]
        seg = re.sub(r'\([^)]*\)', ' ', seg)  # (1명) 같은 괄호 제거
        a = re.search(r'(\d[\d,\.]*\s*(?:억\s*)?(?:\d[\d,]*\s*천\s*)?(?:\d[\d,]*\s*백\s*)?(?:\d[\d,\.]*\s*)?[천백]?만\s*원|\d[\d,]{4,}\s*원)', seg)
        if a:
            w = amount_won(a.group(1))
            if w and 10000 <= w < 5_000_000_000:
                return fmt_amt(a.group(1)), w
    return None, None


def parse_prize(src, t, body):
    """(표시문구, 정렬값). 확실치 않으면 ('공고 참조', 0)"""
    total = first = None
    tw = fw = 0
    if src == 'wevity':
        m = re.search(r'1등 상금\s*(.*?)\s*홈페이지', t)
        if m and m.group(1).strip():
            a = AMT_RE.search(m.group(1))
            if a and amount_won(a.group(1)):
                first, fw = fmt_amt(a.group(1)), amount_won(a.group(1))
    if src == 'linkareer':
        m = re.search(r'시상규모\s*([\d,\.]+\s*(?:억|천만|백만|만)?\s*원?)', t)
        if m:
            s = m.group(1).strip()
            if not s.endswith('원'):
                s += '원'
            w = amount_won(s)
            if w and w < 5e9:
                total, tw = fmt_amt(s), w
    if src == 'contestkorea':
        m = re.search(r'시상내역\s*(.{0,120}?)(?:홈페이지|접수방법)', t)
        if m:
            seg = m.group(1)
            total, tw = find_amount_after(r'총\s*상금\s*[:：]?\s*', seg, 20)
            first, fw = find_amount_after(r'1위\s*[:：]?\s*', seg, 14)
            if total is None:
                total, tw = None, 0
    # 본문
    if total is None:
        total, tw = find_amount_after(r'총\s*(?:상금|시상금|시상\s*규모|상금\s*규모)\s*(?:[:：은]|약)?\s*', body, 22)
        if total is None:
            total, tw = find_amount_after(r'상금\s*총액\s*[:：]?\s*', body, 22)
    if first is None:
        first, fw = find_amount_after(r'(?:1등|1위|대상|최우수상?|금상|그랑프리|Grand Prize)\s*(?:\(\d+\s*[명점팀편]\))?\s*[:：]?\s*(?:\d+\s*[명점팀편])?\s*[,:/·-]?\s*(?:상금)?\s*', body, 26)
    tw, fw = tw or 0, fw or 0
    if total and first and fw > tw:  # 모순 (1등이 총상금보다 큼)
        total, tw = None, 0
    parts = []
    if first:
        parts.append('1등 ' + first)
    if total:
        parts.append('총상금 ' + total)
    if not parts:
        return '공고 참조', 0
    return ' · '.join(parts), max(tw, fw)


def field_after(t, label, stops):
    m = re.search(label + r'\s+(.*?)\s+(?:' + '|'.join(stops) + ')', t)
    return clean(m.group(1)) if m else ''


def parse_dates(src, t):
    s = e = None
    if src in ('wevity', 'thinkyou', 'contestkorea'):
        m = re.search(r'접수기간\s*' + DATE + r'\s*[~∼-]+\s*' + DATE, t)
        if m:
            g = m.groups()
            s, e = to_date(*g[:3]), to_date(*g[3:])
    elif src == 'all-con':
        m = re.search(r'접수기간\s*' + DATE + r'\s*[~∼-]+\s*' + DATE, t)
        if m:
            g = m.groups()
            s, e = to_date(*g[:3]), to_date(*g[3:])
    elif src == 'linkareer':
        m = re.search(r'시작일\s*' + DATE + r'\s*마감일\s*' + DATE, t)
        if m:
            g = m.groups()
            s, e = to_date(*g[:3]), to_date(*g[3:])
    return s, e


def parse_eligibility(src, t, body):
    m = re.search(r'(?:응모자격|참가자격|참여자격|지원자격|공모자격|응모대상|참여대상|참가대상|모집대상|지원대상)\s*[:：]?\s*(.{4,70}?)(?=\s*(?:■|○|▶|◆|●|※|□|\s-\s|\d\.\s|접수|기간|공모|문의|시상|$))', body)
    el = clean(m.group(1)) if m else ''
    el = re.sub(r'^[\-\s:·]+', '', el)
    if len(el) < 3 or re.search(r'^\W*$', el):
        el = ''
    if not el:
        if src == 'wevity':
            el = field_after(t, '응모대상', ['주최/주관'])
        elif src == 'contestkorea':
            el = field_after(t, '참가대상', ['접수기간'])
            el = re.sub(r'\s*,\s*', ', ', el)
        elif src == 'all-con':
            el = field_after(t, '응모대상', ['시상내역', '혜택'])
        elif src == 'linkareer':
            el = field_after(t, '참여대상', ['시상규모', '접수기간'])
    el = re.sub(r'^[\W_]+', '', el.strip(' ,;'))
    if el in ('기타', '전체'):
        el = ''
    el = el.replace('제한없음', '제한 없음').replace('해당자 ▶ ', '')
    if len(el) > 60:
        el = el[:58].rstrip() + '…'
    return el or '공고 참조'


def parse_field(src, t, x):
    if src == 'wevity':
        return field_after(t, r'분야', ['응모대상'])
    if src == 'contestkorea':
        return field_after(t, '대표분야', ['참가대상'])
    if src == 'thinkyou':
        return field_after(t, '응모분야', ['홈페이지'])
    if src == 'all-con':
        return field_after(t, r'분야', ['응모대상', '시상내역'])
    if src == 'linkareer':
        return field_after(t, '공모분야', ['추가혜택', '공유하기'])
    return ''


def parse_org(src, t, x):
    o = ''
    if src == 'wevity':
        o = field_after(t, '주최/주관', ['후원/협찬', '접수기간'])
    elif src == 'contestkorea':
        o = field_after(t, r'주최 \. 주관', ['대표분야'])
    elif src == 'thinkyou':
        o = field_after(t, r'주최', ['접수기간'])
    elif src == 'all-con':
        o = field_after(t, r'주최', ['주관', '접수기간'])
    o = o or clean(x.get('org', ''))
    if o in ('-', ''):
        o = '공고 참조'
    return o[:50]


TAGS = [
    ('문학', r'문학|시나리오|수필|소설|백일장|에세이|글쓰기|(?<!자)동화|시 공모|수기|웹소설|네이밍|슬로건|詩|短歌|俳句|手紙|エッセイ|小説|文学'),
    ('아이디어·정책', r'아이디어|기획|정책|제안|사례|창업|마케팅|광고|비즈니스|アイデア'),
    ('디자인', r'디자인|캐릭터|웹툰|미술|그림|포스터|건축|일러스트|공예|デザイン|イラスト|ロゴ|design'),
    ('영상', r'영상|UCC|사진|숏폼|영화|촬영|릴스|映像|動画|写真|フォト|video'),
    ('논문', r'논문|리포트|학술|paper'),
    ('IT·과학', r'(?<![A-Za-z])IT(?![A-Za-z])|소프트웨어|게임|과학|공학|해커톤|(?<![A-Za-z])AI(?![A-Za-z])|코딩|데이터|hack|Hack|プログラム'),
]
CATS = ['문학', '아이디어·정책', '디자인', '영상', '논문', 'IT·과학', '해외', '기타']

NONCONTEST = re.compile(r'recruitment|Recruitment|걷기|트레킹|마라톤|러닝크루|참가자 모집|봉사단|오디션|세미나|설명회|서포터즈|기자단|교육생|강좌|강연|포럼|채용|워크숍|체험단|멘토링|인턴|발대식|토크콘서트|박람회 참가|지식향연|참가자 모집 공고')
CONTESTY = re.compile(r'공모|콩쿠르|응모|수기|선발대회|페스티벌|페스타|챌린지|아카데미 어워드|경진|콘테스트|콘텐스트|어워드|대회|contest|Contest|hack|Hack|Award|award|Challenge|챌린지|コンテスト|コンペ|募集|賞|公募')


def tags_for(field, title, reg):
    s = field + ' ' + title
    out = [n for n, rx in TAGS if re.search(rx, s)]
    if reg != 'KR':
        out.append('해외')
    return out or ['기타']


def source_of(url):
    h = up.urlparse(url).netloc
    for k, n in (('wevity', 'wevity'), ('contestkorea', 'contestkorea'), ('all-con', 'all-con'),
                 ('thinkyou', 'thinkyou'), ('linkareer', 'linkareer')):
        if k in h:
            return n
    return 'other'


def norm_title(s):
    s = re.sub(r'\[[^\]]*\]|\([^)]*\)|【[^】]*】|[「」『』“”‘’\'"<>]', '', s)
    s = re.sub(r'20\d\d|제?\d+회|년도?', '', s)
    return re.sub(r'[^0-9A-Za-z가-힣ぁ-んァ-ヶ一-龥]', '', s).lower()


def main():
    push = '--no-push' not in sys.argv
    rows = [json.loads(l) for l in open(MASTER, encoding='utf-8') if l.strip()]
    items = {}
    stat = {'src': len(rows), 'past': 0, 'noncontest': 0, 'dup': 0}
    for x in rows:
        if x.get('closed'):  # 공모전 세션이 조기 종료로 표시
            continue
        if x.get('verified') is False:  # 개인 블로그 등 미확인 출처는 사이트에 안 올림
            continue
        if x.get('end_override'):  # 마감 연장 등 공모전 세션 확인값 우선
            x['end'] = x['end_override']
        if x.get('kind') not in KINDS or x.get('end', '') < TODAY.isoformat():
            continue
        title = clean(x['title'])
        title = re.sub(r'\s*\d{4}\.\d{2}\.\d{2}\.?\s*$', '', title)
        title = re.sub(r'\s*(새글|마감임박)\s*$', '', title).strip()
        if title in ('', 'N/A'):
            continue
        src = source_of(x['url'])
        tp = os.path.join(Q, 'txt', x['id'] + '.txt')
        t = clean(open(tp, encoding='utf-8', errors='ignore').read()) if os.path.exists(tp) else ''
        anchor = {'wevity': '조회수 :', 'contestkorea': '주최 . 주관', 'thinkyou': '조회수', 'all-con': '공모전/대외활동 정보', 'linkareer': '기업형태'}.get(src)
        ai = t.find(anchor, 150) if anchor else -1
        core = t[ai:] if ai >= 0 else t
        if src == 'contestkorea':
            bi = core.find('SNS공유')
            body = core[bi:] if bi >= 0 else core
        else:
            bi = core.find('상세내용')
            body = core[bi + 4:] if bi >= 0 else core
        body = re.sub(r'\s+', ' ', body.replace('~', ' ~ '))
        # all-con 은 공모전 카테고리만
        if src == 'all-con' and not re.search(r'(대학생·일반인|청소년)\s*공모전', t[:900]):
            stat['noncontest'] += 1
            continue
        if NONCONTEST.search(title) and not re.search(r'공모전|경진대회|콘테스트', title):
            stat['noncontest'] += 1
            continue
        s, e = parse_dates(src, t)
        if x.get('end_override'):
            e = datetime.date.fromisoformat(x['end_override'])
        fld0 = parse_field(src, core, x) if t else ''
        if not CONTESTY.search(title) or (re.search(r'봉사|교육|동아리|서포터즈|채용|인턴|대외활동', fld0) and not re.search(r'공모전|경진|콘테스트|콩쿠르', title)):
            if not (x['reg'] != 'KR' and x['kind'] in ('hackathon', 'contest')):
                stat['noncontest'] += 1
                continue
        unreliable_end = src in ('contestkorea', 'all-con', 'wevity', 'thinkyou', 'linkareer') or x['reg'] == 'KR'
        if e is None:
            if unreliable_end and src != 'other':
                continue  # 접수기간 못 읽으면 심사일일 수 있어 제외
            e = datetime.date.fromisoformat(x['end'])
        if e < TODAY:
            stat['past'] += 1
            continue
        prize, pv = parse_prize(src, core, body) if t else ('공고 참조', 0)
        field = parse_field(src, core, x) if t else ''
        elig = parse_eligibility(src, core, body) if t else '공고 참조'
        org = parse_org(src, core, x)
        link = x.get('apply') or ''
        if src == 'wevity':
            m = re.search(r'홈페이지\s+(https?://\S+)', core)
            link = m.group(1) if m else ''
        if not link.startswith('http') or 'bannerhit' in link or (src != 'wevity' and any(a in link for a in AGG) and False):
            link = ''
        if not link:
            link = x['url']
        if src == 'all-con' or any(a in up.urlparse(link).netloc for a in ('all-con',)):
            link = x['url']
        d = {
            'id': x['id'], 'title': title[:90], 'org': org, 'start': s.isoformat() if s else '',
            'end': e.isoformat(), 'prize': prize, 'pv': pv, 'elig': elig,
            'field': (field or '')[:30],
            'tags': tags_for(field, title, x['reg']), 'link': link,
        }
        key = norm_title(title)
        if key in items:
            stat['dup'] += 1
            old = items[key]
            if (old['pv'] > 0) >= (d['pv'] > 0):
                continue
        items[key] = d
    out = sorted(items.values(), key=lambda d: (d['end'], d['title']))
    data = {'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'today': TODAY.isoformat(),
            'count': len(out), 'items': [{k: v for k, v in d.items()} for d in out]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print('items', len(out), stat)
    if not push:
        return

    def git(*a):
        r = subprocess.run(['git', '-C', REPO] + list(a), capture_output=True, text=True, encoding='utf-8')
        print('git', ' '.join(a), '->', r.returncode, (r.stdout + r.stderr).strip()[:300])
        return r
    git('pull', '--rebase', '--autostash')
    git('add', 'gongmo')
    if git('diff', '--cached', '--quiet', '--', 'gongmo').returncode == 0:
        print('변경 없음')
        return
    msg = 'gongmo: update data %s (%d items)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' % (TODAY, len(out))
    git('commit', '-m', msg, '--', 'gongmo')
    r = git('push')
    if r.returncode != 0:
        git('pull', '--rebase', '--autostash')
        git('push')


if __name__ == '__main__':
    main()
