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
       '.bk .setup{border:1px solid #cbd5e1;border-radius:16px;padding:16px 18px;margin:16px 0;background:rgba(79,91,213,.05)}.bk .setup h2{margin:0 0 10px;font-size:18px}.bk .setup .row{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:10px 0}.bk .setup .row b{min-width:58px}.bk .setup .grp{display:inline-flex;flex-wrap:wrap;gap:6px}.bk .setup .grp button{padding:9px 14px;border:1px solid #cbd5e1;border-radius:999px;background:#fff;color:#131a2e;cursor:pointer;font-weight:700;min-height:40px}.bk .setup .grp button.on{background:#4f5bd5;border-color:#4f5bd5;color:#fff}.bk .setup input[type=number]{width:110px;padding:9px 10px;border:1px solid #cbd5e1;border-radius:10px;min-height:40px}.bk div.q{border:1px solid #d6dbf0;border-radius:16px;margin:16px 0;padding:18px 18px 14px;background:#fff;box-shadow:0 2px 10px rgba(30,40,100,.07)}.bk .qt{margin:0 0 6px;font-weight:700;line-height:1.7}.bk .qt .n{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;margin-right:8px;border-radius:50%;background:#131a2e;color:#fff;font-size:14px}.bk label.o{display:block;padding:11px 14px;margin:8px 0;border:1.5px solid #d6dbf0;border-radius:12px;cursor:pointer;line-height:1.55;background:#fff}.bk label.o:hover{border-color:#4f5bd5}.bk label.o:has(input:checked){border-color:#4f5bd5;background:#eef0ff;box-shadow:0 0 0 2px rgba(79,91,213,.2)}.bk label.o input{position:absolute;opacity:0;pointer-events:none}.bk label.o em{font-style:normal;display:inline-block;min-width:22px;color:#4f5bd5;font-weight:800}.bk div.q.ok{border-color:#16a34a}.bk div.q.no{border-color:#dc2626}.bk label.ans{background:#dcfce7!important;border-color:#16a34a!important}.bk label.wr{background:#fee2e2!important;border-color:#dc2626!important}.bk .rv{margin-top:10px;line-height:1.7}.bk .clk{position:sticky;top:60px;z-index:5;margin:0 0 8px;padding:8px 12px;border-radius:10px;background:#131a2e;color:#ff7ab6;font-weight:800;font-size:18px}.bk #bk-grade,.bk #bk-start{padding:14px 30px;font-size:17px}'
       '.bk .play .setup button,.bk .play .bar button{display:inline-block;width:auto;text-align:center;margin:0 6px 6px 0;font-size:15px}.bk .play .setup .grp button{margin:0}.bk .play .bar button{padding:12px 22px;border-radius:10px}.bk .setup input[type=number]{background:#fff;color:#131a2e}'
       '.bk div.q{background:#fff;color:#131a2e}.bk div.q .rv{color:#131a2e}'
       '.bk #bk-start,.bk #bk-grade,.bk #b-go,.bk #b-wr{background:#4f5bd5;color:#fff;border-color:#4f5bd5}.bk #bk-start:hover,.bk #bk-grade:hover{background:#3f4ab8}'
       '.bk-big{position:relative;min-height:230px;margin:10px 0 18px;overflow:visible}.bk-sc{font-size:72px;font-weight:900;line-height:1;color:#ff4d7d;text-shadow:0 0 24px rgba(255,77,125,.7);transform:rotate(-3deg)}.bk-one{display:inline-block}.bk-rr{position:absolute;right:0;top:-10px;height:230px;width:auto;filter:drop-shadow(0 0 14px rgba(255,60,120,.6))}.bk-bub{position:absolute;right:150px;top:6px;max-width:210px;background:#ff4d7d;color:#fff;font:800 15px/1.3 system-ui,sans-serif;padding:9px 12px;border-radius:8px;font-style:normal;opacity:0;transition:opacity .15s;transform:rotate(-2deg)}'
       '.nts{margin:16px 0;padding:14px 16px;border:1px solid #2a2f4a;border-radius:10px;background:#0f1220}.nts h2{margin:0 0 8px;font-size:20px}.nts-i{margin:0 0 10px}.nts-s{margin:8px 0;border-top:1px solid #23284a;padding-top:8px}.nts-s summary{cursor:pointer;font-weight:800}.nts-b{white-space:pre-line;line-height:1.75}.nts-k{margin:6px 0;padding-left:18px}.nts-k li{margin:3px 0}.nts-r{margin-top:12px;padding:10px 12px;background:#1a1030;border-left:3px solid #ff4d7d}.nts-r ul{margin:6px 0 0;padding-left:18px}'
       '.bk .rv .ex,.bk details p{white-space:pre-line;display:block;margin:6px 0}.bk .fig{margin:10px 0;padding:10px;background:#0f1220;border:1px solid #2a2f4a;border-radius:8px;overflow-x:auto}.bk .fig svg{max-width:100%;height:auto;color:#e8e8f0}'
       '@keyframes bkTear{0%{transform:none;opacity:1}18%{transform:translate(calc(var(--dx)*.18),-14px) rotate(calc(var(--r)*.3))}100%{transform:translate(var(--dx),var(--dy)) rotate(var(--r));opacity:0}}@keyframes bkHand{from{transform:translate(110%,-30px) rotate(9deg);opacity:0}to{transform:none;opacity:1}}.bk-half{background:#fff!important;box-shadow:0 4px 14px rgba(0,0,0,.5)}.bk-tearmsg{position:fixed;left:50%;top:40%;z-index:99999;transform:translate(-50%,-50%) rotate(-3deg);padding:12px 20px;background:#ff4d7d;color:#fff;font-size:22px;font-weight:800;border-radius:6px;white-space:nowrap;pointer-events:none;animation:bkMsg 1.5s ease-out forwards}@keyframes bkMsg{0%{opacity:0;transform:translate(-50%,-50%) rotate(-3deg) scale(.7)}12%{opacity:1;transform:translate(-50%,-50%) rotate(-3deg) scale(1.05)}85%{opacity:1}100%{opacity:0}}.bk div.q:nth-child(3n+1){transform:rotate(-.5deg)}.bk div.q:nth-child(3n+2){transform:rotate(.45deg) translateX(3px)}.bk div.q:nth-child(3n){transform:rotate(-.25deg) translateX(-3px)}@media (prefers-reduced-motion:reduce){.bk div.q{transform:none!important}}'
       '@media (prefers-color-scheme:dark){.bk div.q{background:#1a2340;color:#e5e9f5;border-color:#2a3558}.bk div.q .rv{color:#e5e9f5}.bk label.o{background:#131a2e;border-color:#2a3558;color:#e5e9f5}.bk label.o:has(input:checked){background:#26336a}.bk .setup .grp button{background:#1a2340;color:#e5e9f5;border-color:#2a3558}.bk label.ans{background:#0f3d24!important;color:#e5e9f5}.bk label.wr{background:#4a1620!important;color:#e5e9f5}.bk .q,.bk .play button{border-color:#334155;background:transparent;color:inherit}.bk .play .ex{background:#1e293b}}</style>')

CSS2 = ('<style>'
 '.bk{max-width:860px;--bg:#0e1222;--bg2:#151b33;--ln:#252d52;--tx:#e8ebf8;--mu:#8e98c0;--ac:#6c7bff;--ac2:#ff5c9a;color:var(--tx)}'
 '.bk h1{font-size:28px;letter-spacing:-.02em;margin:6px 0 12px}.bk h2{font-size:15px;letter-spacing:.04em;color:var(--mu);font-weight:700;margin:30px 0 12px;text-transform:none}.bk h2 small{color:var(--ac);margin-left:4px}'
 '.bk>ul,.bk ul:not(.nts-k):not(.c){list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}'
 '.bk>ul>li{margin:0;padding:0}.bk>ul>li>a{display:block;padding:14px 16px 12px;border:1px solid var(--ln);border-radius:14px;background:linear-gradient(160deg,var(--bg2),var(--bg));text-decoration:none;color:var(--tx);transition:border-color .15s,transform .15s}'
 '.bk>ul>li>a:hover{border-color:var(--ac);transform:translateY(-2px)}.bk>ul>li>a b{display:block;font-size:16px;margin-bottom:6px}'
 '.bk>ul>li .bd{font-size:11px;padding:2px 8px;margin-right:6px}.bk>ul>li small{color:var(--mu);font-size:12px}'
 '.bk .bd{background:rgba(255,92,154,.14);color:#ff8ab8;border:1px solid rgba(255,92,154,.3)}.bk .bd.pb{background:rgba(52,211,153,.12);color:#6ee7b7;border-color:rgba(52,211,153,.3)}'
 '.bk .ai{background:rgba(108,123,255,.1);border:1px solid rgba(108,123,255,.3);color:var(--tx);border-radius:12px}'
 '.bk .setup{border:1px solid var(--ln);background:var(--bg2);border-radius:16px}.bk .setup h2{color:var(--tx);font-size:17px;margin:0 0 10px}.bk .setup .grp button{background:var(--bg);color:var(--tx);border-color:var(--ln)}.bk .setup .grp button.on{background:var(--ac);border-color:var(--ac);color:#fff}.bk .setup input[type=number]{background:var(--bg);color:var(--tx);border-color:var(--ln)}'
 '.bk div.q,.bk div.q:nth-child(n){transform:none!important;background:var(--bg2);color:var(--tx);border:1px solid var(--ln);border-radius:16px;box-shadow:none;padding:20px 20px 14px}'
 '.bk .qt .n{background:var(--ac);width:30px;height:30px}.bk label.o{background:var(--bg);border:1px solid var(--ln);color:var(--tx);border-radius:12px;padding:12px 14px}.bk label.o:hover{border-color:var(--ac)}.bk label.o:has(input:checked){background:rgba(108,123,255,.16);border-color:var(--ac);box-shadow:none}.bk label.o em{color:var(--ac)}'
 '.bk div.q.ok{border-color:#34d399}.bk div.q.no{border-color:#fb7185}.bk label.ans{background:rgba(52,211,153,.14)!important;border-color:#34d399!important}.bk label.wr{background:rgba(251,113,133,.14)!important;border-color:#fb7185!important}'
 '.bk .rv{color:var(--tx)}.bk .rv .ex{background:var(--bg);border-left:3px solid var(--ac);border-radius:6px;padding:10px 12px}'
 '.bk .clk{background:var(--bg2);border:1px solid var(--ln);color:var(--ac2)}.bk #bk-start,.bk #bk-grade{background:linear-gradient(90deg,var(--ac),#8b5cf6);border:0;border-radius:12px;box-shadow:0 6px 18px rgba(108,123,255,.35)}'
 '.bk .bar button.g{background:transparent;color:var(--ac);border-color:var(--ac)}.bk .nt{color:var(--mu)}.bk .nt a{color:var(--ac)}.bk .nag{margin:14px 0;padding:16px 18px;border:1px solid var(--ac2);border-radius:14px;background:linear-gradient(160deg,rgba(255,92,154,.12),rgba(108,123,255,.1))}.bk .nag>b{font-size:18px;display:block;margin-bottom:6px;color:var(--ac2)}.bk .nag p{margin:6px 0}'
 '</style>')
JS = r'''<script>(function(){var el=document.getElementById('bk-data');if(!el)return;var D=JSON.parse(el.textContent),Q=D.questions,key='bk_wrong_'+D.id;
var sheet=document.getElementById('bk-sheet'),res=document.getElementById('bk-res'),clock=document.getElementById('bk-clock'),gb=document.getElementById('bk-grade'),rs=document.getElementById('bk-reset'),setup=document.getElementById('bk-setup'),info=document.getElementById('bk-info'),nin=document.getElementById('bk-n'),bar=document.getElementById('bk-gbar');
var cfg={n:'all',m:'p',o:'seq',r:'all'},order=[],timed=false,tmr=null,tleft=0,tstart=0,graded=false,SEC=D.sec_per_q||60;
var IMG='/assets/ruri/o_sn_smirk_s.webp',FB='/assets/ruri/o_present_s.webp';
var WR=['이걸 틀려? 남들은 이미 땄다더라.','이 점수로 취직하겠냐?','찍었냐? 찍어도 이건 안 틀리겠다.','틀렸어. 해설 읽어. 읽으라고 써 놨으니까.','이거라도 해야 먹고살지 않겠냐?','아깝지도 않냐. 그냥 몰랐던 거잖아.','시험장에서 이러면 올해도 끝이다.','이 정도는 외우고 와야지. 누가 대신 풀어 주냐?'];
function nag(p,w){var tk;try{tk=localStorage.getItem('jupjup_tok')}catch(e){}
if(tk)return '<p class="nt">틀린 문제 '+w+'개 기록했다. 상태창에 반영된다.</p>';
var L=p>=90?'점수는 나쁘지 않네. 근데 이거 저장 안 된다. 다음에 또 처음부터다.':p>=60?'그렇게 해서 살아남겠냐? 틀린 '+w+'개는 이 브라우저에만 남는다.':'이 점수로 살아남겠냐? 틀린 '+w+'개, 이대로 두면 시험장에서 또 틀린다.';
return '<div class="nag"><b>'+L+'</b><p>가입하면 점수와 틀린 문제가 계정에 쌓이고, 헬조선 생존 확률이 나온다. 목표를 정하면 플랜이랑 오늘의 퀘스트도 던져 준다. 전부 무료다.</p><div class="bar"><button id="b-join">가입하고 살아남기</button></div></div>'+'<p class="nt">틀린 문제 '+w+'개는 이 브라우저에만 저장돼.</p>'}
function pick(a){return a[Math.floor(Math.random()*a.length)]}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function ru(t){return '<div class="ru"><img src="'+IMG+'" width="56" height="78" alt="비웃는 루리" onerror="this.onerror=null;this.src=\''+FB+'\'"><p>'+esc(t)+'</p></div>'}
function fmt(s){s=Math.max(0,s);var m=Math.floor(s/60),r=s%60;return m+':'+(r<10?'0':'')+r}
function sv(w){try{localStorage.setItem(key,JSON.stringify(w))}catch(e){}}function ld(){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch(e){return[]}}
function all(){return Q.map(function(_,i){return i})}
function shuffle(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}return a}
function verdict(p,to){if(to)return '시간 초과. 시험장은 안 기다려 준다.';if(p>=90)return '니가? 만점이라고? 남들은 이미 땄다.';if(p>=70)return '그 점수로 취직하겠냐. 틀린 거나 다시 풀어.';if(p>=40)return '이 점수에 잠이 오냐?';return '기초부터 다시 해. 지금 자면 내년에도 똑같다.'}
function pool(){return cfg.r==='wrong'?ld().filter(function(i){return Q[i]}):all()}
function count(){var p=pool().length;var n=cfg.n==='all'?p:parseInt(cfg.n,10);if(!(n>0))n=p;return Math.min(n,p)}
function refresh(){var n=count();info.textContent=n+'문제 · '+(cfg.m==='t'?'시간제 '+Math.max(1,Math.round(n*SEC/60))+'분 (끝나면 자동 채점)':'시간 제한 없음')+' · '+(cfg.o==='shuf'?'섞어서':'순서대로')}
function mark(g,v){g.querySelectorAll('button').forEach(function(b){b.classList.toggle('on',b.getAttribute('data-'+g.getAttribute('data-k'))===String(v))})}
setup.querySelectorAll('.grp').forEach(function(g){var k=g.getAttribute('data-k');g.querySelectorAll('button').forEach(function(b){b.onclick=function(){var v=b.getAttribute('data-'+k);cfg[k]=v;if(k==='n')nin.value='';mark(g,v);refresh()}})});
nin.oninput=function(){var v=parseInt(nin.value,10);if(v>0){cfg.n=String(v);mark(setup.querySelector('.grp[data-k=n]'),'-')}else{cfg.n='all'}refresh()};
var w0=ld().filter(function(i){return Q[i]});var wb=setup.querySelector('[data-r=wrong]');if(wb){if(w0.length){wb.hidden=false;wb.textContent='지난번 틀린 문제 '+w0.length+'개'}}
function render(list,t){order=list.slice();timed=!!t;graded=false;clearInterval(tmr);res.innerHTML='';rs.hidden=true;gb.hidden=false;bar.hidden=false;clock.hidden=true;setup.hidden=true;
var h='';order.forEach(function(qi,n){var q=Q[qi];h+='<div class="q" id="q'+qi+'"><p class="qt"><b class="n">'+(n+1)+'</b>'+esc(q.q)+'</p>';q.choices.forEach(function(c,i){h+='<label class="o"><input type="radio" name="q'+qi+'" value="'+i+'"><span><em>'+(i+1)+'</em>'+esc(c)+'</span></label>'});h+='<div class="rv"></div></div>'});sheet.innerHTML=h;sheet.hidden=false;
if(timed){tleft=Math.max(60,Math.round(order.length*SEC));tstart=Date.now();clock.hidden=false;clock.textContent='남은 시간 '+fmt(tleft);tmr=setInterval(function(){tleft--;clock.textContent='남은 시간 '+fmt(tleft);if(tleft<=0){clearInterval(tmr);grade(true)}},1000)}else{tstart=Date.now()}}
function grade(to){if(graded)return;graded=true;clearInterval(tmr);var score=0,wrong=[];
order.forEach(function(qi){var q=Q[qi],f=document.getElementById('q'+qi),sel=sheet.querySelector('input[name=q'+qi+']:checked'),v=sel?+sel.value:-1,ok=v===q.answer;
f.className='q '+(ok?'ok':'no');f.querySelectorAll('label.o').forEach(function(l,i){l.querySelector('input').disabled=true;if(i===q.answer)l.className='o ans';else if(i===v)l.className='o wr'});
f.querySelector('.rv').innerHTML='<b>'+(ok?'정답':(v<0?'미응답':'오답')+' · 정답 '+(q.answer+1)+'번')+'</b> '+'<span class="ex">'+esc(q.explain||'')+'</span>'+(q.fig?'<div class="fig">'+q.fig+'</div>':'')+(ok?'':ru(pick(WR)));
if(ok)score++;else wrong.push(qi)});
var prev=ld().filter(function(i){return order.indexOf(i)<0});sv(prev.concat(wrong));try{window.jamQ&&jamQ(D.id,order.length,score)}catch(e){}
var p=Math.round(score*100/order.length),used=Math.round((Date.now()-tstart)/1000);
res.innerHTML='<h3>결과: '+score+' / '+order.length+' ('+p+'점)'+' · 걸린 시간 '+fmt(used)+'</h3>'+ru(verdict(p,to))+nag(p,wrong.length)+(wrong.length?'<div class="bar"><button id="b-wr">틀린 문제만 다시</button></div>':'');
var jn=document.getElementById('b-join');if(jn)jn.onclick=function(){if(window.JUP&&JUP.authModal)JUP.authModal(function(){location.reload()});else location.href='/me/'};var w=document.getElementById('b-wr');if(w)w.onclick=function(){render(wrong.slice(),false);window.scrollTo(0,res.offsetTop-70)};
gb.hidden=true;rs.hidden=false;clock.hidden=true;window.scrollTo(0,res.offsetTop-70);if(score===order.length&&order.length>=3&&!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches))shatter()}
function shatter(){var cs=[].slice.call(sheet.querySelectorAll('div.q')),list=order.slice(),fx=[];
cs.forEach(function(c){var r=c.getBoundingClientRect();if(r.bottom<-40||r.top>innerHeight+40)return;var ys=[0,12,26,40,55,70,85,100],pts=ys.map(function(y){return [50+(Math.random()*12-6),y]});
var L='polygon(0 0,'+pts.map(function(p){return p[0].toFixed(1)+'% '+p[1]+'%'}).join(',')+',0 100%)',R='polygon('+pts.map(function(p){return p[0].toFixed(1)+'% '+p[1]+'%'}).join(',')+',100% 100%,100% 0)';
[[L,-1],[R,1]].forEach(function(h){var cl=c.cloneNode(true);cl.removeAttribute('id');cl.className='q bk-half';cl.style.cssText='position:fixed;left:'+r.left+'px;top:'+r.top+'px;width:'+r.width+'px;height:'+r.height+'px;margin:0;z-index:99998;pointer-events:none;clip-path:'+h[0]+';--dx:'+(h[1]*(70+Math.random()*130))+'px;--dy:'+(420+Math.random()*420)+'px;--r:'+(h[1]*(8+Math.random()*26))+'deg;animation:bkTear 1.1s cubic-bezier(.45,0,.85,.5) '+(Math.random()*.2)+'s forwards';document.body.appendChild(cl);fx.push(cl)});c.style.visibility='hidden'});
var tp=document.createElement('div');tp.className='bk-tearmsg';tp.textContent='니가? 만점이라고? 인정 안 해. 다시 풀어.';document.body.appendChild(tp);
setTimeout(function(){fx.forEach(function(e){e.remove()});tp.remove();render(list,false);[].slice.call(sheet.querySelectorAll('div.q')).forEach(function(c,k){c.style.animation='bkHand .7s cubic-bezier(.2,1.2,.4,1) '+(k*.09)+'s both'});res.innerHTML=ru('니가? 만점이라고? 새 시험지 줄 테니까 다시 풀어.');pocket();setTimeout(function(){[].slice.call(sheet.querySelectorAll('div.q')).forEach(function(c){c.style.animation=''})},700+list.length*90+400)},1500)}
function pocket(){var box=document.createElement('div');box.className='bk-big';box.innerHTML='<div class="bk-sc"><b class="bk-one">1</b><span class="bk-zz">00점</span></div><img class="bk-rr" src="/assets/ruri/sc_perfect_1.webp" alt=""><i class="bk-bub"></i>';res.insertBefore(box,res.firstChild);
var one=box.querySelector('.bk-one'),rr=box.querySelector('.bk-rr'),bub=box.querySelector('.bk-bub'),zz=box.querySelector('.bk-zz');
function say(t){bub.textContent=t;bub.style.opacity=1}
if(!rr.animate){return}
var a=rr.animate([{transform:'translateX(160%) rotate(14deg)',opacity:0},{transform:'none',opacity:1}],{duration:650,easing:'cubic-bezier(.2,1.3,.4,1)',fill:'both'});
a.onfinish=function(){say('이게 뭐야? 1이 붙어 있네?');setTimeout(function(){var r1=one.getBoundingClientRect(),r2=rr.getBoundingClientRect(),dx=r2.left+r2.width*.55-r1.left-r1.width/2,dy=r2.top+r2.height*.72-r1.top-r1.height/2;
one.style.position='relative';one.style.zIndex=5;var b=one.animate([{transform:'none',opacity:1},{transform:'translate(-18px,-70px) rotate(-20deg) scale(1.2)',opacity:1,offset:.35},{transform:'translate('+dx+'px,'+dy+'px) rotate(300deg) scale(.15)',opacity:.9}],{duration:900,easing:'ease-in',fill:'forwards'});
b.onfinish=function(){one.style.visibility='hidden';rr.animate([{transform:'none'},{transform:'scale(1.06,.94)'},{transform:'none'}],{duration:260});zz.animate([{transform:'none'},{transform:'translateX(-8px)'},{transform:'none'}],{duration:300});
setTimeout(function(){say('0점이네 ㅋ');setTimeout(function(){say('니가? 만점이라고? 0점인데?')},1700)},900)}},1100)}}
function gate(){var n=count(),list=pool();if(cfg.o==='shuf')list=shuffle(list);list=list.slice(0,n);if(!list.length){res.innerHTML='<p class="nt">풀 문제가 없어.</p>';return}
setup.hidden=true;res.innerHTML='<div class="ai"><b>읽고 시작해</b><br>'+(D.method==='rework'?'AI 에이전트들이 실제 기출을 보고 새로 만들었고, 다른 AI 에이전트가 검수했어.':'AI 에이전트가 공식 자료를 보고 새로 만들었고, 다른 AI 에이전트가 검수했어.')+'</div><p class="nt">'+list.length+'문제 · '+(cfg.m==='t'?'시간제 '+Math.max(1,Math.round(list.length*SEC/60))+'분. 시간 끝나면 자동 채점':'시간 제한 없음. 다 풀고 채점')+'</p><div class="bar"><button id="b-go">시작</button><button class="g" id="b-no">설정으로</button></div>';
document.getElementById('b-go').onclick=function(){render(list,cfg.m==='t');window.scrollTo(0,0)};document.getElementById('b-no').onclick=function(){res.innerHTML='';setup.hidden=false}}
document.getElementById('bk-start').onclick=gate;
gb.onclick=function(){grade(false)};
rs.onclick=function(){sheet.hidden=true;sheet.innerHTML='';res.innerHTML='';bar.hidden=true;setup.hidden=false;refresh();window.scrollTo(0,setup.offsetTop-70)};
sheet.hidden=true;bar.hidden=true;refresh()})();</script>'''


TIME_SEC = [('csat-math', 200), ('csat-english', 55), ('csat-', 60), ('toeic', 45), ('realtor', 150), ('korean-history', 84), ('sqld', 108), ('adsp', 108), ('engineer-info', 90), ('aws', 83), ('driver', 60)]   # 실제 시험의 문항당 시간(초) 기준 안. 은행 파일의 sec_per_q 가 있으면 그것을 쓴다.


def _sec(d):
    if isinstance(d.get('sec_per_q'), (int, float)) and d['sec_per_q'] > 0:
        return int(d['sec_per_q'])
    return next((v for k, v in TIME_SEC if d['id'].startswith(k)), 60)



HUBJS = ("<script>(function(){var tk;try{tk=localStorage.getItem('jupjup_tok')}catch(e){}if(!tk)return;"
 "var API='https://jupjup-api.sung2011103.workers.dev';"
 "fetch(API+'/api/me',{headers:{Authorization:'Bearer '+tk}}).then(function(r){return r.ok?r.json():null}).then(function(m){var P=m&&m.prefs;if(!P||!P.goal)return;"
 "Promise.all([fetch('/assets/jam/goals.json').then(function(r){return r.json()}),fetch('/assets/jam/exams.json').then(function(r){return r.json()})]).then(function(a){"
 "var G=a[0],X=a[1],banks=[],name='';"
 "if(/^exam:/.test(P.goal)){var f=X.fams.filter(function(x){return 'exam:'+x.k===P.goal})[0];if(f){banks=f.banks;name=f.name+' 시험'}}"
 "else{var g=G.goals.filter(function(x){return x.id===P.goal})[0];if(g){banks=g.bank||[];name=g.name}}"
 "if(!banks.length)return;"
 "var root=document.querySelector('.bk');if(!root)return;var lis=root.querySelectorAll('li[data-b]'),all=false;"
 "function apply(){lis.forEach(function(li){li.hidden=!all&&banks.indexOf(li.getAttribute('data-b'))<0});"
 "root.querySelectorAll('h2').forEach(function(h){var u=h.nextElementSibling;if(u&&u.tagName==='UL'){var any=[].some.call(u.children,function(c){return !c.hidden});h.hidden=u.hidden=!any}});}"
 "var bar=document.createElement('p');bar.className='ai';bar.innerHTML='<b>내 목표: '+name.replace(/</g,'')+'</b> · 목표에 맞는 문제만 보여준다. <a href=\"#\" id=\"bk-all\">전체 보기</a>';"
 "var h1=root.querySelector('h1');h1.parentNode.insertBefore(bar,h1.nextSibling.nextSibling||h1.nextSibling);"
 "bar.querySelector('#bk-all').onclick=function(e){e.preventDefault();all=!all;this.textContent=all?'내 목표만 보기':'전체 보기';apply()};apply();"
 "})}).catch(function(){})})();</script>")


def _notes(bid):
    u"""개념 정리(쉬운 말로 다시 쓴 학습 자료) — exam_data/notes/<id>.json: {"title","intro","sections":[{"h","body","fig","key":[..]}],"recap":[..]}"""
    f = os.path.join(HERE, 'exam_data', 'notes', bid + '.json')
    if not os.path.exists(f):
        return ''
    try:
        n = json.load(open(f, encoding='utf-8'))
    except Exception:
        return ''
    out = '<section class="nts"><h2>' + E(n.get('title', '개념 정리')) + '</h2>'
    if n.get('intro'):
        out += '<p class="nts-i">' + E(n['intro']) + '</p>'
    for i, sc in enumerate(n.get('sections', []), 1):
        out += '<details class="nts-s"' + (' open' if i == 1 else '') + '><summary>' + str(i) + '. ' + E(sc.get('h', '')) + '</summary>'
        out += '<p class="nts-b">' + E(sc.get('body', '')) + '</p>'
        if sc.get('fig'):
            out += '<div class="fig">' + sc['fig'] + '</div>'
        if sc.get('key'):
            out += '<ul class="nts-k">' + ''.join('<li>' + E(k) + '</li>' for k in sc['key']) + '</ul>'
        out += '</details>'
    if n.get('recap'):
        out += '<div class="nts-r"><b>한 장 요약</b><ul>' + ''.join('<li>' + E(k) + '</li>' for k in n['recap']) + '</ul></div>'
    return out + '</section>'


def _load():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, 'exam_data', 'bank', '*.json'))):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        qs = [q for q in d.get('questions', []) if q.get('q') and isinstance(q.get('choices'), list) and len(q['choices']) >= 2 and isinstance(q.get('answer'), int) and 0 <= q['answer'] < len(q['choices'])]
        if d.get('hold'):
            continue   # 검증 전 보류(공개 안 함)
        if d.get('id') and qs:
            d['questions'] = qs
            out.append(d)
    return out


def _badge(d):
    return ('<span class="bd pb">공식 기출</span>' if d.get('kind') == 'public' else ('<span class="bd">AI 제작</span>' if d.get('method') == 'rework' else '<span class="bd">AI 제작</span>'))


def pages(page):
    banks = _load()
    if not banks:
        return []
    urls = []
    for d in banks:
        src = d.get('source') or {}
        srct = (f'출처: <a href="{E(src["url"])}" target="_blank" rel="noopener nofollow">{E(src.get("name", "공식 자료"))}</a>' if src.get('url') else E(src.get('name', '')))
        lic = f' · 이용 조건: {E(src["license"])}' if src.get('license') else ''
        note = (('AI 에이전트들이 실제 기출을 보고 새로 만들었고, 다른 AI 에이전트가 검수했어.'
                 if d.get('method') == 'rework' else 'AI 에이전트가 공식 자료를 보고 새로 만들었고, 다른 AI 에이전트가 검수했어.')
                if d.get('kind') != 'public' else '기관이 재사용을 허용한 기출문제야. 이용 조건을 지켜서 올렸어.')
        lst = ''
        for i, q in enumerate(d['questions'], 1):
            lst += (f'<div class="q"><p><b class="n">{i}.</b>{E(q["q"])}</p><ol class="c">' + ''.join(f'<li>{E(c)}</li>' for c in q['choices']) + '</ol>'
                    f'<details><summary>풀이 보기</summary><p>정답 {q["answer"] + 1}번. {E(q.get("explain", ""))}' + '</p>' + (f'<div class="fig">{q["fig"]}</div>' if q.get('fig') else '') + '</details></div>')
        eu = f'/exam/{d["exam_id"]}/' if d.get('exam_id') and os.path.exists(os.path.join(os.path.dirname(HERE), 'exam', d['exam_id'], 'index.html')) else ''
        data = json.dumps({'id': d['id'], 'sec_per_q': _sec(d), 'method': d.get('method', ''), 'questions': [{'q': q['q'], 'choices': q['choices'], 'answer': q['answer'], 'explain': q.get('explain', ''), 'fig': q.get('fig', '')} for q in d['questions']]}, ensure_ascii=False).replace('</', '<' + chr(92) + '/')
        AINOTE = ''
        _n = len(d['questions'])
        _setup = ('<div class="setup" id="bk-setup"><h2>시험 볼 거면 정해</h2>'
                  f'<div class="row"><b>문제 수</b><span class="grp" data-k="n"><button data-n="10">10</button><button data-n="20">20</button><button data-n="all" class="on">전체 {_n}</button></span><input type="number" id="bk-n" min="1" max="{_n}" placeholder="직접 입력" aria-label="문제 수 직접 입력"></div>'
                  '<div class="row"><b>방식</b><span class="grp" data-k="m"><button data-m="p" class="on">풀고 채점</button><button data-m="t">시간제</button></span></div>'
                  '<div class="row"><b>순서</b><span class="grp" data-k="o"><button data-o="seq" class="on">순서대로</button><button data-o="shuf">섞기</button></span></div>'
                  '<div class="row"><b>범위</b><span class="grp" data-k="r"><button data-r="all" class="on">전체</button><button data-r="wrong" hidden>지난번 틀린 문제</button></span></div>'
                  '<p class="nt" id="bk-info"></p><div class="bar"><button id="bk-start">시작해</button></div></div>')
        body = (f'<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › <a href="/exam/bank/">문제은행</a> › {E(d["name"])}</p><h1>{E(d["name"])} 문제은행 {_badge(d)}</h1>'
                f'<p class="nt">{srct}{lic}</p>{AINOTE}<p>{E(note)}</p>' + _notes(d['id']) + (f'<p><a href="{eu}">이 시험의 일정·접수·발표일 보기 →</a></p>' if eu else '')
                + '<div class="play" id="bk-play">' + _setup
                + '<div id="bk-res"></div><p class="clk" id="bk-clock" hidden></p><form id="bk-sheet" onsubmit="return false" hidden></form>'
                '<div class="bar" id="bk-gbar" hidden><button id="bk-grade">채점하기</button></div><div class="bar"><button class="g" id="bk-reset" hidden>설정으로 돌아가기</button></div></div>'
                f'<noscript>{lst}</noscript><script type="application/json" id="bk-data">{data}</script>' + '</div>' + CSS + CSS2 + JS)
        page(f'/exam/bank/{d["id"]}/', f'{d["name"]} 문제은행 — 무료 연습문제 {len(d["questions"])}개 — 가난한 박과장', f'{d["name"]} 연습문제 {len(d["questions"])}개를 한 문제씩 풀고 정답·해설과 근거를 확인해. 틀린 문제만 다시 풀 수 있어.', body,
             [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/'), (d['name'], f'/exam/bank/{d["id"]}/')])
        urls.append(f'/exam/bank/{d["id"]}/')
    def _li(L):
        return ''.join(f'<li data-b="{E(d["id"])}"><a href="/exam/bank/{E(d["id"])}/"><b>{E(d["name"])}</b></a> {_badge(d)} <small>문제 {len(d["questions"])}개</small></li>' for d in L)
    _grp = [('시험·자격증', lambda c: not (c.startswith('초등') or c.startswith('중·고등') or c.startswith('대학 전공') or c == '자기개발')),
            ('초등 교과', lambda c: c.startswith('초등')), ('중·고등 교과', lambda c: c.startswith('중·고등')),
            ('대학 전공 기초', lambda c: c.startswith('대학 전공')), ('자기개발', lambda c: c == '자기개발')]
    li = ''
    for _gn, _fn in _grp:
        _L = [d for d in banks if _fn(d.get('category') or '')]
        if _L:
            li += '<h2>' + _gn + ' <small>' + str(len(_L)) + '개</small></h2><ul>' + _li(_L) + '</ul>'
    hub = ('<div class="bk"><p class="bc"><a href="/">홈</a> › <a href="/exam/">시험</a> › 문제은행</p><h1>시험 문제은행</h1>'
           '<p>시험별 연습문제. 풀고 풀이 봐. AI 에이전트가 만들고 다른 AI 에이전트가 검수했어.</p>'
           f'{li}</div>' + HUBJS + CSS + CSS2)
    page('/exam/bank/', '시험 문제은행 — 자격증·공무원·수능 무료 연습문제 — 가난한 박과장', '자격증·공무원·수능 시험별 연습문제를 풀고 정답과 해설, 근거 링크를 확인해. 틀린 문제만 다시 풀 수 있어.', hub, [('홈', '/'), ('시험', '/exam/'), ('문제은행', '/exam/bank/')])
    urls.append('/exam/bank/')
    print('시험 문제은행', len(banks), '종')
    return urls
