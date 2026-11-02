/* 키워드 3D 지도: 외부 라이브러리 없이 캔버스로 구를 돌린다. 노드=키워드(색=단기/중기/장기), 선=겹치는 단어, 클릭=해당 글로 이동. */
(function () {
  var box = document.getElementById('kwmap'); if (!box) return;
  var data; try { data = JSON.parse(document.getElementById('kwdata').textContent); } catch (e) { return; }
  var N = data.n, E = data.e;
  var cv = document.createElement('canvas'); box.appendChild(cv);
  var tip = document.createElement('div'); tip.className = 'kw-tip'; box.appendChild(tip);
  var ctx = cv.getContext('2d'), W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
  var COL = { 0: '#e5484d', 1: '#d97706', 2: '#2563eb' };   // 단기 / 중기 / 장기
  var RAD = { 0: 0.55, 1: 0.78, 2: 1.0 };                   // 단기가 안쪽, 장기가 바깥 껍질
  var ay = 0.4, ax = -0.25, vy = 0.002, vx = 0, zoom = 1, drag = null, hover = -1, moved = 0;
  var dark = window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches;
  N.forEach(function (n, i) {   // 티어별 껍질 위에 피보나치 구로 고르게 배치
    var same = N.filter(function (m) { return m.t === n.t; }), k = same.indexOf(n), c = same.length;
    var y = 1 - 2 * (k + .5) / c, r = Math.sqrt(1 - y * y), th = k * 2.399963;
    n.x = Math.cos(th) * r * RAD[n.t]; n.y = y * RAD[n.t]; n.z = Math.sin(th) * r * RAD[n.t];
  });
  function size() { W = box.clientWidth; H = Math.max(360, Math.min(560, Math.round(W * .62))); cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px'; }
  size(); window.addEventListener('resize', size);
  var P = [];
  function proj() {
    var sa = Math.sin(ay), ca = Math.cos(ay), sx = Math.sin(ax), cx = Math.cos(ax), s = Math.min(W, H) * .42 * zoom;
    for (var i = 0; i < N.length; i++) {
      var n = N[i], x = n.x * ca + n.z * sa, z = -n.x * sa + n.z * ca, y = n.y * cx - z * sx; z = n.y * sx + z * cx;
      var f = 1 / (1.9 - z * .55);
      P[i] = { x: W / 2 + x * s * f * 1.9, y: H / 2 + y * s * f * 1.9, z: z, f: f };
    }
  }
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    if (!drag) { ay += vy; ax += vx; vx *= .95; if (Math.abs(vx) < 1e-4) vx = 0; }
    proj();
    ctx.lineWidth = 1;
    for (var j = 0; j < E.length; j++) {
      var a = P[E[j][0]], b = P[E[j][1]], on = hover >= 0 && (E[j][0] === hover || E[j][1] === hover);
      ctx.strokeStyle = on ? (dark ? 'rgba(160,190,255,.85)' : 'rgba(29,78,216,.75)') : (dark ? 'rgba(160,170,190,.13)' : 'rgba(60,70,90,.12)');
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    var order = P.map(function (_, i) { return i; }).sort(function (u, v) { return P[u].z - P[v].z; });
    order.forEach(function (i) {
      var p = P[i], n = N[i], r = (n.t === 0 ? 5.5 : n.t === 1 ? 4.5 : 3.6) * p.f * 1.9, near = (p.z + 1) / 2;
      ctx.globalAlpha = i === hover ? 1 : .35 + .65 * near;
      ctx.fillStyle = COL[n.t]; ctx.beginPath(); ctx.arc(p.x, p.y, i === hover ? r + 2 : r, 0, 6.2832); ctx.fill();
      if (n.t < 2 && near > .55 || i === hover) {
        ctx.globalAlpha = i === hover ? 1 : near; ctx.fillStyle = dark ? '#e6e9ee' : '#111827'; ctx.font = (i === hover ? '700 ' : '500 ') + '12px Pretendard,sans-serif';
        ctx.fillText(n.q.length > 16 ? n.q.slice(0, 16) + '…' : n.q, p.x + r + 4, p.y + 4);
      }
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }
  function at(ev) {
    var rc = cv.getBoundingClientRect(), mx = ev.clientX - rc.left, my = ev.clientY - rc.top, best = -1, bd = 14 * 14;
    for (var i = 0; i < P.length; i++) { var d = (P[i].x - mx) * (P[i].x - mx) + (P[i].y - my) * (P[i].y - my); if (d < bd) { bd = d; best = i; } }
    return best;
  }
  cv.addEventListener('pointerdown', function (e) { drag = { x: e.clientX, y: e.clientY }; moved = 0; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener('pointermove', function (e) {
    if (drag) { var dx = e.clientX - drag.x, dy = e.clientY - drag.y; moved += Math.abs(dx) + Math.abs(dy); ay += dx * .006; ax = Math.max(-1.2, Math.min(1.2, ax + dy * .006)); vy = dx * .0006; drag.x = e.clientX; drag.y = e.clientY; return; }
    hover = at(e); cv.style.cursor = hover >= 0 ? 'pointer' : 'grab';
    if (hover >= 0) { tip.textContent = N[hover].q + ' · ' + ['단기', '중기', '장기'][N[hover].t]; tip.style.display = 'block'; tip.style.left = Math.min(W - 200, P[hover].x + 12) + 'px'; tip.style.top = (P[hover].y - 30) + 'px'; } else tip.style.display = 'none';
  });
  cv.addEventListener('pointerup', function (e) { var was = moved < 6; drag = null; if (was) { var i = at(e); if (i >= 0) location.href = N[i].u; } });
  cv.addEventListener('pointerleave', function () { hover = -1; tip.style.display = 'none'; });
  cv.addEventListener('wheel', function (e) { e.preventDefault(); zoom = Math.max(.6, Math.min(2, zoom * (e.deltaY < 0 ? 1.08 : .93))); }, { passive: false });
  draw();
})();
