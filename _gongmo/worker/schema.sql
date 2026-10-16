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
