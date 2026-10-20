// 전세 vs 월세 비교 계산기 (2026-10-20) — 브라우저에서만 계산하고 아무것도 저장·전송하지 않아요.
(function () {
  var R = document.getElementById('jw'); if (!R) return;
  var $ = function (s) { return R.querySelector(s); };
  var n = function (s) { var v = parseFloat(($(s).value || '').replace(/,/g, '')); return isFinite(v) ? v : null; };
  var f = function (v) { return Math.round(v).toLocaleString('ko-KR'); };
  function calc() {
    var A = n('[name=a]'), B = n('[name=b]'), M = n('[name=m]'), r = n('[name=r]'), b = n('[name=base]'), tr = +$('[name=tx]').value;
    var out = $('.jw-out');
    if (A === null || M === null || r === null) { out.innerHTML = '<p class="kwn">전세 보증금, 월세, 이자율을 넣으면 바로 계산해요.</p>'; return; }
    B = B || 0;
    var jy = A * r / 100, wy = M * 12 + B * r / 100, h = '';
    h += '<p>🏠 <b>전세</b> 연 비용 <b>' + f(jy) + '만원</b> <small>(보증금 ' + f(A) + '만원 × ' + r + '%)</small></p>';
    h += '<p>🏢 <b>월세</b> 연 비용 <b>' + f(wy) + '만원</b> <small>(월세 ' + f(M * 12) + '만원 + 보증금 ' + f(B) + '만원 × ' + r + '%)</small></p>';
    var credit = 0;
    if (tr > 0) { credit = Math.min(M * 12, 1000) * tr / 100; h += '<p>🧾 월세 세액공제 예상 <b>' + f(credit) + '만원</b> <small>(조건을 모두 채웠다고 가정: 월세 연 ' + f(Math.min(M * 12, 1000)) + '만원 × ' + tr + '%)</small></p>'; }
    var net = wy - credit, d = net - jy;
    h += '<p class="jw-r">' + (d > 0 ? '👉 같은 기준으로 보면 월세가 전세보다 연 <b>' + f(d) + '만원</b> 더 들어요' : d < 0 ? '👉 같은 기준으로 보면 월세가 전세보다 연 <b>' + f(-d) + '만원</b> 덜 들어요' : '👉 두 쪽 연 비용이 같아요') + (credit ? ' (세액공제 반영)' : '') + '.</p>';
    if (A > B) {
      var cv = M * 12 / (A - B) * 100;
      h += '<p>🔁 월세로 환산한 전환율 <b>' + cv.toFixed(2) + '%</b> <small>(월세×12 ÷ (전세 보증금 − 월세 보증금))</small></p>';
      if (b !== null) { var cap = Math.min(10, b + 2); h += '<p>⚖️ 법정 전환율 상한 <b>' + cap.toFixed(2) + '%</b> (연 10%와 기준금리 ' + b + '% + 2%p 중 낮은 쪽) → ' + (cv <= cap + 1e-9 ? '이 월세는 상한 이하예요' : '이 월세 환산율은 상한을 넘어요. 계약 시점 기준·적용 대상 주택인지 확인하세요') + '.</p>'; }
    }
    out.innerHTML = h;
  }
  R.addEventListener('input', calc); calc();
})();
