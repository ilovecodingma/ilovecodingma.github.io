/* 부부 생활비 분담 계산기: 모든 계산은 브라우저 안에서만. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  var last = null, DAYS = 365 / 12;
  function won(v) { return Math.round(v).toLocaleString('ko-KR') + '원'; }
  function num(id) { var v = parseFloat($(id).value); return isFinite(v) && v >= 0 ? v : 0; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function calc() {
    var r = {
      n1: $('n1').value.trim() || '나', n2: $('n2').value.trim() || '배우자',
      i1: num('i1'), i2: num('i2'), tot: num('tot'), h1: num('h1'), h2: num('h2'), rate: num('rate')
    };
    if (!(r.tot > 0)) { F.toast('공동 생활비를 입력하세요'); return null; }
    if (!(r.i1 + r.i2 > 0)) { F.toast('월 소득을 입력하세요'); return null; }
    r.v1 = r.h1 * DAYS * r.rate; r.v2 = r.h2 * DAYS * r.rate;
    function split(a, b) { var s = a + b, p = s > 0 ? Math.round(r.tot * a / s) : Math.round(r.tot / 2); return [p, r.tot - p]; }
    function house() {
      var pool = r.tot + r.v1 + r.v2, p = Math.round(pool * r.i1 / (r.i1 + r.i2) - r.v1);
      p = Math.max(0, Math.min(r.tot, p)); return [p, r.tot - p];
    }
    r.m = [
      { k: '반반', s: [Math.round(r.tot / 2), r.tot - Math.round(r.tot / 2)] },
      { k: '소득 비례', s: split(r.i1, r.i2) },
      { k: '집안일 반영', s: house() }
    ];
    r.m.forEach(function (x) { x.left = [r.i1 - x.s[0], r.i2 - x.s[1]]; });
    return r;
  }

  function render() {
    var r = calc(); if (!r) return; last = r;
    var pr = r.m[1], pc = Math.round(pr.s[0] / r.tot * 100);
    $('hd').textContent = '월 공동 생활비 ' + won(r.tot);
    $('head').textContent = pc + ' : ' + (100 - pc);
    $('sub').textContent = '소득 비례로 나누면 ' + r.n1 + ' ' + won(pr.s[0]) + ', ' + r.n2 + ' ' + won(pr.s[1]);
    $('c1').textContent = r.n1; $('c2').textContent = r.n2;
    var t = '';
    r.m.forEach(function (x) {
      t += '<tr><td><b>' + x.k + '</b></td>' + [0, 1].map(function (j) {
        return '<td>' + won(x.s[j]) + '<br><span class="note">남는 돈 ' + won(x.left[j]) + '</span></td>';
      }).join('') + '</tr>';
    });
    $('tb').innerHTML = t;
    $('hw').innerHTML = '<div class="kv"><span>' + esc(r.n1) + ' (하루 ' + r.h1 + '시간)</span><b>월 약 ' + won(r.v1) + '</b></div>' +
      '<div class="kv"><span>' + esc(r.n2) + ' (하루 ' + r.h2 + '시간)</span><b>월 약 ' + won(r.v2) + '</b></div>';
    var cv = $('cv'), src = card(r); cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
  }

  function card(r) {
    var c = document.createElement('canvas'); c.width = 1080; c.height = 1350; var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 1080, 1350); g.addColorStop(0, '#7a1f4d'); g.addColorStop(.6, '#e5578a'); g.addColorStop(1, '#f59e0b');
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    x.fillStyle = 'rgba(255,255,255,.14)'; F.rr(x, 60, 60, 960, 1230, 48); x.fill();
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '800 44px ' + F.FONT; x.fillText('생활비 분담 카드', 540, 150);
    x.font = '600 34px ' + F.FONT; x.globalAlpha = .9; x.fillText('월 공동 생활비 ' + won(r.tot), 540, 212); x.globalAlpha = 1;
    var pr = r.m[1], pc = Math.round(pr.s[0] / r.tot * 100);
    x.font = '900 120px ' + F.FONT; x.fillText(pc + ' : ' + (100 - pc), 540, 395);
    x.font = '700 38px ' + F.FONT; x.fillText('소득 비례 분담 비율', 540, 460);
    x.textAlign = 'left'; x.font = '800 34px ' + F.FONT;
    x.fillText(r.n1, 150, 560); x.textAlign = 'right'; x.fillText(r.n2, 930, 560);
    x.fillStyle = 'rgba(255,255,255,.16)'; F.rr(x, 110, 585, 860, 580, 32); x.fill();
    r.m.forEach(function (m, i) {
      var y = 650 + i * 185;
      x.fillStyle = '#fff'; x.textAlign = 'center'; x.font = '800 34px ' + F.FONT; x.fillText(m.k, 540, y);
      x.font = '800 44px ' + F.FONT; x.textAlign = 'left'; x.fillText(won(m.s[0]), 150, y + 62);
      x.textAlign = 'right'; x.fillText(won(m.s[1]), 930, y + 62);
      x.font = '500 26px ' + F.FONT; x.globalAlpha = .85; x.textAlign = 'left'; x.fillText('남는 돈 ' + won(m.left[0]), 150, y + 105);
      x.textAlign = 'right'; x.fillText('남는 돈 ' + won(m.left[1]), 930, y + 105); x.globalAlpha = 1;
    });
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '500 26px ' + F.FONT; x.globalAlpha = .85;
    x.fillText('집안일 시간가치 ' + won(r.rate) + '/시간 · 대화용 참고 계산', 540, 1215); x.globalAlpha = 1;
    x.font = '700 30px ' + F.FONT; x.fillText('sungprofile.cloud/fair', 540, 1260);
    return c;
  }

  $('go').onclick = render;
  ['n1', 'n2', 'i1', 'i2', 'tot', 'h1', 'h2', 'rate'].forEach(function (id) { $(id).addEventListener('input', function () { if (calc()) render(); }); });
  F.shareBar($('share'), {
    title: '부부 생활비 분담 카드', text: '우리 집 생활비 분담 계산해봤어요', url: 'https://sungprofile.cloud/fair/',
    canvas: function () { return card(last || calc()); }, file: 'fair-split.png'
  });
  render();
})();
