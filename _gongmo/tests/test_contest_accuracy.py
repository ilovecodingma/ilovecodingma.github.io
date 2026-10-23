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
