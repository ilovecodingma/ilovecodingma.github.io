# -*- coding: utf-8 -*-
"""웹툰·애니 추천용 목록 수집 (2026-10-20 「웹툰 애니 추천도 recommend 로」)
 - 웹툰: 네이버웹툰 공개 JSON(요일별 연재작 + 완결작 조회순). robots.txt 의 /api 는 허용. 장르·태그·연령·즐겨찾기 수는 작품 정보 API 에서.
 - 애니: AniList 공개 GraphQL (분기별 인기작 + 역대 인기).
 저장: _gongmo/watch/webtoon.json, anime.json (표지는 원 서버 주소만 기록=링크, 시놉시스 문장은 저장하지 않음)
 이어서 실행 가능, 요청 간격 0.7초. 사용: python watch_collect.py [webtoon|anime|all]"""
import os, sys, json, time, re, requests
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'watch'); os.makedirs(OUT, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0 (jupjup-watch/1.0; +https://sungprofile.cloud)'}
DAY = {'MONDAY': '월', 'TUESDAY': '화', 'WEDNESDAY': '수', 'THURSDAY': '목', 'FRIDAY': '금', 'SATURDAY': '토', 'SUNDAY': '일', 'DAILY': '매일', 'DAILYPLUS': '매일+'}


def get(url, params=None, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=25)
            if r.status_code == 200: return r.json()
            if r.status_code in (429, 503): time.sleep(8 * (i + 1))
        except Exception:
            time.sleep(3)
    return None


def load(name):
    f = os.path.join(OUT, name)
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}


def save(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


STOP = set('그리고 그러나 하지만 그런데 그녀는 그는 자신 자신의 이제 정말 모든 어느 어떤 하는 있는 없는 되는 이런 저런 그런 우리 사람 사람들 사실 처음 다시 함께 하나 시작 앞에 위해 대한 통해 이후 이상 하루 바로 순간 지금 계속 결국 마침내 모두 아니 어쩌면 그날 어느날 갑자기 때문 하게 되어 되었다 한다 된다 있다 없다 한다면 그것 이것 무엇 누구 어디 같은 모습 이야기 만난다 시작된다 펼쳐진다 벌어진다'.split())
JOSA = re.compile(r'(으로부터|에게서|에서는|으로는|에게는|이라는|라는|에서|에게|으로|부터|까지|처럼|보다|이다|이며|이고|이란|하며|하고|해서|하는|했던|인|의|은|는|이|가|을|를|에|도|만|와|과|로)$')


def synopsis_kw(text, title):
    """줄거리 → 핵심 낱말(최대 14). 원문은 저장하지 않고 낱말만 쓴다."""
    import collections
    c = collections.Counter()
    for w in re.findall(r'[가-힣]{2,6}', text or ''):
        w2 = JOSA.sub('', w)
        if len(w2) >= 2 and w2 not in STOP and w2 not in (title or ''): c[w2] += 1
    return [w for w, n in c.most_common(14)]


def webtoon(finished_info=1000):
    W = load('webtoon.json'); items = W.get('items', {})
    d = get('https://comic.naver.com/api/webtoon/titlelist/weekday')
    base = []
    for day, L in (d or {}).get('titleListMap', {}).items():
        for t in L:
            base.append((t, False, day))
    fin = []
    p1 = get('https://comic.naver.com/api/webtoon/titlelist/finished', {'page': 1, 'order': 'VIEWCOUNT'})
    pages = (p1 or {}).get('pageInfo', {}).get('totalPages', 0)
    print('완결 쪽수', pages, flush=True)
    for pg in range(1, pages + 1):
        j = p1 if pg == 1 else get('https://comic.naver.com/api/webtoon/titlelist/finished', {'page': pg, 'order': 'VIEWCOUNT'})
        if not j: continue
        for t in j['titleList']: fin.append((t, True, ''))
        time.sleep(0.5)
        if len(fin) >= finished_info: break
    rows = {}
    for t, f, day in base + fin[:finished_info]:
        i = str(t['titleId'])
        r = rows.setdefault(i, {'id': t['titleId'], 'n': t['titleName'], 'a': t.get('author', ''), 'th': t.get('thumbnailUrl', ''), 'fin': f, 'days': [], 'sc': t.get('starScore'), 'adult': bool(t.get('adult')), 'rest': bool(t.get('rest'))})
        if day and DAY.get(day, day) not in r['days']: r['days'].append(DAY.get(day, day))
        if t.get('starScore'): r['sc'] = t['starScore']
    print('웹툰 대상', len(rows), '· 이미 정보 받은 것', sum(1 for k in rows if k in items and items[k].get('tags') is not None), flush=True)
    n = 0
    for k, r in rows.items():
        old = items.get(k)
        if old and old.get('tags') is not None and old.get('kw') is not None:
            old.update({x: r[x] for x in ('sc', 'fin', 'days', 'rest', 'th', 'adult')}); continue
        j = get('https://comic.naver.com/api/article/list/info', {'titleId': k})
        if j:
            r['tags'] = [x['tagName'] for x in (j.get('curationTagList') or [])][:6]
            r['age'] = (j.get('age') or {}).get('type', '')
            r['fav'] = int(j.get('favoriteCount') or 0)
            r['pub'] = j.get('publishDescription', '')
            r['lv'] = j.get('webtoonLevelCode', '')
            r['kw'] = synopsis_kw(j.get('synopsis', ''), r['n'])
        else:
            r['tags'] = None
        items[k] = r; n += 1
        if n % 100 == 0:
            save('webtoon.json', {'at': time.strftime('%Y-%m-%d %H:%M'), 'items': items}); print('웹툰 정보', n, flush=True)
        time.sleep(0.7)
    save('webtoon.json', {'at': time.strftime('%Y-%m-%d %H:%M'), 'items': items})
    print('웹툰 저장', len(items), flush=True)


Q = """query($page:Int,$season:MediaSeason,$year:Int,$sort:[MediaSort]){Page(page:$page,perPage:50){pageInfo{hasNextPage}media(type:ANIME,season:$season,seasonYear:$year,sort:$sort,isAdult:false){id title{romaji english native} synonyms genres tags{name rank} averageScore popularity favourites episodes duration format status season seasonYear startDate{year month day} studios(isMain:true){nodes{name}} coverImage{large color} siteUrl externalLinks{site url type language} trailer{id site} recommendations(sort:RATING_DESC,perPage:8){nodes{rating mediaRecommendation{id}}} reviews(sort:RATING_DESC,limit:4){nodes{score rating ratingAmount summary}}}}}"""
Q2 = Q.replace('season:$season,seasonYear:$year,', '')


def anilist(body):
    for i in range(4):
        try:
            r = requests.post('https://graphql.anilist.co', json=body, headers=H, timeout=30)
            if r.status_code == 200: return r.json()['data']['Page']
            if r.status_code == 429: time.sleep(65)
        except Exception:
            time.sleep(5)
    return None


RV_WORDS = {'art': ['animation', 'visual', 'art', 'beautiful', 'stunning'], 'story': ['story', 'plot', 'narrative', 'writing'], 'char': ['character', 'protagonist', 'development'], 'music': ['music', 'soundtrack', 'ost', 'opening'], 'emotional': ['emotional', 'touching', 'tears', 'heartwarming', 'moving'], 'funny': ['funny', 'comedy', 'hilarious', 'humor'], 'dark': ['dark', 'violent', 'brutal', 'gritty'], 'slow': ['slow', 'pacing', 'boring'], 'action': ['action', 'fight', 'battle']}


def rv_kw(text):
    t = (text or '').lower()
    return [k for k, ws in RV_WORDS.items() if sum(t.count(w) for w in ws) >= 1]


def anime():
    A = load('anime.json'); items = A.get('items', {})
    def add(m):
        k = str(m['id']); kr = next((s for s in (m.get('synonyms') or []) if re.search(r'[가-힣]', s)), '')
        t = m['title']
        st = [s['name'] for s in (m.get('studios') or {}).get('nodes', [])][:2]
        ott = [{'s': x['site'], 'u': x['url']} for x in (m.get('externalLinks') or []) if x.get('type') == 'STREAMING'][:6]
        sd = m.get('startDate') or {}
        items[k] = {'id': m['id'], 'kr': kr, 'ro': t.get('romaji') or '', 'en': t.get('english') or '', 'jp': t.get('native') or '', 'g': m.get('genres') or [], 'tg': [x['name'] for x in (m.get('tags') or []) if x.get('rank', 0) >= 60][:6],
                    'sc': m.get('averageScore'), 'pop': m.get('popularity'), 'fav': m.get('favourites'), 'ep': m.get('episodes'), 'min': m.get('duration'), 'fmt': m.get('format'), 'st': m.get('status'),
                    'season': m.get('season'), 'year': m.get('seasonYear'), 'sd': f"{sd.get('year') or ''}-{sd.get('month') or ''}", 'studio': st, 'cv': (m.get('coverImage') or {}).get('large', ''), 'color': (m.get('coverImage') or {}).get('color', ''),
                    'url': m.get('siteUrl'), 'rec': [(x['mediaRecommendation']['id'], x['rating']) for x in ((m.get('recommendations') or {}).get('nodes') or []) if x.get('mediaRecommendation') and (x.get('rating') or 0) > 0][:8], 'rv': {'n': len((m.get('reviews') or {}).get('nodes') or []), 'sc': round(sum(x['score'] for x in (m.get('reviews') or {}).get('nodes') or []) / max(1, len((m.get('reviews') or {}).get('nodes') or [])), 1), 'kw': rv_kw(' '.join(x['summary'] or '' for x in (m.get('reviews') or {}).get('nodes') or []))}, 'ott': ott, 'tr': (m.get('trailer') or {}).get('id') if (m.get('trailer') or {}).get('site') == 'youtube' else ''}
    now = time.localtime(); y0 = now.tm_year
    for y in range(y0, y0 - 6, -1):
        for s in ('WINTER', 'SPRING', 'SUMMER', 'FALL'):
            if y == y0 and ((s == 'FALL' and now.tm_mon < 9) or (s == 'SUMMER' and now.tm_mon < 6) or (s == 'SPRING' and now.tm_mon < 3)) and False: pass
            pg = 1
            while pg <= 2:
                p = anilist({'query': Q, 'variables': {'page': pg, 'season': s, 'year': y, 'sort': ['POPULARITY_DESC']}})
                if not p: break
                for m in p['media']: add(m)
                if not p['pageInfo']['hasNextPage']: break
                pg += 1; time.sleep(0.8)
            time.sleep(0.8)
        print('애니', y, len(items), flush=True)
    for pg in range(1, 21):   # 역대 인기 1,000
        p = anilist({'query': Q2, 'variables': {'page': pg, 'sort': ['POPULARITY_DESC']}})
        if not p: break
        for m in p['media']: add(m)
        time.sleep(0.8)
        if pg % 5 == 0: print('애니 역대', pg, len(items), flush=True)
    save('anime.json', {'at': time.strftime('%Y-%m-%d %H:%M'), 'items': items})
    print('애니 저장', len(items), flush=True)


if __name__ == '__main__':
    w = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if w in ('anime', 'all'): anime()
    if w in ('webtoon', 'all'): webtoon()
