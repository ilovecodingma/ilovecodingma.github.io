// 코드 블록 복사 버튼 (기술 블로그 글). 서버로 보내는 건 없어요.
(function () {
  document.querySelectorAll('.dev pre').forEach(function (pre) {
    var code = pre.querySelector('code') || pre;
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'dev-cp'; b.textContent = '복사';
    b.style.cssText = 'float:right;margin:-4px -4px 4px 8px;min-height:32px;padding:0 10px;border:1px solid #475569;border-radius:6px;background:#1e293b;color:#e2e8f0;font:inherit;font-size:12px;cursor:pointer';
    b.addEventListener('click', function () {
      var t = code.textContent, ok = function () { b.textContent = '복사됨'; setTimeout(function () { b.textContent = '복사'; }, 1500); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(ok, function () {});
      else { var ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); ok(); } catch (e) {} ta.remove(); }
    });
    pre.insertBefore(b, pre.firstChild);
  });
})();

// 읽기 진행 막대 · 목차 현재 위치 · 허브 글 찾기 (2026-10-26)
(function () {
  var art = document.querySelector('article.dev');
  if (art) {
    var bar = document.createElement('div'); bar.id = 'dev-prog'; document.body.appendChild(bar);
    var links = [].slice.call(document.querySelectorAll('.dev-toc a'));
    var hs = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var tick = function () {
      var r = art.getBoundingClientRect(), tot = r.height - innerHeight;
      bar.style.width = (tot > 0 ? Math.min(100, Math.max(0, -r.top / tot * 100)) : 0) + '%';
      var cur = -1; hs.forEach(function (h, i) { if (h && h.getBoundingClientRect().top < 120) cur = i; });
      links.forEach(function (a, i) { a.classList.toggle('on', i === cur); });
    };
    addEventListener('scroll', tick, { passive: true }); tick();
  }
  var q = document.getElementById('dev-q');
  if (q) {
    var lis = [].slice.call(document.querySelectorAll('.dev-all li')), none = document.createElement('p');
    none.className = 'dev-empty'; none.hidden = true; none.textContent = '맞는 글이 없어요. 다른 낱말로 찾아보세요.';
    var ul = document.querySelector('.dev-all'); if (ul) ul.parentNode.insertBefore(none, ul.nextSibling);
    q.addEventListener('input', function () {
      var v = q.value.trim().toLowerCase(), n = 0;
      lis.forEach(function (li) { var ok = !v || li.textContent.toLowerCase().indexOf(v) > -1; li.hidden = !ok; if (ok) n++; });
      none.hidden = n > 0;
    });
  }
})();
