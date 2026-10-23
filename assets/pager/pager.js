// 스크롤 줄이기 (2026-10-23 사용자 「스크롤 너무 많다 → 네비게이션·스와이프·3D 넘김」)
//  ① 긴 본문: <h2> 구간마다 한 장, 좌우로 밀면(또는 ←→ 키·탭·아래 버튼) 3D 회전하며 넘어간다
//  ② 긴 목록: 10개씩 번호 페이지
//  JS 가 없거나 주소에 ?all=1 이 있으면 전부 그대로 보인다(검색 노출·인쇄 영향 없음). 주소는 바꾸지 않는다.
window.addEventListener('load', function () { setTimeout(function () {   // 도구 화면이 JS 로 채워진 뒤 높이를 잰다
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

  // ① 본문 한 쪽 = 한 화면: 빵부스러기·제목(h1)은 위에 두고, 그 아래 블록들을 화면 높이에 맞춰 쪽으로 쪼갠다
  var kids = [].slice.call(main.children), headN = 0;
  while (headN < kids.length && (kids[headN].matches('p.bc, nav, h1') || /^(SCRIPT|STYLE|LINK)$/.test(kids[headN].tagName))) headN++;
  var blocks = kids.slice(headN).filter(function (e) { return !/^(SCRIPT|STYLE|LINK)$/.test(e.tagName) && !e.hidden && e.offsetHeight > 0; });
  if (blocks.length < 3 || main.scrollHeight < window.innerHeight * 1.8) return;
  var h1 = main.querySelector('h1'), h1t = h1 ? clean(h1.textContent) : '';
  var secName = function (el) { var e = el.tagName === 'H2' ? el : (el.querySelector && el.querySelector(':scope > h2, :scope > div > h2, :scope > summary, :scope h2')); return e ? clean(e.textContent) : ''; };

  var stage = h('div', 'pg-stage'), bar = h('nav', 'pg-bar'), wrap = [], idx = 0, busy = false, secOf = [];
  bar.setAttribute('aria-label', '이 화면 쪽');
  var prevB = h('button', 'pg-arw', '‹'), nextB = h('button', 'pg-arw', '›'), lab = h('b', 'pg-lab'), cnt = h('span', 'pg-cnt'), prog = h('i', 'pg-prog');
  prevB.type = nextB.type = 'button'; prevB.setAttribute('aria-label', '이전 쪽'); nextB.setAttribute('aria-label', '다음 쪽');
  prevB.onclick = function () { show(idx - 1, true); }; nextB.onclick = function () { show(idx + 1, true); };
  var mid = h('span', 'pg-mid'); mid.appendChild(lab); mid.appendChild(cnt); bar.appendChild(prevB); bar.appendChild(mid); bar.appendChild(nextB); bar.appendChild(prog);
  blocks[0].parentNode.insertBefore(stage, blocks[0]); stage.parentNode.insertBefore(bar, stage);
  var closeNow = false, avail = Math.max(380, window.innerHeight - 200), sec = h1t, page = h('div', 'pg-panel'), cur = 0, pageSec = sec;
  stage.appendChild(page);
  blocks.forEach(function (k) {
    var sn = secName(k); if (sn) sec = sn;
    var before = page.offsetHeight; page.appendChild(k); cur++;
    if (closeNow) { closeNow = false; page.removeChild(k); wrap.push(page); secOf.push(pageSec); page = h('div', 'pg-panel'); stage.appendChild(page); page.appendChild(k); cur = 1; pageSec = sec; return; }
    if (page.offsetHeight > avail && cur > 1 && before < avail * .5 && page.offsetHeight <= avail * 1.4) { closeNow = true; return; }   // 앞 쪽이 너무 비면 다음 블록을 같이 담는다
    if (page.offsetHeight > avail && cur > 1) {
      page.removeChild(k); wrap.push(page); secOf.push(pageSec);
      page = h('div', 'pg-panel'); stage.appendChild(page); page.appendChild(k); cur = 1; pageSec = sec;
    } else if (cur === 1) pageSec = sec;
  });
  wrap.push(page); secOf.push(pageSec);
  if (wrap.length < 2) { while (stage.firstChild) { while (stage.firstChild.firstChild) stage.parentNode.insertBefore(stage.firstChild.firstChild, stage); stage.removeChild(stage.firstChild); } stage.remove(); bar.remove(); return; }
  wrap.forEach(function (d, i) { d.id = 'pg' + i; d.hidden = i !== 0; });
  wrap.forEach(function (d, i) { if (i < wrap.length - 1) { var nx = h('button', 'pg-next', '다음 쪽 ›'); nx.type = 'button'; nx.onclick = function () { show(i + 1, true); }; d.appendChild(nx); } });
  function paintTabs(i) {
    lab.textContent = secOf[i].slice(0, 20); cnt.textContent = (i + 1) + ' / ' + wrap.length;
    prog.style.width = ((i + 1) / wrap.length * 100) + '%'; prevB.disabled = i === 0; nextB.disabled = i === wrap.length - 1;
  }

  // ── 책 넘기기: 왼쪽 등을 축으로 한 장이 들리며 넘어간다. 손가락을 따라 움직이고, 놓으면 30% 넘었을 때만 넘어간다
  var MAXA = 112, flip = null;
  var ease = function (t) { return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; };
  var tween = function (a0, a1, ms, step, done) {
    var t0 = null; flip.raf = requestAnimationFrame(function f(ts) {
      if (t0 === null) t0 = ts; var k = Math.min(1, (ts - t0) / ms); step(a0 + (a1 - a0) * ease(k));
      if (k < 1) flip.raf = requestAnimationFrame(f); else done();
    });
  };
  var paint = function (p) {   // p: 0(원래 장) → 1(넘어간 장)
    var f = flip, deg = -MAXA * (f.dir > 0 ? p : 1 - p);
    f.leaf.style.transform = 'rotateY(' + deg + 'deg)';
    f.leaf.style.filter = 'brightness(' + (1 - .28 * Math.sin(Math.min(1, Math.abs(deg) / MAXA) * Math.PI)) + ')';
    f.leaf.style.boxShadow = '' + (10 * Math.sin(Math.min(1, Math.abs(deg) / MAXA) * Math.PI)) + 'px 0 30px rgba(0,0,0,' + (.32 * Math.sin(Math.min(1, Math.abs(deg) / MAXA) * Math.PI)) + ')';
    f.under.style.opacity = '' + (.72 + .28 * (f.dir > 0 ? p : 1 - p));
  };
  var begin = function (i) {   // 넘길 준비: 아래에 깔릴 장과 들릴 장을 정한다
    if (flip || i < 0 || i >= wrap.length || i === idx) return false;
    var dir = i > idx ? 1 : -1, from = wrap[idx], to = wrap[i];
    var leaf = dir > 0 ? from : to, under = dir > 0 ? to : from;
    stage.style.minHeight = Math.max(from.offsetHeight, 0) + 'px';
    under.hidden = false; to.hidden = false; from.hidden = false;
    leaf.classList.add('pg-leaf'); under.classList.add('pg-under');
    flip = { dir: dir, i: i, leaf: leaf, under: under, from: from, to: to, raf: 0 };
    stage.classList.add('pg-flipping'); busy = true; paint(0); return true;
  };
  var end = function (commit) {
    var f = flip; if (!f) return; cancelAnimationFrame(f.raf);
    var keep = commit ? f.to : f.from, drop = commit ? f.from : f.to;
    drop.hidden = true; keep.hidden = false;
    [f.leaf, f.under].forEach(function (e) { e.classList.remove('pg-leaf', 'pg-under'); e.style.transform = e.style.filter = e.style.boxShadow = e.style.opacity = ''; });
    stage.classList.remove('pg-flipping'); stage.style.minHeight = '';
    if (commit) { idx = f.i; paintTabs(idx); } flip = null; busy = false;
  };
  function show(i, top, instant) {
    if (i < 0 || i >= wrap.length || (i === idx && !instant)) return;
    if (flip) end(true);
    if (top) { var r = bar.getBoundingClientRect(); if (r.top < 0) window.scrollTo({ top: window.scrollY + r.top - 4 }); }
    if (calm || instant) { idx = i; wrap.forEach(function (d, j) { d.hidden = j !== i; }); paintTabs(i); return; }
    if (!begin(i)) return;
    tween(0, 1, 620, paint, function () { end(true); });
  }
  paintTabs(0);

  // 손가락 따라 넘기기(세로 스크롤은 그대로 두고, 가로로 확실히 움직일 때만). 가로 스크롤 영역·입력칸에서 시작한 건 무시
  var sx = 0, sy = 0, ok = false, drag = false, pw = 1;
  var scrollsX = function (el) { for (; el && el !== stage; el = el.parentNode) { if (el.nodeType === 1 && /^(INPUT|TEXTAREA|SELECT|CANVAS|IFRAME)$/.test(el.tagName)) return true; if (el.nodeType === 1 && el.scrollWidth > el.clientWidth + 4 && /(auto|scroll)/.test(getComputedStyle(el).overflowX)) return true; } return false; };
  stage.addEventListener('touchstart', function (e) { if (busy) { ok = false; return; } var t = e.touches[0]; sx = t.clientX; sy = t.clientY; drag = false; pw = stage.offsetWidth || 320; ok = e.touches.length === 1 && !scrollsX(e.target); }, { passive: true });
  stage.addEventListener('touchmove', function (e) {
    if (!ok || calm) return; var t = e.touches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (!drag) { if (Math.abs(dx) < 14 || Math.abs(dx) < Math.abs(dy) * 1.6) return; if (!begin(idx + (dx < 0 ? 1 : -1))) { ok = false; return; } drag = true; }
    paint(Math.max(0, Math.min(1, Math.abs(dx) / (pw * .8))));
  }, { passive: true });
  var release = function (e) {
    if (!drag) return; drag = false; var t = e.changedTouches[0], p = Math.max(0, Math.min(1, Math.abs(t.clientX - sx) / (pw * .8))), f = flip; if (!f) return;
    var go = p > .3; tween(p, go ? 1 : 0, 280, paint, function () { end(go); });
  };
  stage.addEventListener('touchend', release, { passive: true }); stage.addEventListener('touchcancel', release, { passive: true });
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
}, 450); });
