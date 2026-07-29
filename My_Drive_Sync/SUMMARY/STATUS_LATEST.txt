# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-REVIEW-TUNE-SURVEY · **FAIL** · 15조합 best ge3=0.1117 · NEXT=K-ATTACK-HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-REVIEW-TUNE-SURVEY | **FAIL** · live walk-forward · predict_review_king 미수정 |
| best | carry=2.2 · decay=0.80 · window=0 |
| best ge3 | **0.1117** · ge3_count=**132** · n=**1182** |
| Δ / p | **-0.0330** / **0.600284** vs pin 0.1447 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored · live baseline ~0.11 불일치) |
| 권고 | **K-ATTACK-HOLD** · 오늘 탐색 전축 소진 · 승인필요=**예** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-REVIEW-TUNE-SURVEY** | review carry/decay/window 15조합 | **FAIL** |
| K-AUX-WEIGHT-SURVEY | 13조합 live · set_no 쿼터 | **FAIL** · 티켓불변 |
| K-STAT-TUNE-WIRE | gap20/hot10 배선 시도 | **FAIL** · 롤백 |
| K-STAT-TUNE | stat 격자 · stored markov/review | PASS(격자) |

---

## 2) REVIEW-TUNE 핵심

| 항목 | 값 |
|------|-----|
| n_eval | **1182** |
| best ge3 | **0.1117** (carry=2.2·decay=0.80·window=0) |
| mean | **1.7107** |
| 15조합 전부 FAIL | ge3 범위 0.0964~0.1117 (< pin 0.1447) |
| recommended_next | **K-ATTACK-HOLD** |

근거: `docs/benchmarks/20260729_KREVIEW_TUNE_survey.json` · `reports/20260729_KREVIEW_TUNE_SURVEY.md`

### 재탕금지 (누적)

REVIEW-TUNE(15조합) · AUX-WEIGHT(13조합) · AUX-BLEND · STAT-WIRE(gap20/hot10) · SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · GENMIX · 슬롯재선택 일체

---

## 3) 다음

K-ATTACK-HOLD — 오늘 탐색 전축 소진 · 다음 공격축 **형 결정 대기**.

---

## 4) 산출물

- docs/benchmarks/20260729_KREVIEW_TUNE_survey.json
- reports/20260729_KREVIEW_TUNE_SURVEY.md
- My_Drive_Sync/커서보고서/20260729_KREVIEW_TUNE_SURVEY.md
- tools/_k_review_tune_survey.py

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| n_eval | 1182 | 1182 | 1182 |
| best_combo | carry=2.2\|decay=0.8\|window=0 | carry=2.2\|decay=0.8\|window=0 | carry=2.2\|decay=0.8\|window=0 |
| ge3_rate | 0.1117 | 0.1117 | 0.1117 |
| Δ | -0.033 | -0.033 | -0.033 |
| p | 0.600284 | 0.600284 | 0.600284 |
| ge3_count | 132 | 132 | 132 |
| verdict | FAIL | FAIL | FAIL |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |
