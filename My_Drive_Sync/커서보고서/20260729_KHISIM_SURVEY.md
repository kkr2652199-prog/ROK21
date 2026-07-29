# K-HISIM-SURVEY — 고차원 구조 유사도

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KHISIM_survey.json`  
📌 도구: `tools/_k_hisim_survey.py` · analog_service **미수정** · **43.4s** · n_eval=**1182**

---

## 0) 검토

HOLD→본 작업 교체 · READ-ONLY · w_struct=0.80 구조 우선.

---

## 1) STEP3 비교

| method | mean | ge3_rate | Δ vs RR |
|--------|------|----------|---------|
| hisim_freq | 0.7876 | — | −0.955 |
| **hisim_weighted** | **0.7910** | 0.0237 | **−0.952** |
| hisim_chain8 | 0.7775 | — | −0.965 |
| orig_chain8 | 0.7665 | — | −0.976 |
| round_robin | 1.7428 | 0.1337 | 0 |

hisim이 orig보다 **소폭↑**(≈+0.02)이나 여전히 **≈null(0.8)** · RR 미달.

---

## 2) STEP4 w_struct 격자 (hisim_weighted)

| w | mean | ge3_rate |
|---|------|----------|
| 0.60 | 0.762 | 0.021 |
| 0.70 | 0.772 | 0.025 |
| **0.80** | **0.791** | 0.024 |
| 0.90 | 0.778 | 0.025 |

**best_w=0.80** — 격자 내 최선이어도 RR 미달.

---

## 3) 판정

gates: any_delta_gt0=**false** · mean/ge3 vs RR **false**  
**verdict=관측종료** · **recommended_next=없음**  
→ Jaccard↓·구조↑만으로는 1장 analog 경로가 null을 넘지 못함.

NEXT=`K-ATTACK-HOLD` (형·동생 재논의).
