// 테마별 루리 챗봇 (2026-10-18 사용자: "챗봇도 최적화") — 이슈·머니·생활·메인 허브. 공모전 테마는 기존 ruri-chat.js 그대로.
// 브라우저 안에서만 동작(모델 없음). 데이터는 패널을 처음 열 때만 불러온다.
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
const J = u => fetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const G = { ok: '✅', warn: '🟡', bad: '🔴' };
const won = v => !v ? '' : v >= 1e8 ? (v / 1e8).toFixed(2) + '억 원' : v >= 1e4 ? Math.floor(v / 1e4).toLocaleString() + '만' + (v % 1e4 ? ' ' + (v % 1e4).toLocaleString() : '') + ' 원' : v.toLocaleString() + '원';

const CONF = {
  hub: { av: '/assets/ruri/avatar.webp', fab: '루리에게 물어보기', sub: '뭘 찾는지 말하면 길을 안내해요', ph: '예) 비트코인, 마감 임박 공모전, 오늘 이슈' },
  issue: { av: '/assets/ruri/o_det_wave_s.webp', fab: '루리 탐정에게 물어보기', sub: '오늘 이슈·기사 확인 신호를 알려 드려요', ph: '예) 국무회의, 의심 기사, 커뮤니티' },
  money: { av: '/assets/ruri/o_present_s.webp', fab: '루리에게 시세·의견 묻기', sub: '증권사·전문가 의견을 정리해 드려요 · 투자 권유 아님', ph: '예) 비트코인, 카카오, 상향 종목' },
  life: { av: '/assets/ruri/o_cook_s.webp', fab: '루리에게 생활 정보 묻기', sub: '지원금·청약·경품·오늘 메뉴', ph: '예) 청년 월세, 부산 지원금, 경품' }
};

export function start(th) {
  const C = CONF[th]; if (!C) return;
  const root = document.createElement('div'); root.className = 'rc rc-' + th;
  root.innerHTML = `<button class="rc-fab" aria-label="${esc(C.fab)}"><img src="${C.av}" alt=""><span>${esc(C.fab)}</span></button>
<section class="rc-panel" hidden aria-label="루리 챗봇"><header><img src="${C.av}" alt=""><div><b>루리</b><small>${esc(C.sub)}</small></div><button class="rc-x rc-ic" aria-label="닫기">✕</button></header>
<div class="rc-log" role="log" aria-live="polite"></div><form class="rc-in"><input placeholder="${esc(C.ph)}" aria-label="질문"><button class="rc-go">보내기</button></form></section>`;
  document.body.appendChild(root);
  const $ = s => root.querySelector(s), log = $('.rc-log'), panel = $('.rc-panel'), input = $('input');
  const add = (who, html) => { const b = document.createElement('div'); b.className = 'rc-m ' + who; b.innerHTML = html; log.appendChild(b); log.scrollTop = log.scrollHeight; return b; };
  const chips = (b, list) => { const w = document.createElement('div'); w.className = 'rc-chips'; list.forEach(([t, f]) => { const x = document.createElement('button'); x.type = 'button'; x.textContent = t; x.onclick = () => { ga('chat_menu', { theme: th, label: t.replace(/[^\p{L}\p{N} ]/gu, '').trim().slice(0, 30) }); w.remove(); add('me', esc(t)); f(); }; w.appendChild(x); }); b.appendChild(w); log.scrollTop = log.scrollHeight; };
  const say = (html, next) => { const b = add('bot', html); if (next) chips(b, next); return b; };
  const list = items => `<ul class="tb-l">${items.map(x => `<li><a href="${esc(x.u)}"${x.ext ? ' target="_blank" rel="noopener nofollow"' : ''}><b>${esc(x.t)}</b>${x.m ? `<small>${x.m}</small>` : ''}</a></li>`).join('')}</ul>`;
  let D = null;
  const B = { menu: null };
  const back = () => [['🏠 처음 메뉴', () => B.menu()]];

  // ---------------- 메인 허브: 길 안내
  if (th === 'hub') {
    B.load = async () => { const [n, a] = await Promise.all([J('/news/data.json'), J('/analyst/data.json')]); D = { n, a }; };
    B.menu = () => say('어떤 정보를 찾으세요?', [['🕵️ 오늘 이슈', () => { const i = (D.n?.issues || [])[0]; say(i ? `지금 가장 많이 보도된 이슈는 <b>${esc(i.t)}</b> (${i.on}곳)이에요.` + list([{ t: '이슈 감별 전체 보기', u: '/news/' }]) : '이슈를 불러오지 못했어요.', back()); }],
      ['📊 코인·주식 의견', () => { const c = (D.a?.coins || []).find(x => x.sym === 'BTC'); say((c && c.price ? `비트코인은 지금 ${c.price.p.toLocaleString()}원, 최근 7일 전망 기사는 강세 ${c.bull} · 약세 ${c.bear}이에요. ` : '') + list([{ t: '애널리스트 종합 보기', u: '/analyst/' }]) + '<small class="tb-n">투자 권유가 아니에요.</small>', back()); }],
      ['🏆 공모전 추천', () => say('질문 몇 개면 딱 맞는 공모전을 골라 드려요.' + list([{ t: '루리 공모전 추천 상담', u: '/contest/' }]), back())],
      ['🍳 지원금·경품·오늘 메뉴', () => say(list([{ t: '지원금·청약', u: '/apply/' }, { t: '경품 이벤트', u: '/event/' }, { t: '냉장고 파먹기', u: '/fridge/' }]), back())]]);
    B.ask = q => /코인|비트|이더|주식|목표가|종목|증권/.test(q) ? (location.href = '/analyst/') : /공모|대회|상금|응모/.test(q) ? (location.href = '/contest/') : /지원금|청약|월세|경품|이벤트|메뉴|요리/.test(q) ? (location.href = '/apply/') : (location.href = '/news/');
  }

  // ---------------- 이슈: 탐정 루리
  if (th === 'issue') {
    B.load = async () => { const [n, t, k] = await Promise.all([J('/news/data.json'), J('/talk/data.json'), J('/kw/archive/' + kst() + '.json')]); D = { n: n || { issues: [], items: [] }, t: t || { issues: [] }, k: k || [] }; };
    const iss = x => ({ t: x.t, u: '/news/#is' + x.n, m: `${x.on}곳 보도 · ${G[x.cf && x.cf.length ? 'bad' : x.g] || ''} ${x.s ?? ''}점${x.claim ? ' · 🗣️ 발언·주장' : ''}` });
    B.menu = () => say('무엇을 알아볼까요?', [
      ['🔥 오늘 이슈 TOP5', () => say('여러 언론사가 가장 많이 다룬 이슈예요.' + list(D.n.issues.slice(0, 5).map(iss)), back())],
      ['🏛️ 정치 이슈', () => say('정치 이슈예요. 「발언·주장」 표시는 말한 건 사실이지만 내용은 따로 확인이 필요하다는 뜻이에요.' + list(D.n.issues.filter(x => x.c === '정치').slice(0, 5).map(iss)), back())],
      ['🔴 확인이 필요한 기사', () => { const L = D.n.items.filter(a => a.g === 'bad').slice(0, 6); say(L.length ? '출처가 약하거나 제목과 본문이 안 맞는 기사예요.' + list(L.map(a => ({ t: a.t, u: a.u, ext: 1, m: `${esc(a.o)} · ${a.s}점 · ${esc((a.why || []).filter(w => /❌|⚠️|🎣/.test(w))[0] || '')}` }))) : '지금은 크게 의심되는 기사가 없어요.', back()); }],
      ['💬 커뮤니티 화제', () => say('여러 커뮤니티에 동시에 뜬 화제예요(사실 확인 전).' + list(D.t.issues.slice(0, 5).map(x => ({ t: x.t, u: '/talk/#t' + x.n, m: `${x.nsite}곳 · 댓글 ${x.nc.toLocaleString()}${x.news ? ' · 📰 언론 보도' : ' · 언론 미확인'}` }))), back())],
      ['🔎 인기 키워드', () => say(D.k.length ? '지금 검색이 확 늘어난 키워드예요.' + list(D.k.slice(0, 8).map(x => ({ t: x.k, u: '/kw/' + encodeURIComponent(x.slug) + '/', m: '검색량 ' + esc(x.traffic || '') }))) : '오늘 키워드를 아직 못 모았어요.', back())],
      ['❓ 점수는 어떻게 매겨요?', () => say('여러 언론사가 같이 보도했는지, 출처가 실명인지, 제목의 숫자·인용이 본문에 있는지, 낚시 표현이 있는지로 매긴 <b>확인 신호</b>예요. 사실을 최종 판정한 건 아니에요.', back())]]);
    B.ask = q => {
      const w = q.replace(/\s+/g, ''), hit = D.n.issues.filter(x => x.t.replace(/\s+/g, '').includes(w) || w.split('').length > 1 && q.split(/\s+/).every(t => x.t.includes(t)));
      const arts = D.n.items.filter(a => q.split(/\s+/).every(t => a.t.includes(t))).slice(0, 5);
      if (hit.length) return say(`「${esc(q)}」 관련 이슈예요.` + list(hit.slice(0, 5).map(iss)), back());
      if (arts.length) return say(`「${esc(q)}」 관련 기사예요.` + list(arts.map(a => ({ t: a.t, u: a.u, ext: 1, m: `${esc(a.o)} · ${G[a.g] || ''} ${a.s ?? ''}점` }))), back());
      say(`「${esc(q)}」 관련 이슈는 아직 없어요. 다른 걸 물어보세요!`, back());
    };
  }

  // ---------------- 머니: 증권사·전문가 의견 정리
  if (th === 'money') {
    B.load = async () => { D = await J('/analyst/data.json') || { stocks: [], coins: [] }; };
    const NOTE = '<small class="tb-n">증권사·전문가 의견을 정리한 거예요. 투자 권유가 아니에요.</small>';
    const coin = c => say(`<b>${esc(c.name)}</b> ${c.price ? `업비트 ${c.price.p.toLocaleString()}원 (${c.price.chg >= 0 ? '+' : ''}${c.price.chg}%)` : ''}<br>최근 7일 전망 기사: 🟢 강세 ${c.bull} · ⚪ 혼조 ${c.neutral} · 🔴 약세 ${c.bear}`
      + list([{ t: c.name + ' 전망 종합 · 차트 보기', u: '/analyst/coin/' + c.sym.toLowerCase() + '/' }]) + NOTE, back());
    const stk = s => ({ t: s.name, u: '/analyst/s/' + s.id + '/', m: `증권사 ${s.nb}곳 · 🔺${s.up} 🔻${s.down} ➖${s.keep}${s.tp_avg ? ' · 평균 목표가 ' + won(s.tp_avg) : ''}` });
    B.menu = () => say('무엇이 궁금하세요?', [
      ['🪙 비트코인', () => coin(D.coins.find(c => c.sym === 'BTC'))], ['🪙 이더리움', () => coin(D.coins.find(c => c.sym === 'ETH'))],
      ['🔺 목표가 올린 종목', () => say('최근 30일 증권사가 목표가를 올린 종목이에요.' + list(D.stocks.filter(s => s.up > s.down).slice(0, 6).map(stk)) + NOTE, back())],
      ['🔻 목표가 내린 종목', () => say('목표가를 내린 종목이에요.' + list(D.stocks.filter(s => s.down > s.up).slice(0, 6).map(stk)) + NOTE, back())],
      ['⚖️ 의견 엇갈린 종목', () => { const L = D.stocks.filter(s => s.mixed); say(L.length ? '증권사끼리 의견이 엇갈린 종목이에요.' + list(L.slice(0, 6).map(stk)) + NOTE : '지금은 의견이 엇갈린 종목이 없어요.', back()); }],
      ['❓ 이거 사도 돼요?', () => say('루리는 남들이 낸 전망을 모아 정리만 해요. 사고팔지는 본인이 판단해야 해요. 대신 근거별로 어느 증권사가 뭐라고 했는지는 다 보여 드릴게요!', back())]]);
    B.ask = q => {
      const c = D.coins.find(c => q.includes(c.name) || q.toUpperCase().includes(c.sym)); if (c) return coin(c);
      const s = D.stocks.filter(s => q.includes(s.name) || s.name.includes(q.trim()));
      if (s.length) return say('찾은 종목이에요.' + list(s.slice(0, 5).map(stk)) + NOTE, back());
      say(`「${esc(q)}」 관련 리포트는 최근 30일엔 없었어요. 매시간 새 리포트를 모으고 있어요.`, back());
    };
  }

  // ---------------- 생활: 지원금·청약·경품·오늘 메뉴
  if (th === 'life') {
    B.load = async () => { const [a, e, r] = await Promise.all([J('/apply.json'), J('/events.json'), J('/assets/fridge/recipes.json')]); D = { a: a || [], e: e || [], r: r || { recipes: [] } }; };
    const today = kst(), ap = x => ({ t: x.title, u: '/a/' + x.id + '/', m: `${esc(x.kind || '')}${x.end ? ' · ~' + x.end.slice(5).replace('-', '/') : ''}` });
    const find = q => { const ws = q.split(/\s+/).filter(Boolean); return D.a.filter(x => (!x.end || x.end >= today) && ws.every(w => (x.title + ' ' + (x.org || '') + ' ' + (x.region || '') + ' ' + (x.target || '')).includes(w))); };
    B.menu = () => say('무엇을 찾아 드릴까요?', [
      ['💰 지원금 찾기', () => { say('찾는 말이나 지역을 적어 주세요. 예) <b>청년 월세</b>, <b>부산</b>, <b>출산</b>'); }],
      ['🏠 청약 일정', () => say('곧 마감하는 청약이에요.' + list(D.a.filter(x => /청약|임대/.test(x.kind || '') && x.end >= today).sort((a, b) => a.end.localeCompare(b.end)).slice(0, 6).map(ap)), back())],
      ['🎁 쉬운 경품', () => say('응모만·댓글 한 줄이면 되는 이벤트예요.' + list(D.e.filter(x => /응모만|댓글 1줄|폼 1분/.test(x.ez || '') && x.end >= today).slice(0, 6).map(x => ({ t: x.title, u: x.link, ext: 1, m: `${esc(x.org || '')} · ${esc(x.ez || '')}` }))), back())],
      ['🍳 오늘 뭐 먹지?', () => { const R = D.r.recipes, x = R[(new Date().getDate() * 7) % R.length]; say(x ? `오늘은 <b>${esc(x.n)}</b> 어때요? ${x.m}분이면 돼요. 재료: ${esc(x.need.join(', '))}` + list([{ t: '냉장고 재료로 다른 메뉴 찾기', u: '/fridge/' }]) : '', back()); }]]);
    B.ask = q => { const L = find(q); say(L.length ? `「${esc(q)}」로 찾은 지원금·청약 ${L.length}건이에요.` + list(L.slice(0, 6).map(ap)) : `「${esc(q)}」로 찾은 게 없어요. 더 짧게 적어 보세요(예: 월세, 청년).`, back()); };
  }

  const open = async () => { ga('chat_open', { theme: th, page: location.pathname }); await B.load(); add('bot', th === 'issue' ? '루리 탐정이에요! 오늘 이슈를 같이 살펴볼까요?' : '안녕하세요, 루리예요!'); B.menu(); };
  $('.rc-fab').onclick = () => { panel.hidden = !panel.hidden; if (!panel.hidden && !log.children.length) open(); };
  $('.rc-x').onclick = () => { panel.hidden = true; };
  $('form').onsubmit = async e => { e.preventDefault(); const q = input.value.trim(); if (!q) return; input.value = ''; add('me', esc(q)); ga('chat_ask', { theme: th, q: q.slice(0, 40) }); if (!D) await B.load(); B.ask(q); };
}
