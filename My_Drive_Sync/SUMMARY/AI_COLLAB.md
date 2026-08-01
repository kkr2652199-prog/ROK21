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

### 최신 상태 (2026-08-01 16:16 KST)
- **HEAD(실측)**: `a076cdd` · SSOT=`kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 **7021**
- **지금(완료)**: **K-BRAIN-TUNE-SURVEY** SURVEY OK — best_combo ge3=**0.1032** · live_baseline 0.1218 미달 · **APPLY HOLD**
- **다음(공식)**: **K-BRAIN-TUNE-APPLY** — survey HOLD 권고 · **형 GO 대기** · auto-apply 금지
- **WORKSTATE**: IDLE
- **C package production stack (연결 완료·변경 HOLD)**:
  ```
  coordinator → stat/markov/review_brain.predict.run()
    → engine.generate → aux_hint rerank (0.15)
    → diversity.pick → aux 1:1 scoring → set_no_asc wire 5장
  ```
  - `HINT_WEIGHT=0.15` · `LEARN_WIRED=True` · `AUX_1TO1_ENABLED=True`
  - Phase0~7 **PASS** · FULL ge3=0.1015 (**FAIL** vs live 0.1218) · wire/repack **HOLD**

### ⚠️ 중단된 지시서 (2026-08-01 · 커서 **미실행**)
- **ID**: `K-CLEANUP-AND-NEW-ENGINE-PREP` → `K-NEW-ENGINE-STAT` (외부 AI 초안)
- **내용 요지**: 레거시 24파일 `_unused/` git mv · `engine.py` 3뇌를 `NotImplementedError` v2 스켈레톤으로 **교체** · `AUX_MODULES=[]` · `random.choices` 신규 알고리즘 예고
- **커서 판정**: **흐름 불일치 → 실행 거부** (형 GO 없음 · NEXT 무단 전환 · 구동 경로 파괴)
- **외부 AI 압축**: 위 지시서 작성 맥락·SSOT NEXT·커서 반문(Q1~Q6)이 세션에서 유실됨 → **§6 압축복구 패킷** 참고

### 벤치 수치 SSOT (20260801 · `docs/benchmarks/*.json`)
| ID | n | ge3 | 판정 |
|----|---|-----|------|
| K-BRAIN-PACKAGE COMPLETE (QUICK) | 200 | 0.125 | PASS |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-WIRE-SELECT-FULL | 1182 | conf_top5 0.1117 · set_no_asc 0.1015 | SURVEY · wire HOLD |
| K-BRAIN-TUNE-SURVEY | 1182 | best_combo **0.1032** | SURVEY · **APPLY HOLD** |

### 논의 이력 (최신순)
1. **[16:10] K-CLEANUP 지시서 커서 검토** — SSOT NEXT 불일치 · engine NotImplementedError 교체 위험 · Q1~Q6 반문 작성 · **실행 중단**
2. **[16:00] K-BRAIN-TUNE-SURVEY 완료** — FULL n=1182 ~28분 · P0 aux_hint_top5=0.1091 · APPLY HOLD · `reports/20260801_KBRAIN_TUNE_SURVEY.md`
3. **[15:30] SUMMARY commit+push** — BOOT/NEXT/RESTORE/STATUS 갱신 · HEAD `a076cdd`
4. **[14:00] K-BACKTEST-FULL-C FAIL** — C package FULL ge3=0.1015 · QUICK collapse −0.0235
5. **[13:00] K-BRAIN-PACKAGE Phase0~7 COMPLETE** — 3뇌 패키지 coordinator 연결 · ge3 QUICK 0.125
6. **[12:00] K-WIRE-SELECT / QUOTA-GAP survey** — QUICK↑ FULL collapse 패턴 · wire GO=wait
7. **[이전] TESTLOTTO UI/신호/repack 라운드** — `20260730_*` 보고서 참고

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-01)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.

```
[ROK21 압축복구 · 2026-08-01]

■ SSOT (GitHub kkr2652199-prog/ROK21 · main)
- HEAD: a076cdd
- NEXT(공식 1건): K-BRAIN-TUNE-APPLY — survey HOLD · 형 GO 시 wire/hint/lb A/B만 · auto-apply 금지
- WORK: IDLE
- 읽을 파일: EXTERNAL_START.md · NEXT_ACTIONS.md · AI_COLLAB.md §3·§6

■ 방금까지 완료된 일 (코드 변경 없음 · survey만)
1. K-BRAIN-PACKAGE Phase0~7 — 3뇌 패키지(stat/markov/review_brain) coordinator 연결 완료
2. K-BACKTEST-FULL-C — FULL n=1182 ge3=0.1015 FAIL (QUICK 0.125→FULL collapse)
3. K-BRAIN-TUNE-SURVEY — P0/P1/P2 sweep · best_combo ge3=0.1032 · APPLY recommendation=HOLD
   근거 JSON: docs/benchmarks/20260801_KBRAIN_TUNE_SURVEY.json

■ production stack (현재 live · 건드리지 말 것)
coordinator → stat/markov/review_brain.predict.run()
  → engine.generate (동작 중!) → aux_hint rerank(0.15)
  → diversity.pick → aux 1:1 → set_no_asc wire 5장
플래그: HINT_WEIGHT=0.15 · LEARN_WIRED=True · AUX_1TO1_ENABLED=True

■ 네(젠스파크)가 작성했던 K-CLEANUP-AND-NEW-ENGINE-PREP — 커서가 실행 거부함
이유:
- NEXT_ACTIONS=K-BRAIN-TUNE-APPLY(형 GO 대기)인데 무단으로 CLEANUP→NEW-ENGINE 전환
- stat/markov/review engine.py 를 NotImplementedError 스켈레톤으로 교체 → 예측 즉시 불능
- aux 4파일 _unused 이동 + AUX_MODULES=[] → predict.py의 aux_balance_keeper import·1:1 aux 붕괴
- predict_statistical/markov/fusion 등 17파일 이동 → routes/engine/data_service 등 live import 다수
- v2 docstring의 random.choices = ROK21 동결 토큰(B단계 전 수정 금지)
- TUNE-SURVEY HOLD(유지 권고) 직후 대규모 엔진 교체는 정반대

■ 커서 반문 — 네가 답해야 할 Q1~Q6
Q1. 형 GO·NEXT 교체 없이 CLEANUP 지시서를 쓴 승인 근거는?
Q2. Phase0~7 검증 stack을 NotImplementedError로 바꾸는 목적? baseline 0.1015/0.1218과 관계?
Q3. aux_balance_keeper 직접 import·AUX_1TO1=True 유지 계획?
Q4. 17파일 이동 시 전체 import 그래프·7021 smoke 계획?
Q5. random.choices 동결 해제(형 B단계 GO) 전제인가?
Q6. HEAD 53c20b8→실측 a076cdd 불일치 — TUNE-SURVEY 후 최신 BOOT 읽고 재작성 의향?

■ 지금 네가 해야 할 일 (방향 확정 전)
1. Q1~Q6에 답하거나, CLEANUP 지시서 철회·수정
2. 형 GO 없이 K-NEW-ENGINE-STAT / engine 교체 / git mv 지시 금지
3. 공식 NEXT 따라갈 경우: K-BRAIN-TUNE-APPLY 지시서 초안
   - 전제: TUNE-SURVEY HOLD → wire set_no_asc·hint 0.15·look_back 52 유지 권고
   - 형 GO 시에만: aux_hint_top5 wire 단독 A/B (best 단일축 +0.0050p · p=0.702)
4. CLEANUP을 다시 원하면: 별도 설계안 — (a) engine 교체 없이 deprecated만 _unused (b) import 그래프 grep (c) smoke (d) 형 GO 선행

■ 동결·금지 (ROK21)
- random.choices · _get_draws_before · boost cap(carry 0.2/ending 0.3/overdue 0.2)
- kweon(D:\3kweon) 쓰기·push 금지
- 수치=docs/benchmarks/*.json만 (기억 금지)
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
