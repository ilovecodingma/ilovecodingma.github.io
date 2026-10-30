/* 루리의 놀이터 공통: 저장·토스트·공유·GA·방문 기록 */
(function () {
  var P = window.PLAY = {};
  P.$ = function (id) { return document.getElementById(id); };
  P.ga = function (n, p) { try { if (window.gtag && location.hostname === 'sungprofile.cloud') gtag('event', n, p || {}); } catch (e) {} };
  P.load = function (k, d) { try { var v = localStorage.getItem('play_' + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  P.save = function (k, v) { try { localStorage.setItem('play_' + k, JSON.stringify(v)); } catch (e) {} };
  P.toast = function (m, ms) {
    var t = P.$('toast'); if (!t) { t = document.createElement('div'); t.id = 'toast'; document.body.appendChild(t); }
    t.textContent = m; t.classList.add('on'); clearTimeout(P.toast.h); P.toast.h = setTimeout(function () { t.classList.remove('on'); }, ms || 2000);
  };
  P.vib = function (n) { try { if (navigator.vibrate) navigator.vibrate(n || 15); } catch (e) {} };
  P.rnd = function (n) { return Math.floor(Math.random() * n); };
  P.fmt = function (n) { n = Math.floor(n); return n >= 1e8 ? (n / 1e8).toFixed(1) + '억' : n >= 1e4 ? (n / 1e4).toFixed(1) + '만' : String(n); };
  P.share = function (text, game) {
    P.ga('play_share', { game: game });
    var url = location.origin + location.pathname + '?utm_source=share';
    var d = { title: document.title, text: text, url: url };
    try {
      if (navigator.share) return navigator.share(d);
      navigator.clipboard.writeText(text + ' ' + url); P.toast('링크를 복사했어요. 붙여넣어 공유하세요');
    } catch (e) {}
  };
  // 하루 접속 연속일(재방문 장치): 게임 공통
  P.streak = function () {
    var s = P.load('streak', { last: '', n: 0 }), t = new Date(), d = t.getFullYear() + '-' + (t.getMonth() + 1) + '-' + t.getDate();
    if (s.last !== d) {
      var y = new Date(t.getTime() - 864e5), yd = y.getFullYear() + '-' + (y.getMonth() + 1) + '-' + y.getDate();
      s.n = s.last === yd ? s.n + 1 : 1; s.last = d; s.fresh = true; P.save('streak', s);
    } else s.fresh = false;
    return s;
  };
  // 방문 기록(운영 도메인만): 사이트 공통 /api/hit 형식
  (function () {
    if (location.hostname !== 'sungprofile.cloud') return;
    try {
      var q = new URLSearchParams(location.search);
      if (q.get('nohit') === '1') localStorage.setItem('jupjup_nohit', '1');
      if (q.get('nohit') === '0') localStorage.removeItem('jupjup_nohit');
      if (localStorage.getItem('jupjup_nohit') === '1') return;
      var v = localStorage.getItem('jupjup_vid');
      if (!/^[0-9a-f]{16}$/.test(v || '')) { v = [].map.call(crypto.getRandomValues(new Uint8Array(8)), function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); localStorage.setItem('jupjup_vid', v); }
      setTimeout(function () {
        fetch('https://jupjup-api.sung2011103.workers.dev/api/hit', { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ p: location.pathname, r: document.referrer, s: (q.get('src') || (q.get('utm_source') || '').replace(/[^a-z0-9_-]/gi, '')).slice(0, 16), c: (q.get('utm_campaign') || '').replace(/[^a-z0-9_-]/gi, '').slice(0, 40), v: v }) }).catch(function () {});
      }, 400);
    } catch (e) {}
  })();
  P.ga('play_open', { path: location.pathname });
})();
