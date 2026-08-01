# K-BACKTEST-FULL-C — C package production stack FULL n=1182 walk-forward

📅 2026-08-01 · **FAIL** · READ-ONLY · `db_code_write=false` · HEAD pending

## Executive Summary

C package production stack (hint=0.15 · learn wired · aux 1:1 · wire=set_no_asc) **FULL n=1182 walk-forward FAIL**.  
overall ge3=**0.1015** (120/1182) — live baseline **0.1218** 미달 · QUICK **0.125** 대비 **−0.0235 collapse**.

근거: `docs/benchmarks/20260801_KBACKTEST_FULL_C.json`

---

## 1. Overall (coordinator FULL path)

| 지표 | 값 | ref | Δ |
|------|-----|-----|---|
| **ge3_rate** | **0.1015** | quick 0.125 | **−0.0235** |
| ge3_count | 120 | — | — |
| mean_match | 1.692 | — | — |
| p_value vs null(0.1137) | 0.916 | — | FAIL |
| n_eval | 1182 | draw 53~1234 | seed=42 |
| LOOK_BACK | 52 | — | — |

### Verdict

| 기준 | threshold | actual | result |
|------|-----------|--------|--------|
| live baseline | ≥ 0.1218 | 0.1015 | **FAIL** |
| strong pass (V2 pin) | ≥ 0.1447 | 0.1015 | **FAIL** |
| null (0.1137) | > null | 0.1015 | **FAIL** |

**Verdict: FAIL** — ge3 < 0.1218 live baseline

---

## 2. by_brain (각 뇌 5세트 단독 · best match per draw)

| brain_tag | ge3_rate | ge3_count | mean_match | p vs null | vs overall |
|-----------|----------|-----------|------------|-----------|------------|
| **stat** | **0.1125** | 133 | 1.754 | 0.564 | +0.0110 |
| markov | 0.1074 | 127 | 1.633 | 0.764 | +0.0059 |
| review | 0.1066 | 126 | 1.684 | 0.791 | +0.0051 |
| **coordinator (wired)** | **0.1015** | 120 | 1.692 | 0.916 | — |

**관찰:** 개별 뇌 단독 ge3가 coordinator wired(0.1015)보다 **모두 높음**. wire quota(set_no_asc) 선택이 풀 품질을 **하향**시키는 패턴 — K-QUOTA-GAP-SURVEY(43%)과 정합.

---

## 3. by_period (overall path · period split)

| period | draw_range | n | ge3_rate | ge3_count | mean_match | p vs null |
|--------|------------|---|----------|-----------|------------|-----------|
| early | 53–447 | 395 | **0.0759** | 30 | 1.610 | 0.995 |
| mid | 448–841 | 394 | 0.1091 | 43 | 1.749 | 0.636 |
| late | 842–1234 | 393 | **0.1196** | 47 | 1.718 | 0.379 |
| **full** | 53–1234 | 1182 | 0.1015 | 120 | 1.692 | 0.916 |

**관찰:** early(0.0759) 극약 · late(0.1196)는 QUICK tail(0.125)에 근접. **tail-200 QUICK가 FULL 평균을 과대 추정** — collapse 원인.

---

## 4. Stack Config (production · 고정)

| 항목 | 값 |
|------|-----|
| HINT_WEIGHT | 0.15 |
| LEARN_WIRED | True |
| AUX_1TO1_ENABLED | True |
| wire | set_no_asc (MARKOV_WIRE unchanged) |
| path | 3뇌 pool → aux scoring → wire quota → best of 5 |

---

## 5. Reference Comparison

| ref | ge3 | Δ vs overall |
|-----|-----|--------------|
| QUICK n=200 (COMPLETE) | 0.125 | −0.0235 |
| live_baseline (K-10SET-DET-LAB-FULL) | 0.1218 | −0.0203 |
| v2_pin (WIRE-V2) | 0.1447 | −0.0432 |
| null | 0.1137 | −0.0122 |

K-WIRE-SELECT-FULL-SURVEY set_no_asc FULL ge3=**0.1015** — **동일** (교차 검증 OK).

---

## 6. Analysis

1. **QUICK→FULL collapse (−0.0235):** tail-200(1035~1234) ge3=0.125가 FULL 0.1015를 과대 추정. late period(0.1196)만 QUICK에 근접.
2. **Wire quota 역효과:** by_brain solo ge3(stat 0.1125 > markov 0.1074 > review 0.1066) > coordinator wired(0.1015). set_no_asc가 oracle 대비 43% gap — wire가 품질 저하.
3. **early period 약세:** draw 53~447 ge3=0.0759 — 초기 학습 데이터 부족·cold start. mid/late 회복.
4. **null 미달:** overall 0.1015 < null 0.1137 — 통계적 우위 없음(p=0.916).
5. **C package core ≠ production 성능:** Phase0~7 QUICK PASS(0.125)이 FULL에서 **FAIL**(0.1015). 패키지 동치·QUICK 게이트만으로 production 승격 불가.

---

## 7. Tune Priority (survey only · auto-tune 금지)

| 우선 | ID | 대상 | 근거 | GO 조건 |
|------|-----|------|------|---------|
| **P0** | wire/selection | set_no_asc → conf/aux_hint | by_brain solo > wired · quota_gap 43% | 형 GO + K-WIRE-SELECT-FULL 재확인 |
| **P1** | period/window | early 약세 · tail bias | early 0.0759 vs late 0.1196 | K-BRAIN-TUNE-SURVEY |
| **P2** | hint/learn | hint=0.15 · learn wired | solo ge3 null 미달 | K-BRAIN-TUNE-SURVEY |

---

## 8. Next

| ID | 할일 | 선행 |
|----|------|------|
| **K-BRAIN-TUNE-SURVEY** | hint/learn/window/selection READ-ONLY sweep · FULL n=1182 | **형 GO 대기** |
| K-WIRE-SELECT-GO-WAIT | wire HOLD · FULL collapse 확인 | FULL FAIL |

**금지:** app/ 코드 변경 · DB write · stack flag 변경 · auto-start tuning

---

## 9. 도구·산출물

- `tools/_k_backtest_full_c.py` — FULL walk-forward bench (READ-ONLY)
- `docs/benchmarks/20260801_KBACKTEST_FULL_C.json` — consolidated 결과
