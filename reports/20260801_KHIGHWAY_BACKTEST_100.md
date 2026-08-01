# K-HIGHWAY-BACKTEST-100 — PHASE1 highway stack n=100

📅 2026-08-01 · **FAIL** · draw 1135~1234

근거: `20260801_KHIGHWAY_BACKTEST_100.json`

## SUMMARY

| 지표 | 값 |
|------|-----|
| overall ge3_rate | **0.0600** (6/100) |
| mean_match | **1.6300** |
| p vs null (0.1137) | 0.976 |
| vs baseline 0.1015 | **-0.0415** |
| verdict | **FAIL** |

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

## dynamic quota avg %

- stat: **40.0%**
- markov: **40.0%**
- review: **20.0%**

## learn_state trace (milestones)

### draw 1135
- **stat** rc=0 avg=0.0000 adj={}
- **markov** rc=0 avg=0.0000 adj={}
- **review** rc=0 avg=0.0000 adj={}
### draw 1159
- **stat** rc=24 avg=1.3333 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}
- **markov** rc=24 avg=1.2500 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}
- **review** rc=24 avg=0.7917 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}
### draw 1184
- **stat** rc=49 avg=1.1000 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}
- **markov** rc=49 avg=1.3333 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3, 'overdue_boost': 0.05}
- **review** rc=49 avg=0.7667 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}
### draw 1234
- **stat** rc=99 avg=1.2000 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3, 'overdue_boost': 0.1}
- **markov** rc=99 avg=1.2000 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3, 'overdue_boost': 0.15000000000000002}
- **review** rc=99 avg=0.8333 adj={'carry_over_boost': 0.2, 'ending_digit_boost': 0.3}

## collapse check

- early→late Δge3 = **+0.0400** (stable)
