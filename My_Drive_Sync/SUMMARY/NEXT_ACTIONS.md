# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-FUSION-INNOVATION-DONE
- 할일: conf bucket+AUX reweight ge3=**0.0900** · vs V2 **+0.0000** · gate FAIL · **INNOVATION 롤백 완료** · V2 live · 0.09+ 경로 · **형 GO 대기**
- 완료조건: gate >0.09 달성 지시서 + 형 GO
- 선행완료: smoke PASS · n=100 FAIL · INNOVATION 2곳 롤백 · V2 quota 유지

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-FUSION-INNOVATION** — early 0.12 · mid 0.04 · late 0.10 · overall tie 0.09 · aux ablation 예상대로 ge3 무변
- **K-FUSION-DYNAMIC-V2** — SOLO_GE3_PRIORS live · ge3=0.0900
- **K-AUX-DIAG** — spotlight 필수 · balance markov 억제
