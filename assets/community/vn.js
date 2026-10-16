// 루리의 줍줍 커뮤니티 — 미연시 모드: 공모전 = 공략 대상 히로인, 팀 = 공략 파티, 루리 = 정보통 친구
// 친구 초대(링크 방문 1점, 가입 3점, 히로인별 기록) 점수만큼 루리 꾸미기(의상·배경·대사창·효과·호칭) 해금. comm.js 의 window.JUP 사용.
(function () {
  const S = document.getElementById('vn'), J = window.JUP; if (!S || !J) return;
  const esc = J.esc, $ = s => S.querySelector(s);
  // 꾸미기 카탈로그: [필요 점수, 값, 이름]
  const CAT = {
    o: ['👗 의상', [[0, 'smile', '오피스룩'], [0, 'o_cardigan', '카디건'], [0, 'o_vest', '니트 베스트'], [0, 'o_suit', '정장'], [0, 'o_trench', '트렌치코트'], [0, 'o_gray', '그레이 셋업'], [0, 'o_anchor', '앵커룩'], [0, 'o_present', '발표 정장'], [1, 'o_summer', '여름 오피스룩'], [3, 'o_resort', '리조트 원피스'], [6, 'o_beach', '비치 커버업'], [10, 'o_swim', '수영복']]],  // 로그인하면 오피스 8벌 기본 제공, 초대 점수로 여름 단계
    b: ['🌆 배경', [[0, 'dusk', '노을 하늘'], [2, 'night', '밤 옥상'], [4, 'sakura', '벚꽃길'], [8, 'fest', '축제 불꽃'], [12, 'sea', '여름 바다'], [20, 'star', '별빛 천문대']]],
    x: ['💬 대사창', [[0, 'basic', '기본'], [3, 'mint', '민트'], [7, 'gold', '골드'], [14, 'dark', '다크'], [30, 'rainbow', '무지개']]],
    f: ['✨ 효과', [[0, 'petal', '벚꽃잎'], [5, 'heart', '하트'], [9, 'star', '반짝이'], [18, 'snow', '눈송이'], [0, 'none', '끄기']]],
  };
  const CALL_AT = 5;  // 호칭 정하기 해금 점수
  const FX = { heart: '💗', star: '✦', snow: '❄' };
  const EXP = { smile: 1, wink: 1, excited: 1, think: 1, surprise: 1, sad: 1, thumbsup: 1, serious: 1 };
  const dday = e => e ? Math.ceil((new Date(e + 'T23:59:59+09:00') - Date.now()) / 864e5) : null;
  let cs = [], tcount = new Map(), auto = false, typing = null, me = null, gen = 0;  // gen: 새 장면이 시작되면 이전 대사 흐름은 버림
  let P = (() => { try { return JSON.parse(localStorage.getItem('jupjup_prefs') || '{}'); } catch { return {}; } })();
  const pts = () => me ? (me.visits || 0) + (me.invites || 0) * 3 : 0;
  const you = () => P.c ? esc(P.c) : '너';

  // ---- 무대 ----
  S.innerHTML = `<div class="vn-bg"></div><div class="vn-petals"></div>
<img class="vn-ruri" alt="루리" width="300" height="415"><div class="vn-sys"><button data-s="auto">AUTO</button><button data-s="skip">SKIP</button><button data-s="ward">🎀 꾸미기</button></div>
<div class="vn-choices" hidden></div><div class="vn-panel" hidden></div>
<div class="vn-box"><span class="vn-name">루리</span><p class="vn-text"></p><span class="vn-next">▼</span></div>`;
  const img = $('.vn-ruri'), txt = $('.vn-text'), box = $('.vn-box'), ch = $('.vn-choices'), panel = $('.vn-panel');
  function apply() {
    S.dataset.b = P.b || 'dusk'; S.dataset.x = P.x || 'basic';
    const f = P.f || 'petal';
    $('.vn-petals').innerHTML = f === 'none' ? '' : Array.from({ length: 18 }, (_, i) => `<i class="${f}" style="--x:${(i * 37) % 100}%;--d:${6 + (i * 7) % 9}s;--w:${(i * 13) % 7}s;--s:${0.6 + (i % 5) * 0.15}">${FX[f] || ''}</i>`).join('');
    face('outfit');
  }
  function save(k, v) {
    P[k] = v; try { localStorage.setItem('jupjup_prefs', JSON.stringify(P)); } catch {} if (k === 'o' && J.wearAll) J.wearAll();
    if (J.st.t) J.api('/api/prefs', { method: 'POST', body: { data: P } }).catch(() => {});
    apply();
  }
  const face = e => { const o = J.st.t && P.o && P.o !== 'smile' ? P.o : ''; const f = o || (EXP[e] ? e : 'smile'); const src = `/assets/ruri/${f}.webp`; if (!img.src.endsWith(src)) { img.classList.remove('pop'); void img.offsetWidth; img.classList.add('pop'); img.src = src; } };

  // ---- 대사 엔진: say([[표정, 대사], ...]) → Promise ----
  function say(lines) {
    const g = ++gen;
    return lines.reduce((p, [e, t]) => p.then(() => new Promise(done => {
      if (g !== gen) return;
      face(e); ch.hidden = true; panel.hidden = true; box.classList.remove('wait');
      let i = 0; const plain = t.replace(/<[^>]+>/g, '');
      clearInterval(typing);
      const finish = () => { clearInterval(typing); typing = null; txt.innerHTML = t; box.classList.add('wait'); if (auto) setTimeout(next, 1400); };
      typing = setInterval(() => { i += 1; txt.textContent = plain.slice(0, i); if (i >= plain.length) finish(); }, 28);
      const next = () => { if (typing) return finish(); box.onclick = null; if (g === gen) done(); };
      box.onclick = next;
    })), Promise.resolve());
  }
  function choose(opts) {
    ch.innerHTML = opts.map((o, i) => `<button data-i="${i}">${o[0]}</button>`).join(''); ch.hidden = false; box.classList.remove('wait');
    ch.querySelectorAll('button').forEach(b => b.onclick = () => { ch.hidden = true; opts[+b.dataset.i][1](); });
  }
  function showPanel(html, line, expr = 'outfit') {
    gen++; panel.innerHTML = html; panel.hidden = false; ch.hidden = true; box.onclick = null; clearInterval(typing); typing = null;
    face(expr); txt.innerHTML = line; box.classList.remove('wait');
    const bk = panel.querySelector('.vn-back'); if (bk) bk.onclick = () => { panel.hidden = true; menu(); };
  }

  // ---- 장면 ----
  async function intro() {
    const first = (() => { try { return !localStorage.getItem('jupjup_vn'); } catch { return true; } })();
    try { localStorage.setItem('jupjup_vn', 1); } catch {}
    if (first) await say([['excited', '앗, 왔구나! 나 루리야. 공모전 정보라면 내가 제일 빠삭하지!'],
      ['wink', '여기 공모전들은 전부 <b>공략 대상 히로인</b>이야. 상금이라는 보상도 있고, 마감이라는 고백 기한도 있어.'],
      ['think', '근데 솔직히 히로인 혼자 공략하는 건 어렵잖아? 그래서 같이 공략할 <b>파티</b>를 짜는 거야!'],
      ['thumbsup', '아, 그리고 친구를 초대해 오면… 내가 옷을 하나씩 갈아입을게. 끝까지 모으면 바다 갈 준비도 해 둘게!']]);
    else await say([['smile', `또 왔네, ${you()}! 오늘은 누구를 공략해 볼까?`]]);
    menu();
  }
  function menu() {
    const n = [...tcount.values()].reduce((a, b) => a + b, 0);
    say([['outfit', `지금 파티 <b>${n}</b>개가 히로인을 노리고 있어. 뭐부터 할래?`]]).then(() => choose([
      ['💗 오늘의 히로인 보기', () => heroines()], ['💘 공략 파티 구경하기', parties], ['✨ 내가 파티 결성하기', () => J.createTeam('', '', reboot)],
      ['🎀 루리 꾸미기 · 친구 초대', dress]]));
  }
  function heroines(q = '') {
    const pool = (q ? cs.filter(c => c.t.includes(q)) : [...cs].sort((a, b) => (tcount.get(b.id) || 0) - (tcount.get(a.id) || 0) || (dday(a.e) ?? 99) - (dday(b.e) ?? 99))).slice(0, 12);
    showPanel(`<div class="vn-ph"><b>💗 공략 대상 선택</b><input class="vn-q" placeholder="히로인(공모전) 이름 검색" value="${esc(q)}"><button class="vn-back">✕</button></div>
<div class="vn-cards">${pool.map(card).join('') || '<p class="note">그런 히로인은 없어…</p>'}</div>`, '누구로 할래? 카드를 눌러 봐!', 'think');
    let tm; panel.querySelector('.vn-q').oninput = e => { clearTimeout(tm); tm = setTimeout(() => { heroines(e.target.value.trim()); const i = panel.querySelector('.vn-q'); i.focus(); i.setSelectionRange(99, 99); }, 300); };
    panel.querySelectorAll('[data-id]').forEach(b => b.onclick = () => heroine(cs.find(c => c.id === b.dataset.id)));
  }
  const stars = c => { const v = c.pv || 0, n = v >= 1e7 ? 5 : v >= 5e6 ? 4 : v >= 1e6 ? 3 : v >= 3e5 ? 2 : 1; return '★'.repeat(n) + '☆'.repeat(5 - n); };
  function card(c) {
    const n = dday(c.e), k = tcount.get(c.id) || 0;
    return `<button class="vn-card${n !== null && n <= 3 ? ' hot' : ''}" data-id="${esc(c.id)}"><span class="vn-art">${c.th ? `<img src="/assets/shots/${esc(c.id)}.webp" alt="" loading="lazy">` : `<em>${esc(c.i || '💗')}</em>`}</span>
<b>${esc(c.t.length > 30 ? c.t.slice(0, 30) + '…' : c.t)}</b><span class="vn-st">🎁 ${esc(c.p || '보상 비공개')}</span><span class="vn-st">💌 고백 마감 ${n === null ? '-' : n <= 0 ? '오늘!' : 'D-' + n}</span>
<span class="vn-st">난이도 <i>${stars(c)}</i></span><span class="vn-heart">${k ? `💘 파티 ${k}` : '파티 모집 전'}</span></button>`;
  }
  async function heroine(c) {
    const n = dday(c.e), k = tcount.get(c.id) || 0;
    await say([['surprise', `오, <b>${esc(c.t)}</b>! ${you()}, 눈이 높네?`],
      ['think', `보상은 <b>${esc(c.p || '비공개')}</b>, 고백 마감까지 <b>${n === null ? '?' : n <= 0 ? '오늘까지' : 'D-' + n}</b>. 취향은 <b>${esc(c.g || '다양')}</b> 쪽이야.`],
      [k ? 'wink' : 'smile', k ? `지금 이 히로인을 노리는 파티가 <b>${k}</b>개 있어. 합류할래, 직접 파티를 만들래?` : '아직 아무도 이 히로인에게 파티를 안 짰어. 선점하면 유리할걸?']]);
    const opts = [];
    if (k) opts.push(['💘 이 히로인 공략 파티 보기', async () => {
      const { teams } = await J.api('/api/teams?contest=' + encodeURIComponent(c.id)).catch(() => ({ teams: [] }));
      choose([...teams.map(t => [`${t.status === 'open' && t.cnt < t.size ? '💌' : '🔒'} ${esc(t.name)} · ${t.cnt}/${t.size}명`, () => J.teamModal(t.id, () => heroine(c))]), ['↩ 돌아가기', () => heroine(c)]]);
    }]);
    opts.push(['✨ 이 히로인으로 파티 결성', () => J.createTeam(c.id, c.t, reboot)], ['💌 이 히로인 같이 공략할 친구 초대', () => invite(c)],
              ['📖 공략집(공모전 정보) 보기', () => { location.href = `/c/${c.id}/`; }], ['💗 다른 히로인 볼래', () => heroines()]);
    choose(opts);
  }
  async function parties() {
    const { teams } = await J.api('/api/teams').catch(() => ({ teams: [] }));
    if (!teams.length) { await say([['sad', '어라… 아직 결성된 파티가 하나도 없어.'], ['excited', `그럼 ${you()}가 첫 파티장이 되는 거야! 해 볼래?`]]); return choose([['✨ 파티 결성하기', () => J.createTeam('', '', reboot)], ['↩ 메뉴로', menu]]); }
    await say([['wink', '지금 파티원을 찾는 파티들이야. 마음에 드는 데 말 걸어 봐!']]);
    choose([...teams.slice(0, 8).map(t => [`${t.status === 'open' && t.cnt < t.size ? '💌' : '🔒'} ${esc(t.name)}${t.contest_title ? ` <small>→ ${esc(t.contest_title.slice(0, 18))}</small>` : ''} · ${t.cnt}/${t.size}`, () => J.teamModal(t.id, menu)]), ['📋 전체 목록으로', () => document.getElementById('cm-teams').scrollIntoView({ behavior: 'smooth' })], ['↩ 메뉴로', menu]]);
  }
  async function needLogin(line) {
    await say([['think', line]]);
    choose([['📝 가입 · 로그인', () => J.authModal(reboot)], ['↩ 메뉴로', menu]]);
  }
  async function getMe() { me = await J.api('/api/me').catch(() => null); if (me && me.prefs && Object.keys(me.prefs).length) { P = { ...me.prefs }; try { localStorage.setItem('jupjup_prefs', JSON.stringify(P)); } catch {} apply(); } return me; }

  // 초대 (히로인별 링크: 공모전 페이지로 보내고 ?ref= 로 기록)
  async function invite(c) {
    if (!J.st.t) return needLogin('초대 링크는 가입한 친구한테만 줄 수 있어. 초대할수록 나를 더 꾸밀 수 있거든!');
    if (!me) await getMe(); if (!me) return menu();
    const link = c ? `${location.origin}/c/${c.id}/?ref=${me.code}` : `${location.origin}/community/?ref=${me.code}`;
    const title = c ? `「${c.t}」 같이 공략할래?` : '같이 공모전 공략 파티 짤래?';
    showPanel(`<div class="vn-ph"><b>💌 친구 초대${c ? ` · ${esc(c.t.slice(0, 20))}` : ''}</b><button class="vn-back">✕</button></div>
<div class="vn-inv"><p>이 링크로 친구가 들어오면 <b>1점</b>, 가입하면 <b>3점</b>! ${c ? '이 히로인 초대 기록에 남아.' : ''}</p><input readonly value="${esc(link)}">
<div class="vn-share"><a class="naver" target="_blank" rel="noopener" href="https://share.naver.com/web/shareView?url=${encodeURIComponent(link)}&title=${encodeURIComponent(title + ' — 루리의 줍줍')}">N 네이버</a>
<a class="mail" href="mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(title + ' 같이 파티 짜자! ' + link)}">✉ 메일</a><button class="kakao">💬 카톡 · 공유</button><button class="copy">🔗 복사</button></div></div>`,
      `친구가 많이 올수록 나도 예쁘게 꾸밀 수 있어! 지금 <b>${pts()}점</b>이야.`, 'wink');
    const cp = e => (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject()).then(() => e.target.textContent = '복사됐어!', () => panel.querySelector('.vn-inv input').select());
    panel.querySelector('.copy').onclick = cp;
    panel.querySelector('.kakao').onclick = e => navigator.share ? navigator.share({ title: '루리의 줍줍', text: title, url: link }).catch(() => {}) : cp(e);
  }

  // 꾸미기
  async function dress(tab = 'o') {
    if (!J.st.t) return needLogin('로그인하면 오피스룩 8벌은 바로 줄게! 친구를 초대할수록 여름옷이 하나씩 열리고, 끝까지 모으면 수영복까지 입어 볼게.');
    if (!me) await getMe(); if (!me) return menu();
    const p = pts(), all = Object.values(CAT).flatMap(([, l]) => l).concat([[CALL_AT]]), nextNeed = all.map(x => x[0]).filter(n => n > p).sort((a, b) => a - b)[0];
    const tabs = Object.entries(CAT).map(([k, [n]]) => `<button data-t="${k}" class="${tab === k ? 'on' : ''}">${n}</button>`).join('') + `<button data-t="c" class="${tab === 'c' ? 'on' : ''}">🏷 호칭</button><button data-t="log" class="${tab === 'log' ? 'on' : ''}">📒 초대 기록</button>`;
    let body = '';
    if (CAT[tab]) {
      const cur = P[tab] || CAT[tab][1][0][1];
      body = `<div class="vn-ward">${CAT[tab][1].map(([need, v, n]) => `<button class="vn-cloth${need <= p ? '' : ' lock'}${cur === v ? ' on' : ''}" data-v="${v}" ${need <= p ? '' : 'disabled'}>${tab === 'o' ? `<img src="/assets/ruri/${v}_s.webp" alt="" width="110" height="152">` : `<span class="vn-sw" data-${tab}="${v}">${tab === 'f' ? (FX[v] || (v === 'petal' ? '🌸' : '∅')) : ''}</span>`}<span>${need <= p ? n : `🔒 ${need}점`}</span></button>`).join('')}</div>`;
    } else if (tab === 'c') {
      body = p >= CALL_AT ? `<div class="vn-inv"><p>루리가 나를 뭐라고 부를까? (최대 8자)</p><input class="vn-call" maxlength="8" value="${esc(P.c || '')}" placeholder="예: 선배, 파티장님"><div class="vn-share"><button class="vn-callsave">저장</button></div></div>`
                         : `<p class="note">🔒 초대 점수 ${CALL_AT}점부터 루리가 부르는 호칭을 정할 수 있어요.</p>`;
    } else {
      const byC = me.by_contest || [], name = id => (cs.find(c => c.id === id) || {}).t || (id ? id : '커뮤니티 전체');
      body = byC.length ? `<ul class="vn-log">${byC.map(x => `<li><b>${esc(name(x.h))}</b><span>방문 ${x.visits} · 가입 ${x.joins} → <b>${x.visits + x.joins * 3}점</b></span></li>`).join('')}</ul>` : '<p class="note">아직 초대 기록이 없어요. 히로인 카드에서 「친구 초대」를 눌러 링크를 보내 보세요.</p>';
    }
    showPanel(`<div class="vn-ph"><b>🎀 루리 꾸미기</b><span class="vn-pts">초대 점수 <b>${p}</b> <small>(방문 ${me.visits || 0} · 가입 ${me.invites || 0}×3)</small></span><button class="vn-back">✕</button></div>
<div class="vn-tabs">${tabs}</div>${body}<div class="vn-share" style="margin-top:12px"><button class="vn-inv-go">💌 친구 초대하고 점수 모으기</button></div>`,
      nextNeed ? `<b>${nextNeed - p}점</b>만 더 모으면 새로운 게 열려! 초대해 줄 거지?` : '전부 다 열었어! 고마워, 진짜 최고야 💕', p ? 'excited' : 'wink');
    panel.querySelectorAll('[data-t]').forEach(b => b.onclick = () => dress(b.dataset.t));
    panel.querySelectorAll('.vn-cloth:not(.lock)').forEach(b => b.onclick = () => { save(tab, b.dataset.v); dress(tab); });
    const cs_ = panel.querySelector('.vn-callsave'); if (cs_) cs_.onclick = () => { save('c', panel.querySelector('.vn-call').value.trim()); say([['excited', `좋아, 앞으로 <b>${you()}</b>(이)라고 부를게!`]]).then(() => dress('c')); };
    panel.querySelector('.vn-inv-go').onclick = () => invite(null);
  }
  function reboot() { load().then(menu); }

  S.querySelector('.vn-sys').onclick = e => {
    const k = e.target.dataset.s; if (!k) return;
    if (k === 'auto') { auto = !auto; e.target.classList.toggle('on', auto); }
    if (k === 'skip') { clearInterval(typing); typing = null; menu(); }
    if (k === 'ward') dress();
  };
  async function load() {
    const [c, t] = await Promise.all([fetch('/assets/community/contests.json').then(r => r.json()).catch(() => []), J.api('/api/teams').catch(() => ({ teams: [] })), J.st.t ? getMe() : null]);
    cs = c; tcount = new Map(); (t.teams || []).forEach(x => tcount.set(x.contest_id, (tcount.get(x.contest_id) || 0) + 1));
  }
  apply();
  load().then(intro);
})();
