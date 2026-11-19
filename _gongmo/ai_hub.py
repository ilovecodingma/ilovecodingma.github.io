# -*- coding: utf-8 -*-
"""AI 격동기 허브(/ai-trend/): issues/*.json 가운데 AI·반도체·데이터센터·미중 정책 관련 글을 키워드로 자동 모아 축별로 보여 준다.
2026-11-16 사장님 지시(방향 전환). 새 글은 issues/ 에 들어오면 다음 빌드에서 자동으로 이 허브에 붙는다."""
import glob
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

# (축 이름, 안내, 키워드). 위에서부터 먼저 맞는 축에 넣는다.
AXES = [
    ('AI와 노동·고용', 'AI가 일자리와 청년 고용에 미친 영향을 공식 통계로 본 정리.', r'AI 일자리|청년 고용|고용동향'),
    ('중국의 추격', '중국 AI 반도체·메모리 추격에 대한 기관별 전망.', r'중국 AI 반도체|중국 AI|추격'),
    ('데이터센터·전력', 'AI 데이터센터 확대와 전력·송전망 병목.', r'전력계통|전력 부족|전력 병목|송전망'),
    ('미국 정책·수출통제와 한국 영향', '수출통제, 데이터센터 규제, 미중 갈등이 한국 반도체에 어떻게 닿는지.',
     r'수출통제|수출 통제|밀반입|규제|데이터센터|정책|관세|미중|미국 민주당'),
    ('한국 정부·기업의 대응', '한국 정부 발표와 기업 투자가 발표인지 시행인지 나눠 본 정리.', r'K-온디바이스|산업통상부|과기정통부|한국 정부|온양'),
    ('AI 반도체·GPU 공급망', '엔비디아, HBM, 삼성전자·SK하이닉스, 실적과 공급 이야기.',
     r'엔비디아|nvidia|젠슨 황|HBM|GPU|AMD|파운드리|TSMC|반도체|하이닉스'),
    ('시장과 자본시장', 'AI 기대와 우려가 주가·수급·기업 재편에 미친 영향.',
     r'상장|나스닥|공모가|IPO|코스피|서킷브레이커|사이드카|외국인|AI 우려|AI 수익화|리밸런싱|삼성전자|SK그룹'),
]
INC = re.compile(r'엔비디아|nvidia|반도체|HBM|GPU|AI 반도체|AI 규제|AI 우려|AI 수익화|데이터센터|인공지능|오픈AI|openai|딥시크|TSMC|AMD|젠슨 황|파운드리|앤트로픽|anthropic|제미나이|gemini|AI 일자리|AI 고용', re.I)
EXC = re.compile(r'안경|부정행위|조류|고병원성|AI 목소리|세일|시그널|논술|노조')


def pages(page):
    items = []
    for f in glob.glob(os.path.join(HERE, 'issues', '*.json')):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        t = d.get('title', '') + ' ' + d.get('desc', '')
        sl = d.get('slug', '')
        if re.match(r'ai-glasses|ai-cheating', sl):   # AI 안경 시리즈는 /ai-glasses/ 몫
            continue
        if (not INC.search(t) and not re.match(r'(ai-|nvidia-|anthropic-|china-ai-|kospi-5000|samsung-skhynix)', sl)) or EXC.search(d.get('title', '')):   # 2026-11-19 마케터: AI·반도체 글은 slug 접두로도 모은다
            continue
        if not os.path.exists(os.path.join(os.path.dirname(HERE), 'issue', d.get('slug', ''), 'index.html')):   # 보관 기간이 지나 내려간 글은 링크하지 않는다
            continue
        items.append(d)
    if not items:
        return []
    items.sort(key=lambda d: (d.get('date', ''), d.get('slug', '')), reverse=True)
    used, blocks = set(), ''
    for name, note, rx in AXES:
        pick = [d for d in items if d['slug'] not in used and re.search(rx, d['title'] + ' ' + d.get('desc', ''))]
        if not pick:
            continue
        used |= {d['slug'] for d in pick}
        li = ''.join(f'<li><a href="/issue/{E(d["slug"])}/">{E(d.get("home_title") or d["title"])}</a> <small>{E(d.get("date", ""))}</small></li>' for d in pick)
        blocks += f'<section class="aih"><h2>{E(name)}<small>{len(pick)}편</small></h2><p class="cat-st">{E(note)}</p><ul class="gm-l">{li}</ul></section>'
    latest = items[0].get('date', '')
    trig = next((d for d in items if d['slug'].startswith('jensen-huang-recent-remarks-timeline')), None)
    chain = [d for d in items if d['slug'].startswith('nvidia-ceo-exit')]
    pillars = [d for d in items if d['slug'] == 'jensen-huang-exit-ai-market-scenarios-1116' or d['slug'].startswith('nvidia-stock-')]
    pre = ''
    if pillars:
        pre = ('<section class="aih aih-p"><h2>종합: 젠슨 황 사임과 AI 시장의 시나리오</h2><p class="cat-st">젠슨 황의 이력부터 사임 경과, 이후 전개를 시나리오로 한 번에 정리한 종합 글입니다.</p><ul class="gm-l">'
               + ''.join(f'<li><a href="/issue/{E(d["slug"])}/">{E(d.get("home_title") or d["title"])}</a> <small>{E(d.get("date", ""))}</small></li>' for d in pillars) + '</ul></section>')
    if trig:
        blocks = (f'<section class="aih aih-t"><h2>출발점: 젠슨 황의 사임<small>11월 12일</small></h2>'
                  f'<p class="cat-st">엔비디아 창업자이자 CEO인 젠슨 황의 사임 발표가 AI 반도체 공급망과 미중 정책, 한국 시장에 어떤 연쇄로 이어지는지 아래 글들을 따라 살펴봅니다. 출발점이 되는 정리: '
                  f'<a href="/issue/{E(trig["slug"])}/">{E(trig.get("home_title") or trig["title"])}</a></p>'
                  + (('<p class="cat-st">이어지는 연결고리:</p><ul class="gm-l">' + ''.join(f'<li><a href="/issue/{E(d["slug"])}/">{E(d.get("home_title") or d["title"])}</a> <small>{E(d.get("date", ""))}</small></li>' for d in chain) + '</ul>') if chain else '')
                  + '</section>') + blocks
    blocks = pre + blocks
    body = ('<div class="sk"><p class="bc">AI 격동기</p><h1>AI 격동기 — 세상이 어떻게 흘러가는지 모아 보는 곳</h1>'
            '<p class="cat-st">AI와 반도체, 미국의 정책, 중국의 추격, 시장의 반응을 공식 자료와 기관별 입장으로 나눠 정리한 글을 한곳에 모았습니다. 글마다 날짜와 확인 상태가 적혀 있고, 새 글은 올라오는 대로 이 목록에 붙습니다.</p>'
            + blocks + f'<p class="note">가장 최근 글은 {E(latest)} 것입니다. 전망은 말한 기관과 사람에게 귀속해 적었고 필자의 예측이나 투자 권유는 없습니다.</p></div>'
            '<style>.aih{margin:26px 0}.aih h2{margin:0 0 4px}.aih h2 small{margin-left:8px;font-size:13px;color:var(--mu,#64748b);font-weight:400}.aih li{margin:6px 0;line-height:1.6}.aih li small{color:var(--mu,#64748b);margin-left:6px}</style>')
    page('/ai-trend/', 'AI 격동기 — AI·반도체·미중 정책 흐름을 모아 보는 곳',
         'AI 반도체와 엔비디아, HBM, 미국 수출통제, 중국 추격, 시장 반응을 공식 자료와 기관별 입장으로 정리한 글을 날짜와 함께 한곳에 모았습니다.',
         body, [('홈', '/'), ('AI 격동기', '/ai-trend/')])
    return ['/ai-trend/']
