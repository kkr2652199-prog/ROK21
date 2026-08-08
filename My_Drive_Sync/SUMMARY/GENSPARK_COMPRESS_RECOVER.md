# GENSPARK_COMPRESS_RECOVER — 젠스파크 세션 압축 복구 SSOT

> **압축되면 채팅 기억 버리고 이 파일 + EXTERNAL_START만 신뢰.**
> 형 큐: `동생, GENSPARK_COMPRESS_RECOVER 붙여넣을게. JSON만 다시 읽어.`
> 자동생성 HEAD=`0789266` · R37 `sync_all_resume_docs()`

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
[ROK21 젠스파크 압축복구 · HEAD=0789266]

■ 신뢰 규칙 (필수)
- 압축된 채팅 기억·긴 요약 = **불신**. 수치·판정은 아래 raw URL JSON만.
- 보고서 '읽었다'고 말해도 JSON을 다시 fetch하기 전엔 확정 금지.
- 당첨P↑·wire GO·quota 변경 = 형 명시 승인 전 금지.

■ LIVE
- HEAD: 0789266 · WORK=IDLE · SSOT=ROK21/7021
- 지금: **K-BRAIN-RNG-INDEPENDENT + K-PREDICT-RESET**(형GO) — **WIRE_CONFORMS 9/9**(1216~1235 · 리셋 후 재검증). ④`expand_pool` 이 3뇌를 **한 난수 흐름**으로 돌려 stat 이 markov 를 오염(발권경로는 이미 뇌별 시드리셋인데 pool 경로만 누락) → **뇌마다 `random.seed` 리셋** ⑤pass0 시드를 `seed+draw_no` 로 맞춰 **pool 1~5 = 실제 발권 5세트**(C8 신설) · 뇌별 상수 dict 개방(`POOL_SLOTS/SCORE_WEIGHTS/LEARN_EMA_BY_BRAIN` · **값 전부 동일=성적 무변화**) · **미해결 명시: hint 는 3뇌 공유**(`W_HINT=0.40` · 뇌별 hint 는 성적 주장이라 범위 밖) · DB 3뇌 예측 **7,094행 삭제**(원천 보존 · rare_hits·transition_log 는 회차파생이라 보존)
- 직전: K-REPACK-SIGNAL-WIRE(성적표 뇌별분리·4·5고정제거·3뇌동일 · 7/7) · K-REPACK-SELECT-DIAG(POOL_EQUALS_RANDOM)
- BOOT다음: **선생님 차례** — ①과거학습 뇌(stat) 예측 튜닝 ②뇌별 hint 분리 ③1236+ 자동시스템 배선 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-BRAIN-INDEPENDENT-NEXT-PICK — 형 지시 3건 **완료** — ⑴ **나머지 2뇌 독립**: 「3뇌 동일 배선」은 앞 턴에 됐지만 **독립은 아니었다**. `expand_pool` 이 `_live_candidates` 로 3뇌를 **한 난수 흐름에서 순차 호출**해 앞 뇌의 뽑기 소비량이 뒤 뇌 결과를 바꿨다(stat→markov 오염). 발권경로 `coordinator._seed_independent_brain` 은 이미 뇌별 시드리셋인데 **pool 경로만 누락**이었다 → `expand_pool` 이 `BRAIN_TAGS` 를 직접 돌며 뇌마다 시드 리셋. 덤으로 pass0 시드를 발권 규칙(`42+draw_no`)과 맞춰 **pool 1~5 = 실제 발권 5세트** 확보(C8 신설 · 분석과 발권이 어긋나던 것도 해소). 뇌별 상수 dict(`POOL_SLOTS_BY_BRAIN`·`SCORE_WEIGHTS_BY_BRAIN`·`LEARN_EMA_BY_BRAIN`) 개방했으나 **값은 3뇌 동일 = 성적 무변화**(차별화는 게이트 통과 후) · 검증 **9/9**(1216~1235 · 리셋 후 재실행) · ⑵ **DB 리셋**: 테스트로또 DB 3뇌 예측 **7,094행 삭제** · 원천데이터 보존 · `rare_bundle_hits`·`transition_log` 는 회차 파생이라 3뇌 예측 아님 → 보존 · ⑶ **미해결 1건 명시**: `HINT_SHARED_ACROSS_BRAINS=True` — `_build_hint` 하나를 3뇌에 그대로 넘기고 `W_HINT=0.40` 이라 **점수의 40%가 3뇌 동일**. 완전 독립이 아니다. 형 확인 후 1건 선택 — **①과거학습 뇌(stat) 예측 튜닝**(권장 · 형이 말한 「과거 회차 분석해 번호 예측하는 뇌 튜닝」 · 통로가 뚫렸으니 이제 개선이 몰아주기까지 전달됨 · 튜닝 지점 후보는 아래 메모) / ②뇌별 hint 분리(남은 마지막 공유축 · 단 어느 hint 가 어느 뇌에 맞는지는 데이터로 정해야 하므로 게이트 필요) / ③1236+ 회차별 자동시스템 배선(형이 「이후 패치」로 미뤄둔 건) / ④트랙정지
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
- `20260808_KREPACK_SIGNAL_WIRE_VERIFY` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KREPACK_SIGNAL_WIRE_VERIFY.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KREPACK_SIGNAL_WIRE_VERIFY.md
- `20260808_KPREDICT_RESET` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KPREDICT_RESET.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KPREDICT_RESET.md
- `20260808_KREPACK_SELECT_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KREPACK_SELECT_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KREPACK_SELECT_DIAG.md
- `20260808_KREPACK_SELECT_DIAG_raw` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KREPACK_SELECT_DIAG_raw.json
- `20260808_KSEED_AVERAGE_DESIGN` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSEED_AVERAGE_DESIGN.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KSEED_AVERAGE_DESIGN.md
- `20260808_KSEED_AVERAGE_DESIGN_raw` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSEED_AVERAGE_DESIGN_raw.json
- `20260808_KSTAT_NOISE_SOURCE` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260808_KSTAT_NOISE_SOURCE.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260808_KSTAT_NOISE_SOURCE.md

■ 진입 파일
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/FLOW_BRIEF.md

■ 복구 후 할 일
1. 첫줄: [복귀] HEAD=0789266 · 지금=**K-BRAIN-RNG-INDEPENDENT + K-PREDICT-RESET**(형GO) — **WIRE_CONFORMS 9/9**(1216~1235 · 리셋 후 재검증). ④`expand_pool` 이 3뇌를 **한 난수 흐름**으로 돌려 stat 이 markov 를 오염(발권경로는 이미 뇌별 시드리셋인데 pool 경로만 누락) → **뇌마다 `random.seed` 리셋** ⑤pass0 시드를 `seed+draw_no` 로 맞춰 **pool 1~5 = 실제 발권 5세트**(C8 신설) · 뇌별 상수 dict 개방(`POOL_SLOTS/SCORE_WEIGHTS/LEARN_EMA_BY_BRAIN` · **값 전부 동일=성적 무변화**) · **미해결 명시: hint 는 3뇌 공유**(`W_HINT=0.40` · 뇌별 hint 는 성적 주장이라 범위 밖) · DB 3뇌 예측 **7,094행 삭제**(원천 보존 · rare_hits·transition_log 는 회차파생이라 보존) · 다음=K-BRAIN-INDEPENDENT-NEXT-PICK
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

_generated: 0789266_
