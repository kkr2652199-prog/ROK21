# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-QUOTA-MARKOV80-DONE
- 할일: markov floor 4/5 ge3=**0.0900** · gate >0.09 **FAIL**(1bp) · **롤백 25/60/15 완료** · 0.09+ 추가 경로 결정 · **형 GO 대기**
- 완료조건: gate 재정의 또는 aux/wire 튜닝 지시서 + 형 GO
- 선행완료: K-QUOTA-MARKOV80-REV2 smoke PASS · n=100 FAIL · rollback

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-QUOTA-MARKOV80** — ge3=0.0900 quota 80/20/0 · vs quota60 +0.01 · rolled back
- **K-AUX-DIAG** — spotlight 필수 · balance markov 억제 · ge3 aux ablation 무변
- **K-FUSION-QUOTA-FIX** — ge3=0.0800 · 20/60/20 live (rollback 후)
