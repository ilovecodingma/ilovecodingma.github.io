// 루리의 줍줍 「내 공간」(/me/) — 가입 혜택을 한곳에: 찜·응모 기록·마감 알림·자격 프로필·청약 가점·문구 진단 기록 (2026-10-17)
// 공모전·청약·지원금·경품 공통 (item id: c:<공모전> / a:<청약> / e:<경품>)
(function () {
  const M = document.getElementById('me'), J = window.JUP; if (!M || !J) return;
  const esc = J.esc, today = (() => { const n = new Date(); return Math.round(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) / 864e5); })();
  const left = e => { if (!e) return null; const p = e.split('-'); return Math.round(Date.UTC(+p[0], p[1] - 1, +p[2]) / 864e5) - today; };
  const link = id => id.startsWith('c:') ? `/c/${id.slice(2)}/` : id.startsWith('a:') ? `/a/${id.slice(2)}/` : '#';
  const gjHTML = () => `<section class="me-sec" id="gajum"><h2>🏠 청약 가점 계산기 <small>84점 만점</small></h2><div class="me-gj">
<label>무주택 기간 <select data-g="h">${['1년 미만', ...Array.from({ length: 14 }, (_, i) => `${i + 1}년 이상`), '15년 이상'].map((v, i) => `<option value="${i}">${v}</option>`).join('')}</select></label>
<label>부양가족 수 <select data-g="f">${['0명', '1명', '2명', '3명', '4명', '5명', '6명 이상'].map((v, i) => `<option value="${i}">${v}</option>`).join('')}</select></label>
<label>청약통장 가입 기간 <select data-g="b">${['6개월 미만', '6개월~1년', ...Array.from({ length: 14 }, (_, i) => `${i + 1}년 이상`), '15년 이상'].map((v, i) => `<option value="${i}">${v}</option>`).join('')}</select></label></div>
<div class="me-gjr"><b class="me-gs">0점</b><span class="me-gd"></span></div><p class="note">무주택 2점×기간(최대 32) + 부양가족 5점×(인원+1)(최대 35) + 통장 기간(최대 17). 실제 판정은 청약홈 기준이에요.</p></section>`;
  function gajum(P, save) {
    const g = { h: +(P.gh || 0), f: +(P.gf || 0), b: +(P.gb || 0) };
    M.querySelectorAll('[data-g]').forEach(s => { s.value = g[s.dataset.g]; s.onchange = () => { g[s.dataset.g] = +s.value; calc(true); }; });
    function calc(store) {
      const H = g.h === 0 ? 2 : Math.min(32, 2 * (g.h + 1)), F = Math.min(35, 5 * (g.f + 1)), B = Math.min(17, g.b + 1), S = H + F + B;
      M.querySelector('.me-gs').textContent = S + '점';
      M.querySelector('.me-gd').textContent = `무주택 ${H} · 부양가족 ${F} · 통장 ${B} — ${S >= 60 ? '수도권 인기 단지도 노려볼 만해요' : S >= 45 ? '지방·비인기 단지 일반공급에 유리해요' : '추첨제·특별공급(신혼·청년)을 같이 보세요'}`;
      if (store && save) save({ gh: String(g.h), gf: String(g.f), gb: String(g.b), gajum: String(S) });
    }
    calc(false);
  }
  const TOPICS = [['recipe', '🍳', '오늘의 메뉴·새 레시피', '매일 아침'], ['apply', '💰', '지원금·청약', '새 공고와 마감 임박'], ['contest', '🏆', '공모전', '마감 3일 전'], ['issue', '📺', '루리 뉴스', '오늘의 브리핑'],
    ['game', '🎮', '무료 게임·스팀 할인', '새 무료 게임이 풀릴 때'], ['money', '📊', '전문가 말 vs 시세', '매일 아침'], ['event', '🎁', '경품·용돈', '오늘 마감']];
  const LSJ = 'jupjup_join_t', qt = (location.search.match(/[?&]t=([a-z]+)/) || [])[1];
  if (qt && TOPICS.some(t => t[0] === qt)) { try { localStorage.setItem(LSJ, qt); } catch {} }
  const STATE = { '': '찜', applied: '✅ 냈어요', won: '🏆 당첨', lost: '😢 아쉬움' };
  if (!J.st.t) {
    M.innerHTML = `<section class="me-hero"><img src="/assets/ruri/p/office_wave.webp" alt="" width="300" height="415"><div><h1>가입하면 루리가 챙겨 줘요</h1>
<ul class="me-ben"><li>🔔 <b>마감 알림 메일</b> — 찜한 공모전·청약 마감 3일 전과 당일</li><li>⭐ <b>찜·응모 기록</b> — 폰·PC 어디서든, 냈어요 → 당첨까지</li><li>🎯 <b>자격 맞춤 추천</b> — 나이·지역·신분에 안 맞는 건 자동으로 빼요</li>
<li>📬 <b>맞춤 소식 메일</b> — 고른 주제(오늘의 메뉴·지원금·공모전·무료 게임·뉴스)만 소식이 있는 날 한 통</li><li>🏠 <b>청약 가점 계산·저장</b></li><li>🏆 <b>수상작 전체 보기 + 내 문구 진단 기록</b></li><li>🎀 <b>루리 꾸미기 · 🚩 원정대</b></li></ul>
<button class="btn2 me-join">구글·카카오·이메일로 1초 가입</button></div></section>${gjHTML()}`;
    gajum({}, null);
    M.querySelector('.me-join').onclick = () => J.authModal(() => location.reload()); return;
  }
  M.innerHTML = '<p class="note">불러오는 중…</p>';
  Promise.all([J.api('/api/items').catch(() => ({ items: [] })), J.api('/api/me').catch(() => ({}))]).then(([it, me]) => {
    const items = it.items || [], P = me.prefs || {};
    const save = data => J.api('/api/prefs', { method: 'POST', body: { data: { ...P, ...data } } }).then(() => Object.assign(P, data));
    const topicsNow = () => String(P.topics || '').split(',').filter(Boolean);
    let pend = ''; try { pend = localStorage.getItem(LSJ) || ''; localStorage.removeItem(LSJ); } catch {}
    if (pend && TOPICS.some(t => t[0] === pend) && !topicsNow().includes(pend)) save({ topics: [...topicsNow(), pend].join(',').slice(0, 78), dg: '1' });
    const lab = (() => { try { return JSON.parse(localStorage.getItem('jupjup_lab') || '[]'); } catch { return []; } })();
    const soon = items.filter(x => x.fav && x.state === '' && (left(x.end) ?? 99) >= 0).sort((a, b) => (left(a.end) ?? 999) - (left(b.end) ?? 999));
    const rec = items.filter(x => x.state), won = rec.filter(x => x.state === 'won').length;
    M.innerHTML = `<section class="me-top"><img src="${J.poseSrc ? J.poseSrc(P.o && P.o !== 'smile' ? P.o.replace(/^o_/, '') : 'office', 'wave', false) || '/assets/ruri/p/office_wave.webp' : '/assets/ruri/p/office_wave.webp'}" alt="" width="300" height="415">
<div><h1>${esc(me.nick || J.st.n)}의 공간</h1><p class="me-stat"><span><b>${soon.length}</b>찜</span><span><b>${rec.length}</b>냈어요</span><span><b>${won}</b>당첨</span><span><b>${(me.visits || 0) + (me.invites || 0) * 3}</b>초대 점수</span></p></div></section>
<section class="me-sec"><h2>🔔 마감 알림</h2><label class="me-sw"><input type="checkbox" class="me-alert" ${P.alert === '1' ? 'checked' : ''}> 찜한 것 마감 3일 전·당일에 메일 받기</label>
<p class="note">받는 곳: ${esc(me.email || '가입 이메일')} · 매일 아침 8시 · 끄면 바로 멈춰요</p></section>
<section class="me-sec" id="topics"><h2>📬 받고 싶은 소식</h2><p class="note">고른 주제만 메일로 보내 드려요. 소식이 있는 날에만 한 통이고, 언제든 끌 수 있어요.</p>
<div class="me-tp">${TOPICS.map(([k, ic, l, d]) => `<label class="me-sw"><input type="checkbox" data-tp="${k}" ${(String(P.topics || '').split(',').includes(k) || pend === k) ? 'checked' : ''}> ${ic} <b>${l}</b> <small>${d}</small></label>`).join('')}</div>
<p class="note me-tpn">받는 곳: ${esc(me.email || '가입 이메일')}</p></section>
<section class="me-sec me-ka" hidden><h2>💬 카카오톡으로 마감 알림 받기</h2><label class="me-sw"><input type="checkbox" class="me-kalert"> 찜한 것 마감 3일 전·1일 전에 카카오톡 「나와의 채팅」으로 받기</label>
<p class="note me-kanote">매일 아침 8시 30분 · 켤 때 카카오 「메시지 전송」 동의를 한 번 받아요 · 끄면 동의도 철회돼요</p></section>
<section class="me-sec"><h2>⭐ 찜 <small>마감 임박순</small></h2><ul class="me-list">${soon.map(x => row(x)).join('') || '<li class="note">아직 찜한 게 없어요. 공모전·청약 상세 페이지나 루리 추천에서 ⭐를 눌러 보세요.</li>'}</ul></section>
<section class="me-sec"><h2>📒 응모 기록</h2><ul class="me-list">${rec.map(x => row(x, true)).join('') || '<li class="note">상세 페이지에서 「✅ 냈어요」를 누르면 여기 쌓여요. 발표 나면 당첨/아쉬움을 골라 두세요.</li>'}</ul></section>
<section class="me-sec"><h2>🎯 자격 프로필 <small>추천에서 안 맞는 건 빼요</small></h2><div class="me-prof">
<label>나이대 <select data-k="age">${['선택 안 함', '10대', '20대', '30대', '40대', '50대 이상'].map(v => `<option${P.age === v ? ' selected' : ''}>${v}</option>`).join('')}</select></label>
<label>사는 곳 <select data-k="region">${['선택 안 함', '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'].map(v => `<option${P.region === v ? ' selected' : ''}>${v}</option>`).join('')}</select></label>
<label>신분 <select data-k="role">${['선택 안 함', '초중고 학생', '대학생', '직장인', '구직·프리랜서', '주부', '기타'].map(v => `<option${P.role === v ? ' selected' : ''}>${v}</option>`).join('')}</select></label>
<label>주택 <select data-k="house">${['선택 안 함', '무주택', '1주택', '다주택'].map(v => `<option${P.house === v ? ' selected' : ''}>${v}</option>`).join('')}</select></label></div><p class="note me-saved"></p></section>
${gjHTML()}
<section class="me-sec"><h2>🏆 내 문구 진단 기록</h2><ul class="me-list">${lab.map(h => `<li><q>${esc(h.q)}</q> <b>${h.score}점</b> <small>${esc(h.th || '')}</small></li>`).join('') || '<li class="note"><a href="/lab/#diag">수상 연구소</a>에서 문구를 진단하면 여기 남아요.</li>'}</ul></section>
<section class="me-sec me-links"><a href="/community/">🚩 원정대</a><a href="/community/#dress">🎀 루리 꾸미기</a><a href="/lab/">🏆 수상 연구소</a><a href="/">💬 루리 상담</a></section>`;
    function row(x, rec) {
      const l = left(x.end);
      return `<li data-id="${esc(x.id)}"><a href="${link(x.id)}">${esc(x.title || x.id)}</a><small>${l === null ? '' : l < 0 ? '마감' : l ? 'D-' + l : 'D-DAY'}</small>
<span class="me-st">${rec ? ['applied', 'won', 'lost'].map(s => `<button data-s="${s}" class="${x.state === s ? 'on' : ''}">${STATE[s]}</button>`).join('') : `<button data-s="applied">✅ 냈어요</button><button data-unfav>☆ 빼기</button>`}</span></li>`;
    }
    M.querySelectorAll('.me-list [data-s],.me-list [data-unfav]').forEach(b => b.onclick = async () => {
      const id = b.closest('li').dataset.id;
      await J.api('/api/items', { method: 'POST', body: b.dataset.s ? { id, state: b.dataset.s } : { id, fav: 0 } }); location.reload();
    });
    M.querySelectorAll('[data-tp]').forEach(c => c.onchange = () => {
      const on = [...M.querySelectorAll('[data-tp]:checked')].map(x => x.dataset.tp);
      save({ topics: on.join(',').slice(0, 78), dg: on.length ? '1' : '0' }).then(() => { M.querySelector('.me-tpn').textContent = on.length ? `✅ 저장했어요. ${on.length}개 주제를 ${me.email || '가입 이메일'}로 보내 드려요.` : '모두 껐어요. 소식 메일은 보내지 않아요.'; J.ga && J.ga('topics_save', { n: on.length }); });
    });
    M.querySelector('.me-alert').onchange = e => save({ alert: e.target.checked ? '1' : '0' }).then(() => J.ga && J.ga('alert_toggle', { on: e.target.checked }));
    const ka = M.querySelector('.me-ka'), kc = M.querySelector('.me-kalert'), kn = M.querySelector('.me-kanote');
    const kh = (location.hash.match(/kalert=(on|fail)/) || [])[1];
    J.api('/api/kakao/alert').then(r => {
      if (!r.ready) return; ka.hidden = false; kc.checked = !!r.on;
      if (kh) { kn.textContent = kh === 'on' && r.on ? '✅ 켜졌어요. 찜한 것 마감 3일 전·1일 전 아침 8시 30분에 카카오톡으로 보내 드려요.' : '⚠️ 연결하지 못했어요. 「메시지 전송」에 동의했는지 확인하고 다시 켜 주세요.'; history.replaceState(null, '', location.pathname); }
    }).catch(() => {});
    kc.onchange = () => {
      if (kc.checked) J.api('/api/kakao/alert/start', { method: 'POST', body: {} }).then(r => { location.href = r.url; }).catch(() => { kc.checked = false; });
      else J.api('/api/kakao/alert/off', { method: 'POST', body: {} }).then(() => { kn.textContent = '껐어요. 카카오 메시지 전송 동의도 철회했어요.'; J.ga && J.ga('kakao_alert_toggle', { on: false }); });
    };
    M.querySelectorAll('.me-prof select').forEach(s => s.onchange = () => save({ [s.dataset.k]: s.value === '선택 안 함' ? '' : s.value }).then(() => { M.querySelector('.me-saved').textContent = '저장했어요. 루리 추천에 바로 반영돼요.'; }));
    gajum(P, save);
  });
})();
