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
        self.assertTrue(B.deadline_row({'id': 'Q01835'}, NEED).startswith('18시'))

    def test_verified_without_time_says_so(self):   # 화성: 공식에 시각 없음
        self.assertIn('시각 명시 없음', B.deadline_row({'id': 'Q01293'}, NEED))

    def test_conflicts_suppress_analysis_marker(self):   # 상충이 있는 공모전은 자동 분석을 보류한다
        self.assertTrue(B.VER['Q01835']['conflicts'])
        self.assertEqual(B.VER['Q01293']['conflicts'], [])

    def test_every_verified_has_source_and_date(self):
        for cid, v in B.VER.items():
            self.assertTrue(v['verified_at'], cid)
            self.assertTrue(v['sources'] and all(s['url'].startswith('https://') for s in v['sources']), cid)
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
