# K-TRANSITION-FULL — 전회차 유사전이·이월 rolling (2026-08-05)

- **판정:** `STRONG` · wire=`False`
- range `[101, 1235]` · baseline_hit=2.0
- brain_replace: **즉시착수** (target=`stat`)

## by_sim_k
- **sim_k2**: n_valid=1135 · mean_hit=2.171806 · delta=0.171806 · **STRONG** · hit_dist={'0': 62, '1': 246, '2': 397, '3': 310, '4': 106, '5': 13, '6': 1}
- **sim_k3**: n_valid=811 · mean_hit=2.065351 · delta=0.065351 · **MARGINAL** · hit_dist={'0': 44, '1': 217, '2': 286, '3': 181, '4': 72, '5': 11, '6': 0}
- **sim_k4**: n_valid=0 · mean_hit=0.0 · delta=-2.0 · **NOISE** · hit_dist={'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0}

## carry_analysis
- full_dist: `{'0': 477, '1': 523, '2': 208, '3': 24, '4': 2, '5': 0, '6': 0}` · mean_carry=0.82577
- 1235 carry=2 nums=`[15, 43]`
- pred_1236_carry_dist: `{'0': 0.338164, '1': 0.487923, '2': 0.15942, '3': 0.014493}` (n=207)

- signal_summary: sim_k2 Δ=0.171806 STRONG · k3 Δ=0.065351 k4 Δ=-2.0
- tool: `tools/_k_transition_full.py`
