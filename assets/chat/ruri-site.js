// 루리 챗봇 — 사이트 전체 두뇌 (2026-10-20 「챗봇도 고도화」): 모델 없이 브라우저에서 동작
//  의도 분류 → 오늘 마감·지원금·경품·레시피(냉장고 재료로 찾기)·웹툰/애니·계산기·이슈·게임 → 카드 답, 못 알아듣으면 사이트 검색(2,900쪽 색인)
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const J = {}; const jget = (u, ttl) => (J[u] ||= fetch(u, { cache: ttl ? 'default' : 'no-cache' }).then(r => r.json()).catch(() => null));
const KST = () => new Date(Date.now() + 324e5);
const dleft = end => Math.round((Date.UTC(+end.slice(0, 4), +end.slice(5, 7) - 1, +end.slice(8, 10)) - Date.UTC(KST().getUTCFullYear(), KST().getUTCMonth(), KST().getUTCDate())) / 864e5);
const ddl = n => n <= 0 ? 'D-DAY' : 'D-' + n;
const slug = n => n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, '');
const card = (href, title, sub, img, tag, ext) => `<a class="rc-sc" href="${esc(href)}"${ext ? ' target="_blank" rel="noopener nofollow"' : ''}>${img ? `<img src="${esc(img)}" alt="" loading="lazy" width="56" height="56">` : `<span class="rc-si">${tag || '📄'}</span>`}<span class="rc-st"><b>${esc(title)}</b><small>${esc(sub || '')}</small></span></a>`;
const list = a => '<div class="rc-sl">' + a.join('') + '</div>';

// ── 의도 ──
const INTENT = [
  ['today', /오늘.*(마감|뭐\s*있|할\s*거)|마감.*(임박|오늘|급한)|급한\s*것/],
  ['support', /지원금|청약|정책|혜택|월세|바우처|보조금|신혼|청년.*(지원|도약)|복지/],
  ['event', /경품|이벤트|추첨|응모권|래플|용돈/],
  ['webtoon', /웹툰|만화|웹소설/],
  ['anime', /애니|애니메이션|라프텔|극장판/],
  ['recipe', /뭐\s*먹|메뉴|레시피|요리|밥\s*뭐|냉장고|야식|점심|저녁|아침|반찬|끓이|만드는\s*법|있어\s*요?$|있는데|남았/],
  ['money', /연봉|실수령|월급|퇴직금|실업급여|세금|계산기|연말정산|주휴|연차/],
  ['issue', /이슈|뉴스|핫|화제|속보|요즘\s*뭐/],
  ['game', /게임|스팀|에픽|무료\s*배포/],
  ['contest', /공모전|대회|상금|슬로건|네이밍|공모/],
  ['hello', /^(안녕|하이|ㅎㅇ|헬로|hi|hello|루리)|뭐 ?할 ?수|도와|기능|무엇을/i],
];
export function intentOf(q) { for (const [k, re] of INTENT) if (re.test(q)) return k; return ''; }

// ── 답 ──
async function today() {
  const [c, e, a] = await Promise.all([jget('/data.json'), jget('/events.json'), jget('/apply.json')]);
  const rows = [];
  (c?.items || []).forEach(x => { const n = dleft(x.end); if (n >= 0 && n <= 3) rows.push([n, card('/c/' + x.id + '/', x.title, `공모전 · ${ddl(n)} · ${x.prize || ''}`, '', '🏆')]); });
  (Array.isArray(e) ? e : e?.items || []).forEach(x => { const n = dleft(x.end); if (n >= 0 && n <= 1 && x.org) rows.push([n, card(x.link, x.title.slice(0, 40), `경품 · ${ddl(n)} · ${x.org}`, '', '🎁', 1)]); });
  (Array.isArray(a) ? a : a?.items || []).forEach(x => { if (x.end && !x.always) { const n = dleft(x.end); if (n >= 0 && n <= 2) rows.push([n, card(x.url, x.title.slice(0, 40), `${x.kind || '지원금'} · ${ddl(n)}`, '', '📋', 1)]); } });
  rows.sort((p, q) => p[0] - q[0]);
  if (!rows.length) return { html: '지금은 3일 안에 마감하는 게 없어요. <a href="/contest/week/">이번 주 마감</a>을 볼까요?', say: '지금은 급한 마감이 없어요.' };
  return { html: `오늘·내일 급한 마감 <b>${rows.length}건</b>이에요! ⏰` + list(rows.slice(0, 6).map(r => r[1])) + '<a class="rc-more" href="/#today">홈에서 전체 보기 →</a>', say: `급한 마감이 ${rows.length}건 있어요.` };
}
async function support(q) {
  const a = await jget('/apply.json'); const L = (Array.isArray(a) ? a : a?.items || []).filter(x => x.end && !x.always && dleft(x.end) >= 0);
  const kw = (q.match(/월세|청약|신혼|청년|주거|임대|출산|육아|창업|취업/g) || []);
  const hit = x => kw.filter(k => (x.title + ' ' + (x.kind || '')).includes(k)).length;
  let P = kw.length ? L.filter(x => hit(x) > 0) : L;
  if (!P.length) P = L; P.sort((p, r) => hit(r) - hit(p) || p.end.localeCompare(r.end));
  return { html: `${kw.length ? kw.join('·') + ' 관련 ' : ''}신청 가능한 지원금·청약이에요. 마감 임박순이에요.` + list(P.slice(0, 5).map(x => card(x.url, x.title.slice(0, 44), `${x.kind || ''} · ${ddl(dleft(x.end))} · ${x.org || ''}`, '', x.icon || '📋', 1))) + '<a class="rc-more" href="/apply/">지원금·청약 전체 →</a> <a class="rc-more" href="/money/policy/">정책 모음 →</a>', say: '신청 가능한 지원금을 마감 임박순으로 보여 드려요.' };
}
async function event() {
  const e = await jget('/events.json'); const L = (Array.isArray(e) ? e : e?.items || []).filter(x => x.org && dleft(x.end) >= 0).sort((p, r) => p.end.localeCompare(r.end) || ((p.effort || 'z') > (r.effort || 'z') ? 1 : -1));
  return { html: '오늘 마감하는 쉬운 경품 이벤트예요! 🎁' + list(L.slice(0, 5).map(x => card(x.link, x.title.slice(0, 44), `${ddl(dleft(x.end))} · ${x.org} · ${x.effort || ''}`, '', '🎁', 1))) + '<a class="rc-more" href="/event/">전체 이벤트 →</a>', say: '오늘 마감하는 경품 이벤트예요.' };
}
let REC = null;
async function recData() { if (REC) return REC; const d = await jget('/assets/fridge/rec.json?v=' + KST().toISOString().slice(0, 10), 1); const pop = (await jget('/assets/fridge/rec_pop.json')) || {}; REC = { d, pop }; return REC; }
const ALIAS = { 계란: '달걀', 파: '대파', 돼지: '돼지고기', 소: '소고기', 닭: '닭고기', 참치: '참치캔', 라면사리: '라면', 스파게티: '파스타면', 파스타: '파스타면', 소면: '국수', 햄: '햄', 만두: '만두' };
export async function recipe(q) {
  const { d, pop } = await recData(); if (!d) return { html: '레시피 목록을 불러오지 못했어요. <a href="/fridge/">냉장고 파먹기</a>로 가 볼까요?' };
  const names = new Set(); d.r.forEach(x => x[7].concat(x[8]).forEach(g => names.add(g)));
  const have = [...new Set((q.match(/[가-힣]{1,6}/g) || []).map(w => ALIAS[w] || w).filter(w => names.has(w)))];
  let rows;
  if (have.length) {
    rows = d.r.map(x => { const need = x[7], miss = need.filter(g => !have.includes(g)), used = need.length - miss.length + x[8].filter(g => have.includes(g)).length; return { x, miss, used }; })
      .filter(o => o.used > 0).sort((a, b) => a.miss.length - b.miss.length || b.used - a.used || (b.x[6] - a.x[6])).slice(0, 5);
  } else {
    const h = KST().getUTCHours(); const want = h < 10 ? ['가벼움'] : h < 15 ? ['든든'] : h < 21 ? ['든든'] : ['안주', '간식'];
    rows = d.r.map(x => ({ x, miss: [], used: 0, sc: (x[6] ? 1 : 0) + ((pop[slug(x[0])] || [0])[0] > 0 ? 1.5 : 0) + (x[4].some(i => want.includes(d.tags[i])) ? 1 : 0) + ((x[0].length * 7 + KST().getUTCDate() * 13) % 10) / 10 })).sort((a, b) => b.sc - a.sc).slice(0, 5);
  }
  const head = have.length ? `${have.join('·')}(으)로 만들 수 있는 메뉴예요. 부족한 재료가 적은 순서예요 🍳` : '지금 시간에 어울리는 메뉴를 골라 봤어요 🍽️ 재료를 말해 주면(예: “김치 달걀 있어”) 만들 수 있는 걸 찾아 드려요.';
  return { html: head + list(rows.map(o => card('/fridge/r/' + slug(o.x[0]) + '/', o.x[0], `${o.x[2]}분 · ${o.miss.length ? '추가 재료 ' + o.miss.join(', ') : '바로 가능'}`, o.x[6] ? '/assets/fridge/ph/t/' + slug(o.x[0]) + '.webp' : '', o.x[1]))) + '<a class="rc-more" href="/fridge/">냉장고 재료로 더 찾기 →</a> <a class="rc-more" href="/fridge/plan/">식단·장보기 →</a>', say: head.replace(/[🍳🍽️]/gu, '') };
}
async function watch(kind, q) {
  const st = (() => { try { return JSON.parse(localStorage.getItem('jupjup_watch_' + kind) || 'null'); } catch { return null; } })();
  const d = await jget('/assets/watch/' + kind + '.json?v=' + KST().toISOString().slice(0, 10), 1);
  const L = '/watch/#' + kind;
  if (!d) return { html: `<a class="rc-more" href="${L}">${kind === 'anime' ? '애니' : '웹툰'} 추천 페이지로 가기 →</a>` };
  const gm = (d.cfg.genres || []).filter(g => q.includes(g[1] || g[0]) || q.includes(g[0])).map(g => g[0]);
  const pick = d.r.filter(x => (kind === 'webtoon' ? !x[11] : true)).map(x => { const tg = kind === 'webtoon' ? x[4] : x[4].concat(x[5]); const m = gm.filter(g => tg.includes(g)).length; return { x, s: (gm.length ? m * 3 : 0) + (kind === 'webtoon' ? (x[6] || 0) - 8.5 + Math.log(1 + (x[7] || 0)) / 8 : (x[6] || 60) / 50 + Math.log(1 + (x[7] || 0)) / 8) + ((x[0] * 31 + KST().getUTCDate()) % 10) / 10 }; }).filter(o => !gm.length || o.s > 2).sort((a, b) => b.s - a.s).slice(0, 4);
  const mk = o => kind === 'webtoon' ? card('https://comic.naver.com/webtoon/list?titleId=' + o.x[0], o.x[1], `${o.x[8] ? '완결' : '연재'} · ★${(o.x[6] || 0).toFixed(1)} · ${(o.x[4] || []).slice(0, 2).join('·')}`, o.x[3], '📖', 1) : card(o.x[16], o.x[1] || o.x[3] || o.x[2], `${o.x[10] || ''} · ★${((o.x[6] || 0) / 10).toFixed(1)} · ${o.x[4].slice(0, 2).join('·')}`, o.x[14], '🎬', 1);
  return { html: `${gm.length ? gm.join('·') + ' 취향으로 ' : ''}${kind === 'anime' ? '애니' : '웹툰'} 골라 봤어요 ✨` + list(pick.map(mk)) + `<a class="rc-more" href="${L}">1분 취향 설문으로 더 정확하게 →</a>`, say: '취향에 맞는 작품을 골라 봤어요.' };
}
const MONEY = [['연봉 실수령액 계산기', '/money/tools/salary/', '🧮'], ['실업급여 계산기', '/money/tools/unemployment/', '🧮'], ['퇴직금 계산기', '/money/tools/severance/', '🧮'], ['청약 가점 계산기', '/apply/recommend/', '🏠'], ['생활 돈 가이드', '/money/guide/', '🧭']];
function money(q) {
  const pri = /실업/.test(q) ? 1 : /퇴직/.test(q) ? 2 : /청약/.test(q) ? 3 : /가이드|주휴|연차/.test(q) ? 4 : 0;
  const L = MONEY.slice(); const f = L.splice(pri, 1)[0]; L.unshift(f);
  return { html: '계산기·가이드를 모아 놨어요 🧮' + list(L.slice(0, 4).map(m => card(m[1], m[0], '2026 기준', '', m[2]))), say: '계산기를 모아 놨어요.' };
}
const SIMPLE = {
  issue: { html: '이슈는 여러 언론을 한 번에 묶어서 보여 드려요 📺' + list([card('/news/#brief', '오늘의 브리핑', '언론사별 기사 확인 신호', '', '📺'), card('/hot/', '핫이슈', '여러 곳에서 동시에 뜬 이슈', '', '🔥'), card('/kw/', '인기 키워드', '지금 검색이 몰리는 말', '', '🔎')]), say: '이슈 페이지를 골라 보세요.' },
  game: { html: '무료 게임·세일 소식이에요 🎮' + list([card('/game/free/', '이번 주 무료 게임', '스팀·에픽 무료 배포', '', '🎮'), card('/game/steam-sale/', '스팀 세일', '할인 정보', '', '🏷️')]), say: '무료 게임 소식이에요.' },
};
// ── 사이트 검색 ──
async function siteSearch(q) {
  const d = await jget('/assets/finder/index.json', 1); const docs = d?.docs || [];
  const ws = (q.toLowerCase().match(/[가-힣a-z0-9]{2,}/g) || []).filter(w => !/^(알려|보여|뭐야|있어|어떻게|해줘|좀|추천)$/.test(w));
  if (!ws.length) return null;
  const need = ws.length <= 2 ? ws.length : 2;
  const sc = docs.map(x => { const t = (x.t || '').toLowerCase(), b = (x.x || '').toLowerCase(); let s = 0, hit = 0; ws.forEach(w => { const a = t.includes(w), c = b.includes(w); if (a || c) hit++; if (a) s += 3; if (c) s += 1; }); return [hit >= need ? s : 0, x]; }).filter(a => a[0] > 0).sort((a, b) => b[0] - a[0]).slice(0, 4);
  if (!sc.length) return null;
  return { html: `“${esc(q.slice(0, 20))}” 관련 페이지를 찾았어요 🔎` + list(sc.map(([, x]) => card(x.u, (x.t || '').replace(/\s*[—|·]\s*루리의.*$/, '').slice(0, 48), (x.l || '').replace(/^\S+\s/, ''), '', (x.l || '📄').split(' ')[0]))), say: '관련된 페이지를 찾았어요.' };
}
export async function siteAnswer(q) {
  const k = intentOf(q);
  if (k === 'today') return await today();
  if (k === 'support') return await support(q);
  if (k === 'event') return await event();
  if (k === 'recipe') return await recipe(q);
  if (k === 'webtoon' || k === 'anime') return await watch(k, q);
  if (k === 'money') return money(q);
  if (SIMPLE[k]) return SIMPLE[k];
  if (k === 'contest') return null;                     // 공모전은 기존 시나리오·검색이 더 정확
  if (k === 'hello') return { html: '안녕하세요, 루리예요! 😊 공모전·지원금·경품 마감부터 오늘 뭐 먹지, 웹툰·애니 추천까지 도와드려요. 아래에서 골라 보세요.', menu: true, say: '안녕하세요, 루리예요.' };
  // 재료 문장("김치 달걀 있어") 감지
  const { d } = await recData(); if (d) { const names = new Set(); d.r.forEach(x => x[7].forEach(g => names.add(g))); const hit = (q.match(/[가-힣]{1,6}/g) || []).map(w => ALIAS[w] || w).filter(w => names.has(w)); if (hit.length >= 1 && q.length <= 24) return await recipe(q); }
  return (await siteSearch(q)) || { html: '음, 그건 잘 모르겠어요 😅 이런 건 도와드릴 수 있어요: 오늘 마감, 지원금·청약, 경품 이벤트, 오늘 뭐 먹지(재료를 말해 보세요), 웹툰·애니 추천, 계산기.', menu: true, say: '잘 모르겠어요. 메뉴에서 골라 주세요.' };
}
// 지금 보는 페이지에 맞춘 인사·버튼
export function pageHints(path) {
  if (/^\/fridge\/r\//.test(path)) return { say: '이 레시피, 같이 만들어 볼까요? 🍳', chips: [['🔊 요리 모드로 따라 하기', () => { location.href = location.pathname + '?cook=1'; }], ['📅 식단에 담기', () => { document.querySelector('.rp-minis .rp-mini:nth-child(2)')?.click(); }], ['🧊 다른 재료로 찾기', () => { location.href = '/fridge/'; }]] };
  if (/^\/fridge\/?$/.test(path)) return { say: '냉장고에 뭐가 있어요? 말해 주면 만들 수 있는 걸 찾아 드려요!', chips: [] };
  if (/^\/watch\//.test(path)) return { say: '웹툰·애니 취향 설문, 같이 해 볼까요? 장르 몇 개만 골라도 돼요.', chips: [] };
  if (/^\/apply\//.test(path)) return { say: '지원금·청약은 마감이 중요해요. 마감 임박순으로 보여 드릴까요?', chips: [['⏰ 마감 임박순', null, 'support']] };
  return null;
}
