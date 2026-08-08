# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-INDEPENDENT-TUNE-DONE
- 할일: **SCORE_WEIGHTS 뇌별 APPLY 완료**. cand_A(stat 0.25/0.35/0.40 · markov·review 0.55/0.20/0.25). 축지표 1100~1235: prefer+0.023 · prize−0.027 · stat hit+0.005 · review 3구간 consistent. 형 1건 — **①군중 BLEND_STRENGTH 소튜닝**(review EV 강화 후보) / ②1235 과거학습 명분리뷰 / ③정지
- 완료조건: 형이 ①~③ 중 1건 지정
- 선행완료: docs/benchmarks/20260808_KBRAIN_INDEPENDENT_TUNE.json · reports/20260808_KBRAIN_INDEPENDENT_TUNE.md
- 승인필요: 없음 (다음 선택만)
- 선행조건: 없음
- 최종갱신: 2026-08-08


## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- SCORE_WEIGHTS 롤백: 전뇌 `(0.40, 0.25, 0.35)`
- 군중 롤백: `K_CROWD_PREFER=0` · `K_PRIZE_EV=0`
