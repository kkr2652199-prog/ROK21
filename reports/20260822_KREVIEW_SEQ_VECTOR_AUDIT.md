# K-REVIEW-SEQ-VECTOR-AUDIT (2026-08-22)

- **판정:** `AUDIT_NOTES` · READ-ONLY · APPLY **없음**
- 시각: 2026-08-22T15:22:40+09:00
- 형: 금액뇌 벡터 결과물 정밀분석 · 버그 · 아이디어
- 근거: `20260822_KREVIEW_SEQ_VECTOR_AUDIT.json` · 선행 `20260822_KREVIEW_SEQ_DISTRIBUTE.json`

## 벡터가 뭔가

정식 `backtest_runs` 등수표가 아니다. 금액뇌 `expand_pool` 소진분포를
캐시 **200**/200 (1037–1236)에 쓴 것 + 게이트 n100 기하.

**1차 캐시(이 턴 초)는 구경로였다.** 게이트 `finally`가 메모리 플래그를 False로
되돌린 채 리필해서 source=`cover_r3_jaccard`·skill5합 **21.385**. 이번 확인에서
발견 → 플래그 ON으로 200장 재기록. 아래 숫자는 **재기록 후**.

## 캐시 전수 (review 1037–1236)

- rows 200 · size≠10 **0** · bad6(중복/길이) **0**
- skill5합 평균 **30.0** · 정확히30 **200**/200
- #1∩#2 평균 **0.0** · 0인회 **200**
- 1~5에서 2장이상 번호 평균 **0.0** · 0인회 **200**
- 1~7합 **40.24** · 10장합 **41.425** · #8~10∩(1~7) **16.815**
- 모니터 set1적중 **0.85** · max **2.125** (우열아님)
- roles `{'skill_native': 1000, 'cover_r3': 600, 'shape_r2': 400}`
- sources `{'skill_native': 1000, 'review_seq_deplete': 1000}`

## 라이브 대조 (빈 learner · seed42 · 1137/1186/1236)

- 캐시=라이브 pool **True**
- 발권 predict_sets(5)=pool #1~#5 **True**

- 1137: cache=live `True` · ticket=pool1-5 `True` peek `False` set1 live `[8, 13, 28, 30, 34, 40]`
- 1186: cache=live `True` · ticket=pool1-5 `True` peek `False` set1 live `[5, 7, 11, 25, 34, 35]`
- 1236: cache=live `True` · ticket=pool1-5 `True` peek `False` set1 live `[6, 7, 11, 24, 26, 42]`

## 1237 캐시 (신규예측 없음)

- `{'ok': True, 'n': 10, 'geom': {'n': 10, 'union5': 30, 'union7': 30, 'union10': 30, 's1_s2': 0, 'multi5': 0, 'wrap_n': 3, 'wrap_overlap7': 16, 'bad6': 0, 'roles': []}, 'set1': [15, 18, 27, 34, 37, 40], 'sources': ['frontload_score', 'frontload_score', 'frontload_score', 'frontload_score', 'frontload_score', 'frontload_rest', 'frontload_rest', 'frontload_rest', 'frontload_rest', 'frontload_rest'], 'looks_seq': True, 'looks_frontload': True}`

## 버그

- **B-REFILL-STALE** · P1(조치함) · 첫 리필이 구경로. 캐시 재기록 후 1137/1186/1236 캐시=라이브·발권5=pool1~5.
- **B-RESET-WRAP** · P2 · #8~10이 1~7과 평균 16.815개 겹침. 45소진 후 풀 리셋(2바퀴). cover/shape 라벨이지만 실제는 재추출.
- **B-1237-STALE** · P3 · 1237 캐시 source=`frontload_*` · #1=`[15,18,27,34,37,40]`. 소진벡터 아님. 신규예측 안 함.

## 아이디어 (APPLY 아님 · 형 선택)

1. 리셋 금지: 45개만 7장+나머지3은 패딩 없이 멈추거나, 8~10은 빈칸/원본 미사용. 2바퀴 겹침 제거.
2. tier1 탈락 시 뽑은 6개를 풀에 되돌리거나, 필터를 소진 후에만 적용. 구멍(union5<30) 방지.
3. 6~10 라벨 cover/shape는 허위. seq면 전부 skill_seq 또는 #6=2순위 엔진장으로 문서화.
4. 발권5와 pool1~5가 같으면(이번 실측) 몰아주기 score5와 #1 정렬은 별 GO.
5. 1237은 예측 재실행 없이 캐시만 소진재조립할지 형이 결정.

- HARD DB MAX `1237` · pred_1237 **0** · 원장 stat `3000`
- 우열금지 · 1237 신규예측 없음

## 파일

- `20260822_KREVIEW_SEQ_VECTOR_AUDIT.json` · `20260822_KREVIEW_SEQ_VECTOR_AUDIT.md`
- `tools/_k_review_seq_vector_audit.py`
