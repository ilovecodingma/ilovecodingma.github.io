(function(){
var $=function(i){return document.getElementById(i)};
var SALE=[[5000,.006,25],[20000,.005,80],[90000,.004,0],[120000,.005,0],[150000,.006,0],[1e12,.007,0]];
var RENT=[[5000,.005,20],[10000,.004,30],[60000,.003,0],[120000,.004,0],[150000,.005,0],[1e12,.006,0]];
function won(n){return Math.round(n*10000).toLocaleString('ko-KR')+'원'}
function man(n){return Math.round(n).toLocaleString('ko-KR')}
$('kind').onchange=function(){$('rw').hidden=this.value!=='rent';$('l1').textContent=this.value==='sale'?'매매가 (만원)':this.value==='jeonse'?'전세금 (만원)':'보증금 (만원)'};
$('kind').onchange();
$('go').onclick=function(){
 var k=$('kind').value,o=$('obj').value,a=parseFloat($('a').value)||0,m=parseFloat($('m').value)||0,v=parseFloat($('vat').value);
 if(a<=0&&!(k==='rent'&&m>0)){$('res').innerHTML='<p>금액을 입력하세요.</p>';return}
 var amt=a,note='';
 if(k==='rent'){amt=a+m*100;note='환산: 보증금 + 월세×100 = '+man(amt)+'만원';if(amt<5000){amt=a+m*70;note='환산(합계 5천만원 미만이므로 월세×70): '+man(amt)+'만원'}}
 var rate,cap=0,desc;
 if(o==='house'){var T=k==='sale'?SALE:RENT;for(var i=0;i<T.length;i++){if(amt<T[i][0]){rate=T[i][1];cap=T[i][2];break}}desc='주택 상한요율 '+(rate*100).toFixed(1)+'%'+(cap?' (한도 '+cap+'만원)':'')}
 else if(o==='op'){rate=k==='sale'?.005:.004;desc='주거용 오피스텔 '+(rate*100).toFixed(1)+'% 이내'}
 else{rate=.009;desc='협의, 0.9% 이내'}
 var fee=amt*rate,capped=false;if(cap&&fee>cap){fee=cap;capped=true}
 var vat=fee*v,tot=fee+vat;
 $('res').innerHTML='<p class="note">'+(note?note+'<br>':'')+'거래금액 '+man(amt)+'만원 · '+desc+(capped?' · 한도액 적용':'')+'</p>'+
 '<table><tr><td>중개보수 상한</td><td><b>'+won(fee)+'</b></td></tr><tr><td>부가세</td><td>'+won(vat)+'</td></tr>'+
 '<tr><td>합계(최대)</td><td class="big">'+won(tot)+'</td></tr></table><p class="note">상한 금액입니다. 실제 금액은 협의로 더 낮아질 수 있고 지자체 조례에 따라 다를 수 있습니다.</p>';
};})();
