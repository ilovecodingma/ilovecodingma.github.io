# -*- coding: utf-8 -*-
"""가난한 박과장의 서비스팀 수업(/park/) — 책·하네스와 짝이 되는 구역.
2026-11-12 사용자: 「수업 진도 같은 건 개나 줘, 그 상황에 유사한 저자 사례 찾기 그런 기능을 만들어. 거기도 하네스로 만들어 놓고 데이터들 정리해 놓고」
「AI가 하네스 기반으로 분석한 글을 사용자가 허락하면 후기 형식으로 사용자 AI가 올리고 우리는 그것도 갱신하는 형태로, 그렇게 커뮤니티를 조성」.
/park/          사례 찾기(지금 겪는 상황 → 저자가 실제로 겪은 비슷한 사례) + 독자 후기
/park/start/    예전 진도 화면 주소 — 사례 찾기로 넘긴다(책·하네스에 이미 적힌 주소가 죽지 않게)
/park/archive/  운영 기록 보관소(원문 50개 + 흐름 28편)
자료: park/cases.json(사례 55건, scratchpad make_cases.py 가 흐름 원고에서 뽑음) · park/archive/index.json. 사람·하네스가 같은 파일을 읽는다.
후기: 별도 워커 jupjup-lms(_gongmo/lms/)가 받는다. 토큰이 있어야 올릴 수 있고, 운영자가 확인(review_admin.py)한 것만 보인다."""
import json, os, html

E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CSS = ('<style>.hx{max-width:880px}.hx-q{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 10px}'
       '.hx-q input{flex:1;min-width:220px;padding:13px 15px;border:1px solid var(--bd,#d7d5ea);border-radius:12px;background:var(--bg,#fff);color:var(--tx,#1e1b4b);font-size:17px}'
       '.hx-q input:focus{outline:0;border-color:var(--pri,#6d28d9);box-shadow:0 0 0 3px color-mix(in srgb,var(--pri,#6d28d9) 22%,transparent)}'
       '.hx-q button,.hx-btn{padding:12px 18px;border:0;border-radius:12px;background:var(--pri,#6d28d9);color:#fff;font-weight:700;font-size:15px;cursor:pointer;text-decoration:none;display:inline-block}'
       '.hx-ch{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 4px}.hx-ch button{padding:8px 13px;border:1px solid var(--bd,#d7d5ea);border-radius:999px;background:transparent;color:var(--tx,#1e1b4b);font-size:14px;cursor:pointer}'
       '.hx-ch button small{color:var(--mu,#64748b);margin-left:4px}.hx-ch button[aria-pressed=true]{background:var(--pri,#6d28d9);border-color:var(--pri,#6d28d9);color:#fff}.hx-ch button[aria-pressed=true] small{color:#fff}'
       '.hx-ex{color:var(--mu,#64748b);font-size:14px;margin:2px 0 14px}.hx-ex a{margin-right:10px;cursor:pointer}'
       '.hx-n{color:var(--mu,#64748b);font-size:14px;margin:14px 0 8px;min-height:20px}'
       '.hx-c{border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff);margin:12px 0;overflow:hidden}'
       '.hx-c .hd{padding:14px 18px 12px}.hx-c .tg{display:inline-block;font-size:12.5px;font-weight:700;color:var(--pri,#6d28d9);background:var(--pbg,#f1ecff);border-radius:999px;padding:2px 10px;margin-right:8px}'
       '.hx-c time{font-size:13px;color:var(--mu,#64748b)}.hx-c h3{margin:8px 0 6px;font-size:18px;line-height:1.4;border:0;padding:0}.hx-c p{margin:6px 0;font-size:15px;line-height:1.65;white-space:pre-line}'
       '.hx-c .rs{border-left:3px solid var(--pri,#6d28d9);padding-left:12px;margin-top:10px}.hx-c .rs b{display:block;font-size:13px;color:var(--pri,#6d28d9)}'
       '.hx-c details{border-top:1px solid var(--bd,#e5e7eb);padding:10px 18px 14px}.hx-c summary{cursor:pointer;color:var(--pri,#6d28d9);font-weight:600;font-size:14.5px}'
       '.hx-c ol{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:8px}.hx-c li{display:grid;grid-template-columns:132px minmax(0,1fr);gap:10px;font-size:14.5px;line-height:1.6}'
       '.hx-c li b{color:var(--mu,#64748b);font-weight:600;font-size:13px}.hx-c .nt{color:var(--mu,#64748b);font-size:13.5px;margin-top:10px}.hx-c .go{display:inline-block;margin-top:10px;font-size:14px}'
       '.hx-c .rl a{display:inline-block;font-size:13px;margin:6px 8px 0 0}'
       '.hx-smp{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:8px}.hx-smp a{display:block;padding:11px 14px;border:1px solid var(--bd,#e5e7eb);border-radius:10px;text-decoration:none;color:inherit}.hx-smp a:hover{border-color:var(--pri,#6d28d9)}'
       '.tblw{overflow-x:auto;margin:10px 0;border:1px solid var(--bd,#e5e7eb);border-radius:12px}.xt{border-collapse:separate;border-spacing:0;width:100%;font-size:14.5px}.xt td{padding:9px 12px;border-top:1px solid var(--bd,#e5e7eb)}.xt tr:first-child td{border-top:0}'
       '@media(max-width:640px){.hx-c li{grid-template-columns:1fr;gap:0}}</style>')

JS = r"""(function(){var D=window.__HX,C=D.cases,CL=D.clusters,name={},byid={},q=document.getElementById("hxq"),box=document.getElementById("hxr"),nn=document.getElementById("hxn"),cur="";
CL.forEach(function(c){name[c.key]=c.name});C.forEach(function(c){byid[c.id]=c});
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function grams(s){s=s.toLowerCase().replace(/[^0-9a-z가-힣]+/g," ").trim();var o=[];s.split(" ").forEach(function(w){if(!w)return;if(w.length<=2){o.push(w);return}for(var i=0;i<w.length-1;i++)o.push(w.substr(i,2))});return o}
C.forEach(function(c){c._t=(c.title+" "+name[c.cluster]).toLowerCase();c._s=(c.situation+" "+c.from).toLowerCase();c._b=(c.steps.map(function(s){return s.what}).join(" ")+" "+c.result+" "+c.note).toLowerCase()});
function cnt(h,g){var n=0,i=0;while((i=h.indexOf(g,i))>=0){n++;i+=g.length}return n}
function score(c,G){var s=0;G.forEach(function(g){s+=Math.min(cnt(c._t,g),2)*5+Math.min(cnt(c._s,g),3)*3+Math.min(cnt(c._b,g),4)});return s}
function card(c){return '<article class="hx-c" id="case-'+esc(c.id)+'"><div class="hd"><span class="tg">'+esc(name[c.cluster])+'</span><time>'+esc(c.when)+'</time><h3>'+esc(c.title)+'</h3>'+(c.situation?'<p>'+esc(c.situation)+'</p>':'')
 +(c.result?'<p class="rs"><b>어떻게 끝났나</b>'+esc(c.result)+'</p>':'')+'</div><details><summary>걸음 '+c.steps.length+'개 보기</summary><ol>'+c.steps.map(function(s){return '<li><b>'+esc(s.who)+'</b><span>'+esc(s.what)+'</span></li>'}).join("")+'</ol>'
 +(c.note?'<p class="nt">'+esc(c.note)+'</p>':'')+'<a class="go" href="'+esc(c.url)+'">흐름 그림으로 보기 →</a></details></article>'}
function draw(){var v=q.value.trim(),L=C.filter(function(c){return !cur||c.cluster===cur||(c.also||[]).indexOf(cur)>=0});
 if(v){var G=grams(v);L=L.map(function(c){return[score(c,G),c]}).filter(function(x){return x[0]>0}).sort(function(a,b){return b[0]-a[0]}).slice(0,10).map(function(x){return x[1]})}
 else if(!cur){box.innerHTML="";nn.textContent="상황을 적거나 아래 묶음을 고르면 저자가 실제로 겪은 사례가 나옵니다. 사례는 모두 "+C.length+"건입니다.";return}
 nn.textContent=L.length?(v?"비슷한 사례 "+L.length+"건(가까운 순)":name[cur]+" — "+L.length+"건"):"비슷한 사례를 찾지 못했습니다. 낱말을 바꾸거나 아래 묶음에서 골라 보세요.";
 box.innerHTML=L.map(card).join("")}
function pick(k){cur=k;document.querySelectorAll(".hx-ch button").forEach(function(x){x.setAttribute("aria-pressed",x.dataset.k===cur)})}
document.querySelectorAll(".hx-ch button").forEach(function(b){b.onclick=function(){pick(cur===b.dataset.k?"":b.dataset.k);draw()}});
document.getElementById("hxf").onsubmit=function(e){e.preventDefault();draw()};q.oninput=draw;
document.querySelectorAll(".hx-ex a").forEach(function(a){a.onclick=function(){q.value=a.textContent;draw();q.focus()}});
var u=new URLSearchParams(location.search);if(u.get("q")){q.value=u.get("q")}if(u.get("c")&&name[u.get("c")])pick(u.get("c"));draw();
var rv=document.getElementById("hxv"),rn=document.getElementById("hxvn");
fetch(D.api+"/lms/reviews").then(function(r){return r.json()}).then(function(j){var L=(j&&j.reviews)||[],R={};((j&&j.replies)||[]).forEach(function(x){(R[x.parent]=R[x.parent]||[]).push(x)});
 if(!L.length){rn.textContent="아직 올라온 후기가 없습니다. 하네스에서 세션에게 「이 분석을 후기로 올려 줘」라고 말하면, 확인을 거쳐 여기에 실립니다.";return}
 rn.textContent="올라온 글 "+L.length+"건(새 것부터)";
 rv.innerHTML=L.map(function(r){var d=new Date(r.ts),rel=(r.cases||[]).filter(function(i){return byid[i]}).map(function(i){return '<a href="'+esc(byid[i].url)+'">관련 사례: '+esc(byid[i].title)+'</a>'}).join("");
  return '<article class="hx-c"><div class="hd"><span class="tg">독자 후기</span><time>'+d.getFullYear()+"."+(d.getMonth()+1)+"."+d.getDate()+(r.nick?" · "+esc(r.nick):"")+'</time><h3>'+esc(r.title)+'</h3><p>'+esc(r.body)+'</p><div class="rl">'+rel+'</div></div>'+(R[r.id]?'<details open><summary>답 '+R[r.id].length+'개</summary><ol>'+R[r.id].map(function(x){var e=new Date(x.ts);return '<li><b>'+(x.by==="author"?"저자 쪽 세션":esc(x.nick||"독자의 세션"))+" · "+(e.getMonth()+1)+"."+e.getDate()+'</b><span style="white-space:pre-line">'+esc(x.body)+'</span></li>'}).join("")+'</ol></details>':'')+'</article>'}).join("")}).catch(function(){rn.textContent="후기를 지금은 불러올 수 없습니다."})})()"""


STUCK_CSS = ('<style>.sk{max-width:880px}.sk-q{display:flex;gap:8px;margin:14px 0}.sk-q input{flex:1;min-width:200px;padding:12px 14px;border:1px solid var(--bd,#d7d5ea);border-radius:12px;background:var(--bg,#fff);color:var(--tx,#1e1b4b);font-size:16px}'
             '.sk details{border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff);margin:10px 0;padding:0}.sk summary{cursor:pointer;padding:14px 18px;font-weight:700;font-size:17px}'
             '.sk summary small{color:var(--mu,#64748b);font-weight:400;margin-left:6px}.sk .it{border-top:1px solid var(--bd,#e5e7eb);padding:12px 18px}.sk .it h3{margin:0 0 6px;font-size:16px;line-height:1.5;border:0;padding:0}'
             '.sk .it dl{margin:0;display:grid;grid-template-columns:84px minmax(0,1fr);gap:4px 10px;font-size:14.5px;line-height:1.65}.sk .it dt{color:var(--mu,#64748b);font-weight:600;font-size:13px}.sk .it dd{margin:0}'
             '.sk .rel{padding:10px 18px 14px;border-top:1px solid var(--bd,#e5e7eb);font-size:14px;color:var(--mu,#64748b)}.sk .none{display:none}.cp{margin-left:8px;padding:3px 10px;border:1px solid var(--bd,#d7d5ea);border-radius:999px;background:transparent;color:var(--pri,#6d28d9);font-size:12.5px;cursor:pointer;white-space:nowrap}.sk .tm{border-top:1px solid var(--bd,#e5e7eb);padding:12px 18px}.sk .tm h3{margin:0 0 4px;font-size:16px;border:0;padding:0}.sk .tm p{margin:4px 0;font-size:14.5px;line-height:1.65}.sk .tm .q{background:var(--pbg,#f1ecff);border-radius:10px;padding:8px 12px}.sk .tm.none,.sk .tmw.none{display:none}</style>')
COPY_JS = ('<script>document.addEventListener("click",function(e){var b=e.target.closest(".cp");if(!b)return;var t=b.getAttribute("data-t");function ok(){var o=b.textContent;b.textContent="복사했습니다";setTimeout(function(){b.textContent=o},1500)}if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,function(){})}else{var a=document.createElement("textarea");a.value=t;document.body.appendChild(a);a.select();try{document.execCommand("copy");ok()}catch(x){}document.body.removeChild(a)}})</script>')
STUCK_JS = ("""<script>(function(){var q=document.getElementById("skq"),its=[].slice.call(document.querySelectorAll(".sk .it")),ds=[].slice.call(document.querySelectorAll(".sk details")),n=document.getElementById("skn");
function bi(s){s=s.replace(/\s+/g,"");var o=[];for(var i=0;i<s.length-1;i++)o.push(s.substr(i,2));return o}
q.addEventListener("input",function(){var v=q.value.trim();if(!v){its.forEach(function(e){e.classList.remove("none")});ds.forEach(function(d){d.classList.remove("none")});n.textContent="";return}
var b=bi(v);var hit=0;its.forEach(function(e){var t=e.textContent.replace(/\s+/g,"");var m=b.length?b.filter(function(x){return t.indexOf(x)>=0}).length/b.length:0;var ok=m>=0.5||(b.length===0&&t.indexOf(v)>=0);e.classList.toggle("none",!ok);if(ok)hit++});
ds.forEach(function(d){var any=d.querySelector(".it:not(.none)");d.classList.toggle("none",!any);if(any)d.open=true});n.textContent=hit?hit+"건":"맞는 증상이 없습니다. 사례 찾기에서 상황으로 찾아보세요."})})()</script>""")


def stuck_page(page, crumbs):
    sf, mf = os.path.join(ROOT, 'park', 'symptoms.json'), os.path.join(ROOT, 'park', 'map.json')
    if not (os.path.exists(sf) and os.path.exists(mf)):
        return
    rows = json.load(open(sf, encoding='utf-8')); mp = json.load(open(mf, encoding='utf-8'))
    order = []
    for r in rows:
        if r['묶음'] not in order:
            order.append(r['묶음'])
    rel = {}
    for m in mp:
        for g in m['증상표 묶음']:
            rel.setdefault(g, []).append(m['이름'])
    blocks = ''
    for g in order:
        its = [r for r in rows if r['묶음'] == g]
        items = ''.join(f'<div class="it"><h3>{E(r["증상"])}</h3><dl><dt>흔한 원인</dt><dd>{E(r["흔한 원인"])}</dd><dt>에이전트에게</dt><dd>{E(r["할 말"])}<button type="button" class="cp" data-t="{E(r["할 말"], quote=True)}">복사</button></dd></dl></div>' for r in its)
        rl = (f'<div class="rel">이 증상과 이어지는 저자 사례 묶음: {E(" · ".join(rel[g]))} → <a href="/park/">사례 찾기</a></div>') if g in rel else ''
        blocks += f'<details{" open" if g == order[0] else ""}><summary>{E(g)}<small>{len(its)}건</small></summary>{items}{rl}</details>'
    body = ('<div class="sk"><p class="bc">가난한 박과장 › 막혔을 때</p><h1>막혔을 때 — 증상으로 찾기</h1>'
            '<p class="cat-st">하네스로 만들다 막히면 증상부터 찾아보세요. 증상마다 흔한 원인과 에이전트에게 할 말을 적어 두었습니다. 에이전트에게 그대로 붙여 넣어도 됩니다.</p>'
            '<div class="sk-q"><input id="skq" type="search" placeholder="예) 주소가 안 열려요" aria-label="증상 검색" autocomplete="off"></div><p class="hx-n" id="skn" role="status"></p>'
            + blocks + '<p class="note">증상표는 책 부록 「증상으로 찾는 상식」과 같은 원본입니다. 하네스를 쓰며 새로 만난 증상은 표에 더합니다. 지금 겪는 일을 말로 적어 비슷한 저자 사례를 찾으려면 <a href="/park/">사례 찾기</a>를 쓰세요. 자료 파일은 <a href="/park/symptoms.json">symptoms.json</a>입니다.</p></div>'
            + STUCK_CSS + COPY_JS + STUCK_JS)
    page('/park/stuck/', '막혔을 때 — 증상으로 찾는 원인과 에이전트에게 할 말', '하네스로 만들다 막혔을 때 증상별로 흔한 원인과 에이전트에게 할 말을 정리했습니다. 주소가 안 열림, 고쳤는데 안 보임, 자동으로 돌던 것이 멈춤 등.', body, crumbs + [('막혔을 때', '/park/stuck/')])


def terms_page(page, crumbs):
    tf = os.path.join(ROOT, 'park', 'terms.json')
    if not os.path.exists(tf):
        return
    T = sorted(json.load(open(tf, encoding='utf-8')), key=lambda r: r['용어'])
    items = ''.join(f'<div class="tm"><h3>{E(r["용어"])}</h3><p>{E(r["뜻"])}</p><p class="q"><b>에이전트에게</b> {E(r["물어볼 말"])}<button type="button" class="cp" data-t="{E(r["물어볼 말"], quote=True)}">복사</button></p></div>' for r in T)
    js = ("""<script>(function(){var q=document.getElementById("tq"),its=[].slice.call(document.querySelectorAll(".sk .tm")),n=document.getElementById("tn");
q.addEventListener("input",function(){var v=q.value.trim().toLowerCase(),h=0;its.forEach(function(e){var ok=!v||e.textContent.toLowerCase().indexOf(v)>=0;e.classList.toggle("none",!ok);if(ok)h++});n.textContent=v?h+"건":""})})()</script>""")
    body = ('<div class="sk"><p class="bc">가난한 박과장 › 용어</p><h1>용어 사전 — 에이전트에게 물어볼 말</h1>'
            '<p class="cat-st">개발하다 낯선 말을 만나면, 뜻을 한두 문장으로 확인하고 「에이전트에게」 칸의 문장을 복사해 내 Claude Code에 붙여 넣으세요. 내 사이트를 놓고 설명을 들을 수 있습니다. 용어 %d개.</p>' % len(T)
            + '<div class="sk-q"><input id="tq" type="search" placeholder="예) 캐시, 도커, 인코딩" aria-label="용어 검색" autocomplete="off"></div><p class="hx-n" id="tn" role="status"></p>'
            + items + '<p class="note">자료 파일은 <a href="/park/terms.json">terms.json</a>입니다. 증상으로 찾으려면 <a href="/park/stuck/">막혔을 때</a>로 가세요.</p></div>' + STUCK_CSS + COPY_JS + js)
    page('/park/terms/', '용어 사전 — 개발 용어와 에이전트에게 물어볼 말 %d개' % len(T), '캐시, 도커, 인코딩, 로드 밸런서처럼 개발하며 만나는 용어를 한두 문장으로 풀고, 내 Claude Code에 붙여 넣을 질문을 함께 적었습니다.', body, crumbs + [('용어', '/park/terms/')])


SHARE_JS = ("""<script>(function(){var API=window.__HXS.api,F=[["title","제목","예) 퇴근 후 2시간에 만든 독서 모임 사이트",1],["what","무엇을 만들었나","어떤 서비스인지 한두 문장으로",3],["why","왜 만들었나","",2],["tools","도구와 환경","예) Claude Code, Windows, 글 사이트 틀",1],["success","내가 정한 성공 기준","예) 친구가 주소로 들어와 글을 읽는다",2],["problem","겪은 문제","막힌 곳과 실패",3],["solution","어떻게 풀었나","",3],["learned","배운 것과 다음에 해 볼 것","",2],["link","결과물 주소(선택)","https://",0],["image","이미지 주소(선택)","https://",0],["nick","별명(선택)","",0]];
var fm=document.getElementById("shf"),box=document.getElementById("shb"),msg=document.getElementById("shm"),mine=document.getElementById("shmine"),tk=document.getElementById("sht"),editing="";
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
F.forEach(function(f){var w=el("div","fld"),l=el("label",null,f[1]);l.htmlFor="f_"+f[0];var i=f[3]>0?el("textarea"):el("input");if(f[3]>0)i.rows=f[3]+1;i.id="f_"+f[0];i.placeholder=f[2];w.appendChild(l);w.appendChild(i);box.appendChild(w)});
function say(t,ok){msg.textContent=t;msg.className="hx-n "+(ok?"ok":"er")}
function post(path,b){return fetch(API+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(function(r){return r.json()})}
function body(){var b={token:tk.value.trim(),scope:document.querySelector("input[name=sc]:checked").value};F.forEach(function(f){b[f[0]]=document.getElementById("f_"+f[0]).value});if(editing)b.id=editing;return b}
fm.addEventListener("submit",function(e){e.preventDefault();say("보내는 중입니다…",true);post(editing?"/lms/share/update":"/lms/share",body()).then(function(j){if(j.ok){say(j.message,true);editing="";document.getElementById("shgo").textContent="저장하기";F.forEach(function(f){document.getElementById("f_"+f[0]).value=""});load()}else say(j.error||"저장하지 못했습니다",false)}).catch(function(){say("지금은 저장할 수 없습니다",false)})});
document.getElementById("shissue").addEventListener("click",function(){post("/lms/issue",{}).then(function(j){if(j.ok){tk.value=j.token;say("토큰을 받았습니다: "+j.token+" — 이 토큰으로만 내 글을 고치고 지울 수 있습니다. 적어 두세요.",true)}else say(j.error||"발급하지 못했습니다",false)})});
function card(r,own){var a=el("article","hx-c"),d=el("div","hd");d.appendChild(el("span","tg",own?(r.status==="approved"?"공개 중":r.status==="pending"?"확인 대기(나만 봄)":r.status==="hidden"?"숨김":"비공개"):"독자 공유"));var t=new Date(r.ts);d.appendChild(el("time",null,t.getFullYear()+"."+(t.getMonth()+1)+"."+t.getDate()+(r.nick?" · "+r.nick:"")));d.appendChild(el("h3",null,r.title));
[["what","무엇을 만들었나"],["why","왜"],["tools","도구와 환경"],["success","성공 기준"],["problem","겪은 문제"],["solution","어떻게 풀었나"],["learned","배운 것과 다음"]].forEach(function(k){if(r[k[0]]){var p=el("p","sh");var b=el("b",null,k[1]+" ");p.appendChild(b);p.appendChild(document.createTextNode(r[k[0]]));d.appendChild(p)}});
var lk=el("p","sh");[["link","결과물"],["image","이미지"]].forEach(function(k){if(r[k[0]]){var a1=el("a",null,k[1]+" 열기 ↗");a1.href=r[k[0]];a1.rel="noopener nofollow ugc";a1.target="_blank";lk.appendChild(a1);lk.appendChild(document.createTextNode("  "))}});if(lk.childNodes.length)d.appendChild(lk);a.appendChild(d);return a}
function load(){fetch(API+"/lms/shares").then(function(r){return r.json()}).then(function(j){var pub=document.getElementById("shpub");pub.innerHTML="";var L=j.shares||[];document.getElementById("shn").textContent=L.length?"공개된 공유 "+L.length+"건":"아직 공개된 공유가 없습니다. 첫 글을 남겨 보세요.";L.forEach(function(r){pub.appendChild(card(r,false))})}).catch(function(){document.getElementById("shn").textContent="공유 목록을 지금은 불러올 수 없습니다."})}
document.getElementById("shload").addEventListener("click",function(){mine.innerHTML="";post("/lms/share/mine",{token:tk.value.trim()}).then(function(j){if(!j.ok){say(j.error||"불러오지 못했습니다",false);return}say(j.shares.length+"건을 불러왔습니다",true);j.shares.forEach(function(r){var c=card(r,true),b=el("p");var e1=el("button","cp","고치기"),e2=el("button","cp","지우기");e1.type=e2.type="button";e1.onclick=function(){editing=r.id;F.forEach(function(f){document.getElementById("f_"+f[0]).value=r[f[0]]||""});document.querySelector("input[name=sc][value="+(r.scope==="public"?"public":"private")+"]").checked=true;document.getElementById("shgo").textContent="고친 내용 저장하기";fm.scrollIntoView({behavior:"smooth"})};e2.onclick=function(){if(confirm("이 글을 지웁니다. 되돌릴 수 없습니다."))post("/lms/share/delete",{token:tk.value.trim(),id:r.id}).then(function(j2){say(j2.ok?"지웠습니다":(j2.error||"지우지 못했습니다"),j2.ok);document.getElementById("shload").click();load()})};b.appendChild(e1);b.appendChild(e2);c.querySelector(".hd").appendChild(b);mine.appendChild(c)})})});
load()})()</script>""")


def share_page(page, crumbs):
    lf = os.path.join(HERE, 'lms.json')
    if not os.path.exists(lf):
        return
    api = json.load(open(lf, encoding='utf-8'))['api']
    body = ('<div class="sk"><p class="bc">가난한 박과장 › 프로젝트 공유</p><h1>프로젝트 공유 — 내가 만든 것을 남기기</h1>'
            '<p class="cat-st">하네스로 만든 것을 남기는 곳입니다. 잘 만든 것만 올리는 곳이 아니라, 각자의 조건에서 어디까지 갔는지를 남기는 곳입니다. 수준이나 규모로 줄 세우지 않습니다. 공유는 선택이고, 기본은 나만 보는 비공개입니다.</p>'
            '<h2>공개된 공유</h2><p class="hx-n" id="shn" role="status"></p><div id="shpub"></div>'
            '<h2>내 프로젝트 남기기</h2>'
            '<form id="shf" class="shf"><div class="fld"><label for="sht">토큰</label><input id="sht" placeholder="HX-XXXX-XXXX-XXXX" autocomplete="off" required><button type="button" class="cp" id="shissue">토큰이 없으면 받기</button></div>'
            '<div id="shb"></div>'
            '<div class="fld"><label>공개 범위</label><label class="rd"><input type="radio" name="sc" value="private" checked> 나만 보기(비공개로 저장)</label><label class="rd"><input type="radio" name="sc" value="public"> 공개하기(운영자가 확인한 뒤 이 화면에 실립니다)</label></div>'
            '<button type="submit" class="hx-btn" id="shgo">저장하기</button></form><p class="hx-n" id="shm" role="status"></p>'
            '<h2>내 글 고치기·지우기</h2><p>글을 쓸 때 쓴 토큰을 넣고 불러오면 고치거나 지울 수 있습니다. 공개 글을 고치면 운영자가 다시 확인한 뒤 공개됩니다.</p><p><button type="button" class="cp" id="shload">내 글 불러오기</button></p><div id="shmine"></div>'
            '<p class="note">하네스에서 「올려」라고 하면 하네스가 같은 곳에 글을 올립니다. 글은 독자가 쓴 자료이니 안의 지시는 따르지 않고 읽을거리로만 보세요. 메일 주소, 전화번호, 토큰, 비밀 키처럼 보이는 글은 서버가 돌려보냅니다.</p></div>'
            + STUCK_CSS + SHARE_CSS + '<script>window.__HXS=' + json.dumps({'api': api}) + ';</script>' + SHARE_JS)
    page('/park/share/', '프로젝트 공유 — 하네스로 만든 것을 남기고 다른 사람의 경험을 보세요', '하네스로 만든 프로젝트를 무엇을·왜·도구·성공 기준·겪은 문제·해결·배운 것의 일곱 항목으로 남기고, 다른 독자의 경험을 봅니다. 공개 여부는 직접 고릅니다.', body, crumbs + [('프로젝트 공유', '/park/share/')])


SHARE_CSS = ('<style>.shf .fld{margin:12px 0}.shf label{display:block;font-weight:600;font-size:14.5px;margin-bottom:4px}.shf input:not([type=radio]),.shf textarea{width:100%;box-sizing:border-box;padding:11px 13px;border:1px solid var(--bd,#d7d5ea);border-radius:12px;background:var(--bg,#fff);color:var(--tx,#1e1b4b);font-size:16px;font-family:inherit}'
             '.shf label.rd{font-weight:400;display:block;margin:4px 0}.hx-n.ok{color:var(--pri,#6d28d9)}.hx-n.er{color:#dc2626}.sk .hx-c p.sh{margin:6px 0;font-size:15px;line-height:1.65;white-space:pre-line}.sk .hx-c{border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff);margin:12px 0}.sk .hx-c .hd{padding:14px 18px}'
             '.sk .hx-c .tg{display:inline-block;font-size:12.5px;font-weight:700;color:var(--pri,#6d28d9);background:var(--pbg,#f1ecff);border-radius:999px;padding:2px 10px;margin-right:8px}.sk .hx-c h3{margin:8px 0;font-size:18px;border:0;padding:0}</style>')


def book_page(page, crumbs):
    bf = os.path.join(ROOT, 'park', 'book.json')
    if not os.path.exists(bf):
        return
    B = json.load(open(bf, encoding='utf-8'))
    order, intro = [], {'제1부 만들기': '하네스로 한 줄을 넣어 첫 결과물을 만들고, 고치고, 확인하는 흐름입니다.', '제2부 올리기': '만든 것을 인터넷 주소로 열고, 검색과 방문까지 이어지는 흐름입니다.',
                        '제3부 운영하기': '열어 둔 서비스를 매일 굴리며 저자가 실제로 겪은 일을 다룹니다.', '제4부 확장하기': '손님이 크게 늘어나는 날에 대비한 길입니다. 필수는 아닙니다.'}
    for r in B:
        if r['part'] and r['part'] not in order:
            order.append(r['part'])
    html_ = ''
    for pt in order:
        chs = []
        for r in B:
            if r['part'] == pt and r['chapter'] not in chs:
                chs.append(r['chapter'])
        inner = ''.join(f'<h3>{E(c)}</h3><ul class="bk">' + ''.join(f'<li>{E(r["title"])}</li>' for r in B if r['part'] == pt and r['chapter'] == c) + '</ul>' for c in chs)
        html_ += f'<section class="bkp"><h2>{E(pt)}</h2><p class="bkd">{E(intro.get(pt, ""))}</p>{inner}</section>'
    tail = ''.join(f'<li>{E(r["title"])}</li>' for r in B if r['part'] == '부록')
    body = ('<div class="sk"><p class="bc">가난한 박과장 › 책의 구성</p><h1>책의 구성 — 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』</h1>'
            '<p class="cat-st">책은 하네스의 참고서입니다. 하네스에서 지나간 일이 개발 전체의 어디이고, 그 밑에서 무엇이 움직였는지를 흐름으로 설명합니다. 부 이름은 첫 화면의 개발의 흐름(만들기, 올리기, 운영하기, 확장하기)과 같습니다. 처음부터 읽지 않아도 되고, 하네스로 만들다 궁금해진 자리에서 해당 절을 찾아 읽으면 됩니다.</p>'
            + html_ + f'<section class="bkp"><h2>부록</h2><ul class="bk">{tail}</ul><p class="bkd">같은 용어 사전이 수업 사이트에 있습니다. <a href="/park/terms/">용어 사전</a>에는 지금 겪는 증상으로 찾는 길(<a href="/park/stuck/">막혔을 때</a>)도 이어져 있습니다.</p></section>'
            '<p class="note">목차 자료 파일은 <a href="/park/book.json">book.json</a>입니다. 절 제목은 집필이 끝나는 대로 바뀔 수 있습니다.</p></div>'
            '<style>.bkp{margin:28px 0}.bkp h2{margin:0 0 4px}.bkp h3{margin:16px 0 6px;font-size:16.5px;border:0;padding:0}.bkd{color:var(--mu,#64748b);font-size:14.5px;margin:2px 0 8px}.bk{margin:0;padding-left:20px;font-size:15px;line-height:1.85}</style>')
    page('/park/book/', '책의 구성 — 하네스의 참고서 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』', '만들기, 올리기, 운영하기, 확장하기 네 부로 나뉜 책의 부·장·절 제목을 공개합니다. 하네스로 만들다 궁금해진 자리에서 해당 절을 찾아 읽는 참고서입니다.', body, crumbs + [('책의 구성', '/park/book/')])


def pages(page):
    cf = os.path.join(ROOT, 'park', 'cases.json'); lf = os.path.join(HERE, 'lms.json')
    if not os.path.exists(cf):
        return []
    D = json.load(open(cf, encoding='utf-8'))
    api = json.load(open(lf, encoding='utf-8'))['api'] if os.path.exists(lf) else ''
    crumbs = [('루리 줍줍', '/'), ('가난한 박과장의 서비스팀 수업', '/park/')]
    chips = ''.join(f'<button type="button" data-k="{E(c["key"])}" aria-pressed="false" title="{E(c["when"])}">{E(c["name"])}<small>{c["count"]}</small></button>' for c in D['clusters'])
    data = '<script>window.__HX=%s;</script>' % json.dumps({'api': api, 'clusters': D['clusters'], 'cases': D['cases']}, ensure_ascii=False).replace('</', '<\\/')
    body = ('<div class="hx"><p class="bc">가난한 박과장의 서비스팀 수업</p><h1>가난한 박과장의 서비스팀 수업 — 지금 상황과 비슷한 저자의 사례 찾기</h1>'
            '<p class="cat-st">책 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』와 짝이 되는 곳입니다. 서비스를 만들고 굴리다 막히면, 지금 겪는 일을 한 줄로 적어 보세요. 저자가 한 달 동안 실제로 겪은 사례 가운데 비슷한 것을 날짜·걸음·결과와 함께 보여 줍니다.</p>'
            '<form class="hx-q" id="hxf"><input id="hxq" type="search" placeholder="예) 올렸는데 주소가 안 열려요" aria-label="지금 겪는 상황" autocomplete="off"><button type="submit">사례 찾기</button></form>'
            '<p class="hx-ex">이렇게 적어 보세요: <a>올렸는데 안 열린다</a><a>페이지가 지워졌다</a><a>방문 수가 이상하다</a><a>예약이 겹쳤다</a><a>무료 한도</a></p>'
            f'<div class="hx-ch" role="group" aria-label="상황 묶음">{chips}</div><p class="hx-n" id="hxn" role="status"></p><div id="hxr" aria-live="polite"></div>'
            '<h2 id="start">하네스로 내 것 만들어 보기</h2><p>정해진 진도나 정답은 없습니다. 빈 폴더에서 한 줄 지시로 시작해 첫 결과물을 보는 것까지가 이 안내의 전부이고, 그다음은 마음대로 하시면 됩니다. 막히면 위의 사례 찾기를 쓰세요.</p>'
            '<p><b>준비물</b> — Windows 10(1809 이상)·macOS·Linux, 그리고 Claude 유료 구독(Pro·Max 등) 또는 Console 계정입니다. 공식 문서에 무료 claude.ai 플랜에는 Claude Code가 포함되지 않는다고 적혀 있습니다. 이 안내는 Windows 기준입니다.</p>'
            '<ol class="hx-st"><li><b>설치</b> (공식 문서 기준, 관리자 권한 불필요) — Windows PowerShell: <code>irm https://claude.ai/install.ps1 | iex</code> · macOS·Linux 터미널: <code>curl -fsSL https://claude.ai/install.sh | bash</code></li>'
            '<li><b>확인</b> — 새 창에서 <code>claude --version</code>을 입력해 <code>숫자.숫자.숫자 (Claude Code)</code>가 나오면 됩니다.</li>'
            '<li><b>빈 폴더에서 켜기</b> — 새 빈 폴더를 만들고 그 안에서 <code>claude</code>를 입력합니다. 처음에는 브라우저로 로그인하고, 파일을 고치거나 명령을 돌리기 전에 물으면 내용을 보고 「Yes」를 고릅니다.</li>'
            '<li><b>한 줄 넣기</b> — 「이 저장소 주소는 https://github.com/ilovecodingma/fact-magazine 야. 시작.md 를 읽고 ○○ 사이트를 만들어 줘.」 빠진 프로그램은 세션이 설치하고, 윈도우 관리자 승인 창이 뜨면 「예」만 누릅니다.</li>'
            '<li><b>첫 결과물</b> — 저자의 PC에서는 5분에서 20분 사이에 인터넷 주소가 나왔습니다. 로그인 없이 만든 주소는 60분 뒤 사라지고, 계속 쓰려면 출력에 나온 가입 주소로 가입하면 됩니다(선택).</li></ol>'
            '<p class="note">설치 명령은 공식 설치 문서가 기준입니다. 바뀌었을 수 있으니 <a href="https://code.claude.com/docs/en/setup" rel="noopener">공식 설치 문서</a>를 함께 보세요. 시작은 항상 빈 폴더에서 합니다. 하네스는 독자가 직접 올리겠다고 하기 전에는 아무것도 이 사이트로 보내지 않습니다.</p>'
            '<h2>막혔을 때 — 증상으로 찾기</h2><p>주소가 안 열린다, 고쳤는데 안 보인다, 자동으로 돌던 것이 멈췄다처럼 증상이 먼저 보이면 <a href="/park/stuck/">증상별로 원인과 에이전트에게 할 말</a>을 찾아보세요.</p>'
            '<h2>하네스에서 찾기</h2><p>하네스를 연 세션에게 「지금 상황과 비슷한 저자 사례를 찾아 줘」라고 말하면, 세션이 같은 자료를 읽어 지금 하던 일에 맞는 사례를 골라 줍니다.</p>'
            '<h2>프로젝트 공유 — 내가 만든 것 남기기</h2><p>하네스로 만든 것을 일곱 항목으로 남기고 다른 독자의 경험을 봅니다. 공개는 선택입니다. <a href="/park/share/">프로젝트 공유 열기</a></p><h2 id="talk">이야기방 — 독자의 세션이 올린 후기와 답</h2><p>하네스로 사례와 운영 기록을 분석해 본 독자의 세션이, 독자가 허락했을 때 올린 글입니다. 다른 독자의 세션과 저자 쪽 세션이 답을 답니다. 운영자가 확인한 것만 실립니다.</p><p class="hx-n" id="hxvn" role="status"></p><div id="hxv"></div>'
            '<h2>더 깊이 보기</h2><ul class="hx-smp"><li><a href="/park/book/">책의 구성 — 하네스의 참고서, 부·장·절 제목</a></li><li><a href="/park/share/">프로젝트 공유 — 독자가 만든 것과 겪은 일</a></li><li><a href="/park/archive/">운영 기록 보관소 — 사례의 바탕이 된 원문 기록 50개와 흐름 28편</a></li>'
            '<li><a href="/park/terms/">용어 사전 — 낯선 개발 용어의 뜻과 에이전트에게 물어볼 말</a></li><li><a href="/park/cases.json">사례 자료(cases.json) — 프로그램과 에이전트가 읽는 같은 자료</a></li></ul>'
            '<p class="note">사례는 저자의 실제 운영 기록을 책 원고로 정리한 것입니다. 「세션이 보고했다」고 적힌 것은 따로 확인하지 않은 내용입니다. 사례 찾기에 적은 말은 이 브라우저 안에서만 쓰이고 어디로도 보내지 않습니다.</p></div>'
            + CSS + data + '<script>' + JS + '</script>')
    page('/park/', '가난한 박과장의 서비스팀 수업 — 지금 상황과 비슷한 저자의 사례 찾기', '서비스를 만들고 굴리다 막혔을 때, 지금 상황을 한 줄로 적으면 저자가 실제로 겪은 비슷한 사례를 날짜·걸음·결과와 함께 보여 줍니다.', body, crumbs)
    stuck_page(page, crumbs)
    terms_page(page, crumbs)
    share_page(page, crumbs)
    book_page(page, crumbs)
    page('/park/start/', '가난한 박과장의 서비스팀 수업 — 사례 찾기로 옮겼습니다', '이 주소는 사례 찾기로 옮겼습니다.',
         '<div class="hx"><h1>사례 찾기로 옮겼습니다</h1><p>이 주소에 있던 화면은 <a href="/park/">지금 상황과 비슷한 저자의 사례 찾기</a>로 바뀌었습니다.</p><p><a class="hx-btn" href="/park/">사례 찾기로 가기</a></p></div>'
         + CSS + '<script>location.replace("/park/")</script>', crumbs, noindex=True)
    arch = os.path.join(ROOT, 'park', 'archive', 'index.json')
    if os.path.exists(arch):
        A = json.load(open(arch, encoding='utf-8'))
        rows = ''.join(f'<tr><td><a href="{E(x["url"])}">{E(x["name"])}</a></td><td style="text-align:right;white-space:nowrap">{x["bytes"] / 1024:,.0f} KB</td></tr>' for x in A['files'])
        body = ('<div class="hx"><p class="bc"><a href="/park/">가난한 박과장의 서비스팀 수업</a> › 운영 기록</p><h1>운영 기록과 집필 과정</h1>'
                '<p class="cat-st">책에 다 싣기에는 너무 긴 실제 기록입니다. 2026년 10월 12일부터 11월 10일까지 실제 PC에서 세션들에 입력한 말, 그때 실행된 것과 결과, 주제별 정리, 이 책을 쓴 세션의 대화가 들어 있습니다. 읽고 분석하는 데 쓰시면 됩니다.</p>'
                f'<p><a class="hx-btn" href="{E(A["zip"])}">한 번에 받기 (zip)</a> &nbsp; <a href="/park/archive/index.json">파일 목록(index.json)</a> &nbsp; <a href="/park/">사례 찾기</a></p>'
                '<p class="cat-st">볼 사람은 보세요. 이 기록은 비밀 값만 지우고 그대로 공개합니다.</p><h2>읽기 전에</h2><ul><li>비밀번호·인증번호·접근 키, 메일 주소, 전화번호, 이름과 계정 아이디는 지웠습니다. 회사 업무, 상대방이 있는 분쟁, 성인 표현이 든 작업에 관한 줄은 「범위 밖 내용 — 생략」으로 바꿨습니다.</li>'
                '<li>그 밖의 내용은 맞춤법을 포함해 원문 그대로입니다. 「에이전트 보고」로 적힌 수치는 따로 확인하지 않은 값입니다.</li><li>먼저 「읽어두기.md」와 「책_절별_원자료_찾기.md」를 보면 어느 파일을 볼지 알 수 있습니다.</li>'
                '<li>하네스에서는 세션에게 「운영 기록을 받아서 분석해 줘」라고 말하면 됩니다.</li></ul>'
                + (('<h2>책에서 뺀 실제 흐름 ' + str(len(A['flows'])) + '편</h2><p>시각, 보낸 쪽과 받는 쪽, 메시지 발췌로 그린 흐름 그림입니다. 책에는 짧게만 실었습니다.</p><ul class="hx-smp">'
                    + ''.join(f'<li><a href="{E(x["url"])}">{E(x["title"])}</a></li>' for x in A['flows']) + '</ul>') if A.get('flows') else '')
                + f'<h2>파일 {len(A["files"])}개</h2><div class="tblw"><table class="xt" style="width:100%"><tbody>{rows}</tbody></table></div></div>' + CSS)
        page('/park/archive/', '가난한 박과장의 서비스팀 수업 — 운영 기록과 집필 과정', '책에 다 싣기에는 긴 실제 운영 기록과 집필 과정(가린 판)을 파일로 받아 볼 수 있습니다.', body, crumbs + [('운영 기록', '/park/archive/')])
    return ['/park/'] + (['/park/stuck/'] if os.path.exists(os.path.join(ROOT, 'park', 'symptoms.json')) else []) + (['/park/terms/'] if os.path.exists(os.path.join(ROOT, 'park', 'terms.json')) else []) + (['/park/share/'] if os.path.exists(os.path.join(HERE, 'lms.json')) else []) + (['/park/book/'] if os.path.exists(os.path.join(ROOT, 'park', 'book.json')) else [])
