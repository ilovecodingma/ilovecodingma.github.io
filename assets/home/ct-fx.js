/* 홈 폭발 연출 — 클릭·터치 폭죽, 주기적 대폭발, 화면 흔들림, 네온 번쩍임. 라이브러리 없음. */
(function () {
  'use strict';
  var reduce = false;
  try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  if (reduce) return;
  var LITE = false; try { LITE = innerWidth < 760 || matchMedia('(pointer:coarse)').matches; } catch (e) {}   /* 폰: 열화판 — 폭죽 적게, 루리 2명, 글자 흩날림·유리·씹기 없음, 1.2초 뒤 차분 */
  var cv = document.createElement('canvas');
  cv.setAttribute('aria-hidden', 'true');
  cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:9990;mix-blend-mode:screen';
  document.body.appendChild(cv);
  var cx = cv.getContext('2d'), W = 0, H = 0, dpr = LITE ? 1 : Math.min(devicePixelRatio || 1, 2);
  function fit() { W = innerWidth; H = innerHeight; cv.width = W * dpr; cv.height = H * dpr; cx.setTransform(dpr, 0, 0, dpr, 0, 0); }
  fit(); addEventListener('resize', fit);
  var P = [], R = [], flash = 0, COL = [330, 345, 15, 35, 50, 190, 280];
  var MAX = LITE ? 160 : 1100;

  function burst(x, y, n, power, hue0) {
    for (var i = 0; i < n && P.length < MAX; i++) {
      var a = Math.random() * 6.2832, s = (Math.random() * .8 + .2) * power;
      P.push({ x: x, y: y, vx: Math.cos(a) * s, vy: Math.sin(a) * s - power * .12, l: 1, d: .008 + Math.random() * .016,
               h: (hue0 == null ? COL[(Math.random() * COL.length) | 0] : hue0 + Math.random() * 40 - 20), r: Math.random() * 2.4 + .8, g: Math.random() < .3 });
    }
    R.push({ x: x, y: y, r: 4, a: 1, p: power });
  }
  function shake(ms, amp) {
    var el = document.querySelector('.ct') || document.body, t0 = performance.now();
    (function f(t) {
      var k = 1 - (t - t0) / ms;
      if (k <= 0) { el.style.transform = ''; return; }
      el.style.transform = 'translate(' + ((Math.random() - .5) * amp * k).toFixed(1) + 'px,' + ((Math.random() - .5) * amp * k).toFixed(1) + 'px)';
      requestAnimationFrame(f);
    })(t0);
  }
  function big() {
    var x = W * (.15 + Math.random() * .7), y = H * (.12 + Math.random() * .45);
    burst(x, y, innerWidth < 700 ? 90 : 170, 9 + Math.random() * 4);
    if (Math.random() < .5) burst(x + (Math.random() - .5) * 220, y + (Math.random() - .5) * 140, 70, 7);
    flash = .55; shake(420, 14);
  }
  // 클릭·터치: 즉시 폭죽 (링크 이동은 막지 않는다)
  addEventListener('pointerdown', function (e) { burst(e.clientX, e.clientY, CALM ? 14 : 46, CALM ? 3.5 : 6.5); }, { passive: true });
  // 마우스 이동: 불꽃 꼬리
  var last = 0;
  addEventListener('pointermove', function (e) {
    var t = performance.now(); if (t - last < 28 || e.pointerType === 'touch') return; last = t;
    for (var i = 0; i < 3; i++) P.push({ x: e.clientX, y: e.clientY, vx: (Math.random() - .5) * 2.2, vy: (Math.random() - .5) * 2.2 + .6, l: .8, d: .03, h: COL[(Math.random() * COL.length) | 0], r: 1.6, g: false });
  }, { passive: true });
  // 첫 진입 대폭발 + 이후 주기적으로
  setTimeout(big, 300); setTimeout(big, 900);
  var T1 = setInterval(function () { if (!document.hidden) big(); }, 5200);



  /* ── 유리 깨짐 ── 충격점에서 금이 번지고, 파편이 회전하며 떨어진다 */
  var CR = [], SH = [], CALM = false, T3 = 0;
  function glass(x, y) {
    var rays = 11 + ((Math.random() * 6) | 0), segs = [], pts = [];
    for (var k = 0; k < rays; k++) {
      var a = k / rays * 6.2832 + Math.random() * .35, px = x, py = y, ring = [];
      for (var j = 0; j < 6; j++) {
        var L = 40 + Math.random() * 120 + j * 22, na = a + (Math.random() - .5) * .45, nx = px + Math.cos(na) * L, ny = py + Math.sin(na) * L;
        segs.push([px, py, nx, ny, j]); px = nx; py = ny; ring.push([px, py]);
      }
      pts.push(ring);
    }
    CR.push({ x: x, y: y, segs: segs, t: 0, life: 1 });
    // 파편: 이웃한 두 금의 같은 단계 점을 이어 삼각형
    for (k = 0; k < rays; k++) {
      var A = pts[k], B = pts[(k + 1) % rays];
      for (j = 0; j < 4; j++) {
        if (SH.length > 220) break;
        var o = j === 0 ? [x, y] : A[j - 1];
        SH.push({ p: [o, A[j], B[j]], cx: (o[0] + A[j][0] + B[j][0]) / 3, cy: (o[1] + A[j][1] + B[j][1]) / 3, dx: 0, dy: 0, rot: 0,
                  vx: (Math.random() - .5) * 5, vy: -2 - Math.random() * 3, vr: (Math.random() - .5) * .25, delay: 22 + j * 6 + Math.random() * 14, l: 1 });
      }
    }
    flash = Math.max(flash, .9); shake(520, 22); burst(x, y, 60, 8, 200);
  }
  addEventListener('pointerdown', function (e) { if (!CALM && Math.random() < .35) glass(e.clientX, e.clientY); }, { passive: true });
  setTimeout(function () { glass(W * .62, H * .3); }, 1100);
  var T2 = setInterval(function () { if (!LITE && !document.hidden && !CALM) glass(W * (.2 + Math.random() * .6), H * (.15 + Math.random() * .5)); }, 7800);

  /* ── 글자 흩날림 → 합체 ── 제목·소제목·카드 글자를 낱자로 쪼개 날렸다가 모은다. 몇 초마다 다시 폭발. */
  var LET = [], io = null;
  function split(el) {
    var tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), nodes = [], n;
    while ((n = tw.nextNode())) if (n.nodeValue.trim()) nodes.push(n);
    nodes.forEach(function (t) {
      var f = document.createDocumentFragment();
      Array.from(t.nodeValue).forEach(function (ch) {
        if (/\s/.test(ch)) { f.appendChild(document.createTextNode(ch)); return; }
        var sp = document.createElement('span'); sp.textContent = ch; sp.setAttribute('aria-hidden', 'true');
        sp.style.cssText = 'display:inline-block;will-change:transform'; f.appendChild(sp); LET.push(sp);
        sp._g = el;
      });
      t.parentNode.replaceChild(f, t);
    });
    el.setAttribute('aria-label', el.textContent);
  }
  function fly(sp, mode, delay) {
    var a = Math.random() * 6.2832, d = 250 + Math.random() * 700;
    var x = Math.cos(a) * d, y = Math.sin(a) * d, r = (Math.random() - .5) * 900, sc = .3 + Math.random() * 3;
    var from = { transform: 'translate(' + x + 'px,' + y + 'px) rotate(' + r + 'deg) scale(' + sc + ')', opacity: 0, filter: 'blur(6px)' };
    var to = { transform: 'none', opacity: 1, filter: 'blur(0)' };
    var kf = mode === 'in' ? [from, to] : [to, from];
    var an = sp.animate(kf, { duration: 900 + Math.random() * 700, delay: delay, easing: mode === 'in' ? 'cubic-bezier(.2,1.4,.4,1)' : 'cubic-bezier(.6,0,.9,.4)', fill: 'both' });
    return an;
  }
  function assemble(group) {
    group.forEach(function (sp, i) { fly(sp, 'in', i * 18 + Math.random() * 120); });
  }
  function explodeAll(group, then) {
    group.forEach(function (sp, i) { fly(sp, 'out', Math.random() * 160); });
    setTimeout(then, 1200);
  }
  function setup() {
    var sel = '.ct h1, .ct .lead, .ct-hd h2, .ct-card h3, .ct-paths b, .ct-tabs a, .ct-rant, .ct-stats span';
    var els = Array.prototype.slice.call(document.querySelectorAll(sel)).filter(function (e) { return e.textContent.length < 90; });
    if (!els.length || LITE) return;
    els.forEach(split);
    var groups = new Map();
    LET.forEach(function (sp) { if (!groups.has(sp._g)) groups.set(sp._g, []); groups.get(sp._g).push(sp); });
    // 화면에 들어올 때마다 날아와서 합쳐진다
    io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { if (en.isIntersecting) { var g = groups.get(en.target); if (g) assemble(g); } });
    }, { threshold: .15 });
    groups.forEach(function (g, el) { g.forEach(function (sp) { sp.style.opacity = 0; }); io.observe(el); });
    // 몇 초마다 보이는 제목 하나가 폭발했다가 다시 합쳐진다
    T3 = setInterval(function () {
      if (document.hidden || CALM) return;
      var vis = []; groups.forEach(function (g, el) { var r = el.getBoundingClientRect(); if (r.bottom > 0 && r.top < innerHeight) vis.push(g); });
      if (!vis.length) return;
      var pick = vis.length > 2 ? [vis[(Math.random() * vis.length) | 0], vis[(Math.random() * vis.length) | 0]] : vis;
      pick.forEach(function (g) { explodeAll(g, function () { assemble(g); }); });
    }, 3600);
  }
  if (document.readyState !== 'loading') setup(); else addEventListener('DOMContentLoaded', setup);


  /* ── 루리 난장판 ── 화면 전체를 튕겨 다니며 돌고, 부딪히면 터지고, 잔소리한다 */
  var RURI = ['hero_1','hero_2','hero_3','hero_4','wrong1_1','wrong1_2','wrong1_3','wrong3_1','wrong3_2','wrong3_3','wrong3_4','right_1','right_2','right_3','right_4','perfect_1','perfect_2','perfect_3','perfect_4','timeout_1','timeout_2','timeout_3','timeout_4','study_1','study_2','study_3','study_4','board_1','board_2','board_3','board_4','dday_1','dday_2','dday_3','dday_4','oops_1','oops_2','oops_3','oops_4','meal_1','meal_2','meal_3','meal_4'];
  var SAY = ['니 점수에 잠이 오냐', '남들은 이미 땄다더라', '그래서 취직하겠냐', '이거라도 해야 먹고살지', '니가? 합격?', '아직도 안 풀었냐', '원서는 냈냐', '지금 자면 망한다', '틀렸네', '한심하다', '공부해라', '내일은 없다'];
  var FL = [], fwrap = document.createElement('div');
  fwrap.setAttribute('aria-hidden', 'true');
  fwrap.style.cssText = 'position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:9980';
  document.body.appendChild(fwrap);
  function spawn(first) {
    var el = document.createElement('div'), im = new Image(), n = RURI[(Math.random() * RURI.length) | 0], base = innerWidth < 700 ? 110 : 170 + Math.random() * 90;
    im.src = '/assets/ruri/sc_' + n + '.webp'; im.alt = ''; im.style.cssText = 'display:block;width:100%;height:auto;filter:drop-shadow(0 0 18px rgba(255,60,120,.8))';
    el.style.cssText = 'position:absolute;left:0;top:0;width:' + base + 'px;will-change:transform';
    var b = document.createElement('b'); b.style.cssText = 'position:absolute;left:50%;top:-6px;transform:translate(-50%,-100%) rotate(-3deg);white-space:nowrap;background:#ff4d7d;color:#fff;font:800 14px/1 system-ui,sans-serif;padding:7px 10px;border-radius:6px;opacity:0;transition:opacity .15s';
    el.appendChild(im); el.appendChild(b); fwrap.appendChild(el);
    var side = (Math.random() * 4) | 0, f = { el: el, b: b, w: base, x: side === 0 ? -base : side === 1 ? W : Math.random() * W, y: side === 2 ? -base * 1.3 : side === 3 ? H : Math.random() * H,
      vx: (Math.random() < .5 ? -1 : 1) * (2 + Math.random() * 4), vy: (Math.random() < .5 ? -1 : 1) * (2 + Math.random() * 4), r: Math.random() * 360, vr: (Math.random() - .5) * 9, ph: Math.random() * 6.28, sp: .03 + Math.random() * .05, say: 0 };
    if (side < 2) f.vx = side === 0 ? Math.abs(f.vx) : -Math.abs(f.vx); else f.vy = side === 2 ? Math.abs(f.vy) : -Math.abs(f.vy);
    FL.push(f);
  }
  function talk(f) { f.b.textContent = SAY[(Math.random() * SAY.length) | 0]; f.b.style.opacity = 1; f.say = 70; }
  var NF = LITE ? 2 : 9; for (var q = 0; q < NF; q++) spawn();
  function stepFly(dt) {
    FL.forEach(function (f) {
      f.x += f.vx * dt; f.y += f.vy * dt; f.r += f.vr * dt; f.ph += f.sp * dt;
      var h = f.w * 1.33, hit = false;
      if (!f.out && (f.x < -f.w * .2 && f.vx < 0 || f.x > W - f.w * .8 && f.vx > 0)) { f.vx = -f.vx * (1 + Math.random() * .12); hit = true; }
      if (!f.out && (f.y < -h * .2 && f.vy < 0 || f.y > H - h * .8 && f.vy > 0)) { f.vy = -f.vy * (1 + Math.random() * .12); hit = true; }
      var m = Math.hypot(f.vx, f.vy); if (!f.out && m > 11) { f.vx *= 11 / m; f.vy *= 11 / m; }
      if (hit && !CALM) { burst(f.x + f.w / 2, f.y + h / 2, 22, 5); if (Math.random() < .5) talk(f); if (Math.random() < .08) glass(f.x + f.w / 2, f.y + h / 2); }
      if (f.say > 0 && (f.say -= dt) <= 0) f.b.style.opacity = 0;
      var sc = 1 + Math.sin(f.ph) * .35;
      f.el.style.transform = 'translate(' + f.x.toFixed(1) + 'px,' + f.y.toFixed(1) + 'px) rotate(' + f.r.toFixed(1) + 'deg) scale(' + sc.toFixed(3) + ')';
    });
  }

  /* ── 15초 뒤: 난장판 종료, 삐뚤어진 평상시로 복귀 ── */
  setTimeout(function () {
    CALM = true; clearInterval(T1); clearInterval(T2); clearInterval(T3);
    (document.querySelector('.ct') || document.body).classList.add('ct-calm');
    FL.forEach(function (f) { f.out = true; f.b.style.opacity = 0; var m = Math.hypot(f.x - W / 2, f.y - H / 2) || 1; f.vx = (f.x - W / 2) / m * 14; f.vy = (f.y - H / 2) / m * 14; });
    setTimeout(function () { FL.length = 0; if (fwrap.parentNode) fwrap.parentNode.removeChild(fwrap); }, 2600);
  }, LITE ? 1200 : 3000);

  /* ── 글자 씹어먹기 ── 루리가 날아와 글자 하나를 물고 와구와구 씹은 뒤 뱉듯이 되돌려 놓는다 */
  function chomp() {
    if (CALM || document.hidden) return;
    var cand = LET.filter(function (sp) { var r = sp.getBoundingClientRect(); return r.width > 8 && r.top > 80 && r.bottom < innerHeight - 40 && r.left > 10 && r.right < innerWidth - 10 && sp.style.visibility !== 'hidden'; });
    if (!cand.length || !document.body.animate) return;
    var sp = cand[(Math.random() * cand.length) | 0], r = sp.getBoundingClientRect(), sz = innerWidth < 700 ? 120 : 170;
    var d = document.createElement('div'), im = new Image(), b = document.createElement('b');
    im.src = '/assets/ruri/sc_' + ['meal_1', 'meal_2', 'meal_3', 'meal_4', 'dday_1', 'perfect_2'][(Math.random() * 6) | 0] + '.webp'; im.alt = '';
    im.style.cssText = 'display:block;width:100%;height:auto;filter:drop-shadow(0 0 16px rgba(255,60,120,.8))';
    b.textContent = '와구와구'; b.style.cssText = 'position:absolute;left:50%;top:-4px;transform:translate(-50%,-100%) rotate(-4deg);white-space:nowrap;background:#ff4d7d;color:#fff;font:800 15px/1 system-ui,sans-serif;padding:7px 10px;border-radius:6px;opacity:0';
    d.style.cssText = 'position:fixed;left:' + (r.left + r.width / 2 - sz * .5) + 'px;top:' + (r.top + r.height / 2 - sz * .55) + 'px;width:' + sz + 'px;pointer-events:none;z-index:9985';
    d.appendChild(im); d.appendChild(b); document.body.appendChild(d);
    var fromX = (Math.random() < .5 ? -1 : 1) * (innerWidth * .7), fromY = (Math.random() - .5) * innerHeight * .6;
    var inn = d.animate([{ transform: 'translate(' + fromX + 'px,' + fromY + 'px) rotate(' + (fromX < 0 ? -40 : 40) + 'deg) scale(.6)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 520, easing: 'cubic-bezier(.2,1.2,.4,1)', fill: 'both' });
    inn.onfinish = function () {
      b.style.opacity = 1; sp.style.visibility = 'hidden';
      var chew = d.animate([{ transform: 'none' }, { transform: 'scale(1.1,.88) translateY(6px)' }, { transform: 'none' }, { transform: 'scale(1.1,.88) translateY(6px)' }, { transform: 'none' }, { transform: 'scale(1.12,.86) translateY(8px)' }, { transform: 'none' }], { duration: 700, fill: 'both' });
      var n = 0, t = setInterval(function () { burst(r.left + r.width / 2, r.top + r.height / 2, 7, 3, 40); if (++n > 3) clearInterval(t); }, 170);
      chew.onfinish = function () {
        b.textContent = '맛없네'; sp.style.visibility = 'visible'; fly(sp, 'in', 0);
        var out = d.animate([{ transform: 'none', opacity: 1 }, { transform: 'translate(' + (-fromX) + 'px,' + (-fromY) + 'px) rotate(' + (fromX < 0 ? 50 : -50) + 'deg) scale(.5)', opacity: 0 }], { duration: 520, delay: 150, easing: 'ease-in', fill: 'both' });
        out.onfinish = function () { d.remove(); };
      };
    };
  }
  if (!LITE) setTimeout(chomp, 500);

  var prev = performance.now();
  function loop(t) {
    var dt = Math.min(2.2, (t - prev) / 16.7); prev = t;
    cx.clearRect(0, 0, W, H); stepFly(dt);
    if (flash > 0) { cx.fillStyle = 'rgba(255,120,170,' + (flash * .35).toFixed(3) + ')'; cx.fillRect(0, 0, W, H); flash -= .035 * dt; }
    for (var i = R.length - 1; i >= 0; i--) {
      var r = R[i]; r.r += r.p * 1.9 * dt; r.a -= .035 * dt;
      if (r.a <= 0) { R.splice(i, 1); continue; }
      cx.strokeStyle = 'rgba(255,200,230,' + r.a.toFixed(3) + ')'; cx.lineWidth = 3 * r.a + .5;
      cx.beginPath(); cx.arc(r.x, r.y, r.r, 0, 6.2832); cx.stroke();
    }

    for (i = CR.length - 1; i >= 0; i--) {
      var c = CR[i]; c.t += dt; var prog = Math.min(1, c.t / 10);
      if (c.t > 24) c.life -= .03 * dt;
      if (c.life <= 0) { CR.splice(i, 1); continue; }
      cx.strokeStyle = 'rgba(255,255,255,' + (c.life * .95).toFixed(3) + ')'; cx.lineWidth = 1.6; cx.shadowColor = '#8fe9ff'; cx.shadowBlur = 8;
      cx.beginPath();
      c.segs.forEach(function (g) { if (g[4] / 6 <= prog) { cx.moveTo(g[0], g[1]); cx.lineTo(g[2], g[3]); } });
      cx.stroke();
    }
    for (i = SH.length - 1; i >= 0; i--) {
      var h = SH[i]; h.delay -= dt;
      if (h.delay > 0) continue;
      h.vy += .45 * dt; h.dx += h.vx * dt; h.dy += h.vy * dt; h.rot += h.vr * dt; h.l -= .006 * dt;
      if (h.l <= 0 || h.cy + h.dy > H + 200) { SH.splice(i, 1); continue; }
      cx.save(); cx.translate(h.cx + h.dx, h.cy + h.dy); cx.rotate(h.rot);
      cx.beginPath(); cx.moveTo(h.p[0][0] - h.cx, h.p[0][1] - h.cy); cx.lineTo(h.p[1][0] - h.cx, h.p[1][1] - h.cy); cx.lineTo(h.p[2][0] - h.cx, h.p[2][1] - h.cy); cx.closePath();
      cx.fillStyle = 'rgba(150,230,255,' + (h.l * .22).toFixed(3) + ')'; cx.fill();
      cx.strokeStyle = 'rgba(255,255,255,' + (h.l * .9).toFixed(3) + ')'; cx.lineWidth = 1.4; cx.stroke(); cx.restore();
    }
    cx.shadowBlur = 0;
    for (i = P.length - 1; i >= 0; i--) {
      var p = P[i]; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += .16 * dt; p.vx *= .985; p.l -= p.d * dt;
      if (p.l <= 0) { P.splice(i, 1); continue; }
      cx.fillStyle = 'hsla(' + p.h + ',100%,' + (p.g ? 78 : 62) + '%,' + p.l.toFixed(3) + ')';
      cx.shadowColor = 'hsl(' + p.h + ',100%,60%)'; cx.shadowBlur = 10;
      cx.beginPath(); cx.arc(p.x, p.y, p.r * (.5 + p.l), 0, 6.2832); cx.fill();
    }
    cx.shadowBlur = 0;
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
