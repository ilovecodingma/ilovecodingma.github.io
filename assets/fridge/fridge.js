// 루리의 냉장고 파먹기 (/fridge/) — 냉장고 사진 → Claude 가 재료를 보고 오늘 메뉴 3개 추천 (2026-10-18 사용자 요청)
(function () {
  const ROOT = document.getElementById('fridge'); if (!ROOT) return;
  const API = document.body.dataset.api || 'https://jupjup-api.sung2011103.workers.dev';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const tok = () => { try { return localStorage.getItem('jupjup_tok') || ''; } catch { return ''; } };
  const OPT = { people: ['1인분', '2인분', '3~4인 가족'], time: ['10분', '20분', '40분'], want: ['아무거나', '든든하게', '가볍게·다이어트', '아이 반찬', '술안주', '안 맵게'] };
  const sel = { people: '1인분', time: '20분', want: '아무거나' };
  let img = '';
  ROOT.innerHTML = `<label class="fr-shot"><input type="file" accept="image/*" capture="environment" hidden><span class="fr-ph"><b>📸 냉장고 사진 찍기</b><small>문 열고 한 장! 앨범 사진도 돼요</small></span><img alt="" hidden></label>
<div class="fr-opts">${Object.entries(OPT).map(([k, vs]) => `<div class="fr-o"><small>${{ people: '몇 명이 먹어요?', time: '시간은?', want: '오늘 기분은?' }[k]}</small><div>${vs.map(v => `<button data-k="${k}" data-v="${v}" class="${sel[k] === v ? 'on' : ''}">${v}</button>`).join('')}</div></div>`).join('')}</div>
<button class="fr-go" disabled>🍳 루리야, 오늘 뭐 해 먹지?</button><p class="fr-err" hidden></p><div class="fr-out"></div>`;
  const q = s => ROOT.querySelector(s), go = q('.fr-go'), out = q('.fr-out'), er = q('.fr-err');
  ROOT.querySelectorAll('.fr-o button').forEach(b => b.onclick = () => { sel[b.dataset.k] = b.dataset.v; ROOT.querySelectorAll(`.fr-o button[data-k="${b.dataset.k}"]`).forEach(x => x.classList.toggle('on', x === b)); });
  // 사진은 폰에서 긴 변 1280px JPEG 로 줄여서 보냄 (서버에 저장 안 함)
  q('.fr-shot input').onchange = e => {
    const f = e.target.files[0]; if (!f) return;
    const im = new Image(); im.onload = () => {
      const r = Math.min(1, 1280 / Math.max(im.width, im.height)), c = document.createElement('canvas');
      c.width = Math.round(im.width * r); c.height = Math.round(im.height * r); c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
      let qq = 0.82; img = c.toDataURL('image/jpeg', qq); while (img.length > 1400000 && qq > 0.4) { qq -= 0.12; img = c.toDataURL('image/jpeg', qq); }
      const pv = q('.fr-shot img'); pv.src = img; pv.hidden = false; q('.fr-ph').innerHTML = '<b>📸 다시 찍기</b>'; q('.fr-shot').classList.add('has'); go.disabled = false; URL.revokeObjectURL(im.src);
    }; im.src = URL.createObjectURL(f);
  };
  const card = (m, i) => `<article class="fr-m${i === 0 ? ' top' : ''}"><header><span class="fr-e">${esc(m.emoji || '🍽️')}</span><div><h3>${esc(m.name)}</h3><p><em>⏱ ${esc(m.time || '')}</em><em>${esc(m.level || '')}</em></p></div></header>
<p class="fr-why">${esc(m.why || '')}</p><p class="fr-use">${(m.use || []).map(x => `<span>${esc(x)}</span>`).join('')}${(m.missing || []).map(x => `<span class="no">+ ${esc(x)}</span>`).join('')}</p>
<details${i === 0 ? ' open' : ''}><summary>만드는 법</summary><ol>${(m.steps || []).map(s => `<li>${esc(s)}</li>`).join('')}</ol>${m.tip ? `<p class="fr-tip">💡 ${esc(m.tip)}</p>` : ''}</details></article>`;
  go.onclick = async () => {
    if (!img) return; go.disabled = true; er.hidden = true; ga('fridge_ask', sel);
    out.innerHTML = '<div class="fr-wait"><img src="/assets/ruri/o_desk.webp" alt=""><p>루리가 냉장고를 들여다보는 중… <span>🥕🥚🧅</span></p></div>';
    try {
      const r = await fetch(API + '/api/fridge', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(tok() ? { Authorization: 'Bearer ' + tok() } : {}) }, body: JSON.stringify({ image: img, opt: sel }) });
      const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || '문제가 생겼어요.');
      if (!d.menus || !d.menus.length) { out.innerHTML = `<p class="fr-note">🤔 ${esc(d.note || '재료가 잘 안 보여요. 냉장고 문을 활짝 열고 밝게 다시 찍어 주세요!')}</p>`; return; }
      out.innerHTML = `<section class="fr-ing"><h2>🧺 루리가 찾은 재료 <small>${d.ingredients.length}개</small></h2><p>${d.ingredients.map(x => `<span>${esc(x)}</span>`).join('')}</p>${d.note ? `<p class="fr-note">💬 ${esc(d.note)}</p>` : ''}</section>
<h2 class="fr-h">🍽️ 오늘의 추천 메뉴</h2>${d.menus.map(card).join('')}
<div class="fr-end"><button class="fr-share">📤 오늘 메뉴 공유하기</button><button class="fr-again">📸 다른 사진으로</button></div><p class="fr-left">오늘 ${d.left >= 0 ? d.left + '번 더' : ''} 볼 수 있어요${tok() ? '' : ' · 가입하면 하루 10번'}</p>`;
      ga('fridge_result', { n: d.menus.length });
      q('.fr-again').onclick = () => { q('.fr-shot input').click(); };
      q('.fr-share').onclick = () => {
        const text = `냉장고 털어서 오늘은 「${d.menus[0].name}」! 루리가 골라 줬어요 🍳`, url = location.origin + '/fridge/';
        if (navigator.share) navigator.share({ title: '루리의 냉장고 파먹기', text, url }).catch(() => {});
        else (navigator.clipboard ? navigator.clipboard.writeText(text + ' ' + url) : Promise.reject()).then(() => { q('.fr-share').textContent = '✅ 링크 복사했어요'; }).catch(() => {});
      };
      out.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) { out.innerHTML = ''; er.textContent = e.message; er.hidden = false; }
    finally { go.disabled = false; }
  };
})();
