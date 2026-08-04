# K-REPACK-HYBRID-WIRE — stat/review hy_p45_r123 배선

`2026-08-04T03:13:54+00:00` · migrated=200 · schema=2

## 0. 한 줄

stat/review **pool4+5+몰1~3** wire · markov baseline 유지 · 검증 PASS=**True**

## 1. ge3 vs ablation 참조

| 뇌 | wire ge3 | ablation ref | Δ | vs null |
|----|---------:|-------------:|---|--------:|
| stat | **0.1650** | 0.1650 | +0.0000 | +0.0513 |
| markov | **0.1300** | 0.1300 | +0.0000 | +0.0163 |
| review | **0.1350** | 0.1350 | +0.0000 | +0.0213 |

## 2. smoke build_pool_and_repack(1230)

- ok: True
- assemble: {'stat': 'hy_p45_r123', 'markov': 'baseline_repack', 'review': 'hy_p45_r123'}
- hybrid meta: {'mode': 'p45_r123', 'brains': ['review', 'stat'], 'markov': 'baseline_repack'}

## 3. 변경 파일

- `app/testlotto/signal_pool.py` — assemble_hybrid_p45_r123 · HYBRID_P45_R123_BRAINS
- `app/testlotto/pool_view_cache.py` — CACHE_SCHEMA_VERSION=2 · schema 필터

## 금지 준수

coordinator/quota 미수정 · random.choices/_get_draws_before/boost상한 미손 · engine 미수정
