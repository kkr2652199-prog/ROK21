# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-TUNE-ENGINE-APPLY
- 할일: 후보 `short_win=26`/`short_mix=0.8`(seed n50 ge3**0.28** Δ+0.16) 상수적용 여부 · 또는 fusion n200 검증 · **형 GO**
- 완료조건: 형 GO(적용/보류/n200) 실행
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_TUNE_ENGINE.json
- 승인필요: 필요
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- base v2 win52/mix0.6: ge3**0.12**/mean**1.78** (SOFT와 시드일치)
- v1: ge3**0.04** · 후보 win26 mix0.8: ge3**0.28**/mean**1.88** · applied=False
- env시험: `K_STAT_ENG_SHORT_WIN=26` `K_STAT_ENG_SHORT_MIX=0.8`
