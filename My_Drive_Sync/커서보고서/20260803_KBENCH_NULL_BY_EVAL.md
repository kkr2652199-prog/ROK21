# K-BENCH-NULL-BY-EVAL — eval_mode별 null 병기

HEAD (push 후 기입) · 2026-08-03 · P0 from K-BT-PRECISION-BENCH

## 변경

| 파일 | 내용 |
|------|------|
| `tools/bench_quick_gate.py` | `null_for_eval_mode` · `enrich_metrics(eval_mode=)` |
| `tools/import_k_signal_backtest.py` | repack/select에 eval_mode null·p·verdict 저장 |
| `BENCH_PROTOCOL.md` | §0.1 eval_mode↔null 표 · §6·§9 정합 |
| `BENCH_REPORT_TEMPLATE.md` | SUMMARY에 eval_mode·모드 null 컬럼 |
| `20260730_KSIGNAL_BACKTEST_tail100.json` | signal_repack FAIL vs null15 |
| `20260730_BACKTEST_TAIL100.md` | 표 정정 |

## 검증 (로컬)

```
best_of_5  → null_ge3=0.1137
best_of_15 → null_ge3=0.3036
enrich(55/200, best_of_15) → FAIL p≈0.830
enrich(29/200, best_of_5_from_30) → PASS p≈0.102
```

## 비고

- 엔진/fusion/동결 토큰 미수정
- pin 갭 패치는 별도 **형 GO**
