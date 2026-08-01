# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-NEW-ENGINE-MARKOV-A1
- 할일: markov_brain engine 개선 (STAT-A1 패턴) · build_weights 변경 · bench A/B · 형 GO 시
- 완료조건: bench PASS 또는 HOLD 확정 + ENGINE_V2 default 안전
- 선행완료: K-NEW-ENGINE-STAT-A1 **PASS** (baseline ge3=0.1350 · v2=0.1350 · delta=0 · ENGINE_V2=False 유지)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
