/* 상태창 기록기 — 기기 안(localStorage)에만 저장한다. 방문(하루 1회/페이지)과 문제 채점 결과를 쌓는다. */
(function () {
  'use strict';
  var K = 'jam_act';
  function ld() { try { return JSON.parse(localStorage.getItem(K) || '{}') || {}; } catch (e) { return {}; } }
  function sv(o) { try { localStorage.setItem(K, JSON.stringify(o)); } catch (e) {} }
  function day(d) { d = d || new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  var CAT = [
    ['bank', /^\/exam\/bank\//], ['exam', /^\/exam\//], ['dev', /^\/(park|ailog|dev|ai|class|prep|lab|devlog|devtrend)\//],
    ['money', /^\/(apply|money|guide|a|price|map|kw|more)\//], ['spec', /^\/(contest|c|event|events|winners|review|watch)\//],
    ['body', /^\/(diet|fridge|play)\//], ['issue', /^\/(issue|news|hot|trend|talk|satire|mag|today)\//], ['wiki', /^\/(wiki|w|ref|qa)\//]
  ];
  function cat(p) { for (var i = 0; i < CAT.length; i++) if (CAT[i][1].test(p)) return CAT[i][0]; return ''; }
  try {   // 가입(로그인)하면 갑자기 이세계 미연시가 시작된다 — 아직 시작 안 했으면 /me/ 로
    if (localStorage.getItem('jupjup_tok') && !localStorage.getItem('jam_seen') && !sessionStorage.getItem('jam_redir')
        && location.pathname.indexOf('/me/') !== 0 && !/^\/(login|admin)\//.test(location.pathname)) {
      sessionStorage.setItem('jam_redir', '1'); location.href = '/me/?start=1';
    }
  } catch (e) {}

  // ── 회원이면 기록을 계정에 저장·복원(기기를 바꿔도 이어진다)
  var API = (document.body && document.body.dataset.api) || 'https://jupjup-api.sung2011103.workers.dev';
  function tok() { try { return localStorage.getItem('jupjup_tok') || ''; } catch (e) { return ''; } }
  function merge(a, b) {
    var r = { d: {}, q: [] }, ad = a.d || {}, bd = b.d || {}, ks = {}, k;
    for (k in ad) ks[k] = 1; for (k in bd) ks[k] = 1;
    Object.keys(ks).forEach(function (k) {
      var x = ad[k] || { v: {}, p: [] }, y = bd[k] || { v: {}, p: [] }, v = {}, c;
      for (c in x.v) v[c] = x.v[c]; for (c in y.v) v[c] = Math.max(v[c] || 0, y.v[c]);
      var pp = (x.p || []).slice(); (y.p || []).forEach(function (z) { if (pp.indexOf(z) < 0) pp.push(z); });
      r.d[k] = { v: v, p: pp.slice(0, 80) };
    });
    var seen = {};
    (a.q || []).concat(b.q || []).forEach(function (x) { var key = x.t + '|' + x.b; if (!seen[key]) { seen[key] = 1; r.q.push(x); } });
    r.q.sort(function (m, n) { return m.t - n.t; }); r.q = r.q.slice(-600);
    var kk = Object.keys(r.d).sort(); while (kk.length > 120) delete r.d[kk.shift()];
    r.a = {}; var aa = a.a || {}, ab = b.a || {}, z; for (z in aa) r.a[z] = aa[z]; for (z in ab) r.a[z] = Math.min(r.a[z] || ab[z], ab[z]);
    return r;
  }
  function pushLog(force) {
    if (!tok()) return;
    try { var last = +localStorage.getItem('jam_sync_t') || 0; if (!force && Date.now() - last < 20000) return; localStorage.setItem('jam_sync_t', String(Date.now())); } catch (e) {}
    var x = ld();
    fetch(API + '/api/jam/sync', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tok() }, body: JSON.stringify({ d: x.d || {}, q: x.q || [], a: x.a || {} }) }).catch(function () {});
  }
  window.jamPull = function () {
    if (!tok()) return Promise.resolve();
    try { if (sessionStorage.getItem('jam_pull')) return Promise.resolve(); } catch (e) {}
    return fetch(API + '/api/jam/log', { headers: { Authorization: 'Bearer ' + tok() } }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (srv) { if (!srv) return; sv(merge(ld(), srv)); try { sessionStorage.setItem('jam_pull', '1'); } catch (e) {} pushLog(true); }).catch(function () {});
  };
  var o = ld(); o.d = o.d || {}; o.q = o.q || [];
  var t = day(), p = location.pathname, c = cat(p);
  if (c) {
    var D = o.d[t] = o.d[t] || { v: {}, p: [] };
    if (D.p.indexOf(p) < 0 && D.p.length < 80) { D.p.push(p); D.v[c] = (D.v[c] || 0) + 1; }
  }
  var keys = Object.keys(o.d).sort();
  while (keys.length > 120) delete o.d[keys.shift()];
  sv(o);
  if (tok()) window.jamPull().then(function () { pushLog(false); });
  window.jamHabit = function () {   // 습관형 목표: 오늘 했다고 체크(하루 1번)
    var x = ld(); x.d = x.d || {};
    var E = x.d[t] = x.d[t] || { v: {}, p: [] };
    if (E.v.habit) return false;
    E.v.habit = 1; sv(x); pushLog(true);
    try { window.dispatchEvent(new Event('jam:update')); } catch (e) {}
    return true;
  };
  window.jamQ = function (bank, n, score) {
    var x = ld(); x.q = x.q || []; x.d = x.d || {};
    x.q.push({ t: Date.now(), b: bank, n: n, s: score });
    if (x.q.length > 600) x.q.splice(0, x.q.length - 600);
    var E = x.d[t] = x.d[t] || { v: {}, p: [] };
    E.v.quiz = (E.v.quiz || 0) + n;
    sv(x); pushLog(true);
    try { window.dispatchEvent(new Event('jam:update')); } catch (e) {}
  };
})();
