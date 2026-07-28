# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-SETCOUNT-NULL PASS · NEXT=K-MARKOV-WIRE

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| NULL | 10·15=장수효과 · **E 5장 실력** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SETCOUNT-NULL** | null MC vs 실측 | **PASS** → MARKOV-WIRE |
| **K-SETCOUNT-SURVEY** | 세트수 격자 | PASS(후 null로 장수기각) |
| **K-COVER-SURVEY** | wheel/pool | FAIL |

---

## 2) NULL 핵심

| 구성 | Δge3 | p | 판정 |
|------|------|---|------|
| n=15 mixed | +0.005 | 0.35 | 장수효과 |
| n=10 mixed | +0.014 | 0.13 | 장수효과 |
| **E markov3mix** | **+0.031** | **0.0007** | **실력** |
| D markov×5 | +0.023 | 0.010 | 실력 |
| F stat×5 | −0.005 | 0.70 | 장수효과 |

null_n5 ge3=**0.1137** · MC 10000×100draws seed42

근거: `docs/benchmarks/20260729_KSETCOUNT_null.json`

---

## 3) 다음

`K-MARKOV-WIRE` — E 배합(또는 D) 5장 배선 (승인 필요) · SETCOUNT 확장 금지

---

## 4) 산출물

- `tools/_k_setcount_null.py`
- `docs/benchmarks/20260729_KSETCOUNT_null.json`
- `reports/20260729_KSETCOUNT_NULL.md`
