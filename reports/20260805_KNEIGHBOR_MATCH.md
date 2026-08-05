# K-NEIGHBOR-MATCH — kNN 유사 회차 패턴 진단 (2026-08-05)

- **판정:** `NOISE` · wire=`False`
- anchor 1235: `[6, 7, 11, 15, 39, 43]`

## knn_scores @1235

### k5 · top1_score=3
- top15: `[44, 7, 13, 16, 18, 24, 1, 3, 4, 5, 6, 11, 12, 14, 19]`

### k10 · top1_score=5
- top15: `[24, 7, 44, 13, 14, 18, 27, 40, 5, 8, 11, 16, 26, 29, 34]`

### k20 · top1_score=7
- top15: `[13, 44, 5, 7, 24, 40, 43, 8, 14, 18, 26, 28, 34, 38, 1]`

## backtest_100

```json
{
  "draw_range": [
    1136,
    1235
  ],
  "k": 10,
  "top_m": 15,
  "n": 100,
  "knn_ge3_rate": 0.23,
  "mean_hit_in_top15": 1.91,
  "baseline_ge3": 0.135,
  "delta": -0.081375,
  "delta_vs_fusion_ticket_ref": 0.095,
  "random_top15_ge3": 0.311375,
  "random_top15_mean_hit": 2.0,
  "delta_mean_hit_vs_random": -0.09,
  "verdict": "NOISE",
  "note": "ge3=|D_n∩score_top15|>=3 · 판정은 Hypergeometric 무작위 대비. baseline_ge3=0.135은 fusion 티켓 참고용(지표 다름·판정 미사용)"
}
```

## high_sum_analysis

```json
{
  "n_high_draws": 42,
  "avg_max_jaccard": 0.461451,
  "avg_max_jaccard_mid_ref": 0.47449,
  "n_mid_ref": 112,
  "max_jaccard_hist": {
    "0.5": 30,
    "0.71": 1,
    "0.33": 11
  },
  "sample": [
    {
      "draw_no": 1047,
      "sum": 181,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1050,
      "sum": 165,
      "max_jaccard": 0.714286
    },
    {
      "draw_no": 1051,
      "sum": 177,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1053,
      "sum": 186,
      "max_jaccard": 0.333333
    },
    {
      "draw_no": 1054,
      "sum": 163,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1056,
      "sum": 170,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1058,
      "sum": 161,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1061,
      "sum": 172,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1062,
      "sum": 209,
      "max_jaccard": 0.5
    },
    {
      "draw_no": 1075,
      "sum": 172,
      "max_jaccard": 0.333333
    }
  ],
  "root_cause": "pool실패",
  "note": "max_jaccard = 해당 HIGH 회차 vs 그 이전 전체 최대 Jaccard"
}
```

## lag_bonus

```json
{
  "carry_numbers": [
    15,
    43
  ],
  "consecutive_pairs": [
    [
      6,
      7
    ]
  ],
  "carry_reappear_rate": 0.138643,
  "consecutive_member_reappear_rate": 0.136029,
  "random_baseline": 0.133333,
  "n_carry_trials": 1017,
  "n_consec_trials": 1632,
  "viable": false,
  "note": "다음회 재출현율 vs 6/45 · 발권 ge3 클레임 금지"
}
```

- wire_implication: neighbor NOISE · cold-free wire GO 여부를 형 결정으로 분리 검토 · kNN 통합 보류
- tool: `tools/_k_neighbor_match.py`
