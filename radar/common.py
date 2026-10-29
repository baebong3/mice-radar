"""MICE 이슈 레이더 공통 설정·DB 유틸"""
import os
import re
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

# 주제 분류 (앞에 있을수록 표시 우선순위가 높음)
CATEGORY_RULES = [
    ("리스크·쟁점", ["국정감사", "국감", "적자", "무산", "삭감", "논란", "특혜", "감사원", "부실", "갈등", "중단", "표류", "좌초", "지적", "질타", "우려", "재정 부담", "재정난", "혈세"]),
    ("정책·예산", ["문체부", "문화체육관광부", "산업부", "산업통상", "예산", "국비", "공모", "제도", "법 개정", "개정안", "진흥계획", "전시산업발전", "기본계획", "지원사업",
                 "국회", "토론회", "정책", "장관", "보증", "활성화 방안", "육성", "조례", "로드맵", "전략"]),
    ("발주처", ["한국관광공사", "코리아MICE뷰로", "코리아마이스뷰로"]),
    ("유치·개최", ["유치", "개최지", "총회", "국제회의", "학술대회", "학회", "컨퍼런스", "콘퍼런스", "포럼", "서밋", "인센티브", "바이어", "팸투어", "로드쇼", "설명회", "마이스 행사", "MICE 행사"]),
    ("통계·실적", ["ICCA", "UIA", "순위", "경제효과", "경제적 효과", "파급효과", "참관객", "관람객", "참가자", "방문객", "역대 최대", "역대 최다", "실적", "통계", "성료", "폐막", "상담", "계약 성사", "수출 계약", "만명", "만 명"]),
    ("해외·경쟁국", ["싱가포르", "일본", "중국", "태국", "홍콩", "대만", "베트남", "해외", "글로벌 MICE", "日", "中"]),
    ("지자체·시설", ["컨벤션센터", "전시장", "건립", "확장", "증축", "착공", "준공", "제2전시장", "제3전시장", "복합지구", "부지", "매각", "호텔", "MICE 단지", "마이스 단지",
                 "복합단지", "복합개발", "리모델링", "운영권", "위탁"]),
    ("산업 동향", ["MICE", "마이스", "비즈니스 관광", "비즈니스 여행", "기업 출장"]),
    ("전시회 개최·참가", ["개막", "참가", "박람회", "엑스포", "전시회", "페어", "FAIR", "개최", "기술대전", "산업대전", "모터쇼", "에어쇼", "위크", "페스타", "전시"]),
]
CATEGORIES = [c for c, _ in CATEGORY_RULES]

# 판정 순서: 구체적인 신호를 먼저 보고, 시설명·전시회처럼 넓은 신호는 나중에 본다
MATCH_ORDER = ["리스크·쟁점", "통계·실적", "발주처", "정책·예산", "유치·개최", "해외·경쟁국", "지자체·시설", "산업 동향", "전시회 개최·참가"]

# 명백한 잡음 (category='기타')
NOISE_WORDS = ["분양", "웨딩", "예식", "콘서트", "공연", "팬미팅", "팬들", "뮤지컬", "모델하우스", "입주", "청약", "[포토]", "포토]", "블로그",
               "굿즈", "가을야구", "플레이오프", "미술관", "갤러리", "회고전", "비엔날레", "아트", "캐시백", "인사혁신", "유치원"]

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


_RULES = dict(CATEGORY_RULES)
# 시설명만 있고 다른 신호가 없으면 지자체·시설로 둔다 (전시회 안내보다 뒤에 판정)
VENUES = ["킨텍스", "벡스코", "엑스코", "코엑스", "송도컨벤시아", "aT센터", "세텍", "DCC", "김대중컨벤션", "창원컨벤션", "수원컨벤션", "GSCO", "UECO", "컨벤션"]
# 해외·경쟁국은 MICE 맥락이 있을 때만
MICE_CONTEXT = ["MICE", "마이스", "컨벤션", "국제회의", "전시회", "전시장", "박람회", "관광"]
# '유치원'·'투자 유치'·'기업 유치' 등 MICE와 무관한 '유치'는 지운 뒤 판정
_FALSE_HITS = re.compile(r"엑스코프리|유치원|투자\s*유치|기업\s*유치|관객\s*유치|고객\s*유치|임차인\s*유치")


def classify(title, summary=""):
    if any(w in title for w in NOISE_WORDS):
        return "기타"
    text = _FALSE_HITS.sub(" ", f"{title} {summary}")
    for cat in MATCH_ORDER:
        if any(w in text for w in _RULES[cat]):
            if cat in ("해외·경쟁국", "리스크·쟁점") and not any(w in text for w in MICE_CONTEXT + VENUES):
                continue
            return cat
    if any(w in text for w in VENUES):
        return "지자체·시설"
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
