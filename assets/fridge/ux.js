// 레시피 화면 UX 보조 (2026-10-23 화면 개선 6·7번): 재료를 고르면 하단에 「선택한 재료 N개 · 추천받기」 고정 막대
// fridge.js 가 만든 DOM 을 읽기만 한다(내부 상태를 건드리지 않음). 챗봇 아이콘과 겹치지 않게 오른쪽을 비운다.
(function () {
  var ROOT = document.getElementById('fridge'); if (!ROOT) return;
  var bar = null, go = null, n = null;
  var ensure = function () {
    if (bar) return true;
    go = ROOT.querySelector('.fr-go'); n = ROOT.querySelector('.fr-n'); if (!go || !n) return false;
    bar = document.createElement('div'); bar.className = 'fr-bar'; bar.hidden = true; bar.setAttribute('role', 'region'); bar.setAttribute('aria-label', '추천 실행');
    bar.innerHTML = '<span>선택한 재료 <b>0</b>개</span><button type="button">추천받기</button>';
    bar.querySelector('button').onclick = function () { go.click(); };
    document.body.appendChild(bar); return true;
  };
  var count = function () { var m = /(\d+)\s*개/.exec((n && n.textContent) || ''); return m ? +m[1] : 0; };
  var visible = function (el) { var r = el.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; };
  var update = function () {
    if (!ensure()) return;
    var c = count(), pane = document.getElementById('fridge');
    var show = c > 0 && pane && !pane.hidden && !visible(go);
    bar.querySelector('b').textContent = c; bar.hidden = !show;
  };
  var mo = new MutationObserver(update); mo.observe(ROOT, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['hidden', 'class'] });
  addEventListener('scroll', update, { passive: true }); addEventListener('resize', update);
  setTimeout(update, 600);
})();
