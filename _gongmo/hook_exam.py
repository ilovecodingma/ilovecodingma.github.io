# -*- coding: utf-8 -*-
"""정보성 글 끝 「관련 시험 같이 준비하기」 위젯용 데이터. 빌드 때 assets/hook/ 에 키워드 색인과 시험별 문제 파일을 만든다."""
import os, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KW = {
 'labor-standards-basic': '근로기준법|퇴직금|연차|최저임금|해고|실업급여|주휴|임금|야근|연장근로|근로계약|퇴사|육아휴직|산재',
 'realtor-law-basic': '공인중개|임대차|전세|월세|계약갱신|보증금|등기부',
 'social-worker-law-basic': '사회복지|기초생활|수급자',
 'civil-servant-law-basic': '공무원|공채|국가직|지방직|공직',
 'fire-science-basic': '소방|화재',
 'heavy-equipment-safety-basic': '굴착기|지게차|건설기계',
 'electric-basic': '전기기능사|전기기사|전기|전력',
 'engineer-info-processing-basic': '정보처리|코딩|개발자|프로그래밍|IT 자격',
 'adsp-basic': '데이터 분석|ADsP|통계|데이터',
 'sqld-basic': 'SQL|데이터베이스|DB',
 'aws-clf-basic': 'AWS|클라우드',
 'linux-network-basic': '리눅스|네트워크|서버',
 'korcham-computer-2': '컴퓨터활용|컴활|엑셀|스프레드시트',
 'korean-history-basic': '한국사|한능검',
 'korean-history-advanced': '한국사|한능검',
 'driver-license-written': '운전면허|면허|운전|교통',
 'driver-road-traffic-law': '도로교통|교통법|과태료|범칙금',
 'driver-signs-markings': '교통표지|도로표지|표지판',
 'driver-safe-driving-first-aid': '안전운전|응급|사고',
 'driver-class1-extra': '1종|대형|화물',
 'toeic-grammar-basic': '토익|영어|문법',
 'toeic-vocab-basic': '토익|영어|단어',
 'transfer-english-basic': '편입|영어',
 'csat-english-vocab': '수능|영어|단어',
 'csat-math-1': '수능|수학',
 'csat-math-2': '수능|수학',
 'gsat-style-reasoning': '취업|인적성|GSAT|NCS|추리',
 'ncs-communication': 'NCS|취업|의사소통|공기업',
 'ncs-numerical': 'NCS|취업|수리|공기업',
 'gumjeong-social-basic': '검정고시|사회',
}
SKIP = re.compile(r'^(기초|기본|문제|문제은행|국가|자격|시험)$')


def build(banks):
    od = os.path.join(ROOT, 'assets', 'hook'); os.makedirs(os.path.join(od, 'b'), exist_ok=True)
    idx = []
    for d in banks:
        qs = d['questions']
        kw = KW.get(d['id'], '')
        toks = [t for t in re.split(r'[\s·()]+', d['name']) if len(t) >= 2 and not SKIP.match(t)]
        idx.append({'id': d['id'], 'name': d['name'], 'n': len(qs), 'kw': (kw + '|' + '|'.join(toks)).strip('|')})
        out = [{'q': q['q'], 'c': q['choices'], 'a': q['answer'], 'e': q.get('explain', '')} for q in qs if not q.get('fig')]
        json.dump({'id': d['id'], 'name': d['name'], 'qs': out}, open(os.path.join(od, 'b', d['id'] + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    json.dump(idx, open(os.path.join(od, 'idx.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('관련 시험 위젯 색인', len(idx))


HOOK_RX = re.compile(r'^/(money/guide|guide|wiki|money/tools|apply|mag|review)/[^/]+/$')


def tag(path):
    if path.startswith('/wiki/') and path.count('/') != 3:
        return ''
    if not HOOK_RX.match(path):
        return ''
    return '<div id="xhook" data-p="' + path + '"></div><script defer src="/assets/hook/hook.js?v=1"></script>'
