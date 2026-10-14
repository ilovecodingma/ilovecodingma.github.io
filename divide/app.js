/* 재산분할 계산기: 모든 계산은 브라우저 안에서만. 금액 단위는 만원. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function man(v) {
    var s = v < 0 ? '-' : '', a = Math.abs(Math.round(v)), e = Math.floor(a / 10000), m = a % 10000;
    return s + (e ? e.toLocaleString('ko-KR') + '억 ' : '') + (m || !e ? m.toLocaleString('ko-KR') + '만' : '') + '원';
  }
  var who = ['A 명의', 'B 명의', '공동'];
  function row(box, name, amt, w, sp) {
    var d = document.createElement('div'); d.className = 'row5';
    d.innerHTML = '<input type="text" maxlength="14" value="' + esc(name) + '" placeholder="항목">' +
      '<input type="number" inputmode="numeric" min="0" value="' + amt + '" placeholder="만원">' +
      '<select>' + who.map(function (x, i) { return '<option value="' + i + '"' + (i === w ? ' selected' : '') + '>' + x + '</option>'; }).join('') + '</select>' +
      '<span><label><input type="checkbox"' + (sp ? ' checked' : '') + '>결혼전·상속</label><button class="rm" type="button" title="삭제">×</button></span>';
    d.querySelector('.rm').onclick = function () { d.remove(); };
    $(box).appendChild(d);
  }
  row('AS', '아파트', 60000, 2, false); row('AS', 'A 예금·주식', 5000, 0, false); row('AS', 'B 예금', 2000, 1, false);
  row('AS', 'A 예상 퇴직금', 4000, 0, false); row('AS', 'A 결혼 전 예금', 3000, 0, true);
  row('DS', '주택담보대출', 25000, 0, false); row('DS', '신용대출', 1000, 1, false);
  $('addA').onclick = function () { row('AS', '', '', 0, false); };
  $('addD').onclick = function () { row('DS', '', '', 0, false); };
  $('pa').oninput = function () { $('pav').textContent = this.value; };
  function read(box) {
    return [].map.call($(box).children, function (d) {
      var i = d.querySelectorAll('input'), v = parseFloat(i[1].value);
      return { n: i[0].value.trim(), a: isFinite(v) && v > 0 ? v : 0, w: +d.querySelector('select').value, sp: i[2].checked };
    }).filter(function (x) { return x.a > 0; });
  }
  var last = null;
  function render() {
    var A = read('AS'), D = read('DS'), inc = $('inc').checked, p = +$('pa').value / 100;
    var na = $('na').value.trim() || 'A', nb = $('nb').value.trim() || 'B';
    var hold = [0, 0], pool = 0, ex = 0;
    function add(x, sign) {
      var v = x.a * sign;
      if (x.sp && !inc) { ex += v; return; }
      pool += v;
      if (x.w === 2) { hold[0] += v / 2; hold[1] += v / 2; } else hold[x.w] += v;
    }
    A.forEach(function (x) { add(x, 1); }); D.forEach(function (x) { add(x, -1); });
    if (!A.length) { F.toast('재산을 한 줄 이상 입력하세요'); return; }
    var share = [pool * p, pool * (1 - p)], pay = [share[0] - hold[0], share[1] - hold[1]];
    last = { na: na, nb: nb, pool: pool, p: p, share: share, hold: hold, pay: pay, ex: ex };
    $('hd').textContent = '분할 대상 순재산 ' + man(pool) + ' · 기여도 ' + Math.round(p * 100) + ' : ' + Math.round((1 - p) * 100);
    var g = pay[0] > 0 ? [nb, na, pay[0]] : [na, nb, pay[1]];
    $('head').textContent = Math.abs(g[2]) < 1 ? '정산금 없음' : man(Math.abs(g[2]));
    $('sub').textContent = Math.abs(g[2]) < 1 ? '지금 명의대로 나눠도 몫과 같아요' : g[0] + ' → ' + g[1] + ' 정산금';
    $('c1').textContent = na; $('c2').textContent = nb;
    $('tb').innerHTML = '<tr><td><b>분할 몫</b></td><td>' + man(share[0]) + '</td><td>' + man(share[1]) + '</td></tr>' +
      '<tr><td><b>지금 명의 순재산</b></td><td>' + man(hold[0]) + '</td><td>' + man(hold[1]) + '</td></tr>' +
      '<tr><td><b>정산금</b></td><td>' + man(pay[0]) + '</td><td>' + man(pay[1]) + '</td></tr>' +
      (ex ? '<tr><td><b>제외한 특유재산</b></td><td colspan="2">' + man(ex) + ' (분할 대상에서 뺌)</td></tr>' : '');
    $('out').classList.remove('hide'); draw(); $('out').scrollIntoView({ behavior: 'smooth' });
    F.shareBar($('share'), { title: '재산분할 계산기', text: '재산분할 대충 계산해 보기', url: 'https://sungprofile.cloud/divide/', canvas: function () { return $('cv'); }, file: 'divide.png' });
    if (window.gtag) gtag('event', 'calc', { svc: 'divide' });
  }
  function draw() {
    var r = last, c = $('cv'), x = c.getContext('2d'); c.width = 1080; c.height = 760;
    x.fillStyle = '#eef5ff'; x.fillRect(0, 0, 1080, 760);
    x.fillStyle = '#1971c2'; x.font = '800 50px ' + F.FONT; x.fillText('재산분할 대략 계산', 70, 110);
    x.fillStyle = '#333'; x.font = '500 32px ' + F.FONT;
    x.fillText('분할 대상 순재산 ' + man(r.pool), 70, 190);
    x.fillText('기여도 ' + r.na + ' ' + Math.round(r.p * 100) + '% · ' + r.nb + ' ' + Math.round((1 - r.p) * 100) + '%', 70, 240);
    [[r.na, 0], [r.nb, 1]].forEach(function (q, k) {
      var y = 320 + k * 170; x.fillStyle = '#fff'; F.rr(x, 70, y, 940, 140, 24); x.fill();
      x.fillStyle = '#1971c2'; x.font = '800 36px ' + F.FONT; x.fillText(q[0], 100, y + 55);
      x.fillStyle = '#333'; x.font = '500 30px ' + F.FONT;
      x.fillText('몫 ' + man(r.share[q[1]]) + '  ·  정산금 ' + man(r.pay[q[1]]), 100, y + 105);
    });
    x.fillStyle = '#888'; x.font = '500 24px ' + F.FONT; x.fillText('참고용 계산이며 법률 자문이 아닙니다 · sungprofile.cloud/divide', 70, 720);
  }
  $('go').onclick = render;
})();
