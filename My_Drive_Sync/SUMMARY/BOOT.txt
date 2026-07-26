# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: EV보정+tier1시뮬 — 위약편향 YES · EV이득 미입증 · D배선 철회
- 직전: RESTORE + EV 리랭커 WF (예측배율 순환 문제)
- 다음: 위약통과형 EV평가 설계(승인) · K-09 · D재제안 금지

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| 보정 b (WF) / R² | **0.643** / 0.108 | EV보정 |
| B/D 실현배율 (신) | **1.056** / **1.049** | 동상 |
| 위약 B/D 배율 | 1.023 / 1.020 (CI>1) → **편향YES** | 동상 |
| EV 축 / D 배선 | **미입증** / **철회** | P1 판정 |
| tier1 완화 p10 실현 vs T0 | ≤**1.002** | P2 참고 |
| A 메타 mean (참고) | 0.773 | 직전 WF |
| testlotto MAX | 1234 | DB |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · K-08 · K-09 · K-10 · K-11 · **K-12** = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `RESTORE.md`
2. `STATUS_LATEST.md`
3. `reports/20260726_ROK21_EV보정_tier1시뮬.md`
4. `docs/benchmarks/20260726_EV보정/summary.json`
