# K-EVOLVE-LOG-EXPAND — evolve_log 53~1234

📅 2026-08-04 · **PASS**

## 결과

- range **53~1234** · logged draws **1182** / expected 1182
- from_cache **200** · from_wf **982** · miss **0**
- weight_applied=**0.0** · live FEATURE_LAMBDA_WIRE=**True**
- sample 100 ok=True · 1200 ok=True

## 뇌별 (발권 best 참고 · 학습입력 금지)

| 뇌 | n | ge3_rate | avg_best | avg_mean |
|----|---|---------:|---------:|---------:|
| markov | 1182 | **0.1201** | 1.8613 | 0.7997 |
| review | 1182 | **0.1252** | 1.7623 | 0.8196 |
| stat | 1182 | **0.1294** | 1.7648 | 0.8005 |

## 비고

- miss 구간: 순차 WF · evolve_log만 · pool_view_cache **미저장**
- 확장 중 λ OFF · 종료 후 live λ(review 0.3) 복원
- 기존 n200 JSON 유지: `20260804_KEVOLVE_LOG.json`

근거: `20260804_KEVOLVE_LOG_EXPAND.json`
