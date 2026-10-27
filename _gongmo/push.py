# -*- coding: utf-8 -*-
"""루리의 줍줍 공모전 웹푸시 발송 (2026-10-18 사용자: 공모전 알림 기능 + 웹푸시)
구독은 사이트 /app/ → 워커 /api/push/sub → D1 push_subs. 이 스크립트가 PC에서 보낸다(개인키 ~/.jupjup_vapid.pem 은 PC에만).
사용: python push.py new     → 관심 분야 새 공모전 모아서 1통 (작업 스케줄러 JupJup_PushNew 19:10)
      python push.py dl      → 인기 공모전 마감 3일 전 1통 (JupJup_PushDL 09:10)
      python push.py meal    → 점심·저녁 「오늘 뭐 먹지?」 메뉴 추천 1통 (작업 스케줄러 JupJup_PushMealLunch 11:20 / JupJup_PushMealDinner 17:20)
      python push.py fit     → 「오늘 운동했나요?」 이용자가 고른 시각(fh)에 맞춰 매시 정각 실행
      python push.py dl2     → 마감 7일·1일 전 (구독자가 켠 것만, 마감일이 있는 공모전만)
      python push.py test    → 대장(uid 16) 구독에만 시험 알림
      --dry                  → 보낼 내용만 출력
처음 실행한 날은 지금 올라온 공모전을 '이미 본 것'으로만 기록하고 새 공모전 알림은 보내지 않는다."""
import os, sys, json, datetime, urllib.request
from pywebpush import webpush, WebPushException
sys.path.insert(0, os.path.expanduser('~/remote_login')); import cf_token
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DB = 'bad84d2c-a24e-4ba9-8de9-dad02f30e30e'
KEY = os.path.expanduser('~/.jupjup_vapid.pem')
CLAIMS = {'sub': 'mailto:sung2011103@naver.com'}
STATE = os.path.join(HERE, 'push_state.json')
LOG = os.path.join(HERE, 'push_log.txt')
SLUG = {'문학': 'literature', '아이디어·정책': 'idea', '디자인': 'design', '영상': 'video', '논문': 'paper', 'IT·과학': 'it', '요리·레시피': 'food', '해외': 'global', '기타': 'etc'}
NAME = {v: k for k, v in SLUG.items()}
ADMIN_UID = 16


def q(sql, params=None):
    a, t = cf_token.get()
    r = urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{a}/d1/database/{DB}/query', method='POST',
        data=json.dumps({'sql': sql, **({'params': params} if params else {})}).encode(), headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json', 'User-Agent': 'wrangler/4.40.0'})
    return json.load(urllib.request.urlopen(r, timeout=60))['result'][0]['results']


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{datetime.datetime.now():%Y-%m-%d %H:%M}] {s}\n')


def slugs(c):
    return {SLUG.get(t, 'etc') for t in (c.get('tags') or ['기타'])}


def want(sub, c):
    cs = [x for x in (sub['cats'] or '').split(',') if x]
    return not cs or bool(slugs(c) & set(cs))


def short(t, n=34):
    return t if len(t) <= n else t[:n - 1] + '…'


def send(sub, msg, dry):
    if dry:
        log('  (dry)', msg['title'], '|', msg['body'])
        return True
    try:
        webpush({'endpoint': sub['endpoint'], 'keys': {'p256dh': sub['p256dh'], 'auth': sub['auth']}}, json.dumps(msg, ensure_ascii=False),
                vapid_private_key=KEY, vapid_claims=dict(CLAIMS), ttl=12 * 3600, timeout=20)
        q('UPDATE push_subs SET sent = sent + 1, fails = 0, last_ok = ? WHERE endpoint = ?', [int(datetime.datetime.now().timestamp()), sub['endpoint']])
        return True
    except WebPushException as e:
        code = e.response.status_code if e.response is not None else 0
        if code in (404, 410):   # 구독이 사라짐(앱 삭제·알림 해제) -> 지움
            q('DELETE FROM push_subs WHERE endpoint = ?', [sub['endpoint']])
        else:
            q('UPDATE push_subs SET fails = fails + 1 WHERE endpoint = ?', [sub['endpoint']])
            q('DELETE FROM push_subs WHERE endpoint = ? AND fails >= 5', [sub['endpoint']])
        log('  실패', code, str(e)[:120])
        return False


def pick_menu(slot, hist):
    """사이트 추천(recommend.js)과 같은 요소로 하나 고른다: 때·오늘 날씨·제철·지금 많이 보는 메뉴·사진 있음, 최근 7번 고른 건 제외."""
    import math, re, hashlib
    R = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'rec.json'), encoding='utf-8'))
    try: td = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'today.json'), encoding='utf-8'))
    except Exception: td = {}
    try: pop = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'rec_pop.json'), encoding='utf-8'))
    except Exception: pop = {}
    TG = R['tags']; slug = lambda n: re.sub(r'[^0-9A-Za-z가-힣]+', '-', n).strip('-')
    SL = {'점심': ({'든든': 1.2}, {'밥': .8, '면': .8}, 30), '저녁': ({'든든': .9}, {'국물': .7, '볶음': .6, '조림': .5, '밥': .3}, 60)}[slot]
    mv = max([v[0] for v in pop.values()] + [1]); best = None
    for r in R['r']:
        n, e, m, lv, tg, cat, ph, need, opt, ns = r
        if not ph or n in hist: continue
        t = [TG[i] for i in tg]; sc = 0; why = []
        sc += max([SL[0].get(x, 0) for x in t] + [0]) + SL[1].get(cat, 0) + (.5 if m <= SL[2] else -.6)
        if td.get('want', {}).get(cat): sc += td['want'][cat] * .8; why.append((td.get('why', '').split('엔')[0] + '엔 ' + cat))
        sea = [i for i in need + opt if i in td.get('season', [])]
        if sea: sc += .5; why.append('제철 ' + sea[0])
        p = pop.get(slug(n))
        if p: sc += 1.4 * math.log(1 + p[0]) / math.log(1 + mv) + min(.8, p[1] * .25); why.append('요즘 많이 보는 메뉴')
        if lv == 0: sc += .35
        sc += int(hashlib.md5((str(datetime.date.today()) + slot + n).encode()).hexdigest(), 16) % 1000 / 1000 * 1.3
        if best is None or sc > best[0]: best = (sc, n, e, m, why, slug(n))
    return best


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'new'
    dry = '--dry' in sys.argv
    items = json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))['items']
    st = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    today = datetime.date.today()
    subs = q('SELECT endpoint, p256dh, auth, cats, newc, dl, meal, uid, fit, fh, dl2 FROM push_subs')
    log(f'== {mode} 구독 {len(subs)} / 진행 중 공모전 {len(items)}{" (dry)" if dry else ""}')
    ok = 0
    if mode == 'test':
        for s in [s for s in subs if s['uid'] == ADMIN_UID]:
            ok += send(s, {'title': '🔔 루리의 줍줍 시험 알림', 'body': '알림이 잘 오는지 확인하는 시험이에요.', 'url': '/app/', 'tag': 'jupjup-test'}, dry)
    elif mode == 'new':
        seen = set(st.get('seen', []))
        first = not seen
        new = [c for c in items if c['id'] not in seen]
        log(f'새 공모전 {len(new)}건' + (' (첫 실행: 기록만)' if first else ''))
        if not first and new:
            for s in subs:
                if not s['newc']:
                    continue
                mine = sorted([c for c in new if want(s, c)], key=lambda c: -(c.get('pv') or 0))
                if not mine:
                    continue
                cs = [x for x in (s['cats'] or '').split(',') if x]
                lab = NAME.get(cs[0], '') if len(cs) == 1 else ''
                top = mine[0]
                body = short(top['title']) + (f' · {top["prize"]}' if top.get('prize') else '') + (f' 외 {len(mine) - 1}건' if len(mine) > 1 else '')
                url = f'/c/{top["id"]}/' if len(mine) == 1 else (f'/cat/{cs[0]}/' if lab else '/')
                ok += send(s, {'title': f'🆕 새 공모전 {len(mine)}건' + (f' · {lab}' if lab else ''), 'body': body, 'url': url, 'tag': 'jupjup-new'}, dry)
        if not dry:
            st['seen'] = sorted(seen | {c['id'] for c in items})
    elif mode == 'meal':
        now_h = datetime.datetime.now().hour
        slot = '점심' if now_h < 15 else '저녁'
        hist = st.get('meal_hist', [])[-7:]
        pk = pick_menu(slot, hist)
        if not pk:
            log('고를 메뉴가 없어요'); return
        sc, n, e, m, why, sl = pk
        body = f'{e} {n} · {m}분' + (f' · {why[0]}' if why else '')
        log(f'{slot} 추천: {n}')
        for s in subs:
            if not s['meal']:
                continue
            ok += send(s, {'title': f'🍽️ 오늘 {slot} 뭐 먹지?', 'body': body, 'url': f'/fridge/r/{sl}/?src=push_meal', 'tag': 'jupjup-meal',
                           'image': f'https://sungprofile.cloud/assets/fridge/ph/t/{sl}.webp'}, dry)
        if not dry:
            st['meal_hist'] = (hist + [n])[-14:]
    elif mode == 'fit':
        hr = datetime.datetime.now().hour
        for s in subs:
            if s['fit'] and int(s['fh'] if s['fh'] is not None else 20) == hr:
                ok += send(s, {'title': '💪 오늘 운동했나요?', 'body': '5분만 해도 연속 기록이 이어져요. 눌러서 바로 시작!', 'url': '/diet/workout/?src=push_fit', 'tag': 'jupjup-fit'}, dry)
    elif mode == 'dl2':
        for n, lab in ((7, '7일'), (1, '하루')):
            dd = (today + datetime.timedelta(days=n)).isoformat()
            due = sorted([c for c in items if c.get('end') == dd], key=lambda c: -(c.get('pv') or 0))
            log(f'D-{n} 공모전 {len(due)}건')
            for s in subs:
                if not s['dl2']:
                    continue
                mine = [c for c in due if want(s, c)]
                if not mine:
                    continue
                top = mine[0]
                body = short(top['title']) + (f' · {top["prize"]}' if top.get('prize') else '') + (f' 외 {len(mine) - 1}건' if len(mine) > 1 else '')
                ok += send(s, {'title': f'📅 마감 {lab} 전 · {len(mine)}건', 'body': body, 'url': f'/c/{top["id"]}/?src=push_dl{n}', 'tag': f'jupjup-dl{n}'}, dry)
    elif mode == 'dl':
        d3 = (today + datetime.timedelta(days=3)).isoformat()
        due = sorted([c for c in items if c['end'] == d3], key=lambda c: -(c.get('pv') or 0))
        log(f'D-3 공모전 {len(due)}건')
        for s in subs:
            if not s['dl']:
                continue
            mine = [c for c in due if want(s, c)]
            if not mine:
                continue
            top = mine[0]
            body = short(top['title']) + (f' · {top["prize"]}' if top.get('prize') else '') + (f' 외 {len(mine) - 1}건' if len(mine) > 1 else '')
            ok += send(s, {'title': f'⏰ 마감 3일 전 · {len(mine)}건', 'body': body, 'url': f'/c/{top["id"]}/', 'tag': 'jupjup-dl'}, dry)
    if not dry:
        st[f'last_{mode}'] = datetime.datetime.now().isoformat(timespec='minutes')
        json.dump(st, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False)
    log(f'보냄 {ok}')


if __name__ == '__main__':
    main()
