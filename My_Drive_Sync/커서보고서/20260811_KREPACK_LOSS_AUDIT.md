# K-REPACK-LOSS-AUDIT — pool>repack 손실 조사

시각: 2026-08-11T14:03:15+09:00 · 범위 [1137, 1236] · n=100

## 판정 **AUDIT_DONE_PROPOSE_HOLD**
- dominant_cause=`POOL_BEST_DROPPED_FROM_REPACK`
- code_changed=False · ge3클레임금지 · 1237아님

## 조립 설정
- `{'ASSEMBLE_MODE': 'signal_top', 'SIGNAL_TOP_BRAINS': ['markov', 'review', 'stat'], 'POOL_SLOTS_BY_BRAIN': {'markov': 2, 'stat': 2, 'review': 2}, 'REPACK_SETS_PER_BRAIN': 5}`

## 뇌별 요약
- **stat**: pool>repack=45 · repack>pool=8 · tie=47 · loss시 pool_best∉repack=45 / ∈repack=0
- **markov**: pool>repack=41 · repack>pool=6 · tie=53 · loss시 pool_best∉repack=41 / ∈repack=0
- **review**: pool>repack=39 · repack>pool=11 · tie=50 · loss시 pool_best∉repack=39 / ∈repack=0

## 티어 하락(손실회) `{'5->0': 41, '4->0': 3, '4->5': 1}`
- sum_hit_delta_on_loss=149

## 개선안 (미적용)
- **P1-PRESERVE-POOL-TOP-K** [PROPOSE] signal_top n_slots↑ 또는 pool 신호상위 K개를 repack 슬롯에 강제보존 · gate=prefer/prize 축 iso · seed≥3 · |Δ|≥0.01
- **P2-ORACLE-FREE-UNION** [PROPOSE] repack = signal_top(pool) ∪ classic_repack 상위 재순위(중복제거 후 5) · gate=동일 · 발권세트수 고정(5) 유지
- **P3-NO-CODE-HOLD** [HOLD_DEFAULT] 손실은 사후정보(당첨) 기준 — live 신호로는 완전제거 불가. 측정만 유지 · gate=형 승인 전

## 샘플(최대24)
```json
[
  {
    "draw": 1137,
    "brain": "stat",
    "pool_hits": 2,
    "repack_hits": 1,
    "delta": 1,
    "pool_set_no": 7,
    "pool_tier": 0,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1138,
    "brain": "stat",
    "pool_hits": 3,
    "repack_hits": 2,
    "delta": 1,
    "pool_set_no": 8,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1138,
    "brain": "markov",
    "pool_hits": 3,
    "repack_hits": 2,
    "delta": 1,
    "pool_set_no": 9,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1139,
    "brain": "stat",
    "pool_hits": 2,
    "repack_hits": 1,
    "delta": 1,
    "pool_set_no": 6,
    "pool_tier": 0,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1139,
    "brain": "review",
    "pool_hits": 3,
    "repack_hits": 2,
    "delta": 1,
    "pool_set_no": 3,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1140,
    "brain": "markov",
    "pool_hits": 3,
    "repack_hits": 1,
    "delta": 2,
    "pool_set_no": 6,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1140,
    "brain": "review",
    "pool_hits": 2,
    "repack_hits": 1,
    "delta": 1,
    "pool_set_no": 6,
    "pool_tier": 0,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1141,
    "brain": "stat",
    "pool_hits": 3,
    "repack_hits": 2,
    "delta": 1,
    "pool_set_no": 5,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1141,
    "brain": "review",
    "pool_hits": 2,
    "repack_hits": 1,
    "delta": 1,
    "pool_set_no": 1,
    "pool_tier": 0,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1144,
    "brain": "stat",
    "pool_hits": 2,
    "repack_hits": 1,
    "delta": 1,
    "pool_set_no": 9,
    "pool_tier": 0,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1144,
    "brain": "markov",
    "pool_hits": 4,
    "repack_hits": 2,
    "delta": 2,
    "pool_set_no": 2,
    "pool_tier": 4,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  },
  {
    "draw": 1144,
    "brain": "review",
    "pool_hits": 3,
    "repack_hits": 1,
    "delta": 2,
    "pool_set_no": 10,
    "pool_tier": 5,
    "repack_tier": 0,
    "pool_best_in_repack": false,
    "assemble": "signal_top"
  }
]
```
