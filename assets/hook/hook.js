/* 정보성 글 끝 「관련 시험 같이 준비하기」 — 글 내용에 맞는 시험을 골라 3문제를 바로 풀게 하고, 끝나면 가입을 권한다. */
(function () {
  'use strict';
  var box = document.getElementById('xhook'); if (!box) return;
  var tok = ''; try { tok = localStorage.getItem('jupjup_tok') || ''; } catch (e) {}
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var css = document.createElement('style');
  css.textContent = '#xhook{margin:34px 0 8px;padding:18px 18px 16px;border:1px solid rgba(255,92,154,.45);border-radius:14px;background:linear-gradient(135deg,rgba(108,123,255,.12),rgba(255,92,154,.10));color:inherit}' +
    '#xhook h2{margin:0 0 6px;font-size:19px;border:0;padding:0}#xhook p{margin:6px 0}#xhook .xq{margin:14px 0;padding-top:10px;border-top:1px dashed rgba(255,255,255,.18)}' +
    '#xhook .xo{display:block;width:100%;text-align:left;margin:6px 0;padding:10px 12px;border-radius:9px;border:1px solid rgba(255,255,255,.22);background:rgba(0,0,0,.18);color:inherit;font:inherit;cursor:pointer}' +
    '#xhook .xo:hover{border-color:#ff5c9a}#xhook .xo.ok{border-color:#3ecf8e;background:rgba(62,207,142,.18)}#xhook .xo.no{border-color:#ff4d6d;background:rgba(255,77,109,.18)}' +
    '#xhook .xb{display:inline-block;margin:6px 8px 0 0;padding:10px 16px;border-radius:9px;border:0;background:linear-gradient(90deg,#6c7bff,#ff5c9a);color:#fff;font:800 15px/1 inherit;cursor:pointer;text-decoration:none}' +
    '#xhook .xb.g{background:transparent;border:1px solid rgba(255,255,255,.3)}#xhook .xe{font-size:14px;opacity:.9;margin-top:6px}';
  document.head.appendChild(css);
  function txt() {
    var m = document.querySelector('main') || document.body;
    return (document.title || '') + ' ' + ((document.querySelector('h1') || {}).textContent || '') + ' ' + (m.textContent || '').slice(0, 4000);
  }
  function pick(idx) {
    var t = txt(), best = null, bs = 0;
    idx.forEach(function (b) {
      var s = 0;
      b.kw.split('|').forEach(function (k) {
        if (k.length < 2) return;
        var i = 0, c = 0;
        while ((i = t.indexOf(k, i)) >= 0 && c < 5) { c++; i += k.length; }
        s += c * (k.length >= 3 ? 2 : 1);
      });
      if (s > bs) { bs = s; best = b; }
    });
    return bs >= 3 ? best : null;
  }
  function join() { if (window.JUP && JUP.authModal) JUP.authModal(function () { location.reload(); }); else location.href = '/me/'; }
  function plain() {
    box.innerHTML = '<h2>📝 읽기만 하면 안 남는다</h2><p>시험 문제로 한 번 풀어봐야 남는다. 자격증·공무원·수능 문제은행 전부 무료다.</p><a class="xb" href="/exam/bank/">문제은행 가기</a>' + (tok ? '' : '<button class="xb g" type="button" id="xj">가입하고 살아남기</button>');
    var j = document.getElementById('xj'); if (j) j.onclick = join;
  }
  function run(b) {
    box.innerHTML = '<h2>📝 이 글 읽었으면 「' + esc(b.name) + '」도 같이 준비해</h2><p>읽고 바로 풀어야 머리에 남는다. 3문제만 풀어봐. 1분 걸린다.</p><button class="xb" type="button" id="xs">3문제 풀어보기</button> <a class="xb g" href="/exam/bank/' + esc(b.id) + '/">전체 ' + b.n + '문제 보기</a>';
    document.getElementById('xs').onclick = function () {
      this.disabled = true; this.textContent = '불러오는 중…';
      fetch('/assets/hook/b/' + b.id + '.json').then(function (r) { return r.json(); }).then(function (d) { quiz(b, d.qs); }).catch(function () { location.href = '/exam/bank/' + b.id + '/'; });
    };
  }
  function quiz(b, all) {
    var qs = all.slice().sort(function () { return Math.random() - .5; }).slice(0, 3), done = 0, ok = 0, h = '<h2>📝 「' + esc(b.name) + '」 3문제</h2>';
    qs.forEach(function (q, i) {
      h += '<div class="xq" data-i="' + i + '"><p><b>' + (i + 1) + '.</b> ' + esc(q.q) + '</p>' + q.c.map(function (c, k) { return '<button type="button" class="xo" data-k="' + k + '">' + esc(c) + '</button>'; }).join('') + '<div class="xe" hidden></div></div>';
    });
    h += '<div id="xr"></div>'; box.innerHTML = h;
    box.querySelectorAll('.xq').forEach(function (el) {
      var q = qs[+el.getAttribute('data-i')];
      el.querySelectorAll('.xo').forEach(function (btn) {
        btn.onclick = function () {
          if (el.getAttribute('data-d')) return; el.setAttribute('data-d', '1');
          var k = +btn.getAttribute('data-k'), right = k === q.a; if (right) ok++;
          btn.classList.add(right ? 'ok' : 'no'); if (!right) el.querySelectorAll('.xo')[q.a].classList.add('ok');
          var e = el.querySelector('.xe'); e.hidden = false; e.textContent = (right ? '맞았다. ' : '틀렸다. 정답 ' + (q.a + 1) + '번. ') + (q.e || '');
          if (++done === qs.length) end();
        };
      });
    });
    function end() {
      var p = Math.round(ok / qs.length * 100), w = qs.length - ok;
      try { if (window.jamQ) window.jamQ(b.id, qs.length, p); } catch (e) {}
      var r = '<h2 style="margin-top:16px">' + ok + '/' + qs.length + ' 맞았다</h2>';
      if (tok) r += '<p>' + (w ? '틀린 ' + w + '개 상태창에 반영된다. 나머지도 풀어서 지력부터 올려라.' : '다 맞았네. 다음 시험도 풀어봐.') + '</p>';
      else r += '<p><b>' + (w >= 2 ? '이 점수로 살아남겠냐?' : w === 1 ? '하나 틀렸다. 시험장에선 그 하나가 떨어지는 점수다.' : '3개 다 맞혔다고 끝난 게 아니다. 이거 저장 안 된다.') + '</b> 가입하면 점수와 틀린 문제가 계정에 쌓이고 헬조선 생존 확률이 나온다. 목표를 정하면 플랜과 오늘의 퀘스트도 던져 준다. 전부 무료다.</p><button class="xb" type="button" id="xj">가입하고 살아남기</button>';
      r += '<a class="xb g" href="/exam/bank/' + esc(b.id) + '/">전체 ' + b.n + '문제 풀기</a><button class="xb g" type="button" id="xa">다른 3문제</button>';
      var x = document.getElementById('xr'); x.innerHTML = r;
      var j = document.getElementById('xj'); if (j) j.onclick = join;
      document.getElementById('xa').onclick = function () { quiz(b, all); };
    }
  }
  fetch('/assets/hook/idx.json').then(function (r) { return r.json(); }).then(function (idx) { var b = pick(idx); if (b) run(b); else plain(); }).catch(function () { plain(); });
})();
