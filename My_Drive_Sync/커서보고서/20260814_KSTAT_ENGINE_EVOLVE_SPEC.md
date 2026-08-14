# K-STAT-ENGINE-EVOLVE-SPEC — 과거학습 뇌 10세트·몰아주기 정밀 + 패치리스트

시각: 2026-08-14T21:49:57+09:00 · **SPEC_OK** · 범위=**stat만** · ge3/등수 **성적클레임 금지** · **1237아님**  
근거: `docs/benchmarks/20260814_KSTAT_ENGINE_EVOLVE_SPEC.json`  
실측창: 패치엔진 리셋+200 (`K-STAT-PATCHED-BT200`) 1037~1236 · ledger stat **3000** · cache stat **200**  
선행: LIST_V3 역할슬롯 · `K-ROLE-LEARN-TUNE-AUDIT` · `K-REPACK-COPY-WHICH-SET` · `K-NEXT-ROUTE-LIT-GITHUB-SURVEY` · `K-TIER-ROLE-SLOTS-ANALYSIS`

형 지시: 4·5등 배출은 보였으니, 6세트부터의 3등·2등 엔진이 도는지 / 몰아주기가 분산 번호를 어떻게 조합하는지 정밀분석 → 문헌·1티어 벤치 → **과거학습 뇌 + 그 뇌 몰아주기만** 단계 패치.

---

## 0) 한 줄 결론

**6~8번은 3등 학습기가 아니고, 9~10번은 2등 학습기가 아니다.**  
둘 다 1~5번 **같은 과거학습 엔진의 파생물**이다. 3등·2등 확률을 올리는 목적함수는 코드에 없다.

**몰아주기도 ‘10세트에 흩어진 번호를 섞어 새 조합을 만든다’가 아니다.**  
5장 중 **4장은 10세트 중 점수한 장을 통째 복사**(비율 **0.80**), 나머지 **1장은 점수 상위 6번호를 한 덩어리로 자른 것**이다.

4등 고유 **10** · 5등 고유 **53** 은 모니터다. 그중 4등은 **skill 6 + shape 4** (cover **0**). 5등은 skill **29** · shape **11** · cover **12** · 몰아주기 전용 **1**. 즉 저등수는 거의 **1~5번 가족**(shape는 1번 세트의 한 칸 변형)에서 나왔다.

다음 진화는 등수P 튜닝이 아니라 **커버 생성기 / 형상 코어 / 몰아주기 조합 규칙**을 문헌의 covering 의미에 맞게 바꾸는 것이다. 게이트는 계속 prefer/prize. 적중 mean·ge3로 APPLY 금지.

---

## 1) 지금 엔진이 실제로 하는 일 (코드)

| 칸 | 역할 이름 | 실제 생성 | 자체 학습기 | 3등/2등/1등 목적함수 |
|----|-----------|-----------|-------------|----------------------|
| 1~5 | `skill_native` | `predict_sets` pass0 그대로 | **있음** (miss_pattern52 · CUTOFF overdue/ending/carry 상한동결 · skill_homework) | 없음 (숙제=패턴) |
| 6~8 | `cover_r3` | **같은** `predict_sets`를 **다른 시드**로 5장 더 뽑고, 1~5와 Jaccard 낮은 3장. 표가 있으면 3맞 번호 가중. 부족 시 skill 1칸 교체 | 원장 3맞 복습표만 (생성기 자체 없음) | **없음** |
| 9~10 | `shape_r2` | **1번 세트에서 번호 1개 빼고** 6번째를 넣음. 표가 있으면 과거 보너스·5맞 상위 (타깃 보너스 금지) | 과거 보너스 표만 | **없음** (보너스 맞춤 하드옵트 PASS) |
| 몰아주기 1~5 | `focus_r1` | 위치EMA 상위 **2장 통째** + 세트점수 보충 → **cap 4장 복사** + 점수순 1~45를 6개씩 자른 **1장** | 원장 번호/칸 EMA blend 0.5 | **없음** (6맞 최적화 없음) |

코드: `app/testlotto/role_slots.py` `build_cover_r3_sets` · `build_shape_r2_sets` · `signal_pool.assemble_signal_union` · `repack_sets`.

상수 실측: `ROLE_TIER_LEARN` stat만 · `COVER_MIN_HITS=3` · `STAT_POOL_LEARN_WIRE=True` · `ASSEMBLE_MODE=signal_union` · slots**2** · cap**4** · SCORE stat `(0.25, 0.35, 0.40)` · `STRUCTURE_COVER_WIRE=False`.

### 몰아주기 5번째 장의 조합 방식 (오해 포인트)

```text
number_scores(n) = 0.25·hint(miss_pattern) + 0.35·(10세트 안 빈도) + 0.40·(learn EMA + 위치부스트)
repack_sets = 점수순 1..45 를 앞에서부터 6개씩 자르기
cap=4 이면 재조합 1장 = 점수 1~6등 번호 한 장
```

10세트에 흩어진 번호를 **교차로 뽑아 새 6장을 조립**하지 않는다. 높은 점수 번호 6개를 그냥 한 티켓에 넣는다. 그게 ‘1등 지향 압축’의 실제 구현이다.

---

## 2) 패치 직후 200회 실측 (모니터 · 클레임 금지)

창 1037~1236 · 뇌=stat · n_ok 200 · peek 0.

### 2-1. 칸별 적중 mean (이론 1장 0.80)

| 칸 | 장수 | mean hits | hits≥3 장수(모니터) | ≥4 | ≥5 |
|----|------|-----------|---------------------|----|----|
| 1~5 skill | 1000 | **0.83** | 35 | 6 | 0 |
| 6~8 cover | 600 | 0.8183 | 12 | **0** | 0 |
| 9~10 shape | 400 | 0.8575 | 15 | 4 | 0 |
| 몰아주기 | 1000 | 0.819 | 29 | 6 | 0 |

cover는 skill보다 mean이 낮고 **4맞이 0**이다. ‘3등 엔진’이면 5맞이 늘어야 하는데 5맞도 0. 역할 이름이 엔진이 아니다.

### 2-2. 고유조합 등수 (같은 번호 중복 제거)

| 등수 | 고유 | 역할 분해 (첫 등장 역할) |
|------|------|--------------------------|
| 1·2·3등 | **0** | — |
| 4등 | **10** | skill **6** · shape **4** · cover **0** · 몰아주기전용 0 |
| 5등 | **53** | skill **29** · shape **11** · cover **12** · 몰아주기전용 **1** |

shape 4등이 4건인 이유: 9~10은 **1번 세트와 번호 5개 공유**(아래 Jaccard **0.7143=5/7**). 1번이 4맞이면 변형도 4맞 근처로 따라간다. 독립 2등 엔진이 아니다.

### 2-3. 번호 기하 (캐시 200회 평균)

| 지표 | 값 | 해석 |
|------|----|------|
| 10세트 번호 union | **29.755** / 45 | 10장이 번호 30개쯤만 씀 |
| 1~5 union | **22.715** | 스킬 5장이 이미 23개 |
| 몰아주기 5 union | **16.585** | 복사+상위6 → **더 좁아짐** (압축) |
| cover vs skill Jaccard | **0.1059** | 의도(안 겹치기)는 약하게 동작 |
| skill 5장 서로 Jaccard | **0.0806** | 스킬끼리 이미 cover보다 덜 겹침 |
| skill+cover 8장 서로 | **0.0941** | cover를 넣어도 분산이 **나빠짐** |
| shape vs 1번 세트 Jaccard | **0.7143** | **5공유/7합 = 한 칸 변형 확정** |

핵심 결함: cover 후보는 **같은 `predict_sets` 재호출**이라 번호 구름이 1~5와 같다. Jaccard 최저를 골라도 skill 내부 다양성(0.0806)을 이기지 못한다. 문헌의 covering(먼저 번호 풀을 정하고 그 안에서 조합을 깐다)과 **구조가 다르다**.

### 2-4. 몰아주기가 복사하는 원본 (200회×5장=1000)

복사 **800** / 재조합 **200** = 비율 **0.80** (cap4 설계와 일치 · 버그 아님).

| pool 세트 | 역할 | 복사 횟수 |
|-----------|------|-----------|
| 1 | skill | **163** |
| 2 | skill | 67 |
| 3 | skill | 47 |
| 4 | skill | 42 |
| 5 | skill | 83 |
| 6~8 | cover | 67+62+52=**181** |
| 9 | shape | 101 |
| 10 | shape | 116 |

역할 합: skill **402**(50.3%) · shape **217**(27.1% · 장수비 20%보다 **과복사**) · cover **181**(22.6% · 장수비 30%보다 **과소**).

9·10이 많이 복사되는 이유: 1번과 거의 같은 장 → 번호점수가 1번과 비슷 → cap4에 같이 들어감. 몰아주기가 1등 압축을 하려다 **같은 가족을 두 장 넣는** 결과가 된다.

---

## 3) 문헌 · 1티어 개방자 — 우리 구조와 맞는 것만

선행 서베이 `20260810_KNEXT_ROUTE_LIT_GITHUB-SURVEY` + 역할분석 `KTIER_ROLE_SLOTS_ANALYSIS` + 이번 재검색. **복붙 금지 · 프로세스만.**

### 3-1. 채택 (이번 패치 리스트에 넣음)

| 출처 | 요지 | 우리 매핑 |
|------|------|-----------|
| Covering design / lottery wheeling (La Jolla, 약식 휠) | 먼저 **번호 풀**을 고르고, 그 풀의 조합을 적은 장수로 **부분보장**. P(잭팟)↑ 아님 | 6~8은 ‘같은 엔진 재샘플’이 아니라 **1~5 union 위(또는 밖)를 덮는 조합기**여야 함 |
| LuckyPicks “Smart Coverage” (greedy, 예산 고정) | 진짜 C(v,k,t) 보장이 장수 부족이면 **3·4맞 커버리지를 greedy 최대화** | 우리 장수=3(cover)+1(재조합). 보장표 불가 → **greedy union / 밖 번호** |
| Moffitt–Ziemba / Thaler–Ziemba | 다양성은 **몫·커버** 도구. P(win) 불변 | 게이트=prefer/prize 유지. 등수 횟수로 APPLY 금지 |
| Stern–Cover 1989 | 이상 EV는 **pick marginal** 필요 | 동행복권에 판매비율 없음 → **흉내 금지 유지** |
| Hai4320 / 정직 GH | null·split-half·예측 고백 | 이번도 null mean 0.80 병기 · 성적 과장 금지 |
| 우리 `structure_cover.py` | 홀짝·합·존 질량 커버 · **WIRE=False** | 축이 **번호 covering과 다름**. 이번 S1에 섞지 않음 (별 GO) |

### 3-2. 기각 (다시 열지 않음)

- 「3등 전용 슬롯이면 3등P↑」 — LIST_V3 PASS · K-P · 초기하.
- 보너스 맞춰 2등 하드옵트 — 타깃 보너스 미지.
- 10장으로 1등 covering 보장 — 6/45 전수 8,145,060. 10장 불가.
- 풀 휠: 번호 10개면 C(10,6)=210장. 우리 cover는 3장.
- Lotterycodex ‘자주 나오는 템플릿=예측’ — 조합 질량 서술일 뿐 다음회 예측 아님. `STRUCTURE_COVER` HOLD와 동형.
- LSTM/유튜브 필터 · WIN_1Y/HINT0.15 재탕 · boost 상한 상향.
- K-PAIR-COVER 전수 페어 커버 부활.
- markov/review 이번 범위 밖.

---

## 4) 진화 방향 (stat 엔진 + stat 몰아주기만)

목표를 등수 횟수가 아니라 **생성 규칙**으로 둔다.

1. **cover**: 같은 구름 재샘플 → **skill union을 기준으로 덮거나 밖으로 나가기** (문헌 covering).
2. **shape**: 1번 클론(J=0.714) → **1~5 합의 코어 5 + 가변1** (2등 ‘형태’만, 보너스 예측 아님).
3. **몰아주기 복사**: shape 과복사 억제 · cover 최소 1장 보존 (압축이 커버를 지우지 않게).
4. **몰아주기 5번째**: 상위6 절단 → **이미 복사된 4장에 없는 고점수 번호를 섞는 보완 조합**.

성공 정의(APPLY): prefer/prize 비악화(기존 iso 0.005) · 설계 모니터= union10↑, shape-set1 Jaccard↓, 몰아주기 copy에서 cover 비율↑, 재조합이 복사 4장과 Jaccard↓.  
실패 정의: ge3/4등 횟수로 이겼다고 쓰기 · 동결 3종 손대기 · 1237 양산.

---

## 5) 패치 리스트 (1건씩 · 롤백 플래그)

> 강제 3뇌 합동·markov 배선은 **이 리스트 밖**. 각 단계 후 스모크 1234~1236. 200회는 S1~S4 묶음 뒤 S5 한 번(중간 모니터는 도구로).

### S0 K-STAT-ENGINE-EVOLVE-SPEC — **DOC_OK (본턴)**
- 본 문서 · JSON · 실측. 코드 APPLY 없음.

### S1 K-STAT-COVER-OUTSIDE-UNION — **다음 1건**
- 대상: `build_cover_r3_sets` (stat 소비 시에만).
- 변경: 후보 순서를 `min Jaccard vs skill` → **`skill union에 없는 번호 수 최대` (동점이면 8장 union 최대, 그다음 Jaccard)**. 숙제표는 tie-break만.
- 유지: 타깃 정답 미사용 · 2nd `predict_sets` 후보 풀 · 1~5 불변.
- 롤백: `COVER_SELECT_MODE="jaccard"` 기본 복귀.
- 게이트: prefer/prize iso. 모니터: union10, cover-vs-skill Jaccard, cover ge4(클레임금지).
- 금지: 등수P↑ 문장.

### S2 K-STAT-SHAPE-CONSENSUS-CORE
- 대상: `build_shape_r2_sets`.
- 변경: core5 = **1~5에서 2회 이상 나온 번호 상위**, 부족 시 1번 세트 보충. 6번째는 기존 보너스 숙제표.
- 모니터: shape vs set1 Jaccard (지금 0.7143에서 내려가는지).
- 롤백: `SHAPE_CORE_MODE="set1"`.
- 보너스 인자 시그니처 금지 유지 (T-NB1).

### S3 K-STAT-REPACK-ROLE-QUOTA
- 대상: `assemble_signal_union` **stat만** (`POOL_UNION_*_BY_BRAIN` 또는 역할쿼터).
- 변경: cap4 복사 때 **cover 최소 1 · shape 최대 1 · skill 최소 1**. 나머지 1은 신호상위.
- 모니터: copy_by_role (지금 shape 27% / cover 23%).
- 롤백: 쿼터 off → 현행 점수순.
- L9 slots/cap 전뇌 스윕 재탕 아님. **stat 역할쿼터만**.

### S4 K-STAT-REPACK-MIX-RECOMBINE
- 대상: `repack_sets` 경로, **stat 5번째 장만**.
- 변경: 복사된 4장의 번호 합을 빼고, 남은 고점수에서 6개 (보완). 부족하면 기존 상위6으로 폴백.
- 이게 형이 말한 ‘분산된 번호를 조합’의 **실제 진화점**.
- 롤백: `REPACK_RECOMBINE_MODE="top6"`.
- 게이트: prefer/prize. 모니터: 재조합 vs 복사4 Jaccard, union_repack (지금 16.585).

### S5 K-STAT-ENGINE-EVOLVE-BT200
- 리셋 후 stat만 1037~1236. HARD peek/size/1237=0. 등수·mean=모니터. prize/prefer 기록.

동결 유지: `random.choices` · `_get_draws_before` · boost 상한. DB 파일 커밋 금지. kweon 미접촉.

---

## 6) 하지 않을 것 (명시)

- 이번 턴 코드 APPLY 없음 (스펙만).
- 4등 10 / 5등 53 을 ‘엔진이 좋아졌다’로 쓰지 않음.
- cover에 3등 손실함수, shape에 보너스 맞춤 학습 넣지 않음.
- 몰아주기 cap을 성적 때문에 5→3 같은 전뇌 스윕 (L9 HOLD).

---

## 7) 다음

**S1 K-STAT-COVER-OUTSIDE-UNION** 1건. 1237아님.
