/* 모임·여행 정산 계산기: 모든 계산은 브라우저 안에서만. */
(function () {
  var F = window.FUN, $ = function (i) { return document.getElementById(i); };
  var mem = ['나', '친구1', '친구2'];
  var exp = [{ label: '식비', amount: '', payer: 0, parts: [0, 1, 2] }];
  var last = null;
  function won(v) { return Math.round(v).toLocaleString('ko-KR') + '원'; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function nm(i) { return (mem[i] || '').trim() || '참여자' + (i + 1); }

  function drawMem() {
    var h = '';
    mem.forEach(function (m, i) {
      h += '<div class="row" style="margin:6px 0"><input type="text" maxlength="8" data-m="' + i + '" value="' + esc(m) + '" aria-label="참여자 ' + (i + 1) + '">' +
        (mem.length > 2 ? '<button type="button" class="btn del" data-dm="' + i + '" aria-label="삭제">×</button>' : '') + '</div>';
    });
    $('mem').innerHTML = h;
  }
  function drawExp() {
    var h = '';
    exp.forEach(function (e, i) {
      h += '<div class="qe"><div class="row"><input type="text" maxlength="12" placeholder="항목 (예: 숙소)" data-el="' + i + '" value="' + esc(e.label) + '" aria-label="항목 이름">' +
        '<input type="number" inputmode="numeric" min="0" placeholder="금액(원)" data-ea="' + i + '" value="' + esc(e.amount) + '" aria-label="금액">' +
        (exp.length > 1 ? '<button type="button" class="btn del" data-de="' + i + '" aria-label="삭제">×</button>' : '') + '</div>' +
        '<label>낸 사람</label><select data-ep="' + i + '" aria-label="낸 사람">';
      mem.forEach(function (m, j) { h += '<option value="' + j + '"' + (e.payer === j ? ' selected' : '') + '>' + esc(nm(j)) + '</option>'; });
      h += '</select><label>같이 나눌 사람</label><div class="chips">';
      mem.forEach(function (m, j) { h += '<button type="button" class="chip' + (e.parts.indexOf(j) > -1 ? ' on' : '') + '" data-et="' + i + ':' + j + '">' + esc(nm(j)) + '</button>'; });
      h += '</div></div>';
    });
    $('exp').innerHTML = h;
  }

  $('mem').addEventListener('input', function (e) { var i = e.target.getAttribute('data-m'); if (i !== null) mem[+i] = e.target.value; });
  $('mem').addEventListener('change', drawExp);
  $('mem').addEventListener('click', function (e) {
    var d = e.target.getAttribute('data-dm'); if (d === null) return; d = +d;
    mem.splice(d, 1);
    exp.forEach(function (x) {
      x.parts = x.parts.filter(function (j) { return j !== d; }).map(function (j) { return j > d ? j - 1 : j; });
      if (x.payer === d) x.payer = 0; else if (x.payer > d) x.payer--;
    });
    drawMem(); drawExp();
  });
  $('addm').onclick = function () {
    if (mem.length >= 20) { F.toast('최대 20명까지예요'); return; }
    mem.push('친구' + mem.length); exp.forEach(function (x) { x.parts.push(mem.length - 1); }); drawMem(); drawExp();
  };
  $('adde').onclick = function () {
    if (exp.length >= 40) { F.toast('최대 40개까지예요'); return; }
    exp.push({ label: '', amount: '', payer: 0, parts: mem.map(function (_, i) { return i; }) }); drawExp();
  };
  $('exp').addEventListener('input', function (e) {
    var t = e.target, a;
    if ((a = t.getAttribute('data-el')) !== null) exp[+a].label = t.value;
    else if ((a = t.getAttribute('data-ea')) !== null) exp[+a].amount = t.value;
  });
  $('exp').addEventListener('change', function (e) { var a = e.target.getAttribute('data-ep'); if (a !== null) exp[+a].payer = +e.target.value; });
  $('exp').addEventListener('click', function (e) {
    var t = e.target, a;
    if ((a = t.getAttribute('data-de')) !== null) { exp.splice(+a, 1); drawExp(); }
    else if ((a = t.getAttribute('data-et')) !== null) {
      var p = a.split(':'), x = exp[+p[0]], j = +p[1], k = x.parts.indexOf(j);
      if (k > -1) x.parts.splice(k, 1); else { x.parts.push(j); x.parts.sort(function (u, v) { return u - v; }); }
      t.classList.toggle('on');
    }
  });

  function calc() {
    var n = mem.length, paid = [], owed = [], i, total = 0, used = 0;
    for (i = 0; i < n; i++) { paid.push(0); owed.push(0); }
    for (i = 0; i < exp.length; i++) {
      var e = exp[i], a = Math.round(parseFloat(e.amount));
      if (!(a > 0)) continue;
      if (!e.parts.length) { F.toast('"' + (e.label || '항목 ' + (i + 1)) + '"에 같이 나눌 사람을 골라주세요'); return null; }
      var k = e.parts.length, base = Math.floor(a / k), rem = a - base * k;
      e.parts.forEach(function (j, idx) { owed[j] += base + (idx < rem ? 1 : 0); });
      paid[e.payer] += a; total += a; used++;
    }
    if (!used) { F.toast('금액을 입력한 항목이 없어요'); return null; }
    var bal = paid.map(function (p, j) { return p - owed[j]; });
    var cr = [], db = [];
    bal.forEach(function (b, j) { if (b > 0) cr.push([j, b]); else if (b < 0) db.push([j, -b]); });
    var tr = [];
    while (cr.length && db.length) {
      cr.sort(function (u, v) { return v[1] - u[1]; }); db.sort(function (u, v) { return v[1] - u[1]; });
      var m = Math.min(cr[0][1], db[0][1]);
      tr.push({ from: db[0][0], to: cr[0][0], amt: m });
      cr[0][1] -= m; db[0][1] -= m;
      if (cr[0][1] === 0) cr.shift();
      if (db[0][1] === 0) db.shift();
    }
    return { total: total, paid: paid, owed: owed, bal: bal, tr: tr, names: mem.map(function (_, j) { return nm(j); }), n: n };
  }

  function text(r) {
    var s = '[정산] 총 ' + won(r.total) + ' / ' + r.n + '명\n';
    if (!r.tr.length) return s + '서로 보낼 돈이 없어요.';
    r.tr.forEach(function (t) { s += r.names[t.from] + ' → ' + r.names[t.to] + ' ' + won(t.amt) + '\n'; });
    return s.trim();
  }

  function render() {
    var r = calc(); if (!r) return; last = r;
    $('out').classList.remove('hide');
    $('hd').textContent = '총 사용 금액';
    $('head').textContent = won(r.total);
    $('sub').textContent = r.tr.length ? r.tr.length + '번만 송금하면 정산 끝' : '서로 보낼 돈이 없어요';
    $('tr').innerHTML = r.tr.length ? r.tr.map(function (t) {
      return '<div class="kv"><span>' + esc(r.names[t.from]) + ' → ' + esc(r.names[t.to]) + '</span><b>' + won(t.amt) + '</b></div>';
    }).join('') : '<p class="note">모두 낸 만큼 썼어요.</p>';
    $('tb').innerHTML = r.names.map(function (name, j) {
      var b = r.bal[j];
      return '<tr><td>' + esc(name) + '</td><td>' + won(r.paid[j]) + '</td><td>' + won(r.owed[j]) + '</td><td>' + (b >= 0 ? '+' : '-') + won(Math.abs(b)) + '</td></tr>';
    }).join('');
    var cv = $('cv'), src = card(r); cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
    $('out').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function card(r) {
    var c = document.createElement('canvas'); c.width = 1080; c.height = 1350; var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 1080, 1350); g.addColorStop(0, '#0f5132'); g.addColorStop(.6, '#16a34a'); g.addColorStop(1, '#0ea5e9');
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    x.fillStyle = 'rgba(255,255,255,.14)'; F.rr(x, 60, 60, 960, 1230, 48); x.fill();
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '800 44px ' + F.FONT; x.fillText('정산 결과', 540, 150);
    x.font = '600 34px ' + F.FONT; x.globalAlpha = .9; x.fillText('총 ' + won(r.total) + ' · ' + r.n + '명', 540, 212); x.globalAlpha = 1;
    x.font = '900 84px ' + F.FONT; x.fillText(r.tr.length ? r.tr.length + '번만 보내면 끝' : '정산할 돈 없음', 540, 340);
    x.fillStyle = 'rgba(255,255,255,.16)'; F.rr(x, 110, 395, 860, 760, 32); x.fill();
    var max = 8, y = 480;
    r.tr.slice(0, max).forEach(function (t) {
      x.fillStyle = '#fff'; x.textAlign = 'left'; x.font = '700 38px ' + F.FONT; x.fillText(r.names[t.from] + ' → ' + r.names[t.to], 150, y);
      x.textAlign = 'right'; x.font = '800 40px ' + F.FONT; x.fillText(won(t.amt), 930, y); y += 84;
    });
    if (r.tr.length > max) { x.textAlign = 'center'; x.font = '600 30px ' + F.FONT; x.fillText('외 ' + (r.tr.length - max) + '건', 540, y); }
    x.fillStyle = '#fff'; x.textAlign = 'center'; x.font = '500 26px ' + F.FONT; x.globalAlpha = .85;
    x.fillText('항목별 균등 분할 · 1원 단위 정확', 540, 1215); x.globalAlpha = 1;
    x.font = '700 30px ' + F.FONT; x.fillText('sungprofile.cloud/split', 540, 1260);
    return c;
  }

  $('go').onclick = render;
  $('cp').onclick = function () { if (last) F.copy(text(last)); };
  F.shareBar($('share'), {
    title: '정산 결과', text: '정산 결과 정리해봤어요', url: 'https://sungprofile.cloud/split/',
    canvas: function () { return card(last || calc()); }, file: 'split-result.png'
  });
  drawMem(); drawExp();
})();
