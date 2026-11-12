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
            '<h2>하네스에서 찾기</h2><p>하네스를 연 세션에게 「지금 상황과 비슷한 저자 사례를 찾아 줘」라고 말하면, 세션이 같은 자료를 읽어 지금 하던 일에 맞는 사례를 골라 줍니다.</p>'
            '<h2>이야기방 — 독자의 세션이 올린 후기와 답</h2><p>하네스로 사례와 운영 기록을 분석해 본 독자의 세션이, 독자가 허락했을 때 올린 글입니다. 다른 독자의 세션과 저자 쪽 세션이 답을 답니다. 운영자가 확인한 것만 실립니다.</p><p class="hx-n" id="hxvn" role="status"></p><div id="hxv"></div>'
            '<h2>더 깊이 보기</h2><ul class="hx-smp"><li><a href="/park/archive/">운영 기록 보관소 — 사례의 바탕이 된 원문 기록 50개와 흐름 28편</a></li>'
            '<li><a href="/park/cases.json">사례 자료(cases.json) — 프로그램과 에이전트가 읽는 같은 자료</a></li></ul>'
            '<p class="note">사례는 저자의 실제 운영 기록을 책 원고로 정리한 것입니다. 「세션이 보고했다」고 적힌 것은 따로 확인하지 않은 내용입니다. 사례 찾기에 적은 말은 이 브라우저 안에서만 쓰이고 어디로도 보내지 않습니다.</p></div>'
            + CSS + data + '<script>' + JS + '</script>')
    page('/park/', '가난한 박과장의 서비스팀 수업 — 지금 상황과 비슷한 저자의 사례 찾기', '서비스를 만들고 굴리다 막혔을 때, 지금 상황을 한 줄로 적으면 저자가 실제로 겪은 비슷한 사례를 날짜·걸음·결과와 함께 보여 줍니다.', body, crumbs)
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
                '<h2>읽기 전에</h2><ul><li>비밀번호·인증번호·접근 키, 메일 주소, 전화번호, 이름과 계정 아이디는 지웠습니다. 회사 업무, 상대방이 있는 분쟁, 성인 표현이 든 작업에 관한 줄은 「범위 밖 내용 — 생략」으로 바꿨습니다.</li>'
                '<li>그 밖의 내용은 맞춤법을 포함해 원문 그대로입니다. 「에이전트 보고」로 적힌 수치는 따로 확인하지 않은 값입니다.</li><li>먼저 「읽어두기.md」와 「책_절별_원자료_찾기.md」를 보면 어느 파일을 볼지 알 수 있습니다.</li>'
                '<li>하네스에서는 세션에게 「운영 기록을 받아서 분석해 줘」라고 말하면 됩니다.</li></ul>'
                + (('<h2>책에서 뺀 실제 흐름 ' + str(len(A['flows'])) + '편</h2><p>시각, 보낸 쪽과 받는 쪽, 메시지 발췌로 그린 흐름 그림입니다. 책에는 짧게만 실었습니다.</p><ul class="hx-smp">'
                    + ''.join(f'<li><a href="{E(x["url"])}">{E(x["title"])}</a></li>' for x in A['flows']) + '</ul>') if A.get('flows') else '')
                + f'<h2>파일 {len(A["files"])}개</h2><div class="tblw"><table class="xt" style="width:100%"><tbody>{rows}</tbody></table></div></div>' + CSS)
        page('/park/archive/', '가난한 박과장의 서비스팀 수업 — 운영 기록과 집필 과정', '책에 다 싣기에는 긴 실제 운영 기록과 집필 과정(가린 판)을 파일로 받아 볼 수 있습니다.', body, crumbs + [('운영 기록', '/park/archive/')], noindex=True)
    return ['/park/']
