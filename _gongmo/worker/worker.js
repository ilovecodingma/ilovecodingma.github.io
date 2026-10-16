// 루리의 줍줍 커뮤니티 API — Cloudflare Worker + D1 (바인딩 이름: DB)
// 회원가입·로그인(이메일+비밀번호만 받음 — 2026-10-16 사용자 "최소 정보, 이메일 주소만"; 표시 이름은 이메일 앞부분을 가린 값), 공모전별 후기·질문 게시판, 댓글, 신고(3회 누적 시 자동 숨김)
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
        return json(req, { token: await newSession(env, r.meta.last_row_id), nick });
      }
      if (p === '/api/login' && req.method === 'POST') {
        const u = await env.DB.prepare('SELECT id, nick, pw, banned FROM users WHERE email = ?').bind(clean(body.email, 120).toLowerCase()).first();
        if (!u || !(await checkPw(String(body.password || ''), u.pw))) return err(req, '이메일 또는 비밀번호가 맞지 않아요.', 401);
        if (u.banned) return err(req, '이용이 제한된 계정이에요.', 403);
        return json(req, { token: await newSession(env, u.id), nick: u.nick });
      }
      if (p === '/api/logout' && req.method === 'POST') {
        const t = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/, '');
        if (t) await env.DB.prepare('DELETE FROM sessions WHERE token = ?').bind(t).run();
        return json(req, { ok: true });
      }
      if (p === '/api/me') { const u = await me(req, env); return u ? json(req, { nick: u.nick }) : err(req, '로그인이 필요해요.', 401); }
      if (p === '/api/withdraw' && req.method === 'POST') {  // 회원 탈퇴: 계정·세션 삭제, 글은 '탈퇴한 회원'으로 숨김
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        await env.DB.batch([env.DB.prepare('UPDATE posts SET hidden = 1 WHERE user_id = ?').bind(u.id), env.DB.prepare('UPDATE comments SET hidden = 1 WHERE user_id = ?').bind(u.id),
          env.DB.prepare('DELETE FROM sessions WHERE user_id = ?').bind(u.id), env.DB.prepare('DELETE FROM users WHERE id = ?').bind(u.id)]);
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
      // ---- 신고 (3명 신고 시 자동 숨김) ----
      if (p === '/api/report' && req.method === 'POST') {
        const u = await me(req, env); if (!u) return err(req, '로그인이 필요해요.', 401);
        const t = /^[pc]:\d+$/.test(body.target || '') ? body.target : '';
        if (!t) return err(req, '대상을 확인해 주세요.');
        const ins = await env.DB.prepare('INSERT OR IGNORE INTO reports (user_id, target, created) VALUES (?, ?, ?)').bind(u.id, t, now()).run();
        if (ins.meta.changes) {
          const [k, id] = t.split(':'), tb = k === 'p' ? 'posts' : 'comments';
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
