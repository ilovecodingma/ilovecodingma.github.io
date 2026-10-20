// 루리의 줍줍 앱 설치 + 공모전 알림 (2026-10-18 사용자: 앱도 사이트 안에서 배포, 공모전 알림, 웹푸시)
// - 모든 페이지: 서비스워커 등록, 설치 안내(beforeinstallprompt) 보관
// - /app/ (#app-page): 설치 버튼 · 웹푸시 알림(분야·새 공모전·마감 임박) · 회원 메일 알림
(function () {
  const KEY = 'BPLJxC8gRWgtgsm8842p6XgxW-wzQoUJdGXYhYPoPimGFAhtgxJHrJfMecIbu-ni8RKb7w_URkEHisoMYnVKTBY';
  const API = (document.body && document.body.dataset.api) || 'https://jupjup-api.sung2011103.workers.dev';
  const LS = 'jupjup_push_v1';
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const get = () => { try { return JSON.parse(localStorage.getItem(LS) || 'null'); } catch { return null; } };
  const put = v => { try { v ? localStorage.setItem(LS, JSON.stringify(v)) : localStorage.removeItem(LS); } catch {} };
  const ua = navigator.userAgent, ios = /iPhone|iPad|iPod/.test(ua) && !window.MSStream;
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const canPush = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  let prompt = null, swReg = null;
  addEventListener('beforeinstallprompt', e => { e.preventDefault(); prompt = e; paintInstall(); });
  addEventListener('appinstalled', () => { prompt = null; ga('app_installed'); paintInstall(); });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').then(r => { swReg = r; }).catch(() => {});
  const ready = () => navigator.serviceWorker.ready;
  const key = () => { const s = KEY.replace(/-/g, '+').replace(/_/g, '/'), b = atob(s + '='.repeat((4 - s.length % 4) % 4)); return Uint8Array.from(b, c => c.charCodeAt(0)); };
  const tok = () => { try { return localStorage.getItem('jupjup_tok') || ''; } catch { return ''; } };
  const post = (path, body) => fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(tok() ? { Authorization: 'Bearer ' + tok() } : {}) }, body: JSON.stringify(body) })
    .then(async r => { const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || '잠시 뒤에 다시 해 주세요.'); return d; });

  async function subscribe(opt) {
    if (!canPush()) throw new Error(ios && !standalone() ? '아이폰은 먼저 홈 화면에 추가한 뒤, 그 앱에서 알림을 켜 주세요.' : '이 브라우저는 알림을 지원하지 않아요. 크롬·엣지·사파리 최신판에서 해 주세요.');
    const perm = await Notification.requestPermission();
    if (perm !== 'granted') throw new Error('알림이 차단돼 있어요. 브라우저 주소창 왼쪽 자물쇠 → 알림 → 허용으로 바꿔 주세요.');
    const reg = await ready();
    const sub = (await reg.pushManager.getSubscription()) || await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key() });
    await post('/api/push/sub', { sub: sub.toJSON(), cats: opt.cats, newc: opt.newc ? 1 : 0, dl: opt.dl ? 1 : 0, meal: opt.meal === false ? 0 : 1 });
    put(opt);
    return reg;
  }
  async function unsubscribe() {
    try { const reg = await ready(), sub = await reg.pushManager.getSubscription(); if (sub) { await post('/api/push/unsub', { endpoint: sub.endpoint }).catch(() => {}); await sub.unsubscribe(); } } catch {}
    put(null);
  }
  async function isOn() {
    if (!canPush() || Notification.permission !== 'granted') return false;
    try { const reg = await ready(); return !!(await reg.pushManager.getSubscription()) && !!get(); } catch { return false; }
  }

  // ---------------- /app/ 화면
  const ROOT = document.getElementById('app-page');
  function paintInstall() {
    const el = ROOT && ROOT.querySelector('.ap-inst'); if (!el) return;
    if (standalone()) { el.innerHTML = '<p class="ap-ok">✅ 지금 앱으로 보고 있어요. 아래에서 알림만 켜면 끝!</p>'; return; }
    if (prompt) {
      el.innerHTML = '<button class="ap-btn ap-install">📲 홈 화면에 앱 설치하기</button><p class="ap-sm">설치해도 용량은 거의 안 차요(1MB 미만). 언제든 지울 수 있어요.</p>';
      el.querySelector('.ap-install').onclick = async () => { prompt.prompt(); const r = await prompt.userChoice.catch(() => ({})); ga('app_install_click', { outcome: r && r.outcome }); prompt = null; paintInstall(); };
      return;
    }
    el.innerHTML = ios
      ? '<ol class="ap-steps"><li>사파리 아래쪽 <b>공유 버튼(□↑)</b>을 눌러요</li><li><b>홈 화면에 추가</b>를 눌러요</li><li>홈 화면의 <b>루리의 줍줍</b> 앱을 열고, 아래에서 알림을 켜요</li></ol><p class="ap-sm">아이폰은 iOS 16.4 이상, 사파리에서만 설치·알림이 돼요.</p>'
      : '<ol class="ap-steps"><li>크롬 오른쪽 위 <b>⋮ 메뉴</b>를 눌러요</li><li><b>홈 화면에 추가</b> 또는 <b>앱 설치</b>를 눌러요</li><li>홈 화면의 <b>루리의 줍줍</b> 앱으로 열면 끝!</li></ol><p class="ap-sm">PC 크롬·엣지는 주소창 오른쪽 <b>설치(⊕)</b> 아이콘을 눌러도 돼요.</p>';
  }
  async function paintPush() {
    const el = ROOT.querySelector('.ap-push'), cats = JSON.parse(ROOT.dataset.cats || '[]');
    const on = await isOn(), cur = Object.assign({ cats: [], newc: true, dl: true, meal: true }, get() || {});
    el.innerHTML = `<label class="ap-sw ap-main"><input type="checkbox" class="ap-meal" ${cur.meal ? 'checked' : ''}> 🍽️ <b>오늘 뭐 먹지?</b> 점심·저녁 메뉴 추천 (11:30·17:30쯤, 하루 최대 2번)</label>
<p class="ap-sm">관심 분야를 고르면 <b>새 공모전이 올라온 날 저녁에 한 번</b>, <b>인기 공모전 마감 3일 전</b>에 폰으로 알려 드려요. 하루 최대 2번이에요.</p>
<div class="ap-cats">${cats.map(([s, n, i]) => `<button data-c="${s}" class="${cur.cats.includes(s) ? 'on' : ''}">${i} ${esc(n)}</button>`).join('')}</div><p class="ap-sm">하나도 안 고르면 전체 분야로 받아요.</p>
<label class="ap-sw"><input type="checkbox" class="ap-newc" ${cur.newc ? 'checked' : ''}> 🆕 새 공모전 올라오면 (저녁 7시쯤 모아서)</label>
<label class="ap-sw"><input type="checkbox" class="ap-dl" ${cur.dl ? 'checked' : ''}> ⏰ 인기 공모전 마감 3일 전 (아침 9시쯤)</label>
<button class="ap-btn ap-on">${on ? '💾 알림 설정 저장' : '🔔 알림 켜기'}</button>${on ? '<button class="ap-off">알림 끄기</button>' : ''}<p class="ap-msg">${on ? '✅ 알림이 켜져 있어요.' : ''}</p>`;
    el.querySelectorAll('.ap-cats button').forEach(b => b.onclick = () => b.classList.toggle('on'));
    const msg = el.querySelector('.ap-msg');
    el.querySelector('.ap-on').onclick = async () => {
      const opt = { cats: [...el.querySelectorAll('.ap-cats button.on')].map(b => b.dataset.c), newc: el.querySelector('.ap-newc').checked, dl: el.querySelector('.ap-dl').checked, meal: el.querySelector('.ap-meal').checked };
      msg.textContent = '설정하는 중…';
      try {
        const reg = await subscribe(opt);
        if (!on) reg.showNotification('🔔 알림이 켜졌어요!', { body: '메뉴 추천과 새 공모전 소식을 루리가 챙겨 드릴게요.', icon: '/assets/icons/icon-192.png', tag: 'jupjup-hello', data: { url: '/app/' } });
        ga('push_on', { cats: opt.cats.join(',') || 'all', meal: opt.meal ? 1 : 0 }); paintPush();
      } catch (e) { msg.textContent = '⚠️ ' + e.message; }
    };
    const off = el.querySelector('.ap-off'); if (off) off.onclick = async () => { await unsubscribe(); ga('push_off'); paintPush(); };
  }
  async function paintMail() {
    const el = ROOT.querySelector('.ap-mail');
    for (let i = 0; i < 40 && !window.JUP; i++) await new Promise(r => setTimeout(r, 100));
    const J = window.JUP;
    if (!J || !J.st.t) {
      el.innerHTML = '<p class="ap-sm">회원이면 찜한 공모전 마감 메일, 관심 분야 새 공모전 메일도 받을 수 있어요.</p><button class="ap-btn ghost ap-login">로그인하고 메일 알림 받기</button>';
      el.querySelector('.ap-login').onclick = () => J && J.authModal(() => location.reload());
      return;
    }
    const me = await J.api('/api/me').catch(() => null); if (!me) return;
    const P = me.prefs || {}, save = d => J.api('/api/prefs', { method: 'POST', body: { data: { ...P, ...d } } }).then(() => Object.assign(P, d));
    el.innerHTML = me.email ? `<p class="ap-sm">받는 주소: <b>${esc(me.email)}</b></p>
<label class="ap-sw"><input type="checkbox" class="ap-m1" ${P.alert === '1' ? 'checked' : ''}> ⏰ 찜한 공모전 마감 3일 전·당일 메일</label>
<label class="ap-sw"><input type="checkbox" class="ap-m2" ${P.anew === '1' ? 'checked' : ''}> 🆕 관심 분야 새 공모전 메일 (위에서 고른 분야, 하루 한 통)</label><p class="ap-msg ap-mmsg"></p>`
      : '<p class="ap-sm">카카오 등 이메일이 없는 계정이에요. 메일 알림 대신 위의 폰 알림을 켜 주세요.</p>';
    const m = el.querySelector('.ap-mmsg'), done = () => { m.textContent = '✅ 저장했어요.'; };
    const c1 = el.querySelector('.ap-m1'), c2 = el.querySelector('.ap-m2');
    if (c1) c1.onchange = () => save({ alert: c1.checked ? '1' : '0' }).then(done);
    if (c2) c2.onchange = () => { const cats = [...ROOT.querySelectorAll('.ap-cats button.on')].map(b => b.dataset.c).join(','); save({ anew: c2.checked ? '1' : '0', acats: cats }).then(done); ga('mail_new_toggle', { on: c2.checked }); };
  }
  if (ROOT) { paintInstall(); paintPush(); paintMail(); }
  window.JPUSH = { subscribe, unsubscribe, isOn };
})();

// ---------------- 자동 번역 (2026-10-18 사용자: "영어 등 자동 번역 기능도 만들어") — 구글 번역 위젯, 누를 때만 불러옴, 고른 언어는 다음 페이지에도 유지
(function () {
  const LANGS = [['ko', '한국어(원문)'], ['en', 'English'], ['ja', '日本語'], ['zh-CN', '中文(简体)'], ['zh-TW', '中文(繁體)'], ['vi', 'Tiếng Việt'], ['th', 'ไทย'], ['id', 'Bahasa Indonesia'], ['es', 'Español'], ['ru', 'Русский']];
  const K = 'jupjup_lang';
  const get = () => { try { return localStorage.getItem(K) || 'ko'; } catch { return 'ko'; } };
  const set = v => { try { localStorage.setItem(K, v); } catch {} };
  let loading = null;
  function load() {
    if (loading) return loading;
    loading = new Promise(res => {
      const d = document.createElement('div'); d.id = 'gt-el'; d.style.display = 'none'; document.body.appendChild(d);
      window.__gtInit = () => { new google.translate.TranslateElement({ pageLanguage: 'ko', autoDisplay: false }, 'gt-el'); const w = () => document.querySelector('.goog-te-combo') ? res() : setTimeout(w, 150); w(); };
      const s = document.createElement('script'); s.src = 'https://translate.google.com/translate_a/element.js?cb=__gtInit'; s.async = true; s.onerror = () => res(); document.head.appendChild(s);
    });
    return loading;
  }
  async function apply(lang) {
    set(lang);
    if (lang === 'ko') { document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'; document.cookie = 'googtrans=; path=/; domain=' + location.hostname + '; expires=Thu, 01 Jan 1970 00:00:00 GMT'; if (document.documentElement.classList.contains('translated-ltr') || document.documentElement.lang !== 'ko') location.reload(); return; }
    document.cookie = 'googtrans=/ko/' + lang + '; path=/';   // 위젯이 시작할 때 이 쿠키를 읽어 자동 번역(다음 페이지에도 유지)
    const first = !document.querySelector('.goog-te-combo');
    await load();
    const c = document.querySelector('.goog-te-combo'); if (!c) return;
    const fire = () => { c.value = lang; c.dispatchEvent(new Event('change', { bubbles: true })); };
    if (!first) fire(); else { setTimeout(fire, 600); setTimeout(() => { if (!document.documentElement.classList.contains('translated-ltr')) fire(); }, 1800); }
    try { window.gtag && gtag('event', 'translate', { lang }); } catch {}
  }
  function button() {
    const hd = document.querySelector('.hd-in'); if (!hd || hd.querySelector('.lang-b')) return;
    const b = document.createElement('div'); b.className = 'lang-b notranslate';
    b.innerHTML = `<button type="button" aria-label="Language / 언어">🌐 <span>${get() === 'ko' ? 'KO' : get().slice(0, 2).toUpperCase()}</span></button><ul hidden>${LANGS.map(([v, t]) => `<li><button type="button" data-l="${v}">${t}</button></li>`).join('')}</ul>`;
    hd.appendChild(b);
    const ul = b.querySelector('ul');
    b.querySelector('button').onclick = e => { e.stopPropagation(); ul.hidden = !ul.hidden; };
    b.querySelectorAll('[data-l]').forEach(x => x.onclick = () => { ul.hidden = true; b.querySelector('span').textContent = x.dataset.l === 'ko' ? 'KO' : x.dataset.l.slice(0, 2).toUpperCase(); apply(x.dataset.l); });
    document.addEventListener('click', () => { ul.hidden = true; });
  }
  const start = () => { button(); if (get() !== 'ko') apply(get()); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();


// ---------------- 앱 셸 (2026-10-20 사용자: "레시피 추천 앱으로 오늘 뭐먹지 느낌으로, 기존 앱 고도화")
(function () {
  const sa = matchMedia('(display-mode: standalone)').matches || navigator.standalone === true, q = new URLSearchParams(location.search), P = location.pathname;
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  // 이미 깔려 있던 앱(시작 화면이 홈)은 한 번만 오늘의 추천으로 데려온다
  try { if (sa && P === '/' && !sessionStorage.getItem('app_go') && !q.has('home')) { sessionStorage.setItem('app_go', '1'); location.replace('/fridge/?src=app'); return; } } catch {}
  if (sa || q.get('src') === 'app') {
    document.documentElement.classList.add('app-mode');
    // 하단바는 지금 보는 섹션(레시피·생활·공모전·이슈·머니…)의 메뉴를 그대로 쓴다. 섹션 이동은 「섹션」 버튼
    const IC = [[/fridge\/solo/, '🏠'], [/fridge\/weather/, '🌤️'], [/^\/fridge\/c\//, '🍲'], [/^\/fridge/, '🍽️'], [/contest\/week/, '⏰'], [/contest\/univ/, '🎓'], [/^\/cat\//, '🗂️'], [/community/, '🚩'], [/^\/contest/, '🏆'], [/prep/, '📋'], [/lab/, '🔬'], [/guide/, '📘'], [/apply\/r/, '📍'], [/apply/, '📋'], [/event/, '🎁'], [/qa/, '💬'], [/plaza/, '🗣️'],
      [/news/, '🕵️'], [/hot/, '🔥'], [/trend/, '📈'], [/talk/, '💬'], [/kw/, '🔎'], [/satire/, '🎭'], [/mag/, '📰'], [/review/, '🖋️'], [/analyst/, '📊'], [/money/, '🧮'], [/game/, '🎮'], [/ailog|dev/, '💻'], [/^\/$/, '🏠'], [/app/, '🔔'], [/me/, '👤']];
    const ic = h => { for (const [r, e] of IC) if (r.test(h)) return e; return '•'; };
    const mount = () => {
      const tb = document.querySelector('nav.tb'), sw = document.querySelector('nav.th-sw');
      const links = tb ? [...tb.querySelectorAll('a')].slice(0, 4) : [];
      const bar = document.createElement('nav'); bar.className = 'app-tb'; bar.setAttribute('aria-label', '앱 메뉴');
      const home = ['🏠', '홈', '/'];
      const items = links.length ? links.map(a => [ic(a.getAttribute('href')), a.textContent.trim().slice(0, 6), a.getAttribute('href'), a.classList.contains('on')]) : [[...home, P === '/']];
      bar.innerHTML = items.map(([i, t, u, on]) => `<a href="${u}"${on ? ' class="on"' : ''}><i>${i}</i>${t}</a>`).join('') + '<button type="button" class="more"><i>☰</i>섹션</button>';
      document.body.appendChild(bar);
      if (tb) tb.classList.add('app-hide');
      bar.querySelector('.more').onclick = () => {
        const sec = sw ? [...sw.querySelectorAll('a')].map(a => `<a href="${a.getAttribute('href')}"><span>${a.textContent.trim().split(' ')[0]}</span><span>${a.textContent.trim().split(' ').slice(1).join(' ')}</span></a>`).join('') : '';
        const sh = document.createElement('div'); sh.className = 'app-sheet';
        sh.innerHTML = `<div><b>섹션 이동</b><a href="/"><span>🏠</span><span>홈</span></a>${sec}<a href="/me/"><span>👤</span><span>내 공간</span></a><a href="/app/"><span>🔔</span><span>알림 설정</span></a></div>`;
        sh.onclick = e => { if (e.target === sh) sh.remove(); }; document.body.appendChild(sh); ga('app_more');
      };
    };
    document.body ? mount() : addEventListener('DOMContentLoaded', mount);
  } else if (P === '/fridge/' || /^\/fridge\/(solo|weather)\//.test(P)) {
    // 레시피 화면을 두 번째 이상 보면 앱 설치를 한 번 권한다(일주일에 한 번)
    try {
      const n = +(localStorage.getItem('jupjup_fr_visit') || 0) + 1; localStorage.setItem('jupjup_fr_visit', n);
      const last = +(localStorage.getItem('jupjup_ins_ask') || 0);
      addEventListener('beforeinstallprompt', e => {
        e.preventDefault(); const ev = e;
        if (n < 2 || Date.now() - last < 7 * 864e5) return;
        const b = document.createElement('div'); b.className = 'app-ins'; b.innerHTML = '<span>📲 <b>오늘 뭐 먹지?</b>를 앱으로 설치하면<br>점심·저녁 메뉴를 알려 드려요</span><button class="go">설치</button><button class="no">나중에</button>';
        document.body.appendChild(b); localStorage.setItem('jupjup_ins_ask', Date.now()); ga('app_install_banner');
        b.querySelector('.no').onclick = () => b.remove();
        b.querySelector('.go').onclick = async () => { ev.prompt(); const r = await ev.userChoice.catch(() => ({})); ga('app_install_click', { outcome: r && r.outcome, from: 'banner' }); b.remove(); };
      });
    } catch {}
  }
})();
