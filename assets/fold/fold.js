// 긴 목록 줄이기 (2026-10-20 사용자: "스크롤이 너무 길다, 최소화")
//  <ol data-fold="12" data-step="24" data-filter="c">  → 처음 12개만 보이고 「더 보기」로 24개씩, data-c 값별 칩 필터.
//  JS 가 없으면 전부 그대로 보이므로 검색 노출·접근성에는 영향이 없다. 목록 안으로 가는 #링크는 자동으로 펼친다.
(function () {
  var h = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  [].forEach.call(document.querySelectorAll('[data-fold]'), function (L) {
    var n = +L.getAttribute('data-fold') || 10, step = +L.getAttribute('data-step') || 20, fa = L.getAttribute('data-filter');
    var kids = [].slice.call(L.children); if (kids.length <= n + 3) return;
    var shown = n, cur = '', btn = h('button', 'fold-btn'); btn.type = 'button';
    var vis = function () { return kids.filter(function (k) { return !cur || k.getAttribute('data-' + fa) === cur; }); };
    var paint = function () {
      var v = vis(), i = 0;
      kids.forEach(function (k) { var on = v.indexOf(k) >= 0; if (!on) { k.classList.add('fold-h'); return; } k.classList.toggle('fold-h', i++ >= shown); });
      var rest = v.length - shown;
      btn.hidden = v.length <= n; btn.textContent = rest > 0 ? '더 보기 (' + Math.min(step, rest) + '개 더 · 남은 ' + rest + '개) ▼' : '접기 ▲';
    };
    btn.onclick = function () { if (vis().length - shown > 0) shown += step; else { shown = n; L.scrollIntoView({ block: 'start' }); } paint(); };
    L.parentNode.insertBefore(btn, L.nextSibling);
    if (fa) {
      var cnt = {}; kids.forEach(function (k) { var v = k.getAttribute('data-' + fa); if (v) cnt[v] = (cnt[v] || 0) + 1; });
      var keys = Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; });
      if (keys.length > 1) {
        var bar = h('div', 'fold-chips'), chips = [];
        var mk = function (v, label) { var b = h('button', 'fold-chip' + (v === '' ? ' on' : ''), label); b.type = 'button'; b.onclick = function () { cur = v; shown = n; chips.forEach(function (c) { c.classList.toggle('on', c === b); }); paint(); }; chips.push(b); bar.appendChild(b); };
        mk('', '전체 ' + kids.length); keys.forEach(function (k) { mk(k, k + ' ' + cnt[k]); });
        L.parentNode.insertBefore(bar, L);
      }
    }
    L._reveal = function (el) { var t = el; while (t && t.parentNode !== L) t = t.parentNode; if (!t) return false; var i = vis().indexOf(t); if (i < 0) { cur = ''; i = kids.indexOf(t); [].forEach.call(L.parentNode.querySelectorAll('.fold-chip'), function (c, j) { c.classList.toggle('on', j === 0); }); } if (i >= shown) shown = i + 1; paint(); return true; };
    paint();
  });
  var go = function () {
    var id = decodeURIComponent((location.hash || '').slice(1)); if (!id) return; var el = document.getElementById(id); if (!el) return;
    [].forEach.call(document.querySelectorAll('[data-fold]'), function (L) { if (L._reveal && L.contains(el)) L._reveal(el); });
    setTimeout(function () { el.scrollIntoView({ block: 'center' }); }, 30);
  };
  window.addEventListener('hashchange', go); document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href^="#"]'); if (a) setTimeout(go, 0); });
  go();
})();
