# AI_COLLAB — 커서×젠스파크 협업 규칙 + 대화 요약

> **세션 압축 대비 SSOT.** 젠스파크 세션이 압축되면 이 파일 + EXTERNAL_START.md 를 읽어 복구.

## 1. 역할 분담

| 역할 | 담당 | 권한 |
|------|------|------|
| **형(오빠)** | 최종 결정·GO/HOLD 승인 | 모든 방향 결정권 |
| **커서** | 코드 실행·commit·push·지시서 작성·벤치마크 | D:\ROK21 직접 접근, GitHub push |
| **젠스파크** | 전략 분석·검토·지시서 초안·팩트체크 | GitHub raw 읽기 전용 |

### 원칙
- AI끼리 논의 OK, **방향 확정은 반드시 형 GO**
- 지시서 작성: 커서가 최종본 작성·실행 (젠스파크 초안 참고 가능)
- 수치 인용: `docs/benchmarks/*.json` SSOT만 (기억으로 쓰지 않음)

## 2. 세션 압축 대비 규칙

1. **GitHub = 영구 기억.** reports/, docs/benchmarks/, EXTERNAL_START.md, NEXT_ACTIONS.md, AI_COLLAB.md 가 SSOT
2. **압축되면 GitHub 파일 먼저 읽기.** 특히 EXTERNAL_START.md (현재상태) + AI_COLLAB.md (협업룰+대화요약)
3. **커서가 매 push 시 이 파일의 §3 대화요약을 갱신** → 압축 후에도 논의 맥락 복구 가능
4. 형이 젠스파크에 "GitHub 보고서 확인해줘" 하면 → 젠스파크가 raw URL로 읽고 팩트체크

## 3. 대화 요약 (커서가 매 push 시 갱신)

### 최신 상태 (2026-08-01 22:45 KST)
- **HEAD(실측)**: `5bba9f3` · SSOT=`kkr2652199-prog/ROK21` · 포트 **7021**
- **지금(판정)**: **K-AUX-DIAG DONE** — baseline ge3=**0.0800** · markov survival **0.668** · worst aux **pattern_spotlight**
- **다음(공식)**: aux 회복(spotlight/balance) 또는 fusion path 변경 · **형 GO 대기**

### 현재 live stack (2026-08-01 · B1 rollback 후)
```
run_coordinated_prediction
  → _auto_feedback(prev) → apply_feedback → learn_state
  → 3뇌 predict_sets(draws)          ← B1 virtual draws **제거됨**
  → aux 1:1 scoring (AUX_1TO1_ENABLED)
  → dynamic_brain_quota (DEFAULT 25/60/15 → 슬롯 ~1/3/1)
  → DB 저장
```
- `pattern_signal.py` **파일 보존** · coordinator에서 signal wiring **없음**
- markov engine: **full draws** (window100 롤백 완료)

### K-AUX-DIAG (형 GO · per-aux ablation · no auto next)
근거: `docs/benchmarks/20260801_KAUX_DIAG.json`

| scenario | ge3 | markov survival | survival Δ |
|----------|-----|-----------------|------------|
| baseline (all ON) | **0.0800** | **0.6680** | — |
| miss OFF | 0.0800 | 0.6680 | 0 |
| **spotlight OFF** | 0.0800 | **0.0000** | **−0.6680** |
| balance OFF | 0.0800 | **0.9480** | **+0.2800** |
| referee OFF | 0.0800 | 0.6680 | 0 |
| all aux OFF | 0.0800 | 0.0280 | −0.6400 |

**dropout ranking:** 1) **pattern_spotlight** (markov top5 생존 필수) · 2~3) miss/referee 무영향 · 4) **balance_keeper** (OFF 시 survival↑ = markov에 불리)

**결론:** ge3는 모든 시나리오 **0.0800 동일**(quota 5장 선택이 ge3 지배) · markov 탈락 1순위 **pattern_spotlight OFF→survival 0** · balance_keeper는 markov ranking 억제 · **형 GO 대기**

### K-FUSION-QUOTA-FIX (형 GO · FAIL · no auto-tune)
근거: `docs/benchmarks/20260801_KQUOTA_FIX_N100.json`

| 항목 | 내용 | 판정 |
|------|------|------|
| coordinator | `DEFAULT_QUOTA_WEIGHTS` stat25/markov60/review15 · `_get_quota_weights` · total-slot largest remainder | **OK** |
| smoke | draw 1230~1234 · 5장 · quota 1/3/1 | **PASS** |
| n=100 walk-forward | draw 1135~1234 · full coordinator | **FAIL** ge3=**0.0800** |

| 지표 | before (40/40/20) | after |
|------|-------------------|-------|
| overall ge3 | 0.0600 | **0.0800** (+0.0200) |
| mean_match | 1.63 | **1.63** |
| quota avg | stat 40% · markov 40% · review 20% | stat **20%** · markov **60%** · review **20%** |
| by_period ge3 | early 0.04 · mid 0.04 · late 0.08 | early **0.08** · mid **0.04** · late **0.10** |
| gate | — | ge3 **>** 0.0900 → **FAIL** |

**결론:** markov 쿼터 60%로 ge3 +0.02 개선 · 0.09 gate 미달 · auto-tune 없음 · **형 GO 대기**

### K-ENGINE-PHASE1-HOLD (형 GO · STEP1~2 · fusion diag)
근거: `docs/benchmarks/20260801_KFUSION_BOTTLE_DIAG.json`

| STEP | 내용 | 판정 |
|------|------|------|
| 1 window100 롤백 | build_transition_matrix full draws 복원 · smoke 1230~1234 5/5 | **OK** |
| 2 fusion diag n=100 | BENCH_FIXED_QUOTA markov=5 · draw 1135~1234 | **AUX_PATH_BOTTLENECK** |

| 지표 | 값 |
|------|-----|
| diag ge3_rate (markov 100%) | **0.0900** (9/100) |
| vs fused ref 0.0600 | **+0.0300** |
| vs solo markov ref 0.1300 | **−0.0400** |
| prod markov quota rate avg | **0.4000** (2/5 slots) |
| aux survival rate avg | **0.6680** (markov in global top5) |
| bottleneck | **aux_or_coordinator_path** (quota also contributes 0.06→0.09) |

**결론:** window100 롤백 완료 · solo 0.13 vs fused 0.06 격차는 quota(40%) + aux/coordinator path 혼합 · 회복 튜닝 **형 GO 대기**

### K-ENGINE-PHASE1 (형 GO · STEP1~3 · window100 FAIL)
근거: `docs/benchmarks/20260801_KMARKOV_WINDOW100_SOLO_N200.json`

| STEP | 내용 | 판정 |
|------|------|------|
| 1 B1 rollback | coordinator signal import/block 제거 · predict_sets(draws) 복원 · smoke 1230~1234 5/5 | **OK** |
| 2 markov window=100 | build_transition_matrix draws[-100:] · smoke 1230~1234 5/5 | **OK** |
| 3 solo bench n=200 | draw 1035~1234 walk-forward · vs K-HIGHWAY solo 0.1300 | **FAIL** ge3=**0.0850** |

| 지표 | 값 |
|------|-----|
| solo ge3_rate | **0.0850** (17/200) |
| mean_match | **1.6150** |
| vs ref 0.1300 | **−0.0450** |
| by_period ge3 | early **0.1194** · mid **0.0896** · late **0.0455** |
| gate | ge3 > 0.1300 → **FAIL** (auto-tune 없음) |

**결론:** B1 rollback 완료 · markov window100은 solo ge3 **하락** → 유지/롤백·fusion 회복 백테 **형 GO 대기**

### K-BRAIN-SIGNAL-B1-BACKTEST-100 (형 GO · FAIL · B1 rollback으로 superseded)
근거: `docs/benchmarks/20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) — 방향1·highway **동일** |
| virtual_active_rate | **100%** |
| delta vs 0.0600 | **+0.0000** |
| by_brain solo | stat 0.09 · markov 0.13 · review 0.11 |
| by_period | early 0.04 · mid 0.04 · late 0.08 |

**결론:** B1 virtual draws도 ge3 개선 없음 → TUNE(_MIN_MAX_SIM) 또는 B1 롤백 검토

### K-BRAIN-SIGNAL-B1 (형 GO · PASS)
| 항목 | 내용 | 판정 |
|------|------|------|
| make_signal_draws | signal top6 → virtual draws×3 | **OK** |
| coordinator | draws_with_signal → predict_sets · conf blend **제거** | **OK** |
| smoke | 1225~1234 · virtual_active 10/10 | **PASS** |

**live stack (B1):**
```
run_coordinated_prediction
  → get_pattern_signal(draws)
  → make_signal_draws → draws_with_signal = virtual + draws
  → predict_sets(draws_with_signal)  ← engine weights에 signal 반영
  → aux 1:1 → dynamic_brain_quota → DB
```

### K-BRAIN-SIGNAL-BACKTEST-100 (형 GO · FAIL)
근거: `docs/benchmarks/20260801_KBRAIN_SIGNAL_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) — highway와 **동일** |
| signal_active_rate | **100%** (100/100) |
| vs highway 0.0600 | **+0.0000** |
| vs baseline 0.1015 | **−0.0415** |
| by_brain solo | stat 0.09 · markov 0.13 · review 0.11 |
| by_period | early 0.04 · mid 0.04 · late 0.08 |
| DB | reset 후 **505행** 유지 · draw **1235** UI 5장 |

**판정:** FAIL (ge3 ≤ 0.0600) · signal 레이어는 **전 회차 active** → ge3 개선 없음 → TUNE(_MIN_MAX_SIM) 검토

### K-BRAIN-SIGNAL-A1 (형 GO · PASS · B1에서 conf blend **대체됨**)
| 항목 | 내용 | 판정 |
|------|------|------|
| pattern_signal.py | 9-dim cosine top-k analog signal | **OK** |
| coordinator (A1) | 85% conf + 15% signal — **B1에서 제거** | superseded |
| BACKTEST-100 (방향1) | ge3=0.0600 = highway 동일 | **FAIL** |

### K-HIGHWAY-PHASE1 (형 GO · 코드 반영 완료 · 백테 FAIL)
| ID | 파일 | 내용 | 판정 |
|----|------|------|------|
| K-HIGHWAY-FEEDBACK | coordinator.py | `_auto_feedback` · `_detect_missed_patterns` · deprecated import 삭제 | **OK** |
| K-HIGHWAY-REFEREE | aux_referee.py | `score_set()` → `get_referee_weights()` 반영 | **OK** |
| K-HIGHWAY-QUOTA | coordinator.py | `dynamic_brain_quota()` · referee 가중 5장 (min 1/뇌) | **OK** |
| K-HIGHWAY-BACKTEST-100 | tools | draw 1135~1234 n=100 · full coordinator walk-forward | **FAIL** ge3=0.0600 |

**현재 live stack (PHASE1 반영):**
```
run_coordinated_prediction 진입
  → _auto_feedback(prev) → apply_feedback → learn_state
  → 3뇌 predict 15장 → aux 1:1 scoring
  → dynamic_brain_quota (referee 가중 5장 · set_no_asc)
  → DB 저장
```

### K-HIGHWAY-BACKTEST-100 수치 SSOT
근거: `docs/benchmarks/20260801_KHIGHWAY_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) |
| mean_match | 1.63 |
| vs K-BACKTEST-FULL-C baseline | **−0.0415** (0.1015) |
| by_brain solo ge3 | stat 0.09 · markov **0.13** · review 0.11 |
| by_period ge3 | early 0.04 · mid 0.04 · late 0.08 |
| dynamic quota avg | stat 40% · markov 40% · review 20% → **K-QUOTA-FIX 후 20/60/20** |
| learn 루프 | **동작 확인** — draw1234 rc=99 · carry/ending adj cap 도달 |

**형 결정 대기:** PHASE1 **HOLD** vs **롤백**(고정 쿼터 markov3/stat1/review1) vs **튜닝**

### 병렬 트랙 (별도 · PHASE1과 독립)
| ID | 판정 | 비고 |
|----|------|------|
| **K-BRAIN-SIGNAL** | **B1-BACKTEST FAIL** | ge3=0.0600 · virtual 100% · TUNE/롤백 **형 GO 대기** |
| K-NEW-ENGINE-STAT-A1 | **PASS** (delta=0) | ENGINE_V2=False 유지 · solo ge3=0.1350 |
| K-BRAIN-TUNE-SURVEY | **HOLD** | best_combo 0.1032 · auto-apply 금지 |
| K-BRAIN-LOGIC-UPGRADE | **설계 검토만** | 젠스파크 4방향 · 커서 Q1~Q5 답변 · 형 GO 전 구현 금지 |
| K-CLEANUP-AND-NEW-ENGINE-PREP | **커서 거부** | engine NotImplementedError 교체 위험 |

### ⚠️ 중단·거부 지시서
- **K-CLEANUP** — 레거시 mv + engine 스켈레톤 → 커서 **실행 거부** (Q1~Q6 반문 · §6 참고)

### 벤치 수치 SSOT (주요 · `docs/benchmarks/*.json`)
| ID | n | ge3 | 판정 |
|----|---|-----|------|
| **K-AUX-DIAG** | 100 | **0.0800** (전 시나리오 동일) | **DONE** |
| K-FUSION-QUOTA-FIX | 100 | **0.0800** | **FAIL** (>0.09) |
| K-FUSION-BOTTLE-DIAG | 100 | **0.0900** (markov100%) | diag |
| K-MARKOV-WINDOW100-SOLO | 200 | **0.0850** | **FAIL** |
| K-HIGHWAY-BACKTEST-100 | 100 | **0.0600** | **FAIL** |
| solo markov (highway by_brain) | — | **0.1300** | ref |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-NEW-ENGINE-STAT-A1 | 200 | 0.1350 (v2=0.1350) | PASS (delta=0) |

### fusion ge3 격차 분해 (확정 · 2026-08-01)
| 단계 | ge3 | vs 이전 | 원인 |
|------|-----|---------|------|
| full coordinator (highway) | 0.0600 | — | quota 40/40/20 + aux |
| quota fix 20/60/20 | **0.0800** | +0.02 | markov quota ↑ |
| markov 100% fixed (diag) | 0.0900 | +0.01 | quota 희석 제거 |
| solo markov | 0.1300 | +0.04 | aux/coordinator path 손실 |
| aux ablation | **0.0800** (변화 없음) | 0 | quota 5장 선택이 ge3 지배 |

### 논의 이력 (최신순)
1. **[22:35] K-AUX-DIAG DONE** — 6시나리오 · ge3 전부 0.0800 · spotlight OFF→surv 0 · balance OFF→surv 0.948
2. **[21:45] K-FUSION-QUOTA-FIX FAIL** — quota 20/60/20 · ge3=0.0800 (+0.02 vs 0.06)
3. **[21:10] K-ENGINE-PHASE1-HOLD** — window100 롤백 · fusion diag AUX_PATH_BOTTLENECK ge3=0.09
4. **[20:30] K-ENGINE-PHASE1** — B1 rollback · window100 solo FAIL ge3=0.0850
5. **[19:30] K-ENGINE-UPGRADE 브리핑** — PHASE1~3 의견 · markov window100만 GO 가치
6. **[18:55] K-BRAIN-SIGNAL** — A1/B1 BACKTEST FAIL ge3=0.0600 · B1 rollback됨
7. **[17:50] K-HIGHWAY-BACKTEST-100 FAIL** — ge3=0.0600 · PHASE1 코드 반영

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-01 22:45)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.

```
[ROK21 압축복구 · 2026-08-01 · K-AUX-DIAG 완료]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- HEAD: 5bba9f3
- NEXT: K-AUX-DIAG-DONE — aux 회복 방향 결정 · **형 GO 대기**
- 진입: EXTERNAL_START.md → AI_COLLAB.md §3·§6

■ 오늘 fusion 회복 타임라인 (ge3 중심)
| 단계 | ge3 | 비고 |
| highway PHASE1 | 0.0600 | quota 40/40/20 |
| quota fix 20/60/20 | 0.0800 | +0.02 · FAIL gate>0.09 |
| fusion diag markov100% | 0.0900 | quota 희석 제거 |
| solo markov ref | 0.1300 | by_brain |
| aux ablation (전 시나리오) | 0.0800 | aux OFF해도 ge3 불변 |

■ K-AUX-DIAG (최신 · 형 GO 완료)
JSON: docs/benchmarks/20260801_KAUX_DIAG.json
보고서: reports/20260801_KAUX_DIAG.md

| scenario | ge3 | markov survival |
| baseline | 0.0800 | 0.6680 |
| spotlight OFF | 0.0800 | **0.0000** ← markov top5 생존 필수 |
| balance OFF | 0.0800 | **0.9480** ← balance가 markov ranking 억제 |
| miss/referee OFF | 0.0800 | 0.6680 (무영향) |
| all aux OFF | 0.0800 | 0.0280 |

**해석:** ge3는 quota 5장 선택이 지배(aux ablation만으론 ge3 안 변함)
**markov 탈락:** pattern_spotlight 필수 · balance_keeper가 markov 불리

■ K-ENGINE-PHASE1 요약 (완료)
- B1 coordinator rollback OK (signal wiring 제거 · pattern_signal.py 보존)
- markov window100 solo FAIL ge3=0.0850 → **롤백(full draws)**
- fusion diag: AUX_PATH_BOTTLENECK · quota+aux 혼합

■ 현재 live stack
_auto_feedback → 3뇌 predict_sets(draws) → aux 1:1 → dynamic_quota(25/60/15→~1/3/1) → DB
(B1 virtual draws **없음**)

■ 다음 후보 (형 GO 전 · 자동 착수 금지)
1. balance_keeper markov 가중 완화 (survival 0.668→0.948 가능성)
2. aux scoring 공식 조정 (ge3 0.08→0.09+ 목표)
3. quota 추가 튜닝 (markov 60%→?)
4. K-ENGINE PHASE2~3 (learn→engine · auto_tune) — fusion ge3 선행

■ 절대 금지
random.choices · _get_draws_before · BOOST_CAPS · engine.py
aux/coordinator 로직 영구 변경(GO 없이) · FINDINGS 무단 갱신 · FAIL→auto-tune

■ 젠스파크 할 일
1. 위 JSON 3종 팩트체크 (KAUX_DIAG · KQUOTA_FIX · KFUSION_BOTTLE_DIAG)
2. 회복 방향 **1개 추천** + 근거 (balance 완화 vs aux formula vs quota)
3. GO 없이 코드·백테 금지
4. 첫줄: [복귀] HEAD=5bba9f3 · 지금=K-AUX-DIAG-DONE · 다음=aux 회복 형 GO 대기
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
