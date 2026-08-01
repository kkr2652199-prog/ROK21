# K-BRAIN-SIGNAL-B1-BACKTEST-100 — B1 virtual draws n=100

📅 2026-08-01 · **FAIL** · draw 1135~1234

근거: `20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.json`

## SUMMARY

| 지표 | 값 |
|------|-----|
| overall ge3_rate | **0.0600** (6/100) |
| mean_match | **1.6300** |
| virtual_active_rate | **100.00%** (100/100) |
| vs direction1/highway 0.0600 | **+0.0000** |
| vs baseline 0.1015 | **-0.0415** |
| verdict | **FAIL** |

## PASS/FAIL (지시서)

- PASS: ge3 **>** 0.0600
- FAIL: ge3 ≤ 0.0600 (현재 **0.0600**)

## by_brain (solo · draws_with_signal + aux on real draws)

| brain | ge3_rate | ge3_count | mean_match |
|-------|----------|-----------|------------|
| stat | 0.0900 | 9 | 1.7100 |
| markov | 0.1300 | 13 | 1.6500 |
| review | 0.1100 | 11 | 1.6500 |

## by_period (draw-range SSOT · n=25 each)

| period | draw_range | ge3_rate | n |
|--------|------------|----------|---|
| early | 1135-1159 | 0.0400 | 25 |
| mid | 1160-1184 | 0.0400 | 25 |
| late | 1185-1234 | 0.0800 | 50 |

## UI / DB

- prediction rows: **505** · UI draw **1235** (5장)

## NEXT

- K-BRAIN-SIGNAL-TUNE (_MIN_MAX_SIM) or B1 rollback — **형 GO 대기**
