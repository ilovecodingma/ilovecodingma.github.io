// 루리의 준비실 (/prep/) — 공모전별 준비 보드(역산 일정·체크리스트·메모), 분량 계산기, 장르별 꿀팁
// 2026-10-18 사용자: "공모전 정보 공유뿐 아니라 공모전 준비할 사람들이 더 편하게 준비할 공간, 꿀팁도 공유"
(function () {
  const ROOT = document.getElementById('prep'); if (!ROOT) return;
  const KEY = 'jupjup_prep_v1';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const today = () => { const n = new Date(); return Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()); };
  const ut = s => { const p = s.split('-'); return Date.UTC(+p[0], p[1] - 1, +p[2]); };
  const left = end => end ? Math.round((ut(end) - today()) / 864e5) : 99;
  const ymd = t => new Date(t).toISOString().slice(0, 10);
  const md = s => s.slice(5).replace('-', '/');
  const dlab = l => l < 0 ? '마감' : l === 0 ? 'D-DAY' : 'D-' + l;
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  let G = [], C = [], S = {}, J = null;
  const load = () => { try { S = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch { S = {}; } };
  const saveLocal = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} };
  let timer = null; const dirty = new Set();
  function save(id) {
    if (S[id]) S[id].updated = Math.floor(Date.now() / 1000);
    saveLocal(); if (!(J && J.st.t)) return;
    dirty.add(id); clearTimeout(timer);
    timer = setTimeout(() => {
      const items = [...dirty].map(i => S[i] ? { id: i, updated: S[i].updated, data: S[i] } : { id: i, del: 1 }); dirty.clear();
      J.api('/api/prep', { method: 'POST', body: { items } }).catch(() => {});
    }, 700);
  }
  async function syncServer() {
    if (!(J && J.st.t)) return;
    const r = await J.api('/api/prep').catch(() => null); if (!r) return;
    const up = [];
    r.prep.forEach(x => { if (!S[x.id] || (S[x.id].updated || 0) < x.updated) S[x.id] = x; });
    Object.keys(S).forEach(id => { const sv = r.prep.find(x => x.id === id); if (!sv || sv.updated < (S[id].updated || 0)) up.push({ id, updated: S[id].updated || 0, data: S[id] }); });
    saveLocal(); if (up.length) J.api('/api/prep', { method: 'POST', body: { items: up } }).catch(() => {});
  }
  const genre = g => G.find(x => x.g === g) || G.find(x => x.g === 'all');
  function genreOf(c) {
    const e = c.effort || '', t = c.title || '', tg = c.tags || [];
    if (/슬로건|네이밍/.test(e) || /슬로건|표어|네이밍|명칭|애칭|캐치프레이즈|삼행시|N행시/.test(t)) return 'slogan';
    if (e === '사진' || (/사진/.test(t) && !/영상/.test(t))) return 'photo';
    if (e === '영상' || tg.includes('영상')) return 'video';
    if (e === '디자인' || tg.includes('디자인')) return 'design';
    if (/원고|짧은 글/.test(e) || tg.includes('문학')) return 'writing';
    if (/제안서|기획서/.test(e) || tg.includes('아이디어·정책')) return 'idea';
    if (tg.includes('논문')) return 'paper';
    if (tg.includes('IT·과학')) return 'it';
    return 'all';
  }
  const maxOff = gg => Math.max(...gg.steps.map(s => -s[0]));
  // 역산 일정: 마감이 가까우면 단계 간격을 남은 날짜에 맞춰 줄임
  function plan(b) {
    const gg = genre(b.g), max = maxOff(gg), l = Math.max(0, left(b.end)), k = l < max ? l / max : 1;
    return gg.steps.map((s, i) => { let t = ut(b.end) + Math.round(s[0] * k) * 864e5; if (t < today() && l < max) t = today(); return { i, d: ymd(t), name: s[1], desc: s[2] }; });
  }
  const checksOf = b => genre(b.g).checks.concat(b.g === 'all' ? [] : genre('all').checks.slice(0, 3));
  const prog = b => { const n = genre(b.g).steps.length + checksOf(b).length, d = (b.steps || []).filter(Boolean).length + (b.checks || []).filter(Boolean).length; return n ? Math.min(100, Math.round(d / n * 100)) : 0; };
  function startBoard(c) {
    const id = 'c:' + c.id;
    if (!S[id]) {
      S[id] = { title: c.title, end: c.end, g: genreOf(c), url: '/c/' + c.id + '/', steps: [], checks: [], memo: '', done: false, created: Math.floor(Date.now() / 1000) };
      save(id); ga('prep_start', { id: c.id, g: S[id].g });
      if (J && J.st.t) J.api('/api/items', { method: 'POST', body: { items: [{ id, title: c.title, end: c.end, fav: 1 }] } }).catch(() => {});
    }
    if (location.hash === '#' + id) board(id); else location.hash = id;
  }
  // ---- 화면 ----
  const top = document.createElement('div'); top.id = 'prep-top'; ROOT.prepend(top);
  function home() {
    const list = Object.entries(S).sort((a, b) => (a[1].done - b[1].done) || left(a[1].end) - left(b[1].end));
    const cards = list.map(([id, b]) => {
      const l = left(b.end), p = prog(b), gg = genre(b.g), nx = plan(b).find(s => !(b.steps || [])[s.i]);
      return `<li><a href="#${esc(id)}" class="pp-card${b.done ? ' done' : ''}"><span class="pp-ic">${gg.icon}</span><div><b>${esc(b.title)}</b><em class="${l <= 3 && l >= 0 ? 'hot' : ''}">${b.done ? '✅ 냈어요' : dlab(l)}</em><small>${b.done ? '결과 기다리는 중' : nx ? '다음: ' + esc(nx.name) + ' (' + md(nx.d) + ')' : '모든 단계 완료!'}</small><i class="pp-bar"><i style="width:${p}%"></i></i></div></a></li>`;
    }).join('');
    top.innerHTML = `<section class="pp-start"><h2>📋 어떤 공모전을 준비할까요?</h2><div class="pp-search"><input type="search" placeholder="공모전 이름으로 찾기 (예: 슬로건, 숏폼, 수기)" aria-label="공모전 찾기"><ul class="pp-res"></ul></div>
<p class="pp-or">찾아서 누르면 마감일에 맞춘 <b>준비 일정·체크리스트</b>가 바로 만들어져요.</p></section>
${list.length ? `<section class="pp-mine"><h2>🗂️ 내 준비 보드 <small>${list.length}개</small></h2><ul>${cards}</ul></section>`
      : '<p class="pp-empty">아직 준비 중인 공모전이 없어요. 위에서 찾거나, 공모전 상세 페이지의 「📋 준비 시작」을 눌러 보세요.</p>'}
${J && J.st.t ? '' : '<p class="pp-login">💡 로그인하면 준비 보드가 폰·PC 어디서나 이어지고, 마감 알림도 받아요. <button class="pp-in">로그인</button></p>'}`;
    const inp = top.querySelector('input'), res = top.querySelector('.pp-res');
    inp.oninput = () => {
      const q = inp.value.trim().toLowerCase(); if (!q) { res.innerHTML = ''; return; }
      const hit = C.filter(c => left(c.end) >= 0 && (c.title + ' ' + (c.org || '') + ' ' + (c.tags || []).join(' ') + ' ' + (c.effort || '')).toLowerCase().includes(q))
        .sort((a, b) => left(a.end) - left(b.end)).slice(0, 8);
      res.innerHTML = hit.length ? hit.map(c => `<li><button data-id="${esc(c.id)}"><span>${genre(genreOf(c)).icon}</span><b>${esc(c.title)}</b><em>${dlab(left(c.end))}</em></button></li>`).join('') : '<li class="pp-none">찾는 공모전이 없어요. 다른 단어로 찾아보세요.</li>';
      res.querySelectorAll('button').forEach(b => b.onclick = () => startBoard(C.find(c => c.id === b.dataset.id)));
    };
    const li = top.querySelector('.pp-in'); if (li) li.onclick = () => J.authModal(() => location.reload());
  }
  function ics(b) {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';
    const ev = plan(b).map(s => ['BEGIN:VEVENT', `UID:${b.url.replace(/\W/g, '')}-${s.i}@sungprofile.cloud`, 'DTSTAMP:' + stamp, 'DTSTART;VALUE=DATE:' + s.d.replace(/-/g, ''),
      `SUMMARY:[${b.title.slice(0, 30)}] ${s.name}`, `DESCRIPTION:${(s.desc || '').replace(/[,;]/g, ' ')} https://sungprofile.cloud/prep/`, 'END:VEVENT'].join('\r\n')).join('\r\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//jupjup//prep//KO\r\n' + ev + '\r\nEND:VCALENDAR'], { type: 'text/calendar' }));
    a.download = '준비일정.ics'; a.click(); ga('prep_ics');
  }
  function board(id) {
    const b = S[id]; if (!b) { home(); return; }
    const gg = genre(b.g), l = left(b.end), pl = plan(b), p = prog(b), td = ymd(today());
    const steps = pl.map(s => `<li class="${(b.steps || [])[s.i] ? 'ok' : s.d < td ? 'late' : s.d === td ? 'now' : ''}"><label><input type="checkbox" data-k="steps" data-i="${s.i}" ${(b.steps || [])[s.i] ? 'checked' : ''}><span class="pp-d">${s.d === td ? '오늘' : md(s.d)}</span><span><b>${esc(s.name)}</b>${s.desc ? `<small>${esc(s.desc)}</small>` : ''}</span></label></li>`).join('');
    const checks = checksOf(b).map((c, i) => `<li><label><input type="checkbox" data-k="checks" data-i="${i}" ${(b.checks || [])[i] ? 'checked' : ''}><span>${esc(c)}</span></label></li>`).join('');
    top.innerHTML = `<section class="pp-board"><p class="pp-back"><a href="#">← 내 준비 보드</a></p>
<header><span class="pp-ic big">${gg.icon}</span><div><small>${esc(gg.name)} 준비</small><h2>${esc(b.title)}</h2><p><em class="${l <= 3 && l >= 0 ? 'hot' : ''}">${dlab(l)}</em> ${b.end ? md(b.end) + ' 마감' : ''} · 진행 <b class="pp-pc">${p}%</b></p><i class="pp-bar"><i style="width:${p}%"></i></i></div></header>
<div class="pp-acts"><a href="${esc(b.url)}">📄 공고 보기</a><button class="pp-ics">📅 캘린더에 넣기</button><button class="pp-done${b.done ? ' on' : ''}">${b.done ? '✅ 냈어요' : '✅ 다 냈어요'}</button><a href="/community/">🚩 같이 할 사람</a></div>
<h3>🗓️ 마감까지 준비 일정</h3>${l >= 0 && l < maxOff(gg) ? '<p class="pp-note">마감이 가까워서 일정을 촘촘하게 줄였어요.</p>' : ''}
<ol class="pp-steps">${steps}</ol>
<h3>✔️ 내기 전 체크리스트</h3><ul class="pp-checks">${checks}</ul>
<h3>📝 메모 <small>아이디어·후보·링크 무엇이든</small></h3><textarea class="pp-memo" rows="6" placeholder="예) 후보: 1) … 2) …  /  담당자 메일: …">${esc(b.memo || '')}</textarea><p class="pp-saved" hidden>저장했어요</p>
<h3>🍯 ${esc(gg.name)} 꿀팁</h3><ul class="pp-tips">${gg.tips.slice(0, 3).map(t => `<li>${esc(t)}</li>`).join('')}</ul><p class="pp-more"><a href="#tips" data-g="${esc(gg.g)}">꿀팁 더 보기·공유하기 →</a>${b.g === 'slogan' ? ' · <a href="/lab/#diag">🏆 내 문구 진단 받기</a>' : ''}</p>
<p class="pp-del"><button>이 보드 지우기</button></p></section>`;
    top.querySelectorAll('input[type=checkbox]').forEach(x => x.onchange = () => {
      const k = x.dataset.k; b[k] = b[k] || []; b[k][+x.dataset.i] = x.checked; save(id);
      const np = prog(b); top.querySelector('.pp-pc').textContent = np + '%'; top.querySelector('header .pp-bar i').style.width = np + '%';
      x.closest('li').classList.toggle('ok', x.checked); if (np === 100) ga('prep_complete');
    });
    const memo = top.querySelector('.pp-memo'), sv = top.querySelector('.pp-saved'); let mt;
    memo.oninput = () => { clearTimeout(mt); mt = setTimeout(() => { b.memo = memo.value; save(id); sv.hidden = false; setTimeout(() => { sv.hidden = true; }, 1200); }, 500); };
    top.querySelector('.pp-ics').onclick = () => ics(b);
    top.querySelector('.pp-done').onclick = () => {
      b.done = !b.done; save(id); ga('prep_done', { on: b.done });
      if (J && J.st.t) J.api('/api/items', { method: 'POST', body: { items: [{ id, title: b.title, end: b.end, state: b.done ? 'applied' : '' }] } }).catch(() => {});
      board(id);
    };
    top.querySelector('.pp-del button').onclick = e => { if (e.target.dataset.sure) { delete S[id]; save(id); location.hash = ''; } else { e.target.dataset.sure = 1; e.target.textContent = '정말 지울까요? 한 번 더 누르세요'; } };
    top.querySelector('.pp-more a').onclick = ev => { ev.preventDefault(); tipsTab(ev.target.dataset.g); document.getElementById('tips').scrollIntoView({ behavior: 'smooth' }); };
    window.scrollTo(0, Math.max(0, top.getBoundingClientRect().top + window.scrollY - 70));
  }
  function route() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (/^c:/.test(h)) {
      if (!S[h]) { const c = C.find(x => 'c:' + x.id === h); if (c) return startBoard(c); }
      return board(h);
    }
    home();
  }
  // ---- 분량 계산기 ----
  function counter() {
    const el = document.getElementById('pp-count'); if (!el) return;
    el.innerHTML = '<textarea rows="5" placeholder="여기에 글을 붙여 넣으면 바로 세어 줘요"></textarea><div class="pp-cnt"></div>';
    const ta = el.querySelector('textarea'), out = el.querySelector('.pp-cnt');
    const run = () => {
      const v = ta.value.replace(/\r/g, ''), a = v.length, b = v.replace(/\s/g, '').length, by = new TextEncoder().encode(v).length;
      const won = v ? v.split('\n').reduce((s, ln) => s + Math.max(1, Math.ceil(ln.length / 20)), 0) : 0;  // 200자 원고지: 한 줄 20칸, 줄바꿈은 새 줄
      out.innerHTML = [['공백 포함', a.toLocaleString() + '자'], ['공백 제외', b.toLocaleString() + '자'], ['200자 원고지', Math.ceil(won / 10) + '매'], ['A4 (10pt)', (a / 1700).toFixed(1) + '쪽'], ['바이트', by.toLocaleString()]]
        .map(([k, x]) => `<div><small>${k}</small><b>${x}</b></div>`).join('');
    };
    ta.oninput = run; run();
  }
  // ---- 꿀팁 ----
  let curG = 'all';
  async function tipsTab(g) {
    curG = g; const box = document.getElementById('tips'); if (!box) return;
    box.querySelectorAll('.tp-chips button').forEach(b => b.classList.toggle('on', b.dataset.g === g));
    const gg = genre(g), list = box.querySelector('.tp-list');
    const seed = gg.tips.map(t => `<li class="tp-ruri"><span class="tp-who">🎀 루리</span><p>${esc(t)}</p></li>`).join('');
    list.innerHTML = seed;
    const r = J ? await J.api('/api/tips?g=' + g).catch(() => ({ tips: [] })) : { tips: [] };
    if (curG !== g) return;
    list.innerHTML = r.tips.map(t => `<li><span class="tp-who">👤 ${esc(t.nick || '회원')}${J.ago ? ' · ' + esc(J.ago(t.created)) : ''}</span><p>${esc(t.body)}</p><button class="tp-like${t.liked ? ' on' : ''}" data-id="${t.id}">👍 도움돼요 <b>${t.likes}</b></button></li>`).join('') + seed;
    list.querySelectorAll('.tp-like').forEach(b => b.onclick = async () => {
      if (!J.st.t) return J.authModal(() => tipsTab(curG));
      const x = await J.api('/api/tips/' + b.dataset.id + '/like', { method: 'POST' }).catch(() => null);
      if (x) { b.classList.toggle('on', x.liked); b.querySelector('b').textContent = x.likes; }
    });
    const sel = box.querySelector('.tp-form select'); if (sel) sel.value = g;
  }
  function tips() {
    const box = document.getElementById('tips'); if (!box) return;
    box.querySelector('.tp-chips').innerHTML = G.map(g => `<button data-g="${g.g}">${g.icon} ${esc(g.name)}</button>`).join('');
    box.querySelectorAll('.tp-chips button').forEach(b => b.onclick = () => tipsTab(b.dataset.g));
    const f = box.querySelector('.tp-form');
    f.innerHTML = `<h3>✍️ 내 꿀팁 공유하기</h3><select aria-label="장르">${G.map(g => `<option value="${g.g}">${g.icon} ${esc(g.name)}</option>`).join('')}</select><textarea rows="3" maxlength="1000" placeholder="직접 해 보고 알게 된 것, 떨어져 보고 깨달은 것 무엇이든요. (예: ○○시 공모전은 접수 확인 메일이 안 와서 전화로 확인했어요)"></textarea><button class="tp-send">공유하기</button><p class="tp-msg" hidden></p>`;
    f.querySelector('.tp-send').onclick = async () => {
      if (!(J && J.st.t)) return J && J.authModal(() => location.reload());
      const msg = f.querySelector('.tp-msg'), ta = f.querySelector('textarea'), g = f.querySelector('select').value;
      try { await J.api('/api/tips', { method: 'POST', body: { g, body: ta.value } }); ta.value = ''; msg.textContent = '공유했어요! 고마워요 🙌'; msg.hidden = false; ga('tip_share', { g }); tipsTab(g); }
      catch (e) { msg.textContent = e.message; msg.hidden = false; }
    };
    tipsTab('all');
  }
  async function init() {
    for (let i = 0; i < 40 && !window.JUP; i++) await new Promise(r => setTimeout(r, 100));
    J = window.JUP || null; load();
    const [d, c] = await Promise.all([fetch('/assets/prep/data.json?v=1').then(r => r.json()), fetch('/data.json').then(r => r.json()).catch(() => ({ items: [] }))]);
    G = d.genres; C = c.items || [];
    route(); counter(); tips();
    await syncServer(); route();
    window.addEventListener('hashchange', () => { if (location.hash !== '#tips') route(); });
  }
  init();
})();
