# -*- coding: utf-8 -*-
"""하네스 과정(/park/) — 책·하네스 저장소와 짝이 되는 학습 구역 (2026-11-12 사용자: 「하네스에 대한 LMS도 하나, 하네스에서 토큰 발급하고 그거 입력하면 우리 사이트에서 관련된 샘플들도 나오게」).
/park/        과정 소개와 관문 여덟 개(토큰 없이도 다 보인다)
/park/start/  토큰을 넣으면 내 진도와 그 자리에 맞는 샘플·다음에 할 말이 나온다
서버는 별도 워커 jupjup-lms(_gongmo/lms/). 받는 것은 토큰과 진도뿐이고 이메일·이름은 받지 않는다. 토큰은 이 브라우저의 localStorage 에만 둔다."""
import json, os, html

E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))

# 관문: 하네스가 보내는 step 이름과 같은 열쇠. samples 는 이 사이트에 실제로 있는 쪽만 건다.
STEPS = [
    dict(k='start', ch='시작', t='토큰을 받았다', done='하네스에서 토큰을 받아 이 사이트와 이었습니다.',
         say='시작하자', why='첫 엔터 뒤에 주소가 나올 때까지 세션이 혼자 채웁니다. 주제를 한 줄 붙여도 됩니다. 예) 시작하자, 주말에 걷기 좋은 길',
         samples=[('/dev/multi-ai-sessions/', '세션 여러 개로 사이트를 돌리며 겪은 일')]),
    dict(k='ch1.made', ch='1장', t='만들었다', done='유명한 글 사이트를 닮은 내 사이트가 내 PC에 떴습니다.',
         say='올려 줘', why='세션은 묻지 않고 바로 올리기 때문에 보통 「만들었다」와 「올렸다」가 함께 열립니다. 아직 주소를 못 받았으면 이 한 줄을 말합니다.',
         samples=[('/money/guide/year-end-prep/', '글 한 편이 이렇게 생겼습니다 — 결론 먼저, 출처, 확인일'), ('/guide/', '글이 쌓이면 이런 목록이 됩니다')]),
    dict(k='ch1.uploaded', ch='1장', t='올렸다', done='주소가 생겼습니다. 휴대폰으로 열리고 남에게 보낼 수 있습니다.',
         say='이름을 첫 캠핑으로 바꿔 줘', why='이름·색·글은 세션이 이미 채워 두었습니다. 바꾸고 싶은 것만 한 줄로 말하면 됩니다. 말 한 줄로 세 번 고치면 다음 관문이 열립니다.',
         samples=[('/about/', '소개 쪽 — 누가 무엇을 왜 하는 곳인지'), ('/money/guide/', '주제 하나로 묶인 글 묶음')]),
    dict(k='ch1.changed', ch='1장', t='고쳐 봤다', done='말하는 대로 고치고, 마음에 안 들면 되돌려 봤습니다.',
         say='이걸 요리법 모음으로', why='같은 사이트가 한 줄에 다른 서비스가 됩니다. 처음으로 돌아가려면 「되돌려 줘」. 충분히 해 봤으면 「2장을 진행해 보자」.',
         samples=[('/fridge/', '요리법 모음으로 틀면 — 재료로 고르는 레시피'), ('/contest/', '목록형으로 틀면 — 마감순 공모전')]),
    dict(k='ch2.made', ch='2장', t='가게를 만들었다', done='상품을 둘러보고 주문하는 내 가게가 떴습니다. 결제는 없고 무통장 입금으로 받습니다.',
         say='올려 줘', why='가게도 세션이 묻지 않고 올립니다. 아직 주소를 못 받았으면 이 한 줄을 말합니다.',
         samples=[('/community/', '방문자가 남기는 것을 받는 쪽의 보기 — 글과 댓글'), ('/dev/d1-read-budget/', '받은 것을 쌓아 두는 곳(자료 저장)에서 겪은 일')]),
    dict(k='ch2.uploaded', ch='2장', t='가게를 올렸다', done='가게에 주소가 생겼고, 손님이 남긴 주문이 파는 사람 화면에 쌓입니다.',
         say='찜을 붙여 줘', why='기능을 붙였다 뗐다 해 봅니다. 떼는 것도 한 줄입니다. 예) 상품평을 떼 줘',
         samples=[('/dev/tax-calculator-statute-verification/', '붙인 기능을 어떻게 확인했나 — 실제 기록'), ('/money/tools/gift-tax-calculator-2026/', '기능 하나가 붙은 모습의 보기')]),
    dict(k='ch2.changed', ch='2장', t='붙였다 뗐다 해 봤다', done='가게에 기능을 붙이고 떼어 봤습니다.',
         say='3장을 진행해 보자', why='이제 사람이 없어도 사이트가 돌게 합니다.',
         samples=[('/dev/multi-ai-sessions/', '세션을 역할로 나눠 돌리며 겪은 사고 네 가지'), ('/ailog/', '사이트를 만들어 온 기록')]),
    dict(k='ch3.ops', ch='3장', t='운영팀을 세웠다', done='자동 운영을 한 번 돌려 봤습니다.',
         say='주문 담당을 맡아 줘', why='세션에 자리를 맡기거나 날마다 저절로 돌게 합니다. 예) 날마다 아침 8시에 돌려 줘',
         samples=[('/dev/gift-tax-calculator-statute-verification/', '운영하며 만든 것을 검증한 기록'), ('/issue/', '날마다 갱신되는 쪽의 보기'), ('/dev/', '운영하며 적은 기술 글')]),
]

CSS = ('<style>.hx{max-width:860px}.hx-road{list-style:none;margin:18px 0;padding:0;display:grid;gap:10px}'
       '.hx-road li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:12px;align-items:start;padding:14px 16px;border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff)}'
       '.hx-road .n{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;background:var(--pbg,#f1ecff);color:var(--pri,#6d28d9)}'
       '.hx-road li.on{border-color:var(--pri,#6d28d9)}.hx-road li.on .n{background:var(--pri,#6d28d9);color:#fff}.hx-road li.now{box-shadow:0 0 0 3px color-mix(in srgb,var(--pri,#6d28d9) 22%,transparent)}'
       '.hx-road b{font-size:16px}.hx-road small{color:var(--mu,#64748b);margin-left:6px}.hx-road p{margin:4px 0 0;color:var(--mu,#64748b);font-size:14px}.hx-road time{font-size:12.5px;color:var(--pri,#6d28d9);margin-left:8px}'
       '.hx-tok{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.hx-tok input{flex:1;min-width:220px;padding:12px 14px;border:1px solid var(--bd,#d7d5ea);border-radius:10px;background:var(--bg,#fff);color:var(--tx,#1e1b4b);font-size:17px;letter-spacing:.06em;text-transform:uppercase}'
       '.hx-tok button,.hx-btn{padding:12px 18px;border:0;border-radius:10px;background:var(--pri,#6d28d9);color:#fff;font-weight:700;font-size:15px;cursor:pointer;text-decoration:none;display:inline-block}'
       '.hx-tok button.g{background:transparent;color:var(--mu,#64748b);border:1px solid var(--bd,#d7d5ea);font-weight:500}.hx-msg{min-height:20px;color:var(--red,#e11d48);font-size:14px}'
       '.hx-now{border:1px solid var(--bd,#e5e7eb);border-radius:16px;overflow:hidden;background:var(--card,#fff);margin:16px 0}'
       '.hx-now .hxt{padding:18px 20px;background:linear-gradient(135deg,color-mix(in srgb,var(--pri,#6d28d9) 16%,var(--card,#fff)),var(--card,#fff))}.hx-now .hxt small{color:var(--mu,#64748b)}.hx-now .hxt b{display:block;font-size:24px;margin-top:2px}'
       '.hx-now .hxm{padding:16px 20px;border-top:1px solid var(--bd,#e5e7eb)}.hx-say{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0}'
       '.hx-say code{flex:1;min-width:200px;padding:11px 14px;border-radius:10px;background:var(--pbg,#f1ecff);color:var(--tx,#1e1b4b);font-size:16px}'
       '.hx-say button{padding:10px 14px;border:1px solid var(--bd,#d7d5ea);border-radius:10px;background:transparent;color:var(--pri,#6d28d9);cursor:pointer;font-weight:600}'
       '.hx-smp{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:8px}.hx-smp a{display:block;padding:11px 14px;border:1px solid var(--bd,#e5e7eb);border-radius:10px;text-decoration:none;color:inherit}.hx-smp a:hover{border-color:var(--pri,#6d28d9)}'
       '.hx-bar{height:8px;border-radius:99px;background:var(--pbg,#f1ecff);overflow:hidden;margin:10px 0}.hx-bar i{display:block;height:100%;width:0;background:var(--pri,#6d28d9);transition:width .3s}</style>')

JS = r"""(function(){var API=window.__HX_API,S=window.__HX_STEPS,K="hx_token";
function q(s){return document.querySelector(s)}function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function get(){try{return localStorage.getItem(K)||""}catch(e){return""}}function put(t){try{t?localStorage.setItem(K,t):localStorage.removeItem(K)}catch(e){}}
function day(ts){var d=new Date(ts);return (d.getMonth()+1)+"/"+d.getDate()}
function norm(v){v=String(v||"").toUpperCase().replace(/[^A-Z0-9]/g,"");if(v.indexOf("HX")===0)v=v.slice(2);return v.length===12?"HX-"+v.slice(0,4)+"-"+v.slice(4,8)+"-"+v.slice(8):""}
function paint(steps){var have={};(steps||[]).forEach(function(x){have[x.step]=x});var last=-1;S.forEach(function(s,i){if(have[s.k])last=i});
 document.querySelectorAll(".hx-road li").forEach(function(li,i){var s=S[i],h=have[s.k];li.classList.toggle("on",!!h);li.classList.toggle("now",i===last);var t=li.querySelector("time");if(t)t.textContent=h?day(h.ts)+(h.note?" · "+h.note:""):""});
 var n=Object.keys(have).filter(function(k){return S.some(function(s){return s.k===k})}).length,bar=q(".hx-bar i");if(bar)bar.style.width=Math.round(n/S.length*100)+"%";
 var box=q("#hx-now");if(!box)return;if(last<0){box.hidden=true;return}var s=S[last],nx=S[last+1];
 box.hidden=false;box.innerHTML='<div class="hxt"><small>지금 여기 · '+esc(s.ch)+' · 관문 '+n+' / '+S.length+'</small><b>'+esc(s.t)+'</b><p style="margin:6px 0 0">'+esc(s.done)+'</p></div>'
  +'<div class="hxm"><b>다음에 할 말</b><div class="hx-say"><code id="hx-line">'+esc(s.say)+'</code><button type="button" id="hx-copy">복사</button></div><p style="margin:4px 0 0;color:var(--mu,#64748b);font-size:14px">'+esc(s.why)+(nx?' 다음 관문: '+esc(nx.t)+'.':'')+'</p></div>'
  +'<div class="hxm"><b>지금 자리에서 볼 만한 것</b><ul class="hx-smp">'+s.samples.map(function(x){return '<li><a href="'+esc(x[0])+'">'+esc(x[1])+'</a></li>'}).join("")+'</ul></div>';
 var c=q("#hx-copy");if(c)c.onclick=function(){if(navigator.clipboard)navigator.clipboard.writeText(s.say).then(function(){c.textContent="복사했습니다"})}}
function load(t){var m=q(".hx-msg");if(m)m.textContent="";return fetch(API+"/lms/me?token="+encodeURIComponent(t)).then(function(r){return r.json()}).then(function(j){if(!j.ok){if(m)m.textContent=j.error||"불러오지 못했습니다";put("");show(false);return}put(t);show(true,t);paint(j.steps)}).catch(function(){if(m)m.textContent="지금은 불러올 수 없습니다. 잠시 뒤 다시 해 주세요."})}
function show(on,t){var f=q("#hx-form"),o=q("#hx-on");if(f)f.hidden=!!on;if(o){o.hidden=!on;var b=o.querySelector("b");if(b&&t)b.textContent=t}if(!on){var box=q("#hx-now");if(box)box.hidden=true;paint([])}}
var f=q("#hx-form");if(f)f.onsubmit=function(e){e.preventDefault();var t=norm(f.token.value),m=q(".hx-msg");if(!t){if(m)m.textContent="토큰은 HX-ABCD-EFGH-JKMN 처럼 생겼습니다. 하네스가 알려 준 것을 그대로 넣어 주세요.";return}load(t)};
var out=q("#hx-out");if(out)out.onclick=function(){put("");show(false);if(f)f.token.value=""};var rf=q("#hx-ref");if(rf)rf.onclick=function(){var t=get();if(t)load(t)};
var t=get();if(t)load(t)})()"""


def _road(with_time):
    return '<ol class="hx-road">' + ''.join(
        f'<li><span class="n">{i}</span><div><b>{E(s["t"])}</b><small>{E(s["ch"])}</small>' + ('<time></time>' if with_time else '') + f'<p>{E(s["done"])}</p></div></li>'
        for i, s in enumerate(STEPS, 1)) + '</ol>'


def pages(page):
    """build.py 의 page() 를 받아 두 쪽을 만든다. 워커 주소(_gongmo/lms.json)가 없으면 만들지 않는다."""
    f = os.path.join(HERE, 'lms.json')
    if not os.path.exists(f):
        return []
    api = json.load(open(f, encoding='utf-8'))['api']
    data = '<script>window.__HX_API=%s;window.__HX_STEPS=%s;</script>' % (json.dumps(api), json.dumps(STEPS, ensure_ascii=False).replace('</', '<\\/'))
    crumbs = [('루리 줍줍', '/'), ('가난한 박과장의 서비스팀 수업', '/park/')]
    intro = ('<div class="hx"><p class="bc">가난한 박과장의 서비스팀 수업</p><h1>가난한 박과장의 서비스팀 수업 — 한 줄씩 말해서 내 서비스를 만들고 굴리기</h1>'
             '<p class="cat-st">책 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』의 실습 수업입니다. AI 세션에게 한 줄씩 말해서 사이트를 만들고, 올리고, 고치고, 사람이 없어도 돌게 하는 실습입니다. 실습은 내 PC의 하네스 저장소에서 하고, 이 쪽은 지금 어디까지 왔는지와 그 자리에서 볼 만한 것을 보여 줍니다.</p>'
             '<p><a class="hx-btn" href="/park/start/">토큰 넣고 내 진도 보기</a></p>'
             '<h2>관문 여덟 개</h2><p>글 사이트를 만들고 올리고 고친 뒤, 가게를 만들고 올리고 기능을 붙였다 떼고, 운영팀을 세웁니다. 하네스가 관문을 지날 때마다 진도를 보내고, 이 사이트가 그 자리에 맞는 보기를 꺼냅니다.</p>' + _road(False)
             + '<h2>토큰은 이렇게 씁니다</h2><ol><li>하네스를 연 세션에게 「토큰 발급해 줘」라고 말합니다.</li><li>세션이 <code>HX-ABCD-EFGH-JKMN</code> 꼴의 토큰을 알려 줍니다.</li>'
             '<li><a href="/park/start/">내 진도 보기</a>에 그 토큰을 넣습니다.</li><li>관문을 지날 때마다 진도가 채워지고 「다음에 할 말」과 볼 만한 것이 바뀝니다.</li></ol>'
             '<h2>받는 정보</h2><p>토큰(무작위 글자)과 지나온 관문 이름, 만든 종류 같은 짧은 메모만 받습니다. 이메일·이름·내 PC의 경로는 받지 않습니다. 토큰은 이 브라우저에만 저장되고 「토큰 지우기」로 지울 수 있습니다.</p></div>' + CSS)
    start = ('<div class="hx"><p class="bc"><a href="/park/">가난한 박과장의 서비스팀 수업</a> › 내 진도</p><h1>내 진도</h1>'
             '<form class="hx-tok" id="hx-form"><input name="token" placeholder="HX-ABCD-EFGH-JKMN" autocomplete="off" autocapitalize="characters" spellcheck="false" aria-label="하네스 토큰" maxlength="24"><button type="submit">진도 보기</button></form>'
             '<div class="hx-tok" id="hx-on" hidden><span style="align-self:center">토큰 <b></b></span><button type="button" class="g" id="hx-ref">새로 고침</button><button type="button" class="g" id="hx-out">토큰 지우기</button></div>'
             '<p class="hx-msg" role="status"></p><div class="hx-bar"><i></i></div><section class="hx-now" id="hx-now" hidden aria-live="polite"></section>'
             '<h2>지나온 관문</h2>' + _road(True)
             + '<p class="note">토큰이 없으면 하네스를 연 세션에게 「토큰 발급해 줘」라고 말하면 됩니다. <a href="/park/">수업 소개</a></p></div>' + CSS + data + '<script>' + JS + '</script>')
    page('/park/', '가난한 박과장의 서비스팀 수업 — 한 줄씩 말해서 내 서비스를 만들고 굴리기', '책 『가난한 박과장과 퇴근후 나의 서비스팀 관리하기』의 실습 수업. AI 세션에게 한 줄씩 말해 사이트를 만들고 올리고 고치고 운영팀을 세우는 실습 과정. 하네스에서 받은 토큰을 넣으면 내 진도와 그 자리에 맞는 보기가 나옵니다.', intro, crumbs)
    page('/park/start/', '가난한 박과장의 서비스팀 수업 — 내 진도 보기', '하네스에서 받은 토큰을 넣으면 지나온 관문과 다음에 할 말, 지금 자리에서 볼 만한 것이 나옵니다.', start, crumbs + [('내 진도', '/park/start/')], noindex=True)
    return ['/park/']
