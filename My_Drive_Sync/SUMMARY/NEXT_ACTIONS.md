# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-TUNE-DONE
- 할일: APPLY PASS(win26/mix0.8·fusion Δ0) 형 확인 · 추가 튜닝(decay 등) or 트랙정지
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- tune n50 ge3**0.28**/mean**1.88** 재현 · holdout1085~1134 ge3**0.14**/mean**1.72**
- fusion n200 ge3**0.135** Δ**0** (pin유지) · 롤백=`V2_SHORT_WIN=52`/`V2_SHORT_MIX=0.6`
