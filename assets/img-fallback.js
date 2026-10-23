// 이미지 로딩 실패 시 깨진 아이콘 대신 대체 이미지 (2026-10-23 P0). 캡처 단계의 error 이벤트로 JS 가 나중에 그린 이미지도 처리한다.
document.addEventListener('error', function (e) {
  var t = e.target;
  if (!t || t.tagName !== 'IMG' || t.dataset.fb) return;
  t.dataset.fb = '1'; t.classList.add('img-fb'); t.removeAttribute('srcset'); t.src = '/assets/img-fallback.svg';
}, true);
