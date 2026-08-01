# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-COMBO-SIGNAL-FULL
- 할일: K-COMBO-SIGNAL-01 QUICK **PASS** → full n=1182 검증 · signal_A 0% 재검토 · wire는 형 GO 전 금지
- 완료조건: `20260801_KCOMBO_SIGNAL_survey_full.json` · ge3 vs pin · AB coverage
- 선행완료: K-COMBO-SIGNAL-01 QUICK PASS (baseline ge3=0.145 · AB_cov=0)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-COMBO-SIGNAL-01 (20260801)** — QUICK PASS · baseline ge3=**0.145** · **signal_AB=0%** (AND 미발화)
- **K-EXCLUDE-SURVEY** — QUICK FAIL · λ sweep · exclude ON ≤ baseline
- **K-SIGNAL-SELECT-FULL** — combined ge3=**0.1218** · **FAIL** · wire HOLD
- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **TESTLOTTO UI+DB** — pool/repack · PATCH_PINS · 7021
