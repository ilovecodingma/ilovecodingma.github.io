# -*- coding: utf-8 -*-
"""에이전트 위키 (2026-11-27 사용자 「나무위키처럼 · 각주 · 에이전트 토론 공개 · 누구나 토론·수정 제안 · 롤백」).
문서 데이터: _gongmo/wiki_data/<slug>.json
  {slug,title,summary,category,updated,rev_note,
   sections:[{h,body}]   body 문단은 빈 줄로 나눔, '- ' 로 시작하는 줄은 목록, 각주는 [1] 형태, 굵게 **x**
   notes:[{n,text,url?}]
   debate:[{r,who,say}]  교차검증 토론 기록(역할: 작성·검증A·검증B·반박·조정)
   verdict, open:[남은 쟁점]}
개정 이력: wiki_data/_rev/<slug>/NNNN.json (내용이 바뀐 빌드마다 자동 저장). 롤백: python wiki_rollback.py <slug> [번호]
주소: /wiki/<slug>/ (문서) · /wiki/<slug>/talk/ (토론 — 에이전트 토론 + 누구나 댓글) · /wiki/<slug>/history/ (역사)
"""
import os, re, json, html as H, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'wiki_data')
E = lambda t: H.escape(str(t), quote=True)
ROLE = {'작성': 'w', '검증A': 'a', '검증B': 'b', '반박': 'c', '조정': 'd'}

CSS = ('<style>.aw{max-width:900px;margin:0 auto;line-height:1.8;--ln:rgba(140,150,200,.28);--ac:#00a495;--mu:#8e98c0}'
       '.aw .tabs{display:flex;gap:0;border-bottom:2px solid var(--ac);margin:8px 0 0}.aw .tabs a{padding:8px 18px;border:1px solid var(--ln);border-bottom:0;border-radius:8px 8px 0 0;text-decoration:none;color:inherit;font-weight:700;margin-right:4px;background:rgba(120,130,180,.08)}.aw .tabs a.on{background:var(--ac);color:#fff;border-color:var(--ac)}'
       '.aw h1{font-size:30px;margin:18px 0 4px;letter-spacing:-.02em}.aw .meta{color:var(--mu);font-size:13px;margin:0 0 14px}'
       '.aw .box{border:1px solid var(--ln);border-radius:8px;padding:12px 16px;margin:14px 0;background:rgba(120,130,180,.07)}.aw .sum{border-left:4px solid var(--ac)}'
       '.aw .toc b{display:block;margin-bottom:6px}.aw .toc ol{margin:0;padding-left:0;list-style:none;columns:2;column-gap:28px}.aw .toc li{margin:2px 0}.aw .toc a{text-decoration:none;color:var(--ac)}.aw .toc i{font-style:normal;color:var(--mu);margin-right:6px}'
       '.aw h2{font-size:21px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--ln);display:flex;justify-content:space-between;align-items:baseline}.aw h2 a.n{color:var(--ac);text-decoration:none;margin-right:8px}.aw h2 .ed{font-size:12px;font-weight:400;color:var(--mu);text-decoration:none;border:1px solid var(--ln);padding:1px 8px;border-radius:4px}'
       '.aw p{margin:8px 0}.aw ul.l{margin:8px 0;padding-left:22px}.aw sup a{color:var(--ac);text-decoration:none;font-weight:700;padding:0 1px}'
       '.aw .fn{margin-top:34px;border-top:2px solid var(--ln);padding-top:10px;font-size:14px}.aw .fn h2{font-size:17px;border:0;margin:0 0 8px}.aw .fn ol{list-style:none;padding:0;margin:0}.aw .fn li{margin:5px 0;padding-left:34px;text-indent:-34px}.aw .fn li a.b{color:var(--ac);text-decoration:none;font-weight:700;margin-right:8px;display:inline-block;min-width:26px;text-indent:0}.aw .fn li:target{background:rgba(0,164,149,.15)}'
       '.aw .cta{margin:26px 0;padding:14px 16px;border:1px dashed var(--ac);border-radius:8px}.aw .cta a{color:var(--ac);font-weight:700}'
       '.aw .vd{padding:10px 14px;border-radius:8px;margin:12px 0;font-weight:700}.aw .vd.ok{background:rgba(52,211,153,.13);border:1px solid rgba(52,211,153,.4)}.aw .vd.op{background:rgba(251,191,36,.13);border:1px solid rgba(251,191,36,.45)}'
       '.aw .rd{margin:22px 0 6px;font-size:13px;color:var(--mu);font-weight:700}.aw .bb{display:flex;gap:10px;margin:8px 0}.aw .bb .who{flex:0 0 58px;text-align:center;font-size:12px;font-weight:800;padding:5px 0;border-radius:6px;height:fit-content;color:#fff;background:#64748b}'
       '.aw .bb.w .who{background:#2563eb}.aw .bb.a .who{background:#059669}.aw .bb.b .who{background:#7c3aed}.aw .bb.c .who{background:#dc2626}.aw .bb.d .who{background:#d97706}'
       '.aw .bb .say{flex:1;border:1px solid var(--ln);border-radius:4px 12px 12px 12px;padding:8px 12px;background:rgba(120,130,180,.07)}'
       '.aw table.h{width:100%;border-collapse:collapse;font-size:14px}.aw table.h td,.aw table.h th{border-bottom:1px solid var(--ln);padding:8px 6px;text-align:left}'
       '@media(max-width:640px){.aw .toc ol{columns:1}.aw h1{font-size:25px}}</style>')


def _inl(t, notes):
    t = E(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)

    def fn(m):
        n = int(m.group(1))
        tip = next((E(x['text'])[:120] for x in notes if x['n'] == n), '')
        return f'<sup><a href="#fn-{n}" id="r-{n}" title="{tip}">[{n}]</a></sup>'
    return re.sub(r'\[(\d{1,2})\]', fn, t)


def _body(txt, notes):
    out, lst = [], []
    for ln in txt.split('\n'):
        s = ln.strip()
        if s.startswith('- '):
            lst.append(f'<li>{_inl(s[2:], notes)}</li>')
            continue
        if lst:
            out.append('<ul class="l">' + ''.join(lst) + '</ul>'); lst = []
        if s:
            out.append(f'<p>{_inl(s, notes)}</p>')
    if lst:
        out.append('<ul class="l">' + ''.join(lst) + '</ul>')
    return ''.join(out)


def _tabs(slug, cur, rounds, revs):
    def a(k, t, u):
        return f'<a class="{"on" if cur == k else ""}" href="{u}">{t}</a>'
    return '<div class="tabs">' + a('d', '문서', f'/wiki/{slug}/') + a('t', f'토론 <small>{rounds}라운드</small>', f'/wiki/{slug}/talk/') + a('h', f'역사 <small>r{revs}</small>', f'/wiki/{slug}/history/') + '</div>'


def _snapshot(d):
    """내용이 바뀌었으면 새 개정으로 저장하고 (개정 번호, 목록)을 돌려준다."""
    slug = d['slug']
    rd = os.path.join(DATA, '_rev', slug)
    os.makedirs(rd, exist_ok=True)
    core = {k: d.get(k) for k in ('title', 'summary', 'sections', 'notes')}
    h = hashlib.sha1(json.dumps(core, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    fs = sorted(f for f in os.listdir(rd) if f.endswith('.json'))
    revs = []
    for f in fs:
        r = json.load(open(os.path.join(rd, f), encoding='utf-8'))
        revs.append({'n': int(f[:4]), 'h': r.get('_h'), 'ts': r.get('_ts'), 'note': r.get('_note', '')})
    if not revs or revs[-1]['h'] != h:
        n = (revs[-1]['n'] + 1) if revs else 1
        rec = dict(d); rec['_h'] = h; rec['_ts'] = d.get('updated') or datetime.date.today().isoformat(); rec['_note'] = d.get('rev_note') or ('최초 작성' if n == 1 else '수정')
        json.dump(rec, open(os.path.join(rd, f'{n:04d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        revs.append({'n': n, 'h': h, 'ts': rec['_ts'], 'note': rec['_note']})
    return revs


def _doc(d, revs):
    notes = d.get('notes', [])
    secs = d['sections']
    slug = d['slug']
    rounds = len({x.get('r', 1) for x in d.get('debate', [])})
    toc = ''.join(f'<li><i>{i}.</i><a href="#s-{i}">{E(s["h"])}</a></li>' for i, s in enumerate(secs, 1)) + ('<li><i>↓</i><a href="#fn">각주</a></li>' if notes else '')
    sec = ''.join(f'<h2 id="s-{i}"><span><a class="n" href="#s-{i}">{i}.</a>{E(s["h"])}</span><a class="ed" href="/wiki/{slug}/talk/#propose">수정 제안</a></h2>{_body(s["body"], notes)}' for i, s in enumerate(secs, 1))
    fn = ''
    if notes:
        fn = f'<div class="fn" id="fn"><h2>각주</h2><p><a href="/wiki/{slug}/talk/">🔎 이 근거가 맞는지 에이전트들이 검증한 토론 보기</a> · 틀린 곳은 토론에 제안</p><ol>' + ''.join(
            f'<li id="fn-{x["n"]}"><a class="b" href="#r-{x["n"]}">[{x["n"]}]</a>{E(x["text"])}' + (f' <a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">원문</a>' if x.get('url') else '') + '</li>' for x in notes) + '</ol></div>'
    return (f'<div class="aw"><p class="bc"><a href="/">홈</a> › <a href="/wiki/">박과장 위키</a> › {E(d["title"])}</p>' + _tabs(slug, 'd', rounds, revs[-1]['n'])
            + f'<h1>{E(d["title"])}</h1><p class="meta">분류: {E(d.get("category", "생활"))} · 최종 수정 {E(d.get("updated", ""))} · r{revs[-1]["n"]} · 에이전트 {rounds}라운드 교차검증</p>'
            f'<div class="box sum">{_inl(d["summary"], notes)}</div><div class="box toc"><b>목차</b><ol>{toc}</ol></div>' + sec + fn
            + f'<div class="cta">틀린 곳이 있으면 <a href="/wiki/{slug}/talk/#propose">토론</a>에 올려 줘. 에이전트가 근거를 다시 확인해서 맞으면 고치고, 아니면 왜 안 고치는지 남긴다. 잘못 올라간 개정은 <a href="/wiki/{slug}/history/">역사</a>에서 되돌린다.</div></div>' + CSS)


def _talk(d, revs):
    slug = d['slug']
    notes = d.get('notes', [])
    deb = d.get('debate', [])
    rounds = sorted({x.get('r', 1) for x in deb})
    bub = ''
    for r in rounds:
        bub += f'<div class="rd">라운드 {r}</div>'
        for x in [y for y in deb if y.get('r', 1) == r]:
            bub += f'<div class="bb {ROLE.get(x["who"], "")}"><div class="who">{E(x["who"])}</div><div class="say">{_inl(x["say"], notes)}</div></div>'
    op = d.get('open') or []
    vd = (f'<div class="vd op">{E(d.get("verdict", "일부 이견"))}</div><ul class="l">' + ''.join(f'<li>{E(o)}</li>' for o in op) + '</ul>') if op else f'<div class="vd ok">{E(d.get("verdict", "합의"))}</div>'
    return (f'<div class="aw"><p class="bc"><a href="/">홈</a> › <a href="/wiki/">박과장 위키</a> › <a href="/wiki/{slug}/">{E(d["title"])}</a> › 토론</p>' + _tabs(slug, 't', len(rounds), revs[-1]['n'])
            + f'<h1>{E(d["title"])} <small style="font-size:16px;font-weight:400">토론</small></h1>'
            '<p class="meta">이 문서를 쓰기 전에 에이전트들이 서로 검증한 과정이야. 그대로 공개한다.</p>' + vd + bub
            + '<div class="box" id="propose"><b>누구나 토론·수정 제안</b><p>틀린 곳을 찾았으면 아래 댓글로 남겨 줘. <b>[수정제안] 몇 번 항목, 뭐가 틀렸고 맞는 내용은 뭔지, 근거 링크</b> 순서로 쓰면 빨라. '
              '매일 빌드 때 에이전트들이 근거를 다시 확인해서, 맞으면 문서를 고치고 틀리면 이유를 여기에 남긴다. 고친 건 역사에 남고, 잘못 올라가면 되돌린다.</p></div></div>' + CSS)


def _hist(d, revs):
    slug = d['slug']
    rows = ''.join(f'<tr><td>r{r["n"]}</td><td>{E(r["ts"] or "")}</td><td>{E(r["note"])}</td><td><a href="/wiki/{slug}/r{r["n"]}/">{"현재판" if r["n"] == revs[-1]["n"] else "그때 내용"}</a></td></tr>' for r in reversed(revs))
    return (f'<div class="aw"><p class="bc"><a href="/">홈</a> › <a href="/wiki/">박과장 위키</a> › <a href="/wiki/{slug}/">{E(d["title"])}</a> › 역사</p>' + _tabs(slug, 'h', len({x.get("r", 1) for x in d.get("debate", [])}), revs[-1]['n'])
            + f'<h1>{E(d["title"])} <small style="font-size:16px;font-weight:400">역사</small></h1>'
            '<p class="meta">고쳐진 판은 전부 남는다. 잘못 올라간 판은 이전 개정으로 되돌려서 다시 빌드한다(운영자 작업).</p>'
            f'<table class="h"><tr><th>판</th><th>날짜</th><th>변경</th><th></th></tr>{rows}</table></div>' + CSS)


def _rev_page(d, r, revs):
    rec = json.load(open(os.path.join(DATA, '_rev', d['slug'], f'{r["n"]:04d}.json'), encoding='utf-8'))
    rec['slug'] = d['slug']
    body = _doc(rec, revs)
    return body.replace('<div class="cta">', f'<div class="vd op">이건 r{r["n"]} ({E(r["ts"] or "")}) 때 내용이야. <a href="/wiki/{d["slug"]}/">현재판 보기</a></div><div class="cta">', 1)


TIPKEY = {'severance-pay': ('severance', 'retirement-pay'), 'unemployment-benefit': ('unemploy',), 'annual-leave': ('annual-leave',),
          'weekly-holiday-pay': ('weekly-holiday', 'holiday-pay'), 'lease-renewal-right': ('lease-renewal', 'deposit-return-lease'), 'year-end-tax-settlement': ('year-end', 'yeonmal')}


def _tips(slug, root):
    g = os.path.join(root, 'money', 'guide')
    if not os.path.isdir(g):
        return []
    ks = TIPKEY.get(slug, ())
    return [f'/money/guide/{n}/' for n in sorted(os.listdir(g)) if any(k in n for k in ks) and os.path.exists(os.path.join(g, n, 'index.html'))][:8]


def link_tips(docs, root):
    """생활 꿀팁(가이드) ↔ 위키: 꿀팁 글 위에 「정의·근거는 위키」, 위키 글 아래에 「관련 꿀팁」을 붙인다."""
    n = 0
    for d in docs:
        tips = _tips(d['slug'], root)
        if not tips:
            continue
        box = ('<div class="aw-tip" style="margin:12px 0;padding:10px 14px;border:1px solid rgba(0,164,149,.5);border-radius:8px;background:rgba(0,164,149,.08)">'
               f'📚 이 제도의 정의·요건·근거 조문은 <a href="/wiki/{d["slug"]}/"><b>루리위키 「{E(d["title"])}」</b></a>에 각주와 함께 정리돼 있다.</div>')
        for u in tips:
            f = os.path.join(root, u.strip('/'), 'index.html')
            h = open(f, encoding='utf-8').read()
            if 'aw-tip' in h:
                continue
            m = re.search(r'</h1>', h)
            if m:
                open(f, 'w', encoding='utf-8', newline='\n').write(h[:m.end()] + box + h[m.end():]); n += 1
        wf = os.path.join(root, 'wiki', d['slug'], 'index.html')
        if os.path.exists(wf):
            h = open(wf, encoding='utf-8').read()
            if 'aw-tips' not in h:
                li = ''.join(f'<li><a href="{u}">{E(u.strip("/").split("/")[-1].replace("-", " "))}</a></li>' for u in tips)
                sec = f'<div class="box aw-tips"><b>🍯 관련 생활 꿀팁</b> <small>(상황별로 뭘 해야 하는지)</small><ul class="l">{li}</ul></div>'
                h = h.replace('<div class="cta">', sec + '<div class="cta">', 1)
                open(wf, 'w', encoding='utf-8', newline='\n').write(h)
    return n


def load():
    out = []
    if not os.path.isdir(DATA):
        return out
    for f in sorted(os.listdir(DATA)):
        if f.endswith('.json') and not f.startswith('_'):
            d = json.load(open(os.path.join(DATA, f), encoding='utf-8'))
            d.setdefault('slug', f[:-5])
            if d.get('hold'):
                continue
            out.append(d)
    return out


def build(page_fn, urls):
    """문서·토론·역사 페이지를 만들고 /wiki/ 허브에 넣을 카드 HTML 을 돌려준다."""
    docs = load()
    cards = ''
    for d in docs:
        slug = d['slug']
        revs = _snapshot(d)
        base = f'/wiki/{slug}/'
        crumbs = [('가난한 박과장', '/'), ('박과장 위키', '/wiki/'), (d['title'], base)]
        desc = re.sub(r'\[\d+\]', '', d['summary'])[:150]
        page_fn(base, f'{d["title"]} — 박과장 위키', desc, _doc(d, revs), crumbs)
        page_fn(base + 'talk/', f'{d["title"]} 토론 — 박과장 위키', f'{d["title"]} 문서를 쓰기 전에 에이전트들이 교차검증한 토론 기록과 수정 제안.', _talk(d, revs), crumbs + [('토론', base + 'talk/')], noindex=True)
        page_fn(base + 'history/', f'{d["title"]} 역사 — 박과장 위키', f'{d["title"]} 문서 개정 이력.', _hist(d, revs), crumbs + [('역사', base + 'history/')], noindex=True)
        for r in revs[:-1]:
            page_fn(f'{base}r{r["n"]}/', f'{d["title"]} r{r["n"]} — 박과장 위키', '지난 개정판', _rev_page(d, r, revs), crumbs, noindex=True)
        urls += [base]
        cards += f'<li><a href="{base}"><b>{E(d["title"])}</b><span>{E(re.sub(r"[[]\d+[]]", "", d["summary"])[:90])}</span></a></li>'
    if not cards:
        return ''
    return f'<section class="wk-card" id="g-agent"><h2>🤖 에이전트 위키 <small>{len(docs)}편 · 토론 공개</small></h2><ul class="wk-list">{cards}</ul></section>'
