# K-BRAIN-FRONTLOAD-NEXT (2026-08-22)

- **판정:** `APPLY_OK` · 공식없음 · 엔진 `number_scores` · 당첨미입력
- 시각: 2026-08-22T14:52:11+09:00
- 이어서: 금액뇌 APPLY 다음 markov·stat. 통과 뇌만 추가
- 근거: `20260822_KBRAIN_FRONTLOAD_NEXT.json`

## 방법

당첨 6개를 모으는 공식 없음. 각 뇌가 이미 가진 `number_scores`로
그 뇌 pool 합집합을 #1부터 채운다. 몰아주기 E = 새 #1~#5.
oracle(사후 당첨모음)은 모니터·금지.

- 유지 review · 추가 `['markov', 'stat']` · HOLD `[]`
- 라이브 BRAINS `['markov', 'review', 'stat']` · ALIGN `True`

## markov

- 캐시 n_ok **1234** / 1234 · skip 0

| 시안 | set1 | max | union | win∈union | full6회 | set1에6 | ge4장 |
|------|------|-----|-------|-----------|---------|---------|-------|
| live | 0.766613 | 1.935981 | 27.972447 | 3.71799 | 54 | 0 | 13 |
| freq | 0.758509 | 1.726904 | 25.215559 | 3.371961 | 33 | 0 | 4 |
| proxy | 0.784441 | 1.84765 | 31.225284 | 4.144246 | 137 | 0 | 11 |
| oracle | 3.71799 | 3.71799 | 25.215559 | 3.71799 | 54 | 54 | 740 |

- 게이트 HARD `True` peek **0** size 0 err 0 20.6s
- off prefer/prize `0.022549` / `0.008127` set1 `0.75`
- E Δprefer `-0.004645` Δprize `-0.001467` iso `True` set1 `0.85`
- D Δprefer `-0.000694` Δprize `-0.001257` iso `True`
- 채택 `E` · 엔진합집합 점수 당첨 `0.189298` 비당첨 `0.190279` Δ `-0.000981`

- 1237 재조립 `{'ok': True, 'tag': 'markov', 'win': [10, 20, 23, 34, 37, 40], 'set1': [1, 3, 7, 12, 17, 27], 'set1_hits': 0, 'note': '캐시재조립. predict_sets 없음'}`

## stat

- 캐시 n_ok **1235** / 1235 · skip 0

| 시안 | set1 | max | union | win∈union | full6회 | set1에6 | ge4장 |
|------|------|-----|-------|-----------|---------|---------|-------|
| live | 0.812146 | 1.996761 | 31.57085 | 4.215385 | 135 | 0 | 23 |
| freq | 0.8 | 1.804858 | 29.22753 | 3.918219 | 90 | 0 | 7 |
| proxy | 0.808097 | 1.836437 | 30.821053 | 4.11417 | 120 | 0 | 8 |
| oracle | 4.215385 | 4.215385 | 29.22753 | 4.215385 | 135 | 135 | 939 |

- 게이트 HARD `True` peek **0** size 0 err 0 16.3s
- off prefer/prize `0.006662` / `-6.2e-05` set1 `0.85`
- E Δprefer `-0.00179` Δprize `-0.001345` iso `True` set1 `0.78`
- D Δprefer `-0.000858` Δprize `-0.001049` iso `True`
- 채택 `E` · 엔진합집합 점수 당첨 `0.195154` 비당첨 `0.197602` Δ `-0.002448`

- 1237 재조립 `{'ok': True, 'tag': 'stat', 'win': [10, 20, 23, 34, 37, 40], 'set1': [3, 15, 16, 29, 34, 38], 'set1_hits': 1, 'note': '캐시재조립. predict_sets 없음'}`

## APPLY / 롤백

- refill [{'tag': 'markov', 'ok': 200, 'fail': 0, 'lo': 1037, 'hi': 1236}, {'tag': 'stat', 'ok': 200, 'fail': 0, 'lo': 1037, 'hi': 1236}]
- HARD DB {'draws_max': 1237, 'pred_1237': 0, 'ledger_stat': 3000}
- 롤백=`POOL_FRONTLOAD_BRAINS=frozenset({"review"})` (금액뇌만) 또는 전부 off
- 우열·1등클레임 금지 · 1237 신규예측 없음

## 파일

- `app/testlotto/signal_pool.py`
- `20260822_KBRAIN_FRONTLOAD_NEXT.json` · `20260822_KBRAIN_FRONTLOAD_NEXT.md`
- `tools/_k_brain_frontload_next.py`
