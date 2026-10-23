# -*- coding: utf-8 -*-
"""공모전 데이터 품질 규칙 (Sprint 1, 2026-10-23). 순수 함수만 둔다 — AI 호출·파일 쓰기 없음, 테스트 가능.
사실(마감일·상금·자격)을 바꾸지 않고, 표시와 분류가 사실과 어긋나지 않게 하는 규칙만 담는다."""
import re
import urllib.parse as up

# 공고를 모아 둔 2차 수집처(주최 측 공식 페이지가 아님)
AGG_HOSTS = ('wevity.com', 'contestkorea.com', 'all-con.co.kr', 'thinkyou.co.kr', 'linkareer.com', 'campuspick.com', 'allforyoung.com', 'detizen.com')

PHOTO_RX = re.compile(r'사진|포토|photo|写真|フォト', re.I)
VIDEO_RX = re.compile(r'영상|UCC|숏폼|쇼츠|릴스|영화|동영상|video|映像|動画', re.I)


def host(u):
    return up.urlparse(u or '').netloc.lower().replace('www.', '')


def is_aggregator(u):
    h = host(u)
    return bool(h) and any(a in h for a in AGG_HOSTS)


def medium_of(title, effort=''):
    """제출물 매체: 'photo' | 'video' | 'photo+video' | ''. 제출물(effort)이 있으면 그것을 우선하고, 없으면 제목으로 판단."""
    e = (effort or '').strip()
    if e == '사진':
        return 'photo'
    if e == '영상':
        return 'video'
    p, v = bool(PHOTO_RX.search(title or '')), bool(VIDEO_RX.search(title or ''))
    if p and v:
        return 'photo+video'
    return 'photo' if p else 'video' if v else ''


def label_for(tag, medium):
    """화면에 쓰는 분야 이름. 분류 체계('영상' 묶음)는 그대로 두고, 사진만 내는 공모전을 영상이라 부르지 않는다."""
    if tag == '영상':
        return {'photo': '사진', 'video': '영상', 'photo+video': '사진·영상'}.get(medium, '영상·사진')
    return tag


TIP_PHOTO = ['촬영 원본(EXIF) 제출 여부와 보정·합성 허용 범위 확인', '해상도·파일 형식·용량 제한 확인', '인물·건축물이 나오면 초상권·재산권 동의 여부 확인']
TIP_VIDEO = ['영상 길이와 화면 비율(가로·세로) 확인', '배경음악·폰트는 상업적 이용 가능한 것만 사용', '출연자 초상권 동의서 준비']


def tips_for(tags, medium, base):
    """base = {태그: 팁 목록}. 영상 묶음일 때만 매체에 맞는 팁을 고른다(사진 공모전에 영상 팁을 붙이지 않음)."""
    out = []
    for tag in tags[:2]:
        if tag == '영상':
            out += TIP_PHOTO if medium == 'photo' else (TIP_PHOTO + TIP_VIDEO if medium == 'photo+video' else base.get(tag, TIP_VIDEO))
        else:
            out += base.get(tag, [])
    return out


def link_kind(link):
    return 'aggregator' if is_aggregator(link) else 'official'


def link_wording(link):
    """(버튼 문구, 안내 문구, 이미지 대체문구 접미). 수집처 링크를 주최 측 공식 공고라고 쓰지 않는다."""
    if is_aggregator(link):
        return ('수집처 공고 페이지 열기 →',
                '이 링크는 공고를 모아 둔 수집처 페이지예요(주최 측 공식 페이지가 아니에요). 접수 전에 주최 측 공식 공고를 찾아 마감 시각과 제출 조건을 꼭 확인하세요.',
                '공고 수집처 화면')
    return ('공식 공고·접수 페이지 열기 →', '링크는 주최 측 공고(또는 접수) 페이지예요. 공고가 바뀌었을 수 있으니 접수 전 다시 확인하세요.', '공식 공고 화면')


def deadline_sentence(end_dot, days_left):
    """마감일 문장. 날짜만 알고 시각을 모르면 마감일 당일에 「접수 중」이라고 확정하지 않는다."""
    if days_left < 0:
        return f'{end_dot}에 접수가 끝났습니다.'
    if days_left == 0:
        return f'마감일은 {end_dot}(오늘)입니다. 마감 시각을 확인하기 전에는 접수 가능 여부를 확정할 수 없습니다.'
    return f'{end_dot}까지 접수합니다.'


AUTO_NOTE = '자동 분류, 공고에서 확인'


def auto_label(value):
    """수집기가 규칙으로 분류한 제출·접수 방식은 30건 대조에서 43%가 공고와 달랐다(2026-10-23). 값에 자동 분류임을 붙여 확정처럼 보이지 않게 한다."""
    v = (value or '').strip()
    return f'{v} ({AUTO_NOTE})' if v and AUTO_NOTE not in v else v


_OFFICIAL_RX = re.compile(r'(?:\.|^)(?:go|or|ac|re|sc|ed)\.kr$|(?:\.|^)(?:applyhome\.co\.kr|apply\.lh\.or\.kr|bokjiro\.go\.kr|gov\.kr|youthcenter\.go\.kr)$')
_INFO_HOSTS = AGG_HOSTS + ('38.co.kr', 'ipostock.co.kr')


def link_label(link, kind=''):
    """URL 의 역할에 따라 버튼 이름을 정한다(2026-10-23 UI 2차 2번). 정보 플랫폼은 「수집 출처 보기」, 기관 도메인만 「공식 공고·접수」, 나머지는 「외부 페이지 보기」."""
    h = host(link)
    if not h:
        return ''
    if any(a in h for a in _INFO_HOSTS):
        return '수집 출처 보기'
    if _OFFICIAL_RX.search(h):
        return '공식 공고·접수'
    return '외부 페이지 보기'
