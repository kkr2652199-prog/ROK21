# K-BT-ISSUE-PATH-METRIC

시각: 2026-08-12T07:51:58+09:00 · wire=**False** · ge3미클레임 · **1237아님**

## 판정
**METRIC_OK**

## 요지
- 목적: 강제BT **pool경로 등수**와 **발권5장 등수**를 같은 구간에 병기
- 구간 1137~1236 n=100 · bt_run_id **13** · 66.7s

## 비교 (모니터만)
| 경로 | mean_hits | ≥3 | ≥4 | tiers |
|------|-----------|----|----|-------|
| pool/repack(BT) | **2.5** | 46 | 4 | {'r4': 4, 'r5': 42} |
| **발권5장** | **1.64** | 12 | 0 | {'r5': 12} |
| gap(pool−issue) | 0.86 | 34 | 4 | — |

## 결론
- 상위적중 튜닝의 **SSOT 지표 = 발권경로**(또는 prefer/prize).
- pool경로 4·5등은 **장수효과**를 포함 → APPLY 근거로 쓰지 않음.

## 근거
- `D:/ROK21/docs/benchmarks/20260812_KBT_ISSUE_PATH_METRIC.json`
- `D:/ROK21/reports/20260812_KBT_ISSUE_PATH_METRIC.md`
- 도구: `tools/_k_bt_issue_path_metric.py`
