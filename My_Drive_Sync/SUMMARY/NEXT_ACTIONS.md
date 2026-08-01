# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: **확정** — survey 전 축 HOLD · V2 pin 유지 · 형 GO 전 wire·survey 중단
- 완료조건: STATUS·TEST_PRIORITY 반영 · coordinator 미배선 확인 ✅
- 선행완료: K-COMBO-V2 FAIL · K-COMBO-SIGNAL-01 hollow PASS · SELECT-FULL FAIL

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-ATTACK-HOLD 확정 · survey 전 축 HOLD** (20260801 마감)
- **coordinator 미배선:** `coordinator.py`에 COMBO/SELECT/EXCLUDE/steering 배선 없음 · 최근 변경 `3b0f619` K-MARKOV-WIRE-V2 set_no 쿼터만
- **K-COMBO-V2** — combo_v2 ge3=0.125 · baseline=0.145 · **FAIL**
- **K-COMBO-SIGNAL-01** — AB=0% hollow PASS · FULL 미실행
- **K-SIGNAL-SELECT-FULL** — combined ge3=0.1218 · FAIL
- V2 pin ge3=0.1447 · wire HOLD
