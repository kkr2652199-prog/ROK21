# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-CROWD-NEXT-PICK
- 할일: **K-BRAIN-CROWD-RESTRUCTURE 완료**(WIRE_SMOKE_OK). markov=선호번호 · review=금액뇌 · crowd_signal 배선 · 학술벤치 반영. 형 1건 — **①선호/금액 EV프록시 소구간 게이트 설계**(권장 · ge3 아님 · first_winners/몫 축) / ②1235 과거학습 명분 샘플 리뷰 / ③정지
- 완료조건: 형이 ①~③ 중 1건 지정
- 선행완료: app/testlotto/brains/shared/crowd_signal.py · docs/benchmarks/20260808_KBRAIN_CROWD_RESTRUCTURE.json · reports/20260808_KBRAIN_CROWD_RESTRUCTURE.md
- 승인필요: 없음 (배선·문서 · DB커밋 안 함)
- 선행조건: 없음
- 최종갱신: 2026-08-08


## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- HOLD 복원: `lotto4.js` → `ROK21_TESTLOTTO_FOCUS_HOLD = false`
- 숨김: 두뇌예측 · 전략 X · 효도로또
- 롤백: `K_CROWD_PREFER=0` · `K_PRIZE_EV=0`
