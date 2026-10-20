// 주간 식단표 · 통합 장보기 (2026-10-20): 담은 메뉴의 필수 재료를 한데 모아 몇 가지 메뉴에 쓰이는지 보여 주고, 체크·복사·인쇄. 서버 없이 이 브라우저에만 저장.
(function () {
  var ROOT = document.getElementById('plan'); if (!ROOT) return;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var LS = function (k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } };
  var SV = function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  var ga = function (n, p) { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  var slug = function (n) { return n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''); };
  var DAYS = ['월', '화', '수', '목', '금', '토', '일'];
  var M = {}, plan = LS('jupjup_plan', []), days = LS('jupjup_plan_days', {}), got = LS('jupjup_plan_got', {}), fav = LS('jupjup_rec_fav', {}), recent = LS('jupjup_rp_recent', []);
  var save = function () { SV('jupjup_plan', plan); SV('jupjup_plan_days', days); SV('jupjup_plan_got', got); };
  var href = function (n) { return '/fridge/r/' + esc(encodeURI(slug(n))) + '/'; };
  var thumb = function (m) { return m && m.ph ? '<img src="/assets/fridge/ph/t/' + esc(encodeURI(slug(m.n))) + '.webp" width="96" height="72" loading="lazy" alt="">' : '<span class="pl-e">' + (m ? m.e : '🍽️') + '</span>'; };
  var toast = function (t) { var d = document.createElement('div'); d.className = 'rp-toast'; d.textContent = t; document.body.appendChild(d); setTimeout(function () { d.classList.add('on'); }, 10); setTimeout(function () { d.remove(); }, 2200); };

  function shopping() {
    var cnt = {}, who = {};
    plan.forEach(function (n) { var m = M[n]; if (!m) return; m.need.forEach(function (g) { cnt[g] = (cnt[g] || 0) + 1; (who[g] = who[g] || []).push(n); }); });
    return Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a] || a.localeCompare(b); }).map(function (g) { return { g: g, n: cnt[g], who: who[g] }; });
  }
  function chips(L) {
    return L.slice(0, 12).map(function (n) {
      var on = plan.indexOf(n) >= 0;
      return '<span class="pl-chip"><a href="' + href(n) + '">' + esc(n) + '</a><button type="button" data-add="' + esc(n) + '"' + (on ? ' disabled' : '') + '>' + (on ? '담김' : '+ 식단') + '</button></span>';
    }).join('');
  }
  function paint() {
    var list = plan.map(function (n, i) {
      var m = M[n]; if (!m) return '';
      return '<li class="pl-it"><a class="pl-th" href="' + href(n) + '">' + thumb(m) + '</a><div class="pl-b"><b><a href="' + href(n) + '">' + esc(n) + '</a></b><small>⏱ ' + m.m + '분 · ' + esc(m.cat) + ' · ' + esc(m.need.join(', ')) + '</small></div>'
        + '<select data-i="' + i + '" aria-label="요일"><option value="">요일</option>' + DAYS.map(function (d) { return '<option' + (days[n] === d ? ' selected' : '') + '>' + d + '</option>'; }).join('') + '</select>'
        + '<button type="button" class="pl-x" data-r="' + i + '" aria-label="빼기">✕</button></li>';
    }).join('');
    var sh = shopping(), left = sh.filter(function (x) { return !got[x.g]; });
    ROOT.innerHTML = '<section class="pl-sec"><div class="pl-h"><h2>📅 내 식단 <small>' + plan.length + '개</small></h2><div class="pl-ac"><button type="button" class="pl-fill">✨ 추천으로 채우기</button>' + (plan.length ? '<button type="button" class="pl-clear">비우기</button>' : '') + '</div></div>'
      + (list ? '<ul class="pl-ls">' + list + '</ul>' : '<p class="pl-empty">아직 담은 메뉴가 없어요. 레시피 페이지의 「📅 식단에 담기」를 누르거나, 위 버튼으로 추천 메뉴를 채워 보세요.</p>') + '</section>'
      + (plan.length ? '<section class="pl-sec"><div class="pl-h"><h2>🛒 장보기 목록 <small>' + left.length + '/' + sh.length + '가지 남음</small></h2><div class="pl-ac"><button type="button" class="pl-copy">복사</button><button type="button" class="pl-print" data-print>🖨️ 인쇄·PDF</button></div></div>'
        + '<ul class="pl-shop">' + sh.map(function (x) { return '<li class="' + (got[x.g] ? 'done' : '') + '"><label><input type="checkbox" data-g="' + esc(x.g) + '"' + (got[x.g] ? ' checked' : '') + '><span>' + esc(x.g) + '</span></label><em>' + (x.n > 1 ? x.n + '개 메뉴에 사용' : esc(x.who[0])) + '</em></li>'; }).join('') + '</ul>'
        + '<p class="pl-note">기본양념(소금·간장·설탕 등)은 집에 있다고 보고 뺐어요. 체크한 재료는 이미 있다는 뜻이라 복사할 때 빠져요.</p></section>' : '')
      + (Object.keys(fav).length ? '<section class="pl-sec"><h2>⭐ 찜한 메뉴</h2><div class="pl-chips">' + chips(Object.keys(fav).filter(function (n) { return M[n]; })) + '</div></section>' : '')
      + (recent.length ? '<section class="pl-sec"><h2>🕘 최근 본 레시피</h2><div class="pl-chips">' + chips(recent.filter(function (n) { return M[n]; })) + '</div></section>' : '');
    wire();
  }
  function wire() {
    [].forEach.call(ROOT.querySelectorAll('.pl-x'), function (b) { b.onclick = function () { var n = plan.splice(+b.getAttribute('data-r'), 1)[0]; delete days[n]; save(); ga('plan_remove'); paint(); }; });
    [].forEach.call(ROOT.querySelectorAll('.pl-it select'), function (s) { s.onchange = function () { var n = plan[+s.getAttribute('data-i')]; if (s.value) days[n] = s.value; else delete days[n]; save(); }; });
    [].forEach.call(ROOT.querySelectorAll('.pl-shop input'), function (c) { c.onchange = function () { var g = c.getAttribute('data-g'); if (c.checked) got[g] = 1; else delete got[g]; save(); paint(); }; });
    [].forEach.call(ROOT.querySelectorAll('[data-add]'), function (b) { b.onclick = function () { var n = b.getAttribute('data-add'); if (plan.indexOf(n) < 0) plan.push(n); save(); ga('plan_add'); paint(); }; });
    var f = ROOT.querySelector('.pl-fill'); if (f) f.onclick = fill;
    var c = ROOT.querySelector('.pl-clear'); if (c) c.onclick = function () { if (!confirm('식단을 모두 비울까요?')) return; plan = []; days = {}; save(); paint(); };
    var cp = ROOT.querySelector('.pl-copy'); if (cp) cp.onclick = function () {
      var L = shopping().filter(function (x) { return !got[x.g]; }).map(function (x) { return '□ ' + x.g + (x.n > 1 ? ' (' + x.n + '개 메뉴)' : ''); });
      var t = '🛒 장보기 (' + plan.join(', ') + ')\n' + (L.length ? L.join('\n') : '(살 것이 없어요!)') + '\n\n' + location.href.split('#')[0]; ga('plan_copy', { n: L.length });
      var ok = function () { toast('장보기 목록을 복사했어요 (' + L.length + '개)'); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(ok, function () { prompt('복사해 가세요', t); }); else prompt('복사해 가세요', t);
    };
  }
  function fill() {
    var dis = LS('jupjup_rec_dis', {}), seed = new Date().getDate(), want = ['국물', '밥', '볶음', '조림', '반찬', '면', '전'];
    var pool = Object.keys(M).map(function (k) { return M[k]; }).filter(function (m) { return m.ph && plan.indexOf(m.n) < 0 && !dis[m.n]; });
    var pick = [];
    want.forEach(function (c, i) { var L = pool.filter(function (m) { return m.cat === c && pick.indexOf(m) < 0; }); if (L.length) pick.push(L[(seed * 7 + i * 13 + L.length) % L.length]); });
    pick.forEach(function (m) { if (plan.length < 14) plan.push(m.n); });
    save(); ga('plan_fill'); paint(); toast(pick.length + '개를 담았어요');
  }
  fetch('/assets/fridge/rec.json?v=' + new Date().toISOString().slice(0, 10)).then(function (r) { return r.json(); }).then(function (R) {
    R.r.forEach(function (x) { M[x[0]] = { n: x[0], e: x[1], m: x[2], cat: x[5], ph: x[6], need: x[7] }; });
    plan = plan.filter(function (n) { return M[n]; }); paint();
  }).catch(function () { ROOT.innerHTML = '<p class="pl-empty">메뉴 목록을 불러오지 못했어요. 새로고침 해 주세요.</p>'; });
})();
