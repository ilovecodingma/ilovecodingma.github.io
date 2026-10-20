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

COMM_TAGS_TPL = '<link rel="stylesheet" href="/assets/community/comm.css?v=15"><script defer src="/assets/community/comm.js?v=28"></script><script defer src="/assets/community/crew.js?v=1"></script>'
GTAG = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4248498719773262" crossorigin="anonymous"></script>\n'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-G9BPFF95GY"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());if(location.hostname!=='sungprofile.cloud')window['ga-disable-G-G9BPFF95GY']=true;gtag('config','G-G9BPFF95GY');</script>")
THEMES = [  # (키, 이름, 아이콘, 테마색, 홈, [하위 메뉴], [이 테마에 속하는 주소 앞부분])
    ('issue', '이슈', '🕵️', '#b45309', '/news/', [('/trend/', '이슈 트렌드'), ('/hot/', '핫이슈'), ('/news/', '기사 확인 신호'), ('/talk/', '커뮤니티 이슈'), ('/kw/', '인기 키워드'), ('/satire/', '루리 풍자'), ('/mag/', '매거진'), ('/review/', '평론')],
     ['/trend/', '/hot/', '/news/', '/talk/', '/kw/', '/satire/', '/mag/', '/review/']),
    ('money', '머니', '📊', '#047857', '/analyst/', [('/analyst/', '애널리스트 종합'), ('/money/experts/', '전문가 코멘트'), ('/money/guide/', '생활 돈 가이드'), ('/money/policy/', '투자 정책'), ('/money/age/', '나이별 원칙'), ('/money/tools/salary/', '계산기'), ('/analyst/coin/btc/', '코인')], ['/analyst/', '/money/']),
    ('contest', '공모전', '🏆', '#6d28d9', '/contest/', [('/contest/', '추천 상담'), ('/cat/literature/', '분야별'), ('/prep/', '준비실'), ('/lab/', '수상 연구소'), ('/community/', '원정대'), ('/guide/', '가이드'), ('/widget/', '위젯')],
     ['/contest/', '/c/', '/cat/', '/prep/', '/lab/', '/community/', '/guide/', '/v/', '/me/', '/widget/']),
    ('recipe', '레시피', '🍳', '#c2410c', '/fridge/', [('/fridge/', '냉장고 파먹기'), ('/fridge/solo/', '자취 요리'), ('/fridge/weather/', '날씨별'), ('/fridge/plan/', '식단·장보기'), ('/fridge/c/guk/', '국·찌개'), ('/fridge/c/bap/', '밥'), ('/fridge/c/myeon/', '면'), ('/fridge/c/bokkeum/', '볶음'), ('/fridge/c/jorim/', '조림·찜'), ('/fridge/c/banchan/', '반찬'), ('/fridge/c/jeon/', '전')], ['/fridge/']),   # 2026-10-20 사용자: 레시피 유입이 많아 별도 카테고리로
    ('life', '생활', '🧺', '#0e7490', '/apply/', [('/apply/', '지원금·청약'), ('/apply/recommend/', '청약 추천'), ('/apply/r/', '지역별'), ('/event/', '경품'), ('/qa/', '고민 해결'), ('/plaza/', '광장')], ['/apply/', '/a/', '/event/', '/qa/', '/ssul/', '/plaza/']),
    ('game', '게임', '🎮', '#4f46e5', '/game/', [('/game/', '게임 허브'), ('/watch/', '웹툰·애니 추천'), ('/game/free/', '무료 게임 기록'), ('/game/release/', '출시 일정'), ('/game/steam-sale/', '세일 달력'), ('/game/refund/', '환불 규정'), ('/game/#timing', '살 타이밍'), ('/game/#contest', '게임 공모전')], ['/game/', '/watch/']),   # 2026-10-20 홍보 세션 기획서: 게임·취미·개발 커뮤니티 콘텐츠
    ('ai', '개발 지식', '🧑‍💻', '#0f172a', '/ailog/', [('/dev/', '기술 블로그'), ('/ailog/', '개발 지식·제작 로그'), ('/dev/faq/', '개발 FAQ'), ('/en/guide/', 'English guides'), ('/class/', '루리의 AI교실'), ('/ailog/#log', 'AI 제작 로그')], ['/ailog/', '/dev/', '/en/', '/class/', '/ai/'])]   # 2026-10-19 사용자: AI 로그 → 개발 지식으로 개편


# 2026-10-19 사용자 「소비 쪽으로 가중치, URL 그대로 메인만」: 테마 줄 순서만 생활 먼저 (주소·테마 소속은 그대로)
THEMES = [next(t for t in THEMES if t[0] == k) for k in ('recipe', 'life', 'contest', 'issue', 'money', 'game', 'ai')]


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
 '/kw/': ('인기 키워드는 이렇게 골라요', '<p>구글 급상승과 시그널에서 발견한 주제를 관련 보도와 함께 살핍니다. 블로그 주제를 고를 때는 독자의 질문부터 정하세요. 예를 들어 ‘김장’은 시기·재료·보관 질문으로 나눌 수 있지만 같은 답을 반복하는 글은 합칩니다. 계절성은 여러 해의 같은 기간과 비교해야 하며, 오늘의 순위만으로 다음 달 수요를 판단할 수 없습니다. 네이버 공식 데이터랩 추이는 실제 조회 데이터가 있는 경우에만 별도로 표시합니다.</p>'),
 '/hot/': ('핫이슈 고르는 기준', '<p>검색 급상승과 언론 보도가 함께 몰린 이슈 가운데 <b>내 돈·내 생활에 바로 영향을 주는 것</b>만 골라요. 청약·지원금·세금·금리·의료·임금처럼 「나한테 달라지는 점」이 있는 이슈에는 관련 계산기와 신청처를 붙이고, 정치 공방이나 사건·사고는 넣지 않아요. 48시간이 지나면 지난 이슈로 내려가요.</p>'),
 '/satire/': ('루리 풍자에 대해', '<p>그날 화제가 된 증시·뉴스를 루리가 한 컷 만평으로 그려요. 특정 개인을 조롱하지 않고, 상황의 아이러니를 짚는 걸 원칙으로 해요. 이미지는 직접 만든 AI 그림이고, 지난 풍자도 날짜별로 모아 두었어요.</p>'),
 '/all/': ('전체 메뉴 안내', '<p>루리의 줍줍은 이슈·머니·공모전·생활·AI 로그 다섯 테마로 나뉘어 있어요. 테마마다 매시간 자동으로 갱신되는 정리 페이지와, 직접 쓴 가이드·계산기가 섞여 있어요. 찾는 메뉴가 없으면 화면 아래 루리 챗봇에게 물어보세요.</p>'),
 '/event/': ('경품 이벤트 볼 때 알아 둘 것', '<p>기업·기관 SNS와 이벤트 사이트에 올라온 경품 이벤트를 매시간 모아 마감순으로 정리해요. 댓글 한 줄·퀴즈·설문처럼 1~5분이면 끝나는 것을 위로 올려요. 당첨됐다며 개인정보나 배송비·세금 송금을 먼저 요구하는 연락은 사기일 가능성이 크니, 꼭 공식 계정의 발표 글과 대조해 보세요. 경품이 5만원을 넘으면 제세공과금(22%)을 낼 수 있어요.</p>'),
 '/fridge/': ('냉장고 파먹기 사용법', '<p>집에 있는 재료를 고르면 루리가 정리한 집밥 레시피 중 지금 바로 만들 수 있는 메뉴를 먼저 보여 드려요. 재료 하나만 더 사면 되는 메뉴도 함께 알려 줘서, 장보기 목록을 줄일 수 있어요. 레시피는 1~2인분 기준이고 조리 시간과 난이도를 함께 적었어요.</p>'),
 '/lab/': ('수상 연구소는 이렇게 분석해요', '<p>슬로건·표어·네이밍 공모전의 실제 수상작을 모아 글자 수, 운율, 대구, 핵심어 위치 같은 구조로 하나씩 풀어 봐요. 수상작을 베끼는 게 아니라 「왜 뽑혔는지」를 알아보는 곳이에요. 내 문구를 넣으면 같은 기준으로 진단해 드려요.</p>'),
 '/apply/': ('청약·지원금 신청 전에', f'<p>여기 모은 일정은 청약홈·LH·지자체·정부24 공고를 바탕으로 마감순으로 정리했어요. 같은 지원금이라도 지역·나이·소득 기준이 달라 신청 전에 자격부터 확인해야 해요. 청약은 <a href="/apply/recommend/">청약 추천</a>에서 내 가점을 먼저 계산해 보세요. 사는 곳 기준으로 보려면 <a href="/apply/r/">지역별 지원금·청약</a>에서 시·도를 고르세요. 달별로는 <a href="/apply/month/{TODAY:%Y-%m}/">{TODAY.month}월 청약 일정</a>·<a href="/apply/month/{(TODAY.replace(day=28) + datetime.timedelta(days=4)):%Y-%m}/">{(TODAY.replace(day=28) + datetime.timedelta(days=4)).month}월 청약 일정</a>, 대상별로는 <a href="/apply/newlywed/">신혼부부 지원금</a>도 있어요.</p>'),
 '/contest/': ('공모전 추천은 이렇게 해요', '<p>진행 중인 공모전을 마감·상금·분야·제출물로 정리해 두고, 내가 고른 조건에 맞는 것부터 보여 줘요. 상금이 큰 것만이 아니라 「준비 시간 대비 할 만한 것」을 위로 올리는 게 루리의 기준이에요. 각 공모전 페이지에는 같은 분야와 비교한 분석, 오늘 기준 준비 일정을 붙여 두었어요. <a href="/contest/week/">이번 주 마감 공모전</a>만 따로 볼 수도 있고, 대상·분야별로는 <a href="/contest/youth/">청소년 공모전</a>, <a href="/contest/novel/">소설 공모전</a>, <a href="/contest/photo/">사진 공모전</a>, <a href="/contest/video/">영상 공모전</a>, <a href="/contest/idea/">아이디어 공모전</a>, <a href="/contest/univ/">대학생 공모전</a>, <a href="/contest/ai-video/">AI 영상 공모전</a> 모음도 있어요.</p>'),
}.items()}


FOLD_TAGS = '<link rel="stylesheet" href="/assets/fold/fold.css?v=1"><script defer src="/assets/fold/fold.js?v=1"></script>'   # 긴 목록 접기·필터 (2026-10-20 스크롤 줄이기)


LAW_ALIAS = {   # 본문에 쓰는 이름 → 국가법령정보센터 법령명
    '근로기준법 시행령': '근로기준법 시행령', '근로기준법': '근로기준법', '국민연금법 시행령': '국민연금법 시행령', '국민연금법': '국민연금법',
    '국민건강보험법 시행령': '국민건강보험법 시행령', '국민건강보험법': '국민건강보험법', '고용보험법 시행령': '고용보험법 시행령', '고용보험법': '고용보험법',
    '산재보험법': '산업재해보상보험법', '산업재해보상보험법': '산업재해보상보험법', '정보통신망법': '정보통신망 이용촉진 및 정보보호 등에 관한 법률',
    '민법': '민법', '상법': '상법', '전자상거래법': '전자상거래 등에서의 소비자보호에 관한 법률', '금융소비자보호법': '금융소비자 보호에 관한 법률',
    '자동차손해배상 보장법': '자동차손해배상 보장법', '자배법': '자동차손해배상 보장법', '소득세법 시행령': '소득세법 시행령', '소득세법': '소득세법',
    '조세특례제한법': '조세특례제한법', '증권거래세법 시행령': '증권거래세법 시행령', '증권거래세법': '증권거래세법', '주택공급에 관한 규칙': '주택공급에 관한 규칙',
    '부가가치세법': '부가가치세법', '근로자퇴직급여 보장법': '근로자퇴직급여 보장법', '주택임대차보호법': '주택임대차보호법', '국민기초생활 보장법': '국민기초생활 보장법',
    'AI기본법': '인공지능 발전과 신뢰 기반 조성 등에 관한 기본법', '채무자회생법': '채무자 회생 및 파산에 관한 법률', '통신사기피해환급법': '전기통신금융사기 피해 방지 및 피해자산 환급에 관한 특별법', '신용정보법': '신용정보의 이용 및 보호에 관한 법률', '금융소비자보호법 시행령': '금융소비자 보호에 관한 법률 시행령'}
LAW_DEFAULT = {   # 경로 → 이름 없이 「제N조」만 쓴 곳이 가리키는 법 (한 가지 법만 다루는 글만)
    '/money/guide/annual-leave-pay-resign/': '근로기준법', '/money/guide/parttime-contract/': '근로기준법', '/money/guide/parttime-weekly-holiday-pay/': '근로기준법',
    '/money/guide/parttime-unpaid-wages/': '근로기준법'}
_LAW_RE = re.compile(r'(' + '|'.join(re.escape(k) for k in sorted(LAW_ALIAS, key=len, reverse=True)) + r'|시행령|법)?(\s*)(제\d+조(?:의\d+)?)')


def law_linkify(html_s, default=None):
    """법령 조문 언급(「근로기준법 제60조」 등)을 국가법령정보센터 조문 주소로 연결. 이름이 없으면 글의 기본 법(default)일 때만 연결하고, 이미 링크·스크립트·스타일 안은 건드리지 않아요."""
    out, depth = [], 0
    for tok in re.split(r'(<[^>]+>)', html_s):
        if tok.startswith('<'):
            low = tok[1:6].lower()
            if re.match(r'<(a|script|style|h1)\b', tok, re.I): depth += 1
            elif re.match(r'</(a|script|style|h1)\b', tok, re.I): depth = max(0, depth - 1)
            out.append(tok); continue
        if depth or '제' not in tok:
            out.append(tok); continue
        def rep(m):
            nm, sp, art = m.group(1), m.group(2), m.group(3)
            if nm in LAW_ALIAS: law = LAW_ALIAS[nm]
            elif nm in ('시행령', '법') and default: law = default + (' 시행령' if nm == '시행령' and not default.endswith('시행령') else '')
            elif not nm and default: law = default
            else: return m.group(0)
            url = 'https://www.law.go.kr/법령/' + law.replace(' ', '') + '/' + art
            return f'<a href="{url}" target="_blank" rel="noopener">{(nm or "") + sp + art}</a>'
        out.append(_LAW_RE.sub(rep, tok))
    return ''.join(out)


def page(path, title, desc, body, crumbs=None, ld=None, full_title=False, noindex=False, og=None, lang='ko', canon=None):
    url = SITE + (canon or path)
    TH = theme_of(path)
    # 사이트맵 lastmod: 날짜·시각·D-day 처럼 매번 바뀌는 글자는 빼고 내용이 바뀐 날만 갱신
    PAGE_HASH[path] = hashlib.md5(re.sub(r'D-\d+|D-DAY|\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}|[\d,]+\s*(?:건|명|개|곳|회|일 남)', '', title + body).encode()).hexdigest()
    if noindex:
        NOINDEX.add(path)
    if path.startswith(('/money/guide/', '/money/tools/', '/guide/', '/ai/', '/qa/')) and not noindex:
        body = law_linkify(body, LAW_DEFAULT.get(path))
    COMM_TAGS = COMM_TAGS_TPL if COMM_API else ''
    t = title if full_title else f'{title} | {NAME}'
    # 2026-10-20 정보성 글 PDF: 미리 만든 PDF 다운로드 + 인쇄(PDF로 저장) 버튼
    if path.count('/') == 3 and not noindex and path.startswith(('/guide/', '/dev/', '/review/', '/ssul/', '/mag/', '/fridge/r/', '/lab/', '/hot/', '/money/')):
        import make_pdf as _MP
        _pb = '<div class="pdf-bar">' + (f'<a class="main" data-pdf href="/pdf/{_MP.pdf_name(path)}" download>📄 PDF 다운로드</a>' if _MP.is_pdf_path(path) else '') + '<button type="button" data-print>🖨️ 인쇄 · PDF로 저장</button></div>'
        body = body.replace('</h1>', '</h1>' + _pb, 1) if '</h1>' in body else body
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
<link rel="canonical" href="{url}">{'<link rel="alternate" type="application/rss+xml" title="루리의 줍줍 기술 블로그" href="/dev/rss.xml">' if path.startswith('/dev/') or path == '/ailog/' else ''}{f'<link rel="alternate" hreflang="en" href="{url}">' if lang == 'en' else ''}
<meta property="og:type" content="website"><meta property="og:locale" content="{'en_US' if lang == 'en' else 'ko_KR'}"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{E(t)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og or "/assets/ruri/og.jpg"}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}{og or "/assets/ruri/og.jpg"}">
<meta name="theme-color" content="{TH[3] if TH else '#5b21b6'}"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="오늘 뭐 먹지">
<link rel="icon" href="/favicon.ico?v=6" sizes="any"><link rel="icon" type="image/png" sizes="48x48" href="/assets/icons/icon-48.png?v=6"><link rel="icon" type="image/png" sizes="96x96" href="/assets/icons/icon-96.png?v=6"><link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png?v=6"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png?v=6"><link rel="manifest" href="/site.webmanifest"><link rel="alternate" type="application/rss+xml" title="루리의 줍줍" href="/rss.xml">
<link rel="preconnect" href="https://cdn.jsdelivr.net"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/gm.css?v=20"><link rel="stylesheet" href="/assets/ds.css?v=14"><link rel="stylesheet" href="/assets/print.css?v=1"><script defer src="/assets/print.js?v=1"></script>{('<link rel="stylesheet" href="/assets/chat/ruri-chat.css?v=9">') if not (TH and TH[0] == 'ai') else ''}{COMM_TAGS}{('<script type="module" src="/assets/chat/ruri-chat.js?v=16"></script>') if not (TH and TH[0] == 'ai') else ''}<link rel="stylesheet" href="/assets/app/shell.css?v=1"><script defer src="/assets/app/app.js?v=4"></script>
{ldh}
{GTAG}
</head><body data-th="{TH[0] if TH else 'hub'}"{(' data-api="' + COMM_API + '"') if COMM_API else ''}>
<header class="hd"><div class="w hd-in"><a class="logo" href="/"><img class="logo-av" src="/assets/ruri/avatar.webp" width="36" height="36" alt="루리의 줍줍"><span>루리의 <b>줍줍</b></span></a>{('<span class="th-name">' + TH[2] + ' ' + TH[1] + '</span>') if TH else ''}</div>
<nav class="th-sw w" aria-label="테마">{"".join(f'<a href="{t[4]}" style="--tc:{t[3]}"{" class=on" if TH and TH[0] == t[0] else ""}>{t[2]} {t[1]}</a>' for t in THEMES)}</nav>
{('<nav class="tb w" aria-label="' + TH[1] + ' 메뉴">' + "".join(f'<a href="{u}"{" class=on" if (path == u or (u != TH[4] and path.startswith(u))) else ""}>{n}</a>' for u, n in TH[5]) + '</nav>') if TH else ''}</header>
<main class="w">
{body}{PAGE_INTRO.get(path, '')}
</main>
<footer class="ft"><div class="w ft-in"><div class="ft-b"><img class="av" src="/assets/ruri/avatar.webp" width="56" height="56" alt="루리" loading="lazy"><div><b>루리의 줍줍</b><p>오늘 뭐 먹지부터 지원금·공모전·이슈까지, 일단 줍고 가세요.</p><p class="ft-m">문의 <a href="mailto:{MAIL}">{MAIL}</a>{"" if PARTNER == MAIL else f' · 제휴 <a href="mailto:{PARTNER}">{PARTNER}</a>'}</p></div></div>
<nav class="ft-g" aria-label="사이트 메뉴"><div><b>🍳 생활</b><a href="/fridge/">냉장고 파먹기</a><a href="/event/">경품·용돈</a><a href="/qa/">고민 해결</a><a href="/plaza/">광장</a></div>
<div><b>💰 지원금·머니</b><a href="/apply/">지원금·청약</a><a href="/money/tools/salary/">계산기</a><a href="/money/experts/">전문가 말 vs 시세</a><a href="/analyst/">애널리스트</a></div>
<div><b>🏆 공모전</b><a href="/contest/">공모전 찾기</a><a href="/prep/">준비실</a><a href="/guide/">응모 가이드</a><a href="/lab/">수상 연구소</a></div>
<div><b>📺 이슈</b><a href="/news/">루리 뉴스</a><a href="/trend/">이슈 트렌드</a><a href="/hot/">핫이슈</a><a href="/kw/">인기 키워드</a></div>
<div><b>ℹ️ 사이트</b><a href="/about/">소개</a><a href="/ailog/">개발 지식</a><a href="/app/">앱·알림</a><a href="/all/">전체 메뉴</a></div></nav>
{('<p class="ft-c">' + comm_btns() + '</p>') if COMM_LINKS else ''}<p class="ft-l"><a href="/privacy/">개인정보처리방침</a><a href="/terms/">이용약관</a><a href="/contact/">문의</a></p>
<p class="ft-n">정보는 각 기관의 공고·언론 보도·공개 자료를 바탕으로 정리했어요. 정확한 내용은 반드시 공식 공고와 원문에서 확인하세요. 일부 링크는 쿠팡 파트너스 활동의 일환으로 수수료를 받을 수 있어요. © 2026 루리의 줍줍 · sungprofile.cloud</p></div></footer>{CL_CSS if COMM_LINKS else ''}
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
        if re.match(r'^\s*(및|등|또는|,|·|\)|이상\b)', c.get('elig') or '') or c.get('elig') in ('공고 참조', '-'):   # 2026-10-19: 잘려 들어온 자격 문구는 비워 「공식 공고 확인 필요」로
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
    cur = set(GONE) | {f'/c/{d}/' for d in DUP} | {f'/a/{d}/' for d in AP_DUP}   # 중복 공고 안내 페이지는 덮어쓰지 않음
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
        if u.startswith('/a/') and u[3:-1] in AP_DUP:   # 중복 공고 안내(대표 /a/ 로 보냄)는 남김 — /apply/?id= 에는 그 id 가 없음
            continue
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
    return ''.join(f'<a class="{cls}" href="{E(x["url"])}" target="_blank" rel="noopener"' + (f' style="background:{E(x["bg"])};color:{E(x.get("fg", "#fff"))}' + (f';box-shadow:inset 0 0 0 2px {E(x["bd"])}' if x.get('bd') else '') + '"' if x.get('bg') else '') + f'>{E(x.get("label") or (x.get("icon", "") + " " + x["name"]))}</a>' for x in COMM_LINKS)   # bg·fg·bd(테두리): 채널 색(없으면 카톡 노랑). 카톡 채널은 톡방과 같은 노랑이라 검은 테두리로 구분


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
{share_bar(c['title'], f'「{c["title"]}」 {ddot(c["end"])[5:]} 마감' + (f' · {c["prize"]}' if c.get('pv') else '') + ' — 자격·제출물 정리')}{comm_banner()}{join_cta('contest')}
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
          'expires': c['end'], 'about': {'@type': 'Thing', 'name': c['title'], 'url': c['link'], 'additionalProperty': [{'@type': 'PropertyValue', 'name': k_, 'value': v_} for k_, v_ in [('주최', (c.get('org') or '').strip()), ('접수 시작', c.get('start') or ''), ('접수 마감', c['end']), ('상금', (c.get('prize') or '').strip()), ('응모 자격', (c.get('elig') or '').strip()[:200]), ('접수 방법', (c.get('ch') or '').strip())] if v_]}, 'publisher': {'@type': 'Organization', 'name': NAME, 'url': SITE + '/'}}
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
    body += cp_box('공모전 대학생 공부', '공모전 준비할 때 많이 찾는 물건:')
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


AP_DUP, AP_SEEN = {}, {}   # 중복 지원금 공고 id → 대표 id


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
        ck = (P.clean(r['title'])[:90], P.clean(r.get('org', ''))[:40], P.clean(r.get('region', ''))[:20], P.clean(r.get('benefit', ''))[:80], end)   # 2026-10-20 같은 사업이 출처 2곳(온통청년·복지로)에 올라온 것
        if ck in AP_SEEN:
            AP_DUP[aid] = AP_SEEN[ck]
            continue
        AP_SEEN[ck] = aid
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
    for d_, r_ in AP_DUP.items():   # 같은 사업 중복 공고: 대표 페이지로 보내고 색인 제외
        page(f'/a/{d_}/', '같은 공고로 합쳐졌어요', '같은 지원 사업의 대표 페이지로 합쳐졌어요.',
             f'<h1>같은 공고로 합쳐졌어요</h1><p>같은 사업이 다른 출처에도 올라와 있어서 대표 페이지 하나로 합쳤어요.</p><p><a class="lab-cta" href="/a/{r_}/"><b>대표 공고 페이지로 가기 →</b></a></p><script>location.replace("/a/{r_}/")</script>',
             noindex=True)
    # 메인 루리 상담(청약·지원금)용 데이터 (2026-10-17)
    with open(os.path.join(ROOT, 'apply.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump([{k: a[k] for k in ('id', 'title', 'org', 'kind', 'icon', 'kk', 'start', 'end', 'always', 'region', 'target', 'benefit', 'how', 'income', 'age_min', 'age_max', 'url') if a.get(k) not in (None, '', False)} for a in aps], f, ensure_ascii=False, separators=(',', ':'))
    for a in aps:
        n, dd = dday(a['end'])
        period = (ddot(a['start']) + ' ~ ' if a['start'] else '~ ') + ddot(a['end'])
        tb = ''.join(f'<tr><th>{k}</th><td>{E(v)}</td></tr>' for k, v in
                     [x for x in [('구분', a['kind']), ('대상', a.get('target')), ('혜택', a.get('benefit')), ('지역', a.get('region')), ('나이', (f"만 {a['age_min'] or ''}~{a['age_max'] or ''}세" if a.get('age_min') or a.get('age_max') else '')),
                      ('소득 조건', a.get('income')), ('신청 방법', a.get('how')), ('주관', a['org']), ('신청 기간', '상시 신청' if a.get('always') else period), ('출처', a['source'] or '공식 공고')] if x[1]])
        _sn = {'youthcenter': '온라인청년센터', 'bokjiro': '복지로', 'gov24': '정부24', 'odcloud': '공공데이터포털', 'applyhome': '청약홈', 'lh': 'LH 청약플러스'}.get((a.get('source') or '').strip(), a.get('source') or '공식 공고')
        tb = re.sub(r'<tr><th>출처</th><td>[^<]*</td></tr>', lambda m: '<tr><th>출처</th><td>' + (f'<a href="{E(a["url"])}" target="_blank" rel="noopener nofollow">공식 공고 원문 →</a> (수집: {E(_sn)})' if a.get('url') else E(_sn)) + '</td></tr>', tb)
        btn = (f'<a class="btn" href="{E(a["url"])}" target="_blank" rel="noopener nofollow">공식 사이트에서 신청하기 →</a>' if a['url'] else '')
        body = f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">청약·신청</a></p>
<section class="dh" data-c="apply"><span class="ic big">{a["icon"]}</span><h1>{E(a["title"])}</h1><p class="lead">{'<span class="d">상시</span> 지금 신청할 수 있어요' if a.get('always') else f'<span class="d{" u3" if n <= 3 else " hot" if n <= 7 else ""}">{dd}</span> {ddot(a["end"])} 마감'}</p></section>
<div class="my-acts" data-id="a:{E(a['id'])}" data-title="{E(a['title'])}" data-end="{'' if a.get('always') else a['end']}"></div>
{say('o_suit', f'신청 기간을 놓치지 마세요! 자격 조건은 <b>공식 공고</b>에서 꼭 확인해 주세요.')}
<div class="panel"><table class="info">{tb}</table>{btn}</div>
{share_bar(a['title'], f'「{a["title"]}」 ' + ('상시 신청' if a.get('always') else f'{ddot(a["end"])[5:]} 마감') + ' — 대상·신청처 정리')}{comm_banner()}{join_cta('apply')}{ap_insight(a, aps)}<h2>신청 전 확인할 것</h2><ul class="chk"><li>신청 자격(나이·소득·자산·거주지·무주택 여부)</li><li>필요 서류와 본인인증 수단</li><li>발표일과 계약·납부 일정</li></ul>'''
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
{say('o_desk', '신청만 하면 되는 기회들이에요. 기간이 짧으니 미리 챙겨요!')}{join_cta('apply')}{APPLY_INTRO}<h2>진행 중 청약·신청 <small>마감 가까운 순 {min(60, len(aps))}건 · 전체 {len(aps)}건</small></h2><ul class="list" id="ap-list">{lst}</ul>
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


def xregions(aps, tk):
    """주제별로 페이지가 만들어질 시·도 [(slug, 이름, 건수)] — cross_pages 와 같은 기준(2건 이상). 홈이 먼저 빌드돼서 따로 셈."""
    f = XTOPIC[tk][2]
    c = collections.Counter(sido_of(a) for a in aps if f(a))
    return [(sl, nm, c[sl]) for sl, nm, _ in SIDO if c[sl] >= 2]


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
                    + ((cp_widget('자취 필수템', 'apply') or cp_box('월세 자취', '자취 시작할 때 많이 사는 것:', 1)) if tk == 'youth-rent' else '')
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
                + (cp_widget('자취 필수템', 'apply') or cp_box('월세 자취', '자취 시작할 때 많이 사는 것:', 1))
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
        ]
    more_h = ''.join(f'<a class="hm-m hm-{k}" href="{u}"><span>{ic}</span><div><b>{E(n)}</b><p>{E(v)}</p><small>{E(sc)}</small></div></a>' for k, u, ic, n, v, sc in more)
    hot_h = ''.join(f'<li><a href="/hot/{v["slug"]}/">{E(v["title"])}<small> · 언론사 {len(v["outs"])}곳</small></a></li>' for v in hot3[:3])
    _rj = os.path.join(ROOT, 'assets', 'fridge', 'recipes.json')
    NR_HOME = f'{len(json.load(open(_rj, encoding="utf-8")).get("recipes", [])):,}' if os.path.exists(_rj) else '1,300'
    XLINKS_HOME = ''.join(f' · <a href="/apply/{tk}/{sl}/">{"청년 월세" if tk == "youth-rent" else "신혼부부"} {nm}</a>' for tk in ('youth-rent', 'newlywed') for sl, nm, n in sorted(xregions(aps, tk), key=lambda x: -x[2])[:3])
    _RS = json.load(open(_rj, encoding='utf-8'))['recipes'] if os.path.exists(_rj) else []
    _TD = _rd('assets/fridge/today.json') or {}
    _picks = [r for n_ in _TD.get('picks', []) for r in _RS if r['n'] == n_][:3]
    _ez = ('댓글 1줄', '퀴즈 1분', '설문 5분', '응모만', '폼 1분')
    _ev3 = sorted([e for e in events if (e.get('org') or '').strip() and dday(e['end'])[0] >= 0], key=lambda e: (e['end'], (e.get('effort') or EASY.get(e['type'], '')) not in _ez))[:6]
    _ing = ['김치', '달걀', '스팸', '두부', '감자', '양파', '참치', '대파']
    import fridge_today as _FT
    _PHJ = (_rd('assets/fridge/recipes_ph.json') or {}).get('recipes') or {}
    _popj = _rd('assets/fridge/rec_pop.json') or {}
    def _rimg(r):
        sl_ = fr_slug(r['n']); t_ = os.path.join(ROOT, 'assets', 'fridge', 'ph', 't', sl_ + '.webp')
        if os.path.exists(t_): return f'/assets/fridge/ph/t/{sl_}.webp'
        mp_ = ((_PHJ.get(r['n']) or {}).get('main') or {}).get('f')
        return mp_ if mp_ and os.path.exists(os.path.join(ROOT, mp_.lstrip('/'))) else ''
    _pool = [r for r in _RS if _rimg(r)]
    _bypop = sorted(_pool, key=lambda r: -(_popj.get(fr_slug(r['n'])) or [0])[0])
    _show, _cats = [], {}
    for r in [x for x in _bypop if (_popj.get(fr_slug(x['n'])) or [0])[0] > 0] + sorted(_pool, key=lambda r: (r['m'], r['n'])):
        c_ = _FT.cat(r['n'])
        if r in _show or _cats.get(c_, 0) >= 2: continue
        _show.append(r); _cats[c_] = _cats.get(c_, 0) + 1
        if len(_show) >= 10: break
    hx_rc = ''.join(f'<li class="hx-rc"><a href="/fridge/r/{fr_slug(r["n"])}/"><div class="ph"><img src="{_rimg(r)}" width="400" height="300" loading="lazy" decoding="async" alt="{E(r["n"])} 완성 사진"><em>⏱ {r["m"]}분</em></div><b>{E(r["n"])}</b><small>{_FT.cat(r["n"])} · {E(r["lv"])}</small></a></li>' for r in _show)
    _hp = next((r for r in _picks if _rimg(r)), None) or (_show[0] if _show else None)
    hx_pick = (f'<a class="hx-ssrpick" href="/fridge/r/{fr_slug(_hp["n"])}/"><img src="{_rimg(_hp)}" width="400" height="300" alt="{E(_hp["n"])} 완성 사진" fetchpriority="high"><b>{_hp["e"]} {E(_hp["n"])}</b><span>⏱ {_hp["m"]}분 · {E(_hp["lv"])} · 재료 {len(_hp["need"])}가지</span></a>') if _hp else ''
    _why0 = (_TD.get('why') or '').replace('엔', '엔 ') if _TD else ''
    hx_say = (f'{E(_why0.strip())}! <b>{E(_hp["n"])}</b> 어때요? 🍽️' if _hp and _why0 else (f'오늘은 <b>{E(_hp["n"])}</b> 어때요? 🍽️' if _hp else '냉장고 재료만 알려 주면 오늘 메뉴를 골라 줄게요!'))
    _eyebrow = f'{E(_TD.get("place", "서울"))} {round(_TD.get("t", 0))}° · {E(_TD.get("why", "오늘 뭐 먹을지 골라 드려요"))}' if _TD else '오늘 뭐 먹을지 골라 드려요'
    _tiles = [('🍳', '오늘 뭐 먹지', '/fridge/', '#fff1e6'), ('🏠', '자취 요리', '/fridge/solo/', '#e8f7ee'), ('🌤️', '날씨별 메뉴', '/fridge/weather/', '#e6f2ff'), ('🏆', '공모전', '/contest/', '#f1e9ff'),
              ('📋', '지원금·청약', '/apply/', '#e6f7f4'), ('🎁', '경품·용돈', '/event/', '#ffe9ef'), ('🕵️', '이슈·뉴스', '/news/', '#fff6d9'), ('🧮', '계산기', '/money/tools/salary/', '#eaeefb')]
    hx_tiles = ''.join(f'<a class="hx-tile" href="{u}" style="--tbg:{bg}"><i>{ic}</i>{n}</a>' for ic, n, u, bg in _tiles)
    hx_ev = ''.join(f'<li><a href="{E(e["link"])}" target="_blank" rel="noopener nofollow"><span class="dd{" u" if dday(e["end"])[0] <= 1 else ""}">{dday(e["end"])[1]}</span><div><b>{E(e["title"][:52])}</b><small>{E(e.get("org") or "")} · {E(e.get("effort") or EASY.get(e["type"], ""))}</small></div></a></li>' for e in _ev3[:6])
    _fc = [('#7c3aed', '#f4efff'), ('#0f766e', '#e8f7f4'), ('#ea580c', '#fff1e6'), ('#2563eb', '#e8f0ff'), ('#db2777', '#ffe9f2'), ('#ca8a04', '#fff8de')]
    hx_more = ''.join(f'<a class="hx-f" href="{u}" style="--fc:{_fc[j % 6][0]};--fbg:{_fc[j % 6][1]}"><i>{ic}</i><b>{E(n)}</b><span>{E(v)}</span></a>' for j, (k, u, ic, n, v, sc) in enumerate(more))
    # ── 홈 v3 데이터: 오늘 마감 보드(공모전·경품·지원금) ──
    _rows = []
    for e_ in events:
        n_, dd_ = dday(e_['end'])
        if 0 <= n_ <= 1 and (e_.get('org') or '').strip():
            _rows.append((n_, '🎁', '경품', e_['title'], e_['link'], 1, dd_))
    for c_ in live:
        n_, dd_ = dday(c_['end'])
        if 0 <= n_ <= 3:
            _rows.append((n_, '🏆', '공모전', c_['title'], f'/c/{c_["id"]}/', 0, dd_))
    for a_ in aps:
        if a_.get('end') and not a_.get('always'):
            n_, dd_ = dday(a_['end'])
            if 0 <= n_ <= 2:
                _rows.append((n_, '📋', a_.get('kind') or '지원금', a_['title'], a_['url'], 1, dd_))
    _by = {}
    for r_ in sorted(_rows, key=lambda r: (r[0], r[2])):
        if _by.get(r_[2], 0) >= 2: continue
        _by[r_[2]] = _by.get(r_[2], 0) + 1
    _board, _cnt = [], {}
    for r_ in sorted(_rows, key=lambda r: (r[0], r[1])):
        if _cnt.get(r_[1], 0) >= 2: continue
        _cnt[r_[1]] = _cnt.get(r_[1], 0) + 1; _board.append(r_)
    _board = sorted(_board, key=lambda r: r[0])[:6]
    hx_board = ''.join(f'<li><a href="{E(u_)}"{" target=_blank rel=\"noopener nofollow\"" if ext_ else ""}><span class="bd-t">{ic_}<small>{E(lb_[:6])}</small></span><b>{E(t_[:46])}</b><span class="bd-d{" u" if n_ == 0 else ""}">{dd_}</span></a></li>' for n_, ic_, lb_, t_, u_, ext_, dd_ in _board)
    _n_today = len([r for r in _rows if r[0] == 0])
    hx_say = (f'오늘 마감이 <b>{_n_today}건</b>이에요! 제일 급한 건 <b>{E(_board[0][3][:22])}</b> ⏰' if _board else '오늘도 남들이 뿌린 기회를 모아 왔어요!')
    hx_pol = sorted([a for a in aps if a.get('end') and not a.get('always') and 0 <= dday(a['end'])[0] <= 14], key=lambda a: a['end'])[:5]
    hx_pol_h = ''.join(f'<li><a href="{E(a["url"])}" target="_blank" rel="noopener nofollow"><span class="dd{" u" if dday(a["end"])[0] <= 1 else ""}">{dday(a["end"])[1]}</span><div><b>{E(a["title"][:48])}</b><small>{E(a.get("kind") or "")} · {E(a.get("org") or "")}</small></div></a></li>' for a in hx_pol)
    _has_policy = os.path.exists(os.path.join(ROOT, 'money', 'policy', 'index.html'))
    _pol_link = '/money/policy/' if _has_policy else '/apply/'
    _fc = [('#7c3aed', '#f4efff'), ('#0f766e', '#e8f7f4'), ('#ea580c', '#fff1e6'), ('#2563eb', '#e8f0ff'), ('#db2777', '#ffe9f2'), ('#ca8a04', '#fff8de')]
    hx_more = ''.join(f'<a class="hx-f" href="{u}" style="--fc:{_fc[j % 6][0]};--fbg:{_fc[j % 6][1]}"><i>{ic}</i><b>{E(n)}</b><span>{E(v)}</span></a>' for j, (k, u, ic, n, v, sc) in enumerate(more))
    AICLASS = '<a class="hx-f" href="/class/" style="--fc:#4338ca;--fbg:#eef0ff"><i>🎓</i><b>루리의 AI교실</b><span>AI를 처음 써 보는 사람을 위한 수업</span></a>' if os.path.exists(os.path.join(ROOT, 'class', 'index.html')) else ''
    _nav = [('today', '⏰', '오늘 마감'), ('policy', '📋', '지원금·정책'), ('contest', '🏆', '공모전'), ('event', '🎁', '경품'), ('issue', '🕵️', '이슈'), ('money', '🧮', '머니'), ('watch', '🎯', '웹툰·애니'), ('learn', '🎓', '배우기'), ('recipe', '🍳', '레시피'), ('plaza', '🗣️', '광장')]
    def _hx_watch():
        import random as _r
        out = ''
        for k, nm in (('webtoon', '📖 웹툰'), ('anime', '🎬 애니')):
            f = os.path.join(HERE, 'watch', k + '.json')
            if not os.path.exists(f): continue
            I = list(json.load(open(f, encoding='utf-8'))['items'].values())
            if k == 'webtoon':
                I = [v for v in I if v.get('th') and not v.get('adult') and not v.get('rest') and not v.get('fin') and (v.get('sc') or 0) >= 9.7]; I.sort(key=lambda v: -(v.get('fav') or 0)); I = I[:40]
            else:
                I = [v for v in I if v.get('cv') and v.get('fmt') in ('TV', 'ONA') and (v.get('sc') or 0) >= 75 and v.get('year', 0) >= (TODAY.year - 2)]; I.sort(key=lambda v: -(v.get('pop') or 0)); I = I[:40]
            _r.Random(TODAY.toordinal() + len(k)).shuffle(I); I = I[:8]
            cards = ''.join('<li class="hx-wc"><a href="/watch/#%s"><span class="wp"><img src="%s" alt="%s 표지" loading="lazy" referrerpolicy="no-referrer"></span><b>%s</b><small>%s</small></a></li>' % (
                k, E(v['th'] if k == 'webtoon' else v['cv']), E(v['n'] if k == 'webtoon' else (v['kr'] or v['en'] or v['ro'])), E((v['n'] if k == 'webtoon' else (v['kr'] or v['en'] or v['ro']))[:22]),
                E(' · '.join((v.get('tags') or [])[:2]) if k == 'webtoon' else ' · '.join(GL_ANIME.get(g, g) for g in v['g'][:2]))) for v in I)
            out += f'<div class="hx-wh"><b>{nm}</b></div><ul class="hx-row hx-wrow">{cards}</ul>'
        return out
    hx_watch = _hx_watch()
    hx_nav = ''.join(f'<a href="#{k}">{ic} {n}</a>' for k, ic, n in _nav)
    home = f'''<section class="hx-hero"><div class="hx-w hx-hero-in">
<div class="hx-copy"><p class="hx-eyebrow"><i></i>매시간 업데이트 · 공식 출처 확인</p>
<h1>남들이 뿌리는 기회,<br><em>루리가 모아</em><br>정리해 드려요</h1>
<p class="hx-sub">공모전·경품 이벤트·지원금·청약·정책을 한곳에 모아, 마감이 급한 순서로 알려 드려요. 놓치지 말고 <b>일단 줍고</b> 가세요.</p>
<div class="hx-cta"><a class="hx-b1" href="#today">⏰ 오늘 마감 보기</a><a class="hx-b2" href="/app/">🔔 마감 알림 받기</a></div>
<p class="hx-free">🆓 매시간 모아 가공한 데이터를 <b>전부 무료</b>로 공개해요</p><div class="hx-stats"><div><b>{len(live)}</b><span>진행 중 공모전</span></div><div><b>{len(events):,}</b><span>경품·이벤트</span></div><div><b>{len(aps)}</b><span>지원금·청약</span></div></div></div>
<div class="hx-stage" id="today"><div class="hx-bubble"><small>루리의 한마디</small>{hx_say}</div>
<img class="hx-ruri" src="/assets/ruri/o_present.webp" width="300" height="415" alt="루리" fetchpriority="high">
<div class="hx-card hx-board"><div class="bd-h"><b>⏰ 오늘 마감 한눈에</b><small>마감 임박순</small></div><ul>{hx_board or '<li class="empty">지금은 마감 임박 항목이 없어요.</li>'}</ul><a class="bd-more" href="/contest/week/">이번 주 마감 전체 보기 →</a></div></div>
</div></section>
<nav class="hx-nav" aria-label="주제로 이동"><div class="hx-w">{hx_nav}</div></nav>
<div class="hx-w">

<section class="hx-sec hx-t-policy" id="policy"><div class="hx-hd"><div><p>📋 지원금 · 청약 · 정책</p><h2>내가 받을 수 있는 혜택</h2></div><a href="{_pol_link}">정책 모음 →</a></div>
<div class="hx-split"><ul class="hx-ev">{hx_pol_h or '<li class="empty">2주 안에 마감하는 공고가 없어요.</li>'}</ul>
<div class="hx-feat hx-feat1"><a class="hx-f" href="/apply/" style="--fc:#0f766e;--fbg:#e8f7f4"><i>📋</i><b>지원금·청약 일정</b><span>신청 가능 {len(aps)}건 · 최근 3일 새 공고 {newap}건</span></a>
<a class="hx-f" href="/apply/r/" style="--fc:#2563eb;--fbg:#e8f0ff"><i>📍</i><b>지역별 지원금</b><span>시·도별 청년 월세·신혼부부 공고</span></a></div></div>
<div class="hx-links"><a href="/apply/youth-rent/">청년 월세 지원</a><a href="/apply/newlywed/">신혼부부 지원금</a><a href="/apply/recommend/">청약 가점 계산기</a></div></section>

<section class="hx-sec hx-t-contest" id="contest"><div class="hx-hd"><div><p>🏆 공모전</p><h2>이번에 도전해 볼 공모전</h2></div><a href="/contest/">공모전 찾기 →</a></div>
<p class="hx-why">진행 중 {len(live)}건 · 7일 안 마감 {wk7}건 · {E(scope_c)}</p>
<ul class="hx-cc">{"".join(cmp_card(c) for c in pick6[:3]) or '<li class="empty">지금 보여 드릴 공모전이 없어요.</li>'}</ul>
<div class="hx-links"><a href="/contest/week/">이번 주 마감</a><a href="/contest/univ/">대학생 공모전</a><a href="/cat/literature/">분야별</a><a href="/prep/">📋 준비실</a><a href="/lab/">🔬 수상 연구소</a><a href="/guide/">📘 응모 가이드</a></div></section>

<section class="hx-sec hx-t-event" id="event"><div class="hx-hd"><div><p>🎁 경품 · 이벤트</p><h2>오늘 마감 경품·용돈</h2></div><a href="/event/">전체 {len(events):,}건 →</a></div>
<ul class="hx-ev">{hx_ev or '<li class="empty">지금은 마감 임박 이벤트가 없어요.</li>'}</ul></section>

<section class="hx-sec hx-t-issue" id="issue"><div class="hx-hd"><div><p>🕵️ 이슈 · 뉴스</p><h2>같은 사건, 여러 언론을 한 번에</h2></div><a href="/news/">루리 뉴스 →</a></div>
{f'<div class="hx-hot"><b>🔥 지금 뜨는 이슈</b><ol>{hot_h}</ol></div>' if hot_h else ''}
<div class="hx-links"><a href="/news/#brief">📺 오늘의 브리핑</a><a href="/hot/">🔥 핫이슈</a><a href="/kw/">🔎 인기 키워드</a><a href="/trend/">🍿 이슈 트렌드</a><a href="https://www.youtube.com/channel/UCdJQUqqrHHXC7mWstly2eXw" target="_blank" rel="noopener">▶️ 루리 뉴스 유튜브</a></div></section>

<section class="hx-sec hx-t-money" id="money"><div class="hx-hd"><div><p>🧮 머니</p><h2>계산기 · 생활 돈 가이드</h2></div><a href="/money/tools/salary/">계산기 →</a></div>
<div class="hx-feat"><a class="hx-f" href="/money/tools/salary/" style="--fc:#7c3aed;--fbg:#f4efff"><i>🧮</i><b>연봉 실수령액 계산기</b><span>2026 기준 · 실업급여·퇴직금도</span></a>
<a class="hx-f" href="/money/guide/" style="--fc:#ea580c;--fbg:#fff1e6"><i>🧭</i><b>생활 돈 가이드</b><span>퇴사·주거·알바·사업 때 돈 문제를 순서대로</span></a>
<a class="hx-f" href="/money/experts/" style="--fc:#ca8a04;--fbg:#fff8de"><i>📊</i><b>전문가 말 vs 시세</b><span>목표가가 얼마나 맞았나</span></a>
<a class="hx-f" href="/analyst/" style="--fc:#0f766e;--fbg:#e8f7f4"><i>📈</i><b>애널리스트 종합</b><span>증권사 의견을 숫자로만 요약</span></a></div>
<div class="hx-links"><a href="/money/guide/journey/resign/">퇴사했을 때</a><a href="/money/guide/journey/housing/">집 구할 때</a><a href="/money/guide/journey/parttime/">알바할 때</a></div></section>

<section class="hx-sec hx-t-watch" id="watch"><div class="hx-hd"><div><p>🎯 웹툰 · 애니 추천</p><h2>장르만 고르면 오늘의 추천</h2></div><a href="/watch/">추천 받기 →</a></div>
{hx_watch}
<div class="hx-links"><a class="hx-primary" href="/watch/">🎯 장르 골라 오늘의 추천 받기</a><a href="/watch/#webtoon">📖 웹툰 추천</a><a href="/watch/#anime">🎬 애니 추천</a></div></section>

<section class="hx-sec hx-t-learn" id="learn"><div class="hx-hd"><div><p>🎓 배우기 · 놀이</p><h2>AI·개발 지식과 무료 게임</h2></div><a href="/ailog/">개발 지식 →</a></div>
<div class="hx-feat">{AICLASS}<a class="hx-f" href="/ailog/" style="--fc:#2563eb;--fbg:#e8f0ff"><i>💻</i><b>개발 지식</b><span>이 사이트를 AI로 만든 과정과 기록</span></a>
<a class="hx-f" href="/dev/faq/" style="--fc:#7c3aed;--fbg:#f4efff"><i>❓</i><b>개발 FAQ</b><span>만들면서 막혔던 것 · 비용 · 구조</span></a>
<a class="hx-f" href="/watch/" style="--fc:#9333ea;--fbg:#f5ecff"><i>🎯</i><b>웹툰·애니 추천</b><span>장르만 고르면 오늘의 추천</span></a>
<a class="hx-f" href="/game/" style="--fc:#db2777;--fbg:#ffe9f2"><i>🎮</i><b>이번 주 무료 게임</b><span>스팀·에픽 무료 배포 모음</span></a></div></section>

<section class="hx-sec hx-t-recipe" id="recipe"><div class="hx-hd"><div><p>🍳 쉬어가는 식탁</p><h2>오늘 뭐 먹지?</h2></div><a href="/fridge/">레시피 {NR_HOME}개 →</a></div>
<ul class="hx-row">{hx_rc}</ul>
<div class="hx-sub2"><a href="/fridge/">🧊 냉장고 재료로 찾기</a><a href="/fridge/solo/">🏠 자취 요리</a><a href="/fridge/weather/">🌤️ 날씨별</a><a href="/fridge/plan/">📅 식단·장보기</a></div></section>

<section class="hx-band" id="join">{join_home()}</section>

<section class="hx-sec hx-t-plaza" id="plaza"><div class="hx-hd"><div><p>🗣️ 줍줍 광장</p><h2>방금 올라온 이야기</h2></div><a href="/plaza/">광장 가기 →</a></div>
<div data-pcrecent="6"></div></section></div>
<link rel="stylesheet" href="/assets/home/consult.css?v=15">'''
    page('/', '루리의 줍줍 — 오늘 뭐 먹지·냉장고 파먹기 레시피, 경품·지원금·공모전',
         f'있는 재료로 찾는 집밥 레시피 {NR_HOME}개와 오늘의 메뉴, 오늘 마감 경품·용돈 이벤트, 지원금·청약 일정, 진행 중 공모전 {len(live)}건까지 생활 정보를 매시간 정리해요.',
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
         f'''<p class="bc"><a href="/">홈</a> › <a href="/apply/">생활</a> › 경품 이벤트</p><h1>🎁 경품 이벤트</h1>{join_cta('event')}
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
    fr_urls = list(fr_urls) + watch_pages()
    app_page()
    news_page()
    extra_urls = talk_pages() + trend_pages() + game_pages(live) + game_extra_pages() + kin_guides() + class_pages() + essay_pages() + kin_answer_pages() + mag_pages(live, aps) + analyst_pages() + satire_pages() + kw_pages() + money_pages() + apply_rec_page() + tool_pages() + hot_pages()
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
    try:
        import make_pdf as _MP
        _pp = [u for u in urls if _MP.is_pdf_path(u) and u not in NOINDEX]
        print('PDF 새로 만듦 %d / 전체 %d' % _MP.make(ROOT, _pp))
    except Exception as e:
        print('PDF 생성 실패(사이트는 계속)', repr(e)[:100])
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
           ('money', ('/analyst/', '/money/')), ('issue', ('/news/', '/talk/', '/mag/', '/kw/', '/hot/', '/satire/', '/review/', '/trend/'))]
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


E2 = lambda t: E(html.unescape(html.unescape(str(t if t is not None else ''))))   # 수집 제목에 &quot; 가 이미 들어 있는 경우


GAME_RX = re.compile(r'게임|e스포츠|이스포츠|esports|해커톤|인디|메타버스|웹툰|VR|XR', re.I)


def game_pages(live):
    """/game/ 게임 허브 (2026-10-20 홍보 세션 기획서): Epic 무료 게임·스팀 할인·인기·출시 예정 + 게임 관련 공모전. 자료는 game.py 가 12시간에 한 번 받아 둔 캐시.
    가격은 스토어 기준 시각을 적고, 이미지는 각 스토어가 공개 API 로 내준 홍보 이미지를 출처와 함께 보여 준다."""
    import game as GM
    d = GM.load()
    ep, st = d.get('epic') or {}, d.get('steam') or {}
    if not ep and not st:
        return []
    won = lambda v: '무료' if not v else f'₩{v:,}'
    img = lambda u, w=232, h=130: f'<img src="{E(u)}" width="{w}" height="{h}" loading="lazy" decoding="async" referrerpolicy="no-referrer" alt="" onerror="this.remove()">' if u else ''
    css = ('<style>.gm-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;list-style:none;padding:0;margin:8px 0}.gm-g li a{display:block;border:1px solid var(--bd,#e5e7eb);border-radius:12px;overflow:hidden;background:var(--card,#fff);color:var(--tx,#111);text-decoration:none;height:100%}'
           '.gm-g img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;background:#e5e7eb}.gm-g b{display:block;padding:8px 10px 2px;font-size:14.5px;line-height:1.35}.gm-g span{display:block;padding:0 10px 10px;font-size:13px;color:var(--mu,#6b7280)}'
           '.gm-g em{font-style:normal;font-weight:800;color:#dc2626}.gm-g s{opacity:.6}.gm-l{padding-left:18px}.gm-l li{margin:4px 0}</style>')
    free = ''.join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">{img(x["img"])}<b>{E(x["name"])}</b><span><s>{E(x["orig"])}</s> <em>무료</em><br>{E(x["start"])} ~ {E(x["end"])} (한국 시간)</span></a></li>' for x in ep.get('free', []))
    upc = ''.join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">{img(x["img"])}<b>{E(x["name"])}</b><span>{E(x["start"])}부터 무료 예정<br>~ {E(x["end"])}</span></a></li>' for x in ep.get('upcoming', []))
    sale = ''.join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">{E(x["name"])}</a> <small><em>{x["off"]}%</em> ↓ {E(x["price"])} <s>{E(x["orig"])}</s> · ~{E(x["end"])}</small></li>' for x in ep.get('sale', []))
    sp = ''.join(f'<li><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">{img(x["img"])}<b>{E(x["name"])}</b><span><em>{x["off"]}%</em> ↓ {won(x["price"])} <s>{won(x["orig"])}</s>{(" · ~" + E(x["until"])) if x["until"] else ""}</span></a></li>' for x in (st.get('specials') or [])[:9])
    tp = ''.join(f'<li><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">{E(x["name"])}</a> <small>{won(x["price"])}{(" · " + str(x["off"]) + "% 할인") if x["off"] else ""}</small></li>' for x in (st.get('top_sellers') or [])[:10])
    cs = ''.join(f'<li><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">{E(x["name"])}</a> <small>{won(x["price"]) if x["price"] else "가격 미정·무료"}</small></li>' for x in (st.get('coming_soon') or [])[:10])
    gc = sorted([c for c in live if GAME_RX.search(c['title'])], key=lambda c: (c['end'], -c.get('pv', 0)))[:12]
    body = (f'<p class="bc"><a href="/">홈</a> › 게임</p><h1>🎮 게임 허브 — 이번 주 무료 게임·스팀 할인·게임 공모전</h1>'
            f'<p class="cat-st">📌 스토어 기준 {E(d.get("at", ""))}(한국 시간)에 받은 정보예요. 가격·할인은 바뀔 수 있으니 결제 전 스토어에서 확인하세요. 출처: Epic Games Store, Steam.</p>'
            '<p class="hm-chips"><a href="/game/free/">🎁 에픽 무료 게임 기록</a><a href="/game/release/">🗓️ 신작 출시 일정</a><a href="/game/steam-sale/">📅 스팀 세일 달력</a><a href="/game/refund/">↩️ 스팀 환불 규정</a><a href="/game/battlefield-6-editions/">🔫 배틀필드6 에디션 비교</a><a href="#timing">🕰️ 살 타이밍</a></p>'
            f'<h2 id="free">🎁 지금 무료로 받는 게임 (Epic Games Store)</h2>' + (f'<ul class="gm-g">{free}</ul>' if free else '<p class="note">지금 무료로 풀린 게임이 없어요.</p>')
            + (f'<h3>⏭️ 다음 무료 예고</h3><ul class="gm-g">{upc}</ul>' if upc else '')
            + (f'<h3>💸 에픽 할인 중</h3><ul class="gm-l">{sale}</ul>' if sale else '')
            + f'<h2 id="steam">🔥 스팀 할인 TOP</h2>' + (f'<ul class="gm-g">{sp}</ul>' if sp else '<p class="note">지금 불러온 할인 정보가 없어요.</p>')
            + game_timing(st, d.get('events') or {})
            + (f'<h2>🏆 스팀 인기 게임</h2><ol class="gm-l">{tp}</ol>' if tp else '') + (f'<h2>🗓️ 곧 나오는 게임</h2><ul class="gm-l">{cs}</ul>' if cs else '')
            + cp_box('게임 게이밍 PC', '게임할 때 많이 찾는 물건:', 2, strict=True) + join_cta('game')
            + f'<h2 id="contest">🏆 게임·e스포츠·해커톤 공모전 (진행 중 {len(gc)}건)</h2>' + (f'<ul class="list">{"".join(card(c) for c in gc)}</ul>' if gc else '<p class="note">지금 진행 중인 게임 관련 공모전이 없어요.</p>')
            + '<p class="note">이미지와 가격은 각 스토어가 공개한 정보를 하루 두 번 받아 보여 줘요. 줍줍은 스토어와 무관하고, 게임 구매를 권하지 않아요. 소통은 오픈채팅에서 해요.</p>'
            '<p class="hm-links"><a href="/contest/">전체 공모전</a> · <a href="/event/">🎁 경품·용돈</a></p>' + css)
    page('/game/', '게임 허브 — 이번 주 에픽 무료 게임·스팀 할인 TOP·게임 공모전 (매일 갱신)', f'Epic 무료 게임 {len(ep.get("free", []))}개와 스팀 할인·인기·출시 예정, 진행 중인 게임·e스포츠·해커톤 공모전 {len(gc)}건을 한곳에. 스토어 기준 시각을 적어요.',
         body, [('루리의 줍줍', '/'), ('게임', '/game/')])
    return ['/game/']


JN_TOPICS = {   # 2026-10-20 사용자 「그 사람이 듣고 싶은 정보를 회원가입하면 보내 주는 서비스」「가입 유도」: 키 → (아이콘, 제목, 보내는 때)
    'recipe': ('🍳', '오늘 뭐 먹지, 아침마다 알려 드려요', '매일 아침 · 이메일'),
    'apply': ('💰', '새 지원금·마감 임박 청약을 놓치지 않게', '새 공고와 마감 3일 전 · 이메일'),
    'contest': ('🏆', '마감 임박 공모전을 놓치지 않게', '마감 3일 전 · 이메일'),
    'issue': ('📺', '루리 뉴스 브리핑을 메일로', '매일 아침 · 이메일'),
    'game': ('🎮', '이번 주 무료 게임·스팀 할인을 먼저', '새 무료 게임이 풀릴 때 · 이메일'),
    'money': ('📊', '전문가 말 vs 시세 요약을 메일로', '매일 아침 · 이메일'),
    'event': ('🎁', '오늘 마감 경품·용돈을 놓치지 않게', '매일 아침 · 이메일')}
_JNP = {}


def jn_preview(t):
    """가입하면 받을 소식의 맛보기 한 줄 — 지금 사이트 자료로(없으면 빈 문자열)."""
    if t in _JNP:
        return _JNP[t]
    out = ''
    try:
        td = datetime.date.today()
        if t == 'recipe':
            pk = (_rd('assets/fridge/today.json') or {}).get('picks') or []
            out = ('오늘의 메뉴: ' + ', '.join(pk[:3])) if pk else ''
        elif t == 'apply':
            L = [a for a in (_rd('apply.json') or []) if a.get('end') and not a.get('always') and 0 <= (datetime.date.fromisoformat(a['end']) - td).days <= 7]
            out = f'지금 7일 안에 마감하는 지원금·청약 {len(L)}건' if L else ''
        elif t == 'contest':
            L = [c for c in ((_rd('data.json') or {}).get('items') or []) if c.get('end') and 0 <= (datetime.date.fromisoformat(c['end']) - td).days <= 7]
            out = f'7일 안에 마감하는 공모전 {len(L)}건' if L else ''
        elif t == 'issue':
            it = (_rd('news/brief.json') or {}).get('items') or []
            out = f'오늘 브리핑 {len(it)}가지: ' + html.unescape(html.unescape(it[0]['headline']))[:22] + '…' if it else ''
        elif t == 'game':
            fr = ((_rd('_gongmo/game_cache.json') or {}).get('epic') or {}).get('free') or []
            out = '지금 Epic 무료: ' + ', '.join(x['name'] for x in fr[:2]) if fr else ''
        elif t == 'money':
            n = ((_rd('analyst/data.json') or {}).get('exp_meta') or {}).get('n24')
            out = f'최근 24시간 전문가 발언 {n}건을 시세와 함께' if n else ''
        elif t == 'event':
            n = len([e for e in (_rd('events.json') or []) if e.get('end', '') >= td.isoformat()])
            out = f'지금 응모할 수 있는 경품·이벤트 {n}건' if n else ''
    except Exception:
        out = ''
    _JNP[t] = out
    return out


def join_cta(t):
    """가입 유도 카드 한 장(페이지당 하나, 팝업 없음). 누르면 가입 창 → 그 주제를 메일로 받기(assets/join/join.js)."""
    if t not in JN_TOPICS:
        return ''
    ic, ti, when = JN_TOPICS[t]
    pv = jn_preview(t)
    return (f'<aside class="jn" data-t="{t}"><div><b>📬 {ic} {E(ti)}</b>' + (f'<p>{E(pv)}</p>' if pv else '') + f'<small>{E(when)} · 가입 무료 · 언제든 끌 수 있어요</small></div>'
            '<button class="jn-b" type="button">무료로 받기</button></aside><link rel="stylesheet" href="/assets/join/join.css?v=1"><script defer src="/assets/join/join.js?v=1"></script>')


def join_home():
    """홈: 주제를 골라 받는 입구(눌러서 /me/ 의 소식 설정으로)."""
    chips = ''.join(f'<a href="/me/?t={k}#topics">{ic} {E(ti.split(",")[0][:14])}</a>' for k, (ic, ti, _) in JN_TOPICS.items())
    return ('<section class="hm-sec jn-home"><h2>📬 원하는 소식만 골라 받기</h2><p class="kwn">가입하면 고른 주제의 새 소식을 메일로 보내 드려요. 마감 임박·새 공고·무료 게임·오늘의 메뉴까지, 끄는 것도 한 번에.</p>'
            f'<p class="hm-chips">{chips}</p></section><link rel="stylesheet" href="/assets/join/join.css?v=1">')


def _gd(x):
    return datetime.date.fromisoformat(x) if x else None


def _gr(a, b):
    return f'{a[5:7].lstrip("0")}/{a[8:].lstrip("0")}' + (f'~{b[5:7].lstrip("0")}/{b[8:].lstrip("0")}' if b else '')


def game_timing(st, ev):
    """스팀 할인 TOP 아래 「살 타이밍」: 현재 할인율 + 줍줍이 기록한 최저가(공개 API 에 가격 이력이 없어 기록 시작일부터) + 다음 시즌 세일."""
    hf = os.path.join(HERE, 'game_hist.json')
    H = json.load(open(hf, encoding='utf-8')) if os.path.exists(hf) else {'steam': {}, 'since': ''}
    won = lambda v: f'₩{v:,}'
    rows = ''
    for x in (st.get('specials') or [])[:9]:
        pts = (H['steam'].get(str(x['id'])) or {}).get('pts') or []
        low = min((q[1] for q in pts), default=None)
        n = len(pts)
        if n >= 2 and low is not None:
            note = '🟢 기록상 최저가와 같아요' if x['price'] <= low else f'기록 최저 {won(low)}({n}일 기록)'
        else:
            note = '기록 시작 — 내일부터 비교돼요'
        rows += (f'<tr><td><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">{E(x["name"])}</a></td><td>{x["off"]}% ↓ <b>{won(x["price"])}</b><br><small><s>{won(x["orig"])}</s></small></td>'
                 f'<td>{note}</td><td>{E(x["until"] or "-")}</td></tr>')
    if not rows:
        return ''
    td = datetime.date.today()
    nxt = next((e for e in (ev.get('seasonal') or []) if e.get('start') and _gd(e['start']) >= td), None)
    nl = f'<li>다음 시즌 세일: <b>{E(nxt["name"])}</b> {E(_gr(nxt["start"], nxt["end"]))} (D-{(_gd(nxt["start"]) - td).days}) — <a href="/game/steam-sale/">세일 달력 보기</a></li>' if nxt else ''
    return ('<h2 id="timing">🕰️ 지금 사도 될까? 살 타이밍</h2>'
            f'<p class="kwn">스팀의 공개 정보에는 역대 최저가 기록이 없어요. 그래서 줍줍이 {E(H.get("since", ""))}부터 매일 받아 둔 가격 중 가장 낮은 값과 비교해요(기록이 짧을수록 참고만 하세요).</p>'
            f'<div class="tblw"><table class="xb"><thead><tr><th>게임</th><th>지금 가격</th><th>줍줍 기록</th><th>할인 종료</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<ul class="gm-l">' + nl + '<li>구매한 게임이 다음 날 더 싸졌다면 환불 후 다시 사도 스팀은 악용으로 보지 않는다고 공식 안내에 적혀 있어요 — <a href="/game/refund/">환불 규정</a></li>'
            '<li>역대 최저가가 궁금하면 <a href="https://steamdb.info/" target="_blank" rel="noopener nofollow">SteamDB</a> 같은 가격 추적 사이트에서 게임별로 확인하세요(줍줍이 가져오지는 않아요).</li></ul>'
            '<style>.tblw{overflow-x:auto}.xb{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}.xb th,.xb td{border-bottom:1px solid var(--bd,#e5e7eb);padding:6px;text-align:left;vertical-align:top}</style>')


def _faq(items):
    ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', a)}} for q, a in items]}
    return ''.join(f'<details class="faq-i"><summary>{E(q)}</summary><div>{a}</div></details>' for q, a in items), ld


GAME_CSS = ('<style>.faq-i{border:1px solid var(--bd,#e5e7eb);border-radius:12px;padding:10px 14px;margin:8px 0;background:var(--card,#fff)}.faq-i summary{font-weight:700;cursor:pointer}.faq-i div{margin-top:8px;line-height:1.7;font-size:14.5px}'
            '.tblw{overflow-x:auto}.xb{border-collapse:collapse;width:100%;font-size:14px;min-width:0}.xb th,.xb td{border-bottom:1px solid var(--bd,#e5e7eb);padding:7px 6px;text-align:left;vertical-align:top}'
            '.gm-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;list-style:none;padding:0;margin:8px 0}.gm-g li a{display:block;border:1px solid var(--bd,#e5e7eb);border-radius:12px;overflow:hidden;background:var(--card,#fff);color:var(--tx,#111);text-decoration:none;height:100%}'
            '.gm-g img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;background:#e5e7eb}.gm-g b{display:block;padding:8px 10px 2px;font-size:14.5px}.gm-g span{display:block;padding:0 10px 10px;font-size:13px;color:var(--mu,#6b7280)}.gm-g em{font-style:normal;font-weight:800;color:#dc2626}.gm-g s{opacity:.6}</style>')


def game_extra_pages():
    """2026-10-20 홍보 세션(지식iN 질문): 스팀 세일 달력 · 스팀 환불 규정 · 에픽 무료 게임 기록. 사실은 스팀 공식 페이지(환불·Steamworks 일정 문서)에서 확인한 것만."""
    import game as GM
    d = GM.load()
    ev, ep = d.get('events') or {}, d.get('epic') or {}
    td = datetime.date.today()
    urls = []
    # ---- 스팀 시즌 세일 달력
    if ev.get('seasonal'):
        def st_(a):
            if not a.get('start'):
                return '날짜 미정 (공식 문서에 TBD)'
            return f'{_gr(a["start"], a["end"])} · ' + (f'D-{(_gd(a["start"]) - td).days}' if _gd(a['start']) > td else ('진행 중' if td <= _gd(a['end']) else '종료'))
        rows = ''.join(f'<tr><td>{E(a["name"])}</td><td>{E(a["start"] or "-")} ~ {E(a["end"] or "-")}</td><td>{E(st_(a))}</td></tr>' for a in ev['seasonal'])
        rows += '<tr><td>Autumn Sale 2026 <small>(지난 시즌)</small></td><td>2026-10-01 ~ 2026-10-08</td><td>종료 · SteamDB 표기(공식 일정 문서에는 지난 일정이 없어서 줍줍 홍보팀이 확인)</td></tr>'
        fr = ''.join(f'<tr><td>{E(a["name"])}</td><td>{E(a["start"])} ~ {E(a["end"])}</td><td>{("D-" + str((_gd(a["start"]) - td).days)) if _gd(a["start"]) > td else ("진행 중" if td <= _gd(a["end"]) else "종료")}</td></tr>' for a in (ev.get('fests') or []) + (ev.get('nextfest') or []) if _gd(a['end']) >= td)
        nxt = next((a for a in ev['seasonal'] if a.get('start') and _gd(a['start']) >= td), None)
        faq, ld = _faq([('스팀 세일은 1년에 몇 번 하나요?', '시즌 세일은 스팀 전체가 참여하는 큰 세일로, 공식 문서에 「1년에 4번」(겨울·봄·여름·가을)으로 적혀 있어요. 그 밖에 장르별 테마 페스티벌과 Next Fest(체험판 행사)가 따로 열려요.'),
                        ('다음 스팀 세일은 언제예요?', (f'공식 일정 문서 기준으로 다음 시즌 세일은 {nxt["name"]}({_gr(nxt["start"], nxt["end"])}, 지금부터 {(_gd(nxt["start"]) - td).days}일 뒤)예요.' if nxt else '공식 일정 문서에 아직 다음 날짜가 없어요.')),
                        ('블랙프라이데이에도 스팀 세일을 하나요?', '2026년 스팀 가을 세일은 SteamDB 에 10월 1일~8일로 표기돼 있어 이미 끝났어요(공식 일정 문서에는 지난 일정이 실리지 않아요). 지금 공식 문서에 예정된 다음 시즌 세일은 겨울 세일이에요. 블랙프라이데이(2026년은 11월 27일)에 스팀이 따로 큰 세일을 한다는 공식 일정은 문서에 없어요.'),
                        ('스팀 마블 스파이더맨2 같은 게임은 할인을 또 언제 하나요?', '특정 게임이 언제 또 할인할지는 줍줍이 알 수 없어요. 할인 여부와 폭은 게임사가 정하고, 다음 큰 할인 기회는 <a href="/game/steam-sale/">시즌 세일 달력</a>에서 확인할 수 있어요. 게임별 가격 이력은 SteamDB 같은 추적 사이트에서 볼 수 있고, <a href="/game/#timing">살 타이밍</a>에는 줍줍이 기록한 가격이 쌓여요.'),
                        ('스듀(스타듀 밸리)처럼 지금 살까 기다릴까 고민될 때는요?', '급하지 않다면 다음 시즌 세일까지 기다리는 선택지가 있어요. 다만 할인 보장은 없고, 먼저 산 뒤 14일·2시간 안이면 환불할 수 있어요(<a href="/game/refund/">환불 규정</a>). 게임별 가격은 스팀 상점에서 확인하세요.'),
                        ('스팀 세일 때까지 기다려야 하나요?', (f'급하지 않다면 다음 시즌 세일({nxt["name"]}, {_gr(nxt["start"], nxt["end"])})까지 기다리는 선택지가 있어요. 다만 할인 여부와 폭은 게임사가 정해서 이전과 같다는 보장은 없어요. 사고 나서 다음 날 더 싸졌다면 환불 후 재구매해도 악용이 아니라는 공식 문장이 있어요(<a href="/game/refund/">환불 규정</a>).' if nxt else '다음 세일 날짜가 공식 문서에 나오면 이 표에 들어와요.')),
                        ('세일 때 산 게임을 환불할 수 있나요?', '구매 후 14일 이내이고 플레이 시간이 2시간 미만이면 요청할 수 있어요. 자세한 조건은 <a href="/game/refund/">스팀 환불 규정</a>에 정리했어요.')])
        body = ('<p class="bc"><a href="/">홈</a> › <a href="/game/">게임</a> › 스팀 세일 달력</p><h1>📅 스팀 세일 언제 하나요? 시즌 세일 달력</h1>'
                + (f'<p class="cat-st">📌 다음 시즌 세일은 <b>{E(nxt["name"])}</b>, {E(_gr(nxt["start"], nxt["end"]))} (D-{(_gd(nxt["start"]) - td).days})예요.</p>' if nxt else '')
                + '<h2>시즌 세일 (스팀 공식 일정)</h2><div class="tblw"><table class="xb"><thead><tr><th>세일</th><th>기간</th><th>상태</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
                + '<p class="kwn">출처: Steamworks 문서 「Upcoming Steam Events」(공식)와 SteamDB(지난 시즌 한 줄). 시즌 세일은 해마다 4번이고, 날짜가 TBD 인 곳은 공식 발표 전이에요. 최종 일정은 스팀 공지로 확인하세요. 지난 시즌 날짜는 <a href="https://store.steampowered.com/news/" target="_blank" rel="noopener nofollow">스팀 공식 뉴스</a>에서 확인하세요.</p>'
                + ('<h2>테마 페스티벌·Next Fest (앞으로 열리는 것)</h2><div class="tblw"><table class="xb"><thead><tr><th>행사</th><th>기간</th><th>상태</th></tr></thead><tbody>' + fr + '</tbody></table></div>'
                   '<p class="kwn">테마 페스티벌은 특정 장르 게임을 모아 홍보하는 행사이고 할인 게임이 우선이에요. Next Fest 는 출시 전 게임의 체험판을 해 보는 행사예요(공식 설명 기준).</p>' if fr else '')
                + '<h2>자주 묻는 질문</h2>' + faq + cp_box('게임 게이밍 PC', '게임할 때 많이 찾는 물건:', 2, strict=True) + join_cta('game') + _cite_box({'basis': f'확인일 {td.isoformat()}', 'sources': [('Steamworks 「Upcoming Steam Events」', ''), ('SteamDB', '')], 'sections': [{'table': 1}]}, '/game/steam-sale/')
                + f'<p class="hm-links"><a href="/game/">🎮 게임 허브</a> · <a href="/game/refund/">↩️ 스팀 환불 규정</a> · <a href="/game/free/">🎁 에픽 무료 게임 기록</a></p>' + GAME_CSS)
        page('/game/steam-sale/', f'스팀 세일 언제 하나요? 시즌 세일 달력 {td.year}~{td.year + 1} (겨울·봄·여름·가을, Next Fest)', '스팀 시즌 세일과 테마 페스티벌, Next Fest 일정을 스팀 공식 일정 문서 기준으로 정리했어요. 다음 세일까지 며칠 남았는지도 매일 갱신해요.',
             body, [('루리의 줍줍', '/'), ('게임', '/game/'), ('스팀 세일 달력', '/game/steam-sale/')], ld)
        urls.append('/game/steam-sale/')
    # ---- 신작 출시 일정 (스팀 인기 출시 예정 중 날짜가 확정된 것만)
    rel = sorted([x for x in (d.get('release') or []) if x['date'] >= td.isoformat()][:40], key=lambda x: (x['date'], x['name']))   # 인기순 상위 40개를 날짜순으로
    if rel:
        wd = '월화수목금토일'
        by = {}
        for x in rel[:60]:
            by.setdefault(x['date'], []).append(x)
        secs = ''.join(f'<h3>{int(k[5:7])}월 {int(k[8:])}일({wd[_gd(k).weekday()]}) <small>D-{(_gd(k) - td).days}</small></h3><ul class="gm-g">' + ''.join(
            f'<li><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">' + (f'<img src="{E(x["img"])}" width="232" height="87" loading="lazy" decoding="async" referrerpolicy="no-referrer" alt="" onerror="this.remove()">' if x['img'] else '')
            + f'<b>{E(x["name"])}</b><span>스팀 출시 예정</span></a></li>' for x in v) + '</ul>' for k, v in by.items())
        faq, ld = _faq([('이번 주 신작 게임 뭐 나와요?', ', '.join(x['name'] for x in rel[:5]) + ' 등이 스팀에서 출시일이 정해져 있어요. 전체는 위 목록을 보세요.'),
                        ('출시일이 안 정해진 게임은요?', '스팀에 「2026년 10월」「2026년」처럼 날짜가 흐리게 적힌 게임은 일부러 뺐어요. 날짜가 정해지면 이 목록에 자동으로 들어와요.'),
                        ('에픽 게임즈 스토어 출시 일정도 있나요?', '에픽은 출시 예정작 날짜를 공개 자료로 내주지 않아서 이 페이지에는 스팀만 있어요. 에픽은 매주 바뀌는 무료 게임 예고를 <a href="/game/free/">무료 게임 기록</a>에 정리해요.')])
        body = ('<p class="bc"><a href="/">홈</a> › <a href="/game/">게임</a> › 신작 출시 일정</p><h1>🗓️ 신작 게임 출시 일정 — 스팀 출시일이 정해진 게임</h1>'
                f'<p class="cat-st">📌 스토어 기준 {E(d.get("at", ""))}(한국 시간). 스팀 「인기 출시 예정」 중 출시일이 날짜까지 정해진 {len(rel)}개 가운데 가까운 순으로 보여 줘요. 추측한 날짜는 넣지 않았어요.</p>'
                + secs + '<h2>자주 묻는 질문</h2>' + faq + cp_box('게임 게이밍 PC', '게임할 때 많이 찾는 물건:', 2, strict=True) + join_cta('game')
                + '<p class="note">출처: Steam 스토어 공개 검색 정보. 출시일은 개발사 사정으로 바뀔 수 있어요. 줍줍은 Valve와 무관해요.</p>'
                '<p class="hm-links"><a href="/game/">🎮 게임 허브</a> · <a href="/game/free/">🎁 에픽 무료 게임 기록</a> · <a href="/game/steam-sale/">📅 스팀 세일 달력</a></p>' + GAME_CSS)
        page('/game/release/', '신작 게임 출시 일정 — 스팀 출시일이 정해진 게임 (이번 주·이번 달)', f'스팀 인기 출시 예정 게임 중 출시일이 날짜까지 정해진 {len(rel)}개를 가까운 순으로 모았어요. 추측한 날짜는 넣지 않아요.',
             body, [('루리의 줍줍', '/'), ('게임', '/game/'), ('신작 출시 일정', '/game/release/')], ld)
        urls.append('/game/release/')
    # ---- 영어: 신작 출시 일정 (글로벌 유입용, 홍보 요청 2026-10-20)
    if rel:
        wd_en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        mo = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        by_en = {}
        for x in rel:
            by_en.setdefault(x['date'], []).append(x)
        secs_en = ''.join(f'<h3>{mo[int(k[5:7]) - 1]} {int(k[8:])} ({wd_en[_gd(k).weekday()]}) <small>in {(_gd(k) - td).days} days</small></h3><ul class="gm-g">' + ''.join(
            f'<li><a href="https://store.steampowered.com/app/{x["id"]}/" target="_blank" rel="noopener nofollow">' + (f'<img src="{E(x["img"])}" width="232" height="87" loading="lazy" decoding="async" referrerpolicy="no-referrer" alt="" onerror="this.remove()">' if x['img'] else '')
            + f'<b>{E(x["name"])}</b><span>Steam, coming soon</span></a></li>' for x in v) + '</ul>' for k, v in by_en.items())
        faq_en, ld_en = _faq([('What games are coming out this week?', ', '.join(x['name'] for x in rel[:5]) + ' are among the popular upcoming Steam games with a confirmed release day. See the full list above.'),
                              ('Why are some games missing?', 'Games whose Steam page only says a month or a year (for example "October 2026" or "2026") are left out on purpose. They appear here automatically once a day is confirmed.'),
                              ('What about Epic Games Store releases?', 'Epic does not publish upcoming release dates in a public feed, so this page covers Steam only. Free Epic games are tracked on the Korean page <a href="/game/free/">/game/free/</a>.')])
        body_en = ('<p class="bc"><a href="/">Home</a> › <a href="/en/guide/">Guides</a> › New game releases</p><h1>New game releases on Steam: confirmed release dates</h1>'
                   f'<p class="cat-st">📌 Updated {E(d.get("at", ""))} (Korea time). Popular upcoming Steam games whose release date is confirmed to the day, shown by date. We do not guess dates ({len(rel)} games).</p>'
                   + secs_en + '<h2>Frequently asked questions</h2>' + faq_en + '<p class="note">Source: Steam store public search data. Release dates can change. Ruri Jupjup is not affiliated with Valve.</p>'
                   '<p class="hm-links"><a href="/en/guide/">All English guides</a> · <a href="/game/release/">한국어 버전</a></p>' + GAME_CSS)
        page('/en/guide/new-game-releases-steam/', 'New Game Releases on Steam: Confirmed Release Dates This Week and Month | Ruri Jupjup', f'Popular upcoming Steam games with a confirmed release day, listed by date ({len(rel)} games). We never guess dates; updated several times a day.',
             body_en, [('Home', '/'), ('Guides', '/en/guide/'), ('New game releases', '/en/guide/new-game-releases-steam/')], ld_en, full_title=True, lang='en')
        urls.append('/en/guide/new-game-releases-steam/')
    # ---- 스팀 환불 규정 (스팀 공식 환불 페이지 2024-04-23 수정본 확인)
    rows = [('게임·소프트웨어', '구매 후 14일 이내 + 플레이 시간 2시간 미만이면 이유와 상관없이 요청 가능'), ('DLC', '구매 후 14일 이내 + DLC 구매 후 게임 플레이 2시간 미만 + DLC를 사용·변경·거래하지 않았을 때(일부 서드파티 DLC는 환불 불가, 상점 페이지에 표시)'),
            ('게임 내 구매', 'Valve 게임은 구매 후 48시간 이내 + 아이템을 쓰지 않았을 때. 서드파티 게임은 개발자가 환불을 켜 둔 경우만(구매 전 표시)'), ('출시 전 구매(예약 구매)', '출시 전에는 언제든 요청 가능. 14일·2시간 기준은 출시일부터 적용. 앞서 해보기는 플레이 시간이 모두 2시간에 포함'),
            ('꾸러미(번들)', '꾸러미에 든 아이템을 거래하지 않았고 전체 플레이 시간이 2시간 미만이면 환불 가능. 환불 불가한 게임 내 아이템·DLC가 들어 있으면 꾸러미는 환불 불가(구매 과정에서 알려 줘요)'),
            ('스팀 하드웨어', '스팀 하드웨어는 별도의 하드웨어 환불 정책을 따라요'),
            ('스팀 지갑', '충전한 금액을 쓰지 않았다면 구매 후 14일 이내'), ('정기 구독', '결제(자동 갱신 포함) 후 48시간 이내 + 그 기간 구독 혜택을 쓰지 않았을 때'), ('선물', '수락 전에는 14일·2시간 기준으로 환불(비용은 구매한 사람에게). 수락한 선물은 받은 사람이 같은 기간 안에 요청'),
            ('스팀 밖에서 산 키', '환불 불가(타사에서 산 CD키·지갑 코드)'), ('VAC 차단', '그 게임에서 VAC 차단되면 그 게임의 환불 권리를 잃어요'), ('동영상 콘텐츠', '영화·시리즈·튜토리얼 등은 환불 불가(환불되는 제품과 묶인 꾸러미는 제외)')]
    tr = ''.join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td></tr>' for a, b in rows)
    faq, ld = _faq([('스팀 환불은 몇 시간까지 되나요?', '게임은 구매 후 14일 이내이고 플레이 시간이 2시간 미만이어야 해요. 규칙에 안 맞아도 일단 요청하면 확인해 준다고 공식 안내에 적혀 있어요.'),
                    ('환불은 어디서 요청하나요? 결제 오류도 거기로 문의하나요?', '<a href="https://help.steampowered.com/" target="_blank" rel="noopener nofollow">help.steampowered.com</a> 에서 환불 요청과 다른 도움(결제 문의 포함)을 받을 수 있어요.'),
                    ('환불금은 언제 어디로 들어오나요?', '요청이 확인된 뒤 1주 안에, 스팀 지갑 또는 구매에 쓴 결제 수단으로 전액 환불돼요. 결제 수단이 환불을 지원하지 않으면 스팀 지갑으로 들어와요.'),
                    ('다음 날 더 싸졌는데 환불하고 다시 사도 되나요?', '공식 안내에 「구매한 제품이 바로 다음 날 더 저렴한 가격으로 판매되고 있어서 환불 후 다시 구매하는 것은 악용으로 판단하지 않는다」고 적혀 있어요. 다만 환불을 무료 플레이 용도로 쓰면 환불 기능이 막힐 수 있어요.'),
                    ('스팀 환불 신청 방법은요?', '<a href="https://help.steampowered.com/" target="_blank" rel="noopener nofollow">help.steampowered.com</a> 에서 요청한다고 스팀 공식 환불 안내에 나와 있어요. 구매 후 14일 이내·게임 플레이 2시간 미만인지 먼저 확인하세요.'),
                    ('스팀 결제가 두 번 됐을 때는요?', '결제 문제도 <a href="https://help.steampowered.com/" target="_blank" rel="noopener nofollow">help.steampowered.com</a> 에서 도움을 받을 수 있다고 공식 안내에 나와 있어요. 줍줍은 개별 결제 내역을 볼 수 없어서, 출금 내역은 카드사·은행에서도 함께 확인하세요.'),
                    ('에픽·콘솔(플레이스테이션·엑스박스·닌텐도) 환불도 같나요?', '플랫폼마다 조건이 달라요. 줍줍은 스팀 공식 안내를 직접 확인한 내용만 적었고, 다른 플랫폼은 아래 공식 고객지원에서 확인하세요.')])
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/game/">게임</a> › 스팀 환불 규정</p><h1>↩️ 스팀 게임 환불 되나요? 환불 규정 (구매 후 14일·플레이 2시간)</h1>'
            '<p class="cat-st">📌 스팀은 구매 후 <b>14일 이내</b>, 게임 플레이 <b>2시간 미만</b>이면 이유와 상관없이 환불을 요청할 수 있어요. 요청은 <a href="https://help.steampowered.com/" target="_blank" rel="noopener nofollow">help.steampowered.com</a>에서 해요.</p>'
            '<h2>구매 종류별 환불 조건</h2><div class="tblw"><table class="xb"><thead><tr><th>구매 종류</th><th>조건</th></tr></thead><tbody>' + tr + '</tbody></table></div>'
            '<h2>환불 요청 방법과 받는 시기</h2><ul class="gm-l"><li>help.steampowered.com 에서 요청해요. 결제 오류 같은 다른 문의도 같은 곳이에요.</li><li>확인된 뒤 <b>1주 안</b>에 스팀 지갑 또는 구매에 쓴 결제 수단으로 전액 환불돼요.</li><li>규칙 밖이어도 요청하면 살펴본다고 공식 안내에 적혀 있고, 일부 지역은 게임에 결함이 있을 때 추가 권리가 있을 수 있어요.</li><li>환불 기능을 무료 플레이용으로 악용하면 막힐 수 있어요.</li></ul>'
            '<h2>스팀 말고 다른 플랫폼은?</h2><p>에픽·콘솔은 조건이 서로 달라서 줍줍이 확인하지 못한 숫자는 적지 않았어요. 아래 공식 고객지원에서 확인하세요: '
            '<a href="https://www.epicgames.com/help/ko" target="_blank" rel="noopener nofollow">에픽게임즈</a> · <a href="https://www.playstation.com/ko-kr/support/" target="_blank" rel="noopener nofollow">플레이스테이션</a> · <a href="https://support.xbox.com/ko-KR" target="_blank" rel="noopener nofollow">엑스박스</a> · <a href="https://www.nintendo.co.kr/" target="_blank" rel="noopener nofollow">닌텐도</a></p>'
            '<h2>자주 묻는 질문</h2>' + faq + cp_box('게임 게이밍 PC', '게임할 때 많이 찾는 물건:', 2, strict=True)
            + '<p class="note">출처: <a href="https://store.steampowered.com/steam_refunds/?l=koreana" target="_blank" rel="noopener nofollow">Steam 환불 공식 안내</a>(수정 2024년 4월 23일본, 줍줍 확인 2026-10-20). 규정은 바뀔 수 있으니 결제 전 공식 안내를 확인하세요. 법률 상담이 아니에요.</p>'
            '<p class="hm-links"><a href="/game/">🎮 게임 허브</a> · <a href="/game/steam-sale/">📅 스팀 세일 달력</a> · <a href="/game/free/">🎁 에픽 무료 게임 기록</a></p>' + GAME_CSS)
    page('/game/refund/', '스팀 환불 규정 — 구매 후 14일·플레이 2시간, 환불 요청 방법과 예외 (DLC·선물·지갑)', '스팀 게임 환불 조건을 공식 안내 기준으로 정리했어요. 14일·2시간 기준, 환불 요청 경로, DLC·게임 내 구매·예약 구매·선물·지갑 예외, 환불금이 들어오는 시기.',
         body, [('루리의 줍줍', '/'), ('게임', '/game/'), ('스팀 환불 규정', '/game/refund/')], ld)
    urls.append('/game/refund/')
    # ---- 에픽 무료 게임 기록
    hf = os.path.join(HERE, 'game_hist.json')
    H = json.load(open(hf, encoding='utf-8')) if os.path.exists(hf) else {'free': [], 'since': ''}
    nowk = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M')
    card_ = lambda x, lab: (f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener nofollow">' + (f'<img src="{E(x["img"])}" width="232" height="130" loading="lazy" decoding="async" referrerpolicy="no-referrer" alt="" onerror="this.remove()">' if x.get('img') else '')
                            + f'<b>{E(x["name"])}</b><span>{lab}<br>{E(x["start"])} ~ {E(x["end"])} (한국 시간)</span></a></li>')
    cur = ''.join(card_(x, f'<s>{E(x["orig"])}</s> <em>무료</em>') for x in ep.get('free', []))
    nxt_ = ''.join(card_(x, '무료 예정') for x in ep.get('upcoming', []))
    past = sorted([g for g in H.get('free', []) if g['end'] < nowk or (g['start'] < nowk and g['end'] < nowk)], key=lambda g: g['start'], reverse=True)
    pl = ''.join(f'<li><a href="{E(g["url"])}" target="_blank" rel="noopener nofollow">{E(g["name"])}</a> <small>{E(g["start"])} ~ {E(g["end"])} · 정가 {E(g["orig"])}</small></li>' for g in H.get('free', []) if g['end'] <= nowk)
    fr0 = (ep.get('free') or [None])[0]
    wk = ''
    if fr0:
        try:
            sd = datetime.datetime.strptime(f'{td.year}/{fr0["start"]}', '%Y/%m/%d %H:%M')
            wk = f'지금 무료 기간은 {E(fr0["start"])}(한국 시간)에 시작해 {E(fr0["end"])}에 끝나요. 새 무료 게임은 보통 이 시각에 바뀌어요.'
        except Exception:
            wk = ''
    faq, ld = _faq([('이번 주 에픽 무료 게임은 뭐예요?', ', '.join(x['name'] for x in ep.get('free', [])) + f' (~{ep["free"][0]["end"]} 한국 시간까지)' if ep.get('free') else '지금 무료로 풀린 게임이 없어요.'),
                    ('다음 무료 게임은 뭐예요?', (', '.join(f'{x["name"]}({x["start"]}부터)' for x in ep.get('upcoming', [])) + ' — 에픽이 미리 공개한 예고예요.') if ep.get('upcoming') else '아직 공개된 예고가 없어요.'),
                    ('지난 무료 게임 목록은 어디서 보나요?', f'이 페이지에 줍줍이 확인한 무료 게임을 {E(H.get("since", ""))}부터 쌓고 있어요. 에픽 공개 자료에는 지난 목록이 없어서 그 이전 기록은 없어요. 공식 무료 게임 페이지는 <a href="https://store.epicgames.com/ko/free-games" target="_blank" rel="noopener nofollow">여기</a>예요.')])
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/game/">게임</a> › 에픽 무료 게임</p><h1>🎁 에픽게임즈 무료 게임 뭐 있나요? 이번 주·다음 예고·지난 기록</h1>'
            f'<p class="cat-st">📌 스토어 기준 {E(d.get("at", ""))}(한국 시간). {wk}</p><h2>지금 무료</h2>' + (f'<ul class="gm-g">{cur}</ul>' if cur else '<p class="note">지금 무료로 풀린 게임이 없어요.</p>')
            + (f'<h2>다음 무료 예고</h2><ul class="gm-g">{nxt_}</ul>' if nxt_ else '') + f'<h2>지난 무료 게임 기록 <small>({E(H.get("since", ""))}부터)</small></h2>'
            + (f'<ul class="gm-l">{pl}</ul>' if pl else '<p class="note">아직 지난 기록이 없어요. 줍줍이 확인한 무료 게임이 끝나면 여기 쌓여요. 에픽이 공개한 자료에는 지난 목록이 없어서 그 이전 기록은 만들 수 없어요.</p>')
            + '<h2>자주 묻는 질문</h2>' + faq + cp_box('게임 게이밍 PC', '게임할 때 많이 찾는 물건:', 2, strict=True) + join_cta('game')
            + '<p class="note">출처: Epic Games Store 공개 프로모션 자료. 줍줍은 에픽게임즈와 무관해요. 이미지는 에픽이 공개한 홍보 이미지예요.</p>'
            '<p class="hm-links"><a href="/game/">🎮 게임 허브</a> · <a href="/game/steam-sale/">📅 스팀 세일 달력</a> · <a href="/game/refund/">↩️ 스팀 환불 규정</a></p>' + GAME_CSS)
    page('/game/free/', '에픽 무료 게임 — 이번 주 무료·다음 예고·지난 무료 게임 기록', '에픽게임즈 스토어에서 지금 무료인 게임과 다음 주 예고, 줍줍이 확인해 쌓은 지난 무료 게임 기록을 한곳에. 한국 시간 기준.',
         body, [('루리의 줍줍', '/'), ('게임', '/game/'), ('에픽 무료 게임', '/game/free/')], ld)
    urls.append('/game/free/')
    return urls


KIN_F = os.path.join(HERE, 'kin_guides.json')


def _cite_box(g, path):
    """인용하기 쉽게(2026-10-20 홍보 요청): 갱신일·출처 문구·인용 안내 한 줄 + 표 복사 버튼(assets/money/cite.js)."""
    m = re.search(r'확인일\s*(\d{4}-\d{2}-\d{2})', g.get('basis', ''))
    dt = m.group(1) if m else datetime.date.today().isoformat()
    names = ' · '.join(n for n, _ in g.get('sources', [])[:4])
    has_tbl = any(sc.get('table') for sc in g['sections'])
    return ('<section class="cite-box"><h2>이 페이지 인용하기</h2>'
            f'<p>업데이트: {dt} · 출처: {E(names)}</p>'
            f'<p>인용: 루리의 줍줍(<a href="{SITE}{path}">{SITE}{path}</a>)</p>'
            + ('<button type="button" class="cite-cp">📋 표 복사하기 (엑셀·문서에 붙여넣기)</button>' if has_tbl else '')
            + '<style>.cite-box{padding:10px 14px;border:1px solid var(--bd,#e5e7eb);border-radius:12px;background:var(--card,#fff);margin:16px 0;font-size:13.5px;line-height:1.7}.cite-box h2{font-size:15px;margin:0 0 4px}.cite-box p{margin:2px 0}.cite-cp{margin-top:6px;min-height:40px;padding:0 14px;border:1px solid var(--bd,#d1d5db);border-radius:8px;background:transparent;color:inherit;font:inherit;cursor:pointer}</style>'
            '<script defer src="/assets/money/cite.js?v=1"></script></section>')


def _jr_nav(g, JIDX, GN):
    """여정 허브 안내: 몇 단계째인지, 이전·다음 가이드 링크."""
    if g['slug'] not in JIDX:
        return ''
    j, i = JIDX[g['slug']]
    st = j['steps']
    pv = f'<a href="/money/guide/{st[i - 1]["slug"]}/">← {E(GN[st[i - 1]["slug"]]["name"])}</a>' if i else ''
    nx = f'<a href="/money/guide/{st[i + 1]["slug"]}/">{E(GN[st[i + 1]["slug"]]["name"])} →</a>' if i + 1 < len(st) else ''
    return f'<p class="hm-links">🧭 <a href="/money/guide/journey/{j["slug"]}/">{E(j["name"])}</a> {i + 1}/{len(st)}단계 · {pv} {"·" if pv and nx else ""} {nx}</p>'


def _jr_box(g, JIDX, GN):
    """「이 단계에서 보통 놓치는 것 / 다음 단계 / 공식 문의처」 세 칸."""
    if g['slug'] not in JIDX or not g.get('miss'):
        return ''
    j, i = JIDX[g['slug']]
    st = j['steps']
    nx = f'<a href="/money/guide/{st[i + 1]["slug"]}/">{E(GN[st[i + 1]["slug"]]["name"])}</a>: {E(st[i + 1].get("note", ""))}' if i + 1 < len(st) else '마지막 단계예요.'
    return ('<h2>이 단계 한눈에</h2><div class="tblw"><table class="xb"><thead><tr><th>보통 놓치는 것</th><th>다음 단계</th><th>공식 문의처</th></tr></thead><tbody><tr><td>'
            + '<br>'.join('· ' + E(x) for x in g['miss']) + f'</td><td>{nx}</td><td>{E(g["contact"])}</td></tr></tbody></table></div>')


def _alert(g):
    """급한 처지에서 읽는 글(채무·보증금·사기·분쟁) 맨 위 안내: 법률 상담이 아니고 개별 사건은 기관에 확인."""
    if not g.get('alert'):
        return ''
    return ('<div class="g-alert" role="note"><b>⚠️ 먼저 읽어 주세요</b><p>' + g['alert'] + '</p></div>'
            '<style>.g-alert{border:2px solid #f59e0b;background:#fffbeb;color:#78350f;border-radius:12px;padding:10px 14px;margin:10px 0}.g-alert p{margin:4px 0 0;line-height:1.7}.g-alert a{color:inherit;text-decoration:underline}'
            '@media (prefers-color-scheme: dark){.g-alert{background:#422006;color:#fde68a;border-color:#b45309}}</style>')


def kin_guides():
    """/money/guide/ 생활 돈 가이드 (2026-10-20 홍보 세션 지식iN 반복 질문): 근로장려금·내일배움카드·월세 세액공제 vs 청년월세·퇴직금. 공식 출처로 확인된 칸만 JSON 에 담고 숫자는 표로 분리."""
    if not os.path.exists(KIN_F):
        return []
    _KD = json.load(open(KIN_F, encoding='utf-8'))
    G = _KD['guides']
    GN = {x['slug']: x for x in G}
    JR = _KD.get('journeys', [])
    JIDX = {}
    for j in JR:
        for i, st in enumerate(j['steps']):
            JIDX.setdefault(st['slug'], (j, i))
    urls, cards = [], ''
    for g in G:
        secs = ''
        for sc in g['sections']:
            h = f'<h2>{E(sc["h"])}</h2>'
            if sc.get('table'):
                head, rows = sc['table'][0], sc['table'][1:]
                h += '<div class="tblw"><table class="xb"><thead><tr>' + ''.join(f'<th>{E(c)}</th>' for c in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{E(c)}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>'
            if sc.get('ul'):
                h += '<ul class="gm-l">' + ''.join(f'<li>{x}</li>' for x in sc['ul']) + '</ul>'
            if sc.get('p'):
                h += f'<p>{sc["p"]}</p>'
            if sc.get('html'):
                h += sc['html']
            secs += h
        faq, ld = _faq([(q, a) for q, a in g['faq']])
        src = ''.join(f'<li><a href="{E(u)}" target="_blank" rel="noopener nofollow">{E(n)}</a></li>' for n, u in g['sources'])
        rel = ' · '.join(f'<a href="{E(u)}">{E(t)}</a>' for u, t in g['related'])
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/money/guide/">생활 돈 가이드</a> › {E(g["name"])}</p><h1>{g["icon"]} {E(g["h1"])}</h1>'
                f'<p class="cat-st">📌 {E(g["lead"])}</p><p class="kwn">기준: {E(g["basis"])}' + (' · 원문 바로가기: ' + ' · '.join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(n)}</a>' for n, u in g['sources'][:4])) + '</p>' + _jr_nav(g, JIDX, GN) + _alert(g) + secs + _jr_box(g, JIDX, GN) + '<h2>자주 묻는 질문</h2>' + faq
                + join_cta('apply')
                + _cite_box(g, f'/money/guide/{g["slug"]}/')
                + f'<h2>공식 출처</h2><ul class="gm-l">{src}</ul>'
                + f'<p class="note">공식 안내를 줍줍이 직접 확인해 정리한 내용이고, 기준 금액과 신청 기간은 해마다 바뀔 수 있어요. 신청 전에 위 공식 출처를 꼭 확인하고, 개별 사정은 {E(g["contact"])}에 문의하세요. 법률·세무 상담이 아니에요.</p>'
                + f'<p class="hm-links">{rel} · <a href="/money/guide/">다른 생활 돈 가이드</a></p>' + GAME_CSS + (f'<script defer src="{E(g["script"])}"></script>' if g.get('script') else ''))
        page(f'/money/guide/{g["slug"]}/', g['title'], g['desc'], body, [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('생활 돈 가이드', '/money/guide/'), (g['name'], f'/money/guide/{g["slug"]}/')], ld)
        urls.append(f'/money/guide/{g["slug"]}/')
        cards += f'<li><a class="card" data-c="guide" href="/money/guide/{g["slug"]}/"><span class="ic">{g["icon"]}</span><div class="cb"><h3 class="t">{E(g["name"])}</h3><p class="o">{E(g["h1"])}</p></div></a></li>'
    jcards = ''
    for j in JR:
        jp = f'/money/guide/journey/{j["slug"]}/'
        rows = ''.join(f'<tr><td>{i + 1}</td><td><a href="/money/guide/{st["slug"]}/">{E(GN[st["slug"]]["name"])}</a></td><td>{E(st.get("note", ""))}</td><td>{E(GN[st["slug"]]["contact"])}</td></tr>' for i, st in enumerate(j['steps']) if st['slug'] in GN)
        hb = (f'<p class="bc"><a href="/">홈</a> › <a href="/money/guide/">생활 돈 가이드</a> › {E(j["name"])}</p><h1>{j["icon"]} {E(j["h1"])}</h1><p class="cat-st">📌 {E(j["lead"])}</p>'
              f'<h2>단계별로 보기</h2><div class="tblw"><table class="xb"><thead><tr><th>단계</th><th>가이드</th><th>이 단계에서 할 일</th><th>공식 문의처</th></tr></thead><tbody>{rows}</tbody></table></div>'
              f'<p class="note">{E(j.get("note", "각 가이드는 공식 안내로 확인한 내용만 적고, 자료마다 다르거나 확인하지 못한 칸은 비워 뒀어요."))}</p>'
              f'<p class="hm-links"><a href="/money/guide/">다른 생활 돈 가이드</a></p>' + GAME_CSS)
        page(jp, j['title'], j['desc'], hb, [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('생활 돈 가이드', '/money/guide/'), (j['name'], jp)])
        urls.append(jp)
        jcards += f'<li><a class="card" data-c="guide" href="{jp}"><span class="ic">{j["icon"]}</span><div class="cb"><h3 class="t">{E(j["name"])}</h3><p class="o">{E(j["h1"])}</p></div></a></li>'
    cards = jcards + cards
    tools = ('<li><a class="card" data-c="guide" href="/money/tools/severance/"><span class="ic">🧮</span><div class="cb"><h3 class="t">퇴직금 계산기</h3><p class="o">입사·퇴사일과 최근 3개월 임금으로 계산</p></div></a></li>'
             '<li><a class="card" data-c="guide" href="/money/tools/unemployment/"><span class="ic">🧮</span><div class="cb"><h3 class="t">실업급여 계산기</h3><p class="o">가입 기간·나이별 받는 날 수와 금액</p></div></a></li>'
             '<li><a class="card" data-c="guide" href="/money/tools/salary/"><span class="ic">🧮</span><div class="cb"><h3 class="t">연봉 실수령액 계산기</h3><p class="o">4대보험·소득세 뺀 월급</p></div></a></li>')
    page('/money/guide/', '생활 돈 가이드 — 근로장려금·국민내일배움카드·월세 세액공제·퇴직금 (공식 출처 정리)', '근로장려금, 국민내일배움카드, 월세 세액공제와 청년월세 지원, 퇴직금을 국세청·고용노동부·고용24 등 공식 안내로 정리했어요. 계산기도 함께.',
         '<p class="bc"><a href="/">홈</a> › 생활 돈 가이드</p><h1>🧾 생활 돈 가이드</h1><p class="cat-st">📌 자주 묻는 돈 문제를 공식 안내로 확인한 것만 정리했어요. 공식에서 확인하지 못한 항목은 일부러 적지 않았고, 기준일과 출처를 페이지마다 밝혀요.</p>'
         f'<ul class="list">{cards}</ul>' + kin_ans_links('/money/guide/') + f'<h2>계산기</h2><ul class="list">{tools}</ul>' + join_cta('apply') + GAME_CSS,
         [('루리의 줍줍', '/'), ('머니', '/analyst/'), ('생활 돈 가이드', '/money/guide/')])
    urls.append('/money/guide/')
    return urls


CLASS_SRC = r'C:\Users\k\Desktop\공모전_2026\유튜브_롱폼\ai_lec\class_lectures.json'
CLASS_F = os.path.join(HERE, 'class_lectures.json')


def class_pages():
    """/class/ 루리의 AI교실 (2026-10-20 연구 세션): 강의 10편 데이터는 class_lectures.json(원본 공모전_2026\유튜브_롱폼\ai_lec). youtube 가 null 이면 「공개 준비 중」, 채워지면 퍼가기."""
    try:
        if os.path.exists(CLASS_SRC) and (not os.path.exists(CLASS_F) or os.path.getmtime(CLASS_SRC) > os.path.getmtime(CLASS_F)):
            shutil.copyfile(CLASS_SRC, CLASS_F)
    except Exception:
        pass
    if not os.path.exists(CLASS_F):
        return []
    D = json.load(open(CLASS_F, encoding='utf-8'))
    L = D['lectures']
    urls = []
    NOTE = ('<div class="cl-note"><b>안내</b> 영상의 목소리와 캐릭터(루리)는 AI로 만들었어요. 영상 속 채팅 화면은 <b>AI 응답 예시</b>이고, 엑셀 화면은 실제 엑셀을 캡처한 거예요. '
            'AI 답은 틀릴 수 있으니 숫자·날짜·법령은 꼭 직접 확인하세요.</div>')
    CSS = ('<style>.cl-note{padding:10px 12px;border:1px solid var(--bd,#e5e7eb);border-radius:12px;background:var(--card,#fff);margin:10px 0;font-size:13.5px;line-height:1.7}'
           '.cl-vid{position:relative;padding-top:56.25%;border-radius:12px;overflow:hidden;background:#0f172a;margin:10px 0}.cl-vid iframe{position:absolute;inset:0;width:100%;height:100%;border:0}'
           '.cl-soon{padding:28px 12px;text-align:center;border:1px dashed var(--bd,#d1d5db);border-radius:12px;color:var(--mu,#6b7280);margin:10px 0}'
           '.cl-pr{position:relative;margin:8px 0}.cl-pr pre{white-space:pre-wrap;word-break:break-word;margin:0;padding:12px 12px 12px;border:1px solid var(--bd,#e5e7eb);border-radius:10px;background:var(--card,#fff);font:inherit;font-size:14px;line-height:1.7}'
           '.cl-cp{margin:6px 0 0;min-height:40px;padding:0 14px;border:1px solid var(--bd,#d1d5db);border-radius:8px;background:transparent;color:inherit;font:inherit;cursor:pointer}'
           '.cl-ck{list-style:none;padding:0;margin:6px 0}.cl-ck li{margin:4px 0}.cl-ck label{display:flex;gap:8px;align-items:flex-start;min-height:36px;line-height:1.6}.cl-ck input{margin-top:5px;width:18px;height:18px}'
           '.cl-bar{height:8px;border-radius:99px;background:var(--bd,#e5e7eb);overflow:hidden;margin:6px 0}.cl-bar i{display:block;height:100%;width:0;background:#4f46e5}'
           '.cl-paid{padding:12px;border:1px dashed var(--bd,#d1d5db);border-radius:12px;color:var(--mu,#6b7280);margin:14px 0;font-size:13.5px}.cl-st{font-size:12.5px;color:var(--mu,#6b7280)}</style>')
    cards = ''
    for i, l in enumerate(L):
        n, slug = l['n'], l['slug']
        p = f'/class/{n:02d}-{slug}/'
        yt = l.get('youtube')
        vid = ''
        if yt:
            m = re.search(r'(?:v=|youtu\.be/|embed/)([\w-]{11})', yt)
            vid = (f'<div class="cl-vid"><iframe src="https://www.youtube-nocookie.com/embed/{m.group(1)}" title="{E(l["title"])}" loading="lazy" allowfullscreen></iframe></div>' if m
                   else f'<p><a href="{E(yt)}" target="_blank" rel="noopener">▶ 유튜브에서 보기</a></p>')
        else:
            vid = '<div class="cl-soon">🎬 영상 공개 준비 중이에요. 아래 프롬프트와 체크리스트는 지금 바로 쓸 수 있어요.</div>'
        goals = ''.join(f'<li>{E(x)}</li>' for x in l['goals'])
        demos = ''.join(f'<h3>실습 {k + 1}. {E(d["name"])}</h3><div class="cl-pr"><pre>{E(d["prompt"])}</pre><button type="button" class="cl-cp">📋 프롬프트 복사</button></div>' for k, d in enumerate(l['demos']))
        pit = ''.join(f'<li>{E(x)}</li>' for x in l['pitfalls'])
        rec = ''.join(f'<li><label><input type="checkbox" data-k="r{k}"> {E(x)}</label></li>' for k, x in enumerate(l['recap']))
        asg = ''.join(f'<li><label><input type="checkbox" data-k="a{k}"> {E(x)}</label></li>' for k, x in enumerate(l['assignment']))
        prev = f'<a href="/class/{L[i - 1]["n"]:02d}-{L[i - 1]["slug"]}/">← {E(L[i - 1]["title"])}</a>' if i else ''
        nxt = f'<a href="/class/{L[i + 1]["n"]:02d}-{L[i + 1]["slug"]}/">{E(L[i + 1]["title"])} →</a>' if i + 1 < len(L) else ''
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/class/">루리의 AI교실</a> › {n}강</p><h1>🎓 {n}강. {E(l["title"])}</h1>'
                f'<p class="cat-st">📌 {E(l["topic"])}</p><div data-cl="{n}">' + vid + NOTE
                + f'<h2>이번 강의 목표</h2><ul class="gm-l">{goals}</ul><h2>따라 해 보기</h2><p class="kwn">복사해서 쓰는 AI 도구에 붙여 넣고, 대괄호나 내 상황에 맞게 바꿔 보세요.</p>{demos}'
                f'<h2>조심할 점</h2><ul class="gm-l">{pit}</ul><h2>정리 체크리스트</h2><ul class="cl-ck">{rec}</ul><h2>과제</h2><ul class="cl-ck">{asg}</ul>'
                f'<p class="cl-st" data-st></p></div>'
                f'<div class="cl-paid" data-paid="{n}">🔒 추가 자료 자리 — 실습 파일·템플릿 같은 추가 자료는 준비되면 여기에 안내할게요.</div>'
                f'<p class="hm-links">{prev} {"·" if prev and nxt else ""} {nxt} · <a href="/class/">전체 강의</a></p>' + join_cta('ai') + CSS
                + '<script defer src="/assets/class/class.js?v=1"></script>')
        page(p, f'{n}강. {l["title"]} — 루리의 AI교실', f'{l["topic"]}. 복사해서 바로 쓰는 프롬프트와 체크리스트로 따라 하는 {n}강.', body,
             [('루리의 줍줍', '/'), ('루리의 AI교실', '/class/'), (f'{n}강', p)])
        urls.append(p)
        cards += (f'<li><a class="card" data-c="guide" href="{p}"><span class="ic">{"🎬" if yt else "📝"}</span><div class="cb"><h3 class="t">{n}강. {E(l["title"])}</h3>'
                  f'<p class="o">{E(l["topic"])} · {"영상 공개" if yt else "영상 준비 중"} <span class="cl-st" data-idx="{n}"></span></p></div></a></li>')
    idx = (f'<p class="bc"><a href="/">홈</a> › 루리의 AI교실</p><h1>🎓 루리의 AI교실</h1>'
           f'<p class="cat-st">📌 AI에게 일 시키는 법부터 엑셀·이메일·회의록·PPT까지, 복사해서 바로 써 보는 10강이에요. 영상이 없는 강의도 프롬프트와 체크리스트는 지금 볼 수 있어요.</p>' + NOTE
           + '<div class="cl-bar"><i data-bar></i></div><p class="cl-st" data-all></p>'
           + f'<ul class="list">{cards}</ul>' + join_cta('ai') + CSS + '<script defer src="/assets/class/class.js?v=1"></script>')
    page('/class/', '루리의 AI교실 — 프롬프트 기본부터 엑셀·이메일·PPT까지 10강', '프롬프트 복사 버튼과 체크리스트로 따라 하는 AI 활용 10강. 엑셀 수식, 매크로, 업무 이메일, 회의록, PPT, 문서 요약.', idx,
         [('루리의 줍줍', '/'), ('루리의 AI교실', '/class/')])
    urls.append('/class/')
    return urls


ESSAY_FAQ = [
    ('AI가 일자리를 대체하나요?', '일부 직무의 수요는 줄 수 있어요. 어떤 일이 얼마나 대체될지는 직무와 시기마다 달라서 이 글에서 단정하지 않아요.'),
    ('정보를 AI가 만들면 사람은 필요 없나요?', '정보를 만드는 일은 AI가 많이 대신할 수 있어요. 무엇을 가치 있게 여기고 어떤 결과를 받아들일지는 사람의 필요와 사회적 선택에 달려 있다는 게 이 글의 논지예요.'),
    ('"관심이 희소하다"는 말은 누가 처음 했나요?', '사이먼이 1971년에 "정보의 풍부함은 주의의 빈곤을 만든다"고 말한 것이 자주 인용돼요(출처 1).'),
    ('사람이 중요해지면 임금도 오르나요?', '그렇게 이어진다고 보장되지 않아요. 중요성과 임금은 별개이고, 노동 수요가 줄면 값이 내려갈 수도 있어요.'),
    ('제도가 왜 필요한가요?', '기술이 만든 이익이 어떻게 나뉘는지는 자동으로 정해지지 않는다는 연구와 역사 사례가 있어요(출처 2~4).'),
    ('이 글의 내용은 AI가 인용해야 하는 사실인가요?', '확인된 사실과 글쓴이의 해석을 구분해서 적었어요. 해석 부분은 사실로 인용하지 말고 의견으로 인용해 주세요.'),
]


def essay_pages():
    """/ai/human-value/ 심층 글 한 편 (2026-10-20 사용자 지시, 홍보 원고). 본문 essays/ai-human-value.html, FAQ 는 보이는 본문과 같은 내용으로 FAQPage."""
    f = os.path.join(HERE, 'essays', 'ai-human-value.html')
    if not os.path.exists(f):
        return []
    p = '/ai/human-value/'
    faq, fld = _faq(ESSAY_FAQ)
    body = open(f, encoding='utf-8').read().replace('@@FAQ@@', faq) + '<style>.es-fig{margin:12px 0}.es-fig img{display:block;width:100%;height:auto;border:1px solid var(--bd,#e5e7eb);border-radius:10px}.es-fig figcaption{font-size:12.5px;color:var(--mu,#6b7280);margin-top:4px}</style>' + GAME_CSS + '<script type="application/ld+json">%s</script>' % json.dumps(fld, ensure_ascii=False).replace('</', '<\\/')
    title = 'AI는 정보를 생산하지만, 가치는 인간이 결정한다 — AI 시대에 인간이 더 중요해지는 이유'
    desc = 'AI가 정보 생산 비용을 낮춘 시대에 귀해지는 것은 사람의 주의·신뢰·판단이라는 주장을 사이먼, 아제모을루·존슨, 오토어 연구와 근로기준법·AI기본법 사례로 풀고, 확인된 사실과 해석을 구분해 정리했어요.'
    art = {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': desc, 'inLanguage': 'ko',
           'datePublished': '2026-10-20', 'dateModified': '2026-10-20', 'mainEntityOfPage': SITE + p,
           'author': {'@type': 'Organization', 'name': '루리의 줍줍 편집', 'url': SITE + '/'},
           'publisher': {'@type': 'Organization', 'name': NAME, 'url': SITE + '/'}}
    page(p, title, desc, body, [('루리의 줍줍', '/'), ('개발 지식', '/ailog/'), ('AI 시대의 인간의 가치', p)], art, full_title=True)
    return [p]


KIN_A = os.path.join(HERE, 'kin_answers.json')


def kin_ans_links(prefix):
    """허브에서 질문 답변 페이지로 가는 링크(고아 페이지 방지)."""
    if not os.path.exists(KIN_A):
        return ''
    L = [a for a in json.load(open(KIN_A, encoding='utf-8'))['answers'] if a['path'].startswith(prefix)]
    return ('<h2>💬 자주 묻는 질문 답변</h2><ul class="gm-l">' + ''.join(f'<li><a href="{E(a["path"])}">{E(a["h1"])}</a></li>' for a in L) + '</ul>') if L else ''


def _mdlink(t):
    """답변 글 안의 [라벨](https://주소) 을 외부 링크로(글자는 먼저 이스케이프, 링크만 살림)."""
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', E(t))


def kin_answer_pages():
    """2026-10-20 홍보 세션: 정확성을 확인한 지식iN 답변을 질문 제목 H1 페이지로 재활용(레시피 3·돈 2·게임 1). 원문 문장 그대로, 확인 못 한 칸은 비워 둔 채."""
    if not os.path.exists(KIN_A):
        return []
    urls = []
    CRUMB = {'recipe': [('레시피', '/fridge/')], 'apply': [('생활 돈 가이드', '/money/guide/')], 'game': [('게임', '/game/')]}
    for a in json.load(open(KIN_A, encoding='utf-8'))['answers']:
        h = ''
        for b in a['blocks']:
            if b[0] == 'h2':
                h += f'<h2>{E(b[1])}</h2>'
            elif b[0] == 'h3':
                h += f'<h3>{E(b[1])}</h3>'
            elif b[0] == 'ul':
                h += '<ul class="gm-l">' + ''.join(f'<li>{_mdlink(x)}</li>' for x in b[1]) + '</ul>'
            elif b[0] == 'plink':
                h += f'<p>{E(b[1])} <a href="{E(urllib.parse.unquote(b[2]))}">{E(b[3])}</a></p>'
            else:
                h += f'<p>{_mdlink(b[1])}</p>'
        first = next((b[1] for b in a['blocks'] if b[0] == 'p'), a['h1'])
        rel = ' · '.join(f'<a href="{E(u)}">{E(t)}</a>' for u, t in a['related'])
        crumbs = CRUMB[a['topic']]
        body = (f'<p class="bc"><a href="/">홈</a> › ' + ' › '.join(f'<a href="{u}">{E(n)}</a>' for n, u in crumbs) + f' › 질문 답변</p><h1>{E(a["h1"])}</h1>'
                f'<p class="kwn">작성 {a["date"]} · 줍줍이 확인한 내용으로 정리한 답변이에요.</p>' + h
                + (f'<p class="note">{_mdlink(a["note"])}</p>' if a.get('note') else '') + join_cta(a['topic']) + f'<p class="hm-links">{rel}</p>' + GAME_CSS)
        page(a['path'], a['h1'], re.sub(r'\s+', ' ', first)[:150], body, [('루리의 줍줍', '/')] + [(n, u) for n, u in crumbs] + [(a['h1'][:40], a['path'])])
        urls.append(a['path'])
    return urls


def trend_pages():
    """이슈 트렌드 (2026-10-20 사용자 「뉴스에서 사람들이 많이 싸운 걸 위주로, 싸움구경하는 루리, 이슈 트렌드로 하나」): 커뮤니티 열기 TOP7 + 사흘 흐름 + 언론이 엇갈려 전한 이슈.
    열기는 댓글·글·커뮤니티 수로만 매기고, 누가 이겼다·틀렸다·편들기는 쓰지 않는다. 본문은 옮기지 않고 제목·링크만."""
    td = _rd('talk/data.json')
    ad = os.path.join(ROOT, 'talk', 'archive')
    if not td or not td.get('issues'):
        return []
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True)[:3] if os.path.isdir(ad) else []
    BADT = re.compile(r'무슬림|난민|이슬람|흑인|조선족|짱깨|한남|김치녀|된장녀|여자들은|남자들은|여자들이|남자들이|여자 병수발|못생긴|불태|살해|살인|성폭|성추행|폭행|자살|시신|사망|숨져|극단|몰카|음란')   # 성별·인종·종교 갈라치기성, 폭력 소재는 열기 순위에서 뺌
    for x_ in td['issues']:
        x_['posts'] = [p for p in (x_.get('posts') or []) if not BADT.search(p['t'])]
    iss = sorted([x for x in td['issues'] if not BADT.search(x['t']) and x.get('posts')], key=lambda x: (-int(x.get('nc') or 0), -int(x.get('np') or 0)))[:7]
    mx = max(int(x.get('nc') or 0) for x in iss) or 1
    cards = ''
    for i, x in enumerate(iss, 1):
        ps = ''.join(f'<li><a href="{E2(p["u"])}" target="_blank" rel="noopener nofollow"><em>{E2(p["s"])}</em>{E2(p["t"])} <small>댓글 {p.get("nc", 0)}</small></a></li>' for p in (x.get('posts') or [])[:3])
        nw = x.get('news')
        nl = f'<p class="hm-links"><a href="/news/#is{nw["n"]}">🕵️ 같은 이슈를 다룬 보도: 언론사 {nw["on"]}곳 · 확인 신호 {nw.get("s", "-")}점 →</a></p>' if nw else ''
        cards += (f'<article class="an-c tr-c"><div class="an-h"><h3>{i}. {E2(x["t"])}</h3></div>'
                  f'<div class="tr-b" aria-hidden="true"><i style="width:{max(int(x.get("nc") or 0) / mx * 100, 6):.0f}%"></i></div>'
                  f'<p class="an-st">💬 댓글 {x["nc"]}개 · 글 {x["np"]}건 · 커뮤니티 {x["nsite"]}곳({E2(", ".join(x["cs"][:4]))}{" 등" if len(x["cs"]) > 4 else ""}) · 인기글에 {x["hrs"]}시간째</p>'
                  f'<ul class="kw-l">{ps}</ul>{nl}</article>')
    rows = ''
    prev_t = set()
    for d in sorted(days):
        a = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        top = sorted([y for y in a.get('issues', []) if not BADT.search(y['t'])], key=lambda y: -int(y.get('nc') or 0))[:3]
        rows += f'<tr><td>{d[5:].replace("-", "/")}</td>' + ''.join(f'<td>{E2(y["t"][:26])}<br><small>댓글 {y["nc"]}{" · 전날에도 올랐어요" if y["t"] in prev_t else ""}</small></td>' for y in top) + '</tr>'
        prev_t = {y['t'] for y in a.get('issues', [])}
    flow = (f'<section class="mg-s"><h2>📈 사흘간 열기 흐름</h2><div class="tblw"><table class="xb"><thead><tr><th>날짜</th><th>1위</th><th>2위</th><th>3위</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<p class="kwn">그날 댓글 수가 가장 많았던 이슈 3개예요(집계 시각 기준 마지막 기록).</p></section>') if len(days) >= 2 else ''
    nd = _rd('news/data.json') or {}
    cf = [x for x in nd.get('issues', []) if (x.get('cf') or x.get('claim')) and int(x.get('on') or 0) >= 3 and not re.search(r'사망|숨져|사고|참사|화재', x['t'])]
    cf = sorted(cf, key=lambda x: (-bool(x.get('cf')), -int(x.get('on') or 0)))[:4]
    nl2 = ''.join(f'<li><a href="/news/#is{x["n"]}"><b>{E2(x["t"][:60])}</b><span>언론사 {x["on"]}곳' + (f' · 숫자가 엇갈림: {E2(", ".join(x["cf"][:3]))}' if x.get('cf') else ' · 발언·주장 기사') + '</span></a></li>' for x in cf)
    news_h = f'<section class="mg-s"><h2>📰 언론이 서로 다르게 전한 이슈</h2><ul class="mg-l">{nl2}</ul><p class="kwn">기사 제목 속 숫자가 서로 다르거나 누군가의 발언·주장이 중심인 이슈예요. 누가 맞는지는 판단하지 않고 기사 제목을 나란히 보여 줘요.</p></section>' if nl2 else ''
    shr = share_bar('이슈 트렌드 — 오늘 커뮤니티가 가장 뜨겁게 이야기한 이슈', '오늘 커뮤니티 TOP: ' + ', '.join(x['t'][:16] for x in iss[:3]))
    css = ('<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><link rel="stylesheet" href="/assets/analyst/analyst.css?v=4"><link rel="stylesheet" href="/assets/news/news.css?v=6">'
           '<style>.tr-hero{display:flex;gap:14px;align-items:center;margin:8px 0 14px;padding:12px;border-radius:16px;background:linear-gradient(135deg,#fff7ed,#fef3c7);color:#451a03}.tr-hero img{width:140px;height:auto;border-radius:12px;flex:none}'
           '.tr-hero b{display:block;font-size:20px;margin-bottom:4px}.tr-hero p{margin:0;font-size:14px;line-height:1.6}.tr-b{height:10px;border-radius:999px;background:var(--pbg,#f1f5f9);margin:6px 0;overflow:hidden}.tr-b i{display:block;height:100%;background:linear-gradient(90deg,#f59e0b,#ea580c)}'
           '.tblw{overflow-x:auto}.xb{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}.xb th,.xb td{border-bottom:1px solid var(--bd,#e5e7eb);padding:6px 6px;text-align:left;vertical-align:top}</style>')
    body = ('<p class="bc"><a href="/">홈</a> › <a href="/news/">이슈</a> › 이슈 트렌드</p><h1>🍿 이슈 트렌드 — 싸움 구경 중인 루리</h1>'
            f'<div class="tr-hero"><img src="/assets/ruri/o_watch.webp" width="140" height="193" alt="팝콘을 먹으며 이슈를 구경하는 루리"><div><b>오늘 커뮤니티가 가장 뜨겁게 이야기한 이슈</b>'
            f'<p>{E2(td.get("updated", ""))} 기준 · 커뮤니티 {td.get("sites", 0)}곳 인기글 {td.get("npost", 0):,}건에서 <b>댓글이 가장 많이 달린 이슈</b> 7개를 골랐어요. 팝콘 들고 구경만 하는 루리는 어느 편도 들지 않아요.</p></div></div>'
            + cards + flow + news_h + shr
            + '<p class="note">열기는 댓글·글·커뮤니티 수로만 매겨요. 댓글이 많다고 찬반이 갈린 건 아니고, 글 속 의견은 줍줍이 판단하지 않아요. 성별·인종·종교 갈라치기성 글, 폭력 사건, 개인 신상·비방성 글은 순위에서 빼고, 글 내용은 옮기지 않고 제목과 링크만 실어요. 더 보기: '
              '<a href="/talk/">커뮤니티 이슈 전체</a> · <a href="/hot/">핫이슈</a> · <a href="/news/">기사 확인 신호</a></p>' + css)
    page('/trend/', '이슈 트렌드 — 오늘 커뮤니티가 가장 뜨겁게 이야기한 이슈 TOP7', '커뮤니티 인기글에서 댓글이 가장 많이 달린 이슈 TOP7과 사흘간 열기 흐름, 언론이 서로 다르게 전한 이슈를 한곳에. 팝콘 들고 구경하는 루리가 정리해요.',
         body, [('루리의 줍줍', '/'), ('이슈', '/news/'), ('이슈 트렌드', '/trend/')], og='/assets/trend/og.jpg')
    return ['/trend/']


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


def kw_play(db, today, L, ENH=None):
    """/kw/ 맨 위 놀이판 + 목록(뱃지·흐름 그래프·관련 줍줍). kw_fun.py 에 로직."""
    import kw_fun as KF
    hist = (_rd('kw/hist.json') or {}).get(today, {})
    SRCB = lambda r: ('<span class="kw-b both">구글·시그널 동시</span>' if len(r.get('src') or []) > 1 else '<span class="kw-b n">시그널 순위</span>' if (r.get('src') or ['google']) == ['naver'] else '<span class="kw-b g">구글 트렌드</span>')
    cur, mx = KF.collect(db, today, L)
    contests = _rd('data.json').get('items', []) if _rd('data.json') else []
    qbox, qdata = KF.quiz(cur, today)
    vbox, vdata = KF.vote(cur, today, os.path.join(ROOT, 'kw', 'vote_cands.json'))
    card = KF.top5_card(cur, today, mx[11:16] or '')
    byslug = {x['slug']: x for x in cur}
    li = ''
    for j, a in enumerate(L):
        r = db.get(a['slug'])
        if not r:
            continue
        x = byslug.get(a['slug'])
        bd_ = ''.join(f'<i title="{E(t)}">{ic}{E(t) if ic in ("⏳", "🌙") else ""}</i>' for ic, t in KF.badges(x, hist)) if x else ''
        if ENH and a['slug'] in ENH:
            bd_ += '<i title="읽을거리가 있어요">📖</i>'
        rl = KF.rules_links(x, contests) if x else []
        ex = ''.join(f'<a href="{E(u)}">{E(t)}</a>' for u, t in rl[:2])   # 규칙표로 맞는 것만(맞는 게 없으면 안 붙임)
        li += (f'<li id="k-{E(a["slug"])}" data-c="{E(KF.cat_of(a["k"], r.get("news")))}"><a href="/kw/{E(a["slug"])}/"><em>{j + 1}</em><b>{E(a["k"])} <span class="kwb">{bd_}</span></b>'
               f'<span>{SRCB(a)} {E(a.get("traffic") or "-")} · {E(a.get("first", ""))} 첫 등장</span>{KF.spark(hist.get(a["slug"]) or [], KF.STY[KF.srckey(a.get("src"))][0])}</a>'
               + (f'<p class="kwr">📎 {ex}</p>' if ex else '') + '</li>')
    note_h = ('<p class="kwn">흐름 그래프(오늘 시간대별 인기도)는 시간마다 기록이 쌓이는 대로 나타나요. 기록은 ' + (min((v[0][0] for v in hist.values() if v), default='') or '다음 갱신') + '부터예요. '
              '🆕 신규(3시간 안에 처음) · 🔥 검색량 1000+ 또는 실시간 3위 안 · ⏳ 오래 버티는 중 · 📉 하락(기록 필요) · 🌙 새벽에만 떴어요. 인기도 = 검색량 구간 + 실시간 순위 합산 상대값이에요.</p>')
    shr = share_bar('오늘의 키워드 TOP5', '오늘 많이 검색된 키워드 TOP5 — ' + ', '.join(card[1][:5]) if card else '오늘의 인기 키워드')
    dl = f'<p class="kwn"><a href="/assets/kw/top5.jpg" download>🖼️ 오늘의 TOP5 카드 이미지 저장</a></p>' if card else ''
    rd = ''.join(f'<li><a href="/kw/{E(sl)}/"><b>{E(db[sl]["k"])}</b><span>섹션 {n}개 · {E(", ".join(KF.STY[KF.srckey(db[sl].get("src"))][1:2]))}</span></a></li>' for sl, (_h, n) in list((ENH or {}).items())[:8])
    rd5 = ''.join(f'<li><a href="/kw/{E(sl)}/"><b>{E(db[sl]["k"])}</b><span>섹션 {n}개 · {E(", ".join(KF.STY[KF.srckey(db[sl].get("src"))][1:2]))}</span></a></li>' for sl, (_h, n) in list((ENH or {}).items())[:5])
    top = (KF.one_liner(cur, db) + KF.top1(cur, hist)
           + (f'<section class="kwc"><h2>📌 오늘의 추천 — 읽어 볼 만한 키워드</h2><ul class="mg-l">{rd5}</ul><p class="kwn">여러 출처에 동시에 뜬 것, 오래 버티는 것, 생활에 닿는 것부터 골랐어요. 정치·가십·사고는 제외해요.</p></section>' if rd5 else '')
           + KF.cloud(cur)
           + '<details class="kw-play"><summary>🎮 놀이판 — 하루살이·장수 키워드, 퀴즈, 내일 예측 투표</summary>' + KF.fleeting(cur) + qbox + vbox + '</details>' + shr + dl
           + '<script type="application/json" id="kw-data">' + json.dumps({'q': qdata, 'v': vdata}, ensure_ascii=False).replace('</', '<' + chr(92) + '/') + '</script>'
           + '<link rel="stylesheet" href="/assets/kw/kw.css?v=3"><script defer src="/assets/kw/kw.js?v=1"></script>' + FOLD_TAGS)
    return {'top': top, 'list': note_h + f'<h2>📋 오늘 뜬 키워드 전체</h2><ol class="mg-l kwl" data-fold="12" data-step="24" data-filter="c">{li}</ol>'}, (card[0] if card else None)


def kw_pages():
    # 인기 키워드 상세 (2026-10-18 사용자: 구글 등 인기 키워드로 블로그 + 사이트 상세 정보, 홍보 세션 연구 ⑂ 요청) — 매시 kw.py
    db = _rd('kw/db.json')
    ad = os.path.join(ROOT, 'kw', 'archive')
    days = sorted([f[:-5] for f in os.listdir(ad) if f.endswith('.json')], reverse=True) if os.path.isdir(ad) else []
    if not db or not days:
        return []
    css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    note = '<p class="note">출처: <a href="https://trends.google.com/trending?geo=KR">Google Trends 한국 급상승</a>과 <a href="https://www.signal.bz/news/guide">시그널</a>. 시그널은 네이버와 별개인 서비스이며 네이버 공식 검색 순위가 아닙니다. 숫자 뒤 + 표시는 구글이 제공하는 검색량 구간, 실시간 N위는 시그널 순위입니다. 이를 합친 화면 점수는 자체 정렬용이며 월간 검색량·방문자 수가 아닙니다. 자동완성은 주제 후보일 뿐 수요나 검색 유입을 보장하지 않습니다. 출처 설명 확인: 2026-10-20.</p>'
    urls = ['/kw/']
    kd = os.path.join(ROOT, 'kw')  # 제외된 키워드 페이지는 지움
    for f in os.listdir(kd):
        if os.path.isdir(os.path.join(kd, f)) and f != 'archive' and not re.match(r'\d{4}-\d{2}-\d{2}$', f) and f not in db:
            shutil.rmtree(os.path.join(kd, f), ignore_errors=True)
    SRCB = lambda r: ('<span class="kw-b both">구글·시그널 동시</span>' if len(r.get('src') or []) > 1 else '<span class="kw-b n">시그널 순위</span>' if (r.get('src') or ['google']) == ['naver'] else '<span class="kw-b g">구글 트렌드</span>')
    import kw_fun as KF, impact as IPK, market as MKT
    ENH = {}   # 2026-10-20 읽을거리 상위 키워드(섹션 3개 이상인 것만, 15개까지)
    try:
        L0 = json.load(open(os.path.join(ad, days[0] + '.json'), encoding='utf-8'))
        cur0, _mx = KF.collect(db, days[0], L0)
        ac0 = _rd('kw/ac.json') or {}
        tsmap = {a['u']: a.get('ts') for a in (_rd('news/data.json') or {}).get('items', [])}
        MK0 = MKT.load()
        for x in KF.priority(cur0, {}):
            if len(ENH) >= 15:
                break
            h_, n_ = KF.enhance(x, db, ac0, tsmap, MK0, cur0, IPK)
            if n_ >= 3:
                ENH[x['slug']] = (h_, n_)
    except Exception as e:
        print('키워드 읽을거리 실패', repr(e)[:150])
    for sl, r in db.items():
        k = r['k']
        lines = [f'「{E2(k)}」{josa_ga(k)} {kdate(r["days"][-1])} ' + ('구글 급상승과 시그널 순위에 동시에' if len(r.get('src') or []) > 1 else '시그널 순위에' if (r.get('src') or ['google']) == ['naver'] else '구글 검색 급상승 키워드에') + f' 올랐어요({E2(r.get("traffic") or "-")}).']
        if r.get('srcs'):
            lines.append(f'관련 보도는 {len(r["srcs"])}곳({E2(", ".join(r["srcs"][:5]))}{" 등" if len(r["srcs"]) > 5 else ""})에서 나왔어요.')
        if r.get('issue'):
            x = r['issue']
            lines.append(f'루리의 기사 확인 신호에서는 언론사 {x["on"]}곳이 보도한 이슈로 묶였고, 확인 신호 점수는 {G.get(x.get("g"), "")} {x.get("s") if x.get("s") is not None else "-"}점이에요.')
        if len(r['days']) > 1:
            lines.append(f'최근 {len(r["days"])}일 동안 급상승에 올랐어요({", ".join(d[5:].replace("-", "/") for d in r["days"][-5:])}).')
        why = ''.join(f'<li><a href="{E2(n["u"])}" target="_blank" rel="noopener nofollow"><em>{E2(n["o"])}</em>{E2(n["t"])}</a></li>' for n in r.get('news', []))
        ours = ''.join(f'<li><a href="{E2(a["u"])}" target="_blank" rel="noopener nofollow"><em>{E2(a["o"])} {G.get(a.get("g"), "")} {a["s"] if a.get("s") is not None else ""}</em>{E2(a["t"])}</a></li>' for a in r.get('ours', []))
        links = []
        if r.get('issue'):
            links.append(f'<a href="/news/#is{r["issue"]["n"]}"><em>🕵️ 기사 확인 신호</em><b>{E2(r["issue"]["t"])}</b></a>')
        links += [f'<a href="/talk/#t{x["n"]}"><em>💬 커뮤니티</em><b>{E2(x["t"])}</b></a>' for x in r.get('talk', [])]
        links += [f'<a href="/analyst/s/{x["id"]}/"><em>📊 애널리스트</em><b>{E2(x["name"])} 목표가 의견</b></a>' for x in r.get('stocks', [])]
        links += [f'<a href="/analyst/coin/{x["sym"].lower()}/"><em>🪙 코인</em><b>{E2(x["name"])} 전망 종합</b></a>' for x in r.get('coins', [])]
        links += [f'<a href="{E2(p_["u"])}"><em>{E2(p_["k"])}</em><b>{E2(p_["t"])}</b></a>' for p_ in r.get('pr', [])]
        trs = r.get('trend') or []
        if len(trs) >= 5:
            W_, H_ = 600, 140; mx = max(v for _, v in trs) or 1
            pts = ' '.join(f'{10 + (W_ - 20) * i / (len(trs) - 1):.1f},{H_ - 22 - (H_ - 40) * v / mx:.1f}' for i, (_, v) in enumerate(trs))
            trend_html = (f'<section class="mg-s"><h2>📈 최근 30일 네이버 검색량 추이</h2><figure class="an-ch"><svg viewBox="0 0 {W_} {H_}" role="img" aria-label="{E2(k)} 검색량 추이">'
                          f'<polyline points="{pts}" fill="none" stroke="#16a34a" stroke-width="3"/><text x="10" y="{H_ - 4}">{trs[0][0][5:]}</text><text x="{W_ - 10}" y="{H_ - 4}" text-anchor="end">{trs[-1][0][5:]}</text></svg>'
                          '<figcaption>네이버 데이터랩 검색어 트렌드(기간 중 최댓값 = 100인 상대값)</figcaption></figure></section>')
        else:
            trend_html = ''
        post = f'<section class="mg-s"><h2>✍️ 루리의 정리 글</h2><div class="nw-pr"><a href="{E2(r["post"])}" target="_blank" rel="noopener"><em>블로그</em><b>{E2(k)} 자세히 정리한 글 보기</b></a></div></section>' if r.get('post') else ''
        css = '<link rel="stylesheet" href="/assets/mag/mag.css?v=10"><link rel="stylesheet" href="/assets/analyst/analyst.css?v=4">'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/kw/">인기 키워드</a> › {E2(k)}</p><h1>🔎 {E2(k)} — 왜 검색이 늘었나</h1><p>{SRCB(r)}</p>'
                + say('o_det_think', ' '.join(lines)) + ((ENH[sl][0] + '<link rel="stylesheet" href="/assets/kw/kw.css?v=2">') if sl in ENH else '') + trend_html + post
                + (f'<section class="mg-s"><h2>📰 왜 떴나: 관련 보도</h2><ul class="kw-l">{why}</ul></section>' if why else '')
                + (f'<section class="mg-s"><h2>🕵️ 관련 기사 확인 신호</h2><ul class="kw-l">{ours}</ul></section>' if ours else '')
                + (f'<section class="mg-s"><h2>📌 루리의 줍줍에서 더 보기</h2><div class="nw-pr">{"".join(links)}</div></section>' if links else '')
                + f'<p class="mg-nav"><a href="/kw/">오늘의 인기 키워드 전체 →</a> · <a href="/mag/">매거진 →</a></p>' + note + css)
        page(f'/kw/{sl}/', f'{k} 검색 급상승 이유 — 관련 보도·정리', f'{k}{josa_ga(k)} 검색 급상승 키워드에 오른 이유: ' + ' / '.join(n['t'] for n in r.get('news', [])[:2])[:140], body,
             [('루리의 줍줍', '/'), ('인기 키워드', '/kw/'), (k, f'/kw/{sl}/')], noindex=not (r.get('post') or (sl in ENH and ENH[sl][1] >= 4)))
        urls.append(f'/kw/{sl}/')
    arch = '<details class="tk-arch"><summary>📅 날짜별 인기 키워드 (최근 90일)</summary><p>' + ''.join(f'<a href="/kw/{d}/">{kdate(d)}</a>' for d in days[:90]) + '</p></details>'
    for i, d in enumerate(days):
        L = json.load(open(os.path.join(ad, d + '.json'), encoding='utf-8'))
        li = ''.join(f'<li><a href="/kw/{x["slug"]}/"><em>{j + 1}</em><b>{E2(x["k"])}</b><span>{SRCB(x)} {E2(x.get("traffic") or "-")} · {E2(x.get("first", ""))} 첫 등장</span></a></li>' for j, x in enumerate([y for y in L if y['slug'] in db]))
        bd = f'<ol class="mg-l">{li}</ol>' + arch + note + css
        play, og_k = '', None
        if i == 0:
            play, og_k = kw_play(db, d, L, ENH)
            bd = play['list'] + arch + note + css
        if i == 0:
            page('/kw/', '오늘의 인기 키워드 — 검색 급상승 이유 정리', f'{kdate(d)} 구글 검색 급상승 키워드와 왜 떴는지: ' + ', '.join(x['k'] for x in L[:6]),
                 f'<p class="bc"><a href="/">홈</a> › 인기 키워드</p><h1>🔎 오늘의 인기 키워드</h1><script defer src="/assets/view/one.js?v=1"></script>' + say('o_det_wave', '구글 급상승 목록과 시그널 순위에 등장한 말을 모았어요. 관련 보도는 배경을 살피는 자료이며 검색 증가 원인을 입증하지는 않아요.') + play['top'] + bd,
                 [('루리의 줍줍', '/'), ('인기 키워드', '/kw/')], og=og_k)
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


DEV_TAGS = {'automation': '자동화', 'ai-agents': 'AI 에이전트', 'seo': '검색·SEO', 'cloudflare': 'Cloudflare', 'static-site': '정적 사이트', 'windows': 'Windows', 'analytics': '방문 집계', 'data': '데이터'}


def _rmin(txt):
    """읽는 시간(분): 글자 수 / 500, 최소 1분."""
    return max(1, round(len(re.sub(r'<[^>]+>', '', txt)) / 500))


def _dev_card(p, rm):
    tg = ''.join(f'<em>#{E(DEV_TAGS.get(t, t))}</em>' for t in p.get('tags', []))
    return (f'<li><a href="{dev_url(p)}"><b>{E(p["title"])}</b><span>{E(p["desc"])}</span>'
            f'<span class="dev-meta">{p["date"]} · 읽는 시간 약 {rm}분 {tg}</span></a></li>')


def dev_blog_pages(P, css):
    """기술 블로그 홈(/dev/)·태그 페이지·RSS (2026-10-20 사용자: 「우리 사이트도 기술 블로그 같은 거 만들어」). 기존 /ailog/ 와 글 주소는 그대로 두고 서로 연결."""
    urls = []
    KO = [p for p in P if p['lang'] == 'ko']
    order = {id(p): i for i, p in enumerate(P)}
    KO.sort(key=lambda p: (p['date'], order[id(p)]), reverse=True)
    rm = {p['slug']: _rmin(open(os.path.join(HERE, 'devsrc', p['slug'] + '.html'), encoding='utf-8').read()) for p in P}
    used = sorted({t for p in KO for t in p.get('tags', [])}, key=lambda t: -sum(t in p.get('tags', []) for p in KO))
    chips = ''.join(f'<a href="/dev/tag/{t}/">#{E(DEV_TAGS.get(t, t))} <small>{sum(t in p.get("tags", []) for p in KO)}</small></a>' for t in used)
    st = '<style>.dev-ch{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.dev-ch a{padding:6px 12px;border:1px solid #e5e7eb;border-radius:99px;text-decoration:none;color:inherit;font-size:.9em}.dev-meta{display:block}.dev-meta em{font-style:normal;margin-left:6px;color:#4f46e5}</style>'
    EN = [p for p in P if p['lang'] == 'en']
    enl = ''.join(f'<li><a href="{dev_url(p)}"><b>{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in sorted(EN, key=lambda p: p['date'], reverse=True)[:6])
    body = ('<p class="bc"><a href="/">홈</a> › 기술 블로그</p><h1>🧑‍💻 루리의 줍줍 기술 블로그</h1>'
            '<p class="cat-st">📌 사람 한 명과 AI 코딩 에이전트로 이 사이트를 운영하며 실제로 겪은 문제와 고친 과정을 「문제 → 원인 → 해결 코드 → 교훈」 순서로 적어요. 실패 사례도 숨기지 않아요.</p>'
            f'<div class="dev-ch" aria-label="태그">{chips}</div>'
            f'<h2>최신 글</h2><ul class="dev-ls">{"".join(_dev_card(p, rm[p["slug"]]) for p in KO)}</ul>'
            + (f'<h2>English guides</h2><ul class="dev-ls">{enl}</ul><p><a href="/en/guide/">All English guides</a></p>' if EN else '')
            + '<p class="hm-links"><a href="/ailog/">🤖 사이트 제작 로그·비용표</a> · <a href="/dev/faq/">❓ 개발 FAQ</a> · <a href="/dev/rss.xml">RSS</a></p>' + st + css)
    page('/dev/', '루리의 줍줍 기술 블로그 — AI 에이전트·자동화·정적 사이트 운영 기록', 'AI 코딩 에이전트와 1인으로 정보 사이트를 운영하며 겪은 문제와 해결을 문제·원인·해결 코드·교훈으로 정리한 기술 블로그. 방문 집계 오염, D1 읽기 한도, 법령 자동 링크, 윈도우 자동화 사고 사례.',
         body, [('루리의 줍줍', '/'), ('기술 블로그', '/dev/')])
    urls.append('/dev/')
    for t in used:
        L = [p for p in KO if t in p.get('tags', [])]
        tb = (f'<p class="bc"><a href="/">홈</a> › <a href="/dev/">기술 블로그</a> › #{E(DEV_TAGS.get(t, t))}</p><h1>#{E(DEV_TAGS.get(t, t))} 글 {len(L)}편</h1>'
              f'<ul class="dev-ls">{"".join(_dev_card(p, rm[p["slug"]]) for p in L)}</ul><p class="hm-links"><a href="/dev/">← 기술 블로그 홈</a></p>' + st + css)
        page(f'/dev/tag/{t}/', f'#{DEV_TAGS.get(t, t)} — 루리의 줍줍 기술 블로그', f'{DEV_TAGS.get(t, t)} 관련 글 {len(L)}편: ' + ' · '.join(p['title'][:30] for p in L[:3]),
             tb, [('루리의 줍줍', '/'), ('기술 블로그', '/dev/'), (f'#{DEV_TAGS.get(t, t)}', f'/dev/tag/{t}/')])
        urls.append(f'/dev/tag/{t}/')
    # RSS (한국어 글 + 영어 글, 최신순)
    allp = sorted(P, key=lambda p: (p['date'], order[id(p)]), reverse=True)
    def rfc(dstr):
        return datetime.datetime.strptime(dstr, '%Y-%m-%d').replace(hour=9).strftime('%a, %d %b %Y %H:%M:%S +0900')
    items = ''.join(f'<item><title>{E(p["title"])}</title><link>{SITE}{dev_url(p)}</link><guid isPermaLink="true">{SITE}{dev_url(p)}</guid><pubDate>{rfc(p.get("updated") or p["date"])}</pubDate>'
                    f'<description>{E(p["desc"])}</description>' + ''.join(f'<category>{E(DEV_TAGS.get(t, t))}</category>' for t in p.get('tags', [])) + '</item>' for p in allp)
    rss = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>루리의 줍줍 기술 블로그</title>'
           f'<link>{SITE}/dev/</link><description>AI 코딩 에이전트와 1인으로 사이트를 운영하며 겪은 문제와 해결 기록</description><language>ko</language>{items}</channel></rss>')
    os.makedirs(os.path.join(ROOT, 'dev'), exist_ok=True)
    open(os.path.join(ROOT, 'dev', 'rss.xml'), 'w', encoding='utf-8', newline='\n').write(rss)
    return urls


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
        _rm = _rmin(body_)
        meta_x = '' if en else f' · 읽는 시간 약 {_rm}분 · 작성 루리의 줍줍 편집'
        tagline_x = '' if en or not p.get('tags') else '<p class="dev-tags">' + ' '.join(f'<a href="/dev/tag/{t}/">#{E(DEV_TAGS.get(t, t))}</a>' for t in p['tags']) + '</p>'
        tail_x = ''
        if not en:
            if p.get('en_summary'):
                tail_x += f'<section lang="en" class="dev-en"><h2>English summary</h2><p>{E(p["en_summary"])}</p></section>'
            rel_ = [q for q in P if q['lang'] == 'ko' and q['slug'] != p['slug'] and set(q.get('tags', [])) & set(p.get('tags', []))][:3]
            if rel_:
                tail_x += '<h2>관련 글</h2><ul class="dev-ls">' + ''.join(f'<li><a href="{dev_url(q)}"><b>{E(q["title"])}</b><span>{E(q["desc"])}</span></a></li>' for q in rel_) + '</ul>'
            tail_x += '<p class="dev-hub"><a href="/dev/">← 기술 블로그 홈</a> · <a href="/ailog/">사이트 제작 로그</a> · <a href="/dev/rss.xml">RSS</a></p>'
        body = (f'<p class="bc"><a href="/">{"Home" if en else "홈"}</a> › <a href="{"/en/guide/" if en else "/dev/"}">{"Guides" if en else "기술 블로그"}</a></p>'
                f'<article class="dev" lang="{p["lang"]}"><h1>{E(p["title"])}</h1><p class="note">{"Published" if en else "작성"} {p["date"]}'
                + (f' · {"updated" if en else "고침"} {p["updated"]}' if p.get('updated') else '') + meta_x + '</p>' + tagline_x
                + body_ + tail_x + (f'<h2>{"Sources" if en else "출처"}</h2><ul>{src}</ul>' if src else '')
                + (f'<p class="dev-hub">{"Related (Korean)" if en else "관련"}: <a href="{E(hub[1])}">{E(hub[0])}</a></p>' if hub else '')
                + ('<p class="dev-hub">Questions about how this was built? <a href="/dev/faq/">Dev FAQ</a></p>' if en else '<p class="dev-hub">이 글에 대해 묻고 싶으면 <a href="/dev/faq/">❓ 개발 FAQ</a>에 남겨 주세요.</p>')
                + share_bar(p['title'], p['desc'], en) + f'</article>{css}<script defer src="/assets/dev/dev.js?v=1"></script>')
        t = p['title'] + ' | Ruri Jupjup' if en and len(p['title']) + 14 <= 70 else p['title']
        ld = {'@context': 'https://schema.org', '@type': 'TechArticle', 'headline': p['title'][:110], 'description': p['desc'], 'inLanguage': p['lang'], 'datePublished': p['date'],
              'dateModified': p.get('updated') or p['date'], 'author': {'@type': 'Organization', 'name': NAME if en else '루리의 줍줍 편집'}, 'publisher': {'@type': 'Organization', 'name': NAME}, 'mainEntityOfPage': SITE + u, **({'keywords': ', '.join(DEV_TAGS.get(t, t) for t in p['tags'])} if p.get('tags') else {})}
        page(u, t, p['desc'], body, [('Home' if en else NAME, '/'), ('Guides' if en else '기술 블로그', '/en/guide/' if en else '/dev/'), (p['title'], u)], ld=ld, full_title=en, lang=p['lang'])
        urls.append(u)
    urls += dev_faq_page(P)
    urls += dev_blog_pages(P, css)
    EP = [p for p in P if p['lang'] == 'en']
    if EP:
        li = ''.join(f'<li><a href="{dev_url(p)}"><b>{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in sorted(EP, key=lambda p: p['date'], reverse=True))
        li = '<li><a href="/en/guide/new-game-releases-steam/"><b>New Game Releases on Steam: Confirmed Release Dates</b><span>Popular upcoming Steam games with a confirmed release day, updated several times a day.</span></a></li>' + li
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
    SER = {}
    for p in DP:   # 2026-10-20 시리즈 섹션 (dev_posts.json 의 series 칸)
        if p.get('series'):
            SER.setdefault(p['series'], []).append(p)
    dli = ''.join(f'<li><a href="{dev_url(p)}"><b>{"[EN] " if p["lang"] == "en" else ""}{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in DP if not p.get('series'))
    dli = ''.join(f'</ul><h3>🔗 시리즈: {E(k)}</h3><ul class="dev-ls">' + ''.join(f'<li><a href="{dev_url(p)}"><b>{E(p["title"])}</b><span>{E(p["desc"])}</span></a></li>' for p in sorted(v, key=lambda p: p['date'])) + '</ul><h3>그 밖의 글</h3><ul class="dev-ls">' for k, v in SER.items()) + dli
    body = (f'<p class="bc"><a href="/">홈</a> › 개발 지식</p><h1>🧑‍💻 개발 지식 — 직접 해 보고 정리한 AI·개발 가이드</h1><p class="note">글 모음은 <a href="/dev/">기술 블로그</a>(태그·RSS)에서도 볼 수 있어요. <a href="/dev/rss.xml">RSS</a></p>'
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
         '사람 한 명의 말과 AI(Claude Code)로 만든 정보 사이트의 개발 기록. 색인 대상 페이지를 10/18 3,744개→1,311개, 10/19 1,446개→863개로 줄이며 얇은 페이지를 합친 과정과 서버비 0원 운영법.',   # 2026-10-19 확인값으로 고정(디스크 파일 수는 이동·검색 제외 페이지까지 세서 뺌)
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


EXP_SER = {'미국 증시': 'sp500', '반도체·AI': 'nasdaq', '금리': 'us10y', '환율': 'usdkrw', '코인': 'btc', '원자재': 'wti'}   # 주제 → 시세(market.py). 없으면 발언 타임라인만
EXP_SER_NOTE = {'반도체·AI': '반도체 지수는 무료 공개 출처가 없어 기술주 비중이 큰 나스닥 종합으로 대신 봐요.', '금리': '한국 국고채는 아직 연결 전이라 미국 국채 10년 금리로 봐요.'}


def exp_all():
    """전문가 발언 전체(30일, 같은 제목 1번) — analyst_db.json."""
    db = _rd('_gongmo/analyst_db.json') or {}
    cut = time.time() - 30 * 86400
    seen, out = set(), []
    for n in sorted([n for n in (db.get('nodes') or {}).values() if n.get('k') == 'expert' and n['ts'] >= cut], key=lambda n: -n['ts']):
        if n['t'] in seen:
            continue
        seen.add(n['t'])
        out.append(n)
    return out


def exp_hit(n, MK):
    """발언 뒤 7일·30일 실제 등락(사실만). 반환 (c7, c30, 판정문구)"""
    import market as M
    s = (MK.get('s') or {}).get(EXP_SER.get(n['topic'], ''))
    if not s:
        return None, None, ''
    d0 = datetime.datetime.fromtimestamp(n['ts']).strftime('%Y-%m-%d')
    c7, c30 = M.chg(s, d0, 7), M.chg(s, d0, 30)
    if c7 is None:
        due = (datetime.date.fromisoformat(d0) + datetime.timedelta(days=7)).strftime('%m/%d')
        return None, None, f'7일 뒤({due}) 확인 예정'
    t = f'7일 뒤 {s["name"]} {c7:+.1f}%' + (f' · 30일 뒤 {c30:+.1f}%' if c30 is not None else '')
    if n['dir'] in ('bull', 'bear'):
        ok = (c7 > 0) == (n['dir'] == 'bull')
        t += ' ✅ 발언 방향대로' if ok else ' ↔️ 발언 방향과 반대'
    return c7, c30, t


def exp_svg(s, ns, tid):
    """30일 선 그래프 + 발언 점(🟢🔴⚪). 점을 누르면 아래에 발언 제목·기관·원문 링크."""
    import market as M
    pts = s['pts'][-30:]
    if len(pts) < 5:
        return ''
    W, H, L, R, T, B = 640, 190, 8, 8, 18, 26
    lo, hi = min(y for _, y in pts), max(y for _, y in pts)
    hi = hi if hi > lo else lo + 1
    d0 = datetime.date.fromisoformat(pts[0][0])
    endd = max([datetime.date.fromisoformat(pts[-1][0]), datetime.date.today()] + [datetime.datetime.fromtimestamp(n['ts']).date() for n in ns])
    span = max((endd - d0).days, 1)   # 시세가 아직 없는 최근 며칠도 칸을 둬서 발언 점이 겹치지 않게
    X = lambda d: L + (W - L - R) * (datetime.date.fromisoformat(d) - d0).days / span
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    path = 'M' + ' L'.join(f'{X(d):.1f},{Y(v):.1f}' for d, v in pts)
    col = {'bull': '#16a34a', 'bear': '#dc2626', 'neutral': '#94a3b8'}
    dots, info = '', ''
    for i, n in enumerate(ns):
        d = datetime.datetime.fromtimestamp(n['ts']).strftime('%Y-%m-%d')
        if d < pts[0][0]:
            continue
        a = M.val_at(s, d)
        if not a:
            continue
        x = min(X(d), W - R - 7)
        same = sum(1 for m in ns[:i] if datetime.datetime.fromtimestamp(m['ts']).strftime('%Y-%m-%d') == d)   # 같은 날 발언은 위로 비켜 찍기
        dots += (f'<circle cx="{x:.1f}" cy="{max(Y(a[1]) - same * 15, 8):.1f}" r="7" fill="{col[n["dir"]]}" stroke="#fff" stroke-width="2"' + (' fill-opacity=".55"' if d > pts[-1][0] else '') + f' data-i="{tid}-{i}" tabindex="0" role="button">'
                 f'<title>{E(d[5:])} {E(n["who"])}: {E(n["t"])}</title></circle>')
        info += (f'<p class="xc-i" id="{tid}-{i}" hidden>{ECOL[n["dir"]][0]} <b>{E(d[5:].replace("-", "/"))} {E(n["who"])}</b> {E(n["t"])} '
                 f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["o"])} 원문 →</a></p>')
    f = lambda v: f'{v:,.2f}' if v < 100 else f'{v:,.0f}'
    return (f'<figure class="xc"><svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(s["name"])} 최근 30거래일">'
            f'<path d="{path}" fill="none" stroke="var(--pri,#047857)" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<text x="{L}" y="12" font-size="12" fill="currentColor" opacity=".7">최고 {f(hi)}</text><text x="{L}" y="{H - 30}" font-size="12" fill="currentColor" opacity=".7">최저 {f(lo)}</text>'
            f'<text x="{L}" y="{H - 6}" font-size="12" fill="currentColor" opacity=".7">{pts[0][0][5:].replace("-", "/")}</text>'
            f'<text x="{W - R}" y="{H - 6}" font-size="12" fill="currentColor" opacity=".7" text-anchor="end">{pts[-1][0][5:].replace("-", "/")} {f(pts[-1][1])}{E(s["unit"]) if s["unit"] != "pt" else ""}</text>{dots}<line x1="{X(pts[-1][0]):.1f}" y1="{T}" x2="{X(pts[-1][0]):.1f}" y2="{H - B}" stroke="currentColor" stroke-dasharray="3 4" opacity=".35"/></svg>'
            f'<figcaption>{E(s["name"])} 최근 30거래일 · 출처 {E(s["src"])} · 점 = 전문가 발언(🟢 낙관 🔴 신중 ⚪ 중립), 눌러서 보기 · 점선 오른쪽은 아직 시세가 안 나온 날(흐린 점)</figcaption>{info}</figure>')


EXP_JS = ('<script>document.addEventListener("click",function(e){var c=e.target.closest&&e.target.closest("circle[data-i]");if(!c)return;var f=c.closest("figure");'
          'f.querySelectorAll(".xc-i").forEach(function(p){p.hidden=p.id!==c.dataset.i});});'
          'document.addEventListener("keydown",function(e){if(e.key==="Enter"&&e.target.matches&&e.target.matches("circle[data-i]"))e.target.dispatchEvent(new MouseEvent("click",{bubbles:true}))});</script>')
EXP_CSS = ('<style>.xc{margin:10px 0}.xc svg{width:100%;height:auto;display:block;color:var(--tx,#111)}.xc circle{cursor:pointer}.xc figcaption{font-size:12px;color:var(--mu,#6b7280);margin-top:4px}'
           '.xc-i{margin:8px 0 0;padding:10px 12px;border-radius:10px;background:var(--pbg,#f1f5f9);font-size:14px;line-height:1.55}.xc-i a{white-space:nowrap}'
           '.xg{display:flex;height:14px;border-radius:999px;overflow:hidden;margin:8px 0}.xg i{display:block}.xs{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:8px 0}'
           '.xh{font-size:13px;color:var(--mu,#6b7280);display:block;margin-top:2px}.xb{width:100%;border-collapse:collapse;font-size:14px}.xb th,.xb td{border-bottom:1px solid var(--bd,#e5e7eb);padding:6px 4px;text-align:left}</style>')


def experts_v2(an):
    """「말 vs 실제」 (2026-10-20 사용자 「시세 흐름을 본다든가 재밌게」): 요약 카드 → 주제별 30일 차트+발언 점+생활 영향 → 적중 보드."""
    import market as M, impact as IP
    MK = M.load()
    S = MK.get('s') or {}
    A = exp_all()
    now = time.time()
    w7 = [n for n in A if n['ts'] >= now - 7 * 86400]
    bu, be, ne = (sum(1 for n in w7 if n['dir'] == k) for k in ('bull', 'bear', 'neutral'))
    tot = max(bu + be + ne, 1)
    mv = ' · '.join(f'{S[k]["name"]} {M.last_chg(S[k]):+.1f}%' for k in ('sp500', 'nasdaq', 'usdkrw', 'btc', 'wti') if k in S and M.last_chg(S[k]) is not None)
    top = (f'<section class="mg-s"><h2>🌡️ 이번 주 시장 분위기</h2><p>최근 7일 전문가 발언 {len(w7)}건 · 🟢 낙관 {bu} · 🔴 신중 {be} · ⚪ 중립 {ne}</p>'
           f'<div class="xg" aria-hidden="true"><i style="width:{bu / tot * 100:.0f}%;background:#16a34a"></i><i style="width:{ne / tot * 100:.0f}%;background:#cbd5e1"></i><i style="width:{be / tot * 100:.0f}%;background:#dc2626"></i></div>'
           + (f'<p class="xs">📈 같은 기간 실제 시세(최근 거래일 기준 7일 등락): {E(mv)}</p>' if mv else '')
           + '<p class="xh">코스피·국고채는 무료 공개 시세 출처를 아직 연결하지 못해 발언만 보여 줘요.</p></section>')
    topics = []
    for tp, _ in [(e['topic'], 0) for e in an.get('experts', [])] + [(k, 0) for k in EXP_SER]:
        if tp not in topics:
            topics.append(tp)
    cards = ''
    for tp in topics:
        ns = [n for n in A if n['topic'] == tp]
        s = S.get(EXP_SER.get(tp, ''))
        if not ns and not s:
            continue
        chart = exp_svg(s, ns, 'x' + hashlib.md5(tp.encode()).hexdigest()[:6]) if s else '<p class="xh">이 주제는 공개 시세 출처가 없어 발언 타임라인만 보여 줘요.</p>'
        li = ''
        for n in ns[:8]:
            _, _, ht = exp_hit(n, MK)
            dt = datetime.datetime.fromtimestamp(n['ts']).strftime('%m/%d')
            li += (f'<li class="{n["dir"]}"><span class="an-d">{ECOL[n["dir"]][0]}</span><div><small>{dt} · {E(n["who"])} · {E(n["cat"])}</small>'
                   f'<a href="{E(n["u"])}" target="_blank" rel="noopener nofollow">{E(n["t"])}</a><em>{E(n["o"])}</em>' + (f'<span class="xh">→ {E(ht)}</span>' if ht else '') + '</div></li>')
        d0 = datetime.datetime.fromtimestamp(ns[0]['ts']).strftime('%Y-%m-%d') if ns else None
        cards += (f'<article class="an-c" id="t-{E(tp)}"><div class="an-h"><h3>{E(tp)}</h3></div>'
                  + (f'<p class="xh">{E(EXP_SER_NOTE[tp])}</p>' if tp in EXP_SER_NOTE and s else '') + chart
                  + (f'<ul class="an-nodes">{li}</ul>' if li else '<p class="xh">최근 30일 이 주제의 전문가 발언은 아직 없어요.</p>')
                  + IP.card(tp + ' ' + ' '.join(n['t'] for n in ns[:3]), d0, [(n['o'], n['t']) for n in ns[:3]], MK) + '</article>')
    # 적중 보드: 방향(낙관·신중)이 있고 7일이 지난 발언만
    by = {}
    for n in A:
        c7, _, _ = exp_hit(n, MK)
        if c7 is None or n['dir'] not in ('bull', 'bear'):
            continue
        by.setdefault(n['who'], []).append((c7 > 0) == (n['dir'] == 'bull'))
    rk = sorted([(w, sum(v), len(v)) for w, v in by.items() if len(v) >= 5], key=lambda x: (-x[1] / x[2], -x[2]))
    small = sorted([(w, sum(v), len(v)) for w, v in by.items() if len(v) < 5], key=lambda x: -x[2])[:8]
    board = ('<section class="mg-s" id="board"><h2>🎯 전문가 적중 보드</h2><p class="xh">낙관·신중 방향이 있는 발언만, 발언일 기준값과 7일 뒤 값을 비교한 사실이에요. 7일이 안 지난 발언은 확인 예정이에요. 시장은 발언 하나로 움직이지 않으니 재미로 봐 주세요.</p>'
             + (('<table class="xb"><thead><tr><th>기관·인물</th><th>방향대로 움직임</th><th>표본</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(w)}</td><td>{k}/{n_}건 ({k / n_ * 100:.0f}%)</td><td>{n_}건</td></tr>' for w, k, n_ in rk) + '</tbody></table>') if rk
                else f'<p>순위표는 판정된 발언이 5건 이상인 기관만 넣어요. 아직 5건을 넘은 곳이 없어요(판정된 발언 {sum(len(v) for v in by.values())}건).</p>')
             + (('<p class="xh">표본이 적은 곳: ' + ' · '.join(f'{E(w)} {k}/{n_}건' for w, k, n_ in small) + '</p>') if small else '') + '</section>')
    return top + cards + board + EXP_CSS + EXP_JS


def money_pages():
    # 머니 테마 정보 섹션 (2026-10-18 사용자: "주식 관련해서도 정책 등, 나이별 포트폴리오 전략 등을 넣고 전문가들 이야기도 넣어서" — 연구 ⑂ 기획)
    an = _rd('analyst/data.json')
    ex = an.get('experts', [])
    css = '<link rel="stylesheet" href="/assets/analyst/analyst.css?v=4"><link rel="stylesheet" href="/assets/mag/mag.css?v=10">'
    urls = []
    how = ('<details class="an-how"><summary>어떻게 모았나요?</summary><ol><li>증권·경제 기사 RSS에서 리서치센터장·CIO·이코노미스트·한국은행·KDI·IMF·월가 기관 등 실명 기관·인물의 발언이 제목에 나온 기사만 골라요.</li>'
           '<li>주제(코스피·미국 증시·금리·환율·반도체·부동산·경기·코인·원자재·기타 시장)와 성격(시장 전망·자산배분 조언·리스크 경고)으로 나눠요.</li><li>발언(따옴표) 부분으로 긍정·신중을 가려, 같은 주제에서 둘 다 있으면 나란히 보여 줘요.</li>'
           '<li>기사 본문은 옮기지 않고 제목(발언 요지)과 원문 링크만 실어요.</li></ol></details>')
    page('/money/experts/', '전문가 말 vs 실제 시세 — 발언 뒤 시장은 어떻게 움직였나',
         '리서치센터장·월가·한은·IMF 등 실명 전문가 발언을 S&P500·나스닥·환율·금리·유가·비트코인 30일 차트 위에 찍고, 발언 뒤 7일·30일 실제 등락과 내 생활에 미칠 수 있는 영향을 함께 보여 줘요.',
         '<p class="bc"><a href="/">홈</a> › <a href="/analyst/">머니</a> › 전문가 코멘트</p><h1>🎙️ 전문가 말 vs 실제 시세</h1>'
         + (f'<p class="cat-st">📡 마지막 수집 {E(an.get("updated", "")[-5:])} · 최근 24시간 {an["exp_meta"]["n24"]}건 · 최근 14일 {an["exp_meta"]["n14"]}건 · 매시간 갱신</p>' if an.get('exp_meta') else '') + MONEY_NOTE
         + join_cta('money') + (experts_v2(an) or '<p class="nw-empty">아직 모인 발언이 없어요. 매시간 새로 모아요.</p>') + how + css,
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


def news_impact():
    """/news/ 아래 이번 주 이슈 평론 (생활 영향 카드는 위 브리핑에 이미 들어 있어서 겹치지 않게 뺌, 2026-10-20 화면 정리)."""
    wk = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    rv = ''.join(f'<li><a href="/review/{x["slug"]}/">🖋️ {E2(x["title"])}</a></li>' for x in load_reviews() if x['date'] >= wk)
    return f'<section class="mg-s" id="review"><h2>🖋️ 이번 주 이슈 평론</h2><ul class="mg-l">{rv}</ul></section>' if rv else ''


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
TOOL_SRC = {  # 기준일·출처 (2026-10-18 확인, 2026-10-20 조문·원문 링크로 교체)
 'salary': '국민연금 본인 4.75%(보험료율 9.5%): <a href="https://www.law.go.kr/법령/국민연금법" target="_blank" rel="noopener">국민연금법 부칙 제4조(법률 제20903호)</a> · 기준소득월액 상·하한 41만~659만원(2026.7~2027.6): <a href="https://www.nps.or.kr" target="_blank" rel="noopener">국민연금공단</a> 고시, 이 상·하한 금액은 원문으로 확인하지 못했어요), 건강보험료율 7.19%: <a href="https://www.law.go.kr/법령/국민건강보험법시행령/제44조" target="_blank" rel="noopener">국민건강보험법 시행령 제44조 제1항</a>(1만분의 719, 직장가입자와 사업주가 각 50%: 국민건강보험법 제76조 제1항 → 근로자 3.595%), 장기요양 0.9448%: <a href="https://www.law.go.kr/법령/노인장기요양보험법시행령/제4조" target="_blank" rel="noopener">노인장기요양보험법 시행령 제4조</a>(100만분의 9,448 = 0.9448%, 2025.12.30 개정). 노사 분담 조문은 확인하지 못했어요, 고용보험 근로자 0.9%: <a href="https://www.law.go.kr/법령/고용보험및산업재해보상보험의보험료징수등에관한법률시행령/제12조" target="_blank" rel="noopener">고용보험·산재보험료징수법 시행령 제12조 제1항 제2호</a>(실업급여 보험료율 1천분의 18, 근로자 부담은 그 2분의 1: 고용보험·산재보험료징수법 제13조 제2항 → 0.9%), 소득세: <a href="https://www.law.go.kr/법령/소득세법/제55조" target="_blank" rel="noopener">소득세법 제55조</a>(기본세율)·<a href="https://www.law.go.kr/법령/소득세법/제47조" target="_blank" rel="noopener">제47조</a>(근로소득공제 표)·소득세법 제50조(기본공제 1명당 연 150만원) · <b>2027.1.1부터</b>: 국민연금 본인 부담 5.0%(<a href="https://www.law.go.kr/법령/국민연금법" target="_blank" rel="noopener">국민연금법 부칙 제4조</a> 2027년 1만분의 500), 최저임금 10,700원(<a href="https://www.law.go.kr/flDownload.do?flSeq=167847381" target="_blank" rel="noopener">고시 제2026-60호</a>). 이 계산기는 2026년 요율 기준이에요',
 'severance': '<a href="https://www.law.go.kr/법령/근로자퇴직급여보장법/제8조" target="_blank" rel="noopener">근로자퇴직급여 보장법 제8조</a>(평균임금 30일분 × 근속연수), <a href="https://www.law.go.kr/법령/소득세법/제48조" target="_blank" rel="noopener">소득세법 제48조</a>(퇴직소득공제: 근속연수공제·환산급여공제)',
 'unemployment': '<a href="https://www.law.go.kr/법령/고용보험법시행령/제68조" target="_blank" rel="noopener">고용보험법 시행령 제68조</a>(임금일액 상한 113,500원 → 구직급여 상한 68,100원, 2026.1.1 이후 이직자), <a href="https://www.law.go.kr/법령/고용보험법/제46조" target="_blank" rel="noopener">고용보험법 제46조</a>(구직급여일액 60%·최저구직급여일액 80%), <a href="https://www.law.go.kr/법령/고용보험법/제50조" target="_blank" rel="noopener">고용보험법 제50조</a>(소정급여일수 별표 1), 2026년 최저임금 시급 10,320원: <a href="https://www.law.go.kr/flDownload.do?flSeq=155278071" target="_blank" rel="noopener">고용노동부 고시 제2025-47호(원문 PDF 확인)</a> · <b>2027.1.1부터</b> 최저임금 10,700원(<a href="https://www.law.go.kr/flDownload.do?flSeq=167847381" target="_blank" rel="noopener">고시 제2026-60호 원문 PDF</a>)이 적용돼 하한 산식값이 올해 66,048원과 달라져요(산식값 68,480원, 상한 개편 반영 여부는 확인 필요)',
 'dividend': '<a href="https://www.law.go.kr/법령/조세특례제한법/제104조의27" target="_blank" rel="noopener">조세특례제한법 제104조의27</a>(고배당기업 배당소득 분리과세)',
 'stocktax': '<a href="https://www.law.go.kr/법령/증권거래세법시행령/제5조" target="_blank" rel="noopener">증권거래세법 시행령 제5조</a>(2026.1.1 시행 개정 세율)',
 'pension': '<a href="https://www.law.go.kr/법령/소득세법/제59조의3" target="_blank" rel="noopener">소득세법 제59조의3</a>(연금계좌세액공제)',
 'loan': '원리금 계산 공식(금리는 직접 입력)', 'fx': '은행 환전 수수료 공식(환율은 직접 입력)'}
TOOL_DATE = {'unemployment': '2026-10-21', 'stocktax': '2026-10-21', 'dividend': '2026-10-21', 'salary': '2026-10-21'}   # 조문·고시 원문을 실제로 대조한 계산기만 날짜를 올림(2026-10-21)
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


# 쿠팡 파트너스 (2026-10-19 사용자 지시 「우리 사이트도 연결해버려」): 링크·주제 규칙은 tools/promo_share/coupang.json
_CPJ = os.path.expanduser('~/tools/promo_share/coupang.json')
CP = json.load(open(_CPJ, encoding='utf-8')) if os.path.exists(_CPJ) else {}


def cp_box(text, title='함께 보면 좋은 물건:', n=2, fill='', body='', want='', strict=False):
    """광고 박스 한 곳. 링크 rel=sponsored nofollow, 공정위 문구는 링크 바로 아래. 팝업·자동 이동 없음.
    text 에 맞는 규칙(coupang.json rules 순서)을 먼저, 모자라면 fill 에 맞는 규칙으로 채움(레시피: 메뉴별 도구 → 일반 요리 도구)."""
    if not CP.get('on'):
        return ''
    items = []
    for t in (text, fill):
        for r in CP.get('rules', []):
            if len(items) >= n:
                break
            hit = any((re.search(re.escape(k) + r'(?:\s|$)', t) if len(k) == 1 else k in t) for k in r['kw']) or (t is text and any(len(k) >= 3 and k in body for k in r['kw']))   # 한 글자(국·탕·찜)는 낱말 끝에서만(국수·그라탕 제외), body(만드는 법)는 3글자 이상 도구 이름만
            if t and hit and not (t is text and fill and any(k in fill for k in r['kw'])):
                items += [x for x in r['items'] if x not in items]
    if want:
        items = [x for x in items if want in x['name']] + [x for x in items if want not in x['name']]
    items = (items or ([] if strict else CP.get('default', [])))[:n]   # strict: 맞는 규칙이 없으면 아무것도 안 붙임(게임·취미 페이지)
    if not items:
        return ''
    lk = ', '.join(f'<a class="cp-in" href="{E(x["url"])}" target="_blank" rel="sponsored nofollow noopener">{E(x["name"])}</a>' for x in items)
    return (f'<p class="cp-line">{E(title)} {lk}<small class="cp-inn">쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</small></p>'
            '<style>.cp-line{margin:12px 0;line-height:1.7}.cp-in{color:#c2410c;font-weight:700;text-decoration:underline;text-underline-offset:3px}.cp-inn{display:block;font-size:12px;color:var(--mu,#6b7280)}</style>')


_CPW_F = os.path.join(HERE, 'cp_widget_cache.json')
_CPW = {}


def cp_items(key, sub):
    """쿠팡 다이나믹 배너(widget_ids)의 상품을 하루 1번 받아 둠 → 우리 HTML 카드로 그림(2026-10-19 사용자 화면에서 iframe 이 차단돼 「이미지 안 나와」)."""
    global _CPW
    wid = (CP.get('widget_ids') or {}).get(key) if CP.get('on') else None
    if not wid:
        return []
    if not _CPW:
        _CPW = (json.load(open(_CPW_F, encoding='utf-8')) if os.path.exists(_CPW_F) else {}) or {'_': 1}
    k = f'{wid}|{sub}'
    c = _CPW.get(k)
    if not c or c.get('d') != TODAY.isoformat():
        try:
            import urllib.request
            u = f'https://ads-partners.coupang.com/widgets.html?id={int(wid)}&template=carousel&trackingCode={CP.get("partner_id", "")}&subId={sub}&width=680&height=140'
            h = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read().decode('utf-8', 'replace')
            m = re.search(r'Carousel\("#container", (\{.*?\})\);', h, re.S)
            its = [{'name': x['name'], 'img': x['imagePath'], 'url': x['landingUrl']} for x in json.loads(m.group(1))['items'] if x.get('landingUrl', '').startswith('https://link.coupang.com/')]
            if its:
                seen_ = set(); its = [x for x in its if not (x['name'] in seen_ or seen_.add(x['name']))]   # 같은 상품 중복 제거
                c = _CPW[k] = {'d': TODAY.isoformat(), 'items': its[:3]}
                json.dump(_CPW, open(_CPW_F, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception as e:
            print('쿠팡 상품 받기 실패', key, sub, e)
    return (c or {}).get('items', [])


def cp_widget(key, sub, note='이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.'):
    """상품 카드 2~3개(사진·이름·「쿠팡에서 보기」, 가격은 바뀌니 안 씀). 사진이 안 뜨면 이름 링크만 남음. 고지는 바로 아래."""
    its = cp_items(key, sub)
    if not its:
        return ''
    cards = ''.join(f'<a class="rp-it" href="{E(x["url"])}" target="_blank" rel="sponsored nofollow noopener">'
                    f'<img src="https://thumbnail.coupangcdn.com/thumbnails/remote/230x230ex/{E(x["img"])}" width="115" height="115" loading="lazy" decoding="async" alt="" onerror="this.remove()">'
                    f'<span>{E(x["name"][:40])}</span><em>쿠팡에서 보기 →</em></a>' for x in its)
    return (f'<div class="rp-tools"><div class="rp-row">{cards}</div><p class="cp-inn">{note}</p></div>'
            '<style>.rp-tools{margin:14px 0}.rp-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.rp-it{display:flex;flex-direction:column;gap:4px;padding:8px;border:1px solid var(--bd,#e5e7eb);border-radius:12px;background:var(--card,#fff);color:var(--tx,#111);text-decoration:none}'
            '.rp-it img{width:100%;height:auto;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:8px}.rp-it span{font-size:13px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'
            '.rp-it em{font-style:normal;font-size:12px;font-weight:700;color:#c2410c}.cp-inn{font-size:12px;color:var(--mu,#6b7280);margin:6px 0 0}</style>')


def cp_recipe_widget(r):
    txt = ' '.join(r['s'])
    if '에어프라이어' in txt:
        return '에어프라이어'
    if re.search(r'(찌개|국|탕|전골)$', r['n']) or re.search(r'뚝배기|냄비', txt):
        return '냄비·뚝배기'
    return '밀키트'


CP_TOOLS = ('에어프라이어', '전자레인지', '뚝배기', '냄비', '찜기', '믹서', '프라이팬')   # 만드는 법 문장 속 도구 이름에 거는 쿠팡 링크 (2026-10-19 사용자 「이렇게 붙이면 누가 누르냐」)


def cp_tool_url(w):
    for r in CP.get('rules', []) if CP.get('on') else []:
        if w in r['kw'] or any(w in x['name'] for x in r['items']):
            return next((x['url'] for x in r['items'] if w in x['name']), r['items'][0]['url'])
    return ''


def cp_inline(html_, used):
    """이미 이스케이프된 문장에서 도구 이름 첫 등장 1곳에 링크. used: 이 페이지에서 건 도구(같은 도구는 한 번, 페이지당 2개까지)."""
    if len(used) >= 2:
        return html_
    for w in CP_TOOLS:
        if w in used or w not in html_:
            continue
        u = cp_tool_url(w)
        if u:
            used.add(w)
            return html_.replace(w, f'<a class="cp-in" href="{E(u)}" target="_blank" rel="sponsored nofollow noopener">{w}</a>', 1)
    return html_


CP_IN_NOTE = ('<p class="cp-inn">밑줄 친 도구 이름은 쿠팡 파트너스 링크로, 이에 따른 일정액의 수수료를 제공받습니다.</p>'
              '<style>.cp-in{color:#c2410c;font-weight:700;text-decoration:underline;text-underline-offset:3px}.cp-inn{font-size:12px;color:var(--mu,#6b7280);margin:4px 0 16px}</style>')


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
            f'<p class="note">기준일 {TOOL_DATE.get("salary", "2026-10-18")} · 출처: {TOOL_SRC["salary"]}. 참고용 계산이며 회사 간이세액표와 소득세가 조금 다를 수 있어요.</p>'
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
            + f'<p class="note">기준일 {TOOL_DATE.get(k, "2026-10-18")} · 출처: {TOOL_SRC.get(k, "")}. 참고용 계산이에요. 실제 금액은 해당 기관 안내로 확인하세요.</p>' + rel_block(*TOOL_REL.get(k, ('', [])))
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
    import impact as IPC, market as M_
    MKH = M_.load()
    RVS = load_reviews()   # 이 핫이슈를 다룬 평론으로 연결
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
                + f'<section class="mg-s"><h2>🙋 나한테 뭐가 달라지나</h2><p>{E(lead)}</p><div class="nw-pr">{tl}</div>'
                + IPC.card(v['title'] + ' ' + v['q'] + ' ' + ' '.join(w['t'] for w in v['what'][:3]), (v.get('first') or '')[:10] or None, [(w['o'], w['t']) for w in v['what']], MKH) + '</section>' + sig
                + ''.join(f'<p class="hm-links"><a href="/review/{x["slug"]}/">🖋️ 이 이슈 평론: {E(x["title"])} →</a></p>' for x in RVS if any(u == f'/hot/{v["slug"]}/' for u, _ in x['rel']))
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


def news_brief():
    """📺 루리 뉴스 — 오늘의 브리핑 (2026-10-20 사용자 「쇼츠 제목은 루리 뉴스, 뉴스 섹션도 제대로」). 이슈 5개를 기사 제목·숫자·언론사 표현 차이로 정리한다.
    사실은 기사 제목 그대로(언론사 표기), 해석·편들기 없음, 사고·사망 제외. 같은 내용을 news/brief.json 으로도 내보내 쇼츠 대본에 씀."""
    d = _rd('news/data.json')
    if not d or not d.get('issues'):
        return ''
    import impact as IPB, market as MKB
    MKv = MKB.load()
    I = {a['id']: a for a in d.get('items', [])}
    hot_db = _rd('hot/db.json') or {}
    hot_by = {(v.get('issue') or {}).get('n'): v['slug'] for v in hot_db.values() if not v.get('dup') and v.get('issue')}
    ok = [x for x in d['issues'] if int(x.get('on') or 0) >= 3 and not re.search(r'사망|숨져|숨진|사고|참사|화재|추락|살해|피살', x['t']) and x.get('c') != '연예']
    ok = sorted(ok, key=lambda x: -int(x['on']))
    pick, cats = [], collections.Counter()
    for x in ok:
        if cats[x.get('c')] >= 2:   # 한 분야가 브리핑을 채우지 않게
            continue
        if any(len(set(x['t'].split()) & set(y['t'].split())) >= 4 for y in pick):
            continue
        pick.append(x); cats[x.get('c')] += 1
        if len(pick) >= 5:
            break
    if not pick:
        return ''
    G = {'ok': '✅', 'warn': '🟡', 'bad': '🔴'}
    out, js = '', []
    for i, x in enumerate(pick, 1):
        arts = [I[a] for a in x['a'] if a in I]
        seen, by = set(), []
        for a in arts:   # 언론사별 제목(같은 언론사는 1건)
            if a['o'] not in seen:
                seen.add(a['o']); by.append(a)
        lead = by[0] if by else None
        if not lead:
            continue
        ns = [(a['o'], n_) for a in by for n_ in IPB.nums_in(a['t'])][:3]
        tsl = sorted([a for a in by if a.get('ts') and int(a['ts']) <= time.time()], key=lambda a: int(a['ts']))
        tl_ = (f'<p><b>흐름</b> 처음 보도 {datetime.datetime.fromtimestamp(int(tsl[0]["ts"])).strftime("%m/%d %H:%M")}({E2(tsl[0]["o"])}) → 최근 {datetime.datetime.fromtimestamp(int(tsl[-1]["ts"])).strftime("%m/%d %H:%M")}({E2(tsl[-1]["o"])}) · 모은 기사 기준이에요</p>' if len(tsl) >= 2 else '')
        _tx = x['t'] + ' ' + ' '.join(a['t'] for a in by[:3])
        ipc = IPB.card(_tx, datetime.datetime.fromtimestamp(int(x['ts'])).strftime('%Y-%m-%d') if x.get('ts') else None, [(a['o'], a['t']) for a in by], MKv, head='체감도와 영향')
        ipc = (f'<details class="nbd"><summary>🙋 내 생활엔? <small>{E2(IPB.gauge_text(_tx))}</small></summary>{ipc}</details>' if ipc else '')
        links = ''
        if x['n'] in hot_by:
            links += f'<a href="/hot/{hot_by[x["n"]]}/">🔥 핫이슈 정리</a> '
        links += f'<a href="#is{x["n"]}">🕵️ 기사별 확인 신호</a>'
        _li = lambda L_: ''.join(f'<li><em>{E2(a["o"])}</em><a href="{E2(a["u"])}" target="_blank" rel="noopener nofollow">{E2(a["t"])}</a></li>' for a in L_)
        li = _li(by[:2])
        more_li = (f'<details class="nbd"><summary>언론사 제목 {len(by[2:5])}개 더 보기</summary><ul class="kw-l nbl">{_li(by[2:5])}</ul></details>' if len(by) > 2 else '')
        out += (f'<article class="nb"><h3>{i}. {E2(x["t"])}</h3><p class="kwn">{E2(x.get("c") or "")} · 언론사 {x["on"]}곳이 보도 · 확인 신호 {G.get(x.get("g"), "")} {x.get("s") if x.get("s") is not None else "-"}점'
                f'{" · 발언·주장 기사" if x.get("claim") else ""}</p>'
                f'{tl_}<ul class="kw-l nbl">{li}</ul>{more_li}'
                + (f'<p>🔢 <b>기사에 나온 숫자</b> ' + ' · '.join(f'{E2(o)} 「{E2(n_)}」' for o, n_ in ns) + (f' <span class="kwn">— 숫자가 엇갈림: {E2(", ".join(x["cf"][:3]))}</span>' if x.get('cf') else '') + '</p>' if ns else '')
                + ipc + f'<p class="hm-links">{links}</p></article>')
        t_ = f'{x["t"]}. 언론사 {x["on"]}곳이 전했어요. ' + ' '.join(f'{a["o"]}는 "{a["t"][:40]}"라고 썼어요.' for a in by[:2])
        if ns:
            t_ += ' 기사에 나온 숫자는 ' + ', '.join(f'{o} {n_}' for o, n_ in ns[:2]) + '예요.'
        js.append({'n': x['n'], 'headline': x['t'], 'cat': x.get('c'), 'outlets': x['on'], 'script': t_, 'sources': [{'o': a['o'], 't': a['t'], 'u': a['u']} for a in by[:3]]})
    try:
        json.dump({'title': '루리 뉴스', 'date': TODAY.isoformat(), 'updated': NOW_KST().strftime('%Y-%m-%d %H:%M'), 'items': js}, open(os.path.join(ROOT, 'news', 'brief.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    except Exception:
        pass
    return ('<section class="mg-s nb-s" id="brief"><div class="nb-h"><img src="/assets/ruri/o_anchor_s.webp" width="64" height="88" alt="루리 뉴스 앵커 루리">'
            f'<p><b>오늘의 브리핑</b> · {E2(NOW_KST().strftime("%m/%d %H:%M"))} 기준 언론사 3곳 이상이 다룬 이슈 {len(js)}개예요. 기사 제목과 숫자만 정리하고, 어느 쪽이 맞는지는 판단하지 않아요.</p></div>'
            + out + '</section><style>.nb{margin:12px 0;padding:14px;border:1px solid var(--bd,#e5e7eb);border-radius:14px;background:var(--card,#fff)}.nb h3{margin:0 0 4px;font-size:17px}.nb p{margin:6px 0;line-height:1.6}'
            '.nb-h{display:flex;gap:10px;align-items:center}.nb-h img{flex:none;width:48px;height:auto}.nbl{margin:6px 0}.nbl em{font-style:normal;font-weight:700;margin-right:6px;color:var(--pri,#b45309)}'
            '.nbd{margin:6px 0;font-size:14px}.nbd summary{cursor:pointer;color:var(--pri,#b45309);font-weight:700}.nbd summary small{font-weight:400;color:var(--mu,#6b7280);margin-left:6px}.nb .ip{margin:8px 0}'
            '.nbn{display:flex;gap:8px;overflow-x:auto;margin:8px 0 12px;padding-bottom:4px}.nbn a{flex:none;padding:7px 14px;border-radius:999px;background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;text-decoration:none;font-weight:700;font-size:14px}'
            '@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .nbn a{background:#2a1f14;color:#fdba74;border-color:#7c2d12}}:root[data-theme=dark] .nbn a{background:#2a1f14;color:#fdba74;border-color:#7c2d12}</style>')


def news_page():
    # 루리 탐정의 이슈 감별 (2026-10-18 사용자: RSS 기사 수집 → 주제별 묶음 → 팩트체크 기반 채점, 피드, 탐정 루리, 기사 관련 줍줍)
    body = f'''<p class="bc"><a href="/">홈</a> › 기사 확인 신호</p><h1>📺 루리 뉴스</h1><p class="kwn">언론사 15곳 기사를 매시간 모아 같은 사건끼리 묶고, 제목·숫자·확인 신호를 정리해요.</p>
<nav class="nbn" aria-label="이 화면 안에서 이동"><a href="#brief">📺 오늘의 브리핑</a><a href="#review">🖋️ 평론</a><a href="#news">🕵️ 이슈 순위·확인 신호</a><a href="/trend/">🍿 이슈 트렌드</a><a href="/hot/">🔥 핫이슈</a></nav>
{news_brief()}{join_cta('issue')}{hot_top(3)}{news_impact()}
<h2 class="nbh" id="rank">🕵️ 이슈 순위와 기사 확인 신호</h2><section id="news" aria-label="이슈 순위와 기사 채점">{news_static()}</section>
<details class="nw-how"><summary>채점은 이렇게 해요</summary><ul><li><b>교차 보도</b> — 같은 사건을 여러 언론사가 보도하면 가점, 한 곳뿐이면 표시만 해요.</li><li><b>출처</b> — 실명 기관·인물 출처는 가점, 익명 관계자뿐이거나 온라인 커뮤니티·SNS 글이 출처면 감점.</li><li><b>제목-본문 일치</b> — 제목의 숫자·인용문이 본문에 없으면 감점.</li><li><b>숫자 엇갈림</b> — 같은 사건인데 언론사마다 사망·부상자 수가 다르면 따로 표시해요.</li><li><b>낚시·홍보</b> — 「충격」「결국」「이것」 같은 낚시 표현, 기업 홍보성 기사는 감점.</li></ul><p>기사 본문은 채점에만 쓰고 이 사이트에 옮겨 싣지 않아요. 제목을 누르면 원래 언론사 기사로 이동해요.</p></details>
<link rel="stylesheet" href="/assets/news/news.css?v=6"><script defer src="/assets/news/news.js?v=4"></script>'''
    page('/news/', '루리 뉴스 — 오늘의 이슈 브리핑·기사 확인 신호 (언론사 15곳)', '언론사 15곳 기사를 매시간 모아 같은 사건끼리 묶고, 교차 보도·출처·제목-본문 일치·숫자 엇갈림·낚시 표현으로 기사마다 점수를 매겨요. 지금 가장 많이 보도된 이슈 순위.',
         body, [('루리의 줍줍', '/'), ('기사 확인 신호', '/news/')])


GL_ANIME = {'Comedy': '코미디', 'Action': '액션', 'Fantasy': '판타지', 'Slice of Life': '일상', 'Drama': '드라마', 'Adventure': '모험', 'Romance': '로맨스', 'Sci-Fi': 'SF', 'Supernatural': '초자연', 'Music': '음악',
            'Mystery': '미스터리', 'Sports': '스포츠', 'Psychological': '심리', 'Horror': '호러', 'Thriller': '스릴러', 'Mecha': '메카', 'Mahou Shoujo': '마법소녀', 'Isekai': '이세계', 'School': '학원', 'Idol': '아이돌',
            'Iyashikei': '힐링', 'Coming of Age': '성장', 'Magic': '마법', 'Tragedy': '비극', 'Super Power': '초능력', 'Swordplay': '검술', 'Shounen': '소년만화', 'Seinen': '성인만화', 'Urban Fantasy': '어반판타지',
            'Cute Girls Doing Cute Things': '귀여운 일상', 'Animals': '동물', 'Work': '직장', 'Demons': '악마', 'Female Protagonist': '여주인공', 'Male Protagonist': '남주인공', 'Ecchi': '에치'}


def watch_data():
    """수집해 둔 웹툰·애니(_gongmo/watch/*.json)를 화면용 가벼운 배열로 바꿔 assets/watch/*.json 에 쓴다."""
    wd = os.path.join(HERE, 'watch'); od = os.path.join(ROOT, 'assets', 'watch'); os.makedirs(od, exist_ok=True)
    wr = lambda n, o: open(os.path.join(od, n), 'w', encoding='utf-8', newline='\n').write(json.dumps(o, ensure_ascii=False, separators=(',', ':')))
    out = {}
    fa = os.path.join(wd, 'anime.json')
    if os.path.exists(fa):
        A = json.load(open(fa, encoding='utf-8')); its = [v for v in A['items'].values() if not (v.get('fmt') in ('SPECIAL', 'MUSIC') or (v.get('sc') or 0) < 55 or (v.get('pop') or 0) < 3000)]
        its.sort(key=lambda v: -(v.get('pop') or 0))
        gc = collections.Counter(g for v in its for g in v['g']); top = [g for g, _ in gc.most_common(16)]
        extra = [x for x in ('Isekai', 'School', 'Idol', 'Iyashikei') if any(x in v['tg'] for v in its)]
        WHY = {'love': '설레고 싶은 기분에', 'fun': '웃고 싶은 기분에', 'tense': '긴장감 있는 이야기가 당길 때', 'cry': '울고 싶은 기분에', 'heal': '힐링이 필요할 때', 'fight': '신나게 보고 싶을 때'}
        mood = lambda k, e, lb, names, kw: {'k': k, 'e': e, 'label': lb, 'why': WHY.get(k, lb), 'names': names, 'kw': kw}
        cfg = {'genres': [[g, GL_ANIME.get(g, g)] for g in top + extra], 'gl': GL_ANIME,
               'moods': [mood('love', '💕', '설레고 싶어요', ['Romance'], []), mood('fun', '😂', '웃고 싶어요', ['Comedy'], ['funny']), mood('tense', '😱', '긴장감 있게', ['Thriller', 'Mystery', 'Psychological', 'Horror'], ['dark']),
                         mood('cry', '😢', '울고 싶어요', ['Drama', 'Tragedy'], ['emotional']), mood('heal', '🍵', '편하게 힐링', ['Slice of Life', 'Iyashikei', 'Cute Girls Doing Cute Things'], []), mood('fight', '⚔️', '신나게 싸움', ['Action', 'Swordplay', 'Super Power'], ['action'])],
               'modes': [{'k': 'any', 'e': '🎲', 'label': '상관없어요'}, {'k': 'tv', 'e': '📺', 'label': 'TV 시리즈'}, {'k': 'short', 'e': '⏱️', 'label': '짧게(13화 이하)'}, {'k': 'movie', 'e': '🎞️', 'label': '극장판'}]}
        rows = [[v['id'], v['kr'] or v['en'] or v['ro'], v['jp'], v['ro'] if (v['kr'] or v['en']) else '', v['g'], v['tg'][:5], v['sc'], v['pop'], v['ep'], v['fmt'], v['year'], v['season'], v['st'], v['studio'], v['cv'], v['color'],
                 v['url'], v['ott'], v.get('rec') or [], (v.get('rv') or {}).get('kw') or [], v['tr'], v['min']] for v in its[:1500]]
        wr('anime.json', {'at': A['at'], 'cfg': cfg, 'r': rows}); out['anime'] = (len(rows), [(r[1] or r[2], r[16]) for r in rows[:12]])
    fw = os.path.join(wd, 'webtoon.json')
    if os.path.exists(fw):
        Wt = json.load(open(fw, encoding='utf-8')); its = [v for v in Wt['items'].values() if v.get('tags') is not None and not v.get('adult') and not v.get('rest')]
        its.sort(key=lambda v: -(v.get('fav') or 0))
        tc = collections.Counter(g for v in its for g in v['tags'])
        GEN = ['로맨스', '판타지', '드라마', '액션', '스릴러', '개그', '일상', '무협/사극', '성장물', '감성적인', '청춘', '우정', '가족', '이능력', '러브코미디', '시리어스', '소설원작']
        top = [g for g in GEN if tc.get(g)]
        kc = collections.Counter(w for v in its for w in (v.get('kw') or [])); common = {w for w, n in kc.items() if n > 60}   # 어디에나 나오는 낱말은 추천 계산에서 뺀다
        for v in its: v['kw'] = [w for w in (v.get('kw') or []) if w not in common][:10]
        WHYW = {'love': '설레고 싶은 기분에', 'fun': '웃고 싶은 기분에', 'tense': '긴장감 있는 이야기가 당길 때', 'cry': '감동받고 싶은 기분에', 'heal': '힐링이 필요할 때', 'fight': '신나게 보고 싶을 때'}
        mood = lambda k, e, lb, names, kw: {'k': k, 'e': e, 'label': lb, 'why': WHYW.get(k, lb), 'names': [n for n in names if tc.get(n)], 'kw': kw}
        alias = {g: [t for t in tc if g in t] + ([g] if g not in tc else []) for g in top}
        alias['감성적인'] = ['감성적인', '감성']; alias['시리어스'] = ['시리어스']
        cfg = {'genres': [[g, g] for g in top], 'gl': {}, 'alias': alias,
               'moods': [mood('love', '💕', '설레고 싶어요', ['로맨스', '설렘폭발', '러브코미디', '리얼로맨스'], ['사랑', '연애']), mood('fun', '😂', '웃고 싶어요', ['개그', '러브코미디', '일상'], []), mood('tense', '😱', '긴장감 있게', ['스릴러', '시리어스', '자극적인'], ['죽음', '복수', '살인']),
                         mood('cry', '😢', '감동받고 싶어요', ['감성적인', '가족', '우정', '성장물', '드라마'], ['가족', '상처']), mood('heal', '🍵', '편하게 힐링', ['일상', '감성적인', '청춘'], []), mood('fight', '⚔️', '신나게 싸움', ['액션', '액션판타지', '무협/사극', '이능력', '사이다'], ['능력', '던전', '헌터'])],
               'modes': [{'k': 'any', 'e': '🎲', 'label': '상관없어요'}, {'k': 'ongoing', 'e': '📆', 'label': '연재 중(매주 보기)'}, {'k': 'finished', 'e': '✅', 'label': '완결(몰아보기)'}]}
        rows = [[v['id'], v['n'], v['a'], v['th'], v['tags'], v.get('kw') or [], round(v.get('sc') or 0, 2), v.get('fav') or 0, 1 if v['fin'] else 0, v['days'], v.get('age', ''), 0, v.get('pub', '')] for v in its[:1800]]
        wr('webtoon.json', {'at': Wt['at'], 'cfg': cfg, 'r': rows}); out['webtoon'] = (len(rows), [(r[1], f'https://comic.naver.com/webtoon/list?titleId={r[0]}') for r in rows[:12]])
    return out


def watch_pages():
    """/watch/ — 웹툰·애니 취향 추천 (설문 → 줄거리 키워드·장르·비슷한 작품 → 추천)."""
    D = watch_data()
    if not D:
        return []
    ssr = ''
    for k, nm in (('webtoon', '웹툰'), ('anime', '애니')):
        if k in D:
            ssr += f'<section class="mg-s"><h2>{nm} 인기작</h2><ul class="fr-rel">' + ''.join(f'<li><a href="{E(u)}" target="_blank" rel="noopener nofollow">{E(n)}</a></li>' for n, u in D[k][1]) + '</ul></section>'
    cnt = ' · '.join(f'{nm} {D[k][0]:,}편' for k, nm in (('webtoon', '웹툰'), ('anime', '애니')) if k in D)
    page('/watch/', '웹툰·애니 추천 — 장르만 고르면 오늘의 추천', f'장르만 고르면 웹툰과 애니 중 그 장르에 맞는 작품을 오늘의 추천으로 골라 드려요. 기분·길이·본 작품을 더하면 더 정확해져요 ({cnt}).',
         '<p class="bc"><a href="/">홈</a> › 웹툰·애니 추천</p><h1>🎯 웹툰·애니 추천</h1>'
         f'<p class="lead" style="display:block">장르만 고르면 바로 오늘의 추천이 나와요. 기분·길이·재밌게 본 작품을 더하면 줄거리 키워드와 비슷한 작품 관계까지 반영해요. 지금 {cnt}을 모아 뒀어요.</p>'
         '<div id="watch"><noscript>자바스크립트를 켜면 설문 추천을 쓸 수 있어요.</noscript></div>' + ssr
         + '<p class="wt-foot">웹툰 정보는 네이버웹툰 공개 목록, 애니 정보는 AniList 공개 데이터를 모아 정리했어요. 작품의 표지·제목에 대한 권리는 각 작가·제작사·서비스에 있고, 이 페이지는 작품을 소개하고 원본 서비스로 연결해요. 줄거리 원문은 저장하지 않고 핵심 낱말만 추천 계산에 써요. 설문 선택값은 개인 식별 없이 장르 선호 집계에만 써요.</p>'
         '<link rel="stylesheet" href="/assets/watch/watch.css?v=2"><script defer src="/assets/watch/watch.js?v=3"></script>',
         [('루리의 줍줍', '/'), ('웹툰·애니 추천', '/watch/')])
    return ['/watch/']


def app_page():
    # 루리의 줍줍 앱(PWA) 설치 + 공모전 알림 (2026-10-18 사용자: 앱도 사이트 안에서 배포, 공모전 알림, 웹푸시, 메일)
    cats = json.dumps([[sl, n, CAT_ICON.get(n, '🧩')] for sl, n in CATS], ensure_ascii=False)
    faq = [('앱은 어디서 받아요?', '이 페이지에서 바로 설치돼요. 플레이스토어·앱스토어를 거치지 않는 웹앱이라 용량이 거의 없고, 늘 최신 공모전이 보여요.'),
           ('알림은 얼마나 자주 와요?', '메뉴 추천은 점심(11시 20분쯤)과 저녁(5시 20분쯤) 하루 2번이에요. 공모전은 저녁 7시쯤 관심 분야 새 공모전을 모아서, 아침 9시쯤 인기 공모전 마감 3일 전 소식을 보내요. 새 공모전이 없는 날은 안 와요. 항목마다 따로 끌 수 있어요.'),
           ('가입해야 해요?', '폰 알림은 가입 없이 바로 켤 수 있어요. 찜한 공모전 마감 메일은 회원만 받을 수 있어요.'),
           ('아이폰도 돼요?', 'iOS 16.4 이상 사파리에서 홈 화면에 추가한 뒤, 홈 화면의 루리의 줍줍 앱을 열어 알림을 켜면 돼요.'),
           ('알림을 끄고 싶어요.', '이 페이지에서 「알림 끄기」를 누르거나, 폰 설정 → 알림에서 루리의 줍줍(또는 sungprofile.cloud)을 끄면 돼요.')]
    body = f'''<p class="bc"><a href="/">홈</a> › 앱·알림</p><h1>📲 오늘 뭐 먹지 앱 · 루리의 줍줍</h1>
{say("o_present", "홈 화면에 앱을 깔면 열 때마다 오늘 메뉴를 골라 드려요. 점심·저녁 메뉴 알림도 켤 수 있고, 새 공모전·마감 소식도 같이 챙겨 드려요!")}
<section id="app-page" data-cats='{E(cats)}'>
<div class="ap-hero"><img src="/assets/icons/icon-192.png" alt="루리의 줍줍 앱 아이콘" width="72" height="72"><div><b>루리의 줍줍</b><span>시간·날씨·냉장고 재료로 오늘 메뉴 추천 · 공모전·지원금 알림 · 무료</span></div></div>
<div class="ap-card ap-feat"><ul><li>🍽️ <b>오늘 뭐 먹지?</b> 앱을 열면 지금 시간·날씨에 맞는 메뉴를 먼저 보여 줘요</li><li>🧊 냉장고 재료만 고르면 지금 만들 수 있는 메뉴를 찾아 줘요</li><li>⭐ 마음에 든 메뉴는 찜, 별로인 메뉴는 👎 — 다음 추천에 반영돼요</li><li>📴 한 번 본 메뉴·사진은 인터넷이 약해도 열려요</li></ul></div>
<h2>1. 앱 설치</h2><div class="ap-card ap-inst"><p class="ap-sm">불러오는 중…</p></div>
<h2>2. 폰 알림 (메뉴 추천 · 공모전)</h2><div class="ap-card ap-push"><p class="ap-sm">불러오는 중…</p></div>
<h2>3. 메일 알림</h2><div class="ap-card ap-mail"><p class="ap-sm">불러오는 중…</p></div>
<h2>자주 묻는 질문</h2><div class="ap-card ap-faq">{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in faq)}</div>
</section><p class="note">알림을 켜면 브라우저가 만든 알림 주소와 고른 분야만 저장해요. 이름·전화번호는 받지 않아요. 알림을 끄면 바로 지워져요.</p>
<link rel="stylesheet" href="/assets/app/app.css?v=2">'''
    page('/app/', '오늘 뭐 먹지 앱 설치 · 메뉴·공모전 알림 받기', '오늘 뭐 먹지 앱을 홈 화면에 설치하면 시간·날씨·냉장고 재료에 맞는 메뉴를 추천해 주고, 점심·저녁 메뉴 알림과 새 공모전 소식을 폰 알림으로 보내 줘요. 무료, 가입 없이 사용 가능.',
         body, [('루리의 줍줍', '/'), ('앱·알림', '/app/')])


FR_SUB = {'돼지고기': '소고기나 닭고기', '소고기': '돼지고기', '닭고기': '돼지고기', '스팸': '햄이나 소시지', '햄': '스팸이나 소시지', '소시지': '햄이나 스팸', '국수': '라면 사리',
          '파스타면': '국수', '애호박': '가지나 양배추', '양배추': '배추', '두부': '달걀', '참치캔': '스팸', '대파': '양파', '고추장': '고춧가루 조금 더', '김치': '볶은 양배추(맛은 달라져요)',
          '오징어': '새우', '새우': '오징어', '당면': '국수', '떡': '어묵', '어묵': '맛살', '버섯': '애호박', '시금치': '부추나 깻잎', '감자': '고구마', '우유': '물(조금 묽어져요)'}


def fr_tips(r, RS):
    """레시피마다 다른 팁(이름·재료·태그로 계산): 맵기 조절·대체 재료·보관·남은 재료 활용. 2026-10-19 상세 본문 보강."""
    n, L = r['n'], []
    if '매움' in r['t']:
        L.append(f'{n}의 매운 양념은 적게 넣고 조절하세요. 설탕을 더한다고 매운 성분이 제거되지는 않으며, 김치·고추장 자체의 매운맛도 고려해야 해요.')
    elif '아이' in r['t'] or '안 매움' in r['t']:
        L.append(f'{n}을 아이와 먹을 때는 양념의 염도와 재료의 알레르기를 따로 확인하세요. 안 매움 태그가 모든 연령에 적합하다는 뜻은 아니에요.')
    sub = [(i, FR_SUB[i]) for i in r['need'] if i in FR_SUB][:2]
    for i, x in sub:
        L.append(f'{i} 대신 {x}을(를) 쓰는 것은 대체 후보예요. 수분·염도·익는 시간이 달라 같은 분량과 조리시간을 그대로 적용하지 말고, 아래 만드는 법의 개별 안내를 우선하세요.')
    if re.search(r'국|찌개|탕|전골', n):
        L.append(f'남은 {n}은(는) 큰 냄비째 실온에서 오래 식히지 말고 얕은 용기에 나누어 빠르게 냉장하세요. 다시 끓이는 것만으로 잘못 보관한 음식이 안전해지는 것은 아니에요.')
    elif re.search(r'조림|볶음|무침|나물|장조림', n):
        L.append(f'{n}의 보관 가능 기간은 재료와 냉각·보관 상태에 따라 달라요. 메뉴명만으로 며칠간 안전하다고 정할 수 없으니 바로 먹을 분량만 덜고 남은 음식은 빠르게 냉장하세요.')
    left = [i for i in r['opt'] if i not in r['need']][:3]
    other = {i: next((x for x in RS if x is not r and i in x['need']), None) for i in left}
    for i, x in other.items():
        if x:
            L.append(f'{n} 만들고 {i}이(가) 남으면 「{x["n"]}」에 쓰면 좋아요.')
            break
    L.append(f'표시된 {r["m"]}분은 예상 시간이에요. 손질 숙련도·재료 크기·화력에 따라 달라지므로 시간만 보지 말고 재료가 충분히 익었는지 확인하세요.')
    return L


def fr_slug(n):
    return re.sub(r'[^0-9A-Za-z가-힣]+', '-', n).strip('-')



def page_rates(min_n=3):
    """회원이 실제로 준 별점만 읽어 온다(구조화 데이터 aggregateRating 용). 실패하면 빈 값."""
    if not COMM_API:
        return {}
    try:
        with urllib.request.urlopen(urllib.request.Request(COMM_API + f'/api/p/rates?min={min_n}', headers={'User-Agent': 'jupjup-build/1'}), timeout=20) as f:   # 파이썬 기본 UA 는 Cloudflare 가 막음(1010)
            return {x['page']: x for x in json.load(f).get('rates') or []}
    except Exception as e:
        print('별점 읽기 실패', repr(e)[:80])
        return {}


FR_CATS = [('guk', '국물', '🍲', '국·찌개·탕', '국물 요리'), ('bap', '밥', '🍚', '밥·덮밥·김밥', '밥 요리'), ('myeon', '면', '🍜', '면 요리', '면 요리'), ('bokkeum', '볶음', '🥘', '볶음 요리', '볶음 요리'),
           ('jorim', '조림', '🐟', '조림·찜', '조림·찜 요리'), ('banchan', '반찬', '🥗', '반찬·무침·나물', '반찬'), ('jeon', '전', '🥞', '전·부침개', '전·부침개')]


REC_TAGS = '<link rel="stylesheet" href="/assets/fridge/recommend.css?v=2"><script defer src="/assets/fridge/recommend.js?v=2"></script>'   # 오늘 뭐 먹지? (2026-10-20)


def rec_pop():
    """지금 많이 보는 메뉴(조회수·좋아요 상위 40). 방문자마다 D1 을 읽지 않도록 빌드가 시간마다 받아 정적 파일(rec_pop.json)로 둔다."""
    import urllib.parse
    out = {}
    if not COMM_API:
        return out
    for by in ('views', 'likes'):
        try:
            req = urllib.request.Request(COMM_API + f'/api/p/top?prefix=/fridge/r/&by={by}&n=40', headers={'User-Agent': 'jupjup-build/1'})
            for x in json.load(urllib.request.urlopen(req, timeout=20)).get('top') or []:
                sl = urllib.parse.unquote(x['page']).strip('/').split('/')[-1]
                o = out.setdefault(sl, [0, 0]); o[0] = max(o[0], x['v']); o[1] = max(o[1], x['l'])
        except Exception as e:
            print('인기 메뉴 읽기 실패', repr(e)[:80])
    return out


def rec_build(RS, PR):
    """추천용 가벼운 데이터(rec.json: 메뉴 요약 배열)와 작은 사진(ph/t/<slug>.webp 240px). 완성 사진이 정제에서 빠진 메뉴는 사진 없이(이모지) 나간다."""
    import fridge_today as FT
    from PIL import Image
    tdir = os.path.join(ROOT, 'assets', 'fridge', 'ph', 't'); os.makedirs(tdir, exist_ok=True)
    TAGS = ['든든', '안 매움', '가벼움', '아이', '간식', '안주', '매움']
    LV = {'쉬움': 0, '보통': 1, '어려움': 2}
    keep, rows = set(), []
    for r in RS:
        sl = fr_slug(r['n']); mp = (PR.get(r['n']) or {}).get('main'); has = 0
        if mp and mp.get('f'):
            src = os.path.join(ROOT, mp['f'].lstrip('/').replace('/', os.sep)); dst = os.path.join(tdir, sl + '.webp')
            if os.path.exists(src):
                if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src) or Image.open(dst).size[0] < 400:
                    im = Image.open(src).convert('RGB'); im.thumbnail((400, 300)); im.save(dst, 'WEBP', quality=72, method=6)
                has = 1; keep.add(sl + '.webp')
        rows.append([r['n'], r['e'], r['m'], LV.get(r['lv'], 0), [TAGS.index(t) for t in r['t'] if t in TAGS], FT.cat(r['n']), has, r['need'], r['opt'][:4], len(r['s'])])
    for f in os.listdir(tdir):
        if f not in keep:
            os.remove(os.path.join(tdir, f))
    wr = lambda name, obj: open(os.path.join(ROOT, 'assets', 'fridge', name), 'w', encoding='utf-8', newline='\n').write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
    wr('rec.json', {'v': 1, 'tags': TAGS, 'r': rows})
    pop = rec_pop()
    if pop or not os.path.exists(os.path.join(ROOT, 'assets', 'fridge', 'rec_pop.json')):
        wr('rec_pop.json', pop)
    return len(rows), sum(1 for x in rows if x[6])


def fridge_page():
    """냉장고 파먹기 + 레시피 상세(/fridge/r/<요리>/, 2026-10-19 검색 유입: Recipe 구조화 데이터). 사진은 자유 이용 사진과 출처를 밝힌 참고 사진(recipes_ph.json)."""
    D = json.load(open(os.path.join(ROOT, 'assets', 'fridge', 'recipes.json'), encoding='utf-8'))
    PH = _rd('assets/fridge/recipes_ph.json') or {}
    PR, PI = PH.get('recipes') or {}, PH.get('ing') or {}
    RS = D['recipes']; NR = len(RS)
    RATE = page_rates()
    import fr_extra as FX, fridge_today as FXT
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
        cpu = set()
        for k, t in enumerate(r['s'], 1):
            im = st.get(k)
            if im and im is not mp and (im.get('by') or im.get('src')):
                cr.append(f'{k}단계 사진: {lic(im)}')
            steps += (f'<li id="step{k}" data-k="{k}"><div class="rp-st"><span class="rp-n">{k}</span><p>{cp_inline(E(t), cpu)}</p></div>'
                      + (f'<img class="rp-sp" src="{E(im["f"])}" width="720" height="540" loading="lazy" decoding="async" alt="{E(r["n"])} {k}단계: {E(t[:40])}">' if im and im.get('f') else '')
                      + '<div class="rp-sb"><button type="button" class="rp-saybtn rp-needtts">🔊 이 단계 듣기</button></div></li>')
        ingl = lambda L, need=False: ''.join(f'<li data-i="{E(i)}"{" data-need=1" if need else ""}><label><input type="checkbox" data-i="{E(i)}">{(f"<img src={chr(34)}{E(PI[i][chr(102)])}{chr(34)} width=28 height=28 alt=>" if i in PI else "")}<span>{E(i)}</span></label></li>' for i in L)
        def pimg(n_):
            sl_ = fr_slug(n_); t_ = os.path.join(ROOT, 'assets', 'fridge', 'ph', 't', sl_ + '.webp')
            if os.path.exists(t_): return f'/assets/fridge/ph/t/{sl_}.webp'
            m_ = ((PR.get(n_) or {}).get('main') or {}).get('f')
            return m_ if m_ and os.path.exists(os.path.join(ROOT, m_.lstrip('/'))) else ''
        cat_ = FXT.cat(r['n'])
        rel = sorted([x for x in RS if x is not r and set(x['need']) & set(r['need'])], key=lambda x: -len(set(x['need'] + x['opt']) & set(r['need'] + r['opt'])))[:6]
        tags = ' '.join(f'#{t}' for t in r['t'])
        tip = (f'필수 재료는 {", ".join(r["need"])} {len(r["need"])}가지이고, ' + (f'{", ".join(r["opt"][:4])} 같은 재료가 있으면 더 맛있어요. ' if r['opt'] else '')
               + f'조리 시간은 약 {r["m"]}분, 난이도는 「{r["lv"]}」이에요. 기본양념({D["basic"]})은 집에 있다고 보고 적었어요.')
        _is_soup = bool(re.search(r'국|찌개|탕|전골|국밥', r['n']))
        tp = FX.tips(r, RS, FR_SUB, cat_, r['t']); sb = FX.subs(r, FR_SUB); kp = FX.keep(cat_); pr_ = FX.pairs(r, RS, FXT.cat, lambda n_: bool(pimg(n_)), 4)
        lvl = {'쉬움': '쉬움', '보통': '보통', '어려움': '어려움'}.get(r['lv'], r['lv'])
        hero_img = (f'<img class="fr-rmain" src="{E(mp["f"])}" width="720" height="540" alt="{E(r["n"])} 완성 사진" fetchpriority="high">' if mp else '')
        sumbar = (f'<ul class="rp-sum"><li><i>⏱</i><b>{r["m"]}분</b><span>조리 시간</span></li><li><i>📊</i><b>{E(lvl)}</b><span>난이도</span></li>'
                  f'<li><i>🍽️</i><b data-serv-label>2인분</b><span>기준</span></li><li><i>🧺</i><b>{len(r["need"])}가지</b><span>필수 재료</span></li></ul>')
        servbar = ('<div class="rp-serv" role="group" aria-label="인분 선택"><span>인분</span><button type="button" data-s="1">1인분</button><button type="button" data-s="2" class="on">2인분</button><button type="button" data-s="4">4인분</button></div>'
                   '<p class="rp-serv-note" hidden>양념·재료 분량(컵·큰술·개 등)을 인분에 맞춰 바꿨어요. 불 세기·시간은 그대로예요.</p>')
        tipsec = ('<section class="rp-tips"><h2>💡 루리의 조리 포인트</h2><ul>' + ''.join(f'<li><b>{E(h_)}</b> {E(t_)}</li>' for h_, t_ in tp) + '</ul></section>') if tp else ''
        subsec = ''
        if sb or kp:
            subsec = '<section class="rp-two">' + (f'<div><h3>🔁 {E(r["n"])} 재료가 없을 땐</h3><ul>{"".join(f"<li>{E(t)}</li>" for t in sb)}</ul></div>' if sb else '') + (f'<div><h3>🧊 {E(r["n"])} 보관·남았을 때</h3><p>{E(kp)}</p></div>' if kp else '') + '</section>'
        pairsec = ''
        if pr_:
            pairsec = '<section class="rp-pair"><h2>🍽️ 함께 먹으면 좋은 메뉴</h2><ul class="hx-row">' + ''.join(
                f'<li class="hx-rc"><a href="/fridge/r/{fr_slug(x["n"])}/"><div class="ph">' + (f'<img src="{pimg(x["n"])}" width="400" height="300" loading="lazy" alt="{E(x["n"])} 완성 사진">' if pimg(x["n"]) else f'<div class="e">{x["e"]}</div>') + f'<em>⏱ {x["m"]}분</em></div><b>{E(x["n"])}</b><small>{FXT.cat(x["n"])} · {E(x["lv"])}</small></a></li>' for x in pr_) + '</ul></section>'
        relsec = (f'<h2>🔗 재료가 비슷한 메뉴</h2><ul class="fr-rel">' + ''.join(f'<li><a href="/fridge/r/{fr_slug(x["n"])}/">{x["e"]} {E(x["n"])} <small>{x["m"]}분</small></a></li>' for x in rel) + '</ul>' if rel else '')
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a> › {E(r["n"])}</p>'
                f'<article class="fr-rp rp2" data-n="{E(r["n"])}" data-base="2"><h1>{r["e"]} {E(r["n"])} {"끓이는 법" if _is_soup else "만드는 법"}</h1><p class="fr-meta">{E(tags)}</p>'
                + (f'<p class="fr-rate">{"★" * round(RATE[u]["avg"])}{"☆" * (5 - round(RATE[u]["avg"]))} {RATE[u]["avg"]} · 회원 {RATE[u]["n"]}명이 준 별점</p>' if RATE.get(u) else '')
                + f'<div class="rp-hero">{hero_img}</div>' + sumbar
                + '<div class="rp-acts"><button type="button" class="rp-cookbtn">🍳 요리 모드 <small>큰 글씨 · 음성 안내</small></button></div>'
                + f'<p class="rp-intro">{E(tip)}</p>'
                + f'<section class="rp-ing"><div class="rp-ih"><h2>🧺 재료</h2>{servbar}</div><div class="fr-ri"><div><h3>꼭 있어야 해요</h3><ul>{ingl(r["need"], True)}</ul></div>'
                + (f'<div><h3>있으면 더 좋아요</h3><ul>{ingl(r["opt"])}</ul></div>' if r['opt'] else '') + '</div>'
                + '<button type="button" class="rp-copy">🛒 없는 재료 장보기 목록 복사</button><p class="rp-hint">체크한 재료는 집에 있는 것으로 보고 빼 드려요.</p></section>'
                + ('' if any(w in ' '.join(r['s']) and cp_tool_url(w) for w in CP_TOOLS) or (CP.get('widget_ids') or {}).get('밀키트') else cp_box('', '재료 사러 가기 번거로우면 이런 것도 있어요:', 1, fill='밀키트 레시피', want='밀키트'))
                + f'<section class="rp-steps"><div class="rp-sh"><h2>👩‍🍳 {E(r["n"])} {"맛있게 끓이는 방법" if _is_soup else "맛있게 만드는 방법"}</h2><button type="button" class="rp-cookbtn rp-needtts ghost">🔊 한 단계씩 듣기</button></div><ol class="fr-rs">{steps}</ol></section>'
                + (cp_widget(cp_recipe_widget(r), 'recipe', ('밑줄 친 도구 이름과 위 상품은 쿠팡 파트너스 링크로, ' if cpu else '') + '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.') or (CP_IN_NOTE if cpu else ''))
                + (f'<p class="note">영문: {E(FR_EN[r["n"]])} recipe</p>' if FR_EN.get(r['n']) else '')
                + tipsec + subsec + pairsec
                + share_bar(f'{r["n"]} 만드는 법', f'{r["n"]} 만드는 법 — 재료 {len(r["need"])}가지로 {r["m"]}분')
                + f'<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 다른 메뉴 찾기</b><span>재료를 고르면 지금 만들 수 있는 메뉴를 골라 드려요 · 레시피 {NR}개 →</span></a>' + join_cta('recipe')
                + relsec
                + (f'<details class="fr-cr"><summary>사진 출처</summary><p>{"<br>".join(cr)}</p></details>' if cr else '')
                + '<p class="note">직접 조리 시험을 완료한 레시피로 소개하지 않습니다. 분량이 적힌 메뉴는 해당 분량을 우선하고, 분량이 없는 메뉴는 재현성 보완이 필요한 조리 아이디어입니다. 시간은 예상값이며 사진은 직접 조리 결과를 보증하지 않습니다. 보관 시에는 <a href="https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/leftovers-and-food-safety">USDA의 남은 음식 안전 안내</a>처럼 얕은 용기에 나누어 신속히 냉장하세요. 일반적인 부패하기 쉬운 음식은 실온 2시간 이내, 32℃를 넘는 더운 환경은 1시간 이내가 기준이며 이미 오래 방치한 음식은 재가열로 해결하지 않습니다. 이는 모든 메뉴의 보관 일수를 보증하는 안내가 아닙니다. 안전 안내 확인: 2026-10-20.</p></article>'
                + '<link rel="stylesheet" href="/assets/fridge/fridge.css?v=13"><link rel="stylesheet" href="/assets/fridge/recipe.css?v=6"><script defer src="/assets/fridge/recipe.js?v=4"></script>')
        def how_step(k, t):
            nm = re.split(r'[,.]', t)[0].strip()[:45] or f'{k}단계'
            d_ = {'@type': 'HowToStep', 'name': nm, 'text': t, 'url': f'{SITE}{u}#step{k}'}
            im_ = st.get(k)
            if im_ and im_.get('f'):
                d_['image'] = SITE + im_['f']
            return d_
        ld = {'@context': 'https://schema.org', '@type': 'Recipe', 'name': r['n'], 'description': tip, 'datePublished': '2026-10-19', 'totalTime': f'PT{r["m"]}M', 'recipeYield': '2인분', 'recipeCategory': '집밥',
              'recipeCuisine': '한식', 'keywords': ', '.join([r['n'] + ' 만드는 법', '냉장고 파먹기'] + r['t']), 'author': {'@type': 'Organization', 'name': NAME},
              'recipeIngredient': r['need'] + r['opt'], 'recipeInstructions': [how_step(k, t) for k, t in enumerate(r['s'], 1)]}
        if mp:
            ld['image'] = [SITE + mp['f']]
        else:   # 2026-10-19 서치 콘솔 레시피 경고: image 필수 → 메뉴 이름·재료 사진 카드 (fr_card.py)
            import fr_card
            ld['image'] = [SITE + fr_card.card(r, PI)]
        rt = RATE.get(u)
        if rt:
            ld['aggregateRating'] = {'@type': 'AggregateRating', 'ratingValue': rt['avg'], 'ratingCount': rt['n'], 'bestRating': 5, 'worstRating': 1}
        how = '끓이는 법 · 레시피' if re.search(r'국|찌개|탕|전골|국밥', r['n']) else '만드는 법 · 양념장' if re.search(r'조림|무침', r['n']) else '만드는 법 · 레시피'   # 2026-10-19 검색 시나리오
        page(u, f'{r["n"]} {how} — 재료 {len(r["need"])}가지로 {r["m"]}분 집밥', f'{r["n"]} 만드는 법: {", ".join(r["need"] + r["opt"][:3])}로 {r["m"]}분. 재료와 단계별 만드는 법, 재료가 비슷한 메뉴까지.',
             body, [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), (r['n'], u)], ld)
        urls.append(u)
    # 2026-10-20 원본 정제: 같은 메뉴가 띄어쓰기만 다르게 두 번 있던 것을 합침 — 옛 주소는 새 주소로 안내(검색 색인 중복 방지)
    ALIAS = _rd('assets/fridge/recipes_alias.json') or {}
    live_names = {r['n'] for r in RS}
    for old, new in ALIAS.items():
        if new in live_names and old not in live_names:
            uo, un = f'/fridge/r/{fr_slug(old)}/', f'/fridge/r/{fr_slug(new)}/'
            page(uo, f'{old} → {new} 레시피로 이동', f'{old} 레시피는 {new} 레시피로 합쳤어요.',
                 f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a></p><h1>{E(old)} → {E(new)} 레시피로 합쳤어요</h1>'
                 f'<p><a href="{un}">{E(new)} 레시피 보기 →</a></p><meta http-equiv="refresh" content="0; url={un}">', noindex=True, canon=un)
    allr = ''.join(f'<li><a href="/fridge/r/{fr_slug(r["n"])}/">{r["e"]} {E(r["n"])}</a></li>' for r in sorted(RS, key=lambda r: r['n']))
    import fridge_today as FT
    n_rec, n_ph = rec_build(RS, PR)
    print('추천 데이터', n_rec, '메뉴 · 사진 있는 메뉴', n_ph)
    ssr = lambda L, note='': '<ul class="rec-ssr">' + ''.join(f'<li><a href="/fridge/r/{fr_slug(x["n"])}/">{x["e"]} {E(x["n"])} <small>{x["m"]}분 · {E(x["lv"])}</small></a></li>' for x in L) + '</ul>' + (f'<p class="note">{note}</p>' if note else '')
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
         + '<div data-rec="weather" data-n="8">' + ssr([x for x in RS if x['n'] in set(TD.get('picks', []))][:3], '자바스크립트를 켜면 오늘 날씨와 시간에 맞춰 골라 드려요.') + '</div>'
         + '<details class="fr-all"><summary>📚 날씨별 전체 메뉴 보기</summary>' + secs + '</details>' + REC_TAGS + FOLD_TAGS
         + '<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 찾기</b><span>있는 재료를 고르면 지금 만들 수 있는 메뉴부터 →</span></a><link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">',
         [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), ('날씨별 메뉴', '/fridge/weather/')])
    SOLO = sorted([x for x in RS if len(x['need']) <= 3 and x['m'] <= 20], key=lambda x: (x['m'], len(x['need'])))
    page('/fridge/solo/', f'자취 요리 추천 — 재료 3개 이하·20분 안에 ({len(SOLO)}가지)', f'자취 요리 추천: 꼭 필요한 재료 3개 이하, 20분 안에 끝나는 1인분 집밥 {len(SOLO)}가지. 설거지 적은 메뉴와 남은 재료 활용까지.',
         f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">냉장고 파먹기</a> › 자취 요리</p><h1>🏠 자취 요리 추천 — 재료 3개 이하·20분 ({len(SOLO)}가지)</h1>'
         '<p>자취방 냉장고에 흔한 달걀·김치·스팸·라면으로 만들 수 있는 메뉴부터 골랐어요. 모두 꼭 필요한 재료가 3개 이하이고, 20분 안에 끝나요. 기본양념(간장·설탕·식용유 등)은 있다고 봤어요.</p>'
         + '<div data-rec="solo" data-n="8">' + ssr(SOLO[:5], '자바스크립트를 켜면 지금 시간에 맞춰 골라 드려요.') + '</div>'
         + f'<details class="fr-all"><summary>📚 자취 요리 전체 {len(SOLO)}가지 보기</summary>' + li(SOLO).replace('<ul class="fr-rel">', '<ul class="fr-rel" data-fold="20" data-step="40">', 1) + '</details>' + REC_TAGS + FOLD_TAGS
         + '<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 찾기</b><span>「설거지 적게」 조건도 고를 수 있어요 →</span></a><link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">',
         [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/'), ('자취 요리', '/fridge/solo/')])
    page('/fridge/plan/', '주간 식단표·장보기 목록 — 메뉴 담으면 재료 한 번에 정리', '이번 주 먹을 메뉴를 담으면 필요한 재료를 한데 모아 장보기 목록으로 만들어 드려요. 체크·복사·인쇄까지.',
         '<p class="bc"><a href="/">홈</a> › <a href="/fridge/">레시피</a> › 식단·장보기</p><h1>📅 주간 식단표 · 장보기</h1>'
         '<p class="lead" style="display:block">먹고 싶은 메뉴를 담으면, 필요한 재료를 한데 모아 몇 가지 메뉴에 쓰이는지 보여 드려요. 이 브라우저에만 저장돼요.</p><div id="plan"><noscript>자바스크립트가 필요해요.</noscript></div>'
         '<link rel="stylesheet" href="/assets/fridge/plan.css?v=1"><script defer src="/assets/fridge/plan.js?v=1"></script>',
         [('루리의 줍줍', '/'), ('레시피', '/fridge/'), ('식단·장보기', '/fridge/plan/')], noindex=True)
    urls += ['/fridge/weather/', '/fridge/solo/', '/fridge/plan/']
    import collections as _co
    shutil.rmtree(os.path.join(ROOT, 'fridge', 'c'), ignore_errors=True)
    CATN = {}
    for sl_, key_, ic_, nm_, nm2_ in FR_CATS:
        L_ = sorted([x for x in RS if FT.cat(x['n']) == key_], key=lambda x: (x['m'], len(x['need']), x['n']))
        CATN[sl_] = len(L_)
        if len(L_) < 10:
            continue
        ing_ = _co.Counter(g for x in L_ for g in x['need']).most_common(5)
        quick = [x for x in L_ if x['m'] <= 15]
        oth = ' · '.join(f'<a href="/fridge/c/{s2}/">{i2} {n2}</a>' for s2, k2, i2, n2, _ in FR_CATS if s2 != sl_ and len([y for y in RS if FT.cat(y['n']) == k2]) >= 10)
        facts = (f'{nm_} 레시피 {len(L_)}가지를 조리 시간 짧은 순으로 모았어요. 가장 빠른 건 {L_[0]["n"]}({L_[0]["m"]}분)이고 평균 {sum(x["m"] for x in L_) / len(L_):.0f}분 걸려요. '
                 f'이 분야에서 필수 재료로 가장 많이 쓰인 건 {", ".join(f"{g}({c}개)" for g, c in ing_)}예요.')
        wk_ = 'cat-' + sl_
        bd = (f'<p class="bc"><a href="/">홈</a> › <a href="/fridge/">레시피</a> › {E(nm_)}</p><h1>{ic_} {E(nm_)} 레시피 모음 — {len(L_)}가지</h1><p class="cat-st">📌 {E(facts)}</p>'
              + f'<div data-rec="cat" data-cat="{E(key_)}" data-n="6">' + ssr(L_[:5]) + '</div>'
              + (f'<h2>⏱️ 15분 안에 끝나는 {E(nm2_)} ({len(quick)}가지)</h2>' + li(quick[:12]).replace('<ul class="fr-rel">', '<ul class="fr-rel" data-fold="6" data-step="12">', 1) if quick else '')
              + cp_widget('냄비·뚝배기' if key_ == '국물' else '밀키트', 'recipe')
              + f'<h2>전체 {E(nm_)} 레시피 (조리 시간순)</h2>' + li(L_).replace('<ul class="fr-rel">', '<ul class="fr-rel" data-fold="15" data-step="30">', 1) + REC_TAGS + FOLD_TAGS
              + join_cta('recipe')
              + f'<p class="hm-links">다른 분류: {oth} · <a href="/fridge/solo/">🏠 자취 요리</a> · <a href="/fridge/weather/">🌤️ 날씨별 메뉴</a></p>'
              + '<a class="lab-cta" href="/fridge/"><b>🍳 내 냉장고 재료로 찾기</b><span>있는 재료를 고르면 지금 만들 수 있는 메뉴부터 →</span></a><link rel="stylesheet" href="/assets/fridge/fridge.css?v=12">')
        page(f'/fridge/c/{sl_}/', f'{nm_} 레시피 모음 {YR} — 집에서 만드는 {len(L_)}가지 (조리 시간순)', f'{nm_} 레시피 {len(L_)}가지: 조리 시간 순서로 만드는 법과 필수 재료. 15분 안에 끝나는 {nm2_} {len(quick)}가지 포함.',
             bd, [('루리의 줍줍', '/'), ('레시피', '/fridge/'), (nm_, f'/fridge/c/{sl_}/')])
        urls.append(f'/fridge/c/{sl_}/')
    page('/fridge/', f'냉장고 파먹기 메뉴 추천 — 있는 재료로 오늘 요리 (레시피 {NR}개)', f'냉장고에 있는 재료만 고르면 집밥 레시피 {NR}개 중 지금 바로 만들 수 있는 오늘 메뉴와 만드는 법, 하나만 사면 되는 메뉴까지 알려 줘요.',
         f"""<p class="bc"><a href="/">홈</a> › 냉장고 파먹기</p><h1>🍳 루리의 냉장고 파먹기</h1>
{say("o_cook", f"냉장고 사진을 찍거나 있는 재료를 눌러 주세요. 집밥 레시피 {NR}개 중에 지금 바로 만들 수 있는 걸 골라 드릴게요!")}
<div class="rec-tabs" data-rec-tabs role="tablist"><button type="button" data-t="rec-pane" class="on">🍽️ 오늘의 추천</button><button type="button" data-t="fridge">🧊 내 냉장고로 찾기</button></div>
<section id="rec-pane" aria-label="오늘의 추천"><div data-rec="today" data-n="8">{ssr([x for x in RS if x['n'] in set(TD.get('picks', []))][:3], '자바스크립트를 켜면 시간·날씨에 맞춰 골라 드려요.')}</div></section>
<section id="fridge" aria-label="냉장고 재료로 메뉴 추천" hidden><noscript><style>#fridge[hidden]{{display:block!important}}</style>자바스크립트가 필요해요. 아래 전체 레시피 목록에서 골라 보세요.</noscript></section>
<p class="hm-more"><a href="/fridge/weather/">🌤️ 날씨별 메뉴</a> · <a href="/fridge/solo/">🏠 자취 요리</a> · <a href="/fridge/r/계란찜/">🥚 계란찜</a></p>
<p class="hm-more">분류로 보기: {' · '.join(f'<a href="/fridge/c/{s2}/">{i2} {n2}</a>' for s2, k2, i2, n2, _ in FR_CATS if CATN.get(s2, 0) >= 10)}</p>
{kin_ans_links('/fridge/q/')}
<details class="fr-all"><summary>📚 전체 레시피 {NR}개 보기</summary><ul>{allr}</ul></details>
<a class="lab-cta" href="/cat/food/"><b>🏆 요리·레시피 공모전</b><span>레시피 공모전·요리경연대회 모아 보기 · 상금 받고 요리 실력 뽐내기 →</span></a><p class="note">사진은 재료를 찾는 데만 쓰고 저장하지 않아요. 고른 재료는 이 폰에만 저장돼요. 알레르기가 있으면 재료를 꼭 다시 확인해 주세요.</p>
<link rel="stylesheet" href="/assets/fridge/fridge.css?v=13"><script defer src="/assets/fridge/fridge.js?v=15"></script>{REC_TAGS}""", [('루리의 줍줍', '/'), ('냉장고 파먹기', '/fridge/')],
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
         '''<section id="me" aria-label="내 공간"></section>''' + (('<section class="me-sec"><h2>💬 톡방</h2><p class="note">공모전·지원금 마감 소식을 매일 나눠요.</p><p class="ft-c">' + comm_btns() + '</p></section>') if COMM_LINKS else '') + '''<link rel="stylesheet" href="/assets/me/me.css?v=3"><script defer src="/assets/me/me.js?v=4"></script>''', [('루리의 줍줍', '/'), ('내 공간', '/me/')])
    page('/login/', '로그인', '루리의 줍줍 로그인 — 내 공간으로 이동해요.', '<p>내 공간으로 이동하고 있어요… <a href="/me/">이동하지 않으면 여기를 눌러 주세요</a></p><script>location.replace("/me/"+location.search+location.hash)</script>', noindex=True)   # 2026-10-19 /login/ 404 → 내 공간(로그인 화면 포함)
    page('/admin/', '관리자', '관리자', '''<section id="admin"></section><section id="gsc-admin"></section><link rel="stylesheet" href="/assets/me/me.css?v=3"><script defer src="/assets/me/admin.js?v=7"></script>''', noindex=True)


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
    try:
        _ng = len(json.load(open(KIN_F, encoding='utf-8'))['guides'])
    except Exception:
        _ng = 0
    page('/about/', '소개', '루리의 줍줍은 개인 개발자가 AI와 함께 운영하는 생활 정보 사이트입니다. 이슈 확인 신호 채점, 애널리스트 의견 종합, 공모전·지원금 정리의 운영 목적과 작성 방식.',
         f'''<h1>소개</h1>
<p class="cat-st">📌 <b>루리의 줍줍</b>(sungprofile.cloud)은 공모전·지원금·청약 공고를 마감일·상금·응모 자격 순으로 비교해 보여 주고, 세금·노동·주거·금융 제도는 법령 조문과 공식 문서 링크로 확인한 가이드({_ng}편)로 정리하는 정보 사이트입니다. {TODAY.isoformat()} 기준 진행 중 공모전 {nl}건, 경품 이벤트 {ne}건을 정리하고 있습니다.</p>
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
