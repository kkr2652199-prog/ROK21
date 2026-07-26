# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: RESTORE 신설 + EV 리랭커 WF — B/D 채택후보 · K-12 · 종료5종
- 직전: 랜덤성·인기도 OOS · 적중학습축 폐기(K-11)
- 다음: 메타에 D 하이브리드 배선(승인) · K-09 스냅샷 · tier1 A/B

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| A 메타K3 **mean** | **0.773** CI[0.68,0.86] | EV리랭커 WF |
| B EV-top3 mean / 수령배율 | **0.810** / **1.088×** | 동상 |
| D 하이브리드 mean / 수령배율 | **0.803** / **1.077×** | 동상 |
| B/D 고유번호 | 14.13 / 16.09 (A=16.95) | 동상 |
| 풀 tier1 통과 | **100%** | trap(a) |
| OOS CI하한>0.80 | NO (적중축 폐기) | K-11 |
| testlotto MAX | 1234 | DB |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · K-08 · K-09 · K-10 · K-11 · **K-12** = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `RESTORE.md` ← 압축 복원 1순위
2. `STATUS_LATEST.md`
3. `reports/20260726_ROK21_EV리랭커_WF실측.md`
4. `docs/benchmarks/20260726_EV리랭커/summary.json`
