# K-TICKET-POOL-UNIFY-SPEC — LIST_V3 L12

시각: 2026-08-13T10:14:51+09:00 · **DOC_OK** · wire=**False** · apply=**False** · **강제병합 안 함**
샘플: 1236 · seed=42 · **1237아님** · ge3미클레임

## 이번 턴 작업

클릭 발권 **5장**과 UI/원장 **pool10+repack5**가 다른 파이프·다른 테이블에 쌓이는 상태를 실측하고,
통합 **옵션만** 고정한다. 코드로 두 경로를 합치지 않는다.

## 실측 HARD

- `has_predictions`: **True**
- `has_pool_cache`: **True**
- `pool10`: **True**
- `repack5`: **True**
- `c8_all`: **True**
- `issued_is_5`: **True**
- `pass0_eq_coord_seed`: **True**

- census predictions@1236: n=0 by_tag={}
- pool_view_cache rows: 3 · ledger: 45
- pool sizes: {'markov': 10, 'stat': 10, 'review': 10} · repack: {'markov': 5, 'stat': 5, 'review': 5}
- issued quota: n=5 by_tag={'stat': 1, 'markov': 1, 'review': 3}
- C8: {'markov': True, 'stat': True, 'review': True}
- pass0 seed 1278 == coord seed 1278

## 두 경로 (코드)

| | 발권(클릭) | pool/UI |
|--|-------------|---------|
| 진입 | `POST /predict/{N}` → `run_coordinated_prediction` | `GET /predict/pool-view/{N}` → `expand_pool`+`repack` |
| 생성 | 뇌별 `predict_sets(5)` → 15장 | 뇌별 skill5+cover3+shape2 = **10** |
| 선별 | dedup → **quota 5장** | 몰아주기 **repack 5×3=15** |
| 저장 | `lotto_predictions` | `testlotto_pool_view_cache` + ledger(결과후) |
| 채점 SSOT | 발권5 (METRIC_OK mean 1.64) | pool경로 (BT mean 2.5, 장수효과) |

이미 같은 것: **pool set1~5 = 발권 predict_sets(5)** (C8, 동일 시드 `42+N`).
다른 것: 클릭은 15장 중 **5장만** DB에 남김. 10+5는 별도 캐시.

## 옵션 (형 선택)

| ID | 내용 | 비고 |
|----|------|------|
| **A** | 현행 유지(분리) | 병합 없음 |
| **B** | pool10도 발권(30장) | 장수↑ · 발권 의미 변경 |
| **C** | repack5×3=15장을 발권 SSOT | 몰아주기=클릭 |
| **D** | 10+5 전부 발권(45장) | 형 문구 직역 · 비용↑ |
| **E** (권고) | 생성 1회 · quota5 발권 + 같은 회차 pool캐시 동기 기록 | 병합 아닌 **이중저장 동기화** |

권고 **E**: C8이 이미 skill1~5를 맞추고 있음. 남은 갭은 저장/채점 분리.
B/D는 발권 장수 제품결정이라 **형 GO 없이 WIRE 금지**.

벤치: `docs/benchmarks/20260813_KTICKET_POOL_UNIFY_SPEC.json`
도구: `tools/_k_ticket_pool_unify_spec.py`

다음: 형 A~E 선택 → **L12b WIRE**
