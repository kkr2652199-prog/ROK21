# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-FUSION-DYNAMIC-V2-DONE
- 할일: solo×ref quota ge3=**0.0900** · gate >0.09 **FAIL**(1bp tie) · live=SOLO_GE3_PRIORS+dominance1.15 · 0.09+ 경로(aux/wire/gate) · **형 GO 대기**
- 완료조건: gate 재정의 또는 aux/wire 튜닝 지시서 + 형 GO
- 선행완료: referee-only 0.06 FAIL → solo prior +0.03 · markov80 floor 동일 0.09

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-FUSION-DYNAMIC-V2** — SOLO_GE3_PRIORS(K-HIGHWAY) × referee · plan 4/0/1 · vs fixed 25/60/15 +0.01
- **K-QUOTA-MARKOV80** — ge3=0.0900 · rolled back (V2 solo prior가 동일 수치 대체)
- **K-AUX-DIAG** — spotlight 필수 · balance markov 억제 · ge3 aux ablation 무변
