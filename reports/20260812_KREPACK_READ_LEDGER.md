# K-REPACK-READ-LEDGER — LIST_V3 L4

시각: 2026-08-12 09:35:15 KST · **WIRE_OK** · wire=**True** · **1237아님** · ge3미클레임
선행: L3 WIRE_OK · 형 L4 GO
다음: **L4b** 역할슬롯 WIRE (게이트 후) · S1 IMMEDIATE는 L4 후 개별승인

---

## 실측

| 항목 | 값 |
|------|-----|
| frame | 1236 |
| seed_draws | [1234, 1235] |
| consumed | True |
| ema_solo_exit | True |
| no_peek | True |
| consume_n_draws | 2 · range=[1234, 1235] |
| blend | 0.5 |
| 1236 ledger/scatter | 45/6 |
| repack sets | 15 |

## consume 로그

```json
{
  "ledger_wire": true,
  "consumed": true,
  "ema_solo_exit": true,
  "target": 1236,
  "blend": 0.5,
  "n_draws": 2,
  "draw_range": [
    1234,
    1235
  ],
  "no_peek_ok": true,
  "skipped": null,
  "n_sets_with_hits": 40,
  "n_scatter_rows": 6,
  "source": "testlotto_pool_hit_ledger+scatter"
}
```

벤치: `docs/benchmarks/20260812_KREPACK_READ_LEDGER.json`

## 비범위

- 역할슬롯(L4b) · S1 BEGIN IMMEDIATE · 강제BT · prefer/prize 게이트
