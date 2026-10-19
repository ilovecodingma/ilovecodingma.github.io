// 관리자 · 홍보 관리 (2026-10-19 SEO·홍보 지침 Phase 3). 상태: DRAFT → REVIEW → APPROVED → SCHEDULED → PUBLISHED, 실패는 FAILED
// 문구 생성은 PC 의 _gongmo/promo.py(하루 슬롯). 여기서는 미리보기·복사·승인·예약·게시 완료 기록만 — 외부 자동 게시는 하지 않음
(function () {
  const R = document.getElementById('promo-admin'), J = window.JUP; if (!R || !J || !J.st.t) return;
  const esc = J.esc, CH = { naver_blog: '네이버 블로그', threads: '스레드', x: 'X', instagram: '인스타그램', shorts: '유튜브 쇼츠', community: '커뮤니티' };
  const ST = { DRAFT: '✏️ 초안(검사 실패)', REVIEW: '👀 검토 대기', APPROVED: '✅ 승인', SCHEDULED: '⏰ 예약', PUBLISHED: '📢 게시 완료', FAILED: '⚠️ 실패' };
  let st = 'REVIEW', ch = '';
  async function load() {
    R.innerHTML = '<h2>📣 홍보 관리</h2><p class="note">불러오는 중…</p>';
    let d; try { d = await J.api(`/api/admin/promo?st=${st}&ch=${ch}`); } catch (e) { R.innerHTML = `<h2>📣 홍보 관리</h2><p class="note">${esc(e.message)}</p>`; return; }
    const cnt = Object.fromEntries(d.cnt.map(x => [x.status, x.n])), clk = Object.fromEntries(d.clicks.map(x => [x.t, x]));
    R.innerHTML = `<h2>📣 홍보 관리</h2><p class="note">문구는 사이트 데이터로 매일 자동 생성되고, 날짜·금액 일치·마감·과장 표현·대상 누락·중복을 자동 검사해요. 게시는 승인 후 사람이 직접 하고 「게시 완료」로 기록해요. 링크마다 꼬리표(?src=p…)가 있어 글별 방문자를 셉니다.</p>
<div class="pa-f">${Object.entries(ST).map(([k, v]) => `<button data-st="${k}" class="${k === st ? 'on' : ''}">${v} ${cnt[k] || 0}</button>`).join('')}</div>
<div class="pa-f">${[['', '전체 채널'], ...Object.entries(CH)].map(([k, v]) => `<button data-ch="${k}" class="${k === ch ? 'on' : ''}">${v}</button>`).join('')}</div>
<p class="note">최근 30일 채널별 방문자(홍보 링크): ${d.byCh.map(x => `${CH[x.ch] || x.ch} ${x.v}명`).join(' · ') || '아직 없어요'}</p>
${d.rows.map(r => { const q = JSON.parse(r.qc || '[]'), c = clk[r.tok];
  return `<article class="pa-i" data-id="${r.id}"><header><b>${esc(CH[r.channel] || r.channel)}</b><span>${ST[r.status]}</span><small>${esc(r.day)} · ${esc(r.kind)} · 방문 ${c ? c.v : 0}명</small></header>
<h3>${esc(r.title)}</h3>${q.length ? `<p class="pa-qc">자동 검사 실패: ${q.map(esc).join(' / ')}</p>` : ''}${r.note ? `<p class="note">메모: ${esc(r.note)}</p>` : ''}
<textarea rows="8">${esc(r.body)}</textarea>
<div class="pa-b"><button data-a="copy">📋 복사</button>
${r.status === 'DRAFT' ? '<button data-a="review">확인했어요 → 검토로</button>' : ''}${['DRAFT', 'REVIEW', 'APPROVED'].includes(r.status) ? '<button data-a="edit">수정 저장</button>' : ''}
${r.status === 'REVIEW' ? '<button data-a="approve">✅ 승인</button>' : ''}${['APPROVED', 'SCHEDULED'].includes(r.status) ? `<input type="datetime-local" value="${esc(r.scheduled || '')}"><button data-a="schedule">⏰ 예약</button><input class="pa-u" placeholder="게시한 글 주소(선택)"><button data-a="publish">📢 게시 완료</button>` : ''}
${['REVIEW', 'APPROVED', 'SCHEDULED'].includes(r.status) ? '<button data-a="fail">⚠️ 실패</button><button data-a="back">초안으로</button>' : ''}${r.status === 'FAILED' ? '<button data-a="retry">🔁 재시도</button>' : ''}
${r.post_url ? `<a href="${esc(r.post_url)}" target="_blank" rel="noopener">게시 글 보기</a>` : ''}</div></article>`; }).join('') || '<p class="note">이 상태의 홍보 글이 없어요.</p>'}`;
    R.querySelectorAll('[data-st]').forEach(b => b.onclick = () => { st = b.dataset.st; load(); });
    R.querySelectorAll('[data-ch]').forEach(b => b.onclick = () => { ch = b.dataset.ch; load(); });
    R.querySelectorAll('.pa-i').forEach(el => el.querySelectorAll('[data-a]').forEach(b => b.onclick = async () => {
      const a = b.dataset.a, ta = el.querySelector('textarea');
      if (a === 'copy') { (navigator.clipboard ? navigator.clipboard.writeText(ta.value) : Promise.reject()).then(() => { b.textContent = '✅ 복사했어요'; }).catch(() => { ta.select(); document.execCommand('copy'); }); return; }
      const body = { id: +el.dataset.id, act: a };
      if (a === 'edit') { body.body = ta.value; body.note = prompt('무엇을 고쳤는지 메모') || ''; }
      if (a === 'review' || a === 'fail') { body.note = prompt(a === 'fail' ? '실패 사유' : '무엇을 확인했는지(필수)') || ''; if (a === 'review' && !body.note) return; }
      if (a === 'schedule') body.scheduled = el.querySelector('input[type=datetime-local]').value;
      if (a === 'publish') body.post_url = el.querySelector('.pa-u').value;
      try { await J.api('/api/admin/promo', { method: 'POST', body }); load(); } catch (e) { alert(e.message); }
    }));
  }
  load();
})();
// 서치 콘솔 리포트 (gsc.py 가 하루 1번 admin/gsc.json 갱신)
(function () {
  const G = document.getElementById('gsc-admin'), J = window.JUP; if (!G || !J || !J.st.t) return;
  const esc = J.esc, tb = (L, cols) => L && L.length ? `<table class="info"><tr>${cols.map(c => `<th>${c[1]}</th>`).join('')}</tr>${L.map(x => `<tr>${cols.map(c => `<td>${esc(String(x[c[0]] ?? ''))}</td>`).join('')}</tr>`).join('')}</table>` : '<p class="note">아직 데이터가 없어요.</p>';
  fetch('/admin/gsc.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    const C = [['query', '검색어'], ['impr', '노출'], ['clicks', '클릭'], ['ctr', 'CTR%'], ['pos', '평균 순위']];
    G.innerHTML = `<h2>🔍 구글 검색 리포트 <small>${esc(d.range.join(' ~ '))} · ${esc(d.at)} 수집</small></h2>
<p class="note">사이트맵 재제출 응답 ${d.sitemap_put} · ${d.sitemaps.map(s => `${esc(s.path.replace('https://sungprofile.cloud/', '/'))} 제출 ${(s.contents || []).map(c => c.submitted).join('/')}`).join(' · ')}</p>
<h3>노출 많은 검색어</h3>${tb(d.top, C)}<h3>11~20위 검색어 (조금만 올리면 1페이지)</h3>${tb(d.near, C)}<h3>노출은 많은데 클릭이 적은 페이지 (CTR 2% 미만)</h3>${tb(d.lowctr, [['page', '페이지'], ['impr', '노출'], ['clicks', '클릭'], ['ctr', 'CTR%'], ['pos', '평균 순위']])}`;
  }).catch(() => { G.innerHTML = '<h2>🔍 구글 검색 리포트</h2><p class="note">아직 리포트가 없어요.</p>'; });
})();
