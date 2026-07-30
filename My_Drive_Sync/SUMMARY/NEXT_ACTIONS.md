# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-SIGNAL-SELECT-FULL
- 할일: **실행 중** — full n=1182 walk-forward · pin+p<0.05 확인 · wire는 형 GO 전 금지
- 완료조건: `20260730_KSIGNAL_SELECT_survey_full.json` · ge3 vs pin 판정
- 선행완료: K-EXCLUDE-HIST-01 · LEAKAGE_POLICY.md

## WORKSTATE
RUNNING:K-SIGNAL-SELECT-FULL

---

## 메모 (커서 아님 · guard 무시)

- **TESTLOTTO UI+DB (20260730)** — `testlotto_backtest_runs` 2건 · pool-view API · 7021 테스트로또 탭
- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **K-SIGNAL-REPACK-01** — top5 ge3=0.085 · combined 0.145 · 5장 공정 FAIL · r3=1
- **K-SIGNAL-SELECT-01 QUICK** — combined ge3=0.145 · set_no_asc=0.08
- **좁은 개선(다음)** — 200회 복습: combined vs repack top5 · **set_no_asc 컷·컨닝 금지**
- **K-QUICK-GATE-01** — BENCH §9 · tail-200 seed=42
- **4AUX_FEEDBACK_REVIEW** — set_no_asc AUX 컷 없음
