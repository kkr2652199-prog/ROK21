# K-FUSION-BOTTLE-DIAG — fusion bottleneck diagnostic

📅 2026-08-01 · draw 1135~1234 · n=100

근거: `20260801_KFUSION_BOTTLE_DIAG.json`

## SUMMARY

| 지표 | 값 |
|------|-----|
| diag overall ge3_rate | **0.0900** (9/100) |
| mean_match | **1.7100** |
| vs fused ref 0.0600 | **+0.0300** |
| vs solo markov ref 0.1300 | **-0.0400** |
| markov quota actual rate (prod dynamic avg) | **0.4000** |
| aux survival rate (markov in global top5 avg) | **0.6680** |
| fixed diag markov allocation | **1.0000** (5/5) |

## PASS/FAIL interpretation

- **AUX_PATH_BOTTLENECK** — primary bottleneck: **aux_or_coordinator_path**
- diag ge3=0.0900 closer to fused ref 0.06 — aux/coordinator path degrades markov
- aux: MIXED aux survival — partial aux ranking loss
- quota: LOW production markov allocation (~0.40/5) — quota dilution significant

## References

| path | ge3_rate |
|------|----------|
| fused coordinator (B1 backtest) | 0.0600 |
| solo markov (K-HIGHWAY ref) | 0.1300 |
| **this diag (markov 100% fixed quota)** | **0.0900** |

## Mode

- `BENCH_FIXED_QUOTA` markov=5 stat=0 review=0 — diagnostic only, production logic preserved
- markov window100 **rolled back** — full draws in build_transition_matrix

