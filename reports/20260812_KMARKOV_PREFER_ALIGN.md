# K-MARKOV-PREFER-ALIGN — LIST_V3 L11b

시각: 2026-08-12T11:23:15+09:00 · **HOLD** · apply=**False** · **1237아님** · ge3미클레임
노브: `PREFER_BDAY_STRENGTH` (annotate_prefer 생일대1~31) · LOCKED BLEND=0.55/W_CROWD=0.9 **재탕안함**
구간: 1137~1236 seeds=[0, 42, 123]

## base bday=0.0

| prefer | prize |
|--------|-------|
| 0.089332 | 0.006498 |

## cands

- `bday_0.5`: prefer=0.089262 prize=0.006498 · d_prefer=-7e-05 d_prize=-0.0 · pass=**False**
- `bday_1.0`: prefer=0.087972 prize=0.006498 · d_prefer=-0.00136 d_prize=-0.0 · pass=**False**
- `bday_1.5`: prefer=0.087334 prize=0.006498 · d_prefer=-0.001998 d_prize=-0.0 · pass=**False**
- `bday_2.0`: prefer=0.086021 prize=0.006498 · d_prefer=-0.003311 d_prize=-0.0 · pass=**False**

## 게이트 실패 요지

- 전 후보 `d_prefer` **음수**(생일대 보너스↑ → pool prefer↓).
- prize iso **완벽**(d=0) — markov pick만 변경.
- 개선 문턱(+0.005) 미달 · **APPLY 금지**.

판정: **HOLD** — `PREFER_BDAY_STRENGTH=0.0` 유지 · BLEND0.55/W_CROWD0.90 **재탕안함** · 다음 L11c stat

벤치: `docs/benchmarks/20260812_KMARKOV_PREFER_ALIGN.json`
도구: `tools/_k_markov_prefer_align.py`

다음: **L11c** K-STAT-HOMEWORK-QUALITY
