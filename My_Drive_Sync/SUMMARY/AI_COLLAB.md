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

### 최신 상태 (2026-08-01 22:35 KST)
- **HEAD(실측)**: pending commit · SSOT=`kkr2652199-prog/ROK21` · 포트 **7021**
- **지금(판정)**: **K-AUX-DIAG DONE** — baseline ge3=**0.0800** · markov survival **0.668** · worst aux **pattern_spotlight**
- **다음(공식)**: aux ablation 기반 회복 방향(pattern_spotlight/balance_keeper) · **형 GO 대기**

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
| K-FUSION-QUOTA-FIX | 100 | **0.0800** | **FAIL** (>0.09) |
| K-BRAIN-SIGNAL-BACKTEST-100 (방향1 conf) | 100 | **0.0600** | **FAIL** |
| K-HIGHWAY-BACKTEST-100 | 100 | **0.0600** | **FAIL** |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-BRAIN-TUNE-SURVEY | 1182 | best 0.1032 | HOLD |
| K-NEW-ENGINE-STAT-A1 | 200 | 0.1350 (v2=0.1350) | PASS |
| K-BRAIN-PACKAGE QUICK | 200 | 0.125 | PASS |

### 논의 이력 (최신순)
1. **[21:45] K-FUSION-QUOTA-FIX FAIL** — quota 20/60/20 · ge3=0.0800 (+0.02 vs 0.06) · gate 0.09 미달
2. **[19:10] K-BRAIN-SIGNAL-B1 PASS** — virtual draws weights · smoke 10/10 · B1-BACKTEST **형 GO 대기**
2. **[18:55] K-BRAIN-SIGNAL-BACKTEST-100 FAIL** — 방향1 conf blend · ge3=0.0600 · signal_active 100%
3. **[18:00] K-BRAIN-SIGNAL-A1 PASS** — pattern_signal + coordinator conf blend
4. **[17:50] K-HIGHWAY-BACKTEST-100 FAIL** — ge3=0.0600 · PHASE1 FEEDBACK+REFEREE+QUOTA
5. **[16:30] K-BRAIN-LOGIC-UPGRADE** · K-BRAIN-SIGNAL Q1~Q4 설계 검토
6. **[16:10] K-CLEANUP 거부** · C package Phase0~7

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-01 20:10)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.

```
[ROK21 압축복구 · 2026-08-01 · B1-BACKTEST-100 완료]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- HEAD: 4d5df6a (최신: git rev-parse --short HEAD)
- NEXT: K-BRAIN-SIGNAL-TUNE — _MIN_MAX_SIM 또는 B1 롤백 · **형 GO 대기**
- JSON: docs/benchmarks/20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.json
- 보고서: reports/20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.md

■ B1-BACKTEST-100 결과 (커서 실행 완료 · 수정본 지시서 준수)
| 지표 | 값 |
| overall ge3 | **0.0600** (6/100) · **FAIL** |
| virtual_active_rate | **100%** |
| vs 0.0600 | **+0.0000** (dir1·highway 동일) |
| by_brain solo | stat 0.09 · markov 0.13 · review 0.11 |
| by_period draw SSOT | early1135-1159 0.04 · mid1160-1184 0.04 · late1185-1234 0.08 |
| mean_match | 1.63 |

■ SIGNAL 타임라인
[A1+BACKTEST] conf blend → FAIL ge3=0.0600
[B1+BACKTEST] virtual draws → FAIL ge3=0.0600 · virtual 100%
→ signal 레이어 2종 모두 ge3 무개선

■ live stack (B1)
_auto_feedback → get_pattern_signal → make_signal_draws
→ predict_sets(draws_with_signal) → aux(실draws) → dynamic_quota

■ 다음 (TUNE 자동 착수 금지)
K-BRAIN-SIGNAL-TUNE: _MIN_MAX_SIM 0.90→0.85 또는 B1 롤백 · 별도 GO

■ 절대 금지
random.choices · _get_draws_before · BOOST_CAPS · engine.py
aux에 virtual 혼입 · FAIL→TUNE 자동 · FINDINGS 무단 갱신

■ 젠스파크 할 일
1. JSON·보고서 팩트체크 (기억 금지)
2. TUNE vs 롤백 vs STEP3 **1개 추천** + 근거
3. GO 없이 코드·백테 금지
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
