# K-REVIEW-ASSOC-CROWD-NETCHECK (2026-08-27)

- **판정:** `HOLD_NO_WIRE` · S0 READ-ONLY · APPLY **없음** · 핫쌍 가중 **없음** · 몰아주기 **미접촉**
- 시각: 2026-08-27T04:45:31+09:00
- 형: 6번 한 장 핫쌍 과다 패스. net 확인 후 배선 여부. 회차 유사도 아이디어 **이번 제외**.
- 근거: `docs/benchmarks/20260827_KREVIEW_ASSOC_CROWD_NETCHECK.json`
- 측정: `tools/_k_review_assoc_crowd_netcheck.py` · seed 42 · review만

## 정의 (수치 고정)

- **crowd_pair_count** = 본번호 6개의 **15쌍** 중, as_of **이전** 당첨 본번호쌍 빈도 상위 **N**위에 든 개수.
- 핫쌍 집합 = `_get_draws_before(target)` 의 본번호 6개만으로 쌍 빈도. **보너스 쌍 미사용**.
- peek = `max(draws_before.draw_no) < target`. 전역 assoc 집계표로 핫쌍을 만들지 **않음**(회차 이후 누수가 됨).
- 주정의: **N=20 · K=3** (한 장에 핫쌍 3개 이상 = 몰림).
- 거의없음 기준: 출력 장 중 `crowd ≥ K` 비율 **< 0.02**.
- **net** = 이미 1·2·3번(reasonable / shape flatten / rare_pass)을 통과한 **review 출력 장** 중 crowd≥K 인 장 수·비율. 1·2·3이 이미 자른 장은 출력에 없으므로, 출력의 crowd≥K = 순수 추가 패스 후보.

널(균등 990쌍) 참고: E[crowd | N=20] ≈ 15×20/990 ≈ **0.303**. 실측 핫쌍은 빈도가 치우쳐 평균이 이보다 클 수 있음(성적 아님).

## S0 1137–1236 n100 (READ-ONLY)

| HARD | 값 |
|------|-----|
| peek_fail | **0** |
| n_ok | **100** |
| n_sets | **1000** (회차당 review 10장) |
| size_bad | 0 |
| bonus_in | **0** (본번호 6개만) |
| n_errors | 0 |
| pred_1237 | **0** |
| pred_1239 | **0** |
| DB MAX | **1238** |
| assoc 행 | **1237** |
| elapsed | **27.7**s |

### review 출력 crowd_pair_count 분포

| N(핫상위) | n | 평균 | hist 0 / 1 / 2 / 3 / 4 | p(≥2) | p(≥3) | p(≥4) | p(≥5) |
|-----------|---|------|-------------------------|-------|-------|-------|-------|
| 10 | 1000 | 0.16 | 851 / 139 / 9 / 1 / 0 | 0.01 | 0.001 | 0.0 | 0.0 |
| **20** | **1000** | **0.387** | **677 / 266 / 51 / 5 / 1** | 0.057 | **0.006** | 0.001 | 0.0 |
| 30 | 1000 | 0.548 | 581 / 311 / 90 / 15 / 3 | 0.108 | 0.018 | 0.003 | 0.0 |

주정의 **N=20 K=3**: crowd≥3 인 장 **6**/1000 = **0.006** (hist 3=5 + 4=1).

### 당첨 본번호 6 (모니터 · 예측재료 아님)

같은 as_of 핫집합으로 그 회 당첨 6개를 잰 값. 적중 클레임 아님.

| N | n | 평균 | hist | p(≥2) | p(≥3) |
|---|---|------|------|-------|-------|
| 10 | 100 | 0.14 | 0:86 · 1:14 | 0.0 | 0.0 |
| 20 | 100 | 0.33 | 0:73 · 1:22 · 2:4 · 3:1 | 0.05 | 0.01 |
| 30 | 100 | 0.48 | 0:62 · 1:30 · 2:6 · 3:2 | 0.08 | 0.02 |

## S1 판정

- **`HOLD_NO_WIRE`**
- 사유: 주정의 N=20 K=3 **net_n=6 · p=0.006** (거의없음 기준 0.02). 1·2·3 통과 뒤에 남는 몰림 장이 **거의 없음**. 라이브 배선 금지. `REVIEW_ASSOC_KB_READ=True` **읽기만** 유지.
- 감도: N=30 K=3 도 p=0.018 < 0.02. N=20 K=2 는 p=0.057(후보 가능)이나 **주정의는 K=3**. K=2로 바꾸려면 형 별 GO.
- S2 **skipped** (배선 분기 아님).
- `REVIEW_ASSOC_CROWD_PASS_WIRE` **신설하지 않음**. 엔진·stat/markov·7번 WIRE **불변**.

## 이번 턴에 하지 않음

- 핫쌍 가중(인기쏠림) — 금지. 패스 방향만 검토했고 패스도 안 켬.
- 보너스 연결을 핫쌍·예측에 사용 — 금지.
- 회차 유사도(직전 닮은 과거→다음) — 이번 오더 제외.
- 몰아주기 · 전체조합 생성공식 · `random.choices` · kweon — 미접촉.
- 1237/1239 예측 · 자동화 배선 · APPLY.

## 플래그 (실측)

- `REVIEW_ASSOC_KB_READ=True` (유지)
- `PREDICT_USE_BONUS_LINKS=False` (유지)
- `REVIEW_CONSEC_PASS_WIRE=False` (유지)
- `REVIEW_SHAPE_KB_WEIGHT_WIRE` — 이 측정 중 라이브 ON 상태(4번). 6번 패스와 무관.

## 롤백

- 읽기까지 되돌릴 때: `REVIEW_ASSOC_KB_READ=False`
- CROWD_PASS 롤백 키: **해당 없음**(플래그 없음)

## 파일

- `docs/benchmarks/20260827_KREVIEW_ASSOC_CROWD_NETCHECK.json`
- `reports/20260827_KREVIEW_ASSOC_CROWD_NETCHECK.md`
- `tools/_k_review_assoc_crowd_netcheck.py`
