/* 러닝 페이스 계산기: 모든 계산은 브라우저 안에서만. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  var mode = 't', last = null;
  var NAMES = [[5, '5K'], [10, '10K'], [21.0975, '하프'], [42.195, '풀']];
  function p2(n) { return (n < 10 ? '0' : '') + n; }
  function hms(s) {
    s = Math.round(s); var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    return h > 0 ? h + ':' + p2(m) + ':' + p2(x) : m + ':' + p2(x);
  }
  function pace(s) { s = Math.round(s); return Math.floor(s / 60) + "'" + p2(s % 60) + '"'; }
  function dstr(d) { return String(+d.toFixed(4)); }
  function n(id) { var v = parseFloat($(id).value); return isFinite(v) && v >= 0 ? v : 0; }

  function calc() {
    var d = parseFloat($('dist').value);
    if (!(d > 0)) { F.toast('거리를 입력하세요'); return null; }
    var T, P;
    if (mode === 't') {
      T = n('th') * 3600 + n('tm') * 60 + n('ts');
      if (!(T > 0)) { F.toast('기록을 입력하세요'); return null; }
      P = T / d;
    } else {
      P = n('pm') * 60 + n('ps');
      if (!(P > 0)) { F.toast('페이스를 입력하세요'); return null; }
      T = P * d;
    }
    return { d: d, T: T, P: P };
  }

  function render() {
    var r = calc(); if (!r) return; last = r;
    $('hd').textContent = dstr(r.d) + 'km · ' + hms(r.T);
    $('pc').textContent = pace(r.P);
    $('ft').textContent = hms(r.T);
    $('sp').textContent = (3600 / r.P).toFixed(2) + ' km/h';
    $('dd').textContent = dstr(r.d) + ' km';
    var step = r.d <= 12 ? 1 : 5, rows = '', k;
    for (k = step; k < r.d - 1e-9; k += step) rows += '<tr><td>' + k + 'km</td><td>' + hms(r.P * k) + '</td></tr>';
    rows += '<tr class="hl"><td>' + dstr(r.d) + 'km (도착)</td><td>' + hms(r.T) + '</td></tr>';
    $('spl').innerHTML = rows;
    $('splnote').textContent = (step === 1 ? '1km마다' : '5km마다') + ' 같은 페이스로 달리는 이븐 페이스 기준입니다.';
    var g = '';
    NAMES.forEach(function (x) {
      var t = r.T * Math.pow(x[0] / r.d, 1.06), same = Math.abs(x[0] - r.d) < 1e-6;
      g += '<tr' + (same ? ' class="hl"' : '') + '><td>' + x[1] + '</td><td>' + hms(t) + '</td><td>' + pace(t / x[0]) + '/km</td></tr>';
    });
    $('rg').innerHTML = g;
    var cv = $('cv'), src = card(r); cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
  }

  function card(r) {
    var c = document.createElement('canvas'); c.width = 1080; c.height = 1350; var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 1080, 1350); g.addColorStop(0, '#0b4f6c'); g.addColorStop(.6, '#0ea5a4'); g.addColorStop(1, '#3b82f6');
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    x.fillStyle = 'rgba(255,255,255,.14)'; F.rr(x, 60, 60, 960, 1230, 48); x.fill();
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '800 44px ' + F.FONT; x.fillText('RUNNING PACE CARD', 540, 150);
    x.font = '600 36px ' + F.FONT; x.globalAlpha = .9; x.fillText(dstr(r.d) + 'km · ' + hms(r.T), 540, 215); x.globalAlpha = 1;
    x.font = '900 230px ' + F.FONT; x.fillText(pace(r.P), 540, 480);
    x.font = '700 44px ' + F.FONT; x.fillText('/ km 페이스', 540, 550);
    x.font = '600 38px ' + F.FONT; x.fillText('평균 ' + (3600 / r.P).toFixed(2) + ' km/h', 540, 620);
    x.fillStyle = 'rgba(255,255,255,.16)'; F.rr(x, 110, 680, 860, 500, 32); x.fill();
    x.fillStyle = '#fff'; x.font = '800 36px ' + F.FONT; x.textAlign = 'left'; x.fillText('이 실력이면 예상 기록', 150, 745);
    NAMES.forEach(function (nm, i) {
      var t = r.T * Math.pow(nm[0] / r.d, 1.06), y = 825 + i * 85;
      x.font = '700 40px ' + F.FONT; x.textAlign = 'left'; x.fillText(nm[1], 150, y);
      x.textAlign = 'right'; x.font = '800 42px ' + F.FONT; x.fillText(hms(t), 930, y);
    });
    x.font = '500 26px ' + F.FONT; x.textAlign = 'left'; x.globalAlpha = .85; x.fillText('리글 공식 기준 단순 추정 · 참고용', 150, 1140); x.globalAlpha = 1;
    x.textAlign = 'center'; x.font = '700 30px ' + F.FONT; x.fillText('sungprofile.cloud/pace', 540, 1250);
    return c;
  }

  function setActive(box, attr, val) {
    [].forEach.call(box.querySelectorAll('.chip'), function (b) { b.classList.toggle('on', b.getAttribute(attr) === String(val)); });
  }
  $('dch').onclick = function (e) {
    var d = e.target.getAttribute && e.target.getAttribute('data-d'); if (!d) return;
    $('dist').value = d; setActive($('dch'), 'data-d', d); render();
  };
  $('dist').oninput = function () {
    var v = parseFloat($('dist').value), hit = '';
    NAMES.forEach(function (x) { if (Math.abs(x[0] - v) < 1e-6) hit = x[0]; });
    setActive($('dch'), 'data-d', hit);
  };
  $('mch').onclick = function (e) {
    var m = e.target.getAttribute && e.target.getAttribute('data-m'); if (!m) return;
    mode = m; setActive($('mch'), 'data-m', m);
    $('bt').classList.toggle('hide', m !== 't'); $('bp').classList.toggle('hide', m !== 'p'); render();
  };
  $('go').onclick = render;
  ['th', 'tm', 'ts', 'pm', 'ps', 'dist'].forEach(function (id) { $(id).addEventListener('input', function () { if (calc()) render(); }); });
  F.shareBar($('share'), {
    title: '러닝 페이스 카드', text: '내 러닝 페이스 카드 만들어봤어요', url: 'https://sungprofile.cloud/pace/',
    canvas: function () { return card(last || calc()); }, file: 'running-pace.png'
  });
  render();
})();
