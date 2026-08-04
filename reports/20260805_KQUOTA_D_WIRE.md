# K-QUOTA-D-WIRE — quota stat30/markov60/review10 실적용 (2026-08-05)

- **판정:** `FAIL` · wire=`False` · pass=`False`
- **변경 1곳:** `app/testlotto/brains/coordinator.py` · `BENCH_FIXED_QUOTA`
- before slots `{'stat': 0, 'markov': 4, 'review': 1}` → after `{'stat': 2, 'markov': 3, 'review': 0}`

## N100 멀티시드 (1136~1235)

| seed | ge3 | mean |
|------|-----|------|
| 42 | 0.09 | 1.59 |
| 0 | 0.11 | 1.72 |
| 7 | 0.1 | 1.62 |
| **avg** | **0.1** | — |
| verdict | **FAIL** | ≥0.135 PASS · ≥0.155 STRONG |

## FULL n200 (1036~1235 · seed42)

- ge3=**0.115** · vs_null=0.0013 · vs_pin=-0.0297
- verdict=**FAIL** (PASS if ge3≥0.150)

## 슬롯

- slot_log_ok=**True**
- `{"totals": {"markov": 600, "stat": 400}, "avg_slots_per_draw": {"stat": 2.0, "markov": 3.0, "review": 0.0}, "n_draws_with_preds": 200, "n_mismatch_draws": 0, "mismatch_sample": [], "stat_slots_ok": true}`

- rollback_target pin=`640cb67` · rolled_back=`True`
- BENCH_FIXED_QUOTA=None (quota-only · not git 640cb67)

## 원인 (중요)

PREP의 D ge3=**0.170**은 `pool_view_cache` **hybrid repack** 슬롯 재조합 결과.  
이번 wire는 `coordinator.predict_sets` → 고정쿼터 경로라 **티켓 소스가 다름**.  
슬롯(2/3/0)은 정상 발권됐으나 live ge3가 붕괴 → **하드롤백** (`BENCH_FIXED_QUOTA=None`).

교훈: quota 후보는 **live coordinator 경로**로 재측정한 뒤에만 wire GO.

## 산출물

- JSON: `docs/benchmarks/20260805_KQUOTA_D_WIRE.json`
- tool: `tools/_k_quota_d_wire_verify.py`
