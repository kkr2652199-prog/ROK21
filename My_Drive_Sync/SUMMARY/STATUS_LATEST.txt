# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-STAT-TUNE · PASS · best ge3=0.1523 > pin 0.1447 · NEXT=K-STAT-TUNE-WIRE(승인대기)

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-STAT-TUNE | **PASS** · READ-ONLY 격자 · 코드 **미수정** |
| best | decay=**0.02** gap=**20** hot=**10** · ge3=**0.1523** · mean=**1.7758** |
| Δ / p | **+0.0076** / **3.6e-05** · verdict=개선 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (유지·미배선) |
| 권고 | **K-STAT-TUNE-WIRE** · 승인필요=**예** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-STAT-TUNE** | stat recency/gap/hot(+pair) 격자 · markov/review stored | **PASS** |
| K-ATTACK-HOLD-MAP | 닫힌축·실레버공백 · 새벤치無 | HOLD맵 |
| K-GENMIX | 뇌별 predict_sets(n) | FAIL |
| K-AUX-BLEND | AUX_WEIGHTS·\*40 | FAIL |
| K-GENDIV | diversify/Jaccard | FAIL |
| K-SUM/BAND/EV/SETNO/SETPACK | 슬롯재선택류 | FAIL |
| K-MARKOV-TUNE | decay/steps/top | FAIL |
| K-MARKOV-WIRE-V2 | set_no 쿼터 | PASS(핀) |

---

## 2) STAT-TUNE 핵심

| 항목 | 값 |
|------|-----|
| n_eval | **1182** |
| STEP1 best | 0.02 / 20 / 10 · ge3=**0.1523** |
| STEP3 pair | 30/0.5 유지가 최선 (추가실익 無) |
| wire 재생성(0.02/30/5) | ge3=0.1481 (시드·stat재생성 ≠ pin) |
| recommended_next | **K-STAT-TUNE-WIRE** |
| 승인필요 | **예** (predict_statistical 리터럴 배선 전) |

근거: `docs/benchmarks/20260729_KSTAT_TUNE_survey.json` · `reports/20260729_KSTAT_TUNE_SURVEY.md`

### 재탕금지 (누적)

SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · AUX-BLEND · GENMIX · 슬롯재선택 일체 · **(STAT 격자 본턴 완료 → WIRE만 승인대기)**

---

## 3) 다음

K-STAT-TUNE-WIRE — best(0.02/20/10 · pairs30/cap0.5)를 `predict_statistical.py`에 배선할지 **형 승인**. 승인 전 코드·DB 변경 금지.

---

## 4) 산출물

- docs/benchmarks/20260729_KSTAT_TUNE_survey.json
- reports/20260729_KSTAT_TUNE_SURVEY.md
- My_Drive_Sync/커서보고서/20260729_KSTAT_TUNE_SURVEY.md
- tools/_k_stat_tune_survey.py

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| best ge3 | 0.1523 | 0.1523 | 0.1523 |
| Δ | +0.0076 | +0.0076 | +0.0076 |
| p | 3.6e-05 | 3.6e-05 | 3.6e-05 |
| recommended_next | K-STAT-TUNE-WIRE | K-STAT-TUNE-WIRE | K-STAT-TUNE-WIRE |
