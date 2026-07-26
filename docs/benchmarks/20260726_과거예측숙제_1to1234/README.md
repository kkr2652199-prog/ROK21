# 20260726 — 과거 예측 숙제 (1~1234)

## 왜 하는가
1235(이번 주)는 지금 중요하지 않다.  
**과거 당첨표(1~1234) + 과거에 했던 예측·복습 결과**가 숙제장이다.  
“과거의 과거로 과거를 맞혀 본 기록” 속에서 명분을 찾는다.

## 데이터 SSOT
| 표 | 역할 | 실측(2026-07-26) |
|----|------|------------------|
| `lotto_draws` | 당첨 빅데이터 | MAX=1234, n=1234 |
| `testlotto_brain_review` | **숙제 본체** (뇌별 best 세트 복습) | stat/review ~1233행, markov 1232행 · MAX=1234 |
| `lotto_predictions` | 세트 원장 | 채점된 distinct target **약 85회**만 (희소) — 전구간 SSOT 아님 |
| `testlotto_brain_learn_state` | 오답 패턴·boost | ending_digit 최다 miss |

숫자 원본: [`homework_stats.json`](./homework_stats.json)

## 핵심 숫자 (brain_review)

| 뇌 | 회차수 | avg match | ≥3 | ≥4 | ≥5 |
|----|--------|-----------|----|----|-----|
| stat | 1233 | **1.700** | 128 | 9 | (ge5 합산 참고 JSON) |
| review | 1233 | **1.681** | 131 | 6 | |
| markov | 1232 | **1.619** | 130 | 8 | |

매칭 히스토그램(전뇌 합): 0×84, 1×1478, 2×1747, 3×366, 4×22, 5×1

최근창 1132~1234 avg: review **1.757** > stat 1.660 > markov 1.612

## 오답 패턴 (learn_state miss_counts 상위)
세 뇌 공통 1위: **ending_digit** (압도적)  
그다음: odd_even · consecutive · carry_over / overdue · pair

→ 숙제 가설: “끝수 스토리”를 boost로 키웠지만, miss 카운트도 끝수가 쌓인다.  
**명분 점검 대상 1호 = ending_digit 루프가 학습인지 자기강화인지.**

## 숙제 질문 (다음 단계 입력)
1. ending_digit miss가 왜 전뇌 공통 1위인가?
2. 4개 일치(희귀) 직전 구조 신호는 무엇인가?
3. review가 최근창에서 앞서는 이유가 feedback인가 우연인가?
4. 전구간 숙제 SSOT를 `brain_review`로 둘지, `lotto_predictions`를 채울지?

## 한 줄
미래가 아니라 **이미 치른 시험지**를 다시 푸는 것이 지금 할 일이다.
