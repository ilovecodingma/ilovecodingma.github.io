# -*- coding: utf-8 -*-
import sys, os, unittest, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import contest_quality as Q
import dup_check as D


def C(i, title, end, org='', link='https://x.example.org/'):
    return {'id': i, 'title': title, 'end': end, 'org': org, 'link': link}


class Dup(unittest.TestCase):
    def test_kobc_pair_is_duplicate(self):
        a = C('Q01119', '한국해양진흥공사와 함께하는 2026 KOBC 해양 사진 공모전', '2026-10-23', '한국해양진흥공사 / 게티이미지코리아, (사)부산메세나협회')
        b = C('Q02723', "2026 KOBC 해양사진공모전 'Ocean in focus, 바다를 향한 시선'", '2026-10-23', '한국해양진흥공사')
        self.assertIn('Q01119', D.dups([a, b])[0].keys() | D.dups([a, b])[0].values())
        self.assertEqual(len(D.dups([a, b])[0]), 1)

    def test_other_ocean_photo_not_merged(self):   # 부산항 해양사진은 다른 공모전(마감일도 다름)
        a = C('Q01119', '한국해양진흥공사와 함께하는 2026 KOBC 해양 사진 공모전', '2026-10-23', '한국해양진흥공사')
        b = C('Q01659', '제13회 부산항 해양사진 공모전', '2026-10-29', '')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_same_generic_words_different_places_not_merged(self):
        a = C('1', '2026 강동구 숏폼 공모전', '2026-11-05')
        b = C('2', '제72회 백제문화제 숏폼 공모전', '2026-11-05')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_same_day_different_events_not_merged(self):
        a = C('1', '2026 군위군 사진 공모전', '2026-11-05')
        b = C('2', '2026 무주관광 사진 공모전', '2026-11-05')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_different_org_same_day_not_merged(self):
        a = C('1', '청년 정책 아이디어 공모전 서울', '2026-11-05', '서울시')
        b = C('2', '청년 정책 아이디어 공모전 부산', '2026-11-05', '부산시')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_different_division_same_org_not_merged(self):
        a = C('1', '2026년 경상북도 탄소중립 미술 공모전', '2026-10-23', '경상북도 탄소중립지원센터')
        b = C('2', '2026년 경상북도 탄소중립 실천 숏폼 영상 공모전', '2026-10-23', '경상북도 탄소중립지원센터')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_different_exhibition_not_merged(self):
        a = C('1', '2026 서울로미디어캔버스 네이처 프로젝트전 2차 공모', '2026-10-31', '서울특별시')
        b = C('2', '2026 서울로미디어캔버스 단편 애니메이션전 공모', '2026-10-31', '서울특별시')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_different_edition_not_merged(self):
        a = C('1', '제0회 리듬으로 부탁해 동인 리듬게임 수록곡 공모전', '2026-11-08', '젤리스노우')
        b = C('2', '제1회 리듬으로 부탁해 BMS 음악 공모전', '2026-11-08', '젤리스노우')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_same_acronym_different_edition_not_merged(self):
        a = C('1', '제7회 ISAC 국제 팝·미디어 음악 작곡 콩쿠르 2027', '2027-01-31', 'Ise-Shima Art Creation')
        b = C('2', '제3회 ISAC 국제 주니어 음악 콩쿠르 2027', '2027-01-31', 'Ise-Shima Art Creation')
        self.assertEqual(D.dups([a, b])[0], {})

    def test_core_containment_merged(self):
        a = C('1', '서울시 탄탄제로 챌린지 도심 쓰레기 처방전 공모', '2026-11-08', '서울시')
        b = C('2', '도심 쓰레기 처방전 공모전', '2026-11-08', '서울시')
        self.assertEqual(len(D.dups([a, b])[0]), 1)

    def test_candidates_lists_unmerged_similar(self):
        a = C('1', '2026년 경상북도 탄소중립 미술 공모전', '2026-10-23', '경상북도')
        b = C('2', '2026년 경상북도 탄소중립 실천 숏폼 영상 공모전', '2026-10-23', '경상북도')
        self.assertEqual(D.candidates([a, b]), [('1', '2')])


class Medium(unittest.TestCase):
    def test_photo_effort_wins(self):
        self.assertEqual(Q.medium_of("2026 KOBC 해양사진공모전", '사진'), 'photo')

    def test_photo_title_only(self):
        self.assertEqual(Q.medium_of('2026 조류사진 공모전'), 'photo')

    def test_video_title(self):
        self.assertEqual(Q.medium_of('CBS 숏폼 공모전'), 'video')

    def test_both(self):
        self.assertEqual(Q.medium_of('사진·영상 공모전'), 'photo+video')

    def test_label_never_calls_photo_video(self):
        self.assertEqual(Q.label_for('영상', 'photo'), '사진')
        self.assertEqual(Q.label_for('영상', 'video'), '영상')
        self.assertEqual(Q.label_for('문학', 'photo'), '문학')

    def test_photo_tips_have_no_video_items(self):
        t = Q.tips_for(['영상'], 'photo', {'영상': Q.TIP_VIDEO})
        self.assertFalse(any('영상 길이' in x or '배경음악' in x for x in t))
        self.assertTrue(any('EXIF' in x for x in t))

    def test_video_tips_unchanged(self):
        self.assertEqual(Q.tips_for(['영상'], 'video', {'영상': Q.TIP_VIDEO}), Q.TIP_VIDEO)


class Links(unittest.TestCase):
    def test_aggregator_detected(self):
        self.assertTrue(Q.is_aggregator('https://www.wevity.com/?c=find&gbn=view&ix=1'))
        self.assertTrue(Q.is_aggregator('https://www.all-con.co.kr/view/contest/1'))
        self.assertFalse(Q.is_aggregator('https://www.kobc.or.kr/'))
        self.assertFalse(Q.is_aggregator('https://forms.gle/abc'))

    def test_wording_does_not_claim_official_for_aggregator(self):
        b, note, alt = Q.link_wording('https://www.contestkorea.com/sub/view.php?x=1')
        self.assertNotIn('공식', b)
        self.assertIn('수집처', note)
        b2, _, _ = Q.link_wording('https://www.kobc.or.kr/')
        self.assertIn('공식', b2)


class Deadline(unittest.TestCase):
    def test_today_not_asserted_open(self):
        s = Q.deadline_sentence('2026.10.23', 0)
        self.assertNotIn('접수합니다', s)
        self.assertIn('확정할 수 없', s)

    def test_future_and_past(self):
        self.assertIn('접수합니다', Q.deadline_sentence('2026.10.30', 7))
        self.assertIn('끝났', Q.deadline_sentence('2026.10.01', -22))

    def test_no_time_invented(self):
        for d in (0, 3, -1):
            s = Q.deadline_sentence('2026.10.23', d)
            self.assertNotRegex(s, r'23:59|23시|24시')


if __name__ == '__main__':
    unittest.main(verbosity=2)
