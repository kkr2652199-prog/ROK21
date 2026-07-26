# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: 겹침 분석 완료 · oversample→diversify 패치 채택(최근40 best 2.33 vs 저장 2.13)
- 직전: SUMMARY 압축 교정 · 중간점검(선별=15장 전체)
- 다음: markov 겹침 강화 A/B · port3+신풀 vs 랜덤3 재측정

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| draws MAX | 1234 | lotto_testlotto.db |
| 15장 Jaccard (저장) | 0.098 | overlap_stored_baseline |
| 뇌내 Jaccard markov | 0.150 | 동상 (가장 높음) |
| 고유번호 저장/다양화(40회) | 36.9 / **37.7** | diversity_live_wf |
| best 저장/다양화/랜덤(40회) | 2.13 / **2.33** / 2.40 | diversity_live_wf |
| 포트폴리오3 best | ~1.44 | portfolio_wf |
| cover6 | ~27.9% | union_coverage |
| Vote≥2 | 기각 | vote2_wf |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 나머지·STATUS는 표·문장 유지.
- PIN: 메타=3뇌×5 전체풀 · 출력 포트폴리오 K=3 · 추가뇌/세트확장 보류.
- 동결: `random.choices` **미수정** (다양성은 oversample 후 선별만) · `_get_draws_before` · boost 상한.
- 순서: 분석 → 결론 → 튜닝/추가뇌. DB 전체초기화 비권고.

## 5) 더 필요하면
1. `STATUS_LATEST.md`
2. `docs/benchmarks/20260726_겹침분석_다양성패치/summary.json`
3. `PINNED_PLAN.md` · `MIDCHECK_선별범위.md`
4. `reports/20260726_ROK21_겹침_다양성패치.md`
