# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: **K-REPACK-SELECT-DIAG**(stat 단독 · 53~1235 n1183 × seed5 = 5915 · 309초) — **POOL_EQUALS_RANDOM**: pool 10세트 최고 **0.2152** = 무작위 **10장** null **0.2143**(±0.0234) 초과False · 몰아주기 5장 0.1190 = 무작위 5장 null 0.1136 초과False ⇒ **20260804 「pool최고 0.245 vs 몰0.125 = 좋은세트 놓침」은 오독 · 실체는 10장 vs 5장 산수** · 사전특성 11개 **Spearman 최대 |0.0088|** · 특성상위5 선별 11개 전부 몰아주기 이하(최선 Δ−0.000507 · R38 UNDECIDABLE) → **선별 재설계 근거 없음 · 몰아주기 구조 유지**
- 직전: K-SEED-AVERAGE-DESIGN(NOISE_CUT_NOT_ESTABLISHED · √R 불성립 1.38배 · 회차로 사면 5.99배 싸다 → 배선안함) · R39 신설
- 다음: ①당첨금(인기회피) 축 설계 ②다른 특성축 탐색(세트궁합·짝동시출현) ③1236+ 전향적 EV로그 중 **형 1건 선택** · 발권가중 금지

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
