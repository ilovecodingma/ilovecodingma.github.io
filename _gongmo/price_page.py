"""최저가 찾기 화면 (/price/) — 2026-11-10 사용자 「이름 → 제품명 → 제품 코드 → 풀 스캔 → 가장 싼 것 + 바로가기」.

- 조회는 따로 둔 Worker(_gongmo/worker_price, 주소는 price_api.json)가 한다. 이 파일은 화면만 만든다.
- 새 상품은 다나와 가격비교의 판매처 목록, 중고는 중고나라 검색 결과. 당근·번개장터는 검색 결과로 바로 가는 주소만 준다.
- render() 가 (제목, 설명, 본문) 을 돌려준다. 주소 파일이 없으면 None(빌드는 그대로 간다).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CSS = """<style>
.pf{max-width:820px;margin:0 auto}
.pf button{margin-top:0;width:auto;flex:none}
.pf input{width:auto}
.pf-f{display:flex;gap:8px;margin:14px 0 6px}
.pf-f input{flex:1;min-width:0;height:50px;padding:0 14px;font-size:17px;border:2px solid var(--pri,#2563eb);border-radius:10px;background:transparent;color:inherit}
.pf-f button,.pf-b{height:50px;padding:0 18px;font-size:16px;font-weight:800;border:0;border-radius:10px;background:var(--pri,#2563eb);color:#fff;cursor:pointer;white-space:nowrap}
.pf-b{display:inline-flex;align-items:center;justify-content:center;height:44px;padding:0 14px;font-size:15px;text-decoration:none}
.pf-b.g{background:transparent;color:inherit;border:1px solid rgba(128,128,128,.5)}
.pf-ex{font-size:14px;opacity:.75;margin:0 0 14px}
.pf-ex button{display:inline;background:none;border:0;color:var(--pri,#2563eb);font-size:14px;text-decoration:underline;cursor:pointer;padding:6px 4px}
.pf-st{padding:14px;border:1px dashed rgba(128,128,128,.5);border-radius:10px;font-size:15px;margin:12px 0}
.pf-st.err{border-style:solid;border-color:#dc2626}
.pf h2{font-size:20px;margin:26px 0 10px}
.pf-l{list-style:none;margin:0;padding:0}
.pf-l li{display:flex;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid rgba(128,128,128,.25)}
.pf-l img{width:64px;height:64px;object-fit:contain;border-radius:8px;background:#fff;flex:none}
.pf-l .nm{flex:1;min-width:0}
.pf-l .nm b{display:block;font-size:16px;line-height:1.4;word-break:keep-all}
.pf-l .nm span{font-size:14px;opacity:.75}
.pf-best{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.pf-best div{border:2px solid var(--pri,#2563eb);border-radius:12px;padding:14px}
.pf-best small{display:block;font-size:13px;opacity:.75}
.pf-best strong{display:block;font-size:24px;margin:4px 0}
.pf-best p{margin:0 0 10px;font-size:14px;line-height:1.45;word-break:keep-all}
.pf-l .rk{flex:none;width:22px;text-align:center;font-size:13px;opacity:.6}
.pf-l .pr{flex:none;font-size:16px;white-space:nowrap;font-variant-numeric:tabular-nums}
.pf-l .pf-b{flex:none;height:40px;padding:0 12px;font-size:14px}
.pf-nt{font-size:14px;opacity:.8;line-height:1.6;margin:10px 0}
.pf-lk{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.pf-uq{display:flex;gap:8px;margin:8px 0}
.pf-uq input{flex:1;min-width:0;height:44px;padding:0 12px;font-size:15px;border:1px solid rgba(128,128,128,.5);border-radius:8px;background:transparent;color:inherit}
@media(max-width:560px){.pf-best{grid-template-columns:1fr}.pf-f button{padding:0 14px}.pf-l li{gap:8px}.pf-l .nm b{font-size:15px}.pf-l .pr{font-size:15px}.pf-l img{width:52px;height:52px}}
</style>"""

JS = r"""<script>
(function(){
var API=%s;
var $=function(i){return document.getElementById(i)};
var box=$('pf-out'),inp=$('pf-q');
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function won(n){return n==null?'-':Number(n).toLocaleString('ko-KR')+'원'}
function safe(u){return /^https:\/\/(prod\.danawa\.com|search\.danawa\.com|www\.daangn\.com|web\.joongna\.com|m\.bunjang\.co\.kr)\//.test(u||'')?u:'#'}
function go(u,t,c){return '<a class="pf-b'+(c?' '+c:'')+'" href="'+esc(safe(u))+'" target="_blank" rel="noopener nofollow">'+esc(t)+'</a>'}
function state(t,err){box.innerHTML='<p class="pf-st'+(err?' err':'')+'" role="status">'+esc(t)+'</p>'}
function call(path,q){var u=API+path+'?'+Object.keys(q).filter(function(k){return q[k]}).map(function(k){return k+'='+encodeURIComponent(q[k])}).join('&');
  return fetch(u).then(function(r){return r.json().then(function(d){if(!r.ok||d.error)throw new Error(d.error||'조회에 실패했습니다.');return d})})}
function search(q){
  q=(q||'').trim();if(q.length<2){state('찾을 물건 이름을 두 글자 이상 적어 주세요.',1);return}
  inp.value=q;history.replaceState(null,'','?q='+encodeURIComponent(q));
  state('「'+q+'」 제품을 찾는 중입니다…');
  call('/api/price/search',{q:q}).then(function(d){
    var h='<h2>1. 제품을 고르세요</h2>';
    if(!d.items.length){h+='<p class="pf-st">가격비교에 등록된 제품을 찾지 못했습니다. 이름을 바꿔 보거나 아래에서 중고 장터만 찾아보세요.</p>'}
    else{h+='<p class="pf-nt">찾은 제품 '+d.items.length+'개입니다. 제품을 고르면 판매처와 중고 장터를 한꺼번에 조회합니다.</p><ul class="pf-l">'+d.items.map(function(x){
      return '<li>'+(x.img?'<img src="'+esc(x.img)+'" alt="" loading="lazy" width="64" height="64">':'')+'<div class="nm"><b>'+esc(x.name)+'</b><span>'+(x.price?'최저 '+won(x.price)+' · ':'')+'제품 코드 '+esc(x.pcode)+'</span></div><button class="pf-b" data-pc="'+esc(x.pcode)+'" data-nm="'+esc(x.name)+'">풀 스캔</button></li>'}).join('')+'</ul>'}
    h+='<p class="pf-lk"><button class="pf-b g" data-uq="'+esc(q)+'">「'+esc(q)+'」 중고 장터만 찾기</button></p>';
    box.innerHTML=h;
  }).catch(function(e){state(e.message,1)})}
function scan(pc,uq,nm,q0){
  q0=(pc&&!uq)?(q0||'').trim():'';
  history.replaceState(null,'','?'+[pc?'pcode='+encodeURIComponent(pc):'',uq?'uq='+encodeURIComponent(uq):'',q0?'q='+encodeURIComponent(q0):''].filter(Boolean).join('&'));
  state((nm||uq||'제품')+' — 판매처와 중고 장터를 조회하는 중입니다…');
  call('/api/price/scan',{pcode:pc,uq:uq,q:q0}).then(function(d){
    var p=d.prod,rows=(p&&p.rows)||[],used=d.used||[],h='',wide=false;
    var title=(p&&p.name)||d.uq;
    h+='<h2>2. '+esc(title)+' 조회 결과</h2><div class="pf-best">';
    if(rows.length){var r=rows[0];h+='<div><small>새 상품 최저(배송비 포함)</small><strong>'+won(r.total)+'</strong><p>'+esc(r.mall)+' · 상품 '+won(r.price)+(r.ship==null?' · 배송비는 판매처에서 확인':r.ship?' + 배송비 '+won(r.ship):' · 무료배송')+'</p>'+go(r.link,'판매처로 바로가기')+'</div>'}
    else if(pc){h+='<div><small>새 상품</small><p>판매처 목록을 가져오지 못했습니다.</p>'+go('https://prod.danawa.com/info/?pcode='+pc,'가격비교에서 보기','g')+'</div>'}
    if(used.length){var u=used[0];wide=pc&&d.uqFull&&d.uq!==d.uqFull;h+='<div><small>'+(wide?'비슷한 이름 중고 최저':'중고 최저')+' · '+esc(u.src)+'</small><strong>'+won(u.price)+'</strong><p>'+esc(u.title)+(u.region?' · '+esc(u.region):'')+'</p>'+go(u.link,'글로 바로가기')+'</div>'}
    else{h+='<div><small>중고</small><p>조건에 맞는 중고 글을 찾지 못했습니다. 아래 검색어를 줄여 다시 찾아보세요.</p></div>'}
    h+='</div>';
    if(rows.length){h+='<h2>새 상품 판매처별 가격</h2><ul class="pf-l">'+rows.map(function(r,i){
      return '<li><span class="rk">'+(i+1)+'</span><div class="nm"><b>'+esc(r.mall)+'</b><span>상품 '+won(r.price)+(r.ship==null?' · 배송비 확인 필요':r.ship?' + 배송비 '+won(r.ship):' · 무료배송')+'</span></div><strong class="pr">'+won(r.total)+'</strong>'+go(r.link,'바로가기','g')+'</li>'}).join('')+'</ul>'
      +'<p class="pf-nt">가격비교에 등록된 판매처 '+(p.offers||rows.length)+'곳 가운데 가격이 낮은 '+rows.length+'곳입니다. 카드 할인·쿠폰은 반영하지 않았습니다. '+go(p.page,'전체 판매처 보기','g')+'</p>'}
    h+='<h2>중고 장터 글</h2><div class="pf-uq"><input id="pf-uq" value="'+esc(d.uq)+'" aria-label="중고 검색어"><button class="pf-b g" id="pf-re">이 검색어로 다시</button></div>';
    if(used.length){h+='<ul class="pf-l">'+used.map(function(u,i){
      return '<li><span class="rk">'+(i+1)+'</span><div class="nm"><b>'+esc(u.title)+'</b><span>'+esc(u.src)+(u.region?' · '+esc(u.region):'')+(u.date?' · '+esc(u.date.slice(5))+' 올림':'')+'</span></div><strong class="pr">'+won(u.price)+'</strong>'+go(u.link,'바로가기','g')+'</li>'}).join('')+'</ul>'}
    var dr=d.usedDrop||{},dn=(dr['이름다름']||0)+(dr['구매글']||0)+(dr['가격없음']||0)+(dr['판매끝']||0);
    if(wide&&used.length){h+='<p class="pf-nt">제품 이름 전체로는 맞는 글이 적어 「'+esc(d.uq)+'」(으)로 넓혀 찾았습니다. 다른 모델이 섞일 수 있습니다.</p>'}
    h+='<p class="pf-nt">읽은 글 '+(d.usedSeen||0)+'건 가운데 '+used.length+'건을 싼 순서로 보여 드립니다'+(dn?'(이름이 다른 글 '+(dr['이름다름']||0)+'건, 삽니다 글 '+(dr['구매글']||0)+'건, 가격 없는 글 '+(dr['가격없음']||0)+'건 제외)':'')+'. 중고 글은 부속품·묶음·다른 모델일 수 있으니 글 내용을 꼭 확인하세요.</p>';
    if(d.links){h+='<h2>다른 장터에서 바로 찾기</h2><p class="pf-lk">'+go(d.links['당근'],'당근에서 찾기','g')+go(d.links['번개장터'],'번개장터에서 찾기','g')+go(d.links['중고나라'],'중고나라에서 찾기','g')+'</p><p class="pf-nt">당근·번개장터는 글 목록을 가져오지 않고, 같은 검색어의 검색 결과로 바로 연결합니다.</p>'}
    var er=Object.keys(d.errs||{});if(er.length){h+='<p class="pf-st err">'+esc(er.join('·'))+' 조회에 실패했습니다. 잠시 뒤 다시 시도해 주세요.</p>'}
    h+='<p class="pf-nt">조회 시각 '+new Date(d.at).toLocaleString('ko-KR')+' 기준입니다. 같은 검색은 1시간 동안 같은 결과를 보여 드립니다. 결제 전에 판매처 화면의 최종 금액을 확인하세요.</p>';
    box.innerHTML=h;box.scrollIntoView({block:'start',behavior:'smooth'});
  }).catch(function(e){state(e.message,1)})}
$('pf-form').addEventListener('submit',function(e){e.preventDefault();search(inp.value)});
document.addEventListener('click',function(e){var t=e.target.closest&&e.target.closest('button');if(!t)return;
  if(t.dataset.ex){search(t.dataset.ex)}
  else if(t.dataset.pc){scan(t.dataset.pc,'',t.dataset.nm,inp.value)}
  else if(t.dataset.uq){scan('',t.dataset.uq,t.dataset.uq)}
  else if(t.id==='pf-re'){var s=new URLSearchParams(location.search);scan(s.get('pcode')||'',($('pf-uq').value||'').trim(),'')}});
var s=new URLSearchParams(location.search);
if(s.get('pcode')||s.get('uq')){if(s.get('q'))inp.value=s.get('q');scan(s.get('pcode')||'',s.get('uq')||'','',s.get('q')||'')}else if(s.get('q')){search(s.get('q'))}
})();
</script>"""


def render():
    try:
        api = json.load(open(os.path.join(HERE, 'price_api.json'), encoding='utf-8'))['api']
    except Exception:
        return None
    title = '최저가 찾기 — 새 상품 판매처와 중고 장터를 한 번에'
    desc = '물건 이름을 넣고 제품을 고르면 가격비교에 등록된 판매처별 가격과 중고 장터 글을 한 번에 조회해, 가장 싼 곳과 바로가기 주소를 보여 드립니다.'
    body = (CSS + '<div class="pf"><p class="bc"><a href="/">홈</a> › 최저가 찾기</p><h1>최저가 찾기</h1>'
            '<p class="cat-st">물건 이름을 넣고 제품을 고르면, 새 상품 판매처별 가격과 중고 장터 글을 한 번에 조회해 가장 싼 곳을 찾아 드립니다.</p>'
            '<form class="pf-f" id="pf-form" role="search"><input id="pf-q" type="search" name="q" placeholder="예: 겨울 장갑, 에어프라이어, 무선 청소기" aria-label="찾을 물건 이름" autocomplete="off" maxlength="60" required><button type="submit">찾기</button></form>'
            '<p class="pf-ex">예시 <button type="button" data-ex="겨울 장갑">겨울 장갑</button><button type="button" data-ex="전기장판">전기장판</button><button type="button" data-ex="가습기">가습기</button></p>'
            '<div id="pf-out" aria-live="polite"></div>'
            '<h2>이렇게 찾습니다</h2>'
            '<ol class="pf-nt"><li>물건 이름으로 가격비교에 등록된 제품 목록과 제품 코드를 찾습니다.</li>'
            '<li>제품을 고르면 그 제품 코드로 판매처별 가격과 배송비를 읽어, 배송비를 더한 합계가 낮은 순서로 줄 세웁니다.</li>'
            '<li>같은 이름으로 중고 장터 글을 읽어, 판매가 끝난 글·삽니다 글·이름이 다른 글을 빼고 싼 순서로 보여 드립니다.</li>'
            '<li>가장 싼 새 상품 판매처와 중고 글에는 원래 화면으로 바로 가는 버튼을 붙입니다.</li></ol>'
            '<h2>알아 둘 점</h2>'
            '<ul class="pf-nt"><li>새 상품 가격은 다나와 가격비교에 등록된 판매처 기준입니다. 홈쇼핑 계열 쇼핑몰(GS SHOP, 롯데홈쇼핑, 신세계라이브쇼핑 등)과 오픈마켓이 여기에 들어 있습니다. 가격비교에 등록되지 않은 판매처는 나오지 않습니다.</li>'
            '<li>중고 글 목록은 중고나라 검색 결과입니다. 당근과 번개장터는 같은 검색어의 검색 결과로 바로 가는 버튼을 드립니다.</li>'
            '<li>카드 할인, 쿠폰, 회원 등급 할인은 반영하지 않았습니다. 중고 글은 상태·구성품·거래 방법이 글마다 다릅니다.</li>'
            '<li>이 화면은 가격을 대신 찾아 보여 드릴 뿐, 판매나 거래에 관여하지 않습니다.</li></ul></div>'
            + JS % json.dumps(api))
    return title, desc, body
