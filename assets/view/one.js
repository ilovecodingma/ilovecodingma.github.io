// 데이터 화면 (2026-10-19 페이지 줄이기): 얇은 자동 페이지를 따로 만들지 않고 JSON 을 불러와 한 화면에서 보여 준다.
//  /apply/?id=<공고 id>  ← 예전 /a/<id>/ (얇은 지원금 공고) · /kw/?k=<키워드>  ← 예전 /kw/<키워드>/ (지난 키워드)
(function () {
  const q = new URLSearchParams(location.search), esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const main = document.querySelector('main') || document.body;
  const box = h => { const el = document.createElement('section'); el.className = 'one-v'; el.innerHTML = h; const bc = main.querySelector('.bc'); (bc ? bc.nextSibling : main.firstChild) ? main.insertBefore(el, bc ? bc.nextSibling : main.firstChild) : main.appendChild(el); el.scrollIntoView({ block: 'start' }); };
  const kst = () => new Date(Date.now() + 324e5).toISOString().slice(0, 10);
  if (location.pathname === '/apply/' && q.get('id')) {
    fetch('/apply.json', { cache: 'no-cache' }).then(r => r.json()).then(L => {
      const a = L.find(x => String(x.id) === q.get('id'));
      if (!a) return box('<h2>찾는 공고가 목록에 없어요</h2><p>신청이 마감돼 목록에서 빠졌거나 주소가 바뀌었을 수 있어요. 아래에서 진행 중인 지원금·청약을 확인해 주세요.</p>');
      const end = a.always ? '상시' : a.end, left = a.always ? '' : Math.round((new Date(a.end) - new Date(kst())) / 864e5);
      const row = (k, v) => v ? `<tr><th>${k}</th><td>${esc(v)}</td></tr>` : '';
      box(`<p class="note">${esc(a.kind || '지원·신청')} · ${esc(a.org || '')}</p><h2>${esc(a.title)}</h2>
<p class="lead">${a.always ? '상시 신청' : left < 0 ? '신청 마감' : left === 0 ? '오늘 마감' : `마감까지 ${left}일`} · ${esc((a.start ? a.start + ' ~ ' : '') + end)}</p>
<table class="info">${row('대상', a.target)}${row('지원 내용', a.benefit)}${row('신청 방법', a.how)}${row('소득 조건', a.income)}${row('나이', a.age_min || a.age_max ? `만 ${a.age_min || ''}~${a.age_max || ''}세` : '')}${row('지역', a.region)}</table>
${a.url ? `<a class="btn" href="${esc(a.url)}" target="_blank" rel="noopener nofollow">공식 공고·신청처 열기 →</a>` : ''}<p class="note">자동 정리한 정보예요. 대상·기간은 공식 공고가 기준이에요.</p>`);
    }).catch(() => box('<p>공고 정보를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.</p>'));
  }
  // /apply/ 가볍게(2026-10-19): 처음엔 마감 가까운 60건만 그리고, 나머지는 버튼을 누르면 apply.json 에서
  const mb = document.getElementById('ap-more');
  if (mb) mb.onclick = () => { mb.disabled = true; mb.textContent = '불러오는 중…';
    fetch('/apply.json', { cache: 'no-cache' }).then(r => r.json()).then(L => {
      const ul = document.getElementById('ap-list'), have = new Set([...ul.querySelectorAll('a[href]')].map(a => a.getAttribute('href')));
      const today = kst(), rows = L.filter(a => !have.has(`/a/${a.id}/`) && !have.has(`/apply/?id=${a.id}`)).map(a => {
        const d = a.always ? '상시' : Math.round((new Date(a.end) - new Date(today)) / 864e5);
        return `<li><a class="card" href="/apply/?id=${encodeURIComponent(a.id)}"><span class="ic">${esc(a.icon || '📝')}</span><div class="cb"><div class="top"><h3 class="t">${esc(a.title)}</h3><span class="d">${a.always ? '상시' : d === 0 ? 'D-DAY' : 'D-' + d}</span></div><p class="o">${esc(a.org || '')} · ${esc(a.kind || '')}</p></div></a></li>`; });
      ul.insertAdjacentHTML('beforeend', rows.join('')); mb.parentElement.remove();
    }).catch(() => { mb.disabled = false; mb.textContent = '다시 시도'; }); };
  if (location.pathname === '/kw/' && q.get('k')) {
    fetch('/kw/db.json', { cache: 'no-cache' }).then(r => r.json()).then(D => {
      const k = q.get('k'), v = D[k] || Object.values(D).find(x => x.slug === k || x.k === k);
      if (!v) return box(`<h2>「${esc(k)}」 키워드 기록이 없어요</h2><p>오래된 키워드는 정리돼 사라질 수 있어요. 아래 오늘의 인기 키워드를 확인해 주세요.</p>`);
      box(`<p class="note">지난 인기 키워드 · ${esc((v.days || []).slice(-3).join(', '))}${v.traffic ? ' · 검색량 ' + esc(v.traffic) : ''}</p><h2>🔎 ${esc(v.k)}</h2>
${(v.news || []).length ? `<h3>그때 나온 기사</h3><ul class="kw-l">${v.news.slice(0, 6).map(n => `<li><a href="${esc(n.u)}" target="_blank" rel="noopener nofollow"><em>${esc(n.o)}</em>${esc(n.t)}</a></li>`).join('')}</ul>` : '<p class="note">기록된 기사가 없어요.</p>'}
<p class="note">기사 제목과 언론사는 각 보도 그대로예요. 루리의 줍줍이 사실을 판정한 게 아니에요.</p>`);
    }).catch(() => box('<p>키워드 기록을 불러오지 못했어요.</p>'));
  }
})();
