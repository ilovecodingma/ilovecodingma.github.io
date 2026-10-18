# -*- coding: utf-8 -*-
"""핫이슈 랜딩 (/hot/<slug>/) — 트렌드(구글+실시간 검색어) × 언론 이슈에서 정보성 이슈를 골라 '한눈에 정리 + 나한테 뭐가 달라지나 + 도구 연결'을 만든다.
2026-10-18 사용자: "우리 사이트도 트렌드 분석에 따른 핫이슈에 맞춘 것들을 만들어"(홍보 세션 연구 ⑂ 기획).
원칙: 우리가 사실을 지어내지 않는다 — '무슨 일'은 여러 언론사 제목을 출처와 함께, 숫자·날짜도 제목에 나온 것만 출처 표시.
      '나한테 뭐가'·FAQ는 이슈 유형별로 미리 검증한 우리 페이지·계산기로 연결하는 틀만. 언론사 2곳 이상 + 자료 충분할 때만 생성.
      제외: 연예 사생활·사건사고·비방(kw.EXCL·news.ACC). 48시간 안 보이면 '지난 이슈'.
결과: root/hot/db.json. news.py → talk → analyst → kw 다음 매시."""
import os, re, json, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DBF = os.path.join(ROOT, 'hot', 'db.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
TYPES = [  # (유형, 정규식) 위에서부터 먼저 맞는 것
    ('housing', r'청약|분양|전세|월세|아파트|주택|임대|부동산|집값'),
    ('grant', r'지원금|적금|수당|바우처|장려금|지원 사업|환급|청년도약|청년미래|근로장려'),
    ('tax', r'세금|과세|세액|공제|세제|세법|소득세|양도세|거래세|배당소득|연말정산|종부세|재산세'),
    ('rate', r'금리|기준금리|대출|환율|원·달러|원달러|엔화|달러'),
    ('market', r'코스피|코스닥|주가|증시|비트코인|이더리움|가상자산|반도체|공모주|상장'),
    ('health', r'진료|의료|병원|의원|약국|처방|건강보험|비대면|백신|검진|실손'),
    ('labor', r'임금|노동|근로|최저임금|퇴직|고용|실업급여|육아휴직|출산휴가|주4일|노동부'),
    ('event', r'축제|박람회|엑스포|공연|콘서트|태풍|폭우|폭염|한파|날씨|단풍|불꽃|마라톤|개최'),
]
TOOL = {  # 유형 → (나한테 뭐가 달라지나 안내, 연결 [(이름, 주소)], FAQ [(질문, 답)])
    'housing': ('청약·분양·전세 이슈예요. 내 청약 가점과 노려볼 공급 유형, 지금 접수 중인 공고부터 확인해 보세요.',
                [('🏠 청약 추천(가점·공급 유형·공고)', '/apply/recommend/'), ('📋 지원금·청약 전체', '/apply/')],
                [('나도 신청할 수 있나요?', '청약 자격(무주택·소득·자산·거주 기간)은 단지마다 달라요. 루리의 청약 추천에서 내 상황을 넣어 보고, 최종 자격은 공고문과 청약홈에서 확인하세요.'),
                 ('청약 가점은 어떻게 계산하나요?', '무주택 기간(32점)·부양가족(35점)·통장 가입 기간(17점)을 더해 84점 만점이에요. 청약 추천에서 바로 계산돼요.')]),
    'grant': ('지원금·적금·수당 이슈예요. 대상·조건·신청 기간은 공식 공고 기준이니, 아래에서 내 조건으로 찾아보세요.',
              [('💰 지원금·청약 찾기', '/apply/'), ('🏛️ 투자·저축 정책 정리', '/money/policy/')],
              [('나도 대상인가요?', '나이·소득·지역 조건이 공고마다 달라요. 루리의 줍줍 지원금 목록에서 지역·키워드로 찾아보고, 신청 전 공식 공고를 확인하세요.'),
               ('언제까지 신청하나요?', '신청 기간은 공고마다 달라요. 목록에 마감일을 표시해 두었고, 폰 알림을 켜면 새 공고를 알려 드려요.')]),
    'tax': ('세금·세제 변화 이슈예요. 바뀐 세율·공제 한도는 공식 자료로 정리한 표와 간단 계산기로 확인해 보세요(참고용).',
            [('🧮 배당소득 분리과세 계산기', '/money/tools/dividend/'), ('🧮 증권거래세 계산기', '/money/tools/stocktax/'), ('🧮 연금 세액공제 계산기', '/money/tools/pension/'), ('🏛️ 투자 관련 세제 정리', '/money/policy/#tax')],
            [('언제부터 적용되나요?', '시행 시점은 법 통과·시행령에 따라 달라요. 투자 정책 정리에 기준일과 공식 출처를 함께 적어 두었어요.'),
             ('내 세금은 얼마나 달라지나요?', '간단 계산기로 대략 비교할 수 있어요. 실제 세액은 다른 소득·공제에 따라 달라지니 국세청 안내를 확인하세요.')]),
    'rate': ('금리·환율 이슈예요. 대출 이자나 환전 금액이 얼마나 달라지는지 계산기로 비교해 보세요(참고용).',
             [('🧮 대출 이자 계산기', '/money/tools/loan/'), ('🧮 환전 계산기', '/money/tools/fx/'), ('🎙️ 금리·환율 전문가 코멘트', '/money/experts/')],
             [('대출 이자는 얼마나 바뀌나요?', '금리가 0.25%p 바뀔 때 매달 이자가 얼마나 달라지는지 대출 이자 계산기로 비교할 수 있어요. 실제 금리는 은행 상품마다 달라요.'),
              ('전문가들은 어떻게 보나요?', '실명 전문가 발언을 주제별로 모아 의견이 엇갈리면 나란히 보여 드려요. 투자 권유가 아니에요.')]),
    'market': ('증시·코인 이슈예요. 증권사·전문가 의견을 모은 정리와 차트로 흐름을 보세요(투자 권유 아님).',
               [('📊 애널리스트 분석 종합', '/analyst/'), ('🎙️ 전문가 코멘트', '/money/experts/'), ('🪙 비트코인 전망 종합', '/analyst/coin/btc/')],
               [('지금 사도 되나요?', '루리의 줍줍은 남들이 낸 전망을 정리만 해요. 사고팔지는 본인이 판단해야 해요.'),
                ('증권사들은 어떻게 보나요?', '목표가 상향·하향과 근거를 종목별로 모아 두었어요. 애널리스트 분석에서 확인하세요.')]),
    'health': ('의료·건강보험 제도 이슈예요. 시행일·대상은 보건복지부·건강보험공단 공식 안내가 기준이에요.',
               [('💰 의료·건강 관련 지원금 찾기', '/apply/'), ('🕵️ 같은 사건 언론사별 보도', '/news/')],
               [('언제부터 바뀌나요?', '기사에 나온 날짜를 위에 모아 두었어요. 정확한 시행일과 대상은 보건복지부·건강보험공단 공식 안내를 확인하세요.'),
                ('나도 해당되나요?', '대상·조건은 제도마다 달라요. 다니는 병원이나 건강보험공단(1577-1000)에 확인하는 게 가장 정확해요.')]),
    'labor': ('일하는 사람의 임금·근로 제도 이슈예요. 시행 여부·일정은 고용노동부 공식 발표가 기준이에요.',
              [('💰 일자리·근로 관련 지원금 찾기', '/apply/'), ('🧮 대출 이자 계산기', '/money/tools/loan/')],
              [('언제부터 적용되나요?', '로드맵·추진 단계인지, 법이 바뀌어 시행되는지에 따라 달라요. 기사에 나온 일정은 위에 모아 두었고, 확정 일정은 고용노동부 발표를 확인하세요.'),
               ('나한테 해당되나요?', '사업장 규모·고용 형태에 따라 적용이 달라질 수 있어요. 고용노동부 고객상담센터(1350)에서 확인할 수 있어요.')]),
    'event': ('기간이 정해진 이슈예요. 날짜·장소는 기사 기준이니 가기 전에 주최 측 공식 안내를 확인하세요.',
              [('🎁 경품 이벤트', '/event/'), ('🏆 진행 중 공모전', '/contest/')],
              [('언제·어디서 하나요?', '아래 「일정」에 기사에 나온 날짜를 모아 두었어요. 변경될 수 있으니 공식 안내를 꼭 확인하세요.')]),
}
USEFUL = re.compile(r'허용|제한|로드맵|추진|의무|금지|바뀐다|달라진다|달라지는|확정|신청|접수|시행|인상|인하|변경|도입|확대|축소|지원|발표|모집|개편|기준|한도|금리|세율|일정|출시|개시|마감|환급|지급|공제|분양|청약|오픈|개최|열린다|연장|폐지|상향|하향|요금|가격|할인|무료')
NOPE = re.compile(r'논란|사과|특검|의혹|검찰|수사|기소|피해|침수|통제|사망|부상|구속|체포|우승|감탄|열애|결혼|이혼|별세|부고|성과급|막 올랐다|와이어|홈런|골프|야구|축구|배구|농구')
NUM = re.compile(r'\d[\d,.]*\s?(?:%p|%|조\s?원|억\s?원|만\s?원|원|조|억|만\s?명|명|배|건|가구|세대|bp|일치|개월|년간)')
DATE = re.compile(r'(\d{1,2})월\s?(\d{1,2})일|(\d{1,2})/(\d{1,2})(?!\d)|\d{1,2}월(?:부터|까지|중|말|초)|연내|올해 안|내년(?:부터)?')


def slug(k):
    s = re.sub(r'[^0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ]+', '-', k.strip()).strip('-')
    return s[:40] or 'hot'


def main():
    import sys
    sys.path.insert(0, HERE)
    import news as NW, kw as KW
    now = datetime.datetime.now(KST)
    rd = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8')) if os.path.exists(os.path.join(ROOT, p)) else {}
    nw, kdb = rd('news/data.json'), rd('kw/db.json')
    I = {a['id']: a for a in nw.get('items', [])}
    C = rd('data.json').get('items', []); A = json.load(open(os.path.join(ROOT, 'apply.json'), encoding='utf-8'))
    db = json.load(open(DBF, encoding='utf-8')) if os.path.exists(DBF) else {}
    cands = []
    # ① 구글+실시간 동시 키워드, ② 언론 이슈 상위(정치 제외: 정보성 우선)
    for v in kdb.values():
        if len(v.get('src') or []) > 1 and now.date().isoformat() in v.get('days', []):
            arts = [a for a in nw.get('items', []) if v['k'].replace(' ', '') in a['t'].replace(' ', '')]
            cands.append({'title': v['k'], 'arts': arts, 'kw': v['slug'], 'traffic': v.get('traffic')})
    for x in nw.get('issues', [])[:30]:
        if x['on'] < 3:   # 분야 거르기는 아래 NOPE·USEFUL·cat 에서
            continue
        cands.append({'title': x['t'], 'arts': [I[a] for a in x['a'] if a in I], 'issue': x})
    made = 0
    for c in cands:
        arts = c['arts']
        txt = c['title'] + ' ' + ' '.join(a['t'] for a in arts)
        if KW.EXCL.search(txt) or NW.ACC.search(c['title']) or NOPE.search(c['title']):
            continue
        cat = NW.cat_of([c['title']] + [a['t'] for a in arts[:3]])
        if cat in ('연예·문화', '스포츠') or not USEFUL.search(c['title'] + ' ' + ' '.join(a['t'] for a in arts[:4])):
            continue
        outs = sorted({a['o'] for a in arts})
        if len(outs) < 2:
            continue
        typ = next((t for t, rx in TYPES if re.search(rx, c['title'])), None) or next((t for t, rx in TYPES if re.search(rx, ' '.join(a['t'] for a in arts[:3]))), None)
        if not typ:
            continue
        iss = c.get('issue') or next((x for x in nw.get('issues', []) if any(a['id'] in x['a'] for a in arts)), None)
        head = iss['t'] if iss else c['title']
        sl = slug(c.get('kw') and c['title'] or re.sub(r'[“”"\'‘’\[\]…·]', ' ', head)[:30])
        seen, what = set(), []
        for a in sorted(arts, key=lambda a: -(a.get('s') or 0)):
            if a['o'] in seen:
                continue
            seen.add(a['o']); what.append({'t': a['t'], 'o': a['o'], 'u': a['u'], 's': a.get('s'), 'g': a.get('g')})
            if len(what) >= 3:
                break
        nums, dates = [], []
        for a in arts:
            for m in NUM.findall(a['t']):
                if not any(m == n['v'] for n in nums):
                    nums.append({'v': m.strip(), 'o': a['o'], 'u': a['u'], 't': a['t']})
            for m in DATE.finditer(a['t']):
                d_ = m.group(0)
                if not any(d_ == x['v'] for x in dates):
                    dates.append({'v': d_, 'o': a['o'], 't': a['t']})
        rec = db.get(sl, {'first': now.strftime('%Y-%m-%d %H:%M')})
        rec.update({'slug': sl, 'title': head, 'q': c['title'], 'type': typ, 'last': now.strftime('%Y-%m-%d %H:%M'), 'outs': outs, 'what': what, 'nums': nums[:6], 'dates': dates[:5],
                    'arts': [{'t': a['t'], 'o': a['o'], 'u': a['u'], 's': a.get('s'), 'g': a.get('g')} for a in arts[:10]], 'kw': c.get('kw'), 'traffic': c.get('traffic'),
                    'issue': {'n': iss['n'], 'on': iss['on'], 's': iss.get('s'), 'g': iss.get('g')} if iss else None,
                    'pr': NW.promos({'t': txt[:200], 'd': ''}, C, A, now.date().isoformat())})
        db[sl] = rec
        made += 1
    os.makedirs(os.path.dirname(DBF), exist_ok=True)
    json.dump(db, open(DBF, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    live = [v for v in db.values() if v['last'] >= (now - datetime.timedelta(hours=48)).strftime('%Y-%m-%d %H:%M')]
    print('후보', len(cands), '갱신', made, '지금 핫이슈', len(live), '전체', len(db))


if __name__ == '__main__':
    main()
