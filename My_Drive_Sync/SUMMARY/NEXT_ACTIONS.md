# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-BRAIN-PACKAGE-PHASE1
- 할일: stat_brain 구현 — predict_statistical·predict_stat_fairy → stat_brain/engine·learn·aux·predict 이전 · **동치 n=200** (draw 1035~1234 · ge3·mean·nums 허용오차 0)
- 완료조건: stat_brain.run() wired · 동치 PASS · 보고서
- 선행완료: K-BRAIN-PACKAGE-PHASE0 **OK** (19파일 스켈레톤 · 기존 미변경)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
