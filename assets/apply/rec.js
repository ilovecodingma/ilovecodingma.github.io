// 루리의 청약 추천 (/apply/recommend/) — 2026-10-18 사용자: "청약 추천도 만들어"
// 내 상황 → ① 청약 가점(84점) ② 노려볼 공급 유형(일반 안내, 세부 자격은 공고문·청약홈) ③ 지금 접수 중인 공고 중 맞는 것. 브라우저 안에서만 계산, 서버 저장 없음.
(function () {
  const R = document.getElementById('aprec'); if (!R) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const KEY = 'jupjup_aprec_v1';
  const REG = ['전국', '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'];
  const CITY = { 경기: '수원|성남|고양|용인|부천|안산|안양|남양주|화성|평택|의정부|시흥|파주|김포|광명|광주시|군포|하남|오산|이천|양주|구리|안성|포천|의왕|여주|동탄|위례', 경남: '창원|김해|양산|진주|거제|통영|사천|밀양|창녕|함안|거창', 경북: '포항|구미|경산|경주|안동|김천|영주|상주|칠곡', 충남: '천안|아산|서산|당진|논산|공주|보령|계룡|내포', 충북: '청주|충주|제천|음성|진천', 전북: '전주|익산|군산|정읍|완주|김제', 전남: '여수|순천|목포|광양|나주|무안', 강원: '춘천|원주|강릉|속초|동해|삼척', 제주: '서귀포' };
  const today = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
  let D = [];
  let S = (() => { try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch { return null; } })() || { reg: '전국', age: 30, mar: 'single', kids: 0, h: 0, f: 0, b: 2, never: true, parent: false, want: 'any', inc: 'mid' };
  const sel = (k, opts) => `<select data-k="${k}">${opts.map(([v, t]) => `<option value="${v}"${String(S[k]) === String(v) ? ' selected' : ''}>${t}</option>`).join('')}</select>`;
  const yrs = (n, f) => Array.from({ length: n }, (_, i) => [i, f(i)]);
  function form() {
    R.innerHTML = `<div class="ar-f">
<label>사는 곳·원하는 지역${sel('reg', REG.map(r => [r, r]))}</label>
<label>나이(만)${sel('age', Array.from({ length: 60 }, (_, i) => [i + 19, (i + 19) + '세']))}</label>
<label>결혼${sel('mar', [['single', '미혼'], ['new', '결혼 7년 이내(예비 포함)'], ['old', '결혼 7년 넘음']])}</label>
<label>미성년 자녀${sel('kids', yrs(5, i => i + '명'))}</label>
<label>무주택 기간${sel('h', yrs(16, i => i === 0 ? '1년 미만' : i === 15 ? '15년 이상' : i + '년 이상'))}</label>
<label>부양가족(본인 제외)${sel('f', yrs(7, i => i === 6 ? '6명 이상' : i + '명'))}</label>
<label>청약통장 가입${sel('b', yrs(16, i => i === 0 ? '1년 미만' : i === 15 ? '15년 이상' : i + '년 이상'))}</label>
<label>소득 수준${sel('inc', [['low', '낮은 편(중위소득 이하)'], ['mid', '보통'], ['high', '높은 편']])}</label>
<label>원하는 집${sel('want', [['any', '상관없음'], ['own', '내 집(분양)'], ['rent', '싸게 오래 살기(임대)']])}</label>
<label class="ar-ck"><input type="checkbox" data-k="never"${S.never ? ' checked' : ''}> 나와 세대원 모두 집을 가져 본 적 없음</label>
<label class="ar-ck"><input type="checkbox" data-k="parent"${S.parent ? ' checked' : ''}> 만 65세 이상 부모님을 3년 넘게 모시고 있음</label>
<button class="ar-go">🏠 청약 추천받기</button></div><div class="ar-out"></div>`;
    R.querySelectorAll('[data-k]').forEach(e => e.onchange = () => { S[e.dataset.k] = e.type === 'checkbox' ? e.checked : (isNaN(+e.value) ? e.value : +e.value); });
    R.querySelector('.ar-go').onclick = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} ga('apply_rec', { reg: S.reg, want: S.want }); result(); R.querySelector('.ar-out').scrollIntoView({ behavior: 'smooth' }); };
    if (localStorage.getItem(KEY)) result();
  }
  function score() {
    const H = S.age < 30 && S.mar === 'single' ? 0 : Math.min(32, 2 * (S.h + 1)), F = Math.min(35, 5 * (S.f + 1)), B = Math.min(17, S.b + 2);
    return { H, F, B, T: H + F + B };
  }
  function types(g) {
    const t = [];
    if (S.mar === 'new') t.push(['💍 신혼부부 특별공급', '혼인 7년 이내(예비 신혼 포함)면 노려볼 수 있어요. 소득·자산 기준이 있어요.']);
    if (S.never) t.push(['🔑 생애최초 특별공급', '세대원 모두 집을 가져 본 적이 없으면 대상이 될 수 있어요. 소득 기준·납입 조건이 있어요.']);
    if (S.kids >= 2) t.push(['👨‍👩‍👧‍👦 다자녀 특별공급', '미성년 자녀가 여러 명이면 대상이 될 수 있어요(자녀 수 기준은 공고 확인).']);
    if (S.parent) t.push(['👵 노부모부양 특별공급', '만 65세 이상 직계존속을 3년 이상 모시면 대상이 될 수 있어요.']);
    if (S.age >= 19 && S.age <= 39 && S.mar !== 'old') t.push(['🌱 청년 대상 공급', '공공분양 청년 특별공급, 행복주택 청년 물량 등 나이·소득 기준이 있는 청년 몫을 같이 보세요.']);
    if (S.want !== 'own' && (S.inc !== 'high')) t.push(['🏘️ 공공임대(행복주택·국민임대)', '시세보다 싸게 오래 살 수 있는 임대예요. 소득·자산 기준이 있어요.']);
    t.push(g.T >= 60 ? ['📈 일반공급 가점제', `가점 ${g.T}점이면 가점제로도 해볼 만한 단지가 많아요. 인기 단지는 커트라인이 더 높을 수 있어요.`]
      : g.T >= 45 ? ['⚖️ 일반공급(가점제+추첨제)', `가점 ${g.T}점이면 지방·비인기 단지 가점제나 추첨제 물량을 같이 노려 보세요.`]
        : ['🎲 일반공급 추첨제·무순위', `가점 ${g.T}점이면 가점제보다 추첨제 물량이나 무순위(줍줍)를 보는 게 현실적이에요.`]);
    return t;
  }
  const inReg = x => { if (S.reg === '전국') return true; const t = x.title + ' ' + (x.org || '') + ' ' + (x.region || ''); return t.includes(S.reg) || (CITY[S.reg] && new RegExp(CITY[S.reg]).test(t)); };
  function picks() {
    let L = D.filter(x => /아파트 청약|공공임대/.test(x.kind || '') && (!x.end || x.end >= today));
    if (S.want === 'own') L = L.filter(x => x.kind === '아파트 청약'); if (S.want === 'rent') L = L.filter(x => x.kind === '공공임대');
    const sc = x => (inReg(x) ? 10 : 0) + (S.mar === 'new' && /신혼|행복/.test(x.title) ? 3 : 0) + (S.age <= 39 && /청년|행복/.test(x.title) ? 2 : 0) + (/무순위|잔여|취소분|줍줍/.test(x.title) && score().T < 45 ? 2 : 0);
    return L.map(x => ({ x, s: sc(x), why: [inReg(x) && S.reg !== '전국' ? S.reg : '', /신혼/.test(x.title) ? '신혼' : '', /청년|행복/.test(x.title) ? '청년·행복주택' : '', /무순위|잔여|취소분/.test(x.title) ? '무순위(가점 없이)' : ''].filter(Boolean) }))
      .filter(o => S.reg === '전국' || o.s >= 10).sort((a, b) => b.s - a.s || (a.x.end || '').localeCompare(b.x.end || '')).slice(0, 10);
  }
  function result() {
    const g = score(), T = types(g), P = picks();
    R.querySelector('.ar-out').innerHTML = `<section class="ar-s"><h2>🧮 내 청약 가점 <b>${g.T}점</b> <small>/ 84점</small></h2><div class="ar-bar"><i style="width:${Math.round(g.T / 84 * 100)}%"></i></div>
<p class="ar-d">무주택 ${g.H}점 · 부양가족 ${g.F}점 · 통장 ${g.B}점 <small>(대략 계산이에요. 무주택 기간·부양가족 인정 기준은 공고문 기준)</small></p></section>
<section class="ar-s"><h2>🎯 노려볼 만한 공급 유형</h2><ul class="ar-t">${T.map(([a, b]) => `<li><b>${a}</b><span>${b}</span></li>`).join('')}</ul>
<p class="ar-n">세부 자격(소득·자산·지역 거주기간 등)은 단지마다 달라요. 꼭 공고문과 <a href="https://www.applyhome.co.kr" target="_blank" rel="noopener">청약홈</a>에서 확인하세요.</p></section>
<section class="ar-s"><h2>🏠 지금 접수 중·곧 열리는 공고 ${P.length ? P.length + '건' : ''}</h2>${P.length ? `<ul class="ar-l">${P.map(({ x, why }) => `<li><a href="/a/${esc(x.id)}/"><b>${esc(x.title)}</b><span>${esc(x.kind)} · ${x.start ? esc(x.start.slice(5).replace('-', '/')) + '~' : ''}${esc((x.end || '').slice(5).replace('-', '/'))}${why.length ? ' · ' + why.map(esc).join(' · ') : ''}</span></a></li>`).join('')}</ul>`
        : `<p class="ar-n">${esc(S.reg)} 지역에 지금 접수 중인 공고가 없어요. 지역을 「전국」으로 바꿔 보거나, <a href="/app/">폰 알림</a>을 켜 두세요.</p>`}</section>`;
  }
  fetch('/apply.json', { cache: 'no-cache' }).then(r => r.json()).then(d => { D = d; form(); }).catch(() => { R.innerHTML = '<p>데이터를 불러오지 못했어요.</p>'; });
})();
