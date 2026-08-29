# K-REVIEW-SHAPE-KB-CONSEC-NEUTRAL

시각: 2026-08-29T12:47:58+09:00 · **SPEC_OK** · 4번 WIRE True 유지 · prize표 미접촉 · 1237아님 · hits 금지
목적=저울의 run_hist(연속) 가점만 중립. 합/폭/홀짝/AC 유지.

## S0) 저울 성분

점수 부품: ['odd_hist', 'run_hist(max_run)', 'sum_gauss', 'span_gauss', 'ac_gauss'].
연속 성분=**run_hist keyed by max_run (1=무연속, 2=run2포함, 3+=run3)**.
패치 후 유지=['odd_hist', 'sum', 'span', 'ac'] · 중립=run_hist / max_run.
롤백=`REVIEW_SHAPE_KB_RUN_NEUTRAL=False`.

## S1) 패치

APPLY=안 함(롤백). WIRE=True · RUN_NEUTRAL 파일=False.

## S2) 게이트 1137–1236 n100 (4번 OFF↔ON, run중립 적용 상태)

| 항 | OFF | ON | Δ(ON−OFF) | 기준 |
|----|-----|-----|-----------|------|
| run2 | 0.667 | 0.693 | 0.026 | ≤0.001 → False |
| run3 | 0.046 | 0.056 | 0.01 | 모니터 |
| prize | 0.024503 | 0.022708 | -0.001795 | ≥-0.00192 → True |
| struct | 0.042302 | 0.036686 | -0.005616 | ≥-0.005521 → False |

peek=0 · n=100 · size_bad=0 · bonus_in=0 · pred_1237=0 · MAX=1238.

## 판정

**SPEC_OK**. 롤백실행=True. 몰아주기/prize표/choices 미수정.

run2 Δ가 0.008→0.026으로 커짐. `run_hist`는 흔한 max_run=1(무연속)에 가점을 줘서 연속을 **누르는** 쪽에 가깝고, 빼면 억제가 풀린다. 연속 가점만 중립화하는 최소패치는 이 게이트를 못 넘김.

