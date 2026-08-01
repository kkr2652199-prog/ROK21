# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-10SET-DET-LAB-FULL
- 할일: K-10SET-DET-LAB-COMBO QUICK PASS → full n=1182 · pool10_combined vs det · wire는 형 GO 전 금지
- 완료조건: `20260801_K10SET_DET_LAB_survey_full.json` · ge3 vs pin · det_topk 판정
- 선행완료: K-10SET-DET-LAB-COMBO QUICK PASS (pool10_combined ge3=0.145 · det FAIL)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-COMBO** — pool10_combined ge3=**0.145** · det_topk **0.095~0.105 FAIL**
- **K-ATTACK-HOLD** — COMBO/V2/SELECT 축 wire HOLD
- V2 pin ge3=0.1447 · SELECT-FULL ge3=0.1218
