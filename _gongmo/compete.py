# -*- coding: utf-8 -*-
"""경쟁 지표 수집 (2026-10-19 사용자 「조회수 기반 실제 경쟁률 등도 확인하는 형식」·연구 세션 A·B·C 안). 하루 1번, 쌓기만 한다(화면은 7일치 이상부터).
C) 관심도 원자료:
  ① 공개 조회수·스크랩: 링커리어 상세(공개 표시값, robots 허용). 콘테스트코리아는 조회수를 HTML 주석으로 숨겨 둬서 수집하지 않음. 위비티·씽굿·올콘은 조회수 미표시.
  ② 공고 원문의 「오늘 N명이 응모하러 갔어요」(모음 사이트 표시값)
  ③ 우리 D1: 상세 조회 방문자·찜·준비하기 누적
A) 실제 응모 수: news.py 가 기사 본문을 읽을 때 「총 N편/건/명 접수·응모·출품」 문장을 compete/appl.jsonl 에 쌓는다(본문은 저장하지 않음, 문장 120자만).
결과: _gongmo/compete/daily.jsonl (한 줄 = 날짜·공모전·지표). 실행: python compete.py [--force]"""
import datetime, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
D = os.path.join(HERE, 'compete'); os.makedirs(D, exist_ok=True)
OUT = os.path.join(D, 'daily.jsonl')
KST = datetime.timezone(datetime.timedelta(hours=9))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'}
MASTER = r'C:\Users\k\Desktop\공모전_2026\data\master.jsonl'
APPL = re.compile(r'(?:총|모두|역대 최다인?|역대 최대)\s*([\d,]{2,7})\s*(여\s*)?(편|건|명|팀|점)(?:의)?\s*(?:작품[이가]?\s*)?(?:이|가)?\s*(?:접수|응모|출품)(?:되|했|하|돼|됐|해|된)')


def linkareer(u):
    m = re.search(r'/activity/(\d+)', u)
    if not m:
        return None
    r = requests.get(u, headers=UA, timeout=20)
    t = r.text; i = t.find(f'"Activity:{m.group(1)}"')
    if i < 0:
        return None
    seg = t[i:i + 20000]
    v = re.search(r'"viewCount":(\d+)', seg); s = re.search(r'"scrapCount":(\d+)', seg)
    return {'views': int(v.group(1)) if v else None, 'scraps': int(s.group(1)) if s else None, 'src': 'linkareer'}


def today_goers(cid):
    f = os.path.join(HERE, 'txt', f'{cid}.txt')
    if not os.path.exists(f):
        return None
    m = re.search(r'오늘\s*([\d,]+)\s*명이\s*응모하러\s*갔어요', open(f, encoding='utf-8', errors='ignore').read())
    return int(m.group(1).replace(',', '')) if m else None


def appl_sentences(title, body, url, ts):
    """news.py 가 부름: 기사 본문에서 응모 수 문장만 뽑아 쌓기(본문 저장 안 함)."""
    if not body or not re.search(r'공모전|공모|백일장|경진대회|콘테스트|신춘문예', title + body[:2000]):
        return 0
    n = 0
    with open(os.path.join(D, 'appl.jsonl'), 'a', encoding='utf-8') as f:
        for m in APPL.finditer(body):
            k = int(m.group(1).replace(',', ''))
            if 10 <= k <= 500000:
                s = body[max(0, m.start() - 60):m.end() + 40].replace('\n', ' ')
                f.write(json.dumps({'ts': ts, 't': title[:100], 'u': url, 'n': k, 'unit': m.group(3), 'approx': bool(m.group(2)), 's': s[:160]}, ensure_ascii=False) + '\n'); n += 1
    return n


def ours():
    """우리 D1: 공모전별 상세 조회 방문자(누적)·찜·준비하기."""
    sys.path.insert(0, HERE)
    import push
    v = {r['p'][3:-1]: r['v'] for r in push.q("SELECT p, COUNT(DISTINCT vid) v FROM hits WHERE p LIKE '/c/%' GROUP BY p")}
    fav = {r['i'][2:]: r['n'] for r in push.q("SELECT item_id i, COUNT(*) n FROM user_items WHERE item_id LIKE 'c:%' AND fav = 1 GROUP BY item_id")}
    prep = {r['i'][2:]: r['n'] for r in push.q("SELECT item_id i, COUNT(*) n FROM prep WHERE item_id LIKE 'c:%' GROUP BY item_id")}
    return v, fav, prep


def main(force=False):
    day = datetime.datetime.now(KST).date().isoformat()
    if not force and os.path.exists(OUT) and any(json.loads(l).get('d') == day for l in open(OUT, encoding='utf-8') if l.strip()):
        return 0
    live = json.load(open(os.path.join(ROOT, 'data.json'), encoding='utf-8'))['items']
    rows = {json.loads(l)['id']: json.loads(l) for l in open(MASTER, encoding='utf-8') if l.strip()}
    try:
        v, fav, prep = ours()
    except Exception as e:
        print('D1 실패', repr(e)[:80]); v, fav, prep = {}, {}, {}
    n = 0
    with open(OUT, 'a', encoding='utf-8') as f:
        for c in live:
            u = (rows.get(c['id']) or {}).get('url') or ''
            rec = {'d': day, 'id': c['id'], 'site_v': v.get(c['id'], 0), 'fav': fav.get(c['id'], 0), 'prep': prep.get(c['id'], 0), 'goers': today_goers(c['id'])}
            if 'linkareer.com' in u:
                try:
                    x = linkareer(u); time.sleep(2)
                    if x:
                        rec.update(x)
                except Exception as e:
                    rec['err'] = repr(e)[:60]
            f.write(json.dumps(rec, ensure_ascii=False) + '\n'); n += 1
    print('경쟁 지표 수집', day, n, '건')
    return n


if __name__ == '__main__':
    main('--force' in sys.argv)
