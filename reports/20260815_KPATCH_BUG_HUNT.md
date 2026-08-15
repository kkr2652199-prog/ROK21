# K-PATCH-BUG-HUNT

시각: 2026-08-15T17:15:52+09:00 · **BUGHUNT_OK** · READ-ONLY · APPLY **없음** · 1237아님
목적=켠 패치(특히 몰아주기 score5)에서 오동작만 실측. 성적 아님.

HARD=통과. MAX=1236 · pred_1237=0 · 원장 {'stat': 3000}.

## 0) 한 줄

찾은 것: B1 UI캐시 몰아주기 ≠ 라이브 build_pool_and_repack · B3 S3역할쿼터·S4보완 플래그 ON인데 score5가 우회

## 1) 캐시 200회 센서스 (1037–1236)

| 뇌 | n | copy/5 | 무효 | 5장중복 | union | assemble |
|----|---|--------|------|---------|-------|----------|
| stat | 200 | 0.0 | 0 | 0 | 30.0 | {'hyena_score5': 1000} |
| markov | 200 | 0.0 | 0 | 0 | 30.0 | {'hyena_score5': 1000} |
| review | 200 | 0.0 | 0 | 0 | 30.0 | {'hyena_score5': 1000} |

## 2) 캐시 vs 라이브 (샘플 7회×3뇌)

cache≠live 몰아주기 **19**/21 · cache≠live pool **0** · cold(리필경로)≠live **19** · cache≠cold **0**.

| 회 | 뇌 | cache=live몰아 | cache=cold | cold=live | cache=live pool |
|----|----|----------------|------------|-----------|-----------------|
| 1037 | stat | False | True | False | True |
| 1037 | markov | False | True | False | True |
| 1037 | review | False | True | False | True |
| 1100 | stat | False | True | False | True |
| 1100 | markov | False | True | False | True |
| 1100 | review | False | True | False | True |
| 1137 | stat | True | True | True | True |
| 1137 | markov | False | True | False | True |
| 1137 | review | False | True | False | True |
| 1216 | stat | False | True | False | True |
| 1216 | markov | False | True | False | True |
| 1216 | review | False | True | False | True |
| 1234 | stat | False | True | False | True |
| 1234 | markov | False | True | False | True |
| 1234 | review | False | True | False | True |
| 1235 | stat | False | True | False | True |
| 1235 | markov | False | True | False | True |
| 1235 | review | False | True | False | True |
| 1236 | stat | True | True | True | True |
| 1236 | markov | False | True | False | True |
| 1236 | review | False | True | False | True |

## 3) 버그 목록

### B1 · P1 · UI캐시 몰아주기 ≠ 라이브 build_pool_and_repack

- 근거: sample 7회×3뇌 중 cache≠live_repack 19 · cold≠live 19 · cache≠cold 0
- 원인: 캐시 refill이 RollingSignalLearner() 빈 스냅샷. 라이브/발권은 warm_learner_to_draw(200). UI는 캐시 우선.

### B3 · P3 · S3역할쿼터·S4보완 플래그 ON인데 score5가 우회

- 근거: hyena=score5가 assemble_signal_union보다 먼저 return. quota/complement 미호출.
- 원인: 죽은 배선. 런타임 오동작은 아님. 문서/튜닝 혼선.

## 4) 라이브 플래그

{"HYENA": {"stat": "score5", "markov": "score5", "review": "score5"}, "S3_QUOTA": true, "S3_BRAINS": ["stat"], "S4_MODE": "complement", "S4_BRAINS": ["stat"], "ASSEMBLE_MODE": "signal_union", "COVER": "outside_union", "SHAPE": "set1", "ROLE_LEARN": ["stat"], "LEDGER": true}

## 5) 논의 (패치 제안 아님 · APPLY 없음)

- B1이 실측되면: 당첨확인 UI(캐시)와 발권(build_pool_and_repack) 몰아주기가 갈라진다. 고치려면 캐시를 warm 경로로 다시 쓰거나, 발권도 캐시를 읽게.
- B3은 버그라기보다 **죽은 스위치**. S3/S4를 끄거나 문서에 ‘score5가 우선’을 박제.
- 타깃 적중 입력·동결토큰은 이번 헌트에서 안 건드림.

## 6) 판정

BUGHUNT_OK. 코드/DB 쓰기 없음. 1237 아님.

