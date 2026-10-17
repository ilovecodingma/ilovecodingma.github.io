// 루리의 수상 연구소 (/lab/): 공모전 수상작을 모아 분석 → 당선 공식 · 내 문구 진단 · 수상작 모음
// 데이터 /winners.json (공모전_2026\data\winners\analyze.py). 문구는 짧게 인용하고 출처 링크를 늘 붙임, 수상자 개인정보 없음.
(function () {
  const L = document.getElementById('lab'); if (!L) return;
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const tok = () => { try { return localStorage.getItem('jupjup_tok') || ''; } catch { return ''; } };
  const pose = p => `/assets/ruri/p/office_${p}.webp`;
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const FEAT = { pair: ['대구', '앞뒤를 비슷한 길이로 맞춤'], contrast: ['대비어', '오늘/내일·나/우리처럼 맞서는 말'], repeat: ['반복', '같은 낱말을 두 번'], rhyme: ['운율', '앞뒤 끝 글자를 맞춤'],
                 comma: ['쉼표 끊기', '두 덩어리로 끊어 읽힘'], end_noun: ['명사로 끝', '「~행복」「~청렴」처럼 딱 끊음'], exclaim: ['느낌표', '외치는 말투'], number: ['숫자', '하나·첫·숫자 활용'] };
  const JOSA = /(으로|에서|에게|까지|부터|처럼|보다|이랑|하고|이며|이고|은|는|이|가|을|를|에|의|도|로|와|과|만|요|다)$/;
  const PAIRS = [['오늘', '내일'], ['나', '우리'], ['작은', '큰'], ['시작', '완성'], ['지금', '미래'], ['너', '나'], ['어제', '오늘'], ['하나', '모두'], ['빚', '빛'], ['안전', '행복'], ['마음', '세상'], ['일터', '일상']];
  function feats(t) {
    const halves = t.split(/[,，·/!?…]|\s{2,}/).map(s => s.trim()).filter(Boolean), words = (t.match(/[가-힣A-Za-z0-9]+/g) || []).map(w => w.replace(JOSA, ''));
    const cnt = {}; words.filter(w => w.length >= 2).forEach(w => cnt[w] = (cnt[w] || 0) + 1); const ends = t.replace(/[!?.~ ^]+$/, '');
    return { len: t.replace(/\s/g, '').length, comma: /[,，]/.test(t), pair: halves.length === 2 && Math.abs(halves[0].length - halves[1].length) <= 4,
      contrast: PAIRS.some(([a, b]) => t.includes(a) && t.includes(b)), repeat: Object.values(cnt).some(c => c >= 2),
      rhyme: halves.length >= 2 && halves[0].slice(-1) === halves[1].slice(-1), number: /\d|하나|둘|셋|첫/.test(t), exclaim: t.includes('!'), end_noun: !/(다|요|자|라|까|죠|네|해|게|면)$/.test(ends) };
  }
  const grams = s => { const m = new Map(); s = s.toLowerCase().replace(/[^0-9a-z가-힣]/g, ''); for (let i = 0; i < s.length - 1; i++) { const g = s.slice(i, i + 2); m.set(g, (m.get(g) || 0) + 1); } return m; };
  const cos = (a, b) => { let d = 0, na = 0, nb = 0; for (const [g, v] of a) { na += v * v; if (b.has(g)) d += v * b.get(g); } for (const v of b.values()) nb += v * v; return d ? d / Math.sqrt(na * nb) : 0; };
  const pct = x => Math.round(x * 100);

  fetch('/winners.json').then(r => r.json()).then(D => {
    const A = D.all, T = D.top || A, R = D.rest || A, items = D.items;
    const themes = Object.keys(D.theme || {}), lift = Object.keys(FEAT).map(k => ({ k, top: T.rate[k] || 0, rest: R.rate[k] || 0, all: A.rate[k] || 0 })).sort((a, b) => b.all - a.all);
    const best = lift.filter(x => x.top > x.rest + 0.05).sort((a, b) => (b.top - b.rest) - (a.top - a.rest)).slice(0, 2);
    L.innerHTML = `<section class="lb-hero"><img src="${pose('think')}" alt="루리" width="300" height="415"><div><p class="lb-kick">루리의 수상 연구소</p><h1>떨어지는 문구와 <em>붙는 문구</em>는 뭐가 다를까?</h1>
<p>공모전 <b>${D.contests}개</b>의 수상작 <b>${D.count}개</b>를 뜯어봤어요. 슬로건·표어·네이밍부터 시작해요. (길이·기법 통계는 슬로건·표어 ${A.n}개 기준)</p></div></section>
<section class="lb-sec"><h2>🔍 당선 공식</h2><div class="lb-grid">
<div class="lb-card big"><b>길이</b><p class="lb-num">공백 빼고 <em>${A.len_p25}~${A.len_p75}자</em></p><p class="note">가운데 값 ${A.len_med}자 · 1등만 보면 ${T.len_med}자</p></div>
${best.length ? `<div class="lb-card big"><b>1등의 차이</b>${best.map(x => `<p class="lb-num"><em>${FEAT[x.k][0]}</em> ${pct(x.top)}% <small>(나머지 ${pct(x.rest)}%)</small></p>`).join('')}<p class="note">대상·최우수가 장려·입선보다 더 많이 쓴 기법</p></div>` : ''}
${D.naming ? `<div class="lb-card big"><b>네이밍 당선 이름</b><p class="lb-num">평균 <em>${D.naming.len_med}자</em></p><p class="note">짧고 부르기 쉬운 이름이 붙어요 · 수상 ${D.naming.n}개</p></div>` : ''}<div class="lb-card wide"><b>수상작이 자주 쓰는 기법</b>${lift.map(x => `<div class="lb-bar"><span>${FEAT[x.k][0]}</span><i style="--w:${pct(x.all)}%"></i><em>${pct(x.all)}%</em></div>`).join('')}</div></div></section>
<section class="lb-sec" id="diag"><h2>🧪 내 문구 진단</h2><div class="lb-diag"><div class="lb-in"><select class="lb-th"><option value="">주제(선택)</option>${themes.map(t => `<option>${esc(t)}</option>`).join('')}</select>
<input class="lb-q" maxlength="60" placeholder="응모할 슬로건·표어를 써 보세요"><button class="btn2 lb-go">진단받기</button></div><div class="lb-out"></div></div></section>
${themes.length ? `<section class="lb-sec"><h2>🗂 주제별로 자주 나온 말</h2><div class="lb-themes">${themes.map(t => `<div class="lb-card"><b>${esc(t)}</b> <small>${D.theme[t].n}개</small><p>${D.theme[t].words.slice(0, 8).map(w => `<span class="lb-w">${esc(w[0])}</span>`).join('')}</p></div>`).join('')}</div></section>` : ''}
<section class="lb-sec"><h2>📚 수상작 모음</h2><div class="lb-filter"></div><ol class="lb-list"></ol><div class="lb-gate" hidden></div></section>
<p class="lb-foot">수상 문구는 주최 기관 발표·보도에서 짧게 인용했고, 모두 출처를 붙였어요. 저작권과 수상자 정보는 원문을 따라요.</p>`;

    // 진단
    const out = L.querySelector('.lb-out');
    L.querySelector('.lb-go').onclick = () => {
      const q = L.querySelector('.lb-q').value.trim(), th = L.querySelector('.lb-th').value; if (q.length < 3) { out.innerHTML = '<p class="note">문구를 조금 더 써 주세요.</p>'; return; }
      const f = feats(q), S = th && D.theme[th] ? D.theme[th] : A, lenOk = f.len >= S.len_p25 && f.len <= S.len_p75;
      const used = Object.keys(FEAT).filter(k => f[k]), miss = best.map(x => x.k).filter(k => !f[k]);
      let score = 50 + (lenOk ? 20 : f.len < S.len_p25 ? 5 : 0) + used.reduce((a, k) => a + Math.round((A.rate[k] || 0) * 20), 0); score = Math.max(20, Math.min(98, score));
      const gq = grams(q), sim = items.map(i => ({ i, s: cos(gq, grams(i.p)) + (th && i.th === th ? 0.15 : 0) })).sort((a, b) => b.s - a.s).slice(0, 5);
      const tips = [];
      if (f.len < S.len_p25) tips.push(`조금 짧아요. 수상작은 보통 <b>${S.len_p25}~${S.len_p75}자</b>예요.`); else if (f.len > S.len_p75) tips.push(`조금 길어요. <b>${S.len_p75}자</b> 안쪽으로 줄여 봐요.`);
      miss.forEach(k => tips.push(`<b>${FEAT[k][0]}</b>을(를) 넣어 보세요 — ${FEAT[k][1]}. 1등 수상작의 ${pct(T.rate[k])}%가 썼어요.`));
      if (!f.comma && !f.pair) tips.push('두 덩어리로 끊어 보세요. 「A하게, B하게」 꼴이 읽기 쉬워요.');
      out.innerHTML = `<div class="lb-score"><img src="${pose(score >= 75 ? 'v' : score >= 55 ? 'think' : 'awkward')}" alt=""><div><b>${score}점</b><p>${score >= 75 ? '수상작이랑 결이 비슷해요!' : score >= 55 ? '괜찮아요. 조금만 다듬어 볼까요?' : '수상작 패턴과는 거리가 있어요.'}</p></div></div>
<p class="lb-chips">${used.map(k => `<span class="on">${FEAT[k][0]}</span>`).join('')}<span>${f.len}자</span></p>${tips.length ? `<ul class="lb-tips">${tips.map(t => `<li>${t}</li>`).join('')}</ul>` : ''}
<h4>비슷한 수상작</h4><ul class="lb-sim">${sim.map(({ i }) => `<li><q>${esc(i.p)}</q> <small>${esc(i.gr)} · ${esc(i.c)} (${i.y || ''}) · <a href="${esc(i.s)}" target="_blank" rel="noopener nofollow">출처</a></small></li>`).join('')}</ul>`;
      ga('lab_diag', { score, theme: th });
      try { const h = JSON.parse(localStorage.getItem('jupjup_lab') || '[]'); h.unshift({ q, score, th, t: Date.now() }); localStorage.setItem('jupjup_lab', JSON.stringify(h.slice(0, 30))); } catch {}
    };
    L.querySelector('.lb-q').addEventListener('keydown', e => { if (e.key === 'Enter') L.querySelector('.lb-go').click(); });

    // 모음 (비회원은 30개까지, 가입하면 전부)
    const FREE = 30; let fg = '', fth = '';
    const filter = L.querySelector('.lb-filter'), list = L.querySelector('.lb-list'), gate = L.querySelector('.lb-gate');
    const genres = [...new Set(items.map(i => i.g))];
    filter.innerHTML = `<button data-g="" class="on">전체</button>${genres.map(g => `<button data-g="${esc(g)}">${esc(g)}</button>`).join('')}<select class="lb-fth"><option value="">주제 전체</option>${[...new Set(items.map(i => i.th))].map(t => `<option>${esc(t)}</option>`).join('')}</select>`;
    const draw = () => {
      const all = items.filter(i => (!fg || i.g === fg) && (!fth || i.th === fth)), shown = tok() ? all : all.slice(0, FREE);
      list.innerHTML = shown.map(i => `<li class="lb-it r${i.rk}"><q>${esc(i.p)}</q>${i.m ? `<p class="lb-m">💡 ${esc(i.m)}</p>` : ''}<small><b>${esc(i.gr || '수상')}</b> · ${esc(i.c)} · ${esc(i.o)}${i.y ? ' · ' + i.y : ''}${i.n ? ` · ${Number(i.n).toLocaleString()}편 중` : ''} · <a href="${esc(i.s)}" target="_blank" rel="noopener nofollow">출처</a></small></li>`).join('');
      gate.hidden = !!tok() || all.length <= FREE;
      gate.innerHTML = `<p>🔒 수상작 <b>${all.length - FREE}개</b> 더 있어요. 무료 가입하면 전부 보고, 내 문구 진단 기록도 저장돼요.</p><button class="btn2 lb-join">구글·이메일로 1초 가입</button>`;
      const j = gate.querySelector('.lb-join'); if (j) j.onclick = () => { const b = document.querySelector('.cm-in'); b ? b.click() : location.href = '/community/'; };
    };
    filter.querySelectorAll('[data-g]').forEach(b => b.onclick = () => { fg = b.dataset.g; filter.querySelectorAll('[data-g]').forEach(x => x.classList.toggle('on', x === b)); draw(); });
    filter.querySelector('.lb-fth').onchange = e => { fth = e.target.value; draw(); };
    draw();
    const qs = new URLSearchParams(location.search).get('theme'); if (qs && D.theme[qs]) { L.querySelector('.lb-th').value = qs; fth = qs; filter.querySelector('.lb-fth').value = qs; draw(); }
  }).catch(() => { L.innerHTML = '<p class="note">연구소 자료를 불러오지 못했어요.</p>'; });
})();
