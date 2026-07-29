# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-POSTHOC-ANALYSIS · **무신호** · 50시드×50회 best ge3=0.18 p=0.109 · NEXT=K-ATTACK-HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-POSTHOC-ANALYSIS | **무신호** · 50시드×50회 역추적 · 체계적 패턴 없음 |
| best seed | #44 ge3=**0.18** · p=**0.109** (n=50 · >0.05 = 유의하지 않음) |
| overall mean ge3 | **0.1052** · std=**0.0417** · max=0.18 · min=0.02 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored · live baseline ~0.11 불일치) |
| 결론 | 상위/하위 시드 뇌별 차이=시드 분산 · 활용 가능한 신호 없음 |
| 권고 | **K-ATTACK-HOLD** · V2 pin 유지 · 형 결정 대기 · 승인필요=**예** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-POSTHOC-ANALYSIS** | 50시드×50회 역추적 · 뇌별/특성 패턴 분석 | **무신호** |
| K-REVIEW-TUNE-SURVEY | review carry/decay/window 15조합 | **FAIL** |
| K-AUX-WEIGHT-SURVEY | 13조합 live · set_no 쿼터 | **FAIL** · 티켓불변 |
| K-STAT-TUNE-WIRE | gap20/hot10 배선 시도 | **FAIL** · 롤백 |

---

## 2) POSTHOC 핵심

| 항목 | 값 |
|------|-----|
| n_seeds | **50** |
| n_eval_per_seed | **50** (draw 53~1234 균등 샘플) |
| overall mean ge3 | **0.1052** · std=0.0417 |
| best seed | #44 ge3=**0.18** p=**0.109** (유의하지 않음) |
| 뇌별 top-bot diff | markov +0.037 · stat +0.04 · review +0.008 (시드 분산) |
| 적중회차 특성 | sum Δ=14 · AC Δ=-0.03 · consec Δ=-0.07 (모두 소폭) |
| 결론 | 체계적 활용 가능 신호 없음 |
| recommended_next | **K-ATTACK-HOLD** |

근거: `docs/benchmarks/20260729_KPOSTHOC_analysis.json` · `reports/20260729_KPOSTHOC_ANALYSIS.md`

### 재탕금지 (누적)

POSTHOC(50시드) · REVIEW-TUNE(15조합) · AUX-WEIGHT(13조합) · AUX-BLEND · STAT-WIRE(gap20/hot10) · SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · GENMIX · 슬롯재선택 일체

---

## 3) 다음

K-ATTACK-HOLD — POSTHOC 무신호 · V2 pin 유지 · 형 결정 대기.

---

## 4) 산출물

- docs/benchmarks/20260729_KPOSTHOC_analysis.json
- reports/20260729_KPOSTHOC_ANALYSIS.md
- My_Drive_Sync/커서보고서/20260729_KPOSTHOC_ANALYSIS.md
- tools/_k_posthoc_analysis.py

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| n_seeds | 50 | 50 | 50 |
| n_eval_per_seed | 50 | 50 | 50 |
| overall mean ge3 | 0.1052 | 0.1052 | 0.1052 |
| best seed ge3 | 0.18 | 0.18 | 0.18 |
| best seed p | 0.108945 | 0.108945 | 0.109 |
| signal_detected | False | 무신호 | 무신호 |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |
