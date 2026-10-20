// 루리의 AI교실 — 프롬프트 복사, 체크리스트, 진행 표시. 진행은 이 브라우저(localStorage)에만 저장해요.
(function () {
  var KEY = 'jupjup_class_v1', S = {};
  try { S = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function done(n) { var d = S[n] || {}; var c = 0; for (var k in d) if (d[k]) c++; return c; }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.cl-cp'); if (!b) return;
    var t = b.parentNode.querySelector('pre').textContent;
    var ok = function () { b.textContent = '✅ 복사됨'; setTimeout(function () { b.textContent = '📋 프롬프트 복사'; }, 1600); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(ok, fb); else fb();
    function fb() { var r = document.createRange(); r.selectNodeContents(b.parentNode.querySelector('pre')); var s = getSelection(); s.removeAllRanges(); s.addRange(r); try { document.execCommand('copy'); ok(); } catch (x) {} }
  });
  var W = document.querySelector('[data-cl]');
  if (W) {
    var n = W.getAttribute('data-cl'), boxes = W.querySelectorAll('input[type=checkbox]'), st = W.querySelector('[data-st]');
    var upd = function () { var c = 0; boxes.forEach(function (x) { if (x.checked) c++; }); if (st) st.textContent = '체크 ' + c + ' / ' + boxes.length + (c === boxes.length ? ' · 이번 강의 완료 🎉' : ''); };
    boxes.forEach(function (x) { x.checked = !!(S[n] && S[n][x.getAttribute('data-k')]); x.addEventListener('change', function () { S[n] = S[n] || {}; S[n][x.getAttribute('data-k')] = x.checked; save(); upd(); }); });
    upd();
  }
  var bar = document.querySelector('[data-bar]');
  if (bar) {
    var total = 0, got = 0;
    document.querySelectorAll('[data-idx]').forEach(function (el) { var k = el.getAttribute('data-idx'), c = done(k); if (c) { el.textContent = '· 체크 ' + c + '개'; } });
    for (var k in S) got += done(k);
    total = 10 * 7;
    bar.style.width = Math.min(100, Math.round(got / total * 100)) + '%';
    var al = document.querySelector('[data-all]'); if (al) al.textContent = got ? '내 진행: 체크 ' + got + '개 (이 브라우저에만 저장돼요)' : '체크리스트를 체크하면 진행이 여기에 표시돼요(이 브라우저에만 저장).';
  }
})();
