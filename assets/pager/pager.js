// 스크롤 줄이기 (2026-10-23 사용자 「스크롤 너무 많다 → 네비게이션·스와이프·3D 넘김」)
//  ① 긴 본문: <h2> 구간마다 한 장, 좌우로 밀면(또는 ←→ 키·탭·아래 버튼) 3D 회전하며 넘어간다
//  ② 긴 목록: 10개씩 번호 페이지
//  JS 가 없거나 주소에 ?all=1 이 있으면 전부 그대로 보인다(검색 노출·인쇄 영향 없음). 주소는 바꾸지 않는다.
(function () {
  if (/[?&]all=1/.test(location.search)) return;
  var main = document.querySelector('main');
  if (!main || main.hasAttribute('data-nopager')) return;
  var p = location.pathname;
  if (!/^\/(fridge|apply|contest|event|news|game|ailog|money\/guide)\/$/.test(p)) return;   // 주제 메인 화면만
  var h = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  var clean = function (t) { return (t || '').replace(/\s+/g, ' ').trim(); };
  var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ② 목록 페이지 나누기 (필터 칩이 붙은 data-filter 목록은 fold.js 에 맡긴다)
  [].forEach.call(main.querySelectorAll('ul,ol'), function (L) {
    if (L.closest('nav,.tb,.th-sw,.hx-nav,details:not([open]),.fold-chips') || L.hasAttribute('data-filter') || L.hasAttribute('data-nopage')) return;
    var kids = [].filter.call(L.children, function (k) { return k.tagName === 'LI'; });
    var per = +L.getAttribute('data-fold') || 10;
    if (per < 6) per = 10;
    if (kids.length < per + 4) return;
    L.removeAttribute('data-fold');
    var pages = Math.ceil(kids.length / per), cur = 0, nav = h('nav', 'pg-nav');
    nav.setAttribute('aria-label', '목록 페이지');
    var paint = function () {
      kids.forEach(function (k, i) { k.hidden = Math.floor(i / per) !== cur; });
      nav.textContent = '';
      var b = function (label, to, dis, on) {
        var x = h('button', 'pg-b' + (on ? ' on' : ''), label); x.type = 'button'; x.disabled = !!dis;
        x.onclick = function () { cur = to; paint(); var r = L.getBoundingClientRect(); if (r.top < 0) window.scrollTo({ top: window.scrollY + r.top - 70 }); };
        nav.appendChild(x);
      };
      b('‹', cur - 1, cur === 0);
      var lo = Math.max(0, Math.min(cur - 2, pages - 5)), hi = Math.min(pages, lo + 5);
      if (lo > 0) { b('1', 0); if (lo > 1) nav.appendChild(h('span', 'pg-dots', '…')); }
      for (var i = lo; i < hi; i++) b(String(i + 1), i, false, i === cur);
      if (hi < pages) { if (hi < pages - 1) nav.appendChild(h('span', 'pg-dots', '…')); b(String(pages), pages - 1); }
      b('›', cur + 1, cur === pages - 1);
    };
    L.parentNode.insertBefore(nav, L.nextSibling); paint();
    L._pgReveal = function (el) { var t = el; while (t && t.parentNode !== L) t = t.parentNode; var i = kids.indexOf(t); if (i < 0) return; cur = Math.floor(i / per); paint(); };
  });

  // ① 본문 한 장씩
  var title = function (el) { var e = el.tagName === 'H2' ? el : el.querySelector(':scope > h2, :scope > div > h2, :scope > summary'); return e ? clean(e.textContent) : ''; };
  var panels = [], curP = null;
  [].slice.call(main.children).forEach(function (el) {
    var t = title(el);
    if (el.tagName === 'H2' || (t && /^(SECTION|DETAILS|DIV)$/.test(el.tagName) && el.querySelector(':scope > h2'))) { curP = { t: t, els: [el] }; panels.push(curP); }
    else if (curP) curP.els.push(el);
  });
  panels = panels.filter(function (x) { return x.t; });
  if (panels.length < 3 || main.scrollHeight < window.innerHeight * 1.8) return;

  var stage = h('div', 'pg-stage'), bar = h('nav', 'pg-bar'), wrap = [], idx = 0, busy = false;
  bar.setAttribute('aria-label', '이 화면 구간');
  var prevB = h('button', 'pg-arw', '‹'), nextB = h('button', 'pg-arw', '›'), lab = h('b', 'pg-lab'), dots = h('span', 'pg-dots2');
  prevB.type = nextB.type = 'button'; prevB.setAttribute('aria-label', '이전'); nextB.setAttribute('aria-label', '다음');
  prevB.onclick = function () { show(idx - 1, true); }; nextB.onclick = function () { show(idx + 1, true); };
  bar.appendChild(prevB); var mid = h('span', 'pg-mid'); mid.appendChild(lab); mid.appendChild(dots); bar.appendChild(mid); bar.appendChild(nextB);
  panels[0].els[0].parentNode.insertBefore(stage, panels[0].els[0]);
  panels.forEach(function (x, i) {
    var d = h('div', 'pg-panel'); d.id = 'pg' + i; stage.appendChild(d);
    x.els.forEach(function (e) { d.appendChild(e); }); wrap.push(d);
    var dt = h('button', 'pg-dot'); dt.type = 'button'; dt.setAttribute('aria-label', x.t); dt.onclick = function () { show(i, true); }; dots.appendChild(dt); x.tab = dt;
  });
  stage.parentNode.insertBefore(bar, stage);

  function paintTabs(i) {
    panels.forEach(function (x, j) { x.tab.classList.toggle('on', j === i); });
    lab.textContent = panels[i].t.slice(0, 18); prevB.disabled = i === 0; nextB.disabled = i === panels.length - 1;
  }
  function show(i, top, instant) {
    if (i < 0 || i >= wrap.length || i === idx && !instant) return;
    var from = wrap[idx], to = wrap[i], dir = i > idx ? 1 : -1; idx = i; paintTabs(i);
    var settle = function () { wrap.forEach(function (d, j) { d.hidden = j !== i; }); busy = false; };
    if (top) { var r = bar.getBoundingClientRect(); if (r.top < 0) window.scrollTo({ top: window.scrollY + r.top - 4 }); }
    if (calm || instant || !from.animate || from === to) { settle(); return; }
    busy = true;
    var out = from.animate([{ transform: 'rotateY(0) translateX(0)', opacity: 1 }, { transform: 'rotateY(' + (-38 * dir) + 'deg) translateX(' + (-26 * dir) + '%)', opacity: 0 }], { duration: 170, easing: 'ease-in' });
    out.onfinish = function () {
      from.hidden = true; to.hidden = false;
      var inn = to.animate([{ transform: 'rotateY(' + (38 * dir) + 'deg) translateX(' + (26 * dir) + '%)', opacity: 0 }, { transform: 'rotateY(0) translateX(0)', opacity: 1 }], { duration: 230, easing: 'ease-out' });
      inn.onfinish = settle; inn.oncancel = settle;
    };
    out.oncancel = settle;
  }
  wrap.forEach(function (d) { d.hidden = true; }); wrap[0].hidden = false; paintTabs(0);

  // 스와이프(가로로 충분히, 세로보다 확실히 클 때만). 가로 스크롤 영역·입력칸에서 시작한 건 무시
  var sx = 0, sy = 0, ok = false;
  var scrollsX = function (el) { for (; el && el !== stage; el = el.parentNode) { if (el.nodeType === 1 && /^(INPUT|TEXTAREA|SELECT|CANVAS|IFRAME)$/.test(el.tagName)) return true; if (el.nodeType === 1 && el.scrollWidth > el.clientWidth + 4 && /(auto|scroll)/.test(getComputedStyle(el).overflowX)) return true; } return false; };
  stage.addEventListener('touchstart', function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; ok = e.touches.length === 1 && !scrollsX(e.target); }, { passive: true });
  stage.addEventListener('touchend', function (e) {
    if (!ok || busy) return; var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.8) { show(idx + (dx < 0 ? 1 : -1), true);  }
  }, { passive: true });
  document.addEventListener('keydown', function (e) {
    if (e.target.closest && e.target.closest('input,textarea,select,[contenteditable]') || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === 'ArrowRight') show(idx + 1, true); else if (e.key === 'ArrowLeft') show(idx - 1, true);
  });

  // #앵커가 가리키는 곳이 숨은 구간·목록 안이면 열어 준다
  var go = function () {
    var id = decodeURIComponent((location.hash || '').slice(1)); if (!id) return; var el = document.getElementById(id); if (!el) return;
    var pn = el.closest('.pg-panel'); if (pn) show(wrap.indexOf(pn), false, true);
    [].forEach.call(main.querySelectorAll('ul,ol'), function (L) { if (L._pgReveal && L.contains(el)) L._pgReveal(el); });
    setTimeout(function () { el.scrollIntoView({ block: 'center' }); }, 30);
  };
  window.addEventListener('hashchange', go);
  document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href^="#"]'); if (a) setTimeout(go, 0); });
  go();
})();
