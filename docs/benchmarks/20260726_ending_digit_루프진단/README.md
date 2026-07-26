# 20260726 — ending_digit miss 루프 진단

## 왜
과거 숙제에서 miss 1위가 ending_digit. 학습인지 자기강화인지 판정.

## 판결: **자기강화 (오탐 루프)**

| 증거 | 값 |
|------|-----|
| review에서 ending miss 비율 | 뇌별 **~97%** (시대별도 96~98% 평탄) |
| 구 detect를 랜덤 6수에 적용 | **98.8%** (우리 뇌와 동일 수준) |
| boost 포화 추정 | stat 약 **10회차**에 상한 도달 |
| 끝수 커버율(stat) 시대별 | 0.56→0.58 수준, boost 후에도 개선 미미 |
| boost가 하는 일 | **직전 회차 끝수** 번호 가중 |
| 구 detect가 보는 일 | 당첨 끝수 집합 − 예측 끝수 집합 ≠ ∅ (거의 항상) |

→ **감지 의미 ≠ boost 의미**. miss는 매회 쌓이고 boost는 초반에 꽉 참.

## 조치 (코드)
1. [`draw_analysis.detect_missed_patterns`](../../../app/testlotto/draw_analysis.py):  
   직전 끝수 중 당첨에 재등장한 끝을 예측이 **하나도** 못 담을 때만 `ending_digit`
2. [`learn_state.apply_feedback`](../../../app/testlotto/learn_state.py): 상한 도달 시 +0.05 중단 + 저장 시 BOOST_CAPS 클램프
3. DB `learn_state`: ending_digit miss/boost **0으로 리셋** (오염 제거). carry/overdue도 상한으로 클램프

신 detect 랜덤 기준선: **~19.5%** (구 98.8% 대비).

## 하지 않은 것
- 과거 `brain_review.missed_patterns` 3000행 재기록 (전구간 WF 재실행은 별도 지시)
- `random.choices` 변경 없음

## 산출
- `evidence.json`
- `learn_state_reset.json`
