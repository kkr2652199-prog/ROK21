# K-STAT-COMBO-ANNOTATE-SPEC

시각: 2026-08-15T15:33:42+09:00 · **SPEC_OK** · READ-ONLY · APPLY **없음** · 1237아님
목적=COOCCUR 다음 A. stat 전용 궁합 **세트 annotate** SPEC. `prefer_table` 미수정. 플래그 OFF.

권고=**HOLD**. 세트 annotate는 부착점·널이 있다. 켜면 pick이 바뀌어 발권 구성이 변한다. markov pair_boost와 같은 쌍통계를 반대로 쓰면 쿼터 혼합 시 상쇄. K-U 쌍층은 널. 플래그 OFF 유지. APPLY 없음.

HARD=통과. peek=0 · pred_1237=0 · MAX=1236 · n_sets=1000.

## 0) SPEC (코드에 아직 없음)

| 항 | 값 |
|----|-----|
| 플래그 | `STAT_COMBO_ANNOTATE_WIRE` 기본 **False** |
| 뇌 | stat만 |
| 끼움점 | `app/testlotto/brains/stat_brain/predict.py: tagged[] 이후 · diversity.pick 직전` |
| 점수 | 세트 15쌍의 window100 pair_freq 합 + consecutive_pairs. pick_score에만 가산(별 GO). |
| 이웃 정의 | 같은회 |a-b|=1 만 연번. 다음회 n±1은 markov 영역·이번 SPEC 제외. |
| 켜면 게이트 | prefer/prize 비악화 · peek0 · stat 캐시 외 불변 |

금지: crowd_signal.prefer_table / prize_table 수정 · stat number_scores / engine.generate 가중 · markov annotate_prefer / blend_weights / pair_boost 복사 · lotto4 lotto_cooccur_* 연결 · random.choices 라인

## 1) 널 (조합 기하)

| 항 | 값 |
|----|-----|
| P(특정쌍) | 0.015152 = C(43,4)/C(45,6) |
| E[연번쌍 수] | 0.6667 |
| E[쌍빈도] window100 | 1.5152 |
| E[세트 15쌍 합] | 22.7273 |

## 2) 지금 stat skill 베이스라인 (annotate OFF · walk-forward)

| 항 | 값 |
|----|-----|
| n | 1000 |
| mean 연번쌍 | 0.557 (Δ -0.1097 vs 널 0.6667) |
| mean 쌍빈도합 | 27.454 (Δ +4.7267 vs 널 22.7273) |

Δ는 축 편차. **누가 낫다·예측신호 금지**. 상위 동반쌍을 번호선택 근거로 쓰지 않음 (K-U).

## 3) 왜 APPLY 안 하나

- annotate ON이면 `diversity.pick` 순서가 바뀌어 **발권 구성 변경**. 표 수정은 아니지만 라이브 출력이 바뀜.
- markov는 이미 `pair_boost`로 같은 `lotto_draws` 쌍을 씀. stat이 반대로 피하면 쿼터 혼합 시 상쇄.
- 다음회 이웃은 널과 같음(DISCUSS 0.7757≈0.80). 이번 SPEC 제외.
- 동결 `random.choices` 미수정. prefer_table 오염 금지.

## 4) 판정

SPEC_OK · HOLD. 플래그 신설·APPLY 없음. 숙제ON·covering휠·S2·1237 없음.
다음 APPLY는 형 1건.

## 5) 금지 확인

DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.

