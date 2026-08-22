# K-REVIEW-SEQ-DISTRIBUTE (2026-08-22)

- **판정:** `APPLY_OK` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음
- 시각: 2026-08-22T15:03:34+09:00
- 형: 세트분포 엔진 공식이 번호를 흩뿌림. 그 구조를 바꾼다. 타뇌는 확인 후.
- 근거: `20260822_KREVIEW_SEQ_DISTRIBUTE.json`

## 흩어짐 공식 (라이브 · 코드)

1. `engine.generate`: 세트마다 pool을 1~45로 **리셋** 후 `random.choices` 6개
2. `diversity.factor` ×3 oversample 후 `diversity.pick` Jaccard **0.85** → 겹침↓
3. cover(review)=Jaccard로 1~5와 **멀리**. shape=1번세트 1칸 교체
4. 앞채움(점수재조립)은 생성 공식이 아님 → 이번 패치에서 **3뇌 앞채움 OFF**

## 구조 변경 (금액뇌)

- 한 풀에서 `random.choices`로 소진. #1=엔진이 먼저 뽑은 6개. 고갈 시 리셋
- oversample·Jaccard 선별·aux 재정렬·cover멀리 **없음**. pool 10장=한 스트림
- `random.choices` 라인 동결

## 게이트 1137–1236 n100

- HARD `True` peek **0** size 0 err 0 11.5s · 변경 100

| | prefer | prize | skill5합 | union10 | Jaccard5 | #1∩#2 | 2장이상번호 |
|--|--------|-------|----------|---------|----------|-------|-------------|
| 구(흩뿌림) | 0.006699 | 0.009798 | 21.5 | 28.82 | 0.108527 | 0.87 | 6.39 |
| 신(소진) | 0.00211 | 0.003108 | 30.0 | 41.39 | 0.0 | 0.0 | 0.0 |
| Δ | -0.004589 | -0.00669 | 8.5 | — | -0.108527 | -0.87 | -6.39 |

- iso `True` · design( #1∩#2 감소 ) `True` · apply `True`
- 우열·hits 클레임 금지. iso=Δprefer<0.005 ∧ Δprize<0.005

## APPLY / 롤백

- `REVIEW_SEQ_DISTRIBUTE=True` · 앞채움 BRAINS `[]`
- refill review {'ok': 200, 'fail': 0, 'lo': 1037, 'hi': 1236}
- 타뇌 앞채움 캐시 되돌림 markov·stat 각 200 (확인은 금액뇌만)
- HARD DB {'draws_max': 1237, 'pred_1237': 0, 'ledger_stat': 3000}
- 롤백=`REVIEW_SEQ_DISTRIBUTE=False`
- 1237 신규예측 없음. 확인은 1037–1236 캐시

## 파일

- `app/testlotto/brains/review_brain/engine.py` · `predict.py`
- `app/testlotto/signal_pool.py`
- `20260822_KREVIEW_SEQ_DISTRIBUTE.json` · `20260822_KREVIEW_SEQ_DISTRIBUTE.md`
