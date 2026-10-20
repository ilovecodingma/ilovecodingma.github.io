// 오늘 뭐 먹지? — 추천 하나로 모든 메뉴 화면을 대신한다 (2026-10-20 사용자: 「오늘 음식 추천 기능 개발, 스크롤 최소화, recommend 로 다 되게」)
//  <div data-rec="today|home|solo|weather|cat" data-n="6" data-cat="국물" data-chips="all,hearty,fast">…정적 대체 목록…</div>
//  모델·서버 호출 없이 브라우저에서 계산: 때(아침·점심·저녁·야식) · 오늘 날씨(today.json) · 제철 재료 · 지금 많이 보는 메뉴(rec_pop.json, 빌드가 시간마다 갱신)
//  · 내가 싫다고 한 것·최근에 본 것 · 사진이 있는 메뉴 · 같은 종류가 연달아 나오지 않게.
(function () {
  var hosts = [].slice.call(document.querySelectorAll('[data-rec]')); if (!hosts.length) return;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var LS = function (k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } };
  var LSset = function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  var ga = function (n, p) { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  var HOUR = new Date(Date.now() + 324e5).getUTCHours(), DAY = new Date(Date.now() + 324e5).toISOString().slice(0, 10);
  var SLOT = HOUR >= 5 && HOUR < 10 ? { k: '아침', want: { 가벼움: 1.2, 간식: .4 }, cat: { 밥: .5, 전: .4 }, max: 20 }
    : HOUR < 15 && HOUR >= 10 ? { k: '점심', want: { 든든: 1.2 }, cat: { 밥: .8, 면: .8 }, max: 30 }
    : HOUR >= 15 && HOUR < 21 ? { k: '저녁', want: { 든든: .9 }, cat: { 국물: .7, 볶음: .6, 조림: .5, 밥: .3 }, max: 60 }
    : { k: '야식', want: { 안주: 1.2, 간식: 1, 가벼움: .6 }, cat: { 면: .6, 전: .6 }, max: 25 };
  var S = { dis: LS('jupjup_rec_dis', {}), seen: LS('jupjup_rec_seen', {}), made: LS('jupjup_fridge_made', {}) };
  var slug = function (n) { return n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''); };
  var seed = function (s) { var h = 0, t = DAY + s; for (var i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0; return (h >>> 0) / 4294967296; };

  var CHIPS = {
    all: ['전체', null], hearty: ['🍚 든든', function (m) { return m.t.indexOf('든든') >= 0; }], light: ['🥗 가벼움', function (m) { return m.t.indexOf('가벼움') >= 0; }],
    fast: ['⏱ 15분 이내', function (m) { return m.m <= 15; }], solo: ['🏠 혼밥(재료 3개↓)', function (m) { return m.need.length <= 3 && m.m <= 20; }],
    mild: ['🙂 안 매움', function (m) { return m.t.indexOf('안 매움') >= 0; }], spicy: ['🌶 매콤', function (m) { return m.t.indexOf('매움') >= 0; }],
    snack: ['🍺 안주·야식', function (m) { return m.t.indexOf('안주') >= 0 || m.t.indexOf('간식') >= 0; }], kid: ['🧒 아이랑', function (m) { return m.t.indexOf('아이') >= 0; }],
    pop: ['🔥 지금 인기', function (m) { return m.pv > 0; }]
  };
  var WX = { rainy: ['☔ 비 오는 날', ['국물', '전']], cold: ['🧣 쌀쌀한 날', ['국물', '조림']], hot: ['☀️ 더운 날', ['면', '반찬']], gap: ['🌗 일교차 큰 날', ['국물', '밥']], mild: ['🌤️ 선선한 날', ['볶음', '밥', '조림']] };

  var DATA = null, loading = null;
  function load() {
    if (DATA) return Promise.resolve(DATA); if (loading) return loading;
    var j = function (u, o) { return fetch(u, o).then(function (r) { return r.json(); }).catch(function () { return null; }); };
    loading = Promise.all([j('/assets/fridge/rec.json?v=' + DAY), j('/assets/fridge/rec_pop.json', { cache: 'no-cache' }), j('/assets/fridge/today.json', { cache: 'no-cache' })]).then(function (a) {
      var R = a[0]; if (!R) return null; var pop = a[1] || {}, td = a[2] || null, TG = R.tags, M = [];
      R.r.forEach(function (x) { var s = slug(x[0]), p = pop[s] || [0, 0];
        M.push({ n: x[0], e: x[1], m: x[2], lv: x[3], t: x[4].map(function (i) { return TG[i]; }), cat: x[5], ph: x[6], need: x[7], opt: x[8], ns: x[9], slug: s, pv: p[0], lk: p[1] }); });
      DATA = { M: M, td: td, mv: Math.max.apply(null, M.map(function (m) { return m.pv; }).concat([1])) }; return DATA;
    }); return loading;
  }

  function score(m, ctx) {
    var td = DATA.td, sc = 0, why = [];
    if (m.t.some(function (t) { return SLOT.want[t]; })) { var w = 0; m.t.forEach(function (t) { w = Math.max(w, SLOT.want[t] || 0); }); sc += w; }
    if (SLOT.cat[m.cat]) { sc += SLOT.cat[m.cat]; }
    if (m.m <= SLOT.max) sc += .5; else sc -= .6;
    if (SLOT.k === '아침' || SLOT.k === '야식') { if (m.m <= 15) { sc += .5; } }
    var wxc = ctx.wxcats;   // 날씨 칩이 있으면 그 분류, 없으면 오늘 날씨
    if (wxc) { if (wxc.indexOf(m.cat) >= 0) { sc += 2.2; why.push(ctx.wxlabel); } }
    else if (td && td.want && td.want[m.cat]) { sc += td.want[m.cat] * .8; why.push((td.why || '').split('엔')[0] + '엔 ' + m.cat); }
    var sea = td && td.season ? m.need.concat(m.opt).filter(function (i) { return td.season.indexOf(i) >= 0; }) : []; if (sea.length) { sc += .5 * Math.min(2, sea.length); why.push('제철 ' + sea[0]); }
    if (m.pv > 0) { sc += 1.4 * Math.log(1 + m.pv) / Math.log(1 + DATA.mv) + Math.min(.8, m.lk * .25); why.push(m.lk > 1 ? '좋아요 ' + m.lk + '개' : '요즘 많이 보는 메뉴'); }
    if (m.ph) sc += .8; if (m.lv === 0) sc += .35;
    var pref = {}; Object.keys(S.made).forEach(function (k) { pref[S.made[k]] = (pref[S.made[k]] || 0) + 1; }); if (pref[m.cat]) sc += Math.min(1, pref[m.cat] * .3);
    if (S.seen[m.n] && Date.now() - S.seen[m.n] < 3 * 864e5) sc -= 1.4;
    sc += seed(m.n + ctx.salt) * 1.3;
    why.unshift(SLOT.k + '엔'); if (SLOT.k) why[0] = SLOT.k + (m.t.indexOf('든든') >= 0 ? '엔 든든하게' : m.t.indexOf('가벼움') >= 0 ? '엔 가볍게' : '에 어울려요');
    return { m: m, sc: sc, why: why };
  }
  function diversify(L, n) {
    var out = [], rest = [], cats = {}, mains = {};
    L.forEach(function (x) { var c = x.m.cat, k = x.m.need[0]; if (out.length < n && (out.length >= 5 || (!cats[c] && !mains[k]))) { out.push(x); cats[c] = 1; mains[k] = 1; } else rest.push(x); });
    return out.concat(rest);
  }

  function mount(host) {
    var mode = host.getAttribute('data-rec') || 'today', N = +host.getAttribute('data-n') || 6, ccat = host.getAttribute('data-cat') || '';
    var ids = (host.getAttribute('data-chips') || (mode === 'home' ? 'all,hearty,light,fast' : mode === 'solo' ? 'all,hearty,light,mild,snack,pop' : mode === 'cat' ? 'all,fast,mild,kid,pop' : mode === 'weather' ? '' : 'all,hearty,light,fast,solo,mild,snack,kid,pop')).split(',').filter(Boolean);
    var base = mode === 'solo' ? function (m) { return m.need.length <= 3 && m.m <= 20; } : mode === 'cat' && ccat ? function (m) { return m.cat === ccat; } : null;
    var chipKey = mode === 'weather' ? (DATA.td && WX[DATA.td.label] ? DATA.td.label : 'mild') : (LS('jupjup_rec_chip_' + mode, 'all')), st = { i: 0, salt: '', order: [], chip: ids.indexOf(chipKey) >= 0 || mode === 'weather' ? chipKey : 'all' };
    var wxKeys = Object.keys(WX), todayLabel = DATA.td && DATA.td.label;

    function build() {
      var f = mode === 'weather' ? null : CHIPS[st.chip] && CHIPS[st.chip][1], ctx = { salt: st.salt };
      if (mode === 'weather') { var w = WX[st.chip] || WX.mild; ctx.wxcats = w[1]; ctx.wxlabel = w[0].replace(/^\S+\s/, '') + '엔 ' + w[1][0]; }
      var L = DATA.M.filter(function (m) { return !S.dis[m.n] || Date.now() - S.dis[m.n] > 30 * 864e5; }).filter(function (m) { return (!base || base(m)) && (!f || f(m)) && (!ctx.wxcats || ctx.wxcats.indexOf(m.cat) >= 0); });
      var R = L.map(function (m) { return score(m, ctx); });
      R.sort(function (a, b) { return (st.chip === 'pop' ? (b.m.pv - a.m.pv) || (b.sc - a.sc) : b.sc - a.sc); });
      st.order = diversify(R, 12); st.i = 0;
    }
    function pickHtml(x) {
      var m = x.m, why = x.why.slice(0, 3); if (m.m <= 20) why.push(m.m + '분'); if (m.need.length <= 3) why.push('재료 ' + m.need.length + '개');
      var img = m.ph ? '<img src="/assets/fridge/ph/t/' + esc(encodeURI(m.slug)) + '.webp" width="120" height="90" alt="' + esc(m.n) + ' 완성 사진" decoding="async">' : '<span class="rec-e">' + m.e + '</span>';
      return '<article class="rec-pick"><a class="rec-img" href="/fridge/r/' + esc(encodeURI(m.slug)) + '/" data-n="' + esc(m.n) + '">' + img + '</a><div class="rec-body"><h3><a href="/fridge/r/' + esc(encodeURI(m.slug)) + '/" data-n="' + esc(m.n) + '">' + esc(m.n) + '</a></h3>'
        + '<p class="rec-meta"><em>⏱ ' + m.m + '분</em><em>' + ['쉬움', '보통', '어려움'][m.lv] + '</em><em>' + esc(m.cat) + '</em></p><p class="rec-why">💡 ' + esc(why.join(' · ')) + '</p>'
        + '<p class="rec-need">필수 재료 ' + m.need.map(esc).join(', ') + '</p></div></article>'
        + '<div class="rec-act"><a class="rec-go" href="/fridge/r/' + esc(encodeURI(m.slug)) + '/" data-n="' + esc(m.n) + '">레시피 보기 →</a><button type="button" class="rec-re">🔄 다른 메뉴</button><button type="button" class="rec-no" aria-label="이 메뉴는 별로예요" title="별로예요">👎</button></div>';
    }
    function altHtml(x) {
      var m = x.m, img = m.ph ? '<img src="/assets/fridge/ph/t/' + esc(encodeURI(m.slug)) + '.webp" width="112" height="84" loading="lazy" alt="">' : '<span class="rec-e s">' + m.e + '</span>';
      return '<a class="rec-alt-c" href="/fridge/r/' + esc(encodeURI(m.slug)) + '/" data-n="' + esc(m.n) + '">' + img + '<b>' + esc(m.n) + '</b><small>' + m.m + '분 · ' + esc(m.cat) + '</small></a>';
    }
    function paint() {
      var o = st.order, cur = o[st.i % Math.max(1, o.length)], title = mode === 'weather' ? '🌤️ 날씨별 오늘 메뉴' : mode === 'solo' ? '🏠 자취 요리 추천' : mode === 'cat' ? '🍽️ 오늘의 ' + esc(ccat) + ' 추천' : '🍽️ 오늘 뭐 먹지?';
      var sub = SLOT.k + (DATA.td ? ' · ' + esc(DATA.td.place || '서울') + ' ' + Math.round(DATA.td.t) + '° · ' + esc(DATA.td.why || '') : '');
      var chips = mode === 'weather' ? wxKeys.map(function (k) { return '<button type="button" class="rec-chip' + (k === st.chip ? ' on' : '') + '" data-c="' + k + '">' + WX[k][0] + (k === todayLabel ? ' · 오늘' : '') + '</button>'; }).join('')
        : ids.map(function (k) { return CHIPS[k] ? '<button type="button" class="rec-chip' + (k === st.chip ? ' on' : '') + '" data-c="' + k + '">' + CHIPS[k][0] + '</button>' : ''; }).join('');
      var alts = o.slice(1 + st.i, 1 + st.i + N); if (alts.length < N) alts = alts.concat(o.slice(0, Math.min(o.length, N - alts.length)).filter(function (x) { return x !== cur; }));
      host.innerHTML = '<div class="rec"><div class="rec-h"><b>' + title + '</b><small>' + sub + '</small></div>' + (chips ? '<div class="rec-chips" role="group" aria-label="조건">' + chips + '</div>' : '')
        + (cur ? pickHtml(cur) + (alts.length ? '<div class="rec-alts" aria-label="다른 추천">' + alts.map(altHtml).join('') + '</div>' : '') : '<p class="rec-empty">조건에 맞는 메뉴가 없어요. 다른 조건을 눌러 보세요.</p>')
        + '<p class="rec-foot"><a href="/fridge/">🧊 내 냉장고 재료로 찾기</a><span>' + DATA.M.length + '개 중 ' + o.length + '개에서 골랐어요</span></p></div>';
      if (cur) { S.seen[cur.m.n] = Date.now(); LSset('jupjup_rec_seen', S.seen); }
      wire();
    }
    function wire() {
      [].forEach.call(host.querySelectorAll('.rec-chip'), function (b) { b.onclick = function () { st.chip = b.getAttribute('data-c'); st.salt = ''; if (mode !== 'weather') LSset('jupjup_rec_chip_' + mode, st.chip); ga('rec_chip', { mode: mode, chip: st.chip }); build(); paint(); }; });
      var re = host.querySelector('.rec-re'); if (re) re.onclick = function () { st.i = (st.i + 1) % Math.max(1, st.order.length); ga('rec_reroll', { mode: mode }); paint(); };
      var no = host.querySelector('.rec-no'); if (no) no.onclick = function () { var c = st.order[st.i]; if (!c) return; S.dis[c.m.n] = Date.now(); LSset('jupjup_rec_dis', S.dis); ga('rec_dislike', { mode: mode }); st.order.splice(st.i, 1); if (st.i >= st.order.length) st.i = 0; paint(); };
      [].forEach.call(host.querySelectorAll('a[data-n]'), function (a) { a.addEventListener('click', function () { var n = a.getAttribute('data-n'); ga('rec_click', { mode: mode, item: n }); try { window.JUP && JUP.api && JUP.api('/api/rec', { method: 'POST', body: { ev: 'click', ids: ['f:' + n], det: [{ m: mode, c: st.chip, s: SLOT.k }] } }).catch(function () {}); } catch (e) {} }); });
    }
    build(); paint(); host.classList.add('rec-on');
  }

  // 탭 (냉장고 화면: 오늘의 추천 ↔ 내 냉장고로 찾기)
  [].forEach.call(document.querySelectorAll('[data-rec-tabs]'), function (bar) {
    var btns = [].slice.call(bar.querySelectorAll('button[data-t]')), panes = btns.map(function (b) { return document.getElementById(b.getAttribute('data-t')); });
    var has = false; try { has = (JSON.parse(localStorage.getItem('jupjup_fridge_v1') || '[]') || []).length > 0 || /[?&]ing=/.test(location.search); } catch (e) {}
    var show = function (k) { btns.forEach(function (b, i) { var on = i === k; b.classList.toggle('on', on); b.setAttribute('aria-selected', on); if (panes[i]) panes[i].hidden = !on; }); };
    btns.forEach(function (b, i) { b.onclick = function () { show(i); ga('rec_tab', { tab: b.getAttribute('data-t') }); }; });
    show(has ? 1 : 0);
  });

  var go = function () { load().then(function (d) { if (!d) return; hosts.forEach(function (h) { if (!h.classList.contains('rec-on')) try { mount(h); } catch (e) {} }); }); };
  if ('IntersectionObserver' in window) { var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); go(); } }, { rootMargin: '500px' }); hosts.forEach(function (h) { io.observe(h); }); } else go();
})();
