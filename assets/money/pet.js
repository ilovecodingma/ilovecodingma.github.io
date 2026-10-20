// 반려견 한 달 비용 계산기 (2026-10-20) — 금액은 직접 넣어요. 이 브라우저에만 저장하고(localStorage) 서버로 보내지 않아요.
(function () {
  var R = document.getElementById('pet'); if (!R) return;
  var KEY = 'jupjup_pet_cost_v1';
  var rows = [].slice.call(R.querySelectorAll('tbody tr'));
  var $ = function (s) { return R.querySelector(s); };
  var f = function (v) { return Math.round(v).toLocaleString('ko-KR'); };
  var saved = {}; try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
  rows.forEach(function (tr, i) {
    var a = tr.querySelector('input'), p = tr.querySelector('select');
    if (saved[i]) { a.value = saved[i][0] || ''; p.value = saved[i][1] || '1'; }
  });
  function calc() {
    var tot = 0, items = [], st = {};
    rows.forEach(function (tr, i) {
      var a = parseFloat((tr.querySelector('input').value || '').replace(/,/g, '')), p = +tr.querySelector('select').value;
      st[i] = [tr.querySelector('input').value, tr.querySelector('select').value];
      if (isFinite(a) && a > 0) { var m = a / p; tot += m; items.push([tr.cells[0].textContent.trim(), m]); tr.querySelector('.pet-m').textContent = f(m) + '원'; } else tr.querySelector('.pet-m').textContent = '';
    });
    try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {}
    var out = $('.pet-out');
    if (!items.length) { out.innerHTML = '<p class="kwn">쓰는 항목의 금액과 주기를 넣으면 한 달 비용으로 바꿔 줘요.</p>'; return; }
    items.sort(function (x, y) { return y[1] - x[1]; });
    out.innerHTML = '<p>🐶 한 달 평균 <b>' + f(tot) + '원</b> · 1년 <b>' + f(tot * 12) + '원</b></p><p class="kwn">가장 큰 항목: ' + items.slice(0, 3).map(function (x) { return x[0] + ' ' + f(x[1]) + '원(' + Math.round(x[1] / tot * 100) + '%)'; }).join(' · ') + '</p>';
  }
  R.addEventListener('input', calc); R.addEventListener('change', calc); calc();
  var b = $('.pet-clear'); if (b) b.onclick = function () { rows.forEach(function (tr) { tr.querySelector('input').value = ''; tr.querySelector('select').value = '1'; }); calc(); };
})();
