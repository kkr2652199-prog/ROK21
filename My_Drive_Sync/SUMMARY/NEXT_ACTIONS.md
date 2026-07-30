# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-SIGNAL-SELECT-FULL
- 할일: QUICK PASS(combined ge3=0.145) → full n=1182 walk-forward 재실행 · pin+p<0.05 확인 · wire는 형 GO 전 금지
- 완료조건: `20260730_KSIGNAL_SELECT_survey.json` full 섹션 또는 full-only JSON · ge3 vs pin 판정
- 승인필요: full 실행=아니(QUICK PASS 후 자동) · wire=예
- 선행완료: 2026-07-30 (K-SIGNAL-REPACK-01 — top5 ge3=0.085 < combined 0.145 · 5장 공정 FAIL)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **K-SIGNAL-REPACK-01** — top5 ge3=0.085 · combined 0.145 · 5장 공정 FAIL · `20260730_KSIGNAL_REPACK_SURVEY.md`
- **K-SIGNAL-SELECT-01 QUICK** — combined ge3=0.145 · set_no_asc=0.08 · `20260730_KSIGNAL_SELECT_SURVEY.md`
- **K-QUICK-GATE-01** — BENCH §9 · bench_quick_gate.py · tail-200 seed=42
- **K-WINDOW-SIGNAL-01** — best w4_zone_mix ge3=0.1328 · pin 미달
- **4AUX_FEEDBACK_REVIEW** — set_no_asc AUX 컷 없음 · `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
