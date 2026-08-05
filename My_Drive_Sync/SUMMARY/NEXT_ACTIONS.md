# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-TRANSITION-COLLECT-DESIGN-DONE
- 할일: 수집 구조 완료 · backfill 검증 · 형 확인 → **STEP2 (데이터 재검증)** 또는 다음 회차 자동수집 대기
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- transition_log 생성 · backfill 101~1234 n=1134 · collect mean_hit≈1.998 (N→N+1)
- FULL 동치 재현 mean_hit=**2.171806** match ✅ · wire/뇌/발권 미접촉
- hook: `.cursor/hooks/transition_collect_hook.py` (stop에 추가)
