# -*- coding: utf-8 -*-
"""게임 DB (2026-10-23 사용자: 각 게임·프로모션 게임·공략을 수집해 정리).
대상: game_cache.json 의 스팀 할인·인기·출시 예정·Epic 무료/할인 게임.
- 스팀 상점 공개 API(appdetails)로 장르·소개·출시일·가격·한국어 지원 (공식 스토어 값)
- 유튜브 검색 결과 화면의 제목·채널·조회수·길이·주소만 읽기 전용으로 모음 (영상 내용·화면 복제 안 함, 보여줄 땐 링크/썸네일)
- 공략 글 본문은 가져오지 않는다.
결과: game_db.json  {games: {key: {...}}, ts}
"""
import json, os, re, sys, time, requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'game_cache.json')
OUT = os.path.join(HERE, 'game_db.json')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'}
MAX_GAMES = 36
YT_TTL = 6 * 86400
ST_TTL = 86400


def slug(s):
    s = re.sub(r'[^0-9A-Za-z가-힣]+', '-', s).strip('-').lower()
    return s[:40] or 'game'


def views(t):
    m = re.search(r'([\d,.]+)\s*(만|천|억)?', t or '')
    if not m:
        return 0
    try:
        n = float(m.group(1).replace(',', ''))
    except ValueError:
        return 0
    return int(n * {'만': 1e4, '천': 1e3, '억': 1e8}.get(m.group(2), 1))


def yt_search(q, n=6):
    try:
        t = requests.get('https://www.youtube.com/results', params={'search_query': q, 'hl': 'ko', 'gl': 'KR'}, headers=H, timeout=30).text
    except Exception:
        return None
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', t, re.S)
    if not m:
        return None
    d = json.loads(m.group(1))
    out = []

    def walk(x):
        if isinstance(x, dict):
            if 'videoRenderer' in x:
                v = x['videoRenderer']
                if v.get('videoId'):
                    out.append({'id': v['videoId'], 't': ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', [])),
                                'v': views(v.get('viewCountText', {}).get('simpleText', '')), 'ago': v.get('publishedTimeText', {}).get('simpleText', ''),
                                'ch': ''.join(r.get('text', '') for r in v.get('ownerText', {}).get('runs', [])), 'dur': v.get('lengthText', {}).get('simpleText', '')})
            for y in x.values():
                walk(y)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(d)
    seen, res = set(), []
    for v in out:
        if v['id'] not in seen and v['dur']:
            seen.add(v['id']); res.append(v)
    return res[:n]


def steam_info(appid):
    try:
        r = requests.get('https://store.steampowered.com/api/appdetails', params={'appids': appid, 'l': 'koreana', 'cc': 'kr'}, headers=H, timeout=30).json()
        x = r.get(str(appid), {})
        if not x.get('success'):
            return None
        d = x['data']
        return {'type': d.get('type'), 'desc': (d.get('short_description') or '')[:300], 'genres': [g['description'] for g in d.get('genres', [])][:5],
                'release': (d.get('release_date') or {}).get('date', ''), 'dev': (d.get('developers') or [''])[0], 'pub': (d.get('publishers') or [''])[0],
                'ko': '한국어' in (d.get('supported_languages') or ''), 'free': bool(d.get('is_free')),
                'price': (d.get('price_overview') or {}).get('final_formatted', ''), 'orig': (d.get('price_overview') or {}).get('initial_formatted', ''),
                'off': (d.get('price_overview') or {}).get('discount_percent', 0), 'header': d.get('header_image', ''),
                'metacritic': (d.get('metacritic') or {}).get('score')}
    except Exception:
        return None


def main():
    c = json.load(open(CACHE, encoding='utf-8'))
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'games': {}}
    G = old.get('games', {})
    cand = []   # (key, name, appid, promo list)
    st = c.get('steam') or {}
    for k_, label in (('specials', '스팀 할인'), ('top_sellers', '스팀 인기'), ('coming_soon', '출시 예정'), ('new_releases', '신작')):
        for x in (st.get(k_) or [])[:10 if k_ != 'new_releases' else 6]:
            cand.append((f's{x["id"]}', x['name'], x['id'], {'kind': label, 'off': x.get('off', 0), 'price': x.get('price'), 'orig': x.get('orig'), 'until': x.get('until'), 'img': x.get('img')}))
    ep = c.get('epic') or {}
    for k_, label in (('free', 'Epic 무료'), ('sale', 'Epic 할인'), ('upcoming', 'Epic 예고')):
        for x in ep.get(k_, []):
            cand.append((f'e{slug(x["name"])}', x['name'], None, {'kind': label, 'orig': x.get('orig'), 'start': x.get('start'), 'end': x.get('end'), 'url': x.get('url'), 'img': x.get('img')}))
    games = {}
    for key, name, appid, promo in cand:
        g = games.setdefault(key, {'name': name, 'appid': appid, 'promos': []})
        g['promos'].append(promo)
    keys = list(games)[:MAX_GAMES]
    now = time.time()
    for key in keys:
        g = games[key]
        prev = G.get(key, {})
        for f in ('steam', 'steam_ts', 'yt', 'yt_ts'):
            if f in prev:
                g[f] = prev[f]
        if g['appid'] and now - g.get('steam_ts', 0) > ST_TTL:
            info = steam_info(g['appid'])
            if info:
                g['steam'] = info
            g['steam_ts'] = now
            time.sleep(1.2)
        if now - g.get('yt_ts', 0) > YT_TTL:
            res = yt_search(f'{g["name"]} 공략', 8) or []
            res2 = yt_search(f'{g["name"]} 초보 가이드', 5) or []
            seen, vids = set(), []
            for v in sorted(res + res2, key=lambda v: -v['v']):
                if v['id'] not in seen and v['v'] >= 500:
                    seen.add(v['id']); vids.append(v)
            if res or res2:
                g['yt'] = vids[:6]
                g['yt_ts'] = now
            time.sleep(2.0)
        print(key, g['name'][:30], len(g.get('yt', [])), 'steam' if g.get('steam') else '-')
    json.dump({'ts': now, 'at': time.strftime('%Y-%m-%d %H:%M'), 'games': {k: games[k] for k in keys}}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
