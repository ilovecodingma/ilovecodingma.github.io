(function(){var $=function(i){return document.getElementById(i)};
function D(s){var p=s.split('-');return Date.UTC(+p[0],+p[1]-1,+p[2])}
function addY(s,y){var p=s.split('-');return Date.UTC(+p[0]+y,+p[1]-1,+p[2])}
function won(n){return Math.round(n).toLocaleString('ko-KR')+'원'}
$('go').onclick=function(){
 var amt=(parseFloat($('amt').value)||0)*10000,free=(parseFloat($('free').value)||0)*10000,r=(parseFloat($('rate').value)||0)/100;
 if(!$('d0').value||!$('d1').value||amt<=0){$('res').innerHTML='<p>금액과 날짜를 입력하세요.</p>';return}
 var d0=D($('d0').value),d1=D($('d1').value),end=addY($('d0').value,+$('yr').value),DAY=86400000;
 if(d1<d0){$('res').innerHTML='<p>상환일이 실행일보다 빠릅니다.</p>';return}
 var total=Math.round((end-d0)/DAY),rem=Math.max(0,Math.round((end-d1)/DAY));
 var base=Math.max(0,amt-free),fee=base*r*rem/total;
 $('res').innerHTML='<table><tr><td>부과 기간 전체</td><td>'+total+'일</td></tr><tr><td>잔존일수</td><td>'+rem+'일</td></tr><tr><td>수수료 대상 금액</td><td>'+won(base)+'</td></tr>'+
 '<tr><td>예상 수수료</td><td class="big">'+won(fee)+'</td></tr></table>'+(rem===0?'<p>부과 기간이 지나 수수료가 없습니다.</p>':'')+
 '<p class="note">금융사별 일수 계산·면제 조건에 따라 실제 청구액과 다를 수 있습니다.</p>';
};})();
