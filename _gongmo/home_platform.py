# -*- coding: utf-8 -*-
"""사이트 메인(/) — 「가난한 박과장」: 하네스 기반으로 새 LMS(수업 사이트)를 운영하는 곳.
2026-11-13 사용자: 「메인을 교육 플랫폼으로」「루리는 하나의 포트폴리오고 내가 메인이야, 가난한 박과장으로」
「가난한 박과장이 만든 루리 서비스가 되는 거야, 정보성 사이트」「가난한 박과장에서 루리로 하나의 서비스가 보이는 거임」.
기존 주소는 그대로 둔다. 예전 홈(루리 줍줍)은 /ruri/ 로 옮긴다. 켜는 스위치: _gongmo/platform_home.on (없으면 예전 홈 그대로).
지침(총괄지침_1113): 정답·진도를 강요하지 않는다, 완성된 서비스를 약속하지 않는다, 성과 수치·반응을 지어내지 않는다."""
import html

E = html.escape

CSS = ('<style>.pk{max-width:920px}.pk h1{margin:6px 0 10px;font-size:clamp(28px,6vw,40px);line-height:1.25}'
       '.pk .lead{font-size:clamp(16px,2.6vw,18.5px);line-height:1.75;margin:0 0 18px;max-width:46em}'
       '.pk .cta{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 6px}.pk .cta a{padding:13px 20px;border-radius:12px;font-weight:700;font-size:16px;text-decoration:none;border:1px solid var(--pri,#6d28d9)}'
       '.pk .cta a.p{background:var(--pri,#6d28d9);color:#fff}.pk .cta a.s{color:var(--pri,#6d28d9);background:transparent}'
       '.pk .fine{color:var(--mu,#64748b);font-size:14px;margin:8px 0 0}.pk h2{margin:34px 0 12px;font-size:22px}'
       '.pk .st{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:0;padding:0;list-style:none;counter-reset:s}'
       '.pk .st li{border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff);padding:16px 16px 14px;counter-increment:s}'
       '.pk .st li:before{content:counter(s);display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--pbg,#f1ecff);color:var(--pri,#6d28d9);font-weight:700;font-size:14px;margin-bottom:8px}'
       '.pk .st b{display:block;font-size:16.5px;margin-bottom:4px}.pk .st span{font-size:14.5px;line-height:1.65;color:var(--mu,#475569)}'
       '.pk .st a{display:block;margin-top:8px;font-size:14.5px;font-weight:600}'
       '.pk .sv{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}'
       '.pk .sv a{display:block;border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff);padding:16px 18px;text-decoration:none;color:inherit}'
       '.pk .sv a:hover{border-color:var(--pri,#6d28d9)}.pk .sv .t{display:inline-block;font-size:12.5px;font-weight:700;color:var(--pri,#6d28d9);background:var(--pbg,#f1ecff);border-radius:999px;padding:2px 10px;margin-bottom:6px}'
       '.pk .sv b{display:block;font-size:18px;margin:2px 0 6px}.pk .sv span.pd{font-size:14.5px;line-height:1.65;color:var(--mu,#475569);display:block}'
       '.pk .sv .go{display:block;margin-top:10px;font-size:14px;font-weight:600;color:var(--pri,#6d28d9)}'
       '.pk ul.rd{margin:0;padding:0;list-style:none;display:grid;gap:8px}.pk ul.rd li{border-bottom:1px solid var(--bd,#e5e7eb);padding:8px 0}.pk ul.rd time{color:var(--mu,#64748b);font-size:13px;margin-right:8px}'
       '</style>')


def home_html(devs):
    """devs: [(제목, 주소, 날짜)] 최신 개발 기록 몇 건."""
    reads = ''.join(f'<li><time>{E(d)}</time><a href="{E(u)}">{E(t)}</a></li>' for t, u, d in devs)
    return (CSS + '<div class="pk"><p class="bc">가난한 박과장</p>'
            '<h1>가난한 박과장 — 퇴근 후 2~3시간, AI 에이전트와 내 서비스를 만들어 봅니다</h1>'
            '<p class="lead">AI 사용법을 가르치는 곳이 아닙니다. 하네스(저자가 쓰는 에이전트 개발 환경)를 열고 한 줄로 시킨 뒤 첫 결과물을 보는 데까지 도와드립니다. 그다음은 정해진 진도도 정답도 없습니다. 막히면 저자가 실제로 겪은 비슷한 일을 찾아보고, 원하면 내 경험도 남기세요.</p>'
            '<div class="cta"><a class="p" href="/park/#start">하네스로 시작하기</a><a class="s" href="/park/">비슷한 저자 사례 찾기</a></div>'
            '<p class="fine">안내는 Windows 기준입니다. 2~3시간 안에 첫 결과물을 보는 것이 목표이고, 완성은 그다음 이야기입니다.</p>'
            '<h2>이렇게 써 보세요 <small style="font-weight:400;color:var(--mu,#64748b);font-size:15px">순서를 강제하지 않습니다</small></h2>'
            '<ol class="st">'
            '<li><b>하네스로 먼저 하나 만든다</b><span>빈 폴더에서 한 줄을 넣고, 첫 결과물이 나오는 것까지 봅니다.</span><a href="/park/#start">시작 안내 →</a></li>'
            '<li><b>막히면 찾아본다</b><span>증상으로 찾거나, 지금 상황을 한 줄로 적으면 저자의 비슷한 사례를 보여 줍니다.</span><a href="/park/stuck/">증상으로 찾기 →</a><a href="/park/">사례 찾기 →</a></li>'
            '<li><b>저자가 겪은 일을 본다</b><span>한 달 동안 실제로 운영하며 겪은 기록을 가려서 공개했습니다. 정답이 아니라 자료입니다.</span><a href="/park/archive/">운영 기록 →</a></li>'
            '<li><b>원하면 이야기방에 남긴다</b><span>공유는 선택입니다. 올린 글은 운영자가 확인한 것만 실립니다.</span><a href="/park/#talk">이야기방 →</a></li></ol>'
            '<h2>가난한 박과장이 만든 서비스</h2>'
            '<p class="fine" style="margin:0 0 12px">모두 저자가 AI 에이전트와 함께 만들고 직접 운영합니다. 이 기록이 수업의 재료입니다.</p>'
            '<div class="sv">'
            '<a href="/ruri/"><span class="t">정보성 사이트</span><b>루리 줍줍</b><span class="pd">이슈, 생활 돈 가이드·계산기, 지원금, 공모전, 레시피를 출처와 함께 정리하고 매시간 갱신합니다.</span><span class="go">루리 줍줍 열기 →</span></a>'
            '<a href="/wiki/"><span class="t">문서 모음</span><b>루리 위키</b><span class="pd">생활 돈 가이드, 응모 가이드, 개발 지식을 문서 형식으로 묶어 둔 곳입니다.</span><span class="go">위키 열기 →</span></a>'
            '<a href="/dev/"><span class="t">개발 기록</span><b>개발 지식</b><span class="pd">직접 만들고 고치며 확인한 방법을 근거와 함께 적은 글입니다.</span><span class="go">글 보기 →</span></a></div>'
            + '<p class="fine" style="margin-top:14px">루리는 이미지 모델을 파인튜닝하다가 그림이 잘 나와서 버리기 아까워 만든 캐릭터입니다. AI로 만든 마스코트이고, 사이트에서 말을 거는 역할만 합니다.</p>'
            + (f'<h2>최근 개발 기록</h2><ul class="rd">{reads}</ul>' if reads else '')
            + '<p class="fine" style="margin-top:28px">수업 사이트는 책 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』와 짝입니다. 책은 참고서이고, 주인공은 하네스입니다.</p></div>')
