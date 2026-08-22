# K-REVIEW-SHAPE-CONSEC (2026-08-22)

- **판정:** `APPLY_OK` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음
- 시각: 2026-08-22T15:38:27+09:00
- 형: 붙는 번호(1-2-3-4-5-6류)가 814만 중 극소. 1~1237 당첨 패턴을 뇌가 예측 전 읽게.
- 근거: `20260822_KREVIEW_SHAPE_CONSEC.json`

## 당첨 1~1237 (실측)

- n **1237** · MAX `1237` · pred_1237 **0** · 금액뇌캐시1037-1236 `200`
- 널 E[연번쌍] **0.6667** (44×C(43,4)/C(45,6))

| | n | 연번쌍평균 | 연번≥1 | run≥3 | run≥4 | run=6 |
|--|---|------------|--------|-------|-------|-------|
| 당첨 1–1237 | 1237 | 0.660469 | 0.516572 | 0.054163 | 0.00485 | 0.0 |
| 금액뇌 skill1–5 | 1000 | 0.645 | 0.532 | 0.049 | 0.0 | 0.0 |
| 금액뇌 pool10 | 2000 | 0.66 | 0.537 | 0.053 | 0.0 | 0.0 |

- 당첨표 as_of `1237` hist `{1: 598, 2: 572, 3: 61, 4: 6, 5: 0, 6: 0}`
- 6연속(1–6류)은 당첨·예측 모두 극소/0이 정상. tier1이 이미 run≥4 탈락.

## 첫 패치

`shape_table.summarize(draws_before)` 를 예측 전 읽고,
가중치에서 3연속 고질량 구간의 가운데를 ×0.75 (random.choices 전).

## 게이트 1137–1236 n100

- HARD `True` peek **0** size 0 err 0 3.9s · 변경 99
- off prefer/prize `0.00211` / `0.003108` pairs `0.642` run3 `0.052`
- on  `0.002078` / `0.00259` pairs `0.648` run3 `0.048`
- Δprefer `-3.2e-05` Δprize `-0.000518` Δpairs `0.006` Δrun3 `-0.004`
- iso `True` design `True` apply `True`

- WIRE `True` · refill `{'ok': 200, 'fail': 0}`
- 롤백=`REVIEW_SHAPE_WIRE=False`
- 우열금지 · 다음 패치(간격/홀짝/구간)는 형 확인 후 1건

## 파일

- `app/testlotto/brains/review_brain/shape_table.py` · `engine.py`
- `20260822_KREVIEW_SHAPE_CONSEC.json` · `20260822_KREVIEW_SHAPE_CONSEC.md`
