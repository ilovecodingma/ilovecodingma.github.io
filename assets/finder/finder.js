// 🔎 자동 자료 찾기 (2026-10-19): 공모전 키워드(빌드 때 공고에서 자동 추출) → 사이트 문서 색인 BM25 검색. 키워드를 빼고 더하면 바로 다시 검색. 모델·서버 없음
(function () {
  const R = document.getElementById('finder'); if (!R) return;
  try { const k = 'jj_seen', L = JSON.parse(localStorage.getItem(k) || '[]').filter(x => x !== R.dataset.id); L.push(R.dataset.id); localStorage.setItem(k, JSON.stringify(L.slice(-50))); } catch (e) {}   // 추천 개인화용(이 폰에만)
  const cid = R.dataset.id, esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch (e) {} };
  const member = () => { try { return !!(window.JUP && JUP.st && JUP.st.t) || !!localStorage.getItem('jupjup_tok'); } catch (e) { return false; } };
  // 토큰: 2글자 이상 단어 + 한글 3글자 이상 단어의 2글자 묶음(부분 일치용)
  const tok = s => { const out = []; (String(s).toLowerCase().match(/[0-9a-z가-힣]{2,}/g) || []).forEach(w => { out.push(w); if (/[가-힣]{3,}/.test(w)) for (let i = 0; i < w.length - 1; i++) out.push('#' + w.slice(i, i + 2)); }); return out; };
  let D = null, Q = [], df = null, avg = 0;
  function prep() {
    df = new Map(); let tot = 0;
    D.forEach(d => { const tf = new Map(); tok(d.t + ' ' + d.t + ' ' + (d.x || '')).forEach(w => tf.set(w, (tf.get(w) || 0) + 1)); d.tf = tf; d.len = [...tf.values()].reduce((a, b) => a + b, 0); tot += d.len; tf.forEach((_, w) => df.set(w, (df.get(w) || 0) + 1)); });
    avg = tot / Math.max(1, D.length);
  }
  function search() {
    const N = D.length, k1 = 1.4, b = 0.75, qt = [];
    Q.forEach(q => tok(q).forEach(w => qt.push([w, w.startsWith('#') ? 0.35 : 1])));
    const res = [];
    D.forEach(d => {
      if (d.u === `/c/${cid}/`) return;
      let s = 0; const hit = new Set();
      qt.forEach(([w, wt]) => { const f = d.tf.get(w); if (!f) return; const idf = Math.log(1 + (N - df.get(w) + 0.5) / (df.get(w) + 0.5)); s += wt * idf * f * (k1 + 1) / (f + k1 * (1 - b + b * d.len / avg)); if (!w.startsWith('#')) hit.add(w); });
      if (s > 0 && (hit.size || s > 2)) res.push([s, d, hit]);
    });
    return res.sort((a, b) => b[0] - a[0]);
  }
  function pub() {   // 공공 통계·정책은 검색 링크만(질의를 그대로 넘김)
    const q = encodeURIComponent(Q.slice(0, 3).join(' '));
    return `<p class="fd-pub">🏛️ 공공 자료에서 더 찾기: <a href="https://www.korea.kr/search/search.do?query=${q}" target="_blank" rel="noopener nofollow">정책브리핑</a> · <a href="https://kosis.kr/search/search.do?query=${q}" target="_blank" rel="noopener nofollow">KOSIS 통계</a> · <a href="https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=${q}" target="_blank" rel="noopener nofollow">공공데이터포털</a> · <a href="https://www.google.com/search?q=${q}+%EC%88%98%EC%83%81%EC%9E%91" target="_blank" rel="noopener nofollow">수상작 검색</a></p>`;
  }
  function paint() {
    const res = search(), all = member(), show = all ? res.slice(0, 30) : res.slice(0, 3);
    R.querySelector('.fd-kw').innerHTML = Q.map((q, i) => `<button data-i="${i}" title="빼기">${esc(q)} ✕</button>`).join('') + '<input class="fd-add" placeholder="+ 키워드 더하기" maxlength="20">';
    R.querySelector('.fd-out').innerHTML = (show.length ? `<ol class="fd-l">${show.map(([s, d, hit]) => `<li><a href="${esc(d.u)}"${d.ext ? ' target="_blank" rel="noopener nofollow"' : ''} data-k="${d.k}"><em>${esc(d.l)}</em><b>${esc(d.t)}</b>${d.x ? `<span>${esc(d.x)}</span>` : ''}<small>일치: ${[...hit].slice(0, 4).map(esc).join(', ') || '부분 일치'}</small></a></li>`).join('')}</ol>` : '<p class="note">이 키워드로 찾은 자료가 없어요. 키워드를 바꿔 보세요.</p>')
      + (!all && res.length > 3 ? `<div class="fd-more"><b>자료 ${res.length}개 중 3개만 보여 드렸어요.</b><p>로그인하면 수상작·가이드·기사·비슷한 공모전 전체를 점수순으로 볼 수 있어요.</p><button class="fd-login">무료로 로그인하고 전체 보기</button></div>` : '') + pub();
    R.querySelectorAll('.fd-kw [data-i]').forEach(b => b.onclick = () => { Q.splice(+b.dataset.i, 1); paint(); ga('finder_kw', { act: 'remove' }); });
    const ad = R.querySelector('.fd-add'); ad.onkeydown = e => { if (e.key === 'Enter' && ad.value.trim()) { Q.push(ad.value.trim()); paint(); R.querySelector('.fd-add').focus(); ga('finder_kw', { act: 'add' }); } };
    const lg = R.querySelector('.fd-login'); if (lg) lg.onclick = () => { const b = document.querySelector('.cm-in'); if (window.JUP && JUP.authModal) JUP.authModal(() => paint()); else if (b) b.click(); ga('finder_login', {}); };
    R.querySelectorAll('.fd-l a').forEach(a => a.addEventListener('click', () => ga('finder_open', { kind: a.dataset.k })));
  }
  R.innerHTML = '<h2>🔎 자동 자료 찾기 <small>공고에서 뽑은 키워드로 사이트 자료를 찾아요</small></h2><div class="fd-kw"></div><div class="fd-out"><p class="note">찾는 중…</p></div>';
  const go = () =>   Promise.all([fetch('/assets/finder/index.json?v=' + (R.dataset.v || '')).then(r => r.json()), fetch('/assets/finder/q.json?v=' + (R.dataset.v || '')).then(r => r.json())])
    .then(([ix, q]) => { D = ix.docs; Q = (q[cid] || []).slice(); prep(); paint(); ga('finder_view', {}); })
    .catch(() => { R.querySelector('.fd-out').innerHTML = '<p class="note">자료 목록을 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.</p>'; });
  if ('IntersectionObserver' in window) { const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); go(); } }, { rootMargin: '600px' }); io.observe(R); } else go();   // 화면 근처에 올 때만 색인 내려받기
})();
