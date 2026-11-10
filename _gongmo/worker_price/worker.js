// 최저가 찾기 API (2026-11-10 사용자 「이름 → 제품명 → 제품 코드 → 풀 스캔 → 가장 싼 것 + 바로가기」)
//   GET /api/price/search?q=겨울 장갑        → 제품 후보(제품 코드·이름·최저가)
//   GET /api/price/scan?pcode=6807997&uq=..  → 새 상품 판매처별 가격 + 중고 장터 글, 싼 순서
//   GET /api/price/scan?uq=겨울 장갑         → 제품 코드 없이 중고 장터만
// - 새 상품: 다나와 가격비교(판매처 목록). 중고: 중고나라 검색 결과.
//   당근은 이 서버에서 물으면 빈 목록만 돌려준다(2026-11-10 확인) → 글을 긁지 않고 검색 결과로 바로 가는 주소만 준다. 번개장터도 같다.
// - 같은 검색은 1시간 동안 저장해 둔 값을 돌려준다(상대 사이트에 같은 요청을 거듭 보내지 않는다).
// - 한 번 조회에 사이트마다 페이지 1장만 읽는다. 원본 글·판매처로 바로 가는 주소를 그대로 돌려준다.
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 jupjup-price/1.0 (+https://sungprofile.cloud/price/)';
const TTL = 3600;
const VER = 'v5';   // 추출 방식이 바뀌면 올린다(저장해 둔 옛 결과를 쓰지 않게)
const ORIGINS = ['https://sungprofile.cloud', 'https://www.sungprofile.cloud', 'http://localhost:8000', 'http://127.0.0.1:8000'];
const WANT = /삽니다|삽니당|구합니다|구해요|구해봅니다|구매합니다|구매원함|구매 원함|매입|구함|교환만/;

const strip = s => (s || '').replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'").replace(/\s+/g, ' ').trim();
const num = s => { const n = parseInt(String(s == null ? '' : s).replace(/[^\d]/g, ''), 10); return isFinite(n) ? n : null; };

async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'ko-KR,ko;q=0.9' }, redirect: 'follow' });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return await r.text();
}

// ── 다나와 통합검색 → 제품 후보
export function parseDanawaSearch(h) {
  const out = [], seen = new Set();
  for (const b0 of h.split('data-product-seq="').slice(1)) {
    const pc = b0.slice(0, b0.indexOf('"'));
    if (!/^\d{3,}$/.test(pc) || seen.has(pc)) continue;
    const b = b0.slice(0, 16000);
    let name = '';
    const re = new RegExp('<a href="https://prod\\.danawa\\.com/info/\\?pcode=' + pc + '[^"]*"[^>]*>([\\s\\S]*?)</a>', 'g');
    let m;
    while ((m = re.exec(b))) { const t = strip(m[1]); if (t.length > name.length && t.length <= 140 && !/^이미지/.test(t)) name = t; }
    if (!name) continue;
    seen.add(pc);
    const txt = b.replace(/<path[^>]*>/g, '').replace(/<[^>]+>/g, '|');
    const pm = txt.match(/([\d,]{3,})\|*원/);
    const im = b.match(/https:\/\/img\.danuri\.io\/[^"?\s\\]+/);
    out.push({ pcode: pc, name, price: pm ? num(pm[1]) : null, img: im ? im[0] + '?shrink=130:130' : '' });
  }
  return out;
}

// ── 다나와 제품 페이지 → 판매처별 가격
export function parseDanawaProduct(h, pcode) {
  const nm = h.match(/"@type":\s*"Product",\s*"name":\s*"([^"]+)"/);
  const lo = h.match(/"lowPrice":\s*"(\d+)"/), oc = h.match(/"offerCount":\s*"(\d+)"/);
  const im = h.match(/https:\/\/img\.danuri\.io\/catalog-image\/[^"?\s]+/);
  const rows = [], seen = new Set();
  const i = h.indexOf('list__mall-price');
  const seg = i < 0 ? '' : h.slice(i, h.indexOf('</ul>', i) < 0 ? i + 60000 : h.indexOf('</ul>', i));
  for (const b0 of seg.split('<li class="list-item">').slice(1)) {
    const b = b0.split('</li>')[0];
    const mall = (b.match(/class='image' alt='([^']*)'/) || b.match(/class="image" alt="([^"]*)"/) || b.match(/aria-label="([^"]*)"/) || [])[1];
    const price = num((b.match(/data-base-price="(\d+)"/) || b.match(/text__num">([\d,]+)/) || [])[1]);
    const lk = (b.match(/href="(https:\/\/prod\.danawa\.com\/bridge\/(?:[^"\\]|\\u0026)+)"/) || [])[1];
    if (!mall || mall === '상품보기' || !price || !lk) continue;
    let ship = null;
    const dp = b.match(/data-delivery-price="(\d+)"/);
    if (dp) ship = num(dp[1]);
    else {
      const dm = b.match(/class="box__delivery">([\s\S]*?)<div class="box__installment/);
      const dt = dm ? strip(dm[1].replace(/<div class="box__fast-notice">[\s\S]*?<\/div>\s*<\/div>\s*<\/div>\s*<\/div>/, '')) : '';
      if (/무료/.test(dt)) ship = 0;
      else { const a = dt.match(/([\d,]+)\s*원/g); if (a) ship = num(a[a.length - 1]); }
    }
    const key = mall + '|' + price;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({ mall, price, ship, total: price + (ship || 0), link: lk.replace(/&amp;/g, '&') });
  }
  if (!rows.length) {   // 새 화면(자료가 스크립트 안 따옴표 처리된 JSON 으로 들어 있음)
    const re = /\{\\"logo\\":\\"([^"\\]*)\\",\\"logoSrc\\":\\"[^"]*?\\",\\"companyCode\\":\\"([^"\\]*)\\"[\s\S]{0,400}?\\"price\\":\\"([\d,]+)\\",\\"delivery\\":\\"([^"\\]*)\\"[\s\S]{0,900}?\\"url\\":\\"(https:\/\/prod\.danawa\.com\/bridge\/(?:[^"\\]|\\u0026)+)\\"[\s\S]{0,200}?\\"deliveryPrice\\":(\d+|null)/g;
    let m;
    while ((m = re.exec(h))) {
      const price = num(m[3]);
      let ship = m[6] === 'null' ? null : num(m[6]);
      if (ship === null && /무료/.test(m[4])) ship = 0;
      const key = m[2] + '|' + price;
      if (!m[1] || !price || seen.has(key)) continue;
      seen.add(key);
      rows.push({ mall: m[1], price, ship, total: price + (ship || 0), link: m[5].replace(/\\u0026/g, '&') });
    }
  }
  const lo2 = h.match(/metaLowestPrice\\?":(\d+)/);
  const oc2 = h.match(/\\"productCode\\":(\d+),\\"name\\":\\"[^"\\]*\\",\\"minPrice\\":\d+,\\"shopCount\\":(\d+)/g);
  let offers = oc ? num(oc[1]) : null;
  if (offers === null && oc2) for (const t of oc2) { const k = t.match(/productCode\\":(\d+)[\s\S]*shopCount\\":(\d+)/); if (k && k[1] === String(pcode)) offers = num(k[2]); }
  rows.sort((a, b) => a.total - b.total);
  return { pcode, name: nm ? nm[1] : strip((h.match(/<title>([\s\S]*?)<\/title>/) || [])[1]).replace(/\s*:\s*다나와.*$/, ''), low: lo ? num(lo[1]) : (lo2 ? num(lo2[1]) : null), offers, img: im ? im[0] + '?shrink=330:330' : '', page: 'https://prod.danawa.com/info/?pcode=' + pcode, rows };
}

// ── 당근 검색 → 중고 글
function cutArray(h, key) {   // "key":[ ... ] 를 문자열 안팎을 구분해 잘라낸다
  const i = h.indexOf('"' + key + '":[');
  if (i < 0) return null;
  let j = i + key.length + 3, dep = 0, str = false;
  for (let k = j; k < h.length && k < j + 3000000; k++) {
    const c = h.charCodeAt(k);
    if (str) { if (c === 92) k++; else if (c === 34) str = false; continue; }
    if (c === 34) str = true;
    else if (c === 91 || c === 123) dep++;
    else if (c === 93 || c === 125) { dep--; if (dep === 0) return h.slice(j, k + 1); }
  }
  return null;
}
export function parseDaangn(h) {
  const out = [];
  try {
    const a = JSON.parse(cutArray(h, 'buySellArticles') || '[]');
    for (const x of a) {
      const p = num(x.price);
      if (!x.title || !x.href) continue;
      out.push({ src: '당근', title: x.title, price: p, ship: null, region: (x.region && x.region.name) || '', date: (x.createdAt || '').slice(0, 10), ok: x.status === 'Ongoing', link: 'https://www.daangn.com' + x.href, body: (x.content || '').slice(0, 300) });
    }
  } catch (e) { /* 아래 예비 경로 */ }
  if (out.length) return out;
  const re = /"@type":"Product","name":"((?:[^"\\]|\\.)*)","description":"((?:[^"\\]|\\.)*)"[\s\S]{0,700}?"url":"([^"]+)","offers":\{"@type":"Offer","price":"([\d.]+)"[^}]*?"availability":"https:\/\/schema\.org\/(\w+)"/g;
  let m;
  while ((m = re.exec(h))) {
    let t = m[1], d = m[2];
    try { t = JSON.parse('"' + t + '"'); d = JSON.parse('"' + d + '"'); } catch (e) { /* 그대로 */ }
    out.push({ src: '당근', title: t, price: num(m[4].split('.')[0]), ship: null, region: '', date: '', ok: m[5] === 'InStock', link: m[3], body: d.slice(0, 300) });
  }
  return out;
}

// ── 중고나라 검색 → 중고 글
export function parseJoongna(h) {
  const out = [], seen = new Set();
  const re = /\{\\"seq\\":(\d+),\\"productPositionNo\\":\d+,\\"platformType\\":\d+,\\"price\\":(\d+),\\"parcelFee\\":(\d+),\\"url\\":\\"[^"]*?\\",\\"title\\":\\"([\s\S]*?)\\",\\"state\\":(\d+),\\"sortDate\\":\\"([^"\\]*)\\",\\"mainLocationName\\":\\"([^"\\]*)\\"/g;
  let m;
  while ((m = re.exec(h))) {
    if (seen.has(m[1])) continue;
    seen.add(m[1]);
    let t = m[4];
    try { t = JSON.parse('"' + JSON.parse('"' + t + '"') + '"'); } catch (e) { t = t.replace(/\\+"/g, '"').replace(/\\+u0026/g, '&'); }
    out.push({ src: '중고나라', title: t, price: num(m[2]), ship: null, region: m[7] || '', date: (m[6] || '').slice(0, 10), ok: m[5] === '0', link: 'https://web.joongna.com/product/' + m[1], body: '' });
  }
  return out;
}

// ── 중고 글 고르기: 제품명과 얼마나 맞는지, 「삽니다」 글·0원·판매 끝난 글 빼기
export function tokens(s) {
  return [...new Set((s || '').toLowerCase().replace(/\([^)]*\)/g, ' ').split(/[^0-9a-z가-힣]+/).filter(t => t.length >= 2))];
}
export function pickUsed(items, uq) {
  const qt = tokens(uq);
  const need = qt.length <= 2 ? qt.length : Math.ceil(qt.length * 0.6);
  const keep = [], drop = { 판매끝: 0, 가격없음: 0, 구매글: 0, 이름다름: 0 };
  for (const x of items) {
    if (!x.ok) { drop.판매끝++; continue; }
    if (!x.price || x.price < 500) { drop.가격없음++; continue; }
    if (WANT.test(x.title)) { drop.구매글++; continue; }
    const t = (x.title + ' ' + (x.body || '')).toLowerCase().replace(/\s+/g, ''), tt = x.title.toLowerCase().replace(/\s+/g, '');
    let hit = 0, hitT = 0;
    for (const k of qt) { if (t.includes(k)) hit++; if (tt.includes(k)) hitT++; }
    if (hit < need || (qt.length && hitT === 0)) { drop.이름다름++; continue; }
    keep.push({ src: x.src, title: x.title, price: x.price, region: x.region, date: x.date, link: x.link, match: qt.length ? Math.round(hit / qt.length * 100) : 100 });
  }
  keep.sort((a, b) => a.price - b.price);
  return { keep, drop };
}

async function search(q) {
  const h = await get('https://search.danawa.com/dsearch.php?query=' + encodeURIComponent(q));
  const items = parseDanawaSearch(h).slice(0, 30);
  const out = { q, items, src: 'https://search.danawa.com/dsearch.php?query=' + encodeURIComponent(q), at: Date.now() };
  if (!items.length) out.diag = { len: h.length, title: strip((h.match(/<title>([\s\S]*?)<\/title>/) || [])[1]).slice(0, 80), seq: h.split('data-product-seq="').length - 1, head: strip(h.slice(0, 3000)).slice(0, 200) };
  return out;
}

async function scan(pcode, uq, q0) {
  const errs = {}, diag = {}, out = { pcode: pcode || '', uq: uq || '', at: Date.now() };
  const jobs = [];
  if (pcode) jobs.push(get('https://prod.danawa.com/info/?pcode=' + pcode).then(h => { out.prod = parseDanawaProduct(h, pcode); diag.다나와 = [h.length, out.prod.rows.length]; }).catch(e => { errs['다나와'] = String(e.message || e); }));
  await Promise.all(jobs);
  const name = uq || (out.prod && out.prod.name) || '';
  out.uq = name.replace(/\([^)]*\)/g, ' ').replace(/\s+/g, ' ').trim();
  // 중고: 제품 이름 전체 → 앞 두 낱말(브랜드+모델) → 처음 넣은 이름 순서로 넓혀 가며, 맞는 글이 3건 이상 나오면 멈춘다(요청은 차례로, 많아야 3번)
  out.uqFull = out.uq;
  const tries = out.uq ? [out.uq] : [];
  if (pcode && !uq) {
    const w = out.uq.split(' ');
    if (w.length > 2) tries.push(w.slice(0, 2).join(' '));
    if (q0 && !tries.includes(q0)) tries.push(q0);
  }
  let pk = { keep: [], drop: {} }, seen = 0, first = true;
  for (const t of tries) {
    let r;
    try { const h = await get('https://web.joongna.com/search/' + encodeURIComponent(t)); r = parseJoongna(h); diag['중고나라 ' + t] = [h.length, r.length]; delete errs['중고나라']; }
    catch (e2) { errs['중고나라'] = String(e2.message || e2); continue; }
    const p = pickUsed(r, t);
    if (first || p.keep.length > pk.keep.length) { pk = p; seen = r.length; out.uq = t; first = false; }
    if (pk.keep.length >= 3) break;
  }
  if (out.uq) {
    const e = encodeURIComponent(out.uq);
    out.links = { 당근: 'https://www.daangn.com/kr/buy-sell/?search=' + e, 중고나라: 'https://web.joongna.com/search/' + e, 번개장터: 'https://m.bunjang.co.kr/search/products?q=' + e };
  }
  out.used = pk.keep.slice(0, 40);
  out.usedSeen = seen;
  out.usedDrop = pk.drop;
  out.errs = errs;
  out.diag = diag;
  return out;
}

function cors(req) {
  const o = req.headers.get('Origin') || '';
  return { 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0], 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'GET, OPTIONS' };
}
function json(req, body, status, extra) {
  return new Response(JSON.stringify(body), { status: status || 200, headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, cors(req), extra || {}) });
}

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(req) });
    if (req.method !== 'GET') return json(req, { error: '지원하지 않는 요청입니다.' }, 405);
    if (u.pathname === '/api/price/health') return json(req, { ok: true });
    const q = (u.searchParams.get('q') || '').replace(/\s+/g, ' ').trim().slice(0, 60);
    const uq = (u.searchParams.get('uq') || '').replace(/\s+/g, ' ').trim().slice(0, 60);
    const pcode = (u.searchParams.get('pcode') || '').trim();
    let key, run;
    if (u.pathname === '/api/price/search') {
      if (q.length < 2) return json(req, { error: '찾을 물건 이름을 두 글자 이상 적어 주세요.' }, 400);
      key = 's|' + q; run = () => search(q);
    } else if (u.pathname === '/api/price/scan') {
      if (pcode && !/^\d{3,12}$/.test(pcode)) return json(req, { error: '제품 코드가 올바르지 않습니다.' }, 400);
      if (!pcode && uq.length < 2) return json(req, { error: '제품 코드나 검색어가 필요합니다.' }, 400);
      key = 'c|' + pcode + '|' + uq + '|' + (pcode && !uq ? q : ''); run = () => scan(pcode, uq, q);
    } else return json(req, { error: '없는 주소입니다.' }, 404);
    const ck = new Request('https://price-cache.local/' + VER + '/' + encodeURIComponent(key));
    const cache = caches.default;
    try {
      const hit = await cache.match(ck);
      if (hit) return new Response(hit.body, { headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8', 'X-Price-Cache': 'hit' }, cors(req)) });
    } catch (e) { /* 저장소를 못 쓰면 바로 조회 */ }
    try {
      const body = await run();
      const good = body.items ? body.items.length > 0 : ((body.prod && body.prod.rows.length) || (body.used && body.used.length));
      if (good) ctx.waitUntil(cache.put(ck, new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=' + TTL } })).catch(() => {}));
      return json(req, body, 200, { 'X-Price-Cache': 'miss' });
    } catch (e) {
      return json(req, { error: '가격 정보를 가져오지 못했습니다. 잠시 뒤 다시 시도해 주세요.', why: String(e.message || e).slice(0, 80) }, 502);
    }
  },
};
