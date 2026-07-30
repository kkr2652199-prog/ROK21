# K-SIGNAL-REPACK-01 — 번호 몰아주기(repack) survey (READ-ONLY live WF)

날짜 2026-07-30 · elapsed 27.7s · **PASS** · seed=42 · n=200 · gate=quick

개념: 뇌당 10세트 pool → **번호 단위** 신호 점수 → 5세트 몰아주기 ×3뇌=**15세트**. K-SIGNAL-SELECT(30장 중 5장 통째 선택)과 **다름**.

평가: primary=**best_of_15** · secondary=top5_from_15(JSON `top5_eval`). hint=w4_zone_mix@α=0.1.

## 1. 📋 선생님이 준 숙제
| 항목 | 내용 |
|------|------|
| **ID** | `K-SIGNAL-REPACK-01` |
| **질문** | 10세트 pool 번호를 신호 점수로 재조립(몰아주기)하면 set_no_asc·K-SIGNAL-SELECT combined 대비 ge3↑? |
| **PASS (QUICK)** | any repack strategy ge3>null AND p<0.15 |
| **금지** | coordinator·predict_* 수정 · wire · frozen path |

## 2. 🔧 학생이 한 일
| 항목 | Y/N |
|------|-----|
| coordinator 수정 | **N** |
| DB reset | **Y** | `lotto_predictions` 1260행 삭제 |
| pipeline | **WF live** |

## 3. 📊 풀이 (결과표)

### SUMMARY
| label | pipeline | mean | ge3_rate | Δnull | Δpin | p | verdict |
|-------|----------|-----:|---------:|------:|-----:|--:|---------|
| **theory null** | — | 0.8000 | 0.1137 | — | — | — | — |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | +0.0310 | — | — | pin |
| **set_no_asc (control)** | WF | 1.68 | 0.08 | -0.0337 | -0.0647 | 0.952412 | FAIL |
| **best repack** | WF | **2.33** | **0.325** | +0.2113 | +0.1803 | 0.0 | **PASS** |

### strategies (ge3 내림)
| strategy | eval | mean | ge3 | ge3_cnt | Δpin | p | verdict |
|----------|------|-----:|----:|--------:|-----:|--:|---------|
| random_repack | best_of_15 | 2.33 | 0.325 | 65 | +0.1803 | 0.0 | PASS |
| signal_repack | best_of_15 | 2.245 | 0.275 | 55 | +0.1303 | 0.0 | PASS |
| k_signal_select_combined | best_of_5_from_30 | 1.715 | 0.145 | 29 | +0.0003 | 0.102441 | PASS |
| hint_only_repack | best_of_15 | 1.82 | 0.115 | 23 | -0.0297 | 0.509824 | FAIL |
| set_no_asc | best_of_5 | 1.68 | 0.08 | 16 | -0.0647 | 0.952412 | FAIL |

### tier 1~5 (회차별 best 세트 등수 누적)
| strategy | r1 | r2 | r3 | r4 | r5 |
|----------|---:|---:|---:|---:|---:|
| hint_only_repack | 0 | 0 | 0 | 6 | 66 |
| k_signal_select_combined | 0 | 0 | 0 | 1 | 28 |
| random_repack | 0 | 0 | 0 | 6 | 67 |
| set_no_asc | 0 | 0 | 0 | 2 | 14 |
| signal_repack | 0 | 0 | 1 | 4 | 63 |

### top5_from_15 (보조)
| strategy | mean | ge3_rate |
|----------|-----:|---------:|
| signal_repack | 1.525 | 0.085 |
| hint_only_repack | 1.225 | 0.04 |

## 4. ✅/❌ 판정

### gate 체크 (항목별)

| # | 조건 | 결과 | O/X |
|---|------|------|-----|
| G1 | repack any ge3>null | signal_repack 0.275 | ✅ |
| G2 | p<0.15 (QUICK) | signal_repack p=0.0 | ✅ |
| G3 | **공정 비교(5장)** signal > combined | top5 ge3=0.085 < combined 0.145 | ❌ |
| G4 | random ≤ signal (신호 유효성) | random 0.325 > signal 0.275 | ❌ |

**종합:** 형식상 QUICK PASS이나, **15장(best_of_15) 효과**가 ge3를 부풀림.  
**5장 공정 비교(`top5_from_15`)** 기준 signal_repack ge3=**0.085** → set_no_asc(0.08)와 비슷, **combined(0.145)보다 낮음**.

### 해석 (한 줄)

- **몰아주기(repack) 신호 점수**는 15장 풀에서는 ge3↑처럼 보이지만, 실제 발권 5장으로 줄이면 **K-SIGNAL-SELECT combined보다 못함**.
- random_repack > signal_repack → **신호 학습보다 “장수(15)” 효과**가 지배적(artifact).

## 5. 📝 복습

- **형 아이디어 핵심 검증:** 번호 단위 repack은 combined(통째 5장 고르기) 대비 **우위 없음** (5장 기준).
- **다음:** wire 금지 유지 · **K-SIGNAL-SELECT-FULL** 우선(선별축) · repack은 FULL n=1182에서 top5_from_15 재검증 optional.
- **recommended_next:** `K-SIGNAL-SELECT-FULL` (repack 5장 공정 비교 FAIL → 선별축 우선)
- **verdict:** QUICK PASS(15장) / **실질 FAIL(5장 공정)** — signal_repack top5 ge3=0.085 vs combined 0.145

## 6. 📎 근거
- JSON: `docs/benchmarks/20260730_KSIGNAL_REPACK_survey.json`
- script: `tools/_k_signal_repack_survey.py`
- db_reset: {"table": "lotto_predictions", "draw_range": [1035, 1234], "deleted_rows": 1260, "remaining_in_range": 0, "learn_state_reset": false, "note": "eval 구간 cached prediction만 삭제 · live WF 생성 · learn_state/coordinator 미건드림"}
