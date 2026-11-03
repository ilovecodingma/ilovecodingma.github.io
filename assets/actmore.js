// 상세 상단 버튼: 주 행동(접수·공고) + 찜만 보이고 나머지는 「더보기」 (2026-11-03). JS가 없으면 모두 보인다.
(function () {
  var row = document.querySelector('.act-row'); if (!row) return;
  var b = document.createElement('button'); b.type = 'button'; b.className = 'am-more'; b.setAttribute('aria-expanded', 'false'); b.textContent = '더보기 ▾';
  b.addEventListener('click', function () { var o = row.classList.toggle('open'); b.setAttribute('aria-expanded', o ? 'true' : 'false'); b.textContent = o ? '접기 ▴' : '더보기 ▾'; });
  row.classList.add('js'); row.appendChild(b);
})();
