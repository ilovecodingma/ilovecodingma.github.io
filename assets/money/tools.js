// 머니 간단 계산기 (2026-10-18 핫이슈 도구) — 참고용, 실제 금액은 기관 확인. 투자 수익 계산은 넣지 않음.
// 숫자 근거: /money/policy/ (금융위·기재부·국세청 공식 자료, 기준일 2026-10-18)
(function () {
  const R = document.getElementById('mtool'); if (!R) return;
  const won = v => (Math.round(v)).toLocaleString() + '원';
  const num = s => +String(s || '').replace(/[^\d.]/g, '') || 0;
  const T = R.dataset.tool;
  const F = {
    dividend: {
      f: '<label>올해 받을 배당금(고배당 기업 배당, 원)<input data-k="a" inputmode="numeric" placeholder="예) 30000000"></label>',
      c: v => {  // 배당소득 분리과세(2026-01-01 지급분~): 2천만 이하 14%, 3억 이하 20%, 50억 이하 25%, 초과 30% — 구간별, 지방소득세 10% 별도
        const a = v.a, B = [[2e7, .14], [3e8, .20], [5e9, .25], [Infinity, .30]]; let t = 0, prev = 0;
        for (const [lim, r] of B) { if (a > prev) t += (Math.min(a, lim) - prev) * r; prev = lim; }
        const local = t * .1, base = a * .154;
        return `<p>분리과세를 고르면 세금 약 <b>${won(t + local)}</b> (국세 ${won(t)} + 지방소득세 ${won(local)})</p><p>비교: 일반 배당 원천징수 15.4%면 ${won(base)}</p>
<p class="mt-n">대상 기업 요건(배당성향 등)과 다른 금융소득에 따라 실제 세금은 달라요. 구간별 세율을 순서대로 적용한 대략 계산이에요.</p>`;
      } },
    stocktax: {
      f: '<label>매도 금액(원)<input data-k="a" inputmode="numeric" placeholder="예) 10000000"></label><label>시장<select data-k="m"><option value="kospi">코스피</option><option value="kosdaq">코스닥·K-OTC</option><option value="konex">코넥스</option></select></label>',
      c: v => {  // 2026-01-01부터: 코스피 거래세 0.05% + 농특세 0.15%, 코스닥 0.20%, 코넥스 0.10%
        const r = v.m === 'kospi' ? .002 : v.m === 'konex' ? .001 : .002;
        return `<p>팔 때 내는 세금 약 <b>${won(v.a * r)}</b> (${v.m === 'kospi' ? '증권거래세 0.05% + 농어촌특별세 0.15%' : v.m === 'konex' ? '0.10%' : '0.20%'})</p><p class="mt-n">증권사 수수료는 따로예요.</p>`;
      } },
    pension: {
      f: '<label>올해 연금저축 납입액(원)<input data-k="p" inputmode="numeric" placeholder="예) 6000000"></label><label>올해 IRP 납입액(원)<input data-k="i" inputmode="numeric" placeholder="예) 3000000"></label><label>총급여<select data-k="g"><option value="lo">5,500만원 이하</option><option value="hi">5,500만원 초과</option></select></label>',
      c: v => {  // 연금저축 600만 + IRP 합산 900만 한도, 공제율 16.5%(총급여 5,500만 이하) / 13.2%
        const base = Math.min(Math.min(v.p, 6e6) + v.i, 9e6), r = v.g === 'lo' ? .165 : .132;
        return `<p>세액공제 대상 <b>${won(base)}</b> × ${r * 100}% = 돌려받는 세금 약 <b>${won(base * r)}</b></p><p class="mt-n">ISA 만기 자금 이전분 추가 공제(최대 300만원)는 빼고 계산했어요.</p>`;
      } },
    loan: {
      f: '<label>대출 금액(원)<input data-k="a" inputmode="numeric" placeholder="예) 200000000"></label><label>연 금리(%)<input data-k="r" inputmode="decimal" placeholder="예) 4.2"></label><label>기간(개월)<input data-k="n" inputmode="numeric" placeholder="예) 360"></label><label>상환 방식<select data-k="m"><option value="eq">원리금균등</option><option value="pr">원금균등</option><option value="bul">만기일시</option></select></label>',
      c: v => {
        const calc = rate => { const i = rate / 100 / 12, n = Math.max(1, v.n);
          if (v.m === 'bul') return { first: v.a * i, total: v.a * i * n };
          if (v.m === 'pr') { const p = v.a / n; let t = 0; for (let k = 0; k < n; k++) t += (v.a - p * k) * i; return { first: p + v.a * i, total: t }; }
          const m = i ? v.a * i / (1 - Math.pow(1 + i, -n)) : v.a / n; return { first: m, total: m * n - v.a }; };
        const now = calc(v.r), up = calc(v.r + .25), dn = calc(Math.max(0, v.r - .25));
        return `<p>첫 달 내는 돈 <b>${won(now.first)}</b> · 총 이자 <b>${won(now.total)}</b></p>
<table class="mt-t"><tr><th>금리</th><th>첫 달</th><th>총 이자</th></tr><tr><td>${(v.r - .25).toFixed(2)}%</td><td>${won(dn.first)}</td><td>${won(dn.total)}</td></tr><tr class="on"><td>${v.r.toFixed(2)}%</td><td>${won(now.first)}</td><td>${won(now.total)}</td></tr><tr><td>${(v.r + .25).toFixed(2)}%</td><td>${won(up.first)}</td><td>${won(up.total)}</td></tr></table>`;
      } },
    fx: {
      f: '<label>바꿀 원화(원)<input data-k="a" inputmode="numeric" placeholder="예) 1000000"></label><label>매매기준율(원, 은행 앱에서 확인)<input data-k="r" inputmode="decimal" placeholder="예) 1380"></label><label>환전 수수료(%)<input data-k="f" inputmode="decimal" placeholder="예) 1.75"></label><label>환율 우대(%)<input data-k="u" inputmode="decimal" placeholder="예) 90"></label>',
      c: v => {
        const fee = v.f * (1 - v.u / 100) / 100, buy = v.r * (1 + fee), got = v.r ? v.a / buy : 0, noU = v.r ? v.a / (v.r * (1 + v.f / 100)) : 0;
        return `<p>적용 환율 약 <b>${buy.toFixed(2)}원</b> → 받는 외화 약 <b>${got.toFixed(2)}</b></p><p>우대 없이 바꾸면 ${noU.toFixed(2)} → 우대로 ${(got - noU).toFixed(2)} 더 받아요.</p>`;
      } },
  }[T];
  if (!F) return;
  R.innerHTML = `<div class="mt-f">${F.f}<button class="mt-go">계산하기</button></div><div class="mt-o" hidden></div><p class="mt-n">참고용 계산이에요. 실제 금액은 금융기관·국세청 안내로 확인하세요.</p>`;
  R.querySelector('.mt-go').onclick = () => {
    const v = {}; R.querySelectorAll('[data-k]').forEach(e => { v[e.dataset.k] = e.tagName === 'SELECT' ? e.value : num(e.value); });
    const o = R.querySelector('.mt-o'); o.hidden = false; o.innerHTML = F.c(v);
    try { window.gtag && gtag('event', 'tool_calc', { tool: T }); } catch {}
  };
})();
