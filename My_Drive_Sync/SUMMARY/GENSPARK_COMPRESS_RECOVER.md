# GENSPARK_COMPRESS_RECOVER — 젠스파크 세션 압축 복구 SSOT

> **압축되면 채팅 기억 버리고 이 파일 + EXTERNAL_START만 신뢰.**
> 형 큐: `동생, GENSPARK_COMPRESS_RECOVER 붙여넣을게. JSON만 다시 읽어.`
> 자동생성 HEAD=`0fe62b1` · R37 `sync_all_resume_docs()`

## 0) 왜 필요한가

- 젠스파크가 세션 압축하면 긴 분석·보고서 해석이 **유실/왜곡**될 수 있다.
- 압축 직후 에이전트가 '보고서를 읽었다'고 해도, 그 내용은 **신뢰 불가**.
- 복구 = **GitHub raw 재페치** + 아래 붙여넣기 블록.
- **기억 스토리보드:** `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md` (**Cursor**)

## 1) 형 → 젠스파크 30초 복구 절차

1. 이 파일(또는 아래 ``` 블록) 전체를 채팅에 붙여넣기
2. `EXTERNAL_START.md` + `GENSPARK_MEMORY_RESTORE_CURSOR.md` raw 함께
3. 에이전트에게: **증거 체인 JSON을 fetch한 뒤 [복귀] 한 줄 + 팩트체크 표**
4. 압축 전 장문과 다르면 JSON을 따르고, 틀린 기억은 명시적으로 폐기 선언

## 2) 붙여넣기 블록 (자동)

```
[ROK21 젠스파크 압축복구 · HEAD=0fe62b1]

■ 신뢰 규칙 (필수)
- 압축된 채팅 기억·긴 요약 = **불신**. 수치·판정은 아래 raw URL JSON만.
- 보고서 '읽었다'고 말해도 JSON을 다시 fetch하기 전엔 확정 금지.
- 당첨P↑·wire GO·quota 변경 = 형 명시 승인 전 금지.

■ LIVE
- HEAD: 0fe62b1 · WORK=IDLE · SSOT=ROK21/7021
- 지금: **K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가**
- 직전: R38 게이트 강제 가동(k_gate 공용모듈 · COMPLIANT) · DECISION-GATE(win26/mix0.8=NOISE_SELECTION_CONFIRMED · 순서불변 2.429e-17)
- BOOT다음: ①1236+ 전향적 EV로그 ②stat 잡음저감(팽창1.27 · markov 0.73 대비 최악) ③legacy 판정 게이트 소급적용 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-NOISE-FLOOR-NEXT-PICK — 잡음 하한 확정 완료(**바닥 b=0.010127** · FULL-WF Δ+0.0047 이 바닥 미만 → 적중축은 표본을 늘려도 판정 불가로 확정) 형 확인 후 1건 선택 — **①회차 1236+ 전향적 EV 로그 시작**(권장 · 적중축이 닫혔으므로 유일하게 남은 인기회피축을 개입 없이 검증) / ②stat 잡음 저감 진단(팽창 stat 1.2739 vs markov 0.7329 — 왜 stat만 잡음을 더하는지 원인 특정) / ③legacy 132건 중 상수·배선에 실제 영향 준 판정만 게이트 소급적용 / ④트랙정지
- kweon(D:\3kweon) 동결 · 1~3군 미기록

■ 기억 스토리보드 (보고서 읽기 순서 · Cursor)
1) GENSPARK_MEMORY_RESTORE_CURSOR.md ← 압축복원 가이드 먼저
2) DIRECTION_BRIEF_CURSOR → 수집우선·교체성급철회
3) KTRANSITION_FULL.json → Δ+0.172 STRONG(미세)
4) COLLECT_DESIGN.json → transition_log PASS · mean≈1.998(N→N+1)
5) FACTCHECK/RANDOM_SAMPLE → 단건 hit=2 · 과장금지
※ collect≈1.998 ≠ FULL 2.172 (지표 다름·버그아님)

■ 증거 체인 (반드시 재페치 · 우선순위↑)
- `20260805_GENSPARK_MEMORY_RESTORE_CURSOR` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md
- `20260805_KTRANSITION_COLLECT_DESIGN` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KTRANSITION_COLLECT_DESIGN.md
- `20260805_KTRANSITION_FULL` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KTRANSITION_FULL.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KTRANSITION_FULL.md
- `20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md
- `20260808_KGATE_COMPLIANCE` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KGATE_COMPLIANCE.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KGATE_COMPLIANCE.md
- `20260808_KSTAT_SEED_NOISE_FLOOR_raw` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSTAT_SEED_NOISE_FLOOR_raw.json
- `20260808_KSTAT_SEED_NOISE_FLOOR` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSTAT_SEED_NOISE_FLOOR.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KSTAT_SEED_NOISE_FLOOR.md
- `20260808_KSTAT_DECISION_GATE` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSTAT_DECISION_GATE.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KSTAT_DECISION_GATE.md
- `20260808_KPAST_LEARN_AUDIT_DIMS` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KPAST_LEARN_AUDIT_DIMS.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KPAST_LEARN_AUDIT_DIMS_ADVISORY.md
- `20260808_KPAST_LEARN_EV_RELABEL` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KPAST_LEARN_EV_RELABEL.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KPAST_LEARN_EV_RELABEL.md
- `20260808_KPAST_LEARN_SCORE_RULE_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KPAST_LEARN_SCORE_RULE_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KPAST_LEARN_SCORE_RULE_DIAG.md
- `20260808_KPAST_LEARN_DETAIL_KEEP` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KPAST_LEARN_DETAIL_KEEP.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KPAST_LEARN_DETAIL_KEEP.md

■ 진입 파일
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/FLOW_BRIEF.md

■ 복구 후 할 일
1. 첫줄: [복귀] HEAD=0fe62b1 · 지금=**K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가** · 다음=K-NOISE-FLOOR-NEXT-PICK
2. MEMORY_RESTORE → COLLECT_DESIGN → FULL JSON fetch → 표로 팩트체크
3. 압축 전 장문과 불일치하면 **JSON 승** · 채팅 기억 폐기
4. 승인 없으면 장문 지시서 금지 · 질문 1개

■ 금지
random.choices · _get_draws_before · boost상한 · kweon쓰기
engine wire(GO없이) · auto-tune · 채팅기억으로 수치 인용
stat 즉시교체 클레임(수집 STEP 완료·교체는 STEP3)
```

## 3) 추가 아이디어 (운영)

| 아이디어 | 설명 |
|----------|------|
| 이중 붙여넣기 | 짧은 LIVE(EXTERNAL_START) + 이 RECOVER 증거체인 |
| 기억 스토리보드 | MEMORY_RESTORE_CURSOR.md 시간순 읽기 |
| 세션 지문 | HEAD+지금ID를 매 답 첫줄에 강제 → 압축 감지 |
| 불신 선언 템플릿 | `압축감지: 채팅기억 폐기 · JSON 재페치 시작` |
| 보고서≠수치 | MD는 해설, 판정·숫자는 항상 `docs/benchmarks/*.json` |
| 커서 동시갱신 | 매 push 후 sync가 이 파일을 갱신(본 자동화) |
| 드라이브 사본 | `My_Drive_Sync/커서보고서`의 동명 MD도 교차확인 |

## 4) 파일 지도

| 용도 | raw |
|------|-----|
| 본 복구 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` |
| **기억복원가이드** | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md` |
| LIVE | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 대화요약 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |

_generated: 0fe62b1_
