# K-FORCE-POOL-BACKTEST-100 v4

📅 2026-08-12 KST · **단계⑫** · 강제 리셋 + live knobs WF 재적재  
(min_each=1 · oversample m5 · cand_B · union · ⑪발권 VERIFY_OK 후)

## 실행
1. `_k_predict_reset` APPLY — 예측·pool캐시·백테·evolve 삭제 (draws 보존)
2. 1137~1236 n100 · `_get_draws_before` · `expand_pool`+`build_hint_by_brain`+`repack_by_brain`
3. 매회 `save_pool_view_cache` (schema4 · tune_snapshot 포함)
4. `backtest_runs` / `draw_results` 적재

## 결과
- run_id=13 · n=100 · range=[1137, 1236]
- pool_draws=100 · bt_rows=100
- mean_hits=2.5 · ge3_rate=0.46 (**모니터만 · 클레임금지**)
- tiers={'r1': 0, 'r2': 0, 'r3': 0, 'r4': 4, 'r5': 42}
- elapsed=53.5s
- knobs={'BLEND_STRENGTH_BY_BRAIN': {'markov': 0.55, 'review': 0.85}, 'W_CROWD_BY_BRAIN': {'markov': 0.9, 'review': 0.9}, 'W_STRUCT_BY_BRAIN': {'markov': 0.1, 'review': 0.1}, 'HINT_SPEC_BY_BRAIN': {'stat': [52, 'miss_pattern'], 'markov': [None, 'crowd_prefer'], 'review': [None, 'crowd_prize']}, 'SCORE_WEIGHTS_BY_BRAIN': {'stat': [0.25, 0.35, 0.4], 'markov': [0.65, 0.15, 0.2], 'review': [0.65, 0.15, 0.2]}, 'ASSEMBLE_MODE': 'signal_union', 'POOL_SLOTS_BY_BRAIN': {'markov': 2, 'stat': 2, 'review': 2}, 'POOL_UNION_CAP_BY_BRAIN': {'markov': 4, 'stat': 4, 'review': 4}, 'HINT_WEIGHT_BY_BRAIN': {'stat': 0.15, 'markov': 0.15, 'review': 0.15}, 'REFEREE_BY_BRAIN': {'stat': {'role_ko': '과거학습감독', 'gain': 2.5, 'baseline': 0.8, 'floor': 0.15, 'set_scale': 0.75}, 'markov': {'role_ko': '선호번호감독', 'gain': 2.5, 'baseline': 0.8, 'floor': 0.15, 'set_scale': 0.75}, 'review': {'role_ko': '금액뇌감독', 'gain': 2.5, 'baseline': 0.8, 'floor': 0.15, 'set_scale': 0.75}}, 'hint_shared_across_brains': False, 'independence_ko': '공유=lotto_draws만 · 예측·감독관 뇌별 분리'}
- peek_checks=[{'draw': 1137, 'max_material': 1136, 'n_draws': 1136}, {'draw': 1138, 'max_material': 1137, 'n_draws': 1137}, {'draw': 1139, 'max_material': 1138, 'n_draws': 1138}, {'draw': 1236, 'max_material': 1235, 'n_draws': 1235}]

## 판정
- **verdict** = **REBUILT_OK** · ge3미클레임 · 1237아님
