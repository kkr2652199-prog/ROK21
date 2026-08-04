# K-EVOLVE-VIRTUAL draw=1235

📅 2026-08-04 · **PASS** · 확정회차 가상 생애(분석스택)

## 적용 스택

- hybrid: `hy_p45_r123 (stat/review) · markov baseline`
- feedback mode: **mean** (predictions 없으면 no-op)
- cache schema: **3**
- λ wire: **False** · cover: struct=False pair=False
- weight: **0**

## 실제번호 · 명분진단

- actual = `[6, 7, 11, 15, 39, 43]`
- prev(1234) = `[1, 15, 19, 31, 35, 43]`
- consec_pairs=1 · carry=2 · odd=5 · sum=121 · zones=[4, 0, 2]

## SCORE (재예측 후)

- **stat** best=2 mean=0.6 assemble=`hy_p45_r123` ge3=False
- **markov** best=1 mean=0.4 assemble=`baseline_repack` ge3=False
- **review** best=2 mean=0.8 assemble=`hy_p45_r123` ge3=False

## before → after (best_hits)

- markov: 1 → **1** (mean 0.4 → 0.4) assemble `unknown` → `baseline_repack`
- review: 2 → **2** (mean 0.4 → 0.8) assemble `unknown` → `hy_p45_r123`
- stat: 2 → **2** (mean 0.8 → 0.6) assemble `unknown` → `hy_p45_r123`

- feedback: `{"ok": true, "draw_no": 1235, "mode": "mean", "via": "_auto_feedback"}`

근거: `20260805_KEVOLVE_VIRTUAL_1235.json`

비고: 1236(이번주) 미추첨 · 본 실행은 스테이징 회차 가상진행. λ/covering 재wire 없음.
