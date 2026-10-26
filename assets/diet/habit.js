// 다이어트 앱 습관화 (2026-10-27): 연속 달성 일수 · 이번 주 7칸 · 홈 화면 설치 안내 · 익명 재방문 지표.
// 기록은 이 기기(localStorage)에만 남고 서버로 보내지 않는다. 분석 도구(GA)로는 「며칠 만에 다시 왔는지」 구간 하나만 보낸다(날짜·몸 데이터·기기 식별값 없음).
(function () {
  var KEY = 'jupjup_habit_v1', DIS_KEY = 'jupjup_install_dismiss';
  var kst = function (add) { return new Date(Date.now() + 9 * 36e5 + (add || 0) * 864e5); };
  var ymd = function (d) { return d.toISOString().slice(0, 10); };
  var load = function () { try { var v = JSON.parse(localStorage.getItem(KEY) || 'null'); if (v && v.days) return v; } catch (e) {} return { first: null, days: {}, sent: {} }; };
  var H = load();
  var save = function () { try { localStorage.setItem(KEY, JSON.stringify(H)); } catch (e) {} };
  var ga = function (n, p) { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  var dayDiff = function (a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 864e5); };

  // 재방문 지표: 첫 방문일은 이 기기에만 저장. 오늘 처음 열었을 때 「첫 방문 후 며칠째」 구간만 이벤트로 보낸다.
  (function visit() {
    var t = ymd(kst());
    if (!H.first) { H.first = t; H.sent = {}; save(); return; }
    if (H.sent.v === t) return;
    var n = dayDiff(H.first, t); H.sent.v = t; save();
    if (n >= 1) ga('diet_return', { days_since_first: n === 1 ? 'd1' : n <= 3 ? 'd2_3' : n <= 7 ? 'd4_7' : n <= 30 ? 'd8_30' : 'd31p' });
  })();

  function mark(kind) {
    var t = ymd(kst()); H.days[t] = H.days[t] || {};
    H.days[t][kind] = (H.days[t][kind] || 0) + 1;
    var keys = Object.keys(H.days).sort(); if (keys.length > 400) keys.slice(0, keys.length - 400).forEach(function (k) { delete H.days[k]; });
    save();
    if (!H.sent.done || H.sent.done !== t) { H.sent.done = t; save(); ga('diet_done', { kind: kind }); }
  }
  // 운동 기록(jupjup_diet_v1.log)도 함께 읽어, 이 기능 이전 기록도 연속 일수에 반영한다.
  function legacy() {
    try { var v = JSON.parse(localStorage.getItem('jupjup_diet_v1') || 'null'); return (v && v.log) || {}; } catch (e) { return {}; }
  }
  function done(k) { var l = legacy(); return !!(H.days[k] || l[k]); }
  function streak() {
    var c = kst(), n = 0; if (!done(ymd(c))) c = new Date(c.getTime() - 864e5);
    while (done(ymd(c))) { n++; c = new Date(c.getTime() - 864e5); }
    return n;
  }
  function week() {
    var now = kst(), dow = (now.getUTCDay() + 6) % 7, out = [], names = ['월', '화', '수', '목', '금', '토', '일'];
    for (var i = 0; i < 7; i++) { var d = new Date(now.getTime() + (i - dow) * 864e5), k = ymd(d); out.push({ n: names[i], k: k, on: done(k), t: i === dow, fut: i > dow }); }
    return out;
  }
  var dp = null;
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); dp = e; var b = document.getElementById('hb-inst'); if (b) b.hidden = false; });
  var standalone = function () { return (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; };
  var ios = function () { return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream; };
  var dismissed = function () { try { return localStorage.getItem(DIS_KEY) === '1'; } catch (e) { return false; } };

  function card() {
    var s = streak(), w = week(), wn = w.filter(function (x) { return x.on; }).length, todayOn = w.some(function (x) { return x.t && x.on; });
    var head = s > 0 ? '🔥 <b>' + s + '일 연속</b> 달성 중' : '오늘 첫 기록을 남겨 볼까요?';
    var sub = todayOn ? '오늘 기록 완료! 내일도 이어 가요.' : (s > 0 ? '오늘 하나만 하면 ' + (s + 1) + '일 연속이 돼요.' : '운동 한 번 또는 식단표 끼니 체크 하나면 돼요.');
    var cells = w.map(function (x) { return '<span class="hb-d' + (x.on ? ' on' : '') + (x.t ? ' t' : '') + (x.fut ? ' f' : '') + '" title="' + x.k + '"><small>' + x.n + '</small><i>' + (x.on ? '✔' : '') + '</i></span>'; }).join('');
    var inst = '';
    if (!standalone() && !dismissed()) {
      inst = '<div class="hb-inst"><button type="button" id="hb-inst" class="dt-2"' + (ios() ? ' hidden' : ' hidden') + '>📲 홈 화면에 추가</button>'
        + (ios() ? '<small id="hb-ios">아이폰은 공유 버튼 → 「홈 화면에 추가」를 누르면 앱처럼 열려요.</small>' : '')
        + '<button type="button" id="hb-x" class="hb-x" aria-label="설치 안내 닫기">닫기</button></div>';
    }
    return '<section class="dt-card hb"><div class="hb-top"><div><div class="hb-h">' + head + '</div><div class="hb-s">' + sub + '</div></div><div class="hb-wk"><b>' + wn + '</b>/7<small>이번 주</small></div></div>'
      + '<div class="hb-week">' + cells + '</div>'
      + inst
      + '<p class="dt-note">기록은 이 기기에만 저장돼요. 알림은 <a href="/app/">앱 알림 설정</a>에서 켤 수 있어요.</p></section>';
  }
  function wire(root) {
    var b = root.querySelector('#hb-inst'), x = root.querySelector('#hb-x');
    if (b) { b.hidden = !dp; b.onclick = function () { if (!dp) return; dp.prompt(); dp.userChoice.then(function (r) { ga('diet_install', { r: r && r.outcome }); dp = null; b.hidden = true; }); }; }
    if (x) x.onclick = function () { try { localStorage.setItem(DIS_KEY, '1'); } catch (e) {} var c = root.querySelector('.hb-inst'); if (c) c.remove(); };
  }
  window.JHabit = { mark: mark, streak: streak, card: card, wire: wire };
})();
