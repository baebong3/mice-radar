# 이슈레이더

주제를 등록하면 매일 뉴스를 모아 **주제별 핵심 뉴스 3개**를 골라 앱 첫 화면과 아침 메일로 보여주는 웹 앱이다. 휴대폰 화면을 기준으로 만들었고 홈 화면에 설치할 수 있다.

## 실행

```bash
pip install -r service/requirements.txt
RADAR_DEV=1 uvicorn service.web:app --reload      # http://localhost:8000
python -m service.jobs daily                      # 수집 → 핵심 3개 선정 → 메일 발송 (하루 한 번)
python -m unittest service.tests.test_service     # 테스트
```

`RADAR_DEV=1`이면 메일 서버 없이 로그인 링크가 화면에 바로 나온다. 운영 서버에서는 켜지 않는다.

## 화면

| 주소 | 내용 |
|---|---|
| `/` | 소개와 가입 (이메일 링크 로그인) |
| `/app` | 오늘: 주제별 핵심 뉴스 3개, 전체 기사 목록. 주제가 없으면 추천 주제를 한 번 눌러 등록 |
| `/topics` | 주제 등록·삭제, 요금제 한도 |
| `/settings` | 메일 켜기·끄기, 요금제, 로그아웃, 계정 삭제 |
| `/plans` | 요금제 |

## 핵심 뉴스 3개를 고르는 방식 (`summarize.py`)

1. `ANTHROPIC_API_KEY`가 있으면 Claude가 그날 기사 목록을 읽고 3개를 골라 제목과 한 문장 요약을 쓴다.
2. 키가 없거나 호출이 실패하면 제목이 비슷한 기사를 묶어 보도 건수가 많은 사안 3개를 고른다. 이때는 요약 문장 없이 대표 기사 제목만 나온다. 표현이 많이 다른 같은 사안은 따로 잡힐 수 있다.

같은 주제를 여러 사람이 등록해도 수집과 선정은 주제당 하루 한 번만 한다.

## 구성

| 파일 | 역할 |
|---|---|
| `web.py` | 화면과 요청 처리 |
| `collector.py` | 주제별 Google News RSS 수집, 중복 제목 제거 |
| `summarize.py` | 핵심 뉴스 3개 선정 |
| `reports.py` | 선정 결과 저장, 사용자별 화면·메일 본문 조립 |
| `mailer.py` | SMTP 발송 (설정이 없으면 `data/outbox/`에 .eml 저장) |
| `jobs.py` | 일일 작업, 요금제 수동 변경(`set-plan`), 현황(`stats`) |
| `config.py` | 환경변수, 요금제 표, 추천 주제 |
| `Dockerfile` | 서버 배포용 (빌드해 보지는 않았다) |

## 환경변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `RADAR_BASE_URL` | `http://localhost:8000` | 메일 링크에 들어가는 서비스 주소. https면 쿠키에 Secure가 붙는다 |
| `RADAR_DB` | `service/data/app.db` | SQLite 파일 위치 |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | 없음 | 메일 발송 계정 |
| `ANTHROPIC_API_KEY` | 없음 | 있으면 한 문장 요약을 만든다 |
| `RADAR_SUMMARY_MODEL`, `RADAR_SUMMARY_EFFORT` | `claude-opus-5-5`, `low` | 요약 모델과 강도 |
| `RADAR_SCHEDULER`, `RADAR_SEND_HOUR` | `0`, `8` | `1`이면 서버가 매일 해당 시각(KST)에 일일 작업을 직접 돌린다. 서버가 한 대일 때만 쓴다 |

## 요금제

| 요금제 | 주제 수 | 월 요금(부가세 포함) |
|---|---|---|
| 무료 | 5개 | 0원 |
| 플러스 | 15개 | 4,900원 |
| 프로 | 40개 | 9,900원 |
| 팀 | 100개 | 29,000원 |

기능은 모두 같고 주제 수만 다르다. `config.py`의 `PLANS`에서 고친다. 결제는 연동하지 않았고, 유료 전환은 `python -m service.jobs set-plan 이메일 plus`로 수동 처리한다.

## 아직 하지 않은 것

- 결제 연동
- 서버 배포와 도메인, 메일 발송 도메인 인증(SPF·DKIM)
- 이용약관·개인정보처리방침 화면
- 로그인 요청의 IP 단위 제한 (지금은 이메일당 시간당 5회만 제한)
