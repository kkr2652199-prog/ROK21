# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: BENCH_PROTOCOL 고정 · K-M/K-N 등재 · 분산·가중 시뮬

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` |
| 성적 | **`BENCH_PROTOCOL.md`** |

---

## 1) K-B 프로토콜 (고정)

성적 SSOT = `testlotto_brain_review.predicted_sets_json` **전세트 mean**  
`lotto_predictions` = 성적 비교 **금지**

---

## 2) K-N / K-M 판정

| ID | 판정 |
|----|------|
| K-N | 창100 best-of-5 **전원** null 기대 미상회 → **실력 증거 없음**. stat 1.687=분산/best 산물 |
| K-M | (a)현행 vs (b)균등: top5 멤버십차 **5%** → 학습가중 **사실상 무의미** |

mean100: stat 0.760 / markov 0.802 / review 0.852  
best천장 ≈2.27

---

## 3) 산출

`reports/20260727_KM_KN_분산검정.md`  
`My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md`

---

## 4) 다음

1. K-N: 학습입력을 mean으로 바꿀지(형)  
2. K-M: 계수/창 또는 set-mean 가중(형 · 코드는 승인 후)  
3. K-A: 프로토콜 준수 재측정 후에만  
