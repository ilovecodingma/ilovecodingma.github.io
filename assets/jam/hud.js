/* 사이트 전체를 게임처럼 — 모든 페이지 HUD(레벨·생존 확률·XP), +XP 알림, 레벨업, 업적 팝업.
   기록은 jam_act(track.js). 업적 정의는 window.JAM_ACH 로 stat.js 도 같이 쓴다. */
(function () {
  'use strict';
  if (window.__jamHud) return; window.__jamHud = 1;
  var K = 'jam_act', H = 'jam_hud';
  function ld(k) { try { return JSON.parse(localStorage.getItem(k) || '{}') || {}; } catch (e) { return {}; } }
  function sv(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function ymd(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }

  // ── 지표 계산 (stat.js 와 같은 공식)
  function metrics() {
    var o = ld(K), D = o.d || {}, Q = o.q || [], now = new Date(), i, days = [];
    for (i = 0; i < 30; i++) { var d = new Date(now); d.setDate(now.getDate() - i); days.push(ymd(d)); }
    function sum() { var ks = arguments, n = 0; days.forEach(function (d) { if (D[d]) for (var j = 0; j < ks.length; j++) n += D[d].v[ks[j]] || 0; }); return n; }
    function act(d) { return D[d] && (D[d].p.length || D[d].v.quiz || D[d].v.habit); }
    var active = days.filter(act).length, streak = 0;
    for (i = 0; i < 30; i++) { if (act(days[i])) streak++; else if (i > 0) break; }
    var cut = Date.now() - 30 * 864e5, q30 = Q.filter(function (x) { return x.t >= cut; });
    var solved = q30.reduce(function (a, x) { return a + x.n; }, 0), right = q30.reduce(function (a, x) { return a + x.s; }, 0);
    var allSolved = Q.reduce(function (a, x) { return a + x.n; }, 0), perfect = Q.filter(function (x) { return x.n >= 3 && x.s === x.n; }).length;
    var habit = 0, cats = {}; Object.keys(D).forEach(function (k) { habit += D[k].v.habit || 0; for (var c in D[k].v) if (c !== 'quiz' && c !== 'habit' && D[k].v[c]) cats[c] = 1; });
    var xp = solved * 2 + right * 3 + sum('exam', 'spec', 'money', 'issue', 'body', 'dev', 'wiki') + streak * 5 + sum('habit') * 4;
    var lv = Math.max(1, Math.floor(Math.sqrt(xp / 4)) + 1);
    return { xp: xp, lv: lv, streak: streak, active: active, solved: solved, right: right, allSolved: allSolved, perfect: perfect, habit: habit, ncat: Object.keys(cats).length,
      acc: solved ? right / solved : 0, login: !!(function () { try { return localStorage.getItem('jupjup_tok'); } catch (e) { return ''; } })() };
  }
  var ACH = [
    { id: 'signup', n: '이세계 입장', d: '가입하고 헬조선에 들어왔다', ok: function (m) { return m.login; } },
    { id: 'q1', n: '첫 문제', d: '문제를 하나라도 풀었다', ok: function (m) { return m.allSolved >= 1; } },
    { id: 'q50', n: '문제 50개', d: '문제 50개를 풀었다', ok: function (m) { return m.allSolved >= 50; } },
    { id: 'q200', n: '문제 200개', d: '문제 200개를 풀었다', ok: function (m) { return m.allSolved >= 200; } },
    { id: 'perfect', n: '만점', d: '문제은행에서 만점을 받았다', ok: function (m) { return m.perfect >= 1; } },
    { id: 'acc80', n: '정답률 80%', d: '30문제 이상 풀고 정답률 80%', ok: function (m) { return m.solved >= 30 && m.acc >= .8; } },
    { id: 'st3', n: '3일 연속', d: '3일 연속 접속했다', ok: function (m) { return m.streak >= 3; } },
    { id: 'st7', n: '7일 연속', d: '7일 연속 접속했다', ok: function (m) { return m.streak >= 7; } },
    { id: 'st30', n: '30일 연속', d: '한 달을 안 빠졌다', ok: function (m) { return m.streak >= 30; } },
    { id: 'explore', n: '탐험가', d: '5개 분야를 둘러봤다', ok: function (m) { return m.ncat >= 5; } },
    { id: 'habit7', n: '습관 7회', d: '습관 체크인 7번', ok: function (m) { return m.habit >= 7; } },
    { id: 'habit21', n: '습관 21회', d: '습관 체크인 21번', ok: function (m) { return m.habit >= 21; } },
    { id: 'lv5', n: '레벨 5', d: '레벨 5 달성', ok: function (m) { return m.lv >= 5; } },
    { id: 'lv10', n: '레벨 10', d: '레벨 10 달성', ok: function (m) { return m.lv >= 10; } },
    { id: 'goal_done', n: '목표 달성', d: '목표 기한을 플랜대로 채웠다', ok: function (m, ex) { return !!(ex && ex.goal_done); } }
  ];
  window.JAM_ACH = ACH; window.jamMetrics = metrics;

  // ── 화면
  var css = document.createElement('style');
  css.textContent = '#jam-hud{position:fixed;left:10px;bottom:10px;z-index:9970;display:flex;gap:8px;align-items:center;padding:6px 10px;background:rgba(5,8,26,.92);border:1px solid #00f0ff;color:#d8fbff;font:700 12px/1.2 ui-monospace,Consolas,"Malgun Gothic",monospace;text-decoration:none;clip-path:polygon(0 0,calc(100% - 8px) 0,100% 8px,100% 100%,8px 100%,0 calc(100% - 8px));box-shadow:0 0 14px rgba(0,240,255,.35)}'
    + '#jam-hud b{color:#ff9be9}#jam-hud i{display:block;width:54px;height:5px;background:#1b2140}#jam-hud i u{display:block;height:100%;background:linear-gradient(90deg,#00f0ff,#ff2bd6);text-decoration:none}#jam-hud em{font-style:normal;color:#ffeb5c}'
    + '#jam-toast{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:9996;display:flex;flex-direction:column;gap:8px;align-items:center;pointer-events:none}'
    + '.jam-t{padding:9px 16px;background:rgba(5,8,26,.95);border:1px solid #ff2bd6;color:#fff;font:800 14px/1.3 ui-monospace,Consolas,"Malgun Gothic",monospace;box-shadow:0 0 18px rgba(255,43,214,.5);animation:jamT 3.6s ease forwards;clip-path:polygon(0 0,calc(100% - 8px) 0,100% 8px,100% 100%,8px 100%,0 calc(100% - 8px))}'
    + '.jam-t.xp{border-color:#00f0ff;box-shadow:0 0 18px rgba(0,240,255,.5)}.jam-t.lv{border-color:#ffe14d;color:#ffe14d;font-size:18px}.jam-t.ac{border-color:#ffe14d;box-shadow:0 0 22px rgba(255,225,77,.6)}.jam-t small{display:block;font-weight:400;color:#9fc4cc}'
    + '@keyframes jamT{0%{opacity:0;transform:translateY(-14px) scale(.9)}8%{opacity:1;transform:none}85%{opacity:1}100%{opacity:0;transform:translateY(-8px)}}'
    + '@media(max-width:620px){#jam-hud{bottom:64px}}@media (prefers-reduced-motion:reduce){.jam-t{animation-duration:.01s;opacity:1}}';
  document.head.appendChild(css);
  var hud = document.createElement('a'); hud.id = 'jam-hud'; hud.href = '/me/'; hud.setAttribute('aria-label', '내 상태창');
  var tw = document.createElement('div'); tw.id = 'jam-toast'; tw.setAttribute('aria-live', 'polite');
  function toast(cls, html, ms) { var t = document.createElement('div'); t.className = 'jam-t ' + cls; t.innerHTML = html; tw.appendChild(t); setTimeout(function () { t.remove(); }, ms || 3700); }
  function xpBar(m) { var cur = (m.lv - 1) * (m.lv - 1) * 4, nxt = m.lv * m.lv * 4; return Math.max(3, Math.min(100, Math.round((m.xp - cur) * 100 / Math.max(1, nxt - cur)))); }
  function paint(m) {
    var sv2 = ld('jam_surv'), surv = sv2.v != null ? sv2.v + '%' : '??%';
    hud.innerHTML = '<b>LV.' + m.lv + '</b><i><u style="width:' + xpBar(m) + '%"></u></i><span>생존 <em>' + surv + '</em></span>';
  }
  function check(first) {
    var m = metrics(), h = ld(H), ex = ld('jam_ach_extra'), got = h.ach || {}, newAch = [];
    ACH.forEach(function (a) { if (!got[a.id] && a.ok(m, ex)) { got[a.id] = Date.now(); newAch.push(a); } });
    var dx = m.xp - (h.xp == null ? m.xp : h.xp);
    if (!first || true) {
      if (dx > 0 && h.xp != null) toast('xp', '+' + dx + ' XP');
      if (h.lv != null && m.lv > h.lv) toast('lv', 'LEVEL UP! LV.' + m.lv);
    }
    newAch.forEach(function (a, i) { setTimeout(function () { toast('ac', '업적 달성 · ' + a.n + '<small>' + a.d + '</small>', 4600); }, 700 + i * 900); });
    sv(H, { xp: m.xp, lv: m.lv, ach: got });
    paint(m);
    try { var o = ld(K); o.a = got; sv(K, o); } catch (e) {}   // 업적도 계정에 같이 저장(track.js 동기화)
  }
  function mount() { document.body.appendChild(tw); document.body.appendChild(hud); check(true); }
  if (document.body) mount(); else addEventListener('DOMContentLoaded', mount);
  addEventListener('jam:update', function () { setTimeout(function () { check(false); }, 150); });
})();
