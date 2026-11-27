// 잠이 오냐 (2026-11-27) — 관심 시험·분야 선택 + 푸시 구독/해지 + 메일 설정. /app/ 전용.
// 푸시는 워커 /api/push/sub(exams·topics·sch·qz·nw·qh) → D1 push_subs → PC 의 _gongmo/exam_push.py 가 보낸다. 서비스워커·설치 프롬프트 등록은 공용 app.js 가 한다.
(function () {
  const ROOT = document.getElementById('jam'); if (!ROOT) return;
  const KEY = 'BPLJxC8gRWgtgsm8842p6XgxW-wzQoUJdGXYhYPoPimGFAhtgxJHrJfMecIbu-ni8RKb7w_URkEHisoMYnVKTBY';
  const API = (document.body && document.body.dataset.api) || 'https://jupjup-api.sung2011103.workers.dev';
  const LS = 'jam_v1';
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const $ = s => ROOT.querySelector(s);
  const ua = navigator.userAgent, ios = /iPhone|iPad|iPod/.test(ua) && !window.MSStream;
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const canPush = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  const tok = () => { try { return localStorage.getItem('jupjup_tok') || ''; } catch { return ''; } };
  const load = () => { try { return JSON.parse(localStorage.getItem(LS) || 'null') || {}; } catch { return {}; } };
  const keep = v => { try { localStorage.setItem(LS, JSON.stringify(v)); } catch {} };
  const call = (path, body) => fetch(API + path, { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json', ...(tok() ? { Authorization: 'Bearer ' + tok() } : {}) }, ...(body ? { body: JSON.stringify(body) } : {}) })
    .then(async r => { const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || '잠시 뒤에 다시 해.'); return d; });
  const key = () => { const s = KEY.replace(/-/g, '+').replace(/_/g, '/'), b = atob(s + '='.repeat((4 - s.length % 4) % 4)); return Uint8Array.from(b, c => c.charCodeAt(0)); };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const S = Object.assign({ exams: [], topics: [], sch: 1, qz: 1, nw: 1, qh: 8, xf: 'd' }, load());
  let cat = { fams: [], fields: [] }, prompt = null;
  addEventListener('beforeinstallprompt', e => { e.preventDefault(); prompt = e; paintInstall(); });

  function chips(el, items, sel, fmt, max) {
    el.innerHTML = items.map(x => `<label class="${sel.includes(x.k) ? 'on' : ''}" data-s="${esc((x.n + ' ' + x.k).toLowerCase())}"><input type="checkbox" value="${x.k}" ${sel.includes(x.k) ? 'checked' : ''}>${esc(x.n)} ${fmt(x)}</label>`).join('');
    el.onchange = e => {
      const i = e.target, on = [...el.querySelectorAll('input:checked')].map(c => c.value);
      if (max && on.length > max) { i.checked = false; msg(`시험은 ${max}개까지만 고른다. 다 하려다 다 놓친다.`); return; }
      sel.length = 0; on.forEach(v => sel.push(v)); i.parentNode.classList.toggle('on', i.checked); keep(S); paintCount();
    };
  }
  const nxFmt = x => x.nx ? `<small>${x.nx.slice(5).replace('-', '.')}</small>` : (x.q ? `<small>문제 ${x.q}</small>` : '');
  function paintCount() { $('.jm-cnt').innerHTML = `시험 <span class="jm-n">${S.exams.length}</span> · 분야 <span class="jm-n">${S.topics.length}</span>`; }
  const msg = t => { const m = $('.jm-msg'); if (m) m.textContent = t; };

  function paintInstall() {
    const el = $('.jm-inst'); if (!el) return;
    if (standalone()) { el.innerHTML = '<p class="jm-sm">앱으로 열었네. 알림만 켜면 끝이다.</p>'; return; }
    if (prompt) { el.innerHTML = '<button class="jm-btn ghost jm-ins">📲 홈 화면에 깔기</button>'; el.querySelector('.jm-ins').onclick = async () => { prompt.prompt(); const r = await prompt.userChoice.catch(() => ({})); ga('jam_install', { outcome: r && r.outcome }); prompt = null; paintInstall(); }; return; }
    el.innerHTML = ios ? '<p class="jm-sm">아이폰은 사파리 공유 버튼(□↑) → 홈 화면에 추가 → 그 앱을 열어서 알림 켜라. 안 그러면 안 온다.</p>' : '<p class="jm-sm">크롬 ⋮ 메뉴 → 앱 설치(홈 화면에 추가). 안 깔아도 알림은 켤 수 있다.</p>';
  }

  async function status() {
    let on = false;
    try { if (canPush() && Notification.permission === 'granted') { const reg = await navigator.serviceWorker.ready; on = !!(await reg.pushManager.getSubscription()); } } catch {}
    const st = $('.jm-stat');
    st.className = 'jm-st' + (on ? ' on' : ''); st.innerHTML = '<i></i>' + (on ? '알림 켜져 있다. 이제 도망 못 간다.' : '알림 꺼져 있다. 그래서 맨날 놓치는 거다.');
    $('.jm-off').hidden = !on; $('.jm-go').textContent = on ? '고른 걸로 다시 저장' : '알림 켜고 정신 차리기';
    return on;
  }

  async function save() {
    if (!S.exams.length && !S.topics.length) { msg('하나도 안 골랐다. 뭘 알려 주라는 거냐.'); return; }
    if (!canPush()) { msg(ios && !standalone() ? '아이폰은 먼저 홈 화면에 추가해라. 그 앱에서 알림을 켜야 한다.' : '이 브라우저는 알림이 안 된다. 크롬·엣지·사파리 최신판을 써라.'); return; }
    const b = $('.jm-go'); b.disabled = true;
    try {
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') throw new Error('알림 차단돼 있다. 주소창 자물쇠 → 알림 → 허용으로 바꿔라.');
      const reg = await navigator.serviceWorker.ready;
      const sub = (await reg.pushManager.getSubscription()) || await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key() });
      await call('/api/push/sub', { sub: sub.toJSON(), exams: S.exams, topics: S.topics, sch: S.sch, qz: S.qz, nw: S.nw, qh: S.qh,
        newc: 0, dl: 0, dl2: 0, meal: 0, fit: 0 });   // 옛 공모전·식단·운동 알림은 이 틀로 흡수 — 옛 플래그는 끈다
      keep(S); ga('jam_push_on', { exams: S.exams.length, topics: S.topics.length }); msg('저장했다. 이제 잔소리 들어갈 차례다.');
    } catch (e) { msg(e.message || '실패했다. 다시 눌러라.'); }
    b.disabled = false; status();
  }
  async function off() {
    try { const reg = await navigator.serviceWorker.ready, sub = await reg.pushManager.getSubscription(); if (sub) { await call('/api/push/unsub', { endpoint: sub.endpoint }).catch(() => {}); await sub.unsubscribe(); } } catch {}
    ga('jam_push_off'); msg('껐다. 그래도 시험은 온다.'); status();
  }

  async function mail() {
    const el = $('.jm-mail');
    if (!tok()) { el.innerHTML = '<p class="jm-sm">메일로도 받으려면 로그인해라. 위에서 고른 시험·분야 그대로 보낸다.</p><a class="jm-btn ghost" style="text-align:center;text-decoration:none" href="/me/">로그인하러 가기</a>'; return; }
    let me = {}; try { me = await call('/api/me'); } catch {}
    const P = me.prefs || {}; if (!me.prefs && !me.email) { el.innerHTML = '<p class="jm-sm">로그인이 풀렸다. <a href="/me/">다시 로그인</a>해라.</p>'; return; }
    const on = P.xm === '1', xf = P.xf === 'w' ? 'w' : 'd';
    el.innerHTML = `<label class="jm-sw"><input type="checkbox" class="jm-xm" ${on ? 'checked' : ''}><span>고른 시험·분야를 메일로도 받는다<small>소식 없는 날은 안 보낸다. 귀찮으면 언제든 끈다.</small></span></label>
<label class="jm-sw"><span>보내는 때</span><select class="jm-sel jm-xf"><option value="d" ${xf === 'd' ? 'selected' : ''}>매일 아침</option><option value="w" ${xf === 'w' ? 'selected' : ''}>월요일에 한 번</option></select></label>
<button class="jm-btn ghost jm-xs">메일 설정 저장</button><p class="jm-sm jm-xm-msg"></p>`;
    el.querySelector('.jm-xs').onclick = async () => {
      const m = el.querySelector('.jm-xm-msg'), want = el.querySelector('.jm-xm').checked;
      if (want && !S.exams.length && !S.topics.length) { m.textContent = '시험이든 분야든 하나는 골라라.'; return; }
      try { await call('/api/prefs', { data: { ...P, exams: S.exams.join(','), sdt: S.topics.join(','), xm: want ? '1' : '0', xf: el.querySelector('.jm-xf').value } }); m.textContent = want ? `저장했다. ${esc(me.email || '가입 메일')}로 간다.` : '메일 껐다.'; ga('jam_mail', { on: want }); }
      catch (e) { m.textContent = e.message; }
    };
    if (!S.exams.length && !S.topics.length && (P.exams || P.sdt)) { S.exams = (P.exams || '').split(',').filter(Boolean); S.topics = (P.sdt || '').split(',').filter(Boolean); keep(S); draw(); }
  }

  function draw() {
    chips($('.jm-fams'), cat.fams, S.exams, nxFmt, 20);
    chips($('.jm-flds'), cat.fields, S.topics, () => '', 0);
    $('.jm-fd').innerHTML = cat.fields.map(f => `<b>${esc(f.n)}</b> ${esc(f.d)}`).join('<br>');
    paintCount();
  }

  ROOT.innerHTML = `<p class="bc"><a href="/">홈</a> › 잠이 오냐</p>
<div class="jm-hero"><img src="/assets/icons/icon-192.png" alt="잠이 오냐 앱 아이콘" width="60" height="60"><div><b>잠이 오냐</b><span>시험 일정·오늘의 문제·헬조선 생존 정보를 니가 고른 것만 쪼아 준다.</span></div></div>
<h2>1. 어떤 시험 볼 거냐 <small class="jm-cnt"></small></h2><div class="jm-card"><input class="jm-q" type="search" placeholder="시험 검색 (토익, 공무원, 기사…)" aria-label="시험 검색"><div class="jm-chips jm-fams"></div><p class="jm-sm">접수 시작·마감·시험일 D-7·3·1·당일에 때려 주고, 오늘의 문제를 하나씩 던진다. 날짜는 다음 일정이다.</p></div>
<h2>2. 또 뭘 놓치고 사냐</h2><div class="jm-card"><div class="jm-chips jm-flds"></div><p class="jm-sm jm-fd"></p></div>
<h2>3. 어떻게 쪼아 줄까</h2><div class="jm-card">
<label class="jm-sw"><input type="checkbox" class="jm-sch"><span>일정·마감<small>접수·시험일·지원금·청약·공모전 마감 임박</small></span></label>
<label class="jm-sw"><input type="checkbox" class="jm-qz"><span>오늘의 문제 (시험만)<small>알림에 문제와 보기가 바로 뜬다. 누르면 풀러 간다</small></span></label>
<label class="jm-sw"><input type="checkbox" class="jm-nw"><span>새 소식<small>고른 시험의 새 글, 고른 분야의 새 항목</small></span></label>
<label class="jm-sw"><span>문제 보내는 시각</span><select class="jm-sel jm-qh"></select></label></div>
<h2>4. 폰 알림</h2><div class="jm-card"><div class="jm-stat jm-st"><i></i>확인 중…</div><div class="jm-inst"></div><button class="jm-btn jm-go">알림 켜고 정신 차리기</button><button class="jm-off" hidden>알림 끄기</button><p class="jm-msg" role="status"></p></div>
<h2>5. 메일</h2><div class="jm-card jm-mail"><p class="jm-sm">불러오는 중…</p></div>`;
  $('.jm-qh').innerHTML = Array.from({ length: 24 }, (_, h) => `<option value="${h}">${h < 12 ? '오전' : '오후'} ${h % 12 || 12}시</option>`).join('');
  for (const k of ['sch', 'qz', 'nw']) { const c = $('.jm-' + k); c.checked = !!S[k]; c.onchange = () => { S[k] = c.checked ? 1 : 0; keep(S); }; }
  $('.jm-qh').value = S.qh; $('.jm-qh').onchange = e => { S.qh = +e.target.value; keep(S); };
  $('.jm-q').oninput = e => { const v = e.target.value.trim().toLowerCase(); ROOT.querySelectorAll('.jm-fams label').forEach(l => { l.hidden = !!v && !l.dataset.s.includes(v); }); };
  $('.jm-go').onclick = save; $('.jm-off').onclick = off;
  paintInstall(); status();
  fetch('/assets/app/jam.json?v=1').then(r => r.json()).then(c => { cat = c; draw(); mail(); }).catch(() => { msg('목록을 못 불러왔다. 새로고침해라.'); });
})();
