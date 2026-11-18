# -*- coding: utf-8 -*-
"""AI 안경 의혹 시리즈 허브(/ai-glasses/): 시리즈 편은 slug 가 ai-glasses-series- 로 시작하는 글(편 번호순), 1편과 연관 글은 아래 목록.
2026-11-18 사장님 지시. 새 편은 같은 접두어로 issues/ 에 들어오면 다음 빌드에서 자동으로 붙는다."""
import glob
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
FIRST = 'ai-cheating-buyers-seller-probe-1118'          # 1편
RELATED = ['suneung-ai-cheating-measures-1117', 'leet-perfect-score-ai-allegation-1118']


def _load(slug):
    f = os.path.join(HERE, 'issues', slug + '.json')
    if not os.path.exists(f) or not os.path.exists(os.path.join(os.path.dirname(HERE), 'issue', slug, 'index.html')):
        return None      # 원고가 없거나 보관 기간이 지나 내려간 글은 링크하지 않는다
    try:
        return json.load(open(f, encoding='utf-8'))
    except Exception:
        return None


def _li(d, tag=''):
    return f'<li>{tag}<a href="/issue/{E(d["slug"])}/">{E(d.get("home_title") or d["title"])}</a> <small>{E(d.get("date", ""))}</small></li>'


def pages(page):
    series = []
    first = _load(FIRST)
    if first:
        series.append(first)
    for f in sorted(glob.glob(os.path.join(HERE, 'issues', 'ai-glasses-series-*.json'))):
        d = _load(os.path.basename(f)[:-5])
        if d:
            series.append(d)
    if not series:
        return []
    rel = [d for d in (_load(s) for s in RELATED) if d]
    li = ''.join(_li(d, f'<b class="agn">{i}편</b> ') for i, d in enumerate(series, 1))
    body = ('<div class="sk"><p class="bc">시리즈</p><h1>AI 안경 의혹 — 시험 부정행위 수사와 대책 시리즈</h1>'
            '<p class="cat-st">AI 안경 등 AI 장비를 쓴 시험 부정행위 의혹을 경찰·교육부·시험 주관 기관 등 공식 출처 기준으로 정리합니다. 글마다 날짜와 확인된 것·확인되지 않은 것이 나뉘어 있고, 수사와 발표가 이어지는 대로 편이 추가됩니다.</p>'
            f'<section class="aig"><h2>시리즈<small>{len(series)}편</small></h2><ol class="gm-l">{li}</ol></section>'
            + (f'<section class="aig"><h2>함께 볼 글</h2><ul class="gm-l">{"".join(_li(d) for d in rel)}</ul></section>' if rel else '')
            + f'<p class="note">가장 최근 편은 {E(series[-1].get("date", ""))} 글입니다. 수사 중인 사안은 수사기관의 발표 범위까지만 적었고 필자의 추측이나 단정은 없습니다.</p></div>'
            '<style>.aig{margin:26px 0}.aig h2 small{margin-left:8px;font-size:13px;color:var(--mu,#64748b);font-weight:400}.aig li{margin:8px 0;line-height:1.6}.aig li small{color:var(--mu,#64748b);margin-left:6px}.agn{color:var(--ac,#2563eb);margin-right:4px}</style>')
    page('/ai-glasses/', 'AI 안경 의혹 시리즈 — 시험 부정행위 수사·대책 정리',
         'AI 안경 등 AI 장비를 쓴 시험 부정행위 의혹과 경찰 수사, 세무사 시험, 수능 당일 단속 대책을 공식 출처 기준으로 편별로 정리한 시리즈입니다.',
         body, [('홈', '/'), ('AI 안경 시리즈', '/ai-glasses/')])
    return ['/ai-glasses/']
