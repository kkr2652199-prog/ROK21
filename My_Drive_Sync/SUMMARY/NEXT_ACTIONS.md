# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-TUNE-SOFT
- 할일: past_learn SOFT_WEIGHT/SOFT_CONF_CAP 스윕 · solo n50 vs wire베이스(ge3**0.14**/mean**1.58**) · ASSOC기본OFF 유지
- 완료조건: 스윕 JSON + 최적후보 1안 보고 · 형 GO 전 fusion n200 금지
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_WIRE.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- past_learn.py WIRE ON · engine v2 ON · ASSOC OFF · transition OFF
- 롤백: `K_PAST_LEARN=0` · `K_STAT_ENGINE_V2=0`
- ASSOC FULL = NOISE_LIKE → 발권 연관힌트 기본 OFF
