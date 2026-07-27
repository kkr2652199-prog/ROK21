# K-AG pair/30·zone 재정의 + 미소비 3키 배선 (2026-07-27)

1등 확률 상승 작업이 아니다. 명분·배선 정합 작업이다.

## STEP 0 실측

출처: `docs/benchmarks/20260727_KAG_step0_measure.json`

| 항목 | 결과 |
|------|------|
| `/30` 출처 | 코드 리터럴만. 유도식·주석 없음 (`aux_pattern_spotlight`) |
| null pair_score (n=5000) | mean≈22.72 · **q95=32.0** · ≥30 포화 **10.74%** |
| 당첨 causal rolling | mean≈22.9 · q95≈34.05 · ≥30 포화 17% |
| 동시창 당첨(누수성) | ≥30 포화 93% → 정규화 근거로 부적합 |
| zone | `tgt["zone"]=max평균` 이나 점수는 `zone_spread`만 → **정의 충돌 사실** |
| LMH 이론 | mode **(2,2,2)** p≈**0.142126** · E[max_zone]≈**3.148** (K-Z 일치) |
| 3키 | apply_feedback·cutoff 갱신되나 aux 산출 **미소비** (K-Y 재확인) |

## STEP 1–2 적용

| 항목 | 변경 |
|------|------|
| pair | `PAIR_NORM_DIVISOR=32.0` (=null_q95). 고빈도=유리 해석 없음 |
| zone | LMH 이론 PMF 점수 `0.3+0.4*(p/p_mode)`. spread·tgt.zone 제거 |
| AC/consec/합138 | **미변경** |
| pair_boost | pattern `pair_term *= (1+b)` |
| consecutive_boost | pattern `consec_term *= (1+b)` |
| odd_even_balance | balance `odd_term *= (1+b)` |
| 키=0 | brain_tag=None ≡ boost 전부 0 → **항등** |
| AUX 구성·가중 | **미변경** `[0.25]*4` |
| 동결토큰 | random.choices / `_get_draws_before` / boost 상한 **미수정** |

## STEP 3 검증

출처: `docs/benchmarks/20260727_KAG_pair_zone_learnkeys.json`

| 테스트 | 결과 |
|--------|------|
| zero-key 항등 (신규 baseline) | **PASS** |
| 단일키 감도 | **PASS** |
| 3×3 격리 | **PASS** |
| zone (2,2,2)=0.7 | **PASS** |
| as_of SHA 2회 | **PASS** |
| E[k]=100 · unresolved=0 · CUTOFF | **PASS** |
| verify | **true** |

참고: 구코드(`/30`·spread) 대비 top15 SHA 불일치는 pair/zone **재정의 정상**. 항등 게이트는 “키=0 vs 미주입”.

## 상태

- FINDINGS **K-AG PATCHED**
- 1~3군 간섭 **0건**
- kweon 미접촉

## 산출

- `docs/benchmarks/20260727_KAG_step0_measure.json`
- `docs/benchmarks/20260727_KAG_pair_zone_learnkeys.json`
- `docs/benchmarks/20260727_KAG_diff.patch`
- 본 보고서
