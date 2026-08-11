# K-REPACK-UNION — P1/P2 패치 APPLY

시각: 2026-08-11 · 형 「패치 진행」 · 양산前 · **1237아님** · ge3 클레임 금지

## 무엇을 했나

- **P1+P2 결합:** `ASSEMBLE_MODE=signal_union`
  - 신호상위 pool `slots=2` 유지
  - primary에 pool을 **cap=4**까지 추가(세트 번호점수 합 상위)
  - 나머지 1장은 classic score_repack
- 구 `signal_top`은 primary=2+classic3으로 5장 고정 → 나머지 pool 사실상 탈락

## 게이트 (repack 세트 축 · seed 0/42/123 · 1137~1236)

| mode | prefer | prize | stat_hit | pool>repack(mean) |
|------|--------|-------|----------|-------------------|
| signal_top | 0.172099 | −0.038768 | 0.265 | s40/m41/r37 |
| **signal_union** | **0.210554** | **−0.072138** | 0.255 | **s39/m36/r33** |

- 판정 **APPLY** (prefer↑ · prize더음수 · stat slack내 · 손실모니터↓)
- 근거: `docs/benchmarks/20260811_KREPACK_UNION_GATE.json`

## 강제 BT v3 (캐시 재적재)

- pool300 / bt100 · mean_hits **2.58**(모니터) · 4등**6** · 5등**47**
- 손실 재측정: pool>repack **37/37/34**(이전이전 v2 캐시 45/41/39)
- 근거: `20260811_KFORCE_POOL_BACKTEST_100_v3.json` · `20260811_KREPACK_LOSS_AUDIT_POST_UNION.json`

## 코드

- `app/testlotto/signal_pool.py` — `assemble_signal_union` · `POOL_UNION_CAP_BY_BRAIN`
- 도구: `tools/_k_repack_union_gate.py`
