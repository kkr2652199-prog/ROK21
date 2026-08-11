# K-NEXT-UPPER-HIT-LIST — 현황·잔여·상위적중 순서리스트 (+문헌/GH)

시각: 2026-08-12 KST · HEAD≈`12b2a6e` · **양산前** · **1237아님** · ge3/등수 **성적클레임 금지**

형 지시: (1) 현재까지 진행 (2) 남은 패치 (3) 4·5등 관측 후 상위적중↑ 방법 (4) 단계 리스트  
각 항목에 인터넷·유튜브·GH 비교·배울 스킬 (5) 순서대로 · **①부터 정밀 완료**

---

## A) 지금 어디까지 왔나 (실측)

| 구간 | 상태 | 요지 |
|------|------|------|
| ①~⑤ | **DONE** | 합동smoke · pool잔여HOLD · BTv4 · learn refill · K-G ACTIVE |
| ⑥~⑦ | **DONE** | K-I fallback WIRE · post-refill smoke |
| ⑧~⑩ | **DONE** | quota min_each=1 · 재스모크 · K-C STALE_CLOSE |
| ⑪~⑫ | **DONE** | 발권quota VERIFY · BTv5 REBUILT · refill_v2 (quota s1/m1/r3) |
| 잠금 knobs | live | markovBLEND**0.55** · reviewBLEND**0.85** · W_CROWD**0.90** · SCORE cand_B · HINT52 · HINT_W**0.15** · union · oversample m**5**/r3/s3 · min_each**1** |

BTv5 모니터(클레임 아님): mean_hits**2.5** · tiers **r1~r3=0 / r4=4 / r5=42**  
근거: `docs/benchmarks/20260812_KFORCE_POOL_BACKTEST_100_v5.json`

---

## B) 남은 패치·열린 과제 (우선순위 필터)

| 구분 | ID | 상태 | 이 리스트에서의 취급 |
|------|-----|------|----------------------|
| 예측축 잔여 | K-POOL-JACCARD | HOLD | 재스윕 후순위 |
| 지표 | K-O / K-P | OPEN | **상위등수 단독최적화 폐기 후보** 유지 |
| 동결 | K-E random.choices | OPEN | **형 승인 전 금지** |
| 문서만 | K-L / K-12 | OPEN | 형만 |
| 인프라 | K-05 tracked DB | OPEN | 형 승인 전 untrack 금지 |
| 4군 | K-00 | OPEN | MAP 전 수정금지 |
| **신규(본턴①)** | K-TIER45-SOURCE | **AUDIT_OK** | 상위적중 착시 해소 · 다음② 근거 |

---

## C) 핵심 정정 — “4등 나왔다”의 의미

① `K-TIER45-SOURCE-AUDIT` 실측:

| 항목 | 값 |
|------|-----|
| BT r4 회차 | 1150, 1160, 1208, 1214 |
| pool≥4 기여 | review×2 · markov×1 |
| **발권5장 재실행 best≥4** | **0 / 4** |
| pool≥4인데 repack<4 | **2 / 100** |
| pool≥3인데 repack<3 | **17 / 100** |

결론:
1. BTv5 등수는 **pool10+repack5×3뇌** 최고치(장수 많음) → **양산 발권 5장 4등과 동일하지 않음**.
2. “상위 적중↑”를 **BT 등수 숫자만으로 쫓으면 착시**.
3. 코드로 손볼 1순위 후보는 **발권경로 지표 병기** + (게이트 후) **pool→repack 보존 / 5장 포트폴리오 다양성**.
4. 문헌상 **P(1등)↑는 불가능에 가깝고**, 배울 축은 **몫EV(비인기)** · **부분당첨 커버(겹침↓)** · **정직한 null**.

근거: `docs/benchmarks/20260812_KTIER45_SOURCE_AUDIT.json`

---

## D) 상위적중 목표 재정의 (이 리스트의 성공 정의)

| 허용 목표 | 금지 목표 |
|-----------|-----------|
| prefer / prize 축 게이트 | ge3·1~3등 **성적클레임** |
| 발권5장 mean/hits **모니터+병기** | BT pool경로 등수만으로 APPLY |
| 5장 간 겹침↓(부분당첨 커버) | LSTM/hot·cold = P(win)↑ |
| review 몫EV 강화(비인기) | buy-the-pot · 전수커버 wire |
| pool 좋은세트 보존(선별신호 있을 때만) | `_get_draws_before` / boost상한 / random.choices 동결 위반 |

---

## E) 순서 리스트 (1건씩 · 각 항목에 외부조사)

### ① K-TIER45-SOURCE-AUDIT — **본턴 완료 · AUDIT_OK**
- **할일:** r4/r5 출처·발권경로 재현·pool/repack 손실 실측
- **문헌/유튜브/GH:** Numberphile·“AI로 로또”류는 **예측력 과장** → 기각. seiv40/lottery-lab·루마니아 ML논문 = **null 수렴** 배울 점. 우리 감사는 그 정직 프로세스와 동형.
- **배울 스킬:** “지표가 어느 경로(장수)에서 왔는지”를 먼저 분해.
- **산출:** `reports/20260812_KTIER45_SOURCE_AUDIT.md` · 벤치 JSON · 도구 `_k_tier45_source_audit.py`

### ② K-BT-ISSUE-PATH-METRIC — **본턴 완료 · METRIC_OK**
- **할일:** 강제BT에 **발권5장 best_hits/tier** 병기. UI/보고서가 pool경로 등수를 양산성적처럼 쓰지 못하게.
- **실측(1137~1236 n100):** pool경로 mean**2.5** / ≥3 **46** / ≥4 **4** · **발권5장** mean**1.64** / ≥3 **12** / ≥4 **0**(r5만12)
- **문헌/GH:** Hai4320·keno_optimizer 계열의 **정직한 백테 프레임**(경로·베이스라인 명시). 유튜브 “이번 주 예상번호”는 비교대상 아님.
- **배울 스킬:** dual metric · path-labeled evaluation.
- **산출:** `docs/benchmarks/20260812_KBT_ISSUE_PATH_METRIC.json` · `reports/20260812_KBT_ISSUE_PATH_METRIC.md` · `tools/_k_bt_issue_path_metric.py`

### ③ K-POST-REFILL-JOINT-SMOKE — 측정
- **할일:** refill_v2(w≈review 주도) 후 prefer/prize/hit 합동 smoke 재확인
- **문헌:** Thaler&Ziemba — 성공축=EV/선호정렬, hit↑ 아님
- **배울 스킬:** 가중 바뀐 뒤 **축 게이트 재검증** (드리프트 감시)
- **완료조건:** SMOKE_OK/FAIL · |Δ|기준 기존 게이트

### ④ K-REPACK-PRESERVE-PROBE — 게이트(APPLY 전)
- **할일:** pool≥3/4 손실 17/2건 구간에서 assemble/slots/union 후보 소형 스윕. **선별 신호가 없으면 HOLD**(K-REPACK-SELECT-DIAG와 정합).
- **문헌/GH:** Moffitt&Ziemba 커버링 = **자본·전수** 전제 → 5장에 과장금지. 배울 점=“놓친 조합”은 **포트폴리오 설계** 문제.
- **배울 스킬:** ablation · 선택보정(R38) · “손실≠버그” 구분
- **완료조건:** 게이트 JSON · APPLY는 prefer/prize 비악화 + 발권경로 모니터만

### ⑤ K-TICKET-COVER-LITE — 5장 겹침↓
- **할일:** 발권5장 Jaccard/번호커버 스윕(dedup 이후). 부분등수(3·4) **기회 분산**이 목표(P(win)↑ 비주장).
- **문헌:** covering design · “buy the pot”는 **기각**. Baker–Lee 조합선호 = shape 프록시 장기검토.
- **배울 스킬:** 소규모 포트폴리오 다양성 지표
- **완료조건:** 게이트 PASS 시에만 상수 APPLY

### ⑥ K-REVIEW-EV-DEEPEN — 금액뇌
- **할일:** prize 축 잔여(BLEND/W_CROWD/shape 프록시). Stern&Cover급은 **pick marginal 없으면 금지**.
- **문헌/유튜브:** Ziemba ARFE2023 · Significance2012 conscious selection. YT “로또 통계로 1등” = **기각**.
- **배울 스킬:** P(win)불변·몫EV 언어 고정
- **완료조건:** prize |Δ|≥문턱 · prefer iso0

### ⑦ K-MARKOV-PREFER-ALIGN — 선호뇌
- **할일:** prefer 축 잔여(구조사전 vs crowd). Wang JdDM 생일대 정합 유지.
- **GH 기각:** opaque score / “LSTM 예측” 레포
- **배울 스킬:** 역할 분리(선호≠금액≠숙제)
- **완료조건:** prefer 게이트 · prize iso0

### ⑧ K-STAT-HOMEWORK-QUALITY — 과거학습 (후순위)
- **할일:** pool 품질·hint weeks 잔여. K-Q 균등·K-A mean서열 주의(K-O).
- **문헌/GH:** ML-on-lottery null · past_learn EV 재라벨 기각 이력 존중
- **배울 스킬:** 숙제 명분 ≠ 적중P
- **완료조건:** hit 모니터 + prefer/prize 비악화

### ✕ 금지 슬롯 (리스트에 넣지 않음)
- 1등/2등/3등 **직접 최적화** · ge3 성적게이트 · LSTM/Transformer 예측 wire  
- buy-the-pot · Stern-Cover without pick_freq · 동결3종 · 1237 양산 취급 · 원본 kweon 쓰기

---

## F) 외부조사 한 장 요약 (이번 턴 재확인)

| 출처 | 채택 | 기각 |
|------|------|------|
| Thaler&Ziemba JEP1988 · Ziemba ARFE2023 | 몫EV·비인기 | hit↑=실력 |
| Moffitt&Ziemba covering | 다양성 아이디어만 | 5장 buy-the-pot |
| Stern&Cover / maxent | 설계 이상 | 데이터 없으면 wire |
| seiv40/lottery-lab · RO ML study · keno_optimizer 정직 README | null·누수방지·백테프레임 | “예측 성공” 마케팅 |
| YT 예상번호·hot/cold | — | 전원 성적근거 부적합 |

선행 상세: `reports/20260810_KNEXT_ROUTE_LIT_GITHUB_SURVEY.md`

---

## G) 진행 상태

| # | ID | 판정 |
|---|-----|------|
| ① | K-TIER45-SOURCE-AUDIT | **AUDIT_OK** (본턴) |
| ② | K-BT-ISSUE-PATH-METRIC | **METRIC_OK** (본턴) |
| ③~⑧ | (위) | **대기** · NEXT=③ |

---

## 경로
- `reports/20260812_KNEXT_UPPER_HIT_LIST.md`
- `reports/20260812_KTIER45_SOURCE_AUDIT.md`
- `docs/benchmarks/20260812_KTIER45_SOURCE_AUDIT.json`
- `tools/_k_tier45_source_audit.py`
