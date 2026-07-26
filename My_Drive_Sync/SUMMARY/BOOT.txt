# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: D배선 구현(기본 OFF) · 창200 순효과 YES[1.020,1.044] · OFF해시 동일
- 직전: EV최종 순효과 생존 · 배선 설계 허용
- 다음: ROK21_EV_RERANK=1 운영시험(승인) · K-09 스냅샷 패치

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| OFF 해시 동일 | **YES** (30회) | D배선 |
| 창200 mean A/D | **0.793** / **0.820** | 동상 |
| 창200 순배율 D / CI | **1.032** [1.020, 1.044] | 동상 |
| CI하한>1 | **YES** | 동상 |
| env 기본 | **OFF** (`ROK21_EV_RERANK=1`만 ON) | ev_rerank |
| 1등↔3등 pearson | ≈0.70 | S4 |
| testlotto MAX | 1234 | DB |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · K-08 · K-09 · K-10 · K-11(적중폐기+EV생존) · K-12 = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `RESTORE.md`
2. `STATUS_LATEST.md`
3. `reports/20260726_ROK21_D배선_사전등록검증.md`
4. `docs/benchmarks/20260726_D배선/summary.json`
