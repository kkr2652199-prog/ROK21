# ROK21 — ending_digit 루프 진단·수정

📅 2026-07-26 KST · `D:\ROK21` · 원본 kweon 미접촉

## 판결
**자기강화(오탐).** 학습이 아니라 miss 카운터가 거의 매회 +1 되던 구조.

## 증거
| 항목 | 값 |
|------|-----|
| review ending miss율 | ~**97%** (전뇌·전시대) |
| 구 detect × 랜덤6수 | **98.8%** |
| boost 포화 | ~**10회차** |
| 끝수 커버율 개선 | 미미 (0.56→0.58) |
| boost 의미 | 직전 회차 끝수 가중 |
| 구 detect 의미 | 당첨 끝수 미커버 (거의 항상) |

## 코드 조치
- `detect_missed_patterns`: 직전 끝수 재등장분을 예측이 **전무**할 때만 miss  
  → 랜덤 기준선 **~19.5%**
- `apply_feedback`: 상한 도달 시 가산 중단 + 저장 클램프
- learn_state ending miss/boost **리셋 0** (carry/overdue도 상한 클램프)

## 벤치
`docs/benchmarks/20260726_ending_digit_루프진단/`

## 미수행
과거 review 행 재기록(전구간 WF) — 별도 지시 시
