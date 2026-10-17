# -*- coding: utf-8 -*-
"""루리의 수상 연구소 — 실제 수상작 + 작품 해설 페이지 (2026-10-17 사용자: "공모전 실제 작품과 분석 형식으로")
winners.json(공모전_2026\\data\\winners\\analyze.py) → /lab/ (공모전별 수상작 카드) + /lab/<키>/ (작품마다 구조 해부·기법·루리 한 줄 평, 등급 비교)"""
import re, html, hashlib, json, os, statistics
E = lambda s: html.escape(str(s or ''), quote=True)
PAIRS = [('오늘', '내일'), ('나', '우리'), ('작은', '큰'), ('시작', '완성'), ('지금', '미래'), ('너', '나'), ('어제', '오늘'), ('하나', '모두'),
         ('빚', '빛'), ('안전', '행복'), ('마음', '세상'), ('일터', '일상'), ('확신', '확인'), ('청탁', '청렴'), ('나', '모두')]
THEMEW = {'청렴': ['청렴', '정직', '투명', '신뢰', '공정', '깨끗'], '안전': ['안전', '확인', '점검', '생명', '지킴', '보호'], '인권': ['인권', '존중', '평등', '차별', '배려'],
          '출산육아': ['아이', '웃음', '가족', '육아', '결혼', '출산'], '비전': ['미래', '내일', '함께', '도약', '꿈', '세계'], '관광축제': ['여행', '축제', '설렘', '머무', '오세요'],
          '도시브랜드': ['도시', '행복', '살기', '품', '중심'], '기념일': ['신문', '한글', '독서', '읽'], '기업캠페인': ['고객', '마음', '행복', '함께']}
ICON = {'대구': '↔️', '두 덩어리': '✂️', '대비어': '⚖️', '반복': '🔁', '운율': '🎵', '주제어': '🎯', '기관명': '🏢', '숫자': '🔢', '느낌표': '❗', '명사 마무리': '⏹️', '작명 의미': '💡'}
COLS = ['대구', '두 덩어리', '대비어', '반복', '운율', '주제어', '기관명', '명사 마무리']
RANKN = {1: '대상·최우수', 2: '우수', 3: '장려', 4: '입선', 5: '기타'}

def chunks(p):
    c = [x.strip() for x in re.split(r'[,，·/!?…]|\s{2,}', p) if x.strip()]
    return c if len(c) >= 2 else [p.strip()]

def anatomy(it, med):
    """작품 하나 해부 → (덩어리 HTML, 기법 목록[(이름, 설명)], 루리 한 줄 평)"""
    p, f = it['p'], it.get('f') or {}
    cs = chunks(p); tech = []
    if len(cs) >= 2:
        if f.get('pair'): tech.append(('대구', f'「{cs[0]}」 / 「{cs[1]}」 — 앞뒤를 {len(cs[0].replace(" ", ""))}자·{len(cs[1].replace(" ", ""))}자로 맞춰 리듬이 생겨요.'))
        else: tech.append(('두 덩어리', f'「{cs[0]}」 다음에 「{"·".join(cs[1:])}」로 받아, 끊어 읽기 쉬워요.'))
    for a, b in PAIRS:
        if a in p and b in p and a != b:
            tech.append(('대비어', f'「{a}」와 「{b}」를 맞세워 메시지가 또렷해요.')); break
    ws = [w for w in re.findall(r'[가-힣A-Za-z0-9]{2,}', p)]
    rep = [w for w in set(ws) if ws.count(w) >= 2]
    if rep: tech.append(('반복', f'「{rep[0]}」를 두 번 써서 귀에 남아요.'))
    if len(cs) >= 2 and cs[0][-1:] == cs[1][-1:]: tech.append(('운율', f'앞뒤 끝 글자를 「{cs[0][-1]}」로 맞췄어요.'))
    th = it.get('th') or ''
    kw = [w for w in THEMEW.get(th, []) if w in p]
    if kw: tech.append(('주제어', f'주제({th})의 핵심어 「{"」·「".join(kw[:2])}」을 직접 넣었어요.'))
    org = re.sub(r'(주식회사|\(주\)|재단법인|사단법인)', '', it.get('o') or '').strip()
    short = [x for x in re.findall(r'[가-힣A-Za-z]{2,}', org) if x in p]
    if short: tech.append(('기관명', f'주최 「{short[0]}」 이름을 품어 그 기관만의 문구가 됐어요.'))
    if f.get('number'): tech.append(('숫자', '숫자·서수로 구체적인 그림을 줘요.'))
    if f.get('exclaim'): tech.append(('느낌표', '외치는 말투로 캠페인 느낌을 살렸어요.'))
    if f.get('end_noun') and it.get('g') != '네이밍': tech.append(('명사 마무리', f'「…{p.rstrip("!?. ")[-3:]}」처럼 명사로 딱 끊어 여운을 남겨요.'))
    n = f.get('len') or len(p.replace(' ', ''))
    if it.get('g') == '네이밍':
        tech.insert(0, ('길이', f'{n}자 — 부르기 쉬운 짧은 이름이에요.'))
        if it.get('m'): tech.append(('작명 의미', it['m']))
    else:
        tech.insert(0, ('길이', f'공백 빼고 {n}자 — 수상작 가운데 값 {med:g}자{"보다 짧고 굵게" if n < med - 3 else "보다 길게 풀어" if n > med + 3 else "에 딱 맞춰"} 썼어요.'))
    names = [t for t, _ in tech if t not in ('길이', '작명 의미')]
    one = (f'{"·".join(names[:3])}을 겹쳐 쓴 게 이 문구의 힘이에요.' if len(names) >= 2 else f'{names[0]} 하나로 승부한 담백한 문구예요.' if names else '군더더기 없이 메시지만 남긴 문구예요.')
    seg = ' <i>/</i> '.join(f'<span class="lw-c">{E(c)}</span>' for c in cs)
    return seg, tech, one

def matrix(mx, med):
    if not mx: return ''
    cols = [c for c in COLS if any(c in t for _, t in mx)]
    mxl = max([med] + [(r.get('f') or {}).get('len', 0) for r, _ in mx]) or 1
    head = ''.join(f'<th title="{c}">{ICON[c]}<small>{c}</small></th>' for c in cols)
    rows = ''.join(f'''<tr class="r{r["rk"]}"><td class="lm-n"><b>{E(r.get("gr") or RANKN.get(r["rk"], ""))}</b><span>{E(r["p"][:22])}{"…" if len(r["p"]) > 22 else ""}</span>
<i class="lm-len" style="--w:{round((r.get("f") or {}).get("len", 0) / mxl * 100)}%"><em>{(r.get("f") or {}).get("len", "")}자</em></i></td>{"".join(f'<td>{"●" if c in t else ""}</td>' for c in cols)}</tr>''' for r, t in mx)
    return f'<section class="lm"><h2>👀 한눈에 보기</h2><div class="lm-w"><table><tr><th>작품 <small>막대=길이 · 가운데 {med:g}자</small></th>{head}</tr>{rows}</table></div></section>'


def compare(rows):
    """같은 공모전 안 등급 비교 한두 줄"""
    top = [r for r in rows if r['rk'] == 1]; low = [r for r in rows if r['rk'] >= 3]
    if not top or not low: return ''
    def rate(sub, k): return sum(1 for r in sub if (r.get('f') or {}).get(k)) / len(sub)
    out = []
    for k, nm in (('pair', '대구'), ('comma', '두 덩어리 끊기'), ('contrast', '대비어'), ('rhyme', '운율')):
        if rate(top, k) - rate(low, k) >= 0.5: out.append(f'1등은 <b>{nm}</b>를 썼는데 장려·입선작은 대부분 안 썼어요.')
    lt, ll = statistics.mean((r.get('f') or {}).get('len', 0) for r in top), statistics.mean((r.get('f') or {}).get('len', 0) for r in low)
    if lt + 3 <= ll: out.append(f'1등이 평균 {ll - lt:.0f}자 더 짧아요. 줄일수록 세졌어요.')
    elif lt >= ll + 3: out.append(f'1등이 평균 {lt - ll:.0f}자 더 길어요. 구체적인 그림을 담았어요.')
    return ''.join(f'<li>{x}</li>' for x in out[:3])

def build(ROOT, page, say):
    fp = os.path.join(ROOT, 'winners.json')
    if not os.path.exists(fp): return []
    D = json.load(open(fp, encoding='utf-8')); med = (D.get('all') or {}).get('len_med', 18)
    groups = {}
    for it in D['items']: groups.setdefault((it['c'], it['o'], it.get('y')), []).append(it)
    cards, urls = [], []
    for (c, o, y), rows in sorted(groups.items(), key=lambda kv: (-(kv[0][2] or 0), min(r['rk'] for r in kv[1]))):
        rows.sort(key=lambda r: r['rk'])
        key = hashlib.md5(f'{c}|{o}|{y}'.encode()).hexdigest()[:8]; url = f'/lab/{key}/'; urls.append(url)
        g, th, n = rows[0].get('g'), rows[0].get('th'), next((r['n'] for r in rows if r.get('n')), None)
        works = ''; mx = []
        for r in rows:
            seg, tech, one = anatomy(r, med)
            badges = ''.join(f'<span class="lw-b" title="{E(d)}">{ICON.get(t, "•")} {E(t)}</span>' for t, d in tech if t != '길이')
            works += f'''<article class="lw-w r{r["rk"]}"><p class="lw-g">{E(r.get("gr") or RANKN.get(r["rk"], ""))} <small>{(r.get("f") or {}).get("len", "")}자</small></p><p class="lw-p">{seg}</p>
<p class="lw-bs">{badges}</p><details><summary>💬 {E(one)} <em>해설 펼치기</em></summary><ul class="lw-t">{"".join(f'<li><b>{E(t)}</b>{E(d)}</li>' for t, d in tech)}</ul><a class="lw-src" href="{E(r["s"])}" target="_blank" rel="noopener nofollow">출처 보기</a></details></article>'''
            mx.append((r, {t for t, _ in tech}))
        cmp_ = compare(rows)
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/lab/">수상 연구소</a></p>
<section class="lw-head"><p class="lw-k">{E(g)} · {E(th)}</p><h1>{E(c)}</h1><p>{E(o)}{f" · {y}년" if y else ""}{f" · 응모 {int(n):,}편" if n else ""} · 수상작 {len(rows)}개</p></section>
{say('think', f'이 공모전에서 붙은 작품들을 하나씩 뜯어봤어요. {"응모 " + format(int(n), ",") + "편 중에서 뽑힌 문구예요. " if n else ""}어디가 달랐는지 같이 봐요!')}
{matrix(mx, med)}{f'<section class="lw-cmp"><h2>🥇 1등과 나머지는 뭐가 달랐을까</h2><ul>{cmp_}</ul></section>' if cmp_ else ''}
<section class="lw-list">{works}</section>
<a class="lab-cta" href="/lab/#diag"><b>🧪 내 문구도 이렇게 분석받기</b><span>수상작 패턴과 비교해 점수와 고칠 점을 알려 줘요 →</span></a>
<p class="lb-foot">수상 문구는 주최 기관 발표·보도에서 짧게 인용했고 출처를 붙였어요. 수상자 정보는 싣지 않아요.</p>
<link rel="stylesheet" href="/assets/lab/lab.css?v=2">'''
        top = rows[0]['p']
        page(url, f'{c} 수상작 분석 — 루리의 수상 연구소', f'{c}({o}) 수상작 {len(rows)}개를 구조·기법별로 해설. 대상작: {top[:40]}', body,
             [('루리의 줍줍', '/'), ('수상 연구소', '/lab/'), (c[:30], url)])
        cards.append({'url': url, 'c': c, 'o': o, 'y': y, 'g': g, 'th': th, 'n': n, 'cnt': len(rows), 'top': top, 'gr': rows[0].get('gr') or '', 'one': anatomy(rows[0], med)[2]})
    return cards, urls, D

def index_html(cards, D):
    A = D.get('all') or {}; T = D.get('top') or {}; R = D.get('rest') or {}
    gs = sorted({c['g'] for c in cards}); ths = sorted({c['th'] for c in cards if c['th']})
    def li(c): return (f'''<li class="lx" data-g="{E(c["g"])}" data-th="{E(c["th"])}"><a href="{c["url"]}"><span class="lx-m">{E(c["g"])} · {E(c["th"])} · {c["y"] or ""}</span>
<q>{E(c["top"])}</q><span class="lx-c">{E(c["gr"])} · {E(c["c"])}</span><span class="lx-o">{E(c["o"])}{f" · 응모 {int(c['n']):,}편" if c["n"] else ""} · 수상작 {c["cnt"]}개 해설 →</span><span class="lx-one">💬 {E(c["one"])}</span></a></li>''')
    GEN = {'슬로건': '✍️ 슬로건', '표어': '📢 표어', '네이밍': '🏷️ 네이밍', '삼행시': '🎤 삼행시'}
    secs = ''.join(f'<section class="lx-sec" id="g-{E(g)}"><h2>{GEN.get(g, g)} 수상작 <small>{sum(1 for c in cards if c["g"] == g)}개 공모전</small></h2><ol class="lx-list lx-row">' + ''.join(li(c) for c in cards if c['g'] == g) + '</ol></section>' for g in sorted({c['g'] for c in cards}, key=lambda g: ['슬로건', '표어', '네이밍', '삼행시'].index(g) if g in ['슬로건', '표어', '네이밍', '삼행시'] else 9))
    pct = lambda x: round((x or 0) * 100)
    return f'''<section class="lb-hero"><img src="/assets/ruri/p/office_think.webp" alt="루리" width="300" height="415"><div><p class="lb-kick">루리의 수상 연구소</p><h1>실제 수상작을 <em>한 편씩</em> 뜯어봤어요</h1>
<p>공모전 <b>{len(cards)}개</b>, 수상작 <b>{D["count"]}개</b>. 작품마다 왜 붙었는지 해설을 달았어요.</p></div></section>
<div class="lx-f">{"".join(f'<a href="#g-{E(g)}">{E(g)}</a>' for g in gs)}<select class="lx-th"><option value="">주제 전체</option>{"".join(f"<option>{E(t)}</option>" for t in ths)}</select></div>
{secs}
<section class="lb-sec lx-sum"><h2>📌 {A.get("n", 0)}개를 다 보고 나니</h2><ul class="lw-t">
<li><b>길이</b>공백 빼고 {A.get("len_p25")}~{A.get("len_p75")}자가 가장 많아요(가운데 {A.get("len_med")}자).</li>
<li><b>대구</b>1등의 {pct((T.get("rate") or {}).get("pair"))}%가 앞뒤 길이를 맞췄어요(장려·입선은 {pct((R.get("rate") or {}).get("pair"))}%).</li>
<li><b>두 덩어리</b>1등의 {pct((T.get("rate") or {}).get("comma"))}%가 쉼표로 끊었어요(장려·입선 {pct((R.get("rate") or {}).get("comma"))}%).</li>
<li><b>대비어</b>1등은 오늘/내일 같은 맞서는 말을 {pct((T.get("rate") or {}).get("contrast"))}% 썼어요(장려·입선 {pct((R.get("rate") or {}).get("contrast"))}%).</li></ul></section>
<section id="lab" class="lb-sec" aria-label="내 문구 진단"></section>
<script>(function(){{var th=document.querySelector('.lx-th');th.onchange=function(){{document.querySelectorAll('.lx').forEach(function(li){{li.hidden=th.value&&li.dataset.th!==th.value}})}}}})();</script>
<link rel="stylesheet" href="/assets/lab/lab.css?v=2"><script defer src="/assets/lab/lab.js?v=2"></script>'''
