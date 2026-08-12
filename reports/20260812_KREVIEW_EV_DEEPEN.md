# K-REVIEW-EV-DEEPEN — LIST_V3 L11

시각: 2026-08-12T11:03:05+09:00 · **HOLD** · apply=**False** · **1237아님** · ge3미클레임 · Stern-Cover금지
노브: `PRIZE_SHAPE_STRENGTH` (annotate_prize 고번호·합 보너스) · LOCKED BLEND=0.85/W_CROWD=0.9 **재탕안함**
구간: 1137~1236 seeds=[0, 42, 123]

## base shape=1.0

| prefer | prize |
|--------|-------|
| 0.089332 | 0.006498 |

## cands

- `shape_0.0`: prefer=0.089332 prize=0.007816 · d_prize=0.001318 d_prefer=0.0 · pass=**False**
- `shape_0.5`: prefer=0.089332 prize=0.006602 · d_prize=0.000104 d_prefer=0.0 · pass=**False**
- `shape_1.5`: prefer=0.089332 prize=0.005946 · d_prize=-0.000552 d_prefer=0.0 · pass=**False**
- `shape_2.0`: prefer=0.089332 prize=0.00445 · d_prize=-0.002048 d_prefer=0.0 · pass=**False**

## 게이트 실패 요지

- base pool-prize가 **양수**(0.0065) → health(`prize<0`) 전원 탈락.
- 최선 `shape_2.0` d_prize=**−0.002** ≪ 문턱 0.005 (노이즈 수준).
- prefer iso **완벽**(d=0) — shape는 review pick만 건드림.

판정: **HOLD** — `PRIZE_SHAPE_STRENGTH=1.0` 유지 · BLEND0.85/W_CROWD0.90 **재탕안함** · 다음 L11b markov

벤치: `docs/benchmarks/20260812_KREVIEW_EV_DEEPEN.json`
도구: `tools/_k_review_ev_deepen.py`

다음: **L11b** K-MARKOV-PREFER-ALIGN
