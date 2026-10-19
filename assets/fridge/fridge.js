// 루리의 냉장고 파먹기 (/fridge/) — 냉장고에 있는 재료를 고르면 레시피 중 지금 만들 수 있는 오늘 메뉴를 추천
// 2026-10-18 사용자: "AI 말고 그냥 레시피 추천으로" → 재료 매칭 방식(서버·AI 없이 브라우저에서 계산)
(function () {
  const ROOT = document.getElementById('fridge'); if (!ROOT) return;
  const KEY = 'jupjup_fridge_v1';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  let IMG = null, D = null, have = new Set(), mood = '아무거나', maxMin = 99, TD = null, expMode = false, easyOnly = false, fewDish = false;
  const LS = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || 'null') ?? d; } catch { return d; } }, LSset = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };
  let exp = new Set(LS('jupjup_fridge_exp', [])), made = LS('jupjup_fridge_made', {}), frSeen = LS('jupjup_fridge_seen', {});
  // 2026-10-19 음식 추천 고도화(모델 없음): 대체 재료·날씨·때·제철·곧 상할 재료·개인화·다양성·이유 한 줄
  const SUB = { 돼지고기: ['스팸', '햄', '참치캔', '소고기'], 소고기: ['돼지고기'], 닭고기: ['돼지고기'], 대파: ['양파'], 양파: ['대파'], 스팸: ['햄', '소시지'], 햄: ['스팸', '소시지'], 소시지: ['햄', '스팸'],
    국수: ['라면', '파스타면'], 파스타면: ['국수'], 떡: ['어묵'], 두부: ['달걀'], 애호박: ['가지', '양배추'], 시금치: ['깻잎', '부추'], 콩나물: ['숙주'], 숙주: ['콩나물'], 오징어: ['새우'], 새우: ['오징어'] };
  const CAT = n => /국|찌개|탕|전골|국밥|수프/.test(n) ? '국물' : /국수|면|파스타|라면|우동|스파게티|라볶이|잡채/.test(n) ? '면' : /전$|전 |부침|땡/.test(n) ? '전' : /밥|덮밥|김밥|리조또|오므라이스|동$/.test(n) ? '밥' : /볶음/.test(n) ? '볶음' : /조림|찜/.test(n) ? '조림' : /무침|나물|샐러드|겉절이|생채/.test(n) ? '반찬' : '기타';
  const RO = w => { const c = w.charCodeAt(w.length - 1) - 0xac00; if (c < 0 || c > 11171) return '로'; const j = c % 28; return j === 0 || j === 8 ? '로' : '으로'; };   // 받침 없거나 ㄹ이면 「로」
  const HOUR = new Date(Date.now() + 324e5).getUTCHours();
  try { have = new Set(JSON.parse(localStorage.getItem(KEY) || '[]')); } catch {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify([...have])); } catch {} };
  const MOODS = ['아무거나', '든든', '가벼움', '아이', '안주', '안 매움', '매움', '간식'];
  const TIMES = [[99, '상관없음'], [10, '10분'], [20, '20분'], [30, '30분']];
  // 같은 점수면 날짜마다 다른 메뉴가 먼저 오게 (오늘의 메뉴)
  const day = new Date().toISOString().slice(0, 10), seed = s => { let h = 0; for (const c of day + s) h = (h * 31 + c.charCodeAt(0)) | 0; return (h >>> 0) / 4294967296; };
  function rank() {
    const pref = {}; Object.values(made).forEach(c => { pref[c] = (pref[c] || 0) + 1; }); const pn = Math.max(1, ...Object.values(pref));
    return D.recipes.map(r => {
      const sub = [], lack = r.need.filter(x => { if (have.has(x)) return false; const alt = (SUB[x] || []).find(y => have.has(y)); if (alt) { sub.push([x, alt]); return false; } return true; });
      const plus = r.opt.filter(x => have.has(x)), cat = CAT(r.n), why = [];
      const fit = mood === '아무거나' || r.t.includes(mood);
      const used = r.need.length - lack.length + plus.length, cover = used / (r.need.length + r.opt.length || 1);
      const meal = r.t.includes('든든') ? 2 : r.t.includes('간식') ? -1 : 0;
      let sc = -10 * lack.length - 0.6 * sub.length + used * 2 + cover * 3 + (mood === '아무거나' ? meal : fit ? 3 : 0) + seed(r.n) * 1.5;
      if (TD && TD.want && TD.want[cat]) { sc += TD.want[cat] * 0.9; why.push(TD.why.split('엔')[0]); }
      const ex = [...r.need, ...r.opt].filter(i => exp.has(i) && have.has(i)); if (ex.length) { sc += 4 * ex.length; why.unshift(`곧 상할 ${ex.join('·')} 먼저 쓰기`); }
      const sea = TD ? [...r.need, ...r.opt].filter(i => TD.season.includes(i) && have.has(i)) : []; if (sea.length) { sc += 0.5 * sea.length; why.push(`제철 ${sea[0]}`); }
      if (HOUR < 10 && r.t.includes('가벼움')) sc += 0.8; if (HOUR >= 21 && (r.t.includes('안주') || r.t.includes('간식'))) { sc += 0.8; why.push('야식'); }
      if (pref[cat]) sc += pref[cat] / pn;   // 만들어 본 종류(국물파·볶음파) 선호
      if (frSeen[r.n] && Date.now() - frSeen[r.n] < 3 * 864e5) sc -= 1.2;   // 최근 3일 안에 본 메뉴는 조금 뒤로(질리지 않게)
      const easy = r.lv === '쉬움', few = r.s.length <= 3 || r.s.some(t => /전자레인지/.test(t));
      const nIng = r.need.length + plus.length + sub.length;
      why.push(`있는 재료 ${r.need.length - lack.length + plus.length}개 사용`, `${r.m}분`);
      return { r, lack, plus, sub, cat, score: sc, why: [...new Set(why)].slice(0, 3), easy, few };
    }).filter(x => x.r.m <= maxMin && (!easyOnly || x.easy) && (!fewDish || x.few) && (mood === '아무거나' || x.r.t.includes(mood) || x.lack.length === 0)).sort((a, b) => b.score - a.score);
  }
  // 위쪽 3개는 주재료가 겹치지 않게 (어묵볶음·어묵탕 연달아 X)
  function spread(L) {
    const top = [], rest = [], seen = new Set();
    const cats = new Set();
    for (const x of L) { const k = x.r.need[0]; if (top.length < 3 && !seen.has(k) && !cats.has(x.cat)) { top.push(x); seen.add(k); cats.add(x.cat); } else rest.push(x); }
    return top.concat(rest);
  }
  // 2026-10-19 사용자: 「재료에 맞게 사진이랑 나오게」 — 사진은 출처 표기가 가능한 자유 이용 사진만(recipes_img.json), 없으면 이모지
  const LIC = c => c ? `${esc(c.by || '작가 미상')} · ${esc((c.lic || '').toUpperCase().replace('PDM', '퍼블릭 도메인'))}${c.lv ? ' ' + esc(c.lv) : ''}${c.src ? ` · <a href="${esc(c.src)}" target="_blank" rel="noopener nofollow">원본</a>` : ''}` : '';
  const ph = (r, k) => { const m = IMG && IMG.recipes && IMG.recipes[r.n]; if (!m) return null; if (k === 'main') return m.main && m.main.f ? m.main : null;
    const st = (m.steps || []).find(x => x.k === k); return st ? (st.main ? m.main : st) : null; };
  const look = n => `https://search.naver.com/search.naver?ssc=tab.blog.all&query=${encodeURIComponent(n + ' 만드는 법')}`;
  const yt = n => `https://www.youtube.com/results?search_query=${encodeURIComponent(n + ' 만드는 법')}`;
  const card = (x, big) => { const mp = ph(x.r, 'main'), cr = [];   // id 앵커: 오늘의 한 상에서 이동
    const head = mp ? `<img class="fr-ph" src="${esc(mp.f)}" width="96" height="96" loading="lazy" decoding="async" alt="${esc(x.r.n)} 완성 사진">` : `<span class="fr-e">${x.r.e}</span>`;
    if (mp) cr.push(`완성 사진: ${LIC(mp)}`);
    const steps = x.r.s.map((s, k) => { const p = ph(x.r, k + 1); if (p && p !== mp) cr.push(`${k + 1}단계 사진: ${LIC(p)}`);
      return `<li>${esc(s)}${p ? `<img class="fr-sp" src="${esc(p.f)}" loading="lazy" decoding="async" alt="${esc(x.r.n)} ${k + 1}단계">` : ''}</li>`; }).join('');
    const ing = x.r.need.filter(i => have.has(i)).concat(x.plus).map(i => { const g = IMG && IMG.ing && IMG.ing[i]; if (g) cr.push(`${esc(i)} 사진: ${LIC(g)}`);
      return `<span>${g ? `<img src="${esc(g.f)}" width="22" height="22" loading="lazy" alt="">` : ''}${esc(i)}</span>`; }).join('');
    return `<article class="fr-m${big ? ' best' : ''}" id="m-${encodeURIComponent(x.r.n)}"><header>${head}<div><h3>${esc(x.r.n)}</h3><p><em>⏱ ${x.r.m}분</em><em>${esc(x.r.lv)}</em>${x.r.t.map(t => `<em class="t">#${esc(t)}</em>`).join('')}</p></div></header>
<p class="fr-why">💡 ${esc((x.why || []).join(' · '))}</p>${(x.sub || []).length ? `<p class="fr-sub">🔁 ${x.sub.map(([a, b]) => `${esc(a)} 대신 ${esc(b)}`).join(', ')}${RO(x.sub[x.sub.length - 1][1])} 만들 수 있어요</p>` : ''}
<p class="fr-use">${ing}${x.lack.map(i => `<span class="no">+ ${esc(i)} 사기</span>`).join('')}</p>
<details${big ? ' open' : ''}><summary>만드는 법</summary><ol class="fr-steps">${steps}</ol>${x.r.opt.length ? `<p class="fr-tip">💡 있으면 더 좋아요: ${x.r.opt.map(esc).join(', ')}</p>` : ''}
<p class="fr-look"><button class="fr-made" data-n="${esc(x.r.n)}">${made[x.r.n] ? '✅ 만들어 봤어요' : '👩‍🍳 만들어 봤어요'}</button></p>
<p class="fr-look"><a class="fr-page" href="/fridge/r/${encodeURIComponent(x.r.n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''))}/">📖 레시피 페이지로 보기</a></p>
<p class="fr-look">📷 과정 사진으로 보기: <a href="${look(x.r.n)}" target="_blank" rel="noopener nofollow">네이버 블로그</a> · <a href="${yt(x.r.n)}" target="_blank" rel="noopener nofollow">유튜브</a></p>
${cr.length ? `<details class="fr-cr"><summary>사진 출처</summary><p>${cr.join('<br>')}</p></details>` : ''}</details></article>`; };
  function paint() {
    const cats = Object.entries(D.ing).map(([c, xs]) => `<div class="fr-cat"><small>${esc(c)}</small><div>${xs.map(x => `<button data-i="${esc(x)}" class="${have.has(x) ? 'on' : ''}">${esc(x)}</button>`).join('')}</div></div>`).join('');
    ROOT.innerHTML = `<label class="fr-cam"><input type="file" accept="image/*" capture="environment" hidden><b>📸 냉장고 사진 찍어서 자동 체크</b><small>사진 속 재료를 찾아 아래에 체크해 드려요 · 틀린 건 눌러서 고치면 돼요</small></label><p class="fr-scan" hidden></p>
<section class="fr-pick"><h2>🧊 냉장고에 뭐 있어요? <small class="fr-n">${have.size}개 골랐어요</small></h2><p class="fr-basic">기본양념(${esc(D.basic)})은 있다고 칠게요.</p>${cats}
<button class="fr-clear">비우기</button></section>
<div class="fr-opts"><div class="fr-o"><small>오늘 기분은?</small><div>${MOODS.map(m => `<button data-m="${m}" class="${mood === m ? 'on' : ''}">${m === '아무거나' ? m : '#' + m}</button>`).join('')}</div></div>
<div class="fr-o"><small>시간은?</small><div>${TIMES.map(([v, l]) => `<button data-t="${v}" class="${maxMin === v ? 'on' : ''}">${l}</button>`).join('')}</div></div>
<div class="fr-o"><small>조건</small><div><button data-f="easy" class="${easyOnly ? 'on' : ''}">쉬운 것만</button><button data-f="few" class="${fewDish ? 'on' : ''}">설거지 적게</button><button data-f="exp" class="${expMode ? 'on' : ''}">⏰ 곧 상할 재료 고르기</button></div></div></div>
${TD && TD.picks ? `<section class="fr-wx"><h2 class="fr-h">🌤️ 오늘 날씨에 어울리는 메뉴 <small>${esc(TD.place)} ${Math.round(TD.t)}도 · ${esc(TD.why)}${TD.day ? ' · ' + esc(TD.day) : ''}</small></h2><div class="fr-wxl">${TD.picks.map(n => { const r = D.recipes.find(x => x.n === n); return r ? `<a href="/fridge/r/${encodeURIComponent(n.replace(/[^0-9A-Za-z가-힣]+/g, '-').replace(/^-|-$/g, ''))}/"><span>${r.e}</span><b>${esc(n)}</b><small>${r.m}분 · ${esc(r.lv)}</small></a>` : ''; }).join('')}</div></section>` : ''}
<button class="fr-go">🍳 이 재료로 메뉴 추천받기</button>
<form class="fr-ask"><b>💬 루리에게 물어보기</b><small>고른 재료에 맞춰 골라 드려요 · 예) 매콤하고 든든한 거, 10분 안에 되는 아침</small>
<div><input type="text" maxlength="60" placeholder="어떤 게 당겨요?" aria-label="루리에게 물어볼 내용"><button type="submit">물어보기</button></div></form>
<div class="fr-ans" hidden></div>
<div class="fr-out"></div>`;
    ROOT.querySelectorAll('[data-i]').forEach(b => { if (exp.has(b.dataset.i)) b.classList.add('exp'); b.onclick = () => { const i = b.dataset.i;
      if (expMode) { exp.has(i) ? exp.delete(i) : (exp.add(i), have.add(i), b.classList.add('on')); b.classList.toggle('exp', exp.has(i)); LSset('jupjup_fridge_exp', [...exp]); save(); result(); return; }
      have.has(i) ? (have.delete(i), exp.delete(i), b.classList.remove('exp')) : have.add(i); b.classList.toggle('on'); save(); LSset('jupjup_fridge_exp', [...exp]); ROOT.querySelector('.fr-n').textContent = have.size + '개 골랐어요'; result(); }; });
    ROOT.querySelectorAll('[data-f]').forEach(b => b.onclick = () => { const f = b.dataset.f; if (f === 'easy') easyOnly = !easyOnly; if (f === 'few') fewDish = !fewDish; if (f === 'exp') { expMode = !expMode; ROOT.querySelector('.fr-n').textContent = expMode ? '⏰ 곧 상할 재료를 눌러 주세요' : have.size + '개 골랐어요'; } b.classList.toggle('on'); result(); });
    ROOT.querySelectorAll('[data-m]').forEach(b => b.onclick = () => { mood = b.dataset.m; ROOT.querySelectorAll('[data-m]').forEach(x => x.classList.toggle('on', x === b)); result(); });
    ROOT.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { maxMin = +b.dataset.t; ROOT.querySelectorAll('[data-t]').forEach(x => x.classList.toggle('on', x === b)); result(); });
    ROOT.querySelector('.fr-cam input').onchange = e => scan(e.target.files[0]);
    ROOT.querySelector('.fr-clear').onclick = () => { have.clear(); save(); paint(); };
    ROOT.querySelector('.fr-ask').onsubmit = e => { e.preventDefault(); ask(); };
    ROOT.querySelector('.fr-go').onclick = () => {   // 2026-10-19 사용자: 「추천받기 누르면 나와야지」
      result(); const o = ROOT.querySelector('.fr-out');
      if (!have.size) o.innerHTML = '<p class="fr-note">👆 먼저 냉장고에 있는 재료를 하나 이상 눌러 주세요. 사진을 찍으면 자동으로 골라 드려요.</p>';
      o.scrollIntoView({ behavior: 'smooth', block: 'start' }); ga('fridge_go', { have: have.size });
    };
    result();
  }
  // 물어보기 → 서버가 고른 재료와 질문에 맞는 레시피를 사이트 레시피 안에서 찾아 추천(2026-10-19)
  async function ask() {
    const box = ROOT.querySelector('.fr-ans'), inp = ROOT.querySelector('.fr-ask input');
    const q = inp.value.trim(), API = document.body.dataset.api || 'https://jupjup-api.sung2011103.workers.dev';
    if (!q && !have.size) { box.hidden = false; box.className = 'fr-ans err'; box.textContent = '재료를 고르거나 궁금한 걸 적어 주세요.'; return; }
    box.hidden = false; box.className = 'fr-ans wait'; box.textContent = '🤔 루리가 메뉴를 고르는 중…';
    let tk = ''; try { tk = localStorage.getItem('jupjup_tok') || ''; } catch {}
    try {
      const ac = new AbortController(), to = setTimeout(() => ac.abort(), 30000);
      const res = await fetch(API + '/api/fridge-ask', { signal: ac.signal, method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(tk ? { Authorization: 'Bearer ' + tk } : {}) },
        body: JSON.stringify({ q, have: [...have] }) });
      clearTimeout(to);
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.error || d.answer || '지금은 답하기 어려워요.');
      box.className = 'fr-ans ok';
      box.innerHTML = `<p>${esc(d.answer || '')}</p>` + ((d.picks || []).length
        ? `<div class="fr-wxl">${d.picks.map(x => `<a href="${esc(x.u)}"><span>${esc(x.e || '🍽️')}</span><b>${esc(x.n)}</b><small>${x.m}분 · ${esc(x.lv)}</small></a>`).join('')}</div>` : '');
      ga('fridge_ask', { picks: (d.picks || []).length, have: have.size });
    } catch (e) {
      box.className = 'fr-ans err';
      box.textContent = e.name === 'AbortError' ? '답이 너무 오래 걸려요. 잠시 뒤 다시 물어봐 주세요.' : e.message;
    }
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
    const all = rank(), now = spread(all.filter(x => !x.lack.length)), buy1 = spread(all.filter(x => x.lack.length === 1)).slice(0, 4);
    const soup = now.find(x => x.cat === '국물'), side = now.find(x => ['볶음', '조림', '반찬', '전'].includes(x.cat)), rice = now.find(x => x.cat === '밥');
    const set = soup && side ? [soup, side].concat(rice ? [rice] : []) : null;
    out.innerHTML = (set ? `<section class="fr-set"><h2 class="fr-h">🍱 오늘의 한 상 <small>국 + 반찬${rice ? ' + 밥' : ' + 흰밥'}</small></h2><p>${set.map(x => `${x.r.e} <a href="#m-${encodeURIComponent(x.r.n)}">${esc(x.r.n)}</a>`).join(' · ')} — 지금 있는 재료로 다 만들 수 있어요.</p></section>` : '') + (now.length ? `<h2 class="fr-h">🍽️ 오늘은 이거 어때요? <small>지금 있는 재료로 바로 · ${now.length}개</small></h2>${card(now[0], true)}${now.slice(1, 3).map(x => card(x)).join('')}
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
    now.slice(0, 3).forEach(x => { frSeen[x.r.n] = frSeen[x.r.n] || Date.now(); }); LSset('jupjup_fridge_seen', frSeen);
    out.querySelectorAll('.fr-made').forEach(b => b.onclick = () => { const n = b.dataset.n; const r = D.recipes.find(x => x.n === n); made[n] ? delete made[n] : (made[n] = CAT(n)); LSset('jupjup_fridge_made', made); b.textContent = made[n] ? '✅ 만들어 봤어요' : '👩‍🍳 만들어 봤어요'; ga('fridge_made', {}); try { window.JUP && JUP.api && JUP.api('/api/rec', { method: 'POST', body: { ev: 'click', ids: ['f:' + n] } }).catch(() => {}); } catch (e) {} });
    clearTimeout(window.__frLog); window.__frLog = setTimeout(() => { try { window.JUP && JUP.api && JUP.api('/api/rec', { method: 'POST', body: { ev: 'imp', ids: now.slice(0, 5).map(x => 'f:' + x.r.n), det: now.slice(0, 5).map(x => ({ s: +x.score.toFixed(2), cat: x.cat })) } }).catch(() => {}); } catch (e) {} }, 3000);
    clearTimeout(gaT); gaT = setTimeout(() => ga('fridge_result', { have: have.size, now: now.length, mood }), 1500);
  }
  Promise.all([fetch('/assets/fridge/recipes.json?v=6').then(r => r.json()), fetch('/assets/fridge/recipes_ph.json?v=' + Math.floor(Date.now() / 36e5)).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch('/assets/fridge/today.json?v=' + Math.floor(Date.now() / 36e5)).then(r => r.ok ? r.json() : null).catch(() => null)])
    .then(([d, im, td]) => { D = d; IMG = im; TD = td; paint(); }).catch(() => { ROOT.innerHTML = '<p class="fr-note">레시피를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.</p>'; });
})();
