# -*- coding: utf-8 -*-
"""오늘 날씨에 어울리는 메뉴 (2026-10-19 음식 추천 고도화). Open-Meteo(무료·키 없음)로 서울 오늘 기온·비 → 분류 → 레시피 3개.
결과 assets/fridge/today.json — 냉장고 화면 맨 위 「오늘 날씨 메뉴 3개」와 추천 가산점, 홍보 세션 블로그 주제로 씀. 실패하면 이전 파일 유지."""
import datetime, json, os, re
import requests

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets', 'fridge', 'today.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
SEASON = {1: ['무', '배추', '시금치', '굴'], 2: ['시금치', '무', '대파'], 3: ['부추', '달래', '냉이', '쪽파'], 4: ['부추', '양배추', '쑥'], 5: ['양파', '감자', '오이'], 6: ['감자', '애호박', '오이', '토마토'],
          7: ['애호박', '가지', '오이', '토마토', '고추'], 8: ['가지', '토마토', '고추', '옥수수'], 9: ['버섯', '고구마', '배'], 10: ['고구마', '버섯', '무', '배추', '대파'], 11: ['무', '배추', '대파', '고구마'], 12: ['무', '배추', '시금치']}
DAYS = {'12-22': ('동지', r'팥|죽'), '01-01': ('새해', r'떡국|만둣국'), '07-15': ('초복 무렵', r'닭|삼계'), '08-15': ('말복 무렵', r'닭|삼계')}


def cat(n):
    return ('국물' if re.search(r'국|찌개|탕|전골|국밥|수프', n) else '면' if re.search(r'국수|면|파스타|라면|우동|스파게티|라볶이|잡채', n) else '전' if re.search(r'전$|전 |부침|땡', n)
            else '밥' if re.search(r'밥|덮밥|김밥|리조또|오므라이스|동$', n) else '볶음' if '볶음' in n else '조림' if re.search(r'조림|찜', n) else '반찬' if re.search(r'무침|나물|샐러드|겉절이|생채', n) else '기타')


def main():
    now = datetime.datetime.now(KST)
    try:
        r = requests.get('https://api.open-meteo.com/v1/forecast', params={'latitude': 37.5665, 'longitude': 126.978, 'current': 'temperature_2m,precipitation,rain,weather_code',
                         'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max', 'timezone': 'Asia/Seoul', 'forecast_days': 1}, timeout=20).json()
        cu, dl = r['current'], r['daily']
        t, tmax, tmin = cu['temperature_2m'], dl['temperature_2m_max'][0], dl['temperature_2m_min'][0]
        rain = (cu.get('precipitation') or 0) > 0 or (dl['precipitation_probability_max'][0] or 0) >= 60
    except Exception as e:
        print('날씨 실패', repr(e)[:80]); return None
    R = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'recipes.json'), encoding='utf-8'))['recipes']
    if rain:
        lab, want, why = 'rainy', {'국물': 3, '전': 3}, f'비 오는 날(강수 확률 {dl["precipitation_probability_max"][0]}%)엔 국물이나 전'
    elif tmax >= 27:
        lab, want, why = 'hot', {'면': 2, '반찬': 2, '밥': 1}, f'최고 {tmax:.0f}도 더운 날엔 시원한 면·비빔'
    elif tmax <= 12 or t <= 8:
        lab, want, why = 'cold', {'국물': 3, '조림': 1}, f'최고 {tmax:.0f}도 쌀쌀한 날엔 뜨끈한 국물'
    elif tmax - tmin >= 10:
        lab, want, why = 'gap', {'국물': 2, '밥': 1}, f'일교차 {tmax - tmin:.0f}도라 저녁엔 따뜻한 국'
    else:
        lab, want, why = 'mild', {'볶음': 1, '밥': 1, '조림': 1}, f'최고 {tmax:.0f}도 선선한 날엔 든든한 한 끼'
    sea = SEASON[now.month]
    dd = DAYS.get(now.strftime('%m-%d'))
    def sc(x):
        s = want.get(cat(x['n']), 0) + sum(0.5 for i in x['need'] + x['opt'] if i in sea) + (1 if '든든' in x['t'] else 0)
        if dd and re.search(dd[1], x['n']):
            s += 4
        return s + int(__import__('hashlib').md5((x['n'] + now.strftime('%Y%m%d')).encode()).hexdigest()[:4], 16) / 262144   # 같은 점수면 날마다 다르게(재현 가능)
    picks = sorted(R, key=sc, reverse=True)
    top, cats = [], set()
    for x in picks:   # 3개는 종류가 겹치지 않게
        if cat(x['n']) in cats and len(cats) < 3:
            continue
        top.append(x['n']); cats.add(cat(x['n']))
        if len(top) == 3:
            break
    out = {'at': now.strftime('%Y-%m-%d %H:%M'), 'place': '서울', 't': t, 'tmax': tmax, 'tmin': tmin, 'rain': rain, 'label': lab, 'why': why, 'want': want, 'season': sea,
           'day': dd[0] if dd else '', 'picks': top}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return out


if __name__ == '__main__':
    print(main())
