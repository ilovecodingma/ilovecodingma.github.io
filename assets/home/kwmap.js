/* 키워드 지도 (2026-11-03 개편): 외부 라이브러리 없는 캔버스 3D. 라벨은 선택·연결·주요 주제만, 선택하면 연결 항목 강조,
   검색·분류 필터·확대·축소·초기화, 키보드(방향키·+/-)와 터치 지원, 같은 내용을 목록으로도 제공. 분류 색은 고정이다. */
(function () {
  var box = document.getElementById('kwmap'); if (!box) return;
  var data; try { data = JSON.parse(document.getElementById('kwdata').textContent); } catch (e) { box.textContent = '지도 데이터를 불러오지 못했어요. 아래 목록을 이용해 주세요.'; return; }
  var N = data.n, E = data.e, TN = ['단기', '중기', '장기'];
  var COL = ['#6d28d9', '#0e7490', '#64748b'], COLD = ['#a78bfa', '#5eead4', '#94a3b8'];   // 단기·중기·장기 고정색(필터를 바꿔도 그대로)
  var RAD = [0.55, 0.78, 1.0];
  var dark = function () { var r = document.documentElement.getAttribute('data-theme'); return r ? r === 'dark' : (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cv = box.querySelector('canvas'), ctx = cv.getContext('2d'), dpr = Math.min(window.devicePixelRatio || 1, 2), W = 0, H = 0;
  var info = document.getElementById('kw-info'), q = document.getElementById('kw-q'), nb = [];
  var show = [true, true, true], sel = -1, hover = -1, ay = 0.4, ax = -0.25, vy = reduce ? 0 : 0.0015, zoom = 1, drag = null, moved = 0, match = null;
  var deg = N.map(function () { return 0; }); nb = N.map(function () { return []; });
  E.forEach(function (e) { deg[e[0]]++; deg[e[1]]++; nb[e[0]].push(e[1]); nb[e[1]].push(e[0]); });
  var top = N.map(function (_, i) { return i; }).sort(function (a, b) { return deg[b] - deg[a] || N[a].t - N[b].t; }).slice(0, 10);
  N.forEach(function (n) {
    var same = N.filter(function (m) { return m.t === n.t; }), k = same.indexOf(n), c = same.length;
    var y = 1 - 2 * (k + .5) / c, r = Math.sqrt(1 - y * y), th = k * 2.399963;
    n.x = Math.cos(th) * r * RAD[n.t]; n.y = y * RAD[n.t]; n.z = Math.sin(th) * r * RAD[n.t];
  });
  function size() { W = box.clientWidth; H = Math.max(380, Math.min(620, Math.round(W * .66))); cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px'; }
  size(); window.addEventListener('resize', size);
  var P = [];
  function proj() {
    var sa = Math.sin(ay), ca = Math.cos(ay), sx = Math.sin(ax), cx = Math.cos(ax), s = Math.min(W, H) * .43 * zoom;
    for (var i = 0; i < N.length; i++) {
      var n = N[i], x = n.x * ca + n.z * sa, z = -n.x * sa + n.z * ca, y = n.y * cx - z * sx; z = n.y * sx + z * cx;
      var f = 1 / (1.9 - z * .55); P[i] = { x: W / 2 + x * s * f * 1.9, y: H / 2 + y * s * f * 1.9, z: z, f: f };
    }
  }
  var vis = function (i) { return show[N[i].t]; };
  var lit = function (i) { return sel >= 0 ? (i === sel || nb[sel].indexOf(i) >= 0) : (match ? match[i] : true); };
  function draw() {
    var dk = dark(); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    if (sel < 0 && !drag && vy) ay += vy;   // 선택 중에는 멈춘다
    proj();
    E.forEach(function (e) {
      if (!vis(e[0]) || !vis(e[1])) return;
      var a = P[e[0]], b = P[e[1]], on = sel >= 0 && (e[0] === sel || e[1] === sel);
      ctx.lineWidth = on ? 2 : 1;
      ctx.strokeStyle = on ? (dk ? 'rgba(196,181,253,.95)' : 'rgba(109,40,217,.9)') : (sel >= 0 ? (dk ? 'rgba(148,163,184,.10)' : 'rgba(71,85,105,.10)') : (dk ? 'rgba(148,163,184,.22)' : 'rgba(71,85,105,.16)'));
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    });
    var order = P.map(function (_, i) { return i; }).filter(vis).sort(function (u, v) { return P[u].z - P[v].z; }), labels = [];
    order.forEach(function (i) {
      var p = P[i], n = N[i], near = (p.z + 1) / 2, on = lit(i), r = (n.t === 0 ? 6 : n.t === 1 ? 5.2 : 3.4) * p.f * 1.9;
      ctx.globalAlpha = i === sel || i === hover ? 1 : (on ? .45 + .55 * near : .12);
      ctx.fillStyle = dk ? COLD[n.t] : COL[n.t]; ctx.beginPath(); ctx.arc(p.x, p.y, i === sel ? r + 3 : i === hover ? r + 2 : r, 0, 6.2832); ctx.fill();
      if (i === sel) { ctx.strokeStyle = dk ? '#fff' : '#0f172a'; ctx.lineWidth = 2; ctx.stroke(); }
      if (i === sel || i === hover || (sel >= 0 && on) || (sel < 0 && !match && top.indexOf(i) >= 0 && near > .5) || (match && match[i] && labels.length < 8)) labels.push(i);
    });
    ctx.font = '600 13px Pretendard,system-ui,sans-serif'; var used = [];
    labels.sort(function (a, b) { return (b === sel) - (a === sel) || (b === hover) - (a === hover); }).forEach(function (i) {
      var p = P[i], t0 = N[i].q.split(/[?—·:]/)[0].trim(), t = t0.length > 14 ? t0.slice(0, 14) + '…' : t0, w = ctx.measureText(t).width, x = p.x + 9, y = p.y + 4, hit = false;
      if (x + w > W - 4) x = p.x - 9 - w; if (x < 4) x = 4;
      for (var k = 0; k < used.length; k++) { var u = used[k]; if (x < u[0] + u[2] && x + w > u[0] && y - 12 < u[1] + 14 && y + 4 > u[1] - 12 + 0) { hit = true; break; } }
      if (hit && i !== sel && i !== hover) return;
      used.push([x, y, w]);
      ctx.globalAlpha = 1; ctx.fillStyle = dk ? 'rgba(22,26,33,.9)' : 'rgba(255,255,255,.92)'; ctx.fillRect(x - 3, y - 12, w + 6, 17);
      ctx.fillStyle = dk ? '#e6e9ee' : '#0f172a'; ctx.fillText(t, x, y);
    });
    ctx.globalAlpha = 1; requestAnimationFrame(draw);
  }
  function at(ev) {
    var rc = cv.getBoundingClientRect(), mx = ev.clientX - rc.left, my = ev.clientY - rc.top, best = -1, bd = 22 * 22;
    for (var i = 0; i < P.length; i++) { if (!vis(i)) continue; var d = (P[i].x - mx) * (P[i].x - mx) + (P[i].y - my) * (P[i].y - my); if (d < bd) { bd = d; best = i; } }
    return best;
  }
  function select(i) {
    sel = i; if (!info) return; info.textContent = '';
    if (i < 0) { var p0 = document.createElement('p'); p0.textContent = '점을 누르거나 아래 목록에서 「지도에서 보기」를 누르면 연결된 질문이 강조됩니다.'; info.appendChild(p0); return; }
    var n = N[i], tg = document.createElement('p'); tg.className = 'tg'; tg.textContent = TN[n.t]; info.appendChild(tg);
    var h = document.createElement('h3'); h.textContent = n.q; info.appendChild(h);
    var a = document.createElement('a'); a.className = 'go'; a.href = n.u; a.textContent = '글 읽기'; info.appendChild(a);
    var h2 = document.createElement('p'); h2.className = 'nb-h'; h2.textContent = nb[i].length ? '같은 단어로 이어진 질문 ' + nb[i].length + '개' : '이어진 질문이 아직 없어요'; info.appendChild(h2);
    var ul = document.createElement('ul'); nb[i].forEach(function (j) { var li = document.createElement('li'), b = document.createElement('button'); b.type = 'button'; b.textContent = N[j].q; b.onclick = function () { select(j); }; li.appendChild(b); ul.appendChild(li); }); info.appendChild(ul);
  }
  cv.addEventListener('pointerdown', function (e) { drag = { x: e.clientX, y: e.clientY }; moved = 0; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener('pointermove', function (e) {
    if (drag) { var dx = e.clientX - drag.x, dy = e.clientY - drag.y; moved += Math.abs(dx) + Math.abs(dy); ay += dx * .006; ax = Math.max(-1.2, Math.min(1.2, ax + dy * .006)); drag.x = e.clientX; drag.y = e.clientY; return; }
    hover = at(e); cv.style.cursor = hover >= 0 ? 'pointer' : 'grab';
  });
  cv.addEventListener('pointerup', function (e) { var tap = moved < 8; drag = null; if (tap) { var i = at(e); select(i); } });
  cv.addEventListener('pointerleave', function () { hover = -1; });
  cv.addEventListener('wheel', function (e) { e.preventDefault(); zoom = Math.max(.6, Math.min(2.4, zoom * (e.deltaY < 0 ? 1.1 : .91))); }, { passive: false });
  cv.addEventListener('keydown', function (e) {
    var k = e.key, used = true;
    if (k === 'ArrowLeft') ay -= .12; else if (k === 'ArrowRight') ay += .12; else if (k === 'ArrowUp') ax = Math.max(-1.2, ax - .1); else if (k === 'ArrowDown') ax = Math.min(1.2, ax + .1);
    else if (k === '+' || k === '=') zoom = Math.min(2.4, zoom * 1.15); else if (k === '-') zoom = Math.max(.6, zoom / 1.15); else if (k === 'Escape') select(-1); else used = false;
    if (used) e.preventDefault();
  });
  function reset() { ay = .4; ax = -.25; zoom = 1; vy = reduce ? 0 : .0015; select(-1); show = [true, true, true]; match = null; if (q) q.value = ''; [].forEach.call(document.querySelectorAll('.kw-f button'), function (b) { b.setAttribute('aria-pressed', 'true'); }); list(); }
  document.getElementById('kw-in').onclick = function () { zoom = Math.min(2.4, zoom * 1.2); };
  document.getElementById('kw-out').onclick = function () { zoom = Math.max(.6, zoom / 1.2); };
  document.getElementById('kw-reset').onclick = reset;
  [].forEach.call(document.querySelectorAll('.kw-f button'), function (b) {
    b.onclick = function () { var t = +b.getAttribute('data-t'); show[t] = !show[t]; b.setAttribute('aria-pressed', show[t] ? 'true' : 'false'); if (sel >= 0 && !vis(sel)) select(-1); list(); };
  });
  if (q) q.addEventListener('input', function () {
    var v = q.value.trim().toLowerCase();
    if (!v) { match = null; list(); return; }
    match = N.map(function (n) { return n.q.toLowerCase().indexOf(v) >= 0; }); list();
  });
  if (q && q.form) q.form.addEventListener('submit', function (e) { e.preventDefault(); if (match) { var i = match.indexOf(true); if (i >= 0) select(i); } });
  var empty = document.getElementById('kw-empty');
  function list() {
    var n = 0; [].forEach.call(document.querySelectorAll('.kw-l li'), function (li) {
      var i = +li.getAttribute('data-i'), ok = show[N[i].t] && (!match || match[i]); li.hidden = !ok; if (ok) n++;
    });
    [].forEach.call(document.querySelectorAll('.kw-l'), function (ul) { var s = ul.previousElementSibling; if (s) s.hidden = !ul.querySelector('li:not([hidden])'); });
    if (empty) empty.hidden = n > 0;
  }
  [].forEach.call(document.querySelectorAll('.kw-l button'), function (b) { b.onclick = function () { select(+b.closest('li').getAttribute('data-i')); box.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' }); }; });
  select(-1); draw();
})();
