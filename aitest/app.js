/* AI 생존력 테스트 - 12문항, 5개 성향축으로 6개 유형을 판정합니다. 재미용이며 서버 전송 없음. */
(function () {
  var F = window.FUN, $ = F.$;
  var AX = ['A', 'C', 'H', 'F', 'R'];
  var AXN = { A: 'AI 활용력', C: '창의력', H: '공감·설득력', F: '현장 대응력', R: '루틴 의존도' };
  var Q = [
    ['새 업무가 떨어졌다. 내 첫 행동은?', [['AI에게 초안부터 시켜 본다', { A: 3 }], ['아이디어를 노트에 마구 적는다', { C: 3 }], ['담당자에게 전화해 맥락부터 듣는다', { H: 3 }], ['이전 자료와 매뉴얼을 찾아 그대로 따라 한다', { R: 3 }]]],
    ['내 일에서 가장 시간을 많이 쓰는 건?', [['문서·자료 정리', { R: 3 }], ['사람 만나기와 설득', { H: 3 }], ['새로운 걸 기획하기', { C: 3 }], ['몸으로 직접 처리하기', { F: 3 }]]],
    ['AI 챗봇은 얼마나 써 봤어?', [['매일 여러 번 쓴다', { A: 3 }], ['가끔 쓴다', { A: 1 }], ['써 봤는데 별로였다', { C: 1 }], ['거의 안 써 봤다', {}]]],
    ['매뉴얼에 없는 돌발상황이 터졌다!', [['현장에서 바로 몸으로 해결한다', { F: 3 }], ['일단 사람들을 진정시킨다', { H: 3 }], ['새로운 방법을 즉석에서 짜낸다', { C: 3 }], ['체크리스트부터 찾아본다', { R: 2 }]]],
    ['내가 제일 듣고 싶은 칭찬은?', [['빠르고 정확하다', { R: 2, A: 1 }], ['아이디어가 신선하다', { C: 3 }], ['같이 일하면 편하다', { H: 3 }], ['손이 야무지다', { F: 3 }]]],
    ['엑셀 100줄 반복 작업이 왔다', [['함수나 자동화로 한 번에 끝낸다', { A: 3 }], ['묵묵히 하나씩 수작업한다', { R: 3 }], ['동료에게 슬쩍 도움을 청한다', { H: 2 }], ['일하는 방식 자체를 바꿔 버린다', { C: 2 }]]],
    ['처음 본 사람과 5분 안에 친해지기', [['식은 죽 먹기다', { H: 3 }], ['어렵지만 해낸다', { H: 1 }], ['글이나 채팅이 훨씬 편하다', { C: 1 }], ['굳이 친해질 필요 없다', { R: 1 }]]],
    ['AI가 써 준 결과물을 받았을 때', [['사실 확인을 꼼꼼히 하고 고친다', { A: 3 }], ['내 말투로 싹 바꾼다', { C: 2, A: 1 }], ['웬만하면 그대로 쓴다', { R: 2 }], ['믿을 수 없어서 안 쓴다', {}]]],
    ['책임이 걸린 중요한 결정을 할 때', [['데이터와 근거를 먼저 본다', { A: 2, R: 1 }], ['직감과 경험을 믿는다', { C: 2, F: 1 }], ['관계자 의견을 두루 듣는다', { H: 3 }], ['위에서 정해 주길 기다린다', { R: 2 }]]],
    ['주말에 제일 신나는 일은?', [['만들기·요리·운동', { F: 3 }], ['영상이나 글 만들기', { C: 3 }], ['사람 만나 수다 떨기', { H: 3 }], ['새로 나온 앱과 툴 탐험', { A: 3 }]]],
    ['5년 뒤 나는 어떤 사람이면 좋겠어?', [['AI를 제일 잘 다루는 사람', { A: 3 }], ['나만의 작품이 있는 사람', { C: 3 }], ['다들 찾는 사람', { H: 3 }], ['현장에서 인정받는 사람', { F: 3 }]]],
    ['회사가 새 AI 도구를 도입한대!', [['제일 먼저 써 본다', { A: 3 }], ['쓰기 쉬우면 쓴다', { A: 1, R: 1 }], ['솔직히 반갑지 않다', {}], ['동료가 알려 주면 쓴다', { H: 1, R: 1 }]]]
  ];
  var MAX = { A: 0, C: 0, H: 0, F: 0, R: 0 };
  Q.forEach(function (q) { var m = {}; q[1].forEach(function (o) { for (var k in o[1]) m[k] = Math.max(m[k] || 0, o[1][k]); }); for (var k in m) MAX[k] += m[k]; });

  var T = {
    A: { n: 'AI 조련사', e: '🤖', c: ['#5b6cff', '#22c1c3'], tag: 'AI를 부리는 쪽에 선 사람', d: 'AI를 도구로 쓰는 데 거리낌이 없고, 결과를 검수할 줄도 압니다. AI가 일을 가져가기 전에 AI에게 일을 시키는 타입이라 가장 안정적인 자리에 서 있어요.', s: '새 도구 적응이 빠르고 결과를 의심할 줄 안다', w: 'AI 의존이 커지면 내 판단 근육이 약해질 수 있다', tips: ['AI 결과에 항상 "왜?"를 한 번 더 물어보기', 'AI가 못 하는 사람 일(설득·조율)도 하나 키우기'], m: 'H' },
    C: { n: '아이디어 폭죽', e: '🎆', c: ['#ff8a3d', '#ff3d81'], tag: '엉뚱함이 곧 경쟁력', d: '남들이 생각 못 한 연결을 만들어 내는 사람입니다. AI가 평균적인 답을 뽑는 동안 당신은 평균을 깨는 한 방을 냅니다. 다만 아이디어를 현실로 굳히는 힘이 숙제예요.', s: '발상의 전환, 취향과 감각', w: '마무리와 반복 작업에서 쉽게 지친다', tips: ['AI를 아이디어 확장 파트너로 붙여 보기', '아이디어를 작게라도 끝까지 만들어 포트폴리오로 남기기'], m: 'A' },
    H: { n: '감정 번역가', e: '🫶', c: ['#ff6fb1', '#ffa07a'], tag: '사람 사이를 잇는 사람', d: '말 속의 진짜 마음을 읽고 사람들을 움직이는 타입입니다. 신뢰와 공감이 필요한 일은 AI가 가장 따라 하기 어려운 영역이라 생존 점수가 높게 나오기 쉬워요.', s: '공감, 조율, 신뢰 쌓기', w: '데이터와 도구에는 약간 소극적일 수 있다', tips: ['회의록·정리는 AI에게 맡기고 시간을 사람에게 쓰기', '내 조율 노하우를 글로 정리해 두기'], m: 'C' },
    F: { n: '현장 장인', e: '🛠️', c: ['#2ea66a', '#9bd13f'], tag: '손과 몸으로 해결하는 실전파', d: '예측 못 한 현장 상황에서 가장 빛나는 사람입니다. 몸을 쓰고 눈치로 판단하는 일은 아직 AI가 넘기 힘든 벽이에요. 기록과 디지털 도구를 조금만 더하면 무적입니다.', s: '돌발상황 대처, 손기술, 체력', w: '기록·공유 습관이 약하면 노하우가 묻힌다', tips: ['내 노하우를 사진·영상으로 기록하기', '일정·견적 같은 서류 일은 AI로 줄이기'], m: 'A' },
    R: { n: '정리왕 루틴러', e: '🗂️', c: ['#6b7a99', '#b5c0d8'], tag: '꼼꼼함은 최고, 변화는 숙제', d: '정확하고 성실하게 일을 굴리는 타입입니다. 하지만 정해진 규칙대로 도는 일은 AI가 가장 먼저 잘하게 되는 영역이라, 지금부터 하나씩 역할을 넓혀 두면 좋아요.', s: '정확성, 성실함, 마감 준수', w: '반복 업무 비중이 높을수록 대체 압력이 크다', tips: ['반복 작업 하나를 골라 AI·자동화로 먼저 줄여 보기', '"정리"에서 "판단·제안"으로 역할 넓히기'], m: 'C' },
    T: { n: '관망하는 거북이', e: '🐢', c: ['#4a8fe7', '#7fd8d1'], tag: '아직 본격 출발 전', d: '아직 AI도, 변화도 거리를 두고 지켜보는 중입니다. 서두를 필요는 없지만 한 걸음만 떼면 점수가 가장 크게 오르는 타입이에요. 오늘 챗봇에 질문 하나만 해 보세요.', s: '신중함, 안정감', w: '변화 속도에 뒤처질 수 있다', tips: ['오늘 해야 할 일 하나를 AI에게 먼저 물어보기', '주변에 AI 잘 쓰는 동료 한 명 따라 해 보기'], m: 'A' }
  };

  var cur = 0, ans = [], res = null;
  function show(id) { ['intro', 'quiz', 'result'].forEach(function (n) { $('#s-' + n).classList.toggle('hide', n !== id); }); window.scrollTo(0, 0); }
  function render() {
    var q = Q[cur];
    $('#bar').style.width = (cur / Q.length * 100) + '%'; $('#qn').textContent = 'Q' + (cur + 1) + ' / ' + Q.length; $('#q').textContent = q[0];
    var box = $('#opts'); box.innerHTML = '';
    q[1].forEach(function (o, i) { var b = document.createElement('button'); b.className = 'opt'; b.type = 'button'; b.textContent = o[0]; b.onclick = function () { pick(i); }; box.appendChild(b); });
  }
  var busy = false;
  function pick(i) { if (busy) return; busy = true; ans[cur] = i; setTimeout(function () { busy = false; cur++; if (cur >= Q.length) finish(); else render(); }, 160); }

  function compute() {
    var sum = { A: 0, C: 0, H: 0, F: 0, R: 0 };
    ans.forEach(function (a, qi) { var sc = Q[qi][1][a][1]; for (var k in sc) sum[k] += sc[k]; });
    var n = {}; AX.forEach(function (k) { n[k] = MAX[k] ? Math.round(sum[k] / MAX[k] * 100) : 0; });
    var top = 'A', best = -1; AX.forEach(function (k) { if (n[k] > best) { best = n[k]; top = k; } });
    var type = (n.A < 15 && best < 45) ? 'T' : top;
    var score = Math.round(35 + .3 * n.A + .25 * n.C + .25 * n.H + .2 * n.F - .25 * n.R + 8);
    score = Math.max(5, Math.min(98, score));
    return { type: type, score: score, n: n };
  }
  function dday(score) { return Math.round(120 + score * score * 0.9); }

  function card(r) {
    var t = T[r.type], c = document.createElement('canvas'); c.width = 1080; c.height = 1350;
    var x = c.getContext('2d'), g = x.createLinearGradient(0, 0, 1080, 1350); g.addColorStop(0, t.c[0]); g.addColorStop(1, t.c[1]);
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    x.fillStyle = 'rgba(255,255,255,.14)'; for (var i = 0; i < 6; i++) { x.beginPath(); x.arc(100 + i * 180, 70 + (i % 2) * 50, 40 + (i % 3) * 10, 0, 7); x.fill(); }
    x.fillStyle = '#fff'; F.rr(x, 70, 170, 940, 1000, 56); x.fill();
    x.textAlign = 'center'; x.font = '170px ' + F.FONT; x.fillText(t.e, 540, 130);
    x.fillStyle = '#7a7a8c'; x.font = '700 36px ' + F.FONT; x.fillText('나의 AI 생존 유형', 540, 270);
    x.fillStyle = '#1e1b30'; x.font = '900 100px ' + F.FONT; x.fillText(t.n, 540, 390);
    x.fillStyle = t.c[0]; x.font = '700 40px ' + F.FONT; x.fillText(t.tag, 540, 460);
    x.fillStyle = '#1e1b30'; x.font = '900 190px ' + F.FONT; x.fillText(r.score, 480, 660);
    x.font = '800 56px ' + F.FONT; x.fillStyle = '#7a7a8c'; x.textAlign = 'left'; x.fillText('점', 650, 660); x.textAlign = 'center';
    x.fillStyle = '#f4f2fb'; F.rr(x, 210, 710, 660, 110, 55); x.fill();
    x.fillStyle = t.c[0]; x.font = '800 46px ' + F.FONT; x.fillText('AI 대체 D-' + dday(r.score).toLocaleString('ko-KR'), 540, 785);
    var y = 880; x.textAlign = 'left';
    ['A', 'C', 'H', 'F'].forEach(function (k) {
      x.fillStyle = '#4b4860'; x.font = '700 32px ' + F.FONT; x.fillText(AXN[k], 150, y + 30);
      x.fillStyle = '#ece9f7'; F.rr(x, 420, y + 6, 480, 30, 15); x.fill();
      x.fillStyle = t.c[0]; F.rr(x, 420, y + 6, Math.max(30, 480 * r.n[k] / 100), 30, 15); x.fill(); y += 66;
    });
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '700 34px ' + F.FONT; x.fillText('AI 생존력 테스트 · 재미로 보는 결과예요', 540, 1255);
    x.font = '600 28px ' + F.FONT; x.fillText('sungprofile.cloud/aitest', 540, 1303);
    return c;
  }

  function finish() {
    res = compute(); showResult(res, false);
    try { history.replaceState(null, '', '#r=' + res.type + '-' + res.score); } catch (e) { }
  }
  function showResult(r, shared) {
    var t = T[r.type];
    $('#r-emoji').textContent = t.e; $('#r-name').textContent = t.n; $('#r-tag').textContent = t.tag;
    $('#r-score').textContent = r.score + '점'; $('#r-dday').textContent = 'AI 대체 D-' + dday(r.score).toLocaleString('ko-KR');
    $('#r-desc').textContent = t.d; $('#r-s').textContent = t.s; $('#r-w').textContent = t.w;
    $('#r-tips').innerHTML = ''; t.tips.forEach(function (x) { var li = document.createElement('li'); li.textContent = x; $('#r-tips').appendChild(li); });
    $('#r-match').textContent = T[t.m].e + ' ' + T[t.m].n + ' 유형과 팀을 이루면 약점이 채워져요';
    var ab = $('#r-axes'); ab.innerHTML = '';
    if (r.n) AX.forEach(function (k) {
      var d = document.createElement('div'); d.className = 'kv'; var a = document.createElement('span'); a.textContent = AXN[k]; var b = document.createElement('b'); b.textContent = r.n[k] + '%'; d.appendChild(a); d.appendChild(b); ab.appendChild(d);
    });
    $('#r-axes-wrap').classList.toggle('hide', !r.n);
    $('#r-shared').classList.toggle('hide', !shared);
    var cv = $('#r-canvas'), src = card(r.n ? r : { type: r.type, score: r.score, n: { A: 50, C: 50, H: 50, F: 50, R: 50 } });
    cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
    var url = location.origin + location.pathname + '#r=' + r.type + '-' + r.score;
    F.shareBar($('#r-share'), {
      title: 'AI 생존력 테스트', text: '나는 [' + t.n + '] ' + r.score + '점! AI 대체 D-' + dday(r.score).toLocaleString('ko-KR') + ' (재미용) 너는 몇 점?', url: url,
      canvas: function () { return card(r.n ? r : { type: r.type, score: r.score, n: { A: 50, C: 50, H: 50, F: 50, R: 50 } }); }, file: 'ai-survival.png'
    });
    show('result');
  }
  function fromHash() {
    var m = location.hash.match(/^#r=([ACHFRT])-(\d{1,2})$/);
    if (m) { showResult({ type: m[1], score: Math.min(98, Math.max(5, +m[2])) }, true); return true; }
    return false;
  }
  $('#start').onclick = function () { cur = 0; ans = []; show('quiz'); render(); };
  $('#retry').onclick = function () { history.replaceState(null, '', location.pathname); cur = 0; ans = []; show('quiz'); render(); };
  $('#shared-go').onclick = $('#retry').onclick;
  if (!fromHash()) show('intro');
})();
