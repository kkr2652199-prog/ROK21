# K-PAST-LEARN-AUDIT-DIMS — 과거학습 뇌 전구간 정밀감사 · 차원 진단 · 외부 AI 자문

- 날짜: 2026-08-08 · 범위: **ROK21 / testlotto / 과거학습(stat)** only
- 정책: READ-ONLY 감사. 코드·가중·DB 변경 없음.
- 동반 진단: `reports/20260808_KPAST_LEARN_EV_RELABEL.md` (신규 실증)
- 근거 원본: `docs/benchmarks/20260808_KPAST_LEARN_AUDIT_DIMS.json`

---

## 0. 세 줄 요약

1. **놓친 작업**: 진짜 미실행으로 남은 것은 6건뿐이다. 나머지 20건 이상은 이미 기각·HOLD가 정당하게 확정된 것이며 되살릴 근거가 없다.
2. **차원(1·2·3차)**: 차원을 올리면 힘이 생기지 않고 **표본이 말라붙는다**. 3차원은 셀당 관측 1.74건이라 순위화 자체가 불가능하다. 우리 앱의 pair/triple NOISE 판정은 실패가 아니라 **공정한 추첨에서 나올 수밖에 없는 결과**였다.
3. **실제로 힘이 남은 차원은 번호 상호작용이 아니라 「조합특성 → 당첨자수」**였고, 이번에 그 축에서 **처음으로 유의한 신호**를 얻었다 (family-wise p=0.0004).

---

## 1. 정밀감사 — 진짜 놓친 작업

### 1-A. 아직 실행되지 않았고 지금도 실행 가능한 것 (6건)

| # | 항목 | 무엇이 빠졌나 | 근거 파일 | 비용 |
|---|---|---|---|---|
| 1 | **`cycle_gap_boost` 단독 A/B** | v2 엔진에 코드로 살아있으나(gap≥1.5×평균 → ×1.25, ≥1.2× → ×1.15) **단독 벤치가 한 번도 없다**. `detail_tune_later` 목록에만 등재 | `engine.py` L122–131 · `past_learn.py` L259–264 | 낮음 |
| 2 | **끝수·합·span bin 단위 null 대비** | 끝수는 "≥1 중복 = 0.7798" 같은 이진 비율만 있고 **분포 bin 전체가 없다**. KRARE 자체가 `taxonomy_gaps`에 MISSING으로 적어둠 | `20260805_KRARE_MEASURE_1_1235.json` | 낮음 |
| 3 | **PMI 카탈로그 → 발권 backtest** | 990쌍 PMI(top 0.421)를 만들어놓고 가중 w3=0, **예측력 측정을 안 했다** | `20260805_KSIGNAL_TAXONOMY_V1.json` | 중간 |
| 4 | **cold-free replace 의 live 경로 검증** | 진단에서 Δge3 **+0.03**이 나왔는데 `_k_cover_diag.py`는 진단 전용이고 **live `predict_sets` 경로에서 재확인이 없다**. QUOTA-D가 정확히 이 함정(sim≠live)에서 FAIL했다 | `20260805_KCOVER_DIAG.json` · `20260805_KQUOTA_D_WIRE.json` | 중간 |
| 5 | **stat 전용 repack (hy_p45_r123)** | ablation에서 stat +0.04였으나 WIRE는 fusion `signal_pool`에만 들어갔고 **stat solo repack 코드는 그대로** | `20260804_KREPACK_HYBRID_survey.json` · `…_WIRE.json` | 중간 |
| 6 | **seed 민감도 full-range 재측정** | stat ge3 range **0.14** (0.09–0.23)를 **n=100**에서 측정했다. 이 수치가 이후 모든 "개선/악화" 판단의 잡음 하한인데 표본이 가장 작다 | `20260805_KSTAT_SEED_DIAG.json` | 낮음 |

> **6번이 가장 중요하다.** 잡음 폭이 0.14인데 우리는 0.0008 차이로 셀을 골라왔다. 잡음 하한을 정확히 모르면 이후 어떤 튜닝도 판정할 수 없다.

### 1-B. 아이디어로만 남고 도구화되지 않은 것

| 아이디어 | 출처 | 상태 |
|---|---|---|
| high_lift ≥2 앵커 투표 → 다음회 커버 전수 | `20260808_KSTAT_NUM_ASSOC_1234.json` ideas | 도구 없음 |
| 1233↓ 번호별 next-top15 카탈로그 전수 | `tools/_k_stat_num_next_freq.py` L213 | anchor 1234 단건만 |
| pos_ema 가중 repack / top-2 pool union | `20260804_KREPACK_DECOMPOSE_survey.json` P0 | 권고만 |
| rank1 skip · rank3–5 mix ablation | 동 P1 | 권고만 |
| freq 25%→35% · overlap bonus | 동 P2 | 권고만 |
| B/C 패턴 → pool 재점수 | `20260805_KPATTERN_OWN_V1.json` | 당첨회차 내부 측정만 |

단, ASSOC 계열(위 1·2번)은 전수 n=1035에서 **NOISE_LIKE**(mean_lift 0.998 vs null 1.002)로 닫혔다. 도구를 더 만들 근거는 약하다.

### 1-C. 되살리면 안 되는 것 (기각이 정당함)

| 항목 | 왜 닫혔나 |
|---|---|
| decay long 0.005→0.01 | DETAIL-KEEP · YT-BENCH · SCORE-RULE **3중 기각** |
| SOFT_WEIGHT / SOFT_CONF_CAP 스윕 | 15셀 전부 ge3 동일 = 발권 불변 |
| ASSOC soft ON | 전수 NOISE_LIKE |
| transition_v1 fusion ON | FUSION-N200 **ROLLBACK** (Δge3 = 0.000) |
| quota B/C/D (stat 슬롯↑) | QUOTA-D live **FAIL** (0.10) |
| PAIR_COVER / STRUCTURE_COVER wire | stat ge3 각 −0.01 / −0.02 |
| neighbor kNN | hit≥3 0.23 < random 0.311 |
| LSTM · 시퀀스 예측 | 독립시행 · YT-BENCH 기각 |

### 1-D. 문서 모순 — 정리 필요

| 위치 | 문제 | 무엇이 SSOT인가 |
|---|---|---|
| `STATUS_LATEST.md` §5 | "transition STEP4 wire **ON**"으로 남아있음 | 실제는 FUSION-N200 ROLLBACK → **OFF**. §5가 드리프트 |
| `KTRANSITION_FULL.json` | `brain_replace_verdict="즉시착수"` | STEP3 DESIGN_HOLD + FUSION ROLLBACK이 최종 |
| `KNEW_ENGINE_STAT_A1` vs `TUNE_ENGINE` | 전자 Δge3=0, 후자 solo n50 ge3=0.28 | 경로·윈도우·seed가 다름. **v2 자체의 uplift 근거로 인용하면 안 됨** |
| `engine.py ENGINE_V2=False` vs live True | `_use_engine_v2()`가 past_learn을 따르는 이중 스위치 | 의도된 설계. 주석 보강 권고 |

---

## 2. 차원(1차·2차·3차) 진단 — 정직한 답

### 2-A. 차원이 올라가면 무엇이 일어나는가

1235회차 기준 **셀당 관측수**를 직접 계산했다.

| 차원 | 공간 크기 | 총 관측 | **셀당 관측** | 판정 |
|---|---:|---:|---:|---|
| 1차 (번호) | 45 | 7,410 | **164.7** | 균등성 검정 가능 |
| 2차 (쌍) | 990 | 18,525 | **18.7** | 큰 효과만 겨우 |
| 3차 (삼중) | 14,190 | 24,700 | **1.74** | **순위화 불가** |
| 4차 | 148,995 | 18,525 | 0.12 | 불가 |
| 6차 (조합) | 8,145,060 | 1,235 | 0.0002 | 사실상 전부 미관측 |

> 차원은 정보를 **더 주지 않고** 표본을 나눈다. 3차원에서 "리프트 상위 삼중항"을 뽑는 것은 관측 1~2건을 순위화하는 것이며, 우리 `KASSOC_RULE_DIAG` 결과(3gram max Δ=0.667 < 시뮬 p95=0.867)는 정확히 그 잡음 폭을 보여준 것이다.

즉 **pair/triple NOISE 판정은 우리 측정의 실패가 아니라 성공**이다. 공정한 6/45 비복원 추출이라면 반드시 그렇게 나와야 한다.

### 2-B. 차원별 커버리지 현황

| 차원 | 이미 측정 | 남은 gap |
|---|---|---|
| 0차 | mean 1.715 · ge3 pin 0.135 · null 0.1137 · full-WF 0.1184 | — |
| 1차 | 빈도 χ²=28.74 · 볼 균등성 p≈0.90 · gap/미출 · EMA hot/cold(NOISE) · decay(NO_SKILL) · 끝수 ≥1중복 0.7798 | 끝수 **bin 분포** |
| 2차 | 쌍 연관(NOISE) · PMI 카탈로그 · carry P(≥1)=0.6135 vs null 0.5994 · carry→next lift(NOISE) · 유사회차 sim_k2 2.172 vs 2.0 · 자리×값 | PMI **예측 backtest** · 자리 postmortem **skill** |
| 3차 이상 | 합(138.25±30.73) · 홀짝 · zone · 연번 ge1 0.5174 · AP · 희귀템플릿 213 · 5장 커버 · 다중필터 AND 0.202 vs null 0.210 | 합/span/연번 **bin 단위** · AC value |
| meta | seed(n=100) · quota · fusion · 평가 프로토콜 · PBO=0 | seed **full-range** |

### 2-C. 실제로 힘이 남아있던 차원

번호 사이의 차원이 아니라 **「조합 특성 → 소비자 선택 → 당첨자 수」** 차원이다.

이 차원의 결정적 장점: 개별 조합(810만 개)을 추정하지 않고, **수백만 조합이 공유하는 저차원 특성**(31 이하 개수, 합, 연번쌍, 끝수중복)으로 압축한다. 그래서 1131회차로도 검정력이 생긴다.

그리고 추첨 조합은 판매량·시기와 **무작위로 배정**되므로, 이 연관은 분포가정 없이 permutation으로 정확검정된다.

**결과 (동반 보고서 참조): family-wise p = 0.0004 로 인기 편향이 실증되었다.** 20년 넘게 축적된 이 앱의 어떤 축보다 강한 신호다. 단, 그것은 **당첨확률이 아니라 분할 인원**에 관한 신호다.

---

## 3. 외부 AI 자문 — 우리 결론에 대한 반대신문

다른 모델(GPT 계열)에 SCORE-RULE-DIAG 전체 수치를 넘기고 적대적 검토를 요청했다. 채택한 지적:

### 3-A. 문구를 좁혀야 한다 (채택)

기존: "recency 가중은 정보가 아니라 자해다."

수정: **"검증한 시간창·혼합비·gap boost 계열에서는** recency 가중이 out-of-sample 예측 정보를 추가하지 못했고, 균등분포에서 멀어지는 정도에 비례해 log-score를 악화시켰다."

이유: 15셀 그리드 밖의 함수족까지 배제한 것은 아니다. "정보가 전혀 없다"는 과장이다.

### 3-B. 통계적 지적과 대응

| 지적 | 우리 상태 | 대응 |
|---|---|---|
| 점수 표준오차는 번호 3,000개가 아니라 **회차 500개 단위**로 계산해야 한다 (한 회차 6개는 독립 아님) | SCORE-RULE의 paired 통계는 이미 **회차 단위 시계열 n=500** | 문제 없음. 보고서에 단위를 명시하도록 보강 |
| 셀 선택 절차 전체를 감싼 **nested walk-forward** 필요 | 미충족 | 이후 어떤 그리드 탐색도 nested 구조로만 판정하도록 규칙화 |
| 차이값에 **block bootstrap CI / permutation p** 를 붙여야 한다 | 미충족 | 다음 튜닝 시 필수 항목으로 승격 |
| χ² p=0.90은 "장기 주변빈도 균등"만 뜻하고 조건부 전이구조 부재를 뜻하지 않는다 | 우리 해석이 과했음 | 문구 수정. 다만 OOS 점수 결과가 그 빈틈을 실질적으로 메움 |
| gap boost는 가설이 아니라 **확률질량 임의 재배치** = 도박사 오류 | 정확 | `cycle_gap_boost` 단독 A/B의 사전 기대값은 "손해" |
| Suetens 등 해외 연구를 한국 인기도 데이터로 대체하면 안 된다. hot/overdue를 자동으로 "비인기"라 라벨링 금지 | **정확한 지적** | 이번에 **한국 데이터로 직접 측정**했고, 실제로 hot1y는 예상과 달리 **인기 방향**으로 나왔다 |

마지막 항목이 결정적이다. 자문의 경고가 없었다면 문헌만 근거로 `overdue`를 "EV 레버"로 재라벨링했을 것이고, 실측은 그것을 지지하지 않는다.

### 3-C. 다음에 저지를 가능성이 가장 높은 실수 5개

1. **null을 이겼다는 착각** — seed 간 ge3 폭이 0.14인데 0.0008 차이를 신호로 읽는 것
2. **튜닝과 검증의 경계 붕괴** — 지표를 보고 바꾼 뒤 같은 구간을 "검증"이라 부르는 것
3. **best-of-5를 확률 개선으로 오해** — 5장 상관을 조작한 효과를 예측력으로 착각
4. **사후 지급액을 설명변수로 넣기** — 1인당 지급액은 당첨자수의 역함수 → collider
5. **시대별 z를 보고 유리한 구간만 골라 재적합** — 사후선택

> 5번은 이번 EV 진단에서 즉시 유혹이 된다. 저번호·저합 효과는 구간3·4에서 강하고 구간2에서 0이다. "최근 구간만 쓰자"는 사후선택이므로 금지했고, 대신 **회차 1236 이후 전향적 홀드아웃**만 인정하도록 보고서에 못박았다.

---

## 4. EV 진단 결과 (요약 · 상세는 동반 보고서)

| 항목 | 결과 |
|---|---|
| 판정 | **SELECTION_YES_TAGS_NO_AXIS_CANDIDATE** |
| 전역 검정 | max\|z\|=4.381 · family-wise p=**0.0004** |
| 유의 축 | `sum_z` (β=−0.0575) · `n_le22` (β=+0.0463) — 사실상 **동일한 저번호·저합 선호 축** (상관 −0.876) |
| 과거학습 태그 | `hot1y` +0.0243 = **인기 방향**(4개 시대 전부) · `overdue` −0.0539 = 비인기 방향이나 z=−0.96 무의미 |
| soft 태그 EV 재정의 | **지지 안 됨** |
| 발권 반영 | **금지** (w=0 · 전향적 검증 전) |

**해석**: 과거학습 뇌가 지금 쓰는 태그축(미출·핫·콜드)은 적중축에서도(SCORE-RULE), EV축에서도 근거가 없다. 반면 뇌에 **아예 없는 축**(저번호·저합 회피)이 유일하게 유의했다.

---

## 5. 권고 우선순위

| 순위 | 할 일 | 이유 |
|---|---|---|
| 1 | **seed 민감도 full-range 재측정** | 잡음 하한을 모르면 이후 모든 판정이 무의미 (감사 1-A #6) |
| 2 | **회차 1236+ 전향적 EV 로그** (개입 없음) | 유일하게 살아있는 신호의 정직한 검증 |
| 3 | `cycle_gap_boost` 단독 A/B | 유일하게 측정 안 된 live 파라미터. 사전 기대는 "손해" |
| 4 | STATUS §5 transition ON 표기 수정 | 문서 드리프트 (감사 1-D) |
| 5 | 끝수·합·span bin 단위 null 대비 | 저비용 · taxonomy 공백 메움 |

**하지 말 것**: soft 태그 가중 상향 · decay 재탐색 · transition/quota 되살리기 · 이번 EV 결과로 발권 즉시 변경.

---

## 6. 참여 도구·에이전트

| 산출물 | 경로 |
|---|---|
| EV 진단 도구 (신규) | `tools/_k_past_learn_ev_relabel_diag.py` |
| EV 벤치 원본 | `docs/benchmarks/20260808_KPAST_LEARN_EV_RELABEL.json` |
| EV 보고서 | `reports/20260808_KPAST_LEARN_EV_RELABEL.md` |
| 본 감사 벤치 원본 | `docs/benchmarks/20260808_KPAST_LEARN_AUDIT_DIMS.json` |
