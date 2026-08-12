# K-POOL-HIT-LEDGER-WIRE — LIST_V3 L3

시각: 2026-08-12 09:01:15 KST · **WIRE_OK** · wire=**True** · **1237아님** · ge3미클레임
선행: L2 SPEC DOC_OK · L2b 역할SPEC DOC_OK
다음: **L4** 몰아주기 원장 SSOT 읽기 (역할코드는 L4b)

---

## 실측

| 항목 | 값 |
|------|-----|
| sample_draw | 1236 |
| actual | [12, 18, 21, 29, 34, 38] · bonus=10 |
| n_ledger | 45 (기대 45) |
| n_scatter | 6 (기대 6) |
| structure_ok | True |
| no_peek | True |
| predict_reset | True |
| role_wire | False (L4b) |

## by_kind

```json
[
  {
    "kind": "pool",
    "n": 30,
    "max_hits": 2,
    "sum_hits": 18
  },
  {
    "kind": "repack",
    "n": 15,
    "max_hits": 2,
    "sum_hits": 13
  }
]
```

## no_peek

```json
{
  "read_lt_1237": {
    "ok": true,
    "target": 1237,
    "n_rows": 45,
    "bad_draws": []
  },
  "read_lt_1236": {
    "ok": true,
    "target": 1236,
    "n_rows": 0,
    "bad_draws": []
  },
  "target_1236_excludes_1236": true,
  "ok": true
}
```

벤치: `docs/benchmarks/20260812_KPOOL_HIT_LEDGER_WIRE.json`

## 비범위

- focus_r1 소비(L4) · 역할슬롯 생성(L4b) · 강제BT
