// 루리의 줍줍 커뮤니티 API — Cloudflare Worker + D1 (바인딩 이름: DB)
// 회원가입·로그인(이메일+비밀번호만 받음 — 2026-10-16 사용자 "최소 정보, 이메일 주소만"; 표시 이름은 이메일 앞부분을 가린 값), 공모전별 팀 모집(만들기·신청·수락), 후기·질문 게시판, 댓글, 신고(3회 누적 시 자동 숨김)
const ORIGINS = ['https://sungprofile.cloud', 'http://localhost:8765'];
const DAY = 86400, LIMIT_POST = 10, LIMIT_COMMENT = 40, HIDE_AT = 3;

const now = () => Math.floor(Date.now() / 1000);
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
const unhex = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));
const clean = (s, n) => String(s || '').replace(/[\u0000-\u0008\u000b-\u001f]/g, '').trim().slice(0, n);
// 페이지 주소를 댓글·좋아요·조회수의 열쇠로 쓰기 위해 한 모양으로 맞춘다(/fridge/r/김치찌개/)
const npage = s => {
  let x = String(s || '').split('#')[0].split('?')[0];
  try { x = decodeURIComponent(x); } catch {}
  x = x.replace(/[\u0000-\u001f\s]/g, '');
  if (!x.startsWith('/') || x.includes('..')) return '';
  if (!/\/$/.test(x)) x += '/';
  return x.length <= 120 ? x : '';
};

async function hashPw(pw, saltHex, iter = 100000) {
  const salt = saltHex ? unhex(saltHex) : crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations: iter }, key, 256);
  return `pbkdf2$${iter}$${hex(salt)}$${hex(bits)}`;
}
async function checkPw(pw, stored) {
  const [, iter, salt] = stored.split('$');
  const h = await hashPw(pw, salt, +iter);
  return h.length === stored.length && crypto.subtle.timingSafeEqual
    ? crypto.subtle.timingSafeEqual(new TextEncoder().encode(h), new TextEncoder().encode(stored)) : h === stored;
}

function cors(req) {
  const o = req.headers.get('Origin');
  return { 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
           'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Max-Age': '86400', Vary: 'Origin' };
}
const json = (req, data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(req) } });
const err = (req, msg, status = 400) => json(req, { error: msg }, status);

async function me(req, env) {
  const t = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/, '');
  if (!t) return null;
  const r = await env.DB.prepare('SELECT u.id, u.nick, u.banned FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ? AND s.expires > ?').bind(t, now()).first();
  return r && !r.banned ? r : null;
}
async function newSession(env, uid) {
  const token = hex(crypto.getRandomValues(new Uint8Array(24)));
  await env.DB.prepare('INSERT INTO sessions (token, user_id, expires) VALUES (?, ?, ?)').bind(token, uid, now() + 30 * DAY).run();
  return token;
}
const ADMINS = [16];  // 관리자 계정(사장님 구글 계정)
async function count(env, sql, ...a) { return (await env.DB.prepare(sql).bind(...a).first('n')) || 0; }

// 사이트 레시피 목록을 30분 캐시해 읽는다(추천 묻기용)
async function recipeIndex(env) {
  const key = new Request('https://jupjup.internal/fridge-recipes'), cache = caches.default;
  let hit = await cache.match(key);
  if (!hit) {
    const r = await fetch('https://sungprofile.cloud/assets/fridge/recipes.json');
    if (!r.ok) throw new Error('recipes ' + r.status);
    hit = new Response(await r.text(), { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'max-age=1800' } });
    await cache.put(key, hit.clone());
  }
  return (await hit.json()).recipes || [];
}


// ---- 카카오톡 마감 알림 (2026-10-19 사용자 승인): 알림을 켤 때만 talk_message 추가 동의 → refresh_token 을 AES-GCM 으로 암호화해 D1 kakao_alert 에 보관
//      매일 08:30 KST(Cron 30 23 * * * UTC) 찜한 것 중 D-3·D-1 을 「나에게 보내기」로. 끄면 talk_message 동의 철회 + 토큰 삭제(로그인 연결은 유지)
async function aesKey(env) { return crypto.subtle.importKey('raw', unhex(env.KAKAO_ALERT_KEY), 'AES-GCM', false, ['encrypt', 'decrypt']); }
async function enc(env, t) { const iv = crypto.getRandomValues(new Uint8Array(12)); return hex(iv) + '.' + hex(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await aesKey(env), new TextEncoder().encode(t))); }
async function dec(env, t) { const [iv, c] = t.split('.'); return new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unhex(iv) }, await aesKey(env), unhex(c))); }
async function kakaoAccess(env, row) {
  const r = await (await fetch('https://kauth.kakao.com/oauth/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'refresh_token', client_id: env.KAKAO_ID, refresh_token: await dec(env, row.rt), ...(env.KAKAO_SECRET ? { client_secret: env.KAKAO_SECRET } : {}) }) })).json();
  if (r.refresh_token) await env.DB.prepare('UPDATE kakao_alert SET rt = ? WHERE user_id = ?').bind(await enc(env, r.refresh_token), row.user_id).run();
  return r.access_token || null;
}
function itemUrl(id, src) {
  const [k, v] = [id.slice(0, 2), id.slice(2)];
  return SITE + (k === 'c:' ? `/c/${encodeURIComponent(v)}/?src=${src}` : k === 'a:' ? `/apply/?id=${encodeURIComponent(v)}&src=${src}` : `/me/?src=${src}`);
}
async function kakaoAlerts(env) {
  if (!env.KAKAO_ALERT_KEY) return;
  const k = Date.now() + 9 * 3600e3, day = d => new Date(k + d * 864e5).toISOString().slice(0, 10), today = day(0), d1 = day(1), d3 = day(3);
  const rows = (await env.DB.prepare('SELECT user_id, rt FROM kakao_alert WHERE last_sent IS NULL OR last_sent != ?').bind(today).all()).results || [];
  for (const row of rows) {
    try {
      const it = (await env.DB.prepare("SELECT item_id, title, end_date FROM user_items WHERE user_id = ? AND fav = 1 AND state = '' AND end_date IN (?, ?) ORDER BY end_date, title").bind(row.user_id, d1, d3).all()).results || [];
      if (!it.length) continue;
      const at = await kakaoAccess(env, row); if (!at) continue;
      const lines = it.slice(0, 5).map(x => `${x.end_date === d1 ? 'D-1' : 'D-3'} ${String(x.title || x.item_id).slice(0, 28)}`).join('\n');
      const text = (`⏰ 찜한 것 마감 알림 ${it.length}건\n` + lines + (it.length > 5 ? `\n외 ${it.length - 5}건` : '')).slice(0, 200);
      const u = it.length === 1 ? itemUrl(it[0].item_id, 'kakao_alert') : SITE + '/me/?src=kakao_alert';
      const r = await fetch('https://kapi.kakao.com/v2/api/talk/memo/default/send', { method: 'POST', headers: { Authorization: 'Bearer ' + at, 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ template_object: JSON.stringify({ object_type: 'text', text, link: { web_url: u, mobile_web_url: u }, button_title: '확인하기' }) }) });
      if (r.ok) await env.DB.prepare('UPDATE kakao_alert SET last_sent = ? WHERE user_id = ?').bind(today, row.user_id).run();
    } catch (e) { /* 한 사람 실패가 다른 사람 발송을 막지 않게 */ }
  }
}

// ---- 소셜 로그인: /api/oauth/<google|kakao>/start?back=<돌아갈 주소> → 제공자 → /api/oauth/<p>/callback → 사이트 #jt=<토큰>&jn=<닉> ----
const SITE = 'https://sungprofile.cloud';
const PROV = {
  google: { auth: 'https://accounts.google.com/o/oauth2/v2/auth', token: 'https://oauth2.googleapis.com/token', scope: 'openid email', id: 'GOOGLE_ID', secret: 'GOOGLE_SECRET' },
  kakao: { auth: 'https://kauth.kakao.com/oauth/authorize', token: 'https://kauth.kakao.com/oauth/token', scope: '', id: 'KAKAO_ID', secret: 'KAKAO_SECRET' },
};
async function oauth(req, env, url, prov, act) {
  const P = PROV[prov], cid = env[P.id], cb = url.origin + `/api/oauth/${prov}/callback`;
  if (!cid) return err(req, '아직 준비 중인 로그인이에요.', 503);
  if (act === 'start') {
    const back = (url.searchParams.get('back') || '/').replace(/^https?:\/\/[^/]+/, '').slice(0, 200) || '/';
    const state = hex(crypto.getRandomValues(new Uint8Array(12)));
    const an = prov === 'kakao' && /^[0-9a-f]{32}$/.test(url.searchParams.get('alert') || '') ? url.searchParams.get('alert') : '';
    const q = new URLSearchParams({ client_id: cid, redirect_uri: cb, response_type: 'code', state, ...(an ? { scope: 'talk_message' } : P.scope ? { scope: P.scope } : {}), ...(prov === 'google' ? { prompt: 'select_account' } : {}) });
    const h = new Headers({ Location: P.auth + '?' + q });
    h.append('Set-Cookie', `jo=${state}.${encodeURIComponent(back)}; Path=/api/oauth; Max-Age=600; HttpOnly; Secure; SameSite=Lax`);
    h.append('Set-Cookie', `ja=${an}; Path=/api/oauth; Max-Age=${an ? 600 : 0}; HttpOnly; Secure; SameSite=Lax`);
    return new Response(null, { status: 302, headers: h });
  }
  const ck = (req.headers.get('Cookie') || '').match(/(?:^|;\s*)jo=([0-9a-f]+)\.([^;]*)/), code = url.searchParams.get('code');
  const fail = m => Response.redirect(SITE + '/#jerr=' + encodeURIComponent(m), 302);
  if (!ck || ck[1] !== url.searchParams.get('state') || !code) return fail('로그인을 다시 시도해 주세요.');
  const back = decodeURIComponent(ck[2] || '/');
  const tk = await (await fetch(P.token, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: cb, client_id: cid, ...(env[P.secret] ? { client_secret: env[P.secret] } : {}) }) })).json();
  if (!tk.access_token) return fail('로그인 확인에 실패했어요.');
  let sub, email = '';
  if (prov === 'google') { const u = await (await fetch('https://openidconnect.googleapis.com/v1/userinfo', { headers: { Authorization: 'Bearer ' + tk.access_token } })).json(); sub = u.sub; email = u.email_verified ? String(u.email || '').toLowerCase() : ''; }
  else { const u = await (await fetch('https://kapi.kakao.com/v2/user/me', { headers: { Authorization: 'Bearer ' + tk.access_token } })).json(); sub = u.id && String(u.id); const ka = u.kakao_account || {}; email = ka.is_email_verified && ka.email ? ka.email.toLowerCase() : ''; }
  if (!sub) return fail('계정 정보를 받지 못했어요.');
  const ja = (req.headers.get('Cookie') || '').match(/(?:^|;\s*)ja=([0-9a-f]{32})/);
  if (prov === 'kakao' && ja) {
    const n = await env.DB.prepare('SELECT user_id FROM kakao_alert_nonce WHERE nonce = ? AND created > ?').bind(ja[1], now() - 900).first('user_id');
    await env.DB.prepare('DELETE FROM kakao_alert_nonce WHERE nonce = ? OR created < ?').bind(ja[1], now() - 900).run();
    const h = new Headers({ Location: SITE + '/me/#kalert=' + (n && tk.refresh_token && /talk_message/.test(tk.scope || '') ? 'on' : 'fail') });
    h.append('Set-Cookie', 'jo=; Path=/api/oauth; Max-Age=0'); h.append('Set-Cookie', 'ja=; Path=/api/oauth; Max-Age=0');
    if (n && tk.refresh_token && /talk_message/.test(tk.scope || '') && env.KAKAO_ALERT_KEY)
      await env.DB.prepare('INSERT OR REPLACE INTO kakao_alert (user_id, sub, rt, created, last_sent) VALUES (?, ?, ?, ?, NULL)').bind(n, sub, await enc(env, tk.refresh_token), now()).run();
    return new Response(null, { status: 302, headers: h });
  }
  let uid = await env.DB.prepare('SELECT user_id FROM oauth_links WHERE provider = ? AND sub = ?').bind(prov, sub).first('user_id');
  if (!uid && email) uid = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first('id');  // 같은 이메일로 이미 가입했으면 연결
  if (!uid) {
    const mail = email || `${prov}_${sub}@${prov}.login`, base = prov === 'kakao' ? 'kko' : (email.split('@')[0].replace(/[^0-9a-z]/g, '').slice(0, 3) || 'ggl');
    let nick = base + '***'; for (let i = 2; await count(env, 'SELECT COUNT(*) n FROM users WHERE nick = ?', nick); i++) nick = base + '***' + i;
    const r = await env.DB.prepare('INSERT INTO users (email, nick, pw, created) VALUES (?, ?, ?, ?)').bind(mail, nick, 'oauth$' + prov, now()).run();
    uid = r.meta.last_row_id;
  }
  await env.DB.prepare('INSERT OR IGNORE INTO oauth_links (provider, sub, user_id, created) VALUES (?, ?, ?, ?)').bind(prov, sub, uid, now()).run();
  const u = await env.DB.prepare('SELECT nick, banned FROM users WHERE id = ?').bind(uid).first();
  if (!u || u.banned) return fail('이용이 제한된 계정이에요.');
  const token = await newSession(env, uid);
  return new Response(null, { status: 302, headers: { Location: SITE + back.split('#')[0] + '#jt=' + token + '&jn=' + encodeURIComponent(u.nick), 'Set-Cookie': 'jo=; Path=/api/oauth; Max-Age=0' } });
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(req) });
    const url = new URL(req.url), p = url.pathname.replace(/\/+$/, '');
    const body = req.method === 'POST' ? await req.json().catch(() => ({})) : {};
    try {
      // ---- 계정 ----
      if (p === '/api/signup' && req.method === 'POST') {
        const email = clean(body.email, 120).toLowerCase(), pw = String(body.password || '');
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return err(req, '이메일 형식을 확인해 주세요.');
        const base = email.split('@')[0].replace(/[^0-9a-z]/g, '').slice(0, 3) || 'jup';
        let nick = base + '***';
        for (let i = 2; await count(env, 'SELECT COUNT(*) n FROM users WHERE nick = ?', nick); i++) nick = base + '***' + i;  // 화면 표시용(가린 이메일)
        if (pw.length < 8) return err(req, '비밀번호는 8자 이상이어야 해요.');
        if (await count(env, 'SELECT COUNT(*) n FROM users WHERE email = ?', email)) return err(req, '이미 가입된 이메일이에요.');
        const r = await env.DB.prepare('INSERT INTO users (email, nick, pw, created) VALUES (?, ?, ?, ?)').bind(email, nick, await hashPw(pw), now()).run();
        const ref = clean(body.ref, 16);
        if (ref) {
          const by = await env.DB.prepare('SELECT user_id FROM invite_codes WHERE code = ?').bind(ref).first('user_id');
          if (by) await env.DB.prepare('INSERT OR IGNORE INTO invited (user_id, by_user, contest_id, created) VALUES (?, ?, ?, ?)').bind(r.meta.last_row_id, by, clean(body.h, 40), now()).run();
        }
        return json(req, { token: await newSession(env, r.meta.last_row_id), nick });
      }
      const om = p.match(/^\/api\/oauth\/(google|kakao)\/(start|callback)$/);
      if (om && req.method === 'GET') return await oauth(req, env, url, om[1], om[2]);
      if (p === '/api/oauth/ready') return json(req, { google: !!env.GOOGLE_ID, kakao: !!env.KAKAO_ID });
      if (p === '/api/login' && req.method === 'POST') {
        const u = await env.DB.prepare('SELECT id, nick, pw, banned FROM users WHERE email = ?').bind(clean(body.email, 120).toLowerCase()).first();
        if (!u || u.pw.startsWith('oauth$') || !(await checkPw(String(body.password || ''), u.pw))) return err(req, u && u.pw.startsWith('oauth$') ? '구글·카카오로 가입한 계정이에요. 그 버튼으로 로그인해 주세요.' : '이메일 또는 비밀번호가 맞지 않아요.', 401);
        if (u.banned) return err(req, '이용이 제한된 계정이에요.', 403);
        return json(req, { token: await newSession(env, u.id), nick: u.nick });
      }
      if (p === '/api/logout' && req.method === 'POST') {
        const t = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/, '');
        if (t) await env.DB.prepare('DELETE FROM sessions WHERE token = ?').bind(t).run();
        return json(req, { ok: true });
      }
      if (p === '/api/ref' && req.method === 'POST') {  // 초대 링크 방문 집계
        const code = clean(body.ref, 16);
        if (!/^[0-9a-f]{8}$/.test(code) || !(await count(env, 'SELECT COUNT(*) n FROM invite_codes WHERE code = ?', code))) return json(req, { ok: false });
        const vh = hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode((req.headers.get('CF-Connecting-IP') || '') + '|' + (req.headers.get('User-Agent') || '')))).slice(0, 16);
        await env.DB.prepare('INSERT OR IGNORE INTO ref_visits (code, vh, contest_id, created) VALUES (?, ?, ?, ?)').bind(code, vh, clean(body.h, 40), now()).run();
        return json(req, { ok: true });
      }
      if (p === '/api/prefs' && req.method === 'POST') {  // 루리 꾸미기 저장
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const d = {}; for (const [k, v] of Object.entries(body.data || {}).slice(0, 40)) if (/^[a-z]{1,12}$/.test(k)) d[k] = clean(v, 80);
        await env.DB.prepare('INSERT OR REPLACE INTO user_prefs (user_id, data) VALUES (?, ?)').bind(u.id, JSON.stringify(d)).run();
        return json(req, { ok: true });
      }
      if (p === '/api/me') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        let code = await env.DB.prepare('SELECT code FROM invite_codes WHERE user_id = ?').bind(u.id).first('code');
        if (!code) { code = hex(crypto.getRandomValues(new Uint8Array(4))); await env.DB.prepare('INSERT OR IGNORE INTO invite_codes (code, user_id) VALUES (?, ?)').bind(code, u.id).run(); }
        const byC = (await env.DB.prepare("SELECT contest_id h, SUM(v) visits, SUM(j) joins FROM (SELECT contest_id, 1 v, 0 j FROM ref_visits WHERE code = ? UNION ALL SELECT contest_id, 0, 1 FROM invited WHERE by_user = ?) GROUP BY contest_id ORDER BY SUM(v) + SUM(j) * 3 DESC LIMIT 50").bind(code, u.id).all()).results;
        const prefs = await env.DB.prepare('SELECT data FROM user_prefs WHERE user_id = ?').bind(u.id).first('data');
        const em = await env.DB.prepare('SELECT email FROM users WHERE id = ?').bind(u.id).first('email') || '';
        return json(req, { nick: u.nick, email: /\.login$/.test(em) ? '' : em, code, invites: byC.reduce((a, x) => a + x.joins, 0), visits: byC.reduce((a, x) => a + x.visits, 0), by_contest: byC, prefs: prefs ? JSON.parse(prefs) : {}, admin: ADMINS.includes(u.id) });
      }
      if (p === '/api/withdraw' && req.method === 'POST') {  // 회원 탈퇴: 계정·세션 삭제, 글은 '탈퇴한 회원'으로 숨김
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        await env.DB.batch([env.DB.prepare('UPDATE posts SET hidden = 1 WHERE user_id = ?').bind(u.id), env.DB.prepare('UPDATE comments SET hidden = 1 WHERE user_id = ?').bind(u.id), env.DB.prepare('UPDATE page_comments SET hidden = 1 WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM page_likes WHERE user_id = ?').bind(u.id),
          env.DB.prepare('DELETE FROM sessions WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM invite_codes WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM user_prefs WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM oauth_links WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM user_items WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM kakao_alert WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM users WHERE id = ?').bind(u.id)]);
        return json(req, { ok: true });
      }
      // ---- 글 ----
      if (p === '/api/posts' && req.method === 'GET') {
        const c = clean(url.searchParams.get('contest'), 40), page = Math.max(0, +url.searchParams.get('page') || 0);
        const q = c ? env.DB.prepare('SELECT p.id, p.contest_id, p.contest_title, p.kind, p.title, p.body, p.rating, p.created, p.user_id, u.nick, (SELECT COUNT(*) FROM comments m WHERE m.post_id = p.id AND m.hidden = 0) cm FROM posts p LEFT JOIN users u ON u.id = p.user_id WHERE p.hidden = 0 AND p.contest_id = ? ORDER BY p.created DESC LIMIT 20 OFFSET ?').bind(c, page * 20)
                    : env.DB.prepare('SELECT p.id, p.contest_id, p.contest_title, p.kind, p.title, substr(p.body, 1, 140) body, p.rating, p.created, p.user_id, u.nick, (SELECT COUNT(*) FROM comments m WHERE m.post_id = p.id AND m.hidden = 0) cm FROM posts p LEFT JOIN users u ON u.id = p.user_id WHERE p.hidden = 0 ORDER BY p.created DESC LIMIT 20 OFFSET ?').bind(page * 20);
        return json(req, { posts: ((await q.all()).results || []).map(x => ({ ...x, adm: ADMINS.includes(x.user_id), user_id: undefined })) });
      }
      if (p === '/api/posts' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const kind = ['review', 'qna', 'tip', 'free', 'recipe', 'story'].includes(body.kind) ? body.kind : 'review';
        const title = clean(body.title, 80), text = clean(body.body, 3000), cid = clean(body.contest_id, 40) || 'free';
        if (title.length < 2 || text.length < 5) return err(req, '제목과 내용을 조금 더 써 주세요.');
        if (await count(env, 'SELECT COUNT(*) n FROM posts WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= LIMIT_POST) return err(req, '하루에 쓸 수 있는 글 수를 넘었어요.', 429);
        const rating = kind === 'review' && body.rating ? Math.min(5, Math.max(1, +body.rating | 0)) : null;
        const r = await env.DB.prepare('INSERT INTO posts (contest_id, contest_title, user_id, kind, title, body, rating, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
          .bind(cid, clean(body.contest_title, 120), u.id, kind, title, text, rating, now()).run();
        return json(req, { id: r.meta.last_row_id });
      }
      let m = p.match(/^\/api\/posts\/(\d+)$/);
      if (m && req.method === 'DELETE') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        await env.DB.prepare('UPDATE posts SET hidden = 1 WHERE id = ? AND user_id = ?').bind(+m[1], u.id).run();
        return json(req, { ok: true });
      }
      // ---- 댓글 ----
      if (p === '/api/comments' && req.method === 'GET') {
        const r = await env.DB.prepare('SELECT c.id, c.body, c.created, c.user_id, u.nick FROM comments c LEFT JOIN users u ON u.id = c.user_id WHERE c.post_id = ? AND c.hidden = 0 ORDER BY c.created LIMIT 200')
          .bind(+url.searchParams.get('post') || 0).all();
        return json(req, { comments: (r.results || []).map(x => ({ id: x.id, body: x.body, created: x.created, nick: x.nick, adm: ADMINS.includes(x.user_id) })) });
      }
      if (p === '/api/comments' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const text = clean(body.body, 1000), pid = +body.post_id || 0;
        if (text.length < 1 || !(await count(env, 'SELECT COUNT(*) n FROM posts WHERE id = ? AND hidden = 0', pid))) return err(req, '댓글을 쓸 수 없어요.');
        if (await count(env, 'SELECT COUNT(*) n FROM comments WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= LIMIT_COMMENT) return err(req, '하루에 쓸 수 있는 댓글 수를 넘었어요.', 429);
        const r = await env.DB.prepare('INSERT INTO comments (post_id, user_id, body, created) VALUES (?, ?, ?, ?)').bind(pid, u.id, text, now()).run();
        return json(req, { id: r.meta.last_row_id });
      }
      m = p.match(/^\/api\/comments\/(\d+)$/);
      if (m && req.method === 'DELETE') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        await env.DB.prepare('UPDATE comments SET hidden = 1 WHERE id = ? AND user_id = ?').bind(+m[1], u.id).run();
        return json(req, { ok: true });
      }
      let im = p.match(/^\/api\/img\/(\d+)$/);
      if (im && req.method === 'GET') {
        const r = await env.DB.prepare('SELECT i.*, t.leader_id FROM team_images i JOIN teams t ON t.id = i.team_id WHERE i.id = ? AND i.hidden = 0').bind(+im[1]).first();
        if (!r) return new Response('not found', { status: 404, headers: cors(req) });
        if (r.kind !== 'cover') {
          const tk = url.searchParams.get('t') || '';
          const u = tk ? await env.DB.prepare('SELECT s.user_id FROM sessions s WHERE s.token = ? AND s.expires > ?').bind(tk, now()).first('user_id') : null;
          const ok = u && (u === r.leader_id || await count(env, "SELECT COUNT(*) n FROM team_members WHERE team_id = ? AND user_id = ? AND state = 'accepted'", r.team_id, u));
          if (!ok) return new Response('forbidden', { status: 403, headers: cors(req) });
        }
        const bin = Uint8Array.from(atob(r.data), c => c.charCodeAt(0));
        return new Response(bin, { headers: { 'Content-Type': r.mime, 'Cache-Control': r.kind === 'cover' ? 'public, max-age=86400' : 'private, max-age=3600', ...cors(req) } });
      }
      // ---- 내 공간: 찜·응모 기록 (공모전·청약·지원금·경품 공통) ----
      if (p === '/api/items') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        if (req.method === 'GET') return json(req, { items: (await env.DB.prepare('SELECT item_id id, title, end_date end, fav, state, updated FROM user_items WHERE user_id = ? AND (fav = 1 OR length(state) > 0) ORDER BY end_date').bind(u.id).all()).results });
        if (req.method === 'POST') {
          const list = Array.isArray(body.items) ? body.items.slice(0, 200) : [body];
          for (const it of list) {
            const id = clean(it.id, 60); if (!/^[cae]:[\w.-]+$/.test(id)) continue;
            const cur = await env.DB.prepare('SELECT fav, state, title, end_date FROM user_items WHERE user_id = ? AND item_id = ?').bind(u.id, id).first() || { fav: 0, state: '', title: '', end_date: '' };
            const fav = it.fav === undefined ? cur.fav : it.fav ? 1 : 0, state = it.state === undefined ? cur.state : (['', 'applied', 'won', 'lost'].includes(it.state) ? it.state : cur.state);
            await env.DB.prepare('INSERT OR REPLACE INTO user_items (user_id, item_id, title, end_date, fav, state, updated) VALUES (?, ?, ?, ?, ?, ?, ?)')
              .bind(u.id, id, clean(it.title, 120) || cur.title, /^\d{4}-\d{2}-\d{2}$/.test(it.end || '') ? it.end : cur.end_date, fav, state, now()).run();
          }
          return json(req, { ok: true });
        }
      }
      // ---- 준비실: 공모전별 준비 보드 (2026-10-18 사용자: 공모전 준비할 사람들이 편하게 준비할 공간) ----
      if (p === '/api/prep' && req.method === 'GET') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const rows = (await env.DB.prepare('SELECT item_id id, data, updated FROM prep WHERE user_id = ? ORDER BY updated DESC LIMIT 100').bind(u.id).all()).results;
        return json(req, { prep: rows.map(r => ({ id: r.id, updated: r.updated, ...JSON.parse(r.data) })) });
      }
      if (p === '/api/prep' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        for (const it of (Array.isArray(body.items) ? body.items : [body]).slice(0, 50)) {
          const id = clean(it.id, 60); if (!/^c:[\w.-]+$/.test(id)) continue;
          if (it.del) { await env.DB.prepare('DELETE FROM prep WHERE user_id = ? AND item_id = ?').bind(u.id, id).run(); continue; }
          const d = it.data || {}, data = JSON.stringify({ title: clean(d.title, 120), end: /^\d{4}-\d{2}-\d{2}$/.test(d.end || '') ? d.end : '', g: clean(d.g, 12), url: clean(d.url, 300),
            steps: (d.steps || []).slice(0, 20).map(x => !!x), checks: (d.checks || []).slice(0, 30).map(x => !!x), memo: clean(d.memo, 3000), done: !!d.done, created: +d.created || now() });
          if (await count(env, 'SELECT COUNT(*) n FROM prep WHERE user_id = ?', u.id) >= 100) return err(req, '준비 보드는 100개까지예요.', 429);
          await env.DB.prepare('INSERT OR REPLACE INTO prep (user_id, item_id, data, updated) VALUES (?, ?, ?, ?)').bind(u.id, id, data, +it.updated || now()).run();
        }
        return json(req, { ok: true });
      }
      // ---- 냉장고 사진 → 재료 자동 체크 (Cloudflare Workers AI 공개 모델, 2026-10-18 사용자: 프론티어 AI 말고 모델로) ----
      // 웹푸시 공모전 알림 구독 (2026-10-18 사용자: 공모전 알림 + 웹푸시). 발송은 PC의 _gongmo/push.py 가 한다.
      if (p === '/api/push/sub' && req.method === 'POST') {
        const sb = body.sub || {}, ep = String(sb.endpoint || ''), k = sb.keys || {};
        if (!/^https:\/\/[a-z0-9.-]+\.(googleapis\.com|mozilla\.com|windows\.com|apple\.com|mozaws\.net)\//.test(ep) || ep.length > 600) return err(req, '이 브라우저는 알림을 지원하지 않아요.');
        const ok = x => typeof x === 'string' && /^[A-Za-z0-9_-]{10,200}$/.test(x);
        if (!ok(k.p256dh) || !ok(k.auth)) return err(req, '알림 등록에 실패했어요.');
        const cats = (Array.isArray(body.cats) ? body.cats : []).filter(c => /^[a-z]{2,12}$/.test(c)).slice(0, 12).join(',');
        const u = await me(req, env), n = await count(env, 'SELECT COUNT(*) n FROM push_subs');
        if (n > 20000) return err(req, '지금은 알림 등록이 많아요. 잠시 뒤에 다시 해 주세요.', 429);
        await env.DB.prepare('INSERT INTO push_subs (endpoint, p256dh, auth, cats, newc, dl, uid, created, sent, fails) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0) ON CONFLICT(endpoint) DO UPDATE SET p256dh = excluded.p256dh, auth = excluded.auth, cats = excluded.cats, newc = excluded.newc, dl = excluded.dl, uid = COALESCE(excluded.uid, push_subs.uid), fails = 0')
          .bind(ep, k.p256dh, k.auth, cats, body.newc === 0 ? 0 : 1, body.dl === 0 ? 0 : 1, u ? u.id : null, now()).run();
        return json(req, { ok: true });
      }
      if (p === '/api/push/unsub' && req.method === 'POST') {
        await env.DB.prepare('DELETE FROM push_subs WHERE endpoint = ?').bind(String(body.endpoint || '').slice(0, 600)).run();
        return json(req, { ok: true });
      }
      if (p === '/api/fridge-scan' && req.method === 'POST') {
        const m = /^data:image\/(?:jpeg|png|webp);base64,([A-Za-z0-9+/=]+)$/.exec(body.image || '');
        if (!m || m[1].length > 1400000) return err(req, '사진을 다시 찍어 주세요.');
        const ip = req.headers.get('CF-Connecting-IP') || '', d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), u = await me(req, env);
        const who = u ? 'u' + u.id : hex(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip + '|fridge')))).slice(0, 16);
        const cap = u ? 15 : 5, mine = await count(env, 'SELECT COUNT(*) n FROM fridge_log WHERE day = ? AND who = ?', d, who);
        if (mine >= cap) return err(req, u ? '사진 인식은 하루 15번까지예요. 재료는 직접 눌러서 골라 주세요!' : '사진 인식은 하루 5번까지예요. 가입하면 15번! 재료는 직접 눌러도 돼요.', 429);
        if (await count(env, 'SELECT COUNT(*) n FROM fridge_log WHERE day = ?', d) >= 400) return err(req, '오늘 사진 인식이 다 찼어요. 재료를 직접 눌러 주세요!', 429);
        const ING = { '양파': 'onion', '대파': 'green onion/leek', '감자': 'potato', '당근': 'carrot', '애호박': 'zucchini', '양배추': 'cabbage', '콩나물': 'soybean sprouts', '숙주': 'mung bean sprouts', '시금치': 'spinach', '버섯': 'mushroom',
          '무': 'white radish', '고추': 'chili pepper', '깻잎': 'perilla leaves', '오이': 'cucumber', '토마토': 'tomato', '상추': 'lettuce', '부추': 'chives', '브로콜리': 'broccoli', '파프리카': 'bell pepper', '고구마': 'sweet potato', '가지': 'eggplant',
          '돼지고기': 'pork', '소고기': 'beef', '닭고기': 'chicken meat', '베이컨': 'bacon', '햄': 'ham', '스팸': 'Spam can', '소시지': 'sausage', '참치캔': 'canned tuna', '어묵': 'fish cake', '맛살': 'crab stick', '오징어': 'squid', '새우': 'shrimp', '고등어': 'mackerel', '멸치': 'dried anchovy',
          '달걀': 'eggs', '두부': 'tofu', '우유': 'milk', '치즈': 'cheese', '버터': 'butter', '김치': 'kimchi', '밥': 'cooked rice', '라면': 'instant ramen', '국수': 'noodles', '파스타면': 'pasta', '떡': 'rice cake', '만두': 'dumplings', '식빵': 'sliced bread',
          '당면': 'glass noodles', '김': 'seaweed (gim)', '미역': 'seaweed (miyeok)', '단무지': 'yellow pickled radish', '고추장': 'gochujang (red pepper paste)', '된장': 'doenjang (soybean paste)', '카레가루': 'curry powder', '케첩': 'ketchup', '마요네즈': 'mayonnaise' };
        const prompt = 'Look at this photo of a fridge or food ingredients. From the list below, name ONLY the items you can clearly see. Answer with the English names exactly as written, separated by commas, nothing else. If none, answer NONE.\nList: ' + Object.values(ING).join(', ');
        const bin = Uint8Array.from(atob(m[1]), c => c.charCodeAt(0));
        const MODEL = '@cf/meta/llama-3.2-11b-vision-instruct';
        const run = () => env.AI.run(MODEL, { prompt, image: [...bin], max_tokens: 200, temperature: 0.1 });
        let out;
        let why = '';
        try { out = await run(); } catch (e) {
          why = String(e && e.message || e).slice(0, 200);
          if (/agree/i.test(String(e && e.message))) { await env.AI.run(MODEL, { prompt: 'agree' }).catch(() => {}); out = await run().catch(e2 => { why = String(e2 && e2.message || e2).slice(0, 200); return null; }); }
          if (!out) { await env.DB.prepare('INSERT INTO fridge_log (day, ts, who, ok) VALUES (?, ?, ?, 0)').bind(d, now(), who).run(); return json(req, { error: '사진을 잘 못 봤어요. 재료를 직접 눌러 주세요.', why }, 502); }
        }
        const txt = String(out.response || out.result || '').toLowerCase();
        const found = Object.entries(ING).filter(([k, en]) => en.toLowerCase().split(/[\/()]/).map(x => x.trim()).filter(x => x.length > 2).some(x => txt.includes(x))).map(([k]) => k);
        await env.DB.prepare('INSERT INTO fridge_log (day, ts, who, ok, tout) VALUES (?, ?, ?, 1, ?)').bind(d, now(), who, found.length).run();
        return json(req, { found, left: cap - mine - 1 });
      }
      // ---- 레시피 추천 묻기(2026-10-19): 사이트 레시피 1,353개에서 후보를 추려 Workers AI 가 한국어로 골라 준다 ----
      if (p === '/api/fridge-ask' && req.method === 'POST') {
        const q = clean(body.q, 160);
        const have = Array.isArray(body.have) ? body.have.slice(0, 40).map(x => clean(x, 12)).filter(Boolean) : [];
        if (!q && !have.length) return err(req, '재료를 고르거나 궁금한 걸 적어 주세요.');
        const ip = req.headers.get('CF-Connecting-IP') || '', d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), u = await me(req, env);
        const who = 'q:' + (u ? 'u' + u.id : hex(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip + '|ask')))).slice(0, 16));
        const cap = u ? 30 : 8, mine = await count(env, 'SELECT COUNT(*) n FROM fridge_log WHERE day = ? AND who = ?', d, who);
        if (mine >= cap) return err(req, u ? '물어보기는 하루 30번까지예요. 재료를 골라 추천을 받아 보세요!' : '물어보기는 하루 8번까지예요. 가입하면 30번! 재료를 골라도 추천이 나와요.', 429);

        let all = [], why = '';
        try { all = await recipeIndex(env); } catch (e) { why = String(e && e.message || e).slice(0, 120); }
        if (!all.length) return json(req, { answer: '레시피를 불러오지 못했어요. 잠시 뒤 다시 해 주세요.', picks: [], why: why || 'empty' }, 502);
        const H = new Set(have), toks = q.replace(/[^0-9A-Za-z가-힣]+/g, ' ').split(' ').filter(t => t.length >= 2);
        const scored = [];
        for (const r of all) {
          const need = r.need || [], opt = r.opt || [];
          const hitN = need.filter(i => H.has(i)).length, hitO = opt.filter(i => H.has(i)).length;
          let sc = need.length ? (hitN / need.length) * 6 : 0;
          sc += Math.min(hitO, 4) * 0.6;
          const ready = need.length > 0 && hitN === need.length;
          if (ready) sc += 3;
          const hay = r.n + ' ' + (r.t || []).join(' ') + ' ' + need.join(' ') + ' ' + opt.join(' ');
          for (const t of toks) { if (r.n.includes(t)) sc += 3; else if (hay.includes(t)) sc += 2; }
          if (sc > 0) scored.push({ r, sc, ready });
        }
        scored.sort((a, b) => b.sc - a.sc);
        const cands = scored.slice(0, 12);
        if (!cands.length) return json(req, { answer: '그 재료로 만들 수 있는 메뉴를 아직 못 찾았어요. 재료를 몇 개 더 골라 주시면 다시 찾아볼게요!', picks: [], n: all.length });

        const slug = n => n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-+|-+$/g, '');
        const line = (x, i) => `${i + 1}) ${x.r.n} — ${x.r.m}분, ${x.r.lv}, 꼭 필요한 재료 ${(x.r.need || []).join('·')}` +
          ((x.r.opt || []).length ? `, 있으면 좋은 재료 ${x.r.opt.slice(0, 4).join('·')}` : '') + (x.ready ? ' [지금 바로 가능]' : '');
        const sys = '너는 한국 가정식 레시피를 골라 주는 「루리」야. 아래 후보 목록에 있는 메뉴만 2~3개 골라서 추천해. 목록에 없는 메뉴 이름은 절대 쓰지 마. ' +
          '존댓말로 3~4문장만 쓰고, 고른 이유를 가진 재료와 조리 시간으로 짧게 설명해. 메뉴 이름은 목록에 적힌 그대로 써. 재료를 더 사라는 말은 하지 마.';
        const user = `가진 재료: ${have.join(', ') || '(고른 재료 없음)'}\n물어본 것: ${q || '(없음)'}\n후보 목록:\n${cands.map(line).join('\n')}`;
        let answer = '';
        try {
          const out = await env.AI.run('@cf/meta/llama-3.3-70b-instruct-fp8-fast',
            { messages: [{ role: 'system', content: sys }, { role: 'user', content: user }], max_tokens: 400, temperature: 0.3 });
          answer = clean(out.response || out.result || '', 900);
        } catch (e) { answer = ''; }
        // AI 가 안 되면 규칙으로 답한다
        const named = cands.filter(x => answer.includes(x.r.n));
        const picks = (named.length ? named : cands.slice(0, 3)).slice(0, 3)
          .map(x => ({ n: x.r.n, e: x.r.e, m: x.r.m, lv: x.r.lv, need: x.r.need, ready: x.ready, u: '/fridge/r/' + slug(x.r.n) + '/' }));
        if (!answer) {
          const top = picks[0];
          answer = top ? `${top.n}은(는) ${top.need.join('·')}만 있으면 ${top.m}분이면 돼요. 아래에서 만드는 법을 볼 수 있어요!` : '';
        }
        await env.DB.prepare('INSERT INTO fridge_log (day, ts, who, ok, tin, tout) VALUES (?, ?, ?, 1, ?, ?)').bind(d, now(), who, have.length, picks.length).run();
        return json(req, { answer, picks, left: cap - mine - 1 });
      }
      // ---- 동료 찾기: 같은 공모전 준비하는 사람끼리 모이기 (2026-10-18 사용자: 같은 사람이 모이는 구조 + 원정대 활성화) ----
      if (p === '/api/crew' && req.method === 'GET') {
        const c = clean(url.searchParams.get('c'), 40), u = await me(req, env);
        if (!c) {  // 전체: 최근 동료 찾는 사람
          const rows = (await env.DB.prepare('SELECT s.user_id uid, s.contest_id, s.contest_title, s.roles, s.intro, s.updated, u.nick FROM seekers s JOIN users u ON u.id = s.user_id WHERE u.banned = 0 ORDER BY s.updated DESC LIMIT 40').all()).results;
          return json(req, { seekers: rows.map(r => ({ ...r, me: !!(u && u.id === r.uid) })) });
        }
        const prep = await count(env, "SELECT COUNT(*) n FROM (SELECT user_id FROM prep WHERE item_id = ? UNION SELECT user_id FROM user_items WHERE item_id = ? AND (fav = 1 OR state != ''))", 'c:' + c, 'c:' + c);
        const seekers = (await env.DB.prepare('SELECT s.user_id uid, s.roles, s.intro, s.updated, u.nick FROM seekers s JOIN users u ON u.id = s.user_id WHERE s.contest_id = ? AND u.banned = 0 ORDER BY s.updated DESC LIMIT 50').bind(c).all()).results;
        const teams = (await env.DB.prepare("SELECT t.id, t.name, t.roles, t.size, t.status, t.leader_id, (SELECT COUNT(*) FROM team_members m WHERE m.team_id = t.id AND m.state = 'accepted') cnt FROM teams t WHERE t.contest_id = ? AND t.hidden = 0 ORDER BY t.status = 'closed', t.created DESC LIMIT 20").bind(c).all()).results;
        let invites = [], myTeams = [];
        if (u) {
          invites = (await env.DB.prepare("SELECT i.team_id, t.name, u.nick leader FROM crew_invites i JOIN teams t ON t.id = i.team_id JOIN users u ON u.id = t.leader_id WHERE i.user_id = ? AND t.contest_id = ? AND t.hidden = 0 AND NOT EXISTS (SELECT 1 FROM team_members m WHERE m.team_id = i.team_id AND m.user_id = i.user_id)").bind(u.id, c).all()).results;
          myTeams = teams.filter(x => x.leader_id === u.id && x.status !== 'closed').map(x => x.id);
        }
        const called = u ? (await env.DB.prepare('SELECT user_id FROM crew_invites WHERE team_id IN (SELECT id FROM teams WHERE leader_id = ? AND contest_id = ?)').bind(u.id, c).all()).results.map(r => r.user_id) : [];
        return json(req, { preparing: Math.max(prep, seekers.length), seekers: seekers.map(s => ({ ...s, me: !!(u && u.id === s.uid), called: called.includes(s.uid) })),
          teams: teams.map(({ leader_id, ...x }) => ({ ...x, mine: !!(u && u.id === leader_id) })), invites, myTeams, joined: !!(u && seekers.some(s => s.uid === u.id)) });
      }
      if (p === '/api/crew' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const c = clean(body.c, 40); if (!/^[\w.-]+$/.test(c)) return err(req, '공모전을 확인해 주세요.');
        if (body.del) { await env.DB.prepare('DELETE FROM seekers WHERE user_id = ? AND contest_id = ?').bind(u.id, c).run(); return json(req, { ok: true }); }
        const roles = clean(body.roles, 120).split(/[,，、]+/).map(r => r.trim().slice(0, 20)).filter(Boolean).slice(0, 6).join(','), intro = clean(body.intro, 300);
        if (!roles && intro.length < 2) return err(req, '잘하는 것이나 한 줄 소개를 적어 주세요.');
        if (await count(env, 'SELECT COUNT(*) n FROM seekers WHERE user_id = ?', u.id) >= 30) return err(req, '동료 찾기는 30개 공모전까지예요.', 429);
        await env.DB.prepare('INSERT OR REPLACE INTO seekers (user_id, contest_id, contest_title, roles, intro, updated) VALUES (?, ?, ?, ?, ?, ?)').bind(u.id, c, clean(body.title, 120), roles, intro, now()).run();
        return json(req, { ok: true });
      }
      if (p === '/api/crew/invite' && req.method === 'POST') {  // 원정대장이 동료 찾는 사람을 부르기
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const tm = await env.DB.prepare("SELECT id, contest_id FROM teams WHERE id = ? AND leader_id = ? AND hidden = 0 AND status != 'closed'").bind(+body.team, u.id).first();
        if (!tm) return err(req, '내가 대장인 모집 중 원정대만 부를 수 있어요.', 403);
        if (!await env.DB.prepare('SELECT 1 FROM seekers WHERE user_id = ? AND contest_id = ?').bind(+body.user, tm.contest_id).first()) return err(req, '이 공모전 동료를 찾는 사람이 아니에요.');
        if (await count(env, 'SELECT COUNT(*) n FROM crew_invites WHERE team_id IN (SELECT id FROM teams WHERE leader_id = ?) AND created > ?', u.id, now() - DAY) >= 30) return err(req, '오늘은 더 부를 수 없어요.', 429);
        await env.DB.prepare('INSERT OR IGNORE INTO crew_invites (team_id, user_id, created) VALUES (?, ?, ?)').bind(tm.id, +body.user, now()).run();
        return json(req, { ok: true });
      }
      if (p === '/api/crew/mine') {  // 나를 부른 원정대 (메뉴 알림용)
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        return json(req, { invites: (await env.DB.prepare("SELECT i.team_id, t.name, t.contest_id, t.contest_title FROM crew_invites i JOIN teams t ON t.id = i.team_id WHERE i.user_id = ? AND t.hidden = 0 AND t.status != 'closed' AND NOT EXISTS (SELECT 1 FROM team_members m WHERE m.team_id = i.team_id AND m.user_id = i.user_id) ORDER BY i.created DESC LIMIT 20").bind(u.id).all()).results });
      }
      // ---- 꿀팁 (posts kind=tip, contest_id = 'g:<장르>' 또는 공모전 id) ----
      if (p === '/api/tips' && req.method === 'GET') {
        const g = clean(url.searchParams.get('g'), 12), u = await me(req, env);
        const sel = `SELECT p.id, p.contest_id, p.contest_title, p.body, p.created, u.nick, (SELECT COUNT(*) FROM post_likes l WHERE l.post_id = p.id) likes${u ? ', (SELECT 1 FROM post_likes l WHERE l.post_id = p.id AND l.user_id = ' + u.id + ') liked' : ''} FROM posts p LEFT JOIN users u ON u.id = p.user_id WHERE p.kind = 'tip' AND p.hidden = 0`;
        const q = g ? env.DB.prepare(sel + ' AND p.contest_id = ? ORDER BY likes DESC, p.created DESC LIMIT 50').bind('g:' + g) : env.DB.prepare(sel + ' ORDER BY p.created DESC LIMIT 50');
        return json(req, { tips: (await q.all()).results });
      }
      if (p === '/api/tips' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const text = clean(body.body, 1000), g = clean(body.g, 12);
        if (text.length < 10) return err(req, '꿀팁을 조금 더 자세히 써 주세요. (10자 이상)');
        if (await count(env, 'SELECT COUNT(*) n FROM posts WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= LIMIT_POST) return err(req, '하루에 쓸 수 있는 글 수를 넘었어요.', 429);
        const r = await env.DB.prepare("INSERT INTO posts (contest_id, contest_title, user_id, kind, title, body, created) VALUES (?, ?, ?, 'tip', ?, ?, ?)")
          .bind('g:' + (g || 'all'), clean(body.contest_title, 120), u.id, text.slice(0, 40), text, now()).run();
        return json(req, { id: r.meta.last_row_id });
      }
      let lk = p.match(/^\/api\/tips\/(\d+)\/like$/);
      if (lk && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const ins = await env.DB.prepare('INSERT OR IGNORE INTO post_likes (user_id, post_id, created) VALUES (?, ?, ?)').bind(u.id, +lk[1], now()).run();
        if (!ins.meta.changes) await env.DB.prepare('DELETE FROM post_likes WHERE user_id = ? AND post_id = ?').bind(u.id, +lk[1]).run();
        return json(req, { liked: !!ins.meta.changes, likes: await count(env, 'SELECT COUNT(*) n FROM post_likes WHERE post_id = ?', +lk[1]) });
      }
      // ---- 위젯 노출 (2026-10-18): 다른 블로그에 붙은 iframe 이 열릴 때 종류·붙은 곳만 기록, 방문 통계와 따로 ----
      if (p === '/api/wv' && req.method === 'POST') {
        const ua = req.headers.get('User-Agent') || '';
        if (/bot|crawl|spider|slurp|headless|lighthouse|preview|python|curl|wget/i.test(ua)) return json(req, { ok: 1 });
        let host = ''; try { host = body.r ? new URL(body.r).hostname.replace(/^www\./, '') : ''; } catch {}
        const k = /^(contest|apply|hot|dday)$/.test(body.k || '') ? body.k : 'etc', d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
        await env.DB.prepare('INSERT INTO widget_views (day, ts, kind, host) VALUES (?, ?, ?, ?)').bind(d, now(), k, clean(host, 60)).run();
        return json(req, { ok: 1 });
      }
      // ---- 방문 기록 (자체 집계, 관리자 화면용) ----
      if (p === '/api/hit' && req.method === 'POST') {
        const ua = req.headers.get('User-Agent') || '';
        if (/bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|daum|yeti|google|inspection|python|curl|wget|go-http|axios|node-fetch|scrapy/i.test(ua)) return json(req, { ok: 1 });
        const ip = req.headers.get('CF-Connecting-IP') || '', d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
        const vid = hex(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip + '|' + ua + '|' + d)))).slice(0, 16);
        let ref = ''; try { ref = body.r ? new URL(body.r).hostname.replace(/^www\./, '') : ''; } catch {}
        if (/sungprofile\.cloud$/.test(ref)) ref = '';
        if (/^[a-z0-9_-]{1,16}$/i.test(body.s || '')) ref = 'src:' + body.s.toLowerCase();  // 홍보 링크 꼬리 ?src=th 등(앱 내 브라우저는 referrer 가 비어서)
        const u = await me(req, env), cf = req.cf || {};
        const pg = npage(body.p);
        const q = [env.DB.prepare('INSERT INTO hits (day, ts, vid, uid, path, ref, country, city, mobile) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)')
          .bind(d, now(), vid, u ? u.id : 0, clean(body.p, 120), clean(ref, 60), clean(cf.country || '', 4), clean(cf.city || '', 40), /Mobi|Android|iPhone/i.test(ua) ? 1 : 0)];
        if (pg) q.push(env.DB.prepare("INSERT INTO page_stats (page, title, views, updated) VALUES (?, ?, 1, ?) ON CONFLICT(page) DO UPDATE SET views = views + 1, updated = excluded.updated, title = CASE WHEN page_stats.title = '' THEN excluded.title ELSE page_stats.title END")
          .bind(pg, clean(body.t, 90), now()));
        await env.DB.batch(q);
        return json(req, { ok: 1 });
      }
      if (p === '/api/admin/visits') {
        const u = await me(req, env); if (!u || !ADMINS.includes(u.id)) return err(req, '권한이 없어요.', 403);
        const d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), mine = url.searchParams.get('mine') === '1';
        const W = (mine ? '' : ` AND uid NOT IN (${ADMINS.join(',')})`) + ` AND vid NOT IN (SELECT vid FROM hits WHERE country NOT IN ('KR', '') GROUP BY vid HAVING MAX(ref) = '')`  /* 해외에서 링크 없이만 온 방문(자동 점검 프로그램)만 제외, 해외 커뮤니티 유입은 셈 */, wk = new Date(Date.now() + 9 * 3600e3 - 6 * 86400e3).toISOString().slice(0, 10);
        const all = async (q, ...a) => (await env.DB.prepare(q).bind(...a).all()).results;
        const first = async (q, ...a) => await env.DB.prepare(q).bind(...a).first();
        return json(req, {
          today: await first(`SELECT COUNT(DISTINCT vid) v, COUNT(*) pv FROM hits WHERE day = ?${W}`, d),
          live: await first(`SELECT COUNT(DISTINCT vid) v FROM hits WHERE ts > ?${W}`, now() - 1800),
          total: await first(`SELECT COUNT(DISTINCT vid || day) v, COUNT(*) pv, MIN(day) since FROM hits WHERE 1=1${W}`),
          byDay: await all(`SELECT day d, COUNT(DISTINCT vid) v, COUNT(*) pv FROM hits WHERE day >= date(?, '-13 days')${W} GROUP BY day ORDER BY day`, d),
          pages: await all(`SELECT path, COUNT(*) pv, COUNT(DISTINCT vid) v FROM hits WHERE day >= ?${W} GROUP BY path ORDER BY v DESC, pv DESC LIMIT 15`, wk),
          // 2026-10-18 사용자: "유입 경로 좀 정리해, 알아들을 수 있게" — 방문자마다 그날 처음 들어온 곳(첫 조회) 기준으로 채널 이름 묶기
          refs: await all(`SELECT CASE WHEN h.ref LIKE 'src:u_share%' THEN '📤 공유 버튼으로 받은 링크'  WHEN h.ref = 'src:nb_notice' THEN '📌 블로그 공지글'  WHEN substr(h.ref, 1, 6) = 'src:w_' THEN '🧩 위젯 클릭'  WHEN h.ref = 'src:kin' OR h.ref LIKE '%kin.naver.com' THEN '💬 네이버 지식인'  WHEN h.ref IN ('src:blog', 'src:u_naver_blog') OR h.ref LIKE '%blog.naver.com' OR h.ref LIKE '%tistory.com' THEN '📝 블로그'  WHEN h.ref IN ('src:cafe', 'src:u_naver_cafe') OR h.ref LIKE '%cafe.naver.com' OR h.ref LIKE '%cafe.daum.net' THEN '☕ 카페'  WHEN h.ref LIKE '%search.naver.com' OR h.ref IN ('naver.com', 'm.naver.com') THEN '🔍 네이버 검색'  WHEN h.ref LIKE '%google.%' AND h.ref NOT LIKE 'accounts.google%' THEN '🔍 구글 검색'  WHEN h.ref LIKE '%daum.net' OR h.ref LIKE '%bing.com' OR h.ref LIKE '%zum.com' THEN '🔍 다음·빙 검색'  WHEN h.ref IN ('src:yt', 'src:shorts', 'src:u_youtube') OR h.ref LIKE '%youtube.com' OR h.ref = 'youtu.be' THEN '▶️ 유튜브'  WHEN h.ref IN ('src:ig', 'src:reel', 'src:u_instagram') OR h.ref LIKE '%instagram.com' THEN '📸 인스타그램'  WHEN h.ref IN ('src:th', 'src:u_threads') OR h.ref LIKE '%threads.%' THEN '🧵 스레드'  WHEN h.ref = 'src:dc' OR h.ref LIKE '%dcinside.com' THEN '🗨️ 디시인사이드'  WHEN h.ref IN ('src:dev', 'src:gn', 'src:dq', 'src:velog') OR h.ref LIKE '%okky.kr' OR h.ref LIKE '%hada.io' OR h.ref LIKE '%velog.io' OR h.ref LIKE '%disquiet.io' THEN '💻 개발자 커뮤니티' WHEN h.ref IN ('src:medium', 'src:devto', 'src:reddit', 'src:hn', 'src:hashnode') OR h.ref LIKE '%medium.com' OR h.ref LIKE '%dev.to' OR h.ref LIKE '%reddit.com' OR h.ref LIKE '%ycombinator.com' OR h.ref LIKE '%hashnode.%' THEN '🌍 해외 개발 커뮤니티(레딧·HN·Medium·dev.to)'  WHEN h.ref LIKE 'accounts.google%' OR h.ref LIKE '%kakao.com' THEN '🔐 로그인하고 돌아옴'  WHEN h.ref = '' THEN '🔗 직접 접속(주소 입력·즐겨찾기·앱 안 링크)'  WHEN h.ref LIKE 'src:%' THEN '🏷️ 기타 홍보 링크(' || substr(h.ref, 5) || ')'  ELSE '🌐 기타 사이트(' || h.ref || ')' END r, COUNT(*) v FROM hits h JOIN (SELECT vid, day, MIN(ts) t FROM hits WHERE day >= ?${W} GROUP BY vid, day) f ON h.vid = f.vid AND h.day = f.day AND h.ts = f.t GROUP BY r ORDER BY v DESC LIMIT 20`, wk),
          refsToday: await all(`SELECT CASE WHEN h.ref LIKE 'src:u_share%' THEN '📤 공유 버튼으로 받은 링크'  WHEN h.ref = 'src:nb_notice' THEN '📌 블로그 공지글'  WHEN substr(h.ref, 1, 6) = 'src:w_' THEN '🧩 위젯 클릭'  WHEN h.ref = 'src:kin' OR h.ref LIKE '%kin.naver.com' THEN '💬 네이버 지식인'  WHEN h.ref IN ('src:blog', 'src:u_naver_blog') OR h.ref LIKE '%blog.naver.com' OR h.ref LIKE '%tistory.com' THEN '📝 블로그'  WHEN h.ref IN ('src:cafe', 'src:u_naver_cafe') OR h.ref LIKE '%cafe.naver.com' OR h.ref LIKE '%cafe.daum.net' THEN '☕ 카페'  WHEN h.ref LIKE '%search.naver.com' OR h.ref IN ('naver.com', 'm.naver.com') THEN '🔍 네이버 검색'  WHEN h.ref LIKE '%google.%' AND h.ref NOT LIKE 'accounts.google%' THEN '🔍 구글 검색'  WHEN h.ref LIKE '%daum.net' OR h.ref LIKE '%bing.com' OR h.ref LIKE '%zum.com' THEN '🔍 다음·빙 검색'  WHEN h.ref IN ('src:yt', 'src:shorts', 'src:u_youtube') OR h.ref LIKE '%youtube.com' OR h.ref = 'youtu.be' THEN '▶️ 유튜브'  WHEN h.ref IN ('src:ig', 'src:reel', 'src:u_instagram') OR h.ref LIKE '%instagram.com' THEN '📸 인스타그램'  WHEN h.ref IN ('src:th', 'src:u_threads') OR h.ref LIKE '%threads.%' THEN '🧵 스레드'  WHEN h.ref = 'src:dc' OR h.ref LIKE '%dcinside.com' THEN '🗨️ 디시인사이드'  WHEN h.ref IN ('src:dev', 'src:gn', 'src:dq', 'src:velog') OR h.ref LIKE '%okky.kr' OR h.ref LIKE '%hada.io' OR h.ref LIKE '%velog.io' OR h.ref LIKE '%disquiet.io' THEN '💻 개발자 커뮤니티' WHEN h.ref IN ('src:medium', 'src:devto', 'src:reddit', 'src:hn', 'src:hashnode') OR h.ref LIKE '%medium.com' OR h.ref LIKE '%dev.to' OR h.ref LIKE '%reddit.com' OR h.ref LIKE '%ycombinator.com' OR h.ref LIKE '%hashnode.%' THEN '🌍 해외 개발 커뮤니티(레딧·HN·Medium·dev.to)'  WHEN h.ref LIKE 'accounts.google%' OR h.ref LIKE '%kakao.com' THEN '🔐 로그인하고 돌아옴'  WHEN h.ref = '' THEN '🔗 직접 접속(주소 입력·즐겨찾기·앱 안 링크)'  WHEN h.ref LIKE 'src:%' THEN '🏷️ 기타 홍보 링크(' || substr(h.ref, 5) || ')'  ELSE '🌐 기타 사이트(' || h.ref || ')' END r, COUNT(*) v FROM hits h JOIN (SELECT vid, day, MIN(ts) t FROM hits WHERE day = ?${W} GROUP BY vid, day) f ON h.vid = f.vid AND h.day = f.day AND h.ts = f.t GROUP BY r ORDER BY v DESC LIMIT 20`, d),
          cities: await all(`SELECT country || ' ' || city c, COUNT(DISTINCT vid) v FROM hits WHERE day >= ?${W} GROUP BY c ORDER BY v DESC LIMIT 10`, wk),
          mobile: await first(`SELECT COUNT(DISTINCT CASE WHEN mobile = 1 THEN vid END) m, COUNT(DISTINCT vid) v FROM hits WHERE day >= ?${W}`, wk),
          widgets: await all(`SELECT kind k, CASE WHEN host = '' THEN '(알 수 없음)' ELSE host END h, COUNT(*) n FROM widget_views WHERE day >= ? GROUP BY k, h ORDER BY n DESC LIMIT 20`, wk),
          widgetClicks: await all(`SELECT substr(ref, 7) k, COUNT(DISTINCT vid) v FROM hits WHERE day >= ? AND substr(ref, 1, 6) = 'src:w_'${W} GROUP BY k ORDER BY v DESC`, wk),
          recent: await all(`SELECT ts, path, ref, city, mobile, uid FROM hits WHERE 1=1${W} ORDER BY ts DESC LIMIT 30`) });
      }
      // ---- 관리자 (대장 계정만) ----
      // ---- 홍보 관리 (2026-10-19 SEO·홍보 지침 Phase 3): 생성은 PC 의 promo.py, 여기서는 검토·승인·예약·게시 완료 기록만. 자동 게시 없음
      // 추천 학습 기록 (2026-10-19): 노출·클릭만, 방문자 식별은 hits 와 같은 일일 해시 없이 개수만
      if (p === '/api/rec' && req.method === 'POST') {
        const ev = body.ev === 'click' ? 'click' : 'imp', ids = (Array.isArray(body.ids) ? body.ids : []).slice(0, 10).map(x => clean(String(x), 20));
        const det = Array.isArray(body.det) ? body.det.slice(0, 10) : [];
        const d = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
        for (let k = 0; k < ids.length; k++) await env.DB.prepare('INSERT INTO rec_log (day, ts, ev, item, pos, det) VALUES (?, ?, ?, ?, ?, ?)').bind(d, now(), ev, ids[k], k, det[k] ? JSON.stringify(det[k]).slice(0, 300) : null).run();
        return json(req, { ok: 1 });
      }
      if (p === '/api/admin/promo') {
        const u = await me(req, env); if (!u || !ADMINS.includes(u.id)) return err(req, '권한이 없어요.', 403);
        if (req.method === 'GET') {
          const st = clean(url.searchParams.get('st') || '', 12), ch = clean(url.searchParams.get('ch') || '', 16);
          const rows = (await env.DB.prepare(`SELECT * FROM promo WHERE (? = '' OR status = ?) AND (? = '' OR channel = ?) ORDER BY id DESC LIMIT 200`).bind(st, st, ch, ch).all()).results;
          const toks = rows.map(r => 'src:' + r.tok);
          const clicks = toks.length ? (await env.DB.prepare(`SELECT substr(ref, 5) t, COUNT(DISTINCT vid) v, COUNT(*) n FROM hits WHERE ref IN (${toks.map(() => '?').join(',')}) GROUP BY ref`).bind(...toks).all()).results : [];
          const byCh = (await env.DB.prepare(`SELECT p.channel ch, COUNT(DISTINCT h.vid) v FROM hits h JOIN promo p ON h.ref = 'src:' || p.tok WHERE h.day >= ? GROUP BY p.channel`).bind(new Date(Date.now() + 9 * 3600e3 - 30 * 864e5).toISOString().slice(0, 10)).all()).results;
          const cnt = (await env.DB.prepare('SELECT status, COUNT(*) n FROM promo GROUP BY status').all()).results;
          return json(req, { rows, clicks, byCh, cnt });
        }
        const id = +body.id, act = String(body.act || ''); const r = await env.DB.prepare('SELECT * FROM promo WHERE id = ?').bind(id).first();
        if (!r) return err(req, '없는 항목이에요.', 404);
        const NEXT = { approve: [['REVIEW'], 'APPROVED'], schedule: [['APPROVED', 'SCHEDULED'], 'SCHEDULED'], publish: [['APPROVED', 'SCHEDULED'], 'PUBLISHED'], fail: [['APPROVED', 'SCHEDULED', 'REVIEW'], 'FAILED'],
          retry: [['FAILED'], 'REVIEW'], review: [['DRAFT'], 'REVIEW'], back: [['REVIEW', 'APPROVED', 'SCHEDULED'], 'DRAFT'] };
        if (act === 'edit') {
          if (!['DRAFT', 'REVIEW', 'APPROVED'].includes(r.status)) return err(req, '게시·예약된 글은 고칠 수 없어요.');
          await env.DB.prepare("UPDATE promo SET body = ?, status = 'REVIEW', note = ?, updated = ? WHERE id = ?").bind(String(body.body || '').slice(0, 4000), '수정됨(사람 확인): ' + clean(body.note || '', 200), now(), id).run();
          return json(req, { ok: 1 });
        }
        const nx = NEXT[act]; if (!nx || !nx[0].includes(r.status)) return err(req, `${r.status} 상태에서는 「${act}」를 할 수 없어요.`);
        if (act === 'review' && JSON.parse(r.qc || '[]').length && !String(body.note || '').trim()) return err(req, '자동 검사에서 걸린 글이에요. 무엇을 확인했는지 메모를 남겨야 검토로 넘길 수 있어요.');
        let sched = r.scheduled;
        if (act === 'schedule') {
          sched = clean(body.scheduled || '', 16); if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(sched)) return err(req, '예약 시각을 골라 주세요.');
          const GAP = { naver_blog: 24, threads: 2, x: 1, instagram: 12, shorts: 24, community: 72 }[r.channel] || 2;   // 채널별 최소 게시 간격(시간)
          const near = await env.DB.prepare("SELECT id, scheduled FROM promo WHERE channel = ? AND id != ? AND status IN ('SCHEDULED', 'PUBLISHED') AND scheduled IS NOT NULL AND abs(julianday(scheduled) - julianday(?)) * 24 < ?").bind(r.channel, id, sched, GAP).first();
          if (near) return err(req, `같은 채널에 ${near.scheduled} 예약이 있어요. ${GAP}시간 이상 띄워 주세요.`);
        }
        await env.DB.prepare('UPDATE promo SET status = ?, scheduled = ?, published = ?, post_url = ?, note = ?, updated = ? WHERE id = ?')
          .bind(nx[1], sched || null, act === 'publish' ? new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 16) : r.published, act === 'publish' ? clean(body.post_url || '', 300) : r.post_url,
                clean(body.note || r.note || '', 300), now(), id).run();
        return json(req, { ok: 1, status: nx[1] });
      }
      if (p === '/api/admin') {
        const u = await me(req, env); if (!u || !ADMINS.includes(u.id)) return err(req, '권한이 없어요.', 403);
        const one = async q => (await env.DB.prepare(q).first('n')) || 0, day = now() - DAY, week = now() - 7 * DAY;
        const recent = (await env.DB.prepare("SELECT id, nick, created, CASE WHEN pw LIKE 'oauth$%' THEN substr(pw, 7) ELSE 'email' END via FROM users ORDER BY created DESC LIMIT 15").all()).results;
        const reported = (await env.DB.prepare("SELECT 'post' k, id, title t, reports, hidden FROM posts WHERE reports > 0 UNION ALL SELECT 'team', id, name, reports, hidden FROM teams WHERE reports > 0 ORDER BY reports DESC LIMIT 20").all()).results;
        const byDay = (await env.DB.prepare("SELECT date(created, 'unixepoch', '+9 hours') d, COUNT(*) n FROM users WHERE created > ? GROUP BY d ORDER BY d").bind(now() - 14 * DAY).all()).results;
        return json(req, {
          users: await one('SELECT COUNT(*) n FROM users'), users_day: await one(`SELECT COUNT(*) n FROM users WHERE created > ${day}`), users_week: await one(`SELECT COUNT(*) n FROM users WHERE created > ${week}`),
          social: await one("SELECT COUNT(*) n FROM oauth_links"), teams: await one('SELECT COUNT(*) n FROM teams WHERE hidden = 0'), open_teams: await one("SELECT COUNT(*) n FROM teams WHERE hidden = 0 AND status = 'open'"),
          posts: await one('SELECT COUNT(*) n FROM posts WHERE hidden = 0'), favs: await one('SELECT COUNT(*) n FROM user_items WHERE fav = 1'), applied: await one("SELECT COUNT(*) n FROM user_items WHERE state != ''"),
          won: await one("SELECT COUNT(*) n FROM user_items WHERE state = 'won'"), alerts: await one("SELECT COUNT(*) n FROM user_prefs WHERE data LIKE '%\"alert\":\"1\"%'"),  push: await one('SELECT COUNT(*) n FROM push_subs'),
          invites: await one('SELECT COUNT(*) n FROM invited'), visits: await one('SELECT COUNT(*) n FROM ref_visits'), recent, reported, byDay });
      }
      // ---- 팀 모집 ----
      if (p === '/api/teams' && req.method === 'GET') {
        const c = clean(url.searchParams.get('contest'), 40), page = Math.max(0, +url.searchParams.get('page') || 0);
        const sel = "SELECT t.id, t.contest_id, t.contest_title, t.name, substr(t.intro, 1, 160) intro, t.roles, t.size, t.deadline, t.status, t.created, u.nick leader, (SELECT COUNT(*) FROM team_members m WHERE m.team_id = t.id AND m.state = 'accepted') cnt, (SELECT data FROM team_prefs f WHERE f.team_id = t.id) prefs FROM teams t LEFT JOIN users u ON u.id = t.leader_id WHERE t.hidden = 0";
        const ord = " ORDER BY t.status = 'closed', t.created DESC LIMIT 30 OFFSET ?";
        const q = c ? env.DB.prepare(sel + ' AND t.contest_id = ?' + ord).bind(c, page * 30) : env.DB.prepare(sel + ord).bind(page * 30);
        return json(req, { teams: (await q.all()).results.map(t => ({ ...t, prefs: t.prefs ? JSON.parse(t.prefs) : {} })) });
      }
      if (p === '/api/teams' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const name = clean(body.name, 60), intro = clean(body.intro, 2000), cid = clean(body.contest_id, 40) || 'free';
        if (name.length < 2 || intro.length < 5) return err(req, '팀 이름과 소개를 조금 더 써 주세요.');
        const roles = clean(body.roles, 200).split(/[,，、]+/).map(r => r.trim().slice(0, 20)).filter(Boolean).slice(0, 8).join(',');
        const size = Math.min(20, Math.max(2, (+body.size | 0) || 4)), dl = /^\d{4}-\d{2}-\d{2}$/.test(body.deadline || '') ? body.deadline : '';
        if (await count(env, 'SELECT COUNT(*) n FROM teams WHERE leader_id = ? AND created > ?', u.id, now() - DAY) >= 5) return err(req, '하루에 만들 수 있는 팀 수를 넘었어요.', 429);
        const r = await env.DB.prepare('INSERT INTO teams (contest_id, contest_title, leader_id, name, intro, roles, size, deadline, contact, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
          .bind(cid, clean(body.contest_title, 120), u.id, name, intro, roles, size, dl, clean(body.contact, 300), now()).run();
        const tid = r.meta.last_row_id;
        await env.DB.prepare("INSERT INTO team_members (team_id, user_id, role, state, created) VALUES (?, ?, '팀장', 'accepted', ?)").bind(tid, u.id, now()).run();
        return json(req, { id: tid });
      }
      if (p === '/api/myteams') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const r = await env.DB.prepare("SELECT t.id, t.name, t.contest_id, t.contest_title, t.status, m.state, (t.leader_id = ?) leader, (SELECT COUNT(*) FROM team_members x WHERE x.team_id = t.id AND x.state = 'pending') waiting FROM team_members m JOIN teams t ON t.id = m.team_id WHERE m.user_id = ? AND t.hidden = 0 ORDER BY t.created DESC LIMIT 50").bind(u.id, u.id).all();
        return json(req, { teams: r.results });
      }
      let tm = p.match(/^\/api\/teams\/(\d+)(?:\/(apply|decide|close|open|leave|edit|image|unimage))?$/);
      if (tm) {
        const tid = +tm[1], act = tm[2] || '';
        const t = await env.DB.prepare('SELECT t.*, u.nick leader FROM teams t LEFT JOIN users u ON u.id = t.leader_id WHERE t.id = ? AND t.hidden = 0').bind(tid).first();
        if (!t) return err(req, '없거나 내려간 팀이에요.', 404);
        const u = await me(req, env), isLeader = !!u && u.id === t.leader_id;
        const mine = u ? await env.DB.prepare('SELECT state, role FROM team_members WHERE team_id = ? AND user_id = ?').bind(tid, u.id).first() : null;
        if (!act && req.method === 'GET') {
          const mem = (await env.DB.prepare("SELECT m.role, u.nick FROM team_members m LEFT JOIN users u ON u.id = m.user_id WHERE m.team_id = ? AND m.state = 'accepted' ORDER BY m.created").bind(tid).all()).results;
          const apps = isLeader ? (await env.DB.prepare("SELECT m.user_id uid, m.role, m.msg, m.created, u.nick FROM team_members m LEFT JOIN users u ON u.id = m.user_id WHERE m.team_id = ? AND m.state = 'pending' ORDER BY m.created").bind(tid).all()).results : [];
          const ok = isLeader || (mine && mine.state === 'accepted');
          const { leader_id, contact, reports, hidden, ...pub } = t;
          const prefs = JSON.parse((await env.DB.prepare('SELECT data FROM team_prefs WHERE team_id = ?').bind(tid).first('data')) || '{}');
          const album = ok ? (await env.DB.prepare("SELECT i.id, i.caption, i.created, u.nick, (i.user_id = ?) mine FROM team_images i LEFT JOIN users u ON u.id = i.user_id WHERE i.team_id = ? AND i.kind = 'post' AND i.hidden = 0 ORDER BY i.created DESC LIMIT 60").bind(u ? u.id : 0, tid).all()).results : [];
          return json(req, { team: { ...pub, contact: ok ? contact : '' }, members: mem, applicants: apps, me: { leader: isLeader, state: mine ? mine.state : '' }, prefs, album });
        }
        if (!act && req.method === 'DELETE') {
          if (!isLeader) return err(req, '팀장만 지울 수 있어요.', 403);
          await env.DB.prepare('UPDATE teams SET hidden = 1 WHERE id = ?').bind(tid).run(); return json(req, { ok: true });
        }
        if (req.method !== 'POST' || !act) return err(req, '없는 주소예요.', 404);
        if (!u) return err(req, '로그인이 필요해요.', 401);
        if (act === 'apply') {
          if (isLeader) return err(req, '내가 만든 팀이에요.');
          if (t.status !== 'open') return err(req, '모집이 끝난 팀이에요.');
          if (mine && mine.state !== 'rejected') return err(req, mine.state === 'accepted' ? '이미 팀원이에요.' : '이미 신청했어요. 팀장 답을 기다려 주세요.');
          if (await count(env, "SELECT COUNT(*) n FROM team_members WHERE user_id = ? AND created > ? AND state = 'pending'", u.id, now() - DAY) >= 20) return err(req, '하루에 신청할 수 있는 수를 넘었어요.', 429);
          await env.DB.prepare("INSERT OR REPLACE INTO team_members (team_id, user_id, role, msg, state, created) VALUES (?, ?, ?, ?, 'pending', ?)").bind(tid, u.id, clean(body.role, 20), clean(body.msg, 500), now()).run();
          return json(req, { ok: true });
        }
        if (act === 'image') {  // 표지(파티장) 또는 앨범(파티원)
          const kind = body.kind === 'cover' ? 'cover' : 'post';
          if (kind === 'cover' ? !isLeader : !(isLeader || (mine && mine.state === 'accepted'))) return err(req, kind === 'cover' ? '표지는 파티장만 바꿀 수 있어요.' : '파티원만 사진을 올릴 수 있어요.', 403);
          const m2 = String(body.data || '').match(/^data:(image\/(?:webp|jpeg|png));base64,([A-Za-z0-9+/=]+)$/);
          if (!m2) return err(req, '이미지 형식을 확인해 주세요.');
          if (m2[2].length > 420000) return err(req, '이미지가 너무 커요.');
          if (await count(env, 'SELECT COUNT(*) n FROM team_images WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= 30) return err(req, '하루에 올릴 수 있는 사진 수를 넘었어요.', 429);
          const r = await env.DB.prepare('INSERT INTO team_images (team_id, user_id, kind, mime, data, caption, created) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(tid, u.id, kind, m2[1], m2[2], clean(body.caption, 100), now()).run();
          if (kind === 'cover') {
            const pr = JSON.parse((await env.DB.prepare('SELECT data FROM team_prefs WHERE team_id = ?').bind(tid).first('data')) || '{}');
            if (pr.cover) await env.DB.prepare('UPDATE team_images SET hidden = 1 WHERE id = ?').bind(pr.cover).run();
            pr.cover = r.meta.last_row_id;
            await env.DB.prepare('INSERT OR REPLACE INTO team_prefs (team_id, data) VALUES (?, ?)').bind(tid, JSON.stringify(pr)).run();
          }
          return json(req, { id: r.meta.last_row_id });
        }
        if (act === 'unimage') {
          await env.DB.prepare('UPDATE team_images SET hidden = 1 WHERE id = ? AND team_id = ? AND (user_id = ? OR ?)').bind(+body.id || 0, tid, u.id, isLeader ? 1 : 0).run();
          return json(req, { ok: true });
        }
        if (act === 'leave') {
          if (isLeader) return err(req, '팀장은 나갈 수 없어요. 모집을 닫거나 팀을 지워 주세요.');
          await env.DB.prepare('DELETE FROM team_members WHERE team_id = ? AND user_id = ?').bind(tid, u.id).run(); return json(req, { ok: true });
        }
        if (!isLeader) return err(req, '팀장만 할 수 있어요.', 403);
        if (act === 'edit') {  // 파티 설정
          const name = clean(body.name, 60), intro = clean(body.intro, 2000);
          if (name.length < 2 || intro.length < 5) return err(req, '파티 이름과 소개를 조금 더 써 주세요.');
          const roles = clean(body.roles, 200).split(/[,，、]+/).map(r => r.trim().slice(0, 20)).filter(Boolean).slice(0, 8).join(',');
          const size = Math.min(20, Math.max(2, (+body.size | 0) || t.size)), dl = /^\d{4}-\d{2}-\d{2}$/.test(body.deadline || '') ? body.deadline : '';
          await env.DB.prepare('UPDATE teams SET name = ?, intro = ?, roles = ?, size = ?, deadline = ?, contact = ? WHERE id = ?').bind(name, intro, roles, size, dl, clean(body.contact, 300), tid).run();
          const pr = JSON.parse((await env.DB.prepare('SELECT data FROM team_prefs WHERE team_id = ?').bind(tid).first('data')) || '{}');
          if (/^#[0-9a-f]{6}$/i.test(body.color || '')) pr.color = body.color;
          if (body.emoji !== undefined) pr.emoji = clean(body.emoji, 4);
          await env.DB.prepare('INSERT OR REPLACE INTO team_prefs (team_id, data) VALUES (?, ?)').bind(tid, JSON.stringify(pr)).run();
          return json(req, { ok: true });
        }
        if (act === 'decide') {
          if (body.accept && await count(env, "SELECT COUNT(*) n FROM team_members WHERE team_id = ? AND state = 'accepted'", tid) >= t.size) return err(req, '정원이 다 찼어요. 모집을 닫거나 인원을 늘려 주세요.');
          await env.DB.prepare("UPDATE team_members SET state = ? WHERE team_id = ? AND user_id = ? AND state = 'pending'").bind(body.accept ? 'accepted' : 'rejected', tid, +body.uid || 0).run();
          return json(req, { ok: true });
        }
        await env.DB.prepare('UPDATE teams SET status = ? WHERE id = ?').bind(act === 'close' ? 'closed' : 'open', tid).run();
        return json(req, { ok: true });
      }
      // ---- 신고 (3명 신고 시 자동 숨김) ----
      // ---- 페이지 댓글·좋아요·조회수 (모든 페이지 공통. 쓰기는 회원만) ----
      if (p === '/api/p' && req.method === 'GET') {
        const pg = npage(url.searchParams.get('page'));
        if (!pg) return err(req, '주소를 확인해 주세요.');
        const u = await me(req, env);
        const fid = (pg.match(/^\/(?:c|a)\/([^/]+)\//) || [])[1];
        const b = [
          env.DB.prepare('SELECT views, likes, cms FROM page_stats WHERE page = ?').bind(pg),
          env.DB.prepare('SELECT c.id, c.body, c.created, c.user_id, u.nick FROM page_comments c LEFT JOIN users u ON u.id = c.user_id WHERE c.page = ? AND c.hidden = 0 ORDER BY c.created DESC LIMIT 100').bind(pg),
          env.DB.prepare('SELECT 1 x FROM page_likes WHERE page = ? AND user_id = ?').bind(pg, u ? u.id : 0)];
        if (fid) b.push(env.DB.prepare('SELECT COUNT(*) n FROM user_items WHERE fav = 1 AND item_id = ?').bind('c:' + fid));
        const r = await env.DB.batch(b);
        const s0 = (r[0].results || [])[0] || { views: 0, likes: 0, cms: 0 };
        return json(req, { views: s0.views, likes: s0.likes, cms: s0.cms, liked: !!(r[2].results || []).length,
          fav: fid ? (((r[3].results || [])[0] || {}).n || 0) : 0,
          comments: (r[1].results || []).map(c => ({ id: c.id, nick: c.nick || '탈퇴한 회원', body: c.body, created: c.created, mine: !!u && c.user_id === u.id, adm: ADMINS.includes(c.user_id) })) });
      }
      if (p === '/api/p/like' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인하면 좋아요를 누를 수 있어요.', 401);
        const pg = npage(body.page); if (!pg) return err(req, '주소를 확인해 주세요.');
        const on = body.on !== false;
        const had = await count(env, 'SELECT COUNT(*) n FROM page_likes WHERE page = ? AND user_id = ?', pg, u.id);
        if (on && !had) {
          if (await count(env, 'SELECT COUNT(*) n FROM page_likes WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= 300) return err(req, '오늘은 여기까지만 눌러 주세요.', 429);
          await env.DB.batch([env.DB.prepare('INSERT OR IGNORE INTO page_likes (user_id, page, created) VALUES (?, ?, ?)').bind(u.id, pg, now()),
            env.DB.prepare('INSERT INTO page_stats (page, title, likes, updated) VALUES (?, ?, 1, ?) ON CONFLICT(page) DO UPDATE SET likes = likes + 1, updated = excluded.updated').bind(pg, clean(body.title, 90), now())]);
        } else if (!on && had) {
          await env.DB.batch([env.DB.prepare('DELETE FROM page_likes WHERE user_id = ? AND page = ?').bind(u.id, pg),
            env.DB.prepare('UPDATE page_stats SET likes = MAX(0, likes - 1), updated = ? WHERE page = ?').bind(now(), pg)]);
        }
        const s0 = await env.DB.prepare('SELECT likes FROM page_stats WHERE page = ?').bind(pg).first('likes');
        return json(req, { likes: s0 || 0, liked: on });
      }
      if (p === '/api/p/comment' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인하면 댓글을 쓸 수 있어요.', 401);
        const pg = npage(body.page); if (!pg) return err(req, '주소를 확인해 주세요.');
        const text = clean(body.body, 1000);
        if (text.length < 2) return err(req, '댓글을 조금 더 써 주세요.');
        if (await count(env, 'SELECT COUNT(*) n FROM page_comments WHERE user_id = ? AND created > ?', u.id, now() - DAY) >= LIMIT_COMMENT) return err(req, '하루에 쓸 수 있는 댓글 수를 넘었어요.', 429);
        if (await count(env, 'SELECT COUNT(*) n FROM page_comments WHERE user_id = ? AND created > ?', u.id, now() - 20)) return err(req, '조금 천천히 써 주세요.', 429);
        const t = now();
        const r = await env.DB.prepare('INSERT INTO page_comments (page, title, user_id, body, created) VALUES (?, ?, ?, ?, ?)').bind(pg, clean(body.title, 90), u.id, text, t).run();
        await env.DB.prepare('INSERT INTO page_stats (page, title, cms, updated) VALUES (?, ?, 1, ?) ON CONFLICT(page) DO UPDATE SET cms = cms + 1, updated = excluded.updated').bind(pg, clean(body.title, 90), t).run();
        return json(req, { id: r.meta.last_row_id, nick: u.nick, created: t, adm: ADMINS.includes(u.id) });
      }
      let gm = p.match(/^\/api\/p\/comment\/(\d+)$/);
      if (gm && req.method === 'DELETE') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const row = await env.DB.prepare('SELECT page, user_id, hidden FROM page_comments WHERE id = ?').bind(+gm[1]).first();
        if (!row || (row.user_id !== u.id && !ADMINS.includes(u.id))) return err(req, '지울 수 없는 댓글이에요.', 403);
        if (!row.hidden) await env.DB.batch([env.DB.prepare('UPDATE page_comments SET hidden = 1 WHERE id = ?').bind(+gm[1]),
          env.DB.prepare('UPDATE page_stats SET cms = MAX(0, cms - 1) WHERE page = ?').bind(row.page)]);
        return json(req, { ok: true });
      }
      if (p === '/api/p/stats' && req.method === 'POST') {   // 목록 화면에서 여러 페이지 수치를 한 번에
        const pages = (Array.isArray(body.pages) ? body.pages : []).map(npage).filter(Boolean).slice(0, 200);
        if (!pages.length) return json(req, { stats: {} });
        const qs = pages.map(() => '?').join(',');
        const r = await env.DB.prepare('SELECT page, views, likes, cms FROM page_stats WHERE page IN (' + qs + ')').bind(...pages).all();
        const out = {};
        for (const x of r.results || []) out[x.page] = { v: x.views, l: x.likes, c: x.cms };
        return json(req, { stats: out });
      }
      if (p === '/api/p/top' && req.method === 'GET') {      // 인기 페이지(조회수·좋아요·댓글 기준)
        const pre = npage(url.searchParams.get('prefix') || '/');
        if (!pre) return err(req, '주소를 확인해 주세요.');
        const by = ['views', 'likes', 'cms'].includes(url.searchParams.get('by')) ? url.searchParams.get('by') : 'views';
        const n = Math.min(40, Math.max(1, +url.searchParams.get('n') || 12));
        const r = await env.DB.prepare("SELECT page, title, views, likes, cms FROM page_stats WHERE page LIKE ? AND page != ? AND page NOT LIKE '/admin%' AND page NOT LIKE '/me/%' AND " + by + " > 0 ORDER BY " + by + " DESC, views DESC LIMIT ?")
          .bind(pre + '%', pre, n).all();
        return json(req, { top: (r.results || []).map(x => ({ page: x.page, title: x.title, v: x.views, l: x.likes, c: x.cms })) });
      }
      if (p === '/api/p/recent' && req.method === 'GET') {   // 사이트 전체 최근 댓글
        const n = Math.min(30, Math.max(1, +url.searchParams.get('n') || 10));
        const r = await env.DB.prepare('SELECT c.id, c.page, c.title, c.body, c.created, c.user_id, u.nick FROM page_comments c LEFT JOIN users u ON u.id = c.user_id WHERE c.hidden = 0 ORDER BY c.created DESC LIMIT ?').bind(n).all();
        return json(req, { comments: (r.results || []).map(c => ({ id: c.id, page: c.page, title: c.title, nick: c.nick || '탈퇴한 회원', body: c.body.slice(0, 140), created: c.created, adm: ADMINS.includes(c.user_id) })) });
      }
      if (p === '/api/report' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const t = /^[pctg]:\d+$/.test(body.target || '') ? body.target : '';
        if (!t) return err(req, '대상을 확인해 주세요.');
        const ins = await env.DB.prepare('INSERT OR IGNORE INTO reports (user_id, target, created) VALUES (?, ?, ?)').bind(u.id, t, now()).run();
        if (ins.meta.changes) {
          const [k, id] = t.split(':'), tb = { p: 'posts', c: 'comments', t: 'teams', g: 'page_comments' }[k];
          await env.DB.prepare(`UPDATE ${tb} SET reports = reports + 1, hidden = CASE WHEN reports + 1 >= ? THEN 1 ELSE hidden END WHERE id = ?`).bind(HIDE_AT, +id).run();
        }
        return json(req, { ok: true });
      }
      if (p.startsWith('/api/kakao/alert')) {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        if (p === '/api/kakao/alert' && req.method === 'GET')
          return json(req, { ready: !!(env.KAKAO_ID && env.KAKAO_ALERT_KEY), on: !!(await env.DB.prepare('SELECT user_id FROM kakao_alert WHERE user_id = ?').bind(u.id).first('user_id')) });
        if (p === '/api/kakao/alert/start' && req.method === 'POST') {
          const nonce = hex(crypto.getRandomValues(new Uint8Array(16)));
          await env.DB.prepare('INSERT INTO kakao_alert_nonce (nonce, user_id, created) VALUES (?, ?, ?)').bind(nonce, u.id, now()).run();
          return json(req, { url: url.origin + '/api/oauth/kakao/start?back=/me/&alert=' + nonce });
        }
        if (p === '/api/kakao/alert/off' && req.method === 'POST') {
          const row = await env.DB.prepare('SELECT user_id, rt FROM kakao_alert WHERE user_id = ?').bind(u.id).first();
          if (row) {
            try {
              const at = await kakaoAccess(env, row);
              if (at) await fetch('https://kapi.kakao.com/v2/user/revoke/scopes', { method: 'POST', headers: { Authorization: 'Bearer ' + at, 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ scopes: '["talk_message"]' }) });
            } catch (e) { /* 철회 실패해도 토큰은 지움 */ }
            await env.DB.prepare('DELETE FROM kakao_alert WHERE user_id = ?').bind(u.id).run();
          }
          return json(req, { ok: true });
        }
      }
      if (p === '/api/health') return json(req, { ok: true, t: now() });
      return err(req, '없는 주소예요.', 404);
    } catch (e) {
      return err(req, '잠시 문제가 생겼어요.', 500);
    }
  },
  async scheduled(ev, env, ctx) {
    if (ev.cron === '30 23 * * *') ctx.waitUntil(kakaoAlerts(env));
  },
};
