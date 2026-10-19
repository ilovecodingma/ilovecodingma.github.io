// 공유 버튼 줄 (2026-10-19 SEO·홍보 지침 Phase 5, 같은 날 카카오톡·네이버 블로그·밴드 추가)
// 공유 링크엔 ?src=u_share_<채널>(관리자 유입 「공유 버튼으로 받은 링크」) + utm. 모바일은 기기 공유창을 먼저 보여 줌.
// 카카오톡 버튼은 data-k(카카오 JS 키, _gongmo/config.json kakao_js_key)가 있을 때만 보임.
(function () {
  const bars = document.querySelectorAll('.shr'); if (!bars.length) return;
  const og = (document.querySelector('meta[property="og:image"]') || {}).content || location.origin + '/assets/ruri/og.jpg';
  const desc = (document.querySelector('meta[name="description"]') || {}).content || '';
  let kakao = null;
  const loadKakao = key => kakao || (kakao = new Promise((ok, no) => {
    if (window.Kakao) return ok(window.Kakao);
    const s = document.createElement('script'); s.src = 'https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js'; s.crossOrigin = 'anonymous';
    s.onload = () => { try { if (!Kakao.isInitialized()) Kakao.init(key); ok(Kakao); } catch (e) { no(e); } }; s.onerror = no; document.head.appendChild(s);
  }));
  bars.forEach(bar => {
    const t = bar.dataset.t || document.title, x = bar.dataset.x || t, key = bar.dataset.k || '';
    const u = location.origin + location.pathname;
    const link = m => u + '?src=u_share_' + m + '&utm_source=share&utm_medium=' + m;
    const ga = m => { try { window.gtag && gtag('event', 'share', { method: m, content_type: location.pathname.split('/')[1] || 'page' }); } catch (e) {} };
    const q = s => bar.querySelector('[data-s=' + s + ']');
    if (!navigator.share && q('native')) q('native').hidden = true;
    if (!key && q('kakao')) q('kakao').hidden = true;
    if (key) loadKakao(key).catch(() => { if (q('kakao')) q('kakao').hidden = true; });
    bar.addEventListener('click', e => {
      const b = e.target.closest('[data-s]'); if (!b) return;
      const s = b.dataset.s; ga(s);
      if (s === 'native') navigator.share({ title: t, text: x, url: link('native') }).catch(() => {});
      if (s === 'kakao') loadKakao(key).then(K => K.Share.sendDefault({ objectType: 'feed',
        content: { title: t.slice(0, 200), description: (x !== t ? x : desc).slice(0, 200), imageUrl: og, link: { mobileWebUrl: link('kakao'), webUrl: link('kakao') } },
        buttons: [{ title: bar.dataset.en ? 'Open' : '자세히 보기', link: { mobileWebUrl: link('kakao'), webUrl: link('kakao') } }] })).catch(() => {});
      if (s === 'copy') (navigator.clipboard ? navigator.clipboard.writeText(link('copy')) : Promise.reject()).then(() => { b.textContent = bar.dataset.en ? '✅ Copied' : '✅ 복사했어요'; }).catch(() => prompt(bar.dataset.en ? 'Copy this link' : '복사해서 쓰세요', link('copy')));
      if (s === 'nblog') open('https://blog.naver.com/openapi/share?url=' + encodeURIComponent(link('nblog')) + '&title=' + encodeURIComponent(t), '_blank', 'noopener');
      if (s === 'band') open('https://band.us/plugin/share?body=' + encodeURIComponent(x + '\n' + link('band')) + '&route=' + encodeURIComponent(location.host), '_blank', 'noopener');
      if (s === 'x') open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(x) + '&url=' + encodeURIComponent(link('x')), '_blank', 'noopener');
      if (s === 'fb') open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(link('fb')), '_blank', 'noopener');
    });
  });
})();
