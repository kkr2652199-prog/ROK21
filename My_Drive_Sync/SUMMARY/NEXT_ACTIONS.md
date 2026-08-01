# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-WIRE-SELECT-GO-WAIT
- 할일: FULL FAIL·collapse(0.135→0.1117) — wire **HOLD 권고** · 형 명시 GO 시 conf_global_top5 wire A/B · coordinator 미패치
- 완료조건: 형 GO + wire patch + FULL backtest PASS
- 선행완료: K-WIRE-SELECT-FULL-SURVEY **OK** (conf_global_top5 FULL ge3=0.1117 p=0.600 · set_no_asc=0.1015 · quota_gap=43.1% · wire_go=wait)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
