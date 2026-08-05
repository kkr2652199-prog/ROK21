# K-TRANSITION-STEP3-DESIGN — transition→stat 대체 설계 (2026-08-05)

> **작성:** Cursor · wire=`False` · brains/engine **미수정** · 설계·시뮬만

- **판정:** `DESIGN_HOLD` · replace=`HOLD`

## [1] stat 현황 (READ-ONLY)
- file: `app/testlotto/brains/predict_stat_fairy.py`
- logic: 1) `_statistical_predict`로 oversample 후보 생성 (빈도 기반). 2) 이월·끝수·미출30+ reasoning + learn_state 부스트로 confidence 조정. 3) `diversify_pick`로 Jaccard 다양성 선별 후 n_sets 반환 (random.choices 동결).
- K-A mean_ref: **0.76** (FINDINGS K-A OPEN: set-level mean=0.760 (최근100·500세트). top15 pool mean(2.0)과 지표 다름 — 교체판정은 top15 hold-out 기준.)

## [2] design_spec
- name: `predict_transition_v1`
- params: `{'min_common': 2, 'min_similar': 10, 'top_m': 15, 'n_sets_default': 5, 'anchor': 'D_{T-1}', 'data_source': 'lotto_draws (+ optional transition_log cache)'}`
- interface_match: True

## [3] backtest (발권경로 = nopeek)
- range [1100, 1234] n=135 · mean_hit=**2.007407** · ge3_rate=**0.274074** (rand≈0.311375)
- hit_dist: {'0': 8, '1': 36, '2': 54, '3': 22, '4': 14, '5': 1, '6': 0}

## [3b] FULL-style hold-out (참고·peek)
- mean_hit=2.177778 · ge3_rate=0.392593 · Δvs prior=0.005972

## [4] replace / risk
- replace_verdict: **HOLD**
- (a) transition_log/hook 미작동 시 캐시 공백 — 런타임은 lotto_draws 재계산 fallback 필수
- (b) 초반·희소 구간 min_similar<10 → top15 불안정 · fallback(빈도/직전풀) 명세 필요
- (c) 롤백: predict_stat_fairy.py·stat_brain.predict 경로 유지·플래그로 전환 (STEP4에서 FEATURE 플래그·하드코딩 금지 검토)

- prior: `docs/benchmarks/20260805_KTRANSITION_STEP2_VERIFY.json`
- tool: `tools/_k_transition_step3_design.py`
