// 웹툰·애니 취향 추천 (2026-10-20): 설문 → 장르·분위기·줄거리 키워드·비슷한 작품(사용자 추천 관계) → 점수 → 6개. 서버 없이 브라우저에서 계산, 설문 선택값만 익명으로 집계.
(function () {
  var ROOT = document.getElementById('watch'); if (!ROOT) return;
  var API = (document.body && document.body.dataset.api) || 'https://jupjup-api.sung2011103.workers.dev';
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var LS = function (k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } };
  var SV = function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  var ga = function (n, p) { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  var post = function (path, body) { try { fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(function () {}); } catch (e) {} };
  var kind = /#anime/.test(location.hash) ? 'anime' : 'webtoon';
  var DATA = {}, STATS = {}, VOTES = {};
  var day = new Date(Date.now() + 324e5).toISOString().slice(0, 10);

  function load(k) {
    if (DATA[k]) return Promise.resolve(DATA[k]);
    return fetch('/assets/watch/' + k + '.json?v=' + day).then(function (r) { return r.json(); }).then(function (d) {
      var I = d.r.map(function (x) { return k === 'webtoon' ? W(x) : Aa(x); }); var by = {}; I.forEach(function (i) { by[i.id] = i; });
      DATA[k] = { cfg: d.cfg, at: d.at, I: I, by: by }; return DATA[k];
    });
  }
  function W(x) { return { id: x[0], t: x[1], sub: x[2], img: x[3], tags: x[4] || [], kw: x[5] || [], sc: x[6] || 0, fav: x[7] || 0, fin: !!x[8], days: x[9] || [], age: x[10], adult: !!x[11], pub: x[12], url: 'https://comic.naver.com/webtoon/list?titleId=' + x[0], site: '네이버웹툰', rec: [], set: (x[4] || []).concat(x[5] || []) }; }
  function Aa(x) { return { id: x[0], t: x[1] || x[3] || x[2], sub: [x[2], x[3]].filter(function (s, i, a) { return s && a.indexOf(s) === i && s !== (x[1] || x[3] || x[2]); }).join(' · '), tags: x[4].concat(x[5]), g: x[4], sc: x[6] || 0, pop: x[7] || 0, ep: x[8], fmt: x[9], year: x[10], season: x[11], st: x[12], studio: x[13], img: x[14], color: x[15], url: x[16], ott: x[17] || [], rec: x[18] || [], rvkw: x[19] || [], tr: x[20], min: x[21], kw: x[19] || [], site: 'AniList', fav: x[7] || 0, set: x[4].concat(x[5], x[19] || []) }; }

  var cfgOf = function () { return DATA[kind].cfg; };
  var gl = function (t) { var m = (DATA[kind] && DATA[kind].cfg.gl) || {}; return m[t] || t; };
  var S = function () { return LS('jupjup_watch_' + kind, { g: [], mood: '', mode: '', seen: [], done: false, dis: {}, fav: {} }); };
  var save = function (s) { SV('jupjup_watch_' + kind, s); };

  // ── 점수 ──
  function jac(a, b) { if (!a.length || !b.length) return 0; var s = {}, n = 0; a.forEach(function (x) { s[x] = 1; }); b.forEach(function (x) { if (s[x]) n++; }); return n / (a.length + b.length - n); }
  function rank(st, salt) {
    var D = DATA[kind], cfg = D.cfg, mood = (cfg.moods || []).filter(function (m) { return m.k === st.mood; })[0], liked = st.seen.map(function (i) { return D.by[i]; }).filter(Boolean), out = [];
    D.I.forEach(function (it) {
      if (it.adult || st.dis[it.id] || st.seen.indexOf(it.id) >= 0) return;
      if (kind === 'webtoon') { if (st.mode === 'ongoing' && it.fin) return; if (st.mode === 'finished' && !it.fin) return; if (st.mode === 'ongoing' && it.days && !it.days.length && !it.fin) return; }
      else { if (st.mode === 'tv' && !(it.fmt === 'TV' || it.fmt === 'ONA')) return; if (st.mode === 'movie' && it.fmt !== 'MOVIE') return; if (st.mode === 'short' && !(it.fmt === 'TV_SHORT' || (it.ep && it.ep <= 13))) return; }
      var sc = 0, why = [];
      var gm = st.g.filter(function (g) { return it.tags.indexOf(g) >= 0; }); if (gm.length) { sc += 3 * gm.length; why.push(gm.slice(0, 2).map(gl).join('·') + ' 취향'); } else if (st.g.length) sc -= 1.5;
      if (mood) { var nm = (mood.names || []).filter(function (g) { return it.tags.indexOf(g) >= 0; }), km = (mood.kw || []).filter(function (w) { return it.kw.indexOf(w) >= 0; }); if (nm.length || km.length) { sc += 2 * nm.length + 1.6 * km.length; why.push(mood.why || mood.label); } }
      var best = null, bs = 0; liked.forEach(function (l) { var j = jac(it.set, l.set) * 5; if (l.rec && l.rec.some(function (r) { return r[0] === it.id; })) j += 4; if (it.rec && it.rec.some(function (r) { return r[0] === l.id; })) j += 3; if (j > bs) { bs = j; best = l; } });
      if (bs > 0.9) { sc += bs; why.push('「' + best.t.slice(0, 14) + '」 좋아했다면'); }
      if (kind === 'webtoon') { sc += Math.max(0, (it.sc - 8.8)) * 3 + Math.log(1 + it.fav) / 9; if (it.sc >= 9.8) why.push('별점 ' + it.sc.toFixed(1)); }
      else { sc += (it.sc || 60) / 100 * 2.2 + Math.log(1 + it.pop) / 7; if (it.sc >= 80) why.push('평점 ' + it.sc); }
      var v = VOTES[it.id]; if (v) sc += Math.min(1.2, v[0] * .3) - Math.min(2, v[1] * .5);
      sc += ((it.id * 2654435761 + salt) % 1000) / 1000 * 1.1;
      out.push({ it: it, sc: sc, why: why.slice(0, 3) });
    });
    out.sort(function (a, b) { return b.sc - a.sc; });
    var pick = [], cnt = {}; out.forEach(function (x) { var g = (x.it.tags[0] || '?'); if (pick.length < 6 && (cnt[g] || 0) < 3) { pick.push(x); cnt[g] = (cnt[g] || 0) + 1; } });
    return { top: pick, all: out };
  }

  // ── 화면 ──
  var step = 0, salt = 0, offset = 0;
  function tabs() { return '<div class="wt-tabs" role="tablist"><button type="button" data-k="webtoon" class="' + (kind === 'webtoon' ? 'on' : '') + '">📖 웹툰</button><button type="button" data-k="anime" class="' + (kind === 'anime' ? 'on' : '') + '">🎬 애니</button></div>'; }
  function render() {
    load(kind).then(function () {
      var st = S(), cfg = cfgOf();
      ROOT.innerHTML = tabs() + (st.done ? results(st) : survey(st, cfg)) + statsBox();
      wire(st); fetchStats();
    });
  }
  var Q = function () { return [['g', '좋아하는 장르를 골라 주세요', '최대 4개', 'multi'], ['mood', '지금 어떤 이야기가 보고 싶어요?', '한 가지', 'one'], ['mode', kind === 'webtoon' ? '어떻게 보고 싶어요?' : '어떤 길이가 좋아요?', '한 가지', 'one'], ['seen', '재밌게 본 작품이 있다면 골라 주세요', '선택 · 최대 5개 · 비슷한 작품을 찾아 드려요', 'seen']]; };
  function survey(st, cfg) {
    var q = Q()[step], dots = Q().map(function (_, i) { return '<i class="' + (i <= step ? 'on' : '') + '"></i>'; }).join('');
    var body = '';
    if (q[0] === 'g') body = '<div class="wt-opts">' + cfg.genres.map(function (g) { return '<button type="button" class="wt-o' + (st.g.indexOf(g[0]) >= 0 ? ' on' : '') + '" data-v="' + esc(g[0]) + '">' + esc(g[1] || g[0]) + '</button>'; }).join('') + '</div>';
    else if (q[0] === 'mood') body = '<div class="wt-opts big">' + cfg.moods.map(function (m) { return '<button type="button" class="wt-o' + (st.mood === m.k ? ' on' : '') + '" data-v="' + m.k + '"><span>' + m.e + '</span>' + esc(m.label) + '</button>'; }).join('') + '</div>';
    else if (q[0] === 'mode') body = '<div class="wt-opts big">' + cfg.modes.map(function (m) { return '<button type="button" class="wt-o' + (st.mode === m.k ? ' on' : '') + '" data-v="' + m.k + '"><span>' + m.e + '</span>' + esc(m.label) + '</button>'; }).join('') + '</div>';
    else body = '<input class="wt-search" type="search" placeholder="작품 이름을 입력해 보세요" aria-label="작품 검색"><div class="wt-sres"></div><div class="wt-picked">' + st.seen.map(function (i) { var it = DATA[kind].by[i]; return it ? '<span class="wt-pk" data-i="' + i + '">' + esc(it.t.slice(0, 16)) + ' ✕</span>' : ''; }).join('') + '</div>';
    return '<section class="wt-card"><div class="wt-prog">' + dots + '</div><p class="wt-q"><small>' + (step + 1) + '/' + Q().length + ' · ' + esc(q[2]) + '</small>' + esc(q[1]) + '</p>' + body
      + '<div class="wt-nav">' + (step ? '<button type="button" class="wt-prev">← 이전</button>' : '<span></span>') + '<button type="button" class="wt-next">' + (step === Q().length - 1 ? '추천 받기 ✨' : '다음 →') + '</button></div>'
      + '<p class="wt-skip"><a href="#" class="wt-skipall">설문 건너뛰고 인기작 보기</a></p></section>';
  }
  function card(x, st, i) {
    var it = x.it, meta = kind === 'webtoon' ? (it.fin ? '완결' : (it.days.join('·') ? it.days.join('·') + ' 연재' : '연재 중')) + ' · ' + (it.age === 'RATE_15' ? '15세' : it.age === 'RATE_12' ? '12세' : it.age === 'RATE_18' ? '18세' : '전체') + (it.sc ? ' · ★' + it.sc.toFixed(2) : '') : [it.fmt === 'MOVIE' ? '극장판' : it.fmt === 'TV' ? 'TV' : it.fmt, it.ep ? it.ep + '화' : '', it.year || '', it.sc ? '★' + (it.sc / 10).toFixed(1) : ''].filter(Boolean).join(' · ');
    var ott = (it.ott || []).slice(0, 3).map(function (o) { return '<a href="' + esc(o.u) + '" target="_blank" rel="noopener nofollow">' + esc(o.s) + '</a>'; }).join('');
    return '<article class="wt-it"><a class="wt-img" href="' + esc(it.url) + '" target="_blank" rel="noopener nofollow" data-id="' + it.id + '">' + (it.img ? '<img src="' + esc(it.img) + '" alt="' + esc(it.t) + ' 표지" loading="lazy" referrerpolicy="no-referrer"' + (it.color ? ' style="background:' + esc(it.color) + '"' : '') + '>' : '<span>' + (kind === 'webtoon' ? '📖' : '🎬') + '</span>') + '</a>'
      + '<div class="wt-b"><h3>' + esc(it.t) + '</h3><p class="wt-m">' + esc(meta) + '</p>' + (it.sub ? '<p class="wt-sub">' + esc(it.sub) + '</p>' : '')
      + '<p class="wt-tg">' + it.tags.slice(0, 4).map(function (t) { return '<em>#' + esc(gl(t)) + '</em>'; }).join('') + '</p>'
      + (x.why.length ? '<p class="wt-why">💡 ' + esc(x.why.join(' · ')) + '</p>' : '') + (ott ? '<p class="wt-ott">볼 수 있는 곳 ' + ott + '</p>' : '')
      + '<div class="wt-ac"><a class="wt-go" href="' + esc(it.url) + '" target="_blank" rel="noopener nofollow" data-id="' + it.id + '">' + esc(it.site) + '에서 보기 →</a><button type="button" class="wt-up' + (st.fav[it.id] ? ' on' : '') + '" data-id="' + it.id + '" aria-label="좋아요">👍</button><button type="button" class="wt-dn" data-id="' + it.id + '" aria-label="별로예요">👎</button></div></div></article>';
  }
  function results(st) {
    var R = rank(st, salt), top = R.top, more = R.all.slice(6 + offset, 6 + offset + 0);
    var sum = [st.g.length ? st.g.slice(0, 4).map(gl).join('·') : '', (cfgOf().moods.filter(function (m) { return m.k === st.mood; })[0] || {}).label || '', st.seen.length ? '본 작품 ' + st.seen.length + '개' : ''].filter(Boolean).join(' / ') || '인기작';
    return '<section class="wt-res"><div class="wt-rh"><div><h2>🎯 내 취향 추천 <small>' + esc(sum) + '</small></h2><p class="note">줄거리·장르·평점과 비슷한 작품 관계를 합쳐 골랐어요.</p></div><div class="wt-ra"><button type="button" class="wt-re">🔄 다른 추천</button><button type="button" class="wt-redo">설문 다시</button></div></div>'
      + '<div class="wt-list">' + top.map(function (x, i) { return card(x, st, i); }).join('') + '</div></section>';
  }
  function statsBox() {
    var s = STATS[kind]; if (!s || !s.n || s.n < 5 || !s.cnt || !s.cnt.g) return '<div class="wt-stats" hidden></div>';
    var g = Object.keys(s.cnt.g).map(function (k) { return [k, s.cnt.g[k]]; }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 6), mx = g[0][1] || 1;
    return '<section class="wt-stats"><h2>📊 다른 사람들은 이런 장르를 좋아해요 <small>설문 ' + s.n + '명</small></h2>' + g.map(function (x) { return '<div class="wt-bar"><span>' + esc(x[0]) + '</span><i style="--w:' + Math.round(x[1] / mx * 100) + '%"></i><em>' + x[1] + '</em></div>'; }).join('') + '</section>';
  }
  function fetchStats() {
    if (STATS[kind] !== undefined) return; STATS[kind] = null;
    fetch(API + '/api/survey/stats?kind=' + kind).then(function (r) { return r.json(); }).then(function (d) { STATS[kind] = d; var el = ROOT.querySelector('.wt-stats'); if (el) el.outerHTML = statsBox(); }).catch(function () {});
    fetch(API + '/api/watch/votes?kind=' + kind).then(function (r) { return r.json(); }).then(function (d) { Object.assign(VOTES, d.votes || {}); }).catch(function () {});
  }
  function wire(st) {
    [].forEach.call(ROOT.querySelectorAll('.wt-tabs button'), function (b) { b.onclick = function () { kind = b.getAttribute('data-k'); step = 0; salt = 0; history.replaceState(null, '', kind === 'anime' ? '#anime' : '#webtoon'); ga('watch_tab', { k: kind }); render(); }; });
    var q = Q()[step], cfg = cfgOf();
    [].forEach.call(ROOT.querySelectorAll('.wt-o'), function (b) {
      b.onclick = function () { var v = b.getAttribute('data-v');
        if (q[0] === 'g') { var i = st.g.indexOf(v); if (i >= 0) st.g.splice(i, 1); else if (st.g.length < 4) st.g.push(v); b.classList.toggle('on', st.g.indexOf(v) >= 0); }
        else { st[q[0]] = v; [].forEach.call(ROOT.querySelectorAll('.wt-o'), function (o) { o.classList.toggle('on', o === b); }); }
        save(st); };
    });
    var se = ROOT.querySelector('.wt-search');
    if (se) se.oninput = function () {
      var t = se.value.trim().toLowerCase(), box = ROOT.querySelector('.wt-sres'); if (t.length < 1) { box.innerHTML = ''; return; }
      var L = DATA[kind].I.filter(function (i) { return (i.t + ' ' + (i.sub || '')).toLowerCase().indexOf(t) >= 0 && st.seen.indexOf(i.id) < 0; }).sort(function (a, b) { return (b.fav || 0) - (a.fav || 0); }).slice(0, 6);
      box.innerHTML = L.map(function (i) { return '<button type="button" class="wt-sr" data-i="' + i.id + '">' + esc(i.t) + (i.sub ? ' <small>' + esc(i.sub.slice(0, 26)) + '</small>' : '') + '</button>'; }).join('');
      [].forEach.call(box.querySelectorAll('.wt-sr'), function (b) { b.onclick = function () { if (st.seen.length < 5) st.seen.push(+b.getAttribute('data-i')); save(st); render(); }; });
    };
    [].forEach.call(ROOT.querySelectorAll('.wt-pk'), function (p) { p.onclick = function () { st.seen = st.seen.filter(function (i) { return i !== +p.getAttribute('data-i'); }); save(st); render(); }; });
    var nx = ROOT.querySelector('.wt-next'); if (nx) nx.onclick = function () {
      if (step < Q().length - 1) { step++; render(); return; }
      st.done = true; save(st); salt = 0; ga('watch_survey', { k: kind, g: st.g.join(','), mood: st.mood, mode: st.mode, seen: st.seen.length });
      post('/api/survey', { kind: kind, a: { g: st.g, mood: st.mood ? [st.mood] : [], mode: st.mode ? [st.mode] : [], seen: st.seen.length ? ['y'] : [] } }); render();
    };
    var pv = ROOT.querySelector('.wt-prev'); if (pv) pv.onclick = function () { step--; render(); };
    var sk = ROOT.querySelector('.wt-skipall'); if (sk) sk.onclick = function (e) { e.preventDefault(); st.done = true; save(st); render(); };
    var re = ROOT.querySelector('.wt-re'); if (re) re.onclick = function () { salt += 977; ga('watch_reroll', { k: kind }); render(); };
    var rd = ROOT.querySelector('.wt-redo'); if (rd) rd.onclick = function () { st.done = false; save(st); step = 0; render(); };
    [].forEach.call(ROOT.querySelectorAll('.wt-up'), function (b) { b.onclick = function () { var id = +b.getAttribute('data-id'); st.fav[id] = !st.fav[id]; if (st.fav[id] && st.seen.indexOf(id) < 0 && st.seen.length < 5) st.seen.push(id); save(st); b.classList.toggle('on', !!st.fav[id]); post('/api/watch/vote', { kind: kind, id: id, v: st.fav[id] ? 1 : 0 || 1 }); ga('watch_like', { k: kind }); }; });
    [].forEach.call(ROOT.querySelectorAll('.wt-dn'), function (b) { b.onclick = function () { var id = +b.getAttribute('data-id'); st.dis[id] = 1; save(st); post('/api/watch/vote', { kind: kind, id: id, v: -1 }); ga('watch_dislike', { k: kind }); render(); }; });
    [].forEach.call(ROOT.querySelectorAll('.wt-go,.wt-img'), function (a) { a.addEventListener('click', function () { ga('watch_out', { k: kind, id: a.getAttribute('data-id') }); }); });
  }
  render();
})();
