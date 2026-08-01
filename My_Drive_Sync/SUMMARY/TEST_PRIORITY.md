# TEST_PRIORITY — 테스트 우선순위 큐 (숙제형)

📅 갱신: 2026-07-30 · SSOT=`My_Drive_Sync/SUMMARY/TEST_PRIORITY.md`  
📌 **형·커서·젠스파크 공통 작업 큐.** NEXT_ACTIONS(1건)와 병행 — 여기서 전체 순위·선행·금지를 본다.

---

## 용어 한글表 (쉬운 말)

| 영문/약어 | 쉬운 말 | 설명 |
|-----------|---------|------|
| **ge3** | 3개 이상 맞춤 비율 | 한 회차에서 5장 중 **3개 이상** 번호가 맞은 비율 (예: 0.145 = 14.5%) |
| **ge4 / ge5** | 4개·5개 맞춤 비율 | ge3보다 더 어려운 적중 등급 |
| **mean** | 평균 맞춘 개수 | 한 장당 평균 몇 개 번호가 맞았는지 (이론값 ≈ 0.8) |
| **pin** | 현재 앱 고정 기준 | WIRE-V2 저장값 ge3=**0.1447** — 이보다 좋아야 “앱에 반영할 만함” |
| **null** | 운 좋은 랜덤 기준 | ge3≈**0.1137** — 아무 것도 안 한 이론적 기대치 |
| **p값** | 우연일 확률 | 작을수록 “운이 아니라 진짜 차이”에 가깝다 (보통 0.05 미만) |
| **QUICK / tail-200** | 빠른 시험 200회 | 최근 200회(1035~1234)만 먼저 돌려 PASS 후 full |
| **full / n=1182** | 전체 시험 | 53~1234회 전부 walk-forward (느리지만 확정 판정) |
| **wire** | 앱에 실제 반영 | coordinator·predict 코드 수정 → 사용자 앱 동작 변경 |
| **survey** | 조사만 | 코드 안 바꾸고 READ-ONLY로 숫자만 뽑음 |
| **walk-forward (WF)** | 과거만 보고 맞추기 | 그 회차 **이전** 데이터만 써서 예측 (컨닝 방지) |
| **set_no_asc** | 세트 번호 순 고르기 | 점수 순이 아니라 markov3+stat1+review1 **고정 쿼터** |
| **hint inject** | 힌트 주입 | 과거 패턴 정보를 3뇌 예측에 **가중치 힌트**로만 넣기 |
| **selector / combined** | 고르기 방식 | 10장 pool에서 5장 뽑는 규칙 (overlap·bin·Jaccard·combined 등) |
| **1~5등 표** | 등수별 적중표 | 1등~5등 각각 몇 번 나왔는지 표 (ge3만으로는 부족할 때) |

---

## P0 — 지금 당장 (앱 반영 직전)

### 0. K-SIGNAL-REPACK-01 ✅ (완료 · 5장 공정 FAIL)

| 항목 | 내용 |
|------|------|
| **순위** | **P0** (완료) |
| **ID** | `K-SIGNAL-REPACK-01` |
| **한글 제목** | 번호 **몰아주기(repack)** — 10pool→5신호세트×3뇌 |
| **숙제 한 줄** | pool 번호를 신호 점수로 재조립(통째 5장 고르기와 다름) · set_no_asc·combined 대비 ge3 |
| **결과 (QUICK n=200)** | best_of_15: signal_repack ge3=**0.275** · **top5_from_15(공정): ge3=0.085** < combined **0.145** |
| **판정** | 15장 artifact PASS · **5장 공정 비교 FAIL** → wire 불필 · SELECT-FULL 우선 |
| **근거** | `reports/20260730_KSIGNAL_REPACK_SURVEY.md` · JSON `20260730_KSIGNAL_REPACK_survey.json` |

---

### 1. K-SIGNAL-SELECT-FULL

| 항목 | 내용 |
|------|------|
| **순위** | **P0** |
| **ID** | `K-SIGNAL-SELECT-FULL` |
| **한글 제목** | 신호셋트 고르기 — **전체 1182회** + 1~5등 표 |
| **숙제 한 줄** | QUICK에서 PASS한 combined 방식이 **전체 1182회**에서도 pin(0.1447)을 넘고 p<0.05인지, 1~5등 표까지 확인 |
| **선행조건** | K-SIGNAL-SELECT-01 **QUICK PASS** (combined ge3=0.145 · p=0.102 · n=200) |
| **PASS 기준** | full n=1182 · best selector ge3 **> pin 0.1447** **AND** p **< 0.05** · 1~5등 breakdown 표 첨부 |
| **금지** | wire(앱 코드 수정) · coordinator·predict_* 수정 · DB 쓰기 |
| **상태** | **대기** (NEXT 1건) |
| **근거 보고서** | `reports/20260730_KSIGNAL_SELECT_SURVEY.md` · `reports/20260729_SIGNAL_SET_ARCHITECTURE.md` |

---

### 2. K-SIGNAL-SELECT-WIRE

| 항목 | 내용 |
|------|------|
| **순위** | **P0** |
| **ID** | `K-SIGNAL-SELECT-WIRE` |
| **한글 제목** | 앱에 **새 고르기 방식** 반영 (combined selector) |
| **숙제 한 줄** | FULL PASS 후, 형 **GO** 받으면 coordinator에 combined 선별·10 pool→5 wire |
| **선행조건** | K-SIGNAL-SELECT-FULL **PASS** · 형 **GO** |
| **PASS 기준** | WIRE-V2 verify JSON · ge3 ≥ FULL survey best · rollback 경로 문서화 |
| **금지** | 형 GO 전 wire **절대 금지** · `random.choices` 수정 · boost 상한 초과 |
| **상태** | **HOLD** (형 GO 대기) |
| **근거 보고서** | `reports/20260730_KSIGNAL_SELECT_SURVEY.md` · `reports/20260729_SIGNAL_SET_ARCHITECTURE.md` |

---

## P1 — FULL 다음 줄

### 3. K-10SET-SURVEY

| 항목 | 내용 |
|------|------|
| **순위** | **P1** |
| **ID** | `K-10SET-SURVEY` |
| **한글 제목** | 뇌당 **10장 pool** — QUICK 200회 조사 |
| **숙제 한 줄** | SETS_PER_BRAIN=10 pool에서 QUICK_GATE(tail-200)로 ge3·p 확인 — wire 전 설계 검증 |
| **선행조건** | K-SIGNAL-SELECT-FULL 결과 · K-QUICK-GATE-01 **DONE** |
| **PASS 기준** | QUICK: ge3 > null(0.1137) **AND** p < 0.15 (BENCH §9) |
| **금지** | coordinator live wire · predict_statistical `random.choices` |
| **상태** | **대기** |
| **근거 보고서** | `reports/20260729_SIGNAL_SET_ARCHITECTURE.md` · `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` §9 |

---

### 4. K-DET-LAB-01

| 항목 | 내용 |
|------|------|
| **순위** | **P1** |
| **ID** | `K-DET-LAB-01` |
| **한글 제목** | 1군 **결정론 top-k** 실험실 (복사본 조사) |
| **숙제 한 줄** | 1군 `deterministic_sets` 방식을 ROK21 lab에 READ-ONLY 복사해 ge3 비교 |
| **선행조건** | K-10SET-SURVEY 또는 FULL 결과 참고 · 1군 READ-ONLY |
| **PASS 기준** | lab survey JSON · ge3 vs pin · p vs null · **wire 없이** 판정만 |
| **금지** | 1군(memoy) 쓰기 · coordinator wire · kweon 접촉 |
| **상태** | **대기** |
| **근거 보고서** | `reports/20260729_MONEY1GUN_VS_ROK21.md` · `reports/20260729_SIGNAL_SET_ARCHITECTURE.md` |

---

### 5. K-QUICK-GATE

| 항목 | 내용 |
|------|------|
| **순위** | **P1** |
| **ID** | `K-QUICK-GATE` |
| **한글 제목** | 빠른 시험(200회) **공통 도구** 만들기 |
| **숙제 한 줄** | BENCH §9 + `bench_quick_gate.py` — 모든 survey가 tail-200 먼저 돌리게 |
| **선행조건** | (완료) K-SIGNAL-SELECT-01 선별 기준 확정 후 설계 |
| **PASS 기준** | `tools/bench_quick_gate.py` 존재 · window/signal survey `--n-eval 200` 동작 |
| **금지** | QUICK만으로 full 대체 선언 금지 |
| **상태** | **완료** |
| **근거 보고서** | `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` §9 · `reports/20260729_SIGNAL_SET_ARCHITECTURE.md` |

---

## P2 — 형 GO 또는 FULL 이후

### 6. E3 PATTERN-HINT-03

| 항목 | 내용 |
|------|------|
| **순위** | **P2** |
| **ID** | `E3-PATTERN-HINT-03` |
| **한글 제목** | 1군 **패턴 힌트** 이식 조사 (READ-ONLY) |
| **숙제 한 줄** | 1군 pattern_store ktier 구조를 draw_features로 재현 → stat/markov 가중 힌트만 주입 survey |
| **선행조건** | K-SIGNAL-SELECT-FULL 결과 · 형 **GO** |
| **PASS 기준** | full n=1182 · best variant ge3 **> pin** · p **< 0.05** |
| **금지** | predict_* 수정 · DB 쓰기 · wire |
| **상태** | **대기** (형 GO) |
| **근거 보고서** | `reports/20260729_AUX_SIGNAL_PIVOT.md` · `reports/20260729_KWINDOW_SIGNAL_SURVEY.md` |

---

### 7. K-POSTHOC-WIRE

| 항목 | 내용 |
|------|------|
| **순위** | **P2** |
| **ID** | `K-POSTHOC-WIRE` |
| **한글 제목** | **200시드** 역추적에서 나온 신호 — live 격자 탐색 |
| **숙제 한 줄** | seed#19 등 상위 시드 특성을 힌트로 live WF 격자 survey (형 GO 후) |
| **선행조건** | K-POSTHOC-ANALYSIS **신호발견** · 형 **GO** |
| **PASS 기준** | live WF · ge3 > pin · p < 0.05 · wire는 별도 GO |
| **금지** | POSTHOC alone으로 wire 금지 · coordinator 수정은 형 GO |
| **상태** | **대기** (형 GO) |
| **근거 보고서** | `reports/20260729_KPOSTHOC_ANALYSIS.md` |

---

### 8. 1군-FUSION-AB

| 항목 | 내용 |
|------|------|
| **순위** | **P2** |
| **ID** | `1G-FUSION-AB` |
| **한글 제목** | 1군 **fusion** 방식 A/B 조사 (wire 없음) |
| **숙제 한 줄** | 1군 fusion PMF 결합 vs ROK21 coordinator-only — READ-ONLY survey로 ge3 비교 |
| **선행조건** | P0·P1 마감 · 형 방향 확인 |
| **PASS 기준** | survey JSON · ge3 vs pin · **1군 stored 경로 wire 금지** 명시 |
| **금지** | fusion/hyena/lstm stored 경로 ROK21 wire · 1군 DB 쓰기 |
| **상태** | **대기** |
| **근거 보고서** | `reports/20260729_MONEY1GUN_BENCH_INVENTORY.md` · `reports/20260729_MONEY1GUN_ROK21_LESSONS.md` |

---

## P3 / HOLD — 나중·보류

### 9. HINT-INJECT-WIRE (E1 + E-window)

| 항목 | 내용 |
|------|------|
| **순위** | **P3 / HOLD** |
| **ID** | `HINT-INJECT-HOLD` |
| **한글 제목** | 힌트 주입 **앱 반영** — E1·window 둘 다 pin 미달 |
| **숙제 한 줄** | K-AUX-SIGNAL-01·K-WINDOW-SIGNAL-01 모두 pin(0.1447) 못 넘김 → wire 보류 |
| **선행조건** | 새 survey에서 pin PASS + 형 GO |
| **PASS 기준** | (현재) 해당 없음 — **HOLD** |
| **금지** | pin 미달 variant wire |
| **상태** | **HOLD** |
| **근거 보고서** | `reports/20260729_KAUX_SIGNAL_SURVEY.md` · `reports/20260729_KWINDOW_SIGNAL_SURVEY.md` |

---

### 10. SET-NO-ASC-TUNE

| 항목 | 내용 |
|------|------|
| **순위** | **P3** |
| **ID** | `SET-NO-ASC-TUNE` |
| **한글 제목** | **set_no_asc 쿼터만** 미세 조정 |
| **숙제 한 줄** | markov3+stat1+review1 비율만 바꿔 ge3 오르는지 (selector 없이) |
| **선행조건** | K-SIGNAL-SELECT 축 **FAIL** 시에만 재검토 |
| **PASS 기준** | full · ge3 > pin · p < 0.05 |
| **금지** | selector PASS인데 set_no_asc만 튜닝으로 우회 |
| **상태** | **HOLD** (우선순위 낮음) |
| **근거 보고서** | `reports/20260729_4AUX_FEEDBACK_REVIEW.md` · `reports/20260729_KBENCH_POSTMORTEM.md` |

---

### 11. VIRTUAL-LOTTO-UI

| 항목 | 내용 |
|------|------|
| **순위** | **P3** |
| **ID** | `VIRTUAL-LOTTO-UI` |
| **한글 제목** | **가상 로또 UI** (형 아이디어) |
| **숙제 한 줄** | 앱에서 “가상 추첨·적중 연습” UI — 성능 survey와 분리 |
| **선행조건** | 형 아이디어 구체화 · P0 wire 안정 후 |
| **PASS 기준** | (미정) 형 승인 범위 정의 후 |
| **금지** | 벤치·wire 작업과 혼동 |
| **상태** | **HOLD** (나중) |
| **근거 보고서** | (아직 없음 — 형 메모) |

---

## 한눈에 보기 (순위表)

| 순위 | ID | 한글 제목 | 상태 |
|:----:|-----|-----------|------|
| P0 | K-SIGNAL-REPACK-01 | 번호 몰아주기 repack QUICK | **완료·5장 FAIL** |
| P0 | K-SIGNAL-SELECT-FULL | 전체1182 + 1~5등 표 | **완료·FAIL** |
| P0 | K-SIGNAL-SELECT-WIRE | 앱 반영 (형 GO) | **HOLD** |
| P0 | K-COMBO-SIGNAL/V2 | AND·steering survey | **완료·FAIL·HOLD** |
| P1 | K-10SET-SURVEY | 10장 pool QUICK200 | 대기 |
| P1 | K-DET-LAB-01 | 1군 결정론 top-k lab | 대기 |
| P1 | K-QUICK-GATE | QUICK 도구 | **완료** |
| P2 | E3-PATTERN-HINT-03 | 1군 패턴 힌트 survey | 대기 |
| P2 | K-POSTHOC-WIRE | 200시드 신호 격자 | 대기 |
| P2 | 1G-FUSION-AB | 1군 fusion A/B | 대기 |
| P3 | HINT-INJECT-HOLD | E1·window wire | HOLD |
| P3 | SET-NO-ASC-TUNE | 쿼터만 튜닝 | HOLD |
| P3 | VIRTUAL-LOTTO-UI | 가상 로또 UI | HOLD |

---

## 운영 규칙

1. **NEXT_ACTIONS** = 큐 맨 앞 1건만 (지금: **K-ATTACK-HOLD** · survey 중단).
2. **PASS/FAIL** 숫자는 `docs/benchmarks/*.json` 이 원본 — 이 파일은 **순위·금지·쉬운 말**만.
3. **wire** = 형 GO 필수. survey PASS만으로 자동 wire **금지**.
4. 보고서는 `BENCH_REPORT_TEMPLATE.md` **숙제 6섹션** 형식 (예: `20260730_KSIGNAL_SELECT_SURVEY.md`).
