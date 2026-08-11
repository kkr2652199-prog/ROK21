# K-I-BRAIN-FALLBACK-WIRE

시각: 2026-08-12T07:22:29+09:00 · target=1236

## 판정 **WIRE_OK**

### expand_pool
`{'tags': {'markov': 0, 'stat': 10, 'review': 10}, 'markov_zero': True, 'others_ok': True, 'no_raise': True}`

### coordinator
`{'error': None, 'brain_errors': {'markov': 'RuntimeError: K-I mock brain failure'}, 'markov_in_errors': True, 'survived': True, 'n_pred_hint': 5, 'status': '예측 완료 (일부뇌 스킵: markov)'}`

## 패치
- `coordinator.run_coordinated_prediction` 뇌별 try/except · `brain_errors`
- `signal_pool.expand_pool` 뇌별 try/except
