// 루리의 줍줍 커뮤니티 — 미연시 모드: 공모전 = 공략 대상 히로인, 팀 = 원정대, 루리 = 정보통 친구
// 친구 초대(링크 방문 1점, 가입 3점, 히로인별 기록) 점수는 기록만 남긴다. comm.js 의 window.JUP 사용.
// 2026-10-28: 꾸미기(의상·배경·대사창·효과·호칭 고르기)는 걷어냈다 — 그 자리는 「루리 옷벗기기」 진입구다.
// 기존 설정값(P)은 localStorage 에 그대로 남아 배경·효과·표정에 계속 쓰인다. 고르는 화면만 없앴다.
(function () {
  const S = document.getElementById('vn'), J = window.JUP; if (!S || !J) return;
  const esc = J.esc, $ = s => S.querySelector(s);
  const FX = { heart: '💗', star: '✦', snow: '❄' };
  const EXP = { smile: 1, wink: 1, excited: 1, think: 1, surprise: 1, sad: 1, thumbsup: 1, serious: 1 };
  const dday = e => e ? Math.ceil((new Date(e + 'T23:59:59+09:00') - Date.now()) / 864e5) : null;
  let cs = [], tcount = new Map(), auto = false, typing = null, me = null, gen = 0;  // gen: 새 장면이 시작되면 이전 대사 흐름은 버림
  let P = (() => { try { return JSON.parse(localStorage.getItem('jupjup_prefs') || '{}'); } catch { return {}; } })();
  const pts = () => me ? (me.visits || 0) + (me.invites || 0) * 3 : 0;
  const you = () => P.c ? esc(P.c) : '너';

  // ---- 무대 ----
  S.innerHTML = `<div class="vn-bg"></div><div class="vn-petals"></div>
<img class="vn-ruri" alt="루리" width="300" height="415"><div class="vn-sys"><button data-s="auto">AUTO</button><button data-s="skip">SKIP</button><button data-s="ward">🎮 게임</button></div>
<div class="vn-choices" hidden></div><div class="vn-panel" hidden></div>
<div class="vn-box"><span class="vn-name">루리</span><p class="vn-text"></p><span class="vn-next">▼</span></div>`;
  const img = $('.vn-ruri'), txt = $('.vn-text'), box = $('.vn-box'), ch = $('.vn-choices'), panel = $('.vn-panel');
  function apply() {
    S.dataset.b = P.b || 'dusk'; S.dataset.x = P.x || 'basic';
    const f = P.f || 'petal';
    $('.vn-petals').innerHTML = f === 'none' ? '' : Array.from({ length: 18 }, (_, i) => `<i class="${f}" style="--x:${(i * 37) % 100}%;--d:${6 + (i * 7) % 9}s;--w:${(i * 13) % 7}s;--s:${0.6 + (i % 5) * 0.15}">${FX[f] || ''}</i>`).join('');
    face('outfit');
  }
  let fn = 0; const face = e => { const o = J.st.t && P.o && P.o !== 'smile' ? P.o : ''; const ps = J.poseSrc(o ? o.replace(/^o_/, '') : 'office', J.POSE_OF[e] || '', false, fn++); const f = o || (EXP[e] ? e : 'smile'); const src = ps || `/assets/ruri/${f}.webp`; if (!img.src.endsWith(src)) { img.classList.remove('pop'); void img.offsetWidth; img.classList.add('pop'); img.src = src; } };

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
      ['think', '근데 솔직히 히로인 혼자 공략하는 건 어렵잖아? 그래서 같이 공략할 <b>원정대</b>를 짜는 거야!'],
      ['thumbsup', '아, 그리고 친구를 초대해 오면… 내가 옷을 하나씩 갈아입을게. 끝까지 모으면 바다 갈 준비도 해 둘게!']]);
    else await say([['smile', `또 왔네, ${you()}! 오늘은 누구를 공략해 볼까?`]]);
    menu();
  }
  function menu() {
    const n = [...tcount.values()].reduce((a, b) => a + b, 0);
    say([['outfit', `지금 원정대 <b>${n}</b>개가 히로인을 노리고 있어. 뭐부터 할래?`]]).then(() => choose([
      ['💗 오늘의 히로인 보기', () => heroines()], ['💘 원정대 구경하기', parties], ['✨ 내가 원정대 결성하기', () => J.createTeam('', '', reboot)],
      ['🎮 루리 옷벗기기 · 경찰서 엔딩', dress]]));
  }
  function heroines(q = '') {
    const pool = (q ? cs.filter(c => c.t.includes(q)) : [...cs].sort((a, b) => (tcount.get(b.id) || 0) - (tcount.get(a.id) || 0) || (dday(a.e) ?? 99) - (dday(b.e) ?? 99))).slice(0, 12);
    showPanel(`<div class="vn-ph"><b>💗 공모전 고르기</b><input class="vn-q" placeholder="히로인(공모전) 이름 검색" value="${esc(q)}"><button class="vn-back">✕</button></div>
<div class="vn-cards">${pool.map(card).join('') || '<p class="note">그런 히로인은 없어…</p>'}</div>`, '누구로 할래? 카드를 눌러 봐!', 'think');
    let tm; panel.querySelector('.vn-q').oninput = e => { clearTimeout(tm); tm = setTimeout(() => { heroines(e.target.value.trim()); const i = panel.querySelector('.vn-q'); i.focus(); i.setSelectionRange(99, 99); }, 300); };
    panel.querySelectorAll('[data-id]').forEach(b => b.onclick = () => heroine(cs.find(c => c.id === b.dataset.id)));
  }
  const stars = c => { const v = c.pv || 0, n = v >= 1e7 ? 5 : v >= 5e6 ? 4 : v >= 1e6 ? 3 : v >= 3e5 ? 2 : 1; return '★'.repeat(n) + '☆'.repeat(5 - n); };
  function card(c) {
    const n = dday(c.e), k = tcount.get(c.id) || 0;
    return `<button class="vn-card${n !== null && n <= 3 ? ' hot' : ''}" data-id="${esc(c.id)}"><span class="vn-art">${c.th ? `<img src="/assets/shots/${esc(c.id)}.webp" alt="" loading="lazy">` : `<em>${esc(c.i || '💗')}</em>`}</span>
<b>${esc(c.t.length > 30 ? c.t.slice(0, 30) + '…' : c.t)}</b><span class="vn-st">🎁 ${esc(c.p || '보상 비공개')}</span><span class="vn-st">💌 고백 마감 ${n === null ? '-' : n <= 0 ? '오늘!' : 'D-' + n}</span>
<span class="vn-st">난이도 <i>${stars(c)}</i></span><span class="vn-heart">${k ? `🚩 원정대 ${k}` : '원정대 모집 전'}</span></button>`;
  }
  async function heroine(c) {
    J.ga('heroine_view', { contest_id: c.id });
    const n = dday(c.e), k = tcount.get(c.id) || 0;
    await say([['surprise', `오, <b>${esc(c.t)}</b>! ${you()}, 눈이 높네?`],
      ['think', `보상은 <b>${esc(c.p || '비공개')}</b>, 고백 마감까지 <b>${n === null ? '?' : n <= 0 ? '오늘까지' : 'D-' + n}</b>. 취향은 <b>${esc(c.g || '다양')}</b> 쪽이야.`],
      [k ? 'wink' : 'smile', k ? `지금 이 히로인을 노리는 원정대가 <b>${k}</b>개 있어. 합류할래, 직접 원정대를 만들래?` : '아직 아무도 이 히로인에게 원정대를 안 짰어. 선점하면 유리할걸?']]);
    const opts = [];
    if (k) opts.push(['💘 이 공모전 원정대 보기', async () => {
      const { teams } = await J.api('/api/teams?contest=' + encodeURIComponent(c.id)).catch(() => ({ teams: [] }));
      choose([...teams.map(t => [`${t.status === 'open' && t.cnt < t.size ? '💌' : '🔒'} ${esc(t.name)} · ${t.cnt}/${t.size}명`, () => J.teamModal(t.id, () => heroine(c))]), ['↩ 돌아가기', () => heroine(c)]]);
    }]);
    opts.push(['✨ 이 히로인으로 원정대 결성', () => J.createTeam(c.id, c.t, reboot)], ['💌 이 히로인 같이 나갈 친구 초대', () => invite(c)],
              ['📖 공모전 정보 보기', () => { location.href = `/c/${c.id}/`; }], ['💗 다른 히로인 볼래', () => heroines()]);
    choose(opts);
  }
  async function parties() {
    const { teams } = await J.api('/api/teams').catch(() => ({ teams: [] }));
    if (!teams.length) { await say([['sad', '어라… 아직 결성된 원정대가 하나도 없어.'], ['excited', `그럼 ${you()}가 첫 대장이 되는 거야! 해 볼래?`]]); return choose([['✨ 원정대 결성하기', () => J.createTeam('', '', reboot)], ['↩ 메뉴로', menu]]); }
    await say([['wink', '지금 대원을 찾는 원정대들이야. 마음에 드는 데 말 걸어 봐!']]);
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
    const title = c ? `「${c.t}」 같이 나갈래?` : '같이 공모전 원정대 짤래?';
    showPanel(`<div class="vn-ph"><b>💌 친구 초대${c ? ` · ${esc(c.t.slice(0, 20))}` : ''}</b><button class="vn-back">✕</button></div>
<div class="vn-inv"><p>이 링크로 친구가 들어오면 <b>1점</b>, 가입하면 <b>3점</b>! ${c ? '이 히로인 초대 기록에 남아.' : ''}</p><input readonly value="${esc(link)}">
<div class="vn-share"><a class="naver" target="_blank" rel="noopener" href="https://share.naver.com/web/shareView?url=${encodeURIComponent(link)}&title=${encodeURIComponent(title + ' — 루리의 줍줍')}">N 네이버</a>
<a class="mail" href="mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(title + ' 같이 원정대 짜자! ' + link)}">✉ 메일</a><button class="kakao">💬 카톡 · 공유</button><button class="copy">🔗 복사</button></div></div>`,
      `친구가 많이 올수록 나도 예쁘게 꾸밀 수 있어! 지금 <b>${pts()}점</b>이야.`, 'wink');
    const cp = e => (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject()).then(() => e.target.textContent = '복사됐어!', () => panel.querySelector('.vn-inv input').select());
    panel.querySelector('.copy').onclick = e => { J.ga('invite_share', { method: 'copy', contest_id: c ? c.id : '' }); cp(e); };
    panel.querySelector('.kakao').onclick = e => { J.ga('invite_share', { method: 'share', contest_id: c ? c.id : '' }); navigator.share ? navigator.share({ title: '루리의 줍줍', text: title, url: link }).catch(() => {}) : cp(e); };
    panel.querySelector('.naver').onclick = () => J.ga('invite_share', { method: 'naver', contest_id: c ? c.id : '' }); panel.querySelector('.mail').onclick = () => J.ga('invite_share', { method: 'mail', contest_id: c ? c.id : '' });
  }

  // 꾸미기 자리 — 「루리 옷벗기기」로 넘긴다. 게임은 /vn/pool/ 에 따로 산다.
  async function dress() {
    showPanel(`<div class="vn-ph"><b>🎮 루리 옷벗기기</b><button class="vn-back">✕</button></div>
<div class="vn-inv"><p>가위바위보 다섯 단계. 루리한테 버릇이 있으니 잘 보면 이겨.</p>
<p class="note">다만 끝까지 이기면 네가 경찰서에 간다. 그건 해 보면 알고.</p>
<div class="vn-share"><button class="vn-go-game">▶ 시작하기</button></div></div>`,
      '이길 자신 있어? 끝까지 가면 후회할 텐데.', 'wink');
    panel.querySelector('.vn-go-game').onclick = () => {
      J.ga('ruri_game_go', {});
      location.href = '/vn/pool/?from=community';
    };
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
  load().then(() => location.hash === '#dress' ? dress() : intro());
})();
