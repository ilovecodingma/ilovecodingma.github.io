// 레시피 상세 (2026-10-20 「다른 사이트 보고 성의있게」): 인분 조절 · 재료 체크/장보기 복사 · 단계별 타이머 · 요리 모드(큰 글씨·한 단계씩·화면 켜짐) · 음성 읽어주기(TTS)
(function () {
  var A = document.querySelector('.rp2'); if (!A) return;
  var BASE = +A.getAttribute('data-base') || 2, TITLE = A.getAttribute('data-n') || document.title;
  var ga = function (n, p) { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  var LS = function (k, d) { try { var v = JSON.parse(localStorage.getItem(k) || 'null'); return v == null ? d : v; } catch (e) { return d; } };
  var LSset = function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  var h = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  var steps = [].slice.call(A.querySelectorAll('.rp-steps li[data-k]'));
  var toast = function (m) { var t = h('div', 'rp-toast', m); document.body.appendChild(t); setTimeout(function () { t.classList.add('on'); }, 10); setTimeout(function () { t.remove(); }, 2300); };

  /* ── 인분 조절: 양념 숫자·단위가 붙은 숫자만 비율로 바꾼다(분·초·단계·온도는 그대로) ── */
  var FR = { 0.25: '¼', 0.5: '½', 0.75: '¾' };
  var fmt = function (v) {
    if (v >= 10) return String(Math.round(v)); var w = Math.floor(v + 1e-9), f = Math.round((v - w) * 4) / 4; if (f >= 1) { w += 1; f = 0; }
    return (w ? w : '') + (FR[f] || '') || '0';
  };
  var num = function (s) { if (/\//.test(s)) { var p = s.split('/'); return +p[0] / +p[1]; } return parseFloat(s); };
  var UNIT = '(컵|큰술|작은술|숟가락|스푼|개|대|쪽|장|g|kg|ml|L|줌|꼬집|조각|마리|봉지|캔|모|단|포기)';
  var SEAS = '(간장|설탕|고춧가루|고추장|된장|참기름|들기름|식초|소금|다진마늘|물엿|올리고당|마요네즈|케첩|굴소스|맛술|후추|물|우유|카레가루|쌈장|액젓|깨)';
  var RX1 = new RegExp('(\\d+(?:\\.\\d+)?(?:/\\d+)?)(\\s*)' + UNIT, 'g');
  var RX2 = new RegExp(SEAS + '(\\s*)(\\d+(?:\\.\\d+)?(?:/\\d+)?)(?!\\s*(?:분|초|단계|도|%|cm|mm|컵|큰술|작은술|숟가락|스푼|개|대|쪽|장|g|kg|ml|L|줌|꼬집|조각|마리|봉지|캔|모|단|포기|인분|배|시간))', 'g');
  function scale(text, f) {
    if (f === 1) return text;
    var out = text.replace(RX1, function (m, n, sp, u) { var v = num(n) * f; return fmt(v) + sp + u; });
    return out.replace(RX2, function (m, w, sp, n) { var v = num(n) * f; return w + sp + fmt(v); });
  }
  var nodes = [];
  steps.forEach(function (li) {
    var p = li.querySelector('p'); if (!p) return;
    var w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT, null), n;
    while ((n = w.nextNode())) nodes.push([n, n.nodeValue]);
  });
  var cur = LS('jupjup_rp_serv', BASE);
  function setServ(s) {
    cur = s; LSset('jupjup_rp_serv', s); var f = s / BASE;
    nodes.forEach(function (x) { x[0].nodeValue = scale(x[1], f); });
    [].forEach.call(A.querySelectorAll('.rp-serv button'), function (b) { b.classList.toggle('on', +b.getAttribute('data-s') === s); });
    [].forEach.call(A.querySelectorAll('[data-serv-label]'), function (e) { e.textContent = s + '인분'; });
    var note = A.querySelector('.rp-serv-note'); if (note) note.hidden = s === BASE;
    timers();
  }
  [].forEach.call(A.querySelectorAll('.rp-serv button'), function (b) { b.onclick = function () { setServ(+b.getAttribute('data-s')); ga('rp_serv', { s: +b.getAttribute('data-s') }); }; });

  /* ── 재료 체크 · 장보기 목록 복사 ── */
  var KEY = 'jupjup_rp_chk_' + TITLE, chk = LS(KEY, {});
  [].forEach.call(A.querySelectorAll('.rp-ing input[type=checkbox]'), function (c) {
    var k = c.getAttribute('data-i'); c.checked = !!chk[k];
    c.onchange = function () { chk[k] = c.checked; if (!c.checked) delete chk[k]; LSset(KEY, chk); c.closest('li').classList.toggle('done', c.checked); };
    c.closest('li').classList.toggle('done', c.checked);
    var li = c.closest('li'), nm = (k || '').replace(/\(.*?\)/g, '').trim();   // 없는 재료(체크 안 함)에만 최저가 검색 링크가 보인다
    if (nm && !li.querySelector('.rp-cheap')) { var a = document.createElement('a'); a.className = 'rp-cheap'; a.textContent = '최저가'; a.target = '_blank'; a.rel = 'noopener nofollow'; a.href = '/money/cheapest/?q=' + encodeURIComponent(nm); a.title = nm + ' 최저가 검색'; a.onclick = function (e) { e.stopPropagation(); }; li.appendChild(a); }
  });
  var cp = A.querySelector('.rp-copy');
  if (cp) cp.onclick = function () {
    var miss = [].filter.call(A.querySelectorAll('.rp-ing li[data-need]'), function (li) { return !li.querySelector('input').checked; }).map(function (li) { return li.getAttribute('data-i'); });
    var txt = '🛒 ' + TITLE + ' 장보기\n' + (miss.length ? miss.map(function (x) { return '□ ' + x; }).join('\n') : '(필수 재료가 모두 있어요!)') + '\n\n' + location.href.split('#')[0];
    var done = function () { toast(miss.length ? '장보기 목록을 복사했어요 (' + miss.length + '개)' : '필수 재료가 모두 있어요!'); ga('rp_copy', { n: miss.length }); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(done, function () { prompt('복사해 가세요', txt); }); else prompt('복사해 가세요', txt);
  };

  /* ── 타이머 ── */
  var AC = null, running = [], bar = null;
  function beep() { try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); [0, 0.25, 0.5].forEach(function (d) { var o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = 880; o.connect(g); g.connect(AC.destination); g.gain.setValueAtTime(0.0001, AC.currentTime + d); g.gain.exponentialRampToValueAtTime(0.35, AC.currentTime + d + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, AC.currentTime + d + 0.2); o.start(AC.currentTime + d); o.stop(AC.currentTime + d + 0.22); }); } catch (e) {} if (navigator.vibrate) navigator.vibrate([300, 150, 300]); }
  function secs(t) { var m = t.match(/(\d+)(?:\s*~\s*(\d+))?\s*(분|초)/); if (!m) return 0; var v = +(m[2] || m[1]); return m[3] === '분' ? v * 60 : v; }
  function mmss(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function paintBar() {
    if (!bar) { bar = h('div', 'rp-tbar'); document.body.appendChild(bar); }
    bar.innerHTML = ''; running = running.filter(function (r) { return !r.done; });
    running.forEach(function (r) { var d = h('div', 'rp-tm'); d.appendChild(h('b', '', '⏱ ' + r.label)); d.appendChild(h('span', '', mmss(r.left))); var x = h('button', '', '✕'); x.onclick = function () { clearInterval(r.id); r.done = true; paintBar(); }; d.appendChild(x); bar.appendChild(d); });
    bar.hidden = !running.length;
  }
  function startTimer(label, s) {
    var r = { label: label, left: s, done: false }; running.push(r); paintBar(); ga('rp_timer', { s: s });
    r.id = setInterval(function () { r.left--; if (r.left <= 0) { clearInterval(r.id); r.done = true; beep(); speak(label + ' 타이머가 끝났어요.', true); toast('⏱ ' + label + ' 끝!'); } paintBar(); }, 1000);
  }
  function timers() {
    [].forEach.call(A.querySelectorAll('.rp-tmb'), function (b) { b.remove(); });
    steps.forEach(function (li) {
      var p = li.querySelector('p'), t = p.textContent, re = /(\d+)(?:\s*~\s*(\d+))?\s*(분|초)/g, m, seen = {};
      var box = li.querySelector('.rp-tms') || (function () { var d = h('div', 'rp-tms'); li.insertBefore(d, li.querySelector('.rp-sp') || li.querySelector('.rp-sb')); return d; })(); box.innerHTML = ''; box.hidden = false;
      while ((m = re.exec(t))) { var lab = m[0].replace(/\s+/g, ''); if (seen[lab]) continue; seen[lab] = 1; (function (lab, m) { var b = h('button', 'rp-tmb', '⏱ ' + lab + ' 타이머'); b.type = 'button'; b.onclick = function () { startTimer(lab, secs(m[0])); }; box.appendChild(b); })(lab, m); }
    });
  }
  timers();

  /* ── 음성 읽어주기(TTS) ── */
  var TTS = 'speechSynthesis' in window, voice = null, rate = LS('jupjup_rp_rate', 1);
  function pick() { if (!TTS) return; var vs = speechSynthesis.getVoices() || []; voice = vs.filter(function (v) { return /^ko/i.test(v.lang); }).sort(function (a, b) { return (/google|natural|online/i.test(b.name) ? 1 : 0) - (/google|natural|online/i.test(a.name) ? 1 : 0); })[0] || null; }
  if (TTS) { pick(); if (speechSynthesis.addEventListener) speechSynthesis.addEventListener('voiceschanged', pick); }
  var clean = function (t) { return t.replace(/[①-⑩]/g, '').replace(/(\d+)\s*~\s*(\d+)/g, '$1에서 $2').replace(/(\d+)\/(\d+)/g, '$2분의 $1').replace(/큰술/g, '큰술').replace(/·/g, ', ').replace(/\(([^)]*)\)/g, ', $1,').replace(/\s*,(\s*,)+/g, ',').replace(/,\s*([.!?])/g, '$1').replace(/\s+/g, ' '); };
  var curU = null;
  function speak(text, force, onend) {
    if (!TTS) return; if (!force) speechSynthesis.cancel(); else if (speechSynthesis.speaking) { /* 타이머 알림은 이어 말하기 */ }
    var u = new SpeechSynthesisUtterance(clean(text)); u.lang = 'ko-KR'; if (voice) u.voice = voice; u.rate = rate; u.pitch = 1.02;
    u.onend = function () { if (curU === u) curU = null; if (onend) onend(); }; u.onerror = function () { if (onend) onend(true); };
    if (!force) curU = u; speechSynthesis.speak(u);
  }
  function stopSpeak() { if (TTS) speechSynthesis.cancel(); curU = null; }
  window.addEventListener('pagehide', stopSpeak);
  var stepText = function (i) { return steps[i].querySelector('p').textContent; };
  var introText = function () { var ing = [].map.call(A.querySelectorAll('.rp-ing li[data-need]'), function (li) { return li.getAttribute('data-i'); }); return TITLE + ' 만드는 방법을 알려 드릴게요. 필수 재료는 ' + ing.join(', ') + '입니다. ' + cur + '인분 기준이에요.'; };

  /* ── 요리 모드 ── */
  var ov = null, idx = -1, auto = false, wl = null;
  function wake() { try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { wl = l; }, function () {}); } catch (e) {} }
  function unwake() { try { if (wl) wl.release(); } catch (e) {} wl = null; }
  function openCook(start) {
    if (ov) return; idx = start || 0; ga('rp_cook', { n: TITLE });
    ov = h('div', 'rp-cook'); ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-label', TITLE + ' 요리 모드');
    ov.innerHTML = '<div class="ck-top"><b></b><span class="ck-prog"></span><button type="button" class="ck-x" aria-label="닫기">✕</button></div><div class="ck-body"><div class="ck-img"></div><div class="ck-n"></div><p class="ck-t"></p><div class="ck-tm"></div></div>' +
      '<div class="ck-ctl"><button type="button" class="ck-prev">◀ 이전</button>' + (TTS ? '<button type="button" class="ck-say">🔊 읽어 주기</button>' : '') + '<button type="button" class="ck-next">다음 ▶</button></div>' +
      '<div class="ck-opt">' + (TTS ? '<label><input type="checkbox" class="ck-auto"> 자동으로 읽고 넘기기</label><label>속도 <select class="ck-rate"><option value="0.8">느리게</option><option value="1">보통</option><option value="1.2">빠르게</option><option value="1.4">아주 빠르게</option></select></label>' : '<span class="ck-na">이 브라우저는 음성 읽기를 지원하지 않아요.</span>') + '</div>';
    document.body.appendChild(ov); document.documentElement.classList.add('ck-lock'); wake();
    ov.querySelector('.ck-top b').textContent = TITLE;
    ov.querySelector('.ck-x').onclick = closeCook;
    ov.querySelector('.ck-prev').onclick = function () { go(idx - 1, true); };
    ov.querySelector('.ck-next').onclick = function () { go(idx + 1, true); };
    var say = ov.querySelector('.ck-say'); if (say) say.onclick = function () { if (curU || (TTS && speechSynthesis.speaking)) { stopSpeak(); say.textContent = '🔊 읽어 주기'; auto = false; var a = ov.querySelector('.ck-auto'); if (a) a.checked = false; } else readCur(); };
    var au = ov.querySelector('.ck-auto'); if (au) au.onchange = function () { auto = au.checked; if (auto) readCur(); else stopSpeak(); };
    var rt = ov.querySelector('.ck-rate'); if (rt) { rt.value = String(rate); if (rt.value !== String(rate)) rt.value = '1'; rt.onchange = function () { rate = +rt.value; LSset('jupjup_rp_rate', rate); if (curU) readCur(); }; }
    document.addEventListener('keydown', key);
    go(idx, false);
  }
  function key(e) { if (!ov) return; if (e.key === 'ArrowRight') go(idx + 1, true); else if (e.key === 'ArrowLeft') go(idx - 1, true); else if (e.key === 'Escape') closeCook(); else if (e.key === ' ' && e.target.tagName !== 'SELECT' && e.target.tagName !== 'INPUT') { e.preventDefault(); var s = ov.querySelector('.ck-say'); if (s) s.click(); } }
  function closeCook() { if (!ov) return; stopSpeak(); unwake(); ov.remove(); ov = null; document.documentElement.classList.remove('ck-lock'); document.removeEventListener('keydown', key); }
  function go(i, user) {
    if (!ov) return; stopSpeak();
    if (i < -1) i = -1; if (i >= steps.length) { i = steps.length; }
    idx = i;
    var img = ov.querySelector('.ck-img'), n = ov.querySelector('.ck-n'), t = ov.querySelector('.ck-t'), tm = ov.querySelector('.ck-tm'), pr = ov.querySelector('.ck-prog');
    img.innerHTML = ''; tm.innerHTML = '';
    if (i === -1) { n.textContent = '시작하기 전에'; t.textContent = introText().replace(' 만드는 방법을 알려 드릴게요.', ''); var m0 = A.querySelector('.rp-hero img'); if (m0) img.appendChild(m0.cloneNode()); pr.textContent = '재료 확인'; }
    else if (i >= steps.length) { n.textContent = '완성!'; t.textContent = '맛있게 드세요. 다음 메뉴가 궁금하면 아래 「함께 먹으면 좋은 메뉴」를 확인해 보세요.'; var m1 = A.querySelector('.rp-hero img'); if (m1) img.appendChild(m1.cloneNode()); pr.textContent = '끝'; }
    else {
      n.textContent = (i + 1) + ' / ' + steps.length + '단계'; t.textContent = stepText(i); pr.textContent = (i + 1) + '/' + steps.length;
      var im = steps[i].querySelector('img'); if (im) { var c = im.cloneNode(); c.removeAttribute('loading'); img.appendChild(c); }
      [].forEach.call(steps[i].querySelectorAll('.rp-tmb'), function (b) { var c = b.cloneNode(true); c.onclick = b.onclick; tm.appendChild(c); });
    }
    ov.querySelector('.ck-prev').disabled = i <= -1; ov.querySelector('.ck-next').textContent = i >= steps.length ? '닫기' : '다음 ▶';
    if (i >= steps.length && user === true && ov.querySelector('.ck-next').dataset.closing === '1') { closeCook(); return; }
    ov.querySelector('.ck-next').dataset.closing = i >= steps.length ? '1' : '0';
    if (auto && TTS) readCur();
  }
  function readCur() {
    if (!ov || !TTS) return; var say = ov.querySelector('.ck-say'); if (say) say.textContent = '⏹ 멈추기';
    var text = idx === -1 ? introText() : idx >= steps.length ? '완성입니다. 맛있게 드세요.' : (idx + 1) + '단계. ' + stepText(idx);
    var me = idx;
    speak(text, false, function (err) { if (say) say.textContent = '🔊 읽어 주기'; if (auto && !err && ov && idx === me) setTimeout(function () { if (ov && auto && idx === me) { if (me >= steps.length) { auto = false; return; } go(me + 1, false); } }, 1400); });
  }
  [].forEach.call(A.querySelectorAll('.rp-cookbtn'), function (b) { b.onclick = function () { openCook(-1); }; });
  [].forEach.call(A.querySelectorAll('.rp-saybtn'), function (b) { if (!TTS) { b.remove(); return; } b.onclick = function () { var li = b.closest('li'); var i = steps.indexOf(li); if (i < 0) { openCook(-1); return; } stopSpeak(); speak((i + 1) + '단계. ' + stepText(i)); ga('rp_say', { k: i + 1 }); }; });
  if (!TTS) [].forEach.call(A.querySelectorAll('.rp-needtts'), function (e) { e.remove(); });
  if (/[?&]cook=1/.test(location.search)) setTimeout(function () { openCook(-1); }, 400);
  /* ── 찜 · 식단에 담기 · 최근 본 ── */
  var fav = LS('jupjup_rec_fav', {}), plan = LS('jupjup_plan', []), rec = LS('jupjup_rp_recent', []);
  rec = [TITLE].concat(rec.filter(function (x) { return x !== TITLE; })).slice(0, 12); LSset('jupjup_rp_recent', rec);
  var bar = A.querySelector('.rp-acts');
  if (bar) {
    var fb = h('button', 'rp-mini'), pb = h('button', 'rp-mini');
    fb.type = pb.type = 'button';
    var pf = function () { fb.textContent = fav[TITLE] ? '⭐ 찜했어요' : '☆ 찜하기'; fb.classList.toggle('on', !!fav[TITLE]); pb.textContent = plan.indexOf(TITLE) >= 0 ? '✅ 식단에 담김' : '📅 식단에 담기'; pb.classList.toggle('on', plan.indexOf(TITLE) >= 0); };
    fb.onclick = function () { if (fav[TITLE]) delete fav[TITLE]; else fav[TITLE] = Date.now(); LSset('jupjup_rec_fav', fav); ga('rp_fav', { on: !!fav[TITLE] }); pf(); toast(fav[TITLE] ? '찜 목록에 담았어요' : '찜을 뺐어요'); };
    pb.onclick = function () { var i = plan.indexOf(TITLE); if (i >= 0) plan.splice(i, 1); else plan.push(TITLE); LSset('jupjup_plan', plan); ga('rp_plan', { on: i < 0 }); pf(); toast(i < 0 ? '식단에 담았어요 · 식단표에서 장보기 목록을 볼 수 있어요' : '식단에서 뺐어요'); };
    var row = h('div', 'rp-minis'); row.appendChild(fb); row.appendChild(pb); var lk = h('a', 'rp-mini', '🛒 식단·장보기 보기'); lk.href = '/fridge/plan/'; row.appendChild(lk); bar.appendChild(row); pf();
  }
  setServ(cur === BASE ? BASE : cur);
})();
