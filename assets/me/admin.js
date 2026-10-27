// 관리자 (/admin/, 검색 노출 안 함) — 관리자 계정(ADMINS)만 서버가 숫자를 내줌
(function () {
  const A = document.getElementById('admin'), J = window.JUP; if (!A || !J) return;
  if (!J.st.t) { A.innerHTML = '<h1>관리자</h1><p>관리자 계정(사장님 구글 계정)으로 로그인하면 보여요.</p><button class="ad-login">로그인</button>'; A.querySelector('.ad-login').onclick = () => J.authModal ? J.authModal(() => location.reload()) : document.querySelector('.cm-in')?.click(); return; }
  const card = (k, v, s) => `<div class="ad-c"><small>${k}</small><b>${v}</b>${s ? `<em>${s}</em>` : ''}</div>`;
  const bars = (rows, key, lab) => { const max = Math.max(1, ...rows.map(x => x[key])); return `<div class="ad-bars">${rows.map(x => `<div><i style="height:${Math.round(x[key] / max * 100)}%"></i><b>${x[key]}</b><small>${lab(x)}</small></div>`).join('') || '<p class="note">아직 없어요</p>'}</div>`; };
  const rank = (rows, k, v) => rows.length ? `<ol class="ad-r">${rows.map(x => `<li><span>${J.esc(x[k] || '-')}</span><b>${x[v]}</b></li>`).join('')}</ol>` : '<p class="note">아직 없어요</p>';
  const ago = ts => { const m = Math.round((Date.now() / 1000 - ts) / 60); return m < 1 ? '방금' : m < 60 ? m + '분 전' : m < 1440 ? Math.round(m / 60) + '시간 전' : Math.round(m / 1440) + '일 전'; };
  let mine = false, fresh = false;
  function load() {
    const qs = '?mine=' + (mine ? '1' : '0') + (fresh ? '&fresh=1' : ''); fresh = false;
    Promise.all([J.api('/api/admin/visits' + qs), J.api('/api/admin' + (qs.includes('fresh') ? '?fresh=1' : ''))]).then(([v, d]) => {
      A.innerHTML = `<h1>관리자</h1>
<h2>👀 방문자 <label class="ad-mine"><input type="checkbox" ${mine ? 'checked' : ''}> 내 방문 포함</label></h2>
<div class="ad-g">${card('오늘 방문자', v.today.v || 0, `페이지 ${v.today.pv || 0}회`)}${card('지금 (30분)', v.live.v || 0)}${card('누적 방문', v.total.v || 0, v.total.since ? v.total.since.slice(5).replace('-', '/') + '부터 · 페이지 ' + v.total.pv + '회' : '')}${card('폰으로 본 비율', v.mobile.v ? Math.round(v.mobile.m / v.mobile.v * 100) + '%' : '-', '최근 7일')}</div>
<h2>최근 14일 방문자</h2>${bars(v.byDay, 'v', x => x.d.slice(5))}
<div class="ad-2"><section><h3>어디서 왔나 · 오늘</h3>${rank(v.refsToday || [], 'r', 'v')}</section><section><h3>어디서 왔나 · 7일</h3>${rank(v.refs, 'r', 'v')}</section><section><h3>지역 (7일)</h3>${rank(v.cities, 'c', 'v')}</section></div>
${v.vn ? `<h2>💗 미연시 유입</h2><div class="ad-g">${card('오늘 방문자', v.vn.today.v, `페이지 ${v.vn.today.pv}회`)}${card('7일 방문자', v.vn.week.v, `페이지 ${v.vn.week.pv}회`)}</div><div class="ad-2"><section><h3>페이지 · 7일</h3>${rank((v.vn.pages || []).map(x => ({ r: x.path, n: x.v })), 'r', 'n')}</section><section><h3>어디서 왔나 · 7일</h3>${rank(v.vn.refs || [], 'r', 'v')}</section></div>` : ''}
<div id="hl"></div><div class="ad-2"><section><h3>🧩 위젯 노출 · 7일 (붙은 곳)</h3>${rank((v.widgets || []).map(x => ({ r: x.k + ' · ' + x.h, n: x.n })), 'r', 'n')}</section><section><h3>🧩 위젯 클릭 · 7일 (방문자)</h3>${rank(v.widgetClicks || [], 'k', 'v')}</section></div>
<h3>많이 본 페이지 (7일, 사람 수)</h3>${rank(v.pages.map(x => ({ ...x, p: x.path })), 'p', 'v')}
<h3>최근 방문</h3><table class="ad-t"><tr><th>언제</th><th>페이지</th><th>유입</th><th>지역</th></tr>${v.recent.map(h => `<tr><td>${ago(h.ts)}</td><td><a href="${J.esc(h.path)}">${J.esc(h.path)}</a></td><td>${J.esc(h.ref || '직접')}</td><td>${J.esc(h.city || '')}${h.mobile ? ' 📱' : ''}${h.uid ? ' 👤' : ''}</td></tr>`).join('')}</table>
<p class="note">${v.cached ? '방문 숫자는 ' + new Date(v.cached * 1000).toLocaleTimeString('ko-KR') + ' 기준(3분마다 다시 셈, hits ' + (v.scanned || 0) + '줄 읽음) <button class="ad-fresh">지금 다시 계산</button>' : ''} 봇·크롤러는 빼고 센 숫자예요. 자세한 건 <a href="https://analytics.google.com/analytics/web/#/a411961216p558909960/reports/intelligenthome" target="_blank" rel="noopener">구글 애널리틱스</a>.</p>
<h2>👤 회원</h2><div class="ad-g">${card('가입자', d.users, `오늘 +${d.users_day} · 7일 +${d.users_week}`)}${card('소셜 연결', d.social)}${card('원정대', d.teams, `모집 중 ${d.open_teams}`)}
${card('찜', d.favs)}${card('냈어요', d.applied, `당첨 ${d.won}`)}${card('메일 알림', d.alerts)}${card('폰 알림(앱)', d.push ?? 0)}${card('초대 가입', d.invites, `초대 방문 ${d.visits}`)}${card('후기·질문 글', d.posts)}</div>
<h2>최근 14일 가입</h2>${bars(d.byDay, 'n', x => x.d.slice(5))}
<h2>최근 가입</h2><table class="ad-t"><tr><th>#</th><th>닉네임</th><th>가입 경로</th><th>가입일</th></tr>${d.recent.map(u => `<tr><td>${u.id}</td><td>${J.esc(u.nick)}</td><td>${J.esc(u.via)}</td><td>${new Date(u.created * 1000).toLocaleString('ko-KR')}</td></tr>`).join('')}</table>
<h2>신고 들어온 것</h2>${d.reported.length ? `<table class="ad-t"><tr><th>종류</th><th>제목</th><th>신고</th><th>숨김</th></tr>${d.reported.map(r => `<tr><td>${r.k}</td><td>${J.esc(r.t)}</td><td>${r.reports}</td><td>${r.hidden ? '숨김' : ''}</td></tr>`).join('')}</table>` : '<p class="note">없어요 👍</p>'}`;
      A.querySelector('.ad-mine input').onchange = e => { mine = e.target.checked; load(); };
      const fb = A.querySelector('.ad-fresh'); if (fb) fb.onclick = () => { fresh = true; fb.textContent = '세는 중…'; load(); };
    }).catch(e => { A.innerHTML = `<h1>관리자</h1><p>${J.esc(e.message)} 관리자 계정으로 로그인했는지 확인해 주세요.</p>`; });
  }
  load();
})();
// 매 빌드 건강 점검 (/admin/health.json, 2026-10-18)
fetch('/admin/health.json?t=' + Date.now()).then(r => r.json()).then(h => { const t = () => { const el = document.getElementById('hl'); if (!el) return setTimeout(t, 800);
  el.innerHTML = `<section style="margin:12px 0;padding:12px;border-radius:12px;background:${h.warn.length ? '#fef2f2' : '#ecfdf5'}"><h3>${h.warn.length ? '⚠️ 사이트 점검 경고' : '✅ 사이트 점검 정상'} <small>${h.at}</small></h3><p>사이트맵 ${h.sitemap}쪽 · 검색 제외 ${h.noindex_pct}% · 깨진 링크 ${h.broken} · 빈 페이지 ${h.empty} · 중복 제목 ${h.dup_titles} · 고아 ${h.orphans}</p>${h.warn.length ? '<p><b>' + h.warn.join(' / ') + '</b></p>' : ''}</section>`; }; t(); }).catch(() => {});
