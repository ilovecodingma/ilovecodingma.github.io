// 루리의 줍줍 커뮤니티 — 공모전별 후기·질문 게시판 (API: Cloudflare Worker, 주소는 <body data-api>)
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
    el.innerHTML = `${all ? '' : `<div class="cm-head"><h2>💬 이 공모전 후기·질문</h2><button class="cm-write btn2">글쓰기</button></div>`}<div class="cm-form" hidden></div><ul class="cm-list"><li class="note">불러오는 중…</li></ul>`;
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

  paintBar();
  document.querySelectorAll('#cm-board').forEach(board);
})();
