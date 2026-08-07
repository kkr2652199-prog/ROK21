# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-DETAIL-TUNE
- 할일: 틀(FRAME_LOCKED) 위 세부 튜닝 — decay(`LONG`/`SHORT`) 등 · 시드 n50+holdout · fusion 회귀 · **형 GO**
- 완료조건: 세부 스윕 JSON + 후보1안(적용은 별도 GO)
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_FRAME_DONE.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- 틀: pipe + win26/mix0.8 + soft/ASSOC/transition OFF 정책
- 세부 예정: LONG_DECAY / SHORT_DECAY · cycle_gap 등
- fusion pin ge3**0.135** 유지 목표
