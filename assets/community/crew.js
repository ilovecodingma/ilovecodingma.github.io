// 동료 찾기·공유 (2026-10-18 사용자: 공유하기 + 같은 사람이 모이는 구조 + 원정대 활성화로 같이 공모전 참가)
// - #cm-crew[data-contest] : 이 공모전 준비 중 N명 · 동료 찾는 사람 · 모집 중 원정대 · 부르기
// - #cm-crew[data-all]     : 전체 최근 동료 찾는 사람 (원정대 페이지)
// - window.JCREW.share({title, text, path}) : 폰 공유창(없으면 링크 복사), 로그인 시 초대 코드(?ref=) 붙임
(function () {
  const ROLES = ['기획', '아이디어', '글쓰기', '디자인', '영상 편집', '사진', '개발', '발표'];
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  let J = null;
  const ready = async () => { for (let i = 0; i < 50 && !window.JUP; i++) await new Promise(r => setTimeout(r, 100)); J = window.JUP; return !!J; };
  const esc = s => J.esc(s);
  async function refCode() {
    if (!J.st.t) return '';
    try { const c = localStorage.getItem('jupjup_code'); if (c) return c; } catch {}
    const me = await J.api('/api/me').catch(() => null); if (!me || !me.code) return '';
    try { localStorage.setItem('jupjup_code', me.code); } catch {} return me.code;
  }
  async function share({ title, text, path }) {
    const code = await refCode(), url = location.origin + path + (code ? (path.includes('?') ? '&' : '?') + 'ref=' + code : '');
    ga('share', { method: navigator.share ? 'native' : 'copy', content_type: path.split('/')[1] || 'page' });
    if (navigator.share) { try { await navigator.share({ title, text, url }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    const m = document.createElement('div'); m.className = 'cm-modal';
    m.innerHTML = `<div class="cm-box cr-share"><button class="cm-x" aria-label="닫기">✕</button><h3>📤 공유하기</h3><p class="note">${esc(text)}</p>
<input class="cr-url" readonly value="${esc(url)}"><button class="btn2 cr-copy">🔗 링크 복사</button>
<p class="note">복사해서 카카오톡·문자·DM에 붙여 넣으면 돼요.${code ? ' 이 링크로 친구가 오면 초대 점수도 쌓여요 🎀' : ''}</p></div>`;
    document.body.appendChild(m);
    m.querySelector('.cm-x').onclick = () => m.remove(); m.onclick = e => { if (e.target === m) m.remove(); };
    const inp = m.querySelector('.cr-url'), b = m.querySelector('.cr-copy');
    b.onclick = () => { inp.select(); (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).catch(() => document.execCommand('copy')).finally(() => { b.textContent = '✅ 복사했어요'; }); };
  }
  const ago = ts => J.ago ? J.ago(ts) : '';
  const tags = r => r ? r.split(',').map(x => `<span class="tm-role">${esc(x)}</span>`).join('') : '';
  async function mount(el) {
    if (!await ready()) return;
    if ('all' in el.dataset) return all(el);
    const cid = el.dataset.contest, title = el.dataset.title || '';
    const shareIt = () => share({ title: title + ' 같이 준비해요', text: `「${title}」 같이 준비할 사람 모여요! 루리의 줍줍에서 원정대 꾸리는 중 🚩`, path: '/c/' + cid + '/' });
    const load = async () => {
      const d = await J.api('/api/crew?c=' + encodeURIComponent(cid)).catch(() => null);
      if (!d) { el.innerHTML = ''; return; }
      const mine = d.seekers.find(s => s.me), open = d.teams.filter(t => t.status !== 'closed' && t.cnt < t.size);
      el.innerHTML = `<div class="cr-head"><h2>👥 같이 할 사람</h2><button class="cr-share-b">📤 공유</button></div>
<div class="cr-stats"><div><b>${d.preparing}</b><small>준비 중</small></div><div><b>${d.seekers.length}</b><small>동료 찾는 중</small></div><div><b>${open.length}</b><small>모집 중 원정대</small></div></div>
${d.invites.map(i => `<div class="cr-inv">📣 <b>${esc(i.leader)}</b>님의 「${esc(i.name)}」 원정대가 같이 하자고 불렀어요! <button class="btn2 cr-inv-b" data-id="${i.team_id}">살펴보기·합류</button></div>`).join('')}
<div class="cr-acts"><button class="btn2 cr-seek">${mine ? '✏️ 내 소개 고치기' : '🙋 나도 같이 할 사람 찾기'}</button><button class="btn2 ghost cr-new">💘 원정대 꾸리기</button></div>
<div class="cr-form" hidden><p class="note">잘하는 것을 고르면, 이 공모전 원정대장이 보고 불러 줘요.</p><div class="cr-roles">${ROLES.map(r => `<button data-r="${r}" class="${mine && mine.roles.split(',').includes(r) ? 'on' : ''}">${r}</button>`).join('')}</div>
<input class="cr-intro" maxlength="300" placeholder="한 줄 소개 (예: 대학생, 주말에 시간 많아요. 영상 편집 해 봤어요)" value="${esc(mine ? mine.intro : '')}"><div class="cr-row"><button class="btn2 cr-save">${mine ? '저장' : '🙋 등록하기'}</button>${mine ? '<button class="btn2 ghost cr-del">내리기</button>' : ''}</div><p class="cm-err"></p></div>
${d.seekers.length ? `<h3>🙋 동료 찾는 사람</h3><ul class="cr-list">${d.seekers.map(s => `<li><div><b>${esc(s.nick)}${s.me ? ' <small>(나)</small>' : ''}</b><span class="cr-ago">${esc(ago(s.updated))}</span></div><div class="tm-roles">${tags(s.roles)}</div>${s.intro ? `<p>${esc(s.intro)}</p>` : ''}
${!s.me && d.myTeams.length ? (s.called ? '<span class="cr-called">📣 불렀어요</span>' : `<button class="btn2 cr-call" data-u="${s.uid}">📣 우리 원정대로 부르기</button>`) : ''}</li>`).join('')}</ul>` : '<p class="cr-empty">아직 동료 찾는 사람이 없어요. 먼저 「나도 같이 할 사람 찾기」를 눌러 두면, 원정대가 생길 때 바로 불러 줘요.</p>'}
${open.length ? `<h3>🚩 모집 중 원정대</h3><ul class="cr-teams">${open.map(t => `<li><button data-id="${t.id}"><b>${esc(t.name)}</b><span>👥 ${t.cnt}/${t.size}명</span><span class="tm-roles">${tags(t.roles)}</span></button></li>`).join('')}</ul>` : ''}`;
      const q = s => el.querySelector(s), need = fn => () => J.st.t ? fn() : J.authModal(() => location.reload());
      q('.cr-share-b').onclick = shareIt;
      q('.cr-new').onclick = need(() => J.createTeam(cid, title, () => load()));
      q('.cr-seek').onclick = need(() => { q('.cr-form').hidden = !q('.cr-form').hidden; });
      el.querySelectorAll('.cr-roles button').forEach(b => b.onclick = () => b.classList.toggle('on'));
      q('.cr-save').onclick = async () => {
        const roles = [...el.querySelectorAll('.cr-roles button.on')].map(b => b.dataset.r).join(',');
        try { await J.api('/api/crew', { method: 'POST', body: { c: cid, title, roles, intro: q('.cr-intro').value } }); ga('crew_seek', { contest_id: cid }); load(); }
        catch (e) { q('.cr-form .cm-err').textContent = e.message; }
      };
      const del = q('.cr-del'); if (del) del.onclick = async () => { await J.api('/api/crew', { method: 'POST', body: { c: cid, del: 1 } }).catch(() => {}); load(); };
      el.querySelectorAll('.cr-call').forEach(b => b.onclick = async () => {
        try { await J.api('/api/crew/invite', { method: 'POST', body: { team: d.myTeams[0], user: +b.dataset.u } }); ga('crew_call', { contest_id: cid }); b.outerHTML = '<span class="cr-called">📣 불렀어요</span>'; }
        catch (e) { b.textContent = e.message; }
      });
      el.querySelectorAll('.cr-inv-b, .cr-teams button').forEach(b => b.onclick = () => J.teamModal(+b.dataset.id, load));
    };
    el.innerHTML = '<p class="note">같이 할 사람 불러오는 중…</p>';
    load();
  }
  async function all(el) {
    const d = await J.api('/api/crew').catch(() => ({ seekers: [] }));
    el.innerHTML = `<div class="cr-head"><h2>🙋 지금 동료 찾는 사람</h2></div>${d.seekers.length ? `<ul class="cr-list">${d.seekers.map(s => `<li><div><b>${esc(s.nick)}</b><span class="cr-ago">${esc(ago(s.updated))}</span></div><a class="cm-on" href="/c/${esc(s.contest_id)}/#cm-crew">📌 ${esc(s.contest_title || s.contest_id)}</a><div class="tm-roles">${tags(s.roles)}</div>${s.intro ? `<p>${esc(s.intro)}</p>` : ''}</li>`).join('')}</ul>`
      : '<p class="cr-empty">아직 없어요. 준비 중인 공모전 페이지에서 「나도 같이 할 사람 찾기」를 눌러 보세요.</p>'}`;
  }
  // 나를 부른 원정대 → 닉네임 메뉴에 알림
  async function invites() {
    if (!await ready() || !J.st.t) return;
    const d = await J.api('/api/crew/mine').catch(() => null); if (!d || !d.invites.length) return;
    const add = () => {
      const me = document.querySelector('.cm-me'), menu = document.querySelector('.cm-menu'); if (!me || !menu) return false;
      if (!me.querySelector('.cr-dot')) me.insertAdjacentHTML('beforeend', `<i class="cr-dot">${d.invites.length}</i>`);
      if (!menu.querySelector('.cr-mi')) menu.insertAdjacentHTML('afterbegin', d.invites.map(i => `<a class="cr-mi" href="/c/${esc(i.contest_id)}/#cm-crew">📣 「${esc(i.name)}」 원정대가 불렀어요</a>`).join(''));
      return true;
    };
    if (!add()) setTimeout(add, 800);
    new MutationObserver(add).observe(document.querySelector('.hd-in') || document.body, { childList: true, subtree: true });
  }
  window.JCREW = { mount, share };
  ready().then(() => { document.querySelectorAll('#cm-crew, .cm-crew').forEach(mount); invites(); });
})();
