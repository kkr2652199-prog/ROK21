# K-ATTACK-BAYES — inv-corr 동적가중 시뮬

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KBAYES_dyn_weight.json`  
📌 도구: `tools/_k_attack_bayes.py`  
📌 범위: WF 2~1234 · n_eval=**1182** (창50 워밍 제외) · DB/코드 **미수정**

---

## 0) 외부AI 지시 검토

| 항목 | 판정 |
|------|------|
| NEXT=`K-ATTACK-BAYES` 정합 | **OK** — 진행 |
| READ-ONLY · JSON만 | **OK** |
| 흐름 이탈 | 없음 → **반문 없음** |

---

## 1) 방법

- 예측벡터: 뇌별 5세트 번호 카운트 (45차원)
- 창=50 · `[d-50, d)` only (컨닝 금지)
- 창 내 매회 뇌쌍 Pearson → 뇌별 avg_corr → `w ∝ 1/(avg_corr+ε)`
- baseline: 고정 1/3 (soft) · round-robin 1장 (pick) · max-conf 1장 (SLICE 대조)

---

## 2) 상관·가중 (실측)

| 쌍 | mean corr |
|----|-----------|
| markov–review | **0.059** |
| stat–markov | 0.111 |
| stat–review | 0.117 |

| 뇌 | mean dyn w |
|----|------------|
| markov | **0.372** (저상관 → 상향) |
| review | 0.356 |
| stat | 0.272 |

CREW Jaccard≈0.11과 같은 스케일(저상관) — 전제 재확인.

---

## 3) 성적 · delta

| 정책 | mean | ge3_rate |
|------|------|----------|
| soft_equal | 1.7115 | 0.1286 |
| soft_invcorr | 1.7105 | 0.1261 |
| **pick_round_robin** | **1.7428** | **0.1337** |
| pick_invcorr | 1.6963 | 0.1261 |
| pick_max_conf | 1.6717 | 0.1091 |

| delta | mean | ge3_rate |
|-------|------|----------|
| soft_invcorr − soft_equal | **−0.001** | −0.0025 |
| pick_invcorr − round_robin | **−0.047** | −0.0076 |
| pick_invcorr − max_conf | +0.025 | +0.017 |

---

## 4) 판정

1. **soft 혼합 ≈ null** — 가중 평균으로는 이득 없음.
2. **inv-corr 1장 선택 < round-robin** — 저상관 뇌 승격은 RR보다 못함.
3. **max_conf 1장은 RR·invcorr보다 약함** — SLICE의 “conf 정렬 여지”는 **뇌 간 선택**이 아니라 **뇌 내 세트 순위/보정** 쪽 힌트로 재해석.
4. **배선 보류** (GATHER/SLICE와 동일).

---

## 5) 다음

`K-ATTACK-CONF-CAL` — 뇌 **내부** best_set conf 보정·순위 시뮬 (READ-ONLY).  
크로스뇌 inv-corr 가중은 본 결과로 **관찰 종료**.
