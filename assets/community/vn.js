// 루리의 줍줍 커뮤니티 — 미연시 모드: 공모전 = 공략 대상 히로인, 팀 = 공략 파티, 루리 = 정보통 친구
// 친구 초대(링크 방문 1점, 가입 3점)로 루리 옷장 의상 해금. comm.js 의 window.JUP 사용.
(function () {
  const S = document.getElementById('vn'), J = window.JUP; if (!S || !J) return;
  const esc = J.esc, $ = s => S.querySelector(s);
  const WARD = [[0, 'smile', '교복'], [1, 'o_cardigan', '카디건'], [3, 'o_vest', '니트 베스트'], [6, 'o_suit', '정장'], [10, 'o_trench', '트렌치코트'],
                [15, 'o_gray', '그레이 셋업'], [25, 'o_anchor', '앵커룩'], [40, 'o_present', '발표 정장']];
  const OKEY = 'jupjup_outfit';
  const outfit = () => { try { return localStorage.getItem(OKEY) || 'smile'; } catch { return 'smile'; } };
  const EXP = { smile: 1, wink: 1, excited: 1, think: 1, surprise: 1, sad: 1, thumbsup: 1, serious: 1 };
  const dday = e => e ? Math.ceil((new Date(e + 'T23:59:59+09:00') - Date.now()) / 864e5) : null;
  let cs = [], tcount = new Map(), auto = false, typing = null;

  // ---- 무대 ----
  S.innerHTML = `<div class="vn-bg"></div><div class="vn-petals">${Array.from({ length: 18 }, (_, i) => `<i style="--x:${(i * 37) % 100}%;--d:${6 + (i * 7) % 9}s;--w:${(i * 13) % 7}s;--s:${0.6 + (i % 5) * 0.15}"></i>`).join('')}</div>
<img class="vn-ruri" alt="루리" width="300" height="415"><div class="vn-sys"><button data-s="auto">AUTO</button><button data-s="skip">SKIP</button><button data-s="ward">👗 옷장</button></div>
<div class="vn-choices" hidden></div><div class="vn-panel" hidden></div>
<div class="vn-box"><span class="vn-name">루리</span><p class="vn-text"></p><span class="vn-next">▼</span></div>`;
  const img = $('.vn-ruri'), txt = $('.vn-text'), box = $('.vn-box'), ch = $('.vn-choices'), panel = $('.vn-panel');
  const face = e => { const f = outfit() !== 'smile' && (e === 'smile' || e === 'outfit') ? outfit() : (EXP[e] ? e : 'smile'); const src = `/assets/ruri/${f}.webp`; if (!img.src.endsWith(src)) { img.classList.remove('pop'); void img.offsetWidth; img.classList.add('pop'); img.src = src; } };

  // ---- 대사 엔진: say([[표정, 대사], ...]) → Promise ----
  function say(lines) {
    return lines.reduce((p, [e, t]) => p.then(() => new Promise(done => {
      face(e); ch.hidden = true; panel.hidden = true; box.classList.remove('wait');
      let i = 0; const plain = t.replace(/<[^>]+>/g, '');
      clearInterval(typing);
      const finish = () => { clearInterval(typing); typing = null; txt.innerHTML = t; box.classList.add('wait'); if (auto) setTimeout(next, 1400); };
      typing = setInterval(() => { i += 1; txt.textContent = plain.slice(0, i); if (i >= plain.length) finish(); }, 28);
      const next = () => { if (typing) return finish(); box.onclick = null; done(); };
      box.onclick = next;
    })), Promise.resolve());
  }
  function choose(opts) {
    ch.innerHTML = opts.map((o, i) => `<button data-i="${i}">${o[0]}</button>`).join(''); ch.hidden = false; box.classList.remove('wait');
    ch.querySelectorAll('button').forEach(b => b.onclick = () => { ch.hidden = true; opts[+b.dataset.i][1](); });
  }

  // ---- 장면 ----
  async function intro() {
    const first = (() => { try { return !localStorage.getItem('jupjup_vn'); } catch { return true; } })();
    try { localStorage.setItem('jupjup_vn', 1); } catch {}
    if (first) await say([['excited', '앗, 왔구나! 나 루리야. 이 학교… 아니, 이 사이트의 정보통이지!'],
      ['wink', '여기 공모전들은 전부 <b>공략 대상 히로인</b>이야. 상금이라는 보상도 있고, 마감이라는 고백 기한도 있어.'],
      ['think', '근데 솔직히 히로인 혼자 공략하는 건 어렵잖아? 그래서 같이 공략할 <b>파티</b>를 짜는 거야!']]);
    else await say([['smile', '또 왔네! 오늘은 누구를 공략해 볼까?']]);
    menu();
  }
  function menu() {
    const n = [...tcount.values()].reduce((a, b) => a + b, 0);
    say([['outfit', `지금 파티 <b>${n}</b>개가 히로인을 노리고 있어. 뭐부터 할래?`]]).then(() => choose([
      ['💗 오늘의 히로인 보기', heroines], ['💘 공략 파티 구경하기', parties], ['✨ 내가 파티 결성하기', () => J.createTeam('', '', reboot)],
      ['👗 루리 옷장 · 친구 초대', wardrobe]]));
  }
  function heroines(q = '') {
    const pool = (q ? cs.filter(c => c.t.includes(q)) : [...cs].sort((a, b) => (tcount.get(b.id) || 0) - (tcount.get(a.id) || 0) || (dday(a.e) ?? 99) - (dday(b.e) ?? 99))).slice(0, 12);
    panel.innerHTML = `<div class="vn-ph"><b>💗 공략 대상 선택</b><input class="vn-q" placeholder="히로인(공모전) 이름 검색" value="${esc(q)}"><button class="vn-back">✕</button></div>
<div class="vn-cards">${pool.map(card).join('') || '<p class="note">그런 히로인은 없어…</p>'}</div>`;
    panel.hidden = false; ch.hidden = true; face('think'); txt.innerHTML = '누구로 할래? 카드를 눌러 봐!'; box.classList.remove('wait'); box.onclick = null;
    let tm; panel.querySelector('.vn-q').oninput = e => { clearTimeout(tm); tm = setTimeout(() => { heroines(e.target.value.trim()); const i = panel.querySelector('.vn-q'); i.focus(); i.setSelectionRange(99, 99); }, 300); };
    panel.querySelector('.vn-back').onclick = () => { panel.hidden = true; menu(); };
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
    await say([['surprise', `오, <b>${esc(c.t)}</b>! 눈이 높네?`],
      ['think', `보상은 <b>${esc(c.p || '비공개')}</b>, 고백 마감까지 <b>${n === null ? '?' : n <= 0 ? '오늘까지' : 'D-' + n}</b>. 취향은 <b>${esc(c.g || '다양')}</b> 쪽이야.`],
      [k ? 'wink' : 'smile', k ? `지금 이 히로인을 노리는 파티가 <b>${k}</b>개 있어. 합류할래, 직접 파티를 만들래?` : '아직 아무도 이 히로인에게 파티를 안 짰어. 선점하면 유리할걸?']]);
    const opts = [];
    if (k) opts.push(['💘 이 히로인 공략 파티 보기', async () => {
      const { teams } = await J.api('/api/teams?contest=' + encodeURIComponent(c.id)).catch(() => ({ teams: [] }));
      choose([...teams.map(t => [`${t.status === 'open' && t.cnt < t.size ? '💌' : '🔒'} ${esc(t.name)} · ${t.cnt}/${t.size}명`, () => J.teamModal(t.id, () => heroine(c))]), ['↩ 돌아가기', () => heroine(c)]]);
    }]);
    opts.push(['✨ 이 히로인으로 파티 결성', () => J.createTeam(c.id, c.t, reboot)], ['📖 공략집(공모전 정보) 보기', () => { location.href = `/c/${c.id}/`; }], ['💗 다른 히로인 볼래', () => heroines()]);
    choose(opts);
  }
  async function parties() {
    const { teams } = await J.api('/api/teams').catch(() => ({ teams: [] }));
    if (!teams.length) { await say([['sad', '어라… 아직 결성된 파티가 하나도 없어.'], ['excited', '그럼 네가 첫 파티장이 되는 거야! 해 볼래?']]); return choose([['✨ 파티 결성하기', () => J.createTeam('', '', reboot)], ['↩ 메뉴로', menu]]); }
    await say([['wink', '지금 파티원을 찾는 파티들이야. 마음에 드는 데 말 걸어 봐!']]);
    choose([...teams.slice(0, 8).map(t => [`${t.status === 'open' && t.cnt < t.size ? '💌' : '🔒'} ${esc(t.name)}${t.contest_title ? ` <small>→ ${esc(t.contest_title.slice(0, 18))}</small>` : ''} · ${t.cnt}/${t.size}`, () => J.teamModal(t.id, menu)]), ['📋 전체 목록으로', () => document.getElementById('cm-teams').scrollIntoView({ behavior: 'smooth' })], ['↩ 메뉴로', menu]]);
  }
  async function wardrobe() {
    if (!J.st.t) { await say([['think', '옷장은 가입한 친구만 열 수 있어. 친구를 초대하면 내 옷이 하나씩 늘어나거든!']]); return choose([['📝 가입 · 로그인', () => J.authModal(reboot)], ['↩ 메뉴로', menu]]); }
    const me = await J.api('/api/me').catch(() => null); if (!me) return menu();
    const pts = (me.visits || 0) + (me.invites || 0) * 3, link = `${location.origin}/community/?ref=${me.code}`;
    const nextT = WARD.find(w => w[0] > pts);
    panel.innerHTML = `<div class="vn-ph"><b>👗 루리 옷장</b><span class="vn-pts">초대 점수 <b>${pts}</b> <small>(방문 ${me.visits || 0} · 가입 ${me.invites || 0}×3)</small></span><button class="vn-back">✕</button></div>
<div class="vn-ward">${WARD.map(([need, k, n]) => `<button class="vn-cloth${need <= pts ? '' : ' lock'}${outfit() === k ? ' on' : ''}" data-k="${k}" ${need <= pts ? '' : 'disabled'}><img src="/assets/ruri/${k}_s.webp" alt="" width="110" height="152"><span>${need <= pts ? n : `🔒 ${need}점`}</span></button>`).join('')}</div>
<div class="vn-inv"><p>내 초대 링크로 친구가 들어오면 <b>1점</b>, 가입하면 <b>3점</b>!</p><input readonly value="${esc(link)}">
<div class="vn-share"><a class="naver" target="_blank" rel="noopener" href="https://share.naver.com/web/shareView?url=${encodeURIComponent(link)}&title=${encodeURIComponent('같이 공모전 공략 파티 짤래? — 루리의 줍줍')}">N 네이버</a>
<a class="mail" href="mailto:?subject=${encodeURIComponent('공모전 같이 나갈래?')}&body=${encodeURIComponent('공모전 같이 공략할 파티 짜자! ' + link)}">✉ 메일</a><button class="kakao">💬 카톡 · 공유</button><button class="copy">🔗 복사</button></div></div>`;
    panel.hidden = false; ch.hidden = true; box.onclick = null;
    face('outfit'); txt.innerHTML = nextT ? `<b>${nextT[0] - pts}점</b>만 더 모으면 「${nextT[2]}」 입어 볼게!` : '옷장 다 열었어! 고마워 💕'; box.classList.remove('wait');
    panel.querySelector('.vn-back').onclick = () => { panel.hidden = true; menu(); };
    panel.querySelectorAll('.vn-cloth:not(.lock)').forEach(b => b.onclick = () => { try { localStorage.setItem(OKEY, b.dataset.k); } catch {} wardrobe(); });
    const cp = e => (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject()).then(() => e.target.textContent = '복사됐어!', () => panel.querySelector('.vn-inv input').select());
    panel.querySelector('.copy').onclick = cp;
    panel.querySelector('.kakao').onclick = e => navigator.share ? navigator.share({ title: '루리의 줍줍', text: '공모전 같이 공략할 파티 짜자!', url: link }).catch(() => {}) : cp(e);
  }
  function reboot() { load().then(menu); }

  S.querySelector('.vn-sys').onclick = e => {
    const k = e.target.dataset.s; if (!k) return;
    if (k === 'auto') { auto = !auto; e.target.classList.toggle('on', auto); }
    if (k === 'skip') { clearInterval(typing); typing = null; menu(); }
    if (k === 'ward') wardrobe();
  };
  async function load() {
    const [c, t] = await Promise.all([fetch('/assets/community/contests.json').then(r => r.json()).catch(() => []), J.api('/api/teams').catch(() => ({ teams: [] }))]);
    cs = c; tcount = new Map(); (t.teams || []).forEach(x => tcount.set(x.contest_id, (tcount.get(x.contest_id) || 0) + 1));
  }
  load().then(intro);
})();
