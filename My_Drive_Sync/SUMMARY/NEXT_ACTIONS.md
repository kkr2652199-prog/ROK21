# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: **확정** — 10SET FULL FAIL · survey 중단 · V2 pin 유지 · 형 GO 대기
- 완료조건: STATUS·TEST_PRIORITY 반영 ✅ · coordinator 미배선 ✅
- 선행완료: K-10SET-DET-LAB-FULL **FAIL** (pool10 ge3=0.1218 · SELECT-FULL 동일)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
