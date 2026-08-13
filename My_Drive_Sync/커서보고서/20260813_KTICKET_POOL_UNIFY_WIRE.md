# K-TICKET-POOL-UNIFY-WIRE — LIST_V3 L12b 옵션 E

시각: 2026-08-13T10:22:36+09:00 · **WIRE_OK** · wire=**True** · apply=**True** · 옵션=**E**
샘플: 1236 · seed=42 · **1237아님** · ge3미클레임 · 강제병합 안 함

## 이번 턴 작업

형 권고 **E**: 클릭 시 pool을 **한 번** 생성하고, skill1~5만 quota **5장** 발권하며,
같은 회차 `testlotto_pool_view_cache`에 10+5를 같이 기록한다.
pool10/repack15를 발권 테이블에 넣지 않는다. BT/`run_prediction`은 기존 경로.

## HARD

- `ticket_pool_sync_on`: **True**
- `api_predict_wired`: **True**
- `engine_bt_unwired`: **True**
- `prebuilt_param`: **True**
- `skill_is_15`: **True**
- `c8_all`: **True**
- `pass0_eq_coord_seed`: **True**
- `live_no_error`: **True**
- `pool_sync_ok`: **True**
- `wrote_cache`: **True**
- `live_skill_is_15`: **True**
- `issued_is_5`: **True**
- `issued_ne_pool10`: **True**
- `issued_ne_repack15`: **True**
- `issued_ne_all45`: **True**
- `cache_rows_3`: **True**
- `pool10`: **True**
- `repack5`: **True**
- `min_each_brain`: **True**
- `restored`: **True**

- issued: n=5 by_tag={'markov': 1, 'review': 3, 'stat': 1}
- pool sizes: {'markov': 10, 'stat': 10, 'review': 10} · repack: {'markov': 5, 'stat': 5, 'review': 5}
- C8: {'markov': True, 'stat': True, 'review': True}
- pool_sync: {'ok': True, 'option': 'E_same_gen_dual_write', 'wrote_cache': True, 'skill_n': 15, 'issued_is_quota': True}

## 배선

| 항목 | 값 |
|------|-----|
| 플래그 | `TICKET_POOL_SYNC=True` (`ticket_pool_sync.py`) |
| 클릭 | `POST /predict/{N}` → `run_live_issue_with_pool_sync` |
| 생성 | `build_pool_and_repack(..., return_raw=True)` 1회 |
| 발권 | skill1~5 → `prebuilt_candidates` → quota5 → `lotto_predictions` |
| 캐시 | 같은 회차 `save_pool_view_cache` |
| BT | `engine.run_prediction` → coordinator (동기 없음) |
| 롤백 | `TICKET_POOL_SYNC=False` (옵션 A 분리) |

벤치: `docs/benchmarks/20260813_KTICKET_POOL_UNIFY_WIRE.json`
도구: `tools/_k_ticket_pool_unify_wire.py`

다음: LIST_V3 L0~L12b 완료 · 형 다음 1건
