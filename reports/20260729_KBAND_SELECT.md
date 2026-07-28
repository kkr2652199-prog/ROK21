# K-BAND-SELECT — V2 쿼터 고정 · 티켓 내 LMH 번호대역 슬롯 재선택

📅 2026-07-29 · DB/coordinator **미수정** · `db_code_write=false`  
선정축 ID: **K-BAND-SELECT**  
도구: `tools/_k_band_select_survey.py`  
JSON: `docs/benchmarks/20260729_KBAND_select.json`  
V2 pin: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json` (ge3=**0.1447**)

---

## 0) 선정 요약

| 항목 | 값 |
|------|-----|
| **선정축** | **K-BAND-SELECT** |
| 가설 | V2(m3+s1+r1) 고정 시, set_no 오름 대신 **티켓 내 LMH(1-15/16-30/31-45) 이론점수**로 슬롯을 고르면 ge3↑ |
| V2와 직교 | 예 — 뇌 믹스·파라미터·생성 불변 · **발권 선택 기준만** |
| 관측 | **실행완료** (0.391s · brain_review nums+matched · LMH=`aux_balance_keeper` 식) |
| 판정 | **FAIL(WIRE금지)** — 어떤 정책도 V2 ge3 미돌파 |
| 실패시 | **HOLD · V2 유지 · BAND-SELECT 재탕금지** |

---

## 1) 후보 2~4개 → 1건

| # | 후보 ID | 가설 스케치 | 기각 사유 |
|---|---------|-------------|-----------|
| A | **K-BAND-SELECT** ✅ | 티켓 LMH 점수/다양으로 V2 슬롯 재선택 | **선정** |
| B | K-DIV-V2 | Jaccard diversify within V2 | COVER/GATHER 다양성 인접 |
| C | K-AUX-THRESH | 보조점수 문턱으로 슬롯 | conf-quota 구WIRE 인접 |
| D | K-ATTACK-SEARCH | 오버샘플→필터 top5 | 재예측↑ · GATHER/SETPACK 인접 · EV-POP 때도 기각 |

**왜 A:** 코드에 `_zone_counts`/`_zone_score_lmh` 실재 · SLICE(당첨/직전 구간일치)와 가설 다름 · V2 직교 · READ-ONLY 즉시 · 재탕금지 목록 미포함.

---

## 2) 관측 방법

1. `testlotto_brain_review` draw **53~1234** · 3뇌 × 5세트 `nums`+`matched_count`
2. LMH score = `0.3 + 0.4*(p/p_mode)` · mode=(2,2,2) · **당첨구간·history 미사용** (SLICE와 직교)
3. V2 쿼터 `{markov:3, stat:1, review:1}` 고정 · 슬롯 모드만 변경
4. baseline = `v2_asc`

**PASS 기준 (사전 · JSON `protocol`):**

| 게이트 | 조건 |
|--------|------|
| **hit_WIRE** | best ge3 > V2 0.1447 **AND** Δge3 ≥ **+0.005** **AND** binom p vs null(0.1137) < 0.05 |
| 종합 PASS | hit_WIRE |

→ 충족 시만 `K-BAND-SELECT-WIRE` **후보 보고**(형 GO 전 coordinator 패치 금지). 아니면 HOLD.

---

## 3) 핵심 숫자 (JSON)

### 3-1) 정책별 (n=**1182**)

| policy | mean | ge3 | Δge3 vs V2 | mean_lmh | p vs null |
|--------|------|-----|------------|----------|-----------|
| **v2_asc** (현행) | **1.7504** | **0.1447** | 0 | **0.5505** | **0.000679** |
| all_lmh_diverse | 1.7538 | 0.1387 | **-0.0060** | 0.6012 | 0.004642 |
| markov_asc_others_lmh_high | 1.7504 | 0.1379 | -0.0068 | 0.5908 | 0.005955 |
| markov_lmh_high_others_asc | 1.7301 | 0.1371 | -0.0076 | 0.5746 | 0.007591 |
| all_lmh_low | 1.7217 | 0.1354 | -0.0093 | 0.4775 | 0.012099 |
| all_odd_bal | 1.7420 | 0.1328 | -0.0119 | 0.5484 | 0.023200 |
| all_lmh_high | 1.7403 | 0.1303 | -0.0144 | 0.6150 | 0.041989 |
| all_lmh_mid | 1.7022 | 0.1201 | -0.0246 | 0.5488 | 0.255289 |

### 3-2) 상관

| 항목 | 값 |
|------|-----|
| spearman(lmh_score, matched) @ v2_asc | **0.0114** (p=**0.379017**) |
| 해석 | LMH점수↔적중 **무상관** → 이론대역 선호가 적중을 끌어올리지 않음 |

### 3-3) 게이트

- hit: 어떤 정책도 V2 ge3 **미돌파** → `best_hit_policy=null`
- 최근접 `all_lmh_diverse` ge3=**0.1387** · Δge3=**-0.0060** · mean만 +0.0034 (무의미)

---

## 4) Verdict

| gate | 결과 |
|------|------|
| hit_beats_v2_ge3 | **false** |
| hit_delta_ge3 ≥ 0.005 | **false** |
| hit_pass_vs_null | **false** |
| **PASS → WIRE** | **FAIL** |

**결론:** 티켓 내 LMH 대역 축은 V2와 직교로 **관측 가치 있음**. 전 정책 ge3 ≤ V2 → **coordinator 수정·WIRE 금지**. V2 set_no_asc 유지.

---

## 5) 실패시 HOLD / NEXT

- **WIRE/coordinator 수정 금지**
- LIVE V2 (`MARKOV_WIRE_ENABLED=True` · set_no 쿼터) **유지**
- NEXT=`K-ATTACK-HOLD` — BAND-SELECT 재탕금지 · 다음 축 재선정
- 재탕금지 추가: **BAND-SELECT** (기존 SETPACK/MARKOV-TUNE/SETNO/EV-POP/conf-quota/HISIM·STRUCT·COVER wheel/GATHER에 합류)

---

## 6) 산출물

- `tools/_k_band_select_survey.py`
- `docs/benchmarks/20260729_KBAND_select.json`
- 본 보고서 · `My_Drive_Sync/커서보고서/` 복사

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/BOOT/NEXT | 일치 |
|------|------|--------|------------------|------|
| n | 1182 | 1182 | 1182 | OK |
| v2_asc mean | 1.7504 | 1.7504 | 1.7504 | OK |
| v2_asc ge3_rate | 0.1447 | 0.1447 | 0.1447 | OK |
| v2_asc ge3 count | 171 | (표 rate) | — | OK |
| v2_asc p_vs_null | 0.000679 | 0.000679 | — | OK |
| nearest policy | all_lmh_diverse | all_lmh_diverse | all_lmh_diverse | OK |
| nearest ge3 | 0.1387 | 0.1387 | 0.1387 | OK |
| nearest Δge3 | -0.006 (ASCII) | -0.0060 | -0.0060 | OK |
| spearman lmh↔matched | 0.0114 / p=0.379017 | 0.0114 / 0.379017 | 0.0114 | OK |
| gates.PASS | false | FAIL | FAIL | OK |
| verdict | FAIL_HOLD_V2 | FAIL · HOLD · V2유지 | HOLD · V2유지 | OK |
| recommended_next | 없음(HOLD·V2유지·BAND-SELECT재탕금지) | 동상 | K-ATTACK-HOLD | OK |
| db_code_write | false | 미수정 | — | OK |

※ 유니코드 마이너스 미사용 · JSON ASCII `-` 그대로 인용.
