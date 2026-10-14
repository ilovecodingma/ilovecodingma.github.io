/* 오늘의 운세 카드 - 날짜(KST)와 별자리로 결정되는 재미용 운세. 같은 날 같은 별자리는 같은 결과가 나옵니다. */
(function () {
  var F = window.FUN, $ = F.$;
  var SIGNS = [
    ['염소자리', '♑', 12, 22, '🐐'], ['물병자리', '♒', 1, 20, '🏺'], ['물고기자리', '♓', 2, 19, '🐟'], ['양자리', '♈', 3, 21, '🐏'],
    ['황소자리', '♉', 4, 20, '🐂'], ['쌍둥이자리', '♊', 5, 21, '👯'], ['게자리', '♋', 6, 22, '🦀'], ['사자자리', '♌', 7, 23, '🦁'],
    ['처녀자리', '♍', 8, 23, '🌾'], ['천칭자리', '♎', 9, 23, '⚖️'], ['전갈자리', '♏', 10, 23, '🦂'], ['사수자리', '♐', 11, 22, '🏹']];
  var ANIMALS = ['원숭이', '닭', '개', '돼지', '쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양'];
  var COLORS = [['코랄 핑크', '#ff7f8a'], ['민트', '#46d6b0'], ['하늘색', '#5ab4ff'], ['라벤더', '#a58bff'], ['레몬 옐로', '#ffd23f'], ['살구', '#ffb482'], ['연두', '#9bdc4f'], ['크림 화이트', '#f3ead7'], ['딥 네이비', '#2c3a6e'], ['버건디', '#a8324f'], ['베이비 블루', '#a9d6ff'], ['올리브', '#8c9a3c']];
  var SNACKS = ['따뜻한 라떼', '달콤한 초콜릿', '바삭한 과자', '시원한 탄산수', '말랑한 젤리', '고소한 견과류', '새콤한 과일', '갓 구운 빵', '진한 아메리카노', '달걀 간식', '떡볶이', '아이스크림'];
  var TIMES = ['오전 9시쯤', '오전 11시쯤', '점심 직후', '오후 2시쯤', '오후 4시쯤', '퇴근길', '저녁 8시쯤', '자기 전 30분'];
  var SAY = ['오늘은 먼저 말 거는 쪽이 이겨요. 가볍게 안부 한 줄 보내 보세요.', '미루던 일 중 제일 작은 것부터 해치우면 하루가 가벼워져요.', '작은 행운이 슬쩍 지나가요. 평소와 다른 길로 가 보세요.', '오늘의 선택은 직감이 맞아요. 너무 오래 고민하지 마세요.', '누군가의 칭찬이 도착할 예정이에요. 겸손은 반만 떠세요.', '컨디션이 최고는 아니니 물 한 잔과 스트레칭을 챙기세요.', '뜻밖의 연락이 반가운 소식을 가져와요.', '오늘은 정리하는 날. 폰 속 사진 100장만 지워 보세요.', '말 한마디가 분위기를 바꿔요. 좋은 쪽으로 써 보세요.', '지금 하는 일이 느려 보여도 방향은 맞아요.', '무리한 약속은 정중히 거절해도 괜찮은 날이에요.', '새로운 사람에게서 힌트를 얻어요. 인사를 아끼지 마세요.', '오늘은 맛있는 걸 먹으면 운이 올라가요. 점심에 투자하세요.', '조급함만 내려놓으면 일이 술술 풀려요.', '내가 먼저 웃으면 오늘 하루가 같이 웃어 줘요.', '잠깐의 산책이 막힌 생각을 뚫어 줘요.', '오늘은 듣는 사람이 승자예요. 끼어들기는 한 박자 늦게.', '작은 지출에 행복이 숨어 있어요. 소소한 선물을 해 보세요.', '어제의 실수는 이미 지나갔어요. 오늘은 새 페이지입니다.', '계획보다 즉흥이 잘 맞는 날. 번개 약속이 대박일 수 있어요.', '집중력이 오전에 몰려 있어요. 어려운 일을 먼저 하세요.', '고마운 사람에게 한 줄 메시지를 보내면 운이 돌아와요.', '오늘은 비교 금지. 내 속도로 가는 게 정답이에요.', '의외의 곳에서 해결책이 나와요. 서랍도 열어 보세요.', '충전이 필요한 날. 일찍 자는 것이 최고의 개운법이에요.', '평소 미뤄 둔 질문을 용기 내 물어보세요. 답이 따뜻해요.', '운이 좋은 하루지만 과신은 금물. 확인 한 번 더!', '표현하지 않으면 몰라요. 마음을 말로 꺼내 보세요.', '작은 도전이 큰 자신감으로 돌아와요.', '오늘의 키워드는 여유. 5분만 일찍 출발하세요.'];
  var AVOID = ['감정이 격할 때 바로 답장하기', '배고픈 상태로 쇼핑하기', '밤 11시 이후 중요한 결정', '남과 비교하며 스크롤 내리기', '"나중에 해야지" 하고 미루기', '카페인 과다 섭취', '약속 시간 직전에 출발하기', '충동적인 장바구니 결제', '단톡방에서 길게 반박하기', '아침 거르고 버티기'];
  var CAT = ['연애·인간관계', '금전', '일·공부', '컨디션'];
  var CSAT = new Date('2026-11-18T15:00:00Z'); // 2026-11-19 00:00 KST

  var sign = -1, year = '', data = null;

  function signOf(m, d) {
    var idx = 0;
    for (var i = 0; i < 12; i++) { var s = SIGNS[i]; if (m > s[2] || (m === s[2] && d >= s[3])) idx = i; }
    if (m === 1 && d < 20) idx = 0;
    return idx;
  }
  function dayMax(m) { return [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m]; }
  function fortune(si, yr, date) {
    var r = F.seed(date + '|' + si + '|' + (yr || ''));
    var score = 45 + Math.floor(r() * 55);
    var cats = CAT.map(function () { return 1 + Math.floor(r() * 5); });
    var pick = function (a) { return a[Math.floor(r() * a.length)]; };
    return { score: score, cats: cats, color: pick(COLORS), num: 1 + Math.floor(r() * 99), snack: pick(SNACKS), time: pick(TIMES), say: pick(SAY), avoid: pick(AVOID), date: date, si: si, yr: yr };
  }
  function stars(n) { return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n); }
  function grade(s) { return s >= 90 ? '대길' : s >= 80 ? '길' : s >= 65 ? '평탄' : s >= 55 ? '소소' : '조심'; }
  function animalOf(y) { return y ? ANIMALS[(+y) % 12] + '띠' : ''; }

  function canvas(f) {
    var c = document.createElement('canvas'); c.width = 1080; c.height = 1350; var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 1080, 1350); g.addColorStop(0, '#2b1f6b'); g.addColorStop(.55, '#6b4bd8'); g.addColorStop(1, '#ff6fb1');
    x.fillStyle = g; x.fillRect(0, 0, 1080, 1350);
    var r = F.seed('stars' + f.si); x.fillStyle = 'rgba(255,255,255,.7)';
    for (var i = 0; i < 70; i++) { x.beginPath(); x.arc(r() * 1080, r() * 1350, r() * 3 + 1, 0, 7); x.fill(); }
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '700 38px ' + F.FONT; x.fillText(f.date.replace(/-/g, '.') + ' 오늘의 운세', 540, 120);
    x.font = '900 70px ' + F.FONT; x.fillText(SIGNS[f.si][1] + ' ' + SIGNS[f.si][0] + (f.yr ? ' · ' + animalOf(f.yr) : ''), 540, 215);
    x.fillStyle = 'rgba(255,255,255,.96)'; F.rr(x, 60, 270, 960, 930, 56); x.fill();
    x.fillStyle = '#7a7a8c'; x.font = '700 36px ' + F.FONT; x.fillText('오늘의 총운', 540, 345);
    x.fillStyle = '#6b4bd8'; x.font = '900 200px ' + F.FONT; x.fillText(String(f.score), 500, 535);
    x.font = '800 56px ' + F.FONT; x.fillStyle = '#7a7a8c'; x.textAlign = 'left'; x.fillText('점', 690, 535); x.textAlign = 'center';
    x.fillStyle = '#fff1f8'; F.rr(x, 410, 565, 260, 76, 38); x.fill(); x.fillStyle = '#ff4f9a'; x.font = '900 44px ' + F.FONT; x.fillText(grade(f.score), 540, 620);
    x.fillStyle = '#241f3a'; x.font = '700 38px ' + F.FONT; F.wrap(x, f.say, 540, 710, 820, 54, 3);
    x.textAlign = 'left'; var y = 880;
    CAT.forEach(function (n, i) {
      x.fillStyle = '#4b4860'; x.font = '700 34px ' + F.FONT; x.fillText(n, 130, y); x.fillStyle = '#ffb400'; x.font = '40px ' + F.FONT; x.fillText(stars(f.cats[i]), 620, y + 2); y += 62;
    });
    x.fillStyle = f.color[1]; x.beginPath(); x.arc(150, 1140, 28, 0, 7); x.fill(); x.strokeStyle = '#ddd'; x.lineWidth = 3; x.stroke();
    x.fillStyle = '#241f3a'; x.font = '700 32px ' + F.FONT; x.fillText('행운색 ' + f.color[0] + '  ·  행운숫자 ' + f.num, 200, 1152);
    x.textAlign = 'center'; x.fillStyle = '#fff'; x.font = '700 32px ' + F.FONT; x.fillText('재미로 보는 운세예요 · sungprofile.cloud/luck', 540, 1275);
    return c;
  }

  function show(f, shared) {
    data = f;
    $('#f-head').textContent = SIGNS[f.si][1] + ' ' + SIGNS[f.si][0] + (f.yr ? ' · ' + animalOf(f.yr) : '') + ' 오늘의 운세';
    $('#f-score').textContent = f.score + '점'; $('#f-grade').textContent = grade(f.score);
    $('#f-say').textContent = f.say;
    var cb = $('#f-cats'); cb.innerHTML = '';
    CAT.forEach(function (n, i) {
      var d = document.createElement('div'); d.className = 'kv'; var a = document.createElement('span'); a.textContent = n;
      var b = document.createElement('span'); b.className = 'stars'; b.textContent = stars(f.cats[i]); d.appendChild(a); d.appendChild(b); cb.appendChild(d);
    });
    $('#f-color').textContent = f.color[0]; $('#f-dot').style.background = f.color[1];
    $('#f-num').textContent = f.num; $('#f-snack').textContent = f.snack; $('#f-time').textContent = f.time; $('#f-avoid').textContent = f.avoid;
    var cv = $('#f-canvas'), src = canvas(f); cv.width = src.width; cv.height = src.height; cv.getContext('2d').drawImage(src, 0, 0);
    F.shareBar($('#f-share'), {
      title: '오늘의 운세 카드', text: '오늘 내 ' + SIGNS[f.si][0] + ' 운세는 ' + f.score + '점 (' + grade(f.score) + ')! 너도 뽑아봐', url: location.origin + location.pathname + '#s=' + f.si,
      canvas: function () { return canvas(f); }, file: 'luck-' + f.date + '.png'
    });
    $('#f-shared').classList.toggle('hide', !shared);
    $('#pick').classList.add('hide'); $('#card').classList.remove('hide');
    table(f.date);
    window.scrollTo(0, 0);
  }
  function table(date) {
    var tb = $('#all'); tb.innerHTML = '';
    var rows = SIGNS.map(function (s, i) { return { i: i, f: fortune(i, '', date) }; }).sort(function (a, b) { return b.f.score - a.f.score; });
    rows.forEach(function (o, n) {
      var tr = document.createElement('tr'); tr.innerHTML = '<td></td><td></td><td></td><td></td>';
      tr.children[0].textContent = (n + 1) + '위'; tr.children[1].textContent = SIGNS[o.i][1] + ' ' + SIGNS[o.i][0];
      tr.children[2].textContent = o.f.score + '점'; tr.children[3].textContent = '행운색 ' + o.f.color[0];
      tb.appendChild(tr);
    });
  }

  /* 폼 */
  var mS = $('#m'), dS = $('#d'), yS = $('#y');
  for (var m = 1; m <= 12; m++) mS.appendChild(new Option(m + '월', m));
  function fillDays() { var cur = +dS.value || 1; dS.innerHTML = ''; for (var d = 1; d <= dayMax(+mS.value); d++) dS.appendChild(new Option(d + '일', d)); dS.value = Math.min(cur, dayMax(+mS.value)); }
  mS.onchange = fillDays; fillDays();
  yS.appendChild(new Option('태어난 해(선택)', ''));
  for (var y = 2012; y >= 1960; y--) yS.appendChild(new Option(y + '년', y));
  $('#go').onclick = function () {
    var si = signOf(+mS.value, +dS.value); year = yS.value;
    try { localStorage.setItem('luck_p', JSON.stringify({ m: +mS.value, d: +dS.value, y: year })); } catch (e) { }
    show(fortune(si, year, F.kstDate()), false);
  };
  $('#again').onclick = function () { $('#card').classList.add('hide'); $('#pick').classList.remove('hide'); history.replaceState(null, '', location.pathname); };
  $('#f-shared-go').onclick = $('#again').onclick;

  /* 수능 D-day */
  var left = Math.ceil((CSAT - new Date()) / 86400000);
  if (left > 0 && left < 400) { $('#csat').textContent = '2027학년도 수능 D-' + left; $('#csat').classList.remove('hide'); }

  table(F.kstDate());
  /* 시작: 공유 링크 > 저장된 정보 > 입력 폼 */
  var hm = location.hash.match(/^#s=(\d{1,2})$/), stored = null;
  try { stored = JSON.parse(localStorage.getItem('luck_p') || 'null'); } catch (e) { }
  if (hm && +hm[1] < 12) { show(fortune(+hm[1], '', F.kstDate()), true); }
  else if (stored && stored.m) { mS.value = stored.m; fillDays(); dS.value = stored.d; yS.value = stored.y || ''; show(fortune(signOf(stored.m, stored.d), stored.y || '', F.kstDate()), false); }
})();
