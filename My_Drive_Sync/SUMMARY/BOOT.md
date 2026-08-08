# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: **K-REPACK-SIGNAL-WIRE**(형GO · 배선수정) — **WIRE_CONFORMS 7/7**. 몰아주기가 설계와 어긋난 3건 수정: ①3뇌가 `pos/num EMA` **한 장 공유**(`for _tag` 로 태그 버림) → **뇌별 분리** + `brain_signal()` 해석기 ②`for sn in (4,5)` **하드코딩** → `signal_top_set_nos()` 로 **위치 EMA 상위 2세트**(실측 4·5 이탈률 markov 1.000/review 1.000/stat 0.900) ③markov 만 pool 슬롯 0개 → **3뇌 동일**. 검증 1216~1235: C1 뇌별분리·C2 신호상위·C2b 4·5이탈·C3 3뇌동일·C4 세트통째보존·C5 결정성·C6 미래참조없음. **성적 주장 아님 → R38 게이트 대상 아님** · 발권경로(`coordinator`) 무변경 · 보존 슬롯수 2는 구 4·5 와 동수 유지(장수는 튜닝이라 범위 외)
- 직전: K-REPACK-SELECT-DIAG(POOL_EQUALS_RANDOM · pool 10세트=무작위10장 · 「좋은세트 놓침」 전제 오독 확인) · K-SEED-AVERAGE-DESIGN(배선안함)
- 다음: **선생님 먼저** — ①과거학습 뇌(stat) 예측 튜닝 ②당첨금(인기회피) 축 ③1236+ 전향적 EV로그 중 **형 1건 선택** · 발권가중 금지

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
