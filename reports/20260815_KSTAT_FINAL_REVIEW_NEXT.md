# K-STAT-FINAL-REVIEW-NEXT — 과거학습 뇌 튜닝 종료점검 + 다음 리스트

시각: 2026-08-15 · **DOC_OK** · 범위=**stat만** · ge3/등수 성적클레임 금지 · 1237아님

근거: S1~S5 벤치 JSON · `20260815_KSTAT_ONLY_CONSUME_RESTORE` · 본턴 DB 실측 · FINDINGS K-A/K-E/K-O

---

## 0) 한 줄 답

**이번 캠페인 리스트(S1~S5)의 튜닝은 끝났다.**  
「엔진이 완벽하다 / 더 손댈 곳이 없다」는 뜻이 **아니다**.

- 끝난 것: 과거학습 **10세트·몰아주기 패치 리스트** (S2는 HOLD로 끝).
- 안 끝난 것: S2 대체 설계, 원장 상태 맞춤, 발권 경로, FINDINGS 오래된 수치.
- 성적(1·2·3등, 적중 mean)으로 ‘좋아졌다’고 쓰면 **안 된다** (K-O · 이론 1장 0.80).

---

## 1) 라이브 플래그 (코드)

| 항목 | 값 | 의미 |
|------|-----|------|
| 숙제 소비 | `ROLE_TIER_LEARN_BRAINS={stat}` | 형 정정 후 과거학습만 |
| 1~5 학습고리 | `STAT_POOL_LEARN_WIRE=True` | 배선 ON · 노브 HOLD (prize 미달) |
| cover 선택 | `COVER_SELECT_MODE=outside_union` | S1 APPLY |
| shape 코어 | `SHAPE_CORE_MODE=set1` | S2 HOLD · 합의코어 꺼짐 |
| 몰아주기 쿼터 | `REPACK_ROLE_QUOTA_WIRE=True` | S3 APPLY · stat만 |
| 5번째 장 | `REPACK_RECOMBINE_MODE=complement` | S4 APPLY · stat만 |
| COVER_MIN_HITS | 3 | 표 빔 패치 |
| HINT 창 | miss_pattern **52** | K-STAT-PATTERN-TUNE APPLY |
| SCORE | (0.25, 0.35, 0.40) | cand_B 잠금 |
| 동결 | `random.choices` · `_get_draws_before` · boost 상한 | 미수정 |

---

## 2) 버그 검토

### 2-1. HARD 버그 (컨닝·크기·보너스입력)

S5 200회: peek **0** · 예외 **0** · pool10/repack5 결손 **0** · pred1237 **0**.  
S2 T-NB1 (shape 시그니처에 bonus/actual 없음) **통과**.  
프로세스 감사(이전 stat 200): 역할 5+3+2 불일치 **0** · 번호 무효 **0**.

**지금 코드 경로에 열린 HARD 버그는 파일상 없음.**

### 2-2. 상태 갭 (버그에 가깝음 · 튜닝 아님)

본턴 DB 실측:

| 표 | 값 |
|----|-----|
| ledger | **markov 3000만** (stat 0) |
| role_homework | stat/markov/review 각 400 |
| skill_homework | 3뇌 각 200 |
| brain_review | **0** |
| lotto_predictions | **0** · 1237=0 |
| draws MAX | **1236** |

원인: markov 200회가 **리셋 후** 원장을 다시 채움. 그 뒤 소비만 `{stat}`로 되돌림.  
그래서 라이브는 과거학습이 숙제를 읽지만, **cover 숙제의 재료(stat 원장)가 비어 있다.**  
S5 때의 stat 원장은 그 리셋으로 지워졌다.

→ 다음 1건 후보: 리셋+stat만 200회 **원장 맞춤** (새 knob 없음).

### 2-3. SOFT (엔진 버그 아님)

- UI `backtest_runs` **0** (강제백테표 ≠ 원장). 이전 감사 SOFT.
- 발권 0. 이번 워킹은 예측 산출물만.
- FINDINGS **K-A** (stat mean 0.760): **오래된 수치**. S5 모니터 1~5 mean_all **0.83**. 패치 근거로 쓰지 말 것. K-O와 충돌(mean 서열 금지).
- FINDINGS **K-E** seed 미고정: **동결**. 형 승인 전 수정 금지.

### 2-4. HOLD로 남은 설계 (버그 아님)

| ID | 왜 안 켰나 |
|----|------------|
| S2 shape consensus | prefer Δ **+0.012169** ≥ 0.005 인기↑ |
| STAT_POOL_LEARN 노브 | prize Δ **-0.00037** ≪ 0.005 |
| L11c WIN_1Y | 전후보 \|Δhit\|≪0.005 |
| L9 slots/cap | 신호 임계 미달 |
| HINT_WEIGHT 0.15 | 재탕 HOLD |
| ASSOC | NOISE_LIKE · OFF |

---

## 3) 엔진 ‘성능’ (게이트만 · 등수 클레임 금지)

게이트 = prefer/prize **비악화** (Δ < 0.005, 음수 OK).

| 단계 | 판정 | prefer Δ | prize Δ | 설계 모니터 |
|------|------|----------|---------|-------------|
| S1 cover-union | **APPLY** | −0.005541 | −0.002831 | union10 30.05→31.72 |
| S2 shape 합의 | **HOLD** | **+0.012169** | −0.00959 | J 0.71→0.29 |
| S3 역할쿼터 | **APPLY** | +0.00049 | −0.000328 | cover0장 49→0 |
| S4 보완조합 | **APPLY** | −0.003394 | −0.002431 | J 0.29→0 · union 17.7→22.7 |
| S5 BT200 | **PASS** | (기록) 0.009443 | 0.004396 | union10 **31.55** · 재조합J **0** |

S5 모니터(클레임 금지): 고유 1·2·3등 **0** · 4등 **12** · 5등 **55**.  
cover mean_all **0.74** (패치전 200회 0.8183) — S1이 1~5 밖 번호를 고른 결과. **적중이 떨어져서 롤백할 이유가 아님.**

이론 1장 0.80 근처면 ‘실력 향상’이 아니다 (K-O).

---

## 4) 다음 할 일 리스트 (과거학습만)

| # | ID | 종류 | 할 일 | 하지 말 것 |
|---|-----|------|--------|------------|
| **1** | **K-STAT-LEDGER-REALIGN-BT200** | 상태복구 | 리셋 후 **stat만** 1037~1236 n200. 원장·숙제를 라이브 소비와 맞춤. HARD peek/1~5/1237=0 | 새 knob · 등수클레임 |
| 2 | K-STAT-PROCESS-AUDIT-S5LIVE | READ | S1/S3/S4 source 라벨·역할 5+3+2·숙제 n_pos 재실측 | 코드 APPLY |
| 3 | K-A-STALE-DOC | DOC | FINDINGS K-A 수치를 ‘구표본’으로 표시. 패치 금지 | mean으로 엔진 서열 |
| 4 | K-STAT-SHAPE-CORE-V2 | 설계(보류) | S2와 **다른** 코어. 인기↑ 없이 클론 해제. 새 아이디어 있을 때만 | consensus 재탕 · 보너스입력 |
| 5 | 잠금 재탕 | 금지 | — | L9 cap · WIN_1Y · HINT 0.15 · ASSOC · S2 consensus |
| 6 | 발권5 성적 | 범위밖 | 쿼터는 3뇌. **형 지시 시** | 지금 발권 mean으로 APPLY |
| 7 | 합동 smoke | 범위밖 | 3뇌 마지막. **형 지시 시** | 지금 3뇌 동시튜닝 |
| 8 | markov/review 숙제 | 범위밖 | 코드는 보존. **형 지시 시** | 자동 재점화 |

권고 다음 1건 = **#1 원장 맞춤**. 튜닝이 아니라 정리.

---

## 5) 금지

- 4등 12 / 5등 55 / cover mean 0.74 를 성적 향상·악화로 쓰지 않음.
- 1237 예측/양산 아님.
- 원본 kweon 미접촉. DB 파일 커밋 금지.
