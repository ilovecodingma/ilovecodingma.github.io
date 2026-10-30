# -*- coding: utf-8 -*-
"""미니게임 페이지 생성기 (play/<slug>/index.html). 공통 머리말·설명·다른 게임 링크를 붙인다.
사용: python -X utf8 _gongmo/make_games.py"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEAD = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());if(location.hostname!=='sungprofile.cloud')window['ga-disable-G-G9BPFF95GY']=true;gtag('config','G-G9BPFF95GY');</script>
<title>%(title)s | 루리의 놀이터</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="https://sungprofile.cloud/play/%(slug)s/">
<meta property="og:title" content="%(og)s"><meta property="og:description" content="%(desc)s"><meta property="og:image" content="https://sungprofile.cloud/assets/ruri/og.jpg"><meta property="og:url" content="https://sungprofile.cloud/play/%(slug)s/">
<link rel="icon" href="/favicon.ico?v=6" sizes="any">
<link rel="stylesheet" href="/play/play.css?v=1">
<style>
html,body{overscroll-behavior:none}
.cvw{position:relative;width:100%%;background:#0e0b18;border-radius:16px;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none}
canvas{display:block;width:100%%}
.ov{position:absolute;inset:0;background:rgba(14,11,24,.86);display:none;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:16px;text-align:center;z-index:5}
.ov.on{display:flex}.ov h2{margin:0;font-size:24px}.ov p{margin:0;color:var(--mu);font-size:14px;line-height:1.6}
%(css)s
</style>
</head>
<body>
<div class="pw">
  <div class="top"><a href="/play/">← 게임 모음</a><b>%(emoji)s %(name)s</b><a href="/">루리의 줍줍</a></div>
%(body)s
  <main class="how">
    <h2>게임 방법</h2>
    <ul>%(how)s</ul>
    <p>다른 게임: <a href="/play/survivor/">루리 서바이벌</a> · <a href="/play/runner/">루리 런</a> · <a href="/play/dodge/">마감 피하기</a> · <a href="/play/clicker/">줍줍 클리커</a> · <a href="/play/mole/">두더지 잡기</a> · <a href="/play/snake/">스네이크</a> · <a href="/play/">미니게임 모음</a></p>
  </main>
</div>
<script src="/play/play.js?v=1"></script>
<script>
%(js)s
</script>
</body>
</html>
'''

G = {}

# ───────────────────────── 루리 런 ─────────────────────────
G['runner'] = dict(emoji='🏃', name='루리 런', title='루리 런 — 무료 달리기 점프 게임, 가입 없이 바로 시작', og='루리 런',
    desc='서류 더미와 알람을 뛰어넘어 최대한 멀리 달리는 무료 러닝 게임. 화면을 탭하면 점프! 설치·가입 없이 모바일과 PC에서 바로 플레이.',
    how='<li>화면을 탭(PC는 스페이스·위 방향키)하면 점프해요. 길게 누르면 더 높이 올라가요.</li><li>서류·알람·상자에 부딪히지 않고 달릴수록 점수가 올라가요. 속도는 점점 빨라져요.</li><li>최고 기록은 이 브라우저에 자동 저장돼요.</li>',
    css='', body='''  <div class="stat"><div><small>거리</small><b id="sc">0</b></div><div><small>최고</small><b id="best">0</b></div><div><small>🔥 접속</small><b id="stk">1일</b></div></div>
  <div class="cvw"><canvas id="cv" width="720" height="360"></canvas>
    <div class="ov on" id="ov"><h2 id="ot">🏃 루리 런</h2><p id="op">탭하면 점프! 장애물을 피해 달려요</p><button class="btn big" id="go" style="max-width:260px">시작</button><button class="btn g" id="sh" style="display:none">📤 자랑</button></div></div>''',
    js='''(function(){var $=PLAY.$,cv=$('cv'),x=cv.getContext('2d'),W=720,H=360,GY=300;
var img=new Image();img.src='/assets/ruri/o_suit_s.webp';
var SP={};function spr(ch,s){var k=ch+s;if(SP[k])return SP[k];var c=document.createElement('canvas');c.width=c.height=s*2;var g=c.getContext('2d');g.font=(s*1.5)+'px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText(ch,s,s+s*0.08);return SP[k]=c;}
var best=PLAY.load('runBest',0),st,run=false,last=0,hold=false;$('best').textContent=best;$('stk').textContent=PLAY.streak().n+'일';
function init(){st={y:GY,vy:0,on:true,sp:260,d:0,ob:[],nx:1.1,t:0,jumps:0};}
function jump(){if(!run)return;if(st.on){st.vy=-560;st.on=false;PLAY.vib(6);}hold=true;}
function rel(){hold=false;}
function loop(n){var dt=Math.min(0.04,(n-last)/1000);last=n;if(run){upd(dt);}draw();requestAnimationFrame(loop);}
function upd(dt){st.t+=dt;st.sp=Math.min(620,260+st.d*0.05);st.d+=st.sp*dt;
var g=hold&&st.vy<0?1100:2000;st.vy+=g*dt;st.y+=st.vy*dt;if(st.y>=GY){st.y=GY;st.vy=0;st.on=true;}
st.nx-=dt;if(st.nx<=0){var k=Math.floor(Math.random()*3),c=['📄','⏰','📦'][k],s=[22,24,30][k];st.ob.push({x:W+40,c:c,s:s});st.nx=Math.max(0.55,1.25-st.d/9000)+Math.random()*0.7;}
for(var i=st.ob.length-1;i>=0;i--){var o=st.ob[i];o.x-=st.sp*dt;if(o.x<-60){st.ob.splice(i,1);continue;}
if(Math.abs(o.x-90)<o.s*0.62+12&&st.y>GY-o.s*1.15-6)die();}
$('sc').textContent=Math.floor(st.d/10);}
function die(){run=false;var s=Math.floor(st.d/10),nb=s>best;if(nb){best=s;PLAY.save('runBest',best);$('best').textContent=best;}
$('ot').textContent=nb?'🏅 신기록!':'💥 아야!';$('op').textContent=s+'m 달렸어요 · 최고 '+best+'m';$('go').textContent='다시 하기';$('sh').style.display='';$('ov').classList.add('on');PLAY.ga('runner_end',{score:s});PLAY.vib(40);}
function draw(){x.clearRect(0,0,W,H);var gr=x.createLinearGradient(0,0,0,H);gr.addColorStop(0,'#1c1533');gr.addColorStop(1,'#2a2142');x.fillStyle=gr;x.fillRect(0,0,W,H);
x.fillStyle='#ffffff14';for(var i=0;i<8;i++){var bx=((i*140-(st?st.d*0.25:0))%(W+140)+W+140)%(W+140)-70;x.fillRect(bx,40+(i%3)*30,60,6);}
x.fillStyle='#3a2f5c';x.fillRect(0,GY+26,W,H-GY-26);x.fillStyle='#b794ff';x.fillRect(0,GY+26,W,3);
if(!st)return;st.ob.forEach(function(o){x.drawImage(spr(o.c,o.s),o.x-o.s,GY+26-o.s*2+4,o.s*2,o.s*2);});
if(img.complete&&img.naturalWidth){var by=st.y-6+(st.on?Math.sin(st.d*0.05)*3:0);x.drawImage(img,70,by-34,40,56);}else{x.fillStyle='#b794ff';x.fillRect(70,st.y-40,36,50);}}
function start(){init();run=true;$('ov').classList.remove('on');$('sh').style.display='none';last=performance.now();PLAY.ga('runner_start');}
$('go').onclick=start;$('sh').onclick=function(){PLAY.share('루리 런 '+best+'m 달렸어요! 도전해 봐요','runner');};
cv.addEventListener('touchstart',function(e){e.preventDefault();jump();},{passive:false});cv.addEventListener('touchend',rel);
cv.addEventListener('mousedown',jump);window.addEventListener('mouseup',rel);
window.addEventListener('keydown',function(e){if(e.code==='Space'||e.key==='ArrowUp'){e.preventDefault();if(!run&&$('ov').classList.contains('on')){start();return;}jump();}});
window.addEventListener('keyup',function(e){if(e.code==='Space'||e.key==='ArrowUp')rel();});
init();requestAnimationFrame(loop);})();''')

# ───────────────────────── 마감 피하기 ─────────────────────────
G['dodge'] = dict(emoji='☄️', name='마감 피하기', title='마감 피하기 — 무료 총알 피하기 게임, 가입 없이 바로 시작', og='마감 피하기',
    desc='하늘에서 쏟아지는 서류·알람·지출을 손가락으로 피하는 무료 탄막 피하기 게임. 별을 먹으면 점수 보너스! 가입 없이 바로 플레이.',
    how='<li>화면을 손가락(PC는 마우스)으로 드래그해 루리를 움직여요. 떨어지는 장애물에 닿으면 끝나요.</li><li>시간이 지날수록 더 많이, 더 빠르게 쏟아져요.</li><li>⭐ 별을 먹으면 보너스 점수와 잠깐의 무적이 생겨요.</li>',
    css='', body='''  <div class="stat"><div><small>생존</small><b id="sc">0.0초</b></div><div><small>최고</small><b id="best">-</b></div><div><small>⭐ 별</small><b id="stars">0</b></div></div>
  <div class="cvw"><canvas id="cv" width="480" height="640"></canvas>
    <div class="ov on" id="ov"><h2 id="ot">☄️ 마감 피하기</h2><p id="op">드래그해서 떨어지는 마감을 피해요</p><button class="btn big" id="go" style="max-width:260px">시작</button><button class="btn g" id="sh" style="display:none">📤 자랑</button></div></div>''',
    js='''(function(){var $=PLAY.$,cv=$('cv'),x=cv.getContext('2d'),W=480,H=640;
var img=new Image();img.src='/assets/ruri/o_suit_s.webp';
var SP={};function spr(ch,s){var k=ch+s;if(SP[k])return SP[k];var c=document.createElement('canvas');c.width=c.height=s*2;var g=c.getContext('2d');g.font=(s*1.5)+'px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText(ch,s,s+s*0.08);return SP[k]=c;}
var best=PLAY.load('dodgeBest',0),st,run=false,last=0,tx=W/2,ty=H-120;$('best').textContent=best?best.toFixed(1)+'초':'-';PLAY.streak();
function init(){st={px:W/2,py:H-120,t:0,hz:[],sp:0.5,stars:0,inv:0};tx=W/2;ty=H-120;$('stars').textContent=0;}
function upd(dt){st.t+=dt;if(st.inv>0)st.inv-=dt;st.px+=(tx-st.px)*Math.min(1,dt*14);st.py+=(ty-st.py)*Math.min(1,dt*14);
st.sp-=dt;if(st.sp<=0){var n=1+Math.floor(st.t/20);for(var i=0;i<n;i++){var k=Math.floor(Math.random()*3),star=Math.random()<0.07;st.hz.push({x:20+Math.random()*(W-40),y:-30,vy:(star?150:150+Math.random()*120+st.t*4),c:star?'⭐':['📄','⏰','💸'][k],s:star?16:20+Math.random()*10,star:star});}st.sp=Math.max(0.16,0.55-st.t*0.006);}
for(var j=st.hz.length-1;j>=0;j--){var h=st.hz[j];h.y+=h.vy*dt;if(h.y>H+40){st.hz.splice(j,1);continue;}
if(Math.hypot(h.x-st.px,h.y-st.py)<h.s*0.7+14){if(h.star){st.stars++;st.inv=1.2;st.hz.splice(j,1);$('stars').textContent=st.stars;PLAY.vib(10);}else if(st.inv<=0){die();return;}}}
$('sc').textContent=(st.t+st.stars*2).toFixed(1)+'초';}
function die(){run=false;var s=st.t+st.stars*2,nb=s>best;if(nb){best=s;PLAY.save('dodgeBest',best);$('best').textContent=best.toFixed(1)+'초';}
$('ot').textContent=nb?'🏅 신기록!':'💥 마감에 맞았어요';$('op').textContent=s.toFixed(1)+'초 버텼어요 (별 '+st.stars+'개) · 최고 '+best.toFixed(1)+'초';$('go').textContent='다시 하기';$('sh').style.display='';$('ov').classList.add('on');PLAY.ga('dodge_end',{score:Math.floor(s)});PLAY.vib(40);}
function draw(){x.fillStyle='#120e1f';x.fillRect(0,0,W,H);x.fillStyle='#ffffff10';for(var i=0;i<30;i++){x.fillRect((i*97)%W,((i*61+(st?st.t*60:0))%H),2,2);}
if(!st)return;st.hz.forEach(function(h){x.drawImage(spr(h.c,h.s),h.x-h.s,h.y-h.s,h.s*2,h.s*2);});
if(st.inv>0){x.strokeStyle='#ffd166';x.lineWidth=3;x.beginPath();x.arc(st.px,st.py,26,0,6.283);x.stroke();}
if(img.complete&&img.naturalWidth)x.drawImage(img,st.px-18,st.py-26,36,50);else{x.fillStyle='#b794ff';x.beginPath();x.arc(st.px,st.py,14,0,6.283);x.fill();}}
function loop(n){var dt=Math.min(0.04,(n-last)/1000);last=n;if(run)upd(dt);draw();requestAnimationFrame(loop);}
function pos(cx,cy){var r=cv.getBoundingClientRect();tx=(cx-r.left)/r.width*W;ty=(cy-r.top)/r.height*H-30;tx=Math.max(16,Math.min(W-16,tx));ty=Math.max(30,Math.min(H-16,ty));}
cv.addEventListener('touchstart',function(e){e.preventDefault();pos(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});cv.addEventListener('touchmove',function(e){e.preventDefault();pos(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});
cv.addEventListener('mousemove',function(e){pos(e.clientX,e.clientY);});
function start(){init();run=true;$('ov').classList.remove('on');$('sh').style.display='none';last=performance.now();PLAY.ga('dodge_start');}
$('go').onclick=start;$('sh').onclick=function(){PLAY.share('마감 피하기 '+best.toFixed(1)+'초 버텼어요! 도전해 봐요','dodge');};
init();requestAnimationFrame(loop);})();''')

# ───────────────────────── 줍줍 클리커 ─────────────────────────
G['clicker'] = dict(emoji='🪙', name='줍줍 클리커', title='줍줍 클리커 — 무료 방치형 클릭 게임, 가입 없이 바로 시작', og='줍줍 클리커',
    desc='루리를 눌러 용돈을 줍고, 자동 줍기를 늘려 부자가 되는 무료 방치형 클릭 게임. 꺼 놔도 쌓여요. 가입 없이 바로 플레이.',
    how='<li>루리를 탭(클릭)하면 용돈을 주워요. 모은 돈으로 업그레이드를 사면 초당 자동 수입이 늘어요.</li><li>게임을 꺼 둬도 시간이 지난 만큼(최대 2시간) 돈이 쌓여 있어요.</li><li>목표: 「공모왕」 칭호까지! 진행 상황은 이 브라우저에 자동 저장돼요. 실제 돈이 아니라 게임 점수예요.</li>',
    css='''#big{display:block;margin:6px auto 12px;width:min(52vw,210px);background:radial-gradient(circle,#4c2a85,#2a2142);border:0;border-radius:50%;aspect-ratio:1/1;cursor:pointer;padding:0;box-shadow:0 10px 30px -10px #b794ff}
#big img{width:70%;pointer-events:none}#big:active{transform:scale(.95)}
.up{display:flex;justify-content:space-between;align-items:center;gap:8px;background:var(--card);border-radius:12px;padding:10px 12px;margin:7px 0;font-size:13px}
.up b{display:block;font-size:14px}.up span{color:var(--mu);font-size:11.5px}.up .btn{padding:8px 12px;font-size:13px;flex:none}
.pop{position:fixed;pointer-events:none;color:var(--gold);font-weight:900;font-size:18px;animation:fl .8s forwards;z-index:30}
@keyframes fl{to{transform:translateY(-50px);opacity:0}}''',
    body='''  <div class="stat"><div><small>🪙 용돈</small><b id="c">0</b></div><div><small>초당</small><b id="ps">0</b></div><div><small>칭호</small><b id="tt" style="font-size:13px">줍줍 신입</b></div></div>
  <button id="big" aria-label="루리를 눌러 용돈 줍기"><img src="/assets/ruri/o_suit.webp" alt="루리"></button>
  <div id="ups"></div>
  <div class="row" style="margin-top:10px"><button class="btn g" id="sh">📤 자랑</button></div>''',
    js='''(function(){var $=PLAY.$;
var U=[['👆','손가락 단련','탭당 +1',15,1.18,'tap',1],['🪙','동전 자판기','초당 +1',60,1.17,'ps',1],['📰','신문 배달','초당 +6',600,1.17,'ps',6],['🏪','편의점 알바','초당 +30',5500,1.16,'ps',30],['📈','주식 줍기','초당 +180',48000,1.16,'ps',180],['🏢','공모전 사무실','초당 +1,200',420000,1.15,'ps',1200],['🏆','공모왕 길드','초당 +9,000',3800000,1.15,'ps',9000]];
var TT=[[0,'줍줍 신입'],[1e3,'용돈 사냥꾼'],[5e4,'알뜰 달인'],[1e6,'공모 부자'],[1e8,'공모왕']];
var S=PLAY.load('clk',{c:0,tot:0,lv:[0,0,0,0,0,0,0],t:Date.now()});if(!S.lv||S.lv.length<U.length)S.lv=U.map(function(_,i){return (S.lv&&S.lv[i])||0;});
function tap(){var v=1;U.forEach(function(u,i){if(u[5]==='tap')v+=u[6]*S.lv[i];});return v;}
function ps(){var v=0;U.forEach(function(u,i){if(u[5]==='ps')v+=u[6]*S.lv[i];});return v;}
function cost(i){return Math.round(U[i][3]*Math.pow(U[i][4],S.lv[i]));}
function f(n){return PLAY.fmt(n);}
var now=Date.now(),off=Math.min(7200,(now-S.t)/1000)*ps();if(off>=1){S.c+=off;S.tot+=off;setTimeout(function(){PLAY.toast('자리를 비운 동안 🪙 '+f(off)+' 쌓였어요!',3000);},400);}S.t=now;
function title(){var t=TT[0][1];TT.forEach(function(x){if(S.tot>=x[0])t=x[1];});return t;}
function render(){$('c').textContent=f(S.c);$('ps').textContent=f(ps());$('tt').textContent=title();
var el=$('ups');if(!el.children.length){U.forEach(function(u,i){var d=document.createElement('div');d.className='up';d.innerHTML='<div><b>'+u[0]+' '+u[1]+' <small id="l'+i+'"></small></b><span>'+u[2]+'</span></div><button class="btn" id="b'+i+'"></button>';el.appendChild(d);$('b'+i).onclick=function(){buy(i);};});}
U.forEach(function(u,i){$('l'+i).textContent='Lv.'+S.lv[i];$('b'+i).textContent='🪙 '+f(cost(i));$('b'+i).disabled=S.c<cost(i);});}
function buy(i){var c=cost(i);if(S.c<c)return;S.c-=c;S.lv[i]++;PLAY.save('clk',S);render();PLAY.vib(8);PLAY.ga('clicker_buy',{i:i,l:S.lv[i]});}
$('big').onclick=function(e){var v=tap();S.c+=v;S.tot+=v;var p=document.createElement('div');p.className='pop';p.textContent='+'+f(v);p.style.left=(e.clientX||innerWidth/2)-10+'px';p.style.top=(e.clientY||innerHeight/2)-20+'px';document.body.appendChild(p);setTimeout(function(){p.remove();},800);PLAY.vib(4);};
setInterval(function(){var v=ps()/4;if(v){S.c+=v;S.tot+=v;}S.t=Date.now();render();},250);setInterval(function(){PLAY.save('clk',S);},3000);
$('sh').onclick=function(){PLAY.share('줍줍 클리커 '+title()+' · 누적 🪙'+f(S.tot)+' — 같이 줍줍해요!','clicker');};
PLAY.streak();render();})();''')

# ───────────────────────── 두더지 잡기 ─────────────────────────
G['mole'] = dict(emoji='🔨', name='루리 두더지 잡기', title='루리 두더지 잡기 — 무료 반응속도 게임, 가입 없이 바로 시작', og='루리 두더지 잡기',
    desc='구멍에서 튀어나오는 루리를 재빨리 눌러 잡는 30초 반응속도 게임. 폭탄은 조심! 최고 점수 자동 저장, 가입 없이 바로 플레이.',
    how='<li>구멍에서 튀어나오는 루리를 눌러 점수를 얻어요. 30초 안에 최대한 많이!</li><li>💣 폭탄을 누르면 점수가 깎여요. 폭탄은 눌러선 안 돼요.</li><li>연속으로 잡으면 콤보 보너스가 붙어요.</li>',
    css='''#hl{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:6px 0}
.h{position:relative;aspect-ratio:1/1;background:radial-gradient(ellipse at 50% 80%,#0b0814 40%,#2a2142 41%);border-radius:50%;overflow:hidden;cursor:pointer;border:0;padding:0}
.h img{position:absolute;left:50%;bottom:-100%;transform:translateX(-50%);height:88%;transition:bottom .12s;pointer-events:none}
.h.up img{bottom:6%}.h .bm{position:absolute;left:0;right:0;bottom:-100%;font-size:44px;text-align:center;transition:bottom .12s;pointer-events:none}.h.bomb .bm{bottom:18%}
.h.hit{background:radial-gradient(ellipse at 50% 80%,#244a35 40%,#2a2142 41%)}''',
    body='''  <div class="stat"><div><small>점수</small><b id="sc">0</b></div><div><small>남은 시간</small><b id="tm">30</b></div><div><small>최고</small><b id="best">0</b></div></div>
  <div style="position:relative"><div id="hl"></div>
    <div class="ov on" id="ov" style="border-radius:16px"><h2 id="ot">🔨 두더지 잡기</h2><p id="op">튀어나오는 루리를 눌러요!<br>💣 폭탄은 누르면 안 돼요</p><button class="btn big" id="go" style="max-width:260px">시작</button><button class="btn g" id="sh" style="display:none">📤 자랑</button></div></div>''',
    js='''(function(){var $=PLAY.$,names=['suit','gray','cardigan','present','desk','anchor','trench','vest','cook'];
var best=PLAY.load('moleBest',0),sc=0,tl=30,run=false,combo=0,timer=null,spawn=null,hs=[];$('best').textContent=best;PLAY.streak();
var hl=$('hl');for(var i=0;i<9;i++){(function(i){var h=document.createElement('button');h.className='h';h.innerHTML='<img src="/assets/ruri/o_suit_s.webp" alt=""><div class="bm">💣</div>';h.onclick=function(){hit(i);};hl.appendChild(h);hs.push({el:h,st:0,to:null});})(i);}
function up(i){var o=hs[i];if(o.st)return;var bomb=Math.random()<0.18;o.st=bomb?2:1;o.el.classList.add(bomb?'bomb':'up');if(!bomb)o.el.querySelector('img').src='/assets/ruri/o_'+names[PLAY.rnd(names.length)]+'_s.webp';
o.to=setTimeout(function(){down(i);if(!bomb)combo=0;},Math.max(520,1050-(30-tl)*14));}
function down(i){var o=hs[i];o.st=0;o.el.classList.remove('up','bomb','hit');clearTimeout(o.to);}
function hit(i){if(!run)return;var o=hs[i];if(!o.st)return;if(o.st===1){combo++;sc+=10+Math.min(combo,10)*2;o.el.classList.add('hit');PLAY.vib(10);}else{sc=Math.max(0,sc-30);combo=0;PLAY.vib(40);}$('sc').textContent=sc;clearTimeout(o.to);setTimeout(function(){down(i);},90);}
function tick(){tl--;$('tm').textContent=tl;if(tl<=0)end();}
function sp(){if(!run)return;var n=1+(tl<15?1:0);for(var k=0;k<n;k++)up(PLAY.rnd(9));spawn=setTimeout(sp,Math.max(330,720-(30-tl)*10));}
function start(){sc=0;tl=30;combo=0;run=true;$('sc').textContent=0;$('tm').textContent=30;$('ov').classList.remove('on');$('sh').style.display='none';timer=setInterval(tick,1000);sp();PLAY.ga('mole_start');}
function end(){run=false;clearInterval(timer);clearTimeout(spawn);hs.forEach(function(o,i){down(i);});var nb=sc>best;if(nb){best=sc;PLAY.save('moleBest',best);$('best').textContent=best;}
$('ot').textContent=nb?'🏅 신기록!':'⏰ 끝!';$('op').textContent=sc+'점 · 최고 '+best+'점';$('go').textContent='다시 하기';$('sh').style.display='';$('ov').classList.add('on');PLAY.ga('mole_end',{score:sc});}
$('go').onclick=start;$('sh').onclick=function(){PLAY.share('루리 두더지 잡기 '+best+'점! 도전해 봐요','mole');};})();''')

# ───────────────────────── 스네이크 ─────────────────────────
G['snake'] = dict(emoji='🐍', name='스네이크', title='스네이크 — 무료 뱀 게임, 가입 없이 바로 시작', og='스네이크',
    desc='먹이를 먹고 길어지는 고전 스네이크(뱀) 게임. 스와이프·방향키로 조작하고 벽과 몸에 부딪히지 않게! 최고 점수 자동 저장.',
    how='<li>스와이프(PC는 방향키·WASD)로 방향을 바꿔요. 🍙를 먹으면 길어지고 점수가 올라요.</li><li>벽이나 자기 몸에 부딪히면 끝나요. 점수가 오를수록 빨라져요.</li><li>최고 점수는 이 브라우저에 저장돼요.</li>',
    css='', body='''  <div class="stat"><div><small>점수</small><b id="sc">0</b></div><div><small>최고</small><b id="best">0</b></div><div><small>🔥 접속</small><b id="stk">1일</b></div></div>
  <div class="cvw"><canvas id="cv" width="540" height="540"></canvas>
    <div class="ov on" id="ov"><h2 id="ot">🐍 스네이크</h2><p id="op">스와이프·방향키로 조작해요</p><button class="btn big" id="go" style="max-width:260px">시작</button><button class="btn g" id="sh" style="display:none">📤 자랑</button></div></div>''',
    js='''(function(){var $=PLAY.$,cv=$('cv'),x=cv.getContext('2d'),N=18,C=30;
var best=PLAY.load('snakeBest',0),sn,dir,nd,food,sc,run=false,iv=null;$('best').textContent=best;$('stk').textContent=PLAY.streak().n+'일';
function rf(){var p;do{p=[PLAY.rnd(N),PLAY.rnd(N)];}while(sn.some(function(s){return s[0]===p[0]&&s[1]===p[1];}));food=p;}
function start(){sn=[[9,9],[8,9],[7,9]];dir=[1,0];nd=[1,0];sc=0;$('sc').textContent=0;rf();run=true;$('ov').classList.remove('on');$('sh').style.display='none';clearInterval(iv);iv=setInterval(step,speed());draw();PLAY.ga('snake_start');}
function speed(){return Math.max(60,150-sc*2);}
function step(){dir=nd;var h=[sn[0][0]+dir[0],sn[0][1]+dir[1]];
if(h[0]<0||h[1]<0||h[0]>=N||h[1]>=N||sn.some(function(s){return s[0]===h[0]&&s[1]===h[1];})){over();return;}
sn.unshift(h);if(h[0]===food[0]&&h[1]===food[1]){sc+=10;$('sc').textContent=sc;rf();PLAY.vib(8);clearInterval(iv);iv=setInterval(step,speed());}else sn.pop();draw();}
function over(){run=false;clearInterval(iv);var nb=sc>best;if(nb){best=sc;PLAY.save('snakeBest',best);$('best').textContent=best;}
$('ot').textContent=nb?'🏅 신기록!':'💥 앗!';$('op').textContent=sc+'점 · 최고 '+best+'점';$('go').textContent='다시 하기';$('sh').style.display='';$('ov').classList.add('on');PLAY.ga('snake_end',{score:sc});PLAY.vib(40);}
function draw(){x.fillStyle='#120e1f';x.fillRect(0,0,540,540);x.fillStyle='#ffffff08';for(var i=0;i<N;i++)for(var j=0;j<N;j++)if((i+j)%2)x.fillRect(i*C,j*C,C,C);
x.font='24px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText('🍙',food[0]*C+C/2,food[1]*C+C/2+2);
sn.forEach(function(s,i){x.fillStyle=i===0?'#d8c4ff':'hsl('+(265-i*3)+',70%,'+(62-Math.min(i,20))+'%)';x.beginPath();x.roundRect?x.roundRect(s[0]*C+2,s[1]*C+2,C-4,C-4,8):x.rect(s[0]*C+2,s[1]*C+2,C-4,C-4);x.fill();});}
function turn(d){if(!run)return;if(d[0]===-dir[0]&&d[1]===-dir[1])return;nd=d;}
window.addEventListener('keydown',function(e){var m={ArrowUp:[0,-1],w:[0,-1],ArrowDown:[0,1],s:[0,1],ArrowLeft:[-1,0],a:[-1,0],ArrowRight:[1,0],d:[1,0]}[e.key];if(m){e.preventDefault();turn(m);}if(e.code==='Space'&&!run&&$('ov').classList.contains('on')){e.preventDefault();start();}});
var sx,sy;cv.addEventListener('touchstart',function(e){e.preventDefault();sx=e.touches[0].clientX;sy=e.touches[0].clientY;},{passive:false});
cv.addEventListener('touchmove',function(e){e.preventDefault();if(sx==null)return;var dx=e.touches[0].clientX-sx,dy=e.touches[0].clientY-sy;if(Math.max(Math.abs(dx),Math.abs(dy))<18)return;if(Math.abs(dx)>Math.abs(dy))turn(dx>0?[1,0]:[-1,0]);else turn(dy>0?[0,1]:[0,-1]);sx=e.touches[0].clientX;sy=e.touches[0].clientY;},{passive:false});
cv.addEventListener('touchend',function(){sx=null;});
$('go').onclick=start;$('sh').onclick=function(){PLAY.share('스네이크 '+best+'점! 도전해 봐요','snake');};
sn=[[9,9],[8,9],[7,9]];food=[12,9];draw();})();''')

for slug, g in G.items():
    d = os.path.join(ROOT, 'play', slug)
    os.makedirs(d, exist_ok=True)
    g = dict(g, slug=slug)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n').write(HEAD % g)
    print('작성', slug)
