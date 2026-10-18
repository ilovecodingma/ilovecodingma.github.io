# -*- coding: utf-8 -*-
"""인기 키워드 상세 (/kw/) — 구글 트렌드 한국 RSS(수집 허용)의 급상승 키워드마다 '왜 떴나'·관련 보도·연결 정보를 모은다.
2026-10-18 사용자: "구글 등에서 인기 키워드로 블로그 글도 올리고, 우리 사이트에 상세 정보도 두게 해"(홍보 세션 연구 ⑂ 요청).
네이버 데이터랩은 robots.txt 금지라 쓰지 않는다. 제외: 연예인 사생활·사건사고(피해자)·성·혐오·정치 비방.
결과: root/kw/db.json(키워드별 최신 기록·등장 날짜), root/kw/archive/YYYY-MM-DD.json(그날 뜬 키워드). news.py → talk → analyst 뒤 매시."""
import os, re, json, html, datetime, email.utils
import requests

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DBF = os.path.join(ROOT, 'kw', 'db.json')
ARCH = os.path.join(ROOT, 'kw', 'archive')
KST = datetime.timezone(datetime.timedelta(hours=9))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'}
EXCL = re.compile(r'투척|추돌|폭발|방화|파경|이혼설|열애설|결혼\s?\d+년\s?만에|구속|체포|열애|결별|이혼|불륜|사생활|폭로|스캔들|성폭|성추행|몰카|음란|자살|살인|살해|숨져|숨진|사망|변사|흉기|참사|추락|실종|부상자|피해자|폭행|학대|마약|음주운전')


def slug(k):
    s = re.sub(r"[^0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ]+", "-", k.strip()).strip("-")   # 한글·영문·숫자만 남김(윈도우 폴더·주소 안전)
    return s[:40] or 'kw'


def fetch():
    r = requests.get('https://trends.google.com/trending/rss', params={'geo': 'KR'}, headers=UA, timeout=20)
    x = r.content.decode('utf-8', 'ignore')
    out = []
    for it in re.findall(r'<item>(.*?)</item>', x, re.S):
        g = lambda tag, s=it: html.unescape((re.search(rf'<{tag}>(.*?)</{tag}>', s, re.S) or [None, ''])[1]).strip()
        news = [{'t': g('ht:news_item_title', n), 'u': g('ht:news_item_url', n), 'o': g('ht:news_item_source', n)} for n in re.findall(r'<ht:news_item>(.*?)</ht:news_item>', it, re.S)]
        try:
            ts = int(email.utils.parsedate_to_datetime(g('pubDate')).timestamp())
        except Exception:
            ts = int(datetime.datetime.now().timestamp())
        out.append({'k': g('title'), 'traffic': g('ht:approx_traffic'), 'ts': ts, 'news': [n for n in news if n['t'] and n['u'].startswith('http')]})
    return out


def fetch_signal():
    """실시간 검색어(네이버 대체) — signal.bz 공개 API(robots.txt Allow: /, 2026-10-18 홍보 세션 확인). 관련 기사는 우리 /news/ 데이터에서 찾는다."""
    try:
        d = requests.get('https://api.signal.bz/news/realtime', headers=UA, timeout=20).json()
    except Exception:
        return []
    now = int(datetime.datetime.now().timestamp())
    return [{'k': x['keyword'].strip(), 'traffic': f'실시간 {x["rank"]}위', 'ts': now, 'news': [], 'rank': x['rank']} for x in d.get('top10', []) if x.get('keyword')]


def main():
    now = datetime.datetime.now(KST)
    today = now.date().isoformat()
    G_, S_ = fetch(), fetch_signal()
    gk = {slug(x['k']): x for x in G_}
    items = []
    for x in G_:
        x['src'] = ['google']
        items.append(x)
    for x in S_:
        sl = slug(x['k'])
        if sl in gk:
            gk[sl]['src'].append('naver'); gk[sl]['traffic'] = (gk[sl]['traffic'] or '') + f' · 실시간 {x["rank"]}위'
        else:
            x['src'] = ['naver']; items.append(x)
    db = json.load(open(DBF, encoding='utf-8')) if os.path.exists(DBF) else {}
    rd = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8')) if os.path.exists(os.path.join(ROOT, p)) else {}
    nw, tk, an = rd('news/data.json'), rd('talk/data.json'), rd('analyst/data.json')
    import sys
    sys.path.insert(0, HERE)
    import news as NW
    C = rd('data.json').get('items', [])
    A = json.load(open(os.path.join(ROOT, 'apply.json'), encoding='utf-8'))
    I = {a['id']: a for a in nw.get('items', [])}
    arch_f = os.path.join(ARCH, today + '.json')
    arch = json.load(open(arch_f, encoding='utf-8')) if os.path.exists(arch_f) else []
    kept = 0
    for it in items:
        k = it['k']
        if not k or EXCL.search(k + ' ' + ' '.join(n['t'] for n in it['news'])):
            continue
        sl = slug(k)
        kre = re.compile(re.escape(k.replace(' ', '')))
        ws = [w for w in k.split() if len(w) >= 2]
        ours = [a for a in nw.get('items', []) if kre.search(a['t'].replace(' ', '')) or (len(ws) >= 2 and all(w in a['t'] for w in ws))][:8]
        if not it['news'] and ours:
            it['news'] = [{'t': a['t'], 'u': a['u'], 'o': a['o']} for a in ours[:4]]
        iss = next((x for x in nw.get('issues', []) if kre.search(x['t'].replace(' ', ''))), None)
        tks = [x for x in tk.get('issues', []) if kre.search((x['t'] + ' '.join(x.get('kw', []))).replace(' ', ''))][:3]
        stocks = [s for s in an.get('stocks', []) if s['name'] in k or k in s['name'] or any(s['name'] in n['t'] for n in it['news'][:3])][:3]
        coins = [c for c in an.get('coins', []) if c['name'] in k or c['sym'] == k.upper()][:2]
        pr = NW.promos({'t': k + ' ' + ' '.join(n['t'] for n in it['news'][:3]), 'd': ''}, C, A, today)
        srcs = sorted({n['o'] for n in it['news'] if n['o']} | {a['o'] for a in ours})
        rec = db.get(sl, {'k': k, 'slug': sl, 'days': []})
        if today not in rec['days']:
            rec['days'].append(today)
        posts = json.load(open(os.path.join(HERE, 'kw_posts.json'), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'kw_posts.json')) else {}
        rec.update({'src': it.get('src', ['google']), 'post': posts.get(sl), 'k': k, 'traffic': it['traffic'], 'ts': it['ts'], 'updated': now.strftime('%Y-%m-%d %H:%M'), 'news': it['news'][:6], 'srcs': srcs,
                    'ours': [{'t': a['t'], 'o': a['o'], 'u': a['u'], 's': a['s'], 'g': a['g']} for a in ours],
                    'issue': {'n': iss['n'], 'on': iss['on'], 's': iss.get('s'), 'g': iss.get('g'), 't': iss['t']} if iss else None,
                    'talk': [{'n': x['n'], 't': x['t'], 'nsite': x['nsite']} for x in tks],
                    'stocks': [{'id': s['id'], 'name': s['name'], 'up': s['up'], 'down': s['down']} for s in stocks],
                    'coins': [{'sym': c['sym'], 'name': c['name']} for c in coins], 'pr': pr})
        db[sl] = rec
        if sl not in [a['slug'] for a in arch]:
            arch.append({'slug': sl, 'k': k, 'traffic': it['traffic'], 'first': now.strftime('%H:%M'), 'src': it.get('src', ['google'])})
        else:
            for a_ in arch:
                if a_['slug'] == sl:
                    a_['src'] = sorted(set(a_.get('src', ['google'])) | set(it.get('src', []))); a_['traffic'] = it['traffic']
        kept += 1
    os.makedirs(ARCH, exist_ok=True)
    json.dump(db, open(DBF, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    arch.sort(key=lambda a: -len(a.get('src', [])))  # 구글+네이버 동시 키워드를 위로
    json.dump(arch, open(arch_f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('트렌드', len(items), '게시', kept, '오늘 누적', len(arch))


if __name__ == '__main__':
    main()
