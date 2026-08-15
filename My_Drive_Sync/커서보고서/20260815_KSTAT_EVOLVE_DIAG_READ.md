# K-STAT-EVOLVE-DIAG-READ

시각: 2026-08-15T14:29:59+09:00 · **READ_OK** · READ-ONLY · stat만 · 1237아님 · hits/tier 클레임 금지
목적=evolve_log stat 200행 모니터 집계. 예측·원장·캐시·learn 미접촉. 파트2 확장 없음.

HARD=통과. n=200 · peek=0 · 타뇌행=0 · pred_1237=0 · MAX=1236.

## 0) 읽는 법

- E[hits]=**0.8**(K-O). 아래 Δ는 이론 대비 편차. **누가 낫다 금지**.
- ge3 회차수=그 역할 세트 중 hits≥3이 1장 이상인 회차. 커버율 모니터. 성적 아님.
- 3뇌 합산 없음. `WHERE brain_tag='stat'`만.
- 파트2 markov/review 확장=**형 GO 후**. 이번 턴 write 없음.

## 1) HARD / census

| 항 | 값 |
|----|-----|
| n_stat | 200 |
| window | [1037, 1236] |
| peek as_of≥draw | 0 |
| evolve 뇌 | {'stat': 200} |
| markov/review 행 | 0 |
| 원장 | {'stat': 3000} |
| 캐시 | {'markov': 200, 'review': 200, 'stat': 200} |
| predictions | 0 |
| pred_1237 | 0 |
| draws MAX | 1236 |

## 2) role별 세트 집계 (pool+repack, stat만)

| role | n_sets | n_draws | mean_hits | Δ vs 0.80 | ge3회차 | ge3율 |
|------|--------|---------|-----------|-----------|--------|------|
| skill | 1000 | 200 | 0.83 | 0.03 | 34 | 0.17 |
| cover | 600 | 200 | 0.74 | -0.06 | 9 | 0.045 |
| shape | 400 | 200 | 0.8575 | 0.0575 | 11 | 0.055 |
| focus | 1000 | 200 | 0.798 | -0.002 | 27 | 0.135 |

행 mean(repack5 모니터)=0.798 · Δ vs 0.80=-0.002 · 성적 아님.

## 3) role별 hits 히스토그램 (세트수, 0~6)

| role | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|------|---|---|---|---|---|---|---|
| skill | 391 | 429 | 145 | 29 | 6 | 0 | 0 |
| cover | 258 | 249 | 84 | 9 | 0 | 0 | 0 |
| shape | 154 | 168 | 63 | 11 | 4 | 0 | 0 |
| focus | 413 | 415 | 140 | 25 | 7 | 0 | 0 |

## 4) role별 tier 분포 (세트수 · 모니터)

- skill: 미적중=965, 5등=29, 4등=6
- cover: 미적중=591, 5등=9
- shape: 미적중=385, 5등=11, 4등=4
- focus: 미적중=968, 5등=25, 4등=7

## 5) ge3 회차 (커버율 관점 · n_draws=200)

- 아무 역할이든 hits≥3 1장 이상인 회차: **50** / 200 (성적 아님).
- 역할별 ge3회차=위 표. 역할 간 우열 문장 없음.

## 6) kind 분리 (참고 · 합산 서열 아님)

| kind | role | n_sets | mean_hits | Δ vs 0.80 |
|------|------|--------|-----------|-----------|
| pool | skill | 1000 | 0.83 | 0.03 |
| pool | cover | 600 | 0.74 | -0.06 |
| pool | shape | 400 | 0.8575 | 0.0575 |
| repack | focus | 1000 | 0.798 | -0.002 |

원 role 라벨: `{'skill_native': 1000, 'cover_r3': 600, 'shape_r2': 400, 'focus_r1': 1000}`.

## 7) 파트2 (미실행)

markov/review 확장 · lotto_predictions 리셋 · 3뇌 write = **형 GO 후**.
이번 턴 DB write 0. EVOLVE_AUTO/FEATURE_LAMBDA 미변경.

## 8) 금지 확인

3뇌 SUM 뷰 없음. 원장 미접촉. hits/tier로 APPLY·서열·성능 클레임 없음. 1237 아님.
