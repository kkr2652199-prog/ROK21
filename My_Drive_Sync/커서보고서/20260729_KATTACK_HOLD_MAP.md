# K-ATTACK-HOLD-MAP — 닫힌 축·실레버 공백 지도

📅 2026-07-29 · DB/coordinator **미수정** · `db_code_write=false`  
판정: **새 벤치 미실행** (실레버 빈약/null 구조)  
권고: **HOLD 유지 · V2 pin 유지**  
승인필요: **예** (형 전략선택)

V2 pin SSOT: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json`  
(`ge3_rate=0.1447` · `mean=1.7504` · `pass=true` · quota markov3+stat1+review1 · set_no_asc)

---

## 0) 이번 턴 판단

| 항목 | 결과 |
|------|------|
| 새 관측 갈지? | **아니오** |
| 이유 | coordinator·predict 실레버가 닫힌 축·금지축·null 신호에 **전면 매핑**됨 |
| 산출 | 본 HOLD맵 (벤치 JSON 신규 없음) |

**금지축(지시문):** 슬롯재선택 · AUX점수 · GENDIV · GENMIX — 본 턴 미실행.

---

## 1) 닫힌 축 표 (재탕금지)

숫자 = 각 `docs/benchmarks/*.json` 실측. 기억값 아님.

| ID | 레버 종류 | 판정 | 핵심(JSON) | 근거 JSON |
|----|-----------|------|------------|-----------|
| **K-MARKOV-WIRE-V2** | 발권 쿼터 set_no_asc | **PASS(현행핀)** | ge3=**0.1447** · mean=**1.7504** | `20260729_KMARKOV_WIRE_V2_verify.json` |
| K-MARKOV-WIRE (v1 conf쿼터) | 발권 conf정렬 | FAIL | ge3=**0.121** | `20260729_KMARKOV_WIRE_verify.json` |
| K-SETCOUNT-NULL | 장수·믹스 null분리 | PASS→WIRE유도 | best5=`E_markov3mix2` | `20260729_KSETCOUNT_null.json` |
| K-MARKOV-TUNE | markov decay/steps/top | FAIL | best ge3=**0.1404** ≤ pin | `20260729_KMARKOV_TUNE_survey.json` |
| K-SETNO-HITMAP | 뇌내 set_no 재배치 | FAIL | Δge3 best=+0.0034 &lt; 0.005 | `20260729_KSETNO_hitmap.json` |
| K-SETPACK-TOP6 | 출현 top6→set1 | FAIL | pool ge3=**0.101** | `20260729_KSETPACK_top6.json` |
| K-EV-POP | 저인기 슬롯픽 | FAIL | hit_beats_v2=false | `20260729_KEV_pop.json` |
| K-BAND-SELECT | LMH 대역 슬롯픽 | FAIL | PASS=false | `20260729_KBAND_select.json` |
| K-SUM-SELECT | 합(이론138) 슬롯픽 | FAIL | PASS=false | `20260729_KSUM_select.json` |
| K-GENDIV | diversify/Jaccard | FAIL | PASS=false | `20260729_KGENDIV_survey.json` |
| K-AUX-BLEND | AUX_WEIGHTS·\*40 | FAIL | 양상관 게이트 미달 | `20260729_KAUX_BLEND_survey.json` |
| K-GENMIX | 뇌별 predict_sets(n) | FAIL | best live ge3=**0.1303** &lt; pin · trunc identical=**1.0** | `20260729_KGENMIX_survey.json` |
| K-COVER / HISIM / STRUCT | wheel·유사·구조재가중 | FAIL | ge3≤RR 또는 Δ≈0 | `KCOVER`/`KHISIM`/`KSTRUCT`_survey.json |
| K-PROB-VECTOR | 빈도·전이·이월·끝수 | null | recommended_strengthen=[] | `20260729_KPROBVEC_survey.json` |
| K-ATTACK-OPEN | analog·tune·conf재점수 | FAIL×3 | recommended_next=없음 | `20260729_KOPEN_survey.json` |
| K-ATTACK-BAYES / CONF-CAL / SLICE | 동적가중·conf·구간 | 보류/미승격 | promote_wire 없음 | 각 JSON |
| K-GATHER v1/v2 | 몰아주기·covering | 보류 | ge5/ge6 회수0 | `KGATHER_*` |

**재탕금지 누적(지시+STATUS):** GENMIX · AUX-BLEND · GENDIV · SUM/BAND/EV/SETNO/SETPACK · TUNE · 슬롯재선택 · conf-quota 구WIRE · HISIM/STRUCT/COVER · GATHER전면.

---

## 2) 코드 실레버 인벤토리 → 상태

| 코드 앵커 | 역할 | 관측 상태 |
|-----------|------|-----------|
| `coordinator.MARKOV_WIRE_BRAIN_QUOTA` + `ENABLED` + set_no_asc | 발권 5장 | **V2 PASS = 현 최선** |
| `coordinator.AUX_WEIGHTS` + `aux_score*40` | 점수(nums 불변) | AUX-BLEND **닫힘** |
| conf 정렬 발권 | 구 WIRE | **FAIL** |
| `registry.SETS_PER_PREDICT_BRAIN` | 생성 n_sets | GENMIX **닫힘** |
| `set_diversity.diversify_pick` / oversample | 생성 다양성 | GENDIV **닫힘** |
| `predict_markov` decay/steps/top | 전이 파라미터 | TUNE **닫힘** |
| 슬롯 재선택(합·대역·인기·set_no·pack) | 동일풀 재픽 | **전부 FAIL** |
| `learn_state` carry/ending/overdue boost | 생성 가중 | live 기본 **0.0** · PROBVEC **null** · 상한 동결 |
| `predict_flow_shaman` learn 미소비 (K-F) | markov←boost | boost=0·신호null → **실레버 아님**(구조적 공허) |
| `get_referee_weights` (K-M) | 뇌가중 ≈균등 | HOLD · WINDOW는 패치됨 · 성적레버로 미개척이나 균등격차 사실상 0 |
| `_unused/aux_gap_scout` | 미등록 AUX | K-H **재배선 금지기본** |

**결론:** “아직 안 연 **실**레버” = **없음**(또는 null·금지·인접재탕만). → 새 READ-ONLY 벤치 **미실행**.

---

## 3) V2가 최선인 근거 (JSON만)

1. **SETCOUNT-NULL:** 5장 실력 후보 중 `E_markov3mix2` → WIRE 경로의 원형.  
2. **WIRE-V2:** `pass=true` · ge3=**0.1447** &gt; null **0.1137** · Δ=**+0.031** · conf쿼터 v1(0.121) 상회.  
3. **이후 직교 공격 전부** pin 미돌파 또는 의미임계(Δge3≥0.005) 미달:  
   - SETNO best Δ=+0.0034 (게이트 FAIL)  
   - TUNE best 0.1404 ≤ 0.1447  
   - GENMIX best live 0.1303 &lt; pin · trunc fillable는 티켓 **identical=1.0**(구조적 null)  
   - SUM/BAND/EV/SETPACK/GENDIV/AUX · COVER류 전부 WIRE 비대상  

→ **현 파이프라인 안에서 발권·생성·점수·파라미터 레버로 pin을 넘긴 후속 없음.**

---

## 4) 남은 후보 (약 · 비권고 기본)

| ID | 스케치 | 왜 약/위험 |
|----|--------|------------|
| K-STATP | stat×pattern 조건부 | PATTERN2 잔여 · STRUCT/AUX 재탕 인접 |
| K-LEARN-MEAN (K-N) | 학습입력 best→mean | 설계 변경 · 즉시 ge3 벤치 레버 아님 · 형 승인 필수 |
| (없음) | 파이프라인 밖 전제 재정의 | 예측레버 아님 · 별도 전략 세션 |

**본맵 권고 다음축ID: 없음** → `K-ATTACK-HOLD` 유지.

---

## 5) 권고 · 형 선택지 (≤2)

| # | 선택 | 의미 |
|---|------|------|
| **A (권고)** | **HOLD 유지** | V2 pin 동결 · 닫힌축 재탕금지 · 추가 예측레버 벤치 중단 |
| **B** | **전략 전환 승인** | 파이프라인 레버 공격 중단 → 형·동생이 **전제/목적함수** 새 프레임 1건만 정의 (예: K-N 학습입력 · 또는 EV목적 명시). 즉시 벤치 ID는 형이 붙인 뒤 커서 실행 |

---

## 6) 팩트체크

| 항목 | 결과 |
|------|------|
| V2 JSON ge3/mean/pass | **일치** 0.1447 / 1.7504 / true |
| GENMIX best_live ge3_rate / Δpin | **일치** 0.1303 / −0.0144 |
| GENMIX trunc fillable identical | **일치** 1.0 |
| SETNO gates PASS=false · Δ임계 | **일치** (any_beats true · delta≥0.005 false) |
| TUNE best_ge3 0.1404 | **일치** |
| coordinator 미수정 · DB 미커밋 | **준수** |
| 새 벤치 미실행 | **준수** (실레버 공백) |

---

## 7) 산출물

- 본 보고서 → `My_Drive_Sync/커서보고서/20260729_KATTACK_HOLD_MAP.md` 복사
- NEXT=`K-ATTACK-HOLD` · 승인필요=예
