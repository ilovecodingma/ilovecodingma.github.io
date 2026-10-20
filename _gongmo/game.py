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


def load(force=False):
    old = json.load(open(F, encoding='utf-8')) if os.path.exists(F) else {}
    if not force and old.get('ts') and time.time() - old['ts'] < 12 * 3600:
        return old
    out = dict(old)
    for k, fn in (('epic', epic), ('steam', steam)):
        try:
            out[k] = fn()
        except Exception as e:
            print('게임 자료 받기 실패', k, repr(e)[:120])
    if out.get('epic') or out.get('steam'):
        out['ts'] = time.time()
        out['at'] = datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M')
        json.dump(out, open(F, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return out


if __name__ == '__main__':
    d = load(force=True)
    print(d.get('at'), {k: {kk: len(vv) for kk, vv in v.items()} for k, v in d.items() if isinstance(v, dict)})
