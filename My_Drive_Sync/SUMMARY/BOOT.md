# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: **SEED-NOISE-FLOOR v2**(n1183·seed24) — **FLOOR_NOT_ESTABLISHED**: 바닥 0.010127→**0.005087** · 잭나이프 95%CI **[−0.008244,0.018012]** 0 포함 → **「표본 늘려도 영원히 판정 불가」 철회**, 올바른 표현은 **「가용데이터로는 불가」** · **R39 신설**(σ 비교 전 σ/√(2(k−1)) 선검증 강제 · `tools/k_precision.py` 7/7)
- 직전: K-STAT-NOISE-SOURCE(잡음 유입점 **'뽑기' 확정** · 뇌별 팽창차 구분가능쌍 **0/3** → stat 전용대책 근거 없음 · 반사실 결정적절단 짝지은 p=0.7156 무손해)
- 다음: ①1236+ 전향적 EV로그 ②seed 평균화 설계(형 GO 필요) ③바닥 0 여부 확정(seed 대폭 증량) 중 **형 1건 선택** · 발권가중 금지

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
