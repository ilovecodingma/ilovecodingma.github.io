# 인기 키워드 놀이판 (2026-10-20 사용자 「뉴스는 재미없고 키워드 쪽을 재밌게」) — /kw/ 맨 위에 붙는 구름·1위 카드·뱃지·스파크라인·퀴즈·내일 예측 투표·TOP5 카드.
# 원칙: 데이터에 있는 것만(시간·검색량 구간·기사 제목) 쓰고, 순위 흐름은 kw.py 가 매시 쌓는 kw/hist.json 이 생긴 뒤부터(그 전엔 「기록 시작」 안내).
import datetime, hashlib, html, json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = lambda s: html.escape(html.unescape(html.unescape(str(s))), quote=True)   # 수집 제목에 &quot; 가 이미 들어 있는 경우
HAN = re.compile(r'[가-힣]')
POL = re.compile(r'대통령|국회|의원|정당|여당|야당|장관|총리|청와대|탄핵|선거|공천|검찰|특검|북한|김정은|김여정|트럼프|시진핑|국민의힘|민주당|혁신당|정권|국정|외교|안보|전쟁|공습|미사일|대남|확성기|해킹|책임')
STY = {'google': ('#2563eb', '구글'), 'naver': ('#16a34a', '시그널'), 'both': ('#9333ea', '동시')}
BAD = re.compile(r'외도|불륜|이혼|열애|결별|폭로|사망|숨져|논란|사과|남편|아내|성폭|운세|궁합|토토|도박|먹튀')   # 놀이판 후보에서 뺄 가십·민감 키워드
WRONG = ['「{k}」 관련 신제품이 오늘 출시돼서', '「{k}」 이름이 들어간 행사 일정이 갑자기 바뀌어서', '포털 첫 화면 추천에 「{k}」 코너가 생겨서', '어젯밤 방송에서 「{k}」 이야기가 나와서', '「{k}」 관련 정부 발표가 있어서']   # 규칙표로 만든 오답 보기


def score(tr):
    """검색량 구간(‘500+’)과 실시간 순위(‘실시간 3위’)를 합친 상대 인기도."""
    s = 0
    m = re.search(r'(\d+)\+', tr or '')
    if m:
        s += int(m.group(1))
    m = re.search(r'실시간\s*(\d+)위', tr or '')
    if m:
        s += (11 - int(m.group(1))) * 100
    return s


def srckey(src):
    src = src or ['google']
    return 'both' if len(src) > 1 else ('naver' if src == ['naver'] else 'google')


def _t(day, hm):
    return datetime.datetime.strptime(f'{day} {hm}', '%Y-%m-%d %H:%M')


def collect(db, today, arch):
    """오늘 뜬 키워드 목록(점수·처음/마지막 시각·지속 시간·현재 순위권 여부)."""
    mx = max((v.get('updated', '') for v in db.values()), default='')
    first = {a['slug']: a.get('first') for a in arch}
    out = []
    for a in arch:
        r = db.get(a['slug'])
        if not r or today not in r['days']:
            continue
        up = r.get('updated', '')
        f = first.get(a['slug']) or '00:00'
        try:
            span = max((datetime.datetime.strptime(up, '%Y-%m-%d %H:%M') - _t(today, f)).total_seconds() / 3600, 0) if up[:10] == today else 0
        except ValueError:
            span = 0
        out.append({'slug': a['slug'], 'k': r['k'], 'r': r, 'score': score(r.get('traffic')), 'first': f, 'last': up[11:16], 'span': span, 'cur': up == mx,
                    'old': len(r['days']) > 1, 'src': srckey(r.get('src')), 'han': bool(HAN.search(r['k'])), 'pol': bool(POL.search(r['k'] + ' ' + ' '.join(n['t'] for n in r.get('news', [])[:3])) or BAD.search(r['k']) or len(r['k']) > 14 or len(r['k'].split()) > 3)})
    return out, mx


def badges(x, hist):
    b = []
    if x['cur'] and x['first'] >= (datetime.datetime.strptime(x['r']['updated'], '%Y-%m-%d %H:%M') - datetime.timedelta(hours=3)).strftime('%H:%M') and not x['old']:
        b.append(('🆕', '신규'))
    if x['cur'] and (x['score'] >= 1000 or re.search(r'실시간\s*[123]위', x['r'].get('traffic') or '')):
        b.append(('🔥', '급상승'))
    if x['cur'] and (x['span'] >= 6 or x['old']):
        b.append(('⏳', f'{int(x["span"]) + 1}시간째' if x['span'] >= 1 and not x['old'] else '이틀째'))
    h = hist.get(x['slug']) or []
    if x['cur'] and len(h) >= 3 and h[-1][1] <= max(v for _, v in h) - 300:
        b.append(('📉', '하락'))
    if not x['cur'] and int(x['first'][:2]) < 6 and x['last'] and int(x['last'][:2]) <= 8 and not x['old']:
        b.append(('🌙', '새벽에만'))
    return b


def spark(h, color='#2563eb'):
    """시간대별 인기도 흐름(2점 이상 오늘 기록이 있어야 그림)."""
    if len(h) < 3:
        return ''
    W, H = 96, 26
    vs = [v for _, v in h]
    lo, hi = min(vs), max(vs)
    hi = hi if hi > lo else lo + 1
    pts = ' '.join(f'{2 + (W - 4) * i / (len(h) - 1):.1f},{H - 3 - (H - 6) * (v - lo) / (hi - lo):.1f}' for i, (_, v) in enumerate(h))
    return f'<svg class="kwsp" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="오늘 인기도 흐름 {h[0][0]}~{h[-1][0]}"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/></svg>'


def cloud(cur):
    L = sorted([x for x in cur if x['han'] and x['cur'] and not x['pol']], key=lambda x: -x['score'])[:28]
    if not L:
        return ''
    mx = max(x['score'] for x in L) or 1
    sp = ''.join(f'<a href="#k-{E(x["slug"])}" style="font-size:{14 + 22 * (x["score"] / mx) ** .6:.0f}px;color:{STY[x["src"]][0]}">{E(x["k"][:14])}</a>' for x in sorted(L, key=lambda x: x['k']))
    leg = ' '.join(f'<i style="color:{c}">●</i> {n}' for c, n in STY.values())
    return (f'<section class="kwc"><h2>☁️ 지금 키워드 구름</h2><p class="kwcl">{sp}</p>'
            f'<p class="kwn">글자 크기 = 구글 검색량 구간과 시그널 순위로 만든 자체 정렬 점수(검색량 자체가 아님) · 색 = 출처 {leg} · 누르면 아래 카드로 이동해요. 정치·가십 키워드는 구름에서 빼요.</p></section>')


def top1(cur, hist):
    L = sorted([x for x in cur if x['cur'] and x['han'] and not x['pol']], key=lambda x: -x['score'])
    if not L:
        return ''
    x = L[0]
    news = ''.join(f'<li><a href="{E(n["u"])}" target="_blank" rel="noopener nofollow"><em>{E(n["o"])}</em>{E(n["t"])}</a></li>' for n in x['r'].get('news', [])[:3])
    dur = f'{x["first"]}에 처음 떴고 {int(x["span"]) + 1}시간째 순위권' if x['span'] >= 1 else f'{x["first"]}에 처음 떴어요'
    if x['old']:
        dur += ' · 어제도 올랐어요'
    return (f'<section class="kw1"><p class="kwn">🥇 지금 1위 <small>(정치·선거·안보 키워드 제외)</small></p><h2>{E(x["k"])} {"".join(b[0] for b in badges(x, hist))}</h2>'
            f'<p>{E(STY[x["src"]][1])} · {E(x["r"].get("traffic") or "")} · {E(dur)}</p><ul class="kw-l">{news}</ul>'
            f'<p><a class="lab-cta" href="/kw/{E(x["slug"])}/"><b>왜 떴는지 자세히 →</b></a></p></section>')


def fleeting(cur):
    """하루살이(잠깐 떴다 사라진) vs 장수(오래 버틴) 키워드."""
    pool = [x for x in cur if x['han'] and not x['pol']]
    fl = sorted([x for x in pool if not x['cur'] and x['span'] < 1.5 and not x['old']], key=lambda x: -x['score'])[:3]
    lg = sorted([x for x in pool if x['cur'] and (x['span'] >= 3 or x['old'])], key=lambda x: (-x['old'], -x['span']))[:3]
    f = lambda L, e: ''.join(f'<li><a href="#k-{E(x["slug"])}">{e} {E(x["k"][:16])}</a> <small>{x["first"]}~{x["last"] or "-"}{" · 어제도" if x["old"] else ""}</small></li>' for x in L) or '<li><small>아직 없어요</small></li>'
    return (f'<section class="kwc"><h2>🦋 하루살이 vs 🐢 장수 키워드</h2><div class="kw2"><div><h3>🦋 잠깐 떴다 사라졌어요</h3><ul>{f(fl, "🦋")}</ul></div>'
            f'<div><h3>🐢 오래 버티는 중이에요</h3><ul>{f(lg, "🐢")}</ul></div></div><p class="kwn">순위권에 머문 시간은 처음 등장 시각부터 마지막 확인 시각까지예요.</p></section>')


def quiz(cur, today):
    pool = [x for x in cur if x['han'] and not x['pol'] and x['r'].get('news') and len(x['k']) >= 2 and HAN.search(x['r']['news'][0]['o']) and not BAD.search(x['r']['news'][0]['t'])]
    if len(pool) < 3:
        return '', []
    rnd = random.Random(today)
    pick = rnd.sample(pool, 3)
    out = []
    for i, x in enumerate(pick):
        n = x['r']['news'][0]
        others = [y for y in pool if y is not x and y['r'].get('news')]
        w1 = rnd.choice(others)['r']['news'][0]
        w2 = WRONG[int(hashlib.md5((today + x['k']).encode()).hexdigest(), 16) % len(WRONG)].format(k=x['k'])
        U = lambda t: html.unescape(html.unescape(t))
        opts = [{'t': U(n['t']), 'ok': 1, 'o': n['o'], 'u': n['u']}, {'t': U(w1['t']), 'ok': 0}, {'t': w2, 'ok': 0}]
        rnd.shuffle(opts)
        out.append({'k': x['k'], 'opts': opts})
    box = ('<section class="kwc"><h2>🎯 키워드 퀴즈 — 왜 떴을까요?</h2><div id="kwq"><noscript>퀴즈는 자바스크립트가 필요해요.</noscript></div>'
           '<p class="kwn">보기는 오늘 실제 기사 제목 2개와 규칙표로 만든 보기 1개예요. 정답이 되는 기사는 구글 트렌드가 그 키워드에 붙인 기사예요. 정치·안보 키워드는 내지 않아요.</p></section>')
    return box, out


def vote(cur, today, day_f):
    """내일도 남을까? 후보 5개는 오늘 처음 정해지면 그대로 유지(투표가 흔들리지 않게). 어제 후보의 생존 여부는 오늘 키워드 목록으로 확정."""
    store = json.load(open(day_f, encoding='utf-8')) if os.path.exists(day_f) else {}
    pool = sorted([x for x in cur if x['cur'] and x['han'] and not x['pol']], key=lambda x: -x['score'])
    if today not in store and len(pool) >= 5:
        store[today] = [{'slug': x['slug'], 'k': x['k']} for x in pool[:5]]
        for d in sorted(store)[:-7]:
            del store[d]
        json.dump(store, open(day_f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    y = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()
    alive = {x['slug'] for x in cur}
    yd = {'day': y, 'items': [{'slug': c['slug'], 'k': c['k'], 'alive': c['slug'] in alive} for c in store[y]]} if y in store else None
    data = {'day': today, 'cands': store.get(today, []), 'y': yd}
    box = ('<section class="kwc"><h2>🔮 내일도 남을까? 예측 투표</h2><p class="kwn">오늘 떠오른 키워드 5개 중, 내일도 급상승 목록에 남을 것 같은 하나를 골라 보세요. 로그인 없이 하루 한 번이에요.</p>'
           '<div id="kwv"><noscript>투표는 자바스크립트가 필요해요.</noscript></div><div id="kwy"></div></section>') if data['cands'] else \
          '<section class="kwc"><h2>🔮 내일도 남을까? 예측 투표</h2><p class="kwn">후보 키워드가 모이면 투표가 열려요(보통 아침 이후).</p></section>'
    return box, data


def rules_links(x, contests):
    """키워드 → 관련 줍줍 (kw_rules.json 규칙표, 맞는 게 없으면 안 붙임). 로컬 주소는 실제 페이지가 있을 때만."""
    f = os.path.join(HERE, 'kw_rules.json')
    R = json.load(open(f, encoding='utf-8'))['rules'] if os.path.exists(f) else []
    txt = x['k'] + ' ' + ' '.join(n['t'] for n in x['r'].get('news', [])[:3])
    out = []
    for r in R:
        if not re.search(r['kw'], txt):
            continue
        for t, u in r.get('links', []):
            if os.path.exists(os.path.join(ROOT, u.strip('/').replace('/', os.sep), 'index.html')) and (u, t) not in out:
                out.append((u, t))
        if r.get('contest'):
            c = next((c for c in contests if re.search(r['contest'], c['title'])), None)
            if c and (f'/c/{c["id"]}/', c['title']) not in out:
                out.append((f'/c/{c["id"]}/', '🏆 ' + c['title'][:30]))
        if len(out) >= 2:
            break
    return out[:2]


def top5_card(cur, today, nowhm):
    """공유용 TOP5 카드 1200×630 (한글 키워드·정치 제외). 5개 키워드가 바뀔 때만 새로 그림."""
    from PIL import Image, ImageDraw
    import widget as W
    L = sorted([x for x in cur if x['cur'] and x['han'] and not x['pol']], key=lambda x: -x['score'])[:5]
    if len(L) < 3:
        return None
    key = hashlib.md5((today + '|' + '|'.join(x['k'] for x in L)).encode()).hexdigest()[:8]
    d = os.path.join(ROOT, 'assets', 'kw')
    os.makedirs(d, exist_ok=True)
    fn = f'top5-{today.replace("-", "")}-{key}.jpg'
    fp = os.path.join(d, fn)
    if not os.path.exists(fp):
        im = Image.new('RGB', (1200, 630), (248, 250, 252)); dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 1200, 12], fill=(14, 116, 144))
        dr.text((60, 40), '루리의 줍줍 · 오늘의 키워드 TOP5', font=W._font(38, True), fill=(14, 116, 144))
        dr.text((60, 92), f'{today[5:7]}월 {today[8:]}일 {nowhm} 기준 · 구글 트렌드·시그널', font=W._font(26), fill=(100, 116, 139))
        y = 150
        for i, x in enumerate(L, 1):
            dr.rounded_rectangle([60, y, 1140, y + 78], 18, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
            dr.ellipse([76, y + 12, 130, y + 66], fill=(14, 116, 144) if i > 1 else (234, 88, 12))
            dr.text((103 - dr.textlength(str(i), font=W._font(34, True)) / 2, y + 17), str(i), font=W._font(34, True), fill=(255, 255, 255))
            dr.text((156, y + 14), x['k'][:20], font=W._font(46, True), fill=(30, 41, 59))
            tag = STY[x['src']][1]
            dr.text((1120 - dr.textlength(tag, font=W._font(26, True)), y + 26), tag, font=W._font(26, True), fill=tuple(int(STY[x['src']][0][j:j + 2], 16) for j in (1, 3, 5)))
            y += 90
        dr.text((60, 598), 'sungprofile.cloud/kw — 왜 떴는지 보기', font=W._font(26), fill=(100, 116, 139))
        im.save(fp, 'JPEG', quality=82, optimize=True)
    for o in os.listdir(d):
        if o.startswith('top5-') and o != fn:
            os.remove(os.path.join(d, o))
    import shutil
    shutil.copyfile(fp, os.path.join(d, 'top5.jpg'))   # 늘 같은 주소(가장 최근)
    return f'/assets/kw/{fn}', [x['k'] for x in L]


# ---------------------------------------------------------------------------------------------------------------------
# 2026-10-20 사용자 「디자인뿐 아니라 사람들이 관심 가질 만한 걸로」: 키워드 상세에 읽을거리(왜 떴나·궁금한 것·타임라인·생활 영향·과거 사례)
CATS = [('외교·안보', r'북한|김정은|김여정|미사일|외교|전쟁|공습|안보|회담|대남|국경'), ('정치', r'국회|대통령|청문|의원|정당|여당|야당|장관|총리|국감|선거|특검|탄핵'),
        ('날씨', r'날씨|기온|한파|가을비|태풍|미세먼지|weather|서리|단풍|추위'), ('증시·경제', r'증시|주가|코스피|코스닥|나스닥|환율|금리|삼성|하이닉스|삼전|반도체|경제|물가|금값|비트|코인|보험|부동산|대출|etf|vix'),
        ('스포츠', r'축구|야구|농구|배구|골프|리그|경기|토트넘|손흥민|올림픽|감독|선수|트윈스|cwc|vs|대 '), ('연예·방송', r'배우|가수|드라마|예능|컴백|아이돌|방송|콘서트|영화|뮤지컬|걸그룹|보이그룹|개그'),
        ('생활·소비', r'김장|연휴|세금|지원금|입시|수능|교통|할인|가격|요금|건강|다이어트|걷기|감량|기부|요리|레시피|여행')]
LIFE = re.compile(r'물가|세금|지원금|날씨|연휴|입시|수능|교통|요금|김장|환율|금리|대출|월세|전세|연말정산|최저임금')
QW = re.compile(r'이유|뜻|란|왜|언제|어디|일정|방법|시기|뭐|가격|나이|시간|결과|순위|중계|후기')


def cat_of(k, news):
    t = (k + ' ' + ' '.join(n['t'] for n in (news or [])[:3])).lower()
    for name, rx in CATS:
        if re.search(rx, t):
            return name
    return '기타'


def one_liner(cur, db):
    """오늘의 한 줄: 분야별 개수 집계만(해석 없음)."""
    pool = [x for x in cur if x['han']]
    if len(pool) < 5:
        return ''
    c = {}
    for x in pool:
        c[cat_of(x['k'], x['r'].get('news'))] = c.get(cat_of(x['k'], x['r'].get('news')), 0) + 1
    parts = ' · '.join(f'{k} {v}개' for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
    return (f'<p class="kw1l">📝 <b>오늘의 한 줄</b> — 오늘 올라온 한글 키워드 {len(pool)}개를 나누면 {E(parts)}예요. '
            '<small>(키워드와 기사 제목 속 단어로 나눈 개수일 뿐, 해석은 붙이지 않아요)</small></p>')


def priority(cur, hist, contests=()):
    """읽을거리를 먼저 만들 키워드 순서: ①여러 출처에 동시에 ②오래 버팀 ③생활 영향이 있음 (+검색 인기도). 정치·가십·사고는 뺌."""
    out = []
    for x in cur:
        if not x['han'] or x['pol'] or not x['r'].get('news'):
            continue
        txt = x['k'] + ' ' + ' '.join(n['t'] for n in x['r']['news'][:3])
        p = 3 * (x['src'] == 'both') + 2 * (x['span'] >= 6 or x['old']) + 2 * bool(LIFE.search(txt)) + x['score'] / 1000
        out.append((p, x))
    return [x for _, x in sorted(out, key=lambda t: -t[0])]


def autocomplete(keys, ac_f, today, delay=0.35):
    """키워드마다 구글 자동완성 연관 검색어를 하루 한 번 모은다(공개 suggest 주소, 키워드 15개 × 질문 접미사 5개). kw/ac.json 에 저장."""
    import time, requests
    ac = json.load(open(ac_f, encoding='utf-8')) if os.path.exists(ac_f) else {}
    for d in [d for d in ac if ac[d].get('d') != today and ac[d].get('d', '') < (datetime.date.fromisoformat(today) - datetime.timedelta(days=3)).isoformat()]:
        del ac[d]
    for sl, k in keys:
        if ac.get(sl, {}).get('d') == today:
            continue
        S = []
        for q in [k + ' ', k + ' 이유', k + ' 뜻', k + ' 언제', k + ' 방법']:
            try:
                r = requests.get('https://suggestqueries.google.com/complete/search', params={'client': 'firefox', 'hl': 'ko', 'q': q}, timeout=10,
                                 headers={'User-Agent': 'Mozilla/5.0'}).json()
                S += [s for s in r[1] if s.startswith(k + ' ') and s.strip() != k]
            except Exception:
                pass
            time.sleep(delay)
        ac[sl] = {'d': today, 'q': list(dict.fromkeys(S))[:20]}
    json.dump(ac, open(ac_f, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    return ac


def enhance(x, db, ac, tsmap, MK, cur, IPmod):
    """키워드 상세의 읽을거리 블록. 반환 (html, 섹션 수). 기사에서 확인되는 것만, 없으면 「아직 알려진 게 없어요」."""
    r, k = x['r'], x['k']
    arts = [(n['t'], n['u'], n['o']) for n in r.get('news', [])] + ([(a['t'], a['u'], a['o']) for a in r.get('ours', [])] if len(k.replace(' ', '')) >= 3 else [])   # 두 글자 이하 흔한 말(삼성·경제)은 제목에 들어간 다른 주제 기사가 섞이므로 구글이 붙인 기사만
    seen, A = set(), []
    for t, u, o in arts:
        if u not in seen:
            seen.add(u); A.append((t, u, o))
    secs, parts = 0, ''
    # 1) 왜 떴나 3줄 (기사 제목 그대로) + 보도 곳수
    outs = sorted({o for _, _, o in A if o})
    if len(A) >= 2:
        secs += 1
        parts += (f'<section class="mg-s"><h2>📰 왜 떴나 — 기사 제목 3줄</h2>' + (f'<p class="kwn">언론사 {len(outs)}곳이 보도</p>' if len(outs) >= 3 else '')
                  + '<ul class="kw-l">' + ''.join(f'<li><a href="{E(u)}" target="_blank" rel="noopener nofollow"><em>{E(o)}</em>{E(t)}</a></li>' for t, u, o in A[:3]) + '</ul></section>')
    # 2) 사람들이 진짜 궁금해하는 것 (자동완성) + 기사로 확인되는 답
    sug = [s for s in (ac.get(x['slug']) or {}).get('q', []) if len(s) > len(k) + 1]
    sug = sorted(sug, key=lambda s: (not QW.search(s), len(s)))
    rows = []
    for s in sug:
        toks = [w for w in s[len(k):].split() if len(w) >= 2]
        rows.append((s, next(((t, u, o) for t, u, o in A for w in toks if w in t), None)))
    rows = sorted(rows, key=lambda r: r[1] is None)[:5]   # 기사에서 답이 확인되는 질문을 앞에
    if len(rows) >= 3 and sum(1 for _, h in rows if h) >= 2:   # 확인되는 답이 2개 미만이면 이 섹션은 만들지 않음(얇은 페이지 방지)
        secs += 1
        lis = ''
        for s, hit in rows:
            ans = (f'기사 제목에서 확인: <a href="{E(hit[1])}" target="_blank" rel="noopener nofollow">{E(hit[0])}</a> <small>({E(hit[2])})</small>' if hit else '아직 알려진 게 없어요')
            lis += f'<li><b>{E(s)}?</b><br><span class="kwn">{ans}</span></li>'
        parts += ('<section class="mg-s"><h2>🙋 사람들이 진짜 궁금해하는 것</h2><p class="kwn">구글 자동완성에 실제로 뜨는 말이에요. 답은 기사 제목에서 확인되는 것만 적어요.</p>'
                  f'<ul class="kwq">{lis}</ul></section>')
    # 3) 타임라인 (급상승 첫 시각 + 기사 시각)
    tl = [(f'{x["first"]}', '수집 기록에서 처음 확인했어요(실제 검색 시작 시각과 다를 수 있음)', '')]
    for t, u, o in A:
        ts = tsmap.get(u)
        if ts and int(ts) <= datetime.datetime.now().timestamp():   # 미래 시각(일부 피드의 날짜 오류)은 타임라인에서 뺌
            tl.append((datetime.datetime.fromtimestamp(int(ts)).strftime('%m/%d %H:%M'), t, f'<a href="{E(u)}" target="_blank" rel="noopener nofollow">{E(o)}</a>'))
    tl = [tl[0]] + sorted(tl[1:], key=lambda z: z[0])
    if len(tl) >= 3:
        secs += 1
        parts += ('<section class="mg-s"><h2>⏱️ 타임라인</h2><ol class="kwt">' + ''.join(f'<li><b>{E(a)}</b> {E(b)} {c}</li>' for a, b, c in tl[:7])
                  + f'</ol><p class="kwn">마지막 확인 {E(x["last"] or "-")} · 기사 시각은 루리가 모은 기사만 보여요.</p></section>')
    # 4) 그래서 나는? (생활 영향 규칙표, 맞는 게 없으면 생략)
    ip = IPmod.card(k + ' ' + ' '.join(t for t, _, _ in A[:3]), None, [(o, t) for t, _, o in A[:6]], MK, head='🙋 그래서 나는? — 내 생활에 미칠 수 있는 영향')
    if ip:
        secs += 1
        parts += ip
    # 5) 비슷한 과거 사례 (db.json 기록)
    c = cat_of(k, r.get('news'))
    same = [v for v in db.values() if cat_of(v['k'], v.get('news')) == c and HAN.search(v['k'])]
    if len(same) >= 8:
        d = sorted(len(v['days']) for v in same)
        first = min(min(v['days']) for v in same)
        n2 = sum(1 for z in d if z >= 2)
        secs += 1
        parts += (f'<section class="mg-s"><h2>📚 비슷한 키워드는 보통 며칠 갈까</h2><p>{E(c)} 분야 키워드 {len(same)}개 중 {n2}개가 이틀 이상 급상승에 올랐고, 보통 <b>{d[len(d) // 2]}일</b> 갔어요. '
                  f'<small>({E(first[5:].replace("-", "/"))}부터 쌓은 기록 기준이라 표본이 작아요)</small></p></section>')
    return parts, secs
