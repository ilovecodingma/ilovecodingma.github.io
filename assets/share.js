// 공유 버튼 줄 (2026-10-19 SEO·홍보 지침 Phase 5): 모바일 공유창·링크 복사·X·페이스북. 공유 링크엔 utm_source=share&utm_medium=<채널>
// 카카오톡 전용 버튼은 카카오 개발자 앱 키(JS 키)가 생기면 Kakao SDK로 붙인다 — 그 전엔 모바일 공유창에서 카카오톡 선택
(function () {
  document.querySelectorAll('.shr').forEach(bar => {
    const t = bar.dataset.t || document.title, u = location.origin + location.pathname;
    const link = m => u + '?utm_source=share&utm_medium=' + m;
    const ga = (m) => { try { window.gtag && gtag('event', 'share', { method: m, content_type: location.pathname.split('/')[1] || 'page' }); } catch (e) {} };
    const nat = bar.querySelector('[data-s=native]');
    if (!navigator.share && nat) nat.hidden = true;
    bar.addEventListener('click', e => {
      const b = e.target.closest('[data-s]'); if (!b) return;
      const s = b.dataset.s; ga(s);
      if (s === 'native') navigator.share({ title: t, text: bar.dataset.x || t, url: link('native') }).catch(() => {});
      if (s === 'copy') (navigator.clipboard ? navigator.clipboard.writeText(link('copy')) : Promise.reject()).then(() => { b.textContent = '✅ 복사했어요'; }).catch(() => prompt('복사해서 쓰세요', link('copy')));
      if (s === 'x') open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(bar.dataset.x || t) + '&url=' + encodeURIComponent(link('x')), '_blank', 'noopener');
      if (s === 'fb') open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(link('facebook')), '_blank', 'noopener');
    });
  });
})();
