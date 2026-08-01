# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-HIGHWAY-PHASE1-HOLD
- 할일: BACKTEST-100 **FAIL** ge3=0.0600 · baseline −0.0415 · **형 GO 대기** (롤백/HOLD/튜닝)
- 완료조건: 형 GO + 후속 지시
- 선행완료: K-HIGHWAY-BACKTEST-100 **FAIL** (overall ge3=0.0600 · n=100 · learn 루프 동작 확인)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **K-BRAIN-SIGNAL-A1** — 설계 검토 완료(2026-08-01) · Q1~Q4 커서 답변 · **형 GO + K-HIGHWAY 결정 후** 착수
- **K-10SET-DET-LAB-FULL** — pool10 ge3=**0.1218** p=0.201 · QUICK 0.145→FULL collapse · **FAIL**
- **K-10SET-DET-LAB-COMBO QUICK** — pool10 ge3=0.145 · det_topk FAIL
- V2 pin ge3=0.1447 · wire HOLD
