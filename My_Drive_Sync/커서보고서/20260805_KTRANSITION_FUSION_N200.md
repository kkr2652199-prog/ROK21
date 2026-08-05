# K-TRANSITION-FUSION-N200 — fusion n200 (2026-08-05)

## 판정
**ROLLBACK** (검증 후 `TRANSITION_V1_WIRE=False` 적용)

| 조건 | 결과 |
|------|------|
| ge3_rate >= 0.135 AND mean_hit >= 2.0 → KEEP | ge3=**0.135** · mean=**1.715** → 미충족 |
| ge3 0.100~0.135 → MARGINAL | ge3는 경계이나 mean&lt;1.8 |
| ge3 &lt; 0.100 OR mean &lt; 1.8 → ROLLBACK | mean=**1.715** &lt; 1.8 → **ROLLBACK** |

## 환경
- `TRANSITION_V1_WIRE=True` (검증 중 유지) · `_use_transition_v1()=True`
- `transition_log` rows=**1134**
- 3뇌: markov + review + transition_v1(stat 슬롯)
- env_ok=**true**
- 경로: in-memory coordinator fuse · `lotto_predictions` 미기록

## fusion n200 (핵심)
- range **1035~1234** · n=**200** · seed=42
- mean_hit=**1.715**
- ge3_rate=**0.135** (ge3_count=**27**) · Δ vs baseline=**0.0**
- hit_dist: 0=3 · 1=82 · 2=88 · 3=23 · 4=4 · 5=0 · 6=0
- 비교: baseline_ge3=0.135 · random_top15=0.311(참고) · step3_nopeek=0.274(참고)

## 구간별
| 구간 | range | ge3_rate |
|------|-------|----------|
| early | 1035~1101 | 0.149254 |
| mid | 1102~1167 | 0.121212 |
| late | 1168~1234 | 0.134328 |

- max_gap=**0.028042** (&lt;0.05) → **STABLE**

## 롤백
- cmd: `K_STAT_TRANSITION_V1=0` 또는 `TRANSITION_V1_WIRE=False`
- applied: **True** (`transition_v1.py` 기본 OFF)

## 산출물
- `docs/benchmarks/20260805_KTRANSITION_FUSION_N200.json`
- tool: `tools/_k_transition_fusion_n200.py`
- prior: `docs/benchmarks/20260805_KTRANSITION_STEP4_WIRE.json`
