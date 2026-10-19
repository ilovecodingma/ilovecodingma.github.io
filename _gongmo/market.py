# 공개 시세 (2026-10-20 사용자 「전문가 말 vs 시세 흐름」). 하루 1번만 받아 market.json 에 둔다(매시 빌드는 캐시만 읽음).
# 출처: FRED 공개 CSV(robots.txt 「User-agent: *」 허용, 미국 지수·환율·유가·미 국채 금리), 업비트 공개 API(비트코인 원화).
# 코스피·국고채·반도체 지수는 무료·허용 출처를 아직 연결하지 못함(한국은행 ECOS 는 인증키 필요) → 그 주제는 발언 타임라인만.
import csv, datetime, io, json, os
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'market.json')
FRED = {'sp500': ('SP500', 'S&P 500', 'pt'), 'nasdaq': ('NASDAQCOM', '나스닥 종합', 'pt'), 'usdkrw': ('DEXKOUS', '원/달러 환율', '원'),
        'wti': ('DCOILWTICO', 'WTI 국제유가', '달러'), 'us10y': ('DGS10', '미국 국채 10년 금리', '%')}
SRC = {'sp500': 'FRED(S&P Dow Jones Indices)', 'nasdaq': 'FRED(Nasdaq OMX)', 'usdkrw': 'FRED(미 연준 H.10)', 'wti': 'FRED(미 에너지정보청)',
       'us10y': 'FRED(미 연준 H.15)', 'btc': '업비트 공개 API'}


def _fred(sid):
    r = requests.get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}', timeout=30, headers={'User-Agent': 'jupjup-market/1.0 (+https://sungprofile.cloud)'})
    r.raise_for_status()
    cut = (datetime.date.today() - datetime.timedelta(days=120)).isoformat()
    out = []
    for row in csv.reader(io.StringIO(r.text)):
        if len(row) == 2 and row[0] >= cut and row[1] not in ('', '.') and row[0][:1].isdigit():
            out.append([row[0], float(row[1])])
    return out


def _btc():
    r = requests.get('https://api.upbit.com/v1/candles/days', params={'market': 'KRW-BTC', 'count': 120}, timeout=20).json()
    return sorted([[x['candle_date_time_kst'][:10], float(x['trade_price'])] for x in r])


def load(force=False):
    """오늘 받은 게 있으면 그대로, 없으면 받는다. 받기 실패한 지표는 어제 값 유지."""
    old = json.load(open(F, encoding='utf-8')) if os.path.exists(F) else {}
    today = datetime.date.today().isoformat()
    if old.get('d') == today and not force:
        return old
    S = dict(old.get('s') or {})
    for k, (sid, nm, unit) in FRED.items():
        try:
            pts = _fred(sid)
            if pts:
                S[k] = {'name': nm, 'unit': unit, 'src': SRC[k], 'pts': pts}
        except Exception as e:
            print('시세 받기 실패', k, e)
    try:
        S['btc'] = {'name': '비트코인(원화)', 'unit': '원', 'src': SRC['btc'], 'pts': _btc()}
    except Exception as e:
        print('시세 받기 실패 btc', e)
    out = {'d': today, 'at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 's': S}
    json.dump(out, open(F, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return out


def val_at(s, d):
    """d(YYYY-MM-DD) 당일 또는 그 전 마지막 거래일 값."""
    v = None
    for x, y in s['pts']:
        if x > d:
            break
        v = (x, y)
    return v


def chg(s, d0, days):
    """d0 기준값 → d0+days 이후 첫 값까지 등락률(%). 아직 그 날이 안 왔으면 None."""
    a = val_at(s, d0)
    t = (datetime.date.fromisoformat(d0) + datetime.timedelta(days=days)).isoformat()
    if not a or s['pts'][-1][0] < t:
        return None
    b = next((y for x, y in s['pts'] if x >= t), None)
    return None if b is None else (b / a[1] - 1) * 100


def last_chg(s, days=7):
    """가장 최근 값과 days 일 전 값의 등락률(%)."""
    if not s['pts']:
        return None
    d1, v1 = s['pts'][-1]
    a = val_at(s, (datetime.date.fromisoformat(d1) - datetime.timedelta(days=days)).isoformat())
    return None if not a else (v1 / a[1] - 1) * 100


if __name__ == '__main__':
    m = load(force=True)
    for k, v in m['s'].items():
        print(k, len(v['pts']), v['pts'][-1])
