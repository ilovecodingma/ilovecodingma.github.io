-- 루리의 줍줍 커뮤니티 (Cloudflare D1)
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  nick TEXT NOT NULL UNIQUE,  -- 표시 이름: 이메일 앞 3글자+*** (따로 입력받지 않음)
  pw TEXT NOT NULL,            -- pbkdf2$반복$솔트hex$해시hex
  created INTEGER NOT NULL,
  banned INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contest_id TEXT NOT NULL,     -- Q00123 / 청약 A1b2c3d4 / 'free'
  contest_title TEXT NOT NULL DEFAULT '',
  user_id INTEGER NOT NULL,
  kind TEXT NOT NULL DEFAULT 'review',   -- review(후기) | qna(질문) | tip(팁)
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  rating INTEGER,               -- 1~5 (후기만)
  created INTEGER NOT NULL,
  reports INTEGER NOT NULL DEFAULT 0,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS posts_contest ON posts(contest_id, created DESC);
CREATE INDEX IF NOT EXISTS posts_recent ON posts(created DESC);
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created INTEGER NOT NULL,
  reports INTEGER NOT NULL DEFAULT 0,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS comments_post ON comments(post_id, created);
CREATE TABLE IF NOT EXISTS reports (
  user_id INTEGER NOT NULL,
  target TEXT NOT NULL,         -- p:12 / c:34
  created INTEGER NOT NULL,
  PRIMARY KEY (user_id, target)
);

-- 팀 모집 (2026-10-16 사용자: "팀도 만들고 그러는 용도")
CREATE TABLE IF NOT EXISTS teams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contest_id TEXT NOT NULL,
  contest_title TEXT NOT NULL DEFAULT '',
  leader_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  intro TEXT NOT NULL,
  roles TEXT NOT NULL DEFAULT '',      -- 쉼표 구분: 기획,디자인,개발
  size INTEGER NOT NULL DEFAULT 4,     -- 팀장 포함 총원
  deadline TEXT NOT NULL DEFAULT '',   -- YYYY-MM-DD 모집 마감
  contact TEXT NOT NULL DEFAULT '',    -- 오픈채팅 링크 등, 수락된 팀원에게만 공개
  status TEXT NOT NULL DEFAULT 'open', -- open | closed
  created INTEGER NOT NULL,
  reports INTEGER NOT NULL DEFAULT 0,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS teams_contest ON teams(contest_id, created DESC);
CREATE INDEX IF NOT EXISTS teams_recent ON teams(created DESC);
CREATE TABLE IF NOT EXISTS team_members (
  team_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT '',
  msg TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'pending', -- pending | accepted | rejected
  created INTEGER NOT NULL,
  PRIMARY KEY (team_id, user_id)
);

-- 초대 (2026-10-16: 네이버·메일·카톡으로 초대 링크 → 방문 1점·가입 3점, 히로인(공모전)별 기록, 점수만큼 루리 꾸미기 해금)
CREATE TABLE IF NOT EXISTS invite_codes (
  code TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS invited (
  user_id INTEGER PRIMARY KEY,   -- 초대받아 가입한 사람
  by_user INTEGER NOT NULL,      -- 초대한 사람
  contest_id TEXT NOT NULL DEFAULT '',  -- 어느 히로인으로 초대했는지
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS invited_by ON invited(by_user);
CREATE TABLE IF NOT EXISTS ref_visits (  -- 초대 링크로 들어온 방문(같은 사람 중복 제외)
  code TEXT NOT NULL,
  vh TEXT NOT NULL,              -- sha256(IP+UA) 앞 16자, 원문 저장 안 함
  contest_id TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL,
  PRIMARY KEY (code, vh)
);
CREATE TABLE IF NOT EXISTS user_prefs (  -- 루리 꾸미기 설정
  user_id INTEGER PRIMARY KEY,
  data TEXT NOT NULL DEFAULT '{}'
);

-- 공략 파티 꾸미기·이미지 (2026-10-17 사용자: "공략파티는 내 설정 느낌으로, 이미지도 올리게")
CREATE TABLE IF NOT EXISTS team_prefs (
  team_id INTEGER PRIMARY KEY,
  data TEXT NOT NULL DEFAULT '{}'   -- {color, emoji, cover(이미지 id)}
);
CREATE TABLE IF NOT EXISTS team_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  kind TEXT NOT NULL DEFAULT 'post',  -- cover(표지, 공개) | post(파티 앨범, 파티원만)
  mime TEXT NOT NULL,
  data TEXT NOT NULL,                 -- base64 (브라우저에서 줄여서 올림, 최대 약 300KB)
  caption TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS team_images_team ON team_images(team_id, created DESC);

-- 소셜 로그인 (2026-10-17: 구글·카카오 OAuth). provider+sub → users.id
CREATE TABLE IF NOT EXISTS oauth_links (
  provider TEXT NOT NULL,   -- google | kakao
  sub TEXT NOT NULL,        -- 제공자 고유 id
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (provider, sub)
);

-- 내 공간 (2026-10-17 사용자: 가입 장점 극대화 — 공모전·청약·지원금·경품 공통)
CREATE TABLE IF NOT EXISTS user_items (
  user_id INTEGER NOT NULL,
  item_id TEXT NOT NULL,          -- c:Q01234 / a:lh-... / e:<경품 id>
  title TEXT NOT NULL DEFAULT '',
  end_date TEXT NOT NULL DEFAULT '', -- YYYY-MM-DD
  fav INTEGER NOT NULL DEFAULT 0,    -- 찜(마감 알림 대상)
  state TEXT NOT NULL DEFAULT '',    -- '' | applied(냈어요) | won(당첨) | lost(아쉬움)
  updated INTEGER NOT NULL,
  PRIMARY KEY (user_id, item_id)
);
CREATE INDEX IF NOT EXISTS user_items_end ON user_items(end_date);

CREATE TABLE IF NOT EXISTS hits (id INTEGER PRIMARY KEY, day TEXT NOT NULL, ts INTEGER NOT NULL, vid TEXT NOT NULL, uid INTEGER NOT NULL DEFAULT 0, path TEXT, ref TEXT, country TEXT, city TEXT, mobile INTEGER DEFAULT 0, campaign TEXT DEFAULT '');
-- 2026-10-19: 기존 DB 에는 ALTER TABLE hits ADD COLUMN campaign TEXT DEFAULT '' 로 한 번 추가함 (utm_campaign)
-- 2026-10-20: 사후 분류·읽음 신호용으로 기존 DB 에 한 번 추가함: ALTER TABLE hits ADD COLUMN ua TEXT DEFAULT '' (브라우저|OS), asn INTEGER DEFAULT 0, org TEXT DEFAULT '' (asOrganization), dc INTEGER DEFAULT 0 (데이터센터 추정, 표시만), dwell INTEGER DEFAULT 0 (체류 초), scroll INTEGER DEFAULT 0 (최대 스크롤 %)
CREATE INDEX IF NOT EXISTS hits_day ON hits(day);
CREATE INDEX IF NOT EXISTS hits_ts ON hits(ts);

-- 준비실 (2026-10-18)
CREATE TABLE IF NOT EXISTS prep (user_id INTEGER NOT NULL, item_id TEXT NOT NULL, data TEXT NOT NULL, updated INTEGER NOT NULL, PRIMARY KEY (user_id, item_id));
CREATE TABLE IF NOT EXISTS post_likes (user_id INTEGER NOT NULL, post_id INTEGER NOT NULL, created INTEGER NOT NULL, PRIMARY KEY (user_id, post_id));
CREATE INDEX IF NOT EXISTS post_likes_post ON post_likes(post_id);

-- 동료 찾기 (2026-10-18)
CREATE TABLE IF NOT EXISTS seekers (user_id INTEGER NOT NULL, contest_id TEXT NOT NULL, contest_title TEXT NOT NULL DEFAULT '', roles TEXT NOT NULL DEFAULT '', intro TEXT NOT NULL DEFAULT '', updated INTEGER NOT NULL, PRIMARY KEY (user_id, contest_id));
CREATE INDEX IF NOT EXISTS seekers_c ON seekers(contest_id, updated DESC);
CREATE TABLE IF NOT EXISTS crew_invites (team_id INTEGER NOT NULL, user_id INTEGER NOT NULL, created INTEGER NOT NULL, PRIMARY KEY (team_id, user_id));

-- 냉장고 메뉴 추천 사용 기록 (하루 한도·비용 확인용, 사진은 저장 안 함)
CREATE TABLE IF NOT EXISTS fridge_log (id INTEGER PRIMARY KEY, day TEXT NOT NULL, ts INTEGER NOT NULL, who TEXT NOT NULL, ok INTEGER NOT NULL DEFAULT 1, tin INTEGER DEFAULT 0, tout INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS fridge_day ON fridge_log(day, who);
-- 웹푸시 공모전 알림 구독 (2026-10-18)
CREATE TABLE IF NOT EXISTS push_subs (endpoint TEXT PRIMARY KEY, p256dh TEXT NOT NULL, auth TEXT NOT NULL, cats TEXT DEFAULT '', newc INTEGER DEFAULT 1, dl INTEGER DEFAULT 1, uid INTEGER, created INTEGER, sent INTEGER DEFAULT 0, fails INTEGER DEFAULT 0, last_ok INTEGER, meal INTEGER DEFAULT 0);   -- meal: 점심·저녁 메뉴 추천 알림(2026-10-20), 기존 DB 는 ALTER TABLE push_subs ADD COLUMN meal INTEGER DEFAULT 0 로 한 번 추가

CREATE TABLE IF NOT EXISTS widget_views (id INTEGER PRIMARY KEY, day TEXT, ts INTEGER, kind TEXT, host TEXT);
CREATE INDEX IF NOT EXISTS widget_views_day ON widget_views (day);

-- 카카오톡 마감 알림 (2026-10-19): refresh_token 은 AES-GCM 암호문(키는 워커 비밀값 KAKAO_ALERT_KEY)
CREATE TABLE IF NOT EXISTS kakao_alert (user_id INTEGER PRIMARY KEY, sub TEXT NOT NULL, rt TEXT NOT NULL, created INTEGER NOT NULL, last_sent TEXT);
CREATE TABLE IF NOT EXISTS kakao_alert_nonce (nonce TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created INTEGER NOT NULL);

-- 페이지 댓글·좋아요·조회수 (2026-10-19 사용자: "개발자 섹션에 댓글 … 모든 곳에 추가 … 회원가입하면 가능하게", "레시피에도 좋아요·조회수")
CREATE TABLE IF NOT EXISTS page_comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,                  -- /fridge/r/김치찌개/ 처럼 주소 그대로
  title TEXT NOT NULL DEFAULT '',      -- 그 페이지 제목(내 댓글 모아보기·관리자용)
  user_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created INTEGER NOT NULL,
  reports INTEGER NOT NULL DEFAULT 0,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS page_comments_page ON page_comments(page, created);
CREATE INDEX IF NOT EXISTS page_comments_recent ON page_comments(created DESC);
CREATE INDEX IF NOT EXISTS page_comments_user ON page_comments(user_id, created DESC);
CREATE TABLE IF NOT EXISTS page_likes (
  user_id INTEGER NOT NULL,
  page TEXT NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (user_id, page)
);
CREATE INDEX IF NOT EXISTS page_likes_page ON page_likes(page);
-- 집계(조회수는 hits 에서 올리고, 좋아요·댓글 수는 쓸 때마다 같이 올린다)
CREATE TABLE IF NOT EXISTS page_stats (
  page TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '',
  views INTEGER NOT NULL DEFAULT 0,
  likes INTEGER NOT NULL DEFAULT 0,
  cms INTEGER NOT NULL DEFAULT 0,
  updated INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS page_stats_views ON page_stats(views DESC);
CREATE INDEX IF NOT EXISTS page_stats_likes ON page_stats(likes DESC);

-- 페이지 별점 (2026-10-19 서치콘솔 aggregateRating 경고 → 실제 회원 별점만 집계)
CREATE TABLE IF NOT EXISTS page_ratings (
  user_id INTEGER NOT NULL,
  page TEXT NOT NULL,
  stars INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (user_id, page)
);
CREATE INDEX IF NOT EXISTS page_ratings_page ON page_ratings(page);

-- 2026-10-19 D1 읽기 한도 대응: 방문 통계를 매번 hits 전체에서 세지 않도록 일별 요약 + 결과 캐시
CREATE TABLE IF NOT EXISTS hit_rollup (day TEXT PRIMARY KEY, v INTEGER NOT NULL DEFAULT 0, pv INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS kvcache (k TEXT PRIMARY KEY, v TEXT NOT NULL, exp INTEGER NOT NULL);

-- 2026-10-20 키워드 내일 예측 투표 (로그인 없음, 사람당 하루 1표는 해시로)
CREATE TABLE IF NOT EXISTS kw_votes (day TEXT NOT NULL, slug TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, slug));
CREATE TABLE IF NOT EXISTS kw_vote_seen (day TEXT NOT NULL, h TEXT NOT NULL, PRIMARY KEY (day, h));

-- 웹툰·애니 취향 설문과 작품 반응 (2026-10-20): 방문자 해시(IP+UA+날짜)로 하루 1회, 개인정보 없음
CREATE TABLE IF NOT EXISTS survey_answers (kind TEXT NOT NULL, day TEXT NOT NULL, vh TEXT NOT NULL, a TEXT NOT NULL, ts INTEGER NOT NULL, PRIMARY KEY (kind, day, vh));
CREATE TABLE IF NOT EXISTS watch_votes (kind TEXT NOT NULL, id TEXT NOT NULL, vh TEXT NOT NULL, v INTEGER NOT NULL, ts INTEGER NOT NULL, PRIMARY KEY (kind, id, vh));
CREATE INDEX IF NOT EXISTS watch_votes_k ON watch_votes(kind, id);
