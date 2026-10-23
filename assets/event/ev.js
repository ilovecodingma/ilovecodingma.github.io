// 경품 이벤트 목록 — 참여 방식·마감 필터·검색, 카드는 제목 → 참여 방법·마감·주최 → 이동 버튼 (2026-10-23 화면 개선 9번)
// 데이터 /events.json(매시간 빌드가 갱신). 참여 방식은 자동 분류라 확정처럼 쓰지 않는다.
(function () {
  const R = document.getElementById('evl'); if (!R) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const T = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), dn = s => Math.round((Date.parse(s) - Date.parse(T)) / 864e5);
  const tidy = t => t.replace(/^\s*\((?:중복|중복 \d+회|\d+회 중복)[^)]*\)\s*/, '').replace(/\s+/g, ' ').trim();
  const NORM = { '댓글 1줄': '댓글 참여', '설문 5분': '설문 참여', '폼 1분': '폼 응모', '퀴즈 1분': '퀴즈 참여', '퀴즈 풀기': '퀴즈 참여', '응모만': '응모' };
  const KINDS = ['전체', '댓글 참여', '퀴즈 참여', '설문 참여', '응모', '폼 응모', '기타'];
  const KEY = 'jupjup_event_state_v1';
  let D = [], k = '전체', q = '', due = '', n = 30;
  try { const sv = JSON.parse(sessionStorage.getItem(KEY) || 'null'); if (sv) { k = sv.k || k; q = sv.q || ''; due = sv.due || ''; n = sv.n || 30; } } catch (e) {}
  const save = () => { try { sessionStorage.setItem(KEY, JSON.stringify({ k, q, due, n, y: scrollY })); } catch (e) {} };
  function paint() {
    const L = D.filter(e => (k === '전체' || (k === '기타' ? !KINDS.slice(1, 6).includes(e.ez) : e.ez === k)) && (!due || dn(e.end) <= +due) && (!q || (e.t + ' ' + e.org).toLowerCase().includes(q)));
    const cd = [k !== '전체' ? k : '', due ? (due === '1' ? '오늘·내일 마감' : due + '일 이내') : '', q ? '“' + q + '”' : ''].filter(Boolean);
    R.querySelector('.ev-n').innerHTML = `결과 <b>${L.length}건</b>` + (cd.length ? ` · 적용: ${esc(cd.join(' · '))} <button type="button" class="ev-reset">초기화</button>` : '');
    R.querySelector('.ev-ul').innerHTML = L.length ? L.slice(0, n).map(e => { const d = dn(e.end);
      return `<li class="ev-c"><h3>${esc(e.t)}</h3><dl><div><dt>참여 방법</dt><dd>${esc(e.ez || '미확인')}</dd></div><div><dt>마감</dt><dd><span class="${d <= 1 ? 'u' : ''}">${d <= 0 ? '오늘' : 'D-' + d}</span> ${esc(e.end.slice(5).replace('-', '.'))}</dd></div><div><dt>주최</dt><dd>${esc(e.org || '공식 계정')}</dd></div></dl><a class="ev-go" href="${esc(e.link)}" target="_blank" rel="noopener nofollow">이벤트 보기 ↗</a></li>`; }).join('') : '<li class="ev-empty">조건에 맞는 이벤트가 없어요. 조건을 줄이거나 초기화해 보세요.</li>';
    R.querySelector('.ev-more').hidden = L.length <= n;
    save();
  }
  fetch('/events.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    D = d.map(e => ({ ...e, ez: NORM[e.ez] || e.ez, t: tidy(e.title) })).filter(e => dn(e.end) >= 0).sort((a, b) => a.end.localeCompare(b.end));
    R.innerHTML = `<div class="ev-bar"><div class="ev-k" role="group" aria-label="참여 방식">${KINDS.map(x => `<button data-k="${x}" class="${x === k ? 'on' : ''}">${x}</button>`).join('')}</div>
<div class="ev-r"><input class="ev-q" placeholder="찾기 (예: 커피, 편의점, 퀴즈)" aria-label="이벤트 찾기" value="${esc(q)}"><select class="ev-d" aria-label="마감"><option value="">마감 전체</option><option value="1">오늘·내일</option><option value="7">7일 이내</option><option value="30">30일 이내</option></select></div><p class="ev-n" aria-live="polite"></p></div><ul class="ev-ul"></ul><button class="ev-more" hidden>30개 더 보기</button>`;
    R.querySelector('.ev-d').value = due;
    R.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { k = b.dataset.k; n = 30; R.querySelectorAll('[data-k]').forEach(x => x.classList.toggle('on', x === b)); paint(); });
    R.querySelector('.ev-q').oninput = e => { q = e.target.value.trim().toLowerCase(); n = 30; paint(); };
    R.querySelector('.ev-d').onchange = e => { due = e.target.value; n = 30; paint(); };
    R.querySelector('.ev-more').onclick = () => { n += 30; paint(); };
    R.addEventListener('click', e => { if (e.target.classList.contains('ev-reset')) { k = '전체'; q = ''; due = ''; n = 30; R.querySelector('.ev-q').value = ''; R.querySelector('.ev-d').value = ''; R.querySelectorAll('[data-k]').forEach(x => x.classList.toggle('on', x.dataset.k === '전체')); paint(); } });
    paint();
    try { const sv = JSON.parse(sessionStorage.getItem(KEY) || 'null'); if (sv && sv.y && (performance.getEntriesByType('navigation')[0] || {}).type === 'back_forward') setTimeout(() => scrollTo(0, sv.y), 60); } catch (e) {}
  }).catch(() => { R.innerHTML = '<p class="note">이벤트 목록을 불러오지 못했어요. <button type="button" onclick="location.reload()">다시 시도</button></p>'; });
  addEventListener('pagehide', save);
})();
