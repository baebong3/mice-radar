# 일일 이슈 브리핑 예약 작업 지시문 - 4장 교체본

예약 작업 지시문의 「4. PDF 생성」과 「4-1 ~ 4-5」를 아래로 바꾼다. 1 ~ 3장(데이터 확보·선별·문체)과 5 ~ 6장(업로드·전달)은 그대로 둔다.
서식(글꼴·색·배치)은 저장소의 `radar/brief.py`가 정하므로, 작업은 내용 JSON만 채운다.

## 4. PDF 생성 - A4 세로 정확히 1쪽 (손그림 서식)

디자인은 서던포스트 「The Gauge 기준」 손그림판을 한국관광공사 과업용으로 옮긴 것이며 `radar/brief.py`에 고정돼 있다. HTML을 직접 쓰지 않고, 아래 순서로 내용 JSON을 만들어 생성기에 넘긴다. 서식 기준본은 `/tmp/mr/docs/briefings/brief_20261029.pdf`(제1호)이며, 처음에 pdftoppm으로 PNG를 떠서 결과가 같은 서식인지 눈으로 비교한다.

### 4-1. 준비 (매 실행 필수)
```
cd /tmp/mr
npm install pretendard @fontsource/gaegu @fontsource/jua @fontsource/nanum-brush-script @fontsource/permanent-marker --no-audit --no-fund --silent
mkdir -p ~/.fonts && cp node_modules/pretendard/dist/public/static/Pretendard-{Regular,Medium,SemiBold,Bold,ExtraBold}.otf ~/.fonts/ && fc-cache -f
pip install -q pypdf playwright 2>/dev/null; true
```
- 로고는 저장소의 `docs/assets/kto_signature.png`(한국관광공사)와 `docs/assets/southernpost.png`(서던포스트)를 생성기가 자동으로 넣는다. 파일이 없으면 생성기가 "로고 파일 없음"으로 멈추므로 PDF를 만들지 말고 그 사실만 알린다.
- 손글씨 글꼴이 설치되지 않으면(npm 실패) Jua·Gaegu 자리는 Pretendard로 대체되므로, 그 경우 알림에 "손글씨 글꼴 미적용"을 적는다.

### 4-2. 내용 JSON 작성
`radar/brief_example.json`을 복사해 `/tmp/brief_YYYYMMDD.json`으로 만들고 값을 채운다. 구조:
- `date`(YYYY-MM-DD, 실행 당일 KST), `no`(호수 = 기존 `docs/briefings/brief_*.pdf` 개수 + 1)
- `kpi`: `new_total`·`new_by_track`(오늘 수집분, 트랙별), `selected`(과업 관련 선별 기사 수)·`merged`(같은 사안 통합 후 건수)·`excluded`·`excluded_pct`, `total`(누적)·`last`("MM.DD HH:MM"), `period`("10.28 ~ 10.29"), `period_note`, `period_warn`(오늘 수집분이 없으면 true - 설명이 레드 굵게 찍힘)
- `counts`: 중요도 분류 7개의 통합 건수 (리스크·쟁점 / 정책·예산 / 발주처 / 유치·개최 / 통계·실적 / 해외·경쟁국 / 지자체·시설)
- `issues`: 주요 이슈 3건. 각각 `rank`, `cat`(분류명), `tracks`(["MICE 유치","전시·컨벤션"] 중 해당), `verified`(원문 대조 성공 여부 - false면 레드 "원문 미확인" 태그), `title`, `bullets`(개조식 3~4개, 핵심 수치는 `<b>`), `source`("매체 外 N개 매체 · 일자"), `insight`(시사점 1문장). 1번은 전폭 카드로 불릿이 2열로 흐르므로 불릿 4개 이하, 각 60자 안쪽
- `trends`: 트랙별 3~4건. 각각 `date`, `media`(`<b>外 N개 매체</b>` 허용), `title`, `desc`(한 줄, 넘치면 잘리므로 28자 안쪽, 핵심어만 `<b>`)
- `trend_empty`: 해당 트랙 선별 건이 없을 때 `{"전시·컨벤션": {"reason": "...", "examples": ["제외한 기사 제목", ...]}}`
- `actions`: 과업 반영사항 3개 `{label, text}` - label은 예산 동향 / 통계 활용 / 시설 수급 / 유치 경쟁 / 성과지표 중에서, 6자 이내
- `verified_count`: 원문 대조에 성공한 주요 이슈 수

문체는 3장 규칙(개조식, 마침표 없음, 천 단위 콤마, 줄표 대신 하이픈, 말줄임 금지)을 그대로 따른다.

### 4-3. 생성 및 검수
```
python3 radar/brief.py /tmp/brief_YYYYMMDD.json --fonts node_modules --html /tmp/brief_YYYYMMDD.html --out /tmp/이슈브리핑_YYYYMMDD.pdf
```
생성기가 pypdf로 쪽수를 확인해 1쪽이 아니면 오류로 멈춘다. 2쪽이 나오면 ① 트랙 동향 `desc`·과업 반영사항 `text`를 줄이고 ② 1번 카드 불릿을 3개로 줄여 다시 만든다(생성기 코드와 글꼴 크기는 고치지 않는다). 1쪽 확인 전에는 전달하지 않는다.
pdftoppm으로 PNG를 떠서 로고 2개가 찍혔는지, 제호의 손글씨(MICE · 이슈 레이더)가 보이는지, 글자 겹침·말줄임·바닥글 잘림이 없는지, 카드 마지막 줄에 한두 글자만 떨어지지 않는지 눈으로 확인하고 문구를 고쳐 다시 뽑는다. 파일명은 `이슈브리핑_YYYYMMDD.pdf`. 작업 파일은 /tmp 아래(저장소 밖)에서 만든다.
