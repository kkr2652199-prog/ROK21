# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: 뇌감사+비인기검증 READ-ONLY — 3뇌=커버리지 샘플러 · 비인기 신호 4변수 · K-09/K-10
- 직전: 지표재정의 MC · mean>0.80 실패 · K-08
- 다음: learn_state cutoff 설계 · 3등 비인기 리랭크 WF · tier1 완화 A/B(승인 후)

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| all3 mean (최근100) | **0.797** CI[0.75,0.845] | 뇌감사 audit |
| no_stat / no_markov / no_review **mean** | 0.789 / 0.835 / 0.768 | 동상 |
| all3 고유번호 | 36.67 (제거 시 −4.4~−6.6) | 동상 |
| 뇌간 Jaccard | ~0.084~0.087 | 동상 |
| 3등 비인기(합) 수령배율 | ≈**1.20×** | audit_supplement |
| tier1 pass/fail **mean** | 0.791 / 0.805 (Δ CI에 0) | 동상 |
| testlotto / lotto4 / hyodo MAX | 1234 / 1234 / **1231** | DB |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · K-08 · **K-09** · **K-10** = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `STATUS_LATEST.md`
2. `reports/20260726_ROK21_뇌감사_비인기검증.md`
3. `docs/benchmarks/20260726_뇌감사_비인기검증/audit_summary.json`
4. `reports/20260726_ROK21_지표재정의_검증.md` (mean/best MC)
