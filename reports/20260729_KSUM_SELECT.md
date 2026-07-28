# K-SUM-SELECT — V2 쿼터 고정 · 티켓 합(이론 138) 슬롯 재선택

📅 2026-07-29 · DB/coordinator **미수정** · `db_code_write=false`  
선정축 ID: **K-SUM-SELECT**  
도구: `tools/_k_sum_select_survey.py`  
JSON: `docs/benchmarks/20260729_KSUM_select.json`  
V2 pin: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json` (ge3=**0.1447**)

---

## 0) 선정 요약

| 항목 | 값 |
|------|-----|
| **선정축** | **K-SUM-SELECT** |
| 가설 | V2(m3+s1+r1) 고정 시, set_no 오름 대신 **티켓 합≈이론평균 138**로 슬롯을 고르면 ge3↑ |
| V2와 직교 | 예 — 뇌 믹스·파라미터·생성 불변 · **발권 선택 기준만** |
| 관측 | **실행완료** (0.253s · brain_review nums+matched · sum=`aux_balance_keeper`식 · 이론138) |
| 판정 | **FAIL(WIRE금지)** — 어떤 정책도 V2 ge3 미돌파 |
| 실패시 | **HOLD · V2 유지 · SUM-SELECT 재탕금지** |

---

## 1) 후보 2~4개 → 1건

| # | 후보 ID | 가설 스케치 | 기각 사유 |
|---|---------|-------------|-----------|
| A | **K-SUM-SELECT** ✅ | 티켓 합≈138 / 극단 / 다양으로 V2 슬롯 재선택 | **선정** |
| B | K-ODD-SELECT | 홀짝 균형으로 슬롯 | BAND-SELECT `all_odd_bal` 부차정책으로 이미 FAIL (ge3 0.1328) |
| C | K-ACFORM-SELECT | AC≈8로 슬롯 | STRUCT/pattern 전역 서베이 인접 · 형태축 재탕 위험 |
| D | K-ATTACK-SEARCH | 오버샘플→필터 top5 | 재예측↑ · GATHER/SETPACK 인접 |

**왜 A:** 코드에 `sum_range`/`sum_score`·K-Z/K-AA 폴백합 **138** 실재 · BAND(LMH)·odd 부차와 **합 축**으로 구분 · V2 직교 · READ-ONLY 즉시 · 재탕금지 목록 미포함.

---

## 2) 관측 방법

1. `testlotto_brain_review` draw **53~1234** · 3뇌 × 5세트 `nums`+`matched_count`
2. sum_score = `1 - min(1, |sum-138|/60)` · **당첨구간·history 미사용** (SLICE·BAND와 직교)
3. V2 쿼터 `{markov:3, stat:1, review:1}` 고정 · 슬롯 모드만 변경
4. baseline = `v2_asc`

**PASS 기준 (사전 · JSON `protocol`):**

| 게이트 | 조건 |
|--------|------|
| **hit_WIRE** | best ge3 > V2 0.1447 **AND** Δge3 ≥ **+0.005** **AND** binom p vs null(0.1137) < 0.05 |
| 종합 PASS | hit_WIRE |

→ 충족 시만 `K-SUM-SELECT-WIRE` **후보 보고**(형 GO 전 coordinator 패치 금지). 아니면 HOLD.

---

## 3) 핵심 숫자 (JSON)

| policy | mean | ge3 | Δge3 vs V2 | mean_sum | mean_sum_score |
|--------|------|-----|------------|----------|----------------|
| **v2_asc** (현행) | **1.7504** | **0.1447** | 0 | **137.1042** | **0.7091** |
| all_sum_near | 1.7310 | 0.1277 | -0.0170 | 137.5183 | 0.8584 |
| **all_sum_far** (최근접) | 1.7174 | **0.1404** | **-0.0043** | 136.5350 | 0.5380 |
| all_sum_high | 1.7014 | 0.1294 | -0.0153 | 154.2394 | 0.6709 |
| all_sum_low | 1.7521 | 0.1311 | -0.0136 | 119.6621 | 0.6557 |
| all_sum_mid | 1.6980 | 0.1159 | -0.0288 | 137.1228 | 0.7171 |
| all_sum_diverse | 1.7428 | 0.1311 | -0.0136 | 137.1506 | 0.8195 |
| markov_asc_others_sum_near | 1.7572 | 0.1362 | -0.0085 | 137.0591 | 0.7981 |
| markov_sum_near_others_asc | 1.7318 | 0.1362 | -0.0085 | 137.5635 | 0.7694 |

- n_eval=**1182** · v2 ge3 count=**171** · p_vs_null(v2)=**0.000679**
- spearman(sum_score, matched) @v2 = **0.0230**
- best hit vs V2: **없음** (전 정책 ge3 ≤ 0.1447)
- 최근접: **all_sum_far** · Δge3=**-0.0043** (V2 미돌파 · 의미임계 +0.005 반대)

---

## 4) Verdict

| gate | 결과 |
|------|------|
| hit_beats_v2_ge3 | **false** |
| hit_delta_ge3 ≥ 0.005 | **false** |
| hit_pass_vs_null | **false** |
| **PASS → WIRE** | **FAIL** |

**결론:** 티켓 합(이론138) 축은 V2와 직교로 **관측 가치 있음**. 전 정책 ge3 ≤ V2 → **coordinator 수정·WIRE 금지**. V2 set_no_asc 유지.  
이론합 근접(`sum_near`)은 mean_sum_score↑에도 ge3↓(-0.0170) — 합 정렬이 적중 신호가 아님.

---

## 5) 실패시 HOLD / NEXT

- **WIRE/coordinator 수정 금지**
- LIVE V2 (`MARKOV_WIRE_ENABLED=True` · set_no 쿼터) **유지**
- NEXT=`K-ATTACK-HOLD` — SUM-SELECT 재탕금지 · 다음 축 재선정
- 재탕금지 추가: **SUM-SELECT** (기존 SETPACK/MARKOV-TUNE/SETNO/EV-POP/BAND-SELECT/conf-quota/HISIM·STRUCT·COVER wheel/GATHER에 합류)

---

## 6) 산출물

- `tools/_k_sum_select_survey.py`
- `docs/benchmarks/20260729_KSUM_select.json`
- 본 보고서 · `My_Drive_Sync/커서보고서/` 복사

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/BOOT/NEXT | 판정 |
|------|------|--------|------------------|------|
| 축ID | K-SUM-SELECT | 동상 | K-SUM-SELECT | OK |
| 가설 | 합≈138 슬롯재선택→ge3↑ | 동상 | 동상 | OK |
| n / V2 ge3 / mean | 1182 / 0.1447 / 1.7504 | 동상 | 동상 | OK |
| 최근접 | all_sum_far · 0.1404 · Δ-0.0043 | 동상 (ASCII `-`) | 동상 | OK |
| gates.PASS | false | FAIL | FAIL·HOLD | OK |
| recommended_next | 없음(HOLD·V2유지·SUM-SELECT재탕금지) | 동상 | K-ATTACK-HOLD | OK |
| db_code_write / coordinator | false / 미수정 | 동상 | WIRE금지 | OK |
