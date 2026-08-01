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

### 최신 상태 (2026-08-01 19:10 KST)
- **HEAD(실측)**: `38ebe73` · SSOT=`kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 **7021**
- **지금(판정)**: **K-BRAIN-SIGNAL-B1 PASS** — virtual draws weights 주입 · smoke 10/10
- **다음(공식)**: **K-BRAIN-SIGNAL-B1-BACKTEST-100** — n=100 walk-forward · **형 GO 대기**
- **WORKSTATE**: IDLE

### K-BRAIN-SIGNAL-B1 (형 GO · 방향2 weights blend · PASS)
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
| dynamic quota avg | stat 40% · markov 40% · review 20% |
| learn 루프 | **동작 확인** — draw1234 rc=99 · carry/ending adj cap 도달 |

**형 결정 대기:** PHASE1 **HOLD** vs **롤백**(고정 쿼터 markov3/stat1/review1) vs **튜닝**

### 병렬 트랙 (별도 · PHASE1과 독립)
| ID | 판정 | 비고 |
|----|------|------|
| **K-BRAIN-SIGNAL** | **B1 PASS** | virtual draws weights · B1-BACKTEST **형 GO 대기** |
| K-NEW-ENGINE-STAT-A1 | **PASS** (delta=0) | ENGINE_V2=False 유지 · solo ge3=0.1350 |
| K-BRAIN-TUNE-SURVEY | **HOLD** | best_combo 0.1032 · auto-apply 금지 |
| K-BRAIN-LOGIC-UPGRADE | **설계 검토만** | 젠스파크 4방향 · 커서 Q1~Q5 답변 · 형 GO 전 구현 금지 |
| K-CLEANUP-AND-NEW-ENGINE-PREP | **커서 거부** | engine NotImplementedError 교체 위험 |

### ⚠️ 중단·거부 지시서
- **K-CLEANUP** — 레거시 mv + engine 스켈레톤 → 커서 **실행 거부** (Q1~Q6 반문 · §6 참고)

### 벤치 수치 SSOT (주요 · `docs/benchmarks/*.json`)
| ID | n | ge3 | 판정 |
|----|---|-----|------|
| K-BRAIN-SIGNAL-BACKTEST-100 (방향1 conf) | 100 | **0.0600** | **FAIL** |
| K-HIGHWAY-BACKTEST-100 | 100 | **0.0600** | **FAIL** |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-BRAIN-TUNE-SURVEY | 1182 | best 0.1032 | HOLD |
| K-NEW-ENGINE-STAT-A1 | 200 | 0.1350 (v2=0.1350) | PASS |
| K-BRAIN-PACKAGE QUICK | 200 | 0.125 | PASS |

### 논의 이력 (최신순)
1. **[19:10] K-BRAIN-SIGNAL-B1 PASS** — virtual draws weights · smoke 10/10 · B1-BACKTEST **형 GO 대기**
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

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-01 19:10)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.

```
[ROK21 압축복구 · 2026-08-01 · K-BRAIN-SIGNAL-B1까지]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- HEAD: 38ebe73
- NEXT: K-BRAIN-SIGNAL-B1-BACKTEST-100 — B1 stack n=100 · **형 GO 대기**
- 읽을 파일: EXTERNAL_START.md · NEXT_ACTIONS.md · AI_COLLAB.md §3·§6
- 보고서(필수):
  reports/20260801_KBRAIN_SIGNAL_B1.md
  reports/20260801_KBRAIN_SIGNAL_BACKTEST_100.md
  reports/20260801_KBRAIN_SIGNAL_A1.md
  reports/20260801_KHIGHWAY_BACKTEST_100.md
- 수치 JSON: docs/benchmarks/20260801_KBRAIN_SIGNAL_BACKTEST_100.json

■ 형의 핵심 의도 (K-BRAIN-SIGNAL)
"현재 상황과 비슷한 과거 회차 → 다음 회차 번호 분포를 예측 신호로 활용"
→ 기존 3뇌는 유사 패턴 탐색 없음 → adj(carry/ending)만으로 ge3 개선 실패

■ SIGNAL 타임라인 (형 GO)

[설계] K-BRAIN-SIGNAL Q1~Q4 — pattern_signal.py 신규 · coordinator hook
[A1 PASS] get_pattern_signal · confidence 0.85/0.15 blend
[BACKTEST-100 FAIL · 방향1] ge3=0.0600 · signal_active=100% · highway와 동일
  → 원인: signal이 confidence(점수)만 바꿈 · 번호 선택 무영향
[B1 PASS · 방향2] make_signal_draws → virtual draws×3 → draws_with_signal
  → predict_sets(draws_with_signal) · engine weights에 signal 주입
  → conf blend **완전 제거** · smoke virtual 10/10

■ 현재 live stack (B1 · HEAD fedf174+)
run_coordinated_prediction(N):
  _auto_feedback(N)                    ← K-HIGHWAY-FEEDBACK
  → get_pattern_signal(draws)
  → make_signal_draws → draws_with_signal = virtual + draws
  → predict_sets(draws_with_signal)  ← B1 weights 주입
  → aux 1:1 scoring
  → dynamic_brain_quota 5장          ← K-HIGHWAY-QUOTA
  → DB 저장

■ 벤치 수치 SSOT (기억 금지 · JSON만)
| ID | ge3 | signal_active | 판정 |
| K-BRAIN-SIGNAL-BACKTEST-100 (방향1) | 0.0600 | 100% | FAIL |
| K-HIGHWAY-BACKTEST-100 (PHASE1) | 0.0600 | — | FAIL |
| K-BACKTEST-FULL-C baseline | 0.1015 | — | FAIL |

방향1 FAIL 상세: by_brain stat0.09 markov0.13 review0.11 · by_period early0.04 mid0.04 late0.08

■ 병렬 대기 (형 GO 필요)
A) K-BRAIN-SIGNAL-B1-BACKTEST-100 — B1 stack n=100 (다음 STEP)
B) K-HIGHWAY-PHASE1-HOLD — 롤백/HOLD/튜닝 (별도 트랙)
C) K-BRAIN-SIGNAL-TUNE — _MIN_MAX_SIM 0.90→0.85 (B1-BACKTEST 후)

■ STEP 로드맵 (젠스파크 제안용)
STEP1 B1-BACKTEST-100 ← **지금 여기 · 형 GO 대기**
  PASS → STEP2 파라미터 튜닝 (_MIN_MAX_SIM·k)
  FAIL → _MIN_MAX_SIM 0.90→0.85 재검증
→ STEP3 markov start_nums 다각화
→ STEP4 warm-up quota
→ STEP5 FULL n=1182

■ 절대 금지 (동결·규칙)
- random.choices · _get_draws_before · BOOST_CAPS 수정
- stat/markov/review engine.py 직접 수정 (B1은 coordinator+pattern_signal만)
- kweon(D:\3kweon) 쓰기·push
- 형 GO 없이 B1-BACKTEST·TUNE 자동 착수
- 수치=docs/benchmarks/*.json만

■ UI
http://127.0.0.1:7021/ 테스트로또 · draw 1235 예측 5장 (이전 BACKTEST reset 후)

■ 젠스파크가 지금 할 일
1. reports/20260801_KBRAIN_SIGNAL_B1.md + BACKTEST JSON 팩트체크
2. B1-BACKTEST-100 지시서 초안 (PASS/FAIL 기준 · ge3 vs 0.0600)
3. 방향1 FAIL→B1 전환 근거를 형에게 3줄 요약
4. 형 GO 없이 코드·백테 실행 금지
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
