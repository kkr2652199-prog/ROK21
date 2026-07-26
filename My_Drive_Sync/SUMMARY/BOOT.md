# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon **복사본(테스트 샌드박스)**. SSOT=`kkr2652199-prog/ROK21` · 로컬 `D:\ROK21` · 포트 **7021**.  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon`) **쓰기·push 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: 랜덤성검정+인기도모델 — 적중학습축 폐기 · Ridge 리랭커 설계 · K-11
- 직전: 뇌감사 · K-09/K-10 · 비인기 신호
- 다음: Ridge EV 리랭커 WF(승인) · K-09 스냅샷 · tier1 A/B

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| 빈도 χ² p (main/bonus) | 0.965 / 0.877 | 랜덤성검정 |
| FDR 생존 편향 | gap KS만 (형식 YES·실질 공정) | K-11 |
| OOS 상위6 mean (freq/markov/recency) | 0.748 / 0.769 / 0.752 | step2 |
| OOS CI하한>0.80 | **NO** → 적중학습축 폐기 | step2 |
| 인기도 Ridge Spearman / 수령배율 | **0.440** / **1.180×** | step3 |
| 전수 단변량 수령배율(참고) | ≈1.20× | 뇌감사 |
| testlotto MAX | 1234 | DB |

## 3) 열린 과제 -> FINDINGS.md
K-00 · K-02 · K-05 · K-06 · K-07 · K-08 · K-09 · K-10 · **K-11** = OPEN.

## 4) 주의 (붕괴 방지)
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `STATUS_LATEST.md`
2. `reports/20260726_ROK21_랜덤성검정_인기도모델.md`
3. `docs/benchmarks/20260726_랜덤성검정/summary.json`
4. `reports/20260726_ROK21_뇌감사_비인기검증.md`
