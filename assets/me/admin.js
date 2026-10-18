// 관리자 (/admin/, 검색 노출 안 함) — 관리자 계정(ADMINS)만 서버가 숫자를 내줌
(function () {
  const A = document.getElementById('admin'), J = window.JUP; if (!A || !J) return;
  if (!J.st.t) { A.innerHTML = '<h1>관리자</h1><p>관리자 계정(사장님 구글 계정)으로 로그인하면 보여요.</p><button class="ad-login">로그인</button>'; A.querySelector('.ad-login').onclick = () => J.authModal ? J.authModal(() => location.reload()) : document.querySelector('.cm-in')?.click(); return; }
  const card = (k, v, s) => `<div class="ad-c"><small>${k}</small><b>${v}</b>${s ? `<em>${s}</em>` : ''}</div>`;
  const bars = (rows, key, lab) => { const max = Math.max(1, ...rows.map(x => x[key])); return `<div class="ad-bars">${rows.map(x => `<div><i style="height:${Math.round(x[key] / max * 100)}%"></i><b>${x[key]}</b><small>${lab(x)}</small></div>`).join('') || '<p class="note">아직 없어요</p>'}</div>`; };
  const rank = (rows, k, v) => rows.length ? `<ol class="ad-r">${rows.map(x => `<li><span>${J.esc(x[k] || '-')}</span><b>${x[v]}</b></li>`).join('')}</ol>` : '<p class="note">아직 없어요</p>';
  const ago = ts => { const m = Math.round((Date.now() / 1000 - ts) / 60); return m < 1 ? '방금' : m < 60 ? m + '분 전' : m < 1440 ? Math.round(m / 60) + '시간 전' : Math.round(m / 1440) + '일 전'; };
  let mine = false;
  function load() {
    Promise.all([J.api('/api/admin/visits' + (mine ? '?mine=1' : '')), J.api('/api/admin')]).then(([v, d]) => {
      A.innerHTML = `<h1>관리자</h1>
<h2>👀 방문자 <label class="ad-mine"><input type="checkbox" ${mine ? 'checked' : ''}> 내 방문 포함</label></h2>
<div class="ad-g">${card('오늘 방문자', v.today.v || 0, `페이지 ${v.today.pv || 0}회`)}${card('지금 (30분)', v.live.v || 0)}${card('누적 방문', v.total.v || 0, v.total.since ? v.total.since.slice(5).replace('-', '/') + '부터 · 페이지 ' + v.total.pv + '회' : '')}${card('폰으로 본 비율', v.mobile.v ? Math.round(v.mobile.m / v.mobile.v * 100) + '%' : '-', '최근 7일')}</div>
<h2>최근 14일 방문자</h2>${bars(v.byDay, 'v', x => x.d.slice(5))}
<div class="ad-2"><section><h3>어디서 왔나 · 오늘</h3>${rank(v.refsToday || [], 'r', 'v')}</section><section><h3>어디서 왔나 · 7일</h3>${rank(v.refs, 'r', 'v')}</section><section><h3>지역 (7일)</h3>${rank(v.cities, 'c', 'v')}</section></div>
<h3>많이 본 페이지 (7일, 사람 수)</h3>${rank(v.pages.map(x => ({ ...x, p: x.path })), 'p', 'v')}
<h3>최근 방문</h3><table class="ad-t"><tr><th>언제</th><th>페이지</th><th>유입</th><th>지역</th></tr>${v.recent.map(h => `<tr><td>${ago(h.ts)}</td><td><a href="${J.esc(h.path)}">${J.esc(h.path)}</a></td><td>${J.esc(h.ref || '직접')}</td><td>${J.esc(h.city || '')}${h.mobile ? ' 📱' : ''}${h.uid ? ' 👤' : ''}</td></tr>`).join('')}</table>
<p class="note">봇·크롤러는 빼고 센 숫자예요. 자세한 건 <a href="https://analytics.google.com/analytics/web/#/a411961216p558909960/reports/intelligenthome" target="_blank" rel="noopener">구글 애널리틱스</a>.</p>
<h2>👤 회원</h2><div class="ad-g">${card('가입자', d.users, `오늘 +${d.users_day} · 7일 +${d.users_week}`)}${card('소셜 연결', d.social)}${card('원정대', d.teams, `모집 중 ${d.open_teams}`)}
${card('찜', d.favs)}${card('냈어요', d.applied, `당첨 ${d.won}`)}${card('메일 알림', d.alerts)}${card('폰 알림(앱)', d.push ?? 0)}${card('초대 가입', d.invites, `초대 방문 ${d.visits}`)}${card('후기·질문 글', d.posts)}</div>
<h2>최근 14일 가입</h2>${bars(d.byDay, 'n', x => x.d.slice(5))}
<h2>최근 가입</h2><table class="ad-t"><tr><th>#</th><th>닉네임</th><th>가입 경로</th><th>가입일</th></tr>${d.recent.map(u => `<tr><td>${u.id}</td><td>${J.esc(u.nick)}</td><td>${J.esc(u.via)}</td><td>${new Date(u.created * 1000).toLocaleString('ko-KR')}</td></tr>`).join('')}</table>
<h2>신고 들어온 것</h2>${d.reported.length ? `<table class="ad-t"><tr><th>종류</th><th>제목</th><th>신고</th><th>숨김</th></tr>${d.reported.map(r => `<tr><td>${r.k}</td><td>${J.esc(r.t)}</td><td>${r.reports}</td><td>${r.hidden ? '숨김' : ''}</td></tr>`).join('')}</table>` : '<p class="note">없어요 👍</p>'}`;
      A.querySelector('.ad-mine input').onchange = e => { mine = e.target.checked; load(); };
    }).catch(e => { A.innerHTML = `<h1>관리자</h1><p>${J.esc(e.message)} 관리자 계정으로 로그인했는지 확인해 주세요.</p>`; });
  }
  load();
})();
