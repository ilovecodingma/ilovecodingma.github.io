// 루리의 냉장고 파먹기 (/fridge/) — 냉장고에 있는 재료를 고르면 레시피 77개 중 지금 만들 수 있는 오늘 메뉴를 추천
// 2026-10-18 사용자: "AI 말고 그냥 레시피 추천으로" → 재료 매칭 방식(서버·AI 없이 브라우저에서 계산)
(function () {
  const ROOT = document.getElementById('fridge'); if (!ROOT) return;
  const KEY = 'jupjup_fridge_v1';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  let D = null, have = new Set(), mood = '아무거나', maxMin = 99;
  try { have = new Set(JSON.parse(localStorage.getItem(KEY) || '[]')); } catch {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify([...have])); } catch {} };
  const MOODS = ['아무거나', '든든', '가벼움', '아이', '안주', '안 매움', '매움', '간식'];
  const TIMES = [[99, '상관없음'], [10, '10분'], [20, '20분'], [30, '30분']];
  // 같은 점수면 날짜마다 다른 메뉴가 먼저 오게 (오늘의 메뉴)
  const day = new Date().toISOString().slice(0, 10), seed = s => { let h = 0; for (const c of day + s) h = (h * 31 + c.charCodeAt(0)) | 0; return (h >>> 0) / 4294967296; };
  function rank() {
    return D.recipes.map(r => {
      const lack = r.need.filter(x => !have.has(x)), plus = r.opt.filter(x => have.has(x));
      const fit = mood === '아무거나' || r.t.includes(mood);
      return { r, lack, plus, score: (lack.length ? -10 * lack.length : 0) + plus.length * 1.2 + r.need.length * 0.8 + (fit ? 3 : 0) + seed(r.n) };
    }).filter(x => x.r.m <= maxMin && (mood === '아무거나' || x.r.t.includes(mood) || x.lack.length === 0)).sort((a, b) => b.score - a.score);
  }
  const card = (x, big) => `<article class="fr-m${big ? ' best' : ''}"><header><span class="fr-e">${x.r.e}</span><div><h3>${esc(x.r.n)}</h3><p><em>⏱ ${x.r.m}분</em><em>${esc(x.r.lv)}</em>${x.r.t.map(t => `<em class="t">#${esc(t)}</em>`).join('')}</p></div></header>
<p class="fr-use">${x.r.need.filter(i => have.has(i)).concat(x.plus).map(i => `<span>${esc(i)}</span>`).join('')}${x.lack.map(i => `<span class="no">+ ${esc(i)} 사기</span>`).join('')}</p>
<details${big ? ' open' : ''}><summary>만드는 법</summary><ol>${x.r.s.map(s => `<li>${esc(s)}</li>`).join('')}</ol>${x.r.opt.length ? `<p class="fr-tip">💡 있으면 더 좋아요: ${x.r.opt.map(esc).join(', ')}</p>` : ''}</details></article>`;
  function paint() {
    const cats = Object.entries(D.ing).map(([c, xs]) => `<div class="fr-cat"><small>${esc(c)}</small><div>${xs.map(x => `<button data-i="${esc(x)}" class="${have.has(x) ? 'on' : ''}">${esc(x)}</button>`).join('')}</div></div>`).join('');
    ROOT.innerHTML = `<label class="fr-cam"><input type="file" accept="image/*" capture="environment" hidden><b>📸 냉장고 사진 찍어서 자동 체크</b><small>사진 속 재료를 찾아 아래에 체크해 드려요 · 틀린 건 눌러서 고치면 돼요</small></label><p class="fr-scan" hidden></p>
<section class="fr-pick"><h2>🧊 냉장고에 뭐 있어요? <small class="fr-n">${have.size}개 골랐어요</small></h2><p class="fr-basic">기본양념(${esc(D.basic)})은 있다고 칠게요.</p>${cats}
<button class="fr-clear">비우기</button></section>
<div class="fr-opts"><div class="fr-o"><small>오늘 기분은?</small><div>${MOODS.map(m => `<button data-m="${m}" class="${mood === m ? 'on' : ''}">${m === '아무거나' ? m : '#' + m}</button>`).join('')}</div></div>
<div class="fr-o"><small>시간은?</small><div>${TIMES.map(([v, l]) => `<button data-t="${v}" class="${maxMin === v ? 'on' : ''}">${l}</button>`).join('')}</div></div></div>
<div class="fr-out"></div>`;
    ROOT.querySelectorAll('[data-i]').forEach(b => b.onclick = () => { const i = b.dataset.i; have.has(i) ? have.delete(i) : have.add(i); b.classList.toggle('on'); save(); ROOT.querySelector('.fr-n').textContent = have.size + '개 골랐어요'; result(); });
    ROOT.querySelectorAll('[data-m]').forEach(b => b.onclick = () => { mood = b.dataset.m; ROOT.querySelectorAll('[data-m]').forEach(x => x.classList.toggle('on', x === b)); result(); });
    ROOT.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { maxMin = +b.dataset.t; ROOT.querySelectorAll('[data-t]').forEach(x => x.classList.toggle('on', x === b)); result(); });
    ROOT.querySelector('.fr-cam input').onchange = e => scan(e.target.files[0]);
    ROOT.querySelector('.fr-clear').onclick = () => { have.clear(); save(); paint(); };
    result();
  }
  // 사진 → 서버(Cloudflare Workers AI 공개 모델)가 재료 이름만 돌려줌 → 칩 자동 체크. 사진은 저장 안 함
  function scan(f) {
    if (!f) return; const msg = ROOT.querySelector('.fr-scan'), API = document.body.dataset.api || 'https://jupjup-api.sung2011103.workers.dev';
    msg.hidden = false; msg.className = 'fr-scan wait'; msg.textContent = '🔍 루리가 냉장고를 들여다보는 중…';
    const im = new Image(); im.onload = async () => {
      const r = Math.min(1, 1024 / Math.max(im.width, im.height)), c = document.createElement('canvas'); c.width = Math.round(im.width * r); c.height = Math.round(im.height * r);
      c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); URL.revokeObjectURL(im.src);
      let tk = ''; try { tk = localStorage.getItem('jupjup_tok') || ''; } catch {}
      try {
        const ac = new AbortController(), to = setTimeout(() => ac.abort(), 25000);
        const res = await fetch(API + '/api/fridge-scan', { signal: ac.signal, method: 'POST', headers: { 'Content-Type': 'application/json', ...(tk ? { Authorization: 'Bearer ' + tk } : {}) }, body: JSON.stringify({ image: c.toDataURL('image/jpeg', 0.8) }) });
        clearTimeout(to);
        const d = await res.json().catch(() => ({})); if (!res.ok) throw new Error(d.error || '사진을 잘 못 봤어요.');
        const nw = d.found.filter(x => !have.has(x)); d.found.forEach(x => have.add(x)); save(); paint(); ga('fridge_scan', { found: d.found.length });
        const m2 = ROOT.querySelector('.fr-scan'); m2.hidden = false; m2.className = 'fr-scan ok';
        m2.innerHTML = d.found.length ? `📸 사진에서 <b>${d.found.map(esc).join(', ')}</b>${nw.length < d.found.length ? '' : ''}을(를) 찾았어요! 틀린 건 눌러서 빼고, 빠진 건 더 눌러 주세요.` : '🤔 사진에서 재료를 못 찾았어요. 밝은 곳에서 가까이 찍거나, 아래에서 직접 눌러 주세요.';
        nw.forEach(x => { const b = ROOT.querySelector(`[data-i="${x}"]`); if (b) b.classList.add('new'); });
      } catch (e) { msg.className = 'fr-scan err'; msg.textContent = e.name === 'AbortError' ? '사진 인식이 너무 오래 걸려요. 잠시 뒤 다시 하거나 재료를 직접 눌러 주세요.' : /fetch|network/i.test(e.message) ? '인터넷 연결이 불안정해요. 다시 해 보거나 재료를 직접 눌러 주세요.' : e.message; }
      ROOT.querySelector('.fr-cam input').value = '';
    }; im.onerror = () => { msg.className = 'fr-scan err'; msg.textContent = '이 사진은 열 수 없어요(HEIC 같은 형식일 수 있어요). 카메라로 바로 찍거나 JPG 사진으로 다시 골라 주세요. 재료는 아래에서 직접 눌러도 돼요.'; };
    im.src = URL.createObjectURL(f);
  }
  let gaT;
  function result() {
    const out = ROOT.querySelector('.fr-out');
    if (!have.size) { out.innerHTML = '<p class="fr-note">👆 냉장고 열어 보고 있는 재료를 눌러 주세요. 고른 재료는 다음에 와도 기억해 둘게요!</p>'; return; }
    const all = rank(), now = all.filter(x => !x.lack.length), buy1 = all.filter(x => x.lack.length === 1).slice(0, 4);
    out.innerHTML = (now.length ? `<h2 class="fr-h">🍽️ 오늘은 이거 어때요? <small>지금 있는 재료로 바로 · ${now.length}개</small></h2>${card(now[0], true)}${now.slice(1, 3).map(x => card(x)).join('')}
${now.length > 3 ? `<details class="fr-more"><summary>바로 만들 수 있는 메뉴 ${now.length - 3}개 더 보기</summary>${now.slice(3).map(x => card(x)).join('')}</details>` : ''}` : '<p class="fr-note">🤔 고른 재료만으로는 딱 맞는 메뉴가 없어요. 아래처럼 하나만 사면 돼요!</p>')
      + (buy1.length ? `<h2 class="fr-h">🛒 하나만 사면 되는 메뉴</h2>${buy1.map(x => card(x)).join('')}` : '')
      + (now.length ? '<div class="fr-end"><button class="fr-share">📤 오늘 메뉴 공유하기</button><button class="fr-top">🔄 재료 다시 고르기</button></div>' : '');
    const sh = out.querySelector('.fr-share'); if (sh) sh.onclick = () => {
      const text = `냉장고 털어서 오늘은 「${now[0].r.n}」! 루리가 골라 줬어요 🍳`, url = location.origin + '/fridge/';
      ga('share', { method: navigator.share ? 'native' : 'copy', content_type: 'fridge' });
      if (navigator.share) navigator.share({ title: '루리의 냉장고 파먹기', text, url }).catch(() => {});
      else (navigator.clipboard ? navigator.clipboard.writeText(text + ' ' + url) : Promise.reject()).then(() => { sh.textContent = '✅ 복사했어요'; }).catch(() => {});
    };
    const tp = out.querySelector('.fr-top'); if (tp) tp.onclick = () => ROOT.scrollIntoView({ behavior: 'smooth' });
    clearTimeout(gaT); gaT = setTimeout(() => ga('fridge_result', { have: have.size, now: now.length, mood }), 1500);
  }
  fetch('/assets/fridge/recipes.json?v=1').then(r => r.json()).then(d => { D = d; paint(); });
})();
