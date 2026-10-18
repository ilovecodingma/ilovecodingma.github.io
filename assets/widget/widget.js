// /widget/ 배포 페이지: 옵션 → 미리보기·코드 (2026-10-18)
(function () {
  const $ = id => document.getElementById(id), S = 'https://sungprofile.cloud';
  const IMG = { contest: c => c === 'all' ? 'contest-week.png' : `contest-week-${c}.png`, apply: () => 'apply-week.png', hot: () => 'hot-today.png' };
  const LAND = { contest: '/contest/', apply: '/apply/', hot: '/hot/', dday: '/contest/' };
  const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let D = null;
  fetch('/w/data.json', { cache: 'no-cache' }).then(r => r.json()).then(d => { D = d; draw(); }).catch(() => {});
  function draw() {
    const k = $('wk').value, c = $('wc').value, n = $('wn').value, [w, h] = $('ws').value.split('x'), t = $('wt').value, id = $('wi').value;
    $('wcl').hidden = k !== 'contest'; $('wil').hidden = k !== 'dday';
    const q = k === 'dday' ? `?id=${encodeURIComponent(id)}${t === 'dark' ? '&t=dark' : ''}` : `?${k === 'contest' ? 'cat=' + c + '&' : ''}n=${n}${t === 'dark' ? '&t=dark' : ''}`;
    const src = `${S}/w/${k}/${q}`, hh = k === 'dday' ? Math.min(+h, 260) : h;
    const f = $('wf'); f.src = `/w/${k}/${q}`; f.width = w; f.height = hh; f.style.cssText = `width:${w}px;max-width:100%;height:${hh}px;border:0`;
    $('c2').value = `<iframe src="${src}" width="${w}" height="${hh}" style="border:0;max-width:100%" loading="lazy" title="루리의 줍줍 위젯"></iframe>`;
    const im = IMG[k], land = `${S}${LAND[k]}?src=w_img`;
    if (im) {
      const iu = `${S}/w/img/${im(c)}`;
      $('wimg').hidden = false; $('wimg').src = `/w/img/${im(c)}?t=${Date.now() / 36e5 | 0}`;
      $('c1').value = `<a href="${land}" target="_blank"><img src="${iu}" alt="루리의 줍줍 ${k === 'contest' ? '이번 주 마감 공모전' : k === 'apply' ? '지원금·청약 마감' : '오늘의 핫이슈'}" width="360"></a>`;
      $('cimg').dataset.u = iu; $('cimg').disabled = false;
    } else { $('wimg').hidden = true; $('c1').value = '(D-day 카운터는 iframe·텍스트만 있어요)'; $('cimg').disabled = true; }
    if (!D) return;
    const tag = `?src=w_${k}`;
    let rows = [];
    if (k === 'contest') rows = (D.contest[c] || []).slice(0, n).map(x => `<li><a href="${S}/c/${x.id}/${tag}">${esc(x.t)}</a> — ${x.e.slice(5).replace('-', '/')} 마감${x.p ? ' · ' + esc(x.p) : ''}</li>`);
    if (k === 'apply') rows = D.apply.slice(0, n).map(x => `<li><a href="${S}/a/${encodeURIComponent(x.id)}/${tag}">${esc(x.t)}</a> — ${x.e.slice(5).replace('-', '/')} 마감</li>`);
    if (k === 'hot') rows = D.hot.slice(0, 3).map(x => `<li><a href="${S}/hot/${encodeURIComponent(x.s)}/${tag}">${esc(x.t)}</a></li>`);
    if (k === 'dday') { const x = D.contest.all.find(x => x.id === id); if (x) { const dd = Math.round((new Date(x.e) - new Date(new Date(Date.now() + 9 * 36e5).toISOString().slice(0, 10))) / 864e5); rows = [`<li><a href="${S}/c/${x.id}/${tag}">${esc(x.t)}</a> — 마감까지 ${dd === 0 ? 'D-DAY' : 'D-' + dd}</li>`]; } }
    $('c3').value = `<ul>\n${rows.join('\n')}\n</ul>\n<p><a href="${S}/${tag}">루리의 줍줍</a>에서 매일 갱신</p>`;
  }
  ['wk', 'wc', 'wn', 'ws', 'wt', 'wi'].forEach(i => $(i).addEventListener('change', draw));
  const copy = (v, b) => { (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => { const o = b.textContent; b.textContent = '복사했어요 ✓'; setTimeout(() => b.textContent = o, 1500); }).catch(() => { prompt('복사해서 쓰세요', v); });
    try { window.gtag && gtag('event', 'widget_copy', { kind: $('wk').value }); } catch {} };
  document.querySelectorAll('.wg-c button[data-c]').forEach(b => b.onclick = () => copy($(b.dataset.c).value, b));
  $('cimg').onclick = e => copy(e.target.dataset.u || '', e.target);
  draw();
})();
