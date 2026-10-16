// 루리의 줍줍 커뮤니티 — 공모전별 팀 모집(만들기·신청·수락) + 후기·질문 게시판 (API: Cloudflare Worker, 주소는 <body data-api>)
// 가입은 이메일+비밀번호만. 표시 이름은 가린 이메일.
(function () {
  const API = document.body.dataset.api; if (!API) return;
  const KEY = 'jupjup_tok', NK = 'jupjup_nick';
  const st = { get t() { try { return localStorage.getItem(KEY) || ''; } catch { return ''; } }, get n() { try { return localStorage.getItem(NK) || ''; } catch { return ''; } },
    set(t, n) { try { if (t) { localStorage.setItem(KEY, t); localStorage.setItem(NK, n); } else { localStorage.removeItem(KEY); localStorage.removeItem(NK); } } catch {} } };
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
<h3>루리의 줍줍 로그인</h3><p class="note">이메일과 비밀번호만 있으면 돼요. 다른 정보는 받지 않아요.</p>
<input type="email" class="cm-em" placeholder="이메일" autocomplete="email"><input type="password" class="cm-pw" placeholder="비밀번호 (8자 이상)" autocomplete="current-password">
<p class="cm-err"></p><div class="cm-row"><button class="cm-login btn2">로그인</button><button class="cm-join btn2 ghost">처음이에요, 가입</button></div>
<p class="note">가입하면 <a href="/terms/">이용약관</a>과 <a href="/privacy/">개인정보처리방침</a>에 동의한 것으로 봐요. 글쓴이 이름은 이메일 앞부분을 가려서(예: sun***) 표시해요.</p></div>`;
    document.body.appendChild(m);
    const em = m.querySelector('.cm-em'), pw = m.querySelector('.cm-pw'), er = m.querySelector('.cm-err');
    const go = async path => {
      er.textContent = '';
      try { const j = await api(path, { method: 'POST', body: { email: em.value, password: pw.value } }); st.set(j.token, j.nick); m.remove(); onDone && onDone(); paintBar(); }
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
    b.innerHTML = st.t ? `<span>${esc(st.n)}</span><button class="cm-out">로그아웃</button>` : '<button class="cm-in">로그인</button>';
    const i = b.querySelector('.cm-in'), o = b.querySelector('.cm-out');
    if (i) i.onclick = () => authModal(() => location.reload());
    if (o) o.onclick = async () => { await api('/api/logout', { method: 'POST' }).catch(() => {}); st.set(''); location.reload(); };
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


  // ---- 팀 모집 (공모전 상세 #cm-teams[data-contest], 전체 /community/ #cm-teams[data-all]) ----
  const ROLE_EX = ['기획', '디자인', '개발', '영상 편집', '글쓰기', '발표'];
  const tag = s => `<span class="tm-role">${esc(s)}</span>`;
  async function teams(el) {
    const cid = el.dataset.contest || '', title = el.dataset.title || '', all = 'all' in el.dataset;
    el.innerHTML = `<div class="cm-head"><h2>🤝 ${all ? '팀원 모집' : '이 공모전 같이 나갈 팀'}</h2><button class="tm-new btn2">+ 팀 만들기</button></div>
${all ? '<div class="tm-mine" hidden></div>' : ''}<div class="cm-form" hidden></div><ul class="tm-list"><li class="note">불러오는 중…</li></ul>`;
    const list = el.querySelector('.tm-list'), form = el.querySelector('.cm-form');
    const load = async () => {
      try {
        const { teams } = await api('/api/teams' + (cid ? '?contest=' + encodeURIComponent(cid) : ''));
        list.innerHTML = teams.length ? '' : `<li class="cm-empty">${all ? '아직 모집 중인 팀이 없어요. 나가고 싶은 공모전이 있다면 첫 팀을 만들어 보세요!' : '아직 이 공모전 팀이 없어요. 팀을 만들어 같이 나갈 사람을 모아 보세요!'}</li>`;
        teams.forEach(t => {
          const li = document.createElement('li'); li.className = 'tm-card' + (t.status === 'closed' ? ' closed' : '');
          const full = t.cnt >= t.size;
          li.innerHTML = `<div class="cm-meta"><span class="tm-st ${t.status === 'closed' || full ? 'off' : 'on'}">${t.status === 'closed' ? '모집 마감' : full ? '정원 참' : '모집 중'}</span><span>👥 ${t.cnt}/${t.size}명</span>${t.deadline ? `<span>~${esc(t.deadline.slice(5).replace('-', '/'))}</span>` : ''}<span>${esc(t.leader || '탈퇴한 회원')} · ${ago(t.created)}</span></div>
<h3>${esc(t.name)}</h3>${all && t.contest_id !== 'free' ? `<a class="cm-on" href="/c/${esc(t.contest_id)}/">📌 ${esc(t.contest_title || t.contest_id)}</a>` : ''}<p class="cm-body">${esc(t.intro)}</p>
<div class="tm-roles">${t.roles ? t.roles.split(',').map(tag).join('') : ''}</div><div class="cm-acts"><button class="tm-open btn2 ghost">자세히 · 신청</button></div>`;
          li.querySelector('.tm-open').onclick = () => teamModal(t.id, load);
          list.appendChild(li);
        });
      } catch (e) { list.innerHTML = '<li class="note">팀 목록을 불러오지 못했어요.</li>'; }
      const mine = el.querySelector('.tm-mine');
      if (mine && st.t) {
        const { teams: my } = await api('/api/myteams').catch(() => ({ teams: [] }));
        mine.hidden = !my.length;
        mine.innerHTML = '<h3>내 팀</h3>' + my.map(t => `<button class="tm-my" data-id="${t.id}">${t.leader ? '👑' : t.state === 'accepted' ? '✅' : '⏳'} ${esc(t.name)}${t.leader && t.waiting ? ` <b class="tm-wait">신청 ${t.waiting}</b>` : ''}${!t.leader && t.state === 'pending' ? ' <small>답 기다리는 중</small>' : ''}${t.state === 'rejected' ? ' <small>거절됨</small>' : ''}</button>`).join('');
        mine.querySelectorAll('.tm-my').forEach(b => b.onclick = () => teamModal(+b.dataset.id, load));
      }
    };
    el.querySelector('.tm-new').onclick = async () => {
      if (!st.t) return authModal(() => location.reload());
      form.hidden = !form.hidden; if (form.hidden) return;
      let pick = '';
      if (all) {
        const cs = await fetch('/assets/community/contests.json').then(r => r.json()).catch(() => []);
        pick = `<input class="tm-cq" list="tm-cl" placeholder="나갈 공모전 이름 검색 (없으면 비워 두세요)"><datalist id="tm-cl">${cs.map(c => `<option value="${esc(c.t)}" data-id="${esc(c.id)}"></option>`).join('')}</datalist>`;
        form._cs = cs;
      } else pick = `<p class="note">📌 ${esc(title)}</p>`;
      form.innerHTML = `${pick}<input class="tm-nm" maxlength="60" placeholder="팀 이름 (예: 영상 공모전 같이 나갈 분)">
<textarea class="tm-in" maxlength="2000" rows="4" placeholder="어떤 팀인지, 지금 몇 명이고 어떤 사람을 찾는지 적어 주세요."></textarea>
<input class="tm-rl" maxlength="200" placeholder="찾는 역할, 쉼표로 (예: ${ROLE_EX.slice(0, 3).join(', ')})">
<div class="tm-row"><label>총 인원 <select class="tm-sz">${[2, 3, 4, 5, 6, 8, 10].map(n => `<option${n === 4 ? ' selected' : ''}>${n}</option>`).join('')}</select>명</label><label>모집 마감 <input type="date" class="tm-dl"></label></div>
<input class="tm-ct" maxlength="300" placeholder="연락 방법 (예: 카카오톡 오픈채팅 링크). 수락한 팀원에게만 보여요">
<p class="cm-err"></p><button class="tm-send btn2">팀 만들기</button>`;
      form.querySelector('.tm-send').onclick = async () => {
        let c_id = cid, c_t = title;
        if (all) { const q = form.querySelector('.tm-cq').value.trim(), hit = (form._cs || []).find(c => c.t === q); c_id = hit ? hit.id : 'free'; c_t = hit ? hit.t : q; }
        try {
          const { id } = await api('/api/teams', { method: 'POST', body: { contest_id: c_id, contest_title: c_t, name: form.querySelector('.tm-nm').value, intro: form.querySelector('.tm-in').value,
            roles: form.querySelector('.tm-rl').value, size: +form.querySelector('.tm-sz').value, deadline: form.querySelector('.tm-dl').value, contact: form.querySelector('.tm-ct').value } });
          form.hidden = true; await load(); teamModal(id, load);
        } catch (e) { form.querySelector('.cm-err').textContent = e.message; }
      };
    };
    load();
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
        act = `<h4>신청한 사람 ${d.applicants.length}명</h4>${d.applicants.length ? d.applicants.map(a => `<div class="tm-app"><b>${esc(a.nick || '탈퇴한 회원')}</b>${a.role ? ' ' + tag(a.role) : ''}<p>${esc(a.msg) || '<span class="note">한마디 없음</span>'}</p><button class="btn2" data-ok="${a.uid}">수락</button> <button class="btn2 ghost" data-no="${a.uid}">거절</button></div>`).join('') : '<p class="note">아직 신청이 없어요. 링크를 공유해 보세요.</p>'}
<div class="cm-row"><button class="btn2 ghost tm-tg">${t.status === 'open' ? '모집 마감하기' : '다시 모집하기'}</button><button class="btn2 ghost tm-del">팀 지우기</button></div>`;
      } else if (me_.state === 'accepted') act = `<p class="tm-okmsg">✅ 팀원이에요!</p><button class="btn2 ghost tm-lv">팀 나가기</button>`;
      else if (me_.state === 'pending') act = '<p class="note">⏳ 신청했어요. 팀장이 수락하면 연락 방법이 여기 보여요.</p>';
      else if (t.status !== 'open') act = '<p class="note">모집이 끝난 팀이에요.</p>';
      else act = `<h4>이 팀에 신청하기</h4>${me_.state === 'rejected' ? '<p class="note">이전 신청은 거절됐어요. 다시 신청할 수 있어요.</p>' : ''}
<select class="tm-ar"><option value="">맡고 싶은 역할</option>${roles.map(r => `<option>${esc(r)}</option>`).join('')}<option>기타</option></select>
<textarea class="tm-am" maxlength="500" rows="3" placeholder="간단한 자기소개, 해 본 것, 가능한 시간 등. 전화번호는 쓰지 마세요."></textarea><p class="cm-err"></p><button class="btn2 tm-ap">신청하기</button>`;
      body.innerHTML = `<div class="cm-meta"><span class="tm-st ${t.status === 'open' ? 'on' : 'off'}">${t.status === 'open' ? '모집 중' : '모집 마감'}</span><span>👥 ${d.members.length}/${t.size}명</span>${t.deadline ? `<span>마감 ${esc(t.deadline)}</span>` : ''}</div>
<h3>${esc(t.name)}</h3>${t.contest_id !== 'free' ? `<a class="cm-on" href="/c/${esc(t.contest_id)}/">📌 ${esc(t.contest_title || t.contest_id)}</a>` : t.contest_title ? `<p class="note">📌 ${esc(t.contest_title)}</p>` : ''}
<p class="cm-body">${esc(t.intro)}</p>${roles.length ? `<div class="tm-roles">찾는 역할 ${roles.map(tag).join('')}</div>` : ''}
<h4>팀원</h4><div class="tm-mem">${d.members.map(x => `<span>${x.role === '팀장' ? '👑' : '🙂'} ${esc(x.nick || '탈퇴한 회원')}${x.role ? ' · ' + esc(x.role) : ''}</span>`).join('')}</div>
${contact ? `<div class="tm-ct2">📞 연락 방법: ${contact}</div>` : ''}
${st.t ? act : '<button class="btn2 tm-login">로그인하고 신청하기</button>'}
<div class="cm-acts"><button class="tm-share">링크 복사</button>${st.t && !me_.leader ? '<button class="tm-rp">신고</button>' : ''}</div>`;
      const q = s => body.querySelector(s);
      body.querySelectorAll('[data-ok],[data-no]').forEach(b => b.onclick = async () => {
        try { await api(`/api/teams/${id}/decide`, { method: 'POST', body: { uid: +(b.dataset.ok || b.dataset.no), accept: !!b.dataset.ok } }); draw(); } catch (e) { b.textContent = e.message; }
      });
      if (q('.tm-tg')) q('.tm-tg').onclick = async () => { await api(`/api/teams/${id}/${t.status === 'open' ? 'close' : 'open'}`, { method: 'POST' }); draw(); };
      if (q('.tm-del')) q('.tm-del').onclick = async e => { if (confirmLite(e.currentTarget)) { await api('/api/teams/' + id, { method: 'DELETE' }); close(); } };
      if (q('.tm-lv')) q('.tm-lv').onclick = async e => { if (confirmLite(e.currentTarget)) { await api(`/api/teams/${id}/leave`, { method: 'POST' }); draw(); } };
      if (q('.tm-ap')) q('.tm-ap').onclick = async () => {
        try { await api(`/api/teams/${id}/apply`, { method: 'POST', body: { role: q('.tm-ar').value, msg: q('.tm-am').value } }); draw(); }
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

  paintBar();
  document.querySelectorAll('#cm-teams').forEach(teams);
  document.querySelectorAll('#cm-board').forEach(board);
  tabs();
})();
