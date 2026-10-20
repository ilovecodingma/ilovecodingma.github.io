// 2026-10-20 가입 유도 카드: 누르면 (로그인 안 했으면 가입 창 → ) 관심 주제를 prefs.topics 에 넣고 메일 소식을 켠다. 팝업·자동 이동 없음.
(function () {
  var LS = 'jupjup_join_t';
  function boot(tries) {
    var J = window.JUP;
    if (!J) { if (tries < 40) setTimeout(function () { boot(tries + 1); }, 100); return; }
    var cards = [].slice.call(document.querySelectorAll('.jn[data-t]'));
    var topicsOf = function (P) { return String((P && P.topics) || '').split(',').filter(Boolean); };
    var toast = function (m) { var t = document.createElement('div'); t.className = 'jn-t'; t.textContent = m; document.body.appendChild(t); setTimeout(function () { t.remove(); }, 3500); };
    var mark = function (el) { el.classList.add('done'); var b = el.querySelector('.jn-b'); if (b) { b.textContent = '✅ 받는 중'; b.onclick = function () { location.href = '/me/#topics'; }; } var s = el.querySelector('small'); if (s) s.innerHTML = '내 공간에서 주제를 바꾸거나 끌 수 있어요 → <a href="/me/#topics">설정</a>'; };
    var subscribe = function (t) {
      return J.api('/api/me').then(function (me) {
        var P = me.prefs || {}, cur = topicsOf(P); if (cur.indexOf(t) < 0) cur.push(t);
        var d = {}; for (var k in P) d[k] = P[k]; d.topics = cur.join(',').slice(0, 78); d.dg = '1';
        return J.api('/api/prefs', { method: 'POST', body: { data: d } }).then(function () { try { J.ga && J.ga('join_topic', { topic: t }); } catch (e) {} return cur; });
      });
    };
    var pend = ''; try { pend = localStorage.getItem(LS) || ''; } catch (e) {}
    if (J.st && J.st.t) {
      if (pend) { try { localStorage.removeItem(LS); } catch (e) {} subscribe(pend).then(function (cur) { toast('✅ 소식을 받을게요! 내 공간에서 바꿀 수 있어요.'); cards.forEach(function (c) { if (cur.indexOf(c.dataset.t) >= 0) mark(c); }); }).catch(function () {}); }
      else if (cards.length) J.api('/api/me').then(function (me) { var cur = topicsOf(me.prefs); cards.forEach(function (c) { if (cur.indexOf(c.dataset.t) >= 0) mark(c); }); }).catch(function () {});
    }
    cards.forEach(function (c) {
      var b = c.querySelector('.jn-b'); if (!b) return;
      b.onclick = function () {
        var t = c.dataset.t;
        if (!(J.st && J.st.t)) { try { localStorage.setItem(LS, t); } catch (e) {} try { J.ga && J.ga('join_click', { topic: t }); } catch (e) {} J.authModal(function () { location.reload(); }); return; }
        b.disabled = true;
        subscribe(t).then(function () { mark(c); b.disabled = false; toast('✅ 신청했어요. 다음 소식부터 보내 드려요.'); }).catch(function () { b.disabled = false; toast('지금은 신청이 안 돼요. 잠시 뒤에 다시 해 주세요.'); });
      };
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { boot(0); }); else boot(0);
})();
