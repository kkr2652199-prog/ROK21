# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: **K-BRAIN-RNG-INDEPENDENT + K-PREDICT-RESET**(형GO) — **WIRE_CONFORMS 9/9**(1216~1235 · 리셋 후 재검증). ④`expand_pool` 이 3뇌를 **한 난수 흐름**으로 돌려 stat 이 markov 를 오염(발권경로는 이미 뇌별 시드리셋인데 pool 경로만 누락) → **뇌마다 `random.seed` 리셋** ⑤pass0 시드를 `seed+draw_no` 로 맞춰 **pool 1~5 = 실제 발권 5세트**(C8 신설) · 뇌별 상수 dict 개방(`POOL_SLOTS/SCORE_WEIGHTS/LEARN_EMA_BY_BRAIN` · **값 전부 동일=성적 무변화**) · **미해결 명시: hint 는 3뇌 공유**(`W_HINT=0.40` · 뇌별 hint 는 성적 주장이라 범위 밖) · DB 3뇌 예측 **7,094행 삭제**(원천 보존 · rare_hits·transition_log 는 회차파생이라 보존)
- 직전: K-REPACK-SIGNAL-WIRE(성적표 뇌별분리·4·5고정제거·3뇌동일 · 7/7) · K-REPACK-SELECT-DIAG(POOL_EQUALS_RANDOM)
- 다음: **선생님 차례** — ①과거학습 뇌(stat) 예측 튜닝 ②뇌별 hint 분리 ③1236+ 자동시스템 배선 중 **형 1건 선택** · 발권가중 금지

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| BASELINE_PIN | **640cb67** | PINNED_BASELINE |
| K-AG verify | **PASS** | KAG JSON |
| 3DB MAX | **1234** | PIN_3db_smoke · KPIN_CLOSE |
| drift | **0** | KAC_doc_drift · KPIN_CLOSE |

## 3) 열린 과제 -> FINDINGS.md
핀=K-Z~AG **고정**. P1~P4 **마감**(K-PIN-CLOSE PASS). K-M/N=**HOLD**. 형 다음 1건.

## 4) 주의 (붕괴 방지)
- 이 레포=ROK21 (kweon 20260726 04:38 복사본). SSOT=ROK21 main
- kweon 은 20260726 `264de3c` 에서 동결. 신규 작업 금지
- 외부 AI 는 ROK21 만 조회할 것
- **성적=BENCH_PROTOCOL.md 준수**
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. mean/best는 null병기·서열단독금지(K-O).
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고. 수집·크롤링은 형 승인 전 금지.

## 5) 더 필요하면
1. **`EXTERNAL_START.md`** (루트 · 외부AI 흐름 1순위)
2. `reports/20260727_KAF_팬아웃잔여정합.md`
3. `RULES_FIXED.md` R35·R36·R37 · `CURSOR_RULES.md` §6
4. `NEXT_ACTIONS.md` · `FINDINGS.md` · `FLOW_BRIEF.md`
