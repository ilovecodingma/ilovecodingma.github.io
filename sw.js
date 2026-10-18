// 루리의 줍줍 앱(PWA) 서비스워커 — 홈 화면 설치 + 공모전 웹푸시 알림 (2026-10-18)
const CACHE = 'jupjup-v1';
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(['/', '/app/'])).catch(() => {})); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
// 페이지는 늘 새로 받고, 인터넷이 끊겼을 때만 저장해 둔 화면을 보여 준다
self.addEventListener('fetch', e => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
});
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || '루리의 줍줍', {
    body: d.body || '새 공모전 소식이 있어요.', icon: '/assets/icons/icon-192.png', badge: '/assets/icons/favicon-32.png',
    tag: d.tag || 'jupjup', renotify: true, data: { url: d.url || '/' }
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ws => {
    for (const w of ws) if (w.url === url && 'focus' in w) return w.focus();
    return self.clients.openWindow(url);
  }));
});
