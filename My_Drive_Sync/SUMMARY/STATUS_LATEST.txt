# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-HISIM-SURVEY 관측종료 · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| HISIM | best mean **0.791** ≪ RR · 관측종료 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-HISIM-SURVEY** | 13D 구조우선 analog | 관측종료 |
| **K-STRUCT-SURVEY** | 4보조·analog | 관측종료 |
| **K-PROB-VECTOR** | 확률벡터 신호 | 유효 0 |

---

## 2) HISIM 핵심

| 항목 | 값 |
|------|-----|
| hisim_weighted | 0.791 |
| orig_chain8 | 0.767 |
| best_w | 0.80 |
| vs RR | **−0.95** |

근거: `docs/benchmarks/20260729_KHISIM_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — 새 축 재선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_hisim_survey.py`
- `docs/benchmarks/20260729_KHISIM_survey.json`
- `reports/20260729_KHISIM_SURVEY.md`
