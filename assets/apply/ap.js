// 지원금·청약 목록: 유형·지역·마감·검색 필터 + 더 보기. 조건·스크롤 위치는 상세에 다녀와도 유지한다(sessionStorage). (2026-10-23)
(function () {
  var $ = function (s) { return document.querySelector(s); };
  var ul = $('#ap-list'), cnt = $('#ap-cnt'), more = $('#ap-more'); if (!ul) return;
  var KEY = 'jupjup_apply_state_v1', PAGE = 30;
  var st = { g: '', r: '', d: '', q: '', n: PAGE };
  try { var sv0 = JSON.parse(sessionStorage.getItem(KEY) || 'null'); if (sv0) st = Object.assign(st, sv0.st || {}); } catch (e) {}
  var data = null;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var kst = function () { return new Date(Date.now() + 324e5).toISOString().slice(0, 10); };
  var dn = function (s) { var p = s.split('-'); return Math.round(Date.UTC(+p[0], p[1] - 1, +p[2]) / 864e5); };
  var T = dn(kst());
  var grp = function (a) {
    if (a.kk === 'ipo') return '공모주';
    if (a.kk === 'apt' || a.kk === 'rent') return '주거 청약';
    return /기업|사업자|법인|소상공인|스타트업|창업|중소|협동조합|사회적경제|수출|R&D|연구개발|참여기관|기관 모집/.test((a.title || '') + ' ' + (a.target || '')) ? '사업자·기업' : '개인·가구';
  };
  var reg = function (a) { var r = (a.region || '').trim(); return r ? r.split(/\s+/)[0] : ''; };
  var card = function (a) {
    var alw = !!a.always, left = alw ? 0 : dn(a.end) - T, cls = 'd' + (alw ? '' : left <= 3 ? ' u3' : left <= 7 ? ' hot' : '');
    var m = [['대상', (a.target || '').trim().slice(0, 14) || '미확인'], ['지원 내용', (a.benefit || '').trim().slice(0, 18) || '미확인'], ['지역', reg(a) || '미확인'], ['마감', alw ? '상시' : a.end.slice(5).replace('-', '.')]];
    var dl = m.map(function (p) { return '<div><dt>' + p[0] + '</dt><dd' + (p[1] === '미확인' ? ' class="nu"' : '') + '>' + esc(p[1]) + '</dd></div>'; }).join('');
    return '<li><a class="card cc" href="/apply/?id=' + encodeURIComponent(a.id) + '"><div class="cb"><div class="top"><h3 class="t">' + esc(a.title) + '</h3><span class="' + cls + '">' + (alw ? '상시' : left <= 0 ? 'D-DAY' : 'D-' + left) + '</span></div><dl class="cm">' + dl + '</dl><p class="o">' + esc(grp(a)) + ' · ' + esc(a.org || '') + (a.verified ? ' · 공식 포털 수집' : '') + '</p></div></a></li>';
  };
  var sync = function () {
    $('#ap-q').value = st.q; $('#ap-r').value = st.r; $('#ap-d').value = st.d;
    [].forEach.call(document.querySelectorAll('.ap-chips button'), function (b) { b.classList.toggle('on', b.getAttribute('data-g') === st.g); });
  };
  var save = function () { try { sessionStorage.setItem(KEY, JSON.stringify({ st: st, y: window.scrollY })); } catch (e) {} };
  var render = function () {
    if (!data) return;
    var q = st.q.trim().toLowerCase();
    var L = data.filter(function (a) {
      if (a.end && !a.always && dn(a.end) < T) return false;
      if (st.g && grp(a) !== st.g) return false;
      if (st.r && (st.r === '__none' ? reg(a) : reg(a) !== st.r)) return false;
      if (st.d === 'x' && a.always) return false;
      if ((st.d === '7' || st.d === '30') && (a.always || dn(a.end) - T > +st.d)) return false;
      if (q && ((a.title || '') + ' ' + (a.org || '') + ' ' + (a.target || '') + ' ' + (a.benefit || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    }).sort(function (a, b) { return (a.always ? 1 : 0) - (b.always ? 1 : 0) || (a.end || '').localeCompare(b.end || '') || (a.title || '').localeCompare(b.title || ''); });
    ul.innerHTML = L.length ? L.slice(0, st.n).map(card).join('') : '<li class="empty"><p>조건에 맞는 공고가 없어요. 조건을 줄이거나 초기화해 보세요.</p></li>';
    var conds = [st.g, st.r === '__none' ? '지역 미확인' : st.r, st.d === 'x' ? '상시 제외' : st.d ? st.d + '일 이내' : '', st.q ? '“' + st.q + '”' : ''].filter(Boolean);
    cnt.innerHTML = '결과 <b>' + L.length + '건</b>' + (conds.length ? ' · 적용: ' + esc(conds.join(' · ')) + ' <button type="button" class="ap-reset">초기화</button>' : '');
    more.hidden = L.length <= st.n; more.textContent = '더 보기 (' + Math.min(PAGE, L.length - st.n) + '건)';
    save();
  };
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.ap-chips button'); if (b) { st.g = b.getAttribute('data-g'); st.n = PAGE; sync(); render(); return; }
    if (e.target.classList && e.target.classList.contains('ap-reset')) { st = { g: '', r: '', d: '', q: '', n: PAGE }; sync(); render(); return; }
    if (e.target.closest && e.target.closest('#ap-list a')) save();
  });
  $('#ap-q').addEventListener('input', function () { st.q = this.value; st.n = PAGE; render(); });
  $('#ap-r').addEventListener('change', function () { st.r = this.value; st.n = PAGE; render(); });
  $('#ap-d').addEventListener('change', function () { st.d = this.value; st.n = PAGE; render(); });
  more.addEventListener('click', function () { st.n += PAGE; render(); });
  window.addEventListener('pagehide', save);
  fetch('/apply.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (d) {
    data = d; sync(); render();
    try { var sv = JSON.parse(sessionStorage.getItem(KEY) || 'null'); if (sv && sv.y && (performance.getEntriesByType('navigation')[0] || {}).type === 'back_forward') setTimeout(function () { window.scrollTo(0, sv.y); }, 60); } catch (e) {}
  }).catch(function () { if (cnt) cnt.textContent = '목록을 새로 불러오지 못해 마지막으로 만든 목록을 보여 드려요.'; });
})();
