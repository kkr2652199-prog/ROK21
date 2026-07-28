# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-SETPACK-TOP6 FAIL · NEXT=HOLD · V2 배선 유지 · WIRE금지

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| SETPACK-TOP6 | **FAIL** · 출현top6→set1 몰아주기 실익 없음 |
| WIRE-V2 | ENABLED=**True** (유지) |
| TUNE | FAIL (직전 · 파라미터 유지) |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-SETPACK-TOP6** | 출현횟수 top6 → set1 재조립 | **FAIL** |
| **K-MARKOV-TUNE** | decay/steps/top 27격자 | FAIL |
| **K-MARKOV-WIRE-V2** | set_no 쿼터 | PASS |

---

## 2) SETPACK 핵심

| 항목 | 값 |
|------|-----|
| 풀 | testlotto_brain_review · stat/markov/review · draw 53~1234 · n=1182/뇌 · pool 3546 |
| null_n5 ge3 | **0.1137** |
| pool base best ge3 / mean | **0.1227** / 1.7084 |
| pool SETPACK best ge3 / mean | **0.1010** / 1.6134 |
| Δ best ge3 | **−0.0217** |
| pool set1 ge3 (base→pack) | 0.0316 → **0.0254** |
| binom p vs null (pack) | **0.9929** |
| 뇌별 PASS | stat/markov/review **전부 FAIL** |
| recommended_next | **없음** |

근거: docs/benchmarks/20260729_KSETPACK_top6.json

---

## 3) 다음

K-ATTACK-HOLD — SETPACK·TUNE WIRE금지 · V2 배선 유지 · 형·커서 다음 축 1건 재선정 (승인 필요)

---

## 4) 산출물

- 	ools/_k_setpack_top6_survey.py
- docs/benchmarks/20260729_KSETPACK_top6.json
- 
eports/20260729_KSETPACK_TOP6.md
- My_Drive_Sync/커서보고서/20260729_KSETPACK_TOP6.md
