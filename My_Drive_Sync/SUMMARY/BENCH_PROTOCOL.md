# BENCH_PROTOCOL — 테스트로또 성적 비교 프로토콜 (K-B 고정)

📅 제정: 2026-07-27 · 개정: 2026-07-29(K-BENCH-05·03 baseline·tier·pipeline) · SSOT=`kkr2652199-prog/ROK21`  
📌 충돌 시 이 문서가 성적 수치의 우선순위.

---

## 정당성) 뇌 정당성 = 전제 실증 (K-T)

- 확률이 조합불변 → ‘선택’ 비용 0. 적중률로 뇌를 서열화하는 질문은 K-O/K-P로 **답 불가**.
- **정당성 정의:** 해당 뇌가 가정하는 **전제(의존·간격·형태·균형 등)가 데이터에서 실증되는가**.
- 판정 라벨: **실증 / 기각 / 미정의**. 적중 mean·best만으로 정당성 선언 금지.
- 이론분포와 **일치**해도 형태·균형 제약은 실패가 아님(비균등 이론 = 명분 있는 제약).
- **명분 SSOT:** `WARRANT.md` (뇌 7개 라벨·근거·p·출처ID). 코드 미러 `brains/warrant.py`.
- **산출 정합성(K-W/K-Y):** 당첨 draws(A) vs 산출/점수후 top(B) vs 균등(C). A근접=정합 · C근접=무해 · 양쪽원격=편향경보.
- **`실증` 라벨:** 전제 실증 ∧ 모듈 구현 검증. draws만 이론부합이면 `전제실증·구현미검증` (K-Y).
- **(K-AA)** K-W A거리는 **게이트가 아니라 관측지표**. A(1234회)는 C와 통계적 구분 불가(K-Q·K-T·K-U)이므로 90슬롯 거리 변동은 노이즈; **상수 채택 기준 = 조합론 참값 일치 단일축**.

---

## 0) 상수·표본 벽 (K-O / K-P) — 뒤집으려면 새 실측

| 명제 | 수치 | 함의 |
|------|------|------|
| E[세트 적중] | **0.8** = 6×(6/45) | 세트 **mean만으로 뇌 서열화 불가** (K-O) |
| P(≥3 적중) ge3_rate | ≈ **0.1137** | 이론 null-check · survey `NULL_GE3` SSOT · **K-BENCH-05** |
| P(정확히 5개) | ≈ **2.873×10⁻⁵** | 1245×100세트 기대 5적중 ≈ **3.58≈3.5건** (K-P) |
| 세트 상위등수 | 기대 건수 ≪ 잡음 | **학습신호 부재** → 최적화 축으로 부적합 |
| 볼 표본(실측) | draws **1234** · 본+보너스 슬롯 **8638** | 세트단위 대비 수량 우위 → **검정 층위=볼** |

따라서: mean/best는 **null-check 전용 또는 폐기 후보**. 신규 후보는 번호 로그우도·calibration·Brier·볼빈도 적합(형 승인 후, K-S).

---

## 1) 성적 SSOT (과도기 · 세트 mean)

| 항목 | 값 |
|------|-----|
| 소스 | `testlotto_brain_review.predicted_sets_json` |
| 집계 | **전세트 mean** (회차×뇌당 5세트 전부) |
| 창 | **최근 100회차** 고정 (현재 실측 기준 1135–1234) |
| 적중 | 본번호 교집합 크기 (보너스는 mean에 미포함 · 별도 표기) |
| 제한 | **서열화·승자선언에 단독 사용 금지** (K-O). null 병기 필수(K-S) |

볼단위 지표가 형 승인·구현되면 이 섹션을 갱신한다.

---

## 2) 운영 / UI (성적 비교 금지)

| 항목 | 값 |
|------|-----|
| 소스 | `lotto_predictions` |
| 용도 | 클릭 캐시 · UI 표시 |
| 금지 | **뇌 실력·벤치 비교에 사용 금지** |
| 알려진 갭 | **1149–1179** (31회) — 2026-07-25 재기록 구멍 |

---

## 3) 학습 입력 (K-N HOLD)

| 항목 | 값 |
|------|-----|
| 경로 | `walkforward.review_single_draw` → `apply_feedback(best)` |
| 지표 | 회차당 **best 세트** `matched_count` |
| 저장 | `testlotto_brain_learn_state.recent_avg_match` (창 없는 누적) |
| 상태 | **HOLD** — best는 분산 산물(원인확정). 교체 설계는 형 승인 |

---

## 4) best 인용 규칙

- best / best-of-N / `recent_avg_match`를 쓸 때 **천장 ≈2.27** 병기 필수.
- best를 mean 대체 실력 지표로 쓰지 말 것 (K-08 · K-N · K-O).

---

## 5) 표 작성 금지

- **표본이 다른 두 수치**를 **같은 표에 나란히** 두지 말 것.
- **null 없는 성적표 출력 금지** (K-S).
- 부득이 언급 시 출처·회차수·집계(전세트/best/볼)를 칸마다 명시.

---

## 6) 이론 baseline 표 행 (K-BENCH-05 · 필수)

모든 벤치 리포트·survey 마크다운의 **SUMMARY 표**(또는 동등한 1행 요약 표)에는 아래 **baseline 행을 반드시 포함**한다. 템플릿=`reports/BENCH_REPORT_TEMPLATE.md`.

| label | mean | ge3_rate | pin | Δge3 | p | 비고 |
|-------|------|----------|-----|------|---|------|
| **theory_baseline** | **0.8000** | **0.1137** | — | — | — | E[match]=6×6/45 · ge3=null |
| (후보) | … | … | (있으면) | vs baseline/pin | binom | pipeline·집계 명시 |

- **mean baseline:** random 6/45 기대 적중수 **E[match] ≈ 0.8** (= 6×6/45). K-O와 동일.
- **ge3 baseline:** P(본번호 교집합 ≥3) 이론값 ≈ **0.1137** — survey 스크립트 `NULL_GE3`·JSON `null_ge3`와 동일 SSOT.
- **pin 행:** WIRE-V2 등 고정 기준선이 있으면 별도 행(예: ge3=0.1447). baseline과 pin **둘 다** 병기.
- **Δ·p:** 후보는 baseline(또는 pin) 대비 Δge3·이항검정 p를 같은 표에 기록. baseline 없는 표 **출력 금지**.

---

## 7) 파이프라인 분리·등수(tier) 집계 (K-BENCH-03 · 필수)

### 7.1 WF live vs stored/pred UI — 혼용 금지

| pipeline | 소스 | 용도 | 벤치 표기 |
|----------|------|------|-----------|
| **WF live** | `predict_sets` → coordinator → (wire) · as_of 컷오프 | survey·WF 백테 | `pipeline=WF live` |
| **stored / pred UI** | `lotto_predictions` · review100 JSON | UI·캐시·BENCH §1 SSOT | `pipeline=stored` 또는 `review100` |

- **같은 표에 WF live 수치와 stored/pred UI 수치를 나란히 두지 말 것** (§5 표본 혼합 금지).
- 분리 방법: **표 2개** 또는 동일 표에 **`pipeline` 컬럼** 필수.
- stored만 쓰는 UI 지표(dashboard-summary·tier-wins API)를 WF 실력으로 해석 **금지** (BENCH §2 · 1149–1179 갭).

### 7.2 등수(tier) 분리 — `routes.py` `_prediction_rank_tier` 동일

본번호 `matched_count`·`bonus_matched`로 1~5등 판정 (코드 SSOT: `app/testlotto/routes.py`):

| tier | rank | 조건 | 라벨 |
|------|------|------|------|
| 1등 | 1 | matched_count == 6 | 1등 |
| 2등 | 2 | matched_count == 5 **and** bonus_matched == 1 | 2등 |
| 3등 | 3 | matched_count == 5 (보너스 없음) | 3등 |
| 4등 | 4 | matched_count == 4 | 4등 |
| 5등 | 5 | matched_count == 3 | 5등 |
| 미당첨 | 0 | 그 외 | (집계 제외) |

- 벤치 리포트에 **ge3_rate(≥3)** 만 단독 제시 시 **tier 피벗 표를 함께** 둘 것 — UI tier-wins 착시 방지.
- tier 표 컬럼 예: `pipeline` · `brain` · `r1`~`r5` · `ge3` · `n_sets` · `window`.

---

## 발권) 회차 내 조합 유일 (K-V)

- 발권 최종 출력의 조합(정렬 6튜플)은 **회차/배치 내에서 유일**해야 한다.
- 계층: 뇌 산출 → 기존 파이프라인 → **dedup** → 발권. 뇌·fusion·referee 로직 수정 금지.
- 스위치: `ROK21_DEDUP` 기본 ON (`0/false/off/no`만 OFF). OFF=기존 동작 동일.
- 이 규칙은 **조합 낭비 제거**이지 예측력 향상이 아니다. P(1등)=k/8,145,060.

---

## 8) 관련 FINDINGS

K-B(**PATCHED**) · K-08 · K-O · K-P · K-Q · K-R · K-S(PATCHED) · K-T · K-U · K-V(PATCHED) · K-W(**PATCHED**) · K-Y · K-Z(PATCHED) · **K-AA(PATCHED)** · K-M/K-N(HOLD) · **K-BENCH-05(PATCHED)** · **K-BENCH-03(PATCHED)** · **WARRANT.md**

기계검증: `python tools/_kb_bench_ssot_verify.py` → `docs/benchmarks/20260727_KB_bench_ssot.json`
