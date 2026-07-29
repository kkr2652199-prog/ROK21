# K-STRUCT-SURVEY — 4보조·analog 구조 서베이

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KSTRUCT_survey.json`  
📌 도구: `tools/_k_struct_survey.py` · READ-ONLY · **82.2s**

---

## 0) 검토

HOLD→본 작업 교체 · READ-ONLY 실행.

---

## 1) STEP1 — 4보조 vs matched (n_sets=18435)

| 점수 | spearman_r |
|------|------------|
| aux_pattern | 0.0087 |
| aux_balance | 0.0076 |
| aux_miss | 0.0000 |
| aux_referee (brain_w) | −0.0070 |
| **composite 0.25×4** | **0.0080** |

PASS(composite>0.03): **FAIL**

---

## 2) STEP2 — analog 구조유사 (d≥100)

| 방법 | mean | ge3_rate |
|------|------|----------|
| M_freq | 0.7419 | (JSON) |
| M_weighted | 0.7656 | |
| M_chain8 | **0.7674** | |
| +aux filter | 0.7436 | |

delta_vs_rr (vs 1.7428): **−0.975** · PASS: **FAIL**  
(1장 analog ≈ null 0.8 · RR/tier 축과 다름)

---

## 3) STEP3 — AUX 가중 combo

| combo | mean |
|-------|------|
| baseline | 0.8297 |
| A / B / C | 0.8299 / 0.8299 / 0.8297 |

best=A · Δ vs baseline **+0.0002** ≪ 0.01 → **FAIL**

---

## 4) 판정

**verdict=관측종료** · **recommended_next=없음**  
보조 재가중·analog 결합 모두 null급. NEXT=`K-ATTACK-HOLD`.
