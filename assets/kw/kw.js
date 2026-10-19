// 2026-10-20 키워드 놀이판: 퀴즈 + 내일 예측 투표 (로그인 없음, 중복은 브라우저 저장)
(function () {
  var el = document.getElementById('kw-data'); if (!el) return;
  var D; try { D = JSON.parse(el.textContent); } catch (e) { return; }
  var API = document.body.dataset.api || 'https://jupjup-api.sung2011103.workers.dev';
  var h = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };

  // 퀴즈
  var Q = D.q || [], qb = document.getElementById('kwq');
  if (qb && Q.length) {
    var qi = 0, hit = 0;
    var show = function () {
      qb.textContent = '';
      if (qi >= Q.length) { qb.appendChild(h('p', 'kwq-q', '결과: ' + hit + ' / ' + Q.length + '개 맞혔어요!')); var r = h('button', 'kwq-n', '다시 하기'); r.onclick = function () { qi = 0; hit = 0; show(); }; qb.appendChild(r); return; }
      var q = Q[qi];
      qb.appendChild(h('p', 'kwq-q', (qi + 1) + '/' + Q.length + ' 「' + q.k + '」 키워드는 왜 떴을까요?'));
      var done = false, rs = h('div', 'kwq-r');
      q.opts.forEach(function (o) {
        var b = h('button', 'kwq-o', o.t); b.type = 'button';
        b.onclick = function () {
          if (done) return; done = true;
          if (o.ok) hit++;
          [].forEach.call(qb.querySelectorAll('.kwq-o'), function (x, i) { x.classList.add(q.opts[i].ok ? 'ok' : 'no'); });
          rs.appendChild(document.createTextNode(o.ok ? '⭕ 맞아요! ' : '❌ 아쉬워요. 정답은 초록색이에요. '));
          var c = q.opts.filter(function (z) { return z.ok; })[0];
          if (c && c.u) { var a = h('a', '', c.o + ' 원문 보기 →'); a.href = c.u; a.target = '_blank'; a.rel = 'noopener nofollow'; rs.appendChild(a); }
          var nx = h('button', 'kwq-n', qi + 1 < Q.length ? '다음 문제' : '결과 보기'); nx.onclick = function () { qi++; show(); }; rs.appendChild(document.createElement('br')); rs.appendChild(nx);
        };
        qb.appendChild(b);
      });
      qb.appendChild(rs);
    };
    show();
  }

  // 내일도 남을까? 투표
  var V = D.v || {}, vb = document.getElementById('kwv'), yb = document.getElementById('kwy');
  var get = function (day) { return fetch(API + '/api/kwvote?day=' + day).then(function (r) { return r.json(); }).then(function (j) { return j.votes || {}; }).catch(function () { return null; }); };
  var bars = function (host, items, votes, mark) {
    var tot = 0; items.forEach(function (c) { tot += votes[c.slug] || 0; });
    items.forEach(function (c) {
      var n = votes[c.slug] || 0, p = tot ? Math.round(n / tot * 100) : 0;
      var r = h('div', 'kwv-r'); var i = h('i'); i.style.width = p + '%'; r.appendChild(i);
      r.appendChild(h('span', '', (mark ? (c.alive ? '✅ ' : '❌ ') : '') + c.k + ' — ' + n + '표 (' + p + '%)' + (mark ? (c.alive ? ' · 오늘도 올랐어요' : ' · 오늘은 안 보여요') : '')));
      host.appendChild(r);
    });
    if (!tot) host.appendChild(h('p', 'kwn', '아직 투표가 없어요.'));
  };
  if (vb && V.cands && V.cands.length) {
    var key = 'kwv:' + V.day, mine = null; try { mine = localStorage.getItem(key); } catch (e) {}
    var result = function () { vb.textContent = ''; vb.appendChild(h('p', 'kwn', '내가 고른 키워드: ' + ((V.cands.filter(function (c) { return c.slug === mine; })[0] || {}).k || '')));
      get(V.day).then(function (v) { if (v) bars(vb, V.cands, v, false); else vb.appendChild(h('p', 'kwn', '결과를 불러오지 못했어요.')); }); };
    if (mine) result(); else V.cands.forEach(function (c) {
      var b = h('button', 'kwv-b', c.k); b.type = 'button';
      b.onclick = function () {
        fetch(API + '/api/kwvote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ day: V.day, k: c.slug }) }).then(function () { try { localStorage.setItem(key, c.slug); } catch (e) {} mine = c.slug; result(); }).catch(function () { vb.appendChild(h('p', 'kwn', '지금은 투표를 보낼 수 없어요. 잠시 뒤 다시 해 주세요.')); });
      };
      vb.appendChild(b);
    });
  }
  if (yb) {
    if (V.y && V.y.items && V.y.items.length) {
      yb.appendChild(h('h3', '', '📅 어제 예측 결과 (' + V.y.day.slice(5).replace('-', '/') + ')'));
      var alive = V.y.items.filter(function (c) { return c.alive; }).length;
      yb.appendChild(h('p', 'kwn', '어제 후보 ' + V.y.items.length + '개 중 ' + alive + '개가 오늘도 급상승 목록에 올랐어요(생존율 ' + Math.round(alive / V.y.items.length * 100) + '%).'));
      get(V.y.day).then(function (v) { bars(yb, V.y.items, v || {}, true); });
    } else yb.appendChild(h('p', 'kwn', '어제 후보 결과는 내일부터 여기에 나와요.'));
  }
})();
