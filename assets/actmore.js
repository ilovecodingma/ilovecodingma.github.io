// 상세 상단 「더보기」: 버튼은 서버 HTML 에 처음부터 접힌 상태로 있어 로딩 중 배치가 움직이지 않는다.
(function () {
  var row = document.querySelector('.act-row'); if (!row) return;
  var b = row.querySelector('.am-more'); if (!b) return;
  b.addEventListener('click', function () { var o = row.classList.toggle('open'); b.setAttribute('aria-expanded', o ? 'true' : 'false'); b.textContent = o ? '접기 ▴' : '더보기 ▾'; });
})();
