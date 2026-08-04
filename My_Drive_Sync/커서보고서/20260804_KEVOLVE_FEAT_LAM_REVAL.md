# K-EVOLVE-FEAT-LAM-REVAL — 풀히스토리 λ 재검증

📅 2026-08-04 · **HOLD** · wire 롤백 완료

range **53~1234** n=**1182**

## 한 줄

SIGNAL n200에서 review λ0.3 (+0.01)은 **희소 히스토리 과적합**.  
풀로그 재검증 후 full Δ=**−0.0025** · tail200 Δ=**−0.030** → **FEATURE_LAMBDA_WIRE=OFF**.

## review

| 구간 | baseline | λ=0.3 | Δ |
|------|----------:|----------:|---:|
| full [53, 1234] | 0.1252 | 0.1227 | -0.0025 |
| tail200 [1035, 1234] | 0.1350 | 0.1050 | -0.0300 |
| early [53, 446] | 0.1320 | 0.1294 | -0.0026 |
| mid [447, 840] | 0.1041 | 0.1371 | +0.0330 |
| late [841, 1234] | 0.1396 | 0.1015 | -0.0381 |

- full best λ=**0.0** ge3=**0.132**
- SIGNAL tail ref λ0.3=**0.145** · 풀히스토리 하 tail 실측=**0.105**

## 전뇌 λ 요약

| 뇌 | baseline | bestλ | best ge3 | λ0.3 ge3 | Δ0.3 |
|----|----------:|------:|---------:|---------:|-----:|
| stat | 0.1294 | 0.5 | 0.1151 | 0.1074 | -0.0220 |
| markov | 0.1201 | 0.1 | 0.1320 | 0.1286 | +0.0085 |
| review | 0.1252 | 0.0 | 0.1320 | 0.1227 | -0.0025 |

## 조치

- `FEATURE_LAMBDA_WIRE=False`
- `FEATURE_LAMBDA_BY_BRAIN={}`
- smoke 1230 review assemble=`hy_p45_r123` (feat_lam 제거 확인)
- markov λ0.3 full +0.0085는 **참고만** · wire 금지(게이트 미달·전뇌 HOLD 원칙)

## 판정

- **HOLD** · review λ0.3 롤백
- AUTO prep gate: **False** (λ 게이트 실패)
- 다음: Phase3 AUTO는 **설계 문서만** 가능 · 실행 wire 전 추가 게이트 · **형 GO**

근거: `20260804_KEVOLVE_FEAT_LAM_REVAL.json`
