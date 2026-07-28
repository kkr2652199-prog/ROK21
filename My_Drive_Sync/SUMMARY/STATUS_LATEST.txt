# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-STRUCT-SURVEY 관측종료 · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| STRUCT | aux/analog/가중 **전부 FAIL** · 추천없음 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-STRUCT-SURVEY** | 4보조·analog·가중 | 관측종료 |
| **K-PROB-VECTOR** | 확률벡터 신호 | 유효 0 |
| **K-ATTACK-OPEN** | 3레버 | 추천없음 |

---

## 2) STRUCT 핵심

| 단계 | 결과 |
|------|------|
| composite spearman | **0.008** |
| analog best mean | 0.767 · vs RR −0.98 |
| AUX 가중 Δ | **+0.0002** |

근거: `docs/benchmarks/20260729_KSTRUCT_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — 새 축 재선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_struct_survey.py`
- `docs/benchmarks/20260729_KSTRUCT_survey.json`
- `reports/20260729_KSTRUCT_SURVEY.md`
