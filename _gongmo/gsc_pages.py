# -*- coding: utf-8 -*-
"""서치콘솔 「페이지」 색인 점검 (2026-10-20 홍보 세션 요청: 색인 수와 미색인 사유 상위 3개를 주 1회).
서치콘솔 「페이지」 보고서 자체는 API 로 안 나와서, 사이트맵 주소를 분야별로 골라(약 120개) URL 검사 API 로 한 건씩 조회해 집계한다 — 전체 숫자가 아니라 표본이에요.
쓰기 없음(읽기만). 키 ~/.gsc_sa.json. 결과 _gongmo/gsc_pages.json (이력은 history 에 누적).
사용: python gsc_pages.py [--n 120]"""
import os, re, sys, json, time, random, datetime, urllib.parse, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from gsc import session, PROP
F = os.path.join(HERE, 'gsc_pages.json')


def sitemap_urls():
    urls = collections.defaultdict(list)
    for fn in os.listdir(ROOT):
        if fn.startswith('sitemap-') and fn.endswith('.xml'):
            cat = fn[8:-4]
            for u in re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, fn), encoding='utf-8').read()):
                urls[cat].append(u)
    return urls


def main():
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 120
    S = session()
    U = sitemap_urls()
    allu = sum(len(v) for v in U.values())
    rnd = random.Random(datetime.date.today().isocalendar()[1])
    pick = []
    for cat, L in U.items():   # 분야별 비율대로 최소 3개씩
        k = max(3, round(n * len(L) / max(allu, 1)))
        pick += rnd.sample(L, min(k, len(L)))
    pick = pick[:n]
    tally, reasons, errs = collections.Counter(), collections.Counter(), 0
    for u in pick:
        try:
            r = S.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect', json={'inspectionUrl': u, 'siteUrl': PROP}, timeout=40)
            if r.status_code != 200:
                errs += 1
                continue
            ix = r.json().get('inspectionResult', {}).get('indexStatusResult', {})
            st = ix.get('coverageState') or ix.get('verdict') or '알 수 없음'
            tally[st] += 1
            if not re.search(r'indexed$|색인이 생성됨', st) or 'not indexed' in st.lower():
                reasons[st] += 1
        except Exception:
            errs += 1
        time.sleep(0.4)
    done = sum(tally.values())
    indexed = sum(v for k, v in tally.items() if re.search(r'^Submitted and indexed|^Indexed|색인이 생성', k))
    out = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'sample': done, 'errors': errs, 'sitemap_urls': allu, 'indexed_in_sample': indexed,
           'indexed_pct': round(indexed / done * 100, 1) if done else None, 'states': tally.most_common(), 'top3_not_indexed': reasons.most_common(3),
           'note': '표본(사이트맵 주소를 분야별로 약 %d개 골라 URL 검사)이라 서치콘솔 「페이지」 보고서의 전체 숫자와 달라요.' % n}
    old = json.load(open(F, encoding='utf-8')) if os.path.exists(F) else {}
    hist = (old.get('history') or []) + [{'at': out['at'], 'indexed_pct': out['indexed_pct'], 'sample': done}]
    out['history'] = hist[-30:]
    json.dump(out, open(F, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'history'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
