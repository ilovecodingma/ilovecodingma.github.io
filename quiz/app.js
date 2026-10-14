/* 찐친 모의고사 메이커 - 서버 없이 링크(#q=...)에 퀴즈 데이터를 담아 공유합니다. */
(function () {
  var F = window.FUN, $ = F.$;
  var MAXQ = 10, MINQ = 3;
  var SAMPLES = {
    me: { t: '나 얼마나 알아? 찐친 모의고사', q: [
      ['내가 가장 좋아하는 음식은?', ['떡볶이', '치킨', '마라탕', '초밥'], 0],
      ['내가 못 참는 것은?', ['지각', '더위', '배고픔', '잠 부족'], 2],
      ['내가 쉬는 날 제일 먼저 하는 일은?', ['늦잠', '넷플릭스', '청소', '약속 잡기'], 0],
      ['내 휴대폰 배터리는 보통 몇 %일까?', ['10% 이하', '30% 안팎', '70% 안팎', '항상 100%'], 1],
      ['내가 해보고 싶은 여행지는?', ['제주', '도쿄', '파리', '집이 최고'], 3]] },
    pair: { t: '우리 사이 모의고사', q: [
      ['우리가 처음 만난 계절은?', ['봄', '여름', '가을', '겨울'], 0],
      ['내가 서운할 때 보이는 행동은?', ['말수가 줄어든다', '바로 말한다', '잠수를 탄다', '먹는 걸로 푼다'], 0],
      ['내가 가장 좋아하는 데이트는?', ['맛집 탐방', '영화관', '산책', '집콕'], 3],
      ['내가 제일 싫어하는 음식은?', ['오이', '고수', '민트초코', '가지'], 1]] },
    fan: { t: '입덕 N년차 덕력 모의고사', q: [
      ['내 최애를 좋아하게 된 계기는?', ['무대 영상', '예능 클립', '친구 추천', '알고리즘'], 0],
      ['내가 가장 많이 돌려본 영상은?', ['직캠', '라이브', '뮤직비디오', '비하인드'], 2],
      ['올해 내가 가장 기다리는 일정은?', ['컴백', '콘서트', '팬미팅', '생일'], 0]] }
  };

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === 'text') e.textContent = attrs[k]; else if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }

  /* ---------- 인코딩 ---------- */
  function b64u(bytes) { var s = ''; for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
  function unb64u(s) { s = s.replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; var b = atob(s), a = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }
  function streamBytes(stream, input) {
    var w = stream.writable.getWriter(); w.write(input); w.close();
    return new Response(stream.readable).arrayBuffer().then(function (b) { return new Uint8Array(b); });
  }
  function encode(obj) {
    var raw = new TextEncoder().encode(JSON.stringify(obj));
    if (typeof CompressionStream !== 'undefined') {
      return streamBytes(new CompressionStream('deflate-raw'), raw).then(function (z) { return 'z' + b64u(z); });
    }
    return Promise.resolve('p' + b64u(raw));
  }
  function decode(s) {
    var kind = s.charAt(0), bytes = unb64u(s.slice(1));
    var p = kind === 'z'
      ? (typeof DecompressionStream === 'undefined' ? Promise.reject(new Error('nostream')) : streamBytes(new DecompressionStream('deflate-raw'), bytes))
      : Promise.resolve(bytes);
    return p.then(function (b) { return JSON.parse(new TextDecoder().decode(b)); });
  }

  /* ---------- 만들기 ---------- */
  var qBox = $('#qlist');
  function addQ(data) {
    if (qBox.children.length >= MAXQ) { F.toast('문제는 최대 ' + MAXQ + '개까지예요'); return; }
    var idx = qBox.children.length, name = 'ans' + Date.now() + idx;
    var box = el('div', { class: 'qe' });
    box.appendChild(el('div', { class: 'qn', text: '문제 ' + (idx + 1) }));
    var qi = el('input', { type: 'text', maxlength: '60', placeholder: '문제를 입력하세요 (예: 내가 제일 좋아하는 음식은?)' });
    box.appendChild(qi);
    box.appendChild(el('div', { class: 'note', text: '보기를 쓰고, 정답 보기 왼쪽 동그라미를 눌러 주세요. (보기는 2~4개)' }));
    var radios = [], opts = [];
    for (var i = 0; i < 4; i++) {
      var r = el('input', { type: 'radio', name: name, value: String(i), 'aria-label': '정답 ' + (i + 1) });
      var t = el('input', { type: 'text', maxlength: '40', placeholder: '보기 ' + (i + 1) });
      radios.push(r); opts.push(t);
      box.appendChild(el('div', { class: 'o' }, [r, t]));
    }
    if (data) { qi.value = data[0]; data[1].forEach(function (o, i) { opts[i].value = o; }); radios[data[2]].checked = true; }
    box._get = function () {
      var q = qi.value.trim(), o = [], ans = -1;
      for (var i = 0; i < 4; i++) { var v = opts[i].value.trim(); if (v) { if (radios[i].checked) ans = o.length; o.push(v); } }
      return { q: q, o: o, a: ans };
    };
    qBox.appendChild(box);
  }
  function fill(sample) {
    qBox.innerHTML = '';
    $('#qtitle').value = sample.t;
    sample.q.forEach(function (q) { addQ(q); });
    F.toast('예시를 채웠어요. 내 얘기로 고쳐 쓰세요!');
  }
  function buildQuiz() {
    var qs = [], title = $('#qtitle').value.trim();
    if (!title) { F.toast('퀴즈 제목을 입력해 주세요'); $('#qtitle').focus(); return null; }
    for (var i = 0; i < qBox.children.length; i++) {
      var g = qBox.children[i]._get();
      if (!g.q && !g.o.length) continue;
      if (!g.q) { F.toast('문제 ' + (i + 1) + '번의 질문을 입력해 주세요'); return null; }
      if (g.o.length < 2) { F.toast('문제 ' + (i + 1) + '번은 보기가 2개 이상 필요해요'); return null; }
      if (g.a < 0) { F.toast('문제 ' + (i + 1) + '번의 정답 동그라미를 눌러 주세요'); return null; }
      qs.push([g.q, g.o, g.a]);
    }
    if (qs.length < MINQ) { F.toast('문제를 ' + MINQ + '개 이상 만들어 주세요'); return null; }
    return { v: 1, t: title, n: $('#qnick').value.trim(), q: qs };
  }

  /* ---------- 캔버스 ---------- */
  function baseCanvas(icon) {
    var c = document.createElement('canvas'); c.width = 1080; c.height = 1350;
    var x = c.getContext('2d'), g = x.createLinearGradient(0, 0, 1080, 1350);
    g.addColorStop(0, '#7c5cff'); g.addColorStop(1, '#ff6fb1'); x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    x.fillStyle = 'rgba(255,255,255,.12)'; for (var i = 0; i < 7; i++) { x.beginPath(); x.arc(120 + i * 160, 90 + (i % 3) * 40, 38 + (i % 4) * 8, 0, 7); x.fill(); }
    x.fillStyle = '#fff'; F.rr(x, 70, 190, 940, 980, 56); x.fill();
    x.textAlign = 'center'; x.font = '150px ' + F.FONT; x.fillText(icon, 540, 150);
    return c;
  }
  function footerTxt(x, s) { x.textAlign = 'center'; x.fillStyle = 'rgba(255,255,255,.92)'; x.font = '700 34px ' + F.FONT; x.fillText(s, 540, 1260); x.font = '600 28px ' + F.FONT; x.fillText('친구들 모의고사 풀어보러 오세요', 540, 1305); }
  function inviteCanvas(quiz) {
    var c = baseCanvas('📝'), x = c.getContext('2d');
    x.textAlign = 'center'; x.fillStyle = '#7c5cff'; x.font = '800 40px ' + F.FONT; x.fillText('모의고사 도착!', 540, 290);
    x.fillStyle = '#241f3a'; x.font = '800 68px ' + F.FONT; F.wrap(x, quiz.t, 540, 410, 800, 92, 3);
    x.font = '700 44px ' + F.FONT; x.fillStyle = '#6d6786';
    x.fillText((quiz.n ? quiz.n + ' 출제 · ' : '') + '총 ' + quiz.q.length + '문항', 540, 760);
    x.fillStyle = '#fff3fa'; F.rr(x, 190, 840, 700, 170, 40); x.fill();
    x.fillStyle = '#ff6fb1'; x.font = '800 46px ' + F.FONT; x.fillText('몇 점 맞을 수 있을까?', 540, 940);
    footerTxt(x, '찐친 모의고사 메이커'); return c;
  }
  function gradeOf(p) {
    var g = p >= 90 ? 1 : p >= 80 ? 2 : p >= 70 ? 3 : p >= 60 ? 4 : p >= 50 ? 5 : p >= 40 ? 6 : p >= 30 ? 7 : p >= 20 ? 8 : 9;
    var msg = ['', '이 정도면 평생 친구 인증!', '거의 다 아는 사이', '꽤 잘 아는 사이', '평범한 친구 사이', '반타작, 더 친해져요', '살짝 모르는 사이', '알고 보니 남남?', '우리 오늘부터 1일', '초면이세요?'];
    return { g: g, m: msg[g] };
  }
  function resultCanvas(quiz, name, correct) {
    var total = quiz.q.length, p = Math.round(correct / total * 100), gr = gradeOf(p);
    var c = baseCanvas(gr.g <= 2 ? '🏆' : gr.g <= 5 ? '📚' : '🥲'), x = c.getContext('2d');
    x.textAlign = 'center'; x.fillStyle = '#7c5cff'; x.font = '800 38px ' + F.FONT; x.fillText('성적표', 540, 285);
    x.fillStyle = '#6d6786'; x.font = '700 40px ' + F.FONT; F.wrap(x, quiz.t, 540, 350, 820, 56, 2);
    x.fillStyle = '#241f3a'; x.font = '800 54px ' + F.FONT; x.fillText((name || '익명') + ' 학생', 540, 500);
    x.fillStyle = '#7c5cff'; x.font = '900 230px ' + F.FONT; x.fillText(String(p), 520, 740);
    x.font = '800 60px ' + F.FONT; x.fillStyle = '#6d6786'; x.fillText('점', 800, 740);
    x.fillStyle = '#fff3fa'; F.rr(x, 250, 800, 580, 120, 60); x.fill();
    x.fillStyle = '#ff6fb1'; x.font = '900 64px ' + F.FONT; x.fillText(gr.g + '등급', 540, 884);
    x.fillStyle = '#241f3a'; x.font = '700 44px ' + F.FONT; x.fillText(gr.m, 540, 1000);
    x.fillStyle = '#6d6786'; x.font = '600 36px ' + F.FONT; x.fillText(total + '문제 중 ' + correct + '문제 정답', 540, 1070);
    footerTxt(x, '찐친 모의고사 메이커'); return c;
  }

  /* ---------- 화면 전환 ---------- */
  var views = ['home', 'take', 'res'];
  function show(v) { views.forEach(function (n) { $('#v-' + n).classList.toggle('hide', n !== v); }); window.scrollTo(0, 0); }
  function baseUrl() { return location.href.split('#')[0]; }

  /* ---------- 응시 ---------- */
  var quiz, who = '', cur = 0, right = 0, wrong = [], lock = false;
  function startTake() {
    $('#t-title').textContent = quiz.t;
    $('#t-meta').textContent = (quiz.n ? quiz.n + ' 님이 낸 모의고사 · ' : '') + '총 ' + quiz.q.length + '문항';
    $('#t-intro').classList.remove('hide'); $('#t-play').classList.add('hide'); show('take');
  }
  function renderQ() {
    var q = quiz.q[cur]; lock = false;
    $('#t-bar').style.width = (cur / quiz.q.length * 100) + '%';
    $('#t-qn').textContent = 'Q' + (cur + 1) + ' / ' + quiz.q.length;
    $('#t-q').textContent = q[0];
    var box = $('#t-opts'); box.innerHTML = '';
    q[1].forEach(function (o, i) {
      var b = el('button', { class: 'opt', type: 'button', text: (i + 1) + '. ' + o });
      b.onclick = function () { pick(i, b); }; box.appendChild(b);
    });
  }
  function pick(i, btn) {
    if (lock) return; lock = true;
    var q = quiz.q[cur], bs = $('#t-opts').children;
    if (i === q[2]) { right++; btn.classList.add('ok'); } else { wrong.push(cur); btn.classList.add('no'); bs[q[2]].classList.add('ok'); }
    setTimeout(function () { cur++; if (cur >= quiz.q.length) finish(); else renderQ(); }, 850);
  }
  function finish() {
    var p = Math.round(right / quiz.q.length * 100), gr = gradeOf(p);
    $('#r-score').textContent = p + '점'; $('#r-grade').textContent = gr.g + '등급 · ' + gr.m;
    $('#r-sub').textContent = quiz.q.length + '문제 중 ' + right + '문제 정답';
    var cv = $('#r-canvas'), src = resultCanvas(quiz, who, right);
    cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
    var wl = $('#r-wrong'); wl.innerHTML = '';
    if (!wrong.length) wl.appendChild(el('p', { class: 'note', text: '틀린 문제가 없어요. 완벽해요!' }));
    wrong.forEach(function (i) {
      var q = quiz.q[i];
      wl.appendChild(el('div', { class: 'kv' }, [el('span', { text: 'Q' + (i + 1) + '. ' + q[0] }), el('b', { text: '정답 ' + q[1][q[2]] })]));
    });
    F.shareBar($('#r-share'), {
      title: quiz.t, text: (who || '나') + '의 모의고사 성적은 ' + p + '점 (' + gr.g + '등급)! 너도 풀어봐', url: location.href,
      canvas: function () { return resultCanvas(quiz, who, right); }, file: 'moui-result.png'
    });
    $('#t-bar').style.width = '100%'; show('res');
  }

  /* ---------- 라우팅 ---------- */
  function route() {
    var m = location.hash.match(/^#q=(.+)$/);
    if (!m) { show('home'); return; }
    decode(m[1]).then(function (obj) {
      if (!obj || !obj.q || !obj.q.length) throw new Error('bad');
      quiz = obj; cur = 0; right = 0; wrong = []; startTake();
    }).catch(function () {
      F.toast('링크를 열 수 없어요. 새로 만들어 볼까요?'); history.replaceState(null, '', baseUrl()); show('home');
    });
  }

  /* ---------- 초기화 ---------- */
  for (var i = 0; i < 5; i++) addQ();
  $('#add-q').onclick = function () { addQ(); };
  $('#chips').onclick = function (e) { var k = e.target.getAttribute('data-s'); if (k) fill(SAMPLES[k]); };
  $('#make').onclick = function () {
    var obj = buildQuiz(); if (!obj) return;
    encode(obj).then(function (code) {
      var url = baseUrl() + '#q=' + code;
      $('#made-url').value = url;
      var cv = $('#made-canvas'), src = inviteCanvas(obj); cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
      F.shareBar($('#made-share'), {
        title: obj.t, text: (obj.n ? obj.n + '의 ' : '') + '모의고사 풀어봐! 나를 얼마나 아는지 점수로 알려줄게', url: url,
        canvas: function () { return inviteCanvas(obj); }, file: 'moui-invite.png'
      });
      $('#made').classList.remove('hide'); $('#made').scrollIntoView({ behavior: 'smooth' });
    });
  };
  $('#made-test').onclick = function () { var u = $('#made-url').value; location.href = u; location.reload(); };
  $('#t-start').onclick = function () { who = $('#t-name').value.trim(); $('#t-intro').classList.add('hide'); $('#t-play').classList.remove('hide'); renderQ(); };
  $('#again').onclick = function () { cur = 0; right = 0; wrong = []; startTake(); };
  $('#mk-mine').onclick = function () { history.pushState(null, '', baseUrl()); show('home'); };
  $('#t-mk').onclick = function () { history.pushState(null, '', baseUrl()); show('home'); };
  window.addEventListener('hashchange', route);
  route();
})();
