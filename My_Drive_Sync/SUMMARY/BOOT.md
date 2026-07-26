# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: SUMMARY 압축 과다 지적 → STATUS/BOOT 본문 복원 · 「채팅 간략≠문서 압축」 고정
- 직전: 중간점검(선별=3뇌 전체풀) · 포트폴리오K=3 · 추가뇌/세트확장 보류
- 다음: 15장 겹침 줄이기 분석·패치 준비 (분석→결론→튜닝 순서)

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| draws MAX | 1234 | lotto_testlotto.db |
| 3뇌×5 최고장 avg | ~2.22 | cover6/set picker WF |
| 단뇌×5 최고장 avg | ~1.62~1.71 | MIDCHECK 집계 |
| 15장 고유번호 avg | ~36.5 | diversity_kpi |
| cover6 (답이 풀에 6개) | ~27.9% | union_coverage |
| aux 시드 1장 | ~0.80~0.81 | hybrid WF |
| 포트폴리오 3장 중 best | ~1.44 | portfolio_wf |
| 랜덤 15장 best / 랜덤 3장 best | ~2.28 / ~1.46 | trust summary |
| Vote≥2 단독 | ~0.79 → 기각 | vote2_wf |
| L_ending KEEP lift | +0.024 | similar_lens_swarm |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 = OPEN. (닫을 때 ID·근거 필수)

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·`reports/`·벤치 README는 **압축 금지** (형 20260726 지적).
- BOOT §1만 3줄. §0·§2·§4·§5 및 STATUS는 문장·표로 충분히.
- PIN: 형계획 메타선별 Primary · 시드=보조4뇌 · 출력=포트폴리오 K=3 · 추가뇌/세트수 확장 **보류**.
- 동결: `random.choices` · `_get_draws_before` · boost 상한 carry0.2/ending0.3/overdue0.2.
- DB 전체 초기화 **비권고**. 원본 kweon 미접촉. 1~3군 내용 ROK21 기록 금지.
- 순서: **분석 → 결론(숫자) → 튜닝/추가뇌**.

## 5) 더 필요하면 (읽을 순서)
1. `STATUS_LATEST.md` (현황 SSOT)
2. `docs/benchmarks/20260726_형계획_세트합집합_메타선별/PINNED_PLAN.md`
3. `MIDCHECK_선별범위.md` · `JUDGMENT_튜닝vs메타.md`
4. `docs/benchmarks/20260726_신뢰_odd_even_순위장선택/summary.json`
5. 최신 보고서: `reports/20260726_ROK21_중간점검_선별범위.md` · `reports/20260726_ROK21_문서압축_교정.md`
