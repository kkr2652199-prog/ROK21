# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-SETCOUNT-SURVEY PASS · NEXT=K-SETCOUNT-WIRE

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| SETCOUNT | n=10·15 **ge3>RR** · WIRE후보(null주의) |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SETCOUNT-SURVEY** | 세트수·뇌단독 격자 | **PASS** → WIRE |
| **K-COVER-SURVEY** | F1 wheel·pool | FAIL (ge3≤RR) |
| **K-HISIM-SURVEY** | 13D analog | 관측종료 |

---

## 2) SETCOUNT 핵심

| 항목 | 값 |
|------|-----|
| n=5 | mean 1.752 · ge3 **0.1151** (<RR) |
| n=10 | mean 2.102 · ge3 **0.2284** |
| n=15 | mean 2.249 · ge3 **0.3088** (≈null 0.313) |
| n=20 | 풀부족 스킵 |
| best_solo | **markov** ge3 0.1362 |
| top1_3 | ge3 **0.1447** |
| recommended | **K-SETCOUNT-WIRE** |

근거: `docs/benchmarks/20260729_KSETCOUNT_survey.json`

---

## 3) 다음

`K-SETCOUNT-WIRE` — 장수 효과 vs 실력 분리 후 SETS 확장 여부 (승인 필요)

---

## 4) 산출물

- `tools/_k_setcount_survey.py`
- `docs/benchmarks/20260729_KSETCOUNT_survey.json`
- `reports/20260729_KSETCOUNT_SURVEY.md`
