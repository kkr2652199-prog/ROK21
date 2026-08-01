# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-WIRE-SELECT-GO-WAIT
- 할일: conf_global_top5(+0.01) 또는 aux_hint_quota(+0.005) wire A/B — 형 GO 전 coordinator 미패치 · FULL n=1182 재검증
- 완료조건: 형 GO + wire patch + FULL backtest PASS
- 선행완료: K-QUOTA-GAP-SURVEY **OK** (conf_global_top5 ge3=0.135 · aux_hint=0.130 · set_no_asc=0.125 · quota_gap=43.0%)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
