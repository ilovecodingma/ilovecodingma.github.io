// 홈 통합 검색 (2026-11-03): 검색 버튼·Enter·범위 칩, 로딩·결과 없음·오류 상태, Esc 로 닫기
(function () {
  var q = document.getElementById('hq'), res = document.getElementById('hr'); if (!q || !res) return;
  var $$ = function (s) { return [].slice.call(document.querySelectorAll(s)); };
  var scope = '', idx = null, loading = null, fail = false;
  var slug = function (n) { return n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''); };
  var J = function (u) { return fetch(u).then(function (r) { if (!r.ok) throw 0; return r.json(); }).catch(function () { fail = true; return null; }); };
  var load = function () {
    if (idx) return Promise.resolve(idx);
    if (!loading) loading = Promise.all([J('/data.json'), J('/apply.json'), J('/assets/wiki/index.json'), J('/assets/fridge/rec.json')]).then(function (a) {
      var out = [];
      ((a[0] && a[0].items) || []).forEach(function (i) { out.push({ s: 'c', t: i.title, d: (i.org || '') + ' · ' + (i.end || '').slice(5).replace('-', '.') + ' 마감', u: '/c/' + i.id + '/' }); });
      (a[1] || []).forEach(function (i) { out.push({ s: 'a', t: i.title, d: (i.kind || '') + ' · ' + (i.org || ''), u: '/a/' + i.id + '/' }); });
      (a[2] || []).forEach(function (i) { out.push({ s: 'w', t: i.t, d: i.d || '', u: i.u }); });
      ((a[3] && a[3].r) || []).forEach(function (r) { if (r && r[0]) out.push({ s: 'r', t: r[0], d: '레시피', u: '/fridge/r/' + slug(r[0]) + '/' }); });
      if (out.length) idx = out; else loading = null;
      return out;
    });
    return loading;
  };
  var LB = { c: '공모전', a: '지원금', r: '레시피', w: '가이드' };
  var msg = function (t) { res.textContent = ''; var p = document.createElement('p'); p.textContent = t; res.appendChild(p); };
  var run = function () {
    var v = q.value.trim().toLowerCase(); res.textContent = '';
    if (!v) return Promise.resolve();
    msg('검색 중…');
    return load().then(function (d) {
      if (q.value.trim().toLowerCase() !== v) return;
      if (!d.length) { msg('검색 데이터를 불러오지 못했어요. 잠시 뒤 다시 시도하거나 위 주제 바로가기를 이용해 주세요.'); return; }
      var tk = v.split(/\s+/);
      var r = d.filter(function (i) { if (scope && i.s !== scope) return false; var h = (i.t + ' ' + i.d).toLowerCase(); return tk.every(function (t) { return h.indexOf(t) >= 0; }); }).slice(0, 10);
      if (!r.length) { msg('「' + q.value.trim() + '」와 일치하는 항목이 없어요. 검색어를 줄이거나 범위를 「전체」로 바꿔 보세요.'); return; }
      res.textContent = '';
      r.forEach(function (i) {
        var a = document.createElement('a'); a.href = i.u;
        var e = document.createElement('em'); e.textContent = LB[i.s];
        var w = document.createElement('span'); var b = document.createElement('b'); b.textContent = i.t; var s = document.createElement('small'); s.textContent = ' ' + i.d; w.appendChild(b); w.appendChild(s);
        a.appendChild(e); a.appendChild(w); res.appendChild(a);
      });
    });
  };
  q.addEventListener('focus', load); q.addEventListener('input', run);
  var hs = document.getElementById('hs'); if (hs) hs.addEventListener('change', function () { scope = hs.value; run(); });
  q.form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && res.firstChild) { res.textContent = ''; q.focus(); } });
  document.addEventListener('click', function (e) { if (!q.form.contains(e.target)) res.textContent = ''; });
})();
