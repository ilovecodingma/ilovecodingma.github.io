// 레시피 기반 식단표 (2026-10-26): 조건(끼니·조리시간·성향·빼고 싶은 재료·냉장고 재료)으로 7일 식단표를 짜고, 장보기 목록과 먹은 끼니 체크를 제공한다.
// 레시피에는 재료별 g 분량이 없어 열량·영양을 계산하지 않는다. /assets/diet/nutrition.json(공식 DB 로 확인된 메뉴 단위 값)이 생기면 등급 1·2 값만 표시한다.
// 모든 선택·기록은 이 기기(localStorage)에만 저장하고 서버로 보내지 않는다.
(function () {
  var ROOT = document.getElementById('dtm'); if (!ROOT) return;
  var KEY = 'jupjup_diet_meal_v1';
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var load = function () { try { var v = JSON.parse(localStorage.getItem(KEY) || 'null'); if (v && v.opts) return v; } catch (e) {} return { opts: { meals: 3, max: 30, tone: '아무거나', ex: [], useFridge: true }, plan: null, checks: {}, shop: {} }; };
  var save = function () { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
  var S = load(), D = null, NUT = null;
  var rpath = function (n) { return '/fridge/r/' + n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, '') + '/'; };
  var kst = function (add) { return new Date(Date.now() + 9 * 36e5 + (add || 0) * 864e5).toISOString().slice(0, 10); };
  var DIS = '참고용이에요. 식단표는 고른 조건에 맞춰 메뉴를 나눠 주는 도구이고, 열량·영양 목표를 맞춰 주거나 치료·진단을 대신하지 않아요. 질환이 있거나 임신 중이면 전문가와 상의하세요.';
  var PRIV = '선택한 조건과 기록은 이 기기의 브라우저에만 저장되고 서버로 전송되지 않아요.';
  var SLOTS = { 2: ['점심', '저녁'], 3: ['아침', '점심', '저녁'] };
  var CAT = function (n) { return /국|찌개|탕|전골|국밥|수프/.test(n) ? '국물' : /국수|면|파스타|라면|우동|스파게티|잡채/.test(n) ? '면' : /전$|부침|땡/.test(n) ? '전' : /밥|덮밥|김밥/.test(n) ? '밥' : /볶음/.test(n) ? '볶음' : /조림|찜/.test(n) ? '조림찜' : '반찬'; };
  var shuffle = function (a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; };
  var fridge = function () { try { return JSON.parse(localStorage.getItem('jupjup_fridge_v1') || '[]'); } catch (e) { return []; } };
  var basics = function () { return (D.basic || '').split(/[·,]/).map(function (x) { return x.trim(); }).filter(Boolean); };

  // ---------- 식단표 만들기 ----------
  function eligible(slot) {
    var o = S.opts, ex = o.ex;
    return D.recipes.filter(function (r) {
      if (r.m > o.max) return false;
      if (r.t.indexOf('안주') >= 0 || r.t.indexOf('간식') >= 0) return false;
      if (r.need.some(function (x) { return ex.indexOf(x) >= 0; })) return false;
      if (o.tone !== '아무거나' && r.t.indexOf(o.tone) < 0) return false;
      if (slot === '아침' && r.t.indexOf('가벼움') < 0 && r.m > 20) return false;   // 아침은 가볍거나 짧게
      return true;
    });
  }
  function makePlan() {
    var have = S.opts.useFridge ? fridge() : [], used = {}, days = [];
    for (var d = 0; d < 7; d++) {
      var meals = [], prevCat = '';
      SLOTS[S.opts.meals].forEach(function (slot) {
        var pool = shuffle(eligible(slot)).filter(function (r) { return !used[r.n]; });
        pool.sort(function (a, b) { return score(b, have, prevCat) - score(a, have, prevCat); });
        var r = pool[0]; if (r) { used[r.n] = 1; prevCat = CAT(r.n); meals.push({ slot: slot, n: r.n }); } else meals.push({ slot: slot, n: null });
      });
      days.push({ date: kst(d), meals: meals });
    }
    S.plan = days; S.checks = {}; S.shop = {}; save();
  }
  function score(r, have, prevCat) { var s = Math.random() * 0.8; if (CAT(r.n) === prevCat) s -= 2; r.need.forEach(function (x) { if (have.indexOf(x) >= 0) s += 1; }); return s; }
  function swap(di, mi) {
    var cur = S.plan[di].meals[mi], slot = cur.slot, used = {};
    S.plan.forEach(function (d) { d.meals.forEach(function (m) { if (m.n) used[m.n] = 1; }); });
    var pool = shuffle(eligible(slot)).filter(function (r) { return !used[r.n]; });
    if (pool.length) { cur.n = pool[0].n; delete S.checks[S.plan[di].date + '|' + slot]; S.shop = {}; save(); }
  }
  var byName = function (n) { for (var i = 0; i < D.recipes.length; i++) if (D.recipes[i].n === n) return D.recipes[i]; return null; };

  // ---------- 장보기 ----------
  function shopping() {
    var cnt = {}, bs = basics(), have = fridge();
    S.plan.forEach(function (d) { d.meals.forEach(function (m) { var r = m.n && byName(m.n); if (!r) return; r.need.forEach(function (x) { if (bs.indexOf(x) < 0) cnt[x] = (cnt[x] || 0) + 1; }); }); });
    var groups = {};
    Object.keys(D.ing).forEach(function (c) { D.ing[c].forEach(function (x) { if (cnt[x]) (groups[c] = groups[c] || []).push(x); }); });
    return { cnt: cnt, groups: groups, have: have };
  }

  // ---------- 화면 ----------
  function nutText(n) {
    if (!NUT) return '';
    var v = NUT[n]; if (!v || v.grade > 2) return '';
    return '<span class="dm-kcal">약 ' + esc(v.kcal) + 'kcal <small>참고용 추정치 · 출처: ' + esc(v.src || '식약처 식품영양성분DB') + '</small></span>';
  }
  var tones = ['아무거나', '든든', '가벼움', '안 매움', '매움', '아이'];
  function paint() {
    var o = S.opts, fr = fridge();
    var optsHtml = '<section class="dt-card"><img class="dt-cut dt-cut-r" src="/assets/ruri/o_dt_salad.webp" width="120" height="166" alt="샐러드를 든 루리" loading="lazy"><h2>조건 고르기</h2><p class="dt-sub">조건에 맞는 메뉴로 7일 식단표를 짜 드려요. 같은 메뉴는 한 주에 한 번만 나오고, 같은 종류(국물·면·볶음…)가 연달아 나오지 않게 해요.</p>'
      + '<p class="dt-l">하루 끼니</p><div class="dt-ch" data-k="meals">' + [[2, '2끼(점심·저녁)'], [3, '3끼']].map(function (x) { return '<button type="button" data-v="' + x[0] + '" class="' + (o.meals === x[0] ? 'on' : '') + '">' + x[1] + '</button>'; }).join('') + '</div>'
      + '<p class="dt-l">조리 시간(최대)</p><div class="dt-ch" data-k="max">' + [[15, '15분'], [30, '30분'], [60, '60분']].map(function (x) { return '<button type="button" data-v="' + x[0] + '" class="' + (o.max === x[0] ? 'on' : '') + '">' + x[1] + '</button>'; }).join('') + '</div>'
      + '<p class="dt-l">성향</p><div class="dt-ch" data-k="tone">' + tones.map(function (x) { return '<button type="button" data-v="' + esc(x) + '" class="' + (o.tone === x ? 'on' : '') + '">' + esc(x) + '</button>'; }).join('') + '</div>'
      + '<p class="dt-l">빼고 싶은 재료 <small>(알레르기·싫어하는 재료 — 이 재료가 꼭 필요한 메뉴는 제외해요)</small></p><div class="dt-ch" id="dm-ex">' + o.ex.map(function (x) { return '<button type="button" data-x="' + esc(x) + '" class="on">' + esc(x) + ' ✕</button>'; }).join('') + '</div>'
      + '<input class="dm-in" id="dm-exin" list="dm-dl" placeholder="재료 이름을 쓰고 Enter (예: 새우, 우유)" aria-label="빼고 싶은 재료"><datalist id="dm-dl">' + Object.keys(D.ing).reduce(function (a, c) { return a.concat(D.ing[c]); }, []).map(function (x) { return '<option value="' + esc(x) + '">'; }).join('') + '</datalist>'
      + '<label class="dm-chk"><input type="checkbox" id="dm-fr"' + (o.useFridge ? ' checked' : '') + '> 냉장고 재료(' + fr.length + '개)를 우선 써요 <small>(냉장고 파먹기에서 고른 재료)</small></label>'
      + '<button type="button" class="dt-go" id="dm-make">🗓️ ' + (S.plan ? '식단표 다시 짜기' : '7일 식단표 만들기') + '</button></section>';
    var planHtml = '', shopHtml = '', progress = '';
    if (S.plan) {
      var total = 0, done = 0;
      planHtml = '<section class="dt-card"><h2>7일 식단표</h2><div class="dm-days">' + S.plan.map(function (d, di) {
        return '<div class="dm-day"><b>' + esc(d.date.slice(5).replace('-', '.')) + (d.date === kst() ? ' <em>오늘</em>' : '') + '</b>' + d.meals.map(function (m, mi) {
          var r = m.n && byName(m.n), ck = !!S.checks[d.date + '|' + m.slot]; if (r) { total++; if (ck) done++; }
          return '<div class="dm-m' + (ck ? ' ok' : '') + '"><span class="dm-sl">' + esc(m.slot) + '</span>' + (r
            ? '<a href="' + esc(rpath(r.n)) + '"><b>' + esc(r.e + ' ' + r.n) + '</b></a><small>' + r.m + '분 · ' + esc(r.lv) + '</small>' + nutText(r.n)
              + '<span class="dm-ac"><button type="button" data-ck="' + di + ',' + mi + '" aria-pressed="' + ck + '">' + (ck ? '✅ 먹었어요' : '☐ 먹었어요') + '</button><button type="button" data-sw="' + di + ',' + mi + '" aria-label="다른 메뉴로 바꾸기">🔄</button></span>'
            : '<small>조건에 맞는 메뉴가 없어요. 조건을 넓혀 보세요.</small>') + '</div>';
        }).join('') + '</div>';
      }).join('') + '</div>' + (NUT ? '' : '<p class="dt-note">열량·영양 수치는 재료 분량이 없는 레시피로는 계산할 수 없어서 보여 주지 않아요. 식약처 식품영양성분 DB 등 공식 값이 확인된 메뉴부터 표시할 예정이에요.</p>') + '</section>';
      progress = '<p class="dt-today">이번 식단표에서 ' + done + '/' + total + '끼를 먹었다고 체크했어요(' + (total ? Math.round(done / total * 100) : 0) + '%).</p>';
      var sh = shopping(), ks = Object.keys(sh.groups);
      shopHtml = '<section class="dt-card"><h2>🛒 장보기 목록</h2><p class="dt-sub">식단표 메뉴에 꼭 필요한 재료예요(기본 양념 제외). 이미 있는 재료는 체크해 두세요.</p>' + (ks.length ? ks.map(function (c) {
        return '<h3>' + esc(c) + '</h3><ul class="dm-shop">' + sh.groups[c].map(function (x) { var have = sh.have.indexOf(x) >= 0, on = !!S.shop[x]; return '<li class="' + (on ? 'ok' : '') + '"><label><input type="checkbox" data-sp="' + esc(x) + '"' + (on ? ' checked' : '') + '> ' + esc(x) + ' <small>(' + sh.cnt[x] + '개 메뉴' + (have ? ' · 냉장고에 있음' : '') + ')</small></label></li>'; }).join('') + '</ul>';
      }).join('') : '<p class="dt-sub">필요한 재료가 없어요.</p>') + '</section>';
    }
    ROOT.innerHTML = optsHtml + progress + planHtml + shopHtml + '<p class="dt-note">' + esc(DIS) + '</p><p class="dt-note">' + esc(PRIV) + '</p>';
    ROOT.querySelectorAll('.dt-ch[data-k]').forEach(function (g) { g.onclick = function (e) { var b = e.target.closest('button'); if (!b) return; var k = g.getAttribute('data-k'), v = b.getAttribute('data-v'); S.opts[k] = (k === 'meals' || k === 'max') ? +v : v; save(); paint(); }; });
    var inp = document.getElementById('dm-exin');
    inp.onkeydown = function (e) { if (e.key !== 'Enter') return; e.preventDefault(); var v = inp.value.trim(); if (v && S.opts.ex.indexOf(v) < 0) { S.opts.ex.push(v); save(); paint(); } };
    document.getElementById('dm-ex').onclick = function (e) { var b = e.target.closest('button'); if (!b) return; S.opts.ex = S.opts.ex.filter(function (x) { return x !== b.getAttribute('data-x'); }); save(); paint(); };
    document.getElementById('dm-fr').onchange = function (e) { S.opts.useFridge = e.target.checked; save(); };
    document.getElementById('dm-make').onclick = function () { makePlan(); paint(); window.scrollTo({ top: ROOT.querySelector('.dm-days') ? ROOT.querySelector('.dm-days').getBoundingClientRect().top + scrollY - 70 : 0, behavior: 'smooth' }); };
    ROOT.querySelectorAll('[data-ck]').forEach(function (b) { b.onclick = function () { var p = b.getAttribute('data-ck').split(','), d = S.plan[+p[0]], k = d.date + '|' + d.meals[+p[1]].slot; S.checks[k] = !S.checks[k]; save(); paint(); }; });
    ROOT.querySelectorAll('[data-sw]').forEach(function (b) { b.onclick = function () { var p = b.getAttribute('data-sw').split(','); swap(+p[0], +p[1]); paint(); }; });
    ROOT.querySelectorAll('[data-sp]').forEach(function (b) { b.onchange = function () { S.shop[b.getAttribute('data-sp')] = b.checked; save(); paint(); }; });
  }

  Promise.all([fetch('/assets/fridge/recipes.json?v=6').then(function (r) { return r.json(); }), fetch('/assets/diet/nutrition.json?v=1').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })])
    .then(function (a) { D = a[0]; NUT = a[1]; paint(); })
    .catch(function () { ROOT.innerHTML = '<p class="dt-note">레시피를 불러오지 못했어요. 새로고침해 주세요.</p>'; });
})();
