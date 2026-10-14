/* 생일 선물 정산 도우미: 계산은 브라우저 안에서만, 장부는 localStorage 에만 저장. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  function won(v) { return Math.round(v).toLocaleString('ko-KR') + '원'; }
  function num(id) { var v = parseFloat($(id).value); return isFinite(v) && v >= 0 ? v : 0; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  document.querySelector('.tabs').onclick = function (e) {
    var t = e.target.getAttribute('data-t'); if (!t) return;
    [].forEach.call(this.children, function (b) { b.classList.toggle('on', b === e.target); });
    $('A').classList.toggle('hide', t !== 'A'); $('B').classList.toggle('hide', t !== 'B');
  };
  $('goA').onclick = function () {
    var who = $('who').value.trim() || '생일자', amt = num('amt'), n = Math.max(1, Math.floor(num('ppl'))), u = +$('unit').value;
    if (!amt) { F.toast('선물 총액을 입력하세요'); return; }
    var per = Math.ceil(amt / n / u) * u, rest = per * n - amt;
    $('per').textContent = won(per);
    $('perSub').textContent = '총 ' + won(amt) + ' ÷ ' + n + '명' + (rest ? ' · 올림으로 ' + won(rest) + ' 남아요' : '');
    $('warn').innerHTML = '⚠️ <b>' + esc(who) + '</b>님이 있는 단톡방에는 보내지 마세요. 선물 가격이 그대로 공개돼요. 생일자를 뺀 방을 따로 만들거나 1:1로 보내세요.';
    var m = '🤫 ' + who + ' 생일 선물 정산 (' + who + '한테는 비밀!)\n' +
      '선물 총액 ' + won(amt) + ' / ' + n + '명\n1인당 ' + won(per) + ' 보내주세요' + ($('due').value.trim() ? ' (' + $('due').value.trim() + '까지)' : '') + '\n' +
      ($('bank').value.trim() ? '계좌: ' + $('bank').value.trim() + '\n' : '') +
      (rest ? '남는 ' + won(rest) + '은 케이크·포장비에 보탤게요 🎂' : '딱 맞게 나눠졌어요 🎂');
    $('msg').value = m; $('outA').classList.remove('hide'); $('outA').scrollIntoView({ behavior: 'smooth' });
    if (window.gtag) gtag('event', 'calc', { svc: 'gift' });
  };
  $('cpA').onclick = function () { F.copy($('msg').value); };
  var K = 'lab_gift_book';
  function load() { try { return JSON.parse(localStorage.getItem(K)) || []; } catch (e) { return []; } }
  function save(a) { try { localStorage.setItem(K, JSON.stringify(a)); } catch (e) {} }
  function show() {
    var a = load(), m = {};
    a.forEach(function (x) { var p = m[x.n] = m[x.n] || { got: 0, gave: 0 }; p[x.d] += x.a; });
    var rows = Object.keys(m).sort().map(function (k) {
      var p = m[k], d = p.got - p.gave;
      return '<tr><td><b>' + esc(k) + '</b></td><td>' + won(p.got) + '</td><td>' + won(p.gave) + '</td><td>' + (d > 0 ? won(d) : '이미 충분') + '</td></tr>';
    });
    $('sum').innerHTML = rows.join('') || '<tr><td colspan="4" class="note">아직 기록이 없어요</td></tr>';
    $('hist').innerHTML = a.slice(-10).reverse().map(function (x) {
      return x.t + ' · ' + esc(x.n) + ' · ' + (x.d === 'got' ? '받음 ' : '줌 ') + won(x.a) + (x.m ? ' · ' + esc(x.m) : '');
    }).join('<br>') || '없음';
  }
  $('add').onclick = function () {
    var n = $('bn').value.trim(), amt = num('ba');
    if (!n || !amt) { F.toast('이름과 금액을 입력하세요'); return; }
    var a = load(); a.push({ n: n, d: $('bd').value, a: amt, m: $('bm').value.trim(), t: F.kstDate() }); save(a);
    $('ba').value = ''; $('bm').value = ''; show(); F.toast('추가했어요');
  };
  $('clr').onclick = function () { if (confirm('장부를 모두 지울까요?')) { save([]); show(); } };
  show();
})();
