# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-AUX-WEIGHT-SURVEY · **FAIL** · 13조합 ge3=0.1100 동일 · NEXT=K-ATTACK-HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-AUX-WEIGHT-SURVEY | **FAIL** · live walk-forward · coordinator 미수정 |
| best ge3 | **0.1100** (combo A~M 전부 동일) · ge3_count=**130** · n=**1182** |
| Δ / p | **-0.0347** / **0.669622** vs pin 0.1447 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored · live baseline 0.1100 불일치) |
| 권고 | **K-ATTACK-HOLD** · AUX_WEIGHTS 배선 금지 · 승인필요=**예** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-AUX-WEIGHT-SURVEY** | 13조합 live · set_no 쿼터 | **FAIL** · 티켓불변 |
| K-STAT-TUNE-WIRE | gap20/hot10 배선 시도 | **FAIL** · 롤백 |
| K-STAT-TUNE | stat 격자 · stored markov/review | PASS(격자) |
| K-MARKOV-WIRE-V2 | set_no 쿼터 | PASS(핀·stored) |

---

## 2) AUX-WEIGHT 핵심

| 항목 | 값 |
|------|-----|
| n_eval | **1182** |
| live ge3 (13조합 공통) | **0.1100** (< pin 0.1447) |
| mean | **1.7191** |
| best_combo | **A** [0.25,0.25,0.25,0.25] |
| 관측 | V2 set_no_asc → AUX 가중 변경해도 발권 5장 동일 |
| recommended_next | **K-ATTACK-HOLD** |

근거: `docs/benchmarks/20260729_KAUX_WEIGHT_survey.json` · `reports/20260729_KAUX_WEIGHT_SURVEY.md`

### 재탕금지 (누적)

AUX-WEIGHT(13조합) · AUX-BLEND · STAT-WIRE(gap20/hot10) · SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · GENMIX · 슬롯재선택 일체

---

## 3) 다음

K-ATTACK-HOLD — AUX_WEIGHTS 실레버 아님 확인 · 다음 공격축 **형 결정 대기**.

---

## 4) 산출물

- docs/benchmarks/20260729_KAUX_WEIGHT_survey.json
- reports/20260729_KAUX_WEIGHT_SURVEY.md
- My_Drive_Sync/커서보고서/20260729_KAUX_WEIGHT_SURVEY.md
- tools/_k_aux_weight_survey.py

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| n_eval | 1182 | 1182 | 1182 |
| best_combo | A | A | A |
| ge3_rate | 0.11 | 0.1100 | 0.1100 |
| Δ | -0.0347 | -0.0347 | -0.0347 |
| p | 0.669622 | 0.669622 | 0.669622 |
| 13조합 동일 | true | true | true |
| verdict | FAIL | FAIL | FAIL |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |
