# K-SIGNAL-SELECT-01 — 신호셋트 선별 축 survey (READ-ONLY live WF)

날짜 2026-07-30 · gate=**quick** · verdict=**QUICK PASS**

---

## 1. 📋 선생님이 준 숙제

| 항목 | 내용 |
|------|------|
| **ID** | `K-SIGNAL-SELECT-01` |
| **질문 (한 문장)** | 3뇌×10 pool(survey 2-pass)에서 통합 5신호셋트를 고를 때, window overlap·draw_features bin·Jaccard·combined 중 어떤 선별 축이 null/pin 대비 ge3를 올리는가? |
| **PASS 기준 (QUICK)** | any selector: ge3 > null(0.1137) **AND** p < 0.15 |
| **FAIL 기준** | 모든 selector가 null 이하 또는 p ≥ 0.15 |
| **금지사항** | coordinator·predict_* 수정 금지 · production wire 금지(형 GO 전) · DB 쓰기 금지 · READ-ONLY live WF만 |
| **선행 완료** | K-WINDOW-SIGNAL-01 (window hint: w4_zone_mix@α=0.1) |

---

## 2. 🔧 학생이 한 일

### 코드·배선 (wire)

| 항목 | Y/N | 비고 |
|------|-----|------|
| coordinator / predict_* 수정 | **N** | `coordinator_modified`: false |
| production wire (형 GO) | **N** | WIRE-V2 pin ge3=0.1447 유지 |
| DB 쓰기 | **N** | `db_code_write`: false |
| pipeline | **WF live** | stored pin은 비교 기준행만 |

### 실행 파라미터

| key | value | 출처 |
|-----|-------|------|
| n_eval | 200 | JSON |
| draw_range | 1035–1234 | JSON |
| sample_mode | tail | JSON `eval_window` |
| seed | 42 | JSON `mc_seed` |
| pool_sets_per_brain | 10 | JSON |
| selected_n | 5 | JSON |
| window_hint | w4 · zone_mix · α=0.1 | JSON `window_hint` |
| selectors | set_no_asc, window_overlap, bin_match, jaccard_div, combined | JSON |

---

## 3. 📊 풀이 (결과표)

### SUMMARY (필수)

| label | pipeline | mean | ge3_rate | ge3_cnt | Δge3 vs null | Δge3 vs pin | p (vs null) | verdict |
|-------|----------|-----:|---------:|--------:|-------------:|------------:|------------:|---------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | null |
| **WIRE-V2 pin** | stored | **1.7504** | **0.1447** | — | +0.0310 | — | — | pin |
| **set_no_asc (control)** | WF live | 1.68 | 0.08 | 16 | −0.0337 | −0.0647 | 0.952412 | FAIL |
| **best selector** | WF live | **1.715** | **0.145** | 29 | +0.0313 | +0.0003 | **0.102441** | **PASS** |

### selectors 전체 (ge3 내림)

| selector | mean | ge3_rate | ge3_cnt | ge4_rate | ge4_cnt | Δpin | Δnull | p | verdict |
|----------|-----:|---------:|--------:|---------:|--------:|-----:|------:|--:|---------|
| combined | 1.715 | 0.145 | 29 | 0.005 | 1 | +0.0003 | +0.0313 | 0.102441 | PASS |
| bin_match | 1.68 | 0.115 | 23 | 0.0 | 0 | −0.0297 | +0.0013 | 0.509824 | FAIL |
| jaccard_div | 1.595 | 0.115 | 23 | 0.0 | 0 | −0.0297 | +0.0013 | 0.509824 | FAIL |
| set_no_asc | 1.68 | 0.08 | 16 | 0.01 | 2 | −0.0647 | −0.0337 | 0.952412 | FAIL |
| window_overlap | 1.64 | 0.08 | 16 | 0.005 | 1 | −0.0647 | −0.0337 | 0.952412 | FAIL |

### tier 피벗

**tier: 미수집 (본 survey)** — JSON에 r1~r5 없음. ge3/ge4만 기록.

---

## 4. ✅ 맞은 것 / ❌ 틀린 것

### PASS gate 체크 (항목별 O/X)

| # | gate 조건 | 결과 | O/X |
|---|-----------|------|-----|
| G1 | any selector ge3 > null (0.1137) | combined ge3=0.145 | ✅ |
| G2 | p < 0.15 (QUICK) | combined p=0.102441 | ✅ |
| G3 | coordinator_modified = false | false | ✅ |
| G4 | full: ge3 > pin AND p < 0.05 | 미실행 (QUICK) | N/A |

**종합 verdict:** **QUICK PASS** — JSON `pass_gate`: true · `verdict`: "QUICK PASS: combined ge3=0.145 p=0.102441"

### 해석 (한 줄)

- **combined**만 null·pin 동시 상회(+0.0313 vs null, +0.0003 vs pin); overlap·bin·jaccard·control(set_no_asc) 단독은 pin·null 모두 FAIL.

---

## 5. 📝 복습 (다음에 고칠 것)

- QUICK은 탐색 gate — pin 대비 +0.0003은 사실상 동률; **full n=1182**에서 ge3>pin(0.1447) AND p<0.05 재검증 필요.
- window_overlap·set_no_asc ge3=0.08로 control 대비 combined lift 확인됐으나, overlap 단독 축은 기각.
- production wire(combined 선별)는 **형 GO 전 금지** — FULL PASS 후 판단.

**recommended_next:** `K-SIGNAL-SELECT-FULL` — full 1182 walk-forward · pin+p<0.05 확인

---

## 6. 📎 근거

| 항목 | 값 |
|------|-----|
| JSON SSOT | `docs/benchmarks/20260730_KSIGNAL_SELECT_survey.json` |
| seed | 42 |
| n_eval | 200 |
| elapsed_sec | 18.1 |
| pass_gate (JSON) | true |
| script | `tools/_k_signal_select_survey.py` |

### 팩트체크 (JSON ↔ 보고서)

| 필드 | JSON | 보고서 | 일치 |
|------|------|--------|------|
| n_eval | 200 | 200 | ✅ |
| baseline control ge3 | 0.08 (set_no_asc) | 0.08 | ✅ |
| best ge3 | 0.145 (combined) | 0.145 | ✅ |
| pass_gate | true | true | ✅ |
| coordinator_modified | false | false | ✅ |
