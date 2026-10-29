"""MICE 이슈 레이더 공통 설정·DB 유틸"""
import os
import sqlite3
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "news.db")
DOCS = os.path.join(ROOT, "docs")
BRIEF_DIR = os.path.join(DOCS, "briefings")
KST = timezone(timedelta(hours=9))

TRACKS = ["MICE 유치", "전시·컨벤션"]

# 트랙별 검색어 (Google News RSS, 재현율 위주)
QUERIES = {
    "MICE 유치": [
        "MICE 유치", "MICE 산업", "국제회의 유치", "국제회의 개최",
        "코리아MICE뷰로", "한국관광공사 MICE", "국제회의복합지구", "국제회의도시",
        "ICCA 국제회의", "UIA 국제회의 통계", "기업회의 인센티브 관광", "MICE 예산",
    ],
    "전시·컨벤션": [
        "컨벤션센터", "전시컨벤션센터", "전시산업", "전시회 폐막",
        "킨텍스", "코엑스 전시", "벡스코", "엑스코", "송도컨벤시아", "전시장 건립",
    ],
}

# 중요도 분류 (앞에 있을수록 우선)
CATEGORY_RULES = [
    ("리스크·쟁점", ["국정감사", "국감", "적자", "무산", "삭감", "논란", "지연", "특혜", "감사원", "부실", "갈등", "중단"]),
    ("정책·예산", ["문체부", "문화체육관광부", "산업부", "산업통상", "예산", "지정", "공모", "제도", "법 개정", "개정안", "진흥계획", "전시산업발전", "기본계획", "지원사업"]),
    ("발주처", ["한국관광공사", "코리아MICE뷰로", "관광공사 MICE"]),
    ("유치·개최", ["유치", "유치 확정", "개최지", "선정", "총회", "국제회의", "포럼", "학술대회"]),
    ("통계·실적", ["ICCA", "UIA", "순위", "경제효과", "경제적 효과", "참관객", "참가자", "역대 최대", "실적", "통계", "방문객"]),
    ("해외·경쟁국", ["싱가포르", "일본", "중국", "태국", "홍콩", "대만", "해외", "글로벌"]),
    ("지자체·시설", ["컨벤션센터", "전시장", "건립", "확장", "증축", "착공", "준공", "제2", "제3전시장", "복합지구"]),
]
CATEGORIES = [c for c, _ in CATEGORY_RULES]

# 명백한 잡음 (category='기타'로 분류)
NOISE_WORDS = ["분양", "웨딩", "예식", "콘서트", "공연", "팬미팅", "뮤지컬", "모델하우스", "입주", "청약"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS news (
  url TEXT PRIMARY KEY,
  track TEXT,
  title TEXT,
  media TEXT,
  date TEXT,
  summary TEXT,
  note TEXT,
  category TEXT,
  source TEXT,
  collected_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_news_date ON news(date);
CREATE INDEX IF NOT EXISTS idx_news_track ON news(track);
"""


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    return con


def classify(title, summary=""):
    text = f"{title} {summary}"
    if any(w in title for w in NOISE_WORDS):
        return "기타"
    for cat, words in CATEGORY_RULES:
        if any(w in text for w in words):
            return cat
    return "기타"


def now_kst():
    return datetime.now(KST)


def list_briefings():
    """docs/briefings/brief_YYYYMMDD.pdf 목록 (최신순)"""
    out = []
    if not os.path.isdir(BRIEF_DIR):
        return out
    for f in os.listdir(BRIEF_DIR):
        if f.startswith("brief_") and f.endswith(".pdf") and len(f) == len("brief_20260101.pdf"):
            d = f[6:14]
            if d.isdigit():
                out.append((d, f, os.path.getsize(os.path.join(BRIEF_DIR, f))))
    return sorted(out, reverse=True)
