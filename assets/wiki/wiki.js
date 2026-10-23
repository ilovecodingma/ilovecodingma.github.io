// 루리 위키: 사이드바 검색·모바일 목록 토글·오른쪽 목차 현재 위치 표시·허브 검색 (2026-10-23)
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  var tg = $('.wk-toggle'), side = $('.wk-side');
  if (tg && side) tg.onclick = function () { var o = side.classList.toggle('open'); tg.setAttribute('aria-expanded', o); };
  var q = $('.wk-q');
  if (q) q.addEventListener('input', function () {
    var v = q.value.trim().toLowerCase();
    $$('.wk-g').forEach(function (g) {
      var any = false;
      $$('li', g).forEach(function (li) { var m = !v || li.textContent.toLowerCase().indexOf(v) >= 0; li.style.display = m ? '' : 'none'; if (m) any = true; });
      g.style.display = any ? '' : 'none'; if (v && any) g.open = true;
    });
  });
  // 오른쪽 목차: 지금 읽는 소제목 강조
  var links = $$('.wk-toc a');
  if (links.length && 'IntersectionObserver' in window) {
    var map = {}; links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (a) { a.classList.remove('on'); }); var a = map[e.target.id]; if (a) a.classList.add('on'); } });
    }, { rootMargin: '-80px 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var h = document.getElementById(id); if (h) io.observe(h); });
  }
  // 허브 검색
  var hq = $('.wk-hq'), res = $('.wk-res');
  if (hq && res) {
    var idx = null, load = function () { return idx ? Promise.resolve(idx) : fetch('/assets/wiki/index.json').then(function (r) { return r.json(); }).then(function (d) { idx = d; return d; }); };
    hq.addEventListener('focus', load);
    hq.addEventListener('input', function () {
      var v = hq.value.trim().toLowerCase(); if (!v) { res.textContent = ''; return; }
      load().then(function (d) {
        var r = d.filter(function (a) { return (a.t + ' ' + a.d).toLowerCase().indexOf(v) >= 0; }).slice(0, 8);
        res.textContent = '';
        if (!r.length) { var p = document.createElement('p'); p.textContent = '일치하는 글이 없어요.'; res.appendChild(p); return; }
        r.forEach(function (a) { var x = document.createElement('a'); x.href = a.u; x.textContent = a.t; var s = document.createElement('small'); s.textContent = a.d; x.appendChild(s); res.appendChild(x); });
      });
    });
  }
})();
