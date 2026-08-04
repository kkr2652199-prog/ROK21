# K-EVOLVE-LOG — Phase1 회차 진화 로그 (가중 0)

`2026-08-04T03:36:23+00:00` · 1035~1234 · **wire 없음 · weight=0.0**

## 0. 한 줄

pool_view 캐시→`testlotto_evolve_log` 백필 **200**회차 · 캐시 miss **0** · 학습 가중 **0** · PASS=**True**

## 1. 뇌별 요약 (발권 repack best_of_5 참고)

| 뇌 | n | ge3_rate | avg_best | avg_mean |
|----|---|---------:|---------:|---------:|
| markov | 200 | **0.1300** | 1.885 | 0.806 |
| review | 200 | **0.1350** | 1.785 | 0.841 |
| stat | 200 | **0.1650** | 1.745 | 0.791 |

> ge3/best는 **참고 지표**. Phase1에서 학습 입력으로 쓰지 않음 (K-N).

## 2. 저장 내용

- pool 10 + repack 5 nums/hits
- features: sum·parity·zone·max_run·span (발권 평균 + best 세트)
- miss_tags: carry_over / overdue / ending_digit
- assemble_mode · weight_applied=0 · as_of=draw_no

## 3. 조회 API

- `GET .../evolve/log/{draw_no}` · sample 1200 ok=True
- `GET .../evolve/summary?start=1035&end=1234`

## 4. 다음 (Phase2 · 형 GO)

- `K-EVOLVE-SIGNAL` — best학습 차단 + 구조신호 λ survey
- 이번 패치: predict/W_*/quota/coordinator **미수정**

## 금지 준수

동결 3종 · kweon · FINDINGS 무단 · FAIL→auto-tune · best→실력 학습
