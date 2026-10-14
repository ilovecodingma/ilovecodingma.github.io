(function(){var $=function(i){return document.getElementById(i)};
function P(s){var p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2])}
function won(n){return Math.round(n).toLocaleString('ko-KR')+'원'}
function fmt(d){return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)}
$('go').onclick=function(){
 if(!$('hd').value){$('res').innerHTML='<p>입사일을 입력하세요.</p>';return}
 var h=P($('hd').value),t=$('td').value?P($('td').value):new Date();t=new Date(t.getFullYear(),t.getMonth(),t.getDate());
 if(t<h){$('res').innerHTML='<p>기준일이 입사일보다 빠릅니다.</p>';return}
 var yrs=t.getFullYear()-h.getFullYear();var ann=new Date(h.getFullYear()+yrs,h.getMonth(),h.getDate());if(ann>t)yrs--;
 var months=(t.getFullYear()-h.getFullYear())*12+t.getMonth()-h.getMonth();if(t.getDate()<h.getDate())months--;
 var out='',cur=0,used=parseFloat($('used').value)||0,att=$('att').value==='1';
 if(yrs<1){cur=Math.min(11,months);out='<tr><td>근속</td><td>1년 미만 ('+months+'개월)</td></tr><tr><td>누적 발생 연차</td><td><b>'+cur+'일</b> (개근 가정)</td></tr>'}
 else{cur=att?Math.min(25,15+Math.floor((yrs-1)/2)):11;
  var nx=new Date(h.getFullYear()+yrs+1,h.getMonth(),h.getDate());
  out='<tr><td>근속</td><td>만 '+yrs+'년</td></tr><tr><td>최근 기념일('+fmt(new Date(h.getFullYear()+yrs,h.getMonth(),h.getDate()))+') 발생 연차</td><td><b>'+cur+'일</b>'+(att?'':' (출근율 80% 미만: 개근한 달 수만큼, 최대 11일로 가정)')+'</td></tr><tr><td>다음 발생일</td><td>'+fmt(nx)+'</td></tr>'}
 var rem=Math.max(0,cur-used);out+='<tr><td>사용</td><td>'+used+'일</td></tr><tr><td>잔여 연차</td><td class="big">'+rem+'일</td></tr>';
 var pay=parseFloat($('pay').value)||0;
 if(pay>0){var day=pay/209*8;out+='<tr><td>1일 통상임금(추정)</td><td>'+won(day)+'</td></tr><tr><td>잔여 연차 수당(미사용 시)</td><td><b>'+won(day*rem)+'</b></td></tr>'}
 $('res').innerHTML='<table>'+out+'</table><p class="note">발생 연차는 입사일 기준이며 소멸 시점·이월 여부는 회사 규정과 사용 촉진 제도 이행 여부에 따라 달라질 수 있습니다.</p>';
};})();
