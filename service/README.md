# 이슈레이더 (주제 구독형 뉴스 리포트)

주제를 등록하면 매일 뉴스를 모아 요약 리포트를 메일로 보내는 웹 앱이다. `radar/`의 MICE 이슈 레이더 수집 방식을 주제 단위로 일반화했다. 기존 `radar/`, `docs/`, GitHub Actions와는 파일을 공유하지 않는다.

## 실행

```bash
pip install -r service/requirements.txt
RADAR_DEV=1 uvicorn service.web:app --reload      # http://localhost:8000
python -m service.jobs daily                      # 수집 → 요약 → 발송 (하루 한 번)
python -m unittest service.tests.test_service     # 테스트
```

`RADAR_DEV=1`이면 메일 서버 없이 로그인 링크가 화면에 바로 나온다. 운영 서버에서는 켜지 않는다.

## 구성

| 파일 | 역할 |
|---|---|
| `web.py` | 화면과 요청 처리 (로그인, 주제 등록·삭제, 요금제, 수신 거부, 계정 삭제) |
| `collector.py` | 주제별 Google News RSS 수집, 중복 제목 제거 |
| `summarize.py` | 주제별 일일 요약 (Claude API, 인증 정보가 없으면 주요 기사 제목으로 대체) |
| `reports.py` | 요약 저장, 사용자별 리포트와 메일 본문 조립 |
| `mailer.py` | SMTP 발송 (설정이 없으면 `data/outbox/`에 .eml 저장) |
| `jobs.py` | 일일 작업, 요금제 수동 변경(`set-plan`), 현황(`stats`) |
| `config.py` | 환경변수, 요금제 표 |
| `static/`, `templates/` | 화면, 홈 화면 설치용 매니페스트와 서비스 워커 |

같은 주제를 여러 사람이 등록해도 수집과 요약은 주제당 하루 한 번만 한다.

## 환경변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `RADAR_BASE_URL` | `http://localhost:8000` | 메일 링크에 들어가는 서비스 주소. https면 쿠키에 Secure가 붙는다 |
| `RADAR_DB` | `service/data/app.db` | SQLite 파일 위치 |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | 없음 | 메일 발송 계정 |
| `ANTHROPIC_API_KEY` | 없음 | 있으면 핵심 이슈 요약을 만든다 |
| `RADAR_SUMMARY_MODEL`, `RADAR_SUMMARY_EFFORT` | `claude-opus-5-5`, `low` | 요약 모델과 강도 |
| `RADAR_SCHEDULER`, `RADAR_SEND_HOUR` | `0`, `8` | `1`이면 서버가 매일 해당 시각(KST)에 일일 작업을 직접 돌린다. 서버가 한 대일 때만 쓴다 |

## 요금제

`config.py`의 `PLANS`에서 고친다. 금액은 가안이고 결제는 연동하지 않았다. 유료 전환은 `python -m service.jobs set-plan 이메일 basic`으로 수동 처리한다.

## 아직 하지 않은 것

- 결제 연동 (토스페이먼츠, 포트원 등 가맹 계약 필요)
- 서버 배포와 도메인, 메일 발송 도메인 인증(SPF·DKIM)
- 이용약관·개인정보처리방침 화면
- 로그인 요청의 IP 단위 제한 (지금은 이메일당 시간당 5회만 제한)
- 가입자가 늘면 SQLite를 PostgreSQL로, RSS 수집을 정식 뉴스 API로 바꾸는 검토
