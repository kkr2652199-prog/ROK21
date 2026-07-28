# K-PROB-VECTOR — 확률벡터 신호 실측

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KPROBVEC_survey.json`  
📌 도구: `tools/_k_prob_vector_survey.py` · READ-ONLY · **26.3s**

---

## 0) 검토

HOLD→본 작업 교체(지시문) · NEXT 정합 후 실행.

---

## 1) 신호별 실측

| 신호 | 핵심 수치 | 기대/null | 유효 |
|------|-----------|-----------|------|
| stat recency (best=50) | spearman **0.0024** · top6 overlap 0.1325 | null≈0.133 | **아니오** |
| stat gap≥30 / ≥50 | hit 0.1278 / **0.1064** | 0.1333 | **아니오**(미달) |
| markov 전이 top6 | overlap **0.1333** | null | **아니오** |
| markov 5세트 합집합 | hit 0.435 · \|U\|≈19.7 | null \|U\|/45=**0.438** | **아니오** (Δ−0.002) |
| review carry | mean **0.825** | 0.80 · z p≈0.15 | **아니오** |
| review ending | hit **0.134** | 0.133 | **아니오** |

**recommended_strengthen = []**  
**verdict = 없음**

---

## 2) 해석

- OPEN 실패와 일관: 현재 쓰는 빈도·전이·이월·끝수 축은 WF에서 **null 수준**.
- markov pool이 single보다 높아 보인 것은 **합집합 크기 효과**뿐(null 보정 후 소멸).
- gap≥50은 오히려 기대 **미만**(과열 보정 역효과 가능 — 강화 금지).

---

## 3) 다음

유효 신호 0 → `K-ATTACK-HOLD` 복귀 (형·동생 **새 축** 논의).  
`K-PROB-STRENGTHEN` **등록 안 함**.
