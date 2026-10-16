// 루리의 줍줍 메인 = 루리 공모전 상담: 몇 가지 묻고, 우리 DB(/data.json)에서 유사도로 골라 추천만 보여 줌 (2026-10-17 사용자 "그냥 루리 추천해주는 거")
// 유사도 = 상담 답으로 만든 관심 문장 ↔ 공모전(제목·분야·태그·형식·자격) 글자 2-gram 코사인 + 신분·시간·중요한 것 가중
(function () {
  const S = document.getElementById('consult'); if (!S) return;
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const today = (() => { const n = new Date(); return Math.round(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) / 864e5); })();
  const left = e => { const p = e.split('-'); return Math.round(Date.UTC(+p[0], p[1] - 1, +p[2]) / 864e5) - today; };
  const KEY = 'jupjup_consult_v1';
  const Q = [
    { k: 'can', multi: true, ask: '먼저, 뭘 잘하거나 해 보고 싶어요? 여러 개 골라도 돼요.', pose: 'think',
      opts: { '✍️ 글·슬로건': '글 슬로건 네이밍 표어 시 수필 수기 에세이 문학 백일장 삼행시', '💡 아이디어·기획': '아이디어 정책 제안 기획 창업 마케팅', '🎨 그림·디자인': '디자인 캐릭터 포스터 일러스트 웹툰 그림 로고',
              '🎬 영상·사진': '영상 숏폼 사진 UCC 릴스 촬영 영화', '💻 코딩·AI': 'AI 해커톤 개발 데이터 SW 코딩 앱', '🎲 아무거나': '' } },
    { k: 'who', ask: '지금 어떤 상황이에요? 자격에 맞는 것만 고를게요.', pose: 'point',
      opts: { '🎒 초중고 학생': /청소년|중학|고등|초등|학생|누구나|제한\s*없/, '🎓 대학생': /대학|대학생|대학원|청년|누구나|제한\s*없|국민|일반/, '💼 직장인·일반': /일반|성인|국민|누구나|제한\s*없|청년/ } },
    { k: 'time', ask: '시간은 얼마나 쓸 수 있어요?', pose: 'think',
      opts: { '⚡ 10분이면 끝나는 거': 'quick', '📅 주말 하루 정도': 'mid', '🔥 한 달 공들여서': 'long' } },
    { k: 'want', ask: '마지막! 뭐가 더 중요해요?', pose: 'wink',
      opts: { '💰 상금 큰 거': 'prize', '🍀 경쟁 적어서 될 것 같은 거': 'chance', '⏰ 마감 급해도 OK': 'soon' } },
  ];
  const EASY = /슬로건|네이밍|명칭|표어|문구|한\s*줄|삼행시|N행시|디카시|사진|댓글|퀴즈|설문|손편지|짧은/;
  const HEAVY = /논문|영상|영화|해커톤|창업|기획서|제안서|시나리오|소설|웹툰|애니메이션|앱/;
  const LOCAL = /(시민|도민|구민|군민|거주|재학|재직|관내)/;

  let items = null, prof = null, shown = 0, ranked = [];
  const outfit = () => { try { const t = localStorage.getItem('jupjup_tok'), o = (JSON.parse(localStorage.getItem('jupjup_prefs') || '{}').o || ''); return t && o && o !== 'smile' ? o.replace(/^o_/, '') : 'office'; } catch { return 'office'; } };
  const pose = p => (window.JUP && window.JUP.poseSrc && window.JUP.poseSrc(outfit(), p, false)) || `/assets/ruri/p/office_${p}.webp`;

  S.innerHTML = `<div class="cs-stage"><p class="cs-title">이 공모전이나<br><em>해 볼까?</em></p><div class="cs-ruri"><img alt="루리" width="300" height="415"></div>
<div class="cs-talk"><span class="cs-name">루리 · 공모전 상담</span><p class="cs-say"></p><div class="cs-opts"></div><form class="cs-free" hidden><input maxlength="40" placeholder="관심 주제가 있으면 적어 주세요 (예: 환경, 반려동물, 부산)"><button>추천받기</button></form></div></div>
<div class="cs-dday" hidden><div class="cs-head"><h2>⏰ 마감 임박 D-3</h2><span class="cs-sum">오늘 안 내면 놓쳐요</span></div><div class="cs-strip"></div></div><div class="cs-res" hidden><div class="cs-head"><h2>이 공모전이나 해 볼까?</h2><span class="cs-sum"></span></div><ol class="cs-list"></ol>
<div class="cs-act"><button class="cs-more">더 보여줘</button><button class="cs-redo">다시 상담할래</button></div></div>`;
  const img = S.querySelector('.cs-ruri img'), say = S.querySelector('.cs-say'), opts = S.querySelector('.cs-opts'), free = S.querySelector('.cs-free');
  const res = S.querySelector('.cs-res'), list = S.querySelector('.cs-list');
  let typing;
  function talk(text, p) {
    const src = pose(p); if (!img.src.endsWith(src)) { img.classList.remove('pop'); void img.offsetWidth; img.classList.add('pop'); img.src = src; }
    clearInterval(typing); const plain = text.replace(/<[^>]+>/g, ''); let i = 0;
    return new Promise(done => { typing = setInterval(() => { i += 2; say.textContent = plain.slice(0, i); if (i >= plain.length) { clearInterval(typing); say.innerHTML = text; done(); } }, 22); });
  }
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };

  async function step(n, ans) {
    if (n >= Q.length) {
      await talk('좋아요! 관심 있는 주제가 있으면 하나만 더 알려 주세요. 없으면 바로 추천할게요.', 'v');
      opts.innerHTML = '<button class="cs-go">✨ 그냥 추천해 줘</button>'; free.hidden = false; free.querySelector('input').focus({ preventScroll: true });
      const go = topic => { free.hidden = true; opts.innerHTML = ''; prof = { ...ans, topic }; try { localStorage.setItem(KEY, JSON.stringify(prof)); } catch {} ga('consult_done', { can: (ans.can || []).join(','), who: ans.who, time: ans.time, want: ans.want }); recommend(); };
      opts.querySelector('.cs-go').onclick = () => go('');
      free.onsubmit = e => { e.preventDefault(); go(free.querySelector('input').value.trim()); };
      return;
    }
    const q = Q[n]; await talk(q.ask, q.pose);
    const keys = Object.keys(q.opts), sel = new Set();
    opts.innerHTML = keys.map(k => `<button type="button">${k}</button>`).join('') + (q.multi ? '<button type="button" class="cs-next" disabled>다음 →</button>' : '');
    opts.querySelectorAll('button:not(.cs-next)').forEach((b, i) => b.onclick = () => {
      if (!q.multi) { step(n + 1, { ...ans, [q.k]: keys[i] }); return; }
      b.classList.toggle('on'); b.classList.contains('on') ? sel.add(keys[i]) : sel.delete(keys[i]); opts.querySelector('.cs-next').disabled = !sel.size;
    });
    if (q.multi) opts.querySelector('.cs-next').onclick = () => step(n + 1, { ...ans, [q.k]: [...sel] });
  }

  // ---- 유사도 추천 ----
  const grams = s => { const m = new Map(); s = s.toLowerCase().replace(/[^0-9a-z가-힣]/g, ''); for (let i = 0; i < s.length - 1; i++) { const g = s.slice(i, i + 2); m.set(g, (m.get(g) || 0) + 1); } return m; };
  const cos = (a, b) => { let d = 0, na = 0, nb = 0; for (const [g, v] of a) { na += v * v; if (b.has(g)) d += v * b.get(g); } for (const v of b.values()) nb += v * v; return d ? d / Math.sqrt(na * nb) : 0; };
  function recommend() {
    const want = (prof.can || []).map(k => Q[0].opts[k]).join(' ') + ' ' + (prof.topic || '');
    const qv = grams(want), whoRe = Q[1].opts[prof.who], time = Q[2].opts[prof.time], pref = Q[3].opts[prof.want];
    ranked = items.map(i => {
      const hay = i.title + ' ' + i.field + ' ' + i.tags.join(' ') + ' ' + (i.effort || ''), why = [];
      let s = want.trim() ? cos(qv, grams(hay)) * 3 : 0.5;
      if (prof.topic && hay.concat(i.org, i.elig || '').includes(prof.topic)) { s += 1.2; why.push(`「${prof.topic}」 관련`); }
      if (whoRe) { if (whoRe.test(i.elig || '')) { s += 0.4; why.push(prof.who.replace(/^\S+\s/, '') + ' 참가 가능'); } else s -= 0.8; }
      const easy = EASY.test(hay), heavy = HEAVY.test(hay);
      if (time === 'quick') { if (easy) { s += 0.9; why.push('금방 낼 수 있어요'); } if (heavy) s -= 0.7; }
      if (time === 'long' && heavy) { s += 0.4; why.push('공들일 만한 대회'); }
      if (pref === 'prize' && i.pv) { s += Math.min(1.2, Math.log10(i.pv) - 5); if (i.pv >= 1e6) why.push(i.prize.split('·')[0].trim()); }
      if (pref === 'chance') { if (LOCAL.test(i.elig || '')) { s += 0.6; why.push('지역·자격 한정이라 경쟁 적을 듯'); } if (i.pv && i.pv < 1e6) s += 0.2; }
      const l = left(i.end);
      if (pref === 'soon' && l <= 7) { s += 0.6; why.push('곧 마감'); } else if (l <= 1) s -= 0.6;
      if (!why.length && want.trim()) why.push('관심 분야와 비슷해요');
      return { i, s, why, l };
    }).filter(x => x.l >= 0 && x.s > 0).sort((a, b) => b.s - a.s);
    const top = ranked[0] ? ranked[0].s : 1;
    ranked.forEach(x => x.pct = Math.max(41, Math.min(98, Math.round(58 + 40 * x.s / top))));
    shown = 0; list.innerHTML = ''; res.hidden = false; more();
    const n = ranked.length, hot = ranked.slice(0, 5).some(x => x.l <= 3);
    res.querySelector('.cs-sum').textContent = `우리 DB ${items.length}건 중 ${Math.min(n, 99)}건이 맞았어요`;
    talk(!n ? '음… 딱 맞는 게 지금은 없어요. 조건을 조금 바꿔 볼까요?' : hot ? `이거 어때요? 근데 <b>마감이 코앞</b>인 게 있어요. 하려면 지금!` : `<b>${esc(ranked[0].i.title)}</b> 이거나 해 볼래요? 제일 잘 맞아요!`, !n ? 'awkward' : hot ? 'surprise' : 'v');
    opts.innerHTML = '<button type="button" class="cs-redo2">🔄 다시 상담</button>'; opts.querySelector('.cs-redo2').onclick = restart;
    res.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function more() {
    const part = ranked.slice(shown, shown + 5); shown += part.length;
    list.insertAdjacentHTML('beforeend', part.map(({ i, why, l, pct }, k) => `<li class="cs-card" style="--d:${k * 70}ms"><a href="/c/${i.id}/">
<span class="cs-th">${i.th ? `<img src="/assets/shots/${i.id}.webp" alt="" loading="lazy">` : '<em>🏆</em>'}</span>
<span class="cs-b"><span class="cs-match"><i style="width:${pct}%"></i><b>일치도 ${pct}%</b></span><strong>${esc(i.title)}</strong>
<span class="cs-why">💬 ${esc(why.slice(0, 3).join(' · '))}</span>
<span class="cs-meta"><em class="${l <= 3 ? 'hot' : ''}">${l ? 'D-' + l : 'D-DAY'}</em>${i.pv ? esc(i.prize.split('·')[0]) : ''} · ${esc(i.org || '')}</span></span></a></li>`).join(''));
    S.querySelector('.cs-more').hidden = shown >= ranked.length;
  }
  function restart() { try { localStorage.removeItem(KEY); } catch {} res.hidden = true; free.hidden = true; S.scrollIntoView({ behavior: 'smooth' }); step(0, {}); }
  S.querySelector('.cs-more').onclick = () => { more(); ga('consult_more', {}); };
  S.querySelector('.cs-redo').onclick = restart;
  fetch('/data.json').then(r => r.json()).then(d => {
    items = d.items;
    const dd = items.map(i => ({ i, l: left(i.end) })).filter(x => x.l >= 0 && x.l <= 3).sort((a, b) => a.l - b.l || (b.i.pv || 0) - (a.i.pv || 0)).slice(0, 12);
    if (dd.length) { S.querySelector('.cs-dday').hidden = false;
      S.querySelector('.cs-strip').innerHTML = dd.map(({ i, l }) => `<a class="cs-dc" href="/c/${i.id}/"><span class="cs-dth">${i.th ? `<img src="/assets/shots/${i.id}.webp" alt="" loading="lazy">` : '<em>⏰</em>'}<b class="${l <= 1 ? 'hot' : ''}">${l ? 'D-' + l : 'D-DAY'}</b></span><strong>${esc(i.title)}</strong><small>${i.pv ? esc(i.prize.split('·')[0]) : esc(i.org || '')}</small></a>`).join(''); }
    try { prof = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { prof = null; }
    if (prof) { talk('또 왔네! 오늘은 <b>이거나 해 볼까?</b> 지난번 얘기한 거 기준으로 새로 골라 왔어요.', 'wave').then(recommend); }
    else talk('심심한데 <b>공모전이나 하나 해 볼까?</b> 뭐가 맞을지 내가 골라 줄게! 몇 개만 물어볼게요.', 'wave').then(() => setTimeout(() => step(0, {}), 500));
  });
})();
