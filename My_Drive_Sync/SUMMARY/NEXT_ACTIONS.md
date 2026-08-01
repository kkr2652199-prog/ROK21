# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-HIGHWAY-REFEREE
- 할일: coordinator referee 가중 자동 갱신 · **형 GO 대기**
- 완료조건: 형 GO + K-HIGHWAY-PHASE1 연속 PASS
- 선행완료: K-HIGHWAY-FEEDBACK **OK** — `_auto_feedback` · `_detect_missed_patterns` · deprecated import 삭제

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
