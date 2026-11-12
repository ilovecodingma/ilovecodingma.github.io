// 하네스 학습 사이트(LMS) 토큰·진도 API — 별도 워커(jupjup-lms)·별도 D1(jupjup-lms). 운영 중인 jupjup-api 와 분리해 서로 영향이 없게 한다.
// 받는 정보: 토큰(서버가 만든 무작위 값), 진도 단계 이름, 짧은 메모(120자). 이메일·이름·경로·IP 원본은 받거나 저장하지 않는다(IP 는 시간당 발급 횟수 제한에만 쓰는 해시).
const ORIGINS = ['https://sungprofile.cloud'];
const ALPHA = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';   // 헷갈리는 글자(I,L,O,0,1) 뺌
const cors = (req) => {
  const o = req.headers.get('Origin') || '';
  return { 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
           'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '86400', Vary: 'Origin' };
};
const json = (req, data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...cors(req) } });

function newToken() {
  const b = new Uint8Array(12); crypto.getRandomValues(b);
  const c = Array.from(b, (x) => ALPHA[x % ALPHA.length]);
  return 'HX-' + c.slice(0, 4).join('') + '-' + c.slice(4, 8).join('') + '-' + c.slice(8, 12).join('');
}
const TOKEN_RE = /^HX-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$/;
const STEP_RE = /^[a-z0-9][a-z0-9._-]{0,39}$/;

async function sha(s) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return Array.from(new Uint8Array(d).slice(0, 8), (x) => x.toString(16).padStart(2, '0')).join('');
}
// 고정 창(시간) 제한: 같은 열쇠가 한 시간에 limit 번 넘게 부르면 거절
async function limited(env, key, limit) {
  const win = Math.floor(Date.now() / 3600000);
  const r = await env.DB.prepare('SELECT win, n FROM lms_rate WHERE k = ?').bind(key).first();
  if (!r || r.win !== win) { await env.DB.prepare('INSERT OR REPLACE INTO lms_rate (k, win, n) VALUES (?, ?, 1)').bind(key, win).run(); return false; }
  if (r.n >= limit) return true;
  await env.DB.prepare('UPDATE lms_rate SET n = n + 1 WHERE k = ?').bind(key).run();
  return false;
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(req) });
    const url = new URL(req.url), p = url.pathname.replace(/\/+$/, '');
    try {
      if (p === '/lms/health') return json(req, { ok: true });
      if (p === '/lms/issue' && req.method === 'POST') {
        const ip = req.headers.get('CF-Connecting-IP') || 'x';
        if (await limited(env, 'issue:' + (await sha(ip + new Date().toISOString().slice(0, 10))), 5)) return json(req, { ok: false, error: '잠시 뒤에 다시 해 주세요(시간당 발급 횟수 제한)' }, 429);
        let token = '';
        for (let i = 0; i < 5; i++) {
          const t = newToken();
          const r = await env.DB.prepare('INSERT OR IGNORE INTO lms_tokens (token, kind, created, last_seen) VALUES (?, ?, ?, ?)').bind(t, 'harness', Date.now(), Date.now()).run();
          if (r.meta && r.meta.changes) { token = t; break; }
        }
        if (!token) return json(req, { ok: false, error: '발급에 실패했습니다' }, 500);
        await env.DB.prepare('INSERT OR REPLACE INTO lms_progress (token, step, ts, note) VALUES (?, ?, ?, ?)').bind(token, 'start', Date.now(), '').run();
        return json(req, { ok: true, token });
      }
      if (p === '/lms/progress' && req.method === 'POST') {
        const b = await req.json().catch(() => ({}));
        const token = String(b.token || ''), step = String(b.step || ''), note = String(b.note || '').slice(0, 120);
        if (!TOKEN_RE.test(token) || !STEP_RE.test(step)) return json(req, { ok: false, error: '토큰이나 단계 이름 형식이 맞지 않습니다' }, 400);
        const t = await env.DB.prepare('SELECT token FROM lms_tokens WHERE token = ?').bind(token).first();
        if (!t) return json(req, { ok: false, error: '없는 토큰입니다' }, 404);
        if (await limited(env, 'prog:' + token, 120)) return json(req, { ok: false, error: '요청이 너무 잦습니다' }, 429);
        const n = await env.DB.prepare('SELECT count(*) AS c FROM lms_progress WHERE token = ?').bind(token).first();
        const has = await env.DB.prepare('SELECT 1 AS x FROM lms_progress WHERE token = ? AND step = ?').bind(token, step).first();
        if (!has && n.c >= 60) return json(req, { ok: false, error: '단계가 너무 많습니다' }, 400);
        await env.DB.batch([
          env.DB.prepare('INSERT OR REPLACE INTO lms_progress (token, step, ts, note) VALUES (?, ?, ?, ?)').bind(token, step, Date.now(), note),
          env.DB.prepare('UPDATE lms_tokens SET last_seen = ? WHERE token = ?').bind(Date.now(), token),
        ]);
        return json(req, { ok: true });
      }
      if (p === '/lms/me' && req.method === 'GET') {
        const token = (url.searchParams.get('token') || '').trim().toUpperCase();
        if (!TOKEN_RE.test(token)) return json(req, { ok: false, error: '토큰 형식이 맞지 않습니다(예: HX-ABCD-EFGH-JKMN)' }, 400);
        if (await limited(env, 'me:' + (await sha(req.headers.get('CF-Connecting-IP') || 'x')), 120)) return json(req, { ok: false, error: '요청이 너무 잦습니다' }, 429);
        const t = await env.DB.prepare('SELECT created, last_seen FROM lms_tokens WHERE token = ?').bind(token).first();
        if (!t) return json(req, { ok: false, error: '없는 토큰입니다. 하네스에서 발급한 토큰인지 확인해 주세요' }, 404);
        const rows = await env.DB.prepare('SELECT step, ts, note FROM lms_progress WHERE token = ? ORDER BY ts').bind(token).all();
        return json(req, { ok: true, created: t.created, steps: rows.results || [] });
      }
      return json(req, { ok: false, error: '없는 주소입니다' }, 404);
    } catch (e) {
      return json(req, { ok: false, error: '서버 안에서 오류가 났습니다' }, 500);
    }
  },
};
