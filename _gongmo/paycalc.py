"""2026 급여·퇴직금·실업급여 계산식 (참고용). assets/money/tools.js 와 같은 식 — 고칠 땐 둘 다.
근거(2026-10-18 확인): 국민연금 9.5%(근로자 4.75%), 기준소득월액 41만~659만원(2026.7~2027.6, 국민연금공단)
건강보험 7.19%(근로자 3.595%), 장기요양 0.9448%(건강보험료 × 0.9448/7.19, 보건복지부·건보공단), 고용보험 근로자 0.9%
소득세 기본세율·근로소득공제·근로소득세액공제(소득세법), 퇴직소득 근속연수공제·환산급여공제(2023.1.1 이후 퇴직분)
구직급여 상한 68,100원(2026.1.1 이후 이직자, 고용노동부)·하한 최저임금 10,320원 × 80% × 소정근로시간"""
NPS, HI, LTC, EI = .0475, .03595, .9448 / 7.19, .009
NPS_LO, NPS_HI = 410000, 6590000
BR = [(14e6, .06, 0), (50e6, .15, 1.26e6), (88e6, .24, 5.76e6), (150e6, .35, 15.44e6), (300e6, .38, 19.94e6), (500e6, .40, 25.94e6), (1e9, .42, 35.94e6), (float('inf'), .45, 65.94e6)]


def basic_tax(x):
    for lim, r, d in BR:
        if x <= lim:
            return max(0, x * r - d)


def earn_ded(g):
    d = g * .7 if g <= 5e6 else 3.5e6 + (g - 5e6) * .4 if g <= 15e6 else 7.5e6 + (g - 15e6) * .15 if g <= 45e6 else 12e6 + (g - 45e6) * .05 if g <= 1e8 else 14.75e6 + (g - 1e8) * .02
    return min(d, 2e7)


def earn_credit(tax, g):
    c = tax * .55 if tax <= 1.3e6 else 715000 + (tax - 1.3e6) * .3
    lim = 740000 if g <= 33e6 else max(660000, 740000 - (g - 33e6) * .008) if g <= 70e6 else max(500000, 660000 - (g - 70e6) / 2) if g <= 120e6 else max(200000, 500000 - (g - 120e6) / 2)
    return min(c, lim)


def salary(annual, nontax=200000, fam=1):
    """연봉(세전) → 월 공제와 실수령액. 소득세는 연말정산식으로 1년치를 계산해 12로 나눈 대략값."""
    m = annual / 12
    t = max(0, m - nontax)
    base = min(max(t, NPS_LO), NPS_HI) // 1000 * 1000
    p = base * NPS // 10 * 10
    h = t * HI // 10 * 10
    l = h * LTC // 10 * 10
    e = t * EI // 10 * 10
    g = t * 12
    taxable = max(0, g - earn_ded(g) - 1.5e6 * fam - (p + h + l + e) * 12)
    tx = basic_tax(taxable)
    tx = max(0, tx - earn_credit(tx, g) - 130000)  # 표준세액공제 13만원 (간이세액표 수준에 맞춤)
    it = tx / 12 // 10 * 10
    lt = it * .1 // 10 * 10
    ded = p + h + l + e + it + lt
    return {'m': m, 'p': p, 'h': h, 'l': l, 'e': e, 'it': it, 'lt': lt, 'ded': ded, 'net': m - ded}


def severance_tax(amt, years):
    """퇴직소득세(지방세 포함). years = 근속연수(1년 미만 끝수는 1년으로 올림)"""
    n = max(1, years)
    ys = n * 1e6 if n <= 5 else 5e6 + (n - 5) * 2e6 if n <= 10 else 15e6 + (n - 10) * 2.5e6 if n <= 20 else 40e6 + (n - 20) * 3e6
    conv = max(0, amt - ys) * 12 / n
    cd = conv if conv <= 8e6 else 8e6 + (conv - 8e6) * .6 if conv <= 7e7 else 45.2e6 + (conv - 7e7) * .55 if conv <= 1e8 else 61.7e6 + (conv - 1e8) * .45 if conv <= 3e8 else 151.7e6 + (conv - 3e8) * .35
    t = basic_tax(max(0, conv - cd)) / 12 * n // 10 * 10
    return t + t * .1 // 10 * 10
