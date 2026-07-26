# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: 지표재정의 검증 — (A)(B) 재현 · mean 유의>0.80 실패 · K-08 신설 · 비인기EV 1순위
- 직전: 다양성 패치 채택 · SUMMARY 압축 교정
- 다음: mean 병기 정착 · 비인기전략 재활용 설계(실행은 별도) · hyodo 갭은 승인 후

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| 이론/MC 1장 mean | 0.80 / 0.802 | monte_carlo_summary |
| 이론/MC best-of-15 | 2.269 / 2.277 | 동상 |
| 최근40 저장/다양화/랜덤 **mean** | 0.752 / 0.835 / 0.758 | 동상 |
| 다양화 mean−0.80 CI95 | [-0.055, +0.123] (0 포함) | bootstrap |
| testlotto / lotto4 / hyodo MAX | 1234 / 1234 / **1231** | DB 실측 |
| cover6 | ~27.9% | union_coverage |
| port3 best | ~1.44 | portfolio_wf |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · **K-08** = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `STATUS_LATEST.md`
2. `reports/20260726_ROK21_지표재정의_검증.md`
3. `docs/benchmarks/20260726_지표재정의_검증/monte_carlo_summary.json`
4. `reports/20260529_4군_비인기전략_기반분석_정찰.md` (재활용 후보)
