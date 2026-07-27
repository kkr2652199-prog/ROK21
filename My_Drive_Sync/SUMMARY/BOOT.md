# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: K-V dedup 구현·검증 (E[k]97.09→100 · DEDUP기본ON · PATCHED)
- 직전: K-S선결 · K-T/U/V 전제·쌍·포트폴리오 감사
- 다음: 형—제약채택 · WF잔여/K-R · hyodo

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| 100장 E[k] OFF/ON | **97.091 / 100.000** | K-V |
| P배수(낭비제거) | **≈1.030×** | K-V |
| DEDUP 기본 | **ON** | K-V |
| CUTOFF 기본 | **ON** | K-S |
| draws MAX (testlotto) | **1234** | DB |
| kweon 동결 | **264de3c** | 실측 |

## 3) 열린 과제 -> FINDINGS.md
K-V=**PATCHED**. K-S=**PATCHED**. K-T/U OPEN. K-M·N=**HOLD**.  
정당성=전제 실증. 발권 조합 회차내 유일.

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
1. `BENCH_PROTOCOL.md` (정당성·발권유일)
2. `reports/20260727_KV_중복제거_구현검증.md`
3. `FINDINGS.md` (K-V PATCHED)
4. `RESTORE.md` · `STATUS_LATEST.md`
