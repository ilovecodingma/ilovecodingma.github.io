// 루리 탐정의 이슈 감별 (/news/) — 이슈 순위 피드 + 기사 채점(팩트체크 신호) + 기사 관련 줍줍 (2026-10-18)
(function () {
  const ROOT = document.getElementById('news'); if (!ROOT) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };
  const G = { ok: ['✅', '믿을 만함', 'wave'], warn: ['🟡', '확인 필요', 'think'], bad: ['🔴', '의심', 'surprise'], opinion: ['🗣️', '의견 글', 'think'] };
  const SAY = {
    ok: ['여러 언론사가 같은 내용을 확인했어요. 믿고 봐도 좋아요!', '출처도 분명하고 숫자도 맞아요. 합격!'],
    warn: ['큰 틀은 맞지만, 세부 내용은 기사마다 조금씩 달라요.', '아직 확인이 덜 된 부분이 있어요. 한 번 더 보세요!'],
    bad: ['잠깐! 제목이랑 본문이 안 맞거나 출처가 약해요.', '숫자가 엇갈려요. 공식 발표를 기다려 봐요!']
  };
  const CATS = ['정치', '전체', '경제', '사회', '국제', 'IT·과학', '스포츠', '연예·문화'];
  let D = null, cat = '정치', only = '';
  const ago = ts => { const m = Math.max(1, Math.round((Date.now() / 1000 - ts) / 60)); return m < 60 ? m + '분 전' : m < 1440 ? Math.round(m / 60) + '시간 전' : Math.round(m / 1440) + '일 전'; };
  const badge = (s, g) => g && G[g] ? `<span class="nw-b ${g}">${G[g][0]} ${s ?? ''}${s != null ? '점' : ''} <small>${G[g][1]}</small></span>` : '';
  const pick = (arr, k) => arr[Math.abs([...String(k)].reduce((a, c) => a * 31 + c.charCodeAt(0), 7)) % arr.length];
  const prs = list => list && list.length ? `<div class="nw-pr"><small>📌 이 이슈랑 관련 있는 줍줍</small>${list.map(p => `<a href="${esc(p.u)}" data-ga="news_promo"><em>${esc(p.k)}</em><b>${esc(p.t)}</b>${p.e ? `<span>~${esc(p.e.slice(5).replace('-', '/'))}</span>` : ''}</a>`).join('')}</div>` : '';
  const art = a => `<li class="nw-a ${a.g || ''}"><div class="nw-ah"><b>${esc(a.o)}</b>${badge(a.s, a.g)}<span class="nw-t">${esc(ago(a.ts))}</span></div>
<a class="nw-at" href="${esc(a.u)}" target="_blank" rel="noopener nofollow" data-ga="news_out">${esc(a.t)}</a><ul class="nw-why">${a.why.map(w => `<li>${esc(w)}</li>`).join('')}</ul></li>`;
  function issue(x, i, I) {
    const arts = x.a.map(id => I[id]).filter(Boolean), g = x.cf && x.cf.length ? 'bad' : x.g;
    const words = t => (t.match(/[가-힣A-Za-z0-9]{2,}/g) || []);
    const cnt = {}; arts.forEach(a => new Set(words(a.t)).forEach(w => { cnt[w] = (cnt[w] || 0) + 1; }));
    const hl = t => esc(t).replace(/[가-힣A-Za-z0-9]{2,}/g, w => cnt[w] === 1 && arts.length >= 3 ? `<mark>${w}</mark>` : w);
    const cmp = x.c === '정치' ? `<div class="nw-cmp"><small>📰 같은 사건, 언론사별 제목 <i>(이 언론사만 쓴 표현은 노란색)</i></small>${arts.map(a => `<p><b>${esc(a.o)}</b>${hl(a.t)}</p>`).join('')}</div>` : '';
    const line = x.claim ? '이건 발언(주장)을 전한 기사들이에요. 그런 말을 한 건 사실이지만, 말한 내용이 맞는지는 따로 따져 봐야 해요!' : x.cf && x.cf.length ? `언론사마다 숫자가 달라요(${x.cf.join(' / ')}). 공식 발표를 확인해 보세요!` : pick(SAY[g] || SAY.warn, x.t);
    return `<article class="nw-is ${g || ''}" id="is${x.n}"><div class="nw-rank">${i + 1}</div><div class="nw-ib">
<p class="nw-meta"><span class="nw-cat">${esc(x.c)}</span><span class="nw-hot">🔥 ${x.on}곳 보도</span><span class="nw-t">${esc(ago(x.ts))}</span></p>
<h2>${esc(x.t)}</h2>${badge(x.s, g)}${x.claim ? '<span class="nw-b claim">🗣️ 발언·주장</span>' : ''}
<div class="nw-say"><img src="/assets/ruri/o_det_${G[g] ? G[g][2] : 'think'}_s.webp" width="44" height="61" alt="루리 탐정"><p><b>루리 탐정</b>${esc(line)}</p></div>
${cmp}${prs(x.pr)}
<details class="nw-d"><summary>🔎 언론사별 기사 채점 ${arts.length}건 보기</summary><ul class="nw-al">${arts.map(art).join('')}</ul></details>
<button class="nw-sh" data-n="${x.n}">📤 공유</button></div></article>`;
  }
  const ent = I => { const L = (D.ent || []).map(i => I[i]).filter(Boolean); return L.length ? `<section class="nw-sus nw-ent"><h2>🎣 연예 낚시 감별 <small>점수 낮은 순</small></h2><p class="nw-note">「파격」「몸매」「근황」 같은 낚시 표현, 연예인 SNS 글·사진을 옮겨 쓴 기사를 골랐어요.</p><ul class="nw-al">${L.slice(0, 15).map(art).join('')}</ul></section>` : ''; };
  function paint() {
    const I = Object.fromEntries(D.items.map(a => [a.id, a]));
    const iss = D.issues.filter(x => cat === '전체' || x.c === cat).filter(x => !only || (only === 'bad' ? (x.g === 'bad' || (x.cf && x.cf.length)) : x.g === only));
    const inIss = new Set(D.issues.flatMap(x => x.a));
    const sus = D.items.filter(a => !inIss.has(a.id) && a.g === 'bad' && (cat === '전체' || a.c === cat)).slice(0, 15);
    ROOT.querySelector('.nw-feed').innerHTML = (iss.length ? iss.map((x, i) => issue(x, i, I)).join('') : '<p class="nw-empty">이 분야는 지금 여러 언론사가 함께 다룬 이슈가 없어요.</p>')
      + (cat === '연예·문화' || cat === '전체' ? ent(I) : '')
      + (sus.length && !only ? `<section class="nw-sus"><h2>🕵️ 루리 탐정 수첩: 확인이 필요한 기사</h2><ul class="nw-al">${sus.map(art).join('')}</ul></section>` : '');
    ROOT.querySelectorAll('.nw-sh').forEach(b => b.onclick = () => {
      const x = D.issues.find(y => y.n === +b.dataset.n), text = `「${x.t}」 ${x.on}곳 보도 · 루리 탐정 감별 ${x.s ?? ''}점`, path = '/news/#is' + x.n;
      ga('share', { content_type: 'news' });
      if (window.JCREW) return JCREW.share({ title: '루리 탐정의 이슈 감별', text, path });
      const url = location.origin + path;
      if (navigator.share) navigator.share({ title: '루리 탐정의 이슈 감별', text, url }).catch(() => {}); else navigator.clipboard && navigator.clipboard.writeText(text + ' ' + url).then(() => { b.textContent = '✅ 복사했어요'; });
    });
    ROOT.querySelectorAll('[data-ga]').forEach(a => a.addEventListener('click', () => ga(a.dataset.ga, { link_url: a.href })));
    ROOT.querySelectorAll('.nw-d').forEach(d => d.addEventListener('toggle', () => d.open && ga('news_open', {})));
  }
  function frame() {
    const n = D.issues.length, ok = D.items.filter(a => a.g === 'ok').length, bad = D.items.filter(a => a.g === 'bad').length;
    ROOT.innerHTML = `<div class="nw-hero"><img src="/assets/news/ruri_det.webp" width="448" height="576" alt="돋보기를 든 탐정 루리"><div><small>${esc(D.updated)} 기준 · 매시간 갱신</small>
<b>지금 이슈 ${n}개 · 기사 ${D.items.length}건 감별</b><p>✅ 믿을 만함 ${ok} · 🔴 의심 ${bad}</p><p class="nw-hs">언론사 ${new Set(D.items.map(a => a.o)).size}곳 기사를 모아, 여러 곳이 같이 보도했는지·출처가 분명한지·제목 숫자와 인용이 본문과 맞는지·낚시 표현이 있는지로 채점해요.</p></div></div>
<div class="nw-tabs">${CATS.map(c => `<button data-c="${c}" class="${c === cat ? 'on' : ''}">${c}</button>`).join('')}</div>
<div class="nw-f"><button data-g="" class="on">전체</button><button data-g="ok">✅ 믿을 만함</button><button data-g="warn">🟡 확인 필요</button><button data-g="bad">🔴 의심·엇갈림</button></div>
<div class="nw-feed"></div>
<section class="nw-board"><h2>📊 언론사별 평균 점수 <small>최근 36시간 · 기사 10건 이상</small></h2><table><tr><th>언론사</th><th>기사</th><th>평균</th><th>의심 비율</th></tr>${D.outlets.map(o => `<tr><td>${esc(o.o)}</td><td>${o.n}</td><td><b>${o.avg}</b></td><td>${o.bad}%</td></tr>`).join('')}</table>
<p class="nw-note">점수는 기사 제목·본문에서 자동으로 뽑은 확인 신호예요. 기사 내용이 사실인지 아닌지를 최종 판정한 게 아니에요. 단독·현장 기사는 처음엔 한 곳만 보도해서 점수가 낮게 나올 수 있어요.</p></section>`;
    ROOT.querySelectorAll('.nw-tabs button').forEach(b => b.onclick = () => { cat = b.dataset.c; ROOT.querySelectorAll('.nw-tabs button').forEach(x => x.classList.toggle('on', x === b)); paint(); ga('news_tab', { cat }); });
    ROOT.querySelectorAll('.nw-f button').forEach(b => b.onclick = () => { only = b.dataset.g; ROOT.querySelectorAll('.nw-f button').forEach(x => x.classList.toggle('on', x === b)); paint(); });
    paint();
    if (location.hash) { const el = document.querySelector(location.hash); if (el) { el.querySelector('details') && (el.querySelector('details').open = true); el.scrollIntoView(); } }
  }
  fetch('/news/data.json', { cache: 'no-cache' }).then(r => r.json()).then(d => { D = d; frame(); }).catch(() => { ROOT.innerHTML = '<p class="nw-empty">뉴스를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요.</p>'; });
})();
