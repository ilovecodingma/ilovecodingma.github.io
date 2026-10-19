# -*- coding: utf-8 -*-
"""구글 서치 콘솔 연동 (2026-10-19 연구 세션 요청 · SEO 지침 Phase 4). 서비스 계정 키 ~/.gsc_sa.json (저장소 밖).
하루 1번: ① sitemap_index.xml 재제출 ② 최근 7일 검색어·페이지별 노출·클릭 + 사이트맵 제출·색인 수 → _gongmo/gsc_daily.json, 관리 화면용 요약 admin/gsc.json
Indexing API(urlNotifications)는 쓰지 않는다 — 구글 정책상 JobPosting·BroadcastEvent 페이지 전용이라 공모전·레시피 주소에는 지침 위반.
실행: python gsc.py [--force]"""
import datetime, json, os, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KEY = os.path.expanduser('~/.gsc_sa.json')
PROP = 'https://sungprofile.cloud/'
STATE = os.path.join(HERE, 'gsc_state.json')
KST = datetime.timezone(datetime.timedelta(hours=9))


def session():
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    cr = service_account.Credentials.from_service_account_file(KEY, scopes=['https://www.googleapis.com/auth/webmasters'])
    return AuthorizedSession(cr)


def main(force=False):
    today = datetime.datetime.now(KST).date().isoformat()
    st = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    if st.get('day') == today and not force:
        return st
    if not os.path.exists(KEY):
        print('gsc: 키 없음', KEY); return {}
    S = session(); P = urllib.parse.quote(PROP, safe='')
    B = f'https://www.googleapis.com/webmasters/v3/sites/{P}'
    res = {'day': today, 'at': datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M')}
    r = S.put(f'{B}/sitemaps/' + urllib.parse.quote(PROP + 'sitemap_index.xml', safe=''), timeout=30)
    res['sitemap_put'] = r.status_code
    sm = S.get(f'{B}/sitemaps', timeout=30)
    res['sitemaps'] = [{'path': x.get('path'), 'submitted': x.get('lastSubmitted'), 'downloaded': x.get('lastDownloaded'), 'errors': x.get('errors'), 'warnings': x.get('warnings'),
                        'contents': x.get('contents')} for x in (sm.json().get('sitemap') or [])] if sm.ok else sm.status_code
    end = (datetime.date.fromisoformat(today) - datetime.timedelta(days=2)).isoformat()   # 서치 콘솔 데이터는 2~3일 늦음
    start = (datetime.date.fromisoformat(end) - datetime.timedelta(days=6)).isoformat()
    def q(dims, n):
        r = S.post(f'{B}/searchAnalytics/query', json={'startDate': start, 'endDate': end, 'dimensions': dims, 'rowLimit': n}, timeout=60)
        return [{**{d: k for d, k in zip(dims, x['keys'])}, 'clicks': x['clicks'], 'impr': x['impressions'], 'ctr': round(x['ctr'] * 100, 1), 'pos': round(x['position'], 1)} for x in r.json().get('rows', [])] if r.ok else r.status_code
    res['range'] = [start, end]
    res['queries'] = q(['query'], 200)
    res['pages'] = q(['page'], 200)
    res['qp'] = q(['query', 'page'], 300)
    json.dump(res, open(os.path.join(HERE, 'gsc_daily.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 관리 화면용 요약 (공개 경로지만 검색 제외 /admin/): 검색어 상위·11~20위 검색어·노출 많고 클릭 적은 페이지
    Q = res['queries'] if isinstance(res['queries'], list) else []
    Pg = res['pages'] if isinstance(res['pages'], list) else []
    summ = {'at': res['at'], 'range': res['range'], 'sitemap_put': res['sitemap_put'],
            'sitemaps': res['sitemaps'] if isinstance(res['sitemaps'], list) else [],
            'top': sorted(Q, key=lambda x: -x['impr'])[:30], 'near': [x for x in Q if 10 < x['pos'] <= 20][:30],
            'lowctr': sorted([x for x in Pg if x['impr'] >= 20 and x['ctr'] < 2], key=lambda x: -x['impr'])[:30]}
    os.makedirs(os.path.join(ROOT, 'admin'), exist_ok=True)
    json.dump(summ, open(os.path.join(ROOT, 'admin', 'gsc.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    st = {'day': today, 'sitemap_put': res['sitemap_put'], 'queries': len(Q), 'pages': len(Pg)}
    json.dump(st, open(STATE, 'w', encoding='utf-8'))
    print('gsc', st)
    return st


if __name__ == '__main__':
    main('--force' in sys.argv)
