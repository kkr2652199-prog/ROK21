# K-BRAIN3-PRECISION-AUDIT — 3뇌 정밀·버그사냥

시각: 2026-08-11T15:50:07+09:00 · 회차 [1216, 1236] n=21 · seed=42

## 판정 **AUDIT_OK** · bugs=0
- ge3클레임금지 · 1237아님 · READ-ONLY

## 0. 현행 패치 (간략)
- 뇌독립: HINT/SCORE/W/BLEND BY_BRAIN · 공유=lotto_draws만
- 몰아주기: signal_union(slots2+cap4) · 뇌별 learner
- aux: pick_score→diversity.pick · HINT_WEIGHT 0.15 HOLD
- K-J: referee SSOT=live · DB미러
- tune_json 캐시 보존

## 1. live knobs
```json
{
  "ASSEMBLE_MODE": "signal_union",
  "POOL_UNION_CAP": {
    "markov": 4,
    "stat": 4,
    "review": 4
  },
  "POOL_SLOTS": {
    "markov": 2,
    "stat": 2,
    "review": 2
  },
  "SCORE": {
    "stat": [
      0.25,
      0.35,
      0.4
    ],
    "markov": [
      0.65,
      0.15,
      0.2
    ],
    "review": [
      0.65,
      0.15,
      0.2
    ]
  },
  "HINT_SPEC": {
    "stat": [
      52,
      "miss_pattern"
    ],
    "markov": [
      null,
      "crowd_prefer"
    ],
    "review": [
      null,
      "crowd_prize"
    ]
  },
  "hint_shared": false,
  "W_CROWD": {
    "markov": 0.9,
    "review": 0.9
  },
  "BLEND": {
    "markov": 0.55,
    "review": 0.85
  },
  "HINT_WEIGHT_BY_BRAIN": {
    "stat": 0.15,
    "markov": 0.15,
    "review": 0.15
  },
  "HINT_WEIGHT_modules": {
    "stat": 0.15,
    "markov": 0.15,
    "review": 0.15
  },
  "FEATURE_LAMBDA_WIRE": false
}
```

## 2. 검사
- `A_완전성_pool10_repack5`: PASS
  - {'fail_sample': [], 'n_fail': 0}
- `B_교차동일세트0`: PASS
  - {'cross_pool': 0, 'cross_repack': 0}
- `B_hint테이블분리`: PASS
  - {'distinct_rate': 1.0, 'hint_shared_flag': False}
- `C_RNG단독=합동`: PASS
  - {'by_brain': {'stat': True, 'markov': True, 'review': True}}
- `C_배선생존_SCORE`: PASS
  - {'detail': {'live': True, 'restored': True}}
- `C_배선생존_HINT_WEIGHT`: PASS
  - {'detail': {'live': True, 'restored': True}, 'note': 'pick_score 경로'}
- `C_배선생존_W_CROWD`: PASS
  - {'detail': {'live': True, 'restored': True}}
- `C_배선생존_UNION_CAP`: PASS
  - {'detail': {'live': True, 'restored': True}}
- `D_assemble_signal_union`: PASS
  - {'mode': 'signal_union'}
- `D_peek_ok`: PASS
  - {}
- `E_정보_pool적중번호포착`: PASS (정보)
  - {'is_informational': True, 'mean_pool_hit_nums': {'stat': 4.429, 'markov': 3.476, 'review': 3.667}, 'mean_repack_hit_nums': {'stat': 2.476, 'markov': 2.619, 'review': 2.238}, 'mean_preserve_pool_to_repack': {'stat': 0.5579, 'markov': 0.7458, 'review': 0.5992}, 'note': '클레임아님 · 몰아주기 전 pool에 적중번호가 얼마나 있는지만 모니터'}
- `E_정보_pick_score_pool잔존`: PASS (정보)
  - {'is_informational': True, 'mean_fraction_in_pool_dicts': 1.0, 'note': 'expand 결과가 pick_score를 안 실을 수 있음(predict내부만 사용) — 0이어도 배선과 무관할 수 있음'}

## 3. 버그
```json
[]
```

## 4. 몰아주기 전제 (형 요지)
- 각 뇌 **10세트**에 적중번호가 먼저 들어와야, 뇌별 몰아주기(5장)가 극대화된다.
- 모니터(클레임아님) mean pool적중번호수={'stat': 4.429, 'markov': 3.476, 'review': 3.667}
- mean repack적중번호수={'stat': 2.476, 'markov': 2.619, 'review': 2.238}
- pool→repack 번호보존비율={'stat': 0.5579, 'markov': 0.7458, 'review': 0.5992}
- pool적중>repack적중 회차수={'stat': 19, 'markov': 13, 'review': 15}
