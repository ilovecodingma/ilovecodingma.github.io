// 운동 사이클 뽑기 · 실행 · 완료 체크 · 기록 (2026-10-26). 모든 기록은 이 기기(localStorage)에만 저장하고 서버로 보내지 않는다.
// 운동 목록은 /assets/diet/workouts.json 한 곳에서 읽는다. 세트·횟수가 「공식 확인」이면 숫자를 지어내지 않고 안내 문구를 보여 준다. 칼로리는 표시하지 않는다.
(function () {
  var ROOT = document.getElementById('dtw'); if (!ROOT) return;
  var KEY = 'jupjup_diet_v1';
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var load = function () { try { var v = JSON.parse(localStorage.getItem(KEY) || 'null'); if (v && v.log) return v; } catch (e) {} return { log: {}, goal: 3 }; };
  var save = function () { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
  var S = load(), W = [], view = 'make', plan = null, run = null, tm = null, wake = null, voiceOn = true;
  var today = function () { return new Date(Date.now() + 9 * 36e5).toISOString().slice(0, 10); };
  var DIS = '참고용이에요. 통증이 있거나 어지러우면 바로 멈추고, 몸 상태에 맞게 강도를 조절하세요. 질환이 있거나 임신 중이면 시작 전에 전문가와 상의하세요.';
  var PRIV = '기록은 이 기기의 브라우저에만 저장되고 서버로 전송되지 않아요. 브라우저 데이터를 지우면 기록도 사라져요.';
  var NOTE_SET = '권장 횟수 미확인 — 본인 체력에 맞게 하세요(타이머는 30초 기준이에요).';

  // ---------- 음성 안내(요리 모드와 같은 방식: 브라우저 내장 TTS) ----------
  var TTS = 'speechSynthesis' in window, voice = null;
  function pick() { if (!TTS) return; var vs = speechSynthesis.getVoices() || []; voice = vs.filter(function (v) { return /ko/i.test(v.lang); })[0] || null; }
  if (TTS) { pick(); if (speechSynthesis.addEventListener) speechSynthesis.addEventListener('voiceschanged', pick); }
  function say(t) { if (!TTS || !voiceOn) return; try { speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance(t); u.lang = 'ko-KR'; if (voice) u.voice = voice; u.rate = 1; speechSynthesis.speak(u); } catch (e) {} }

  // ---------- 사이클 뽑기 ----------
  var WARM = ['목 스트레칭', '어깨 스트레칭', '팔벌려뛰기', '제자리 무릎 올리기'];
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function make(min, part, place) {
    var byPlace = function (w) { return place === '집' ? w.place === '집' : true; };
    var all = W.filter(byPlace);
    var warmPool = all.filter(function (w) { return WARM.indexOf(w.name) >= 0; });
    var warm = shuffle(warmPool).slice(0, 2);
    var used = warm.map(function (w) { return w.id; });
    var stretches = all.filter(function (w) { return w.part === '스트레칭' && WARM.indexOf(w.name) < 0; });
    var mainPool = all.filter(function (w) { return used.indexOf(w.id) < 0 && (part === '스트레칭' ? w.part === '스트레칭' && WARM.indexOf(w.name) < 0 : part === '전신' ? w.part !== '스트레칭' : w.part === part); });
    var n = { 10: 3, 20: 4, 30: 5 }[min] || 3;
    var main = shuffle(mainPool);
    if (place === '밖') { var out = main.filter(function (w) { return w.place === '밖'; }); if (out.length) main = out.slice(0, 1).concat(main.filter(function (w) { return out.indexOf(w) < 0; })); }
    main = main.slice(0, n);
    var mainIds = main.map(function (w) { return w.id; });
    var cool = shuffle(stretches.filter(function (w) { return mainIds.indexOf(w.id) < 0 && used.indexOf(w.id) < 0; })).slice(0, 2);
    var budget = Math.max(60, min * 60 - (warm.length + cool.length) * 30);
    var sets = main.length ? Math.max(1, Math.min(4, Math.round(budget / main.length / 45))) : 1;
    return { min: min, part: part, place: place, warm: warm, main: main, cool: cool, sets: sets };
  }
  function seq(p) {
    var out = [];
    var add = function (w, kind, sets) { for (var s = 1; s <= sets; s++) { out.push({ w: w, kind: kind, set: s, sets: sets, phase: 'work', sec: 30 }); out.push({ w: w, kind: kind, set: s, sets: sets, phase: 'rest', sec: 15 }); } };
    p.warm.forEach(function (w) { add(w, '워밍업', 1); });
    p.main.forEach(function (w) { add(w, '본운동', p.sets); });
    p.cool.forEach(function (w) { add(w, '쿨다운', 1); });
    if (out.length) out.pop();   // 마지막 휴식은 뺀다
    return out;
  }
  var CUT = { '스트레칭': 'o_dt_stretch', '하체': 'o_dt_mat', '복부': 'o_dt_mat', '상체': 'o_dt_dumbbell', '전신': 'o_dt_run' };
  var cutImg = function (name, cls, w) { return '<img class="dt-cut ' + (cls || '') + '" src="/assets/ruri/' + name + '.webp" width="' + (w || 150) + '" height="' + Math.round((w || 150) * 415 / 300) + '" alt="운동하는 루리" loading="lazy">'; };
  var setText = function (w) { return (w.sets === '공식 확인' || w.reps_or_sec === '공식 확인') ? '세트·횟수: 공식 안내를 확인하세요 · ' + NOTE_SET : '세트 ' + esc(w.sets) + ' · ' + esc(w.reps_or_sec); };

  // ---------- 화면 ----------
  function tabs() {
    return '<div class="dt-tabs" role="tablist"><button type="button" data-v="make" class="' + (view !== 'log' ? 'on' : '') + '">🏃 운동 뽑기</button><button type="button" data-v="log" class="' + (view === 'log' ? 'on' : '') + '">📅 기록</button></div>';
  }
  function foot() { return '<p class="dt-note">' + esc(DIS) + '</p><p class="dt-note">' + esc(PRIV) + '</p>'; }
  function render() {
    if (view === 'log') return paintLog();
    if (view === 'run') return paintRun();
    if (view === 'done') return paintDone();
    if (view === 'plan') return paintPlan();
    paintMake();
  }
  var sel = { min: 20, part: '전신', place: '집' };
  function chips(name, arr, cur) { return '<div class="dt-ch" data-k="' + name + '">' + arr.map(function (x) { return '<button type="button" data-v="' + esc(x[0]) + '" class="' + (String(cur) === String(x[0]) ? 'on' : '') + '">' + esc(x[1]) + '</button>'; }).join('') + '</div>'; }
  function paintMake() {
    ROOT.innerHTML = tabs() + '<section class="dt-card">' + cutImg('o_dt_stretch', 'dt-cut-r', 120) + '<h2>오늘은 얼마나 움직일까요?</h2><p class="dt-sub">시간·부위·장소를 고르면 워밍업 → 본운동 → 쿨다운을 무작위로 짜 드려요. 같은 운동이 연달아 나오지 않아요.</p>'
      + '<p class="dt-l">시간</p>' + chips('min', [[10, '10분'], [20, '20분'], [30, '30분']], sel.min)
      + '<p class="dt-l">부위</p>' + chips('part', [['전신', '전신'], ['하체', '하체'], ['상체', '상체'], ['복부', '복부'], ['스트레칭', '스트레칭']], sel.part)
      + '<p class="dt-l">장소</p>' + chips('place', [['집', '집'], ['밖', '밖']], sel.place)
      + '<button type="button" class="dt-go" id="dt-draw">🎲 운동 뽑기</button></section>' + todayBox() + foot();
    wireTabs();
    ROOT.querySelectorAll('.dt-ch').forEach(function (g) { g.onclick = function (e) { var b = e.target.closest('button'); if (!b) return; var k = g.getAttribute('data-k'); sel[k] = k === 'min' ? +b.getAttribute('data-v') : b.getAttribute('data-v'); paintMake(); }; });
    document.getElementById('dt-draw').onclick = function () { plan = make(sel.min, sel.part, sel.place); view = 'plan'; render(); };
  }
  function todayBox() {
    var d = S.log[today()]; if (!d) return '';
    return '<p class="dt-today">✅ 오늘 이미 ' + d.cycles + '번 완료했어요 · 누적 ' + d.minutes + '분. 더 하고 싶다면 다시 뽑아도 돼요.</p>';
  }
  function liHtml(arr, label) {
    if (!arr.length) return '';
    return '<h3>' + label + '</h3><ol class="dt-li">' + arr.map(function (w) { return '<li><b>' + esc(w.name) + '</b> <small>' + esc(w.part) + ' · ' + esc(w.place) + '</small></li>'; }).join('') + '</ol>';
  }
  function paintPlan() {
    var enough = plan.main.length >= 1;
    ROOT.innerHTML = tabs() + '<section class="dt-card">' + cutImg('o_dt_dumbbell', 'dt-cut-r', 110) + '<h2>오늘의 운동 사이클 <small>' + plan.min + '분 · ' + esc(plan.part) + ' · ' + esc(plan.place) + '</small></h2>'
      + (enough ? liHtml(plan.warm, '워밍업') + liHtml(plan.main, '본운동 (각 ' + plan.sets + '세트)') + liHtml(plan.cool, '쿨다운') : '<p>조건에 맞는 운동이 부족해요. 부위나 장소를 바꿔 다시 뽑아 보세요.</p>')
      + '<p class="dt-sub">동작은 30초 동안 하고 15초 쉬는 타이머로 진행해요. ' + esc(NOTE_SET) + '</p>'
      + '<div class="dt-row"><button type="button" class="dt-go" id="dt-start"' + (enough ? '' : ' disabled') + '>▶ 시작하기</button><button type="button" class="dt-2" id="dt-again">🎲 다시 뽑기</button><button type="button" class="dt-2" id="dt-back">← 조건 바꾸기</button></div></section>' + foot();
    wireTabs();
    document.getElementById('dt-again').onclick = function () { plan = make(plan.min, plan.part, plan.place); paintPlan(); };
    document.getElementById('dt-back').onclick = function () { view = 'make'; render(); };
    var st = document.getElementById('dt-start'); if (st) st.onclick = startRun;
  }

  // ---------- 실행 ----------
  function startRun() {
    run = { q: seq(plan), i: 0, left: 0, paused: false, done: {}, t0: Date.now() };
    if (!run.q.length) return;
    run.left = run.q[0].sec; view = 'run'; announce(); render(); lockScreen();
    clearInterval(tm); tm = setInterval(tick, 1000);
  }
  function lockScreen() { try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { wake = l; }).catch(function () {}); } catch (e) {} }
  function unlockScreen() { try { if (wake) wake.release(); } catch (e) {} wake = null; }
  function announce() {
    var s = run.q[run.i]; if (!s) return;
    if (s.phase === 'work') say(s.kind + ' ' + s.w.name + (s.sets > 1 ? ', ' + s.set + '세트' : '') + ' 시작');
    else { var nx = run.q[run.i + 1]; say('잠깐 쉬어요' + (nx && nx.set === 1 ? '. 다음은 ' + nx.w.name : '')); }
  }
  function tick() {
    if (!run || run.paused) return;
    run.left--; var s = run.q[run.i];
    if (run.left === 3 && s.phase === 'work') say('삼, 이, 일');
    if (run.left <= 0) {
      if (s.phase === 'work' && s.set === s.sets) run.done[s.w.id] = true;   // 마지막 세트까지 끝낸 운동만 체크
      next();
    } else { var el = document.getElementById('dt-t'); if (el) el.textContent = fmt(run.left); }
  }
  function next() {
    run.i++;
    if (run.i >= run.q.length) { finish(); return; }
    run.left = run.q[run.i].sec; announce(); paintRun();
  }
  var fmt = function (n) { return Math.floor(n / 60) + ':' + ('0' + (n % 60)).slice(-2); };
  function paintRun() {
    var s = run.q[run.i], w = s.w, total = run.q.length;
    var order = [].concat(plan.warm, plan.main, plan.cool);
    ROOT.innerHTML = '<section class="dt-card dt-run ' + s.phase + '">' + cutImg(s.phase === 'work' ? (CUT[w.part] || 'o_dt_run') : 'o_dt_water', 'dt-cut-r', 96) + '<p class="dt-kind">' + esc(s.kind) + ' · ' + (s.phase === 'work' ? '운동 중' : '휴식') + ' <small>' + (run.i + 1) + '/' + total + '</small></p>'
      + '<h2>' + esc(s.phase === 'work' ? w.name : '쉬는 시간') + '</h2>'
      + '<div class="dt-timer" id="dt-t" aria-live="off">' + fmt(run.left) + '</div>'
      + (s.sets > 1 && s.phase === 'work' ? '<p class="dt-setno">세트 ' + s.set + ' / ' + s.sets + '</p>' : '')
      + '<div class="dt-bar"><i style="width:' + Math.round(run.i / total * 100) + '%"></i></div>'
      + (s.phase === 'work' ? '<ol class="dt-steps">' + w.steps.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ol><p class="dt-caution">⚠ ' + esc(w.caution) + '</p><p class="dt-sub">' + setText(w) + '</p>'
        : '<p class="dt-sub">다음: <b>' + esc((run.q[run.i + 1] || {}).w ? run.q[run.i + 1].w.name : '마무리') + '</b></p>')
      + '<div class="dt-row"><button type="button" class="dt-2" id="dt-pause">' + (run.paused ? '▶ 계속' : '⏸ 일시정지') + '</button><button type="button" class="dt-2" id="dt-skip">⏭ 건너뛰기</button><button type="button" class="dt-2" id="dt-voice">' + (voiceOn ? '🔊 음성 켜짐' : '🔇 음성 꺼짐') + '</button><button type="button" class="dt-2" id="dt-end">■ 그만하기</button></div>'
      + '<ul class="dt-chk">' + order.map(function (x) { return '<li class="' + (run.done[x.id] ? 'ok' : '') + '">' + (run.done[x.id] ? '✅ ' : '▫️ ') + esc(x.name) + '</li>'; }).join('') + '</ul></section>' + foot();
    document.getElementById('dt-pause').onclick = function () { run.paused = !run.paused; if (run.paused) { try { speechSynthesis.cancel(); } catch (e) {} } paintRun(); };
    document.getElementById('dt-skip').onclick = function () { next(); };
    document.getElementById('dt-voice').onclick = function () { voiceOn = !voiceOn; if (!voiceOn) { try { speechSynthesis.cancel(); } catch (e) {} } paintRun(); };
    document.getElementById('dt-end').onclick = function () { finish(true); };
  }
  function finish(early) {
    clearInterval(tm); unlockScreen(); try { speechSynthesis.cancel(); } catch (e) {}
    var mins = Math.max(1, Math.round((Date.now() - run.t0) / 6e4)), doneN = Object.keys(run.done).length;
    run.mins = mins; run.early = !!early; run.doneN = doneN;
    if (doneN > 0) {   // 한 가지라도 끝까지 한 날만 기록에 남긴다
      var k = today(), d = S.log[k] || { cycles: 0, minutes: 0, items: [] };
      d.cycles += 1; d.minutes += mins; d.items = d.items.concat(Object.keys(run.done)).slice(-60); S.log[k] = d; save();
    }
    view = 'done'; render();
    if (doneN > 0 && !early) say('오늘 운동 끝! 수고했어요');
  }
  function paintDone() {
    var order = [].concat(plan.warm, plan.main, plan.cool), ok = run.doneN > 0;
    ROOT.innerHTML = '<section class="dt-card dt-done"><div class="say"><img src="/assets/ruri/' + (ok && !run.early ? 'thumbsup' : 'smile') + '_s.webp" width="56" height="77" alt="루리" loading="lazy"><div class="bub"><b>루리</b><div>'
      + (ok ? (run.early ? '여기까지 해낸 것도 충분해요. 한 가지라도 끝까지 한 건 오늘 기록에 남겨 뒀어요.' : '오늘 사이클 완주! ' + run.mins + '분 동안 움직였어요. 물 한 잔 마시고 쉬어 가요.') : '아직 끝낸 운동이 없어서 기록에는 남기지 않았어요. 다음에 편할 때 다시 해 봐요.') + '</div></div></div>'
      + (ok ? '<p class="dt-stamp">🎖️ ' + today() + ' 완료</p>' : '')
      + '<ul class="dt-chk">' + order.map(function (x) { return '<li class="' + (run.done[x.id] ? 'ok' : '') + '">' + (run.done[x.id] ? '✅ ' : '▫️ ') + esc(x.name) + '</li>'; }).join('') + '</ul>'
      + '<div class="dt-row"><button type="button" class="dt-go" id="dt-new">🎲 한 번 더 뽑기</button><button type="button" class="dt-2" id="dt-log">📅 기록 보기</button></div></section>' + foot();
    document.getElementById('dt-new').onclick = function () { view = 'make'; render(); };
    document.getElementById('dt-log').onclick = function () { view = 'log'; render(); };
  }

  // ---------- 기록 ----------
  var ymd = function (d) { return d.toISOString().slice(0, 10); };
  function paintLog() {
    var now = new Date(Date.now() + 9 * 36e5), y = now.getUTCFullYear(), m = now.getUTCMonth();
    var first = new Date(Date.UTC(y, m, 1)), days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate(), lead = first.getUTCDay();
    var cells = ''; for (var i = 0; i < lead; i++) cells += '<span></span>';
    for (var d = 1; d <= days; d++) { var k = ymd(new Date(Date.UTC(y, m, d))), on = !!S.log[k], isT = k === today(); cells += '<span class="' + (on ? 'on' : '') + (isT ? ' t' : '') + '" title="' + k + '">' + (on ? '✔' : d) + '</span>'; }
    // 연속 일수: 오늘(없으면 어제)부터 거꾸로
    var streak = 0, c = new Date(Date.now() + 9 * 36e5); if (!S.log[ymd(c)]) c = new Date(c.getTime() - 864e5);
    while (S.log[ymd(c)]) { streak++; c = new Date(c.getTime() - 864e5); }
    // 이번 주(월~일) 달성 일수·운동 시간
    var dow = (now.getUTCDay() + 6) % 7, wk = 0, wmin = 0;
    for (var j = 0; j <= dow; j++) { var kk = ymd(new Date(now.getTime() - j * 864e5)); if (S.log[kk]) { wk++; wmin += S.log[kk].minutes; } }
    var goal = S.goal || 3, pct = Math.min(100, Math.round(wk / goal * 100));
    var tot = Object.keys(S.log).reduce(function (a, k) { return a + S.log[k].cycles; }, 0);
    ROOT.innerHTML = tabs() + '<section class="dt-card">' + cutImg('o_dt_scale', 'dt-cut-r', 96) + '<h2>' + y + '년 ' + (m + 1) + '월 운동 기록</h2><div class="dt-cal"><b>일</b><b>월</b><b>화</b><b>수</b><b>목</b><b>금</b><b>토</b>' + cells + '</div>'
      + '<div class="dt-stats"><div><small>연속 일수</small><b>' + streak + '일</b></div><div><small>이번 주 운동한 날</small><b>' + wk + '일</b></div><div><small>이번 주 운동 시간</small><b>' + wmin + '분</b></div><div><small>누적 사이클</small><b>' + tot + '회</b></div></div>'
      + '<p class="dt-l">주간 목표 <select id="dt-goal" aria-label="주간 목표 횟수">' + [1, 2, 3, 4, 5, 6, 7].map(function (n) { return '<option value="' + n + '"' + (n === goal ? ' selected' : '') + '>주 ' + n + '회</option>'; }).join('') + '</select></p>'
      + '<div class="dt-bar big"><i style="width:' + pct + '%"></i></div><p class="dt-sub">이번 주 달성률 <b>' + pct + '%</b> (' + wk + '/' + goal + '일)</p>'
      + '<p class="dt-sub">기록은 한 가지 이상 끝까지 한 날만 남아요. 알림 기능은 아직 없어요.</p></section>' + foot();
    wireTabs();
    document.getElementById('dt-goal').onchange = function (e) { S.goal = +e.target.value; save(); paintLog(); };
  }
  function wireTabs() {
    ROOT.querySelectorAll('.dt-tabs button').forEach(function (b) { b.onclick = function () { view = b.getAttribute('data-v') === 'log' ? 'log' : 'make'; render(); }; });
  }

  fetch('/assets/diet/workouts.json?v=1').then(function (r) { return r.json(); }).then(function (d) { W = d; if (location.hash === '#log') view = 'log'; render(); })
    .catch(function () { ROOT.innerHTML = '<p class="dt-note">운동 목록을 불러오지 못했어요. 새로고침해 주세요.</p>'; });
  addEventListener('pagehide', function () { unlockScreen(); });
})();
