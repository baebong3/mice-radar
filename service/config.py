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
ARTICLES_PER_TOPIC = 20

# 요금제: (코드, 이름, 주제 수, 월 요금(원), 한 줄 설명). 결제는 아직 연동하지 않았다.
PLANS = [
    ("free", "무료", 5, 0, "관심사 몇 가지를 챙기는 개인"),
    ("plus", "플러스", 15, 4900, "업계와 경쟁사를 함께 보는 실무자"),
    ("pro", "프로", 40, 9900, "여러 과제를 맡은 담당자"),
    ("team", "팀", 100, 29000, "부서 단위 모니터링"),
]
PLAN_LIMIT = {p[0]: p[2] for p in PLANS}
PLAN_NAME = {p[0]: p[1] for p in PLANS}

LOGIN_TOKEN_MINUTES = 20
SESSION_DAYS = 30
LOGIN_REQUESTS_PER_HOUR = 5


def now_kst():
    return datetime.now(KST)


def today_kst():
    return now_kst().strftime("%Y-%m-%d")

WEEKDAYS = "월화수목금토일"
# 처음 들어온 사람에게 한 번 눌러 등록하도록 보여주는 주제
SUGGESTED = ["인공지능", "반도체", "부동산 정책", "전기차", "환율", "관광 산업"]


def pretty_date(day):
    """'2026-11-26' → '11월 26일 (목)'"""
    d = datetime.strptime(day, "%Y-%m-%d")
    return f"{d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"
