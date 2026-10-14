/* 대리효도 체크: 모든 계산은 브라우저 안에서만. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  var T = [
    ['생신상·생신 모임 준비', 1, 5], ['안부 전화', 52, 0.25], ['병원 동행·입원 간병', 2, 5], ['명절 음식·준비', 2, 8],
    ['김장', 1, 10], ['선물 고르기·구매', 4, 2], ['폰·가전 교체 등 생활 도움', 2, 3], ['건강검진 예약·결과 설명', 1, 1.5]
  ];
  var W = ['남편', '아내', '같이', '안 함'];
  function list(id, defs) {
    var h = '<div class="hd2"><span>할 일</span><span class="cen">연 횟수</span><span class="cen">1회 시간</span></div>';
    T.forEach(function (t, i) {
      h += '<div class="it"><b>' + t[0] + '</b><input type="number" min="0" step="1" id="' + id + 'n' + i + '" value="' + t[1] + '"><input type="number" min="0" step="0.25" id="' + id + 'h' + i + '" value="' + t[2] + '"></div>' +
        '<div class="who" data-k="' + id + i + '">' + W.map(function (w, j) { return '<button type="button" data-v="' + j + '"' + (j === defs[i] ? ' class="on"' : '') + '>' + w + '</button>'; }).join('') + '</div>';
    });
    $(id).innerHTML = h;
  }
  list('L1', [1, 1, 1, 1, 2, 1, 1, 1]); list('L2', [1, 1, 3, 1, 3, 1, 1, 1]);
  document.addEventListener('click', function (e) {
    var b = e.target; if (!b.parentNode || !b.parentNode.classList || !b.parentNode.classList.contains('who')) return;
    [].forEach.call(b.parentNode.children, function (x) { x.classList.remove('on'); }); b.classList.add('on');
  });
  function sel(id, i) { var o = document.querySelector('[data-k="' + id + i + '"] .on'); return o ? +o.getAttribute('data-v') : 3; }
  function num(id) { var v = parseFloat($(id).value); return isFinite(v) && v >= 0 ? v : 0; }
  function side(id) {
    var h = 0, w = 0, rows = [];
    T.forEach(function (t, i) {
      var tot = num(id + 'n' + i) * num(id + 'h' + i), s = sel(id, i);
      var a = s === 0 ? tot : s === 2 ? tot / 2 : 0, b = s === 1 ? tot : s === 2 ? tot / 2 : 0;
      h += a; w += b; rows.push([t[0], a, b]);
    });
    return { h: h, w: w, rows: rows };
  }
  function hr(v) { return (Math.round(v * 10) / 10).toLocaleString('ko-KR') + '시간'; }
  function won(v) { return Math.round(v).toLocaleString('ko-KR') + '원'; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var last = null;
  function render() {
    var nh = $('nh').value.trim() || '남편', nw = $('nw').value.trim() || '아내';
    var a = side('L1'), b = side('L2');
    var ta = a.h + a.w, tb = b.h + b.w;
    var pa = ta ? Math.round(a.w / ta * 100) : 0, pb = tb ? Math.round(b.h / tb * 100) : 0;
    var r = { nh: nh, nw: nw, a: a, b: b, pa: pa, pb: pb, m1: num('m1'), m2: num('m2'), H: a.h + b.h, Wt: a.w + b.w };
    last = r;
    $('head').textContent = pa + '%';
    $('sub').textContent = '시댁 일 1년 ' + hr(ta) + ' 중 ' + nw + ' ' + hr(a.w) + ' · 처가 일 중 ' + nh + ' 몫 ' + pb + '%';
    $('c1').textContent = nh; $('c2').textContent = nw;
    $('tb').innerHTML = '<tr><td><b>시댁 일</b></td><td>' + hr(a.h) + '</td><td>' + hr(a.w) + '</td></tr>' +
      '<tr><td><b>처가 일</b></td><td>' + hr(b.h) + '</td><td>' + hr(b.w) + '</td></tr>' +
      '<tr><td><b>양가 합계</b></td><td>' + hr(r.H) + '</td><td>' + hr(r.Wt) + '</td></tr>' +
      '<tr><td><b>월 용돈</b></td><td>시댁 ' + won(r.m1) + '</td><td>처가 ' + won(r.m2) + '</td></tr>';
    var top = a.rows.filter(function (x) { return x[2] > x[1]; }).sort(function (x, y) { return (y[2] - y[1]) - (x[2] - x[1]); }).slice(0, 3).map(function (x) { return x[0]; });
    var msg = pa >= 60 ? '시댁 효도의 ' + pa + '%를 ' + nw + '가 하고 있어요. ' + (top.length ? '특히 ' + top.join(', ') + '부터 ' + nh + '가 직접 맡아보는 건 어때요?' : '')
      : pa >= 40 ? '시댁 효도는 비교적 반반에 가까워요.' : '시댁 효도는 ' + nh + '가 주로 하고 있어요.';
    if (r.m1 || r.m2) msg += ' 용돈은 시댁 ' + won(r.m1) + ', 처가 ' + won(r.m2) + (r.m1 === r.m2 ? '로 같아요.' : '로 차이가 ' + won(Math.abs(r.m1 - r.m2)) + ' 나요.');
    $('talk').innerHTML = '<b>한 줄 정리</b><p style="margin:6px 0 0">' + esc(msg) + '</p>';
    $('out').classList.remove('hide'); draw(); $('out').scrollIntoView({ behavior: 'smooth' });
    F.shareBar($('share'), { title: '대리효도 체크', text: '우리집 시댁 효도 중 아내 몫 ' + pa + '%. 너희 집은?', url: 'https://sungprofile.cloud/hyodo/', canvas: function () { return $('cv'); }, file: 'hyodo.png' });
    if (window.gtag) gtag('event', 'calc', { svc: 'hyodo' });
  }
  function draw() {
    var r = last, c = $('cv'), x = c.getContext('2d'); c.width = 1080; c.height = 1080;
    x.fillStyle = '#fff4ec'; x.fillRect(0, 0, 1080, 1080);
    x.fillStyle = '#d9480f'; x.font = '800 54px ' + F.FONT; x.fillText('우리집 대리효도 체크', 80, 140);
    x.fillStyle = '#333'; x.font = '500 34px ' + F.FONT; x.fillText('시댁 효도 중 ' + r.nw + '가 한 비율', 80, 230);
    x.fillStyle = '#d9480f'; x.font = '900 190px ' + F.FONT; x.fillText(r.pa + '%', 70, 420);
    function bar(y, label, a, b) {
      var t = a + b || 1; x.fillStyle = '#333'; x.font = '700 34px ' + F.FONT; x.fillText(label, 80, y);
      if (a > 0) { x.fillStyle = '#4c6ef5'; F.rr(x, 80, y + 20, 920 * a / t, 56, 12); x.fill(); }
      if (b > 0) { x.fillStyle = '#d9480f'; F.rr(x, 80 + 920 * a / t, y + 20, 920 * b / t, 56, 12); x.fill(); }
      x.fillStyle = '#555'; x.font = '500 28px ' + F.FONT; x.fillText(r.nh + ' ' + hr(a) + '  ·  ' + r.nw + ' ' + hr(b), 80, y + 120);
    }
    bar(520, '시댁 일 (1년)', r.a.h, r.a.w); bar(720, '처가 일 (1년)', r.b.h, r.b.w);
    x.fillStyle = '#888'; x.font = '500 28px ' + F.FONT; x.fillText('파랑 ' + r.nh + ' · 주황 ' + r.nw + '   |   sungprofile.cloud/hyodo', 80, 1000);
  }
  $('go').onclick = render;
})();
