# 「💥 내 생활에 미칠 수 있는 영향」 카드 (2026-10-20 사용자 「그 사건에 의한 사이드 이펙트, 대중에게 발생할」)
# 문장은 impact_rules.json 에 있는 것만. 기사 숫자는 출처(언론사·제목)와 함께, 시세는 market.json(하루 1번)으로 사후 확인만.
import datetime, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(HERE, 'impact_rules.json'), encoding='utf-8'))['rules']
for _r in RULES:
    _r['rx'] = re.compile(_r['kw'])
E = lambda s: html.escape(str(s), quote=True)
LV = ['낮음', '보통', '높음']
SKIP = re.compile(r'사망|숨져|숨진|사고|참사|화재|추락|살해|피살|실종')   # 사고·사망 이슈는 붙이지 않음
CSS = ('<style>.ip{margin:14px 0;padding:14px;border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff)}.ip h3{margin:0 0 8px;font-size:16px}'
       '.ip ul{margin:0;padding-left:18px}.ip li{margin:6px 0;line-height:1.6;font-size:14.5px}.ip li b{color:var(--tx,#111)}.ip .ip-g{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}'
       '.ip .ip-g span{font-size:12.5px;padding:3px 9px;border-radius:999px;background:var(--pbg,#f1f5f9)}.ip .ip-g .l2{background:#fee2e2;color:#991b1b}.ip .ip-g .l1{background:#fef3c7;color:#92400e}.ip .ip-g .l0{background:#e0f2fe;color:#075985}'
       '.ip .ip-x{font-size:13.5px;margin:8px 0 0}.ip .ip-n{font-size:12px;color:var(--mu,#6b7280);margin:8px 0 0}</style>')


def match(text, n=2):
    if SKIP.search(text):
        return []
    return [r for r in RULES if r['rx'].search(text)][:n]


def gauge_text(text):
    rs = match(text)
    if not rs:
        return ''
    g = [max(r['gauge'][i] for r in rs) for i in range(3)]
    return ' · '.join(f'{nm} {LV[v]}' for nm, v in zip(('💳 지갑', '🏠 일상', '📅 일정'), g))


def nums_in(title):
    """제목 속 실제 숫자(인상 폭·%·금액·시행일)."""
    return re.findall(r'\d+(?:\.\d+)?\s?%p?|\d[\d,]*(?:\.\d+)?\s?(?:원|달러|bp)|\d{1,2}월\s?\d{1,2}일', title)


def card(text, d0=None, srcs=None, market=None, head='💥 내 생활에 미칠 수 있는 영향'):
    """text: 이슈 제목·키워드 · d0: 발표(첫 보도) 날짜 YYYY-MM-DD · srcs: [(언론사, 기사 제목)] 숫자 출처 · market: market.load() 결과."""
    rs = match(text)
    if not rs:
        return ''
    li = ''
    for r in rs:
        for who, what, how, url in r['lines'][:3]:
            li += f'<li><b>{E(who)}</b> → {E(what)} → ' + (f'<a href="{E(url)}">{E(how)}</a>' if url else E(how)) + '</li>'
    g = [max(r['gauge'][i] for r in rs) for i in range(3)]
    gauge = ''.join(f'<span class="l{v}">{nm} {LV[v]}</span>' for nm, v in zip(('💳 내 지갑', '🏠 내 일상', '📅 내 일정'), g))
    extra = ''
    for o, t in (srcs or [])[:6]:
        ns = nums_in(t)
        if ns:
            extra += f'<p class="ip-x">🔢 기사에 나온 숫자: <b>{E(", ".join(ns[:3]))}</b> <small>— {E(o)} 「{E(t[:40])}」</small></p>'
            break
    if market and d0:
        import market as M
        for r in rs:
            s = (market.get('s') or {}).get(r.get('series') or '')
            if not s:
                continue
            c7 = M.chg(s, d0, 7)
            a = M.val_at(s, d0)
            if c7 is not None:
                extra += f'<p class="ip-x">📈 발표 뒤 실제로: {E(s["name"])} {d0[5:].replace("-", "/")} 이후 7일 {c7:+.1f}% <small>({E(s["src"])})</small></p>'
            elif a and a[0] != s['pts'][-1][0]:
                last = s['pts'][-1]
                extra += (f'<p class="ip-x">📈 지금까지: {E(s["name"])} {a[0][5:].replace("-", "/")} {a[1]:,.2f} → {last[0][5:].replace("-", "/")} {last[1]:,.2f} '
                          f'({(last[1] / a[1] - 1) * 100:+.1f}%) · 7일 뒤 다시 확인해요 <small>({E(s["src"])})</small></p>')
            break
    return (f'<section class="ip"><h3>{head}</h3><div class="ip-g">{gauge}</div><ul>{li}</ul>{extra}'
            '<p class="ip-n">주제별로 미리 정해 둔 일반 정보예요. 개인 상황마다 다르고, 투자 권유가 아니에요.</p></section>' + CSS)
