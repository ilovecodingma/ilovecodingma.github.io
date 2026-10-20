# 게임 허브 자료 (2026-10-20 홍보 세션 기획서 「커뮤니티 콘텐츠」 1번): Epic 무료 게임 + 스팀 할인·인기·출시 예정.
# 출처: Epic Games Store 공개 프로모션 JSON(robots 제한 없음), Steam 스토어 featuredcategories 공개 API(robots.txt 에서 /api/ 제한 없음).
# 12시간에 한 번만 받아 game_cache.json 에 두고, 빌드는 캐시만 읽는다(Epic 무료 게임은 목요일 새벽 한국 시간에 바뀌어서 하루 1번보다 조금 자주).
import datetime, json, os, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'game_cache.json')
UA = {'User-Agent': 'jupjup-game/1.0 (+https://sungprofile.cloud)'}
KST = datetime.timezone(datetime.timedelta(hours=9))
EPIC = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=ko&country=KR&allowCountries=KR'
STEAM = 'https://store.steampowered.com/api/featuredcategories?cc=kr&l=koreana'


def _kst(s):
    return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(KST).strftime('%m/%d %H:%M')


def epic():
    els = requests.get(EPIC, headers=UA, timeout=25).json()['data']['Catalog']['searchStore']['elements']
    free, up, sale = [], [], []
    for x in els:
        p = x.get('promotions') or {}
        cur = [o for g in (p.get('promotionalOffers') or []) for o in g['promotionalOffers']]
        nxt = [o for g in (p.get('upcomingPromotionalOffers') or []) for o in g['promotionalOffers']]
        slug = next((m['pageSlug'] for m in (x.get('offerMappings') or []) if m.get('pageSlug')), None) or next((m['pageSlug'] for m in ((x.get('catalogNs') or {}).get('mappings') or []) if m.get('pageSlug')), None) or x.get('productSlug') or x.get('urlSlug')
        img = next((i['url'] for t in ('OfferImageWide', 'DieselStoreFrontWide', 'Thumbnail') for i in x.get('keyImages', []) if i.get('type') == t and i['url'].startswith('http')), '')
        tp = x['price']['totalPrice']
        base = {'name': x['title'], 'url': f'https://store.epicgames.com/ko/p/{slug}' if slug else 'https://store.epicgames.com/ko/free-games', 'img': img, 'orig': tp['fmtPrice']['originalPrice']}
        if cur and cur[0]['discountSetting']['discountPercentage'] == 0:   # 낼 돈 0%
            free.append(dict(base, start=_kst(cur[0]['startDate']), end=_kst(cur[0]['endDate'])))
        elif nxt and nxt[0]['discountSetting']['discountPercentage'] == 0:
            up.append(dict(base, start=_kst(nxt[0]['startDate']), end=_kst(nxt[0]['endDate'])))
        elif cur:
            sale.append(dict(base, off=100 - cur[0]['discountSetting']['discountPercentage'], price=tp['fmtPrice']['discountPrice'], end=_kst(cur[0]['endDate'])))
    return {'free': free, 'upcoming': up, 'sale': sale}


def steam():
    d = requests.get(STEAM, headers=UA, timeout=25).json()
    won = lambda v: None if v in (None, 0) else int(v) // 100   # API 가격은 100배 값(원 단위 ×100)
    out = {}
    for k in ('specials', 'top_sellers', 'coming_soon', 'new_releases'):
        items = []
        for x in d.get(k, {}).get('items', []):
            if x.get('type') != 0:
                continue
            items.append({'id': x['id'], 'name': x['name'], 'img': x.get('large_capsule_image') or x.get('header_image') or '', 'off': x.get('discount_percent') or 0,
                          'orig': won(x.get('original_price')), 'price': won(x.get('final_price')) if x.get('final_price') is not None else None,
                          'until': (datetime.datetime.fromtimestamp(x['discount_expiration'], KST).strftime('%m/%d %H:%M') if x.get('discount_expiration') else '')})
        out[k] = items
    return out


STEAMDOC = 'https://partner.steamgames.com/doc/marketing/upcoming_events'
MON = {m: i for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 1)}
MON3 = {m[:3]: i for m, i in MON.items()}


def steam_events():
    """스팀 공식(Steamworks 문서 「Upcoming Steam Events」, robots 제한 없음)에서 시즌 세일·테마 페스티벌·Next Fest 일정. 날짜가 TBD 면 None."""
    import re, html
    h = requests.get(STEAMDOC, headers=UA, timeout=25).text
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', t))
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n', t)
    i = t.rfind('Seasonal Sales')
    t = t[i:]
    iso = lambda d, m, y: f'{int(y):04d}-{MON[m]:02d}-{int(d):02d}'
    out = {'seasonal': [], 'fests': [], 'nextfest': []}
    for m in re.finditer(r'((?:Winter|Spring|Summer|Autumn) Sale \d{4})\s*\|\s*([^\n]+)', t):
        r = re.match(r'(\d{1,2}) (\w+),? (\d{4}) - (\d{1,2}) (\w+),? (\d{4})', m.group(2).strip())
        out['seasonal'].append({'name': m.group(1), 'start': iso(r.group(1), r.group(2), r.group(3)) if r else None, 'end': iso(r.group(4), r.group(5), r.group(6)) if r else None})
    for ym in re.finditer(r'(\d{4}) Fests\s*\nEvent Dates\s*\nTheme\s*\nRegistration\s*\nEligibility & Notes\s*\n(.*?)(?=\n\d{4} Fests|\nNext Fest)', t, re.S):
        yr = ym.group(1)
        for r in re.finditer(r'\n?(\w{3}) (\d{1,2})\n(\w{3}) (\d{1,2})\n([^\n]+)\nRegistration details', ym.group(2)):
            ey = int(yr) + (1 if MON3[r.group(3)] < MON3[r.group(1)] else 0)
            out['fests'].append({'name': r.group(5), 'start': f'{yr}-{MON3[r.group(1)]:02d}-{int(r.group(2)):02d}', 'end': f'{ey}-{MON3[r.group(3)]:02d}-{int(r.group(4)):02d}'})
    for r in re.finditer(r'Next Fest \| (\w+) (\d{1,2}) - (?:(\w+) )?(\d{1,2}), (\d{4})', t):
        em = r.group(3) or r.group(1)
        out['nextfest'].append({'name': 'Steam Next Fest', 'start': iso(r.group(2), r.group(1), r.group(5)), 'end': iso(r.group(4), em, r.group(5))})
    return out


def record_history(d):
    """우리가 받은 날의 가격·무료 게임을 game_hist.json 에 쌓는다(공개 API 에는 가격 이력이 없어서 기록 시작일부터만). 하루 한 번."""
    hf = os.path.join(HERE, 'game_hist.json')
    H = json.load(open(hf, encoding='utf-8')) if os.path.exists(hf) else {'since': datetime.datetime.now(KST).strftime('%Y-%m-%d'), 'steam': {}, 'free': []}
    today = datetime.datetime.now(KST).strftime('%Y-%m-%d')
    st = d.get('steam') or {}
    for k in ('specials', 'top_sellers'):
        for x in st.get(k, []):
            if x.get('price') is None:
                continue
            e = H['steam'].setdefault(str(x['id']), {'name': x['name'], 'pts': []})
            if not e['pts'] or e['pts'][-1][0] != today:
                e['pts'].append([today, x['price'], x.get('off', 0)])
            e['pts'] = e['pts'][-400:]
    ep = d.get('epic') or {}
    have = {(g['name'], g['start']) for g in H['free']}
    for k in ('free', 'upcoming'):
        for g in ep.get(k, []):
            if (g['name'], g['start']) not in have:
                H['free'].append({'name': g['name'], 'url': g['url'], 'img': g.get('img', ''), 'orig': g.get('orig', ''), 'start': g['start'], 'end': g['end'], 'seen': today})
                have.add((g['name'], g['start']))
    json.dump(H, open(hf, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return H


def load(force=False):
    old = json.load(open(F, encoding='utf-8')) if os.path.exists(F) else {}
    if not force and old.get('ts') and time.time() - old['ts'] < 12 * 3600:
        return old
    out = dict(old)
    for k, fn in (('epic', epic), ('steam', steam), ('events', steam_events)):
        try:
            out[k] = fn()
        except Exception as e:
            print('게임 자료 받기 실패', k, repr(e)[:120])
    if out.get('epic') or out.get('steam'):
        out['ts'] = time.time()
        out['at'] = datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M')
        json.dump(out, open(F, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        try:
            record_history(out)
        except Exception as e:
            print('게임 기록 저장 실패', repr(e)[:100])
    return out


if __name__ == '__main__':
    d = load(force=True)
    print(d.get('at'), {k: {kk: len(vv) for kk, vv in v.items()} for k, v in d.items() if isinstance(v, dict)})
