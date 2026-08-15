# K-REVIEW-WSTRUCT-UP

시각: 2026-08-15T15:14:12+09:00 · **APPLY_OK** · review만 · 1237아님 · hits 클레임 금지
후보=W_CROWD 0.90→0.80 · W_STRUCT 0.10→0.20 (합1). markov 0.90/0.10 불변. seed=42 · 1137–1236 n100.

APPLY=함.

## 1) 측정

| 설정 | n | peek | fw_prize | hi32 | end089 |
|------|---|------|----------|------|--------|
| base 0.90/0.10 | 100 | 0 | -0.122235 | 1.977 | 1.816 |
| cand 0.80/0.20 | 100 | 0 | -0.120724 | 1.994 | 1.815 |
| Δ | | | 0.001511 | 0.017 | -0.001 |

fw_prize=top15 번호의 first_winners편차(음수=군중 비인기). hi32=세트당 고번호 개수(Ziemba).

## 2) 게이트

| 항 | 값 |
|----|-----|
| peek | 0/0 |
| hi32 Δ>0 | True (0.017) |
| fw Δ≤+0.005 | True (0.001511) |
| markov 노브 | 불변 |

## 3) 판정

게이트 통과 → 노브 APPLY + review 캐시만 1037–1236 재생성(200/200).
stat fp `1030e5b6341dc581` · markov fp `cb8968f3ce9b4dff` **불변**. review fp `21d7d3d861d99dae`→`a505859e840ad332`.
evolve_log review 200행 재채점(타뇌 미접촉). 원장 미기록.
hi32 Δ=+0.017은 작음. 성적 아님. 롤백=`review W_CROWD=0.90 / W_STRUCT=0.10` + 백업 캐시.

## 4) 금지 확인

숙제ON·covering·S2·apply_learn_boost복사·1237 없음. 동결 토큰 미수정.
