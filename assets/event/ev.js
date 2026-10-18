// 경품 이벤트 목록 (2026-10-18 사용자: "경품 이벤트도 좀 적당히 보이게 하고 갱신도 자동으로") — 종류 칩·검색·30개씩. 데이터 /events.json(매시간 빌드가 갱신)
(function () {
  const R = document.getElementById('evl'); if (!R) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const T = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10), dn = s => Math.round((Date.parse(s) - Date.parse(T)) / 864e5);
  const tidy = t => t.replace(/^\s*\((?:중복|중복 \d+회|\d+회 중복)[^)]*\)\s*/, '').replace(/\s+/g, ' ').trim();
  const KINDS = ['전체', '댓글 1줄', '퀴즈 1분', '설문 5분', '응모만', '기타'];
  let D = [], k = '전체', q = '', n = 30;
  function paint() {
    const L = D.filter(e => (k === '전체' || (k === '기타' ? !KINDS.slice(1, 5).includes(e.ez) : e.ez === k)) && (!q || (e.t + ' ' + e.org).toLowerCase().includes(q)));
    R.querySelector('.ev-n').textContent = `${L.length}건`;
    R.querySelector('.ev-ul').innerHTML = L.slice(0, n).map(e => { const d = dn(e.end);
      return `<li><a href="${esc(e.link)}" target="_blank" rel="noopener nofollow"><b>${esc(e.t)}</b><span><em class="${d <= 1 ? 'u' : ''}">${d <= 0 ? '오늘 마감' : 'D-' + d}</em>${esc(e.org || '공식 계정')} · <i>${esc(e.ez)}</i></span></a></li>`; }).join('') || '<li class="ev-0">조건에 맞는 이벤트가 없어요.</li>';
    R.querySelector('.ev-more').hidden = L.length <= n;
  }
  fetch('/events.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    D = d.map(e => ({ ...e, t: tidy(e.title) })).filter(e => dn(e.end) >= 0).sort((a, b) => a.end.localeCompare(b.end));
    R.innerHTML = `<div class="ev-bar"><div class="ev-k">${KINDS.map(x => `<button data-k="${x}" class="${x === k ? 'on' : ''}">${x}</button>`).join('')}</div>
<input class="ev-q" placeholder="찾기 (예: 커피, 편의점, 퀴즈)" aria-label="이벤트 찾기"><small class="ev-n"></small></div><ul class="ev-ul"></ul><button class="ev-more" hidden>30개 더 보기</button>`;
    R.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { k = b.dataset.k; n = 30; R.querySelectorAll('[data-k]').forEach(x => x.classList.toggle('on', x === b)); paint(); });
    R.querySelector('.ev-q').oninput = e => { q = e.target.value.trim().toLowerCase(); n = 30; paint(); };
    R.querySelector('.ev-more').onclick = () => { n += 30; paint(); };
    paint();
  }).catch(() => { R.innerHTML = '<p class="note">이벤트 목록을 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.</p>'; });
})();
