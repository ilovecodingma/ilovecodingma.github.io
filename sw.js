// 오늘 뭐 먹지? · 루리의 줍줍 앱(PWA) 서비스워커 — 홈 화면 설치 + 오프라인 추천 + 웹푸시 (2026-10-18 최초, 2026-10-20 레시피 추천 앱으로 고도화)
//  · 화면(HTML)은 늘 새로 받고, 인터넷이 끊기면 저장해 둔 화면 → 그것도 없으면 오늘의 추천(/fridge/)을 보여 준다
//  · 추천 데이터·스크립트·작은 사진은 한 번 받아 두면 오프라인에서도 「오늘 뭐 먹지」가 돈다
const PAGES = 'jupjup-pages-v2', ASSETS = 'jupjup-assets-v2', IMGS = 'jupjup-img-v1', KEEP = [PAGES, ASSETS, IMGS];
const SHELL = ['/', '/fridge/', '/app/', '/assets/fridge/rec.json', '/assets/fridge/today.json', '/assets/fridge/rec_pop.json'];
const trim = async (name, max) => { const c = await caches.open(name), ks = await c.keys(); for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]); };

self.addEventListener('install', e => {
  e.waitUntil(caches.open(PAGES).then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {})))).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => !KEEP.includes(k)).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET') return;
  const u = new URL(r.url); if (u.origin !== self.location.origin) return;
  // 화면: 네트워크 우선, 끊기면 저장본 → 오늘의 추천
  if (r.mode === 'navigate') {
    e.respondWith(fetch(r).then(res => { if (res.ok && /^\/(fridge|app)\//.test(u.pathname) || u.pathname === '/') { const cp = res.clone(); caches.open(PAGES).then(c => c.put(r, cp)).then(() => trim(PAGES, 60)); } return res; })
      .catch(() => caches.match(r, { ignoreSearch: true }).then(x => x || caches.match('/fridge/') || caches.match('/'))));
    return;
  }
  // 추천 데이터: 저장본을 바로 쓰고 뒤에서 새로 받아 둔다
  if (/^\/assets\/fridge\/(rec|rec_pop|today|recipes)\.json$/.test(u.pathname)) {
    e.respondWith(caches.open(ASSETS).then(c => c.match(r, { ignoreSearch: true }).then(hit => {
      const net = fetch(r).then(res => { if (res.ok) c.put(new Request(u.origin + u.pathname), res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  // 음식 사진: 한 번 본 건 저장(최대 220장)
  if (/^\/assets\/fridge\/(ph|rc|img)\//.test(u.pathname)) {
    e.respondWith(caches.open(IMGS).then(c => c.match(r).then(hit => hit || fetch(r).then(res => { if (res.ok) { c.put(r, res.clone()); trim(IMGS, 220); } return res; }))));
    return;
  }
  // 스크립트·스타일: 주소에 버전(?v=)이 붙어 있어 저장본을 그대로 써도 안전
  if (/\.(js|css)$/.test(u.pathname) && u.pathname.startsWith('/assets/')) {
    e.respondWith(caches.open(ASSETS).then(c => c.match(r).then(hit => hit || fetch(r).then(res => { if (res.ok) c.put(r, res.clone()); return res; }))));
  }
});

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || '루리의 줍줍', {
    body: d.body || '새 소식이 있어요.', icon: d.icon || '/assets/icons/icon-192.png', badge: '/assets/icons/favicon-32.png',
    ...(d.image ? { image: d.image } : {}), tag: d.tag || 'jupjup', renotify: true, data: { url: d.url || '/' },
    ...(d.tag === 'jupjup-meal' ? { actions: [{ action: 'open', title: '레시피 보기' }, { action: 'another', title: '다른 메뉴' }] } : {})
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const base = (e.notification.data && e.notification.data.url) || '/';
  const url = new URL(e.action === 'another' ? '/fridge/?src=push_meal&reroll=1' : base, self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ws => {
    for (const w of ws) if (w.url === url && 'focus' in w) return w.focus();
    return self.clients.openWindow(url);
  }));
});
