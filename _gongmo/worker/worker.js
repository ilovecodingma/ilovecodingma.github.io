// 루리의 줍줍 커뮤니티 API — Cloudflare Worker + D1 (바인딩 이름: DB)
// 회원가입·로그인(이메일+비밀번호만 받음 — 2026-10-16 사용자 "최소 정보, 이메일 주소만"; 표시 이름은 이메일 앞부분을 가린 값), 공모전별 팀 모집(만들기·신청·수락), 후기·질문 게시판, 댓글, 신고(3회 누적 시 자동 숨김)
const ORIGINS = ['https://sungprofile.cloud', 'http://localhost:8765'];
const DAY = 86400, LIMIT_POST = 10, LIMIT_COMMENT = 40, HIDE_AT = 3;

const now = () => Math.floor(Date.now() / 1000);
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
const unhex = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));
const clean = (s, n) => String(s || '').replace(/[\u0000-\u0008\u000b-\u001f]/g, '').trim().slice(0, n);

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
async function count(env, sql, ...a) { return (await env.DB.prepare(sql).bind(...a).first('n')) || 0; }


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
    const q = new URLSearchParams({ client_id: cid, redirect_uri: cb, response_type: 'code', state, ...(P.scope ? { scope: P.scope } : {}), ...(prov === 'google' ? { prompt: 'select_account' } : {}) });
    return new Response(null, { status: 302, headers: { Location: P.auth + '?' + q, 'Set-Cookie': `jo=${state}.${encodeURIComponent(back)}; Path=/api/oauth; Max-Age=600; HttpOnly; Secure; SameSite=Lax` } });
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
        const d = {}; for (const [k, v] of Object.entries(body.data || {}).slice(0, 12)) if (/^[a-z]{1,12}$/.test(k)) d[k] = clean(v, 24);
        await env.DB.prepare('INSERT OR REPLACE INTO user_prefs (user_id, data) VALUES (?, ?)').bind(u.id, JSON.stringify(d)).run();
        return json(req, { ok: true });
      }
      if (p === '/api/me') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        let code = await env.DB.prepare('SELECT code FROM invite_codes WHERE user_id = ?').bind(u.id).first('code');
        if (!code) { code = hex(crypto.getRandomValues(new Uint8Array(4))); await env.DB.prepare('INSERT OR IGNORE INTO invite_codes (code, user_id) VALUES (?, ?)').bind(code, u.id).run(); }
        const byC = (await env.DB.prepare("SELECT contest_id h, SUM(v) visits, SUM(j) joins FROM (SELECT contest_id, 1 v, 0 j FROM ref_visits WHERE code = ? UNION ALL SELECT contest_id, 0, 1 FROM invited WHERE by_user = ?) GROUP BY contest_id ORDER BY SUM(v) + SUM(j) * 3 DESC LIMIT 50").bind(code, u.id).all()).results;
        const prefs = await env.DB.prepare('SELECT data FROM user_prefs WHERE user_id = ?').bind(u.id).first('data');
        return json(req, { nick: u.nick, code, invites: byC.reduce((a, x) => a + x.joins, 0), visits: byC.reduce((a, x) => a + x.visits, 0), by_contest: byC, prefs: prefs ? JSON.parse(prefs) : {} });
      }
      if (p === '/api/withdraw' && req.method === 'POST') {  // 회원 탈퇴: 계정·세션 삭제, 글은 '탈퇴한 회원'으로 숨김
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        await env.DB.batch([env.DB.prepare('UPDATE posts SET hidden = 1 WHERE user_id = ?').bind(u.id), env.DB.prepare('UPDATE comments SET hidden = 1 WHERE user_id = ?').bind(u.id),
          env.DB.prepare('DELETE FROM sessions WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM invite_codes WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM user_prefs WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM oauth_links WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM users WHERE id = ?').bind(u.id)]);
        return json(req, { ok: true });
      }
      // ---- 글 ----
      if (p === '/api/posts' && req.method === 'GET') {
        const c = clean(url.searchParams.get('contest'), 40), page = Math.max(0, +url.searchParams.get('page') || 0);
        const q = c ? env.DB.prepare('SELECT p.id, p.contest_id, p.contest_title, p.kind, p.title, p.body, p.rating, p.created, u.nick, (SELECT COUNT(*) FROM comments m WHERE m.post_id = p.id AND m.hidden = 0) cm FROM posts p LEFT JOIN users u ON u.id = p.user_id WHERE p.hidden = 0 AND p.contest_id = ? ORDER BY p.created DESC LIMIT 20 OFFSET ?').bind(c, page * 20)
                    : env.DB.prepare('SELECT p.id, p.contest_id, p.contest_title, p.kind, p.title, substr(p.body, 1, 140) body, p.rating, p.created, u.nick, (SELECT COUNT(*) FROM comments m WHERE m.post_id = p.id AND m.hidden = 0) cm FROM posts p LEFT JOIN users u ON u.id = p.user_id WHERE p.hidden = 0 ORDER BY p.created DESC LIMIT 20 OFFSET ?').bind(page * 20);
        return json(req, { posts: (await q.all()).results });
      }
      if (p === '/api/posts' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const kind = ['review', 'qna', 'tip'].includes(body.kind) ? body.kind : 'review';
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
        const r = await env.DB.prepare('SELECT c.id, c.body, c.created, u.nick FROM comments c LEFT JOIN users u ON u.id = c.user_id WHERE c.post_id = ? AND c.hidden = 0 ORDER BY c.created LIMIT 200')
          .bind(+url.searchParams.get('post') || 0).all();
        return json(req, { comments: r.results });
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
      if (p === '/api/report' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const t = /^[pct]:\d+$/.test(body.target || '') ? body.target : '';
        if (!t) return err(req, '대상을 확인해 주세요.');
        const ins = await env.DB.prepare('INSERT OR IGNORE INTO reports (user_id, target, created) VALUES (?, ?, ?)').bind(u.id, t, now()).run();
        if (ins.meta.changes) {
          const [k, id] = t.split(':'), tb = { p: 'posts', c: 'comments', t: 'teams' }[k];
          await env.DB.prepare(`UPDATE ${tb} SET reports = reports + 1, hidden = CASE WHEN reports + 1 >= ? THEN 1 ELSE hidden END WHERE id = ?`).bind(HIDE_AT, +id).run();
        }
        return json(req, { ok: true });
      }
      if (p === '/api/health') return json(req, { ok: true, t: now() });
      return err(req, '없는 주소예요.', 404);
    } catch (e) {
      return err(req, '잠시 문제가 생겼어요.', 500);
    }
  },
};
