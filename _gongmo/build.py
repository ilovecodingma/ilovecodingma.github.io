#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""루리의 줍줍(sungprofile.cloud) 정적 사이트 생성.
사용: python _gongmo/build.py [--push]
원본: 바탕화면 공모전_2026/주말큐_master.jsonl + _gongmo/txt/<id>.txt(공고 본문 캐시, 비공개)
"""
import collections, json, os, re, sys, html, shutil, datetime, subprocess, hashlib, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = r'C:\Users\k\Desktop\공모전_2026\data'  # 공모전 세션 정본 (2026-10-16 합의)
MASTER = os.path.join(DATA, 'master.jsonl')
if not os.path.exists(MASTER):
    MASTER = r'C:\Users\k\Desktop\공모전_2026\주말큐_master.jsonl'
SHOTS = os.path.join(DATA, 'shots')  # 공식 공고 캡처 <id>.webp 640x400
SITE = 'https://sungprofile.cloud'
NAME = '루리의 줍줍'
_CT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contact.json'), encoding='utf-8'))
MAIL, PARTNER = _CT['contact'], _CT['partner']
_CM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'community.json')
COMM_API = json.load(open(_CM, encoding='utf-8')).get('api', '') if os.path.exists(_CM) else ''  # 비어 있으면 게시판·로그인 숨김  # 에이전트채널 규약: 일반 문의 / 제휴·광고
KST_TZ = datetime.timezone(datetime.timedelta(hours=9))
NOW_KST = lambda: datetime.datetime.now(KST_TZ).replace(tzinfo=None)   # 모든 표시·마감 계산은 한국 시간
TODAY = NOW_KST().date()
KEEP_PAST = 0  # 마감 후 상세페이지 보존 일수 (2026-10-16 사용자: 마감된 건 내림)
TXT_SRC = [os.path.join(DATA, 'txt'),
           r'C:\Users\k\AppData\Local\Temp\claude\C--Users-k\4f3e089f-943b-4eb1-9e20-4a85afd47dac\scratchpad\collect\q\txt']
E = html.escape

CATS = [('literature', '문학'), ('idea', '아이디어·정책'), ('design', '디자인'), ('video', '영상'),
        ('paper', '논문'), ('it', 'IT·과학'), ('food', '요리·레시피'), ('global', '해외'), ('etc', '기타')]
SLUG = {n: s for s, n in CATS}
CAT_INTRO = {
 '요리·레시피': '레시피 공모전, 요리경연대회, 지역 특산물 요리대회처럼 음식으로 응모하는 공모전입니다. 레시피 서류 심사 후 본선에서 직접 조리하는 경우가 많아 재료비·조리 시간·인원 제한과 본선 날짜를 먼저 확인하세요. 지정 식재료(쌀, 과일, 계란 등)를 꼭 써야 하는 대회가 많습니다.',
 '문학': '시·소설·수필·수기·네이밍·슬로건처럼 글로 응모하는 공모전입니다. 분량과 형식(원고지 매수, 글자 수, 파일 형식)이 요강마다 달라 제출 전 반드시 확인해야 합니다. 수기 공모는 실제 경험을 구체적인 장면으로 쓰는 것이, 네이밍·슬로건은 주최 기관이 내세우려는 가치를 짧게 담는 것이 중요합니다.',
 '아이디어·정책': '지자체·공공기관·기업이 정책 제안, 사업 아이디어, 마케팅 기획을 받는 공모전입니다. 국민신문고·국민생각함 같은 공식 창구로 접수하는 경우가 많고, 현황·문제점·개선안·기대효과 순서의 제안서 형식이 일반적입니다. 실현 가능성과 예산 규모를 함께 적으면 심사에서 유리합니다.',
 '디자인': '캐릭터·포스터·일러스트·웹툰·건축·공예 등 시각 작품을 받는 공모전입니다. 해상도, 파일 형식(AI·PSD·PNG), 원본 파일 제출 여부, 저작권 귀속 조건을 꼭 확인하세요. 수상작의 저작권이 주최 측으로 넘어가는 경우가 많습니다.',
 '영상': '숏폼·UCC·사진·영화 공모전입니다. 영상 길이, 화면 비율(세로형 9:16 여부), 배경음악 저작권, 초상권 동의서 제출 여부가 자주 탈락 사유가 됩니다. 유튜브·인스타그램 업로드 후 링크를 제출하는 방식도 많습니다.',
 '논문': '학술 논문·리포트·연구 제안 공모입니다. 분량 기준, 인용 양식, 표절 검사(유사도) 기준과 공동 저자 허용 여부를 먼저 확인하세요. 학생부·일반부로 나뉘는 경우가 많습니다.',
 'IT·과학': '해커톤, SW 개발, AI 활용, 데이터 분석, 과학 탐구 공모전입니다. 팀 구성 인원, 개발 기간, 결과물 공개 여부(오픈소스), 사용 가능한 API·데이터 조건을 확인하세요.',
 '해외': '해외 기관이 주최하는 국제 공모전·해커톤입니다. 대부분 영어(일부 일본어)로 응모하며 국적 제한, 시차를 고려한 마감 시각(현지 시간 기준), 상금 송금 방식(해외 송금 수수료)을 확인해야 합니다.',
 '기타': '위 분야에 속하지 않는 다양한 공모전입니다. 요강의 응모 자격과 제출물을 꼼꼼히 읽어 보세요.',
}
TIPS = {
 '요리·레시피': ['지정 식재료(쌀·과일·계란 등)를 주재료로 썼는지 확인', '레시피는 재료 g·계량과 조리 순서를 사진과 함께', '본선 조리 시간·인원·재료 지참 여부 확인', '완성 사진은 밝은 자연광에서 위·45도 두 컷', '집에 있는 재료로 연습하려면 루리의 냉장고 파먹기 활용'],
 '문학': ['분량(글자 수·원고지 매수)과 파일 형식을 요강 그대로 맞추기', '주제어가 제목과 첫 문단에 드러나게 쓰기', '미발표 창작물 조건 확인(다른 공모전 중복 응모 금지가 흔함)'],
 '아이디어·정책': ['현황 → 문제점 → 개선안 → 기대효과 순서로 정리', '비슷한 기존 정책이 있는지 먼저 검색해 차별점 적기', '소요 예산과 실행 주체를 구체적으로 제시'],
 '디자인': ['요구 해상도·규격·파일 형식 확인', '원본 파일(AI·PSD) 제출 요구 여부 확인', '저작권 귀속·2차 활용 조건 읽기'],
 '영상': ['영상 길이와 화면 비율(가로·세로) 확인', '배경음악·폰트는 상업적 이용 가능한 것만 사용', '출연자 초상권 동의서 준비'],
 '논문': ['분량·인용 양식·유사도 기준 확인', '공동 저자 허용 여부와 소속 표기 방법 확인', '초록과 결론에 주최 측 주제 키워드 반영'],
 'IT·과학': ['팀 인원 제한과 개발 기간 확인', '사용 가능한 API·데이터·라이선스 확인', '시연 영상·README 등 제출물 형식 준비'],
 '해외': ['마감 시각의 기준 시간대(현지 시간) 확인', '국적·거주지 제한 여부 확인', '상금 수령 방식(해외 송금, 세금 서류) 확인'],
 '기타': ['응모 자격(나이·지역·학생 여부) 먼저 확인', '제출 방법(이메일·홈페이지·구글폼) 확인', '마감 당일 접속 폭주에 대비해 하루 전 제출'],
}
CH = {'mail': '이메일 접수', 'mail?': '이메일 접수(공고 확인)', 'web': '홈페이지 접수', 'gform': '구글폼 접수', 'nform': '네이버폼 접수',
      'ig': '인스타그램 참여', 'yt': '유튜브 참여'}
EV_KIND = {'event': '이벤트', 'sweepstakes': '추첨 경품', 'quiz': '퀴즈', 'survey': '설문', 'sns_comment': '댓글 이벤트',
           'sns_tag_required': '친구 태그', 'sns_story_required': '스토리 공유', 'sns_capture': '캡처 인증', 'sns_form_only': '폼 응모',
           'sns_comment+form': '댓글+폼', 'sns_purchase': '구매 인증', 'sns_region': '지역 한정', 'sns_other': 'SNS 이벤트'}

COMM_TAGS_TPL = '<link rel="stylesheet" href="/assets/community/comm.css?v=15"><script defer src="/assets/community/comm.js?v=24"></script><script defer src="/assets/community/crew.js?v=1"></script>'
GTAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4248498719773262" crossorigin="anonymous"></script>\n'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());if(location.hostname!=='sungprofile.cloud')window['ga-disable-G-G9BPFF95GY']=true;gtag('config','G-G9BPFF95GY');</script>")
THEMES = [  # (키, 이름, 아이콘, 테마색, 홈, [하위 메뉴], [이 테마에 속하는 주소 앞부분])
    ('issue', '이슈', '🕵️', '#b45309', '/news/', [('/hot/', '핫이슈'), ('/news/', '기사 확인 신호'), ('/talk/', '커뮤니티 이슈'), ('/kw/', '인기 키워드'), ('/satire/', '루리 풍자'), ('/mag/', '매거진'), ('/review/', '평론')],
     ['/hot/', '/news/', '/talk/', '/kw/', '/satire/', '/mag/', '/review/']),
    ('money', '머니', '📊', '#047857', '/analyst/', [('/analyst/', '애널리스트 종합'), ('/money/experts/', '전문가 코멘트'), ('/money/policy/', '투자 정책'), ('/money/age/', '나이별 원칙'), ('/money/tools/salary/', '계산기'), ('/analyst/coin/btc/', '코인')], ['/analyst/', '/money/']),
    ('contest', '공모전', '🏆', '#6d28d9', '/contest/', [('/contest/', '추천 상담'), ('/cat/literature/', '분야별'), ('/prep/', '준비실'), ('/lab/', '수상 연구소'), ('/community/', '원정대'), ('/guide/', '가이드'), ('/widget/', '위젯')],
     ['/contest/', '/c/', '/cat/', '/prep/', '/lab/', '/community/', '/guide/', '/v/', '/me/', '/widget/']),
    ('life', '생활', '🍳', '#0e7490', '/apply/', [('/apply/', '지원금·청약'), ('/apply/recommend/', '청약 추천'), ('/apply/r/', '지역별'), ('/event/', '경품'), ('/fridge/', '냉장고 파먹기'), ('/qa/', '고민 해결'), ('/plaza/', '광장')], ['/apply/', '/a/', '/event/', '/fridge/', '/qa/', '/ssul/', '/plaza/']),
    ('ai', '개발 지식', '🧑‍💻', '#0f172a', '/ailog/', [('/ailog/', '개발 지식'), ('/dev/faq/', '개발 FAQ'), ('/en/guide/', 'English guides'), ('/ailog/#log', 'AI 제작 로그')], ['/ailog/', '/dev/', '/en/'])]   # 2026-10-19 사용자: AI 로그 → 개발 지식으로 개편


def theme_of(path):
    if path == '/':
        return None
    for th in THEMES:
        if any(path.startswith(px) for px in th[6]):
            return th
    return None


TABS = [('/news/', '🕵️ 이슈'), ('/analyst/', '📊 애널리스트'), ('/', '🏆 공모전'), ('/mag/', '📰 매거진'), ('/all/', '☰ 전체')]   # 2026-10-18 난잡함 정리: 5개만, 나머지는 /all/
NAV = [('apply', '청약·신청'), ('ssul', '썰'), ('event', '경품·용돈'), ('cat/literature', '문학'), ('cat/idea', '아이디어'), ('cat/design', '디자인'),
       ('cat/video', '영상'), ('cat/it', 'IT'), ('cat/global', '해외'), ('guide', '가이드')]


PAGE_HASH, NOINDEX = {}, set()
REVIEWS = []   # 평론 (review_pages 가 채움, rss_feed 가 읽음)


PAGE_INTRO = {k: f'<section class="pg-intro"><h2>{h}</h2>{v}</section>' for k, (h, v) in {  # 2026-10-18 애드센스 보강: 목록·홈에 운영자가 쓴 안내문
 '/': ('루리의 줍줍은 어떤 곳인가요?', '<p>루리의 줍줍은 개인 개발자 한 명이 AI와 함께 만들고 운영하는 생활 정보 사이트예요. 매일 쏟아지는 기사·리포트·공고를 그대로 옮기지 않고, 같은 내용끼리 묶어 숫자를 다시 계산한 뒤 「그래서 나한테 무슨 뜻인지」를 정리하는 게 목표예요.</p><ul class="chk"><li><b>🕵️ 이슈</b>: 언론사 15곳 기사를 사건별로 묶어 몇 곳이 보도했는지, 출처가 실명인지, 제목 속 숫자가 본문에 있는지 같은 확인 신호로 점수를 매겨요. 진실 판정이 아니라 「더 확인해 볼 곳」을 알려 주는 점수예요.</li><li><b>📊 머니</b>: 증권사 리포트 기사 속 목표가·투자의견을 노드로 쪼개 종목별로 상향·하향을 다시 셉니다. 투자 권유가 아니라 의견 분포를 보여 주는 정리예요. 세금·대출 계산기와 2026년 투자 정책 표도 있어요.</li><li><b>🏆 공모전</b>·<b>🍳 생활</b>: 마감·상금·자격을 같은 형식으로 정리하고, 같은 분야와 비교한 분석과 준비 일정을 붙여요. 지원금·청약·경품 이벤트도 마감순으로 모아요.</li></ul><p>모든 자동 정리에는 원문 링크를 함께 달고, 틀린 정보는 <a href="/contact/">문의</a>로 받으면 바로 고쳐요. 만드는 과정은 <a href="/ailog/">AI 제작 로그</a>에 공개하고 있어요.</p>'),
 '/guide/': ('응모 가이드 읽는 법', '<p>공모전을 처음 내 보는 분부터 여러 번 떨어져 본 분까지, 루리가 실제 공고와 수상작을 보며 정리한 글이에요. 제안서 구성, 수기·문학 분량 맞추기, 영상 저작권, 상금 세금(기타소득 22%)과 수상 사칭 사기 구별법처럼 응모 전후에 자주 묻는 것들을 다뤄요. 글마다 관련 공모전 목록을 붙여 두었으니 읽고 바로 골라 보세요.</p>'),
 '/qa/': ('고민 해결은 이렇게 만들어요', '<p>사이트 챗봇과 문의로 실제 받은 질문 가운데 여러 사람이 비슷하게 묻는 것을 골라 답을 정리해요. 청년 지원금 자격, 공모전 준비 순서, 청약 가점처럼 공식 기준이 있는 질문은 정부24·청약홈 같은 공식 안내를 확인한 뒤 써요. 개인 사정에 따라 답이 달라지는 부분은 「어디에 물어보면 되는지」까지 적어 두어요.</p>'),
 '/mag/': ('루리의 이슈 리딩이란', '<p>하루에 한 장, 정치 이슈의 기사 확인 신호와 커뮤니티 화제, 마감 임박 공모전, 새 지원금을 한 번에 훑어보는 데일리 매거진이에요. 기사 제목을 옮기는 대신 「몇 곳이 보도했고 무엇이 아직 확인되지 않았는지」를 짧게 정리하고, 지난 호도 날짜별로 다시 볼 수 있어요.</p>'),
 '/kw/': ('인기 키워드는 이렇게 골라요', '<p>구글 트렌드와 실시간 검색어 자료에서 지금 검색이 몰리는 말을 모으고, 같은 시간 언론 보도와 맞춰 「왜 떴는지」를 붙여요. 사건·사고, 연예인 사생활, 혐오성 키워드는 일부러 빼요. 키워드가 이틀 넘게 이어지면 추세선으로 얼마나 오래 화제인지도 보여 드려요.</p>'),
 '/hot/': ('핫이슈 고르는 기준', '<p>검색 급상승과 언론 보도가 함께 몰린 이슈 가운데 <b>내 돈·내 생활에 바로 영향을 주는 것</b>만 골라요. 청약·지원금·세금·금리·의료·임금처럼 「나한테 달라지는 점」이 있는 이슈에는 관련 계산기와 신청처를 붙이고, 정치 공방이나 사건·사고는 넣지 않아요. 48시간이 지나면 지난 이슈로 내려가요.</p>'),
 '/satire/': ('루리 풍자에 대해', '<p>그날 화제가 된 증시·뉴스를 루리가 한 컷 만평으로 그려요. 특정 개인을 조롱하지 않고, 상황의 아이러니를 짚는 걸 원칙으로 해요. 이미지는 직접 만든 AI 그림이고, 지난 풍자도 날짜별로 모아 두었어요.</p>'),
 '/all/': ('전체 메뉴 안내', '<p>루리의 줍줍은 이슈·머니·공모전·생활·AI 로그 다섯 테마로 나뉘어 있어요. 테마마다 매시간 자동으로 갱신되는 정리 페이지와, 직접 쓴 가이드·계산기가 섞여 있어요. 찾는 메뉴가 없으면 화면 아래 루리 챗봇에게 물어보세요.</p>'),
 '/event/': ('경품 이벤트 볼 때 알아 둘 것', '<p>기업·기관 SNS와 이벤트 사이트에 올라온 경품 이벤트를 매시간 모아 마감순으로 정리해요. 댓글 한 줄·퀴즈·설문처럼 1~5분이면 끝나는 것을 위로 올려요. 당첨됐다며 개인정보나 배송비·세금 송금을 먼저 요구하는 연락은 사기일 가능성이 크니, 꼭 공식 계정의 발표 글과 대조해 보세요. 경품이 5만원을 넘으면 제세공과금(22%)을 낼 수 있어요.</p>'),
 '/fridge/': ('냉장고 파먹기 사용법', '<p>집에 있는 재료를 고르면 루리가 정리한 집밥 레시피 중 지금 바로 만들 수 있는 메뉴를 먼저 보여 드려요. 재료 하나만 더 사면 되는 메뉴도 함께 알려 줘서, 장보기 목록을 줄일 수 있어요. 레시피는 1~2인분 기준이고 조리 시간과 난이도를 함께 적었어요.</p>'),
 '/lab/': ('수상 연구소는 이렇게 분석해요', '<p>슬로건·표어·네이밍 공모전의 실제 수상작을 모아 글자 수, 운율, 대구, 핵심어 위치 같은 구조로 하나씩 풀어 봐요. 수상작을 베끼는 게 아니라 「왜 뽑혔는지」를 알아보는 곳이에요. 내 문구를 넣으면 같은 기준으로 진단해 드려요.</p>'),
 '/apply/': ('청약·지원금 신청 전에', f'<p>여기 모은 일정은 청약홈·LH·지자체·정부24 공고를 바탕으로 마감순으로 정리했어요. 같은 지원금이라도 지역·나이·소득 기준이 달라 신청 전에 자격부터 확인해야 해요. 청약은 <a href="/apply/recommend/">청약 추천</a>에서 내 가점을 먼저 계산해 보세요. 사는 곳 기준으로 보려면 <a href="/apply/r/">지역별 지원금·청약</a>에서 시·도를 고르세요. 달별로는 <a href="/apply/month/{TODAY:%Y-%m}/">{TODAY.month}월 청약 일정</a>·<a href="/apply/month/{(TODAY.replace(day=28) + datetime.timedelta(days=4)):%Y-%m}/">{(TODAY.replace(day=28) + datetime.timedelta(days=4)).month}월 청약 일정</a>, 대상별로는 <a href="/apply/newlywed/">신혼부부 지원금</a>도 있어요.</p>'),
 '/contest/': ('공모전 추천은 이렇게 해요', '<p>진행 중인 공모전을 마감·상금·분야·제출물로 정리해 두고, 내가 고른 조건에 맞는 것부터 보여 줘요. 상금이 큰 것만이 아니라 「준비 시간 대비 할 만한 것」을 위로 올리는 게 루리의 기준이에요. 각 공모전 페이지에는 같은 분야와 비교한 분석, 오늘 기준 준비 일정을 붙여 두었어요. <a href="/contest/week/">이번 주 마감 공모전</a>만 따로 볼 수도 있고, 대상·분야별로는 <a href="/contest/youth/">청소년 공모전</a>, <a href="/contest/novel/">소설 공모전</a>, <a href="/contest/photo/">사진 공모전</a>, <a href="/contest/video/">영상 공모전</a>, <a href="/contest/idea/">아이디어 공모전</a>, <a href="/contest/univ/">대학생 공모전</a>, <a href="/contest/ai-video/">AI 영상 공모전</a> 모음도 있어요.</p>'),
}.items()}


def page(path, title, desc, body, crumbs=None, ld=None, full_title=False, noindex=False, og=None, lang='ko'):
    url = SITE + path
    TH = theme_of(path)
    # 사이트맵 lastmod: 날짜·시각·D-day 처럼 매번 바뀌는 글자는 빼고 내용이 바뀐 날만 갱신
    PAGE_HASH[path] = hashlib.md5(re.sub(r'D-\d+|D-DAY|\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}', '', title + body).encode()).hexdigest()
    if noindex:
        NOINDEX.add(path)
    COMM_TAGS = COMM_TAGS_TPL if COMM_API else ''
    t = title if full_title else f'{title} | {NAME}'
    lds = []
    if crumbs:
        lds.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(crumbs)]})
    if ld:
        lds.append(ld)
    ldh = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False).replace('</', '<\\/') for x in lds)
    nav = ''.join(f'<a href="/{s}/">{n}</a>' for s, n in NAV + ([('community', '원정대')] if COMM_API else []))
    doc = f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(t)}</title>
<meta name="description" content="{E(desc)}">{'<meta name="robots" content="noindex,follow">' if noindex else ''}
<link rel="canonical" href="{url}">{f'<link rel="alternate" hreflang="en" href="{url}">' if lang == 'en' else ''}
<meta property="og:type" content="website"><meta property="og:locale" content="{'en_US' if lang == 'en' else 'ko_KR'}"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{E(t)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og or "/assets/ruri/og.jpg"}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}{og or "/assets/ruri/og.jpg"}">
<meta name="theme-color" content="{TH[3] if TH else '#5b21b6'}">
<link rel="icon" href="/favicon.ico?v=6" sizes="any"><link rel="icon" type="image/png" sizes="48x48" href="/assets/icons/icon-48.png?v=6"><link rel="icon" type="image/png" sizes="96x96" href="/assets/icons/icon-96.png?v=6"><link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png?v=6"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png?v=6"><link rel="manifest" href="/site.webmanifest"><link rel="alternate" type="application/rss+xml" title="루리의 줍줍" href="/rss.xml">
<link rel="preconnect" href="https://cdn.jsdelivr.net"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/gm.css?v=17">{('<link rel="stylesheet" href="/assets/chat/ruri-chat.css?v=8">') if not (TH and TH[0] == 'ai') else ''}{COMM_TAGS}{('<script type="module" src="/assets/chat/ruri-chat.js?v=13"></script>') if not (TH and TH[0] == 'ai') else ''}<script defer src="/assets/app/app.js?v=3"></script>
{ldh}
{GTAG}
</head><body data-th="{TH[0] if TH else 'hub'}"{(' data-api="' + COMM_API + '"') if COMM_API else ''}>
<header class="hd"><div class="w hd-in"><a class="logo" href="/"><img src="/assets/icons/logo.svg" width="30" height="30" alt="루리의 줍줍"><span>루리의 <b>줍줍</b></span></a>{('<span class="th-name">' + TH[2] + ' ' + TH[1] + '</span>') if TH else ''}</div>
<nav class="th-sw w" aria-label="테마">{"".join(f'<a href="{t[4]}" style="--tc:{t[3]}"{" class=on" if TH and TH[0] == t[0] else ""}>{t[2]} {t[1]}</a>' for t in THEMES)}</nav>
{('<nav class="tb w" aria-label="' + TH[1] + ' 메뉴">' + "".join(f'<a href="{u}"{" class=on" if (path == u or (u != TH[4] and path.startswith(u))) else ""}>{n}</a>' for u, n in TH[5]) + '</nav>') if TH else ''}</header>
<main class="w">
{body}{PAGE_INTRO.get(path, '')}
</main>
<footer class="ft"><div class="w ft-in"><div class="ft-b"><img class="av" src="/assets/ruri/avatar.webp" width="56" height="56" alt="루리" loading="lazy"><div><b>루리의 줍줍</b><p>마감 놓치지 마세요! 매일 아침 새 공모전을 정리해 둘게요.</p><p class="ft-m">문의 <a href="mailto:{MAIL}">{MAIL}</a>{"" if PARTNER == MAIL else f' · 제휴 <a href="mailto:{PARTNER}">{PARTNER}</a>'}</p></div></div>
<p class="ft-l"><a href="/about/">소개</a><a href="/all/">전체 메뉴</a><a href="/plaza/">🗣️ 광장</a><a href="/ailog/">🤖 AI 제작 로그</a><a href="/news/">🕵️ 기사 확인 신호</a><a href="/app/">📲 앱·알림</a><a href="/prep/">준비실</a><a href="/qa/">고민 해결</a><a href="/guide/">응모 가이드</a><a href="/event/">경품 이벤트</a><a href="/privacy/">개인정보처리방침</a><a href="/terms/">이용약관</a><a href="/contact/">문의</a></p>
{('<p class="ft-c">' + comm_btns() + '</p>') if COMM_LINKS else ''}<p class="ft-n">공모전 정보는 각 주최 기관의 공고를 바탕으로 정리했으며, 정확한 요강은 반드시 공식 공고에서 확인하세요. © 2026 루리의 줍줍 · sungprofile.cloud</p></div></footer>{CL_CSS if COMM_LINKS else ''}
</body></html>'''
    d = os.path.join(ROOT, path.strip('/'))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(doc)


CAT_OUTFIT = {'요리·레시피': 'o_cook', '문학': 'o_cardigan', '아이디어·정책': 'o_present', '디자인': 'o_gray', '영상': 'o_anchor', '논문': 'o_vest', 'IT·과학': 'o_desk', '해외': 'o_trench', '기타': 'o_suit'}
CAT_ICON = {'요리·레시피': '🍳', '문학': '✍️', '아이디어·정책': '💡', '디자인': '🎨', '영상': '🎬', '논문': '📚', 'IT·과학': '💻', '해외': '🌏', '기타': '🧩'}


def say(expr, html_, cls=''):
    return (f'<div class="say {cls}"><img src="/assets/ruri/{expr}_s.webp" width="56" height="77" alt="루리" loading="lazy">'
            f'<div class="bub"><b>루리</b><div>{html_}</div></div></div>')


def dday(end):
    n = (datetime.date.fromisoformat(end) - TODAY).days
    return n, ('마감' if n < 0 else 'D-DAY' if n == 0 else f'D-{n}')


def ddot(s):
    return s.replace('-', '.') if s else ''


def sync_txt():
    """공모전 세션이 새로 받은 공고 본문을 _gongmo/txt 로 복사(없는 것·갱신된 것만)"""
    dst = os.path.join(HERE, 'txt')
    os.makedirs(dst, exist_ok=True)
    n = 0
    for src in TXT_SRC:
        if not os.path.isdir(src):
            continue
        for f in os.listdir(src):
            a, b = os.path.join(src, f), os.path.join(dst, f)
            if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
                shutil.copy2(a, b)
                n += 1
    return n


def sync_shots(live):
    """진행 중 공모전 캡처만 assets/shots 에 두고, 마감된 건 지움"""
    dst = os.path.join(ROOT, 'assets', 'shots')
    os.makedirs(dst, exist_ok=True)
    keep = {c['id'] + '.webp' for c in live if c.get('th')}
    for f in keep:
        a, b = os.path.join(SHOTS, f), os.path.join(dst, f)
        if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
            shutil.copy2(a, b)
    gone = [f for f in os.listdir(dst) if f not in keep]
    for f in gone:
        os.remove(os.path.join(dst, f))
    print('shots', len(keep), 'removed', len(gone))


def load():
    print('txt synced', sync_txt())
    rows = [json.loads(l) for l in open(MASTER, encoding='utf-8') if l.strip()]
    # 공모전 판정·추출은 parse.py 로직 그대로, 마감 후 KEEP_PAST 일까지 포함
    P.Q = HERE
    P.MASTER = MASTER
    P.TODAY = TODAY - datetime.timedelta(days=KEEP_PAST)
    tmp = os.path.join(HERE, '_c.json')
    P.OUT = tmp
    argv, sys.argv = sys.argv, ['x', '--no-push']
    P.main()
    sys.argv = argv
    contests = json.load(open(tmp, encoding='utf-8'))['items']
    os.remove(tmp)
    byid = {r['id']: r for r in rows}
    for c in contests:
        r = byid.get(c['id'], {})
        c['ch'] = CH.get(r.get('ch', ''), '공고 참조')
        c['th'] = 1 if os.path.exists(os.path.join(SHOTS, c['id'] + '.webp')) else 0
        # 공모전 세션 수집 필드(있으면 우선): quick, effort, region, fee
        c['quick'] = r.get('quick')
        c['effort'] = P.clean(r.get('effort', ''))[:12]
        c['region'] = P.clean(r.get('region', '') if isinstance(r.get('region'), str) else '')[:10]
        c['fee'] = r.get('fee') or 0
        c['submit'] = P.clean(r.get('submit', ''))[:10]
        c['ai'] = r.get('ai') if r.get('ai') in ('허용', '금지', '표기') else ''
        if re.match(r'^\s*(및|등|또는|,|·|\)|이상)', c.get('elig') or '') or c.get('elig') in ('공고 참조', '-'):   # 2026-10-19: 잘려 들어온 자격 문구는 비워 「공식 공고 확인 필요」로
            c['elig'] = ''
        if r.get('prize_first') and not c['pv']:
            c['pv'] = int(r['prize_first']); c['prize'] = f"1등 {int(r['prize_first']) // 10000:,}만원"
    seen, events = set(), []
    cids = {c['id'] for c in contests}
    for r in rows:
        k = r.get('kind', '')
        if k not in EV_KIND or r.get('end', '') < TODAY.isoformat() or r['id'] in cids:
            continue
        t = P.clean(r.get('title', ''))[:90]
        if not t or t == 'N/A':
            continue
        key = P.norm_title(t) + r.get('end', '')
        if key in seen:
            continue
        seen.add(key)
        events.append({'id': r['id'], 'title': t, 'org': P.clean(r.get('org', ''))[:40], 'end': r['end'],
                       'type': EV_KIND[k], 'ch': CH.get(r.get('ch', ''), ''), 'link': r.get('apply') or r['url'], 'effort': P.clean(r.get('effort', ''))[:12]})
    events.sort(key=lambda e: (e['end'], e['title']))
    return contests, events


def score(c):
    """추천순: 상금(로그) + 적당히 남은 기간(2~14일 최고) − 오늘 마감"""
    n = dday(c['end'])[0]
    import math
    s = (math.log10(c['pv']) - 4) * 1.2 if c['pv'] else 0
    s += 2 if 2 <= n <= 14 else 1 if n <= 30 else 0
    s -= 3 if n <= 0 else 0
    s += 1 if c.get('effort') or c.get('quick') else 0
    return s


def card(c):
    n, dd = dday(c['end'])
    cls = 'd off' if n < 0 else 'd u3' if n <= 3 else 'd hot' if n <= 7 else 'd'
    tg = ''.join(f'<span class="tg">{E(t)}</span>' for t in c['tags'])
    pz = (f'<span class="ez e0">{E(c["effort"])}</span>' if c.get('effort') else '') + (f'<span class="pz">🏆 {E(c["prize"])}</span>' if c['pv'] else '') + (f'<span class="tg rg">📍 {E(c["region"])}</span>' if c.get('region') else '')
    th = f'<img class="th" src="/assets/shots/{c["id"]}.webp" width="640" height="400" alt="" loading="lazy">' if c.get('th') else ''
    return (f'<li><a class="card{" has-th" if th else ""}" data-c="{SLUG[c["tags"][0]]}" href="/c/{c["id"]}/">{th}<span class="ic">{CAT_ICON[c["tags"][0]]}</span><div class="cb"><div class="top"><h3 class="t">{E(c["title"])}</h3><span class="{cls}">{dd}</span></div>'
            f'<p class="o">{E(c["org"])}</p><p class="pd">접수 {(ddot(c["start"])[5:] + " ~ ") if c.get("start") else "~ "}{ddot(c["end"])[5:]}</p><div class="tags">{pz}{tg}</div></div></a></li>')


ELIG_NOTE = [  # 응모 자격 글자 → 준비할 것 (2026-10-18 애드센스 보강: 공모전마다 다른 해설)
    (r'제한\s?없|누구나|전\s?국민|일반\s?국민', '나이·지역 제한이 없어 누구나 낼 수 있어요. 다만 1인당 응모 편수 제한이 있는지 공고에서 확인하세요.'),
    (r'외국인', '외국인도 낼 수 있게 열려 있어요. 수상 시 외국인등록증 등 신분 확인 서류를 요구할 수 있어요.'),
    (r'대학원생|대학생', '대학(원)생이 대상에 들어 있어요. 수상 후 재학·휴학 증명서를 요구하는 경우가 많으니 미리 발급해 두세요.'),
    (r'청소년|초등|중학|고등|유치원', '학생부가 따로 있을 수 있어요. 미성년자는 보호자 동의서가 필요한 경우가 많아요.'),
    (r'거주|도민|시민|군민|구민|지역', '지역 거주자로 제한될 수 있어요. 주민등록상 주소나 재직·재학지가 기준인지 확인하세요.'),
    (r'팀|공동|2인|3인', '팀이나 공동 작품도 받아요. 팀 응모는 대표자 한 명이 접수하고 상금을 나누는 방식이 흔해요.'),
]
EFFORT_NOTE = {'영상': '영상은 길이(초)·해상도·파일 형식(mp4)과 음원·폰트 저작권이 심사 전에 가장 많이 걸리는 부분이에요. 무료 음원도 출처를 적어 두세요.',
               '원고': '원고는 분량 기준(글자 수·원고지 매수)과 파일 형식(hwp·docx·pdf)을 먼저 맞추세요. 분량을 넘기면 심사에서 빠지는 경우가 있어요.',
               '아이디어 제안서': '제안서는 현황 → 문제점 → 개선안 → 기대효과 순서가 기본이에요. 이미 시행 중인 정책과 겹치지 않는지 검색해 보고 차별점을 한 줄로 적어 두세요.',
               '디자인': '디자인은 원본 파일(ai·psd)과 미리보기(jpg·png)를 함께 내라는 공고가 많아요. 폰트·이미지 라이선스를 꼭 확인하세요.',
               '사진': '사진은 촬영 원본(EXIF 포함)을 요구하는 경우가 많고, 사람이 나오면 초상권 동의가 필요해요. 과한 보정은 감점될 수 있어요.',
               '기획서': '기획서는 목표·대상·실행 방법·예산·일정을 한 장 요약으로 먼저 보여 주면 심사위원이 읽기 쉬워요.',
               '실물 출품': '실물 출품은 접수 기간 안에 도착해야 하는지(도착 기준) 보낸 날짜 기준인지 확인하고, 포장·배송 기간을 넉넉히 잡으세요.'}
GONE = {}
HIST = {}   # 공모전 변경 이력 (contest_hist.json)
DUP = {}   # 중복 공고 id → 대표 id (build 가 채움)


def gone_pages():
    """한 번 만든 /c/·/a/ 주소는 데이터에서 빠져도 「마감」 안내로 남긴다(검색 제외). 2026-10-18 애드센스 심사 중 404 방지."""
    G = os.path.join(HERE, 'gone_pages.json')
    old = json.load(open(G, encoding='utf-8')) if os.path.exists(G) else {}
    cur = set(GONE) | {f'/c/{d}/' for d in DUP}   # 중복 공고 안내 페이지는 덮어쓰지 않음
    old.update(GONE)
    for u, (t, back, bn, end) in old.items():
        if u in cur:
            continue
        msg = f'아쉽지만 끝났어요. <a href="{back}">진행 중인 {E(bn)}</a>을 봐 주세요!'
        page(u, f'{t} (마감)', f'{t} — 접수가 끝났어요. 진행 중인 {bn}을 확인하세요.',
             f'<p class="bc"><a href="/">홈</a> › <a href="{back}">{E(bn)}</a></p><h1>{E(t)}</h1><p class="warn">{ddot(end)}에 마감된 공고예요. 정보가 더 이상 갱신되지 않아요.</p>'
             + say('sad', msg), [('루리의 줍줍', '/'), (bn, back)], noindex=True)
    json.dump(old, open(G, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


COLL = {}   # 합쳐서 없앤 얇은 페이지 → 데이터 화면 주소 (collapse_thin 이 채움)
COLL_RULES = [(re.compile(r'^/a/([^/]+)/$'), lambda m: f'/apply/?id={m.group(1)}'), (re.compile(r'^/kw/([^/]+)/$'), lambda m: f'/kw/?k={m.group(1)}'),
              (re.compile(r'^/lab/[^/]+/$'), lambda m: '/lab/'), (re.compile(r'^/analyst/s/[^/]+/$'), lambda m: '/analyst/'),
              (re.compile(r'^/apply/r/([^/]+)/[^/]+/$'), lambda m: f'/apply/r/{m.group(1)}/'), (re.compile(r'^/apply/r/[^/]+/$'), lambda m: '/apply/r/')]


def collapse_thin(urls):
    """2026-10-19 사용자 「페이지가 너무 많으니 줄이고 데이터 기반 reload 형식으로」: 검색 제외(noindex)된 얇은 자동 페이지는 파일을 만들지 않고
    데이터 화면 하나(/apply/?id=·/kw/?k=)나 상위 허브로 합친다. 예전 주소는 404.html 이 같은 규칙으로 바로 넘겨 주고, 사이트 안 링크는 새 주소로 바꾼다.
    색인 대상 페이지·마감 공모전 안내(/c/)는 건드리지 않는다."""
    COLL.clear()
    for u in sorted(NOINDEX, key=len, reverse=True):
        for rx, to in COLL_RULES:
            m = rx.match(u)
            if m:
                COLL[u] = to(m)
                break
    for u in COLL:
        shutil.rmtree(os.path.join(ROOT, u.strip('/')), ignore_errors=True)
    LINK = re.compile(r'href="(/(?:a|kw|lab|analyst/s|apply/r)/[^"#?]*)"')
    n = 0
    for dp, dn, fn in os.walk(ROOT):
        if any(x in dp for x in (os.sep + 'assets', os.sep + '.git', os.sep + '_gongmo', os.sep + 'og')):
            continue
        for f in fn:
            if f.endswith('.html'):
                fp = os.path.join(dp, f)
                t = open(fp, encoding='utf-8').read()
                t2 = LINK.sub(lambda m: f'href="{COLL.get(m.group(1), m.group(1))}"', t)
                if t2 != t:
                    open(fp, 'w', encoding='utf-8', newline='\n').write(t2); n += 1
    urls[:] = [u for u in urls if u not in COLL]
    # /apply/ 를 60건만 그리게 바꿔서(2026-10-19) 링크가 끊긴 색인 대상 /a/ 상세는 /apply/ 맨 아래 짧은 목록으로 이어 준다
    ap_f = os.path.join(ROOT, 'apply', 'index.html')
    if os.path.exists(ap_f):
        t = open(ap_f, encoding='utf-8').read()
        linked = set()
        for dp, dn, fn in os.walk(ROOT):
            if any(x in dp for x in (os.sep + 'assets', os.sep + '.git', os.sep + '_gongmo', os.sep + 'og', os.sep + 'a' + os.sep)):
                continue
            for f in fn:
                if f.endswith('.html'):
                    linked |= set(re.findall(r'href="(/a/[^"]+/)"', open(os.path.join(dp, f), encoding='utf-8').read()))
        lone = [u for u in urls if u.startswith('/a/') and u not in linked and u not in NOINDEX]
        if lone and '<!--ap-rest-->' not in t:
            ti = {u: (re.search(r'<title>([^<|]*)', open(os.path.join(ROOT, u.strip('/'), 'index.html'), encoding='utf-8').read()) or [None, u])[1].strip() for u in lone}
            t = t.replace('<ul class="list" id="ap-list">', f'<!--ap-rest--><details class="fr-all"><summary>그 밖의 공고 {len(lone)}건 바로 가기</summary><ul>' + ''.join(f'<li><a href="{u}">{E(ti[u])}</a></li>' for u in lone) + '</ul></details><ul class="list" id="ap-list">', 1)
            open(ap_f, 'w', encoding='utf-8', newline=chr(10)).write(t)
    NOINDEX.difference_update(COLL)   # 없어진 페이지는 검색 제외 비율 계산에서도 뺌
    json.dump(COLL, open(os.path.join(HERE, 'collapsed.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return len(COLL), n


def auto_thin(urls):
    """빌드가 끝난 뒤 상세 페이지의 고유 본문을 세어 200자 미만이면 검색 제외로 돌린다(adsense_audit 와 같은 셈법)."""
    import adsense_audit as A
    DET = ('/c/', '/a/', '/lab/', '/kw/', '/analyst/s/', '/analyst/coin/', '/money/tools/', '/apply/r/', '/contest/univ/', '/contest/ai-video/', '/hot/', '/satire/', '/mag/', '/ssul/', '/guide/', '/review/', '/fridge/r/')
    got, freq = {}, collections.Counter()
    for u in urls:
        f = os.path.join(ROOT, u.strip('/'), 'index.html')
        if not os.path.exists(f):
            continue
        doc = open(f, encoding='utf-8').read()
        lines = A.parts(doc)[0]
        freq.update({re.sub(r'[\d,.]+', '#', l) for l in lines})
        got[u] = (f, doc, lines)
    n = 0
    for u, (f, doc, lines) in got.items():
        if u in NOINDEX or not any(u.startswith(d) and u != d for d in DET):
            continue
        own = sum(len(l.replace(' ', '')) for l in lines if freq[re.sub(r'[\d,.]+', '#', l)] < 5)
        if own < 200:
            NOINDEX.add(u); n += 1
            open(f, 'w', encoding='utf-8', newline='\n').write(doc.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow">\n<link rel="canonical"', 1))
    return n


NP_KEYS = [('공모 주제', r'공모\s?주제|공모\s?내용|공모\s?분야|주\s?제'), ('참가 자격', r'응모\s?자격|참가\s?자격|참여\s?대상|공모\s?대상|응모\s?대상|지원\s?자격'),
           ('제출물·규격', r'제출\s?(?:서류|물|방법)|출품\s?(?:규격|형식|방법)|작품\s?규격|분\s?량|형\s?식'), ('접수', r'접수\s?(?:방법|기간)|응모\s?방법|제출\s?처'),
           ('시상', r'시상\s?(?:내역|내용|규모)?|상\s?금|포\s?상'), ('발표', r'(?:결과\s?)?발\s?표(?:\s?일)?|수상자\s?발표'), ('심사 기준', r'심사\s?(?:기준|방법)')]
NP_NAV = re.compile(r'콘테스트코리아|인기검색어|대외활동|로그인|회원가입|전체현황|바로가기|공유하기|스크랩|조회수|목록|이전글|다음글|Copyright|개인정보|씽굿|링커리어|위비티|올콘')
_NP_ALL = '|'.join(r for _, r in NP_KEYS)


_CFG = os.path.join(HERE, 'config.json')   # {"kakao_js_key": ""} — 카카오 JS 키가 생기면 여기에(공개되는 키라 저장소에 있어도 됨)
KAKAO_JS = (json.load(open(_CFG, encoding='utf-8')).get('kakao_js_key') or '').strip() if os.path.exists(_CFG) else ''
# 톡방·커뮤니티 채널 (2026-10-19): config.json community_links = [{name, label, banner, url, icon, on}] — 카톡 오픈채팅·라인·밴드·텔레그램을 켜고 끄기만 하면 됨
COMM_LINKS = [x for x in (json.load(open(_CFG, encoding='utf-8')).get('community_links') or [] if os.path.exists(_CFG) else []) if x.get('on') and x.get('url')]


CL_CSS = ('<style>.ft-c{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.cl-b{display:inline-flex;align-items:center;min-height:40px;padding:6px 14px;border-radius:999px;background:#fee500;color:#191919;font-weight:700;text-decoration:none;font-size:14px}'
          '.cl-ban{display:flex;align-items:center;gap:6px;margin:8px 0;padding:10px 14px;border-radius:12px;background:#fff9c4;border:1px solid #fde047;color:#422006;font-weight:700;text-decoration:none;font-size:14px}</style>')


def comm_btns(cls='cl-b'):
    return ''.join(f'<a class="{cls}" href="{E(x["url"])}" target="_blank" rel="noopener"' + (f' style="background:{E(x["bg"])};color:{E(x.get("fg", "#fff"))}"' if x.get('bg') else '') + f'>{E(x.get("label") or (x.get("icon", "") + " " + x["name"]))}</a>' for x in COMM_LINKS)   # bg·fg: 채널 색(없으면 카톡 노랑)


def comm_banner():
    return ''.join(f'<a class="cl-ban" href="{E(x["url"])}" target="_blank" rel="noopener">{E(x.get("icon", "💬"))} {E(x.get("banner") or x["name"])}</a>' for x in COMM_LINKS[:2])


def share_bar(t, x='', en=False):
    """공유 버튼 줄 HTML (assets/share.js). t=제목, x=공유 문구. 카카오톡 버튼은 KAKAO_JS 가 있을 때만 보임."""
    L = ('Share', 'Share…', 'KakaoTalk', '🔗 Copy link', 'Naver Blog', 'BAND') if en else ('공유', '공유하기', '카카오톡', '🔗 링크 복사', '네이버 블로그', '밴드')
    return (f'<div class="shr" data-t="{E(t)}" data-x="{E(x or t)}"' + (f' data-k="{E(KAKAO_JS)}"' if KAKAO_JS else '') + (' data-en="1"' if en else '') + f'><b>📤 {L[0]}</b>'
            f'<button data-s="native">{L[1]}</button><button data-s="kakao"' + ('' if KAKAO_JS else ' hidden') + f'>{L[2]}</button><button data-s="copy">{L[3]}</button>'
            f'<button data-s="nblog">{L[4]}</button><button data-s="band">{L[5]}</button><button data-s="x">X</button><button data-s="fb">Facebook</button></div><script defer src="/assets/share.js?v=2"></script>')


def notice_points(cid):
    """공고 원문에서 「항목: 내용」 꼴만 항목당 한 줄(110자까지). 못 찾으면 빈 목록(지어내지 않음)."""
    f = os.path.join(HERE, 'txt', f'{cid}.txt')
    if not os.path.exists(f):
        return []
    t = re.sub(r'\s+', ' ', html.unescape(html.unescape(open(f, encoding='utf-8', errors='ignore').read()))).replace('\xa0', ' ')
    out, used = [], set()
    for lab, rx in NP_KEYS:
        for m in re.finditer(rf'(?:^|[\s■□▶●○◆◇※\-·•\d\.\)])(?:{rx})\s*[:：]\s*(.{{8,140}}?)(?=\s(?:[■□▶●○◆◇※]|\d+\.\s|(?:{_NP_ALL})\s*[:：])|$)', t):
            v = m.group(1).strip(' -·•,')
            if NP_NAV.search(v) or len(v) < 8 or v in used:
                continue
            out.append((lab, v[:110] + ('…' if len(v) > 110 else ''))); used.add(v)
            break
    return out


def og_card(c):
    """공모전 공유 미리보기 카드 1200×630 (제목·마감일·상금·분야·브랜드). 날짜(D-day)는 넣지 않아 매일 다시 그리지 않음 — 내용이 바뀔 때만 새로."""
    from PIL import Image, ImageDraw
    import widget as W
    key = hashlib.md5(json.dumps([c['title'], c['end'], c.get('prize'), c['tags'][:2], c.get('org')], ensure_ascii=False).encode()).hexdigest()[:8]
    rel = f'/og/c/{c["id"]}-{key}.jpg'
    f = os.path.join(ROOT, rel.strip('/').replace('/', os.sep))
    if os.path.exists(f):
        return rel
    os.makedirs(os.path.dirname(f), exist_ok=True)
    for old in os.listdir(os.path.dirname(f)):
        if old.startswith(c['id'] + '-'):
            os.remove(os.path.join(os.path.dirname(f), old))
    im = Image.new('RGB', (1200, 630), (246, 245, 253)); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 1200, 10], fill=(109, 40, 217))
    dr.text((70, 60), ' · '.join(c['tags'][:2]) + ' 공모전', font=W._font(34, True), fill=(109, 40, 217))
    lines = W._wrap(dr, c['title'], W._font(60, True), 1060, 3)
    y = 130
    for l in lines:
        dr.text((70, y), l, font=W._font(60, True), fill=(30, 27, 75)); y += 78
    y += 20
    dr.rounded_rectangle([70, y, 470, y + 80], 20, fill=(225, 29, 72))
    dr.text((270, y + 40), f'마감 {int(c["end"][5:7])}월 {int(c["end"][8:10])}일', font=W._font(40, True), fill=(255, 255, 255), anchor='mm')
    if c.get('pv'):
        dr.rounded_rectangle([500, y, 1130, y + 80], 20, fill=(255, 246, 224))
        dr.text((815, y + 40), W._fit(dr, '상금 ' + re.sub(r'\s+', ' ', c['prize']), W._font(38, True), 600), font=W._font(38, True), fill=(180, 83, 9), anchor='mm')
    dr.rectangle([0, 540, 1200, 630], fill=(109, 40, 217))
    dr.text((70, 585), '루리의 줍줍', font=W._font(40, True), fill=(255, 255, 255), anchor='lm')
    dr.text((1130, 585), '자격·제출물·공식 공고 정리 · sungprofile.cloud', font=W._font(28), fill=(237, 233, 254), anchor='rm')
    im.save(f, 'JPEG', quality=82, optimize=True)
    return rel


def c_insight(c, live):
    """공모전마다 숫자가 다른 루리 분석 + 같은 분야 비교표. 공고 원문을 옮기지 않고 우리 데이터로 계산한 것만."""
    n = dday(c['end'])[0]
    tag = c['tags'][0]
    same = [x for x in live if tag in x['tags'] and x['id'] != c['id']]
    L = []
    if same:
        early = sum(1 for x in same if x['end'] < c['end'])
        L.append(f'지금 접수 중인 {tag} 공모전은 이것 말고 {len(same)}건이 더 있고, 이 공모전은 ' + ('가장 먼저 마감해요.' if early == 0 else '가장 늦게 마감하는 편이라 준비할 시간이 넉넉해요.' if early >= len(same) * .8 else f'그중 {early + 1}번째로 마감이 빨라요.'))
    pv = [x['pv'] for x in same if x.get('pv')]
    if c.get('pv') and pv:
        big = sum(1 for v in pv if v > c['pv'])
        med = sorted(pv)[len(pv) // 2]
        L.append(f'상금은 {won_txt(c["pv"])}로, 같은 분야에서 상금이 숫자로 나온 {len(pv)}건 중 {big + 1}번째로 커요. 이 분야 상금 중간값({won_txt(med)})보다 ' + ('큰 편이에요.' if c['pv'] > med else '작은 편이라, 경쟁이 덜할 수 있어요.' if c['pv'] < med else '딱 중간이에요.'))
    elif not c.get('pv'):
        L.append('상금이 숫자로 정리되지 않은 공모전이에요. 상장·기념품만 주는지, 부상이 따로 있는지 공고에서 확인해 보세요.')
    if c.get('start'):
        try:
            tot = (datetime.date.fromisoformat(c['end']) - datetime.date.fromisoformat(c['start'])).days + 1
            L.append(f'접수 기간은 모두 {tot}일' + (f'이고 오늘 기준 {n}일 남았어요.' if n >= 0 else '이었어요.'))
        except Exception:
            pass
    if n >= 2:   # 공모전마다 다른 준비 여유(제목 포함 문장 — 숫자만 다른 문장은 고유 본문으로 치지 않음)
        we = sum(1 for k in range(1, n + 1) if (TODAY + datetime.timedelta(days=k)).weekday() == 5)
        L.append(f'「{c["title"][:40]}」 마감({ddot(c["end"])[5:]})까지 준비에 쓸 수 있는 토요일은 {we}번이에요.' + (' 주말 하루 안에 초안을 끝내는 일정이 현실적이에요.' if we <= 1 else ' 첫 주말에 기획, 마지막 주말에 마무리하는 식으로 나눠 보세요.'))
    if c.get('org') and c['org'] not in ('공고 참조', ''):
        L.append(f'주최는 {c["org"][:40]}이고, ' + (f'{c["region"]} 지역 공모전이에요. ' if c.get('region') else '') + f'{"·".join(c["tags"][:2])} 분야로 분류했어요.')
    el = c.get('elig') or ''
    for pat, note in ELIG_NOTE:
        if re.search(pat, el):
            L.append(note)
            break
    if c.get('effort') in EFFORT_NOTE:
        L.append(f'제출물은 「{c["effort"]}」이에요. ' + EFFORT_NOTE[c['effort']])
    if c.get('fee'):
        L.append(f'참가비가 있는 공모전이에요({c["fee"]:,}원). 주최 기관이 맞는지 한 번 더 확인하세요.' if isinstance(c['fee'], int) else '참가비가 있는 공모전이에요. 주최 기관이 맞는지 한 번 더 확인하세요.')
    org_n = sum(1 for x in live if x['org'] == c['org'] and x['id'] != c['id']) if c['org'] not in ('공고 참조', '') else 0
    if org_n:
        L.append(f'같은 주최({c["org"]})가 지금 받는 공모전이 {org_n}건 더 있어요. 한 번에 같이 준비하면 시간을 아낄 수 있어요.')
    plan = ''
    if n >= 4:
        e = datetime.date.fromisoformat(c['end'])
        d1 = TODAY + datetime.timedelta(days=max(1, n // 3)); d2 = e - datetime.timedelta(days=max(1, n // 5)); d3 = e - datetime.timedelta(days=1)
        plan = (f'<h2>📅 추천 준비 일정 <small>루리 제안 · 공식 일정 아님</small></h2><p class="note">오늘({TODAY.month}/{TODAY.day})부터 마감일까지를 나눠 잡은 권장 일정이에요. 주최 측 공식 일정(발표·서류 제출 등)은 공고를 따르세요.</p><ul class="chk"><li>{d1.month}/{d1.day}까지: 요강 읽고 자격·제출물·분량 표시해 두기, 아이디어 3개 뽑기</li>'
                f'<li>{d2.month}/{d2.day}까지: 초안 완성하고 하루 묵힌 뒤 고치기</li><li>{d3.month}/{d3.day}까지: 파일 형식·이름 맞춰 제출 (마감일엔 접수 서버가 몰려요)</li></ul>')
    cmp_ = sorted(same, key=lambda x: (abs((datetime.date.fromisoformat(x['end']) - datetime.date.fromisoformat(c['end'])).days), -(x.get('pv') or 0)))[:5]
    tb = ''
    if cmp_:
        rows = ''.join(f'<tr><td><a href="/c/{x["id"]}/">{E(x["title"][:40])}</a></td><td>{E(won_txt(x["pv"]) if x.get("pv") else "상금 공고 확인")}</td><td>{ddot(x["end"])[5:]} 마감</td><td>{E((x.get("effort") or "공고 확인"))}</td></tr>' for x in cmp_)
        tb = (f'<h2>🔍 마감이 비슷한 {E(tag)} 공모전 비교</h2><table class="info cmp"><tr><th>공모전</th><th>상금</th><th>마감</th><th>제출물</th></tr>'
              f'<tr class="on"><td>이 공모전</td><td>{E(won_txt(c["pv"]) if c.get("pv") else "상금 공고 확인")}</td><td>{ddot(c["end"])[5:]} 마감</td><td>{E(c.get("effort") or "공고 확인")}</td></tr>{rows}</table>')
    return (f'<h2>🧐 루리 분석</h2><p>{" ".join(E(x) for x in L)}</p>' if L else '') + plan + tb


def detail(c, live):
    if c['id'] in DUP:   # 같은 공고가 여러 곳에서 수집됨 → 검색 제외 + 대표 공고로 안내(주소는 유지)
        r_ = DUP[c['id']]
        page(f'/c/{c["id"]}/', f'{c["title"][:40]} (같은 공고)', '같은 공모전의 대표 페이지로 합쳐졌어요.',
             f'<p class="bc"><a href="/">홈</a> › 공모전</p><h1>{E(c["title"])}</h1><p>이 공모전은 같은 공고가 여러 곳에서 수집돼 대표 페이지 하나로 합쳤어요.</p>'
             f'<p><a class="lab-cta" href="/c/{r_}/"><b>🏆 대표 공고 페이지로 가기</b><span>마감·자격·제출물·공식 링크 →</span></a></p><script>location.replace("/c/{r_}/")</script>',
             [('루리의 줍줍', '/'), (c['title'][:30], f'/c/{c["id"]}/')], noindex=True)
        return
    n, dd = dday(c['end'])
    main_tag = c['tags'][0]
    tips = ''.join(f'<li>{E(t)}</li>' for tag in c['tags'][:2] for t in TIPS[tag])
    sim = [x for x in live if x['id'] != c['id'] and main_tag in x['tags']][:6]
    simh = ''.join(card(x) for x in sim)
    status = ('<p class="warn">접수가 마감된 공모전입니다. 같은 분야의 진행 중 공모전을 아래에서 확인하세요.</p>' if n < 0
              else f'<p class="lead"><span class="{"d u3" if n <= 3 else "d hot" if n <= 7 else "d"}">{dd}</span> {ddot(c["end"])} 마감</p>')
    ruri = (say('sad', '아쉽지만 이건 마감됐어요. 아래 진행 중인 공모전을 봐 주세요!') if n < 0 else
            say('surprise', f'마감까지 <b>{dd}</b>! 오늘 바로 요강부터 확인해요.') if n <= 3 else
            say('thumbsup', f'상금 <b>{E(c["prize"])}</b>! 응모 자격만 맞으면 도전해 볼 만해요.') if c['pv'] else
            say('smile', '공식 공고에서 제출 양식과 파일 형식을 먼저 확인해 주세요!'))
    period = (ddot(c['start']) + ' ~ ' if c['start'] else '~ ') + ddot(c['end'])
    # 2026-10-19 사용자 개선 지시: 자격·지역·마감 시각·제출물·상금·공식 링크·확인할 것. 모르는 값은 채우지 않고 「공식 공고 확인 필요」
    NEED = '공식 공고 확인 필요'
    v_ = lambda x: x if (x and str(x).strip() not in ('', '-', '공고 참조', '공고 확인')) else NEED
    sub = ' · '.join(x for x in (c.get('effort'), c.get('submit')) if x)
    rows = [('주최·주관', v_(c['org'])), ('분야', c['field'] or ', '.join(c['tags'])), ('응모 자격', v_(c['elig'])), ('지역 제한', c.get('region') or ('있음 — ' + NEED if re.search(r'거주|도민|시민|군민|구민|관내|재학|재직', c.get('elig') or '') else '따로 적힌 제한 없음(공고 확인)')),
            ('접수 기간', period), ('마감 시각', NEED + ' (자동 정리 데이터에 시각이 없어요)'), ('제출물·제출 방식', v_(sub)), ('접수 방법', v_(c['ch'])), ('상금·혜택', v_(c['prize'])),
            ('참가비', (f'{c["fee"]:,}원' if isinstance(c.get('fee'), int) and c['fee'] > 1 else '있음 — ' + NEED) if c.get('fee') else '없음으로 정리됨(공고 확인)')]
    tb = ''.join(f'<tr><th>{k}</th><td{" class=need" if NEED in str(v) else ""}>{E(v)}</td></tr>' for k, v in rows)
    todo = ['마감 시각(예: 18시·23시 59분)과 접수 마감이 「도착 기준」인지']
    if v_(c['elig']) == NEED:
        todo.append('응모 자격(나이·신분·지역)')
    if not sub:
        todo.append('제출물 종류·분량·파일 형식')
    if not c.get('pv'):
        todo.append('상금·부상 내용')
    if c.get('fee'):
        todo.append('참가비가 필요한 이유와 주최 기관이 맞는지')
    todo.append('1인당 응모 편수, 수상 발표일과 발표 방법')
    NPs = notice_points(c['id'])
    hh = HIST.get(c['id']) or {}
    _tf = os.path.join(HERE, 'txt', f'{c["id"]}.txt')
    FL = {'title': '제목', 'end': '마감일', 'prize': '상금', 'elig': '자격', 'link': '공고 링크'}
    hist_html = ('<p class="note">📝 정보 이력: 처음 수집 ' + (hh.get('first') or '-') + (' · 공고 원문 수집 ' + datetime.datetime.fromtimestamp(os.path.getmtime(_tf)).strftime('%Y-%m-%d %H:%M') if os.path.exists(_tf) else '')
                 + ''.join(f' · {x["d"]} 변경: ' + ', '.join(f'{FL[k]} 「{E(str(v[0])[:20])}」→「{E(str(v[1])[:20])}」' for k, v in x['f'].items()) for x in (hh.get('chg') or [])[-3:]) + ' (한국 시간)</p>')
    np_html = ('<h2>📄 공고에서 확인한 핵심</h2><table class="info np">' + ''.join(f'<tr><th>{E(k)}</th><td>{E(v)}</td></tr>' for k, v in NPs) + '</table><p class="note">공고 원문의 항목을 그대로 옮긴 거예요(자동 추출이라 일부만 보일 수 있어요). 전체 내용은 공식 공고에서 확인하세요.</p>') if NPs else ''
    chk_need = '<h2>✅ 공식 공고에서 꼭 확인할 것</h2><ul class="chk">' + ''.join(f'<li>{E(t)}</li>' for t in todo) + '</ul>'
    catl = ' · '.join(f'<a href="/cat/{SLUG[t]}/">{E(t)}</a>' for t in c['tags'])
    org = c['org'] if c['org'] != '공고 참조' else '주최 기관'
    summary = (f'「{c["title"]}」은 {org}에서 진행하는 {", ".join(c["tags"])} 분야 공모전으로 {ddot(c["end"])}까지 접수합니다. '
               + (f'응모 자격은 "{c["elig"]}"이고 ' if c.get('elig') else '응모 자격은 공식 공고에서 확인이 필요하고 ') + (f'상금은 {c["prize"]}입니다. ' if c.get('pv') else '상금은 공식 공고에서 확인하세요. ') +
               f'접수 방법은 {c["ch"]}이고, 마감 시각과 제출 양식·파일 형식은 공식 공고에서 먼저 확인하세요.')
    body = f'''<p class="bc"><a href="/">홈</a> › <a href="/cat/{SLUG[main_tag]}/">{E(main_tag)}</a></p>
<section class="dh" data-c="{SLUG[main_tag]}"><span class="ic big">{CAT_ICON[main_tag]}</span><h1>{E(c["title"])}</h1>{status}</section>
{ruri}
<a class="shot" href="{E(c["link"])}" target="_blank" rel="noopener nofollow">{f'<img src="/assets/shots/{c["id"]}.webp" width="640" height="400" alt="{E(c["title"])} 공식 공고 화면" fetchpriority="high">' if c.get('th') else f'<img class="ruri" src="/assets/ruri/thumbsup.webp" width="300" height="415" alt="루리">'}<span>공식 공고 페이지 열기 →</span></a>
<div class="panel"><table class="info">{tb}</table>
<a class="btn" href="{E(c["link"])}" target="_blank" rel="noopener nofollow">공식 공고·접수 페이지 열기 →</a><p class="note">링크는 주최 측 공고(또는 접수) 페이지예요. 공고가 바뀌었을 수 있으니 접수 전 다시 확인하세요.</p></div>
{chk_need}
{share_bar(c['title'], f'「{c["title"]}」 {ddot(c["end"])[5:]} 마감' + (f' · {c["prize"]}' if c.get('pv') else '') + ' — 자격·제출물 정리')}{comm_banner()}
<div class="my-acts" data-id="c:{c["id"]}" data-title="{E(c["title"])}" data-end="{c["end"]}"></div>
<h2>한눈에 보기</h2><p>{E(summary)}</p>
{np_html}{c_insight(c, live)}
{('<section id="finder" data-id="' + c['id'] + '" data-v="' + TODAY.strftime('%m%d') + '"></section><script defer src="/assets/finder/finder.js?v=3"></script>') if c in live else ''}
<h2>응모 전 체크리스트</h2><ul class="chk">{tips}</ul>
{'<a class="lab-cta" href="/lab/#diag"><b>🏆 이런 공모전 수상작은 어떻게 생겼을까?</b><span>수상작 300여 개를 분석한 당선 공식과 내 문구 진단 →</span></a>' if re.search(r'슬로건|표어|네이밍|명칭|캐치프레이즈|삼행시|N행시|이행시|애칭', c['title']) else ''}
{hist_html}<p class="note">분야: {catl}. 상금·자격·기간은 공고 원문에서 자동으로 정리한 값이라 오차가 있을 수 있습니다. 최종 기준은 주최 측 공식 공고입니다.</p>
{f'<section id="cm-crew" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section><section id="cm-teams" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section><section id="cm-board" data-contest="{c["id"]}" data-title="{E(c["title"])}"></section>' if COMM_API else ''}
<h2>같은 분야 진행 중 공모전</h2><ul class="list">{simh or '<li class="empty">진행 중인 같은 분야 공모전이 없어요.</li>'}</ul>'''
    # 2026-10-19: 접수 공고는 실제 행사가 아니라 Event 대신 WebPage(데이터와 맞는 유형만)
    ld = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': c['title'], 'description': summary, 'inLanguage': 'ko',
          'dateModified': ((HIST.get(c['id']) or {}).get('chg') or [{'d': (HIST.get(c['id']) or {}).get('first') or TODAY.isoformat()}])[-1]['d'],
          'about': {'@type': 'Thing', 'name': c['title'], 'url': c['link']}, 'publisher': {'@type': 'Organization', 'name': NAME, 'url': SITE + '/'}}
    desc = f'{c["title"]} — {org} 주최, {ddot(c["end"])} 마감, 상금 {c["prize"]}. 응모 자격·접수 방법·체크리스트 정리.'
    md_ = c['end'][5:].replace('-', '/').lstrip('0').replace('/0', '/')
    pz = re.sub(r'\s+', ' ', (c.get('prize') or '')).strip()
    yr_ = '' if re.search(r'20\d\d', c['title']) else f' {c["end"][:4]}'
    _tail = [f"{c['end'][5:7].lstrip('0')}.{c['end'][8:10]} 마감"] + ([pz[:20]] if pz and pz not in ('공고 확인', '공고 참조', '-') else []) + ([c['effort']] if c.get('effort') else [])
    while len(_tail) > 1 and len(c['title'] + yr_) + 3 + len(' · '.join(_tail)) > 58:
        _tail.pop()   # 검색 결과에서 잘리지 않게(브랜드 포함 70자 안쪽): 제출물 → 상금 순으로 뺀다
    _nm = c['title'] + yr_
    if len(_nm) + 3 + len(_tail[0]) > 58:
        _nm = _nm[:58 - 4 - len(_tail[0])].rstrip() + '…'
    seo_t = f"{_nm} | {' · '.join(_tail)}"   # 2026-10-19 자연 유입: 이름 맨 앞 + 연도·마감·상금·제출물
    page(f'/c/{c["id"]}/', seo_t, desc[:155], body,
         [('루리의 줍줍', '/'), (main_tag, f'/cat/{SLUG[main_tag]}/'), (c['title'], f'/c/{c["id"]}/')], ld, noindex=n < 0 or c not in live, og=og_card(c) if c in live else None)
    GONE[f'/c/{c["id"]}/'] = [c['title'], f'/cat/{SLUG[main_tag]}/', f'{main_tag} 공모전', c['end']]


def listing_js(cat=''):
    return '''<script>
(function(){var IC=%s,SL=%s;var $=function(i){return document.getElementById(i)};var items=[],cat=%s,PAGE=40,shown=PAGE;
var n=new Date(Date.now()+324e5),LATE=n.getUTCHours()>=18,T=Math.round(Date.UTC(n.getUTCFullYear(),n.getUTCMonth(),n.getUTCDate())/864e5);/* 한국 시간 기준 */
function dn(s){var p=s.split('-');return Math.round(Date.UTC(+p[0],p[1]-1,+p[2])/864e5)}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function render(){var q=$('q').value.trim().toLowerCase(),due=+$('due').value||0,s=$('sort').value;
function sc(i){var s=i.pv?(Math.log(i.pv)/Math.LN10-4)*1.2:0;s+=(i.left>=2&&i.left<=14)?2:i.left<=30?1:0;if(i.left<=0)s-=3;if(i.effort)s+=1;return s}
var r=items.filter(function(i){return i.left>=(LATE?1:0)&&(!cat||i.tags.indexOf(cat)>=0)&&(!due||i.left<=due)&&(!q||i.hay.indexOf(q)>=0)});
r.sort(s==='prize'?function(a,b){return b.pv-a.pv||a.left-b.left}:s==='end'?function(a,b){return a.left-b.left||b.pv-a.pv}:function(a,b){return sc(b)-sc(a)||a.left-b.left});
$('cnt').textContent='진행 중 공모전 '+r.length+'건';var ul=$('list');ul.textContent='';
if(!r.length){var li=el('li','empty');li.innerHTML='<img src="/assets/ruri/sad_s.webp" width="56" height="77" alt=""><p>조건에 맞는 공모전이 없어요. 검색어를 바꿔 볼까요?</p>';ul.appendChild(li)}
r.slice(0,shown).forEach(function(i){var li=el('li'),a=el('a','card');a.href='/c/'+i.id+'/';a.dataset.c=SL[i.tags[0]]||'etc';if(i.th){a.className+=' has-th';var im=el('img','th');im.src='/assets/shots/'+i.id+'.webp';im.loading='lazy';im.alt='';a.appendChild(im)}a.appendChild(el('span','ic',IC[i.tags[0]]||'🧩'));var cb=el('div','cb'),top=el('div','top');top.appendChild(el('h3','t',i.title));
top.appendChild(el('span','d'+(i.left<=3?' u3':i.left<=7?' hot':''),i.left?'D-'+i.left:'D-DAY'));cb.appendChild(top);cb.appendChild(el('p','o',i.org));cb.appendChild(el('p','pd','접수 '+(i.start?i.start.slice(5).replace('-','.')+' ~ ':'~ ')+i.end.slice(5).replace('-','.')));
var tg=el('div','tags');if(i.effort)tg.appendChild(el('span','ez e0',i.effort));if(i.pv)tg.appendChild(el('span','pz','🏆 '+i.prize));i.tags.forEach(function(x){tg.appendChild(el('span','tg',x))});cb.appendChild(tg);a.appendChild(cb);li.appendChild(a);ul.appendChild(li)});
$('more').hidden=r.length<=shown}
['q','due','sort'].forEach(function(i){$(i).addEventListener('input',function(){shown=PAGE;render()})});$('more').onclick=function(){shown+=PAGE;render()};
fetch('/data.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(d){items=d.items.map(function(i){i.left=dn(i.end)-T;i.hay=(i.title+' '+i.org+' '+i.field+' '+i.tags.join(' ')).toLowerCase();return i});render()}).catch(function(){var u=document.querySelector('.list');if(u)u.insertAdjacentHTML('beforebegin','<p class="note">목록을 새로 불러오지 못해 마지막으로 만든 목록을 보여 드려요. 마감 여부는 공식 공고로 확인해 주세요.</p>')});
})();</script>''' % (json.dumps(CAT_ICON, ensure_ascii=False), json.dumps(SLUG, ensure_ascii=False), json.dumps(cat, ensure_ascii=False))


TOOLBAR = '''<div class="bar"><input type="search" id="q" placeholder="공모전, 주최, 키워드 검색" aria-label="검색">
<select id="due" aria-label="마감"><option value="">마감 전체</option><option value="7">7일 이내</option><option value="30">30일 이내</option></select>
<select id="sort" aria-label="정렬"><option value="rec">추천순</option><option value="end">마감 임박순</option><option value="prize">상금 큰 순</option></select></div>
<p class="cnt" id="cnt"></p>'''


# 참여 난이도 배지 (공모전 세션 합의: "설문 5분", "댓글 1줄" 처럼 쉬운 정도를 앞에)
EASY = {'댓글 이벤트': '댓글 1줄', '설문': '설문 5분', '퀴즈': '퀴즈 풀기', '폼 응모': '폼 1분', '댓글+폼': '댓글+폼', '추첨 경품': '응모만',
        '친구 태그': '친구 태그', '스토리 공유': '스토리 공유', '캡처 인증': '캡처 인증', '구매 인증': '구매 필요', '지역 한정': '지역 한정',
        '이벤트': '참여형', 'SNS 이벤트': 'SNS 참여'}
EASY_RANK = {'댓글 1줄': 0, '폼 1분': 0, '응모만': 0, '설문 5분': 1, '퀴즈 풀기': 1, '댓글+폼': 1, '참여형': 2, 'SNS 참여': 2,
             '친구 태그': 2, '스토리 공유': 3, '캡처 인증': 3, '지역 한정': 4, '구매 필요': 5}


def ev_card(e):
    n, dd = dday(e['end'])
    ch = f'<span class="tg">{E(e["ch"])}</span>' if e['ch'] else ''
    ez = e.get('effort') or EASY.get(e['type'], e['type'])
    return (f'<li><a class="card" data-c="event" href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><span class="ic">🎁</span><div class="cb"><div class="top"><h3 class="t">{E(e["title"])}</h3>'
            f'<span class="d{" u3" if n <= 3 else ""}">{dd}</span></div><p class="o">{E(e["org"] or "공식 계정")} · ~{ddot(e["end"])}</p>'
            f'<div class="tags"><span class="ez e{EASY_RANK.get(ez, 2)}">{E(ez)}</span>{ch}</div></div></a></li>')


# ---- 청약·신청 (공모전 세션이 data/apply.jsonl 에 쌓음: title, org, kind, start, end, url, source, verified) ----
APPLY_KIND = {'apt': ('아파트 청약', '🏠'), 'rent': ('공공임대', '🏘️'), 'ipo': ('공모주', '📈'), 'grant': ('지원금 신청', '💰')}


def apply_kind(k):
    k = (k or '').lower()
    for key, v in APPLY_KIND.items():
        if key in k or v[0] in k:
            return v
    if any(w in k for w in ('청약', '분양')):
        return APPLY_KIND['apt']
    if any(w in k for w in ('임대', '행복주택', '매입')):
        return APPLY_KIND['rent']
    if '공모주' in k or '상장' in k:
        return APPLY_KIND['ipo']
    return ('신청', '📝')


def load_apply():
    fp = os.path.join(DATA, 'apply.jsonl')
    mp = os.path.join(HERE, 'manual_apply.jsonl')  # 사이트 쪽 확인분(정본은 공모전 세션 apply.jsonl)
    lines = (open(fp, encoding='utf-8').readlines() if os.path.exists(fp) else []) + (open(mp, encoding='utf-8').readlines() if os.path.exists(mp) else [])
    out, seen = [], set()
    for l in lines:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if not r.get('title') or not (r.get('end') or r.get('always')) or r.get('closed'):
            continue
        end = r.get('end_override') or r.get('end') or '2099-12-31'  # always: 상시 신청
        try:
            if dday(end)[0] < 0:
                continue
        except ValueError:
            continue
        aid = str(r['id']) if r.get('id') else 'A' + hashlib.md5((r['title'] + '|' + r.get('url', '')).encode('utf-8')).hexdigest()[:8]
        if aid in seen:
            continue
        seen.add(aid)
        nm, ic = apply_kind(r.get('kind'))
        out.append({'id': aid, 'title': P.clean(r['title'])[:90], 'org': P.clean(r.get('org', ''))[:40] or '공고 참조', 'kind': nm, 'icon': ic, 'kk': r.get('kind') or ('apt' if re.search(r'아파트|분양|자이|힐스테이트|푸르지오|래미안|e편한|롯데캐슬|하늘채|더샵|아이파크|위브|포레나|센트레빌|리슈빌|공공분양', r['title']) else 'rent' if re.search(r'임대|전세|월세|행복주택|매입', r['title']) else 'grant'),
                    'start': r.get('start', ''), 'end': end, 'url': r.get('url', ''), 'source': r.get('source', ''), 'verified': bool(r.get('verified')),
                    'always': bool(r.get('always')), 'region': P.clean(r.get('region', ''))[:20], 'target': P.clean(r.get('target', ''))[:80], 'benefit': P.clean(r.get('benefit', ''))[:80],
                    'how': P.clean(r.get('how', ''))[:60], 'income': P.clean(r.get('income', ''))[:30], 'age_min': r.get('age_min'), 'age_max': r.get('age_max')})
    out.sort(key=lambda a: (a['end'], a['title']))
    return out


def ap_card(a):
    n, dd = dday(a['end'])
    v = '<span class="tg">확인됨</span>' if a['verified'] else ''
    return (f'<li><a class="card" data-c="apply" href="/a/{a["id"]}/"><span class="ic">{a["icon"]}</span><div class="cb"><div class="top"><h3 class="t">{E(a["title"])}</h3>'
            f'<span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span></div><p class="o">{E(a["org"])} · ~{ddot(a["end"])}</p>'
            f'<div class="tags"><span class="ez e1">{E(a["kind"])}</span>{v}</div></div></a></li>')


APPLY_INTRO = '''<p>아파트 청약, 공공임대, 공모주 청약, 지원금 신청처럼 <b>기간 안에 신청만 하면 되는 기회</b>를 모았어요. 신청은 반드시 공식 사이트에서 하세요.</p>
<h2>어디서 신청하나요?</h2><ul class="chk"><li><b>아파트 청약</b>: 한국부동산원 청약홈(applyhome.co.kr). 청약통장 가입 기간·납입 횟수가 순위를 가릅니다.</li>
<li><b>공공임대</b>: LH청약플러스(apply.lh.or.kr), SH·GH 등 지역 공사. 소득·자산 기준을 먼저 확인하세요.</li>
<li><b>공모주</b>: 증권사 앱에서 청약. 증거금(신청금액의 50% 안팎)이 필요하고, 배정 후 남은 돈은 환불됩니다.</li>
<li><b>지원금</b>: 정부24·복지로·지자체 홈페이지. 대부분 본인인증 후 온라인으로 신청합니다.</li></ul>
<p class="note">정보는 공고를 바탕으로 정리했으며, 자격·일정은 바뀔 수 있으니 공식 공고를 기준으로 하세요. 투자·청약 결과에 대한 판단은 본인 책임입니다.</p>'''


def ap_insight(a, aps):
    """지원금 상세 고유 해설: 같은 지역·같은 종류 진행 중 건수, 남은 기간, 정리된 조건 해석."""
    n = dday(a['end'])[0]
    sl = sido_of(a)
    nm = next((x[1] for x in SIDO if x[0] == sl), '')
    same = [x for x in aps if x['id'] != a['id'] and sl and sido_of(x) == sl]
    kind = [x for x in aps if x['id'] != a['id'] and x['kind'] == a['kind']]
    L = []
    if a.get('always'):
        L.append('상시 신청 사업이라 마감 걱정은 없지만, 예산이 떨어지면 일찍 끝날 수 있어요.')
    elif a.get('start'):
        try:
            tot = (datetime.date.fromisoformat(a['end']) - datetime.date.fromisoformat(a['start'])).days + 1
            L.append(f'신청 기간은 모두 {tot}일이고 ' + ('오늘이 마감일이에요.' if n == 0 else f'{n}일 남았어요.'))
        except Exception:
            pass
    if a.get('age_min') or a.get('age_max'):
        L.append(f'나이 조건(만 {a.get("age_min") or ""}~{a.get("age_max") or ""}세)은 보통 공고일 기준이라, 생일이 가까우면 기준일을 꼭 확인하세요.')
    if a.get('income'):
        L.append(f'소득 조건은 「{a["income"]}」이에요. 기준 중위소득 %로 적힌 경우 가구원 수에 따라 금액이 달라져요.')
    if nm and same:
        L.append(f'지금 {nm}에서 신청할 수 있는 공고가 {len(same)}건 더 있어요.')
    if kind:
        L.append(f'같은 종류({a["kind"]}) 진행 중 공고는 전국 {len(kind)}건이에요.')
    links = ([(f'/apply/r/{sl}/', f'{nm} 지원금·청약 모아 보기')] if sl else []) + [('/apply/', '전체 지원금·청약 일정'), ('/apply/recommend/', '청약 가점 추천')]
    return (f'<h2>🧐 루리 분석</h2><p>{" ".join(E(x) for x in L)}</p>' if L else '') + rel_block(r'지원금|청년|월세|청약', links)


_RX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'review_extra.json')  # 평론 원고(연구 세션이 추가, 2026-10-19)
INVEST_RE = r'투자|주식|증시|코인|비트코인|ETF|금리|환율|부동산|집값|종목|목표가'


def load_reviews():
    import markdown
    if not os.path.exists(_RX):
        return []
    try:
        raw = json.load(open(_RX, encoding='utf-8'))
    except Exception as e:
        print('review_extra.json 읽기 실패', e)
        return []
    out = []
    for r in raw if isinstance(raw, list) else []:
        slug = re.sub(r'[^0-9A-Za-z가-힣_-]', '', str(r.get('slug', '')))[:60]
        if not slug or not r.get('title') or not r.get('body_md') or r.get('draft'):
            continue
        h = markdown.markdown(html.escape(r['body_md'].replace('\r\n', '\n'), quote=False), extensions=['extra'])
        # 「루리의 시선」 제목부터 다음 h2 전까지를 의견 상자로 감싼다 (사실·의견 구분 표시)
        h = re.sub(r'(<h2>[^<]*루리의 시선[^<]*</h2>)(.*?)(?=<h2>|$)', r'<div class="rv-op"><p class="rv-tag">💭 의견 · 루리의 시선</p>\1\2</div>', h, flags=re.S)
        h = re.sub(r'<a href="(https?://)', r'<a rel="noopener" target="_blank" href="\1', h)
        kw = r.get('kw') or []
        kw = [kw] if isinstance(kw, str) else kw
        rel = []
        for x in r.get('related') or []:
            if isinstance(x, dict) and x.get('u'):
                rel.append((x['u'], x.get('t') or x['u']))
            elif isinstance(x, (list, tuple)) and x:
                rel.append((x[0], x[1] if len(x) > 1 else x[0]))
            elif isinstance(x, str):
                rel.append((x, x))
        out.append({'slug': slug, 'title': str(r['title'])[:90], 'date': str(r.get('date') or TODAY.isoformat())[:10], 'kw': [str(k) for k in kw][:8],
                    'desc': str(r.get('desc') or re.sub(r'<[^>]+>|\s+', ' ', h).strip()[:140]), 'html': h,
                    'src': [(x.get('t') or x.get('u'), x['u']) for x in r.get('sources') or [] if isinstance(x, dict) and str(x.get('u', '')).startswith('http')],
                    'rel': [(u, t) for u, t in rel if u.startswith('/') or u.startswith('http')],
                    'invest': bool(r.get('invest')) or bool(re.search(INVEST_RE, str(r['title']) + ' '.join(map(str, kw))))})
    out = [x for x in out if x['date'] <= TODAY.isoformat()]   # 날짜가 미래면 그날 공개
    out.sort(key=lambda x: (x['date'], x['slug']), reverse=True)
    return out


REVIEW_NOTE = '<p class="an-warn">📈 전망 정리·투자 권유 아님 — 기사·공식 자료에 나온 전망을 모은 글이에요. 특정 종목·상품을 권하지 않고, 투자 판단과 책임은 본인에게 있어요.</p>'


def review_pages():
    """/review/ 평론: 무슨 일 → 쟁점(찬반) → 나한테 뭐가 달라지나 → 남은 질문. 사실은 출처 링크, 의견은 「루리의 시선」 상자."""
    shutil.rmtree(os.path.join(ROOT, 'review'), ignore_errors=True)
    R = load_reviews()
    urls = ['/review/']
    for x in R:
        u = f'/review/{x["slug"]}/'
        src = ''.join(f'<li><a href="{E(su)}" rel="noopener" target="_blank">{E(st)}</a></li>' for st, su in x['src'])
        others = [y for y in R if y is not x][:4]
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/news/">이슈</a> › <a href="/review/">평론</a></p>'
                f'<article class="ssul rv"><p class="note">{E(kdate(x["date"]))} · 루리의 평론' + (' · ' + ' '.join(f'#{E(k)}' for k in x['kw']) if x['kw'] else '') + f'</p><h1>{E(x["title"])}</h1>'
                + (REVIEW_NOTE if x['invest'] else '') + x['html']
                + (f'<section class="rv-src"><h2>📰 사실 확인 출처</h2><ul>{src}</ul></section>' if src else '') + '</article>'
                + '<p class="note">사실 부분은 위 출처를 바탕으로 썼고, 「루리의 시선」은 운영자 의견이에요. 틀린 사실은 <a href="/contact/">문의</a>로 알려 주시면 고쳐요.</p>'
                + rel_block('', x['rel'] + [(f'/review/{y["slug"]}/', y['title']) for y in others] + [('/review/', '평론 전체 보기'), ('/news/', '오늘의 기사 확인 신호')]))
        page(u, x['title'], x['desc'], body, [('루리의 줍줍', '/'), ('평론', '/review/'), (x['title'], u)],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': x['title'], 'datePublished': x['date'], 'dateModified': x['date'],
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}, 'publisher': {'@type': 'Organization', 'name': '루리의 줍줍'},
              'keywords': ', '.join(x['kw']), 'citation': [su for _, su in x['src']]})
        urls.append(u)
    li = ''.join(f'<li><a class="card" data-c="guide" href="/review/{x["slug"]}/"><span class="ic">🖋️</span><div class="cb"><h3 class="t">{E(x["title"])}</h3><p class="o">{E(kdate(x["date"]))} · {E(x["desc"][:90])}</p></div></a></li>' for x in R) \
        or '<li class="empty"><p>첫 평론을 준비하고 있어요.</p></li>'
    page('/review/', '루리의 평론 — 오늘 이슈·정책·지원금 해설 칼럼', '오늘 뜬 이슈·정책·지원금·공모전 하나를 골라 무슨 일인지, 쟁점은 무엇인지, 나한테 뭐가 달라지는지, 남은 질문은 무엇인지 짚는 해설 칼럼.',
         '<p class="bc"><a href="/">홈</a> › <a href="/news/">이슈</a> › 평론</p><h1>🖋️ 루리의 평론</h1>'
         '<section class="pg-intro"><h2>평론은 이렇게 써요</h2><p>하루에 한 가지 이슈·정책·지원금·공모전을 골라 <b>무슨 일 → 쟁점(찬반 나란히) → 나한테 뭐가 달라지나 → 남은 질문</b> 순서로 짚어요. 사실은 기사·공식 자료 링크를 달고, 운영자 의견은 「💭 루리의 시선」 상자로 따로 표시해요. 투자 관련 글은 전망 정리일 뿐 투자 권유가 아니고, 정치인 비방·연예인 사생활은 다루지 않아요.</p></section>'
         f'<ul class="list">{li}</ul>' + rel_block('', [('/news/', '오늘의 기사 확인 신호'), ('/hot/', '핫이슈'), ('/mag/', '데일리 매거진')]),
         [('루리의 줍줍', '/'), ('평론', '/review/')], noindex=not R)
    return urls, R


def build_apply(aps):
    # 메인 루리 상담(청약·지원금)용 데이터 (2026-10-17)
    with open(os.path.join(ROOT, 'apply.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{k: a[k] for k in ('id', 'title', 'org', 'kind', 'icon', 'kk', 'start', 'end', 'always', 'region', 'target', 'benefit', 'how', 'income', 'age_min', 'age_max', 'url') if a.get(k) not in (None, '', False)} for a in aps], f, ensure_ascii=False, separators=(',', ':'))
    for a in aps:
        n, dd = dday(a['end'])
        period = (ddot(a['start']) + ' ~ ' if a['start'] else '~ ') + ddot(a['end'])
        tb = ''.join(f'<tr><th>{k}</th><td>{E(v)}</td></tr>' for k, v in
                     [x for x in [('구분', a['kind']), ('대상', a.get('target')), ('혜택', a.get('benefit')), ('지역', a.get('region')), ('나이', (f"만 {a['age_min'] or ''}~{a['age_max'] or ''}세" if a.get('age_min') or a.get('age_max') else '')),
                      ('소득 조건', a.get('income')), ('신청 방법', a.get('how')), ('주관', a['org']), ('신청 기간', '상시 신청' if a.get('always') else period), ('출처', a['source'] or '공식 공고')] if x[1]])
        btn = (f'<a class="btn" href="{E(a["url"])}" target="_blank" rel="noopener nofollow">공식 사이트에서 신청하기 →</a>' if a['url'] else '')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">청약·신청</a></p>
<section class="dh" data-c="apply"><span class="ic big">{a["icon"]}</span><h1>{E(a["title"])}</h1><p class="lead">{'<span class="d">상시</span> 지금 신청할 수 있어요' if a.get('always') else f'<span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span> {ddot(a["end"])} 마감'}</p></section>
<div class="my-acts" data-id="a:{E(a['id'])}" data-title="{E(a['title'])}" data-end="{'' if a.get('always') else a['end']}"></div>
{say('o_suit', f'신청 기간을 놓치지 마세요! 자격 조건은 <b>공식 공고</b>에서 꼭 확인해 주세요.')}
<div class="panel"><table class="info">{tb}</table>{btn}</div>
{share_bar(a['title'], f'「{a["title"]}」 ' + ('상시 신청' if a.get('always') else f'{ddot(a["end"])[5:]} 마감') + ' — 대상·신청처 정리')}{comm_banner()}{ap_insight(a, aps)}<h2>신청 전 확인할 것</h2><ul class="chk"><li>신청 자격(나이·소득·자산·거주지·무주택 여부)</li><li>필요 서류와 본인인증 수단</li><li>발표일과 계약·납부 일정</li></ul>'''
        _org = (a.get('org') or '').strip()[:14]
        _end = f' · {ddot(a["end"])[5:]} 마감' if a.get('end') and not a.get('always') else ''
        _og = (a.get('org') or '').strip().split()[-1][:10] if (a.get('org') or '').strip() else ''   # 제목용 기관명은 마지막 단위(과·국)만
        _t = f'{a["title"][:40]} {YR}' + (f' — {_og}' if _og else '') + _end
        _ft = len(_t) + len(f' | {NAME}') > 70   # 빙 경고(2026-10-19): 제목 70자 상한 — 길면 브랜드 빼고, 그래도 길면 기관명 빼고 자름
        if len(_t) > 70:
            _t = f'{a["title"][:40]} {YR}' + _end
        _t = _t[:70]
        page(f'/a/{a["id"]}/', _t, f'{a["title"]} — ' + (f'{_org} ' if _org else '') + f'{a["kind"]}, ' + (f'{ddot(a["end"])} 마감' if a.get('end') and not a.get('always') else '상시 신청') + '. 신청 기간과 공식 신청처 정리.', body,
             [('루리의 줍줍', '/'), ('청약·신청', '/apply/'), (a['title'], f'/a/{a["id"]}/')], noindex=sum(1 for k in ('target', 'benefit', 'how', 'income') if a.get(k)) < 2, full_title=_ft)
        GONE[f'/a/{a["id"]}/'] = [a['title'], '/apply/', '청약·신청', a['end']]
    lst = ''.join(ap_card(a) for a in aps[:60]) or '<li class="empty"><img src="/assets/ruri/o_desk_s.webp" width="64" height="88" alt=""><p>지금 정리 중이에요. 곧 청약·신청 일정을 올릴게요!</p></li>'
    page('/apply/', f'청약·신청 일정 모음', '아파트 청약, 공공임대, 공모주, 지원금 신청 일정을 마감 순서로 정리했어요.',
         f'''<p class="bc"><a href="/">홈</a> › 청약·신청</p><section class="dh" data-c="apply"><span class="ic big">📝</span><h1>청약·신청</h1><p class="lead">진행 중 <b>{len(aps)}건</b> · 마감 임박순</p></section>
{say('o_desk', '신청만 하면 되는 기회들이에요. 기간이 짧으니 미리 챙겨요!')}{APPLY_INTRO}<h2>진행 중 청약·신청 <small>마감 가까운 순 {min(60, len(aps))}건 · 전체 {len(aps)}건</small></h2><ul class="list" id="ap-list">{lst}</ul>
{f'<p class="hm-more"><button class="btn2" id="ap-more" data-n="{len(aps) - 60}">나머지 {len(aps) - 60}건 더 보기</button> · <a href="/apply/month/{TODAY:%Y-%m}/">달별 일정</a> · <a href="/apply/r/">지역별</a></p>' if len(aps) > 60 else ''}
<script defer src="/assets/view/one.js?v=2"></script>''',
         [('루리의 줍줍', '/'), ('청약·신청', '/apply/')])


HERO_JS = '''<script>(function(){var o=[['smile','오늘도 마감 임박 공모전 챙겨 왔어요 ✨'],['o_suit','오늘의 공모전 브리핑 시작할게요!'],['o_gray','상금 큰 공모전부터 정리해 뒀어요.'],['o_present','이번 주 마감, 같이 확인해 볼까요?'],['o_desk','새 공모전을 방금 업데이트했어요.'],['o_cardigan','글쓰기 공모전도 많아요. 천천히 골라 보세요.'],['o_trench','해외 공모전도 챙겨 왔어요.'],['o_anchor','마감 소식 전해 드릴게요!'],['o_vest','응모 전 체크리스트도 잊지 마세요.']];
try{var p=o[Math.floor(Math.random()*o.length)],i=document.getElementById('hero-ruri'),b=document.querySelector('.hb');if(i){i.src='/assets/ruri/'+p[0]+'.webp'}if(b){b.innerHTML='안녕하세요, <b>루리</b>예요!<br>'+p[1]}}catch(e){}})();</script>'''


YR = TODAY.year  # 허브 제목 연도는 해가 바뀌면 자동으로 넘어감 (계산기 제목은 요율 확인 뒤 사람이 바꿈)
CAT_T = {  # 2026-10-18 키워드 전략: 자동완성 문구 제목 (진행 중 건수는 뒤에)
 '영상': f'영상 공모전 {YR} 모음 (마감순)', '문학': f'소설·글쓰기 공모전 {YR} — 문학·수기·슬로건 모음', '디자인': f'디자인 공모전 {YR} 모음 (마감순)',
 '아이디어·정책': f'아이디어 공모전 {YR} — 정책 제안·기획 공모전 모음', '요리·레시피': f'요리 공모전 {YR} — 레시피·요리대회 모음', '논문': f'논문 공모전 {YR} — 대학생·대학원생 학술 공모전 모음',
 'IT·과학': f'IT 공모전 {YR} — 개발·AI·과학 공모전 모음', '해외': f'해외 공모전 {YR} 모음 (국제 공모전·영문 공모)', '기타': f'기타 공모전 {YR} 모음 (사진·캐릭터·이벤트형)'}


def cat_stats(n, cl):
    """분야별 지금 숫자: 건수·상금 중간값·이번 주 마감·제출물 분포 (매 빌드 계산)."""
    if not cl:
        return ''
    pv = sorted(x['pv'] for x in cl if x.get('pv'))
    wk = sum(1 for x in cl if dday(x['end'])[0] <= 7)
    ef = collections.Counter(x['effort'] for x in cl if x.get('effort')).most_common(3)
    big = max(cl, key=lambda x: x.get('pv') or 0)
    t = f'지금 접수 중인 {n} 공모전은 {len(cl)}건이고, 이 중 {wk}건이 일주일 안에 마감해요. '
    if pv:
        t += f'상금이 숫자로 나온 {len(pv)}건의 중간값은 {won_txt(pv[len(pv) // 2])}, 가장 큰 곳은 「{big["title"][:30]}」({won_txt(big["pv"])})예요. '
    if ef:
        t += '제출물은 ' + ', '.join(f'{k} {v}건' for k, v in ef) + ' 순으로 많아요.'
    return f'<p class="cat-st">📌 {E(t)}</p>'


SIDO = [('seoul', '서울', r'서울'), ('busan', '부산', r'부산'), ('daegu', '대구', r'대구'), ('incheon', '인천', r'인천'), ('jeonnam-gwangju', '광주·전남', r'광주광역|전남|전라남도|광주$|^광주'),
        ('daejeon', '대전', r'대전'), ('ulsan', '울산', r'울산'), ('sejong', '세종', r'세종'), ('gyeonggi', '경기', r'경기'), ('gangwon', '강원', r'강원'),
        ('chungbuk', '충북', r'충북|충청북도'), ('chungnam', '충남', r'충남|충청남도'), ('jeonbuk', '전북', r'전북|전라북도'), ('gyeongbuk', '경북', r'경북|경상북도'),
        ('gyeongnam', '경남', r'경남|경상남도'), ('jeju', '제주', r'제주')]


def sido_of(a):
    """지원금 → 시·도 slug. 지역 칸 첫 단어 → 제목 [ ] → 주관 기관 순."""
    for src in ((a.get('region') or '').split(' ')[0], (re.match(r'\[([^\]]+)\]', a['title']) or [0, ''])[1], (a.get('org') or '').split(' ')[0]):
        if not src or src in ('전국', '공고', '공고 참조'):
            continue
        for sl, nm, pat in SIDO:
            if re.search(pat, src):
                return sl
    blob = a['title'] + ' ' + (a.get('org') or '')   # 2026-10-19 키워드 구멍: 지역 칸이 빈 청약·임대 공고
    for sl, nm, pat in SIDO:
        if re.search(r'광주광역|전남|전라남도' if sl == 'jeonnam-gwangju' else pat, blob):
            return sl
    return None


SIDO_FULL = {'seoul': '서울시', 'busan': '부산시', 'daegu': '대구시', 'incheon': '인천시', 'jeonnam-gwangju': '광주·전남', 'daejeon': '대전시', 'ulsan': '울산시', 'sejong': '세종시', 'gyeonggi': '경기도',
             'gangwon': '강원도', 'chungbuk': '충청북도', 'chungnam': '충청남도', 'jeonbuk': '전북', 'gyeongbuk': '경상북도', 'gyeongnam': '경상남도', 'jeju': '제주도'}
REG_TYPES = {'': ('지원금·청약', None), 'youth': ('청년 지원금', lambda a: re.search(r'청년|대학생|사회초년', a['title'])),
             'house': ('청약·월세·주거 지원', lambda a: a.get('kk') in ('rent', 'apt') or re.search(r'월세|주거|임대|청약|전세|주택', a['title']))}


def region_pages(aps):
    """지역(시·도) × 유형 허브 (2026-10-18 키워드 전략 ②). 항목이 적으면 검색 제외."""
    by = {}
    for a in aps:
        sl = sido_of(a)
        if sl:
            by.setdefault(sl, []).append(a)
    nat = [a for a in aps if (a.get('region') or '').startswith('전국')]
    urls, idx = [], []
    for sl, nm, _ in SIDO:
        L = by.get(sl, [])
        for tk, (tn, f) in REG_TYPES.items():
            M = [a for a in L if not f or f(a)]
            path = f'/apply/r/{sl}/' + (f'{tk}/' if tk else '')
            kinds = collections.Counter(a['kind'] for a in M).most_common(3)
            wk = sum(1 for a in M if not a.get('always') and dday(a['end'])[0] <= 7)
            info = sum(1 for a in M if a.get('target') or a.get('benefit'))
            t = (f'지금 {nm}에서 신청할 수 있는 {tn} 공고는 {len(M)}건이에요. ' + (f'이 중 {wk}건이 일주일 안에 마감하고, ' if wk else '') +
                 ('종류는 ' + ', '.join(f'{k} {v}건' for k, v in kinds) + '이에요. ' if kinds else '') +
                 (f'대상·혜택이 정리된 공고는 {info}건이라, 나머지는 공식 공고에서 자격을 꼭 확인하세요. ' if M else '') +
                 (f'가장 먼저 끝나는 건 「{M[0]["title"][:30]}」({ddot(M[0]["end"])} 마감)이에요.' if M and not M[0].get('always') else ''))
            orgs = collections.Counter(a['org'] for a in M if a.get('org') and a['org'] != '공고 참조').most_common(3)
            if orgs:
                t += ' 공고를 많이 낸 곳은 ' + ', '.join(f'{o} {n}건' for o, n in orgs) + '이에요.'
            guide = {'youth': f'{nm} 청년 지원금은 시·도와 시·군·구가 따로 공고하는 경우가 많아요. 거주 기간(보통 6개월~1년 이상), 나이(만 19~34세 또는 39세), 소득 기준(기준 중위소득 %)을 먼저 확인하고, 국가 사업인 청년월세 지원·청년도약계좌와 겹쳐 받을 수 있는지도 공고에서 보세요.',
                     'house': f'{nm} 아파트 청약은 청약홈, 공공임대는 LH청약플러스와 지역 도시공사, 월세 지원은 복지로와 시·군·구에서 신청해요. 청약은 해당 지역 거주 기간에 따라 우선 공급이 갈리니 <a href="/apply/recommend/">청약 가점 추천</a>으로 내 점수부터 계산해 보세요.',
                     '': f'{nm} 지역 공고만 골라 마감순으로 모았어요. 전국 대상 공고 {len(nat)}건은 <a href="/apply/">전체 일정</a>에서 함께 확인하세요.'}[tk]
            subs = ' · '.join(f'<a href="/apply/r/{sl}/{k2 + "/" if k2 else ""}"{" class=on" if k2 == tk else ""}>{nm} {n2}</a>' for k2, (n2, f2) in REG_TYPES.items())
            lst = ''.join(ap_card(a) for a in M) or '<li class="empty">지금은 이 지역 공고가 없어요.</li>'
            fn = SIDO_FULL.get(sl, nm)   # 2026-10-19 검색 시나리오: 검색어는 「경기도」「서울시」처럼 정식 이름으로 친다
            title = {'': f'{fn} 지원금·청약 {YR} — 진행 중 {len(M)}건 마감순', 'youth': f'{fn} 청년 지원금 {YR} — 종류·금액·신청기간 ({len(M)}건)', 'house': f'{fn} 청약 일정 {YR} — 아파트·공공임대·월세 지원 ({len(M)}건)'}[tk]
            body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › <a href="/apply/r/">지역별</a> › {nm}</p><h1>📍 {E(title)}</h1><p class="hm-links">{subs}</p>'
                    f'<p class="cat-st">📌 {t}</p><p>{guide}</p><h2>진행 중 공고 (마감순)</h2><ul class="list">{lst}</ul>'
                    + rel_block(r'청년|월세|청약|지원금' if tk != 'house' else r'월세|청약|주거', [('/apply/recommend/', '청약 가점 추천'), ('/apply/', '전국 지원금·청약 일정'), ('/money/tools/loan/', '대출 이자 계산기')]))
            page(path, title, f'{nm} {tn} {YR}: 진행 중 {len(M)}건을 마감순으로 정리. 신청 기간·대상·공식 신청처.', body,
                 [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), ('지역별', '/apply/r/'), (nm, path)], noindex=len(M) < (8 if not tk else 5))
            urls.append(path)
        idx.append((sl, nm, len(L)))
    body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › 지역별</p><h1>📍 지역별 지원금·청약 {YR}</h1>'
            '<p>시·도별로 지금 신청할 수 있는 지원금·청약·월세 지원 공고를 모았어요. 지역 칸이나 제목에 시·도가 적힌 공고만 들어가고, 전국 대상 공고는 <a href="/apply/">전체 일정</a>에 있어요. 매시간 새 공고를 반영해요.</p><ul class="reg-l">'
            + ''.join(f'<li><a href="/apply/r/{sl}/"><b>{nm}</b><span>{n}건</span></a></li>' for sl, nm, n in sorted(idx, key=lambda x: -x[2])) + '</ul>')
    page('/apply/r/', f'지역별 지원금·청약 {YR} — 서울·경기·부산 등 시·도별 신청 일정', '시·도별 청년 지원금, 월세 지원, 아파트 청약 일정을 마감순으로 정리했어요.', body,
         [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), ('지역별', '/apply/r/')])
    return ['/apply/r/'] + urls


XTOPIC = {  # 2026-10-19 홍보 세션 키워드 구멍(구글 자동완성 866개): 주제 × 시·도, 진행 중 2건 이상인 조합만 만든다
    'youth-rent': ('청년 월세 지원', '🏠', lambda a: re.search(r'청년', a['title']) and re.search(r'월세|주거비|임차|전월세|보증금|이사비|중개보수|주거', a['title']),
                   lambda fn, nm: f'청년 월세 지원 {fn if nm == "경기" else nm} 조건·신청 ({YR})',
                   '청년 월세·주거비 지원은 보통 무주택 청년이 대상이고, 부모와 따로 사는지(독립 거주), 본인·부모 소득(기준 중위소득 %), 임차보증금·월세 상한을 함께 봐요. 기준은 사업마다 달라서 아래 표의 대상 칸과 공고 원문을 꼭 같이 확인하세요. 필요한 서류와 지급일도 공고마다 달라요.'),
    'newlywed': ('신혼부부 지원금·결혼장려금', '💍', lambda a: re.search(r'신혼|결혼|예비부부|혼인|웨딩', a['title'] + ' ' + (a.get('target') or '')),
                 lambda fn, nm: f'{fn} 신혼부부 지원금·결혼장려금 {YR}',
                 '신혼부부 지원은 혼인 기간, 부부 합산 소득, 해당 지역 거주 기간을 공고마다 다르게 봐요. 결혼장려금처럼 현금으로 주는 것과 전세·월세 대출이자, 공공임대·특별공급처럼 주거로 돕는 것은 신청처가 달라 따로 신청해야 하는 경우가 많아요.'),
}
XMADE = {}


def _xcell(v):
    return E(v) if v else '<span class="mu">공고 원문 확인</span>'


def _xtarget(a):
    if a.get('target'):
        return a['target']
    if a.get('age_min') or a.get('age_max'):
        return f'만 {a.get("age_min") or ""}~{a.get("age_max") or ""}세'
    return ''


def cross_pages(aps):
    """주제 × 시·도 (2026-10-19 키워드 구멍). 대상·지원 내용·신청 칸은 공고에서 정리된 값만, 없으면 「공고 원문 확인」."""
    urls = []
    for tk in XTOPIC:
        d = os.path.join(ROOT, 'apply', tk)
        if tk == 'newlywed':   # /apply/newlywed/index.html 은 apply_hubs 가 만듦 — 하위 지역 폴더만 지움
            for f in (os.listdir(d) if os.path.isdir(d) else []):
                if os.path.isdir(os.path.join(d, f)):
                    shutil.rmtree(os.path.join(d, f), ignore_errors=True)
        else:
            shutil.rmtree(d, ignore_errors=True)
    css = ('<style>.tblw{overflow-x:auto}.xt{border-collapse:collapse;width:100%;font-size:14px;min-width:560px}.xt th,.xt td{border:1px solid #e5e7eb;padding:6px 8px;vertical-align:top;text-align:left}'
           '.xt th{background:#f8fafc}.xt .mu{color:#94a3b8}</style>')
    for tk, (tn, ic, f, tt, guide) in XTOPIC.items():
        allm = sorted([a for a in aps if f(a)], key=lambda a: (a.get('always'), a['end']))
        by = {}
        for a in allm:
            by.setdefault(sido_of(a) or '', []).append(a)
        made = []
        for sl, nm, _ in SIDO:
            M = by.get(sl, [])
            if len(M) < 2:
                continue
            fn = SIDO_FULL.get(sl, nm)
            path = f'/apply/{tk}/{sl}/'
            title = tt(fn, nm)
            wk = sum(1 for a in M if not a.get('always') and dday(a['end'])[0] <= 7)
            rows = ''.join(f'<tr><td><a href="/a/{a["id"]}/">{E(a["title"][:60])}</a><br><small>{E(a["org"])}</small></td><td>{_xcell(_xtarget(a))}</td>'
                           f'<td>{_xcell(a.get("benefit"))}</td><td>{_xcell(a.get("how"))}</td><td>{"상시" if a.get("always") else ddot(a["end"])}</td></tr>' for a in M)
            first = next((a for a in M if not a.get('always')), None)
            stat = (f'지금 {fn}에서 신청할 수 있는 {tn} 공고는 {len(M)}건이에요. ' + (f'이 중 {wk}건은 일주일 안에 마감해요. ' if wk else '')
                    + (f'가장 먼저 끝나는 건 「{first["title"][:30]}」({ddot(first["end"])} 마감)이에요.' if first else ''))
            others = ' · '.join(f'<a href="/apply/{tk}/{s2}/">{n2}</a>' for s2, n2, _ in SIDO if s2 != sl and len(by.get(s2, [])) >= 2)
            body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › <a href="/apply/{tk}/">{tn}</a> › {nm}</p><h1>{ic} {E(title)}</h1>'
                    f'<p class="cat-st">📌 {E(stat)}</p><p>{guide}</p>'
                    f'<h2>{nm} 공고별 조건 한눈에</h2><div class="tblw"><table class="xt"><thead><tr><th>공고</th><th>대상</th><th>지원 내용</th><th>신청 방법</th><th>마감</th></tr></thead><tbody>{rows}</tbody></table></div>'
                    '<p class="note">대상·지원 내용·신청 방법은 공고에서 확인된 값만 적었어요. 비어 있는 칸은 공고 원문(각 공고 페이지의 공식 공고 링크)에서 확인하세요. 서류와 지급일은 공고마다 달라요.</p>'
                    f'<h2>진행 중 공고 (마감순)</h2><ul class="list">{"".join(ap_card(a) for a in M)}</ul>'
                    + (f'<p class="hm-links">다른 지역 {tn}: {others}</p>' if others else '')
                    + rel_block(r'청년|월세|신혼|결혼|주거', [(f'/apply/r/{sl}/', f'{fn} 지원금·청약 전체'), (f'/apply/r/{sl}/house/', f'{fn} 청약 일정'), ('/apply/recommend/', '청약 가점 계산기'), ('/apply/', '전국 지원금·청약 일정')])
                    + css)
            page(path, title, f'{title}: 진행 중 {len(M)}건의 대상·지원 내용·신청 방법·마감일을 공고 기준으로 정리.', body,
                 [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), (tn, f'/apply/{tk}/'), (nm, path)])
            urls.append(path)
            made.append((sl, nm, len(M)))
        XMADE[tk] = made
        if tk == 'newlywed':   # 전국 허브는 apply_hubs 의 /apply/newlywed/ — 거기에 지역 링크만 붙음
            continue
        idx = ''.join(f'<li><a href="/apply/{tk}/{sl}/"><b>{nm}</b><span>{n}건</span></a></li>' for sl, nm, n in sorted(made, key=lambda x: -x[2]))
        title = f'청년 월세 지원금 {YR} — 지역별 조건·신청 ({len(allm)}건)'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › {tn}</p><h1>{ic} {E(title)}</h1>'
                f'<p class="cat-st">📌 제목에 청년과 월세·주거비·임차 등이 들어간 진행 중 공고는 모두 {len(allm)}건이에요.</p><p>{guide}</p>'
                + (f'<h2>지역별로 보기</h2><ul class="reg-l">{idx}</ul>' if idx else '')
                + f'<h2>진행 중 공고 (마감순)</h2><ul class="list">{"".join(ap_card(a) for a in allm)}</ul>'
                + rel_block(r'청년|월세|주거', [('/apply/r/', '지역별 지원금·청약'), ('/apply/', '전국 지원금·청약 일정')]))
        page(f'/apply/{tk}/', title, f'청년 월세 지원금 {YR}: 진행 중 {len(allm)}건, 지역별 조건·신청 방법·마감일.', body,
             [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), (tn, f'/apply/{tk}/')], noindex=len(allm) < 3)
        urls.append(f'/apply/{tk}/')
    return urls


def apply_hubs(aps):
    """2026-10-19 검색 시나리오: 「11월 청약 일정」「신혼부부 지원금 2026 지역별」 — 데이터에서 골라 만든 모음(사실 문장은 공고 값만)."""
    urls = []
    for mo in (TODAY.replace(day=1), (TODAY.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)):
        ym = mo.strftime('%Y-%m'); m = mo.month
        L = [a for a in aps if not a.get('always') and ((a.get('end') or '')[:7] == ym or (a.get('start') or '')[:7] == ym)]
        apt = [a for a in L if a.get('kk') in ('apt', 'rent')]; ipo = [a for a in L if a.get('kk') == 'ipo']; etc = [a for a in L if a not in apt and a not in ipo]
        sec = lambda t, X: (f'<h2>{t} ({len(X)}건)</h2><ul class="list">{"".join(ap_card(a) for a in sorted(X, key=lambda a: a.get("end") or ""))}</ul>' if X else '')
        path = f'/apply/month/{ym}/'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › {m}월 일정</p><h1>📅 {m}월 청약 일정 {mo.year} — 아파트·공공임대·공모주·지원금 ({len(L)}건)</h1>'
                f'<p class="cat-st">📌 {mo.year}년 {m}월에 접수를 시작하거나 마감하는 공고 {len(L)}건이에요(아파트·임대 {len(apt)}건, 공모주 {len(ipo)}건, 지원금 등 {len(etc)}건). 공모주는 투자 상품이라 청약 전 투자설명서를 꼭 읽어 보세요.</p>'
                f'<p class="hm-scope">기준: 공공·지자체·청약홈 공고 중 접수 시작일이나 마감일이 {m}월인 것 · {NOW_KST():%m/%d %H:%M} 갱신(한국 시간)</p>'
                + sec('🏠 아파트·공공임대', apt) + sec('📈 공모주 (투자 권유 아님)', ipo) + sec('💰 지원금·기타', etc)
                + '<h2>청약홈 신청 방법</h2><ol><li>청약홈(applyhome.co.kr)에 접속해 공동·금융인증서나 간편인증으로 로그인해요.</li><li>「청약 신청」에서 공고 단지와 주택형을 고르고, 특별공급·일반공급(1·2순위) 접수일에 맞춰 신청해요.</li><li>신청 전 「청약 자격 확인」으로 무주택 기간·청약통장 가입 기간을 확인하고, 신청 뒤 「청약 신청 내역」에서 접수됐는지 꼭 확인해요.</li></ol>'
                + '<h2>청약 철회(신청 취소)</h2><p>접수 기간 안에는 청약홈의 청약 신청 내역에서 신청을 취소할 수 있어요. 당첨된 뒤 계약하지 않으면 당첨자로 관리돼 재당첨 제한 같은 불이익이 생길 수 있으니, 단지 공고의 「당첨자 계약 포기」 안내를 미리 읽어 두세요.</p><p class="note">일반적인 절차 안내예요. 단지마다 다를 수 있으니 공고문과 청약홈 안내(1644-7445)를 기준으로 하세요.</p>'
                + rel_block(r'청약|지원금|청년', [('/apply/recommend/', '청약 가점 계산기'), ('/apply/r/', '지역별 지원금·청약'), ('/apply/', '전체 일정')]))
        page(path, f'{m}월 청약 일정 {mo.year} — 아파트·공공임대·공모주 ({len(L)}건)', f'{mo.year}년 {m}월 청약 일정: 아파트·공공임대 {len(apt)}건, 공모주 {len(ipo)}건, 지원금 {len(etc)}건 접수 시작·마감일 정리.',
             body, [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), (f'{m}월 일정', path)], noindex=len(L) < 5)
        urls.append(path)
    L = [a for a in aps if re.search(r'신혼|결혼|예비부부|웨딩|혼인', a['title'] + ' ' + (a.get('target') or ''))]
    by = collections.Counter(SIDO_FULL.get(sido_of(a), '전국·기타') for a in L)
    body = (f'<p class="bc"><a href="/">홈</a> › <a href="/apply/">지원금·청약</a> › 신혼부부</p><h1>💍 신혼부부 지원금 {YR} — 지역별 결혼·주거 지원 ({len(L)}건)</h1>'
            f'<p class="cat-st">📌 제목이나 대상에 신혼·결혼·예비부부가 들어간 진행 중 공고 {len(L)}건이에요. 지역별로는 ' + ', '.join(f'{k} {v}건' for k, v in by.most_common(6)) + ' 순이에요.</p>'
            '<p>신혼부부 지원은 혼인 기간(보통 7년 이내), 부부 합산 소득, 거주 기간 조건이 공고마다 달라요. 주거 지원(전세·월세·특별공급)과 결혼 장려금은 따로 신청하는 경우가 많으니 둘 다 확인해 보세요.</p>'
            + ((f'<h2>지역별로 보기</h2><ul class="reg-l">' + ''.join(f'<li><a href="/apply/newlywed/{sl}/"><b>{nm}</b><span>{n}건</span></a></li>' for sl, nm, n in sorted(XMADE.get('newlywed', []), key=lambda x: -x[2])) + '</ul>') if XMADE.get('newlywed') else '')
            + f'<p class="hm-scope">기준: 진행 중 공고 · {NOW_KST():%m/%d %H:%M} 갱신(한국 시간)</p><ul class="list">{"".join(ap_card(a) for a in L) or "<li class=empty>지금은 없어요.</li>"}</ul>'
            + rel_block(r'신혼|청약|주거', [('/apply/recommend/', '청약 가점 계산기'), ('/apply/r/', '지역별 지원금·청약')]))
    page('/apply/newlywed/', f'신혼부부 지원금 {YR} — 지역별 결혼·주거 지원 ({len(L)}건)', f'신혼부부 지원금 {YR}: 진행 중 {len(L)}건을 지역별로. 결혼 장려금·전세·월세·특별공급 신청 기간과 대상.', body,
         [('루리의 줍줍', '/'), ('지원금·청약', '/apply/'), ('신혼부부', '/apply/newlywed/')], noindex=len(L) < 5)
    return urls + ['/apply/newlywed/']


def week_hub(live):
    """「이번 주 마감 공모전」 (2026-10-18 키워드 전략): 오늘부터 7일 안에 마감, 매 빌드 갱신."""
    e7 = TODAY + datetime.timedelta(days=7)
    L = sorted([c for c in live if dday(c['end'])[0] <= 7], key=lambda c: (c['end'], -(c.get('pv') or 0)))
    pv = [c for c in L if c.get('pv')]
    big = max(pv, key=lambda c: c['pv']) if pv else None
    tg = collections.Counter(c['tags'][0] for c in L).most_common(3)
    ef = collections.Counter(c['effort'] for c in L if c.get('effort')).most_common(2)
    days = collections.Counter(c['end'] for c in L).most_common(1)
    t = (f'{TODAY.month}/{TODAY.day}부터 {e7.month}/{e7.day}까지 마감하는 공모전은 {len(L)}건이에요. '
         + (f'분야는 ' + ', '.join(f'{k} {v}건' for k, v in tg) + ' 순으로 많고, ' if tg else '')
         + (f'제출물은 ' + ', '.join(f'{k} {v}건' for k, v in ef) + '이 많아요. ' if ef else '')
         + (f'마감이 가장 몰린 날은 {ddot(days[0][0])[5:]}({days[0][1]}건)이에요. ' if days else '')
         + (f'상금이 가장 큰 곳은 「{big["title"][:30]}」({won_txt(big["pv"])})예요.' if big else ''))
    body = (f'<p class="bc"><a href="/">홈</a> › <a href="/contest/">공모전</a> › 이번 주 마감</p><h1>⏰ 이번 주 마감 공모전 ({TODAY.month}/{TODAY.day}~{e7.month}/{e7.day}, {len(L)}건)</h1>'
            f'<p class="cat-st">📌 {E(t)}</p><p>남은 기간이 짧을수록 분량이 적은 슬로건·네이밍·사진 공모전부터 고르는 게 좋아요. 영상·기획서처럼 준비가 오래 걸리는 건 이번 주보다 다음 주 마감을 노리세요. 매시간 새로 정리돼요.</p>'
            f'<ul class="list">{"".join(card(c) for c in L) or "<li class=empty>이번 주 마감 공모전이 없어요.</li>"}</ul>'
            + rel_block(r'공모전|마감|응모', [('/contest/univ/', '대학생 공모전 모음'), ('/cat/video/', '영상 공모전 모음'), ('/widget/', '블로그용 이번 주 마감 위젯')]))
    page('/contest/week/', f'이번 주 마감 공모전 — {TODAY.month}/{TODAY.day}~{e7.month}/{e7.day} 마감 {len(L)}건 (상금·자격)', f'{TODAY.month}/{TODAY.day}~{e7.month}/{e7.day} 마감하는 공모전 {len(L)}건을 마감순으로 정리. 분야·상금·제출물 한눈에.',
         body, [('루리의 줍줍', '/'), ('공모전', '/contest/'), ('이번 주 마감', '/contest/week/')])
    return ['/contest/week/']


def hub_extra(nm, L, path):
    """검색어 허브 공통: 집계 문장 + FAQ + ItemList/FAQPage 구조화 데이터 (숫자는 매 빌드 계산, 2026-10-19 자연 유입)."""
    if not L:
        return '', None
    pv = [c for c in L if c.get('pv')]
    big = max(pv, key=lambda c: c['pv']) if pv else None
    day = collections.Counter(c['end'] for c in L).most_common(1)[0]
    soon = min(L, key=lambda c: c['end'])
    wk = sum(1 for c in L if dday(c['end'])[0] <= 7)
    ef = collections.Counter(c['effort'] for c in L if c.get('effort')).most_common(2)
    faq = [(f'지금 접수 중인 {nm}은 몇 개예요?', f'{TODAY.month}월 {TODAY.day}일(한국 시간) 기준 {len(L)}건이고, 일주일 안에 마감하는 건 {wk}건이에요. 매시간 새로 정리해요.'),
           (f'{nm} 중 상금이 가장 큰 건 뭐예요?', (f'「{big["title"][:40]}」로 {won_txt(big["pv"])}이에요. 상금이 숫자로 나온 {len(pv)}건 기준이에요.' if big else '상금이 숫자로 정리된 공모전이 아직 없어요. 공고마다 확인하세요.')),
           (f'{nm} 마감은 언제 몰려 있어요?', f'{ddot(day[0])} 마감이 {day[1]}건으로 가장 많고, 가장 먼저 마감하는 건 「{soon["title"][:40]}」({ddot(soon["end"])})예요. 마감 시각은 공고마다 달라 공식 공고를 확인하세요.'),
           ('무엇을 내야 하나요?', ('제출물은 ' + ', '.join(f'{k} {v}건' for k, v in ef) + ' 순으로 많아요. 분량·파일 형식은 공고마다 달라요.') if ef else '제출물은 공모전마다 달라요. 상세 페이지의 제출물 칸과 공식 공고를 확인하세요.')]
    h = '<section class="hub-faq"><h2>❓ 자주 묻는 질문</h2>' + ''.join(f'<details class="faq"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq) + '</section>'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': f'{nm} {YR}', 'numberOfItems': len(L), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/c/{c["id"]}/', 'name': c['title']} for i, c in enumerate(L[:30])]},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}]}
    return h, ld


def contest_hubs(live):
    """자동완성 문구 허브: 대학생 공모전, AI 영상 공모전 (2026-10-18 키워드 전략 ③)."""
    H = [('univ', f'대학생 공모전 사이트 — {YR} 진행 중 모음 (마감순)', '대학생 공모전', lambda c: '대학생' in (c.get('elig') or ''),
          '응모 자격에 대학생이 들어간 공모전만 모았어요. 대외활동 사이트마다 흩어진 공고를 마감·상금·제출물 기준으로 한 번에 비교할 수 있어요. 수상하면 재학·휴학 증명서를 요구하는 경우가 많으니 미리 발급해 두세요.'),
         ('ai-video', f'AI 영상 공모전 {YR} — 생성형 AI 영상·숏폼 공모전 모음', 'AI 영상 공모전', lambda c: re.search(r'AI|인공지능|생성형', c['title']) and (re.search(r'영상|숏폼|쇼츠|릴스|뮤직비디오|애니', c['title']) or '영상' in c['tags']),
          '제목에 AI·생성형이 들어가고 영상·숏폼을 받는 공모전만 골랐어요. AI 도구로 만든 영상은 음원·이미지 저작권과 「AI 사용 표기」 규정을 공고마다 다르게 정해 두니 꼭 확인하세요.'),
         ('youth', f'청소년 공모전 {YR} — 중고등학생·초등학생 공모전 모음', '청소년 공모전', lambda c: re.search(r'청소년|초등|중학|고등|초·중·고|초중고|학생', c.get('elig') or '') is not None,
          '응모 자격에 청소년·초중고 학생이 들어간 공모전만 모았어요. 학생부가 따로 있는지, 보호자 동의서가 필요한지 공고에서 꼭 확인하세요. 봉사시간·생활기록부 반영 여부도 공고마다 달라요.'),
         ('novel', f'소설 공모전 {YR} — 웹소설·단편소설·신춘문예 모음', '소설 공모전', lambda c: re.search(r'소설|웹소설|신춘문예|문학상|스토리', c['title']) is not None,
          '제목에 소설·웹소설·신춘문예·문학상이 들어간 공모전만 골랐어요. 분량(원고지 매수·글자 수)과 「미발표 창작물」 조건, 연재 플랫폼 공모는 연재 기간 규정을 먼저 확인하세요.'),
         ('photo', f'사진 공모전 {YR} — 사진·포토 공모전 모음 (마감순)', '사진 공모전', lambda c: re.search(r'사진|포토|촬영', c['title']) is not None,
          '제목에 사진·포토가 들어간 공모전만 모았어요. 촬영 원본(EXIF)을 요구하는 경우가 많고, 사람이 나오면 초상권 동의가 필요해요. 과한 보정·합성은 감점되거나 실격될 수 있어요.'),
         ('video', f'영상 공모전 {YR} — 숏폼·UCC·홍보영상 공모전 모음', '영상 공모전', lambda c: '영상' in c['tags'] or re.search(r'영상|숏폼|쇼츠|UCC|릴스', c['title']) is not None,
          '영상 분야로 분류됐거나 제목에 영상·숏폼·UCC가 들어간 공모전만 모았어요. 길이(초)·해상도·파일 형식과 음원·폰트 저작권을 제출 전에 확인하세요.'),
         ('essay', f'에세이 공모전 {YR} — 수필·수기·대학생 에세이 공모전 모음', '에세이 공모전', lambda c: re.search(r'에세이|수필|수기|체험담|사연', c['title']) is not None,
          '제목에 에세이·수필·수기·체험담이 들어간 공모전만 모았어요. 분량(원고지 매수·A4 장수)과 「실화 여부」 조건을 먼저 보고, 개인정보가 들어간 사연은 가명 처리 규정을 확인하세요.'),
         ('poem', f'시 공모전 {YR} — 시·동시·디카시·백일장 모음', '시 공모전', lambda c: re.search(r'(?<![가-힣])시(?:\s|$|·|,|\)|부문| 공모)|동시|디카시|시조|백일장|시인|시화', c['title']) is not None,
          '제목에 시·동시·디카시·시조·백일장이 들어간 공모전만 골랐어요. 편수(보통 3~5편)와 「미발표작」 조건, 원고 양식(한글 hwp·글꼴·크기)을 공고에서 꼭 확인하세요.'),
         ('character', f'캐릭터 공모전 {YR} — 캐릭터·마스코트 디자인 공모전 모음', '캐릭터 공모전', lambda c: re.search(r'캐릭터|마스코트|이모티콘', c['title']) is not None,
          '캐릭터·마스코트·이모티콘 공모전만 모았어요. 대부분 「판넬(제출용 한 장)」에 기본형·응용 동작·컬러 칩·기획 의도를 함께 넣으라고 해요. 원본 파일(ai·psd) 제출 여부와 저작권 양도 조항을 먼저 보세요.'),
         ('slogan', f'슬로건 공모전 {YR} — 슬로건·네이밍·표어 공모전 모음', '슬로건·네이밍 공모전', lambda c: re.search(r'슬로건|네이밍|명칭|표어|캐치프레이즈|이름\s*짓기|애칭|BI', c['title']) is not None,
          '슬로건·네이밍·표어 공모전만 모았어요. 짧아서 응모가 많으니 「주최 기관의 핵심 단어 + 리듬」이 중요해요. <a href="/lab/">수상작 분석</a>에서 실제 당선작 구조를 먼저 보세요.'),
         ('ucc', f'UCC 공모전 {YR} — UCC·숏폼·홍보영상 공모전 (심사기준 정리)', 'UCC·숏폼 공모전', lambda c: re.search(r'UCC|숏폼|쇼츠|릴스|틱톡|짧은 영상|1분 영상|30초', c['title']) is not None,
          'UCC·숏폼 공모전만 모았어요. 심사기준은 보통 주제 적합성·창의성·전달력·완성도(편집·음향)로 나뉘고, 조회수·좋아요를 점수에 넣는 공모전도 있어요. 음원·폰트 저작권 표기를 꼭 확인하세요.'),
         ('webnovel', f'웹소설 공모전 {YR} — 플랫폼 웹소설 공모전 일정', '웹소설 공모전', lambda c: re.search(r'웹소설|웹 소설|연재|노벨|문피아|카카오페이지|시리즈|조아라', c['title']) is not None,
          '웹소설 공모전만 마감순으로 모았어요. 플랫폼 공모전은 「공모 기간 안 연재 회차·글자 수」가 조건인 경우가 많아요. 연재 시작일과 최소 회차를 먼저 확인하세요.'),
         ('idea', f'아이디어 공모전 {YR} — 정책 제안·기획 공모전 모음', '아이디어 공모전', lambda c: '아이디어·정책' in c['tags'] or re.search(r'아이디어|제안|정책', c['title']) is not None,
          '아이디어·정책 제안 공모전만 모았어요. 이미 시행 중인 정책과 겹치지 않는지 검색해 보고, 현황 → 문제점 → 개선안 → 기대효과 순서로 쓰면 심사위원이 읽기 쉬워요.')]
    for mo in sorted({int(c['end'][5:7]) for c in live if c['end'][:4] == str(TODAY.year)} & {TODAY.month, TODAY.month % 12 + 1}):
        H.append((f'deadline-{mo}', f'{mo}월 마감 공모전 {YR} — {mo}월에 접수 끝나는 공모전 모음', f'{mo}월 마감 공모전', (lambda m: lambda c: c['end'][:4] == str(TODAY.year) and int(c['end'][5:7]) == m)(mo),
                  f'{YR}년 {mo}월 안에 접수가 끝나는 공모전만 마감 날짜순으로 모았어요. 같은 날 마감이 몰리면 접수 서버가 느려지니 하루 전에 내는 걸 권해요.'))
    urls = []
    for sl, title, nm, f, intro in H:
        L = [c for c in live if f(c)]
        path = f'/contest/{sl}/'
        L.sort(key=lambda c: (c['end'], -(c.get('pv') or 0)))
        fq, ld_ = hub_extra(nm, L, path)
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/contest/">공모전</a> › {nm}</p><h1>🏆 {E(title)}</h1><p>{intro}</p>{cat_stats(nm.replace(" 공모전", ""), L)}'
                f'<p class="hm-scope">오늘 {TODAY.month}/{TODAY.day}(한국 시간) 기준 접수 마감 전 · 제목이 같은 공모전은 1건 · {NOW_KST():%m/%d %H:%M} 갱신 · 마감순</p>'
                f'<h2>진행 중 {nm} ({len(L)}건)</h2><ul class="list">{"".join(card(c) for c in L[:80]) or "<li class=empty>지금은 없어요.</li>"}</ul>{fq}'
                + '<p class="hm-more">다른 모음: ' + ' · '.join(f'<a href="/contest/{x[0]}/">{E(x[2])}</a>' for x in H if x[0] != sl) + '</p>'
                + rel_block(r'공모전|대학생|영상', [('/guide/', '공모전 응모 가이드'), ('/widget/', '블로그용 공모전 위젯'), ('/cat/video/', f'영상 공모전 {YR} 모음')]))
        page(path, title, f'{nm} 진행 중 {len(L)}건을 마감순으로 정리. 상금·자격·제출물 비교.', body, [('루리의 줍줍', '/'), ('공모전', '/contest/'), (nm, path)], ld_, noindex=len(L) < 5)
        urls.append(path)
    return urls


def build():
    contests, events = load()
    late = NOW_KST().hour >= 18  # 대부분 18시·업무시간 마감 → 저녁 빌드부터 오늘 마감은 내림
    live = [c for c in contests if dday(c['end'])[0] >= (1 if late else 0)]
    import dup_check   # 2026-10-19: 같은 공고(주소·제목 유사도·주최·마감)는 대표 1건만 목록에, 나머지 주소는 대표로 안내
    DUP.clear(); DUP.update(dup_check.dups(live)[0])
    live = [c for c in live if c['id'] not in DUP]
    print('중복 공고 합침', len(DUP))
    # 공고 변경 이력 (2026-10-19 지침 3.3): 마감일·상금·자격·제목·링크가 바뀌면 날짜와 함께 기록
    HF = os.path.join(HERE, 'contest_hist.json')
    HIST.update(json.load(open(HF, encoding='utf-8')) if os.path.exists(HF) else {})
    for c in contests:
        cur = {k: c.get(k) or '' for k in ('title', 'end', 'prize', 'elig', 'link')}
        h_ = HIST.setdefault(c['id'], {'first': TODAY.isoformat(), 'cur': cur, 'chg': []})
        diff = [k for k in cur if h_['cur'].get(k) != cur[k]]
        if diff:
            h_['chg'] = (h_['chg'] + [{'d': TODAY.isoformat(), 'f': {k: [h_['cur'].get(k), cur[k]] for k in diff}}])[-10:]
            h_['cur'] = cur
    json.dump(HIST, open(HF, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    events = [e for e in events if dday(e['end'])[0] >= (1 if late else 0)]
    for d in ('c', 'cat', 'event', 'guide'):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    for c in contests:
        detail(c, live)
    sync_shots(live)
    keys = ('id', 'title', 'org', 'start', 'end', 'prize', 'pv', 'field', 'tags', 'th', 'elig', 'effort', 'region', 'fee', 'submit', 'ai', 'win')
    for c in live:   # 수상 인원 추정(공고 원문 시상 항목의 「N명·N팀·N편」 합) — 추천 1인당 기대 상금용, 못 찾으면 0
        sw = next((v for k_, v in notice_points(c['id']) if k_ == '시상'), '')
        ns = [int(x) for x in re.findall(r'(\d{1,3})\s*(?:명|팀|편|점|작품)', sw)]
        c['win'] = sum(ns) if ns and sum(ns) <= 300 else 0
    with open(os.path.join(ROOT, 'data.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'updated': NOW_KST().strftime('%Y-%m-%d %H:%M'), 'late': late, 'items': [{k: c[k] for k in keys} for c in live]},
                  f, ensure_ascii=False, separators=(',', ':'))
    # 챗봇 추천용 경품 이벤트 목록 (진행 중만)
    with open(os.path.join(ROOT, 'events.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{'title': e['title'], 'org': e['org'], 'end': e['end'], 'ez': e.get('effort') or EASY.get(e['type'], e['type']), 'link': e['link']} for e in events],
                  f, ensure_ascii=False, separators=(',', ':'))
    live_rec = sorted(live, key=lambda c: -score(c))
    pre = ''.join(card(c) for c in live_rec[:60])  # 크롤러용 서버 렌더, JS 가 전체 목록으로 교체
    big = sorted(live, key=lambda c: -c['pv'])[:6]
    aps = load_apply()
    wk = [c for c in live if 1 <= dday(c['end'])[0] <= 7]
    quick = sorted([e for e in events if EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2) <= 1],
                   key=lambda e: (e['end'], EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2)))
    SHORT = re.compile(r'슬로건|네이밍|명칭|표어|캐치프레이즈|아이디어|사진|한\s*줄|삼행시|사행시|디카시|짧은\s*글|문구|애칭|이름\s*짓기|BI|캐릭터\s*이름')
    short = [c for c in live if not c.get('fee') and not re.search('우편|방문', c.get('submit') or '') and (c.get('quick') is True or (c.get('quick') is None and SHORT.search(c['title'] + ' ' + (c['field'] or ''))))]
    short = [c for c in short if dday(c['end'])[0] >= 2]
    short.sort(key=lambda c: -score(c))
    LOCAL = re.compile(r'(시민|도민|군민|구민|주민|거주|재학|재직|소재|관내|출신)')
    SMALLORG = re.compile(r'(군|구|읍|면|동)(청|청장|의회)?$|문화재단|복지관|도서관|센터$')
    hidden = sorted([c for c in live if c not in short and not c.get('fee') and (c.get('region') or LOCAL.search(c['elig'] or '') or SMALLORG.search((c['org'] or '').strip()))],
                    key=lambda c: -score(c))
    hidden = [c for c in hidden if dday(c['end'])[0] >= 2]
    cats = ''.join(f'<a class="cat" data-c="{s_}" href="/cat/{s_}/"><span class="ic">{CAT_ICON[n]}</span><b>{n}</b><span class="n">{sum(1 for c in live if n in c["tags"])}건</span></a>' for s_, n in CATS)
    # 2026-10-18 사용자: "메인이 너무 난잡 → 테마를 정하고 테마별 맞춤 UI, AI 로그 등 분리, 기획부터 다시"
    # → 메인(/)은 테마 입구(허브)만, 공모전 상담은 /contest/ 로. 유입(src·referrer)에 맞는 테마 입구를 맨 위로 + 루리 안내
    contest_home = f'''<h1 class="cs-h1">🏆 루리 공모전 추천 상담 — 이 공모전이나 해 볼까?</h1>
<section id="consult" aria-label="루리 공모전 추천 상담"><noscript><p>루리 상담은 자바스크립트가 필요해요. 진행 중 공모전 {len(live)}건이 있어요.</p></noscript></section>
{qa_home()}<p class="cs-foot">진행 중 공모전 {len(live)}건(오늘 {TODAY.month}/{TODAY.day} 한국 시간 기준 접수 마감 전 · 제목이 같은 공모전은 1건 · {NOW_KST():%m/%d %H:%M} 갱신)의 마감일·상금·응모 자격·접수 방법과 공식 공고 캡처를 정리해 두고, 루리가 상황에 맞는 것만 골라 드려요.</p>
<link rel="stylesheet" href="/assets/home/consult.css?v=14"><script defer src="/assets/home/consult.js?v=13"></script>'''
    _il = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': f'진행 중 공모전 {YR}', 'numberOfItems': len(live), 'itemListElement': [{'@type': 'ListItem', 'position': k + 1, 'url': f'{SITE}/c/{c["id"]}/', 'name': c['title']} for k, c in enumerate(live_rec[:30])]}
    page('/contest/', '루리 공모전 추천 상담 — 진행 중 공모전 ' + str(len(live)) + '건', f'진행 중인 공모전 {len(live)}건을 마감 임박순·상금순으로. 질문 몇 개면 루리가 딱 맞는 공모전을 골라 드려요.',
         contest_home, [('루리의 줍줍', '/'), ('공모전', '/contest/')], _il)
    nw, an, tk = _rd('news/data.json'), _rd('analyst/data.json'), _rd('talk/data.json')
    # 2026-10-19 사용자 개선 지시: 메인 = 공모전 추천·준비가 중심(소개 → 행동 버튼 → 비교 → 준비 지원 → 이슈·머니·생활은 보조)
    # 숫자에는 집계 범위·단위·중복 제거 기준·갱신 시각을 붙인다. 추천 기준을 밝히고 「맞춤」이라고 부르지 않는다.
    built = NOW_KST().strftime('%Y-%m-%d %H:%M')
    d3 = sum(1 for c in live if 0 <= dday(c['end'])[0] <= 3)
    wk7 = sum(1 for c in live if 0 <= dday(c['end'])[0] <= 7)
    newap = sum(1 for a in aps if a.get('start') and a['start'] >= (TODAY - datetime.timedelta(days=2)).isoformat())
    scope_c = (f'집계: 수집한 공모전 중 오늘({TODAY.month}/{TODAY.day}, 한국 시간) 기준 접수 마감 전인 것'
               + (' · 오늘 마감은 18시 이후 제외' if late else '') + ' · 제목이 같은 공모전(연도·회차 표기 무시)은 1건 · ' + built + ' 갱신')
    pick6 = live_rec[:6]
    def cmp_card(c):
        n, dd = dday(c['end'])
        elig = (c.get('elig') or '').strip()
        reg = c.get('region') or ''
        sub = ' · '.join(x for x in (c.get('effort'), c.get('submit')) if x)
        cls = 'd u3' if n <= 3 else 'd hot' if n <= 7 else 'd'
        return (f'<li><a class="cc" href="/c/{c["id"]}/"><div class="cc-h"><b>{E(c["title"])}</b><span class="{cls}">{dd}</span></div>'
                f'<p class="cc-o">{E(c["org"] or "주최 공고 확인")}</p><dl>'
                f'<dt>분야</dt><dd>{E(" · ".join(c["tags"][:2]) or "공고 확인")}</dd>'
                f'<dt>자격</dt><dd>{E((elig[:40] + ("…" if len(elig) > 40 else "")) or "공식 공고 확인 필요")}{(" · 지역 " + E(reg)) if reg else ""}</dd>'
                f'<dt>마감</dt><dd>{ddot(c["end"])[5:]} <small>(마감 시각은 공식 공고 확인)</small></dd>'
                f'<dt>제출물</dt><dd>{E(sub) or "공식 공고 확인 필요"}</dd>'
                f'<dt>상금</dt><dd>{E(c["prize"]) if c.get("pv") else E(c.get("prize") or "공고 확인")}</dd></dl></a></li>')
    stocks = an.get('stocks', [])
    n_up, n_dn = sum(s_['up'] for s_ in stocks), sum(s_['down'] for s_ in stocks)
    n_rep, n_art = sum(s_['nb'] for s_ in stocks), sum(s_['nn'] for s_ in stocks)
    hot3, _ = hot_live()
    more = [
        ('issue', '/news/', '🕵️', '이슈', (f'언론사 2곳 이상이 다룬 이슈 {len(nw.get("issues", []))}개' if nw.get('issues') else '이슈 정리 준비 중'),
         f'언론사 15곳 RSS 최근 36시간 · 같은 언론사 여러 기사는 1곳 · {nw.get("updated", "갱신 시각 없음")} 갱신'),
        ('money', '/analyst/', '📊', '머니', (f'목표가 상향 {n_up}건 · 하향 {n_dn}건' if stocks else '증권사 의견 정리 준비 중'),
         f'최근 30일 · 종목 {len(stocks)}개 · 리포트 {n_rep}건(증권사·종목별 최신 1건, 여러 기사가 인용해도 1건) · 기사 {n_art}건 · {an.get("updated", "갱신 시각 없음")} 갱신'),
        ('life', '/apply/', '🍳', '생활', f'지원금·청약 신청 가능 {len(aps)}건 · 최근 3일 새 공고 {newap}건',
         f'공공·지자체 공고 중 오늘 기준 신청 마감 전 · {built} 갱신')]
    more_h = ''.join(f'<a class="hm-m hm-{k}" href="{u}"><span>{ic}</span><div><b>{E(n)}</b><p>{E(v)}</p><small>{E(sc)}</small></div></a>' for k, u, ic, n, v, sc in more)
    hot_h = ''.join(f'<li><a href="/hot/{v["slug"]}/">{E(v["title"])}<small> · 언론사 {len(v["outs"])}곳</small></a></li>' for v in hot3[:3])
    home = f'''<section class="hm-hero"><h1>나에게 맞는 공모전을 찾고,<br>마감 전에 준비하세요.</h1>
<p class="hm-sub">진행 중 공모전 <b>{len(live)}건</b>의 분야·자격·마감·제출물을 한 형식으로 정리했어요. 몇 가지 질문에 답하면 조건에 맞는 공모전부터 보여 드려요.</p>
<div class="hm-cta"><a class="hm-b1" href="/contest/">🔎 맞는 공모전 찾기</a><a class="hm-b2" href="/contest/week/">⏰ 마감 임박 보기 <small>7일 안 {wk7}건</small></a></div>
<p class="hm-scope">{E(scope_c)}</p>
<div class="hm-ruri"><img src="/assets/ruri/o_det_wave_s.webp" width="44" height="61" alt=""><p><b>루리</b>사흘 안에 마감하는 공모전이 {d3}건 있어요. 마감 시각은 공고마다 달라서 상세 화면의 공식 공고에서 꼭 확인해 주세요.</p></div></section>
<section class="hm-sec"><h2>📋 지금 볼 만한 공모전 <a href="/contest/">조건으로 찾기 →</a></h2>
<p class="hm-why">고른 기준: 상금 규모 + 마감까지 2~14일 남은 것 + 제출물 정보가 있는 것. 내 조건을 반영한 추천은 「맞는 공모전 찾기」에서 할 수 있어요.</p>
<ul class="hm-cc">{"".join(cmp_card(c) for c in pick6) or '<li class="empty">지금 보여 드릴 공모전이 없어요. 데이터 갱신이 늦어지고 있을 수 있어요.</li>'}</ul>
<p class="hm-more"><a href="/contest/week/">이번 주 마감 전체</a> · <a href="/contest/univ/">대학생 공모전</a> · <a href="/cat/literature/">분야별 보기</a></p></section>
<section class="hm-sec"><h2>🛠️ 준비 지원</h2><div class="hm-prep">
<a href="/prep/"><b>📋 준비실</b><span>마감일에서 거꾸로 짠 준비 일정과 체크리스트</span></a>
<a href="/lab/"><b>🔬 수상 연구소</b><span>슬로건·네이밍 수상작 구조 분석과 내 문구 진단</span></a>
<a href="/guide/"><b>📘 응모 가이드</b><span>제안서·분량·저작권·상금 세금·사기 구별법</span></a></div></section>
<section class="hm-sec"><h2>🧭 다른 정보</h2><div class="hm-more3">{more_h}</div>
{f'<div class="hm-hot"><b>🔥 지금 뜨는 이슈</b><ol>{hot_h}</ol></div>' if hot_h else ''}
<p class="hub-ai"><a href="/all/">☰ 전체 메뉴</a> · <a href="/ailog/">🤖 사람 1명 + AI로 만든 과정</a></p></section>
<section class="hm-sec"><div data-pcrecent="6"></div>
<p class="hm-more"><a href="/plaza/">🗣️ 줍줍 광장 — 내 글 올리기</a> · <a href="/dev/faq/">❓ 개발 FAQ</a></p></section>
<link rel="stylesheet" href="/assets/home/consult.css?v=14">'''
    page('/', '루리의 줍줍 — 나에게 맞는 공모전 찾기·마감 전 준비',
         f'진행 중 공모전 {len(live)}건의 분야·참가 자격·마감일·제출물을 비교하고, 조건에 맞는 공모전을 찾아 준비 일정까지. 이슈·머니·생활 정보도 함께.',
         home, full_title=True, ld={'@context': 'https://schema.org', '@graph': [  # 2026-10-19 구글 검색 결과 사이트 이름·로고
             {'@type': 'WebSite', '@id': SITE + '/#website', 'name': NAME, 'alternateName': ['줍줍', '루리의줍줍', '루리 줍줍'], 'url': SITE + '/', 'publisher': {'@id': SITE + '/#org'}},
             {'@type': 'Organization', '@id': SITE + '/#org', 'name': NAME, 'url': SITE + '/', 'logo': {'@type': 'ImageObject', 'url': SITE + '/assets/icons/icon-512.png', 'width': 512, 'height': 512}}]})
    for s, n in CATS:
        cl = [c for c in live if n in c['tags']]
        tips = ''.join(f'<li>{E(t)}</li>' for t in TIPS[n])
        body = f'''<p class="bc"><a href="/">홈</a> › {n}</p><section class="dh" data-c="{s}"><span class="ic big">{CAT_ICON[n]}</span><h1>{CAT_T.get(n, n + ' 공모전')}</h1><p class="lead">진행 중 <b>{len(cl)}건</b> · 마감 임박순</p><p class="hm-scope">오늘 {TODAY.month}/{TODAY.day}(한국 시간) 기준 접수 마감 전 · 제목이 같은 공모전은 1건 · {NOW_KST():%m/%d %H:%M} 갱신 · 마감 시각은 공식 공고 확인</p></section>
<p>{CAT_INTRO[n]}</p>{cat_stats(n, cl)}
{say(CAT_OUTFIT[n], f'<b>{n} 공모전 응모 팁</b><ul class="chk">{tips}</ul>')}{'<a class="lab-cta" href="/fridge/"><b>🍳 루리의 냉장고 파먹기</b><span>집에 있는 재료로 만들 수 있는 집밥 레시피 · 요리대회 연습용으로 딱 →</span></a>' if s == 'food' else ''}
<h2>진행 중 {n} 공모전</h2>{TOOLBAR}<ul class="list" id="list">{''.join(card(c) for c in cl[:60])}</ul>{('<details class="rest"><summary>나머지 ' + str(len(cl) - 60) + '건 제목으로 보기</summary><ul>' + ''.join(f'<li><a href="/c/{c["id"]}/">{E(c["title"])}</a> · {ddot(c["end"])[5:]} 마감</li>' for c in cl[60:]) + '</ul></details>') if len(cl) > 60 else ''}<p class="hm-links">{' '.join(f'<a href="/cat/{s2}/">{n2}</a>' for s2, n2 in CATS if s2 != s)}</p><button class="more" id="more" hidden>더 보기</button>'''
        fq, ld_ = hub_extra(f'{n} 공모전', sorted(cl, key=lambda c: c['end']), f'/cat/{s}/')
        page(f'/cat/{s}/', f'{CAT_T.get(n, n + " 공모전 모음")} · 진행 중 {len(cl)}건', f'{n} 분야 진행 중 공모전 {len(cl)}건 마감 임박순 정리. {CAT_INTRO[n][:70]}',
             body + fq + listing_js(n), [('루리의 줍줍', '/'), (n, f'/cat/{s}/')], ld_)
    # 2026-10-18 사용자: "경품 이벤트도 좀 적당히 보이게, 갱신도 자동으로" — 1,300여 건 통째 나열 대신 '오늘·내일 마감 + 쉬운 것' 12개만 크게, 나머지는 종류·검색으로(events.json 매시 빌드 갱신)
    EZT = ('댓글 1줄', '퀴즈 1분', '설문 5분', '응모만', '폼 1분')
    tidy_ev = lambda t: re.sub(r'^\s*\((?:중복|\d+회 중복)[^)]*\)\s*', '', t).strip()
    top = sorted([e for e in events if dday(e['end'])[0] <= 1 and (e.get('effort') or EASY.get(e['type'], '')) in EZT and (e.get('org') or '').strip()],
                 key=lambda e: (e['end'], EASY_RANK.get(e.get('effort') or EASY.get(e['type'], ''), 2)))[:12]
    if len(top) < 12:
        top += [e for e in sorted(events, key=lambda e: e['end']) if e not in top and (e.get('effort') or EASY.get(e['type'], '')) in EZT][:12 - len(top)]
    tcards = ''.join(f'<li><a href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><b>{E(tidy_ev(e["title"]))}</b><span><em class="{"u" if dday(e["end"])[0] <= 1 else ""}">{dday(e["end"])[1]}</em>{E(e["org"] or "공식 계정")} · <i>{E(e.get("effort") or EASY.get(e["type"], e["type"]))}</i></span></a></li>' for e in top)
    page('/event/', f'경품 이벤트 — 오늘 마감·쉬운 것부터 (진행 중 {len(events)}건)', f'댓글 1줄·퀴즈·설문·응모만 하면 되는 경품 이벤트 {len(events)}건. 오늘·내일 마감하는 쉬운 이벤트부터, 종류별·검색으로 골라 보세요. 매시간 갱신.',
         f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">생활</a> › 경품 이벤트</p><h1>🎁 경품 이벤트</h1>
{say('excited', f'오늘·내일 마감하는 쉬운 이벤트부터 골랐어요! 지금 진행 중인 이벤트는 {len(events):,}건이고, 매시간 새로 정리돼요.')}
<section class="ev-top"><h2>⚡ 오늘·내일 마감 · 쉬운 것 {len(top)}</h2><ul class="ev-ul">{tcards}</ul></section>
<h2 class="ev-h">🔎 종류별로 골라 보기</h2><section id="evl" aria-label="경품 이벤트 목록"><noscript>자바스크립트가 필요해요.</noscript></section>
<p class="note">마지막 갱신 {datetime.datetime.now().strftime('%m/%d %H:%M')} · 참여 조건(팔로우·태그·공유)과 당첨자 발표는 이벤트마다 달라요. 당첨 연락을 사칭해 개인정보나 송금을 요구하면 사기예요.</p>
<link rel="stylesheet" href="/assets/event/ev.css?v=1"><script defer src="/assets/event/ev.js?v=1"></script>''', [('루리의 줍줍', '/'), ('생활', '/apply/'), ('경품 이벤트', '/event/')])
    shutil.rmtree(os.path.join(ROOT, 'a'), ignore_errors=True)
    build_apply(aps)
    ss = load_ssul()
    build_ssul(ss, live, aps)
    guides(live)
    qa_pages(live)
    prep_page()
    try:
        import fridge_today   # 오늘 날씨 메뉴(Open-Meteo, 매시 빌드 — 실패하면 이전 파일)
        fridge_today.main()
    except Exception as e:
        print('오늘 날씨 메뉴 실패', repr(e)[:80])
    fr_urls = fridge_page()
    app_page()
    news_page()
    extra_urls = talk_pages() + mag_pages(live, aps) + analyst_pages() + satire_pages() + kw_pages() + money_pages() + apply_rec_page() + tool_pages() + hot_pages()
    import widget
    extra_urls += widget.build(ROOT, live, aps, hot_live()[0], page, say, COMM_API, TODAY)  # 퍼가기 위젯 (2026-10-18 연구 세션 요청)
    extra_urls += region_pages(aps) + contest_hubs(live) + week_hub(live) + cross_pages(aps) + apply_hubs(aps)
    rv_urls, REVIEWS[:] = review_pages()
    extra_urls += rv_urls
    extra_urls += fr_urls
    extra_urls += dev_pages(live) + ailog_page(live, len(extra_urls)) + plaza_page() + all_page()
    community(live)
    lab_urls = lab() or []
    me_pages()
    statics(len(live), len(events))
    urls = ['/', '/contest/', '/apply/', '/event/', '/guide/', '/ssul/'] + lab_urls + [f'/ssul/{x["slug"]}/' for x in ss] + [f'/a/{a["id"]}/' for a in aps] + [f'/cat/{s}/' for s, _ in CATS] + [f'/guide/{g[0]}/' for g in GUIDES] + ['/qa/', '/prep/', '/fridge/', '/app/', '/news/'] + extra_urls + [f'/guide/{q["slug"]}/' for q in QA] + \
           ['/about/', '/privacy/', '/terms/', '/contact/'] + [f'/c/{c["id"]}/' for c in contests]
    gone_pages()
    import finder   # 공모전 자동 자료 찾기 색인·질의 (2026-10-19)
    print('자료 색인', finder.build_index(urls, NOINDEX, {c['id'] for c in live}), '질의', len(finder.build_queries(live, notice_points)))
    print('auto_thin noindex', auto_thin(urls))
    print('얇은 페이지 합침', collapse_thin(urls))
    global NEW_URLS
    sm = os.path.join(ROOT, 'sitemap.xml')
    SENT = os.path.join(HERE, 'indexnow_sent.json')   # 2026-10-19: 로컬 빌드가 먼저 돌아도 새 주소를 놓치지 않게, 실제로 보낸 주소를 기록해서 비교
    old = set(json.load(open(SENT, encoding='utf-8'))) if os.path.exists(SENT) else (set(re.findall(r'<loc>([^<]+)</loc>', open(sm, encoding='utf-8').read())) if os.path.exists(sm) else set())
    NEW_URLS = [SITE + u for u in urls if SITE + u not in old and u not in NOINDEX]
    with open(sm, 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
        LM = os.path.join(HERE, 'lastmod.json')
        lm = json.load(open(LM, encoding='utf-8')) if os.path.exists(LM) else {}
        _lm_old = {k: v[0] for k, v in lm.items()}
        for u in urls:
            h_ = PAGE_HASH.get(u)
            if u not in lm or (h_ and lm[u][0] != h_):
                lm[u] = [h_, TODAY.isoformat()]
        json.dump(lm, open(LM, 'w', encoding='utf-8'), ensure_ascii=False)
        chg = [SITE + u for u in urls if u.startswith('/c/') and u not in NOINDEX and lm[u][1] == TODAY.isoformat() and SITE + u not in NEW_URLS and lm[u][0] != _lm_old.get(u)]
        NEW_URLS.extend(chg[:100])   # 2026-10-19: 바뀐 공모전 상세도 IndexNow 로
        f.writelines(f'<url><loc>{SITE}{u}</loc><lastmod>{lm[u][1]}</lastmod>' + (f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{u}"/>' if u.startswith('/en/') else '') + '</url>\n' for u in urls if u not in NOINDEX)
        f.write('</urlset>\n')
    SMT = [('contest', ('/c/', '/cat/', '/contest/', '/lab/', '/guide/', '/prep/', '/widget/', '/ssul/')), ('apply', ('/a/', '/apply/', '/event/', '/fridge/', '/qa/')),
           ('money', ('/analyst/', '/money/')), ('issue', ('/news/', '/talk/', '/mag/', '/kw/', '/hot/', '/satire/', '/review/'))]
    idx = []
    for nm, pre in SMT + [('etc', None)]:
        L = [u for u in urls if u not in NOINDEX and ((pre and u.startswith(pre)) or (not pre and not any(u.startswith(x) for _, ps in SMT for x in ps)))]
        with open(os.path.join(ROOT, f'sitemap-{nm}.xml'), 'w', encoding='utf-8', newline='\n') as f2:
            f2.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
            f2.writelines(f'<url><loc>{SITE}{u}</loc><lastmod>{lm[u][1]}</lastmod>' + (f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{u}"/>' if u.startswith('/en/') else '') + '</url>\n' for u in L)
            f2.write('</urlset>\n')
        idx.append((nm, max([lm[u][1] for u in L] or [TODAY.isoformat()])))
    with open(os.path.join(ROOT, 'sitemap_index.xml'), 'w', encoding='utf-8', newline='\n') as f2:
        f2.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 + ''.join(f'<sitemap><loc>{SITE}/sitemap-{nm}.xml</loc><lastmod>{d}</lastmod></sitemap>\n' for nm, d in idx) + '</sitemapindex>\n')
    rss_feed(live, aps)
    print('contests', len(contests), 'live', len(live), 'events', len(events), 'urls', len(urls), 'noindex', len(NOINDEX))
    try:
        import health
        hr = health.run(ROOT, urls, NOINDEX)
        print('health', '정상' if not hr['warn'] else hr['warn'])
    except Exception as e:
        print('health fail', e)


GUIDES = [
 ('first', '공모전 처음 응모할 때 꼭 확인할 7가지', '처음 공모전에 응모할 때 요강에서 놓치기 쉬운 응모 자격, 제출 형식, 저작권, 중복 응모, 마감 시각 등 7가지를 정리했습니다.', '''
<p>공모전은 요강을 얼마나 꼼꼼히 읽었는지에서 결과가 갈리는 경우가 많습니다. 작품이 좋아도 형식 미달로 심사에 오르지 못하는 일이 생각보다 흔합니다. 처음 응모한다면 아래 일곱 가지를 순서대로 확인해 보세요.</p>
<h2>1. 응모 자격</h2><p>나이, 거주 지역, 학생 여부, 개인·팀 여부를 먼저 봅니다. 지자체 공모전은 해당 지역 거주자나 생활권 주민만 받는 경우가 많고, 대학생 공모전은 재학 증명서를 요구하기도 합니다.</p>
<h2>2. 제출물 형식</h2><p>분량(글자 수, 원고지 매수, 영상 길이), 파일 형식(HWP·PDF·JPG·MP4), 파일명 규칙을 확인합니다. 지정 양식이 있다면 반드시 그 양식에 작성해야 합니다.</p>
<h2>3. 접수 방법</h2><p>이메일, 홈페이지, 구글폼·네이버폼, SNS 해시태그 등 방식이 다양합니다. 이메일 접수라면 제목 형식을 지정하는 경우가 많고, 첨부 용량 제한도 확인하세요.</p>
<h2>4. 마감 시각</h2><p>마감일 자정이 아니라 오후 6시나 업무 시간 기준인 경우가 있습니다. 해외 공모전은 현지 시간 기준이라 한국 시간으로 바꿔 계산해야 합니다.</p>
<h2>5. 저작권과 활용 조건</h2><p>수상작의 저작권이 주최 측에 귀속되거나, 응모작 전체를 홍보에 활용할 수 있다는 조건이 붙기도 합니다. 내 작품을 다른 곳에 다시 쓰고 싶다면 꼭 읽어 보세요.</p>
<h2>6. 중복 응모·미발표 조건</h2><p>다른 공모전 수상작이나 이미 공개한 작품은 받지 않는 경우가 대부분입니다. 수상 후에도 결격 사유가 밝혀지면 수상이 취소될 수 있습니다.</p>
<h2>7. 생성형 AI 사용 규정</h2><p>최근에는 생성형 AI 사용을 금지하거나, 사용 시 표기를 요구하는 공모전이 늘고 있습니다. 규정이 없더라도 애매하면 주최 측에 문의하는 것이 안전합니다.</p>'''),
 ('proposal', '정책·아이디어 제안서 쓰는 법', '지자체·공공기관 정책 제안과 아이디어 공모전에서 쓰는 제안서 구조(현황, 문제점, 개선안, 기대효과)와 작성 요령을 정리했습니다.', '''
<p>정책 제안·아이디어 공모전은 글솜씨보다 <b>구조</b>가 중요합니다. 심사위원은 많은 제안서를 짧은 시간에 읽기 때문에, 무엇이 문제이고 무엇을 바꾸자는 것인지가 첫 페이지에서 보여야 합니다.</p>
<h2>기본 구조</h2><ul class="chk"><li><b>제목</b>: 제안 내용을 한 줄로. 예) "버스정류장 도착 안내를 마을버스까지 확대"</li><li><b>현황</b>: 지금 어떻게 운영되고 있는지 사실 위주로</li><li><b>문제점</b>: 누가, 언제, 어떤 불편을 겪는지 구체적으로</li><li><b>개선안</b>: 무엇을 어떻게 바꿀지, 실행 주체와 단계</li><li><b>기대효과</b>: 수혜 대상과 효과(가능하면 숫자로)</li><li><b>소요 예산·추진 일정</b>: 대략이라도 제시하면 실현 가능성 평가에 유리</li></ul>
<h2>좋은 제안의 조건</h2><p>이미 시행 중인 정책과 겹치지 않아야 합니다. 제안 전에 해당 기관 홈페이지와 보도자료를 검색해 비슷한 사업이 있는지 확인하고, 있다면 그것과 무엇이 다른지 적으세요. 다른 지자체의 성공 사례를 근거로 들면 설득력이 높아집니다.</p>
<h2>접수 창구</h2><p>국민신문고(국민제안), 국민생각함, 각 지자체 홈페이지 제안 게시판으로 받는 경우가 많습니다. 본인인증이 필요한 창구가 많으니 마감 직전보다 여유 있게 제출하세요.</p>'''),
 ('writing', '수기·문학 공모전에서 눈에 띄는 글 쓰기', '수기, 수필, 시, 네이밍·슬로건 공모전에서 심사위원 눈에 띄는 글의 공통점과 분량·형식 맞추는 요령.', '''
<p>수기·문학 공모전은 응모작이 많아 첫 문단에서 인상이 결정되는 경우가 많습니다. 다음 원칙을 기억해 두세요.</p>
<h2>수기·수필</h2><p>주제를 설명하기보다 <b>장면</b>으로 보여 주세요. "도움을 받아 감사했다"보다 그날의 날씨, 들은 말, 손에 쥐고 있던 물건을 쓰는 편이 훨씬 오래 기억됩니다. 주최 기관의 사업(예: 장기요양, 안전, 환경)과 내 경험이 만나는 지점을 분명히 하세요.</p>
<h2>시</h2><p>주제어를 그대로 반복하기보다 구체적인 사물과 이미지로 바꿔 보세요. 분량 제한(편수, 행 수)을 지키는 것이 기본입니다.</p>
<h2>네이밍·슬로건</h2><p>짧고, 소리 내어 읽기 쉽고, 주최 측이 내세우려는 가치를 담아야 합니다. 후보를 여러 개 만든 뒤 기존 상표·슬로건과 겹치는지 검색해 보세요. 의미 설명을 한두 줄 붙이게 하는 공모전이 많습니다.</p>
<h2>형식</h2><p>원고지 매수 기준이라면 200자 원고지 환산 분량을, 글자 수 기준이라면 공백 포함 여부를 확인하세요. 지정 서식(HWP)이 있으면 글꼴과 줄 간격까지 그대로 두는 것이 안전합니다.</p>'''),
 ('prize', '공모전 상금 수령과 당첨 연락 확인법', '공모전 상금을 받을 때 필요한 서류, 제세공과금 공제, 당첨 사칭 연락을 구별하는 방법을 정리했습니다.', '''
<h2>상금 지급 절차</h2><p>수상자로 선정되면 주최 측이 신분증 사본, 통장 사본, 개인정보 동의서 등을 요청하는 것이 일반적입니다. 상금은 대개 제세공과금(기타소득세 등)을 원천징수한 뒤 지급되므로 공고에 적힌 금액보다 적게 입금될 수 있습니다. 공제 기준은 주최 측과 상금 성격에 따라 다르니 안내를 확인하세요.</p>
<h2>팀 수상</h2><p>팀으로 수상하면 대표자 계좌로 한 번에 지급하는 경우가 많습니다. 미리 팀원끼리 배분 방식을 정해 두면 분쟁을 줄일 수 있습니다.</p>
<h2>당첨 사칭 주의</h2><p>"당첨되었으니 수수료나 세금을 먼저 입금하라"는 연락은 사기일 가능성이 높습니다. 정상적인 공모전은 상금에서 세금을 공제하고 지급하며, 응모자에게 먼저 돈을 보내라고 하지 않습니다. 발표는 반드시 주최 기관의 공식 홈페이지나 공식 SNS 계정에서 다시 확인하세요.</p>
<h2>발표 확인</h2><p>발표일을 메모해 두고, 발표 방법(홈페이지 게시, 개별 연락, SNS 댓글)을 확인해 두세요. 연락이 닿지 않으면 수상이 취소되는 공모전도 있습니다.</p>'''),
 ('unemployment-2026', '실업급여 조건 2026 — 받을 수 있는 사람·금액·기간·신청 방법', '실업급여(구직급여) 2026 조건: 고용보험 가입 기간 180일, 비자발적 이직, 하루 상한 68,100원, 지급 기간 120~270일, 고용24 신청 순서를 정리했어요.', '''
<p class="note">기준일 2026-10-19 · 고용노동부 고용24 안내 기준으로 정리한 일반 정보예요. 내 경우에 해당하는지는 고용센터(국번 없이 1350)에서 확인하는 게 가장 정확해요.</p>
<h2>1. 실업급여 신청자격</h2><ul class="chk"><li><b>가입 기간:</b> 이직일 전 18개월 동안 고용보험 피보험 단위기간이 180일 이상이어야 해요(주 15시간 미만 초단시간 근로자 등은 기준이 달라요).</li>
<li><b>비자발적 이직:</b> 권고사직·계약 기간 만료·폐업처럼 본인 뜻이 아닌 퇴사여야 해요. 자진 퇴사라도 임금 체불, 통근이 어려워진 이사, 직장 내 괴롭힘처럼 정당한 사유가 인정되면 받을 수 있어요.</li>
<li><b>재취업 의사와 노력:</b> 일할 의사와 능력이 있고, 수급 기간 동안 구직 활동을 해야 해요.</li><li><b>신청 기한:</b> 이직 다음 날부터 12개월이 지나면 남은 날이 있어도 받을 수 없어요. 퇴사 후 되도록 빨리 신청하세요.</li></ul>
<h2>2. 실업급여 계산기로 미리 계산</h2><p>퇴직 전 3개월 급여, 가입 기간, 나이를 넣으면 <a href="/money/tools/unemployment/">실업급여 계산기</a>가 하루 금액과 총액을 계산해요(참고용).</p><h2>3. 실업급여 금액</h2><p>하루 금액은 퇴직 전 평균임금의 60%예요. 다만 2026년 1월 1일 이후 이직하면 <b>하루 상한 68,100원</b>이고, 하한은 최저임금의 80%(하루 8시간 기준 66,048원)예요. 계산은 <a href="/money/tools/unemployment/">실업급여 계산기</a>로 해 볼 수 있어요(참고용).</p>
<h2>4. 실업급여 기간</h2><table class="info"><tr><th>가입 기간</th><th>50세 미만</th><th>50세 이상·장애인</th></tr><tr><td>1년 미만</td><td>120일</td><td>120일</td></tr><tr><td>1~3년</td><td>150일</td><td>180일</td></tr><tr><td>3~5년</td><td>180일</td><td>210일</td></tr><tr><td>5~10년</td><td>210일</td><td>240일</td></tr><tr><td>10년 이상</td><td>240일</td><td>270일</td></tr></table>
<h2>5. 실업급여 신청방법</h2><ol><li>회사가 이직확인서를 고용센터에 냈는지 확인해요.</li><li>고용24(www.work24.go.kr)에서 구직 등록을 해요.</li><li>온라인 수급자격 신청자 교육을 들어요.</li><li>거주지 관할 고용센터에 수급자격 인정 신청을 해요.</li><li>정해진 날마다 실업 인정(구직 활동 보고)을 하면 지급돼요.</li></ol>
<h2>6. 자주 헷갈리는 것</h2><ul class="chk"><li>65세 이후 새로 취업한 경우는 원칙적으로 받을 수 없어요(65세 전부터 계속 일한 경우는 가능).</li><li>수급 중 아르바이트로 소득이 생기면 반드시 신고해야 해요. 신고하지 않으면 부정 수급이 돼요.</li><li>퇴직금은 실업급여와 별개라 둘 다 받을 수 있어요. <a href="/money/tools/severance/">퇴직금 계산기</a>로 먼저 확인해 보세요.</li></ul>'''),
 ('contest-sites', '공모전 사이트 추천·비교 — 어디서 찾고 어떻게 고를까', '공모전 사이트 추천: 콘테스트코리아·위비티·링커리어·씽굿·올콘 같은 공모전 정보 사이트 특징과, 여러 사이트 공고를 한 번에 비교하는 방법을 정리했어요.', '''
<p>공모전 정보는 여러 사이트에 흩어져 있어서, 같은 공모전이 사이트마다 조금씩 다른 제목으로 올라오기도 해요. 사이트마다 강점이 달라서 한 곳만 보면 놓치는 공고가 생겨요.</p>
<h2>대표적인 공모전 정보 사이트</h2><table class="info"><tr><th>사이트</th><th>특징</th></tr><tr><td>콘테스트코리아</td><td>분야별 공모전 목록이 오래 쌓인 대형 공모전 포털이에요. 청소년·대학생·일반 분야 구분이 잘 되어 있어요.</td></tr>
<tr><td>위비티</td><td>공모전과 대외활동을 함께 다루고, 분야별 목록과 마감 순 정렬이 편해요.</td></tr><tr><td>링커리어</td><td>대학생 대외활동·인턴·공모전을 함께 보여 줘요. 대학생 대상 공고를 찾을 때 많이 써요.</td></tr>
<tr><td>씽굿</td><td>공모전 전문 사이트로, 공모전 운영 대행 공고도 함께 올라와요.</td></tr><tr><td>올콘</td><td>공모전·대외활동 일정을 목록으로 모아 보여 줘요.</td></tr></table>
<p class="note">사이트 특징은 2026년 10월 기준 일반적인 이용 방식으로 정리했어요. 공고의 최종 기준은 언제나 주최 기관의 공식 공고예요.</p>
<h2>고를 때 기준</h2><ul class="chk"><li><b>마감일과 마감 시각:</b> 사이트 목록의 마감일과 공식 공고가 다를 때가 있어요. 접수 전 공식 공고에서 다시 확인하세요.</li><li><b>자격:</b> 지역 거주·재학 조건이 있는 공모전은 경쟁이 덜한 편이라 해당되면 먼저 보세요.</li><li><b>준비 시간:</b> 슬로건·사진은 짧게, 영상·기획서는 2주 이상 잡으세요.</li><li><b>참가비·저작권:</b> 참가비를 받거나 저작권을 통째로 넘기는 조건이면 한 번 더 따져 보세요.</li></ul>
<h2>루리의 줍줍에서는</h2><p>여러 사이트에 올라온 공고를 모아 같은 공모전은 하나로 합치고, 분야·자격·마감·제출물을 같은 형식으로 정리해요. <a href="/contest/">맞는 공모전 찾기</a>에서 조건을 고르면 추천 이유와 함께 보여 주고, 공모전마다 「자동 자료 찾기」로 관련 수상작·가이드를 찾아 줘요.</p>'''),
 ('idea-proposal-form', '아이디어 공모전 기획서 양식 — 순서·분량·ppt 구성', '아이디어 공모전 기획서·제안서 양식: 표지부터 요약, 현황·문제, 아이디어, 실행 계획, 기대효과까지 순서와 분량, ppt로 낼 때 장 구성을 정리했어요.', '''
<p>아이디어 공모전은 양식을 주는 곳이 많아요. 주최 측 양식이 있으면 반드시 그 양식을 쓰고, 칸과 순서를 바꾸지 않는 게 기본이에요. 양식이 없을 때 쓸 수 있는 기본 구성을 정리했어요.</p>
<h2>기본 순서</h2><ol><li><b>제목·한 줄 요약:</b> 무엇을 누구에게 어떻게 바꾸는지 한 문장으로.</li><li><b>현황과 문제:</b> 공공 통계나 기사로 숫자 하나를 근거로 들어요(출처 표기).</li><li><b>아이디어:</b> 핵심 기능 2~3개, 그림이나 흐름도 한 장.</li><li><b>실행 방법:</b> 누가, 어떤 순서로, 얼마의 비용으로.</li><li><b>기대효과:</b> 숫자로 쓸 수 있는 것과 없는 것을 나눠요.</li><li><b>차별점:</b> 이미 시행 중인 정책·서비스와 다른 점.</li></ol>
<h2>분량</h2><p>요강에 분량(A4 몇 장, 글자 수)이 있으면 그 안에서 맞추고, 없으면 A4 3~5장 정도가 심사위원이 읽기 편해요. 요약은 첫 장 맨 위에 두세요.</p>
<h2>ppt로 낼 때</h2><p>10장 안팎으로: 표지 → 요약 → 문제 2장 → 아이디어 3장 → 실행·예산 2장 → 기대효과 → 마무리. 한 장에 메시지 하나, 글자는 줄이고 그림을 늘려요. PDF로 바꿔 내면 글꼴이 깨지지 않아요.</p>
<h2>제출 전 점검</h2><ul class="chk"><li>파일 이름 규칙(예: 공모전명_이름)을 지켰나요?</li><li>개인정보(이름·학교)를 넣지 말라는 블라인드 심사인지 확인했나요?</li><li>인용한 통계·사진의 출처를 적었나요?</li></ul>'''),
 ('character-panel', '캐릭터 공모전 판넬 만드는 법 — 구성·크기·제출 전 점검', '캐릭터 공모전 판넬(제출용 한 장) 구성: 기본형, 3면도, 응용 동작, 컬러 칩, 기획 의도, 활용 예시 배치와 파일 크기·해상도 점검 목록을 정리했어요.', '''
<p>캐릭터·마스코트 공모전은 대부분 「판넬」이라고 부르는 한 장짜리 제출 이미지를 받아요. 심사위원이 이 한 장으로 캐릭터를 이해하니 배치가 중요해요. 크기·형식은 공고마다 다르니 공고 기준이 먼저예요.</p>
<h2>판넬에 들어가는 것</h2><ol><li><b>캐릭터 이름과 한 줄 소개</b></li><li><b>기본형:</b> 가장 크게, 정면 전신.</li><li><b>3면도:</b> 정면·측면·뒷면(공고에서 요구하면).</li><li><b>응용 동작 3~5개:</b> 인사, 기쁨, 응원처럼 실제로 쓸 장면.</li><li><b>컬러 칩:</b> 주요 색 3~5개와 색 값.</li><li><b>기획 의도:</b> 주최 기관·지역과 연결되는 이유를 3~4줄로.</li><li><b>활용 예시:</b> 굿즈·현수막·SNS에 넣은 모습 1~2개.</li></ol>
<h2>크기·형식 점검</h2><ul class="chk"><li>공고에 크기가 없으면 A3·300dpi가 무난하고, 미리보기용 JPG와 원본(AI·PSD) 제출 여부를 확인하세요.</li><li>기존 캐릭터와 닮았다는 지적을 받지 않도록 비슷한 캐릭터를 미리 검색해 보세요.</li><li>AI 도구 사용 허용 여부와 「AI 사용 표기」 규정을 확인하세요.</li><li>수상 시 저작권이 주최 측으로 넘어가는지 공고의 저작권 조항을 읽어 두세요.</li></ul>
<p>진행 중인 캐릭터 공모전은 <a href="/contest/character/">캐릭터 공모전 모음</a>에서 마감순으로 볼 수 있어요.</p>'''),
]
_GX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guides_extra.json')  # 지식인 고민 해결 글(연구 세션이 추가)
# 고민 해결(/qa/ 목록, 글은 /guide/<slug>/ 유지 — 지식인 답변 링크). 항목: [slug, 제목, 요약, 본문HTML] 또는 {slug,title,desc,body,icon,tag}
QA = []
if os.path.exists(_GX):
    for g in json.load(open(_GX, encoding='utf-8')):
        g = g if isinstance(g, dict) else dict(zip(('slug', 'title', 'desc', 'body'), g))
        QA.append({'slug': g['slug'], 'title': g['title'], 'desc': g.get('desc', ''), 'body': g.get('body', ''), 'icon': g.get('icon') or '💬', 'tag': g.get('tag', '')})
    QA.reverse()  # 새 글이 위로


# ---- 썰 코너 (본문은 공모전 세션이 바탕화면 공모전_2026\daily\ssul\<slug>.md 로 씀) ----
# md 맨 위 머리말:  ---\ntitle: 제목\ndate: 2026-10-17\nsummary: 한 줄 요약\nfacts: Q00123, Q00456\nexpr: o_cardigan\n---\n본문(마크다운)
SSUL_DIR = r'C:\Users\k\Desktop\공모전_2026\daily\ssul'


def load_ssul():
    import markdown
    out = []
    if not os.path.isdir(SSUL_DIR):
        return out
    for f in sorted(os.listdir(SSUL_DIR)):
        if not f.endswith('.md'):
            continue
        slug = re.sub(r'[^0-9A-Za-z가-힣_-]', '', f[:-3])[:60]
        raw = open(os.path.join(SSUL_DIR, f), encoding='utf-8').read().replace('\r\n', '\n')
        meta, body = {}, raw
        m = re.match(r'---\n(.*?)\n---\n', raw, re.S)
        if m:
            for line in m.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1); meta[k.strip()] = v.strip()
            body = raw[m.end():]
        if not meta.get('title') or meta.get('draft') in ('true', '1'):
            continue
        html_ = markdown.markdown(html.escape(body, quote=False), extensions=['extra', 'nl2br'])
        out.append({'slug': slug, 'title': meta['title'][:80], 'date': meta.get('date', ''), 'summary': meta.get('summary', '')[:140],
                    'facts': [x.strip() for x in re.split(r'[,\s]+', meta.get('facts', '')) if x.strip()],
                    'expr': meta.get('expr', 'o_cardigan') if re.fullmatch(r'[a-z_]+', meta.get('expr', 'x')) else 'o_cardigan', 'html': html_})
    out.sort(key=lambda x: x['date'], reverse=True)
    return out


def build_ssul(ss, live, aps):
    shutil.rmtree(os.path.join(ROOT, 'ssul'), ignore_errors=True)
    byc = {c['id']: c for c in live}; bya = {a['id']: a for a in aps}
    for x in ss:
        rel = ''.join(card(byc[i]) for i in x['facts'] if i in byc) + ''.join(ap_card(bya[i]) for i in x['facts'] if i in bya)
        tail = (f'<h2>루리가 골라 둔 진짜 기회</h2><ul class="list">{rel}</ul>' if rel else
                '<h2>지금 낼 수 있는 대회</h2><p><a href="/">바로 낼 수 있는 대회 보러 가기 →</a></p>')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/ssul/">썰</a></p>
<article class="ssul"><p class="note">{E(x["date"])}</p><h1>{E(x["title"])}</h1>{say(x["expr"], E(x["summary"]) or "루리가 들려주는 이야기예요.")}{x["html"]}</article>{tail}'''
        page(f'/ssul/{x["slug"]}/', x['title'], x['summary'] or x['title'], body,
             [('루리의 줍줍', '/'), ('썰', '/ssul/'), (x['title'], f'/ssul/{x["slug"]}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': x['title'], 'datePublished': x['date'] or str(TODAY),
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})
    li = ''.join(f'<li><a class="card" data-c="guide" href="/ssul/{x["slug"]}/"><span class="ic">💬</span><div class="cb"><h3 class="t">{E(x["title"])}</h3><p class="o">{E(x["summary"])}</p></div></a></li>' for x in ss) \
        or '<li class="empty"><img src="/assets/ruri/o_cardigan_s.webp" width="64" height="88" alt=""><p>루리가 첫 이야기를 준비하고 있어요!</p></li>'
    page('/ssul/', '루리의 썰', '루리가 들려주는 용돈·공모전 이야기. 이야기 끝에 실제로 낼 수 있는 대회를 이어 드려요.',
         f'''<p class="bc"><a href="/">홈</a> › 썰</p><section class="dh" data-c="guide"><span class="ic big">💬</span><h1>루리의 썰</h1><p class="lead">이야기 끝에 진짜 낼 수 있는 대회가 이어져요</p></section>
{say("o_cardigan", "오늘은 무슨 얘기 해 볼까요? 재밌게 읽고, 마음에 드는 대회는 바로 넣어 봐요!")}<ul class="list">{li}</ul>''',
         [('루리의 줍줍', '/'), ('썰', '/ssul/')])


def prep_page():
    # 루리의 준비실 (2026-10-18 사용자: 공모전 준비할 사람들이 더 편하게 준비할 공간 + 꿀팁 공유)
    G = json.load(open(os.path.join(ROOT, 'assets', 'prep', 'data.json'), encoding='utf-8'))['genres']
    seed = ''.join(f'<li class="tp-ruri"><span class="tp-who">{g["icon"]} {E(g["name"])}</span><p>{E(x)}</p></li>' for g in G for x in g['tips'][:2])
    body = f'''<p class="bc"><a href="/">홈</a> › 준비실</p><h1>📋 루리의 공모전 준비실</h1>
{say("o_desk", "공모전 하나 고르면 마감일에 맞춰 할 일을 날짜별로 짜 드릴게요. 체크하면서 따라오기만 하면 돼요!")}
<section id="prep" aria-label="공모전 준비 보드">
<h2>🧰 준비 도구</h2><div class="pp-tools"><div class="pp-tool"><h3>📏 분량 계산기 <small>글자 수·원고지 매수·A4 쪽수</small></h3><div id="pp-count"><noscript>자바스크립트가 필요해요.</noscript></div></div>
<div class="pp-links"><a href="/lab/#diag"><b>🏆 내 문구 진단</b>슬로건·네이밍을 수상작 공식과 비교</a><a href="/lab/"><b>🔬 수상 연구소</b>실제 수상작과 분석</a><a href="/community/"><b>🚩 원정대</b>같이 할 팀원 찾기</a><a href="/qa/"><b>💬 고민 해결</b>준비하다 막힌 것들</a></div></div>
<section id="tips"><h2>🍯 장르별 공모전 꿀팁 <small>루리 팁 + 회원들이 직접 나눈 팁</small></h2><div class="tp-chips"></div><ul class="tp-list">{seed}</ul><div class="tp-form"></div></section>
</section><link rel="stylesheet" href="/assets/prep/prep.css?v=3"><script defer src="/assets/prep/prep.js?v=3"></script>'''
    page('/prep/', '루리의 공모전 준비실 — 마감 역산 일정·체크리스트·꿀팁', '공모전을 고르면 마감일에 맞춘 준비 일정과 장르별 체크리스트를 만들어 줘요. 슬로건·수기·디자인·영상·사진·정책 제안 꿀팁과 분량 계산기까지.',
         body, [('루리의 줍줍', '/'), ('준비실', '/prep/')])


KDAY = '월화수목금토일'
GRADE = {'ok': ('✅', '확인 신호 많음'), 'warn': ('🟡', '추가 확인 필요'), 'bad': ('🔴', '주의 신호')}


def kdate(d):
    d = datetime.date.fromisoformat(d) if isinstance(d, str) else d
    return f'{d.month}월 {d.day}일({KDAY[d.weekday()]})'


TALK_NOTE = '<p class="tk-warn">💬 커뮤니티 반응을 정리한 것이며 사실 확인 전이에요. 원문은 각 커뮤니티 글이고, 언론 보도 여부를 함께 표시해요.</p>'


def talk_issue(x, day):
    n = x.get('news')
    if n and day == TODAY.isoformat():
        g = GRADE.get(n.get('g'), ('', ''))[0]
        sc = n.get('s') if n.get('s') is not None else ''
        nw = f'<a class="tk-news" href="/news/#is{n["n"]}">📰 언론사 {n["on"]}곳 보도 · 확인 신호 {g} {sc}점 →</a>'
    elif n:
        nw = '<span class="tk-news">📰 언론에도 보도됨</span>'
    else:
        nw = '<span class="tk-nn">📰 언론 미확인 · 커뮤니티에서만 도는 이야기</span>'
    pr = ''.join(f'<a href="{E(p["u"])}"><em>{E(p["k"])}</em><b>{E(p["t"])}</b></a>' for p in x.get('pr') or [])
    prh = f'<div class="nw-pr"><small>📌 관련 있는 줍줍</small>{pr}</div>' if pr else ''
    posts = ''.join(f'<li><a href="{E(p["u"])}" target="_blank" rel="noopener nofollow ugc"><em>{E(p["s"])}</em>{E(p["t"])}</a><small>💬 {p["nc"]}</small></li>' for p in x['posts'])
    kw = ''.join(f'<span>#{E(k)}</span>' for k in x['kw'][:5])
    sm = '<br>'.join(E(l) for l in x['sum'])
    return (f'<article class="tk-is" id="t{x["n"]}"><div class="tk-r">{x["n"] + 1}</div><div class="tk-b"><p class="tk-m"><span class="tk-hot">🔥 {x["nsite"]}개 커뮤니티</span><span>댓글 {x["nc"]:,}</span></p>'
            f'<h2>{E(x["t"])}</h2><p class="tk-s">{sm}</p><p class="tk-kw">{kw}</p>{nw}{prh}'
            f'<details><summary>커뮤니티 원문 {len(x["posts"])}건</summary><ul class="tk-ps">{posts}</ul></details></div></article>')


def talk_pages():
    # 루리의 커뮤니티 이슈 (2026-10-18 사용자 승인: "서로 이야기하면서 만들어, 매거진이랑", "정보성으로") — 매시 talk.py, 날짜별 아카이브
    ad = os.path.join(ROOT, 'talk', 'archive')
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True) if os.path.isdir(ad) else []
    if not days:
        return []
    arch = '<section class="tk-arch"><h2>📅 날짜별 커뮤니티 이슈</h2><p>' + ''.join(f'<a href="/talk/{d}/">{kdate(d)}</a>' for d in days[:60]) + '</p></section>'
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><link rel="stylesheet" href="/assets/news/news.css?v=6">'
    note = '<p class="note">순위는 여러 커뮤니티에 동시에 뜬 정도·댓글 수·인기글에 머문 시간으로 매겨요. 성·혐오·개인 신상·비방·사생활 폭로성 글은 모으지 않아요. 요약은 루리가 제목과 수치만 보고 정리했어요.</p>'
    urls = ['/talk/']
    for i, d in enumerate(days):
        x = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        iss = x.get('issues', [])
        st = ' · 매시간 갱신' if i == 0 else ' · 확정'
        head = (f'<div class="tk-hero"><img src="/assets/ruri/o_det_think.webp" width="300" height="415" alt="커뮤니티 이슈를 정리하는 루리"><div><small>{E(x["updated"])} 기준{st}</small>'
                f'<b>{kdate(d)} 커뮤니티 이슈 TOP{len(iss)}</b><p>커뮤니티 {x.get("sites", 0)}곳 인기글 {x.get("npost", 0):,}건을 같은 화제끼리 묶어, 몇 곳에서 동시에 떴는지로 순위를 매겼어요.</p></div></div>')
        body = head + TALK_NOTE + ''.join(talk_issue(y, d) for y in iss) + arch + note + css
        dsc = f'{kdate(d)} 커뮤니티 13곳 인기글을 화제별로 묶은 이슈 순위: ' + ', '.join(y['t'] for y in iss[:3])
        if i == 0:
            page('/talk/', '루리의 커뮤니티 이슈 — 지금 여러 커뮤니티에서 동시에 뜨는 화제', dsc,
                 '<p class="bc"><a href="/">홈</a> › 커뮤니티 이슈</p><h1>💬 루리의 커뮤니티 이슈</h1>' + body, [('루리의 줍줍', '/'), ('커뮤니티 이슈', '/talk/')])
        page(f'/talk/{d}/', f'{kdate(d)} 커뮤니티 이슈 TOP{len(iss)} — 더쿠·클리앙·디시 등 지금 뜨는 화제', f'{kdate(d)} 기준 ' + dsc,
             f'<p class="bc"><a href="/">홈</a> › <a href="/talk/">커뮤니티 이슈</a> › {kdate(d)}</p><h1>💬 {kdate(d)} 커뮤니티 이슈</h1>' + body,
             [('루리의 줍줍', '/'), ('커뮤니티 이슈', '/talk/'), (kdate(d), f'/talk/{d}/')])
        urls.append(f'/talk/{d}/')
    return urls


MAG0 = datetime.date(2026, 10, 18)


def _rd(p):
    try:
        return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
    except Exception:
        return {}


def mag_snapshot(live, aps):
    """오늘 호 재료를 mag/archive/YYYY-MM-DD.json 에 저장(매 빌드 갱신, 자정 지나면 그날 호 확정)."""
    md = os.path.join(ROOT, 'mag', 'archive')
    os.makedirs(md, exist_ok=True)
    nw, tk = _rd('news/data.json'), _rd('talk/data.json')
    I = {a['id']: a for a in nw.get('items', [])}
    pol = []
    for x in nw.get('issues', []):
        if x.get('c') != '정치':
            continue
        a0 = I.get(x['a'][0]) or {}
        pol.append({'t': x['t'], 'on': x['on'], 's': x.get('s'), 'g': x.get('g'), 'claim': x.get('claim', 0), 'cf': x.get('cf') or [], 'u': a0.get('u', ''), 'o': a0.get('o', ''), 'n': x['n']})
    pol = pol[:3]
    talk = [{'t': x['t'], 'nsite': x['nsite'], 'nc': x['nc'], 'sum': x['sum'][0], 'n': x['n'], 'news': bool(x.get('news'))} for x in tk.get('issues', [])][:5]
    soon = sorted([c for c in live if 1 <= dday(c['end'])[0] <= 3], key=lambda c: -(c.get('pv') or 0))[:3]
    con = [{'id': c['id'], 't': c['title'], 'p': c.get('prize', ''), 'e': c['end']} for c in soon]
    new = []
    for a in aps:
        try:
            if a.get('start') and (TODAY - datetime.date.fromisoformat(a['start'])).days in (0, 1, 2):
                new.append(a)
        except Exception:
            pass
    new = sorted(new, key=lambda a: a['start'], reverse=True)[:5]
    apl = [{'id': a['id'], 't': a['title'], 'k': a.get('kind', ''), 'e': a.get('end', '')} for a in new]
    R = _rd('assets/fridge/recipes.json').get('recipes', [])
    mn = R[(TODAY - MAG0).days * 7 % len(R)] if R else None
    snap = {'date': TODAY.isoformat(), 'no': (TODAY - MAG0).days + 1, 'updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'pol': pol, 'talk': talk, 'con': con, 'apl': apl,
            'menu': {'n': mn['n'], 'e': mn['e'], 'm': mn['m'], 'need': mn['need'], 's': mn['s']} if mn else None}
    json.dump(snap, open(os.path.join(md, TODAY.isoformat() + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))


LEAD_DIR = r'C:\Users\k\Desktop\공모전_2026\이슈리딩'


def lead_html(d):
    """홍보 세션(연구 ⑂)이 쓰는 「루리의 이슈 리딩」 원고 mag.json + 카드 10장을 매거진 호 맨 위에 그대로 싣는다(2026-10-18 합의)."""
    dd = datetime.date.fromisoformat(d)
    src = os.path.join(LEAD_DIR, f'{dd:%m%d}')
    mj = os.path.join(src, 'mag.json')
    if not os.path.exists(mj):
        return '', None
    try:
        m = json.load(open(mj, encoding='utf-8'))
    except Exception:
        return '', None
    out_dir = os.path.join(ROOT, 'mag', d, 'cards')
    os.makedirs(out_dir, exist_ok=True)
    from PIL import Image
    secs = []
    for i, pg in enumerate(m.get('pages', [])):
        png = os.path.join(src, 'cards', f'{i + 1:02d}.png')
        img = ''
        if os.path.exists(png):
            wp = os.path.join(out_dir, f'{i + 1:02d}.webp')
            if not os.path.exists(wp) or os.path.getmtime(wp) < os.path.getmtime(png):
                Image.open(png).convert('RGB').resize((720, 900), Image.LANCZOS).save(wp, quality=82)
            img = f'<img src="/mag/{d}/cards/{i + 1:02d}.webp" width="720" height="900" alt="{E(pg.get("title", ""))}" loading="{"eager" if i == 0 else "lazy"}">'
        rows = ''.join(f'<li>{E(r)}</li>' for r in pg.get('rows', []))
        say_ = ' '.join(pg.get('say', []))
        secs.append(f'<section class="ld-p">{img}<div class="ld-t">{("<small>" + E(pg["kicker"]) + "</small>") if pg.get("kicker") else ""}<h2>{E(pg.get("title", ""))}</h2>'
                    f'{("<p class=ld-big>" + E(pg["big"]) + "</p>") if pg.get("big") else ""}<ul>{rows}</ul>{("<p class=ld-say>💬 " + E(say_) + "</p>") if say_ else ""}'
                    f'{("<p class=ld-src>출처: " + E(pg["src"]) + "</p>") if pg.get("src") else ""}</div></section>')
    first = (m.get('pages') or [{}])[0].get('title', '')
    return f'<div class="ld">{"".join(secs)}</div><h2 class="ld-more">📌 오늘의 줍줍 모음</h2>', first


def mag_issue_html(m, d):
    is_today = d == TODAY.isoformat()
    sec = []
    if m['pol']:
        li = ''
        for i, x in enumerate(m['pol']):
            g = GRADE.get('bad' if x['cf'] else x['g'], ('', ''))[0]
            sc = x['s'] if x['s'] is not None else ''
            cl = ' · 🗣️ 발언·주장' if x['claim'] else ''
            href = f'/news/#is{x["n"]}' if is_today else E(x['u'])
            ext = '' if is_today else ' target="_blank" rel="noopener nofollow"'
            li += f'<li><a href="{href}"{ext}><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["on"]}곳 보도 · {g} {sc}점{cl}</span></a></li>'
        sec.append(f'<section class="mg-s"><h2>🕵️ 오늘의 정치 이슈 TOP{len(m["pol"])}</h2>' + say('o_det_think', '여러 언론사가 가장 많이 다룬 정치 이슈예요. 점수는 교차 보도·출처·제목-본문 일치로 매긴 확인 신호예요.')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/news/">기사 확인 신호 전체 보기 →</a></section>')
    if m['talk']:
        li = ''
        for i, x in enumerate(m['talk']):
            nb = ' · 📰 언론 보도' if x['news'] else ' · 언론 미확인'
            li += f'<li><a href="/talk/{d}/#t{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["nsite"]}개 커뮤니티 · 댓글 {x["nc"]:,}{nb}</span></a></li>'
        sec.append(f'<section class="mg-s"><h2>💬 커뮤니티 이슈 TOP{len(m["talk"])}</h2>' + say('o_det_wave', '여러 커뮤니티에 동시에 뜬 화제예요. 커뮤니티 반응이라 사실 확인 전이에요!')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/talk/{d}/">커뮤니티 이슈 전체 보기 →</a></section>')
    if m['con']:
        li = ''.join(f'<li><a href="/c/{x["id"]}/"><em>🏆</em><b>{E(x["t"])}</b><span>{E(x["p"] or "상금 공고 확인")} · {x["e"][5:].replace("-", "/")} 마감</span></a></li>' for x in m['con'])
        sec.append('<section class="mg-s"><h2>⏰ 마감 임박 공모전</h2>' + say('o_present', '사흘 안에 마감하는 공모전 중 상금이 큰 것만 골랐어요. 지금 넣어도 늦지 않아요!')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/">공모전 전체 보기 →</a></section>')
    if m['apl']:
        li = ''
        for x in m['apl']:
            e = (' · ~' + x['e'][5:].replace('-', '/')) if x['e'] else ''
            li += f'<li><a href="/a/{x["id"]}/"><em>💰</em><b>{E(x["t"])}</b><span>{E(x["k"])}{e}</span></a></li>'
        sec.append('<section class="mg-s"><h2>💰 새로 열린 지원금·청약</h2>' + say('o_cardigan', '이틀 안에 새로 접수를 시작한 지원금·청약이에요. 조건이 맞는지 확인해 보세요.')
                   + f'<ol class="mg-l">{li}</ol><a class="mg-more" href="/apply/">지원금·청약 전체 보기 →</a></section>')
    if m.get('menu'):
        mn = m['menu']
        steps = ''.join(f'<li>{E(x)}</li>' for x in mn['s'])
        sec.append('<section class="mg-s"><h2>🍳 루리의 오늘 메뉴</h2>' + say('o_cook', f'오늘은 {E(mn["n"])} 어때요? {mn["m"]}분이면 돼요!')
                   + f'<div class="mg-menu"><b>{mn["e"]} {E(mn["n"])}</b><span>필요한 재료: {E(", ".join(mn["need"]))}</span><ol>{steps}</ol></div><a class="mg-more" href="/fridge/">냉장고 재료로 다른 메뉴 찾기 →</a></section>')
    st = '기준 · 오늘 하루 계속 갱신' if is_today else '확정'
    head = (f'<div class="mg-hero"><small>루리의 줍줍 데일리 · 제{m["no"]}호</small><b>{kdate(d)}</b><p>오늘의 정치 이슈 · 커뮤니티 화제 · 마감 임박 공모전 · 새 지원금 · 오늘 메뉴를 한 장에 모았어요.</p>'
            f'<span>{E(m["updated"])} {st}</span></div>')
    lead, _ = lead_html(d)
    return head + lead + ''.join(sec)


def mag_pages(live, aps):
    # 루리의 줍줍 데일리 (2026-10-18 사용자: "매거진이랑 등등으로", "정보성으로") — 하루 한 호, 정적 페이지 + 아카이브
    mag_snapshot(live, aps)
    md = os.path.join(ROOT, 'mag', 'archive')
    days = sorted([f[:-5] for f in os.listdir(md) if f.endswith('.json')], reverse=True)
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    urls, cards = ['/mag/'], []
    for d in days:
        m = json.load(open(os.path.join(md, d + '.json'), encoding='utf-8'))
        _, lt = lead_html(d)
        tops = ([lt] if lt else []) + [x['t'] for x in m['pol'][:1]] + [x['t'] for x in m['talk'][:1]]
        nm = '루리의 이슈 리딩' if lt else '루리의 줍줍 데일리'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/mag/">매거진</a> › {kdate(d)}</p><h1>📰 {nm} {kdate(d)}</h1>' + mag_issue_html(m, d)
                + '<p class="mg-nav"><a href="/mag/">📚 지난 호 모두 보기</a></p>' + css)
        page(f'/mag/{d}/', f'{nm} {kdate(d)} — ' + (lt or '정치 이슈·커뮤니티 화제·마감 공모전'), (f'{kdate(d)} 하루 정보 모음: ' + ' / '.join(tops))[:150], body,
             [('루리의 줍줍', '/'), ('매거진', '/mag/'), (kdate(d), f'/mag/{d}/')])
        urls.append(f'/mag/{d}/')
        cards.append(f'<li><a href="/mag/{d}/"><small>제{m["no"]}호</small><b>{kdate(d)}</b><span>{E(" · ".join(tops))}</span></a></li>')
    page('/mag/', '루리의 줍줍 데일리 — 매일 정보 매거진', '매일 한 장으로 보는 정치 이슈 기사 확인 신호, 커뮤니티 화제, 마감 임박 공모전, 새 지원금·청약, 오늘 메뉴. 루리의 줍줍 데일리 매거진 전체 호.',
         '<p class="bc"><a href="/">홈</a> › 매거진</p><h1>📰 루리의 줍줍 데일리</h1>' + say('o_present', '매일 한 장으로 정리해 드려요. 오늘 호는 하루 동안 계속 새 소식으로 바뀌어요!')
         + f'<ul class="mg-idx">{"".join(cards)}</ul>' + css, [('루리의 줍줍', '/'), ('매거진', '/mag/')])
    return urls


DIRN = {'up': ('🔺', '목표가 상향'), 'down': ('🔻', '목표가 하향'), 'keep': ('➖', '의견 유지'), 'bull': ('🟢', '강세 전망'), 'bear': ('🔴', '약세 전망'), 'neutral': ('⚪', '중립·혼조')}
AN_NOTE = ('<p class="an-warn">📊 증권사 리포트·전문가 전망을 다룬 기사를 모아 다시 정리한 정보예요. 루리의 줍줍이 직접 주가를 예측하거나 매수·매도를 권하지 않아요. '
           '투자 판단과 책임은 본인에게 있어요. 목표가·의견은 각 증권사·기관의 것이며 원문 기사에서 확인해 주세요.</p>')


def won_txt(v):
    if not v:
        return '-'
    return f'{v // 10000:,}만{(" " + format(v % 10000, ",")) if v % 10000 else ""}원' if v >= 10000 else f'{v:,}원'


def an_tree(tree, keys):
    out = ''
    for d in keys:
        rows = tree.get(d) or []
        if not rows:
            continue
        li = ''.join(f'<li><b>{E(r[0])}</b><span>{E(", ".join(r[1]))}{(" 외 " + str(r[2] - len(r[1])) + "건") if len(r) > 2 and r[2] > len(r[1]) else ""}</span></li>' for r in rows[:6])
        out += f'<div class="an-br {d}"><p>{DIRN[d][0]} {DIRN[d][1]} 근거</p><ul>{li}</ul></div>'
    return f'<div class="an-tree">{out}</div>' if out else ''


def an_nodes(nodes, coin=False):
    li = ''
    for n in nodes[:12]:
        dt = datetime.datetime.fromtimestamp(n['ts']).strftime('%m/%d')
        if coin:
            meta = f'{E(n.get("who") or n["o"])}{(" · 목표 " + format(n["tgt"], "g") + "만 달러") if n.get("tgt") else ""}'
        else:
            tp = (f'{won_txt(n["tp0"])} → {won_txt(n["tp"])}' if n.get('tp0') else won_txt(n['tp'])) if n.get('tp') else ''
            meta = f'{E(n["br"])}{(" · " + E(n["op"])) if n.get("op") else ""}{(" · " + tp) if tp else ""}{" · ⚠️ 숫자 확인 필요(평균 제외)" if n.get("chk") else ""}'
        li += (f'<li class="{n["dir"]}"><span class="an-d">{DIRN[n["dir"]][0]}</span><div><small>{dt} · {meta}</small>'
               f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["t"])}</a><em>{E(n["o"])}</em></div></li>')
    return f'<ul class="an-nodes">{li}</ul>'


DCOL = {'up': '#ef4444', 'bull': '#ef4444', 'down': '#3b82f6', 'bear': '#3b82f6', 'keep': '#94a3b8', 'neutral': '#94a3b8'}


def kdate_of(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')


def coin_svg(c):
    """30일 종가 선 + 전망 기사가 나온 날 강세(빨강)·약세(파랑)·혼조(회색) 점을 겹친다."""
    h = c.get('hist') or []
    if len(h) < 5:
        return ''
    W, H, L, R, T, B = 640, 250, 70, 14, 16, 34
    ps = [v for _, v in h]
    lo, hi = min(ps), max(ps)
    pad = (hi - lo) * 0.08 or hi * 0.01
    lo, hi = lo - pad, hi + pad
    X = lambda i: L + (W - L - R) * i / (len(h) - 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    pts = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, (_, v) in enumerate(h))
    area = f'{X(0):.1f},{H - B} ' + pts + f' {X(len(h) - 1):.1f},{H - B}'
    idx = {d: i for i, (d, _) in enumerate(h)}
    dots, stack = '', {}
    for n in c.get('nodes', []):
        i = idx.get(kdate_of(n['ts']))
        if i is None:
            continue
        k = stack[i] = stack.get(i, 0) + 1
        if k > 6:
            continue
        y = Y(h[i][1]) - 11 * k
        dots += f'<circle cx="{X(i):.1f}" cy="{y:.1f}" r="4.5" fill="{DCOL[n["dir"]]}" stroke="#fff" stroke-width="1.5"><title>{E(n["t"])}</title></circle>'
    dots += ''.join(f'<text x="{X(i) - 8:.1f}" y="{Y(h[i][1]) - 80:.1f}" text-anchor="end" class="lb">+{k - 6}</text>' for i, k in stack.items() if k > 6)
    fmt = (lambda v: f'{v / 1e8:.2f}억') if hi >= 1e8 else (lambda v: f'{v / 1e4:,.0f}만') if hi >= 1e5 else (lambda v: f'{v:,.0f}')
    ax = ''.join(f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{fmt(v)}</text><line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="g"/>' for v in (lo + pad, (lo + hi) / 2, hi - pad))
    xs = ''.join(f'<text x="{X(i):.1f}" y="{H - 10}" text-anchor="middle">{h[i][0][5:].replace("-", "/")}</text>' for i in (0, len(h) // 2, len(h) - 1))
    return (f'<figure class="an-ch"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(c["name"])} 30일 가격과 전망 기사"><defs><linearGradient id="ga{c["sym"]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".25"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></linearGradient></defs>'
            f'{ax}<polygon points="{area}" fill="url(#ga{c["sym"]})"/><polyline points="{pts}" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linejoin="round"/>{dots}{xs}</svg>'
            f'<figcaption>업비트 일봉 종가(원) · 점 = 그날 나온 전망 기사 <i style="color:#ef4444">● 강세</i> <i style="color:#3b82f6">● 약세</i> <i style="color:#94a3b8">● 혼조</i></figcaption></figure>')


def stock_svg(s):
    """증권사별 목표가: 점(새 목표가) + 이전 목표가에서 이어지는 선, 평균 목표가 점선."""
    ns = [n for n in s.get('nodes', []) if n.get('tp') and not n.get('chk')]
    if not ns:
        return ''
    W, H, L, R, T, B = 640, 240, 86, 16, 20, 34
    now = time.time()
    t0 = min(min(n['ts'] for n in ns), now - 7 * 86400)
    vals = [n['tp'] for n in ns] + [n['tp0'] for n in ns if n.get('tp0')]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or hi * 0.1
    lo, hi = lo - pad, hi + pad
    X = lambda ts: L + (W - L - R) * (ts - t0) / max(1, now - t0)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    g = ''
    for n in ns:
        x = X(n['ts'])
        if n.get('tp0'):
            g += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y(n["tp0"]):.1f}" y2="{Y(n["tp"]):.1f}" stroke="{DCOL[n["dir"]]}" stroke-width="3" stroke-opacity=".45"/><circle cx="{x:.1f}" cy="{Y(n["tp0"]):.1f}" r="3.5" fill="#fff" stroke="{DCOL[n["dir"]]}" stroke-width="2"/>'
        g += f'<circle cx="{x:.1f}" cy="{Y(n["tp"]):.1f}" r="6" fill="{DCOL[n["dir"]]}" stroke="#fff" stroke-width="2"><title>{E(n["br"])} {won_txt(n["tp"])}</title></circle><text x="{x + 9:.1f}" y="{Y(n["tp"]) + 4:.1f}" class="lb">{E(n["br"].replace("투자증권", "").replace("증권", "").replace("금융투자", ""))}</text>'
    avg = s.get('tp_avg')
    av = f'<line x1="{L}" x2="{W - R}" y1="{Y(avg):.1f}" y2="{Y(avg):.1f}" stroke="#10b981" stroke-dasharray="6 4" stroke-width="2"/><text x="{W - R}" y="{Y(avg) - 6:.1f}" text-anchor="end" class="lb" fill="#047857">평균 {won_txt(avg)}</text>' if avg else ''
    ax = ''.join(f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{won_txt(int(v))}</text><line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="g"/>' for v in (lo + pad, hi - pad) if v > 0)
    xs = f'<text x="{L}" y="{H - 10}">{kdate_of(t0)[5:].replace("-", "/")}</text><text x="{W - R}" y="{H - 10}" text-anchor="end">오늘</text>'
    return (f'<figure class="an-ch"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(s["name"])} 증권사별 목표가">{ax}{av}{g}{xs}</svg>'
            f'<figcaption>증권사별 목표가(원) · <i style="color:#ef4444">● 상향</i> <i style="color:#3b82f6">● 하향</i> <i style="color:#94a3b8">● 유지</i> · 흰 점 = 이전 목표가</figcaption></figure>')


def an_sum(s):
    """종목 노드를 다시 계산한 해설 (기사 문장 전재 없음, 숫자는 노드에서)."""
    ns = s.get('nodes') or []
    up, dn, kp = s['up'], s['down'], s['keep']
    L = [f'최근 30일 동안 {s["name"]} 목표가·투자의견이 나온 리포트 기사 {s["nn"]}건을 증권사 {s["nb"]}곳 기준으로 다시 묶었어요. 상향 {up}곳 · 유지 {kp}곳 · 하향 {dn}곳으로 '
         + ('상향 의견이 더 많아요.' if up > dn else '하향 의견이 더 많아요.' if dn > up else '상향과 하향이 같아요.')]
    if s.get('tp_avg'):
        if s.get('tp_min') and s.get('tp_max') and s['tp_min'] != s['tp_max']:
            L.append(f'제시된 목표가는 평균 {won_txt(s["tp_avg"])}이고, 가장 낮은 곳({won_txt(s["tp_min"])})과 높은 곳({won_txt(s["tp_max"])}) 차이는 {round((s["tp_max"] - s["tp_min"]) * 100 / s["tp_min"])}%예요.')
        else:
            L.append(f'목표가를 밝힌 곳은 모두 {won_txt(s["tp_avg"])}를 제시했어요.')
    for x in [x for x in ns if x.get('tp') and x.get('tp0') and x['tp0'] != x['tp']][:3]:
        L.append(f'{x["br"]}은 목표가를 {won_txt(x["tp0"])}에서 {won_txt(x["tp"])}로 {abs(round((x["tp"] - x["tp0"]) * 100 / x["tp0"]))}% {"올렸" if x["tp"] > x["tp0"] else "내렸"}어요.')
    rc = collections.Counter(r for x in ns for r in (x.get('rs') or []))
    if rc:
        r, k = rc.most_common(1)[0]
        L.append(f'노드에서 가장 많이 나온 근거는 「{r}」({k}건)이에요.')
    if s.get('mixed'):
        L.append('증권사끼리 방향이 엇갈려요. 리포트 날짜가 서로 다를 수 있으니 아래 노드에서 날짜와 근거를 함께 보세요.')
    if any(x.get('chk') for x in ns):
        L.append('목표가 숫자나 방향이 기사 제목과 어긋나 보이는 노드는 「확인 필요」로 따로 표시했어요.')
    return '<section class="an-sum"><h2>🧐 루리 해설</h2><p>' + ' '.join(E(x) for x in L) + '</p></section>'


def coin_sum(c):
    L = [f'최근 7일 {c["name"]} 전망 기사 {c["n"]}건을 강세 {c["bull"]} · 혼조 {c["neutral"]} · 약세 {c["bear"]} 노드로 나눴어요. '
         + ('강세 쪽 발언이 더 많아요.' if c['bull'] > c['bear'] else '약세 쪽 발언이 더 많아요.' if c['bear'] > c['bull'] else '강세와 약세가 같아요.')]
    h = [v for _, v in (c.get('hist') or []) if v]
    if len(h) > 5:
        L.append(f'업비트 일봉으로 보면 최근 {len(h)}일 동안 {round((h[-1] - h[0]) * 100 / h[0], 1):+}% 움직였고, 고점과 저점 차이는 {round((max(h) - min(h)) * 100 / min(h), 1)}%예요.')
    for side, nm in (('bull', '강세'), ('bear', '약세')):
        t = (c.get('tree') or {}).get(side) or []
        if t:
            L.append(f'{nm} 근거는 「{t[0][0]}」가 가장 많았어요.')
    return '<section class="an-sum"><h2>🧐 루리 해설</h2><p>' + ' '.join(E(x) for x in L) + '</p></section>'


def stock_card(s, full=False):
    tot = s['up'] + s['down'] + s['keep']
    bar = ''.join(f'<i class="{d}" style="width:{round(100 * s[d] / tot)}%"></i>' for d in ('up', 'keep', 'down') if tot and s[d])
    rng = f'{won_txt(s["tp_min"])} ~ {won_txt(s["tp_max"])}' if s['tp_min'] and s['tp_max'] and s['tp_min'] != s['tp_max'] else ''
    head = (f'<div class="an-h"><h3><a href="/analyst/s/{s["id"]}/">{E(s["name"])}</a></h3>{"<span class=an-mix>⚖️ 의견 엇갈림</span>" if s["mixed"] else ""}</div>'
            f'<p class="an-st">증권사 {s["nb"]}곳 · 🔺{s["up"]} ➖{s["keep"]} 🔻{s["down"]}{(" · 평균 목표가 " + won_txt(s["tp_avg"])) if s["tp_avg"] else ""}{(" (" + rng + ")") if rng else ""}{(" · 기사 속 상승여력 평균 " + str(s["upside"]) + "%") if s.get("upside") is not None else ""}</p>'
            f'<div class="an-bar">{bar}</div>')
    return f'<article class="an-c">{head}{stock_svg(s)}{an_tree(s["tree"], ("up", "down", "keep"))}' + (an_nodes(s['nodes']) if full else f'<a class="an-more" href="/analyst/s/{s["id"]}/">리포트 노드 {s["nn"]}개 자세히 →</a>') + '</article>'


def coin_card(c, full=False):
    p = c.get('price') or {}
    pr = f'<span class="an-p">{p["p"]:,.0f}원 <b class="{"up" if p["chg"] >= 0 else "down"}">{p["chg"]:+.2f}%</b> <small>업비트</small></span>' if p else ''
    tot = c['bull'] + c['bear'] + c['neutral']
    bar = ''.join(f'<i class="{d}" style="width:{round(100 * c[d] / tot)}%"></i>' for d in ('bull', 'neutral', 'bear') if tot and c[d])
    tg = f' · 기사 속 목표 {format(c["tgt"][0], "g")}~{format(c["tgt"][1], "g")}만 달러' if c.get('tgt') else ''
    return (f'<article class="an-c"><div class="an-h"><h3><a href="/analyst/coin/{c["sym"].lower()}/">{E(c["name"])} <small>{c["sym"]}</small></a></h3>{pr}</div>'
            f'<p class="an-st">최근 7일 전망 기사 {c["n"]}건 · 🟢 강세 {c["bull"]} · ⚪ 혼조 {c["neutral"]} · 🔴 약세 {c["bear"]}{tg}</p><div class="an-bar">{bar}</div>'
            + coin_svg(c) + an_tree(c['tree'], ('bull', 'bear', 'neutral')) + (an_nodes(c['nodes'], True) if full else f'<a class="an-more" href="/analyst/coin/{c["sym"].lower()}/">전망 노드 {c["n"]}개 자세히 →</a>') + '</article>')


def analyst_pages():
    # 애널리스트 분석의 분석 (2026-10-18 사용자: 애널리스트 발언을 노드로 나눠 2차 가공, 비트코인·이더리움 등, 사이트 비중 40%)
    d = _rd('analyst/data.json')
    if not d:
        return []
    S, C = d.get('stocks', []), d.get('coins', [])
    css = '<link rel="stylesheet" href="/assets/analyst/analyst.css?v=4">'
    ups = sorted([s for s in S if s['up'] > s['down']], key=lambda s: (-s['up'], -s['last']))[:10]
    dns = sorted([s for s in S if s['down'] > s['up']], key=lambda s: (-s['down'], -s['last']))[:10]
    mix = [s for s in S if s['mixed']][:10]
    nn = sum(s['nn'] for s in S)
    hero = (f'<div class="an-hero"><img src="/assets/ruri/o_present.webp" width="300" height="415" alt="애널리스트 분석을 정리하는 루리"><div><small>마지막 수집·집계 {E(d["updated"])} (한국 시간) · 매시간 갱신</small>'
            f'<b>최근 30일 · 종목 {len(S)}개 · 리포트 {sum(s["nb"] for s in S)}건 · 기사 {sum(s["nn"] for s in S)}건</b><p class="an-scope">리포트 수는 종목마다 증권사별 최신 의견 1건으로 셌어요(같은 리포트를 여러 기사가 인용해도 1건). 기사 수는 그 리포트를 다룬 기사 전체예요. 코인 {len(C)}개는 최근 7일 전망 기사 기준이에요.</p><p>증권사 리포트 기사 속 발언을 「상향·하향·유지」 노드로 쪼개고, 근거별로 어느 증권사가 말했는지 다시 묶었어요.</p></div></div>')
    how = ('<details class="an-how"><summary>노드 분석은 이렇게 해요</summary><ol><li>증권 기사 RSS에서 「목표가」「투자의견」이 나온 기사만 골라요.</li><li>기사 1건 = 노드 1개: 증권사·종목·방향(상향/하향/유지)·투자의견·목표가(이전→새)·근거 태그를 뽑아요.</li>'
           '<li>근거 태그(실적 개선·업황 호조·수주·주주환원·저평가 / 실적 부진·업황 둔화·고평가·규제·심리 악화)는 노드 방향과 맞는 것만 붙여요.</li><li>종목별로 증권사마다 최신 노드 하나만 남겨 상향·하향·유지 수, 평균 목표가, 의견 엇갈림을 계산해요.</li>'
           '<li>코인은 전문가·기관 발언 기사를 강세·약세·혼조 노드로 나누고 근거(ETF 자금·금리·규제·기관 매수·거래소 유입 등)별로 묶어요.</li></ol></details>')
    sec = ''
    if C:
        sec += '<h2>🪙 코인 전망 종합</h2>' + ''.join(coin_card(c) for c in C if c['n'])
    if ups:
        sec += '<h2>🔺 목표가 상향이 많은 종목</h2>' + ''.join(stock_card(s) for s in ups)
    if dns:
        sec += '<h2>🔻 목표가 하향이 많은 종목</h2>' + ''.join(stock_card(s) for s in dns)
    if mix:
        sec += '<h2>⚖️ 증권사 의견이 엇갈린 종목</h2>' + ''.join(stock_card(s) for s in mix)
    rest = [s for s in S if s not in ups and s not in dns and s not in mix]
    if rest:
        sec += '<h2>📋 최근 리포트가 나온 종목</h2><ul class="an-all">' + ''.join(f'<li><a href="/analyst/s/{s["id"]}/">{E(s["name"])}<small>{"🔺" * min(3, s["up"])}{"🔻" * min(3, s["down"])}{"➖" * min(3, s["keep"])}</small></a></li>' for s in rest) + '</ul>'
    page('/analyst/', '루리의 애널리스트 분석 종합 — 증권사 목표가 상향·하향, 코인 전망 노드 분석',
         f'증권사 리포트 기사 속 목표가·투자의견을 노드로 쪼개 종목별로 다시 정리했어요. 최근 30일 증권사별 최신 리포트 기준 상향 {sum(s["up"] for s in S)}건 · 하향 {sum(s["down"] for s in S)}건, 비트코인·이더리움 전망 강세·약세 근거까지.',
         '<p class="bc"><a href="/">홈</a> › 애널리스트 분석</p><h1>📊 루리의 애널리스트 분석 종합</h1>' + hero + AN_NOTE + sec + how + css, [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/')])
    urls = ['/analyst/']
    for s in S:
        page(f'/analyst/s/{s["id"]}/', f'{s["name"]} 목표가·투자의견 종합 — 증권사 {s["nb"]}곳 리포트 노드 분석',
             f'{s["name"]} 최근 30일 증권사 리포트: 상향 {s["up"]} · 유지 {s["keep"]} · 하향 {s["down"]}' + (f', 평균 목표가 {won_txt(s["tp_avg"])}' if s['tp_avg'] else '') + '. 상승·하락 근거별로 어느 증권사가 말했는지 정리.',
             f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">애널리스트 분석</a> › {E(s["name"])}</p><h1>📊 {E(s["name"])} 애널리스트 의견 종합</h1>' + AN_NOTE + an_sum(s) + stock_card(s, True) + '<p class="mg-nav"><a href="/analyst/">다른 종목 보기 →</a></p>' + css,
             [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/'), (s['name'], f'/analyst/s/{s["id"]}/')], noindex=s['nb'] < 2)
        urls.append(f'/analyst/s/{s["id"]}/')
    for c in C:
        if not c['n']:
            continue
        page(f'/analyst/coin/{c["sym"].lower()}/', f'{c["name"]}({c["sym"]}) 전망 종합 — 강세·약세 의견 노드 분석', f'{c["name"]} 최근 7일 전망 기사 {c["n"]}건: 강세 {c["bull"]} · 약세 {c["bear"]} · 혼조 {c["neutral"]}. 근거별 정리와 업비트 현재가.',
             f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">애널리스트 분석</a> › {E(c["name"])}</p><h1>🪙 {E(c["name"])} 전망 종합</h1>' + AN_NOTE + coin_sum(c) + coin_card(c, True) + '<p class="mg-nav"><a href="/analyst/">다른 코인·종목 보기 →</a></p>' + css,
             [('루리의 줍줍', '/'), ('애널리스트 분석', '/analyst/'), (c['name'], f'/analyst/coin/{c["sym"].lower()}/')], noindex=c['n'] < 5)
        urls.append(f'/analyst/coin/{c["sym"].lower()}/')
    return urls


def analyst_top():
    d = _rd('analyst/data.json')
    if not d:
        return ''
    S, C = d.get('stocks', []), d.get('coins', [])
    li = ''
    for c in [c for c in C if c['n']][:2]:
        p = c.get('price') or {}
        li += f'<li><a href="/analyst/coin/{c["sym"].lower()}/"><em>🪙</em><b>{E(c["name"])}{(" " + format(p["p"], ",.0f") + "원") if p else ""}</b><span>🟢{c["bull"]} 🔴{c["bear"]}</span></a></li>'
    for s in sorted(S, key=lambda s: (-s['nb'], -s['last']))[:3]:
        li += f'<li><a href="/analyst/s/{s["id"]}/"><em>📈</em><b>{E(s["name"])}</b><span>🔺{s["up"]} 🔻{s["down"]}{(" · " + won_txt(s["tp_avg"])) if s["tp_avg"] else ""}</span></a></li>'
    return f'<section class="nw-home an-home"><h2>📊 애널리스트 분석 종합 <a href="/analyst/">전체 →</a></h2><ol>{li}</ol></section>' if li else ''


def talk_top():
    d = _rd('talk/data.json')
    li = ''.join(f'<li><a href="/talk/#t{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{x["nsite"]}곳 · 💬{x["nc"]:,}</span></a></li>' for i, x in enumerate(d.get('issues', [])[:3]))
    return f'<section class="nw-home tk-home"><h2>💬 지금 커뮤니티 이슈 <a href="/talk/">TOP30 →</a></h2><ol>{li}</ol></section>' if li else ''


SAT_DIR = r'C:\Users\k\Desktop\공모전_2026\풍자툰'


def satire_days():
    """풍자툰 폴더의 satire_MMDD.png(만평)·toon_MMDD.png(4컷)·cap_MMDD.txt → [(YYYY-MM-DD, {'imgs': [...], 'cap': [...]})], 최신 먼저."""
    if not os.path.isdir(SAT_DIR):
        return []
    days = {}
    for f in os.listdir(SAT_DIR):
        m = re.match(r'(satire|toon)_(\d{2})(\d{2})\.png$', f)
        if not m:
            continue
        y = TODAY.year if (int(m.group(2)), int(m.group(3))) <= (TODAY.month, TODAY.day) else TODAY.year - 1
        d = f'{y}-{m.group(2)}-{m.group(3)}'
        days.setdefault(d, {'imgs': [], 'mmdd': m.group(2) + m.group(3)})['imgs'].append((0 if m.group(1) == 'satire' else 1, f))
    out = []
    for d, v in days.items():
        v['imgs'] = [f for _, f in sorted(v['imgs'])]
        cp = os.path.join(SAT_DIR, f'cap_{v["mmdd"]}.txt')
        lines = []
        if os.path.exists(cp):
            for l in open(cp, encoding='utf-8-sig').read().splitlines():
                l = l.strip()
                if l and not l.startswith('#') and '프로필 링크' not in l and '캐릭터 이미지' not in l:
                    lines.append(l)
        v['cap'] = lines
        out.append((d, v))
    return sorted(out, reverse=True)


def satire_img(d, f):
    od = os.path.join(ROOT, 'satire', d)
    os.makedirs(od, exist_ok=True)
    src, dst = os.path.join(SAT_DIR, f), os.path.join(od, f[:-4] + '.webp')
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        from PIL import Image
        Image.open(src).convert('RGB').resize((864, 1080), Image.LANCZOS).save(dst, quality=84)
    return f'/satire/{d}/{f[:-4]}.webp'


def satire_pages():
    # 루리 풍자 (2026-10-18 사용자: "루리 풍자도 메인에 올리고 매일매일 하나씩 나오게 하고 이전꺼도 보게") — 원고·그림은 홍보 세션이 풍자툰 폴더에 매일 둔다
    days = satire_days()
    if not days:
        return []
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    note = '<p class="note">풍자 만화예요. 특정 종목·인물을 비방하거나 투자를 권하려는 게 아니에요. 숫자는 그날 보도 기준이에요.</p>'
    urls = ['/satire/']
    def one(d, v, h='h2'):
        imgs = ''.join(f'<img src="{satire_img(d, f)}" width="864" height="1080" alt="{kdate(d)} 루리 풍자 {"만평" if f.startswith("satire") else "4컷"}" loading="lazy">' for f in v['imgs'])
        cap = ''.join(f'<p>{E(l)}</p>' for l in v['cap'])
        return f'<article class="st-d"><{h}>🎨 {kdate(d)} 루리 풍자</{h}><div class="st-imgs">{imgs}</div>{("<div class=st-cap>" + cap + "</div>") if cap else ""}</article>'
    arch = '<section class="tk-arch"><h2>📅 지난 풍자 모아 보기</h2><p>' + ''.join(f'<a href="/satire/{d}/">{kdate(d)}</a>' for d, _ in days[:90]) + '</p></section>'
    d0, v0 = days[0]
    title0 = (v0['cap'][0] if v0['cap'] else '오늘의 풍자')
    page('/satire/', '루리 풍자 — 매일 한 컷, 증시·뉴스 만평', f'루리가 매일 그리는 풍자 만화. 오늘: {title0}. 지난 풍자도 날짜별로 모아 봐요.',
         '<p class="bc"><a href="/">홈</a> › 루리 풍자</p><h1>🎨 루리 풍자</h1>' + one(d0, v0) + note + arch + css, [('루리의 줍줍', '/'), ('루리 풍자', '/satire/')])
    for i, (d, v) in enumerate(days):
        od = os.path.join(ROOT, 'satire', d)  # 원본이 빠진 그림(사용자가 뺀 컷)은 사이트에서도 지움
        keep = {f[:-4] + '.webp' for f in v['imgs']}
        for f in (os.listdir(od) if os.path.isdir(od) else []):
            if f.endswith('.webp') and f not in keep:
                os.remove(os.path.join(od, f))
        nav = ''
        if i + 1 < len(days):
            nav += f'<a href="/satire/{days[i + 1][0]}/">← {kdate(days[i + 1][0])}</a>'
        if i > 0:
            nav += f'<a href="/satire/{days[i - 1][0]}/">{kdate(days[i - 1][0])} →</a>'
        page(f'/satire/{d}/', f'{kdate(d)} 루리 풍자 — ' + (v['cap'][0] if v['cap'] else '증시·뉴스 만평'), f'{kdate(d)} 루리 풍자 만화. ' + ' '.join(v['cap'][:2])[:120],
             f'<p class="bc"><a href="/">홈</a> › <a href="/satire/">루리 풍자</a> › {kdate(d)}</p>' + one(d, v, 'h1') + f'<p class="st-nav">{nav}</p>' + note + arch + css,
             [('루리의 줍줍', '/'), ('루리 풍자', '/satire/'), (kdate(d), f'/satire/{d}/')])
        urls.append(f'/satire/{d}/')
    return urls


def satire_top():
    days = satire_days()
    if not days:
        return ''
    d, v = days[0]
    img = satire_img(d, v['imgs'][0])
    t = v['cap'][0] if v['cap'] else '오늘의 풍자'
    return (f'<section class="nw-home st-home"><h2>🎨 오늘의 루리 풍자 <a href="/satire/">지난 풍자 →</a></h2><a class="st-hm" href="/satire/{d}/"><img src="{img}" width="864" height="1080" alt="{E(t)}" loading="lazy" decoding="async">'
            f'<span><b>{E(t)}</b>{E(" ".join(v["cap"][1:3]))[:90]}</span></a></section>')


def josa_ga(w):
    c = w[-1]
    return '이' if '가' <= c <= '힣' and (ord(c) - 0xAC00) % 28 else '가'


def kw_pages():
    # 인기 키워드 상세 (2026-10-18 사용자: 구글 등 인기 키워드로 블로그 + 사이트 상세 정보, 홍보 세션 연구 ⑂ 요청) — 매시 kw.py
    db = _rd('kw/db.json')
    ad = os.path.join(ROOT, 'kw', 'archive')
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True) if os.path.isdir(ad) else []
    if not db or not days:
        return []
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    note = '<p class="note">구글 트렌드 한국 급상승 검색어를 바탕으로 루리가 관련 보도와 사이트 정보를 모은 페이지예요. 연예인 사생활·사건사고·비방성 키워드는 다루지 않아요.</p>'
    urls = ['/kw/']
    kd = os.path.join(ROOT, 'kw')  # 제외된 키워드 페이지는 지움
    for f in os.listdir(kd):
        if os.path.isdir(os.path.join(kd, f)) and f != 'archive' and not re.match(r'\d{4}-\d{2}-\d{2}$', f) and f not in db:
            shutil.rmtree(os.path.join(kd, f), ignore_errors=True)
    SRCB = lambda r: ('<span class="kw-b both">구글+네이버 동시</span>' if len(r.get('src') or []) > 1 else '<span class="kw-b n">실시간 검색어</span>' if (r.get('src') or ['google']) == ['naver'] else '<span class="kw-b g">구글 트렌드</span>')
    for sl, r in db.items():
        k = r['k']
        lines = [f'「{E(k)}」{josa_ga(k)} {kdate(r["days"][-1])} ' + ('구글 급상승과 실시간 검색어에 동시에' if len(r.get('src') or []) > 1 else '실시간 검색어에' if (r.get('src') or ['google']) == ['naver'] else '구글 검색 급상승 키워드에') + f' 올랐어요({E(r.get("traffic") or "-")}).']
        if r.get('srcs'):
            lines.append(f'관련 보도는 {len(r["srcs"])}곳({E(", ".join(r["srcs"][:5]))}{" 등" if len(r["srcs"]) > 5 else ""})에서 나왔어요.')
        if r.get('issue'):
            x = r['issue']
            lines.append(f'루리의 기사 확인 신호에서는 언론사 {x["on"]}곳이 보도한 이슈로 묶였고, 확인 신호 점수는 {G.get(x.get("g"), "")} {x.get("s") if x.get("s") is not None else "-"}점이에요.')
        if len(r['days']) > 1:
            lines.append(f'최근 {len(r["days"])}일 동안 급상승에 올랐어요({", ".join(d[5:].replace("-", "/") for d in r["days"][-5:])}).')
        why = ''.join(f'<li><a href="{E(n["u"])}" target="_blank" rel="noopener nofollow"><em>{E(n["o"])}</em>{E(n["t"])}</a></li>' for n in r.get('news', []))
        ours = ''.join(f'<li><a href="{E(a["u"])}" target="_blank" rel="noopener nofollow"><em>{E(a["o"])} {G.get(a.get("g"), "")} {a["s"] if a.get("s") is not None else ""}</em>{E(a["t"])}</a></li>' for a in r.get('ours', []))
        links = []
        if r.get('issue'):
            links.append(f'<a href="/news/#is{r["issue"]["n"]}"><em>🕵️ 기사 확인 신호</em><b>{E(r["issue"]["t"])}</b></a>')
        links += [f'<a href="/talk/#t{x["n"]}"><em>💬 커뮤니티</em><b>{E(x["t"])}</b></a>' for x in r.get('talk', [])]
        links += [f'<a href="/analyst/s/{x["id"]}/"><em>📊 애널리스트</em><b>{E(x["name"])} 목표가 의견</b></a>' for x in r.get('stocks', [])]
        links += [f'<a href="/analyst/coin/{x["sym"].lower()}/"><em>🪙 코인</em><b>{E(x["name"])} 전망 종합</b></a>' for x in r.get('coins', [])]
        links += [f'<a href="{E(p_["u"])}"><em>{E(p_["k"])}</em><b>{E(p_["t"])}</b></a>' for p_ in r.get('pr', [])]
        trs = r.get('trend') or []
        if len(trs) >= 5:
            W_, H_ = 600, 140; mx = max(v for _, v in trs) or 1
            pts = ' '.join(f'{10 + (W_ - 20) * i / (len(trs) - 1):.1f},{H_ - 22 - (H_ - 40) * v / mx:.1f}' for i, (_, v) in enumerate(trs))
            trend_html = (f'<section class="mg-s"><h2>📈 최근 30일 네이버 검색량 추이</h2><figure class="an-ch"><svg viewBox="0 0 {W_} {H_}" role="img" aria-label="{E(k)} 검색량 추이">'
                          f'<polyline points="{pts}" fill="none" stroke="#16a34a" stroke-width="3"/><text x="10" y="{H_ - 4}">{trs[0][0][5:]}</text><text x="{W_ - 10}" y="{H_ - 4}" text-anchor="end">{trs[-1][0][5:]}</text></svg>'
                          '<figcaption>네이버 데이터랩 검색어 트렌드(기간 중 최댓값 = 100인 상대값)</figcaption></figure></section>')
        else:
            trend_html = ''
        post = f'<section class="mg-s"><h2>✍️ 루리의 정리 글</h2><div class="nw-pr"><a href="{E(r["post"])}" target="_blank" rel="noopener"><em>블로그</em><b>{E(k)} 자세히 정리한 글 보기</b></a></div></section>' if r.get('post') else ''
        css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><link rel="stylesheet" href="/assets/analyst/analyst.css?v=4">'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/kw/">인기 키워드</a> › {E(k)}</p><h1>🔎 {E(k)} — 왜 검색이 늘었나</h1><p>{SRCB(r)}</p>'
                + say('o_det_think', ' '.join(lines)) + trend_html + post
                + (f'<section class="mg-s"><h2>📰 왜 떴나: 관련 보도</h2><ul class="kw-l">{why}</ul></section>' if why else '')
                + (f'<section class="mg-s"><h2>🕵️ 루리가 채점한 관련 기사</h2><ul class="kw-l">{ours}</ul></section>' if ours else '')
                + (f'<section class="mg-s"><h2>📌 루리의 줍줍에서 더 보기</h2><div class="nw-pr">{"".join(links)}</div></section>' if links else '')
                + f'<p class="mg-nav"><a href="/kw/">오늘의 인기 키워드 전체 →</a> · <a href="/mag/">매거진 →</a></p>' + note + css)
        page(f'/kw/{sl}/', f'{k} 검색 급상승 이유 — 관련 보도·정리', f'{k}{josa_ga(k)} 검색 급상승 키워드에 오른 이유: ' + ' / '.join(n['t'] for n in r.get('news', [])[:2])[:140], body,
             [('루리의 줍줍', '/'), ('인기 키워드', '/kw/'), (k, f'/kw/{sl}/')], noindex=not r.get('post'))
        urls.append(f'/kw/{sl}/')
    arch = '<section class="tk-arch"><h2>📅 날짜별 인기 키워드</h2><p>' + ''.join(f'<a href="/kw/{d}/">{kdate(d)}</a>' for d in days[:90]) + '</p></section>'
    for i, d in enumerate(days):
        L = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        li = ''.join(f'<li><a href="/kw/{x["slug"]}/"><em>{j + 1}</em><b>{E(x["k"])}</b><span>{SRCB(x)} {E(x.get("traffic") or "-")} · {E(x.get("first", ""))} 첫 등장</span></a></li>' for j, x in enumerate([y for y in L if y['slug'] in db]))
        bd = f'<ol class="mg-l">{li}</ol>' + arch + note + css
        if i == 0:
            page('/kw/', '오늘의 인기 키워드 — 검색 급상승 이유 정리', f'{kdate(d)} 구글 검색 급상승 키워드와 왜 떴는지: ' + ', '.join(x['k'] for x in L[:6]),
                 f'<p class="bc"><a href="/">홈</a> › 인기 키워드</p><h1>🔎 오늘의 인기 키워드</h1><script defer src="/assets/view/one.js?v=1"></script>' + say('o_det_wave', '지금 검색이 확 늘어난 키워드를 모아, 왜 떴는지 관련 보도와 함께 정리했어요.') + bd,
                 [('루리의 줍줍', '/'), ('인기 키워드', '/kw/')])
        page(f'/kw/{d}/', f'{kdate(d)} 인기 키워드 — 검색 급상승 정리', f'{kdate(d)} 구글 검색 급상승 키워드: ' + ', '.join(x['k'] for x in L[:8]),
             f'<p class="bc"><a href="/">홈</a> › <a href="/kw/">인기 키워드</a> › {kdate(d)}</p><h1>🔎 {kdate(d)} 인기 키워드</h1>' + bd, [('루리의 줍줍', '/'), ('인기 키워드', '/kw/'), (kdate(d), f'/kw/{d}/')], noindex=True)
        urls.append(f'/kw/{d}/')
    return urls


DEV_F = os.path.join(HERE, 'dev_posts.json')   # 개발 지식 글 목록(본문은 devsrc/<slug>.html). 2026-10-19 사용자: 「AI 로그는 개발 지식 쪽으로, 레딧 질문에 답·테스트 자료를 바로 올려 유입」


def dev_url(p):
    return f'/en/guide/{p["slug"]}/' if p['lang'] == 'en' else f'/dev/{p["slug"]}/'


def dev_posts():
    P = json.load(open(DEV_F, encoding='utf-8')) if os.path.exists(DEV_F) else []
    return [p for p in P if os.path.exists(os.path.join(HERE, 'devsrc', p['slug'] + '.html'))]


def dev_requests(P):
    """홍보 세션이 community_posted.jsonl rule_note 에 남긴 needs_page:<slug> 를 모아, 아직 글이 없는 주제를 dev_requests.json 으로 (다음 글 후보)."""
    have = {p['slug'] for p in P}; req = {}
    src = os.path.join(os.path.expanduser('~'), 'Desktop', '공모전_2026', 'daily', 'community_posted.jsonl')
    if os.path.exists(src):
        for l in open(src, encoding='utf-8'):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            for m in re.finditer(r'needs_page:([a-z0-9-]+)', r.get('rule_note') or ''):
                x = req.setdefault(m.group(1), {'slug': m.group(1), 'count': 0, 'first': r.get('time'), 'last': r.get('time'), 'threads': []})
                x['count'] += 1; x['last'] = r.get('time')
                if r.get('url') and len(x['threads']) < 5:
                    x['threads'].append({'url': r['url'], 'title': (r.get('title') or '')[:120]})
    out = sorted([x for k, x in req.items() if k not in have], key=lambda x: (-x['count'], x['first'] or ''))
    json.dump({'updated': datetime.datetime.now().isoformat(timespec='minutes'), 'todo': out, 'done': sorted(k for k in req if k in have)},
              open(os.path.join(HERE, 'dev_requests.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return out


FOREIGN_OK = re.compile(r'외국인|국적\s*(무관|불문|제한\s*없)|foreigner|nationality', re.I)
FOREIGN_NO = re.compile(r'외국인\s*(은|의)?\s*(제외|불가|응모\s*불가|참여\s*불가)|내국인\s*만|대한민국\s*국적(자)?\s*만|외국\s*국적\s*(자\s*)?(제외|불가)')


def foreign_contests(live):
    """외국인도 낼 수 있는 진행 중 공모전 (응모자격 원문에 외국인·국적 무관이 있고, 제외 문구가 없는 것). 2026-10-19 레딧(한국 거주 외국인) 가이드용"""
    L = [c for c in live if FOREIGN_OK.search(c.get('elig') or '') and not FOREIGN_NO.search(c.get('elig') or '') and ' > ' not in c['title'] and c['end'] >= TODAY.isoformat()]
    return sorted(L, key=lambda c: (c['end'], -(c.get('pv') or 0)))


def foreign_list_html(live):
    L = foreign_contests(live)
    if not L:
        return '<p>No open contests mention foreigners right now. Check back tomorrow.</p>'
    rows = ''.join(f'<tr><td>{c["end"]}</td><td><a href="/c/{c["id"]}/">{E(c["title"][:70])}</a></td><td>{E(c["prize"]) if c.get("pv") else "-"}</td><td lang="ko">{E((c.get("elig") or "")[:90])}</td></tr>' for c in L[:60])
    return (f'<p><b>{len(L)}</b> open contests as of {TODAY.isoformat()} (deadline order' + (', first 60 shown' if len(L) > 60 else '') + ').</p>'
            f'<table><tr><th>Deadline</th><th>Contest (Korean)</th><th>Top prize</th><th>Eligibility (original)</th></tr>{rows}</table>')


def dev_pages(live=()):
    P = dev_posts(); urls = []
    try:
        print('개발 글 요청 후보', len(dev_requests(P)))
    except Exception as e:
        print('개발 글 요청 읽기 실패', repr(e)[:100])
    css = ('<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><style>.dev table{width:100%;border-collapse:collapse;margin:12px 0;font-size:.92em;display:block;overflow-x:auto}.dev th,.dev td{border:1px solid #e5e7eb;padding:6px 8px;text-align:left;vertical-align:top}'
           '.dev pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow-x:auto;font-size:.85em}.dev code{font-size:.92em}.dev dt{font-weight:700;margin-top:10px}.dev dd{margin:4px 0 0 0}'
           '.dev-ls{list-style:none;padding:0}.dev-ls li{margin:8px 0}.dev-ls a{display:block;padding:12px;border:1px solid #e5e7eb;border-radius:10px;text-decoration:none;color:inherit}.dev-ls span{display:block;font-size:.88em;color:#64748b;margin-top:4px}</style>')
    for p in P:
        u = dev_url(p); en = p['lang'] == 'en'
        body_ = open(os.path.join(HERE, 'devsrc', p['slug'] + '.html'), encoding='utf-8').read()
        if '<!--FOREIGN_LIST-->' in body_:
            body_ = body_.replace('<!--FOREIGN_LIST-->', foreign_list_html(live))
        src = ''.join(f'<li><a href="{E(x[1])}"' + ('' if x[1].startswith('/') else ' rel="nofollow noopener" target="_blank"') + f'>{E(x[0])}</a> — {"checked" if en else "확인"} {E(x[2])}</li>' for x in p.get('sources', []))
        hub = p.get('hub')
        body = (f'<p class="bc"><a href="/">{"Home" if en else "홈"}</a> › <a href="{"/en/guide/" if en else "/ailog/"}">{"Guides" if en else "개발 지식"}</a></p>'
                f'<article class="dev" lang="{p["lang"]}"><h1>{E(p["title"])}</h1><p class="note">{"Published" if en else "작성"} {p["date"]}'
                + (f' · {"updated" if en else "고침"} {p["updated"]}' if p.get('updated') else '') + '</p>'
                + body_ + (f'<h2>{"Sources" if en else "출처"}</h2><ul>{src}</ul>' if src else '')
                + (f'<p class="dev-hub">{"Related (Korean)" if en else "관련"}: <a href="{E(hub[1])}">{E(hub[0])}</a></p>' if hub else '')
                + ('<p class="dev-hub">Questions about how this was built? <a href="/dev/faq/">Dev FAQ</a></p>' if en else '<p class="dev-hub">이 글에 대해 묻고 싶으면 <a href="/dev/faq/">❓ 개발 FAQ</a>에 남겨 주세요.</p>')
                + share_bar(p['title'], p['desc'], en) + f'</article>{css}')
        t = p['title'] + ' | Ruri Jupjup' if en and len(p['title']) + 14 <= 70 else p['title']
        ld = {'@context': 'https://schema.org', '@type': 'TechArticle', 'headline': p['title'][:110], 'description': p['desc'], 'inLanguage': p['lang'], 'datePublished': p['date'],
              'dateModified': p.get('updated') or p['date'], 'author': {'@type': 'Organization', 'name': NAME}, 'mainEntityOfPage': SITE + u}
        page(u, t, p['desc'], body, [('Home' if en else NAME, '/'), ('Guides' if en else '개발 지식', '/en/guide/' if en else '/ailog/'), (p['title'], u)], ld=ld, full_title=en, lang=p['lang'])
        urls.append(u)
    urls += dev_faq_page(P)
    EP = [p for p in P if p['lang'] == 'en']
    if EP:
        li = ''.join(f'<li><a href="{dev_url(p)}"><b>{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in sorted(EP, key=lambda p: p['date'], reverse=True))
        page('/en/guide/', 'Practical Guides: Life in Korea, AI Tools, Self-Hosting | Ruri Jupjup', 'Step-by-step English guides on living and working in Korea, AI tools at work, self-hosting and software testing, with official sources and dates.',
             f'<p class="bc"><a href="/">Home</a> › Guides</p><h1>Practical guides</h1><p>Step-by-step guides with tables and FAQs. Numbers come from official sources, with the date we checked them.</p><ul class="dev-ls">{li}</ul>{css}',
             [('Home', '/'), ('Guides', '/en/guide/')], full_title=True, lang='en')
        urls.append('/en/guide/')
    return urls


def ailog_page(live, nurls):
    # AI 제작 로그 (2026-10-18 사용자: "AI로 이 사이트 어케 만들었는지 다 공개", "홍보 마케팅은 기밀, 사이트 쪽만", "핵심은 비용 0원으로 그럴듯한 운영")
    a = json.load(open(os.path.join(HERE, 'ailog.json'), encoding='utf-8'))
    first = a.get('start', '2026-10-17')   # 2026-10-18 사용자: "2일이야" — 루리의 줍줍 제작 시작일 기준
    try:
        commits = int(subprocess.run(['git', 'rev-list', '--count', f'--since={first}T00:00', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() or 0)
    except Exception:
        commits = 0
    npage = sum(1 for _r, _d, fs in os.walk(ROOT) if 'index.html' in fs and '.git' not in _r)
    days = (TODAY - datetime.date.fromisoformat(first)).days + 1
    stat = [('제작 기간', f'{days}일', f'{first[5:].replace("-", "/")} 시작'), ('코드 변경(커밋)', f'{commits:,}번', 'AI가 고치고 올린 횟수'),
            ('페이지', f'{npage:,}개', '매시간 다시 만들어요'), ('진행 중 공모전', f'{len(live):,}건', '상세 페이지 자동 생성'),
            ('매시간 자동 작업', '6가지', '뉴스·커뮤니티·애널리스트·키워드·빌드·배포'), ('서버·API 비용', '0원', '무료 한도 + 내 PC')]
    st = ''.join(f'<div><small>{E(k)}</small><b>{E(v)}</b><span>{E(d)}</span></div>' for k, v, d in stat)
    cost = ''.join(f'<tr><td>{E(x)}</td><td>{E(y)}</td><td><b>{E(z)}</b></td></tr>' for x, y, z in a['costs'])
    arch = ''.join(f'<li><b>{E(x)}</b><span>{E(y)}</span></li>' for x, y in a['arch'])
    chat = ''.join(f'<li><p class="al-u">🙋 {E(u)}</p><p class="al-a">🤖 {E(r)}</p></li>' for u, r in a['chat'])
    fixes = ''.join(f'<li><b>❌ {E(x)}</b><span>✅ {E(y)}</span></li>' for x, y in a['fixes'])
    rules = ''.join(f'<li>{E(x)}</li>' for x in a['rules'])
    tl = ''.join(f'<li><em>{E(d)}</em><span>{E(t)}</span></li>' for d, t in a['timeline'])
    DP = sorted(dev_posts(), key=lambda p: p['date'], reverse=True)
    dli = ''.join(f'<li><a href="{dev_url(p)}"><b>{"[EN] " if p["lang"] == "en" else ""}{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in DP)
    body = (f'<p class="bc"><a href="/">홈</a> › 개발 지식</p><h1>🧑‍💻 개발 지식 — 직접 해 보고 정리한 AI·개발 가이드</h1>'
            + (f'<style>.dev-ls{{list-style:none;padding:0}}.dev-ls li{{margin:8px 0}}.dev-ls a{{display:block;padding:12px;border:1px solid #e5e7eb;border-radius:10px;text-decoration:none;color:inherit}}.dev-ls span{{display:block;font-size:.88em;color:#64748b;margin-top:4px}}</style><section class="mg-s"><h2>📚 가이드·실험 노트</h2><p class="note">질문이 들어온 주제를 직접 테스트하고 공식 문서 숫자로 정리해요. 영어 글은 <a href="/en/guide/">English guides</a>에 모여 있어요.</p><ul class="dev-ls">{dli}</ul></section>' if DP else '')
            + '<h2 id="log">🤖 AI 제작 로그 — 서버비 0원으로 이 사이트를 만든 방법</h2>'
            + say('o_desk', E(a['lead']))
            + f'<div class="al-st">{st}</div>'
            + f'<section class="mg-s"><h2>💸 비용표: 어디에 얼마 드나</h2><table class="al-t"><tr><th>무엇</th><th>쓰는 것</th><th>비용</th></tr>{cost}</table><p class="note">{E(a["cost_note"])}</p></section>'
            + f'<section class="mg-s"><h2>🧩 구조: 매시간 이렇게 돌아가요</h2><ol class="al-ar">{arch}</ol></section>'
            + f'<section class="mg-s"><h2>💬 사람이 한 말 → AI가 만든 것</h2><p class="note">실제 지시를 그대로 옮겼어요. 사람은 방향만 말하고, 코드·디자인·배포·검사는 AI가 했어요.</p><ul class="al-c">{chat}</ul></section>'
            + f'<section class="mg-s"><h2>🛠️ AI가 틀린 것과 고친 것</h2><ul class="al-f">{fixes}</ul></section>'
            + f'<section class="mg-s"><h2>📏 지킨 원칙</h2><ul class="al-r">{rules}</ul></section>'
            + f'<section class="mg-s"><h2>🗓️ 날짜별 기록</h2><ul class="al-tl">{tl}</ul></section>'
            + '<section class="mg-s" id="faq"><h2>❓ 개발 FAQ — 이건 어떻게 만들었나요?</h2>'
              '<p class="note">빌드 시간·무료 한도·이미지 변환·검색 색인처럼 자주 받는 질문은 FAQ에 정리해 뒀어요. 없는 건 거기에 바로 남기면 답해 드려요.</p>'
              '<div data-devqna="4"></div></section>'
            + '<section class="mg-s"><div data-pcrecent="6"></div></section>'
            + '<p class="note">이 페이지는 사이트 개발 과정만 공개해요. 숫자는 빌드할 때마다 자동으로 갱신돼요.</p><link rel="stylesheet" href="/assets/mag/mag.css?v=10">')
    page('/ailog/', '개발 지식 — AI·개발 가이드와 사이트 제작 로그(Claude Code)',
         f'사람 한 명의 말과 AI(Claude Code)로 {days}일 동안 페이지 {npage:,}개짜리 정보 사이트를 만든 기록. 무료 호스팅·무료 서버리스·공개 RSS로 서버비 0원, 매시간 자동 갱신.',
         body, [('루리의 줍줍', '/'), ('개발 지식', '/ailog/')])
    return ['/ailog/']




def dev_faq_page(P):
    """개발 FAQ (2026-10-19 사용자: "Q&A보다는 FAQ형식으로"). 자주 받는 질문은 여기서 답하고, 없는 건 아래 게시판에."""
    F = json.load(open(os.path.join(HERE, 'dev_faq.json'), encoding='utf-8'))
    secs, qa_all = '', []
    for g in F['groups']:
        items = ''
        for q, a in g['qa']:
            qa_all.append((q, a))
            items += f'<details class="faq-i"><summary>{E(q)}</summary><div>{E(a)}</div></details>'
        secs += f'<section class="mg-s"><h2>{E(g["g"])}</h2>{items}</section>'
    ls = ''.join(f'<li><a href="{dev_url(p)}" data-pcs="{dev_url(p)}"><b>{"[EN] " if p["lang"] == "en" else ""}{E(p["title"])}</b></a></li>'
                 for p in sorted(P, key=lambda x: x['date'], reverse=True)[:8])
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/ailog/">개발 지식</a> › 개발 FAQ</p>'
            '<h1>❓ 개발 FAQ — 이 사이트 어떻게 만들었나요</h1>'
            + say('o_desk', E(F['lead']))
            + f'<p class="note">{len(qa_all)}개 질문 · {F["updated"]} 기준. 여기에 없는 건 아래에 남겨 주시면 답하고, 답이 길어지면 글로 정리해서 FAQ에 올려요.</p>'
            + secs
            + '<section class="mg-s"><h2>🙋 여기에 없는 걸 묻고 싶다면</h2>'
              '<p class="note">로그인(이메일·카카오·구글)하면 바로 쓸 수 있어요. 에러 메시지나 코드 일부를 붙여 주면 답하기 쉬워요. 「운영자」 표시가 붙은 답이 제 답이에요.</p>'
              '<div id="cm-board" data-contest="dev" data-title="개발 FAQ" data-head="남겨 주신 질문" data-kinds="qna,tip,free" '
              'data-ph="어떤 부분이 궁금한지 적어 주세요. 에러 메시지나 코드 일부를 붙여 주면 답하기 쉬워요." data-empty="아직 남겨 주신 질문이 없어요. 첫 질문을 남겨 주세요."></div></section>'
            + (f'<section class="mg-s"><h2>📚 길게 답한 건 글로 정리했어요</h2><ul class="dev-ls">{ls}</ul></section>' if ls else '')
            + '<style>.faq-i{border:1px solid #e5e7eb;border-radius:12px;padding:10px 14px;margin:8px 0;background:#fff}'
              '.faq-i summary{font-weight:700;cursor:pointer;font-size:15px}.faq-i div{margin-top:8px;font-size:14.5px;line-height:1.7;color:#334155}'
              '.dev-ls{list-style:none;padding:0}.dev-ls li{margin:8px 0}.dev-ls a{display:block;padding:12px;border:1px solid #e5e7eb;border-radius:10px;text-decoration:none;color:inherit}</style>'
            + '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">')
    ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qa_all]}
    page('/dev/faq/', '개발 FAQ — 1인+AI로 사이트 만들고 돌리는 법 (비용·빌드·D1)',
         '정적 사이트 빌드 시간, Cloudflare Workers·D1 무료 한도, 이미지 변환, 검색 색인, 댓글 스팸 대응까지 자주 받는 질문 '
         + str(len(qa_all)) + '개를 정리했어요.',
         body, [('루리의 줍줍', '/'), ('개발 지식', '/ailog/'), ('개발 FAQ', '/dev/faq/')], ld=ld)
    # 먼저 만들었던 /dev/qna/ 는 FAQ 로 안내만 (주소가 이미 나간 상태라 지우지 않음)
    page('/dev/qna/', '개발 FAQ로 옮겼어요',
         '개발 질문과 답은 개발 FAQ 페이지로 옮겼어요.',
         '<p class="bc"><a href="/">홈</a> › <a href="/ailog/">개발 지식</a></p><h1>개발 FAQ로 옮겼어요</h1>'
         '<p>질문과 답은 <a href="/dev/faq/">개발 FAQ</a>에 모았어요. 자동으로 넘어가지 않으면 눌러 주세요.</p>'
         '<meta http-equiv="refresh" content="0; url=/dev/faq/">', noindex=True)
    return ['/dev/faq/']

def plaza_page():
    """광장: 누구나 자기 글·레시피·썰을 올리는 공간 (2026-10-19 사용자: "사람들이 그냥 글을 자기 컨텐츠를 올릴수 있는 공간")"""
    body = ('<p class="bc"><a href="/">홈</a> › 광장</p><h1>🗣️ 줍줍 광장 — 아무거나 올리는 곳</h1>'
            + say('o_present', '공모전 후기든, 오늘 만든 밥이든, 그냥 하고 싶은 말이든 올려 주세요. 가입은 이메일·카카오·구글 중 하나면 끝나요.')
            + '<p>여기는 루리가 정리한 글이 아니라 <b>이용자가 직접 올리는 공간</b>이에요. 내가 만든 레시피, 겪은 일(썰), 알게 된 팁, 묻고 싶은 것 아무거나 괜찮아요. '
              '광고·도배·개인정보(전화번호·주소·계좌)는 지워요.</p>'
            + '<div id="cm-board" data-contest="free" data-title="광장" data-head="올라온 글" data-kinds="free,recipe,story,tip,qna" '
              'data-ph="내가 만든 것, 겪은 일, 알게 된 팁을 자유롭게 써 주세요. 개인정보(전화번호·주소)는 쓰지 마세요." data-empty="아직 글이 없어요. 첫 글을 올려 보세요."></div>'
            + '<section class="mg-s"><div data-pcrecent="8"></div></section>'
            + '<section class="mg-s" data-pctop="/" data-by="cms" data-n="8" data-head="💬 댓글이 많은 페이지"></section>'
            + '<p class="note">올린 글은 본인이 지울 수 있고, 신고가 3번 쌓이면 자동으로 가려져요. 운영자 계정에는 「운영자」 표시가 붙어요.</p>'
            + '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">')
    page('/plaza/', '줍줍 광장 — 내 글·레시피·썰 올리는 공간', '공모전 후기, 내가 만든 레시피, 오늘 겪은 썰, 궁금한 것까지 누구나 올리고 댓글을 달 수 있는 공간이에요.',
         body, [('루리의 줍줍', '/'), ('광장', '/plaza/')])
    return ['/plaza/']


def all_page():
    # 전체 메뉴 (2026-10-18 홈 단순화로 빠진 기능 모음)
    G = [('🕵️ 이슈', [('/news/', '기사 확인 신호', '언론사 기사 묶음·기사 확인 신호'), ('/talk/', '커뮤니티 이슈', '여러 커뮤니티에 동시에 뜬 화제'), ('/kw/', '인기 키워드', '검색 급상승 이유'),
                       ('/satire/', '루리 풍자', '매일 한 컷 만평'), ('/mag/', '데일리 매거진', '이슈 리딩·하루 정보 한 장'), ('/review/', '루리의 평론', '이슈·정책 해설 칼럼')]),
         ('📊 투자 정보', [('/analyst/', '애널리스트 분석', '목표가 상향·하향 노드 트리'), ('/analyst/coin/btc/', '코인 전망', '비트코인·이더리움 강세·약세')]),
         ('🏆 공모전', [('/', '공모전 추천 상담', '질문 몇 개로 딱 맞는 공모전'), ('/cat/literature/', '분야별 공모전', '문학·아이디어·디자인·영상·IT·요리'), ('/prep/', '준비실', '마감 역산 일정·체크리스트·꿀팁'),
                       ('/lab/', '수상 연구소', '수상작 분석·당선 공식'), ('/community/', '원정대', '같이 나갈 팀 모으기'), ('/guide/', '응모 가이드', '공모전 처음이라면')]),
         ('💰 생활 정보', [('/apply/', '지원금·청약', '청년 지원금·청약 일정'), ('/event/', '경품 이벤트', '응모만 하면 되는 이벤트'), ('/fridge/', '냉장고 파먹기', '있는 재료로 오늘 메뉴'), ('/qa/', '고민 해결', '실제 고민에 답 정리')]),
         ('⚙️ 더 보기', [('/app/', '앱·알림', '홈 화면 설치·폰 알림'), ('/me/', '내 공간', '찜·응모 기록'), ('/ailog/', 'AI 제작 로그', '이 사이트를 만든 방법'), ('/plaza/', '줍줍 광장', '내 글·레시피·썰 올리기')])]
    body = '<p class="bc"><a href="/">홈</a> › 전체 메뉴</p><h1>☰ 루리의 줍줍 전체 메뉴</h1>' + ''.join(
        f'<section class="mg-s"><h2>{E(g)}</h2><ul class="al-menu">' + ''.join(f'<li><a href="{u}"><b>{E(n)}</b><span>{E(d)}</span></a></li>' for u, n, d in items) + '</ul></section>' for g, items in G) + '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    page('/all/', '전체 메뉴', '루리의 줍줍 전체 메뉴: 기사 확인 신호, 커뮤니티 이슈, 인기 키워드, 풍자, 매거진, 애널리스트 분석, 공모전, 지원금·청약, 경품, 냉장고 파먹기, 앱·알림.', body, [('루리의 줍줍', '/'), ('전체 메뉴', '/all/')])
    return ['/all/']


MONEY_NOTE = ('<p class="an-warn">📊 공개된 기사·공식 자료를 정리한 일반 정보예요. 루리의 줍줍이 특정 종목·상품을 권하거나 수익을 약속하지 않아요. '
              '개인 상황에 따라 맞는 답이 다르고, 투자 판단과 책임은 본인에게 있어요.</p>')
ECOL = {'bull': ('🟢', '긍정'), 'bear': ('🔴', '신중'), 'neutral': ('⚪', '중립')}


def exp_li(n):
    dt = datetime.datetime.fromtimestamp(n['ts']).strftime('%m/%d')
    return (f'<li class="{n["dir"]}"><span class="an-d">{ECOL[n["dir"]][0]}</span><div><small>{dt} · {E(n["who"])} · {E(n["cat"])}</small>'
            f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["t"])}</a><em>{E(n["o"])}</em></div></li>')


def experts_html(ex, cats=None, limit=None):
    out = ''
    for e in ex[:limit]:
        ns = [n for n in e['nodes'] if not cats or n['cat'] in cats]
        if not ns:
            continue
        if e['mixed']:
            b = [n for n in ns if n['dir'] == 'bull'][:4]
            r = [n for n in ns if n['dir'] == 'bear'][:4]
            body = (f'<div class="ex-vs"><div><p>🟢 긍정적으로 본 쪽</p><ul class="an-nodes">{"".join(exp_li(n) for n in b)}</ul></div>'
                    f'<div><p>🔴 신중하게 본 쪽</p><ul class="an-nodes">{"".join(exp_li(n) for n in r)}</ul></div></div>')
        else:
            body = f'<ul class="an-nodes">{"".join(exp_li(n) for n in ns[:6])}</ul>'
        cc = ' · '.join(f'{k} {v}' for k, v in e['cats'].items() if v)
        out += (f'<article class="an-c"><div class="an-h"><h3>{E(e["topic"])}</h3>{"<span class=an-mix>⚖️ 의견 엇갈림</span>" if e["mixed"] else ""}</div>'
                f'<p class="an-st">최근 14일 전문가 발언 {e["n"]}건 · 🟢 {e["bull"]} · 🔴 {e["bear"]} · {E(cc)}</p>{body}</article>')
    return out


def money_pages():
    # 머니 테마 정보 섹션 (2026-10-18 사용자: "주식 관련해서도 정책 등, 나이별 포트폴리오 전략 등을 넣고 전문가들 이야기도 넣어서" — 연구 ⑂ 기획)
    an = _rd('analyst/data.json')
    ex = an.get('experts', [])
    css = '<link rel="stylesheet" href="/assets/analyst/analyst.css?v=4"><link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    urls = []
    how = ('<details class="an-how"><summary>어떻게 모았나요?</summary><ol><li>증권·경제 기사 RSS에서 리서치센터장·CIO·이코노미스트·한국은행·KDI·IMF·월가 기관 등 실명 기관·인물의 발언이 제목에 나온 기사만 골라요.</li>'
           '<li>주제(코스피·미국 증시·금리·환율·반도체·부동산·경기·코인·원자재)와 성격(시장 전망·자산배분 조언·리스크 경고)으로 나눠요.</li><li>발언(따옴표) 부분으로 긍정·신중을 가려, 같은 주제에서 둘 다 있으면 나란히 보여 줘요.</li>'
           '<li>기사 본문은 옮기지 않고 제목(발언 요지)과 원문 링크만 실어요.</li></ol></details>')
    page('/money/experts/', '전문가 코멘트 종합 — 리서치센터장·CIO·한은·IMF 시장 전망 비교',
         '증권사 리서치센터장, 운용사 CIO, 한국은행·KDI·IMF 등 실명 전문가 발언을 주제별로 모으고, 같은 주제에서 의견이 엇갈리면 나란히 비교했어요.',
         '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 전문가 코멘트</p><h1>🎙️ 전문가 코멘트 종합</h1>' + MONEY_NOTE
         + (experts_html(ex) or '<p class="nw-empty">아직 모인 발언이 없어요. 매시간 새로 모아요.</p>') + how + css,
         [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('전문가 코멘트', '/money/experts/')])
    urls.append('/money/experts/')
    a = json.load(open(os.path.join(HERE, 'money_age.json'), encoding='utf-8'))
    common = ''.join(f'<li><b>{E(k)}</b><span>{E(v)}</span></li>' for k, v in a['common'])
    rule = f'<section class="mg-s"><h2>📏 {E(a["rule"]["title"])}</h2><p>{E(a["rule"]["body"])}</p><ul class="al-r">{"".join(f"<li>{E(x)}</li>" for x in a["rule"]["limits"])}</ul></section>'
    ages = ''.join(f'<section class="mg-s ag-{x["k"]}" id="{x["k"]}"><h2>{E(x["t"])} <small>— {E(x["focus"])}</small></h2><ul class="ag-l">{"".join(f"<li>{E(i)}</li>" for i in x["items"])}</ul></section>' for x in a['ages'])
    jump = ''.join(f'<a href="#{x["k"]}">{E(x["t"].split(" · ")[0])}</a>' for x in a['ages'])
    adv = experts_html(ex, cats=('자산배분 조언', '리스크 경고'), limit=4)
    page('/money/age/', '나이별 자산관리 일반 원칙 — 20대부터 은퇴 후까지',
         '20대 사회초년생, 30대 결혼·내 집 마련, 40대, 50대 은퇴 준비, 60대 이상 인출기까지 흔히 쓰이는 자산관리 원칙: 비상금, 세제 혜택 계좌 순서, 100−나이 규칙과 한계, 분산·리밸런싱.',
         '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 나이별 원칙</p><h1>🧭 나이별 자산관리 일반 원칙</h1>'
         + f'<p class="an-warn">⚠️ {E(a["note"])}</p><p class="hm-links">{jump}<a href="/money/policy/">투자 정책 정리 →</a></p>'
         + f'<section class="mg-s"><h2>🧱 나이와 상관없는 공통 원칙</h2><ul class="ag-c">{common}</ul></section>' + rule + ages
         + (f'<h2>🎙️ 요즘 전문가들의 자산배분·리스크 이야기</h2>{adv}' if adv else '') + css,
         [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('나이별 원칙', '/money/age/')])
    urls.append('/money/age/')
    pol = os.path.join(HERE, 'money_policy.json')
    if os.path.exists(pol):
        P = json.load(open(pol, encoding='utf-8'))
        secs = ''
        for it in P.get('items', []):
            rows = ''.join(f'<tr><th>{E(r[0])}</th><td>{E(r[1])}</td></tr>' for r in it.get('rows', []) if len(r) >= 2)
            src = ''.join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">{E(x["title"])}</a>{(" · " + E(x["date"])) if x.get("date") else ""}</li>' for x in it.get('sources', []))
            ver = '' if it.get('verified', True) else '<p class="an-warn">🔎 공식 자료를 찾지 못해 보도 기준으로 정리했어요. 가입 전 공식 안내를 꼭 확인하세요.</p>'
            secs += (f'<section class="mg-s" id="{E(it["key"])}"><h2>{E(it["name"])}</h2>{ver}<table class="pl-t">{rows}</table>'
                     + (f'<p class="pl-ch">🆕 {E(it["changes"])}</p>' if it.get('changes') else '') + (f'<details class="pl-src"><summary>출처</summary><ul>{src}</ul></details>' if src else '') + '</section>')
        jump = ''.join(f'<a href="#{E(it["key"])}">{E(it["name"].split("(")[0])}</a>' for it in P.get('items', []))
        rel = experts_html([e for e in ex if e['topic'] in ('금리', '코스피·국내 증시', '경기·성장률')], limit=2)
        page('/money/policy/', '투자 관련 정책·제도 정리 — ISA·연금저축·IRP·청년도약계좌·공모주·세제·공매도',
             'ISA, 연금저축·IRP 세액공제, 청년도약계좌, 공모주 청약 배정, 금투세·배당소득 과세, 공매도 제도를 공식 자료 기준으로 표로 정리했어요(기준일·출처 표시).',
             '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 투자 정책</p><h1>🏛️ 투자 관련 정책·제도 정리</h1>' + MONEY_NOTE
             + f'<p class="pl-asof">기준일 {E(P.get("asof", ""))} · 금융위원회·기획재정부·국세청 등 공식 자료 기준. 제도는 바뀔 수 있으니 가입 전 공식 안내를 확인하세요.</p><p class="hm-links">{jump}</p>'
             + secs + '<p class="hm-links"><a href="/apply/">💰 지원금·청약 데이터 보기</a><a href="/money/age/">🧭 나이별 원칙</a></p>' + (f'<h2>🎙️ 관련 전문가 코멘트</h2>{rel}' if rel else '') + css,
             [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('투자 정책', '/money/policy/')])
        urls.append('/money/policy/')
    return urls


def apply_rec_page():
    # 루리의 청약 추천 (2026-10-18 사용자: "청약 추천도 만들어") — 생활 테마
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/apply/">생활</a> › 청약 추천</p><h1>🏠 루리의 청약 추천</h1>'
            + say('o_cardigan', '내 상황을 고르면 청약 가점이랑 노려볼 만한 공급 유형, 지금 접수 중인 공고 중 맞는 걸 골라 드려요. 입력한 내용은 이 폰에만 저장돼요.')
            + '<section id="aprec" aria-label="청약 추천"><noscript>자바스크립트가 필요해요.</noscript></section>'
            + '<p class="note">청약 가점은 대략 계산이며, 특별공급 자격(소득·자산·거주 기간 등)은 단지마다 달라요. 신청 전 공고문과 청약홈에서 꼭 확인하세요.</p>'
            + '<link rel="stylesheet" href="/assets/apply/rec.css?v=1"><script defer src="/assets/apply/rec.js?v=1"></script>')
    page('/apply/recommend/', '청약 가점 계산기 · 청약 추천 — 내 가점·노려볼 공급 유형·지금 접수 중인 공고', '지역·나이·결혼·자녀·무주택 기간·부양가족·통장 기간을 고르면 청약 가점(84점)과 신혼·생애최초·다자녀·청년·공공임대 등 노려볼 공급 유형, 지금 접수 중인 공고를 골라 드려요.',
         body, [('루리의 줍줍', '/'), ('생활', '/apply/'), ('청약 추천', '/apply/recommend/')])
    return ['/apply/recommend/']


def rss_feed(live, aps):
    """/rss.xml — 새로 생기는 페이지(매거진·풍자·새 공모전·새 지원금·고민 해결)를 최신순 60개. 2026-10-18 자연 유입 전략 ①."""
    from email.utils import format_datetime
    KST_ = datetime.timezone(datetime.timedelta(hours=9))
    it = []
    def add(u, t, d, desc):
        if u in COLL:   # 합쳐진 얇은 페이지는 RSS 에 넣지 않음
            return
        if d[:10] > TODAY.isoformat():   # 시작일이 미래인 공고는 아직 새 글이 아님
            return
        try:
            dt = datetime.datetime.fromisoformat(d).replace(tzinfo=KST_) if len(d) > 10 else datetime.datetime.combine(datetime.date.fromisoformat(d), datetime.time(7, 30), KST_)
        except Exception:
            return
        it.append((dt, u, t, desc))
    for f in sorted(os.listdir(os.path.join(ROOT, 'mag', 'archive')), reverse=True)[:14] if os.path.isdir(os.path.join(ROOT, 'mag', 'archive')) else []:
        d = f[:-5]; add(f'/mag/{d}/', f'루리의 이슈 리딩 {kdate(d)}', d, f'{kdate(d)} 정치 이슈·커뮤니티 화제·마감 공모전·새 지원금 한 장 정리')
    for d, v in satire_days()[:14]:
        add(f'/satire/{d}/', f'{kdate(d)} 루리 풍자 — ' + (v['cap'][0] if v['cap'] else '만평'), d, ' '.join(v['cap'][:2])[:150])
    for c in sorted([c for c in live if (c.get('start') or '9') <= TODAY.isoformat()], key=lambda c: c['start'], reverse=True)[:25]:
        if c.get('start'):
            add(f'/c/{c["id"]}/', f'{c["title"]} — {c["end"][5:].replace("-", "/")} 마감', c['start'], f'{c.get("org") or ""} 주최 · 상금 {c.get("prize") or "공고 확인"} · 응모 자격·접수 방법 정리')
    for a in sorted([a for a in aps if a.get('start') and a['start'] <= TODAY.isoformat()], key=lambda a: a['start'], reverse=True)[:15]:
        add(f'/a/{a["id"]}/', a['title'], a['start'], f'{a.get("kind", "")} · {a.get("org") or ""} · 신청 기간과 방법 정리')
    for x in REVIEWS[:15]:
        add(f'/review/{x["slug"]}/', '[평론] ' + x['title'], x['date'] + 'T09:00:00', x['desc'])
    for q in QA[:10]:
        add(f'/guide/{q["slug"]}/', q['title'], (q.get('date') or TODAY.isoformat())[:10], q.get('desc', ''))
    it.sort(key=lambda x: x[0], reverse=True)
    items = ''.join(f'<item><title>{E(t)}</title><link>{SITE}{u}</link><guid>{SITE}{u}</guid><pubDate>{format_datetime(dt)}</pubDate><description>{E(desc)}</description></item>\n' for dt, u, t, desc in it[:60])
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>루리의 줍줍</title><link>{SITE}/</link>'
           f'<description>이슈·기사 확인 신호·애널리스트 분석·공모전·지원금 정보를 매일 정리하는 루리의 줍줍</description><language>ko</language>\n{items}</channel></rss>\n')
    open(os.path.join(ROOT, 'rss.xml'), 'w', encoding='utf-8', newline='\n').write(xml)


def issue_note(x, I):
    """이슈 묶음 숫자로 만든 루리 해설 (기사 문장 전재 없음)."""
    A = [I[a] for a in x['a'] if a in I]
    sc = [a['s'] for a in A if a.get('s') is not None]
    t = f'루리 해설: 기사 {len(A)}건을 같은 사건으로 묶었어요.'
    if sc:
        t += f' 확인 신호 점수는 가장 높은 기사 {max(sc)}점, 가장 낮은 기사 {min(sc)}점' + (f'으로 {max(sc) - min(sc)}점 차이가 나요.' if max(sc) != min(sc) else '으로 같아요.')
    w = collections.Counter(y for a in A for y in a.get('why', []))
    neg = [k for k in w if k.startswith(('⚠', '❓', '🔎'))]
    if neg:
        t += f' 자주 걸린 신호는 「{neg[0].lstrip("⚠️❓🔎 ").strip()}」({w[neg[0]]}건)이에요.'
    if x.get('cf'):
        t += ' 언론사마다 숫자가 달라서, 공식 발표가 나오면 다시 확인해야 해요.'
    elif x.get('claim'):
        t += ' 누군가의 발언·주장을 전하는 기사라, 사실 여부는 따로 확인이 필요해요.'
    elif int(x.get('on') or 0) >= 5:
        t += ' 여러 언론사가 같은 내용을 전해 사건 자체는 확인된 편이에요.'
    return t


def news_static():
    """검색엔진·자바스크립트 없는 환경용으로 이슈 순위를 글자로 미리 그려 둔다(화면에선 news.js 가 바로 대체). 2026-10-18 자연 유입 전략 ①."""
    d = _rd('news/data.json')
    if not d:
        return '<noscript>자바스크립트가 필요해요.</noscript>'
    I = {a['id']: a for a in d.get('items', [])}
    G = {'ok': '확인 신호 많음', 'warn': '추가 확인 필요', 'bad': '주의 신호'}
    out = f'<p>{E(d.get("updated", ""))} 기준 · 언론사 기사 {len(d.get("items", []))}건을 같은 사건끼리 묶은 이슈 순위와 확인 신호 점수예요.</p><ol class="nw-static">'
    for x in sorted(d.get('issues', []), key=lambda x: (x.get('c') != '정치', x['n']))[:40]:
        arts = ''.join(f'<li>{E(I[a]["o"])} · {I[a]["s"] if I[a].get("s") is not None else "-"}점 · <a href="{E(I[a]["u"])}" rel="nofollow noopener" target="_blank">{E(I[a]["t"])}</a></li>' for a in x['a'][:6] if a in I)
        why = ''
        if x['a'] and x['a'][0] in I:
            why = ' / '.join(E(w) for w in I[x['a'][0]].get('why', [])[:3])
        out += (f'<li id="is{x["n"]}"><h2>{E(x["t"])}</h2><p>{E(x["c"])} · 언론사 {x["on"]}곳 보도 · 확인 신호 {x["s"] if x.get("s") is not None else "-"}점({G.get(x.get("g"), "")})'
                f'{" · 발언·주장 기사" if x.get("claim") else ""}{(" · 숫자 엇갈림: " + E(", ".join(x["cf"]))) if x.get("cf") else ""}</p><p>{why}</p><p class="nw-ins">{E(issue_note(x, I))}</p><ul>{arts}</ul></li>')
    return out + '</ol>'


TOOLS = {'dividend': ('배당소득 분리과세 계산기', '고배당 기업 배당을 분리과세로 받으면 세금이 얼마인지 구간별 세율(14·20·25·30%)로 대략 계산해요.'),
         'stocktax': ('증권거래세 계산기', '2026년 증권거래세율(코스피 0.05%+농특세 0.15%, 코스닥 0.20%, 코넥스 0.10%)로 팔 때 세금을 계산해요.'),
         'pension': ('연금 세액공제 계산기', '연금저축(600만원)·IRP 합산(900만원) 한도와 공제율(16.5%·13.2%)로 돌려받는 세금을 계산해요.'),
         'loan': ('대출 이자 계산기', '원리금균등·원금균등·만기일시 상환별로 첫 달 상환액과 총 이자, 금리 0.25%p 오르내릴 때 차이를 비교해요.'),
         'fx': ('환전 계산기', '매매기준율·수수료·환율 우대로 실제 받는 외화를 계산하고, 우대로 얼마나 더 받는지 비교해요.'),
         'salary': ('연봉 실수령액 계산기', '2026년 4대보험 요율(국민연금 4.75%·건강보험 3.595%·장기요양·고용보험 0.9%)과 소득세로 연봉에서 매달 실제 받는 돈을 계산해요.'),
         'severance': ('퇴직금 계산기', '입사일·퇴사일과 최근 3개월 임금으로 법정 퇴직금(세전)과 퇴직소득세를 뺀 세후 금액을 계산해요. 알바도 같은 기준이에요.'),
         'unemployment': ('실업급여 계산기', '2026년 구직급여 상한액(하루 68,100원)·하한액과 가입기간·나이별 받는 날 수로 실업급여 총액을 계산해요.')}
TOOL_T = {  # 2026-10-18 키워드 전략: 검색 자동완성 문구 제목 (주소는 그대로)
 'dividend': '배당금 계산기 — 2026 고배당 분리과세 세금',
 'stocktax': '주식 세금 계산기 — 2026 증권거래세 (코스피·코스닥)',
 'pension': '연금저축 IRP 세액공제 계산기 2026 (환급액)',
 'loan': '대출 이자 계산기 (주담대 원리금균등·원금균등·만기일시)',
 'fx': '환율 계산기 (달러·엔화 환전 수수료·우대 포함)',
 'salary': '연봉 실수령액 계산기 2026 (4대보험·소득세 공제 후 월급)',
 'severance': '퇴직금 계산기 2026 — 퇴직금 계산법·세전 세후 (알바 포함)',
 'unemployment': '실업급여 계산기 2026 — 신청자격·금액·기간 (상한 68,100원)'}
TOOL_SRC = {  # 기준일·출처 (2026-10-18 확인)
 'salary': '국민연금 9.5%·기준소득월액 41만~659만원(국민연금공단, 2026.7~2027.6), 건강보험료율 7.19%·장기요양 0.9448%(보건복지부·국민건강보험공단), 고용보험 근로자 0.9%(고용노동부), 소득세 기본세율·근로소득공제(소득세법)',
 'severance': '근로자퇴직급여 보장법(평균임금 30일분 × 근속연수), 소득세법 퇴직소득 근속연수공제·환산급여공제(2023.1.1 이후 퇴직분)',
 'unemployment': '고용노동부 「고용보험법 시행령」 개정(구직급여 상한 66,000원 → 68,100원, 2026.1.1 이후 이직자), 2026년 최저임금 시급 10,320원(최저임금위원회), 고용보험법 소정급여일수 표',
 'dividend': '기획재정부 2025년 세법개정(고배당 기업 배당소득 분리과세)', 'stocktax': '기획재정부 증권거래세법 시행령(2026.1.1 시행)',
 'pension': '소득세법 연금계좌 세액공제(국세청)', 'loan': '원리금 계산 공식(금리는 직접 입력)', 'fx': '은행 환전 수수료 공식(환율은 직접 입력)'}
TOOL_FAQ = {
 'salary': [('연봉 4,000만원이면 월 실수령액은 얼마인가요?', '비과세 식대 월 20만원, 본인 1명 기준으로 4대보험과 소득세를 빼면 한 달 약 292만원이에요. 부양가족이 많으면 소득세가 줄어 조금 더 받아요.'),
            ('2026년에 실수령액이 줄어든 이유는?', '국민연금 보험료율이 9%에서 9.5%로, 건강보험료율이 7.09%에서 7.19%로 올라 같은 연봉이라도 공제액이 늘었어요.'),
            ('회사 명세서와 금액이 조금 다른 이유는?', '회사는 국세청 간이세액표로 소득세를 떼고, 이 계산기는 연말정산 식으로 1년치를 계산해 12로 나눠요. 그래서 소득세가 몇천~몇만 원 다를 수 있어요.')],
 'severance': [('알바도 퇴직금을 받을 수 있나요?', '주 15시간 이상 일하고 1년(365일) 이상 일했다면 알바·계약직도 법정 퇴직금 대상이에요.'),
               ('퇴직금은 언제까지 받아야 하나요?', '퇴사 후 14일 안에 받아야 해요. 당사자 합의로 기한을 늦출 수는 있어요.'),
               ('퇴직금에도 세금이 붙나요?', '퇴직소득세가 붙지만 근속연수공제·환산급여공제가 커서 근로소득보다 훨씬 적어요. IRP로 받으면 연금을 받을 때까지 세금이 미뤄져요.')],
 'unemployment': [('2026년 실업급여 상한액은 얼마인가요?', '2026년 1월 1일 이후 이직자부터 하루 68,100원이에요. 2019년부터 이어진 66,000원에서 올랐어요.'),
                  ('하한액은 어떻게 정해지나요?', '그해 최저임금의 80%에 하루 소정근로시간을 곱해요. 2026년 하루 8시간이면 10,320원 × 80% × 8시간 = 66,048원이에요.'),
                  ('실업급여는 며칠 동안 받나요?', '고용보험 가입기간과 나이에 따라 120일에서 270일까지예요. 50세 이상이거나 장애인이면 같은 가입기간이라도 더 오래 받아요.')],
 'loan': [('원리금균등과 원금균등 중 뭐가 이자가 적나요?', '원금균등이 총 이자가 가장 적어요. 대신 첫 달 내는 돈이 가장 커요.'), ('금리 0.25%p 차이가 크나요?', '2억원 30년 대출이면 총 이자가 1천만원 넘게 달라질 수 있어요.')],
 'pension': [('연금저축과 IRP 세액공제 한도는?', '연금저축 연 600만원, IRP를 합쳐 연 900만원까지 공제돼요.'), ('공제율은 얼마인가요?', '총급여 5,500만원 이하는 16.5%, 넘으면 13.2%예요.')],
 'dividend': [('고배당 분리과세 세율은?', '2천만원까지 14%, 3억원까지 20%, 50억원까지 25%, 그 위 30%이고 지방소득세 10%가 붙어요.')],
 'stocktax': [('2026년 증권거래세율은?', '코스피 0.20%(거래세 0.05% + 농어촌특별세 0.15%), 코스닥 0.20%, 코넥스 0.10%예요.')],
 'fx': [('환율 우대 90%는 무슨 뜻인가요?', '은행 환전 수수료의 90%를 깎아 준다는 뜻이에요. 수수료 1.75%면 실제로는 0.175%만 내요.')]}
TOOL_HELP_NEW = {
 'salary': '<h2>어떻게 계산하나요?</h2><p>연봉을 12로 나눈 월급에서 비과세(식대 월 20만원 등)를 뺀 금액에 4대보험 요율을 곱해요. 국민연금은 기준소득월액(41만~659만원) 안에서 4.75%, 건강보험 3.595%, 장기요양은 건강보험료의 13.14%, 고용보험 0.9%예요. 소득세는 근로소득공제·인적공제(1명 150만원)·보험료 공제를 뺀 과세표준에 기본세율(6~45%)을 매기고, 근로소득세액공제와 표준세액공제를 뺀 뒤 12로 나눠요. 지방소득세는 소득세의 10%예요.</p><p>연봉 구간별 결과는 <a href="/money/tools/salary/table/">2026 연봉 실수령액표</a>에서 한눈에 볼 수 있어요.</p><h2>주의할 점</h2><ul class="chk"><li>국민연금 상한(659만원)을 넘는 고연봉은 연금이 더 늘지 않아요.</li><li>자녀세액공제, 신용카드·의료비 공제는 연말정산 때 따로 반영돼요.</li><li>상여금이 따로 나오는 회사는 상여가 나오는 달 공제가 커져요.</li></ul>',
 'severance': '<h2>어떻게 계산하나요?</h2><p>퇴직금 = 1일 평균임금 × 30일 × (재직일수 ÷ 365)예요. 1일 평균임금은 퇴사 전 3개월 동안 받은 임금 총액(지난 1년 상여금과 연차수당의 3/12 포함)을 그 3개월의 날짜 수로 나눠요. 퇴직소득세는 근속연수공제와 환산급여공제를 빼고 계산해서 같은 금액의 근로소득보다 세금이 훨씬 적어요.</p><h2>예시</h2><p>월 300만원을 받으며 3년(1,095일) 일했다면 1일 평균임금은 약 9만 8천원, 퇴직금은 약 880만원이에요. 퇴직소득세는 근속연수공제(300만원)를 빼고 계산해 몇만 원 수준이에요.</p><h2>주의할 점</h2><ul class="chk"><li>주 15시간 미만 근무 기간은 재직일수에서 빠질 수 있어요.</li><li>퇴직 직전 3개월에 휴업·육아휴직 기간이 있으면 그 기간은 빼고 계산해요.</li><li>회사가 14일 안에 주지 않으면 고용노동부에 진정할 수 있어요.</li></ul>',
 'unemployment': '<h2>어떻게 계산하나요?</h2><p>하루 받는 돈(구직급여일액)은 퇴사 전 3개월 1일 평균임금의 60%예요. 이 값이 상한액(2026년 1월 1일 이후 이직자 68,100원)보다 크면 상한액을, 하한액(최저임금 10,320원 × 80% × 하루 소정근로시간)보다 작으면 하한액을 줘요. 받는 날 수(소정급여일수)는 고용보험 가입기간과 나이로 정해져요.</p><table class="info"><tr><th>가입기간</th><th>50세 미만</th><th>50세 이상·장애인</th></tr><tr><td>1년 미만</td><td>120일</td><td>120일</td></tr><tr><td>1~3년</td><td>150일</td><td>180일</td></tr><tr><td>3~5년</td><td>180일</td><td>210일</td></tr><tr><td>5~10년</td><td>210일</td><td>240일</td></tr><tr><td>10년 이상</td><td>240일</td><td>270일</td></tr></table><h2>받을 수 있는 조건</h2><ul class="chk"><li>이직 전 18개월 동안 고용보험 가입일(피보험 단위기간)이 180일 이상</li><li>권고사직·계약 만료·폐업처럼 본인 뜻이 아닌 퇴사 (자발적 퇴사라도 임금 체불·통근 곤란 등 정당한 사유가 있으면 가능)</li><li>일할 의사와 능력이 있고 재취업 활동을 할 것</li></ul><p>신청은 퇴사 후 고용24에서 구직 등록 → 수급자격 신청 순서로 해요. 퇴사 다음 날부터 12개월이 지나면 남은 날은 못 받으니 빨리 신청하세요.</p>'}


def rel_block(pat, links):
    # 같이 보면 좋은: 직접 쓴 가이드(QA) 중 pat 이 제목에 든 것 + 고정 링크
    g = [(f'/guide/{q["slug"]}/', q['title']) for q in QA if re.search(pat, q['title'])][:4] if pat else []
    L = g + [x for x in links if x[0] not in [y[0] for y in g]]
    return ('<section class="rel"><h2>📎 같이 보면 좋은</h2><ul>' + ''.join(f'<li><a href="{u}">{E(t)}</a></li>' for u, t in L[:8]) + '</ul></section>') if L else ''


TOOL_REL = {'salary': (r'연봉|월급|4대보험|연말정산|세금', [('/money/tools/salary/table/', '2026 연봉 실수령액표'), ('/money/tools/severance/', '퇴직금 계산기'), ('/money/tools/pension/', '연금저축 IRP 세액공제 계산기'), ('/money/age/', '나이별 돈 관리 원칙')]),
            'severance': (r'퇴직|퇴사|실업|IRP', [('/money/tools/unemployment/', '실업급여 계산기'), ('/money/tools/salary/', '연봉 실수령액 계산기'), ('/money/tools/pension/', 'IRP 세액공제 계산기')]),
            'unemployment': (r'실업|퇴사|구직|청년', [('/money/tools/severance/', '퇴직금 계산기'), ('/apply/', '지원금·청약 일정'), ('/money/tools/salary/', '연봉 실수령액 계산기')]),
            'loan': (r'대출|금리|주담대|청약', [('/apply/recommend/', '청약 가점 추천'), ('/money/policy/', '2026 투자 정책 정리')]),
            'pension': (r'연금|IRP|ISA|세액공제', [('/money/tools/salary/', '연봉 실수령액 계산기'), ('/money/age/', '나이별 원칙')]),
            'dividend': (r'배당|ISA|세금', [('/money/policy/', '2026 투자 정책 정리'), ('/analyst/', '애널리스트 의견 종합')]),
            'stocktax': (r'주식|세금|ISA', [('/money/policy/', '2026 투자 정책 정리'), ('/analyst/', '애널리스트 의견 종합')]),
            'fx': (r'환율|환전|여행', [('/money/tools/loan/', '대출 이자 계산기')])}


def salary_table():
    import paycalc
    rows = ''.join(f'<tr><td>{a // 10000:,}만원</td><td>{won_txt(int(r["m"]))}</td><td>{int(r["p"] + r["h"] + r["l"] + r["e"]):,}원</td><td>{int(r["it"] + r["lt"]):,}원</td><td><b>{int(r["net"]):,}원</b></td></tr>'
                   for a in range(20_000_000, 100_000_001, 1_000_000) for r in [paycalc.salary(a)])
    r40, r30, r60 = paycalc.salary(40_000_000), paycalc.salary(30_000_000), paycalc.salary(60_000_000)
    body = (f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › <a href="/money/tools/salary/">연봉 실수령액 계산기</a> › 실수령액표</p><h1>📋 연봉 실수령액 표 2026 (2,000만~1억)</h1>'
            f'<p>2026년 4대보험 요율과 소득세 기본세율로 연봉 100만원 단위 월 실수령액을 계산한 표예요. 비과세 식대 월 20만원, 본인 1명(부양가족 없음) 기준이에요. 예를 들어 연봉 3,000만원은 월 약 {int(r30["net"]):,}원, 4,000만원은 약 {int(r40["net"]):,}원, 6,000만원은 약 {int(r60["net"]):,}원을 받아요. '
            f'연봉이 1,000만원 오를 때 실수령액은 생각보다 덜 늘어나는데, 소득세 세율 구간이 올라가고 4대보험도 함께 늘기 때문이에요. 부양가족이 있거나 비과세가 다르면 <a href="/money/tools/salary/">계산기</a>에 직접 넣어 보세요.</p>'
            f'<div class="tbl-w"><table class="info sal-t"><tr><th>연봉</th><th>월 세전</th><th>4대보험</th><th>소득세+지방세</th><th>월 실수령액</th></tr>{rows}</table></div>'
            f'<p class="note">기준일 2026-10-18 · 출처: {E(TOOL_SRC["salary"])}. 참고용 계산이며 회사 간이세액표와 소득세가 조금 다를 수 있어요.</p>'
            + rel_block(r'연봉|월급|4대보험|연말정산', [('/money/tools/salary/', '연봉 실수령액 계산기'), ('/money/tools/severance/', '퇴직금 계산기'), ('/money/tools/unemployment/', '실업급여 계산기')]))
    page('/money/tools/salary/table/', '연봉 실수령액 표 2026 — 2,000만~1억 월급 (4대보험·세금 공제 후)', f'2026년 4대보험·소득세 기준 연봉 실수령액표. 연봉 4,000만원 월 {int(r40["net"]):,}원 등 2,000만~1억 원을 100만원 단위로 정리.',
         body + '<link rel="stylesheet" href="/assets/money/tools.css?v=2">', [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('연봉 실수령액 계산기', '/money/tools/salary/'), ('실수령액표', '/money/tools/salary/table/')])
    return ['/money/tools/salary/table/']



TOOL_HELP = {  # 2026-10-18 애드센스 보강: 계산기마다 계산 방법·예시·주의 (숫자 근거는 /money/policy/)
 'dividend': '<h2>어떻게 계산하나요?</h2><p>2026년 1월 1일 이후 받는 고배당 기업 배당은 다른 금융소득과 합치지 않고 따로 세금을 매기는 분리과세를 고를 수 있어요. 세율은 구간별로 올라가요. 2천만원까지 14%, 3억원까지 20%, 50억원까지 25%, 그 위로 30%이고, 여기에 국세의 10%가 지방소득세로 붙어요.</p><h2>예시</h2><p>배당 3천만원이면 2천만원 × 14% = 280만원, 나머지 1천만원 × 20% = 200만원, 국세 480만원에 지방소득세 48만원을 더해 약 528만원이에요. 같은 돈을 일반 원천징수 15.4%로 내면 462만원이라, 금액이 크지 않으면 원천징수가 더 쌀 수도 있어요.</p><h2>주의할 점</h2><ul class="chk"><li>배당성향 등 요건을 채운 「고배당 기업」 배당에만 적용돼요.</li><li>금융소득이 연 2천만원을 넘으면 종합과세와 비교해 유리한 쪽을 골라야 해요.</li><li>건강보험료(피부양자 자격)에 영향이 있을 수 있어요.</li></ul>',
 'stocktax': '<h2>어떻게 계산하나요?</h2><p>증권거래세는 주식을 팔 때 매도 금액에 세율을 곱해 증권사가 바로 떼어 가요. 2026년부터 코스피는 증권거래세 0.05%에 농어촌특별세 0.15%를 더해 0.20%, 코스닥과 K-OTC는 0.20%, 코넥스는 0.10%예요. 이익이 났는지 손해를 봤는지와 상관없이 팔 때마다 붙어요.</p><h2>예시</h2><p>코스피 주식을 1천만원어치 팔면 1천만원 × 0.20% = 2만원이에요. 같은 금액을 하루에 다섯 번 사고팔면 세금만 10만원이 나가요.</p><h2>주의할 점</h2><ul class="chk"><li>증권사 매매 수수료는 따로 붙어요.</li><li>대주주 양도소득세는 별도 세금이에요.</li><li>해외 주식은 이 세율이 아니라 양도소득세(연 250만원 공제 후 22%)가 적용돼요.</li></ul>',
 'pension': '<h2>어떻게 계산하나요?</h2><p>연금저축은 연 600만원까지, 연금저축과 IRP를 합쳐 연 900만원까지 낸 돈의 일부를 세금에서 돌려받아요. 총급여 5,500만원 이하(종합소득 4,500만원 이하)는 16.5%, 그보다 많으면 13.2%를 공제받아요.</p><h2>예시</h2><p>총급여 5천만원인 직장인이 연금저축 600만원과 IRP 300만원을 내면 900만원 × 16.5% = 148만 5천원을 연말정산에서 돌려받아요. 연금저축만 900만원을 내면 한도 600만원만 인정돼 99만원이에요.</p><h2>주의할 점</h2><ul class="chk"><li>중도 해지하면 공제받은 세금을 기타소득세(16.5%)로 다시 내요.</li><li>55세 이후 연금으로 받을 때 연금소득세(3.3~5.5%)가 붙어요.</li><li>ISA 만기 자금을 옮기면 300만원 한도가 더 생겨요(이 계산기에는 빠져 있어요).</li></ul>',
 'loan': '<h2>상환 방식별 차이</h2><p><b>원리금균등</b>은 매달 같은 금액을 내서 계획 세우기 쉽지만, 초반엔 이자 비중이 커요. <b>원금균등</b>은 원금을 똑같이 나눠 갚아 첫 달 부담이 가장 크지만 총 이자가 가장 적어요. <b>만기일시</b>는 매달 이자만 내고 마지막에 원금을 한 번에 갚아 총 이자가 가장 많아요.</p><h2>예시</h2><p>2억원을 연 4.2%, 30년(360개월) 원리금균등으로 빌리면 매달 약 97만 8천원, 총 이자는 약 1억 5천 2백만원이에요. 금리가 0.25%p만 올라도 총 이자가 1천만원 넘게 늘어요. 계산 결과 표에서 금리가 바뀔 때 차이를 바로 볼 수 있어요.</p><h2>주의할 점</h2><ul class="chk"><li>변동금리는 기준금리·코픽스에 따라 매달 내는 돈이 바뀌어요.</li><li>중도상환수수료(보통 3년 이내 1% 안팎)는 따로예요.</li><li>DSR 규제로 실제 대출 한도는 소득에 따라 달라요.</li></ul>',
 'fx': '<h2>어떻게 계산하나요?</h2><p>은행은 매매기준율에 환전 수수료(현찰 기준 보통 1.75% 안팎)를 붙여 팔아요. 환율 우대 90%는 이 수수료의 90%를 깎아 준다는 뜻이라, 실제 수수료는 1.75% × 10% = 0.175%가 돼요.</p><h2>예시</h2><p>100만원을 매매기준율 1,380원에 우대 없이 바꾸면 적용 환율은 약 1,404원이라 약 712달러를 받아요. 90% 우대를 받으면 약 1,382원이 되어 약 723달러로, 11달러쯤 더 받아요.</p><h2>주의할 점</h2><ul class="chk"><li>현찰과 송금(전신환)은 수수료가 달라요.</li><li>공항 환전소는 우대가 적은 편이라, 은행 앱으로 미리 신청하고 공항에서 받으면 유리해요.</li><li>매매기준율은 하루에도 여러 번 바뀌어요.</li></ul>'}


def tool_pages():
    # 이슈형 미니 도구 (2026-10-18 핫이슈 기획) — 참고용, 투자 수익 계산 없음
    urls = []
    TOOL_HELP.update(TOOL_HELP_NEW)
    for k, (n, d) in TOOLS.items():
        others = ''.join(f'<a href="/money/tools/{k2}/">{E(n2)}</a>' for k2, (n2, _) in TOOLS.items() if k2 != k)
        tt = TOOL_T.get(k, f'{n} — 2026 기준 간단 계산')
        fq = TOOL_FAQ.get(k, [])
        ld = {'@context': 'https://schema.org', '@graph': [{'@type': 'WebApplication', 'name': tt, 'url': f'{SITE}/money/tools/{k}/', 'applicationCategory': 'FinanceApplication', 'operatingSystem': 'Any', 'inLanguage': 'ko', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW'}, 'description': d}]
              + ([{'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in fq]}] if fq else [])}
        extra = (('<h2>자주 묻는 질문</h2>' + ''.join(f'<details class="faq"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in fq)) if fq else '') \
            + f'<p class="note">기준일 2026-10-18 · 출처: {E(TOOL_SRC.get(k, ""))}. 참고용 계산이에요. 실제 금액은 해당 기관 안내로 확인하세요.</p>' + rel_block(*TOOL_REL.get(k, ('', [])))
        page(f'/money/tools/{k}/', tt, d,
             f'<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › {E(n)}</p><h1>🧮 {E(tt)}</h1><p>{E(d)}</p>'
             f'<section id="mtool" data-tool="{k}"><noscript>자바스크립트가 필요해요.</noscript></section>{TOOL_HELP.get(k, '')}{extra}<p class="hm-links">{others}<a href="/money/policy/">🏛️ 근거: 투자 정책 정리</a></p>'
             '<link rel="stylesheet" href="/assets/money/tools.css?v=2"><link rel="stylesheet" href="/assets/mag/mag.css?v=10"><script defer src="/assets/money/tools.js?v=2"></script>',
             [('루리의 줍줍', '/'), ('머니', '/analyst/'), (n, f'/money/tools/{k}/')], ld)
        urls.append(f'/money/tools/{k}/')
    return urls + salary_table()


HOT_TYPE = {'health': '🏥 의료·건강', 'labor': '💼 일·임금', 'housing': '🏠 청약·주거', 'grant': '💰 지원금·저축', 'tax': '🧾 세금·세제', 'rate': '📉 금리·환율', 'market': '📈 증시·코인', 'event': '📅 행사·날씨'}


def hot_live():
    d = _rd('hot/db.json')
    cut = (datetime.datetime.now() - datetime.timedelta(hours=48)).strftime('%Y-%m-%d %H:%M')
    return sorted([v for v in d.values() if not v.get('dup') and v['last'] >= cut], key=lambda v: (-len(v['outs']), v['last']), reverse=False), d


def hot_pages():
    # 핫이슈 랜딩 (2026-10-18 사용자: "트렌드 분석에 따른 핫이슈에 맞춘 것들을 만들어") — hot.py 매시
    live, db = hot_live()
    if not db:
        return []
    import sys
    sys.path.insert(0, HERE)
    import hot as H
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><link rel="stylesheet" href="/assets/analyst/analyst.css?v=4"><link rel="stylesheet" href="/assets/news/news.css?v=6">'
    urls = ['/hot/']
    livesl = {v['slug'] for v in live}
    hd = os.path.join(ROOT, 'hot')
    for v in db.values():
        if v.get('dup') and v['dup'] in db:   # 같은 사건으로 합쳐진 옛 주소: 검색 제외 + 대표 페이지로 안내 (주소는 유지)
            m = db[v['dup']]
            page(f'/hot/{v["slug"]}/', f'{m["title"][:40]} (합쳐진 이슈)', '같은 사건을 다룬 핫이슈 페이지로 합쳐졌어요.',
                 f'<p class="bc"><a href="/">홈</a> › <a href="/hot/">핫이슈</a></p><h1>이 이슈는 한 페이지로 합쳤어요</h1><p>같은 사건을 다룬 기사가 제목만 달라 따로 정리돼 있었어요. 아래 페이지에서 언론사 보도를 함께 볼 수 있어요.</p>'
                 f'<p><a class="lab-cta" href="/hot/{m["slug"]}/"><b>🔥 {E(m["title"])}</b><span>합쳐진 페이지로 가기 →</span></a></p><script>location.replace("/hot/{m["slug"]}/")</script>',
                 [('루리의 줍줍', '/'), ('핫이슈', '/hot/')], noindex=True)
            urls.append(f'/hot/{v["slug"]}/')
            continue
        lead, links, faq = H.TOOL[v['type']]
        what = ''.join(f'<li><b>{E(w["o"])}</b> {E(w["t"])}</li>' for w in v['what'])
        nums = ''.join(f'<li><b>{E(n["v"])}</b> <small>— {E(n["o"])} 「{E(n["t"][:40])}」</small></li>' for n in v['nums'])
        dates = ''.join(f'<li><b>{E(x["v"])}</b> <small>— {E(x["o"])} 「{E(x["t"][:40])}」</small></li>' for x in v['dates'])
        arts = ''.join(f'<li><a href="{E(a["u"])}" target="_blank" rel="noopener nofollow"><em>{E(a["o"])} {G.get(a.get("g"), "")} {a["s"] if a.get("s") is not None else ""}</em>{E(a["t"])}</a></li>' for a in v['arts'])
        tl = ''.join(f'<a href="{u}"><em>바로 가기</em><b>{E(n)}</b></a>' for n, u in links)
        pr = ''.join(f'<a href="{E(p_["u"])}"><em>{E(p_["k"])}</em><b>{E(p_["t"])}</b></a>' for p_ in v.get('pr') or [])
        fq = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq)
        ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}
        old = '' if v['slug'] in livesl else f'<p class="an-warn">📦 지난 이슈예요(마지막 확인 {E(v["last"])}). 지금은 상황이 바뀌었을 수 있어요.</p>'
        iss = v.get('issue')
        kwl = f'<a href="/kw/{v["kw"]}/">🔎 키워드 상세 →</a>' if v.get('kw') else ''
        sig = (f'<p class="hm-links"><a href="/news/#is{iss["n"]}">🕵️ 기사 확인 신호: 언론사 {iss["on"]}곳 · 확인 신호 {G.get(iss.get("g"), "")} {iss.get("s") if iss.get("s") is not None else "-"}점 →</a>{kwl}</p>') if iss else (f'<p class="hm-links">{kwl}</p>' if kwl else '')
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/hot/">핫이슈</a> › {E(v["q"][:30])}</p><h1>🔥 {E(v["title"])}</h1>'
                f'<p><span class="kw-b both">{HOT_TYPE[v["type"]]}</span> 언론사 {len(v["outs"])}곳 보도 · 처음 {E(v["first"])} · 갱신 {E(v["last"])}</p>' + old
                + f'<section class="mg-s"><h2>📌 한눈에 정리</h2><p class="hot-n">여러 언론사가 이렇게 전했어요(기사 제목 그대로).</p><ul class="hot-l">{what}</ul>'
                + (f'<h3>🔢 기사에 나온 숫자</h3><ul class="hot-l">{nums}</ul>' if nums else '') + (f'<h3>📅 기사에 나온 날짜</h3><ul class="hot-l">{dates}</ul>' if dates else '') + '</section>'
                + f'<section class="mg-s"><h2>🙋 나한테 뭐가 달라지나</h2><p>{E(lead)}</p><div class="nw-pr">{tl}</div></section>' + sig
                + (f'<section class="mg-s"><h2>📎 관련 줍줍</h2><div class="nw-pr">{pr}</div></section>' if pr else '')
                + f'<section class="mg-s"><h2>📰 관련 기사 (확인 신호 점수)</h2><ul class="kw-l">{arts}</ul></section>'
                + f'<section class="mg-s"><h2>❓ 자주 묻는 질문</h2><div class="hot-faq">{fq}</div></section>'
                + '<p class="note">기사 제목·숫자·날짜는 각 언론사 보도 그대로이고, 루리의 줍줍이 사실을 새로 판정한 게 아니에요. 정책·세금·금융은 공식 기관 안내를 확인하세요.</p>' + css)
        q = re.sub(r'[“”"]', '', v['q'])
        page(f'/hot/{v["slug"]}/', f'{q[:40]} — 무슨 일·나한테 달라지는 점 정리', f'{q[:40]}: 여러 언론사 보도를 모아 무슨 일인지, 기사에 나온 숫자·날짜, 나한테 달라지는 점과 관련 도구를 정리했어요.',
             body, [('루리의 줍줍', '/'), ('핫이슈', '/hot/'), (q[:30], f'/hot/{v["slug"]}/')], ld)
        urls.append(f'/hot/{v["slug"]}/')
    for f in os.listdir(hd):
        if os.path.isdir(os.path.join(hd, f)) and f not in db:
            shutil.rmtree(os.path.join(hd, f), ignore_errors=True)
    card = lambda v: f'<li><a href="/hot/{v["slug"]}/"><em>{HOT_TYPE[v["type"]]}</em><b>{E(v["title"])}</b><span>언론사 {len(v["outs"])}곳 · {E(v["last"][5:])}</span></a></li>'
    past = sorted([v for v in db.values() if v['slug'] not in livesl and not v.get('dup')], key=lambda v: v['last'], reverse=True)[:60]
    page('/hot/', '지금 뜨는 핫이슈 — 무슨 일·나한테 달라지는 점 정리', '검색 급상승·언론 보도가 몰린 정보성 이슈를 골라 무슨 일인지, 나한테 달라지는 점, 관련 계산기·지원금을 정리했어요.',
         '<p class="bc"><a href="/">홈</a> › 핫이슈</p><h1>🔥 지금 뜨는 핫이슈</h1>' + say('o_det_wave', '검색이 몰리고 여러 언론사가 다룬 이슈 중, 나한테 실제로 쓸모 있는 것만 골랐어요.')
         + (f'<ul class="mg-l hot-c">{"".join(card(v) for v in live)}</ul>' if live else '<p class="nw-empty">지금은 정리할 핫이슈가 없어요.</p>')
         + (f'<h2>📦 지난 이슈</h2><ul class="mg-l hot-c">{"".join(card(v) for v in past)}</ul>' if past else '') + css,
         [('루리의 줍줍', '/'), ('핫이슈', '/hot/')])
    return urls


def hot_top(n=4):
    live, _ = hot_live()
    if not live:
        return ''
    li = ''.join(f'<li><a href="/hot/{v["slug"]}/"><em>🔥</em><b>{E(v["title"])}</b><span>{HOT_TYPE[v["type"]]}</span></a></li>' for v in live[:n])
    return f'<section class="nw-home hot-home"><h2>🔥 지금 뜨는 핫이슈 <a href="/hot/">전체 →</a></h2><ol>{li}</ol></section>'


def news_top():
    # 홈 투트랙(2026-10-18 사용자: 공모전과 투트랙) — 이슈 감별 상위 3개
    try:
        d = json.load(open(os.path.join(ROOT, 'news', 'data.json'), encoding='utf-8'))
    except Exception:
        return ''
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    li = ''.join(f'<li><a href="/news/#is{x["n"]}"><em>{i + 1}</em><b>{E(x["t"])}</b><span>{G.get("bad" if x.get("cf") else x.get("g"), "")} {x["s"] if x.get("s") is not None else ""}점 · {x["on"]}곳</span></a></li>' for i, x in enumerate([y for y in d.get('issues', []) if y.get('c') == '정치'][:3] or d.get('issues', [])[:3]))
    return f'<section class="nw-home"><h2>🕵️ 오늘의 정치 이슈 · 기사 확인 신호 <a href="/news/">이슈 순위 전체 →</a></h2><ol>{li}</ol></section>' if li else ''


def news_page():
    # 루리 탐정의 이슈 감별 (2026-10-18 사용자: RSS 기사 수집 → 주제별 묶음 → 팩트체크 기반 채점, 피드, 탐정 루리, 기사 관련 줍줍)
    body = f'''<p class="bc"><a href="/">홈</a> › 기사 확인 신호</p><h1>🕵️ 루리 탐정의 기사 확인 신호</h1>{hot_top(3)}
<section id="news" aria-label="이슈 순위와 기사 채점">{news_static()}</section>
<details class="nw-how"><summary>채점은 이렇게 해요</summary><ul><li><b>교차 보도</b> — 같은 사건을 여러 언론사가 보도하면 가점, 한 곳뿐이면 표시만 해요.</li><li><b>출처</b> — 실명 기관·인물 출처는 가점, 익명 관계자뿐이거나 온라인 커뮤니티·SNS 글이 출처면 감점.</li><li><b>제목-본문 일치</b> — 제목의 숫자·인용문이 본문에 없으면 감점.</li><li><b>숫자 엇갈림</b> — 같은 사건인데 언론사마다 사망·부상자 수가 다르면 따로 표시해요.</li><li><b>낚시·홍보</b> — 「충격」「결국」「이것」 같은 낚시 표현, 기업 홍보성 기사는 감점.</li></ul><p>기사 본문은 채점에만 쓰고 이 사이트에 옮겨 싣지 않아요. 제목을 누르면 원래 언론사 기사로 이동해요.</p></details>
<link rel="stylesheet" href="/assets/news/news.css?v=6"><script defer src="/assets/news/news.js?v=4"></script>'''
    page('/news/', '기사 확인 신호 — 오늘의 이슈 순위와 기사별 확인 항목', '언론사 15곳 기사를 매시간 모아 같은 사건끼리 묶고, 교차 보도·출처·제목-본문 일치·숫자 엇갈림·낚시 표현으로 기사마다 점수를 매겨요. 지금 가장 많이 보도된 이슈 순위.',
         body, [('루리의 줍줍', '/'), ('기사 확인 신호', '/news/')])


def app_page():
    # 루리의 줍줍 앱(PWA) 설치 + 공모전 알림 (2026-10-18 사용자: 앱도 사이트 안에서 배포, 공모전 알림, 웹푸시, 메일)
    cats = json.dumps([[sl, n, CAT_ICON.get(n, '🧩')] for sl, n in CATS], ensure_ascii=False)
    faq = [('앱은 어디서 받아요?', '이 페이지에서 바로 설치돼요. 플레이스토어·앱스토어를 거치지 않는 웹앱이라 용량이 거의 없고, 늘 최신 공모전이 보여요.'),
           ('알림은 얼마나 자주 와요?', '하루 최대 2번이에요. 저녁 7시쯤 관심 분야 새 공모전을 한 번에 모아서, 아침 9시쯤 인기 공모전 마감 3일 전 소식을 보내요. 새 공모전이 없는 날은 안 와요.'),
           ('가입해야 해요?', '폰 알림은 가입 없이 바로 켤 수 있어요. 찜한 공모전 마감 메일은 회원만 받을 수 있어요.'),
           ('아이폰도 돼요?', 'iOS 16.4 이상 사파리에서 홈 화면에 추가한 뒤, 홈 화면의 루리의 줍줍 앱을 열어 알림을 켜면 돼요.'),
           ('알림을 끄고 싶어요.', '이 페이지에서 「알림 끄기」를 누르거나, 폰 설정 → 알림에서 루리의 줍줍(또는 sungprofile.cloud)을 끄면 돼요.')]
    body = f'''<p class="bc"><a href="/">홈</a> › 앱·알림</p><h1>📲 루리의 줍줍 앱 · 공모전 알림</h1>
{say("o_present", "홈 화면에 앱을 깔고 관심 분야만 골라 두면, 새 공모전이랑 마감 임박을 제가 폰으로 알려 드릴게요!")}
<section id="app-page" data-cats='{E(cats)}'>
<div class="ap-hero"><img src="/assets/icons/icon-192.png" alt="루리의 줍줍 앱 아이콘" width="72" height="72"><div><b>루리의 줍줍</b><span>공모전·청약·지원금·경품 이벤트 · 무료 · 광고 클릭 강요 없음</span></div></div>
<h2>1. 앱 설치</h2><div class="ap-card ap-inst"><p class="ap-sm">불러오는 중…</p></div>
<h2>2. 공모전 폰 알림 (웹푸시)</h2><div class="ap-card ap-push"><p class="ap-sm">불러오는 중…</p></div>
<h2>3. 메일 알림</h2><div class="ap-card ap-mail"><p class="ap-sm">불러오는 중…</p></div>
<h2>자주 묻는 질문</h2><div class="ap-card ap-faq">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in faq)}</div>
</section><p class="note">알림을 켜면 브라우저가 만든 알림 주소와 고른 분야만 저장해요. 이름·전화번호는 받지 않아요. 알림을 끄면 바로 지워져요.</p>
<link rel="stylesheet" href="/assets/app/app.css?v=1">'''
    page('/app/', '루리의 줍줍 앱 설치 · 공모전 알림 받기', '루리의 줍줍 앱을 홈 화면에 설치하고, 관심 분야 새 공모전과 마감 임박 소식을 폰 알림(웹푸시)·메일로 받아 보세요. 무료, 가입 없이 폰 알림 가능.',
         body, [('루리의 줍줍', '/'), ('앱·알림', '/app/')])


FR_SUB = {'돼지고기': '소고기나 닭고기', '소고기': '돼지고기', '닭고기': '돼지고기', '스팸': '햄이나 소시지', '햄': '스팸이나 소시지', '소시지': '햄이나 스팸', '국수': '라면 사리',
          '파스타면': '국수', '애호박': '가지나 양배추', '양배추': '배추', '두부': '달걀', '참치캔': '스팸', '대파': '양파', '고추장': '고춧가루 조금 더', '김치': '볶은 양배추(맛은 달라져요)',
          '오징어': '새우', '새우': '오징어', '당면': '국수', '떡': '어묵', '어묵': '맛살', '버섯': '애호박', '시금치': '부추나 깻잎', '감자': '고구마', '우유': '물(조금 묽어져요)'}


def fr_tips(r, RS):
    """레시피마다 다른 팁(이름·재료·태그로 계산): 맵기 조절·대체 재료·보관·남은 재료 활용. 2026-10-19 상세 본문 보강."""
    n, L = r['n'], []
    if '매움' in r['t']:
        L.append(f'{n}은(는) 매콤한 메뉴라 아이와 먹을 때는 고춧가루·고추장을 절반으로 줄이고 설탕을 조금 더 넣으면 순해져요.')
    elif '아이' in r['t'] or '안 매움' in r['t']:
        L.append(f'{n}은(는) 맵지 않아 아이 반찬이나 도시락 메뉴로도 좋아요.')
    sub = [(i, FR_SUB[i]) for i in r['need'] if i in FR_SUB][:2]
    for i, x in sub:
        L.append(f'{n}에 넣을 {i}이(가) 없으면 {x}(으)로 바꿔도 만들 수 있어요.')
    if re.search(r'국|찌개|탕|전골', n):
        L.append(f'남은 {n}은(는) 한 김 식혀 냉장 보관하고 이틀 안에 다시 끓여 드세요.')
    elif re.search(r'조림|볶음|무침|나물|장조림', n):
        L.append(f'{n}은(는) 밀폐 용기에 담아 냉장 보관하면 2~3일 반찬으로 먹을 수 있어요.')
    left = [i for i in r['opt'] if i not in r['need']][:3]
    other = {i: next((x for x in RS if x is not r and i in x['need']), None) for i in left}
    for i, x in other.items():
        if x:
            L.append(f'{n} 만들고 {i}이(가) 남으면 「{x["n"]}」에 쓰면 좋아요.')
            break
    L.append(f'모두 {len(r["s"])}단계라 처음 해 봐도 {r["m"]}분 안팎이면 완성돼요.' if r['lv'] == '쉬움' else f'{len(r["s"])}단계로 조금 손이 가지만, 순서대로 하면 {r["m"]}분 정도 걸려요.')
    return L


def fr_slug(n):
    return re.sub(r'[^0-9A-Za-z가-힣]+', '-', n).strip('-')



def page_rates(min_n=3):
    """회원이 실제로 준 별점만 읽어 온다(구조화 데이터 aggregateRating 용). 실패하면 빈 값."""
    if not COMM_API:
        return {}
    try:
        with urllib.request.urlopen(COMM_API + f'/api/p/rates?min={min_n}', timeout=20) as f:
            return {x['page']: x for x in json.load(f).get('rates') or []}
    except Exception as e:
        print('별점 읽기 실패', repr(e)[:80])
        return {}


def fridge_page():
    """냉장고 파먹기 + 레시피 상세(/fridge/r/<요리>/, 2026-10-19 검색 유입: Recipe 구조화 데이터). 사진은 자유 이용 사진과 출처를 밝힌 참고 사진(recipes_ph.json)."""
    D = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'recipes.json'), encoding='utf-8'))
    PH = _rd('assets/fridge/recipes_ph.json') or {}
    PR, PI = PH.get('recipes') or {}, PH.get('ing') or {}
    RS = D['recipes']; NR = len(RS)
    RATE = page_rates()
    FR_EN = _rd('assets/fridge/en.json') or {}   # 영문 보조 표기(본문 한 줄)
    shutil.rmtree(os.path.join(ROOT, 'fridge', 'r'), ignore_errors=True)
    lic = lambda c: (E(c.get('by') or '작가 미상')
                     + (f' · {E((c.get("lic") or "").upper().replace("PDM", "퍼블릭 도메인"))} {E(c.get("lv") or "")}'.rstrip() if c.get('lic') else '')
                     + (f' · <a href="{E(c["src"])}" target="_blank" rel="noopener nofollow">원본</a>' if c.get('src') else ''))
    urls = []
    for r in RS:
        sl = fr_slug(r['n']); u = f'/fridge/r/{sl}/'
        ph = PR.get(r['n']) or {}
        mp = ph.get('main')
        st = {x['k']: (mp if x.get('main') else x) for x in ph.get('steps') or []}
        cr = ([f'완성 사진: {lic(mp)}'] if mp and (mp.get('by') or mp.get('src')) else [])
        steps = ''
        for k, t in enumerate(r['s'], 1):
            im = st.get(k)
            if im and im is not mp and (im.get('by') or im.get('src')):
                cr.append(f'{k}단계 사진: {lic(im)}')
            steps += f'<li id="step{k}"><p>{E(t)}</p>' + (f'<img src="{E(im["f"])}" width="720" height="540" loading="lazy" decoding="async" alt="{E(r["n"])} {k}단계">' if im and im.get('f') else '') + '</li>'
        ingl = lambda L: ''.join(f'<li>{(f"<img src={chr(34)}{E(PI[i][chr(102)])}{chr(34)} width=28 height=28 alt=>" if i in PI else "")}{E(i)}</li>' for i in L)
        rel = sorted([x for x in RS if x is not r and set(x['need']) & set(r['need'])], key=lambda x: -len(set(x['need'] + x['opt']) & set(r['need'] + r['opt'])))[:6]
        tags = ' '.join(f'#{t}' for t in r['t'])
        tip = (f'필수 재료는 {", ".join(r["need"])} {len(r["need"])}가지이고, ' + (f'{", ".join(r["opt"][:4])} 같은 재료가 있으면 더 맛있어요. ' if r['opt'] else '')
               + f'조리 시간은 약 {r["m"]}분, 난이도는 「{r["lv"]}」이에요. 기본양념({D["basic"]})은 집에 있다고 보고 적었어요.')
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a> › {E(r["n"])}</p>'
                f'<article class="fr-rp"><h1>{r["e"]} {E(r["n"])} {"끓이는 법" if re.search(r"국|찌개|탕|전골|국밥", r["n"]) else "만드는 법"}</h1><p class="fr-meta">⏱ {r["m"]}분 · {E(r["lv"])} · {E(tags)}</p>'
                + (f'<p class="fr-rate">{"★" * round(RATE[u]["avg"])}{"☆" * (5 - round(RATE[u]["avg"]))} {RATE[u]["avg"]} · 회원 {RATE[u]["n"]}명이 준 별점</p>' if RATE.get(u) else '')
                + (f'<img class="fr-rmain" src="{E(mp["f"])}" width="720" height="540" alt="{E(r["n"])} 완성 사진" fetchpriority="high">' if mp else '')
                + f'<p>{E(tip)}</p><h2>🧺 재료</h2><div class="fr-ri"><div><h3>꼭 있어야 해요</h3><ul>{ingl(r["need"])}</ul></div>'
                + (f'<div><h3>있으면 더 좋아요</h3><ul>{ingl(r["opt"])}</ul></div>' if r['opt'] else '') + '</div>'
                + (f'<h2>👩‍🍳 {E(r["n"])} 맛있게 끓이는 방법</h2>' if re.search(r'국|찌개|탕|전골|국밥', r['n']) else f'<h2>👩‍🍳 {E(r["n"])} 맛있게 만드는 방법</h2>') + f'<ol class="fr-rs">{steps}</ol>'
                + (f'<p class="note">영문: {E(FR_EN[r["n"]])} recipe</p>' if FR_EN.get(r['n']) else '')
                + share_bar(f'{r["n"]} 만드는 법', f'{r["n"]} 만드는 법 — 재료 {len(r["need"])}가지로 {r["m"]}분')
                + '<h2>💡 루리 팁</h2><ul class="chk">' + ''.join(f'<li>{E(t)}</li>' for t in fr_tips(r, RS)) + '</ul>'
                + f'<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 다른 메뉴 찾기</b><span>재료를 고르면 지금 만들 수 있는 메뉴를 골라 드려요 · 레시피 {NR}개 →</span></a>'
                + (f'<h2>🔗 재료가 비슷한 메뉴</h2><ul class="fr-rel">' + ''.join(f'<li><a href="/fridge/r/{fr_slug(x["n"])}/">{x["e"]} {E(x["n"])} <small>{x["m"]}분</small></a></li>' for x in rel) + '</ul>' if rel else '')
                + (f'<details class="fr-cr"><summary>사진 출처</summary><p>{"<br>".join(cr)}</p></details>' if cr else '')
                + '<p class="note">루리의 줍줍이 직접 정리한 1~2인분 기준 레시피예요. 사진은 자유 이용 사진이거나 출처를 밝힌 참고 사진이고, 맞는 사진이 없는 메뉴는 비워 뒀어요. 알레르기가 있으면 재료를 꼭 확인하세요.</p></article>'
                + '<link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">')
        def how_step(k, t):
            nm = re.split(r'[,.]', t)[0].strip()[:45] or f'{k}단계'
            d_ = {'@type': 'HowToStep', 'name': nm, 'text': t, 'url': f'{SITE}{u}#step{k}'}
            im_ = st.get(k)
            if im_ and im_.get('f'):
                d_['image'] = SITE + im_['f']
            return d_
        ld = {'@context': 'https://schema.org', '@type': 'Recipe', 'name': r['n'], 'description': tip, 'datePublished': '2026-10-19', 'totalTime': f'PT{r["m"]}M', 'recipeYield': '1~2인분', 'recipeCategory': '집밥',
              'recipeCuisine': '한식', 'keywords': ', '.join([r['n'] + ' 만드는 법', '냉장고 파먹기'] + r['t']), 'author': {'@type': 'Organization', 'name': NAME},
              'recipeIngredient': r['need'] + r['opt'], 'recipeInstructions': [how_step(k, t) for k, t in enumerate(r['s'], 1)]}
        if mp:
            ld['image'] = [SITE + mp['f']]
        rt = RATE.get(u)
        if rt:
            ld['aggregateRating'] = {'@type': 'AggregateRating', 'ratingValue': rt['avg'], 'ratingCount': rt['n'], 'bestRating': 5, 'worstRating': 1}
        how = '끓이는 법 · 레시피' if re.search(r'국|찌개|탕|전골|국밥', r['n']) else '만드는 법 · 양념장' if re.search(r'조림|무침', r['n']) else '만드는 법 · 레시피'   # 2026-10-19 검색 시나리오
        page(u, f'{r["n"]} {how} — 재료 {len(r["need"])}가지로 {r["m"]}분 집밥', f'{r["n"]} 만드는 법: {", ".join(r["need"] + r["opt"][:3])}로 {r["m"]}분. 재료와 단계별 만드는 법, 재료가 비슷한 메뉴까지.',
             body, [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), (r['n'], u)], ld)
        urls.append(u)
    allr = ''.join(f'<li><a href="/fridge/r/{fr_slug(r["n"])}/">{r["e"]} {E(r["n"])}</a></li>' for r in sorted(RS, key=lambda r: r['n']))
    import fridge_today as FT
    li = lambda L: '<ul class="fr-rel">' + ''.join(f'<li><a href="/fridge/r/{fr_slug(x["n"])}/">{x["e"]} {E(x["n"])} <small>{x["m"]}분 · {E(x["lv"])}</small></a></li>' for x in L) + '</ul>'
    TD = _rd('assets/fridge/today.json') or {}
    W = [('rainy', '☔ 비 오는 날', '비 오는 날엔 국물이나 전이 당겨요. 부침개는 기름 소리가 빗소리 같아서라는 말도 있죠.', ('국물', '전')),
         ('cold', '🧣 쌀쌀한 날', '기온이 뚝 떨어진 날엔 뜨끈한 국물과 조림이 좋아요.', ('국물', '조림')),
         ('hot', '☀️ 더운 날', '더운 날엔 불 앞에 오래 서지 않는 면·비빔·무침이 좋아요.', ('면', '반찬')),
         ('gap', '🌗 일교차 큰 날', '아침저녁으로 쌀쌀한 날엔 저녁에 따뜻한 국 한 그릇.', ('국물', '밥'))]
    secs = ''.join(f'<section class="mg-s" id="{k}"><h2>{t}</h2><p>{E(d_)}</p>' + li([x for x in RS if FT.cat(x['n']) in cs][:10]) + '</section>' for k, t, d_, cs in W)
    page('/fridge/weather/', '비 오는 날 음식 추천 — 날씨별 오늘 메뉴(쌀쌀한 날·더운 날)', '비 오는 날·쌀쌀한 날·더운 날·일교차 큰 날에 어울리는 집밥 메뉴를 날씨별로 모았어요. 매시간 서울 날씨로 오늘의 메뉴 3개도 골라 드려요.',
         f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a> › 날씨별 메뉴</p><h1>🌤️ 날씨별 오늘 메뉴 — 비 오는 날·쌀쌀한 날·더운 날</h1>'
         + (f'<p class="cat-st">📌 오늘 {E(TD.get("place", "서울"))} {round(TD.get("t", 0))}도 · {E(TD.get("why", ""))} → ' + ', '.join(f'<a href="/fridge/r/{fr_slug(n)}/">{E(n)}</a>' for n in TD.get('picks', [])) + f' <small>({E(TD.get("at", ""))} 기준, Open-Meteo)</small></p>' if TD.get('picks') else '')
         + secs + '<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 찾기</b><span>있는 재료를 고르면 지금 만들 수 있는 메뉴부터 →</span></a><link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">',
         [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), ('날씨별 메뉴', '/fridge/weather/')])
    SOLO = sorted([x for x in RS if len(x['need']) <= 3 and x['m'] <= 20], key=lambda x: (x['m'], len(x['need'])))
    page('/fridge/solo/', f'자취 요리 추천 — 재료 3개 이하·20분 안에 ({len(SOLO)}가지)', f'자취 요리 추천: 꼭 필요한 재료 3개 이하, 20분 안에 끝나는 1인분 집밥 {len(SOLO)}가지. 설거지 적은 메뉴와 남은 재료 활용까지.',
         f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a> › 자취 요리</p><h1>🏠 자취 요리 추천 — 재료 3개 이하·20분 ({len(SOLO)}가지)</h1>'
         '<p>자취방 냉장고에 흔한 달걀·김치·스팸·라면으로 만들 수 있는 메뉴부터 골랐어요. 모두 꼭 필요한 재료가 3개 이하이고, 20분 안에 끝나요. 기본양념(간장·설탕·식용유 등)은 있다고 봤어요.</p>'
         + li(SOLO) + '<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 찾기</b><span>「설거지 적게」 조건도 고를 수 있어요 →</span></a><link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">',
         [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), ('자취 요리', '/fridge/solo/')])
    urls += ['/fridge/weather/', '/fridge/solo/']
    page('/fridge/', f'냉장고 파먹기 메뉴 추천 — 있는 재료로 오늘 요리 (레시피 {NR}개)', f'냉장고에 있는 재료만 고르면 집밥 레시피 {NR}개 중 지금 바로 만들 수 있는 오늘 메뉴와 만드는 법, 하나만 사면 되는 메뉴까지 알려 줘요.',
         f"""<p class="bc"><a href="/">홈</a> › 냉장고 파먹기</p><h1>🍳 루리의 냉장고 파먹기</h1>
{say("o_cook", f"냉장고 사진을 찍거나 있는 재료를 눌러 주세요. 집밥 레시피 {NR}개 중에 지금 바로 만들 수 있는 걸 골라 드릴게요!")}
<section id="fridge" aria-label="냉장고 재료로 메뉴 추천"><noscript>자바스크립트가 필요해요. 아래 전체 레시피 목록에서 골라 보세요.</noscript></section>
<section class="mg-s" data-pctop="/fridge/r/" data-by="likes" data-n="8" data-head="❤️ 지금 인기 있는 메뉴"></section>
<section class="mg-s" data-pctop="/fridge/r/" data-by="views" data-n="8" data-head="👀 많이 본 레시피"></section>
<p class="hm-more"><a href="/fridge/weather/">🌤️ 날씨별 메뉴</a> · <a href="/fridge/solo/">🏠 자취 요리</a> · <a href="/fridge/r/계란찜/">🥚 계란찜</a></p>
<details class="fr-all"><summary>📚 전체 레시피 {NR}개 보기</summary><ul>{allr}</ul></details>
<a class="lab-cta" href="/cat/food/"><b>🏆 요리·레시피 공모전</b><span>레시피 공모전·요리경연대회 모아 보기 · 상금 받고 요리 실력 뽐내기 →</span></a><p class="note">사진은 재료를 찾는 데만 쓰고 저장하지 않아요. 고른 재료는 이 폰에만 저장돼요. 알레르기가 있으면 재료를 꼭 다시 확인해 주세요.</p>
<link rel="stylesheet" href="/assets/fridge/fridge.css?v=12"><script defer src="/assets/fridge/fridge.js?v=14"></script>""", [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/')],
         {'@context': 'https://schema.org', '@type': 'ItemList', 'name': '냉장고 파먹기 집밥 레시피', 'numberOfItems': NR, 'itemListElement': [{'@type': 'ListItem', 'position': k + 1, 'url': f'{SITE}/fridge/r/{fr_slug(r["n"])}/', 'name': r['n']} for k, r in enumerate(RS[:50])]})
    return urls


def qa_card(q):
    return f'<li><a class="card" data-c="guide" href="/guide/{q["slug"]}/"><span class="ic">{q["icon"]}</span><div class="cb"><h3 class="t">{E(q["title"])}</h3><p class="o">{(E(q["tag"]) + " · ") if q["tag"] else ""}{E(q["desc"])}</p></div></a></li>'


def qa_home():
    if not QA: return ''
    return f'<section class="qa-home"><h2>💬 루리의 고민 해결 <a href="/qa/">전체 {len(QA)}편 →</a></h2><ul class="list">{"".join(qa_card(q) for q in QA[:4])}</ul></section>'


def qa_pages(live):
    page('/qa/', '루리의 고민 해결', '청년 지원금, 진로, 공모전 준비까지 실제로 받은 고민에 루리가 답을 정리했어요.',
         f'<p class="bc"><a href="/">홈</a> › 고민 해결</p><section class="dh" data-c="guide"><span class="ic big">💬</span><h1>루리의 고민 해결</h1></section>{say("o_cardigan", "실제로 받은 고민에 하나씩 답을 정리했어요. 비슷한 고민이면 골라 읽어 보세요!")}<ul class="list">{"".join(qa_card(q) for q in QA)}</ul>',
         [('루리의 줍줍', '/'), ('고민 해결', '/qa/')])
    rel = ''.join(card(c) for c in live[:4])
    for i, q in enumerate(QA):
        page(f'/guide/{q["slug"]}/', q['title'], q['desc'], f'<p class="bc"><a href="/">홈</a> › <a href="/qa/">고민 해결</a></p><article><h1>{E(q["title"])}</h1>{say(["o_suit", "o_cardigan", "o_desk", "o_present"][i % 4], E(q["desc"]))}{q["body"]}{share_bar(q["title"])}</article><p class="qa-more"><a href="/qa/">💬 다른 고민 보기</a> · <a href="/">🎯 루리에게 추천 상담 받기</a></p><h2>마감 임박 공모전</h2><ul class="list">{rel}</ul>',
             [('루리의 줍줍', '/'), ('고민 해결', '/qa/'), (q['title'], f'/guide/{q["slug"]}/')],
             {'@context': 'https://schema.org', '@type': 'Article', 'headline': q['title'], 'description': q['desc'], 'datePublished': '2026-10-17',
              'author': {'@type': 'Person', 'name': 'Seongsang Park'}})


GUIDE_FAQ = {'unemployment-2026': [
    ('실업급여 신청자격은 어떻게 되나요?', '이직 전 18개월 동안 고용보험 가입(피보험 단위기간)이 180일 이상이고, 권고사직·계약만료처럼 비자발적으로 퇴사했으며, 재취업 의사와 능력이 있어야 해요. 자진 퇴사도 임금 체불 같은 정당한 사유가 있으면 인정될 수 있어요.'),
    ('실업급여는 하루에 얼마 받나요?', '퇴직 전 평균임금의 60%이고, 2026년 1월 1일 이후 이직하면 하루 상한 68,100원, 하한은 최저임금의 80%(8시간 기준 66,048원)예요.'),
    ('실업급여는 며칠 동안 받나요?', '가입 기간과 나이에 따라 120일에서 270일이에요. 50세 미만은 120~240일, 50세 이상·장애인은 120~270일이에요.'),
    ('실업급여 신청방법은요?', '고용24에서 구직 등록과 수급자격 신청자 교육을 마친 뒤 거주지 관할 고용센터에 수급자격 인정을 신청해요. 이직 다음 날부터 12개월 안에 신청해야 해요.')]}


def guides(live):
    li = ''.join(f'<li><a class="card" data-c="guide" href="/guide/{s}/"><span class="ic">📖</span><div class="cb"><h3 class="t">{E(t)}</h3><p class="o">{E(d)}</p></div></a></li>' for s, t, d, _ in GUIDES)
    page('/guide/', '공모전 응모 가이드', '공모전 처음 응모하는 법, 제안서 쓰는 법, 수기·문학 공모 요령, 상금 수령과 사칭 주의까지.',
         f'<p class="bc"><a href="/">홈</a> › 응모 가이드</p><section class="dh" data-c="guide"><span class="ic big">📖</span><h1>공모전 응모 가이드</h1></section>{say("o_vest", "처음 응모한다면 1번부터 차근차근 읽어 보세요. 실수로 탈락하는 일이 확 줄어요!")}<ul class="list">{li}</ul>', [('루리의 줍줍', '/'), ('응모 가이드', '/guide/')])
    rel = ''.join(card(c) for c in live[:4])
    for s, t, d, b in GUIDES:
        fq = GUIDE_FAQ.get(s, [])   # 화면에 실제로 보이는 문답만 FAQPage 로 (2026-10-19)
        fqh = ('<section class="hub-faq"><h2>❓ 자주 묻는 질문</h2>' + ''.join(f'<details class="faq"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in fq) + '</section>') if fq else ''
        art = {'@type': 'Article', 'headline': t, 'description': d, 'datePublished': '2026-10-16', 'author': {'@type': 'Person', 'name': 'Seongsang Park'}}
        ld_ = {'@context': 'https://schema.org', '@graph': [art, {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in fq]}]} if fq else {'@context': 'https://schema.org', **art}
        page(f'/guide/{s}/', t, d, f'<p class="bc"><a href="/">홈</a> › <a href="/guide/">응모 가이드</a></p><article><h1>{E(t)}</h1>{say(["o_suit", "o_cardigan", "o_desk", "o_present"][GUIDES.index((s, t, d, b)) % 4], E(d))}{b}{fqh}{share_bar(t)}</article><h2>마감 임박 공모전</h2><ul class="list">{rel}</ul>',
             [('루리의 줍줍', '/'), ('응모 가이드', '/guide/'), (t, f'/guide/{s}/')], ld_)


PRIV_MEMBER = ('<p>루리의 줍줍(sungprofile.cloud)은 커뮤니티(후기·질문 게시판)를 쓰려는 회원에게서 <b>이메일 주소 한 가지</b>만 받습니다. 이름·전화번호·주소 등 다른 정보는 받지 않습니다.</p>'
               '<h2>회원 정보</h2><ul class="chk"><li>수집 항목: 이메일 주소(필수). 비밀번호는 복원할 수 없는 암호화 값(PBKDF2)으로만 저장합니다.</li>'
               '<li>이용 목적: 로그인, 게시글·댓글 작성자 구분, 부정 이용 방지</li><li>표시: 글쓴이 이름은 이메일 앞부분을 가린 값(예: sun***)으로만 보입니다.</li>'
               '<li>보관: 회원 탈퇴 시 즉시 삭제하며, 작성한 글·댓글은 비공개 처리합니다. 탈퇴·삭제 요청은 문의 메일로도 받습니다.</li>'
               '<li>처리 위탁: 회원·게시판 데이터는 Cloudflare(Workers, D1)에 저장됩니다.</li></ul>'
               '<p>회원이 아닌 방문자의 이름·연락처 같은 개인정보는 받지 않습니다. 아래 광고·통계·알림 항목을 확인하세요.</p>') if COMM_API else               '<p>루리의 줍줍(sungprofile.cloud)은 회원가입 기능이 없으며 이용자의 이름·연락처 같은 개인정보를 받지 않습니다. 아래 광고·통계·알림 항목을 확인하세요.</p>'


def community(live=()):
    if not COMM_API:
        shutil.rmtree(os.path.join(ROOT, 'community'), ignore_errors=True)
        return
    # 팀 만들 때 고르는 공모전 목록 (진행 중만)
    with open(os.path.join(ROOT, 'assets', 'community', 'contests.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{'id': c['id'], 't': c['title'], 'e': c['end'], 'p': c.get('prize', ''), 'pv': c.get('pv', 0), 'g': (c.get('tags') or [''])[0], 'i': CAT_ICON.get((c.get('tags') or ['기타'])[0], '💗'), 'th': c.get('th', 0)} for c in live], f, ensure_ascii=False, separators=(',', ':'))
    page('/community/', '공모전 원정대 · 커뮤니티', '공모전에 같이 나갈 사람을 찾는 루리의 줍줍 원정대. 원정대를 꾸리고 대원을 모아요.',
         f'''<p class="bc"><a href="/">홈</a> › 커뮤니티</p><h1 class="vn-h1">🚩 공모전 원정대</h1>
<section id="vn" aria-label="루리와 공모전 원정대 찾기"></section>
<button class="btn2 cm-join-cta" hidden>무료 가입 · 로그인 (이메일만 있으면 돼요)</button>
<div class="cm-tabs"><button data-k="team">🚩 전체 원정대</button><button data-k="crew">🙋 동료 찾기</button><button data-k="board">💬 후기·질문</button></div>
<section id="cm-teams" data-all data-tab="team"></section>
<section id="cm-crew" data-all data-tab="crew" hidden></section><section id="cm-board" data-all data-tab="board" hidden></section>
<script defer src="/assets/community/vn.js?v=7"></script>''', [('루리의 줍줍', '/'), ('커뮤니티', '/community/')])


def me_pages():
    """내 공간(가입 혜택 모음) · 관리자 (2026-10-17)"""
    page('/me/', '내 공간 — 찜·응모 기록·마감 알림', '찜한 공모전·청약, 응모 기록, 마감 알림 메일, 자격 프로필, 청약 가점 계산기를 한곳에서.',
         '''<section id="me" aria-label="내 공간"></section>''' + (('<section class="me-sec"><h2>💬 톡방</h2><p class="note">공모전·지원금 마감 소식을 매일 나눠요.</p><p class="ft-c">' + comm_btns() + '</p></section>') if COMM_LINKS else '') + '''<link rel="stylesheet" href="/assets/me/me.css?v=2"><script defer src="/assets/me/me.js?v=3"></script>''', [('루리의 줍줍', '/'), ('내 공간', '/me/')])
    page('/login/', '로그인', '루리의 줍줍 로그인 — 내 공간으로 이동해요.', '<p>내 공간으로 이동하고 있어요… <a href="/me/">이동하지 않으면 여기를 눌러 주세요</a></p><script>location.replace("/me/"+location.search+location.hash)</script>', noindex=True)   # 2026-10-19 /login/ 404 → 내 공간(로그인 화면 포함)
    page('/admin/', '관리자', '관리자', '''<section id="admin"></section><section id="gsc-admin"></section><link rel="stylesheet" href="/assets/me/me.css?v=3"><script defer src="/assets/me/admin.js?v=6"></script>''', noindex=True)


def lab():
    """루리의 수상 연구소 — 실제 수상작 + 작품 해설 (2026-10-17 사용자: 공모전 실제 작품과 분석 형식, 장르별)"""
    import lab_pages
    r = lab_pages.build(ROOT, page, say)
    if not r:
        return []
    cards, urls, D = r
    page('/lab/', '루리의 수상 연구소 — 공모전 수상작 해설', f'슬로건·표어·네이밍 공모전 실제 수상작 {D["count"]}개를 한 편씩 구조·기법으로 해설했어요. 내 문구 진단도 해 드려요.',
         lab_pages.index_html(cards, D), [('루리의 줍줍', '/'), ('수상 연구소', '/lab/')])
    return ['/lab/'] + urls


def statics(nl, ne):
    page('/about/', '소개', '루리의 줍줍은 개인 개발자가 AI와 함께 운영하는 생활 정보 사이트입니다. 이슈 확인 신호 채점, 애널리스트 의견 종합, 공모전·지원금 정리의 운영 목적과 작성 방식.',
         f'''<h1>소개</h1>
<p>루리의 줍줍(sungprofile.cloud)은 개인 개발자 Seongsang Park이 운영하는 생활 정보 사이트입니다. 마스코트 「루리」가 안내를 맡고, 사이트 제작과 데이터 정리에는 AI(Anthropic Claude)를 적극적으로 씁니다. 회사나 언론사가 아닌 개인 운영 사이트이며, 특정 기업·정당·증권사와 제휴하거나 돈을 받고 글을 쓰지 않습니다.</p>
<h2>운영 목적</h2><p>뉴스·증권 리포트·공모전·지원금 공고는 여기저기 흩어져 있고, 같은 내용이 제목만 바꿔 반복되는 경우가 많습니다. 루리의 줍줍은 이런 정보를 <b>그대로 옮기지 않고</b>, 같은 내용끼리 묶어 숫자를 다시 세고 비교해서 「몇 곳이 말했는지, 무엇이 아직 확인되지 않았는지, 나한테 무슨 뜻인지」를 짧게 정리하는 것을 목표로 합니다.</p>
<h2>테마별로 하는 일</h2><ul class="chk">
<li><b>🕵️ 이슈</b>: 언론사 15곳의 RSS 기사를 사건별로 묶고, 보도한 언론사 수·실명 출처·제목 속 숫자와 따옴표가 본문에 있는지 같은 <b>확인 신호</b>로 점수를 매깁니다. 이 점수는 기사의 진실 여부를 판정하는 것이 아니라, 더 확인해 볼 곳을 알려 주는 참고 지표입니다. 사건·사고와 사생활 기사는 일부러 다루지 않습니다.</li>
<li><b>📊 머니</b>: 증권사 리포트 기사에 나온 목표가·투자의견을 「상향·하향·유지」 노드로 나눠 종목별로 다시 셉니다. 투자 권유나 주가 예측이 아니며, 세금·대출 계산기와 투자 정책 표는 금융위원회·기획재정부·국세청 공식 자료를 확인해 만들었습니다.</li>
<li><b>🏆 공모전</b>: 진행 중 공모전 {nl}건의 마감·상금·자격·제출물을 같은 형식으로 정리하고, 같은 분야 공모전과 비교한 분석과 오늘 기준 준비 일정을 붙입니다. 실제 수상작을 구조로 풀어 보는 수상 연구소와 응모 가이드도 직접 씁니다.</li>
<li><b>🍳 생활</b>: 지원금·청약 일정, 청약 가점 계산, 경품 이벤트 {ne}건, 냉장고 재료로 고르는 레시피를 정리합니다.</li></ul>
<h2>콘텐츠 작성 방식</h2><ul class="chk">
<li><b>출처</b>: 공식 기관 공고, 언론사 RSS, 공개 API(업비트 시세 등)만 씁니다. 사이트의 robots.txt가 수집을 막는 곳은 쓰지 않습니다.</li>
<li><b>전재 금지</b>: 기사·공고 본문은 옮기지 않고 제목과 원문 링크만 남깁니다. 요약과 해설은 루리의 줍줍이 계산하고 쓴 것입니다.</li>
<li><b>갱신 주기</b>: 이슈·키워드·애널리스트 종합은 매시간, 공모전·지원금·경품 이벤트는 하루 여러 번 자동으로 갱신합니다. 가이드·고민 해결 글은 사람이 검토해 매일 추가합니다.</li>
<li><b>자동화와 검토</b>: 수집과 숫자 계산은 프로그램이 하고, 판정 기준(점수 규칙, 제외 키워드, 정책 표)은 운영자가 정하고 고칩니다. 자동 정리라 오류가 있을 수 있어 모든 페이지에 원문 링크를 함께 둡니다.</li>
<li><b>AI 활용</b>: 사이트 코드와 루리 그림, 일부 해설 문장은 AI로 만들고 운영자가 검토합니다. 제작 과정은 <a href="/ailog/">AI 제작 로그</a>에 공개합니다.</li></ul>
<h2>광고</h2><p>운영비를 마련하기 위해 Google AdSense 광고를 싣습니다. 광고는 본문과 구분해 표시하며, 광고주가 콘텐츠 내용에 관여하지 않습니다. 자세한 내용은 <a href="/privacy/">개인정보처리방침</a>을 참고하세요.</p>
<h2>문의와 정정</h2><p>틀린 정보, 삭제 요청, 제휴 문의는 <a href="mailto:{MAIL}">{MAIL}</a> 또는 <a href="/contact/">문의</a> 페이지로 보내 주세요. 정보 오류는 확인하는 대로 고칩니다.</p>''', [('루리의 줍줍', '/'), ('소개', '/about/')])
    page('/contact/', '문의', '루리의 줍줍 문의: 공모전·지원금 정보 오류 제보, 새 공모전 등록 요청, 페이지 삭제·수정 요청을 메일로 받아요. 확인 후 바로 고쳐요.',
         f'''<h1>문의</h1><p>정보 오류 제보, 공모전 등록 요청, 삭제 요청은 이메일 <a href="mailto:{MAIL}">{MAIL}</a>, 제휴·광고 문의는 <a href="mailto:{PARTNER}">{PARTNER}</a> 로 보내 주세요. <a href="https://github.com/ilovecodingma/ilovecodingma.github.io/issues" rel="noopener">GitHub Issues</a>에 남기셔도 됩니다. 공모전 등록을 요청할 때는 공식 공고 주소를 함께 적어 주시면 확인 후 반영합니다.</p><p class="note">개인정보(이름·연락처)는 공개 게시판에 올리지 마세요.</p>''', [('루리의 줍줍', '/'), ('문의', '/contact/')])
    page('/privacy/', '개인정보처리방침', '루리의 줍줍 개인정보처리방침 — 수집 항목, Google AdSense 광고 쿠키와 맞춤 광고 해제 방법, 방문 통계, 알림 구독 정보 안내.',
         f'''<h1>개인정보처리방침</h1>{PRIV_MEMBER}
<h2>1. 광고와 쿠키 (Google AdSense)</h2><p>이 사이트는 Google AdSense 광고를 게재합니다. Google을 포함한 제3자 광고 사업자는 쿠키를 사용해 이용자가 이 사이트와 다른 사이트를 방문한 기록을 바탕으로 광고를 표시할 수 있습니다. Google은 광고 쿠키를 사용해 이용자에게 이 사이트 및 인터넷의 다른 사이트 방문 기록에 기반한 광고를 제공합니다.</p>
<ul class="chk"><li><b>맞춤 광고 해제</b>: <a href="https://adssettings.google.com" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 끌 수 있습니다. 제3자 광고 사업자의 쿠키는 <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info</a>에서 해제할 수 있습니다.</li>
<li><b>쿠키 거부</b>: 브라우저 설정(크롬: 설정 → 개인정보 보호 및 보안 → 서드 파티 쿠키)에서 쿠키를 막거나 지울 수 있습니다. 쿠키를 막아도 사이트는 이용할 수 있지만, 광고가 관심사와 관계없이 표시됩니다.</li>
<li>Google이 데이터를 쓰는 방식은 <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">Google 파트너 사이트 데이터 사용 안내</a>와 <a href="https://policies.google.com/technologies/ads" rel="noopener">Google 광고 정책</a>에서 볼 수 있습니다.</li></ul>
<h2>2. 방문 통계</h2><p>서비스 개선을 위해 Google Analytics로 페이지 조회, 유입 경로, 기기 종류를 수집합니다. <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">Google 애널리틱스 차단 부가기능</a>으로 거부할 수 있습니다. 이와 별도로 자체 방문 집계를 위해 브라우저에 무작위 방문자 번호를 저장하고, 방문한 페이지·이전 사이트 주소·국가와 도시(접속 IP로 추정, IP 자체는 저장하지 않음)·모바일 여부를 기록합니다. 이 기록으로 개인을 알아볼 수 없으며 집계 후 통계로만 씁니다.</p>
<h2>3. 알림 구독</h2><ul class="chk"><li><b>웹 푸시</b>: 공모전 알림을 켜면 브라우저가 만든 푸시 주소와 암호 키, 고른 분야만 저장합니다. 알림을 끄면 바로 지웁니다.</li>
<li><b>이메일 알림</b>: 신청한 경우에만 이메일 주소와 고른 분야를 저장하고, 알림 발송 외에는 쓰지 않습니다. 문의 메일로 요청하면 언제든 지웁니다.</li></ul>
<h2>4. 브라우저 저장소</h2><p>찜한 공모전, 챗봇 설정, 언어 선택은 이용자의 브라우저(localStorage)에만 저장되며 서버로 보내지 않습니다. 번역 기능을 쓰면 Google 번역이 언어 쿠키(googtrans)를 저장합니다.</p>
<h2>5. 처리 위탁과 보관</h2><p>사이트는 GitHub Pages로 호스팅되며, 호스팅 제공자가 보안 목적으로 접속 로그(IP 주소 등)를 처리할 수 있습니다. 회원·알림·방문 집계 데이터는 Cloudflare(Workers, D1)에 저장합니다. 방문 집계는 통계 외의 목적으로 쓰지 않습니다.</p>
<h2>6. 외부 링크</h2><p>공모전 공식 공고나 기사 원문 링크를 누르면 해당 사이트로 이동하며, 그 사이트의 개인정보처리방침이 적용됩니다.</p>
<h2>7. 문의</h2><p>개인정보 관련 문의·삭제 요청: <a href="mailto:{MAIL}">{MAIL}</a> (운영자 Seongsang Park). <a href="/contact/">문의</a> 페이지도 이용할 수 있습니다.</p><p class="note">시행일: 2026-10-16 · 개정: 2026-10-18 (광고 쿠키 해제 방법, 방문 집계·알림 구독 항목 추가)</p>''', [('루리의 줍줍', '/'), ('개인정보처리방침', '/privacy/')])
    page('/terms/', '이용약관', '루리의 줍줍 이용약관: 자동 정리 정보의 정확성과 면책, 공식 공고 우선 원칙, 회원 기능·커뮤니티 이용 규칙 안내.',
         '''<h1>이용약관</h1><h2>1. 서비스 내용</h2><p>루리의 줍줍은 공개된 공모전·지원사업·이벤트 공고를 정리해 소개하는 무료 정보 서비스입니다. 공모전의 주최·심사·시상에는 관여하지 않습니다.</p>
<h2>2. 정보의 정확성</h2><p>마감일·상금·응모 자격 등은 공고 원문에서 자동으로 정리한 값으로 오류가 있을 수 있습니다. 응모 전 반드시 주최 측 공식 공고를 확인해야 하며, 사이트 정보만 믿고 응모해 생긴 불이익에 대해 운영자는 책임지지 않습니다.</p>
<h2>3. 저작권</h2><p>각 공모전 공고의 저작권은 주최 기관에 있습니다. 루리의 줍줍은 요약 정보와 공식 공고 링크만 제공합니다. 게재를 원하지 않는 주최 측은 <a href="/contact/">문의</a>로 요청하시면 삭제합니다.</p>
<h2>4. 광고</h2><p>사이트 운영을 위해 Google AdSense 광고를 게재합니다.</p><p class="note">시행일: 2026-10-16</p>''', [('루리의 줍줍', '/'), ('이용약관', '/terms/')])


NEW_URLS = []
INDEXNOW_KEY = '5d0b54e7778c4d46a6de43d65f168163'


def indexnow(urls):
    """새로 생긴 주소만 Bing·네이버·Yandex 에 알림 (키 파일은 사이트 루트)"""
    import urllib.request
    ok_ = False
    body = json.dumps({'host': 'sungprofile.cloud', 'key': INDEXNOW_KEY, 'keyLocation': f'{SITE}/{INDEXNOW_KEY}.txt', 'urlList': urls}).encode()
    for ep in ('https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow'):
        try:
            r = urllib.request.urlopen(urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'}), timeout=30)
            print('indexnow', ep, r.status, len(urls))
            ok_ = True
        except Exception as e:
            print('indexnow', ep, 'fail', e)
    if ok_:   # 보낸 주소 기록(사이트맵 기준 첫 실행 이후로는 이 파일로 새 주소 판정)
        SENT = os.path.join(HERE, 'indexnow_sent.json')
        old = set(json.load(open(SENT, encoding='utf-8'))) if os.path.exists(SENT) else set()
        json.dump(sorted(old | set(urls)), open(SENT, 'w', encoding='utf-8'), ensure_ascii=False)


def daily_jobs():
    """하루 슬롯 작업 (2026-10-19 SEO·홍보 지침 Phase 6): 오전 07시~ 마감 임박 공모전 홍보 후보·월요일 주간 요약, 오후 13시~ 지원금 후보, 서치 콘솔 리포트·사이트맵 재제출.
    실패해도 빌드는 계속. 상태는 _gongmo/promo_state.json"""
    SF = os.path.join(HERE, 'promo_state.json')
    st = json.load(open(SF, encoding='utf-8')) if os.path.exists(SF) else {}
    h, d = NOW_KST().hour, TODAY.isoformat()
    # 2026-10-19 사용자 「관리자에서 홍보 관리는 없애, 필요없는 기능」: 홍보 후보 생성(promo.run)·동기화(promo.sync) 중단. promo.py 는 남겨 둠
    if TODAY.weekday() == 0 and st.get('tune') != d:   # 매주 월요일: 추천 가중치 조정(클릭된 추천의 점수 구성이 평균보다 높은 항목은 가중치 +10%, 낮으면 -10%)
        try:
            import push
            rows = push.q("SELECT ev, item, det FROM rec_log WHERE day >= ?", [(TODAY - datetime.timedelta(days=7)).isoformat()])
            imp = [json.loads(r['det']) for r in rows if r['ev'] == 'imp' and r['det']]
            clk = {r['item'] for r in rows if r['ev'] == 'click'}
            WF = os.path.join(ROOT, 'assets', 'rec_w.json'); w = json.load(open(WF, encoding='utf-8'))
            if len(imp) >= 200 and clk:
                ci = [json.loads(r['det']) for r in rows if r['ev'] == 'imp' and r['det'] and r['item'] in clk]
                for k in ('fit', 'val', 'feas', 'pers', 'int'):
                    a_ = sum(x.get(k, 0) for x in imp) / len(imp); c_ = sum(x.get(k, 0) for x in ci) / max(1, len(ci))
                    w[k] = round(min(2, max(0.3, w[k] * (1.1 if c_ > a_ * 1.05 else 0.9 if c_ < a_ * 0.95 else 1))), 3)
                w['updated'] = d; w['note'] = f'노출 {len(imp)} · 클릭 {len(clk)} 기준 조정'
                json.dump(w, open(WF, 'w', encoding='utf-8'), ensure_ascii=False)
            print('추천 가중치', w)
            st['tune'] = d
        except Exception as e:
            print('추천 가중치 조정 실패', repr(e)[:100])
    try:
        import compete   # 경쟁 지표 원자료 하루 1번 쌓기(화면은 7일치 이상부터)
        compete.main()
    except Exception as e:
        print('경쟁 지표 수집 실패', repr(e)[:120])
    try:
        import gsc
        gsc.main()
    except Exception as e:
        print('gsc 실패', repr(e)[:120])
    json.dump(st, open(SF, 'w', encoding='utf-8'))


def take_lock():
    """수집기 호출과 1시간 예약이 겹치지 않게: 20분 안의 잠금이 있으면 이번 실행은 건너뜀"""
    import time
    lk = os.path.join(HERE, '.lock')
    if os.path.exists(lk) and time.time() - os.path.getmtime(lk) < 1200:
        print('다른 생성이 진행 중이라 건너뜀')
        sys.exit(0)
    open(lk, 'w').write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(lk) and os.remove(lk))


if __name__ == '__main__':
    take_lock()
    build()
    if '--push' in sys.argv:
        daily_jobs()   # 홍보 후보·서치 콘솔 리포트(하루 슬롯마다 1번, admin/gsc.json 이 같은 커밋에 실리게 git 전에)
        def git(*a):
            r = subprocess.run(['git', '-C', ROOT] + list(a), capture_output=True, text=True, encoding='utf-8')
            print('git', a[0], r.returncode, (r.stdout + r.stderr).strip()[:200])
            return r
        git('add', '-A')
        if git('diff', '--cached', '--quiet').returncode:
            git('commit', '-q', '-m', f'사이트 데이터 갱신 {datetime.datetime.now():%m-%d %H:%M}')
            git('pull', '-q', '--rebase', '-X', 'ours')
            if git('push', '-q').returncode == 0 and NEW_URLS:
                indexnow([SITE + '/'] + NEW_URLS)
