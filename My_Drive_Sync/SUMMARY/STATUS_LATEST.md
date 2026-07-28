# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-PROB-VECTOR 유효신호 0 · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| PROB-VECTOR | 유효신호 **0** · STRENGTHEN 없음 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-PROB-VECTOR** | recency/gap/전이/pool/carry/ending | 전부 null급 |
| **K-ATTACK-OPEN** | 3레버 서베이 | 추천없음 |
| **K-REFEREE-WINDOW** | W=30 | PASS |

---

## 2) PROB-VECTOR 핵심

| 신호 | 결과 |
|------|------|
| recency best | sp 0.002 |
| gap≥50 | **기대 미만** |
| markov pool | null 보정 후 Δ−0.002 |
| carry | +0.025 · p≈0.15 |

근거: `docs/benchmarks/20260729_KPROBVEC_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — 새 축 재선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_prob_vector_survey.py`
- `docs/benchmarks/20260729_KPROBVEC_survey.json`
- `reports/20260729_KPROB_VECTOR.md`
