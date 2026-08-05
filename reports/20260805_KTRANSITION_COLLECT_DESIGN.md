# K-TRANSITION-COLLECT-DESIGN — transition_log 수집 구조 (2026-08-05)

> **작성:** Cursor · wire=`False` · coordinator/발권 **미접촉**

- **판정:** `PASS` · table=`transition_log`
- backfill range: `[101, 1234]` · inserted=1134 · skipped=0

## collect 검증 (hit vs N+1)
- total_rows=1134 · mean_hit=1.998236 · delta=-0.001764 · hit_ge3=352
- match_prior_json(collect≈FULL): **False** (지표 상이 시 False 정상)

## FULL 동치 재현 (hit vs N)
- mean_hit=2.171806 · delta=0.171806 · match_prior=**True** · n=1135

- hook_registered: **True**
- next_step: STEP2 — 수집 데이터 재검증 (데이터 쌓인 후)
- tool: `tools/_k_transition_collect.py`
