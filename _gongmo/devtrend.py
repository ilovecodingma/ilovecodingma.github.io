# -*- coding: utf-8 -*-
"""개발·AI 트렌드 노트(/devtrend/): 해외 개발·AI 뉴스레터를 읽고 자기 말로 정리한 글을 한곳에 모은다(2026-11-17 사용자 지시).
데이터는 _gongmo/devtrend_data.json (issues: 뉴스레터 글 요약, themes: 이번 기간의 큰 흐름). 새 기간은 json 에 덧붙이면 다음 빌드에서 바뀐다.
원문은 베끼지 않고, 출처(뉴스레터 이름·날짜)와 유료 구간 미확인 여부를 함께 적는다."""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

TOPIC_ORDER = ['코딩 에이전트', 'AI 에이전트', '소프트웨어 개발 방식 변화', '시스템 설계·인프라', 'LLM 추론·학습', '보안·공급망', '개발자 커리어·고용', '제품·사업']


def pages(page):
    f = os.path.join(HERE, 'devtrend_data.json')
    if not os.path.exists(f):
        return []
    D = json.load(open(f, encoding='utf-8'))
    issues = sorted(D['issues'], key=lambda x: (x['date'], x['uid']), reverse=True)
    byuid = {str(x['uid']): x for x in issues}
    th = ''
    for i, t in enumerate(D['themes'], 1):
        refs = ''.join(f'<li>{E(byuid[str(u)]["source"])} · {E(byuid[str(u)]["date"])} — {E(byuid[str(u)]["title"])}</li>' for u in t['refs'] if str(u) in byuid)
        pts = ''.join(f'<li>{E(p)}</li>' for p in t.get('points', []))
        th += (f'<section class="dt-th"><h3><span>{i}</span>{E(t["title"])}</h3><p>{E(t["lead"])}</p>'
               + (f'<ul class="dt-pt">{pts}</ul>' if pts else '')
               + (f'<details><summary>이 흐름의 근거가 된 글 {len(t["refs"])}편</summary><ul class="dt-rf">{refs}</ul></details>' if refs else '') + '</section>')
    tp = ''
    for name in TOPIC_ORDER:
        its = [x for x in issues if name in x.get('topics', [])]
        if not its:
            continue
        cards = ''.join(
            f'<article class="dt-it"><h4>{E(x["title"])}</h4><p class="dt-m">{E(x["source"])} · {E(x["date"])}</p><p>{E(x["summary"])}</p>'
            + (f'<p class="dt-pr"><b>실무 시사점</b> {E(x["practical"])}</p>' if x.get('practical') else '') + '</article>' for x in its)
        tp += f'<details class="dt-tp"><summary>{E(name)}<small>{len(its)}편</small></summary>{cards}</details>'
    srcs = sorted({x['source'] for x in issues})
    body = ('<div class="sk"><p class="bc">개발 트렌드 노트</p><h1>개발·AI 트렌드 노트 — ' + E(D['period']) + '</h1>'
            '<p class="cat-st">해외 개발·AI 뉴스레터를 읽고, 소프트웨어를 만들고 운영하는 사람에게 닿는 흐름만 자기 말로 정리했습니다. 글마다 출처 뉴스레터와 날짜를 적었고, 메일에서 유료 구간이라 읽지 못한 부분은 확인하지 못했다고 밝혔습니다. 원문을 그대로 옮기지 않으니 자세한 내용은 각 뉴스레터에서 확인하세요.</p>'
            f'<h2>이번 기간의 큰 흐름 {len(D["themes"])}가지</h2>' + th +
            '<h2>주제별로 보기</h2>' + tp +
            f'<p class="note">정리한 뉴스레터: {E(" · ".join(srcs))}. 기간은 {E(D["period"])}이고 마지막 갱신은 {E(D["updated"])}입니다. 숫자와 주장은 각 글이 말한 것으로 귀속했으며 이 사이트가 직접 검증한 값이 아닙니다. '
            'AI 반도체와 미국 정책 흐름은 <a href="/ai-trend/">AI 격동기</a>에서 따로 모읍니다.</p></div>'
            '<style>.dt-th{margin:22px 0;padding:16px 18px;border:1px solid var(--bd,#e5e7eb);border-radius:14px}.dt-th h3{margin:0 0 6px;font-size:17px}.dt-th h3 span{display:inline-block;min-width:24px;height:24px;line-height:24px;text-align:center;border-radius:50%;background:var(--tc,#2563eb);color:#fff;font-size:13px;margin-right:8px}'
            '.dt-pt{margin:8px 0;padding-left:20px;line-height:1.75}.dt-rf{font-size:13.5px;color:var(--mu,#64748b);line-height:1.7}.dt-tp{margin:10px 0;border:1px solid var(--bd,#e5e7eb);border-radius:12px;padding:8px 14px}.dt-tp>summary{cursor:pointer;font-weight:700;padding:6px 0}.dt-tp small{margin-left:8px;font-weight:400;color:var(--mu,#64748b)}'
            '.dt-it{padding:12px 0;border-top:1px solid var(--bd,#e5e7eb)}.dt-it h4{margin:0 0 2px;font-size:15.5px}.dt-m{margin:0 0 6px;font-size:13px;color:var(--mu,#64748b)}.dt-pr{margin:6px 0 0;font-size:14.5px}</style>')
    page('/devtrend/', '개발·AI 트렌드 노트 — 해외 개발 뉴스레터에서 읽은 흐름 (' + D['period'] + ')',
         '코딩 에이전트, AI 에이전트 운영, 시스템 설계, LLM 추론, 개발자 고용까지. 해외 개발·AI 뉴스레터를 읽고 출처와 날짜를 밝혀 자기 말로 정리한 개발 트렌드 노트입니다.',
         body, [('홈', '/'), ('개발 트렌드 노트', '/devtrend/')])
    return ['/devtrend/']
