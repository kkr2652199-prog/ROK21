# K-REVIEW-REASONABLE-SET (2026-08-22)

- **판정:** `APPLY_OK` · 금액뇌만 · 당첨미입력 · 1237 신규예측 없음
- 시각: 2026-08-22T16:01:00+09:00
- 형: 소진=찌꺼기. 장마다 합리한 장. Jaccard멀리 없음. 장겹침 허용.
- 근거: `20260822_KREVIEW_REASONABLE_SET.json`

## 재구성

- **끔:** 45소진 찌꺼기장 · Jaccard 0.85 선별 · cover Jaccard멀리 · aux 재정렬
- **켬:** 장마다 1–45 리셋 후 `random.choices` 6개 · `tier1`(합 80–210 · 홀수 1–5 · 구간 2+ · 연번&lt;4)
- #1=엔진이 먼저 완성한 한 장. 장끼리 같은 믿는 번호 겹침 허용
- `random.choices` 라인 동결. 형태표(3능선×0.75) 유지. 몰아주기 score5 불변
- 롤백=`REVIEW_REASONABLE_SET=False` (소진 재켜려면 `REVIEW_SEQ_DISTRIBUTE=True`)

## 게이트 1137–1236 n100

- HARD `True` peek **0** size 0 err 0 · 변경 100

| | prefer | prize | skill5합 | Jaccard5 | #1∩#2 | 2장이상 | wrap8-10 |
|--|--------|-------|----------|----------|-------|---------|----------|
| 소진(라이브) | 0.002078 | 0.00259 | 30.0 | 0.0 | 0.0 | 0.0 | 5.586667 |
| 합리장 | 0.007701 | 0.009157 | 21.72 | 0.098615 | 1.06 | 6.66 | 4.02 |
| Δ vs소진 | +0.005623 | +0.006567 | −8.28 | +0.098615 | +1.06 | +6.66 | −1.566667 |

- 설계 `True` (#1∩#2↑ · skill5합↓)
- **ISO vs 소진 `False`** — 찌꺼기장이 축을 낮춰 둔 대비. 소진을 되돌리면 축이 다시 올라감
- **ISO vs 원흩뿌림(Jaccard) `True`** — Jaccard prefer/prize `0.006699`/`0.009798` → Δprefer **+0.001002** Δprize **−0.000641**
- 형 GO=재구성. 적용 근거=설계+원흩뿌림 ISO. vs소진 ISO 실패는 숨기지 않음

## APPLY

- SEQ `False` · REASONABLE `True` · refill `{'ok': 200, 'fail': 0, 'lo': 1037, 'hi': 1236}`
- HARD DB draws_max **1237** · pred_1237 **0** · ledger stat **3000**
- 확인=1037–1236 금액뇌. 타뇌 캐시 불변

## 1236 캐시 샘플 (성적 아님)

당첨 `12 18 21 29 34 38`

| # | 번호 | #1과 겹침 |
|---|------|-----------|
| 1 | 6 7 11 24 26 42 | (기준) |
| 2 | 6 21 22 26 32 39 | 6, 26 |
| 3 | 13 15 27 28 36 42 | 42 |
| 5 | 1 10 18 28 32 34 | — |

#1은 소진 때와 같다(먼저 6개). #2부터는 남은 공 덤프가 아니라 **다시 1–45에서 한 장**. #2가 #1과 6·26을 공유.

## 파일

- `app/testlotto/brains/review_brain/engine.py` · `predict.py` · `app/testlotto/signal_pool.py`
- `20260822_KREVIEW_REASONABLE_SET.json` · `20260822_KREVIEW_REASONABLE_SET.md`
