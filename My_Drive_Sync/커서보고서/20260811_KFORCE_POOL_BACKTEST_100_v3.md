# K-FORCE-POOL-BACKTEST-100

📅 2026-08-11 KST · **강제 리셋 + 최신 3뇌 WF 재적재**

## 사전 실측 (문제)
- 페이지에 100회 백테가 안 보임 → DB `backtest_draw_results=0` · `lotto_predictions=0`
- pool 캐시는 일부 회차(1225~1236)만 잔존 · **100회 아님**

## 실행
1. `_k_predict_reset` APPLY — 예측·pool캐시·백테·evolve 삭제 (draws 보존)
2. 1137~1236 n100 · `_get_draws_before` · `expand_pool`+`build_hint_by_brain`+`repack_by_brain`
3. 매회 `save_pool_view_cache` (schema4 · tune_snapshot 포함)
4. `backtest_runs` / `draw_results` 적재

## 결과
- run_id=11 · n=100 · range=[1137, 1236]
- pool_draws=100 · bt_rows=100
- mean_hits=2.58 · ge3_rate=0.53 (**모니터만 · 클레임금지**)
- elapsed=40.1s
- knobs={'markov': 0.55, 'review': 0.85} / HINT={'stat': [52, 'miss_pattern'], 'markov': [None, 'crowd_prefer'], 'review': [None, 'crowd_prize']}
- peek_checks=[{'draw': 1137, 'max_material': 1136, 'n_draws': 1136}, {'draw': 1138, 'max_material': 1137, 'n_draws': 1137}, {'draw': 1139, 'max_material': 1138, 'n_draws': 1138}, {'draw': 1236, 'max_material': 1235, 'n_draws': 1235}]

## 답 (형 질문)
| 질문 | 답 |
|------|-----|
| 100회 백테 기록이었나? | **의도 100회(1137~1236)** 였으나 UI용 backtest/pool 테이블엔 **미기록**(실측0). 복습 DB `brain_review`만 잔존 가능. |
| 리셋 없이 재백테? | 캐시 hit면 **구 예측 재사용** 가능 → **강제 리셋 필수** |
| 강제 백테 후? | **최신 knobs로 재예측** · 구값 재입력 아님 |
| 컨닝? | `_get_draws_before` · max_material < target 가드 |
