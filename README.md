# MICE 이슈 레이더

한국관광공사 MICE 산업 일일 이슈 모니터링 (발주 한국관광공사 · 수행 (주)서던포스트)

- 메인: https://baebong3.github.io/mice-radar/
- 브리핑 모음: https://baebong3.github.io/mice-radar/briefings/

## 구성
| 경로 | 역할 |
|---|---|
| `radar/collect.py` | Google News RSS로 MICE 유치·전시·컨벤션 2개 트랙 수집 → `data/news.db` |
| `radar/build.py --days 7` | 메인 페이지 `docs/index.html` 생성 (브리핑 건수 포함) |
| `radar/briefings.py` | 브리핑 모음 `docs/briefings/index.html` 생성 |
| `.github/workflows/collect.yml` | 매일 08:30 KST 수집·페이지 갱신·커밋 (수동 실행 가능) |
| `docs/assets/kto_signature.png` | 한국관광공사 시그니처 (브리핑 PDF 헤더용, 직접 추가) |
| `docs/briefings/brief_YYYYMMDD.pdf` | 일일 이슈 브리핑 (예약 작업이 추가) |

## news 테이블
url, track(MICE 유치|전시·컨벤션), title, media, date(보도일 KST), summary, note(검색어), category(리스크·쟁점/정책·예산/발주처/유치·개최/통계·실적/해외·경쟁국/지자체·시설/기타), source, collected_at(KST)

검색어·분류 규칙은 `radar/common.py`에서 고친다.
