"""이슈레이더 서비스 설정 (환경변수로 덮어쓴다)"""
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("RADAR_DB", os.path.join(HERE, "data", "app.db"))
OUTBOX = os.environ.get("RADAR_OUTBOX", os.path.join(HERE, "data", "outbox"))
BASE_URL = os.environ.get("RADAR_BASE_URL", "http://localhost:8000").rstrip("/")
# 개발 모드: 메일 서버 없이 로그인 링크를 화면에 바로 보여준다. 운영에서는 반드시 끈다.
DEV = os.environ.get("RADAR_DEV", "0") == "1"
SERVICE_NAME = "이슈레이더"
KST = timezone(timedelta(hours=9))

# 메일 (SMTP_HOST가 없으면 data/outbox 폴더에 .eml 파일로 남긴다)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "이슈레이더 <no-reply@localhost>")

# 요약 (API 인증 정보가 없으면 주요 기사 제목 나열로 대신한다)
SUMMARY_MODEL = os.environ.get("RADAR_SUMMARY_MODEL", "claude-opus-5-5")
SUMMARY_EFFORT = os.environ.get("RADAR_SUMMARY_EFFORT", "low")

# 수집·발송
COLLECT_WHEN = os.environ.get("RADAR_COLLECT_WHEN", "2d")
SEND_HOUR = int(os.environ.get("RADAR_SEND_HOUR", "8"))  # KST, 내장 스케줄러용
SCHEDULER = os.environ.get("RADAR_SCHEDULER", "0") == "1"
ARTICLES_PER_TOPIC = 8

# 요금제: (코드, 이름, 주제 수, 월 요금(원)). 금액은 가안이며 결제 연동 전이다.
PLANS = [
    ("free", "무료", 5, 0),
    ("basic", "베이직", 15, 4900),
    ("pro", "프로", 40, 9900),
    ("business", "비즈니스", 100, 29000),
]
PLAN_LIMIT = {code: limit for code, _, limit, _ in PLANS}
PLAN_NAME = {code: name for code, name, _, _ in PLANS}

LOGIN_TOKEN_MINUTES = 20
SESSION_DAYS = 30
LOGIN_REQUESTS_PER_HOUR = 5


def now_kst():
    return datetime.now(KST)


def today_kst():
    return now_kst().strftime("%Y-%m-%d")
