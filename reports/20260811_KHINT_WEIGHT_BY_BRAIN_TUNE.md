# K-HINT-WEIGHT-BY-BRAIN — 다음튜닝 (I-AUX-HINT-WEIGHT)

시각: 2026-08-11 · 형 「다음 진행」 · 양산前 · **1237아님** · ge3 클레임 금지

## 요약

1. **SSOT 추가:** `HINT_WEIGHT_BY_BRAIN` (`aux_hint.py`) · 3뇌 predict 연결
2. **v1 스윕:** 전후보 prefer/prize **완전동일** → 원인=`diversity.pick(confidence)`가 aux 재정렬 무시 (**DEAD_WIRE**)
3. **배선 패치:** `pick_score`(confidence×aux) · `diversity.pick(..., conf_key="pick_score")`
4. **v2 스윕:** 축이 w에 반응(배선생존) · 개선후보 **게이트 전원 FAIL** → **`0.15 HOLD`**

## v2 게이트 요지

| brain | base@0.15 | 최선후보 | 결과 |
|-------|-----------|----------|------|
| markov prefer | **0.294005** | 전부↓ | HOLD |
| review prize | **−0.111224** | 0.25:−0.111372 (Δ≪0.005) | HOLD |
| stat hit | **0.315555** | 전부↓ | HOLD |

근거: `docs/benchmarks/20260811_KHINT_WEIGHT_BY_BRAIN_TUNE.json`(v1) · `..._v2.json`

## 판정

- 배선: **PATCHED** (DEAD_WIRE 해소)
- 노브값: **NO_IMPROVE_HOLD** (0.15 유지)
- 값 변경 없음 · APPLY 금지
