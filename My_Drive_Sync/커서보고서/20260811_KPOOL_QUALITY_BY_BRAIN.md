# K-POOL-QUALITY-BY-BRAIN

시각: 2026-08-11 · 양산前 · **1237아님** · ge3미클레임

## 요지
뇌별 pool 품질 튜닝 2노브 스윕(1137~1236 · seeds `[0,42,123]`).

| 노브 | 판정 | chosen |
|------|------|--------|
| `JACCARD_PENALTY_BY_BRAIN` | **NO_IMPROVE_HOLD** | 전뇌 **0.85** |
| `OVERSAMPLE_MULT_BY_BRAIN` | **APPLY** | markov **5** · stat/review **3** |

## 배선
- `shared/diversity.py`: `JACCARD_PENALTY_BY_BRAIN` · `OVERSAMPLE_MULT_BY_BRAIN`
- 3뇌 `predict.py`: `diversity.factor(..., brain=)` · `diversity.pick(..., brain=, conf_key=pick_score)`
- 동결(`random.choices` / `_get_draws_before` / boost상한) 무접촉

## Jaccard (HOLD)
- markov j=0.55 prefer +0.0011 ≪ thr0.005
- review |Δprize|≪0.005 · pool prize base≥0(절대음수 게이트 비적용 여지)
- stat dhit≈+0.002 ≪0.005
- 근거: `docs/benchmarks/20260811_KPOOL_JACCARD_BY_BRAIN_TUNE.json`

## Oversample (APPLY)
- markov m=5 prefer **0.083519→0.091380** (Δ**+0.007861**≥0.005 · prize iso0 · split+)
- m=4/6도 PASS, 최선 m=5
- review m=5 prize↓이나 |Δ|≪0.005 → HOLD
- stat dhit≪0.005 → HOLD
- 근거: `docs/benchmarks/20260811_KPOOL_OVERSAMPLE_BY_BRAIN_TUNE.json`

## 도구
- `tools/_k_pool_jaccard_by_brain_tune.py`
- `tools/_k_pool_oversample_by_brain_tune.py`
