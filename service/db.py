"""SQLite 스키마와 연결"""
import os
import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  plan TEXT NOT NULL DEFAULT 'free',
  mail_on INTEGER NOT NULL DEFAULT 1,
  unsub_token TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_tokens (
  token_hash TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  csrf TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY,
  query TEXT NOT NULL,
  norm TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  last_collected_at TEXT
);
CREATE TABLE IF NOT EXISTS subscriptions (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  PRIMARY KEY (user_id, topic_id)
);
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  title_key TEXT NOT NULL,
  media TEXT,
  date TEXT,
  summary TEXT,
  collected_on TEXT NOT NULL,
  UNIQUE (topic_id, url)
);
CREATE INDEX IF NOT EXISTS idx_articles_topic_day ON articles(topic_id, collected_on);
CREATE TABLE IF NOT EXISTS digests (
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  date TEXT NOT NULL,
  items TEXT NOT NULL,
  method TEXT NOT NULL,
  article_count INTEGER NOT NULL,
  PRIMARY KEY (topic_id, date)
);
CREATE TABLE IF NOT EXISTS deliveries (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date TEXT NOT NULL,
  status TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  PRIMARY KEY (user_id, date)
);
"""


def connect(path=None):
    path = path or config.DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con
