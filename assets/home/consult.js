// 루리의 줍줍 메인 = 루리 공모전·청약 상담: 몇 가지 묻고, 우리 DB(/data.json)에서 유사도로 골라 추천만 보여 줌 (2026-10-17 사용자 "그냥 루리 추천해주는 거")
// 유사도 = 상담 답으로 만든 관심 문장 ↔ 공모전(제목·분야·태그·형식·자격) 글자 2-gram 코사인 + 신분·시간·중요한 것 가중
(function () {
  const S = document.getElementById('consult'); if (!S) return;
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const today = (() => { const n = new Date(Date.now() + 324e5); return Math.round(Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate()) / 864e5); })();   // 한국 시간 기준 날짜
  const LATE = new Date(Date.now() + 324e5).getUTCHours() >= 18;   // 18시 이후엔 오늘 마감 공모전을 빼요(마감 시각 정보가 없어서 보수적으로)
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


  // 청약·지원금 상담 (2026-10-17 사용자 "청약 상담도 메인 상담기능에")
  const AQ = [
    { k: 'kinds', multi: true, ask: '어떤 걸 찾아요? 여러 개 골라도 돼요.', pose: 'think',
      opts: { '🏠 아파트 분양': 'apt', '🏘️ 임대·전세임대': 'rent', '💰 지원금·보조금': 'grant', '📈 공모주': 'ipo' } },
    { k: 'region', ask: '어느 지역이 좋아요?', pose: 'point',
      opts: { '서울': /서울/, '경기·인천': /경기|인천|수원|성남|고양|용인|화성|부천|안산|안양|남양주|평택|시흥|파주|김포|의정부|광명|하남|오산|이천|양주|구리|군포|의왕|포천|여주|동두천|과천|가평|양평|연천/,
              '부산·울산·경남': /부산|울산|경남|창원|김해|양산|진주|거제|통영|사천|밀양/, '대구·경북': /대구|경북|포항|구미|경산|안동|김천|영주|경주/,
              '대전·세종·충청': /대전|세종|충북|충남|청주|천안|아산|충주|제천|논산|당진|서산/, '광주·전라': /광주|전북|전남|전주|익산|군산|여수|순천|목포|나주/,
              '강원·제주': /강원|제주|춘천|원주|강릉|속초|서귀포/, '🌏 어디든': null } },
    { k: 'who', ask: '어떤 상황이에요? 우선순위가 달라져요.', pose: 'think',
      opts: { '🎓 청년·대학생': /청년|대학생|사회초년|취업준비|1인/, '💍 신혼·아이 있는 집': /신혼|신생아|출산|육아|자녀|다자녀|한부모/, '🏡 무주택 일반': /무주택|일반|국민|공공/, '🤷 상관없어요': null } },
    { k: 'when', ask: '마지막! 언제까지 넣을 수 있는 게 좋아요?', pose: 'wink',
      opts: { '⚡ 이번 주 안': 7, '📅 한 달 안': 31, '🗓️ 상관없어요': 9999 } },
  ];
  let apps = null, mode = 'contest';
  let items = null, prof = null, shown = 0, ranked = [];
  const outfit = () => { try { const t = localStorage.getItem('jupjup_tok'), o = (JSON.parse(localStorage.getItem('jupjup_prefs') || '{}').o || ''); return t && o && o !== 'smile' ? o.replace(/^o_/, '') : 'office'; } catch { return 'office'; } };
  const pose = p => (window.JUP && window.JUP.poseSrc && window.JUP.poseSrc(outfit(), p, false)) || `/assets/ruri/p/office_${p}.webp`;

  S.innerHTML = `<div class="cs-stage"><p class="cs-title">이 공모전이나<br><em>해 볼까?</em></p><div class="cs-ruri"><img alt="루리" width="300" height="415"></div>
<div class="cs-talk"><span class="cs-name">루리 · 공모전 상담</span><p class="cs-say"></p><div class="cs-opts"></div><form class="cs-free" hidden><input maxlength="40" placeholder="관심 주제가 있으면 적어 주세요 (예: 환경, 반려동물, 부산)"><button>추천받기</button></form></div></div>
<div class="cs-dday" hidden><div class="cs-head"><h2>⏰ 마감 임박 D-3</h2><span class="cs-sum">오늘 안 내면 놓쳐요</span></div><div class="cs-strip"></div></div><div class="cs-res" hidden role="dialog" aria-label="루리 추천"><div class="cs-pbox"><button type="button" class="cs-x" aria-label="닫기">✕</button><div class="cs-ptop"><img class="cs-pr" alt="" width="300" height="415"><div><b class="cs-pname">루리의 추천</b><p class="cs-psay"></p></div></div><div class="cs-head"><h2>이 공모전이나 해 볼까?</h2><span class="cs-sum"></span></div><ol class="cs-list"></ol>
<div class="cs-act"><button class="cs-more">더 보여줘</button><button class="cs-redo">다시 상담할래</button></div></div></div>`;
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
    const QS = mode === 'apply' ? AQ : Q;
    if (mode === 'apply' && n >= QS.length) { prof = { ...ans, mode }; try { localStorage.setItem(KEY, JSON.stringify(prof)); } catch {} ga('consult_done', { mode, kinds: (ans.kinds || []).join(','), region: ans.region, who: ans.who }); opts.innerHTML = ''; recommend(); return; }
    if (n >= QS.length) {
      await talk('좋아요! 관심 있는 주제가 있으면 하나만 더 알려 주세요. 없으면 바로 추천할게요.', 'v');
      opts.innerHTML = '<button class="cs-go">✨ 그냥 추천해 줘</button>'; free.hidden = false; free.querySelector('input').focus({ preventScroll: true });
      const go = topic => { free.hidden = true; opts.innerHTML = ''; prof = { ...ans, topic, mode }; try { localStorage.setItem(KEY, JSON.stringify(prof)); } catch {} ga('consult_done', { can: (ans.can || []).join(','), who: ans.who, time: ans.time, want: ans.want }); recommend(); };
      opts.querySelector('.cs-go').onclick = () => go('');
      free.onsubmit = e => { e.preventDefault(); go(free.querySelector('input').value.trim()); };
      return;
    }
    const q = QS[n]; await talk(q.ask, q.pose);
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
    if ((prof.mode || 'contest') === 'apply') return recApply();
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
    }).filter(x => x.l >= (LATE ? 1 : 0) && x.s > 0).sort((a, b) => b.s - a.s);
    const top = ranked[0] ? ranked[0].s : 1;
    ranked.forEach(x => x.pct = Math.max(41, Math.min(98, Math.round(58 + 40 * x.s / top))));
    shown = 0; list.innerHTML = ''; more(); openPop();
    const n = ranked.length, hot = ranked.slice(0, 5).some(x => x.l <= 3);
    res.querySelector('.cs-sum').textContent = `우리 DB ${items.length}건 중 ${Math.min(n, 99)}건이 맞았어요`;
    talk(!n ? '음… 딱 맞는 게 지금은 없어요. 조건을 조금 바꿔 볼까요?' : hot ? `이거 어때요? 근데 <b>마감이 코앞</b>인 게 있어요. 하려면 지금!` : `<b>${esc(ranked[0].i.title)}</b> 이거나 해 볼래요? 제일 잘 맞아요!`, !n ? 'awkward' : hot ? 'surprise' : 'v');
    const line = !n ? '음… 딱 맞는 게 지금은 없어요. 조건을 조금 바꿔 볼까요?' : hot ? '이거 어때요? 근데 <b>마감이 코앞</b>인 게 있어요. 하려면 지금!' : `<b>${esc(ranked[0].i.title)}</b> 이거나 해 볼래요? 제일 잘 맞아요!`;
    res.querySelector('.cs-psay').innerHTML = line; res.querySelector('.cs-pr').src = pose(!n ? 'awkward' : hot ? 'surprise' : 'v');
    opts.innerHTML = '<button type="button" class="cs-again">✨ 추천 다시 보기</button><button type="button" class="cs-redo2">🔄 다시 상담</button>';
    opts.querySelector('.cs-again').onclick = openPop; opts.querySelector('.cs-redo2').onclick = restart;
  }

  const myAge = () => { try { const a = (JSON.parse(localStorage.getItem('jupjup_prefs') || '{}').age || ''); const m = a.match(/(\d+)/); return m ? +m[1] + 5 : 0; } catch { return 0; } };  // 나이대 가운데값
  async function recApply() {
    mode = 'apply';
    if (!apps) apps = await fetch('/apply.json').then(r => r.json()).catch(() => []);
    const kinds = (prof.kinds || []).map(k => AQ[0].opts[k]), reg = AQ[1].opts[prof.region], who = AQ[2].opts[prof.who], within = AQ[3].opts[prof.when] || 9999;
    ranked = apps.map(i => {
      const hay = i.title + ' ' + i.org, l = left(i.end), why = [];
      if (kinds.length && !kinds.includes(i.kk)) return null;
      if (l < 0 || (l > within && !i.always)) return null;
      let s = 1;
      if (reg) { if (reg.test(hay + ' ' + (i.region || ''))) { s += 2; why.push(prof.region + ' 지역'); } else if (i.region === '전국') { s += 1.6; why.push('전국 누구나'); } else if (/전국|국민|LH|한국주택|HUG|주택도시/.test(hay) || i.kk === 'grant' || i.kk === 'ipo') s += 0.3; else s -= 1.5; }
      if (who) { if (who.test(hay)) { s += 1.2; why.push(prof.who.replace(/^\S+\s/, '') + ' 대상'); } }
      s += l <= 3 ? 0.6 : l <= 7 ? 0.4 : l <= 31 ? 0.2 : 0; if (l <= 7) why.push(l ? `D-${l}` : '오늘 마감');
      const hay2 = hay + ' ' + (i.region || '') + ' ' + (i.target || '');
      if (reg && i.region && i.region !== '전국' && !reg.test(i.region)) return null;  // 지역 한정인데 다른 지역
      if (i.always) { s += 0.5; why.push('지금 신청 가능'); }
      if (who && i.target && who.test(i.target) && !why.some(w => w.includes('대상'))) { s += 1; why.push(prof.who.replace(/^\S+\s/, '') + ' 대상'); }
      const ag = myAge(); if (ag && ((i.age_min && ag < i.age_min - 9) || (i.age_max && ag > i.age_max))) return null;  // 나이 밖
      why.unshift({ apt: '아파트 분양', rent: '임대·전세임대', grant: '지원금', ipo: '공모주' }[i.kk] || i.kind);
      if (i.benefit) why.splice(1, 0, i.benefit.length > 34 ? i.benefit.slice(0, 33) + '…' : i.benefit);
      if (i.target) s += 0.2;  // 대상이 명시된 개인 지원금 우선
      return { i, s, why, l, a: 1 };
    }).filter(Boolean).sort((a, b) => b.s - a.s || a.l - b.l);
    const top = ranked[0] ? ranked[0].s : 1;
    ranked.forEach(x => x.pct = Math.max(41, Math.min(98, Math.round(58 + 40 * x.s / top))));
    shown = 0; list.innerHTML = ''; more(); openPop();
    const n = ranked.length, hot = ranked.slice(0, 5).some(x => x.l <= 3);
    res.querySelector('.cs-head h2').textContent = '이 청약이나 넣어 볼까?';
    res.querySelector('.cs-sum').textContent = `청약·신청 ${apps.length}건 중 ${n}건이 맞았어요`;
    const line = !n ? '음… 지금 조건엔 열려 있는 게 없어요. 지역이나 기간을 넓혀 볼까요?' : hot ? '이거 봐요! <b>곧 마감</b>인 게 있어요. 서류 미리 챙겨요!' : `<b>${esc(ranked[0].i.title)}</b> 이거 넣어 볼래요? 제일 잘 맞아요!`;
    res.querySelector('.cs-psay').innerHTML = line; res.querySelector('.cs-pr').src = pose(!n ? 'awkward' : hot ? 'surprise' : 'v');
    talk(line, !n ? 'awkward' : hot ? 'surprise' : 'v');
    opts.innerHTML = '<button type="button" class="cs-again">✨ 추천 다시 보기</button><button type="button" class="cs-redo2">🔄 다시 상담</button>';
    opts.querySelector('.cs-again').onclick = openPop; opts.querySelector('.cs-redo2').onclick = restart;
  }
  function openPop() { res.hidden = false; document.documentElement.classList.add('cs-lock'); res.scrollTop = 0; ga('consult_popup', {}); }
  function closePop() { res.hidden = true; document.documentElement.classList.remove('cs-lock'); }
  res.addEventListener('click', e => { if (e.target === res || e.target.closest('.cs-x')) closePop(); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && !res.hidden) closePop(); });
  function more() {
    const part = ranked.slice(shown, shown + 5); shown += part.length;
    list.insertAdjacentHTML('beforeend', part.map(({ i, why, l, pct, a }, k) => a ? `<li class="cs-card cs-ap" style="--d:${k * 70}ms"><a href="/a/${esc(i.id)}/"><span class="cs-th"><em>${({ apt: '🏠', rent: '🏘️', grant: '💰', ipo: '📈' })[i.kk] || '📝'}</em></span><span class="cs-b"><span class="cs-match"><i style="width:${pct}%"></i><b>일치도 ${pct}%</b></span><strong>${esc(i.title)}</strong><span class="cs-why">💬 ${esc(why.slice(0, 3).join(' · '))}</span><span class="cs-meta"><em class="${l <= 3 ? 'hot' : ''}">${i.always ? '상시' : l ? 'D-' + l : 'D-DAY'}</em>${esc(i.org || '')}${i.always ? '' : ' · ~' + esc(i.end.slice(5).replace('-', '/'))}</span></span></a></li>` : `<li class="cs-card" style="--d:${k * 70}ms"><a href="/c/${i.id}/">
<span class="cs-th">${i.th ? `<img src="/assets/shots/${i.id}.webp" alt="" loading="lazy">` : '<em>🏆</em>'}</span>
<span class="cs-b"><span class="cs-match"><i style="width:${pct}%"></i><b>일치도 ${pct}%</b></span><strong>${esc(i.title)}</strong>
<span class="cs-why">💬 ${esc(why.slice(0, 3).join(' · '))}</span>
<span class="cs-meta"><em class="${l <= 3 ? 'hot' : ''}">${l ? 'D-' + l : 'D-DAY'}</em>${i.pv ? esc(i.prize.split('·')[0]) : ''} · ${esc(i.org || '')}</span></span></a></li>`).join(''));
    S.querySelector('.cs-more').hidden = shown >= ranked.length;
  }
  function choose() {
    talk('뭐 상담해 줄까요? <b>공모전</b>이든 <b>청약·지원금</b>이든 딱 맞는 걸 골라 줄게요!', 'wave').then(() => {
      opts.innerHTML = '<button type="button" data-m="contest">🏆 공모전 추천받기</button><button type="button" data-m="apply">🏠 청약·지원금 상담</button>';
      opts.querySelectorAll('[data-m]').forEach(b => b.onclick = () => { mode = b.dataset.m; ga('consult_mode', { mode });
        S.querySelector('.cs-title').innerHTML = mode === 'apply' ? '이 청약이나<br><em>넣어 볼까?</em>' : '이 공모전이나<br><em>해 볼까?</em>';
        S.querySelector('.cs-name').textContent = mode === 'apply' ? '루리 · 청약 상담' : '루리 · 공모전 상담';
        res.querySelector('.cs-head h2').textContent = mode === 'apply' ? '이 청약이나 넣어 볼까?' : '이 공모전이나 해 볼까?';
        step(0, {}); });
    });
  }
  function restart() { try { localStorage.removeItem(KEY); } catch {} closePop(); mode = 'contest'; free.hidden = true; S.scrollIntoView({ behavior: 'smooth' }); choose(); return; free.hidden = true; S.scrollIntoView({ behavior: 'smooth' }); step(0, {}); }
  S.querySelector('.cs-more').onclick = () => { more(); ga('consult_more', {}); };
  S.querySelector('.cs-redo').onclick = restart;
  fetch('/data.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    items = d.items;
    const age = (Date.now() - new Date(String(d.updated).replace(' ', 'T') + ':00+09:00')) / 36e5;
    if (age > 3) S.insertAdjacentHTML('afterbegin', `<p class="cs-stale">⏳ 공모전 목록 마지막 갱신이 ${Math.floor(age)}시간 전(${esc(d.updated)})이에요. 마감 여부는 공식 공고로 확인해 주세요.</p>`);
    const dd = items.map(i => ({ i, l: left(i.end) })).filter(x => x.l >= (LATE ? 1 : 0) && x.l <= 3).sort((a, b) => a.l - b.l || (b.i.pv || 0) - (a.i.pv || 0)).slice(0, 12);
    if (dd.length) { S.querySelector('.cs-dday').hidden = false;
      S.querySelector('.cs-strip').innerHTML = dd.map(({ i, l }) => `<a class="cs-dc" href="/c/${i.id}/"><span class="cs-dth">${i.th ? `<img src="/assets/shots/${i.id}.webp" alt="" loading="lazy">` : '<em>⏰</em>'}<b class="${l <= 1 ? 'hot' : ''}">${l ? 'D-' + l : 'D-DAY'}</b></span><strong>${esc(i.title)}</strong><small>${i.pv ? esc(i.prize.split('·')[0]) : esc(i.org || '')}</small></a>`).join(''); }
    try { prof = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { prof = null; }
    if (prof) { mode = prof.mode || 'contest'; if (mode === 'apply') { S.querySelector('.cs-title').innerHTML = '이 청약이나<br><em>넣어 볼까?</em>'; S.querySelector('.cs-name').textContent = '루리 · 청약 상담'; } talk('또 왔네! 오늘은 <b>이거나 해 볼까?</b> 지난번 얘기한 거 기준으로 새로 골라 왔어요.', 'wave').then(recommend); }
    else choose();
  }).catch(() => { S.insertAdjacentHTML('afterbegin', '<p class="cs-stale">공모전 목록을 불러오지 못했어요. 잠시 뒤 새로고침하거나 <a href="/contest/week/">이번 주 마감 목록</a>을 봐 주세요.</p>'); });
})();
