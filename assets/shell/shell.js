// 한 화면 셸 (2026-10-23 사용자 「스크롤 최소화·페이지 딱 고정·내용 가려지면 안 됨」) — 개발 섹션부터 적용
//  <h2> 구간마다 한 화면: 위쪽 탭으로 고르거나 좌우로 밀어 넘긴다. 화면 높이는 고정이라 바뀌지 않고,
//  탭 줄은 영역 안에 있어서(고정 배치 아님) 계정 메뉴·헤더를 덮지 않는다. 구간이 길면 그 화면 안에서만 스크롤.
//  JS 가 없거나 ?all=1 이면 전부 그대로 보인다(검색 노출·인쇄 영향 없음). 주소는 바꾸지 않는다.
(function () {
  var go = function () {
    if (/[?&]all=1/.test(location.search)) return;
    if (!/^\/(ailog|dev|dev\/faq)\/$/.test(location.pathname)) return;
    var main = document.querySelector('main'); if (!main || main.hasAttribute('data-noshell') || main.querySelector('.sh')) return;
    var h = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
    var clean = function (t) { return (t || '').replace(/\s+/g, ' ').trim(); };
    var kids = [].slice.call(main.children), i = 0;
    while (i < kids.length && (kids[i].matches('p.bc, nav.bc, h1') || /^(SCRIPT|STYLE|LINK)$/.test(kids[i].tagName))) i++;
    var body = kids.slice(i), sections = [], cur = null, lead = [];
    body.forEach(function (el) {
      if (/^(SCRIPT|STYLE|LINK)$/.test(el.tagName)) return;
      if (el.tagName === 'H2') { cur = { t: clean(el.textContent), els: [el] }; sections.push(cur); return; }
      var inner = el.querySelector && el.querySelector(':scope > h2');
      if (inner && !cur) { cur = { t: clean(inner.textContent), els: [el] }; sections.push(cur); cur = null; return; }
      if (inner) { cur = { t: clean(inner.textContent), els: [el] }; sections.push(cur); return; }
      if (cur) cur.els.push(el); else lead.push(el);
    });
    if (lead.length) sections[0].els = lead.concat(sections[0].els);   // 도입 문단은 첫 구간 맨 위로(한 줄짜리 「개요」 탭을 만들지 않는다)
    if (sections.length < 3) return;

    var root = h('div', 'sh'), tabs = h('nav', 'sh-tabs'), view = h('div', 'sh-view'), track = h('div', 'sh-track'), cnt = h('div', 'sh-cnt');
    main.classList.add('sh-on'); main.insertBefore(root, kids[i] || null);   // 머리글(빵부스러기·h1) 바로 아래 — 구간을 옮기기 전에 자리를 잡는다
    tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', '이 화면의 구간');
    var screens = [], btns = [], idx = 0, start = null;
    sections.forEach(function (s, n) {
      var sc = h('section', 'sh-screen'); sc.setAttribute('role', 'tabpanel'); s.els.forEach(function (e) { sc.appendChild(e); }); screens.push(sc); track.appendChild(sc);
      var b = h('button', 'sh-tab', s.t.replace(/^[^\p{L}\p{N}]+/u, function (m) { return m.length > 4 ? '' : m; }).slice(0, 12)); b.type = 'button'; b.setAttribute('role', 'tab');
      b.onclick = function () { show(n); }; btns.push(b); tabs.appendChild(b);
    });
    view.appendChild(track); root.appendChild(tabs); root.appendChild(view); root.appendChild(cnt);

    var fit = function () { var top = view.getBoundingClientRect().top; var hgt = Math.max(440, window.innerHeight - top - 56); view.style.height = hgt + 'px'; };
    function show(n, instant) {
      n = Math.max(0, Math.min(screens.length - 1, n)); idx = n;
      track.style.transition = instant ? 'none' : ''; track.style.transform = 'translateX(' + (-100 * n) + '%)';
      screens.forEach(function (s, j) { s.setAttribute('aria-hidden', j === n ? 'false' : 'true'); s.toggleAttribute('inert', j !== n); if (j === n) s.scrollTop = 0; });
      btns.forEach(function (b, j) { b.classList.toggle('on', j === n); b.setAttribute('aria-selected', j === n); });
      cnt.textContent = (n + 1) + ' / ' + screens.length + ' · 좌우로 밀어서 넘기기';
      var on = btns[n]; if (on) tabs.scrollTo({ left: on.offsetLeft - 12, behavior: instant ? 'auto' : 'smooth' });
    }
    // 손가락 따라 넘기기: 가로로 확실히 움직일 때만(세로 스크롤은 그대로). 가로 스크롤 영역·입력칸에서 시작한 건 무시
    var sx = 0, sy = 0, drag = false, ok = false, pw = 1;
    var xscroll = function (el) { for (; el && el !== view; el = el.parentNode) { if (el.nodeType !== 1) continue; if (/^(INPUT|TEXTAREA|SELECT|CANVAS|IFRAME)$/.test(el.tagName)) return true; if (el.scrollWidth > el.clientWidth + 4 && /(auto|scroll)/.test(getComputedStyle(el).overflowX)) return true; } return false; };
    view.addEventListener('touchstart', function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; drag = false; pw = view.offsetWidth || 320; ok = e.touches.length === 1 && !xscroll(e.target); }, { passive: true });
    view.addEventListener('touchmove', function (e) {
      if (!ok) return; var t = e.touches[0], dx = t.clientX - sx, dy = t.clientY - sy;
      if (!drag) { if (Math.abs(dx) < 12 || Math.abs(dx) < Math.abs(dy) * 1.5) return; drag = true; track.style.transition = 'none'; }
      var edge = (idx === 0 && dx > 0) || (idx === screens.length - 1 && dx < 0) ? .3 : 1;
      track.style.transform = 'translateX(calc(' + (-100 * idx) + '% + ' + (dx * edge) + 'px))';
    }, { passive: true });
    var end = function (e) {
      if (!drag) return; drag = false; var dx = e.changedTouches[0].clientX - sx; track.style.transition = '';
      show(idx + (Math.abs(dx) > pw * .22 ? (dx < 0 ? 1 : -1) : 0));
    };
    view.addEventListener('touchend', end, { passive: true }); view.addEventListener('touchcancel', end, { passive: true });
    document.addEventListener('keydown', function (e) {
      if ((e.target.closest && e.target.closest('input,textarea,select,[contenteditable]')) || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === 'ArrowRight') show(idx + 1); else if (e.key === 'ArrowLeft') show(idx - 1);
    });
    // #앵커가 가리키는 구간 열기
    var jump = function () { var id = decodeURIComponent((location.hash || '').slice(1)); if (!id) return; var el = document.getElementById(id); if (!el) return; var sc = el.closest('.sh-screen'); if (sc) { show(screens.indexOf(sc), true); setTimeout(function () { el.scrollIntoView({ block: 'nearest' }); }, 30); } };
    window.addEventListener('hashchange', jump); document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href^="#"]'); if (a) setTimeout(jump, 0); });
    window.addEventListener('resize', fit);
    fit(); show(0, true); jump();
    setTimeout(fit, 400); setTimeout(fit, 1500);   // 늦게 뜨는 이미지·글꼴로 위쪽 높이가 바뀔 수 있다
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
