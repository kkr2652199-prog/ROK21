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

### 최신 상태 (2026-08-01 17:50 KST)
- **HEAD(실측)**: `57485db` · SSOT=`kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 **7021** (서버 재기동됨)
- **지금(판정)**: **K-HIGHWAY-BACKTEST-100 FAIL** — overall ge3=**0.0600** · baseline 0.1015 대비 **−0.0415**
- **다음(공식)**: **K-HIGHWAY-PHASE1-HOLD** — 롤백/HOLD/튜닝 **형 GO 대기**
- **WORKSTATE**: IDLE
- **서버**: `python run_v13.py` · http://127.0.0.1:7021/ · 테스트로또 탭에서 확인

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
| K-NEW-ENGINE-STAT-A1 | **PASS** (delta=0) | ENGINE_V2=False 유지 · solo ge3=0.1350 |
| K-BRAIN-TUNE-SURVEY | **HOLD** | best_combo 0.1032 · auto-apply 금지 |
| K-BRAIN-LOGIC-UPGRADE | **설계 검토만** | 젠스파크 4방향 · 커서 Q1~Q5 답변 · 형 GO 전 구현 금지 |
| K-CLEANUP-AND-NEW-ENGINE-PREP | **커서 거부** | engine NotImplementedError 교체 위험 |

### ⚠️ 중단·거부 지시서
- **K-CLEANUP** — 레거시 mv + engine 스켈레톤 → 커서 **실행 거부** (Q1~Q6 반문 · §6 참고)

### 벤치 수치 SSOT (주요 · `docs/benchmarks/*.json`)
| ID | n | ge3 | 판정 |
|----|---|-----|------|
| K-HIGHWAY-BACKTEST-100 | 100 | **0.0600** | **FAIL** |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-BRAIN-TUNE-SURVEY | 1182 | best 0.1032 | HOLD |
| K-NEW-ENGINE-STAT-A1 | 200 | 0.1350 (v2=0.1350) | PASS |
| K-BRAIN-PACKAGE QUICK | 200 | 0.125 | PASS |

### 논의 이력 (최신순)
1. **[17:50] 서버 재기동** — 7021 · 테스트로또 UI 확인용
2. **[17:35] K-HIGHWAY-BACKTEST-100 FAIL** — ge3=0.0600 · learn adj 누적 OK · quota 40/40/20
3. **[17:25] K-HIGHWAY-QUOTA** — dynamic_brain_quota · PHASE1 코드 완료
4. **[17:20] K-HIGHWAY-REFEREE** — aux_referee score_set 실동작
5. **[17:15] K-HIGHWAY-FEEDBACK** — _auto_feedback live 연결
6. **[16:30] K-BRAIN-LOGIC-UPGRADE** — 젠스파크 설계 · 커서 Q1~Q5 · A1 stat bench PASS
7. **[16:10] K-CLEANUP 거부** · TUNE-SURVEY HOLD · C package Phase0~7

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-01 17:50)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.

```
[ROK21 압축복구 · 2026-08-01 · K-HIGHWAY까지]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- HEAD: 57485db
- NEXT: K-HIGHWAY-PHASE1-HOLD — BACKTEST-100 FAIL · 롤백/HOLD/튜닝 **형 GO 대기**
- 읽을 파일: EXTERNAL_START.md · NEXT_ACTIONS.md · AI_COLLAB.md §3·§6
- 보고서: reports/20260801_KHIGHWAY_*.md · 20260801_KHIGHWAY_BACKTEST_100.md

■ 오늘 타임라인 (형 GO 기준)

[오전~오후] C package Phase0~7 · TUNE-SURVEY HOLD · CLEANUP 지시서 → 커서 거부
[설계] K-BRAIN-LOGIC-UPGRADE — stat/markov/review/coordinator 4방향 · 커서 Q1~Q5 답변
[A1] K-NEW-ENGINE-STAT-A1 PASS (ge3=0.1350 delta=0 · ENGINE_V2=False)

[K-HIGHWAY-PHASE1 · 형 GO · 코드 push 완료]
1. FEEDBACK — coordinator _auto_feedback · prev회차 apply_feedback
2. REFEREE   — aux_referee score_set → get_referee_weights()
3. QUOTA     — dynamic_brain_quota (고정 markov3/stat1/review1 폐지)
4. BACKTEST-100 — draw1135~1234 n=100 walk-forward

■ BACKTEST-100 결과 (SSOT JSON)
- overall ge3=0.0600 (6/100) · mean=1.63 · **FAIL**
- vs K-BACKTEST-FULL-C baseline 0.1015 → **delta −0.0415**
- by_brain solo: stat 0.09 · markov 0.13 · review 0.11
- by_period: early 0.04 · mid 0.04 · late 0.08 (collapse 없음)
- quota avg: stat 40% · markov 40% · review 20%
- learn 루프 **실동작** — ending_digit miss 다수 · adj cap(carry0.2/ending0.3) 도달

■ 현재 live 코드 경로
run_coordinated_prediction(N):
  _auto_feedback(N)  ← K-HIGHWAY-FEEDBACK
  → 3뇌×5 predict → aux 1:1
  → dynamic_brain_quota  ← K-HIGHWAY-QUOTA (referee 가중)
  → 5장 DB 저장

■ 형이 결정해야 할 것 (젠스파크 제안 전 확인)
A) PHASE1 HOLD — 코드 유지 · 추가 튜닝 survey
B) PHASE1 롤백 — dynamic_brain_quota → 고정 markov3/stat1/review1 복원
C) PHASE1 부분 롤백 — FEEDBACK만 유지 / QUOTA만 롤백 등
D) K-BRAIN-LOGIC-UPGRADE 착수 — engine 가중치 (별 트랙 · A1~A3 순)

■ 절대 금지 (동결·규칙)
- random.choices · _get_draws_before · BOOST_CAPS 수정
- kweon(D:\3kweon) 쓰기·push
- 형 GO 없이 코드 변경·지시서 실행
- 수치=docs/benchmarks/*.json만 (기억 금지)

■ K-CLEANUP (이전 · still 거부됨)
engine NotImplementedError 교체 · AUX_MODULES=[] · 24파일 mv → 커서 거부
Q1~Q6 답변 또는 철회 필요 시 §3 참고

■ 서버 (형 UI 확인)
http://127.0.0.1:7021/ → 테스트로또 탭
※ BACKTEST-100이 learn_state DB reset+99회 feedback 적용 — UI 예측에 영향 가능

■ 젠스파크가 지금 할 일
1. 위 BACKTEST FAIL 원인 분석 초안 (ending_digit miss 폭주? quota shift? feedback adj?)
2. A/B/C/D 옵션 중 형에게 **1개 추천** + 근거 (수치 JSON 인용)
3. 형 GO 없이 지시서·코드 변경 금지
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
