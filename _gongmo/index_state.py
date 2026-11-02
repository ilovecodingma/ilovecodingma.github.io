# -*- coding: utf-8 -*-
"""사이트맵의 /money/ 주소 전체를 서치 콘솔 URL 검사 API 로 조회해 색인 여부를 _gongmo/index_state.json 에 저장한다(읽기 전용).
홈에서 아직 색인 안 된 가이드를 번갈아 링크하는 데 쓴다(2026-11-02). 하루 한도(2,000건)가 있어 한 번에 최대 --n 건만 돌고, 오래된 조회부터 다시 한다.
사용: python -X utf8 index_state.py [--n 400] [--prefix /money/]"""
import os, re, sys, json, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from gsc import session, PROP
F = os.path.join(HERE, 'index_state.json')


def main():
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 400
    prefix = sys.argv[sys.argv.index('--prefix') + 1] if '--prefix' in sys.argv else '/money/'
    urls = []
    for fn in os.listdir(ROOT):
        if fn.startswith('sitemap-') and fn.endswith('.xml'):
            urls += [u for u in re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, fn), encoding='utf-8').read())
                     if u.replace('https://sungprofile.cloud', '').startswith(prefix)]
    old = json.load(open(F, encoding='utf-8')) if os.path.exists(F) else {}
    st = old.get('urls', {})
    todo = sorted(urls, key=lambda u: st.get(u, {}).get('at', ''))[:n]   # 한 번도 안 본 주소 → 오래된 순
    S = session(); done = err = 0
    for u in todo:
        try:
            r = S.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect', json={'inspectionUrl': u, 'siteUrl': PROP}, timeout=40)
            if r.status_code != 200:
                err += 1
                if r.status_code == 429:
                    break
                continue
            ix = r.json().get('inspectionResult', {}).get('indexStatusResult', {})
            st[u] = {'state': ix.get('coverageState') or ix.get('verdict') or '알 수 없음', 'indexed': 'indexed' in (ix.get('coverageState') or '').lower() and 'not indexed' not in (ix.get('coverageState') or '').lower(),
                     'crawl': ix.get('lastCrawlTime', ''), 'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
            done += 1
        except Exception:
            err += 1
        time.sleep(0.35)
    st = {u: v for u, v in st.items() if u in set(urls)}
    out = {'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'prefix': prefix, 'total': len(urls), 'checked': len(st),
           'indexed': sum(1 for v in st.values() if v['indexed']), 'urls': st}
    json.dump(out, open(F, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=1)
    print(f'조회 {done} 오류 {err} / 전체 {len(urls)} 중 기록 {len(st)}, 색인됨 {out["indexed"]}')


if __name__ == '__main__':
    main()
