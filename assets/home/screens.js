// 홈 통합 검색 · 오늘 마감 필터 (2026-10-23)
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  // ── 오늘 마감: 유형 필터 ──
  var tf = $('.td-f');
  if (tf) {
    tf.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      $$('button', tf).forEach(function (x) { x.classList.toggle('on', x === b); });
      var f = b.getAttribute('data-f'), n = 0;
      $$('#tdl .td-c').forEach(function (li) { var on = !f || li.getAttribute('data-t') === f; li.hidden = !on; if (on) n++; });
      var m = $('#tdn'); if (m) m.hidden = n > 0;
    });
  }
  // ── 홈: 통합 검색 ──
  var q = $('#hq'), res = $('#hr'); if (!q || !res) return;
  var scope = '', idx = null, loading = null;
  var slug = function (n) { return n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''); };
  var J = function (u) { return fetch(u).then(function (r) { return r.json(); }).catch(function () { return null; }); };
  var load = function () {
    if (idx) return Promise.resolve(idx);
    if (!loading) loading = Promise.all([J('/data.json'), J('/apply.json'), J('/events.json'), J('/assets/wiki/index.json'), J('/assets/fridge/rec.json')]).then(function (a) {
      var out = [];
      ((a[0] && a[0].items) || []).forEach(function (i) { out.push({ s: 'c', t: i.title, d: (i.org || '') + ' · ' + (i.end || '').slice(5).replace('-', '.') + ' 마감', u: '/c/' + i.id + '/' }); });
      (a[1] || []).forEach(function (i) { out.push({ s: 'a', t: i.title, d: (i.kind || '') + ' · ' + (i.org || ''), u: '/a/' + i.id + '/' }); });
      (a[2] || []).forEach(function (i) { out.push({ s: 'e', t: i.title, d: (i.org || '') + ' · ' + (i.end || '').slice(5).replace('-', '.') + ' 마감', u: i.link, x: 1 }); });
      (a[3] || []).forEach(function (i) { out.push({ s: 'w', t: i.t, d: i.d || '', u: i.u }); });
      ((a[4] && a[4].r) || []).forEach(function (r) { if (r && r[0]) out.push({ s: 'r', t: r[0], d: '레시피', u: '/fridge/r/' + slug(r[0]) + '/' }); });
      idx = out; return out;
    });
    return loading;
  };
  var LB = { c: '공모전', a: '지원금', e: '이벤트', r: '레시피', w: '가이드' };
  var run = function () {
    var v = q.value.trim().toLowerCase(); res.textContent = '';
    if (!v) return;
    load().then(function (d) {
      var tk = v.split(/\s+/);
      var r = d.filter(function (i) { if (scope && i.s !== scope) return false; var h = (i.t + ' ' + i.d).toLowerCase(); return tk.every(function (t) { return h.indexOf(t) >= 0; }); }).slice(0, 10);
      if (!r.length) { var p = document.createElement('p'); p.textContent = '일치하는 항목이 없어요. 검색어를 줄이거나 범위를 「전체」로 바꿔 보세요.'; res.appendChild(p); return; }
      r.forEach(function (i) {
        var a = document.createElement('a'); a.href = i.u; if (i.x) { a.target = '_blank'; a.rel = 'noopener nofollow'; }
        var e = document.createElement('em'); e.textContent = LB[i.s];
        var w = document.createElement('span'); var b = document.createElement('b'); b.textContent = i.t; var s = document.createElement('small'); s.textContent = ' ' + i.d; w.appendChild(b); w.appendChild(s);
        a.appendChild(e); a.appendChild(w); res.appendChild(a);
      });
    });
  };
  q.addEventListener('focus', load); q.addEventListener('input', run);
  $('.hm-sc').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; $$('.hm-sc button').forEach(function (x) { x.classList.toggle('on', x === b); }); scope = b.getAttribute('data-s'); run(); });
  q.form.addEventListener('submit', function (e) { e.preventDefault(); var a = $('a', res); if (a) a.click(); });
})();
