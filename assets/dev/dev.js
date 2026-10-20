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
