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
       '.bk .ai{padding:10px 14px;border-radius:10px;background:#eef0ff;border:1px solid #c7cdf5;color:#26336a;font-size:14px}.bk .ai b{color:#4f5bd5}.bk .ru{display:flex;gap:10px;align-items:center;margin:8px 0 10px;padding:10px 12px;background:#1a2340;border-radius:12px 12px 12px 4px;color:#e5e9f5}.bk .ru img{flex:0 0 auto;border-radius:8px}.bk .ru p{margin:0;font-weight:700}.bk .clk{font-weight:800;font-size:18px;color:#b8235a;margin:0 0 4px}'
       '@media (prefers-color-scheme:dark){.bk .q,.bk .play button{border-color:#334155;background:transparent;color:inherit}.bk .play .ex{background:#1e293b}}</style>')
JS = r'''<script>(function(){var el=document.getElementById('bk-data');if(!el)return;var D=JSON.parse(el.textContent),Q=D.questions,key='bk_wrong_'+D.id;var box=document.getElementById('bk-play'),idx=0,score=0,order=[],wrong=[],timed=false,ans={},tleft=0,tmr=null,tstart=0;
var IMG='/assets/ruri/sn_smirk_s.webp',FB='/assets/ruri/o_present_s.webp';
var WR=['이걸 틀려? 지금 자면 라면 값 오르는 소리 들릴 텐데.','보기에 답이 있었는데 못 찾았네. 눈은 장식이냐?','이건 중학생도 맞히겠다. 진짜로.','틀렸어. 학점도 월급도 이 모양인 이유가 있네.','응, 틀렸어. 해설 읽어. 읽으라고 써 놓은 거니까.','아깝지도 않아. 그냥 몰랐던 거잖아.','시험장에서 이러느니 지금 틀리는 게 낫지. 뭐, 시험장에서도 그럴 수 있겠지만.','이 정도는 외우고 와야지. 누가 대신 풀어 주냐?'];
var RT=['…우연이지? 다음 문제 가.','맞혔네. 한 문제야. 기뻐하긴 일러.','흥, 이건 쉬운 거였어.','한 문제 맞혔다고 이 나라에서 살아남는 건 아니야.'];
function pick(a){return a[Math.floor(Math.random()*a.length)]}
function ru(t){return '<div class="ru"><img src="'+IMG+'" width="56" height="78" alt="비웃는 루리" onerror="this.onerror=null;this.src=\''+FB+'\'"><p>'+esc(t)+'</p></div>'}
function sv(){try{localStorage.setItem(key,JSON.stringify(wrong))}catch(e){}}function ld(){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch(e){return[]}}
function fmt(s){s=Math.max(0,s);var m=Math.floor(s/60),r=s%60;return m+':'+(r<10?'0':'')+r}
function intro(list,t){var m=Math.round(list.length*(D.sec_per_q||60)/60);box.innerHTML='<div class="ai"><b>읽고 시작해</b><br>해당 모든 문제는 멀티 에이전트(AI)들이 기출문제를 서치해 분석한 뒤 다시 개편한 문제야. 처음부터 만든 게 아니야. 실제 시험이랑 달라. 시험 전에 공식 자료로 한 번 더 확인해.</div>'+(t?'<p class="nt">실전 모드: 실제 시험의 문항당 시간 기준으로 <b>'+m+'분</b> 안에 '+list.length+'문항을 풀어. 정답은 끝난 뒤에 공개되고, 시간이 끝나면 자동으로 채점돼.</p>':'<p class="nt">연습 모드: 풀면 바로 정답 나와.</p>')+'<div class="bar"><button id="b-go">'+(t?'⏱ 시험 시작':'풀기 시작')+'</button><button class="g" id="b-no">취소</button></div>';document.getElementById('b-go').onclick=function(){start(list,t)};document.getElementById('b-no').onclick=function(){location.reload()}}
function start(list,t){order=list.slice();idx=0;score=0;wrong=[];ans={};timed=!!t;clearInterval(tmr);if(timed){tleft=Math.round(order.length*(D.sec_per_q||60));tstart=Date.now();tmr=setInterval(function(){tleft--;var e=document.getElementById('bk-clock');if(e)e.textContent='남은 시간 '+fmt(tleft);if(tleft<=0){clearInterval(tmr);finish(true)}},1000)}show()}
function verdict(p,to){if(to)return '시간 초과. 실전에선 기다려 주는 사람 없어.';if(p>=90)return '…인정은 안 해. 실전에서도 이래야 돼.';if(p>=70)return '그 정도로 합격하면 다행이지. 틀린 거나 다시 풀어.';if(p>=40)return '이 점수로 시험 보면 내년에 또 만나겠네.';return '솔직히 말할까? 기초부터 다시 해. 틀린 문제부터.'}
function finish(to){clearInterval(tmr);if(timed){score=0;wrong=[];order.forEach(function(qi){if(ans[qi]===Q[qi].answer)score++;else wrong.push(qi)});sv()}
var p=Math.round(score*100/order.length),used=timed?Math.round((Date.now()-tstart)/1000):0;
box.innerHTML='<h3>결과: '+score+' / '+order.length+' ('+p+'점)'+(timed?' · 걸린 시간 '+fmt(used):'')+'</h3>'+ru(verdict(p,to))+'<p class="nt">틀린 문제 '+wrong.length+'개는 이 브라우저에만 저장돼(서버로 안 보내).</p>'+(timed&&wrong.length?'<details open><summary>틀린 문제 해설</summary>'+wrong.map(function(qi){var q=Q[qi];return '<p><b>'+esc(q.q)+'</b><br>내 답: '+(ans[qi]===undefined?'미응답':(ans[qi]+1)+'번')+' · 정답 '+(q.answer+1)+'번. '+esc(q.explain||'')+'</p>'}).join('')+'</details>':'')+'<div class="bar"><button id="b-again">연습으로 다시</button><button class="g" id="b-t">실전 모드 다시</button>'+(wrong.length?'<button class="g" id="b-wr">틀린 문제만 다시</button>':'')+'</div>';
document.getElementById('b-again').onclick=function(){start(Q.map(function(_,i){return i}),false)};document.getElementById('b-t').onclick=function(){start(Q.map(function(_,i){return i}),true)};var w=document.getElementById('b-wr');if(w)w.onclick=function(){start(wrong.slice(),false)}}
function show(){if(idx>=order.length){finish(false);return}
var q=Q[order[idx]],h=(timed?'<p class="clk" id="bk-clock">남은 시간 '+fmt(tleft)+'</p>':'')+'<p class="nt">'+(idx+1)+' / '+order.length+(timed?' · 실전 모드(정답은 마지막에 공개)':'')+'</p><p><b>'+esc(q.q)+'</b></p>';q.choices.forEach(function(c,i){h+='<button data-i="'+i+'">'+(i+1)+'. '+esc(c)+'</button>'});box.innerHTML=h;
box.querySelectorAll('button').forEach(function(b){b.onclick=function(){var i=+b.getAttribute('data-i');
if(timed){ans[order[idx]]=i;idx++;show();return}
if(i===q.answer){score++}else{wrong.push(order[idx]);sv()}
box.querySelectorAll('button').forEach(function(x){x.disabled=true;var j=+x.getAttribute('data-i');if(j===q.answer)x.className='ok';else if(j===i)x.className='no'});
var e=document.createElement('div');e.className='ex';e.innerHTML=ru(i===q.answer?pick(RT):pick(WR))+'<b>'+(i===q.answer?'정답.':'정답은 '+(q.answer+1)+'번이야.')+'</b> '+esc(q.explain||'')+(q.ref_url?' <a href="'+esc(q.ref_url)+'" target="_blank" rel="noopener nofollow">근거 보기</a>':'');box.appendChild(e);
var n=document.createElement('div');n.className='bar';n.innerHTML='<button>다음 문제</button>';box.appendChild(n);n.firstChild.onclick=function(){idx++;show()}}})}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var all=function(){return Q.map(function(_,i){return i})};var w0=ld();document.getElementById('bk-start').onclick=function(){intro(all(),false)};var tb=document.getElementById('bk-timed');if(tb)tb.onclick=function(){intro(all(),true)};var rb=document.getElementById('bk-redo');if(rb){if(w0.length){rb.hidden=false;rb.textContent='지난번 틀린 문제 '+w0.length+'개 다시 풀기'}rb.onclick=function(){intro(ld(),false)}}
var sh=document.getElementById('bk-shuf');if(sh)sh.onclick=function(){var a=all();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}intro(a,false)}})();</script>'''


TIME_SEC = [('csat-math', 200), ('csat-english', 55), ('csat-', 60), ('toeic', 45), ('realtor', 150), ('korean-history', 84), ('sqld', 108), ('adsp', 108), ('engineer-info', 90), ('aws', 83), ('driver', 60)]   # 실제 시험의 문항당 시간(초) 기준 안. 은행 파일의 sec_per_q 가 있으면 그것을 쓴다.


def _sec(d):
    if isinstance(d.get('sec_per_q'), (int, float)) and d['sec_per_q'] > 0:
        return int(d['sec_per_q'])
    return next((v for k, v in TIME_SEC if d['id'].startswith(k)), 60)


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
    return ('<span class="bd pb">공식 공개 기출</span>' if d.get('kind') == 'public' else ('<span class="bd">AI가 기출을 분석해 개편한 문제</span>' if d.get('method') == 'rework' else '<span class="bd">공식 자료 기반 유사문제</span>'))


def pages(page):
    banks = _load()
    if not banks:
        return []
    urls = []
    for d in banks:
        src = d.get('source') or {}
        srct = (f'출처: <a href="{E(src["url"])}" target="_blank" rel="noopener nofollow">{E(src.get("name", "공식 자료"))}</a>' if src.get('url') else E(src.get('name', '')))
        lic = f' · 이용 조건: {E(src["license"])}' if src.get('license') else ''
        note = (('해당 모든 문제는 멀티 에이전트(AI)들이 기출문제를 서치해 분석한 뒤 다시 개편한 문제야. 처음부터 만든 게 아니고, 실제 시험이랑 달라. 법령은 시험 전에 다시 확인해.'
                 if d.get('method') == 'rework' else '기출 원문 아니야. 공식 자료 보고 새로 쓴 유사문제. 법령은 시험 전에 다시 확인해.')
                if d.get('kind') != 'public' else '기관이 재사용을 허용한 기출문제야. 이용 조건을 지켜서 올렸어.')
        lst = ''
        for i, q in enumerate(d['questions'], 1):
            lst += (f'<div class="q"><p><b class="n">{i}.</b>{E(q["q"])}</p><ol class="c">' + ''.join(f'<li>{E(c)}</li>' for c in q['choices']) + '</ol>'
                    f'<details><summary>정답과 해설</summary><p>정답 {q["answer"] + 1}번. {E(q.get("explain", ""))}' + (f' <a href="{E(q["ref_url"])}" target="_blank" rel="noopener nofollow">근거 보기</a>' if q.get('ref_url') else '') + '</p></details></div>')
        eu = f'/exam/{d["exam_id"]}/' if d.get('exam_id') and os.path.exists(os.path.join(os.path.dirname(HERE), 'exam', d['exam_id'], 'index.html')) else ''
        data = json.dumps({'id': d['id'], 'sec_per_q': _sec(d), 'method': d.get('method', ''), 'questions': [{'q': q['q'], 'choices': q['choices'], 'answer': q['answer'], 'explain': q.get('explain', ''), 'ref_url': q.get('ref_url', '')} for q in d['questions']]}, ensure_ascii=False).replace('</', '<' + chr(92) + '/')
        AINOTE = ('<p class="ai"><b>AI 개편 문제</b> · 기출을 분석해서 AI가 다시 개편했어. 처음부터 만든 거 아니야.</p>' if d.get('method') == 'rework' else '')
        body = (f'<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › <a href="/exam/bank/">문제은행</a> › {E(d["name"])}</p><h1>{E(d["name"])} 문제은행 {_badge(d)}</h1>'
                f'<p class="nt">{srct}{lic}</p>{AINOTE}<p>{E(note)}</p>' + (f'<p><a href="{eu}">이 시험의 일정·접수·발표일 보기 →</a></p>' if eu else '')
                + f'<div class="play" id="bk-play"><div class="bar"><button id="bk-start">문제 {len(d["questions"])}개 풀기 시작</button><button id="bk-timed">⏱ 실전 모드 · {len(d["questions"]) * _sec(d) // 60}분 안에 풀기</button><button class="g" id="bk-shuf">섞어서 풀기</button><button class="g" id="bk-redo" hidden>지난번 틀린 문제 다시</button></div></div>'
                f'<h2>전체 문제 보기</h2>{lst}<script type="application/json" id="bk-data">{data}</script>' + '</div>' + CSS + JS)
        page(f'/exam/bank/{d["id"]}/', f'{d["name"]} 문제은행 — 무료 연습문제 {len(d["questions"])}개 — 가난한 박과장', f'{d["name"]} 연습문제 {len(d["questions"])}개(멀티 에이전트가 기출문제를 분석해 다시 개편한 문제)를 한 문제씩 풀고 정답·해설과 근거를 확인해. 틀린 문제만 다시 풀 수 있어.', body,
             [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/'), (d['name'], f'/exam/bank/{d["id"]}/')])
        urls.append(f'/exam/bank/{d["id"]}/')
    li = ''.join(f'<li><a href="/exam/bank/{E(d["id"])}/"><b>{E(d["name"])}</b></a> {_badge(d)} <small>문제 {len(d["questions"])}개</small></li>' for d in banks)
    hub = ('<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › 문제은행</p><h1>시험 문제은행</h1>'
           '<p>시험별 연습문제. 풀고 해설 봐. 멀티 에이전트(AI)들이 기출문제를 서치해 분석한 뒤 다시 개편한 문제이며, 기출 원문 그대로가 아닙니다.</p>'
           f'<ul>{li}</ul></div>' + CSS)
    page('/exam/bank/', '시험 문제은행 — 자격증·공무원·수능 무료 연습문제 — 가난한 박과장', '자격증·공무원·수능 시험별 연습문제를 풀고 정답과 해설, 근거 링크를 확인해. 틀린 문제만 다시 풀 수 있어.', hub, [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/')])
    urls.append('/exam/bank/')
    print('시험 문제은행', len(banks), '종')
    return urls
