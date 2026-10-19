# -*- coding: utf-8 -*-
"""홍보 콘텐츠 후보 생성기 (2026-10-19 SEO·홍보 지침 Phase 2·6).
사이트 데이터(공모전·지원금·핫이슈·레시피·애널리스트)에서 채널별 문구를 '틀 + 실제 값'으로 만든다(숫자·날짜를 지어내지 않음).
만든 뒤 자동 검사(qc): 원문 값과 날짜·금액 일치, 마감 지남, 과장 표현, 지원 대상 누락, 길이, 14일 안 중복. 실패하면 DRAFT 에 사유를 남겨 승인 못 하게.
통과하면 REVIEW. 게시는 하지 않는다 — 관리자 화면에서 승인 → 예약 → 사람이 게시 후 「게시 완료」 처리.
결과는 D1 promo 테이블(push.q). 실행: python promo.py [am|pm|mon|all] [--dry] | sync   (build.py 가 하루 슬롯마다 1번 부른다)"""
import datetime, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SITE = 'https://sungprofile.cloud'
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST).replace(tzinfo=None)
TODAY = NOW.date()
CH = ['naver_blog', 'threads', 'x', 'instagram', 'shorts', 'community']
CH_NAME = {'naver_blog': '네이버 블로그', 'threads': '스레드', 'x': 'X', 'instagram': '인스타그램', 'shorts': '유튜브 쇼츠', 'community': '커뮤니티'}
HYPE = re.compile(r'무조건|100%|역대급|대박|충격|필수|꼭 받으세요|놓치면 손해|전원 지급|누구나 받는|무료로 돈|확정 수령')
DISC = '※ 제가 운영하는 정보 사이트(루리의 줍줍) 링크예요. 최종 내용은 공식 공고로 확인해 주세요.'
SCHEMA = """CREATE TABLE IF NOT EXISTS promo (id INTEGER PRIMARY KEY AUTOINCREMENT, tok TEXT UNIQUE, created INTEGER, day TEXT, slot TEXT, kind TEXT, ref TEXT, channel TEXT,
 title TEXT, body TEXT, link TEXT, src TEXT, status TEXT, qc TEXT, scheduled TEXT, published TEXT, post_url TEXT, note TEXT, updated INTEGER)"""


def rd(p):
    f = os.path.join(ROOT, p)
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}


def dd(end):
    return (datetime.date.fromisoformat(end) - TODAY).days


def md(end):
    return f'{int(end[5:7])}월 {int(end[8:10])}일'


def link(path, ch, kind, tok):
    return f'{SITE}{path}?src={tok}&utm_source={ch}&utm_medium=social&utm_campaign={kind}_{TODAY:%Y%m%d}'


def tok_of(kind, ref, ch):
    return 'p' + hashlib.md5(f'{kind}|{ref}|{ch}|{TODAY}'.encode()).hexdigest()[:9]


# ---------------- 채널별 문구 (fact: 검사에 쓸 원문 값 dict)
def contest_texts(c, ch, url):
    n = dd(c['end']); m = md(c['end'])
    prize = c['prize'] if c.get('pv') else ''
    elig = c.get('elig') or ''
    eff = c.get('effort') or ''
    tags = ' · '.join(c['tags'][:2])
    if ch == 'naver_blog':
        titles = [f'{c["title"]} — {m} 마감 · 응모 자격 정리', f'{tags} 공모전 {c["end"][:4]} | {c["title"][:30]}' + (f' 상금 {prize}' if prize else ''),
                  f'{m} 마감 공모전: {c["title"][:34]} 제출물·접수 방법']
        body = (f'[검색형 제목 후보]\n1. {titles[0]}\n2. {titles[1]}\n3. {titles[2]}\n\n[요약]\n{c.get("org") or "주최 기관"}에서 여는 {tags} 공모전 「{c["title"]}」이(가) {m}에 접수를 마감해요.'
                + (f' 상금은 {prize}이에요.' if prize else ' 상금은 공식 공고에서 확인이 필요해요.')
                + f'\n\n[주요 자격 조건]\n{elig or "공식 공고 확인 필요"}\n\n[마감일]\n{c["end"]} (마감 시각은 공식 공고 확인)\n\n[제출물]\n{eff or "공식 공고 확인 필요"}'
                + f'\n\n[공식 출처]\n주최: {c.get("org") or "공고 참조"} · 상세 페이지에 공식 공고 링크가 있어요.\n\n[사이트 링크]\n{url}\n\n[관련 키워드]\n{c["title"][:20]}, {tags} 공모전, {c["end"][:4]} 공모전, {m[:-3]} 마감 공모전')
        return titles[0], body
    if ch in ('threads', 'x'):
        lim = 280 if ch == 'x' else 480
        body = (f'⏰ {m} 마감 · {c["title"]}\n\n· 분야: {tags}\n· 자격: {elig[:40] or "공식 공고 확인"}\n· ' + (f'상금: {prize}' if prize else f'제출물: {eff or "공고 확인"}')
                + f'\n\n자격·제출물·공식 공고 링크 정리해 뒀어요 👇\n{url}')
        if len(body) > lim:
            body = f'⏰ {m} 마감 · {c["title"][:60]}\n· 자격: {elig[:30] or "공고 확인"}\n' + (f'· 상금: {prize}\n' if prize else '') + url
        return c['title'], body
    if ch == 'instagram':
        cards = [f'[1] {m} 마감\n{c["title"]}', f'[2] 누가 낼 수 있나요?\n{elig or "공식 공고 확인 필요"}', f'[3] 무엇을 내나요?\n{eff or "공식 공고 확인 필요"}',
                 f'[4] 상금·혜택\n{prize or "공식 공고 확인 필요"}', f'[5] 마감 {c["end"]}\n공식 공고 링크는 프로필 링크 → 루리의 줍줍']
        tagsh = ' '.join('#' + re.sub(r'\W', '', x) for x in [f'{c["tags"][0]}공모전', '공모전', f'{c["end"][:4]}공모전', '대외활동', '루리의줍줍'])
        body = '[카드뉴스 5장]\n' + '\n\n'.join(cards) + f'\n\n[게시글 설명]\n{c["title"]} {m} 마감. 자격·제출물 정리는 프로필 링크에서 확인하세요.\n{url}\n\n[해시태그]\n{tagsh}'
        return c['title'], body
    if ch == 'shorts':
        body = (f'[대본 25초]\n0~3초(후킹): "{m} 마감인데, 아직 모르는 사람 많은 공모전!"\n3~10초: 자막 「{c["title"][:30]}」\n10~18초: 자막 「자격: {elig[:24] or "공고 확인"}」'
                + (f'\n18~23초: 자막 「상금 {prize}」' if prize else f'\n18~23초: 자막 「제출물: {eff or "공고 확인"}」')
                + f'\n23~25초(행동 유도): "자세한 건 고정 댓글 링크, 루리의 줍줍에서 확인해요!"\n\n[고정 댓글]\n{url}')
        return c['title'], body
    if ch == 'community':
        body = (f'[제목] {m} 마감 {tags} 공모전 정리: {c["title"][:40]}\n\n[내용]\n· 주최: {c.get("org") or "공고 참조"}\n· 자격: {elig or "공식 공고 확인 필요"}\n· 제출물: {eff or "공식 공고 확인 필요"}\n· 상금: {prize or "공식 공고 확인 필요"}\n· 마감: {c["end"]}'
                + f'\n\n[출처] 주최 측 공식 공고(아래 정리 페이지에 링크)\n{url}\n\n{DISC}')
        return f'{m} 마감 {tags} 공모전 정리: {c["title"][:40]}', body


def apply_texts(a, ch, url):
    m = md(a['end']) if a.get('end') and not a.get('always') else '상시'
    tgt = (a.get('target') or '').strip(); ben = (a.get('benefit') or '').strip()
    org = a.get('org') or '공고 기관'
    base = {'naver_blog': None}
    if ch == 'naver_blog':
        titles = [f'{a["title"]} {TODAY.year} — 대상·신청기간 정리', f'{a.get("kind", "지원금")} | {a["title"][:30]} {m} 마감', f'{org} {a["title"][:30]} 신청 방법']
        body = (f'[검색형 제목 후보]\n1. {titles[0]}\n2. {titles[1]}\n3. {titles[2]}\n\n[요약]\n{org}의 「{a["title"]}」 신청 ' + (f'마감은 {m}이에요.' if m != '상시' else '은 상시예요.')
                + f'\n\n[지원 대상]\n{tgt or "공식 공고 확인 필요"}\n\n[지원 내용]\n{ben or "공식 공고 확인 필요"}\n\n[신청 기간]\n{(a.get("start") or "") + " ~ " + (a.get("end") or "상시")}\n\n[공식 출처]\n{org} 공고 · 상세 페이지에 신청처 링크\n\n[사이트 링크]\n{url}\n\n[관련 키워드]\n{a["title"][:20]}, {a.get("kind", "")}, 청년 지원금 {TODAY.year}')
        return titles[0], body
    if ch in ('threads', 'x'):
        body = f'💰 {a["title"]}\n· 대상: {tgt[:40] or "공고 확인"}\n· 내용: {ben[:40] or "공고 확인"}\n· 신청: ~{m}\n\n조건 정리 👇\n{url}'
        if ch == 'x' and len(body) > 280:
            body = f'💰 {a["title"][:60]} · ~{m}\n· 대상: {tgt[:30] or "공고 확인"}\n{url}'
        return a['title'], body
    if ch == 'instagram':
        cards = [f'[1] {a["title"]}', f'[2] 누가?\n{tgt or "공식 공고 확인 필요"}', f'[3] 무엇을?\n{ben or "공식 공고 확인 필요"}', f'[4] 언제까지?\n{m}', '[5] 신청처·조건은 프로필 링크 → 루리의 줍줍']
        body = '[카드뉴스 5장]\n' + '\n\n'.join(cards) + f'\n\n[게시글 설명]\n{a["title"]} 신청 {m}. 조건은 프로필 링크.\n{url}\n\n[해시태그]\n#지원금 #청년지원금 #{TODAY.year}지원금 #정부지원 #루리의줍줍'
        return a['title'], body
    if ch == 'shorts':
        body = (f'[대본 20초]\n0~3초(후킹): "이 지원금, {m}까지예요!"\n3~9초: 자막 「{a["title"][:30]}」\n9~15초: 자막 「대상: {tgt[:24] or "공고 확인"}」\n15~20초(행동 유도): "조건은 고정 댓글 링크에서 확인!"\n\n[고정 댓글]\n{url}')
        return a['title'], body
    if ch == 'community':
        body = f'[제목] {a["title"]} 신청 정리 ({m})\n\n· 대상: {tgt or "공식 공고 확인 필요"}\n· 내용: {ben or "공식 공고 확인 필요"}\n· 기관: {org}\n\n[출처] 기관 공식 공고(정리 페이지에 링크)\n{url}\n\n{DISC}'
        return f'{a["title"]} 신청 정리 ({m})', body


def weekly_texts(L, ch, url):
    head = f'{TODAY.month}/{TODAY.day} 주간 공모전: 이번 주 마감 {len(L)}건'
    lines = '\n'.join(f'· {md(c["end"])} {c["title"][:34]}' + (f' ({c["prize"]})' if c.get('pv') else '') for c in L[:5])
    if ch == 'naver_blog':
        return head, f'[검색형 제목 후보]\n1. 이번 주 마감 공모전 {TODAY.year} ({TODAY.month}/{TODAY.day}~)\n2. {TODAY.month}월 마감 공모전 모음\n3. 주간 공모전 정리 TOP5\n\n[요약]\n이번 주 마감 공모전 {len(L)}건 중 5건:\n{lines}\n\n[사이트 링크]\n{url}\n\n[관련 키워드]\n이번 주 마감 공모전, {TODAY.month}월 공모전, 공모전 {TODAY.year}'
    if ch in ('threads', 'x'):
        b = f'📅 {head}\n{lines}\n\n전체 👇\n{url}'
        return head, b if len(b) <= (280 if ch == 'x' else 480) else f'📅 {head}\n전체 목록 👇\n{url}'
    if ch == 'instagram':
        return head, '[카드뉴스 5장]\n' + '\n\n'.join(f'[{i + 1}] {md(c["end"])} 마감\n{c["title"]}' for i, c in enumerate(L[:5])) + f'\n\n[게시글 설명]\n{head}\n{url}\n\n[해시태그]\n#공모전 #이번주마감 #대외활동 #루리의줍줍'
    if ch == 'shorts':
        return head, f'[대본 30초]\n0~3초(후킹): "이번 주에 끝나는 공모전, {len(L)}개나 있어요!"\n' + '\n'.join(f'{3 + i * 5}~{8 + i * 5}초: 자막 「{md(c["end"])} {c["title"][:22]}」' for i, c in enumerate(L[:4])) + f'\n23~30초: "전체 목록은 고정 댓글!"\n\n[고정 댓글]\n{url}'
    if ch == 'community':
        return head, f'[제목] {head}\n\n{lines}\n\n[출처] 각 주최 측 공식 공고(정리 페이지에 링크)\n{url}\n\n{DISC}'


# ---------------- 자동 검사
def qc(kind, src, ch, title, body, recent):
    bad = []
    if HYPE.search(title + body):
        bad.append('과장 표현: ' + HYPE.search(title + body).group(0))
    lim = {'x': 280, 'threads': 500}.get(ch)
    if lim and len(body) > lim:
        bad.append(f'길이 {len(body)}자(제한 {lim}자)')
    if kind in ('contest', 'apply') and src.get('end') and not src.get('always'):
        if dd(src['end']) < 1:
            bad.append('마감이 오늘이거나 지남(오래된 정보)')
        if md(src['end']) not in body and src['end'] not in body:
            bad.append('마감일이 본문에 원문과 같게 들어가지 않음')
    if kind == 'contest':
        if src.get('pv') and src['prize'] not in body and ch not in ('x',):
            bad.append('상금이 원문 표기와 다름')
        if not src.get('elig'):
            bad.append('지원 대상(자격) 원문 없음 — 공고 확인 필요')
        for m in re.finditer(r'(\d{1,2})월 (\d{1,2})일', body):
            if f'{int(m.group(1)):02d}-{int(m.group(2)):02d}' != src['end'][5:]:
                bad.append(f'본문 날짜 {m.group(0)}가 마감일과 다름'); break
    if kind == 'apply' and not src.get('always') and (src.get('start') or '') > TODAY.isoformat():
        bad.append(f'신청 시작 전({src["start"]}) — 연도·기간 원문 확인 필요')
    if kind == 'apply' and not (src.get('target') or '').strip():
        bad.append('지원 대상 원문 없음 — 공고 확인 필요')
    key = (kind, str(src.get('id') or src.get('slug') or title), ch)
    if key in recent:
        bad.append('최근 14일 안에 같은 채널로 만든 적 있음(중복)')
    return bad


def candidates(slot):
    out = []
    C = rd('data.json').get('items', [])
    sys.path.insert(0, HERE)
    import build as B   # apply.json 에는 대상·혜택이 없어 원본 로더를 그대로 씀
    A = B.load_apply()
    if slot in ('am', 'all'):   # 매일 오전: 마감 임박 공모전 (D-2~D-7, 상금 큰 순 3건)
        L = sorted([c for c in C if 2 <= dd(c['end']) <= 7], key=lambda c: -(c.get('pv') or 0))[:3]
        out += [('contest', c, f'/c/{c["id"]}/') for c in L]
    if slot in ('pm', 'all'):   # 매일 오후: 새 지원금·청약 2건(최근 3일 시작, 마감 2일 이상 남음)
        L = [a for a in A if a.get('kind') != '공모주' and (a.get('target') or '').strip() and (a.get('always') or (a.get('end') and dd(a['end']) >= 2 and (a.get('start') or '') <= TODAY.isoformat()))]   # 공모주는 투자 권유가 될 수 있어 제외. 시작 전(연도 오파싱 의심 포함)은 제외
        L.sort(key=lambda a: (a.get('start') or '') , reverse=True)
        out += [('apply', a, f'/a/{a["id"]}/') for a in L[:2]]
    if slot in ('mon', 'all'):   # 매주 월요일: 주간 공모전 요약
        L = sorted([c for c in C if 0 <= dd(c['end']) <= 7], key=lambda c: (c['end'], -(c.get('pv') or 0)))
        if L:
            out.append(('weekly', {'id': f'week-{TODAY}', 'items': L}, '/contest/week/'))
    return out


def run(slot, dry=False):
    import push
    if not dry:
        push.q(SCHEMA)
    rec = set() if dry else {(r['kind'], r['ref'], r['channel']) for r in push.q('SELECT kind, ref, channel FROM promo WHERE day >= ?', [(TODAY - datetime.timedelta(days=14)).isoformat()])}
    made = []
    for kind, src, path in candidates(slot):
        ref = str(src.get('id'))
        for ch in CH:
            tok = tok_of(kind, ref, ch); url = link(path, ch, kind, tok)
            f = {'contest': contest_texts, 'apply': apply_texts, 'weekly': lambda s, c, u: weekly_texts(s['items'], c, u)}[kind]
            title, body = f(src, ch, url)
            bad = qc(kind, src, ch, title, body, rec)
            st = 'DRAFT' if bad else 'REVIEW'
            made.append((tok, kind, ref, ch, title, body, url, st, bad))
            if not dry:
                push.q('INSERT OR IGNORE INTO promo (tok, created, day, slot, kind, ref, channel, title, body, link, src, status, qc, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       [tok, int(NOW.timestamp()), TODAY.isoformat(), slot, kind, ref, ch, title[:200], body, url, path, st, json.dumps(bad, ensure_ascii=False), int(NOW.timestamp())])
            rec.add((kind, ref, ch))
    return made


REVIEW_F = os.path.join(HERE, 'promo_review.json'); DONE_F = os.path.join(HERE, 'promo_done.jsonl'); DONE_SEEN = os.path.join(HERE, 'promo_done_seen.json')


def sync():
    """홍보 세션 연동 (2026-10-19): ① promo_done.jsonl({tok, channel, post_url, time}) 을 D1 에 반영 — 승인·예약(APPROVED·SCHEDULED) 글만 PUBLISHED 로,
    승인 전 글은 상태를 바꾸지 않고 note 에만 남김(2중 승인 유지). ② 검토 대기~예약 목록을 promo_review.json 으로 내보냄. build.py 가 빌드마다 부른다."""
    import push
    seen = set(json.load(open(DONE_SEEN, encoding='utf-8'))) if os.path.exists(DONE_SEEN) else set()
    res = []
    if os.path.exists(DONE_F):
        for l in open(DONE_F, encoding='utf-8'):
            try:
                d = json.loads(l)
            except ValueError:
                continue
            k = f"{d.get('tok')}|{d.get('time')}"
            if not d.get('tok') or k in seen:
                continue
            r = push.q('SELECT id, status, channel FROM promo WHERE tok = ?', [d['tok']])
            if not r:
                res.append((d['tok'], '없는 tok')); seen.add(k); continue
            r = r[0]; url = str(d.get('post_url') or '')[:300]; t = str(d.get('time') or NOW.isoformat(timespec='minutes'))[:25]
            if d.get('channel') and d['channel'] != r['channel']:
                res.append((d['tok'], f"채널 불일치 {d['channel']}≠{r['channel']}"))
            elif r['status'] in ('APPROVED', 'SCHEDULED'):
                push.q("UPDATE promo SET status = 'PUBLISHED', published = ?, post_url = ?, note = ?, updated = ? WHERE id = ?", [t, url, '게시 완료(홍보 세션 보고)', int(NOW.timestamp()), r['id']])
                res.append((d['tok'], 'PUBLISHED'))
            elif r['status'] == 'PUBLISHED':
                res.append((d['tok'], '이미 게시 완료'))
            else:
                push.q('UPDATE promo SET post_url = ?, note = ?, updated = ? WHERE id = ?', [url, f"승인 전 게시 보고({r['status']}) {t}", int(NOW.timestamp()), r['id']])
                res.append((d['tok'], f"승인 전({r['status']}) — 상태 유지, 관리자 승인 필요"))
            seen.add(k)
        json.dump(sorted(seen), open(DONE_SEEN, 'w', encoding='utf-8'), ensure_ascii=False)
    rows = push.q("SELECT tok, day, slot, kind, ref, channel, status, title, body, link, scheduled, post_url, note FROM promo WHERE status IN ('REVIEW', 'APPROVED', 'SCHEDULED') AND day >= ? ORDER BY day DESC, id",
                  [(TODAY - datetime.timedelta(days=14)).isoformat()])
    json.dump({'updated': NOW.isoformat(timespec='minutes'), 'note': 'APPROVED·SCHEDULED 만 게시 가능(REVIEW 는 관리자 승인 전). 게시 후 promo_done.jsonl 에 한 줄 추가',
               'done_result': [{'tok': a, 'result': b} for a, b in res], 'items': rows}, open(REVIEW_F, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, rows


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'sync':
        R, W = sync()
        for x in R:
            print('게시 완료 반영', *x)
        print('promo_review.json', len(W), '건 (상태별', {s: sum(1 for w in W if w['status'] == s) for s in ('REVIEW', 'APPROVED', 'SCHEDULED')}, ')')
        sys.exit()
    slot = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'all'
    M = run(slot, '--dry' in sys.argv)
    for tok, kind, ref, ch, title, body, url, st, bad in M:
        print(f'[{st}] {kind}:{ref} {CH_NAME[ch]} — {title[:40]}' + (f'  검사 실패: {bad}' if bad else ''))
    print('후보', len(M), '검토 대기', sum(1 for m in M if m[7] == 'REVIEW'), '검사 실패', sum(1 for m in M if m[7] == 'DRAFT'))
