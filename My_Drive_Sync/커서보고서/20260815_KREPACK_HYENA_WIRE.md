# K-REPACK-HYENA-WIRE

시각: 2026-08-15T16:44:55+09:00 · **APPLY_OK** · APPLY=True · 1237아님 · 등수 게이트 아님
단계: S0리스트 → S1 stat → S2 markov → S3 review → S4 합동스모크 → 통과뇌 캐시재생.

## 0) 한 줄

몰아주기를 뇌별 점수로 **새 5장**을 짜는 하이에나로 바꿨다. 라이브 stat=`score5` · markov=`score5` · review=`score5`. 점수축은 기존 그대로(stat 과거/원장 · markov prefer · review prize). 타깃 적중 미입력.

## 1) 단계 리스트

| 단계 | 뇌 | 1순위 | 실패시 | 게이트 |
|------|----|--------|--------|--------|
| S0 | — | 플래그 신설 | — | 코드 |
| S1 | stat | score5 | keep1 | prefer/prize · pool불변 |
| S2 | markov | score5 | keep1 | 동상 · 타뇌 플래그OFF |
| S3 | review | score5 | keep1 | 동상 · 타뇌 플래그OFF |
| S4 | 3뇌 | 합동 스모크 1234–1236 | — | peek0 · 10+5 |

## 2) 게이트 결과

| 단계 | 뇌 | 모드 | HARD | iso | design | Δprefer | Δprize | copy off→on | union off→on | 변경 | 판정 |
|------|----|------|------|-----|--------|---------|--------|-------------|--------------|------|------|
| S1 | stat | score5 | True | True | True | -0.003327 | -0.002864 | 4→0 | 22.83→30 | 100 | APPLY |
| S2 | markov | score5 | True | True | True | -0.017677 | -0.005144 | 4→0 | 18.33→30 | 100 | APPLY |
| S3 | review | score5 | True | True | True | 2e-05 | -0.013669 | 4→0 | 17.64→30 | 100 | APPLY |

## 3) S4 합동 스모크

ok=True · peek=0 · modes={'stat': 'score5', 'markov': 'score5', 'review': 'score5'}

## 4) 캐시 재생성

{"skipped": false, "applied": ["stat", "markov", "review"], "ok": 600, "fail": 0}

## 5) HARD DB

{"draws_max": 1236, "pred_1237": 0, "ledger": {"stat": 3000}}

## 6) 롤백

`REPACK_HYENA_MODE_BY_BRAIN` 세 뇌를 `""` 로.

## 7) 뇌별 스킬 (같은 조립 · 다른 점수축)

조립은 공통 `score5`(복사 0 · 상위 30점을 6개씩 5장). 훔치는 번호는 뇌 점수축이 가른다.

| 뇌 | 점수축 | hint | 게이트 Δprefer | 게이트 Δprize | 5장 union |
|----|--------|------|----------------|---------------|-----------|
| stat | 빈도+원장 EMA (0.25/0.35/0.40) | miss_pattern 52 | **−0.003327** | **−0.002864** | 22.83→**30** |
| markov | prefer 가중 (0.65/0.15/0.20) | crowd_prefer | **−0.017677** | **−0.005144** | 18.33→**30** |
| review | prize 가중 (0.65/0.15/0.20) | crowd_prize | **+0.000020** | **−0.013669** | 17.64→**30** |

ISO=0.005. 인기↑·prize↑ 아님. 복사 4→**0**. 5장 변경 100/100. pool 1~10 HARD 불변.

keep1은 예비. 1차 도구가 `copy_on==0` 을 `or 9`로 잘못 읽어 HOLD_NO_DESIGN 냈다. 재측정에서 copy_on **0** 확인 후 score5 확정.

## 8) 금지 확인

타깃 적중 미입력. 원장 stat **3000** 불변. 1237 아님. 동결 토큰 미수정. hits/등수 클레임 금지.
캐시 1037–1236 3뇌 **600**/0. 롤백=`REPACK_HYENA_MODE_BY_BRAIN` 전부 `""`.

