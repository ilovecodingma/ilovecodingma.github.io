import re
# -*- coding: utf-8 -*-
"""공모전 상세 표시 정확도 테스트 (2026-10-23). 사용: python -m pytest _gongmo/tests/test_contest_accuracy.py -q
빌드를 실행하지 않고 build.py 의 판정 함수만 부른다(모듈 import 는 부작용 없이 가능)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build as B

NEED = '공식 공고 확인 필요'


class RegionRow(unittest.TestCase):
    def test_nationwide_students_is_not_regional(self):   # 재학·재직은 신분 조건이지 지역 조건이 아니다
        self.assertEqual(B.region_row({'elig': '전국 대학교 재학생 및 휴학생'}, NEED), '제한 없음(자격 문구 기준)')

    def test_explicit_no_region_limit(self):
        self.assertTrue(B.region_row({'elig': '누구나 (지역 제한 없음)'}, NEED).startswith('제한 없음'))

    def test_province_residents_flagged(self):
        self.assertTrue(B.region_row({'elig': '강원도 내 초·중·고 학생 및 학부모'}, NEED).startswith('있음'))

    def test_unknown_stays_unknown(self):   # 정보가 없다고 「제한 없음」으로 단정하지 않는다
        self.assertIn('공고 확인', B.region_row({'elig': '대상 제한 없음'}, NEED))

    def test_explicit_region_field_wins(self):
        self.assertEqual(B.region_row({'elig': '전국', 'region': '부산'}, NEED), '부산')


class PrizeBasis(unittest.TestCase):
    def test_split(self):
        self.assertEqual(B.prize_split({'prize': '1등 1,000만원 · 총상금 2,100만원'}), (10000000, 21000000))
        self.assertEqual(B.prize_split({'prize': '총상금 1,840만원'}), (0, 18400000))
        self.assertEqual(B.prize_split({'prize': '공고 참조'}), (0, 0))

    def test_same_basis_only(self):   # 1등 상금이 있는 건과 총상금만 있는 건을 한 순위에 섞지 않는다
        items = [{'id': 'a', 'prize': '1등 100만원'}, {'id': 'b', 'prize': '1등 300만원'}, {'id': 'c', 'prize': '1등 200만원 · 총상금 900만원'}, {'id': 'd', 'prize': '총상금 5,000만원'}]
        basis, vals = B.prize_basis(items)
        self.assertEqual(basis, '1등 상금')
        self.assertEqual(vals, {'a': 1000000, 'b': 3000000, 'c': 2000000})
        self.assertNotIn('d', vals)   # 총상금 5,000만원이 1등 상금 순위에 끼어들지 않는다


class UnknownIsNotFavorable(unittest.TestCase):
    def test_zero_fee_is_unconfirmed(self):   # 원본 fee 0 은 값 없음이 기본값 — 「무료」로 읽지 않는다
        self.assertTrue(B.fee_row({'id': 'zz', 'fee': 0}, NEED).startswith('미확인'))

    def test_positive_fee_is_shown(self):
        self.assertIn('50,000원', B.fee_row({'id': 'zz', 'fee': 50000}, NEED))

    def test_missing_ai_is_unconfirmed(self):   # 비어 있으면 「AI 허용」이 아니다
        self.assertTrue(B.ai_row({'id': 'zz', 'ai': ''}, NEED).startswith('미확인'))
        self.assertTrue(B.ai_row({'id': 'zz'}, NEED).startswith('미확인'))

    def test_ai_values_carried(self):
        self.assertIn('금지', B.ai_row({'id': 'zz', 'ai': '금지'}, NEED))
        self.assertIn('표기', B.ai_row({'id': 'zz', 'ai': '표기'}, NEED))

    def test_unknown_deadline_time_not_invented(self):   # 시각을 모르면 자정·23:59 로 채우지 않는다
        r = B.deadline_row({'id': 'zz'}, NEED)
        self.assertIn('확인 필요', r)
        self.assertNotIn('23:59', r)
        self.assertNotIn('24:00', r)


class VerifiedValues(unittest.TestCase):
    def test_end_time_is_last_time_not_start(self):   # 부산 파빌리온: 09:00 시작 ~ 17:00 마감
        self.assertTrue(B.deadline_row({'id': 'Q01471'}, NEED).startswith('17:00'))

    def test_time_from_korean_hour(self):   # 외황강: 마감 당일 18시
        self.assertTrue(B.deadline_row({'id': 'Q01835'}, NEED).startswith('18:00'))

    def test_verified_without_time_says_so(self):   # 화성: 공식에 시각 없음
        self.assertIn('시각 명시 없음', B.deadline_row({'id': 'Q01293'}, NEED))

    def test_conflicts_suppress_analysis_marker(self):   # 상충이 있는 공모전은 자동 분석을 보류한다
        self.assertTrue(B.VER['Q01835']['conflicts'])
        self.assertEqual(B.VER['Q01293']['conflicts'], [])

    def test_every_verified_has_source_and_date(self):
        for cid, v in B.VER.items():
            self.assertTrue(v['verified_at'], cid)
            self.assertTrue(v['sources'] and all(s['url'].startswith(('https://', 'http://')) for s in v['sources']), cid)
            self.assertTrue(v['facts'], cid)


if __name__ == '__main__':
    unittest.main()


# ---- 2026-10-23 애드센스 재심사 지침: 잘린 문구·수집 오염·링크 종류·중복 ----
def test_shorten_rejects_truncated_and_ui_noise():
    import shorten as S
    assert S.repair('개인 또는 팀(3인') == '개인 또는 팀'
    assert S.repair('40세 이하(1987.1.') == '40세 이하'
    assert S.repair('Official B') == ''
    assert S.repair('초, 중, 고, 학') == ''
    assert S.clip('인 1년 최대 400,000원 /', 40) is None
    assert S.strip_ui('영상/UCC/사진 첨부파일 다운로드 다운로드 다운로드 ') == '영상/UCC/사진'


def test_link_label_by_role():
    import contest_quality as CQ
    assert CQ.link_label('https://www.all-con.co.kr/view/1') == '수집 출처 보기'
    assert CQ.link_label('http://www.38.co.kr/html/fund/?o=v') == '수집 출처 보기'
    assert CQ.link_label('https://www.gangdong.go.kr/x') == '공식 공고·접수'
    assert CQ.link_label('https://example.com/x') == '외부 페이지 보기'


def test_same_run_dup_rule():
    import dup_check as D
    a = {'id': 'Q1', 'title': '제20회 월간 아이러브캐릭터 캐릭터 공모전', 'org': '월간 아이러브캐릭터 / 주식회사 인큐베이팅', 'start': '2026-10-26', 'end': '2026-10-31', 'prize': '1등 200만원'}
    b = {'id': 'Q2', 'title': '제20회 월간 캐릭터 공모전', 'org': '월간<아이러브캐릭터>/주식회사 인큐베이팅', 'start': '2026-10-26', 'end': '2026-10-31', 'prize': '1등 200만원 · 총상금 200만원'}
    assert D._same_run(a, b)
    c = dict(b, id='Q3', title='제21회 월간 캐릭터 공모전')
    assert not D._same_run(a, c)            # 회차가 다르면 다른 공모전
    d = dict(b, id='Q4', title='제20회 월간 아이러브 미술 공모전')
    assert not D._same_run(dict(a, title='제20회 월간 아이러브 숏폼 공모전'), d)   # 부문 낱말이 어긋나면 다른 공모전


# ---- 2026-10-23 재심사 2차: 분류·지역·추출·게이트 ----
def test_tags_do_not_come_from_category_label_words():
    import parse as P
    t = P.tags_for('아이디어·창업·마케팅·네이밍, 과학·공학·학술', '2026 Tech Discovery 실험실창업 경진대회', 'KR')
    assert t[0] == '아이디어·정책' and '문학' not in t and '논문' not in t


def test_domestic_residence_is_not_regional_limit():
    import build as B
    assert B.region_kind('대한민국 거주하고 있는 누구나') == 'national'
    assert B.region_kind('이천시 거주 또는 재직자') == 'specific'
    assert B.region_kind('') == ''
    assert '이천' not in B.region_row({'elig': '대한민국 거주하고 있는 누구나'}, '확인')


def test_notice_points_not_cut_inside_dates():
    import build as B
    v = dict(B.notice_points('Q01152')).get('접수', '')
    assert '10. 23.' in v and not v.rstrip().endswith('∼')


def test_gate_holds_mismatches_and_keeps_missing_as_missing():
    import contest_gate as G, build as B
    h, _ = G.check({'id': 'x', 'title': '창업 경진대회', 'tags': ['문학'], 'elig': '', 'region': ''}, B.region_kind)
    assert h and '분류' in h[0]
    h2, r2 = G.check({'id': 'y', 'title': '숏폼 공모전', 'tags': ['영상'], 'elig': '', 'elig_raw': '개인 또는 팀(3인', 'region': ''}, B.region_kind)
    assert not h2 and r2   # 잘린 자격은 비우고 재수집 대상으로


def test_common_guide_links_exist_after_build():
    import os, build as B
    root = B.ROOT
    if not os.path.isdir(os.path.join(root, 'guide')):
        return
    for sl in ('contest-rules-reading-eligibility-deadline', 'media-art-video-contest-submission-check', 'contest-music-font-license-check',
               'local-photo-contest-permission-portrait', 'ai-contest-rules-check', 'idea-contest-ppt-structure', 'contest-deadline-day-mistakes'):
        assert os.path.exists(os.path.join(root, 'guide', sl, 'index.html')), sl


def test_every_verified_has_structured_deadline_and_no_invented_time():
    import build as B
    for cid, v in B.VER.items():
        assert 'deadline' in v, cid
        dl = v['deadline']
        assert dl.get('time') is None or re.fullmatch(r'\d{2}:\d{2}', dl['time']), cid
        if dl.get('time') is None:
            assert B.deadline_row({'id': cid}, '확인 필요').startswith('시각 명시 없음'), cid
    assert B.deadline_state({'id': 'Q01299'}) == 'absent'      # 대전: 공고 본문에 시각 없음(게시판 헤더 23:59는 확정하지 않음)
    assert B.deadline_state({'id': 'ZZZ'}) == 'unknown'
    assert '23:59' not in B.deadline_row({'id': 'Q01299'}, '확인 필요').split('—')[0]


# ---- 2026-11-05 품질 지시서 P0-2·P0-4·P0-1 회귀 테스트 ----
def test_broad_academic_label_does_not_make_it_science():
    import parse as P
    # 수집처의 넓은 묶음 라벨 「학문•과학•IT」만으로 IT·과학이 붙으면 안 된다
    assert P.tags_for('학문•과학•IT', '2026 전국대학생 통일토론경연대회', 'KR') == ['기타']
    assert P.tags_for('학문•과학•IT', '제 9 회 법학경시대회', 'KR') == ['기타']
    assert P.tags_for('학문•과학•IT', '2026 GSA 영어 말하기 대회', 'KR') == ['기타']
    assert 'IT·과학' in P.tags_for('학문•과학•IT', '현대자동차그룹 차량용 앱 개발 공모전', 'KR')      # 제목이 IT 면 유지
    assert 'IT·과학' in P.tags_for('학문•과학•IT', '2026 AI 서비스 기획 공모전', 'KR')


def test_service_scenario_is_not_literature():
    import parse as P
    t = P.tags_for('', '[과학기술정보통신부] 6G 서비스 시나리오 공모전', 'KR')
    assert '문학' not in t and 'IT·과학' in t and '아이디어·정책' in t
    assert '문학' in P.tags_for('', '제5회 영화 시나리오 공모전', 'KR')                              # 진짜 시나리오 공모는 문학
    assert '문학' not in P.tags_for('글로벌', '2026 수출 아이디어 공모전', 'KR')                      # 라벨 「글로벌」의 「글」


def test_analyst_entity_rules():
    import analyst as A
    for bad in ('28일', '영업익', '증권가', '증권주', '하루에', '석화기업', '번스타인·도이체방크'):
        assert A.norm_stock(bad) is None, bad
    assert A.norm_stock('LG생건') == 'LG생활건강' and A.norm_stock('KAI') == '한국항공우주' and A.norm_stock('HL만도') == 'HL만도'
    assert A.who_of('빼면 IMF 수준 "경고"') == 'IMF' and A.who_of('날린 월가 "AI 버블"') == '월가'
    assert A.who_of('국수본부장 "수사기관 국무회의 참석"') is None and A.who_of('통상본부장 "리스크 확대"') is None
    assert A.who_of('NH투자증권 리서치센터장 "코스피 6000"') == 'NH투자증권 리서치센터장'
    for bad in ('구조 "비트코인"', '금융화는 "위험"', '차트 "하락"', '높인다 "전망"', '서버 "다운"'):
        assert A.coin_who(bad) is None, bad
    assert A.coin_who('헤이즈 "비트코인 20만 달러"') == '헤이즈'


def test_apply_field_cleanup_and_age():
    assert B.ap_fields('ㅇ 신청자격 : 산학협력단', 'ㅇ 지원내용 : 실습 비용') == ('산학협력단', '실습 비용')
    assert B.ap_fields('청년', 'ㅇ지원대상: 연소득 5,000만원 이하 청년')[1] == ''          # 혜택 칸의 대상 설명은 혜택으로 보여 주지 않는다
    assert B.ap_fields('청년', "기간/사업비 : '21.~'30. / 34,500백만원")[1] == ''
    assert B.age_txt({'age_min': 24, 'age_max': 24}) == '만 24세' and B.age_txt({'age_min': 19, 'age_max': 39}) == '만 19~39세'


def test_dday_boundaries():
    import datetime
    t = B.TODAY
    iso = lambda d: (t + datetime.timedelta(days=d)).isoformat()
    assert B.dday(iso(0)) == (0, 'D-DAY') and B.dday(iso(1)) == (1, 'D-1') and B.dday(iso(-1)) == (-1, '마감')
    assert B.dday('2099-12-31')[1] == '상시'
    kst = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=9)
    assert abs((B.NOW_KST() - kst).total_seconds()) < 5                                            # 날짜 기준은 PC 시간대가 아니라 한국 시간
