# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-TRANSITION-FUSION-N200-DONE
- 할일: n200 결과 형 확인 · KEEP→현배선유지 / MARGINAL→추가검증or조건부유지 / ROLLBACK→`K_STAT_TRANSITION_V1=0` 즉시적용(**적용완료·WIRE=False**) · 다음회차 자동수집 대기
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KTRANSITION_FUSION_N200.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- fusion n200: ge3=**0.135**(=baseline) · mean_hit=**1.715**(&lt;1.8) → **ROLLBACK**
- `TRANSITION_V1_WIRE=False` 적용됨 · 재ON=`K_STAT_TRANSITION_V1=1`
- by_period STABLE (max_gap 0.028)
