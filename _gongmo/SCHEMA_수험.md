# 시험 정보·평생교육 사이트 스키마 (2026-11-25 확정안)
사이트 목적(2026-11-25 사용자 정정): 「수험 사이트」가 아니라 ① 시험 정보 제공 ② 평생교육·자기개발 정보 제공 사이트.
기존 목적: 수험생·취준생에게 다양한 시험 정보를 주고, 준비를 돕는다. 주소(URL)는 기존 것 그대로 유지한다.

## 0. 두 갈래(사용자 확정 11/25)
사이트는 ① 시험을 위한 정보(일정·컷·문제) ② 시험과 무관한 자기개발 정보, 이 둘을 함께 다룬다. 홈 첫 화면에서 둘 중 고르게 한다.

## 1. 서비스 범위 — 모든 데이터의 `category` (사용자 확정 12개 대분류, 2026-11-25)
| category | 주요 시험 |
|---|---|
| 대학 입시 | 수능, 모의고사, 논술, 편입 |
| 대학원·전문대학원 | LEET, GRE, GMAT |
| 공무원 | 국가직, 지방직, 경찰, 소방, 군무원 |
| 전문직 | 변호사, 회계사, 세무사, 노무사, 감정평가사 |
| 국가기술자격 | 기사, 산업기사, 기능사, 기술사 |
| 국가전문자격 | 공인중개사, 주택관리사, 행정사, 관세사 |
| 어학 | TOEIC, TOEFL, IELTS, JLPT, HSK |
| 금융·투자 | 투자자산운용사, AFPK, CFA |
| IT | 정보처리기사, SQLD, ADsP, AWS |
| 의료·보건 | 의사, 간호사, 약사 국가시험 |
| 취업 | NCS, GSAT, SKCT, 인적성 |
| 기타 | 검정고시, 한국사능력검정, 운전면허 |
| 자기개발 | 시험과 무관한 배움(AI·코딩·글쓰기·습관·독서) — 일정 대신 「배울 거리·로드맵」 형식, 주소 /park/·/ailog/·/book/ 등 |
(교원·임용은 사용자 목록에 없음 → 우선 「공무원」 아래 두고 확인 필요)

## 2. 콘텐츠 유형과 필수 필드
| 유형 | 주소 | 데이터 파일 | 필수 필드 | 구조화 데이터(JSON-LD) |
|---|---|---|---|---|
| 시험 | /exam/<id>/ | exam_data/exams_2027.json | id, name, category, reg_start, reg_end, exam_date, result_date, fee, organizer, official_url, status(확정/예년 시기), basis_year | Event |
| 컷·합격선 | /exam/<id>/ 안 | exam_data/cuts/<id>.json | exam_id, official_cut, estimates, source, checked | — |
| 문제은행 | /exam/bank/<id>/ | exam_data/bank/<id>.json | id, name, category, kind(유사문제), source, updated, questions[q, choices, answer, explain] | Quiz |
| 시험 뉴스 | /issue/<slug>/ | 글 본문 + exam_articles.json | exam_id, kind(일정·접수·발표·컷·제도변경·준비물), published, updated, sources[≥1], 마감·시험일 날짜 | NewsArticle |
| 시험 글(가이드) | /exam/articles/ 목록 | exam_data/exam_articles.json | url, title, exam_id, type(뉴스/가이드) | Article |
| 스펙 | /contest/…, /c/<id>/ | data(공모전) | id, title, category(공모전·대외활동·인턴·자격), deadline, eligibility(학생·취준생), prize, source | Event |
| 식단 | /diet/, /fridge/… | recipes.json 등 | id, title, tags(시험기간·야식·도시락·간편), kcal | Recipe |
| 위키 | /wiki/… | 기존 가이드 | slug, title, checked | Article |

## 3. 규칙
- 날짜는 공식 공고로 확인한 값만. 미확인은 「지난해 값」 표시. 출처 URL 필수.
- 시험 뉴스는 「줍줍」 말투·소재(연예·소문) 금지. 시험·입시·채용 뉴스만, 육하원칙+마감일 먼저.
- 문제은행은 기출 원문 복제 금지(유사문제만).
- `exam_id` 는 문자열 하나 또는 목록(예: ["teacher-exam-2027","korean-history-81"])
- 한 글에 `exam_id` 하나 이상 연결 → /exam/<id>/ 에 관련 글로 노출.
- 새 글·새 시험은 exam_articles.json / exams_2027.json 에 등록해야 허브·홈에 보인다.
