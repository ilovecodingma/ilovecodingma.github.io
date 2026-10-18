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
EXCL = re.compile(r'열애|결별|이혼|불륜|사생활|폭로|스캔들|성폭|성추행|몰카|음란|자살|살인|살해|숨져|숨진|사망|변사|흉기|참사|추락|실종|부상자|피해자|폭행|학대|마약|음주운전')


def slug(k):
    s = re.sub(r'[\s/?#%&+]+', '-', k.strip()).strip('-')
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


def main():
    now = datetime.datetime.now(KST)
    today = now.date().isoformat()
    items = fetch()
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
        ours = [a for a in nw.get('items', []) if kre.search(a['t'].replace(' ', ''))][:8]
        iss = next((x for x in nw.get('issues', []) if kre.search(x['t'].replace(' ', ''))), None)
        tks = [x for x in tk.get('issues', []) if kre.search((x['t'] + ' '.join(x.get('kw', []))).replace(' ', ''))][:3]
        stocks = [s for s in an.get('stocks', []) if s['name'] in k or k in s['name'] or any(s['name'] in n['t'] for n in it['news'][:3])][:3]
        coins = [c for c in an.get('coins', []) if c['name'] in k or c['sym'] == k.upper()][:2]
        pr = NW.promos({'t': k + ' ' + ' '.join(n['t'] for n in it['news'][:3]), 'd': ''}, C, A, today)
        srcs = sorted({n['o'] for n in it['news'] if n['o']} | {a['o'] for a in ours})
        rec = db.get(sl, {'k': k, 'slug': sl, 'days': []})
        if today not in rec['days']:
            rec['days'].append(today)
        rec.update({'k': k, 'traffic': it['traffic'], 'ts': it['ts'], 'updated': now.strftime('%Y-%m-%d %H:%M'), 'news': it['news'][:6], 'srcs': srcs,
                    'ours': [{'t': a['t'], 'o': a['o'], 'u': a['u'], 's': a['s'], 'g': a['g']} for a in ours],
                    'issue': {'n': iss['n'], 'on': iss['on'], 's': iss.get('s'), 'g': iss.get('g'), 't': iss['t']} if iss else None,
                    'talk': [{'n': x['n'], 't': x['t'], 'nsite': x['nsite']} for x in tks],
                    'stocks': [{'id': s['id'], 'name': s['name'], 'up': s['up'], 'down': s['down']} for s in stocks],
                    'coins': [{'sym': c['sym'], 'name': c['name']} for c in coins], 'pr': pr})
        db[sl] = rec
        if sl not in [a['slug'] for a in arch]:
            arch.append({'slug': sl, 'k': k, 'traffic': it['traffic'], 'first': now.strftime('%H:%M')})
        kept += 1
    os.makedirs(ARCH, exist_ok=True)
    json.dump(db, open(DBF, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    json.dump(arch, open(arch_f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('트렌드', len(items), '게시', kept, '오늘 누적', len(arch))


if __name__ == '__main__':
    main()
