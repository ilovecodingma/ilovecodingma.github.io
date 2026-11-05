/* 정적 화면의 마감일 표시 보정 (2026-11-05 품질 지시서 P0-1).
   화면은 빌드할 때 한 번 만들어지므로, 자정이 지나고 다음 빌드 전까지는 「D-DAY」「D-1」이 하루씩 어긋난다(실제 사례: 11/5에 11/4 마감이 D-DAY로 보임).
   <html data-built="YYYY-MM-DD">(빌드한 날, 한국 시간)와 오늘(한국 시간)의 차이만큼 D-day 글자를 다시 계산하고, 지난 항목은 「마감」으로 바꾼 뒤 흐리게 표시한다. */
(function () {
  var b = document.documentElement.getAttribute('data-built'); if (!b) return;
  var now = new Date(Date.now() + 9 * 3600e3);   // UTC 필드로 읽으면 한국 시간
  var today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  var p = b.split('-'), built = Date.UTC(+p[0], p[1] - 1, +p[2]);
  var delta = Math.round((today - built) / 864e5);
  if (!(delta > 0) || delta > 90) return;
  var root = document.querySelector('main') || document.body, RX = /D-DAY|D-(\d{1,3})(?!\d)/g;
  function fix() {
    var tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), L = [], n, changed = 0;
    while ((n = tw.nextNode())) {
      var t = n.nodeValue;
      if (t.length > 28 || (t.indexOf('D-') < 0 && t.indexOf('오늘') < 0)) continue;
      var pe = n.parentElement;
      if (!pe || pe.closest('script,style,h1,h2,h3,.cat-st,.dd-note,[data-dd-fixed]')) continue;
      L.push(n);
    }
    L.forEach(function (n) {
      var t = n.nodeValue, over = false;
      var t2 = t.replace(RX, function (m, d) { var left = (m === 'D-DAY' ? 0 : +d) - delta; if (left < 0) { over = true; return '마감'; } return left === 0 ? 'D-DAY' : 'D-' + left; });
      if (/^\s*오늘( 마감)?\s*$/.test(t)) { t2 = '마감'; over = true; }
      if (t2 !== t) {
        n.nodeValue = t2; changed++; n.parentElement.setAttribute('data-dd-fixed', '1');
        if (over) { var row = n.parentElement.closest('li,tr,.card'); if (row) row.classList.add('dd-over'); }
      }
    });
    return changed;
  }
  if (fix() && !root.querySelector('.dd-note')) {
    var note = document.createElement('p'); note.className = 'dd-note';
    note.textContent = '이 화면은 ' + (+p[1]) + '/' + (+p[2]) + '에 만든 화면이에요. 마감까지 남은 날은 오늘(' + (now.getUTCMonth() + 1) + '/' + now.getUTCDate() + ', 한국 시간) 기준으로 다시 계산했고, 이미 지난 항목은 「마감」으로 표시했어요.';
    var h = root.querySelector('h1'); if (h && h.parentNode) h.parentNode.insertBefore(note, h.nextSibling); else root.insertBefore(note, root.firstChild);
  }
})();
