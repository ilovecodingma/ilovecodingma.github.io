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
