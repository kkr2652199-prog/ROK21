# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: K-AE 룰반영(R35/R36·§6) · K-06팬아웃 PATCHED
- 직전: K-AD 훅동적주입 · RESTORE복귀
- 다음: 형—pair/zone·미소비키·hyodo후속 중 선택

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| K-06 | **PATCHED** | K-AE |
| fanout verify | **PASS** | KAE JSON |
| drift n_issues | **0** | 반영 직후 |
| draws MAX 3DB | **1234** | 운영 불변 |
| kweon 동결 | **264de3c** | 실측 |

## 3) 열린 과제 -> FINDINGS.md
K-AE·06·AD·AB…=**PATCHED**. K-AC OPEN(이력). K-M·N=**HOLD**.  
수집팬아웃 자동화 완료. 예측력무관.

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
1. `reports/20260727_KAE_룰반영_K06팬아웃.md`
2. `app/lotto/draw_fanout.py` · `docs/benchmarks/20260727_KAE_fanout_verify.json`
3. `RULES_FIXED.md` R35·R36 · `CURSOR_RULES.md` §6
4. `NEXT_ACTIONS.md` · `FINDINGS.md`

