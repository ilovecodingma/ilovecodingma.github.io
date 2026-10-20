// 표 복사: 이 페이지의 표를 탭으로 나눈 글자로 복사(엑셀·문서에 붙여넣기). 서버로 보내지 않아요.
(function () {
  var b = document.querySelector('.cite-cp'); if (!b) return;
  b.addEventListener('click', function () {
    var out = [];
    document.querySelectorAll('.tblw table').forEach(function (t) {
      var h = t.closest('.tblw').previousElementSibling; if (h && /^H[23]$/.test(h.tagName)) out.push(h.textContent.trim());
      t.querySelectorAll('tr').forEach(function (r) { out.push([].map.call(r.cells, function (c) { return c.textContent.replace(/\s+/g, ' ').trim(); }).join('\t')); });
      out.push('');
    });
    var box = document.querySelector('.cite-box'), ps = box.querySelectorAll('p');
    out.push([].map.call(ps, function (p) { return p.textContent; }).join('\n'));
    var txt = out.join('\n'), ok = function () { b.textContent = '✅ 복사됨'; setTimeout(function () { b.textContent = '📋 표 복사하기 (엑셀·문서에 붙여넣기)'; }, 1800); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(ok);
    else { var ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); ok(); } catch (e) {} ta.remove(); }
  });
})();
