# K-SIGNAL-BACKTEST-TAIL100 — 최근 100회 walk-forward 백테스트

날짜 2026-08-03 · gate=**tail100** · seed=**42**

---

## 1. 📋 선생님이 준 숙제

| 항목 | 내용 |
|------|------|
| **ID** | `K-SIGNAL-BACKTEST-TAIL100` |
| **질문** | 최근 100회에서 combined·signal_repack ge3/tier는? pin/null 대비? |
| **PASS (참고)** | QUICK: ge3>null(0.1137) AND p<0.15 |
| **금지** | coordinator wire · backtest 테이블 삭제 · 컨닝 |

## 2. 🔧 학생이 한 일

### DB reset (eval 구간만)

```json
{
  "deleted": {
    "lotto_predictions": {
      "draw_range": [
        1035,
        1234
      ],
      "deleted_rows": 0,
      "remaining_in_range": 0
    },
    "testlotto_pool_view_cache": {
      "draw_range": [
        1035,
        1234
      ],
      "deleted_rows": 0
    }
  },
  "kept": [
    "testlotto_backtest_runs",
    "testlotto_backtest_draw_results",
    "testlotto_pool_view_cache(범위外)"
  ],
  "learn_state_reset": false,
  "note": "eval 구간 cached prediction만 삭제 · live WF · backtest 기록 유지"
}
```

| 유지 | 삭제(범위内) |
|------|-------------|
| testlotto_backtest_runs · draw_results(기존 run) | lotto_predictions eval구간 |
| pool_view_cache(범위外) | pool_view_cache 1035~1234 |

### 실행 파라미터

| key | value |
|-----|-------|
| n_eval | 100 |
| draw_range | 1035–1234 |
| sample_mode | tail |
| seed | 42 |
| strategies | combined · signal_repack |

## 3. 📊 풀이 (결과표)

### SUMMARY

| label | strategy | mean | ge3_rate | ge3_cnt | Δpin | p | verdict | run_id |
|-------|----------|-----:|---------:|--------:|-----:|--:|---------|-------:|
| theory_baseline | — | 0.8000 | 0.1137 | — | — | — | null | — |
| WIRE-V2 pin | stored | 1.7504 | 0.1447 | — | — | — | pin | — |
| **signal_repack** | WF live | 2.2500 | 0.2750 | 55 | +0.1303 | 0.000000 | PASS | 5 |
| **combined** | WF live | 1.7300 | 0.1450 | 29 | +0.0003 | 0.102441 | PASS | 7 |

### tier 피벗 (run별)

- **signal_repack** (run_id=5): 1등=0 · 2등=0 · 3등=1 · 4등=7 · 5등=47
- **combined** (run_id=7): 1등=0 · 2등=0 · 3등=0 · 4등=0 · 5등=29

## 4. ✅ 맞은 것 / ❌ 틀린 것

- walk-forward only · frozen 경로 미수정 · backtest 기록 append/replace(동 survey+strategy)
- UI: 「🎯 3뇌 예측」 단일 버튼 SSOT

## 5. 다음

- K-SIGNAL-SELECT-FULL (1182) · wire=형 GO 전 금지

*JSON:* `D:/ROK21/docs/benchmarks/20260730_KSIGNAL_BACKTEST_tail100.json`
