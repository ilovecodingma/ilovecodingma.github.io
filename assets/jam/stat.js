/* 상태창 + 가입 후 설정(직업→목표→목표일, 전부 객관식) + 목표 달성 플랜 + 헬조선 생존 확률.
   기록: jam_act(기기 안) / 프로필: 서버 user_prefs(job·goal·gdate·gstart) / 템플릿: goals.json / 문구: lines.json(매일 갱신).
   대상: <div id="jam-stat"></div> */
(function () {
  'use strict';
  var box = document.getElementById('jam-stat'); if (!box) return;
  function run() {
  var API = (document.body && document.body.dataset.api) || 'https://jupjup-api.sung2011103.workers.dev';
  var now = new Date(), i;
  function ymd(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function pd(s) { var m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(s || ''); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; }
  function dayDiff(a, b) { return Math.round((b - a) / 864e5); }
  var DEMO = window.JAM_DEMO || null;
  function tok() { if (DEMO) return 'demo'; try { return localStorage.getItem('jupjup_tok') || ''; } catch (e) { return ''; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function call(path, body) {
    if (DEMO) return Promise.resolve(path === '/api/me' ? { prefs: DEMO.prefs || {} } : { ok: true });
    return fetch(API + path, { method: body ? 'POST' : 'GET', headers: Object.assign({ 'Content-Type': 'application/json' }, tok() ? { Authorization: 'Bearer ' + tok() } : {}), body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || '실패'); return d; }); });
  }
  function jget(u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }

  // ── 활동 기록
  var o = {}; try { o = JSON.parse(localStorage.getItem('jam_act') || '{}') || {}; } catch (e) {}
  var D = o.d || {}, Q = o.q || [];
  var days30 = []; for (i = 0; i < 30; i++) { var dd = new Date(now); dd.setDate(now.getDate() - i); days30.push(ymd(dd)); }
  function sum() { var ks = arguments, n = 0; days30.forEach(function (d) { if (D[d]) for (var j = 0; j < ks.length; j++) n += D[d].v[ks[j]] || 0; }); return n; }
  function act(d) { return D[d] && (D[d].p.length || D[d].v.quiz || D[d].v.habit); }
  var active = days30.filter(act), streak = 0;
  for (i = 0; i < 30; i++) { if (act(days30[i])) streak++; else if (i > 0) break; }
  var cut = Date.now() - 30 * 864e5, q30 = Q.filter(function (x) { return x.t >= cut; });
  var solved = q30.reduce(function (a, x) { return a + x.n; }, 0), right = q30.reduce(function (a, x) { return a + x.s; }, 0), acc = solved ? right / solved : 0;
  function cl(v) { return Math.max(0, Math.min(100, Math.round(v))); }
  var S = [
    { k: '지력', v: cl(acc * 40 + Math.min(solved / 150, 1) * 40 + Math.min(sum('dev', 'wiki') / 20, 1) * 20), to: '/exam/bank/', quest: '문제 10개 풀어' },
    { k: '끈기', v: cl(Math.min(streak / 10, 1) * 60 + active.length / 30 * 40), to: '/', quest: '오늘 도장 찍어' },
    { k: '스펙', v: cl(Math.min(sum('exam', 'spec') / 25, 1) * 100), to: '/exam/', quest: '시험 일정이나 봐' },
    { k: '생활력', v: cl(Math.min(sum('money') / 15, 1) * 100), to: '/apply/', quest: '받을 돈이나 확인해' },
    { k: '눈치', v: cl(Math.min(sum('issue') / 15, 1) * 100), to: '/issue/', quest: '세상 돌아가는 건 알아라' },
    { k: '체력', v: cl(Math.min(sum('body') / 10, 1) * 100), to: '/diet/', quest: '밥이나 챙겨 먹어' }
  ];
  var xp = solved * 2 + right * 3 + sum('exam', 'spec', 'money', 'issue', 'body', 'dev', 'wiki') + streak * 5 + sum('habit') * 4;
  var lv = Math.max(1, Math.floor(Math.sqrt(xp / 4)) + 1), nxt = lv * lv * 4, cur = (lv - 1) * (lv - 1) * 4, gain = Math.round((xp - cur) * 100 / Math.max(1, nxt - cur));
  var byHigh = S.slice().sort(function (a, b) { return b.v - a.v; }), byLow = S.slice().reverse().sort(function (a, b) { return a.v - b.v; });

  var G = null, L = null, X = null, P = null, loggedIn = !!tok();
  try { if (loggedIn && !DEMO) localStorage.setItem('jam_seen', '1'); } catch (e) {}
  function lsP() { try { return JSON.parse(localStorage.getItem('jam_prof') || 'null'); } catch (e) { return null; } }
  var TITLE = { zero: '아직 아무것도 안 한 자', low: '잠이 오는 자', mid: '근근이 버티는 자', good: '그나마 사람 구실 하는 자', high: '살아남을 것 같은 자', max: '헬조선 졸업반' };
  var IMG = { zero: 'wrong3_1', low: 'wrong3_2', mid: 'hero_1', good: 'dday_1', high: 'perfect_1', max: 'perfect_2' };
  var DEF = {
    zero: ['기록이 없다. 니 헬조선 생존 확률 {p}%. 일단 하나라도 해라.'], low: ['{p}%. 이 점수로 취직하겠냐?', '{p}%다. 남들은 이미 뭐 땄다더라. {low}부터 올려라.'],
    mid: ['{p}%. {low}이 발목 잡는다. 그것부터 해라.'], good: ['{p}%. 그래도 {high}은 봐줄 만하다. 나머지는 왜 그 모양이냐.'],
    high: ['{p}%. 니가? 이 정도라고? 방심하지 마라.'], max: ['{p}%. 인정은 안 해. 다음 달에도 이러는지 보자.']
  };

  // ── 목표 찾기: 시험 목표('exam:<계열>')는 시험 데이터로 플랜을 즉석에서 짠다
  function goalOf(id) {
    if (/^exam:/.test(id || '')) {
      var f = X && X.fams.filter(function (x) { return 'exam:' + x.k === id; })[0]; if (!f) return null;
      var u = f.banks.length ? '/exam/bank/' + f.banks[0] + '/' : '/exam/bank/';
      return { id: id, name: f.name + ' 시험', phases: [
        { name: '개념 잡기', share: .35, tasks: [{ t: '문제 5개 풀고 풀이를 읽어라', cat: 'bank', qty: 5, url: u }, { t: '시험 일정부터 확인해라', cat: 'exam', qty: 1, url: '/exam/' }] },
        { name: '문제 풀이', share: .4, tasks: [{ t: '문제 15개 풀어라. 틀린 건 다시', cat: 'bank', qty: 15, url: u }] },
        { name: '실전 감각', share: .25, tasks: [{ t: '시간제로 문제 25개 풀어라', cat: 'bank', qty: 25, url: u }] }] };
    }
    return G.goals.filter(function (g) { return g.id === id; })[0] || null;
  }

  // ── 플랜 계산
  function planOf() {
    if (!P || !G) return null;
    var goal = goalOf(P.goal), job = G.jobs.filter(function (j) { return j.id === P.job; })[0];
    var end = pd(P.gdate), st = pd(P.gstart) || now;
    if (!goal || !job || !end) return null;
    var total = Math.max(1, dayDiff(st, end)), left = dayDiff(new Date(now.getFullYear(), now.getMonth(), now.getDate()), end);
    function phaseAt(d) {
      var f = Math.max(0, Math.min(.9999, dayDiff(st, d) / total)), acc2 = 0;
      for (var k = 0; k < goal.phases.length; k++) { acc2 += goal.phases[k].share; if (f < acc2) return { ph: goal.phases[k], idx: k }; }
      return { ph: goal.phases[goal.phases.length - 1], idx: goal.phases.length - 1 };
    }
    function done(d, t) { var v = D[ymd(d)]; if (!v) return 0; var n = t.cat === 'bank' ? (v.v.quiz || 0) + (v.v.bank || 0) : (v.v[t.cat] || 0); return Math.min(1, n / Math.max(1, t.qty)); }
    var cur = phaseAt(now), tasks = cur.ph.tasks.map(function (t) { return { t: t, f: done(now, t) }; });
    var adh = 0, cnt = 0;
    for (var k = 1; k <= 14; k++) {
      var d = new Date(now); d.setDate(now.getDate() - k); if (d < st) break;
      var ts = phaseAt(d).ph.tasks, s = 0; ts.forEach(function (t) { s += done(d, t); }); adh += s / Math.max(1, ts.length); cnt++;
    }
    adh = cnt ? adh / cnt : 0;
    return { goal: goal, job: job, left: left, total: total, cur: cur, tasks: tasks, adh: adh, pct: Math.max(0, Math.min(100, Math.round((1 - left / total) * 100))), expired: left < 0 };
  }

  function compute() {
    var pl = planOf(), surv = null, tier = 'zero';
    if (pl && !pl.expired) {
      var R = 0, W = pl.job.w; S.forEach(function (s) { R += (W[s.k] || 1 / 6) * s.v; });
      var ready = 0.5 * R + 0.5 * pl.adh * 100, pen = Math.max(0, 0.6 - pl.adh) * (1 - Math.min(pl.left, 60) / 60) * 40;
      surv = Math.max(3, Math.min(97, Math.round(6 + 0.88 * ready - pen + Math.min(streak, 7) * 0.4)));
      tier = xp < 15 ? 'zero' : surv < 25 ? 'low' : surv < 45 ? 'mid' : surv < 65 ? 'good' : surv < 85 ? 'high' : 'max';
    }
    return { pl: pl, surv: surv, tier: tier };
  }

  // ── 화면
  function gaugeSvg(surv) {
    var C = 2 * Math.PI * 70, off = (C * (1 - (surv == null ? 0 : surv) / 100)).toFixed(1);
    return '<svg viewBox="0 0 180 180" width="180" height="180" role="img" aria-label="헬조선 생존 확률 ' + (surv == null ? '미정' : surv + '%') + '"><circle cx="90" cy="90" r="70" fill="none" stroke="#1b2140" stroke-width="14"/>'
      + '<circle cx="90" cy="90" r="70" fill="none" stroke="url(#jg)" stroke-width="14" stroke-dasharray="' + C.toFixed(1) + '" stroke-dashoffset="' + off + '" transform="rotate(-90 90 90)"/>'
      + '<defs><linearGradient id="jg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00f0ff"/><stop offset="1" stop-color="#ff2bd6"/></linearGradient></defs>'
      + '<text x="90" y="98" text-anchor="middle" font-size="' + (surv == null ? 36 : 42) + '" font-weight="900" fill="#fff" font-family="ui-monospace,Consolas,monospace">' + (surv == null ? '??' : surv) + '<tspan font-size="20">%</tspan></text>'
      + '<text x="90" y="122" text-anchor="middle" font-size="11" fill="#00f0ff" font-family="ui-monospace,Consolas,monospace">SURVIVAL RATE</text></svg>';
  }
  function radar() {
    var n = S.length, R = 92, cx = 130, cy = 120, pts = [], grid = '', lab = '', j;
    for (j = 0; j < n; j++) {
      var a = -Math.PI / 2 + j * 2 * Math.PI / n;
      pts.push((cx + Math.cos(a) * R * S[j].v / 100).toFixed(1) + ',' + (cy + Math.sin(a) * R * S[j].v / 100).toFixed(1));
      grid += '<line x1="' + cx + '" y1="' + cy + '" x2="' + (cx + Math.cos(a) * R).toFixed(1) + '" y2="' + (cy + Math.sin(a) * R).toFixed(1) + '" stroke="currentColor" stroke-opacity=".25"/>';
      lab += '<text x="' + (cx + Math.cos(a) * (R + 20)).toFixed(1) + '" y="' + (cy + Math.sin(a) * (R + 20) + 5).toFixed(1) + '" text-anchor="middle" font-size="14" fill="currentColor">' + S[j].k + '</text>';
    }
    var rings = [.33, .66, 1].map(function (f) { var p = []; for (var m = 0; m < n; m++) { var b = -Math.PI / 2 + m * 2 * Math.PI / n; p.push((cx + Math.cos(b) * R * f).toFixed(1) + ',' + (cy + Math.sin(b) * R * f).toFixed(1)); } return '<polygon points="' + p.join(' ') + '" fill="none" stroke="currentColor" stroke-opacity=".25"/>'; }).join('');
    return '<svg viewBox="0 0 260 245" role="img" aria-label="능력치 레이더" width="100%" style="max-width:300px;color:#d8fbff">' + rings + grid + '<polygon points="' + pts.join(' ') + '" fill="#ff2bd6" fill-opacity=".3" stroke="#00f0ff" stroke-width="2"/>' + lab + '</svg>';
  }
  function bars() {
    return S.map(function (s) { var c = '', k, on = Math.round(s.v / 10); for (k = 0; k < 10; k++) c += '<u' + (k < on ? ' class="on"' : '') + '></u>'; return '<div class="js-r"><span>' + s.k + '</span><i>' + c + '</i><em>' + s.v + '</em></div>'; }).join('');
  }

  function viewGuest() {
    box.innerHTML = '<section class="js js-lock"><div class="js-top"><div class="js-gauge">' + gaugeSvg(null) + '</div><div class="js-id"><small>// 헬조선 생존 확률</small><h2>??%</h2>'
      + '<p class="js-t">LV.' + lv + ' · 미등록</p><p class="js-say2">가입해야 목표를 정하고 생존 확률이 나온다. 가입 안 한 놈한테 알림도 안 간다.</p>'
      + '<p><a class="js-btn" href="/me/">가입하고 목표 정하기</a></p></div></div>'
      + '<div class="js-g"><div class="js-rad">' + radar() + '</div><div class="js-bars"><small class="js-sub">// 능력치 6 (활동 기록)</small>' + bars() + '</div></div></section>';
  }

  var wiz = { job: '', goal: '', gdate: '', fam: '' };
  var DATES = [['2주 안에', 14], ['한 달', 30], ['두 달', 60], ['석 달', 90], ['여섯 달', 180], ['1년', 365]];
  // ── 이세계 미연시: 루리가 말하고, 선택지로 직업·목표·기한을 고른다
  var INTRO = [
    ['눈 떴냐. 여기는 헬조선이다. 니는 방금 죽었다. 월급은 안 오르는데 월세만 올라서.', 'wrong3_2'],
    ['나는 루리. 니 전속 비서다. 살려 줄 테니 말 잘 들어라.', 'hero_1'],
    ['상태창부터 열자. …상태창 오픈.', 'dday_1']
  ];
  var VN_LINE = {
    1: ['일단 니 정체부터 불어라. 직업이 뭐냐.', 'hero_2'],
    2: ['목표 없이 살아남을 줄 알았냐? 하나 골라라. 우리가 준비한 시험도 있다.', 'dday_2'],
    r: ['시험이냐. 언제 보는데. 일정에 있으면 골라라.', 'timeout_1'],
    q: ['여기 없는 목표냐. 적어 봐라. 요청하면 내가 플랜을 새로 짠다. 최대 하루 걸린다.', 'study_2'],
    3: ['기한은 정해야 플랜이 나온다. 언제까지 할 거냐.', 'timeout_2']
  };
  function typeIn(el, txt) {
    var k = 0, t; el.textContent = '';
    function fin() { clearInterval(t); el.textContent = txt; el.onclick = null; }
    t = setInterval(function () { k += 2; el.textContent = txt.slice(0, k); if (k >= txt.length) fin(); }, 28);
    el.onclick = fin;
  }
  function vnFrame(img, line, inner, cls) {
    box.innerHTML = '<section class="js js-wiz js-vn ' + (cls || '') + '"><div class="js-vnbg"></div><img class="js-por" src="/assets/ruri/sc_' + img + '.webp" alt="" width="220">'
      + '<div class="js-dlg"><b class="js-nm">루리 <small>전속 서큐버스 비서</small></b><p class="js-tx"></p></div><div class="js-ch">' + inner + '</div><p class="js-msg" id="js-msg"></p></section>';
    typeIn(box.querySelector('.js-tx'), line);
  }
  function viewIntro(n) {
    var it = INTRO[n];
    vnFrame(it[1], it[0], '<button class="js-next" id="js-next">' + (n < INTRO.length - 1 ? '▶ 다음' : '▶ 상태창 열기') + '</button>', n === INTRO.length - 1 ? 'js-open' : '');
    document.getElementById('js-next').onclick = function () { if (n < INTRO.length - 1) viewIntro(n + 1); else viewWizard(1); };
  }
  function viewWizard(step) {
    if (step === 0) return viewIntro(0);
    var vn = VN_LINE[step], h = '';
    if (step === 1) {
      h = '<div class="js-opt">' + G.jobs.map(function (j) { return '<button data-job="' + j.id + '"' + (wiz.job === j.id ? ' class="on"' : '') + '>' + esc(j.name) + '</button>'; }).join('') + '</div>';
    } else if (step === 2) {
      var job = G.jobs.filter(function (j) { return j.id === wiz.job; })[0];
      h = '<p class="js-hd">우리가 준비한 시험</p><div class="js-opt">' + ((X && X.fams) || []).map(function (f) { return '<button data-fam="' + f.k + '">' + esc(f.name) + '</button>'; }).join('') + '</div>'
        + '<p class="js-hd">' + esc(job.name) + ' 목표</p><div class="js-opt js-col">' + job.goals.map(function (id) { var g = G.goals.filter(function (x) { return x.id === id; })[0]; return g ? '<button data-goal="' + g.id + '"><b>' + esc(g.name) + '</b><small>' + esc(g.desc) + '</small></button>' : ''; }).join('') + '</div>'
        + '<p class="js-hd">여기 없는 목표</p><div class="js-opt"><button class="js-req" data-req="1">+ 목표 추가 요청하기</button></div>'
        + '<p><button class="js-ghost" data-back="1">← 직업 다시</button></p>';
    } else if (step === 'r') {
      var f = X.fams.filter(function (x) { return x.k === wiz.fam; })[0];
      h = (f.exams.length ? '<div class="js-opt js-col">' + f.exams.map(function (e) { return '<button data-ed="' + e.date + '"><b>' + esc(e.name) + '</b><small>시험일 ' + e.date + (e.reg_end ? ' · 접수 마감 ' + e.reg_end : '') + '</small></button>'; }).join('') + '</div><p class="js-hd">일정에 없으면</p>' : '')
        + '<div class="js-opt"><button data-ed="">내가 날짜를 고른다</button></div><p><button class="js-ghost" data-back="2">← 목표 다시</button></p>';
    } else if (step === 'q') {
      h = '<div class="js-ask"><input id="js-rq" maxlength="40" placeholder="예: 정보처리기사 실기 합격"><button class="js-btn" id="js-rqgo">요청</button></div><p><button class="js-ghost" data-back="2">← 돌아가기</button></p>';
    } else {
      h = '<div class="js-opt">' + DATES.map(function (d) { var dt = new Date(now); dt.setDate(now.getDate() + d[1]); var v = ymd(dt); return '<button data-gdate="' + v + '"' + (wiz.gdate === v ? ' class="on"' : '') + '>' + d[0] + '<small>' + v + '</small></button>'; }).join('') + '</div>'
        + '<p><button class="js-ghost" data-back="2">← 목표 다시</button></p>';
    }
    vnFrame(vn[1], vn[0], h);
    box.querySelectorAll('[data-job]').forEach(function (b) { b.onclick = function () { wiz.job = b.dataset.job; wiz.goal = ''; viewWizard(2); }; });
    box.querySelectorAll('[data-goal]').forEach(function (b) { b.onclick = function () { wiz.goal = b.dataset.goal; viewWizard(3); }; });
    box.querySelectorAll('[data-fam]').forEach(function (b) { b.onclick = function () { wiz.fam = b.dataset.fam; wiz.goal = 'exam:' + b.dataset.fam; viewWizard('r'); }; });
    box.querySelectorAll('[data-ed]').forEach(function (b) { b.onclick = function () { if (b.dataset.ed) { wiz.gdate = b.dataset.ed; saveProfile(); } else viewWizard(3); }; });
    box.querySelectorAll('[data-gdate]').forEach(function (b) { b.onclick = function () { wiz.gdate = b.dataset.gdate; saveProfile(); }; });
    box.querySelectorAll('[data-req]').forEach(function (b) { b.onclick = function () { viewWizard('q'); }; });
    box.querySelectorAll('[data-back]').forEach(function (b) { b.onclick = function () { var v = b.dataset.back; viewWizard(v === '1' ? 1 : v === '2' ? 2 : v); }; });
    var go = document.getElementById('js-rqgo');
    if (go) go.onclick = function () {
      var t = (document.getElementById('js-rq').value || '').trim(), m = document.getElementById('js-msg');
      if (t.length < 2) { m.textContent = '두 글자는 써라.'; return; }
      go.disabled = true; m.textContent = '보내는 중이다…';
      call('/api/goal/req', { job: wiz.job, text: t }).then(function () { m.textContent = '접수했다. 최대 하루 안에 플랜을 세워서 목록에 넣어 둔다. 내일 다시 와라.'; }).catch(function (e) { go.disabled = false; m.textContent = (e.message || '실패') + ' 다시 눌러라.'; });
    };
  }
  function saveProfile() {
    var msg = document.getElementById('js-msg'); if (msg) msg.textContent = '저장 중이다…';
    var np = { job: wiz.job, goal: wiz.goal, gdate: wiz.gdate, gstart: ymd(now) };
    if (!/^\d{4}-\d\d-\d\d$/.test(np.gdate)) { if (msg) msg.textContent = '날짜가 이상하다.'; return; }
    call('/api/me').then(function (m) { var pf = Object.assign({}, m.prefs || {}, np); return call('/api/prefs', { data: pf }); })
      .then(function () { P = np; try { localStorage.setItem('jam_prof', JSON.stringify(np)); } catch (e) {} vnFrame('perfect_1', '좋아, 플랜 짰다. 도망치면 알림으로 쫓아간다.', '<button class="js-next" id="js-next">▶ 상태창 보기</button>', 'js-open'); document.getElementById('js-next').onclick = view; })
      .catch(function (e) { if (msg) msg.textContent = (e.message || '실패') + ' 다시 눌러라.'; });
  }

  function achHtml() {
    var A = window.JAM_ACH || [], got = {}; try { got = (JSON.parse(localStorage.getItem('jam_hud') || '{}').ach) || {}; } catch (e) {}
    if (!A.length) return '';
    return '<div class="js-ach"><b>// 업적 ' + A.filter(function (a) { return got[a.id]; }).length + '/' + A.length + '</b><ul>' + A.map(function (a) { return '<li class="' + (got[a.id] ? 'on' : '') + '" title="' + esc(a.d) + '"><i>' + (got[a.id] ? '★' : '☆') + '</i>' + esc(a.n) + '</li>'; }).join('') + '</ul></div>';
  }
  function view() {
    if (!loggedIn) return viewGuest();
    if (!P || !P.goal) return viewWizard(0);
    var c = compute(), pl = c.pl;
    if (!pl) return viewWizard(0);
    if (pl.expired) {
      var won = pl.adh >= 0.6;
      if (won) { try { localStorage.setItem('jam_ach_extra', JSON.stringify({ goal_done: 1 })); window.dispatchEvent(new Event('jam:update')); } catch (e) {} }
      box.innerHTML = '<section class="js ' + (won ? 'js-max' : 'js-low') + '"><h3>' + (won ? '목표 달성' : '기한이 지났다') + '</h3><p>' + esc(pl.goal.name) + (won ? ' — 플랜 이행 ' + Math.round(pl.adh * 100) + '%. 업적을 받았다. 인정은 하는데 칭찬은 안 한다.' : ' 목표일이 지났다. 플랜 이행 ' + Math.round(pl.adh * 100) + '%. 못 했네. 다시 정해라.') + '</p><p><button class="js-btn" id="js-reset">새 목표 정하기</button></p></section>'; document.getElementById('js-reset').onclick = function () { P = null; wiz = { job: '', goal: '', gdate: '', fam: '' }; viewWizard(1); }; return; }
    try { localStorage.setItem('jam_surv', JSON.stringify({ v: c.surv, d: ymd(now) })); window.dispatchEvent(new Event('jam:update')); } catch (e) {}
    var seed = parseInt(ymd(now).replace(/-/g, ''), 10), pool = (L && L.tier && L.tier[c.tier]) || DEF[c.tier];
    var line = pool[seed % pool.length].replace(/\{p\}/g, c.surv).replace(/\{low\}/g, byLow[0].k).replace(/\{high\}/g, byHigh[0].k);
    var ex = (L && L.stat && L.stat[byLow[0].k]) ? L.stat[byLow[0].k][seed % L.stat[byLow[0].k].length] : '';
    var tk = pl.tasks.map(function (x) {
      if (x.t.cat === 'habit') return '<li class="' + (x.f >= 1 ? 'ok' : '') + '"><span>' + (x.f >= 1 ? '✔' : '□') + '</span> ' + esc(x.t.t) + ' ' + (x.f >= 1 ? '<em class="js-done">오늘 했다</em>' : '<button class="js-chk" data-chk="1">했다 ▶ 체크인</button>') + '</li>';
      return '<li class="' + (x.f >= 1 ? 'ok' : '') + '"><span>' + (x.f >= 1 ? '✔' : '□') + '</span> <a href="' + esc(x.t.url || '/') + '">' + esc(x.t.t) + '</a></li>';
    }).join('');
    var allDone = pl.tasks.length && pl.tasks.every(function (x) { return x.f >= 1; });
    var phs = pl.goal.phases.map(function (p, k) { return '<span class="' + (k === pl.cur.idx ? 'on' : k < pl.cur.idx ? 'pass' : '') + '">' + esc(p.name) + '</span>'; }).join('');
    box.innerHTML = '<section class="js js-' + c.tier + '"><div class="js-top"><div class="js-gauge">' + gaugeSvg(c.surv) + '</div>'
      + '<div class="js-id"><small>// 헬조선 생존 확률</small><h2>' + c.surv + '%</h2><p class="js-t">' + esc(pl.job.name) + ' LV.' + lv + ' · ' + TITLE[c.tier] + '</p>'
      + '<div class="js-x"><i><b style="width:' + Math.max(2, Math.min(100, gain)) + '%"></b></i><small>NEXT LV ' + Math.max(0, nxt - xp) + ' XP</small></div></div></div>'
      + '<div class="js-goal"><small class="js-sub">// 목표</small><b>' + esc(pl.goal.name) + '</b><span>D-' + pl.left + ' · ' + P.gdate + '</span><i><b style="width:' + pl.pct + '%"></b></i><div class="js-ph">' + phs + '</div></div>'
      + '<p class="js-say"><img src="/assets/ruri/sc_' + IMG[c.tier] + '.webp" alt="" width="64" height="85"><span>' + line + (ex ? '<br><small>' + ex + '</small>' : '') + '</span></p>'
      + '<div class="js-q"><b>// 오늘 할 일 — ' + esc(pl.cur.ph.name) + '</b><ul class="js-tk">' + tk + '</ul>' + (allDone ? '<p class="js-ok">오늘 치는 끝냈다. 내일도 하는지 보자.</p>' : '') + '</div>'
      + '<div class="js-g"><div class="js-rad">' + radar() + '</div><div class="js-bars"><small class="js-sub">// 능력치 6</small>' + bars() + '</div></div>'
      + achHtml() + '<p class="js-m">푼 문제 ' + solved + ' · 정답률 ' + Math.round(acc * 100) + '% · 연속 ' + streak + '일 · 플랜 이행 ' + Math.round(pl.adh * 100) + '% · <a href="#" id="js-edit">목표 바꾸기</a></p></section>';
    var chk = box.querySelector('[data-chk]');
    if (chk) chk.onclick = function () { if (window.jamHabit && window.jamHabit()) { var k = ymd(now); D[k] = D[k] || { v: {}, p: [] }; D[k].v.habit = 1; view(); } };
    var ed = document.getElementById('js-edit'); if (ed) ed.onclick = function (e) { e.preventDefault(); P = null; wiz = { job: '', goal: '', gdate: '', fam: '' }; viewWizard(1); };
  }

  Promise.all([jget('/assets/jam/goals.json?v=1'), jget('/assets/jam/lines.json?d=' + ymd(now)), jget('/assets/jam/exams.json?d=' + ymd(now)), loggedIn ? call('/api/me').catch(function () { return null; }) : Promise.resolve(null)]).then(function (r) {
    G = r[0]; L = r[1]; X = r[2];
    if (loggedIn && r[3] === null) loggedIn = false;      // 만료된 로그인
    if (r[3] && r[3].prefs && r[3].prefs.goal) P = { job: r[3].prefs.job, goal: r[3].prefs.goal, gdate: r[3].prefs.gdate, gstart: r[3].prefs.gstart };
    else if (loggedIn) P = lsP();
    if (!G) { box.innerHTML = '<p class="js-m">상태창을 못 불러왔다. 새로고침해라.</p>'; return; }
    view();
  });
  }
  var pr = (window.jamPull && !window.JAM_DEMO) ? window.jamPull() : Promise.resolve();
  function withHud() { return new Promise(function (ok) { if (window.JAM_ACH) return ok(); var sc = document.createElement('script'); sc.src = '/assets/jam/hud.js?v=1'; sc.onload = sc.onerror = function () { ok(); }; document.head.appendChild(sc); setTimeout(ok, 1500); }); }
  pr.then(withHud, withHud).then(run, run);
})();
