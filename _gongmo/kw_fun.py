# 인기 키워드 놀이판 (2026-10-20 사용자 「뉴스는 재미없고 키워드 쪽을 재밌게」) — /kw/ 맨 위에 붙는 구름·1위 카드·뱃지·스파크라인·퀴즈·내일 예측 투표·TOP5 카드.
# 원칙: 데이터에 있는 것만(시간·검색량 구간·기사 제목) 쓰고, 순위 흐름은 kw.py 가 매시 쌓는 kw/hist.json 이 생긴 뒤부터(그 전엔 「기록 시작」 안내).
import datetime, hashlib, html, json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = lambda s: html.escape(str(s), quote=True)
HAN = re.compile(r'[가-힣]')
POL = re.compile(r'대통령|국회|의원|정당|여당|야당|장관|총리|청와대|탄핵|선거|공천|검찰|특검|북한|김정은|김여정|트럼프|시진핑|국민의힘|민주당|혁신당|정권|국정|외교|안보|전쟁|공습|미사일|대남|확성기|해킹|책임')
STY = {'google': ('#2563eb', '구글'), 'naver': ('#16a34a', '실시간'), 'both': ('#9333ea', '동시')}
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
    L = sorted([x for x in cur if x['han'] and x['cur']], key=lambda x: -x['score'])[:28]
    if not L:
        return ''
    mx = max(x['score'] for x in L) or 1
    sp = ''.join(f'<a href="#k-{E(x["slug"])}" style="font-size:{14 + 22 * (x["score"] / mx) ** .6:.0f}px;color:{STY[x["src"]][0]}">{E(x["k"][:14])}</a>' for x in sorted(L, key=lambda x: x['k']))
    leg = ' '.join(f'<i style="color:{c}">●</i> {n}' for c, n in STY.values())
    return (f'<section class="kwc"><h2>☁️ 지금 키워드 구름</h2><p class="kwcl">{sp}</p>'
            f'<p class="kwn">글자 크기 = 검색량 구간과 실시간 순위를 합친 상대 인기도 · 색 = 출처 {leg} · 누르면 아래 카드로 이동해요.</p></section>')


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
        opts = [{'t': n['t'], 'ok': 1, 'o': n['o'], 'u': n['u']}, {'t': w1['t'], 'ok': 0}, {'t': w2, 'ok': 0}]
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
        dr.text((60, 92), f'{today[5:7]}월 {today[8:]}일 {nowhm} 기준 · 구글 트렌드·실시간 검색어', font=W._font(26), fill=(100, 116, 139))
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
