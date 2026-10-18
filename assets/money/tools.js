// 머니 간단 계산기 (2026-10-18 핫이슈 도구) — 참고용, 실제 금액은 기관 확인. 투자 수익 계산은 넣지 않음.
// 숫자 근거: /money/policy/ (금융위·기재부·국세청 공식 자료, 기준일 2026-10-18)
(function () {
  const R = document.getElementById('mtool'); if (!R) return;
  const won = v => (Math.round(v)).toLocaleString() + '원';
  const num = s => +String(s || '').replace(/[^\d.]/g, '') || 0;
  // ---- 급여 계산식 (paycalc.py 와 같음) ----
  const BR = [[14e6, .06, 0], [50e6, .15, 1.26e6], [88e6, .24, 5.76e6], [150e6, .35, 15.44e6], [300e6, .38, 19.94e6], [500e6, .40, 25.94e6], [1e9, .42, 35.94e6], [Infinity, .45, 65.94e6]];
  const BT = x => { for (const [l, r, d] of BR) if (x <= l) return Math.max(0, x * r - d); };
  const f10 = x => Math.floor(x / 10) * 10;
  const ED = g => Math.min(2e7, g <= 5e6 ? g * .7 : g <= 15e6 ? 3.5e6 + (g - 5e6) * .4 : g <= 45e6 ? 7.5e6 + (g - 15e6) * .15 : g <= 1e8 ? 12e6 + (g - 45e6) * .05 : 14.75e6 + (g - 1e8) * .02);
  const EC = (t, g) => Math.min(t <= 1.3e6 ? t * .55 : 715000 + (t - 1.3e6) * .3, g <= 33e6 ? 740000 : g <= 70e6 ? Math.max(660000, 740000 - (g - 33e6) * .008) : g <= 120e6 ? Math.max(500000, 660000 - (g - 70e6) / 2) : Math.max(200000, 500000 - (g - 120e6) / 2));
  const SAL = (a, nt, fam) => { const m = a / 12, t = Math.max(0, m - nt), base = Math.floor(Math.min(Math.max(t, 410000), 6590000) / 1000) * 1000;
    const p = f10(base * .0475), h = f10(t * .03595), l = f10(h * .9448 / 7.19), e = f10(t * .009), g = t * 12;
    let tx = BT(Math.max(0, g - ED(g) - 1.5e6 * fam - (p + h + l + e) * 12)); tx = Math.max(0, tx - EC(tx, g) - 130000);
    const it = f10(tx / 12), lt = f10(it * .1), ded = p + h + l + e + it + lt; return { m, p, h, l, e, it, lt, ded, net: m - ded }; };
  const SEVTAX = (amt, n) => { n = Math.max(1, n); const ys = n <= 5 ? n * 1e6 : n <= 10 ? 5e6 + (n - 5) * 2e6 : n <= 20 ? 15e6 + (n - 10) * 2.5e6 : 40e6 + (n - 20) * 3e6;
    const cv = Math.max(0, amt - ys) * 12 / n, cd = cv <= 8e6 ? cv : cv <= 7e7 ? 8e6 + (cv - 8e6) * .6 : cv <= 1e8 ? 45.2e6 + (cv - 7e7) * .55 : cv <= 3e8 ? 61.7e6 + (cv - 1e8) * .45 : 151.7e6 + (cv - 3e8) * .35;
    const t = f10(BT(Math.max(0, cv - cd)) / 12 * n); return t + f10(t * .1); };
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
    salary: {  // 2026 실수령액 — _gongmo/paycalc.py 와 같은 식 (국민연금 4.75%·기준소득월액 41만~659만, 건강 3.595%, 장기요양 건강×0.9448/7.19, 고용 0.9%)
      f: '<label>연봉(세전, 원)<input data-k="a" inputmode="numeric" placeholder="예) 40000000"></label><label>월 비과세(식대 등, 원)<input data-k="n" inputmode="numeric" value="200000"></label><label>부양가족 수(본인 포함)<select data-k="f"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select></label>',
      c: v => { const r = SAL(v.a, v.n, +v.f || 1);
        return `<p>월 실수령액 약 <b>${won(r.net)}</b> (연 ${won(r.net * 12)})</p><table class="mt-t"><tr><th>항목</th><th>월</th></tr><tr><td>세전 월급</td><td>${won(r.m)}</td></tr><tr><td>국민연금 4.75%</td><td>-${won(r.p)}</td></tr><tr><td>건강보험 3.595%</td><td>-${won(r.h)}</td></tr><tr><td>장기요양</td><td>-${won(r.l)}</td></tr><tr><td>고용보험 0.9%</td><td>-${won(r.e)}</td></tr><tr><td>소득세(대략)</td><td>-${won(r.it)}</td></tr><tr><td>지방소득세</td><td>-${won(r.lt)}</td></tr><tr class="on"><td>공제 합계</td><td>-${won(r.ded)}</td></tr></table>
<p class="mt-n">소득세는 연말정산 식으로 1년치를 계산해 12로 나눈 값이라 회사 간이세액표와 몇천~몇만 원 다를 수 있어요. 자녀세액공제·각종 소득공제는 빠져 있어요.</p>`;
      } },
    severance: {  // 퇴직금 = 1일 평균임금 × 30일 × 재직일수/365, 퇴직소득세(2023.1.1 이후 퇴직분 공제)
      f: '<label>입사일<input data-k="s" type="date"></label><label>퇴사일(마지막 근무 다음 날)<input data-k="e" type="date"></label><label>퇴사 전 3개월 임금 합계(세전, 원)<input data-k="w" inputmode="numeric" placeholder="예) 9000000"></label><label>지난 1년 상여금 합계(원)<input data-k="b" inputmode="numeric" placeholder="없으면 0"></label><label>지난 1년 연차수당(원)<input data-k="y" inputmode="numeric" placeholder="없으면 0"></label>',
      c: v => {
        const s = new Date(v.s), e = new Date(v.e); if (isNaN(s) || isNaN(e) || e <= s) return '<p>입사일과 퇴사일을 확인해 주세요.</p>';
        const days = Math.round((e - s) / 864e5), p3 = new Date(e); p3.setMonth(p3.getMonth() - 3); const d3 = Math.round((e - p3) / 864e5);
        const avg = (v.w + v.b * 3 / 12 + v.y * 3 / 12) / d3, amt = avg * 30 * days / 365, yrs = Math.ceil(days / 365), tax = SEVTAX(amt, yrs);
        if (days < 365) return `<p>재직 ${days}일 — 1년(365일) 미만이라 법정 퇴직금 대상이 아니에요.</p><p class="mt-n">주 15시간 이상, 1년 이상 일해야 받을 수 있어요. 알바도 같은 기준이에요.</p>`;
        return `<p>세전 퇴직금 약 <b>${won(amt)}</b> → 세후 약 <b>${won(amt - tax)}</b></p><table class="mt-t"><tr><th>항목</th><th>값</th></tr><tr><td>재직일수</td><td>${days.toLocaleString()}일</td></tr><tr><td>1일 평균임금</td><td>${won(avg)}</td></tr><tr><td>퇴직소득세+지방세</td><td>-${won(tax)}</td></tr></table>
<p class="mt-n">1일 평균임금이 통상임금보다 낮으면 통상임금으로 계산해요. IRP로 받으면 세금은 연금 수령 때까지 미뤄져요.</p>`;
      } },
    unemployment: {  // 구직급여: 평균임금 60%, 상한 68,100원(2026.1.1 이후 이직), 하한 최저임금 10,320원 × 80% × 소정근로시간
      f: '<label>퇴사 전 3개월 임금 합계(세전, 원)<input data-k="w" inputmode="numeric" placeholder="예) 9000000"></label><label>1일 소정근로시간<select data-k="h"><option value="8">8시간(주 40시간)</option><option value="7">7시간</option><option value="6">6시간</option><option value="5">5시간</option><option value="4">4시간</option></select></label><label>고용보험 가입기간<select data-k="y"><option value="0">1년 미만</option><option value="1">1년~3년 미만</option><option value="3">3년~5년 미만</option><option value="5">5년~10년 미만</option><option value="10">10년 이상</option></select></label><label>퇴사 당시 나이<select data-k="o"><option value="0">50세 미만</option><option value="1">50세 이상 또는 장애인</option></select></label>',
      c: v => {
        const avg = v.w / 91, lo = 10320 * .8 * (+v.h || 8), day = Math.min(68100, Math.max(lo, avg * .6));
        const T = { 0: [120, 120], 1: [150, 180], 3: [180, 210], 5: [210, 240], 10: [240, 270] }[v.y][+v.o ? 1 : 0];
        return `<p>하루 약 <b>${won(day)}</b> × <b>${T}일</b> = 총 약 <b>${won(day * T)}</b></p><p>한 달(30일) 기준 약 ${won(day * 30)}${day >= 68100 ? ' — 상한액이 적용됐어요' : day <= lo ? ' — 하한액이 적용됐어요' : ''}</p>
<p class="mt-n">3개월 일수를 91일로 잡은 대략 계산이에요. 비자발적 퇴사(권고사직·계약 만료 등)와 이직 전 18개월 중 피보험 180일 이상이 기본 조건이에요. 실제 금액은 고용24 모의계산으로 확인하세요.</p>`;
      } },
  }[T];
  if (!F) return;
  R.innerHTML = `<div class="mt-f">${F.f}<button class="mt-go">계산하기</button></div><div class="mt-o" hidden></div><p class="mt-n">참고용 계산이에요. 실제 금액은 금융기관·국세청 안내로 확인하세요.</p>`;
  R.querySelector('.mt-go').onclick = () => {
    const v = {}; R.querySelectorAll('[data-k]').forEach(e => { v[e.dataset.k] = e.tagName === 'SELECT' || e.type === 'date' ? e.value : num(e.value); });
    const o = R.querySelector('.mt-o'); o.hidden = false; o.innerHTML = F.c(v);
    try { window.gtag && gtag('event', 'tool_calc', { tool: T }); } catch {}
  };
})();
