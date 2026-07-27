# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: BENCH_PROTOCOL 고정 · K-M/N등재 · null상 best전원비실력 · 가중(a)≈(b)
- 직전: K-A~L · K-B/C/D 원인규명
- 다음: K-N/M 후속설계(형) · K-A는 프로토콜 준수 재측정 후

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| 성적 SSOT | review JSON **전세트 mean** | BENCH_PROTOCOL |
| stat/markov/review mean100 | 0.760 / 0.802 / 0.852 | KN분산 |
| null best 상회 | **전원 NO** | 동상 |
| top5 (a)vs(b) 멤버십차 | **5%** | KM시뮬 |
| Y풀 EV 순배율 | 1.033 [1.019,1.048] | K09 |
| kweon 동결 HEAD | **264de3c** | 실측 |

## 3) 열린 과제 -> FINDINGS.md
K-00·02·05~08·10~12 OPEN. **K-09 CLOSED.**  
K-A~K-N OPEN. 성적=**BENCH_PROTOCOL**. 우선: K-N/M 설계 → K-A.

## 4) 주의 (붕괴 방지)
- 이 레포=ROK21 (kweon 20260726 04:38 복사본). SSOT=ROK21 main
- kweon 은 20260726 `264de3c` 에서 동결. 신규 작업 금지
- 외부 AI 는 ROK21 만 조회할 것
- **성적=BENCH_PROTOCOL.md 준수**
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `BENCH_PROTOCOL.md`
2. `RESTORE.md` · `STATUS_LATEST.md`
3. `reports/20260727_KM_KN_분산검정.md`
4. `FINDINGS.md` (K-A~K-N)
