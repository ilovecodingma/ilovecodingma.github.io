# -*- coding: utf-8 -*-
"""건강 레시피 분류 — 영양 수치 없이 재료·조리법·기존 태그로만 나눈다(2026-10-26).
수치(kcal·g)는 공식 DB 값이 들어오기 전까지 쓰지 않는다. 문구는 「재료상 ~한 편」 수준으로 제한한다.
"""
import re

PROTEIN = ('달걀', '계란', '두부', '순두부', '닭', '소고기', '돼지고기', '참치', '고등어', '오징어', '새우', '생선', '연어', '콩', '멸치', '명란', '조개', '바지락')
VEG = ('양파', '대파', '당근', '애호박', '양배추', '콩나물', '숙주', '시금치', '버섯', '무', '깻잎', '오이', '토마토', '상추', '부추', '브로콜리', '파프리카', '가지', '배추', '미역', '나물')
OIL_STEP = re.compile(r'식용유|기름을? 두르|튀기|튀김|부쳐|부치|버터|마요네즈')
OIL_NAME = re.compile(r'튀김|전$|부침|까스|돈가스|탕수|볶음밥|마요')

GOALS = [
    # slug, 아이콘, 이름, 한 줄, 고르는 기준(사용자에게 그대로 보여 줌)
    ('light', '🥗', '가볍게 먹기', '속이 편한 가벼운 한 끼', '메뉴 분류가 「가벼움」이고, 튀기거나 기름을 많이 쓰는 조리가 아닌 메뉴만 골랐어요.'),
    ('protein', '💪', '단백질 챙기기', '달걀·두부·고기·생선이 들어간 메뉴', '꼭 필요한 재료에 달걀·두부·닭고기·생선·콩 같은 단백질 재료가 들어간 메뉴예요. 양이나 영양 수치는 적지 않았어요.'),
    ('veggie', '🥬', '채소 듬뿍', '채소가 두 가지 이상 들어간 메뉴', '재료에 채소·버섯·해조류가 두 가지 이상 들어가거나 무침·나물·샐러드류인 메뉴예요.'),
    ('lowoil', '🫕', '기름 적게', '삶기·끓이기·찌기·무치기 위주', '조리 과정에 식용유·튀김·부침이 나오지 않는 메뉴를 골랐어요. 참기름 한두 방울 정도는 포함돼요.'),
    ('full', '🍚', '든든하게', '한 끼로 배부른 메뉴', '메뉴 분류가 「든든」인 메뉴 중 채소나 단백질 재료가 함께 들어간 것만 골랐어요.'),
    ('night', '🌙', '야식 말고 가볍게', '15분 안에 끝나는 부담 적은 메뉴', '15분 안에 끝나고 「가벼움」으로 분류된, 튀기지 않는 메뉴예요.'),
]
G = {g[0]: g for g in GOALS}


def _isveg(x):
    return any(x == w or x.startswith(w) or x.endswith(w) for w in VEG)


PROCESSED = ('라면', '스팸', '햄', '소시지', '베이컨', '맛살', '어묵', '참치캔')


def processed(r):
    return any(any(p in x for p in PROCESSED) for x in r.get('need', [])) or '라면' in r['n']


def _has(words, ing):
    return any(any(w in x for w in words) for x in ing)


def feats(r):
    ing = list(r.get('need', [])) + list(r.get('opt', []))
    nd = list(r.get('need', []))
    steps = ' '.join(r.get('s', []))
    t = r.get('t', [])
    oil = bool(OIL_STEP.search(steps)) or bool(OIL_NAME.search(r['n']))
    nveg = sum(1 for x in nd if _isveg(x))
    return dict(
        protein=_has(PROTEIN, nd), veggie=nveg >= 2 or bool(re.search(r'무침|나물|샐러드|겉절이|생채', r['n'])),
        oil=oil, light='가벼움' in t, full='든든' in t, quick=r['m'] <= 15,
    )


def goals_of(r):
    f = feats(r); out = []
    if processed(r):
        return ['protein'] if f['protein'] and not f['oil'] else []
    if f['light'] and not f['oil']: out.append('light')
    if f['protein']: out.append('protein')
    if f['veggie']: out.append('veggie')
    if not f['oil']: out.append('lowoil')
    if f['full'] and (f['protein'] or f['veggie']): out.append('full')
    if f['light'] and f['quick'] and not f['oil']: out.append('night')
    return out


def groups(RS):
    out = {k: [] for k, *_ in GOALS}
    for r in RS:
        for g in goals_of(r):
            out[g].append(r)
    for k in out:
        out[k].sort(key=lambda x: (x['m'], len(x['need']), x['n']))
    return out


def points(r):
    """레시피 상세용 「건강 포인트」 문장(수치 없음). 재료·조리법에서 확인되는 것만 적는다."""
    f = feats(r); pts = []
    ing = [x for x in r['need'] if any(w in x for w in PROTEIN)]
    if ing: pts.append(f'단백질 재료({", ".join(ing[:3])})가 들어가요.')
    veg = [x for x in r['need'] if _isveg(x)]
    if veg: pts.append(f'채소·버섯류({", ".join(dict.fromkeys(veg))[:40]})를 함께 먹을 수 있어요.')
    if not f['oil']: pts.append('조리 과정에 튀기거나 기름을 많이 쓰는 단계가 없어요.')
    if re.search(r'국$|국 |찌개|탕|전골|국밥', r['n']): pts.append('국물 요리는 간을 약하게 하고 건더기 위주로 먹으면 나트륨을 줄이는 데 도움이 돼요.')
    if re.search(r'햄|스팸|소시지|베이컨|어묵|맛살|라면|김치', ' '.join(r['need'])): pts.append('가공식품·김치가 들어가 짠 편일 수 있어요. 간장·소금은 맛을 보며 조금씩 넣으세요.')
    if f['oil']: pts.append('기름을 쓰는 조리라 먹는 양은 한 접시 기준으로 잡고, 채소 반찬을 곁들이면 균형이 좋아요.')
    return pts[:4]
