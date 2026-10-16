// 루리의 줍줍 커뮤니티 — 공모전별 팀 모집(만들기·신청·수락) + 후기·질문 게시판 (API: Cloudflare Worker, 주소는 <body data-api>)
// 가입은 이메일+비밀번호만. 표시 이름은 가린 이메일.
(function () {
  const API = document.body.dataset.api; if (!API) return;
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };  // GA4 맞춤 이벤트
  try { const rf = new URLSearchParams(location.search).get('ref'); if (rf && /^[0-9a-f]{8}$/.test(rf)) { const h = new URLSearchParams(location.search).get('h') || (location.pathname.match(/^\/c\/([^/]+)\//) || [])[1] || ''; localStorage.setItem('jupjup_ref', rf); localStorage.setItem('jupjup_ref_h', h); fetch(API + '/api/ref', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: rf, h }) }).catch(() => {}); } } catch {}
  const KEY = 'jupjup_tok', NK = 'jupjup_nick';
  const st = { get t() { try { return localStorage.getItem(KEY) || ''; } catch { return ''; } }, get n() { try { return localStorage.getItem(NK) || ''; } catch { return ''; } },
    set(t, n) { try { if (t) { localStorage.setItem(KEY, t); localStorage.setItem(NK, n); } else { localStorage.removeItem(KEY); localStorage.removeItem(NK); } } catch {} } };
  // 구글·카카오 로그인 후 돌아옴 (st 정의 뒤에 있어야 함 — 2026-10-17 앞에 두었다가 스크립트 전체가 멈춤)
  { const h = location.hash.match(/#jt=([0-9a-f]+)&jn=([^&]+)/), e = location.hash.match(/#jerr=([^&]+)/);  // 구글·카카오 로그인 후 돌아옴
    if (h) { st.set(h[1], decodeURIComponent(h[2])); try { localStorage.removeItem('jupjup_prefs_t'); } catch {} ga('login', { method: 'oauth' }); history.replaceState(null, '', location.pathname + location.search); }
    else if (e) { history.replaceState(null, '', location.pathname + location.search); setTimeout(() => alert(decodeURIComponent(e[1])), 300); } }
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const ago = t => { const d = Date.now() / 1000 - t; return d < 60 ? '방금' : d < 3600 ? Math.floor(d / 60) + '분 전' : d < 86400 ? Math.floor(d / 3600) + '시간 전' : new Date(t * 1000).toLocaleDateString('ko-KR'); };
  const KIND = { review: '후기', qna: '질문', tip: '팁' };
  async function api(path, opt = {}) {
    const r = await fetch(API + path, { ...opt, headers: { 'Content-Type': 'application/json', ...(st.t ? { Authorization: 'Bearer ' + st.t } : {}) }, body: opt.body ? JSON.stringify(opt.body) : undefined });
    const j = await r.json().catch(() => ({}));
    if (r.status === 401 && st.t && path !== '/api/login') st.set('');
    if (!r.ok) throw new Error(j.error || '문제가 생겼어요.');
    return j;
  }

  // ---- 로그인/가입 창 ----
  function authModal(onDone) {
    const m = document.createElement('div'); m.className = 'cm-modal';
    m.innerHTML = `<div class="cm-box" role="dialog" aria-label="로그인"><button class="cm-x" aria-label="닫기">✕</button>
<h3>🚩 가입 · 로그인</h3><p class="note">이메일과 비밀번호만 있으면 돼요. 다른 정보는 받지 않아요.</p>
<div class="cm-soc"><a class="soc kakao" href="${API}/api/oauth/kakao/start?back=${encodeURIComponent(location.pathname)}">💬 카카오로 시작</a><a class="soc google" href="${API}/api/oauth/google/start?back=${encodeURIComponent(location.pathname)}"><b>G</b> 구글로 시작</a></div><p class="cm-or">또는 이메일로</p><input type="email" class="cm-em" placeholder="이메일" autocomplete="email"><input type="password" class="cm-pw" placeholder="비밀번호 (8자 이상)" autocomplete="current-password">
<p class="cm-err"></p><div class="cm-row"><button class="cm-login btn2">로그인</button><button class="cm-join btn2 ghost">처음이에요, 가입</button></div>
<p class="note">가입하면 <a href="/terms/">이용약관</a>과 <a href="/privacy/">개인정보처리방침</a>에 동의한 것으로 봐요. 글쓴이 이름은 이메일 앞부분을 가려서(예: sun***) 표시해요.</p></div>`;
    document.body.appendChild(m);
    const em = m.querySelector('.cm-em'), pw = m.querySelector('.cm-pw'), er = m.querySelector('.cm-err');
    fetch(API + '/api/oauth/ready').then(r => r.json()).then(r => { m.querySelectorAll('.soc').forEach(a => { if (!r[a.classList.contains('kakao') ? 'kakao' : 'google']) a.remove(); }); if (!m.querySelector('.soc')) { const s = m.querySelector('.cm-soc'), o = m.querySelector('.cm-or'); s && s.remove(); o && o.remove(); } }).catch(() => {});
    const go = async path => {
      er.textContent = '';
      try { const j = await api(path, { method: 'POST', body: { email: em.value, password: pw.value, ref: (() => { try { return localStorage.getItem('jupjup_ref') || ''; } catch { return ''; } })(), h: (() => { try { return localStorage.getItem('jupjup_ref_h') || ''; } catch { return ''; } })() } }); st.set(j.token, j.nick); ga(path === '/api/signup' ? 'sign_up' : 'login', { method: 'email' }); try { localStorage.removeItem('jupjup_prefs_t'); } catch {} syncPrefs(); m.remove(); onDone && onDone(); paintBar(); }
      catch (e) { er.textContent = e.message; }
    };
    m.querySelector('.cm-login').onclick = () => go('/api/login');
    m.querySelector('.cm-join').onclick = () => go('/api/signup');
    m.querySelector('.cm-x').onclick = () => m.remove();
    m.onclick = e => { if (e.target === m) m.remove(); };
    em.focus();
  }

  // ---- 헤더 로그인 표시 ----
  function paintBar() {
    let b = document.querySelector('.cm-acct');
    if (!b) { b = document.createElement('div'); b.className = 'cm-acct'; const h = document.querySelector('.hd-in'); if (h) h.appendChild(b); else return; }
    // 메뉴바를 없앤 뒤(2026-10-17) 로그인 기능 입구: 닉네임 누르면 내 메뉴
    const favs = (() => { try { return JSON.parse(localStorage.getItem('jupjup_fav_v1') || '[]'); } catch { return []; } })();
    const dl = e => { const p = e.split('-'), n = new Date(); return Math.round((Date.UTC(+p[0], p[1] - 1, +p[2]) - Date.UTC(n.getFullYear(), n.getMonth(), n.getDate())) / 864e5); };
    const fl = favs.map(f => ({ ...f, l: dl(f.end) })).filter(f => f.l >= 0).sort((a, b) => a.l - b.l).slice(0, 5);
    b.innerHTML = st.t ? `<button class="cm-me">${esc(st.n)} ▾</button><div class="cm-menu" hidden>
<a href="/community/">🚩 원정대</a><a href="/community/#dress">🎀 루리 꾸미기</a>
<b>⭐ 찜한 공모전</b>${fl.length ? fl.map(f => `<a class="cm-fv" href="/c/${esc(f.id)}/"><em>${f.l ? 'D-' + f.l : 'D-DAY'}</em>${esc(f.title)}</a>`).join('') : '<p>챗봇 카드의 ☆로 찜해 두면 여기 모여요.</p>'}
<button class="cm-out">로그아웃</button></div>` : '<button class="cm-in">로그인</button>';
    const me = b.querySelector('.cm-me'), menu = b.querySelector('.cm-menu');
    if (me) { me.onclick = e => { e.stopPropagation(); menu.hidden = !menu.hidden; }; document.addEventListener('click', e => { if (!b.contains(e.target)) menu.hidden = true; }); }
    const i = b.querySelector('.cm-in'), o = b.querySelector('.cm-out');
    if (i) i.onclick = () => authModal(() => location.reload());
    if (o) o.onclick = async () => { await api('/api/logout', { method: 'POST' }).catch(() => {}); st.set(''); try { localStorage.removeItem('jupjup_prefs'); localStorage.removeItem('jupjup_prefs_t'); } catch {} location.reload(); };
  }

  // ---- 게시판 (공모전 상세 #cm-board[data-contest], 전체 /community/ #cm-board[data-all]) ----
  async function board(el) {
    const cid = el.dataset.contest || '', title = el.dataset.title || '', all = 'all' in el.dataset;
    el.innerHTML = `<div class="cm-head"><h2>💬 ${all ? '후기·질문·자유' : '이 공모전 후기·질문'}</h2><button class="cm-write btn2">글쓰기</button></div><div class="cm-form" hidden></div><ul class="cm-list"><li class="note">불러오는 중…</li></ul>`;
    const list = el.querySelector('.cm-list'), form = el.querySelector('.cm-form');
    const load = async () => {
      try {
        const { posts } = await api('/api/posts' + (cid ? '?contest=' + encodeURIComponent(cid) : ''));
        list.innerHTML = posts.length ? '' : `<li class="cm-empty">${all ? '아직 글이 없어요.' : '아직 후기가 없어요. 응모해 보셨다면 첫 후기를 남겨 주세요!'}</li>`;
        posts.forEach(p => {
          const li = document.createElement('li'); li.className = 'cm-post';
          li.innerHTML = `<div class="cm-meta"><span class="cm-k k-${p.kind}">${KIND[p.kind] || '글'}</span>${p.rating ? '<span class="cm-star">' + '★'.repeat(p.rating) + '☆'.repeat(5 - p.rating) + '</span>' : ''}<span>${esc(p.nick || '탈퇴한 회원')} · ${ago(p.created)}</span></div>
<h3>${esc(p.title)}</h3>${all && p.contest_id !== 'free' ? `<a class="cm-on" href="/c/${esc(p.contest_id)}/">📌 ${esc(p.contest_title || p.contest_id)}</a>` : ''}<p class="cm-body">${esc(p.body)}</p>
<div class="cm-acts"><button class="cm-cm">댓글 ${p.cm}</button>${st.n && st.n === p.nick ? '<button class="cm-del">삭제</button>' : ''}<button class="cm-rp">신고</button></div><div class="cm-cms" hidden></div>`;
          li.querySelector('.cm-cm').onclick = () => comments(li.querySelector('.cm-cms'), p.id);
          const d = li.querySelector('.cm-del'); if (d) d.onclick = async () => { if (confirmLite(d)) { await api('/api/posts/' + p.id, { method: 'DELETE' }); load(); } };
          li.querySelector('.cm-rp').onclick = e => report(e.currentTarget, 'p:' + p.id);
          list.appendChild(li);
        });
      } catch (e) { list.innerHTML = '<li class="note">게시판을 불러오지 못했어요.</li>'; }
    };
    const w = el.querySelector('.cm-write');
    if (w) w.onclick = () => {
      if (!st.t) return authModal(() => w.click());
      form.hidden = !form.hidden; if (form.hidden) return;
      form.innerHTML = `<div class="cm-kinds"><label><input type="radio" name="k" value="review" checked> 후기</label><label><input type="radio" name="k" value="qna"> 질문</label><label><input type="radio" name="k" value="tip"> 팁</label>
<select class="cm-rate"><option value="">별점(후기)</option>${[5, 4, 3, 2, 1].map(n => `<option value="${n}">${'★'.repeat(n)}</option>`).join('')}</select></div>
<input class="cm-ti" maxlength="80" placeholder="제목"><textarea class="cm-tx" maxlength="3000" rows="5" placeholder="응모 과정, 결과, 팁을 나눠 주세요. 개인정보(전화번호·주소)는 쓰지 마세요."></textarea>
<p class="cm-err"></p><button class="cm-send btn2">올리기</button>`;
      form.querySelector('.cm-send').onclick = async () => {
        const k = form.querySelector('input[name=k]:checked').value;
        try { await api('/api/posts', { method: 'POST', body: { contest_id: cid, contest_title: title, kind: k, rating: k === 'review' ? +form.querySelector('.cm-rate').value || null : null,
                                                              title: form.querySelector('.cm-ti').value, body: form.querySelector('.cm-tx').value } });
              form.hidden = true; load(); }
        catch (e) { form.querySelector('.cm-err').textContent = e.message; }
      };
    };
    load();
  }
  async function comments(box, pid) {
    box.hidden = !box.hidden; if (box.hidden) return;
    box.innerHTML = '<p class="note">불러오는 중…</p>';
    const { comments } = await api('/api/comments?post=' + pid).catch(() => ({ comments: [] }));
    box.innerHTML = comments.map(c => `<div class="cm-c"><b>${esc(c.nick || '탈퇴한 회원')}</b> ${esc(c.body)} <small>${ago(c.created)}</small></div>`).join('')
      + `<div class="cm-cf"><input maxlength="1000" placeholder="${st.t ? '댓글 달기' : '로그인하고 댓글 달기'}"><button class="btn2">등록</button></div>`;
    const inp = box.querySelector('input');
    box.querySelector('.cm-cf button').onclick = async () => {
      if (!st.t) return authModal();
      try { await api('/api/comments', { method: 'POST', body: { post_id: pid, body: inp.value } }); box.hidden = true; comments(box, pid); }
      catch (e) { inp.value = ''; inp.placeholder = e.message; }
    };
  }
  async function report(btn, target) {
    if (!st.t) return authModal();
    await api('/api/report', { method: 'POST', body: { target } }).catch(() => {});
    btn.textContent = '신고됨'; btn.disabled = true;
  }
  function confirmLite(btn) { if (btn.dataset.sure) return true; btn.dataset.sure = 1; btn.textContent = '한 번 더 누르면 삭제'; return false; }



  // ---- 원정대 꾸리기 창 (공용) ----
  async function createTeam(cid, title, onDone) {
    if (!st.t) return authModal(() => createTeam(cid, title, onDone));
    const m = document.createElement('div'); m.className = 'cm-modal';
    let pick = `<p class="note">💗 히로인: ${esc(title)}</p>`, cs = [];
    if (!cid) {
      cs = await fetch('/assets/community/contests.json').then(r => r.json()).catch(() => []);
      pick = `<input class="tm-cq" list="tm-cl" placeholder="공략할 히로인(공모전) 검색 — 없으면 비워 두세요"><datalist id="tm-cl">${cs.map(c => `<option value="${esc(c.t)}"></option>`).join('')}</datalist>`;
    }
    m.innerHTML = `<div class="cm-box tm-box" role="dialog" aria-label="원정대 꾸리기"><button class="cm-x" aria-label="닫기">✕</button><h3>💘 원정대 꾸리기</h3>${pick}
<input class="tm-nm" maxlength="60" placeholder="원정대 이름 (예: 영상 공모전 같이 깰 사람)">
<textarea class="tm-in" maxlength="2000" rows="4" placeholder="어떤 원정대인지, 지금 몇 명이고 어떤 대원을 찾는지 적어 주세요."></textarea>
<input class="tm-rl" maxlength="200" placeholder="찾는 역할, 쉼표로 (예: 기획, 디자인, 영상 편집)">
<div class="tm-row"><label>정원 <select class="tm-sz">${[2, 3, 4, 5, 6, 8, 10].map(n => `<option${n === 4 ? ' selected' : ''}>${n}</option>`).join('')}</select>명</label><label>모집 마감 <input type="date" class="tm-dl"></label></div>
<input class="tm-ct" maxlength="300" placeholder="연락 방법 (예: 카카오톡 오픈채팅 링크) — 수락한 대원에게만 보여요">
<p class="cm-err"></p><button class="tm-send btn2">💘 원정대 출발!</button></div>`;
    document.body.appendChild(m);
    m.querySelector('.cm-x').onclick = () => m.remove(); m.onclick = e => { if (e.target === m) m.remove(); };
    const q = s => m.querySelector(s);
    q('.tm-send').onclick = async () => {
      let c_id = cid, c_t = title;
      if (!cid) { const v = q('.tm-cq').value.trim(), hit = cs.find(c => c.t === v); c_id = hit ? hit.id : 'free'; c_t = hit ? hit.t : v; }
      try {
        const { id } = await api('/api/teams', { method: 'POST', body: { contest_id: c_id, contest_title: c_t, name: q('.tm-nm').value, intro: q('.tm-in').value,
          roles: q('.tm-rl').value, size: +q('.tm-sz').value, deadline: q('.tm-dl').value, contact: q('.tm-ct').value } });
        ga('party_create', { contest_id: c_id }); m.remove(); onDone && onDone(id); teamModal(id, onDone && (() => onDone()));
      } catch (e) { q('.cm-err').textContent = e.message; }
    };
  }
  // ---- 팀 모집 (공모전 상세 #cm-teams[data-contest], 전체 /community/ #cm-teams[data-all]) ----
  const ROLE_EX = ['기획', '디자인', '개발', '영상 편집', '글쓰기', '발표'];
  const tag = s => `<span class="tm-role">${esc(s)}</span>`;
  async function teams(el) {
    const cid = el.dataset.contest || '', title = el.dataset.title || '', all = 'all' in el.dataset;
    el.innerHTML = `<div class="cm-head"><h2>💘 ${all ? '원정대 모집' : '이 공모전 원정대'}</h2><button class="tm-new btn2">💘 원정대 꾸리기</button></div>
${all ? '<div class="tm-mine" hidden></div>' : ''}<div class="cm-form" hidden></div><ul class="tm-list"><li class="note">불러오는 중…</li></ul>`;
    const list = el.querySelector('.tm-list'), form = el.querySelector('.cm-form');
    const load = async () => {
      try {
        const { teams } = await api('/api/teams' + (cid ? '?contest=' + encodeURIComponent(cid) : ''));
        list.innerHTML = teams.length ? '' : `<li class="cm-empty">${all ? '아직 결성된 원정대가 없어요. 첫 원정대를 만들어 보세요!' : '아직 이 히로인을 노리는 원정대가 없어요. 원정대를 꾸려 같이 나갈 사람을 모아 보세요!'}</li>`;
        teams.forEach(t => {
          const li = document.createElement('li'); li.className = 'tm-card' + (t.status === 'closed' ? ' closed' : '');
          const pr = t.prefs || {}; li.style.setProperty('--tc', pr.color || '#7c3aed');
          const full = t.cnt >= t.size;
          li.innerHTML = `<div class="cm-meta"><span class="tm-st ${t.status === 'closed' || full ? 'off' : 'on'}">${t.status === 'closed' ? '모집 마감' : full ? '정원 참' : '대원 모집 중'}</span><span>👥 ${t.cnt}/${t.size}명</span>${t.deadline ? `<span>~${esc(t.deadline.slice(5).replace('-', '/'))}</span>` : ''}<span>${esc(t.leader || '탈퇴한 회원')} · ${ago(t.created)}</span></div>
${pr.cover ? `<div class="tm-ccov" style="background-image:url(${imgUrl(pr.cover)})"></div>` : ''}<h3>${esc(pr.emoji || '🚩')} ${esc(t.name)}</h3>${all && t.contest_id !== 'free' ? `<a class="cm-on" href="/c/${esc(t.contest_id)}/">📌 ${esc(t.contest_title || t.contest_id)}</a>` : ''}<p class="cm-body">${esc(t.intro)}</p>
<div class="tm-roles">${t.roles ? t.roles.split(',').map(tag).join('') : ''}</div><div class="cm-acts"><button class="tm-open btn2 ghost">살펴보기 · 합류</button></div>`;
          li.querySelector('.tm-open').onclick = () => teamModal(t.id, load);
          list.appendChild(li);
        });
      } catch (e) { list.innerHTML = '<li class="note">팀 목록을 불러오지 못했어요.</li>'; }
      const mine = el.querySelector('.tm-mine');
      if (mine && st.t) {
        const { teams: my } = await api('/api/myteams').catch(() => ({ teams: [] }));
        mine.hidden = !my.length;
        mine.innerHTML = '<h3>🚩 내 원정대</h3>' + my.map(t => `<button class="tm-my" data-id="${t.id}">${t.leader ? '👑' : t.state === 'accepted' ? '✅' : '⏳'} ${esc(t.name)}${t.leader && t.waiting ? ` <b class="tm-wait">신청 ${t.waiting}</b>` : ''}${!t.leader && t.state === 'pending' ? ' <small>대장 답 기다리는 중</small>' : ''}${t.state === 'rejected' ? ' <small>거절됨</small>' : ''}</button>`).join('');
        mine.querySelectorAll('.tm-my').forEach(b => b.onclick = () => teamModal(+b.dataset.id, load));
      }
    };
    el.querySelector('.tm-new').onclick = () => createTeam(cid, title, () => load());
    load();
  }

  // ---- 이미지: 폰에서 고른 사진을 줄여 webp data URL 로 (표지 960x540 꽉 채움, 사진첩 긴 변 1280) ----
  function shrink(file, cover) {
    return new Promise((ok, no) => {
      const im = new Image(); im.onload = () => {
        const c = document.createElement('canvas'), x = c.getContext('2d');
        if (cover) { c.width = 960; c.height = 540; const r = Math.max(960 / im.width, 540 / im.height), w = im.width * r, h = im.height * r; x.drawImage(im, (960 - w) / 2, (540 - h) / 2, w, h); }
        else { const r = Math.min(1, 1280 / Math.max(im.width, im.height)); c.width = Math.round(im.width * r); c.height = Math.round(im.height * r); x.drawImage(im, 0, 0, c.width, c.height); }
        let q = 0.82, d = c.toDataURL('image/webp', q); while (d.length > 400000 && q > 0.4) { q -= 0.12; d = c.toDataURL('image/webp', q); }
        URL.revokeObjectURL(im.src); ok(d);
      }; im.onerror = () => no(new Error('이미지를 읽지 못했어요.')); im.src = URL.createObjectURL(file);
    });
  }
  const pick = () => new Promise(ok => { const i = document.createElement('input'); i.type = 'file'; i.accept = 'image/*'; i.onchange = () => ok(i.files[0]); i.click(); });
  const imgUrl = (id, priv) => API + '/api/img/' + id + (priv && st.t ? '?t=' + st.t : '');
  const COLORS = ['#7c3aed', '#ec4899', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#334155'];
  const EMOJIS = ['🚩', '🚀', '🔥', '🎬', '✍️', '🎨', '💡', '📸', '🎯', '🏆', '⚡', '🌱'];
  // 원정대 설정: 내 꾸미기처럼 탭(기본 정보 / 표지 / 색·깃발)
  async function teamSettings(id, d, done) {
    const t = d.team, pr = d.prefs || {};
    const m = document.createElement('div'); m.className = 'cm-modal';
    m.innerHTML = `<div class="cm-box tm-box ts-box"><button class="cm-x" aria-label="닫기">✕</button><h3>⚙️ 원정대 설정</h3>
<div class="vn-tabs ts-tabs"><button data-t="info" class="on">📝 기본 정보</button><button data-t="cover">🖼 표지</button><button data-t="look">🎨 색·깃발</button></div>
<div class="ts-p" data-p="info"><input class="tm-nm" maxlength="60" value="${esc(t.name)}" placeholder="원정대 이름"><textarea class="tm-in" maxlength="2000" rows="4">${esc(t.intro)}</textarea>
<input class="tm-rl" maxlength="200" value="${esc(t.roles)}" placeholder="찾는 역할, 쉼표로"><div class="tm-row"><label>정원 <select class="tm-sz">${[2, 3, 4, 5, 6, 8, 10].map(n => `<option${n === t.size ? ' selected' : ''}>${n}</option>`).join('')}</select>명</label><label>모집 마감 <input type="date" class="tm-dl" value="${esc(t.deadline)}"></label></div>
<input class="tm-ct" maxlength="300" value="${esc(t.contact)}" placeholder="연락 방법 (수락한 대원에게만 보여요)"></div>
<div class="ts-p" data-p="cover" hidden><div class="ts-cover" style="${pr.cover ? `background-image:url(${imgUrl(pr.cover)})` : ''}">${pr.cover ? '' : '표지 없음'}</div><button class="btn2 ts-up">📷 표지 사진 올리기</button><p class="note">가로 16:9로 맞춰 줄여 올려요. 누구나 볼 수 있어요.</p></div>
<div class="ts-p" data-p="look" hidden><b>테마 색</b><div class="ts-colors">${COLORS.map(c => `<button data-c="${c}" style="background:${c}" class="${(pr.color || COLORS[0]) === c ? 'on' : ''}"></button>`).join('')}</div>
<b>깃발</b><div class="ts-emojis">${EMOJIS.map(e => `<button data-e="${e}" class="${(pr.emoji || '🚩') === e ? 'on' : ''}">${e}</button>`).join('')}</div></div>
<p class="cm-err"></p><button class="btn2 ts-save">저장</button></div>`;
    document.body.appendChild(m);
    const q = s => m.querySelector(s), close = () => { m.remove(); done && done(); };
    q('.cm-x').onclick = close; m.onclick = e => { if (e.target === m) close(); };
    m.querySelectorAll('.ts-tabs button').forEach(b => b.onclick = () => { m.querySelectorAll('.ts-tabs button').forEach(x => x.classList.toggle('on', x === b)); m.querySelectorAll('.ts-p').forEach(x => x.hidden = x.dataset.p !== b.dataset.t); });
    let color = pr.color || COLORS[0], emoji = pr.emoji || '🚩';
    m.querySelectorAll('[data-c]').forEach(b => b.onclick = () => { color = b.dataset.c; m.querySelectorAll('[data-c]').forEach(x => x.classList.toggle('on', x === b)); });
    m.querySelectorAll('[data-e]').forEach(b => b.onclick = () => { emoji = b.dataset.e; m.querySelectorAll('[data-e]').forEach(x => x.classList.toggle('on', x === b)); });
    q('.ts-up').onclick = async () => {
      const f = await pick(); if (!f) return; q('.ts-up').textContent = '올리는 중…';
      try { const data = await shrink(f, true); const r = await api(`/api/teams/${id}/image`, { method: 'POST', body: { kind: 'cover', data } }); ga('party_cover', {});
            q('.ts-cover').style.backgroundImage = `url(${imgUrl(r.id)})`; q('.ts-cover').textContent = ''; q('.ts-up').textContent = '📷 다른 사진으로 바꾸기'; }
      catch (e) { q('.cm-err').textContent = e.message; q('.ts-up').textContent = '📷 표지 사진 올리기'; }
    };
    q('.ts-save').onclick = async () => {
      try { await api(`/api/teams/${id}/edit`, { method: 'POST', body: { name: q('.tm-nm').value, intro: q('.tm-in').value, roles: q('.tm-rl').value, size: +q('.tm-sz').value, deadline: q('.tm-dl').value, contact: q('.tm-ct').value, color, emoji } }); close(); }
      catch (e) { q('.cm-err').textContent = e.message; }
    };
  }
  async function teamModal(id, reload) {
    const m = document.createElement('div'); m.className = 'cm-modal';
    m.innerHTML = '<div class="cm-box tm-box" role="dialog" aria-label="팀"><button class="cm-x" aria-label="닫기">✕</button><div class="tm-body"><p class="note">불러오는 중…</p></div></div>';
    document.body.appendChild(m);
    const close = () => { m.remove(); reload && reload(); };
    m.querySelector('.cm-x').onclick = close; m.onclick = e => { if (e.target === m) close(); };
    const body = m.querySelector('.tm-body');
    const draw = async () => {
      let d; try { d = await api('/api/teams/' + id); } catch (e) { body.innerHTML = `<p class="cm-err">${esc(e.message)}</p>`; return; }
      const t = d.team, me_ = d.me, roles = t.roles ? t.roles.split(',') : [];
      const contact = t.contact ? (/^https?:\/\//.test(t.contact) ? `<a href="${esc(t.contact)}" target="_blank" rel="noopener nofollow">${esc(t.contact)}</a>` : esc(t.contact)) : '';
      let act = '';
      if (me_.leader) {
        act = `<h4>합류 신청 ${d.applicants.length}명</h4>${d.applicants.length ? d.applicants.map(a => `<div class="tm-app"><b>${esc(a.nick || '탈퇴한 회원')}</b>${a.role ? ' ' + tag(a.role) : ''}<p>${esc(a.msg) || '<span class="note">한마디 없음</span>'}</p><button class="btn2" data-ok="${a.uid}">수락</button> <button class="btn2 ghost" data-no="${a.uid}">거절</button></div>`).join('') : '<p class="note">아직 합류 신청이 없어요. 링크를 뿌려 대원을 모아 보세요.</p>'}
<div class="cm-row"><button class="btn2 ghost tm-tg">${t.status === 'open' ? '모집 마감하기' : '다시 모집하기'}</button><button class="btn2 ghost tm-del">원정대 해산</button></div>`;
      } else if (me_.state === 'accepted') act = `<p class="tm-okmsg">💖 이 원정대의 대원이에요!</p><button class="btn2 ghost tm-lv">원정대 나가기</button>`;
      else if (me_.state === 'pending') act = '<p class="note">⏳ 합류 신청을 보냈어요. 대장이 수락하면 연락 방법이 여기 보여요.</p>';
      else if (t.status !== 'open') act = '<p class="note">모집이 끝난 원정대예요.</p>';
      else act = `<h4>이 원정대에 합류 신청</h4>${me_.state === 'rejected' ? '<p class="note">지난 신청은 거절됐어요. 다시 신청할 수 있어요.</p>' : ''}
<select class="tm-ar"><option value="">맡고 싶은 역할</option>${roles.map(r => `<option>${esc(r)}</option>`).join('')}<option>기타</option></select>
<textarea class="tm-am" maxlength="500" rows="3" placeholder="간단한 자기소개, 해 본 것, 가능한 시간 등. 전화번호는 쓰지 마세요."></textarea><p class="cm-err"></p><button class="btn2 tm-ap">💌 합류 신청</button>`;
      const pr = d.prefs || {}, col = pr.color || '#7c3aed';
      m.querySelector('.tm-box').style.setProperty('--tc', col);
      const head = `<div class="tm-cov" style="${pr.cover ? `background-image:url(${imgUrl(pr.cover)})` : `background:linear-gradient(135deg,${col},#1e1b4b)`}"><span class="tm-flag">${esc(pr.emoji || '🚩')}</span></div>`;
      const album = (me_.leader || me_.state === 'accepted') ? `<h4>📸 원정대 사진첩 <small>대원끼리만 봐요</small></h4><div class="tm-album">${(d.album || []).map(a => `<figure><img src="${imgUrl(a.id, true)}" alt="" loading="lazy"><figcaption>${esc(a.nick || '')}${a.caption ? ' · ' + esc(a.caption) : ''}${a.mine || me_.leader ? ` <button data-rm="${a.id}">지우기</button>` : ''}</figcaption></figure>`).join('') || '<p class="note">아직 사진이 없어요. 시안·참고 자료를 올려 보세요.</p>'}</div><div class="cm-row"><input class="tm-cap" maxlength="100" placeholder="사진 설명 (선택)"><button class="btn2 tm-pic">📷 사진 올리기</button></div>` : '';
      body.innerHTML = head + (me_.leader ? '<button class="btn2 tm-set">⚙️ 원정대 설정</button>' : '') + `<div class="cm-meta"><span class="tm-st ${t.status === 'open' ? 'on' : 'off'}">${t.status === 'open' ? '대원 모집 중' : '모집 마감'}</span><span>👥 ${d.members.length}/${t.size}명</span>${t.deadline ? `<span>마감 ${esc(t.deadline)}</span>` : ''}</div>
<h3>${esc(t.name)}</h3>${t.contest_id !== 'free' ? `<a class="cm-on" href="/c/${esc(t.contest_id)}/">📌 ${esc(t.contest_title || t.contest_id)}</a>` : t.contest_title ? `<p class="note">📌 ${esc(t.contest_title)}</p>` : ''}
<p class="cm-body">${esc(t.intro)}</p>${roles.length ? `<div class="tm-roles">찾는 역할 ${roles.map(tag).join('')}</div>` : ''}
<h4>대원</h4><div class="tm-mem">${d.members.map(x => `<span>${x.role === '팀장' ? '👑' : '🙂'} ${esc(x.nick || '탈퇴한 회원')}${x.role ? ' · ' + esc(x.role === '팀장' ? '대장' : x.role) : ''}</span>`).join('')}</div>
${contact ? `<div class="tm-ct2">📞 연락 방법: ${contact}</div>` : ''}
${st.t ? act : '<button class="btn2 tm-login">가입하고 합류 신청</button>'}
${album}<div class="cm-acts"><button class="tm-share">링크 복사</button>${st.t && !me_.leader ? '<button class="tm-rp">신고</button>' : ''}</div>`;
      const q = s => body.querySelector(s);
      if (q('.tm-set')) q('.tm-set').onclick = () => teamSettings(id, d, draw);
      if (q('.tm-pic')) q('.tm-pic').onclick = async () => {
        const f = await pick(); if (!f) return; q('.tm-pic').textContent = '올리는 중…';
        try { await api(`/api/teams/${id}/image`, { method: 'POST', body: { kind: 'post', data: await shrink(f, false), caption: q('.tm-cap').value } }); ga('party_photo', {}); draw(); }
        catch (e) { q('.tm-pic').textContent = e.message; }
      };
      body.querySelectorAll('[data-rm]').forEach(b => b.onclick = async () => { if (confirmLite(b)) { await api(`/api/teams/${id}/unimage`, { method: 'POST', body: { id: +b.dataset.rm } }); draw(); } });
      body.querySelectorAll('[data-ok],[data-no]').forEach(b => b.onclick = async () => {
        try { await api(`/api/teams/${id}/decide`, { method: 'POST', body: { uid: +(b.dataset.ok || b.dataset.no), accept: !!b.dataset.ok } }); ga('party_decide', { accept: !!b.dataset.ok }); draw(); } catch (e) { b.textContent = e.message; }
      });
      if (q('.tm-tg')) q('.tm-tg').onclick = async () => { await api(`/api/teams/${id}/${t.status === 'open' ? 'close' : 'open'}`, { method: 'POST' }); draw(); };
      if (q('.tm-del')) q('.tm-del').onclick = async e => { if (confirmLite(e.currentTarget)) { await api('/api/teams/' + id, { method: 'DELETE' }); close(); } };
      if (q('.tm-lv')) q('.tm-lv').onclick = async e => { if (confirmLite(e.currentTarget)) { await api(`/api/teams/${id}/leave`, { method: 'POST' }); draw(); } };
      if (q('.tm-ap')) q('.tm-ap').onclick = async () => {
        try { await api(`/api/teams/${id}/apply`, { method: 'POST', body: { role: q('.tm-ar').value, msg: q('.tm-am').value } }); ga('party_apply', { team_id: id }); draw(); }
        catch (e) { q('.cm-err').textContent = e.message; }
      };
      if (q('.tm-login')) q('.tm-login').onclick = () => authModal(draw);
      if (q('.tm-rp')) q('.tm-rp').onclick = e => report(e.currentTarget, 't:' + id);
      q('.tm-share').onclick = e => { const u = location.origin + '/community/#team-' + id; (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(() => e.target.textContent = '복사됐어요', () => prompt('링크', u)); };
    };
    draw();
  }

  // ---- 커뮤니티 탭 ----
  function tabs() {
    const bar = document.querySelector('.cm-tabs'); if (!bar) return;
    const show = k => { bar.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.k === k)); document.querySelectorAll('[data-tab]').forEach(s => s.hidden = s.dataset.tab !== k); };
    bar.querySelectorAll('button').forEach(b => b.onclick = () => show(b.dataset.k));
    const j = document.querySelector('.cm-join-cta'); if (j) { j.hidden = !!st.t; j.onclick = () => authModal(() => location.reload()); }
    show('team');
    const h = location.hash.match(/^#team-(\d+)$/); if (h) teamModal(+h[1]);
  }

  // ---- 로그인한 사람이 고른 루리 옷으로 사이트 전체 루리 일괄 갈아입히기 ----
  const KEEP = /\/assets\/ruri\/(avatar|profile|og)\b/;
  const prefs = () => { try { return JSON.parse(localStorage.getItem('jupjup_prefs') || '{}'); } catch { return {}; } };
  // 포즈 세트: /assets/ruri/poses.json = {"office": ["wave", ...], "<복장키>": [...]} → /assets/ruri/p/<복장>_<포즈>(_s).webp
  // 같은 복장이라도 자리(맥락)·접속마다 포즈가 바뀜. 세트가 없는 복장은 기존 단일 이미지.
  let POSES = null; const seed = Math.floor(Math.random() * 1e6);
  const POSE_OF = { smile: 'wave', wink: 'wink', excited: 'v', thumbsup: 'clap', think: 'think', sad: 'awkward', surprise: 'surprise', serious: 'point' };
  const ctxPose = (img, base) => img.id === 'hero-ruri' ? ['wave', 'v', 'clap'][seed % 3] : img.closest('.shot') ? 'surprise' : img.closest('.empty') ? 'think' : POSE_OF[base] || '';  // 그 밖(말풍선 등)은 표정 따라, 없으면 순번·접속마다 순환
  function poseSrc(outfit, want, small, salt = 0) {  // outfit: 'office' | 'cardigan' ..., want: 원하는 포즈(없으면 순환)
    const list = POSES && POSES[outfit]; if (!list || !list.length) return '';
    const pose = list.includes(want) ? want : list[(seed + salt) % list.length];
    return `/assets/ruri/p/${outfit}_${pose}${small ? '_s' : ''}.webp`;
  }
  let wearN = 0;
  function wearOne(img) {
    if (img.closest('#vn')) return;
    const o = st.t ? prefs().o : '', src = img.getAttribute('src') || '', m = src.match(/^\/assets\/ruri\/([a-z_]+?)(_s)?\.webp$/);
    if (!m || KEEP.test(src)) return;
    if (!img.dataset.ruri) { img.dataset.ruri = m[1]; img.dataset.rn = wearN++; }
    const base = img.dataset.ruri, outfit = o && o !== 'smile' ? o.replace(/^o_/, '') : /^o_/.test(base) ? base.slice(2) : 'office';  // 로그인 옷 > 원래 자리 옷 > 오피스룩
    const ps = poseSrc(outfit, ctxPose(img, img.dataset.ruri), !!m[2], +img.dataset.rn);
    const nsrc = ps || `/assets/ruri/${o && o !== 'smile' ? o : img.dataset.ruri}${m[2] || ''}.webp`;
    if (src !== nsrc) img.setAttribute('src', nsrc);
  }
  function wearAll() { document.querySelectorAll('img[src^="/assets/ruri/"]').forEach(wearOne); }
  async function syncPrefs() {  // 다른 기기에서 고른 옷도 따라오게: 로그인 상태면 하루 한 번 서버 값 가져오기
    if (!st.t) return;
    let last = 0; try { last = +localStorage.getItem('jupjup_prefs_t') || 0; } catch {}
    if (Date.now() - last < 864e5 && localStorage.getItem('jupjup_prefs')) return;
    const me = await api('/api/me').catch(() => null); if (!me) return;
    try { localStorage.setItem('jupjup_prefs', JSON.stringify(me.prefs || {})); localStorage.setItem('jupjup_prefs_t', Date.now()); } catch {}
    wearAll();
  }
  new MutationObserver(ms => ms.forEach(m => { if (m.type === 'attributes') wearOne(m.target); else m.addedNodes.forEach(n => { if (n.nodeType === 1) { if (n.tagName === 'IMG') wearOne(n); else n.querySelectorAll && n.querySelectorAll('img[src^="/assets/ruri/"]').forEach(wearOne); } }); }))
    .observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['src'] });
  fetch('/assets/ruri/poses.json').then(r => r.ok ? r.json() : null).catch(() => null).then(j => { POSES = j; wearAll(); }); syncPrefs();
  paintBar();
  document.querySelectorAll('#cm-teams').forEach(teams);
  document.querySelectorAll('#cm-board').forEach(board);
  tabs();
  window.JUP = { api, st, esc, ago, authModal, teamModal, createTeam, teams, wearAll, ga, poseSrc, POSE_OF, poses: () => POSES };
})();
