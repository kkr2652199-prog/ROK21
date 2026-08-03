# K-SIGNAL-BACKTEST-TAIL100 — walk-forward 백테스트 (n=200)

날짜 2026-08-03 · gate=**tail100/QUICK** · seed=**42** · **K-BENCH-NULL-BY-EVAL** 정합

---

## 1. 📋 선생님이 준 숙제

| 항목 | 내용 |
|------|------|
| **ID** | `K-SIGNAL-BACKTEST-TAIL100` |
| **질문** | combined·signal_repack ge3/tier는? **eval_mode 정합** null/pin 대비? |
| **PASS (참고)** | QUICK: ge3 > **null(eval_mode)** AND p<0.15 |
| **금지** | coordinator wire · 컨닝 · best_of_15를 null 0.1137로 판정 |

## 2. 🔧 학생이 한 일

### DB reset (eval 구간만)

| 유지 | 삭제(범위内) |
|------|-------------|
| testlotto_backtest_runs · draw_results | lotto_predictions 1035~1234 |
| pool_view_cache(범위外) | pool_view_cache 1035~1234 |

### 실행 파라미터

| key | value |
|-----|-------|
| n_eval | **200** |
| draw_range | **1035–1234** |
| sample_mode | tail |
| seed | 42 |
| strategies | combined · signal_repack |

## 3. 📊 풀이 (결과표)

### SUMMARY (eval_mode · null 병기)

| label | strategy | eval_mode | mean | ge3_rate | ge3_cnt | null_ge3 | Δnull | Δpin | p | verdict | run_id |
|-------|----------|-----------|-----:|---------:|--------:|---------:|------:|-----:|--:|---------|-------:|
| theory_baseline | — | best_of_5 | 1.7289 | 0.1137 | — | 0.1137 | — | — | — | null | — |
| theory_baseline | — | best_of_15 | 2.2692 | 0.3036 | — | 0.3036 | — | — | — | null | — |
| WIRE-V2 pin | stored | best_of_5 | 1.7504 | 0.1447 | — | 0.1137 | — | — | — | pin | — |
| **signal_repack** | WF live | **best_of_15** | 2.2500 | 0.2750 | 55 | **0.3036** | **−0.0286** | +0.1303 | 0.830398 | **FAIL** | 5 |
| **combined** | WF live | **best_of_5_from_30** | 1.7300 | 0.1450 | 29 | **0.1137** | +0.0313 | +0.0003 | 0.102441 | **PASS** | 7 |

> 이전 표가 signal_repack을 null 0.1137로 PASS 처리한 것은 **단위 오류**(장수 착시). 올바른 null=0.3036이면 FAIL.

### tier 피벗 (run별)

- **signal_repack** (run_id=5): 1등=0 · 2등=0 · 3등=1 · 4등=7 · 5등=47
- **combined** (run_id=7): 1등=0 · 2등=0 · 3등=0 · 4등=0 · 5등=29

## 4. ✅ 맞은 것 / ❌ 틀린 것

| # | 조건 | 결과 | O/X |
|---|------|------|-----|
| G1 | combined ge3>null5(0.1137) | 0.145 | ✅ |
| G2 | combined p<0.15 | 0.102 | ✅ |
| G3 | signal_repack ge3>null15(0.3036) | 0.275 | ❌ |
| G4 | eval_mode·null 병기 | 본 표 | ✅ |

## 5. 다음

- pin 갭(FULL 0.1184→0.1447) · **형 GO**
- wire=형 GO 전 금지

*JSON:* `docs/benchmarks/20260730_KSIGNAL_BACKTEST_tail100.json`
