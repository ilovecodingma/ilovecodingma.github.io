# -*- coding: utf-8 -*-
"""시험 문제은행(/exam/bank/): 2026-11-20 사장님 지시(모든 시험). 문제 데이터는 _gongmo/exam_data/bank/<bank_id>.json
 {"id","name","exam_id"(선택, /exam/<id>/ 연결),"category","kind":"original|public","source":{"name","url","license"},"updated","questions":[{"q","choices":[..],"answer":0부터 번호,"explain","ref_url"}]}
 kind=original: 공식 자료(법령·공고)를 근거로 새로 쓴 연습문제(기출 원문 아님). kind=public: 기관이 재사용을 허용한 기출(공공누리 등)이며 source.license 를 반드시 적는다.
 화면: 한 문제씩 풀기(JS) + 자바스크립트가 없어도 읽을 수 있는 전체 목록(정답·해설 접힘). 정답은 HTML 에 있다(채점은 브라우저에서 한다).
 틀린 문제는 브라우저에 저장해 「틀린 문제만 다시」 풀 수 있게 한다(서버로 보내지 않음)."""
import glob
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
CSS = ('<style>.bk{max-width:820px;margin:0 auto;line-height:1.75}.bk h2{margin:26px 0 8px}.bk .q{border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;margin:12px 0}.bk .q b.n{color:#2563eb;margin-right:6px}'
       '.bk ol.c{margin:8px 0 0;padding-left:22px}.bk ol.c li{margin:4px 0}.bk details{margin-top:8px}.bk summary{cursor:pointer;font-weight:700;color:#2563eb}'
       '.bk .bd{display:inline-block;font-size:12px;padding:1px 8px;border-radius:999px;background:#fef3c7;color:#92400e}.bk .bd.pb{background:#dcfce7;color:#166534}'
       '.bk .nt{font-size:13px;color:#64748b}.bk .play button{display:block;width:100%;text-align:left;margin:6px 0;padding:12px 14px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;font-size:16px;cursor:pointer;min-height:44px}'
       '.bk .play button.ok{background:#dcfce7;border-color:#16a34a}.bk .play button.no{background:#fee2e2;border-color:#dc2626}.bk .play .ex{margin:10px 0;padding:10px 12px;background:#f8fafc;border-radius:8px}'
       '.bk .bar{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.bk .bar button{padding:10px 14px;border:1px solid #2563eb;border-radius:8px;background:#2563eb;color:#fff;cursor:pointer;min-height:44px}.bk .bar button.g{background:#fff;color:#2563eb}'
       '@media (prefers-color-scheme:dark){.bk .q,.bk .play button{border-color:#334155;background:transparent;color:inherit}.bk .play .ex{background:#1e293b}}</style>')
JS = r'''<script>(function(){var el=document.getElementById('bk-data');if(!el)return;var D=JSON.parse(el.textContent),Q=D.questions,key='bk_wrong_'+D.id;var box=document.getElementById('bk-play'),idx=0,score=0,order=[],wrong=[];
function sv(){try{localStorage.setItem(key,JSON.stringify(wrong))}catch(e){}}function ld(){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch(e){return[]}}
function start(list){order=list.slice();idx=0;score=0;wrong=[];show()}
function show(){if(idx>=order.length){var old=ld();box.innerHTML='<h3>결과: '+score+' / '+order.length+'</h3><p class="nt">틀린 문제 '+wrong.length+'개는 이 브라우저에만 저장돼요(서버로 보내지 않아요).</p><div class="bar"><button id="b-again">처음부터 다시</button>'+(wrong.length?'<button class="g" id="b-wr">틀린 문제만 다시</button>':'')+'</div>';document.getElementById('b-again').onclick=function(){start(Q.map(function(_,i){return i}))};var w=document.getElementById('b-wr');if(w)w.onclick=function(){start(wrong.slice())};return}
var q=Q[order[idx]],h='<p class="nt">'+(idx+1)+' / '+order.length+'</p><p><b>'+esc(q.q)+'</b></p>';q.choices.forEach(function(c,i){h+='<button data-i="'+i+'">'+(i+1)+'. '+esc(c)+'</button>'});box.innerHTML=h;
box.querySelectorAll('button').forEach(function(b){b.onclick=function(){var i=+b.getAttribute('data-i');if(i===q.answer){score++}else{wrong.push(order[idx]);sv()}
box.querySelectorAll('button').forEach(function(x){x.disabled=true;var j=+x.getAttribute('data-i');if(j===q.answer)x.className='ok';else if(j===i)x.className='no'});
var e=document.createElement('div');e.className='ex';e.innerHTML='<b>'+(i===q.answer?'정답이에요.':'정답은 '+(q.answer+1)+'번이에요.')+'</b> '+esc(q.explain||'')+(q.ref_url?' <a href="'+esc(q.ref_url)+'" target="_blank" rel="noopener nofollow">근거 보기</a>':'');box.appendChild(e);
var n=document.createElement('div');n.className='bar';n.innerHTML='<button>다음 문제</button>';box.appendChild(n);n.firstChild.onclick=function(){idx++;show()}}})}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var w0=ld();document.getElementById('bk-start').onclick=function(){start(Q.map(function(_,i){return i}))};var rb=document.getElementById('bk-redo');if(rb){if(w0.length){rb.hidden=false;rb.textContent='지난번 틀린 문제 '+w0.length+'개 다시 풀기'}rb.onclick=function(){start(ld())}}
var sh=document.getElementById('bk-shuf');if(sh)sh.onclick=function(){var a=Q.map(function(_,i){return i});for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}start(a)}})();</script>'''


def _load():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, 'exam_data', 'bank', '*.json'))):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        qs = [q for q in d.get('questions', []) if q.get('q') and isinstance(q.get('choices'), list) and len(q['choices']) >= 2 and isinstance(q.get('answer'), int) and 0 <= q['answer'] < len(q['choices'])]
        if d.get('id') and qs:
            d['questions'] = qs
            out.append(d)
    return out


def _badge(d):
    return ('<span class="bd pb">공식 공개 기출</span>' if d.get('kind') == 'public' else '<span class="bd">공식 자료 기반 유사문제</span>')


def pages(page):
    banks = _load()
    if not banks:
        return []
    urls = []
    for d in banks:
        src = d.get('source') or {}
        srct = (f'출처: <a href="{E(src["url"])}" target="_blank" rel="noopener nofollow">{E(src.get("name", "공식 자료"))}</a>' if src.get('url') else E(src.get('name', '')))
        lic = f' · 이용 조건: {E(src["license"])}' if src.get('license') else ''
        note = ('이 문제는 기출 원문이 아니라 위 공식 자료(법령·공고)를 근거로 실제 시험과 비슷한 유형으로 새로 쓴 유사문제예요. 실제 시험 문제와 다르고, 법령은 바뀔 수 있어 시험 전에 공식 자료로 한 번 더 확인하세요.'
                if d.get('kind') != 'public' else '기관이 재사용을 허용한 기출문제예요. 이용 조건을 지켜 올렸어요.')
        lst = ''
        for i, q in enumerate(d['questions'], 1):
            lst += (f'<div class="q"><p><b class="n">{i}.</b>{E(q["q"])}</p><ol class="c">' + ''.join(f'<li>{E(c)}</li>' for c in q['choices']) + '</ol>'
                    f'<details><summary>정답과 해설</summary><p>정답 {q["answer"] + 1}번. {E(q.get("explain", ""))}' + (f' <a href="{E(q["ref_url"])}" target="_blank" rel="noopener nofollow">근거 보기</a>' if q.get('ref_url') else '') + '</p></details></div>')
        eu = f'/exam/{d["exam_id"]}/' if d.get('exam_id') and os.path.exists(os.path.join(os.path.dirname(HERE), 'exam', d['exam_id'], 'index.html')) else ''
        data = json.dumps({'id': d['id'], 'questions': [{'q': q['q'], 'choices': q['choices'], 'answer': q['answer'], 'explain': q.get('explain', ''), 'ref_url': q.get('ref_url', '')} for q in d['questions']]}, ensure_ascii=False).replace('</', '<' + chr(92) + '/')
        body = (f'<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › <a href="/exam/bank/">문제은행</a> › {E(d["name"])}</p><h1>{E(d["name"])} 문제은행 {_badge(d)}</h1>'
                f'<p class="nt">{srct}{lic}</p><p>{E(note)}</p>' + (f'<p><a href="{eu}">이 시험의 일정·접수·발표일 보기 →</a></p>' if eu else '')
                + f'<div class="play" id="bk-play"><div class="bar"><button id="bk-start">문제 {len(d["questions"])}개 풀기 시작</button><button class="g" id="bk-shuf">섞어서 풀기</button><button class="g" id="bk-redo" hidden>지난번 틀린 문제 다시</button></div></div>'
                f'<h2>전체 문제 보기</h2>{lst}<script type="application/json" id="bk-data">{data}</script>' + '</div>' + CSS + JS)
        page(f'/exam/bank/{d["id"]}/', f'{d["name"]} 문제은행 — 무료 연습문제 {len(d["questions"])}개 — 루리 줍줍', f'{d["name"]} 연습문제 {len(d["questions"])}개를 한 문제씩 풀고 정답·해설과 근거를 확인합니다. 틀린 문제만 다시 풀 수 있어요.', body,
             [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/'), (d['name'], f'/exam/bank/{d["id"]}/')])
        urls.append(f'/exam/bank/{d["id"]}/')
    li = ''.join(f'<li><a href="/exam/bank/{E(d["id"])}/"><b>{E(d["name"])}</b></a> {_badge(d)} <small>문제 {len(d["questions"])}개</small></li>' for d in banks)
    hub = ('<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › 문제은행</p><h1>시험 문제은행</h1>'
           '<p>자격증·공무원·수능 등 시험별 연습문제를 한 문제씩 풀고 해설을 확인합니다. 기출문제를 옮기지 않고, 실제 시험과 비슷한 유형으로 공식 자료(법령·공고)를 근거로 새로 쓴 유사문제만 올리며, 문제마다 근거 링크를 답니다. 시험이 계속 늘어납니다.</p>'
           f'<ul>{li}</ul></div>' + CSS)
    page('/exam/bank/', '시험 문제은행 — 자격증·공무원·수능 무료 연습문제 — 루리 줍줍', '자격증·공무원·수능 시험별 연습문제를 풀고 정답과 해설, 근거 링크를 확인합니다. 틀린 문제만 다시 풀 수 있어요.', hub, [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/')])
    urls.append('/exam/bank/')
    print('시험 문제은행', len(banks), '종')
    return urls
