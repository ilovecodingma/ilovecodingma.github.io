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
  // 허브 검색: 범위(전체·생활 돈·가이드·개발기타), 결과에 분류·확인일 표시
  var hq = $('.wk-hq'), res = $('.wk-res');
  if (hq && res) {
    var SC = { '': null, money: ['money'], guide: ['guide'], dev: ['dev', 'en', 'review'] }, PH = { '': '예: 에너지바우처, 근로장려금, 퇴직금', money: '예: 에너지바우처, 근로장려금, 퇴직금', guide: '예: ISA, 전입신고, 포트폴리오', dev: '예: 비용, 빌드, 색인' };
    var LB = { money: '생활 돈', guide: '가이드', dev: '개발', en: 'English', review: '평론' }, scope = '';
    var idx = null, load = function () { return idx ? Promise.resolve(idx) : fetch('/assets/wiki/index.json').then(function (r) { return r.json(); }).then(function (d) { idx = d; return d; }); };
    var run = function () {
      var v = hq.value.trim().toLowerCase(); res.textContent = ''; if (!v) return;
      load().then(function (d) {
        var tk = v.split(/\s+/), ok = SC[scope];
        var r = d.filter(function (a) { if (ok && ok.indexOf(a.g) < 0) return false; var h = (a.t + ' ' + a.d).toLowerCase(); return tk.every(function (t) { return h.indexOf(t) >= 0; }); }).slice(0, 8);
        if (!r.length) { var p = document.createElement('p'); p.textContent = '일치하는 글이 없어요. 범위를 「전체」로 바꿔 보세요.'; res.appendChild(p); return; }
        r.forEach(function (a) {
          var x = document.createElement('a'); x.href = a.u;
          var t = document.createElement('b'); t.textContent = a.t; x.appendChild(t);
          var s = document.createElement('small'); s.textContent = (LB[a.g] || '') + (a.dt ? ' · 확인일 ' + a.dt : '') + (a.d ? ' — ' + a.d : ''); x.appendChild(s); res.appendChild(x);
        });
      });
    };
    hq.addEventListener('focus', load); hq.addEventListener('input', run);
    var sc = $('.wk-sc');
    if (sc) sc.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; $$('button', sc).forEach(function (x) { x.classList.toggle('on', x === b); }); scope = b.getAttribute('data-s'); hq.placeholder = PH[scope]; run(); });
  }
  // 긴 목록은 12개만 먼저 보이고 더 보기
  $$('.wk-card .wk-list').forEach(function (ul) {
    var li = $$('li', ul); if (li.length <= 12) return;
    li.slice(12).forEach(function (x) { x.hidden = true; });
    var b = document.createElement('button'); b.type = 'button'; b.className = 'wk-more'; b.textContent = '더 보기 (' + (li.length - 12) + '편)';
    b.onclick = function () { li.forEach(function (x) { x.hidden = false; }); b.remove(); };
    ul.parentNode.appendChild(b);
  });
})();
