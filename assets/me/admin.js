// 관리자 (/admin/, 검색 노출 안 함) — 대장 계정만 서버가 숫자를 내줌
(function () {
  const A = document.getElementById('admin'), J = window.JUP; if (!A || !J) return;
  if (!J.st.t) { A.innerHTML = '<p>로그인이 필요해요.</p>'; return; }
  J.api('/api/admin').then(d => {
    const card = (k, v, s) => `<div class="ad-c"><small>${k}</small><b>${v}</b>${s ? `<em>${s}</em>` : ''}</div>`;
    const max = Math.max(1, ...d.byDay.map(x => x.n));
    A.innerHTML = `<h1>관리자</h1><div class="ad-g">${card('가입자', d.users, `오늘 +${d.users_day} · 7일 +${d.users_week}`)}${card('소셜 연결', d.social)}${card('원정대', d.teams, `모집 중 ${d.open_teams}`)}
${card('찜', d.favs)}${card('냈어요', d.applied, `당첨 ${d.won}`)}${card('알림 받는 사람', d.alerts)}${card('초대 가입', d.invites, `초대 방문 ${d.visits}`)}${card('후기·질문 글', d.posts)}</div>
<h2>최근 14일 가입</h2><div class="ad-bars">${d.byDay.map(x => `<div><i style="height:${Math.round(x.n / max * 100)}%"></i><b>${x.n}</b><small>${x.d.slice(5)}</small></div>`).join('') || '<p class="note">아직 없어요</p>'}</div>
<h2>최근 가입</h2><table class="ad-t"><tr><th>#</th><th>닉네임</th><th>가입 경로</th><th>가입일</th></tr>${d.recent.map(u => `<tr><td>${u.id}</td><td>${J.esc(u.nick)}</td><td>${J.esc(u.via)}</td><td>${new Date(u.created * 1000).toLocaleString('ko-KR')}</td></tr>`).join('')}</table>
<h2>신고 들어온 것</h2>${d.reported.length ? `<table class="ad-t"><tr><th>종류</th><th>제목</th><th>신고</th><th>숨김</th></tr>${d.reported.map(r => `<tr><td>${r.k}</td><td>${J.esc(r.t)}</td><td>${r.reports}</td><td>${r.hidden ? '숨김' : ''}</td></tr>`).join('')}</table>` : '<p class="note">없어요 👍</p>'}`;
  }).catch(e => { A.innerHTML = `<p>${J.esc(e.message)}</p>`; });
})();
