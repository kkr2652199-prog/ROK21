# K-BRAIN-SIGNAL-BACKTEST-100 — pattern_signal stack n=100

📅 2026-08-01 · **FAIL** · draw 1135~1234

근거: `20260801_KBRAIN_SIGNAL_BACKTEST_100.json`

## SUMMARY

| 지표 | 값 |
|------|-----|
| overall ge3_rate | **0.0600** (6/100) |
| mean_match | **1.6300** |
| p vs null (0.1137) | 미확인 |
| signal_active_rate | **100.00%** (100/100) |
| vs highway 0.0600 | **+0.0000** |
| vs baseline 0.1015 | **-0.0415** |
| verdict | **FAIL** |

## PASS/FAIL 기준

- PASS: ge3 > 0.0600 **AND** signal_active > 20%
- FAIL: ge3 ≤ 0.0600 **OR** signal_active ≤ 5%

## by_brain (solo best-of-5)

| brain | ge3_rate | ge3_count | mean_match |
|-------|----------|-----------|------------|
| stat | 0.0900 | 9 | 1.7100 |
| markov | 0.1300 | 13 | 1.6500 |
| review | 0.1100 | 11 | 1.6500 |

## by_period

| period | ge3_rate | n |
|--------|----------|---|
| early | 0.0400 | 25 |
| mid | 0.0400 | 25 |
| late | 0.0800 | 50 |

## UI / DB 상태

- DB reset: **True** (lotto_draws 보존)
- walk-forward 예측 **유지** (cleanup 없음)
- 총 prediction 행: **505**
- UI 다음 회차: **1235** (5장)

## NEXT

- **K-BRAIN-SIGNAL-TUNE** — _MIN_MAX_SIM·k 조정 · **형 GO 대기**
