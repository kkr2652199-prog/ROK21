# K-QUOTA-MIN-EACH — 단계⑧

시각: 2026-08-12 KST · **양산前** · **1237아님** · ge3미클레임

## 판정 **APPLY_OK**

### 문제
⑦ post-refill 후 live referee spread0.176 → dominance 발동 → quota **markov4 / review1 / stat0**.  
과거학습(stat) 발권 0장 = 3뇌 독립 원칙과 충돌.

### 패치
- `QUOTA_ADAPTIVE_MIN_EACH`: **0 → 1**
- dominance 분기: top 초과분에서 부족 뇌로 이체 → 전뇌 ≥1

### 실측 (live 가중)
| | quota |
|--|-------|
| min_each=0 | `{stat:0, markov:4, review:1}` |
| min_each=1 | `{stat:1, markov:3, review:1}` |

근거: `docs/benchmarks/20260812_KQUOTA_MIN_EACH_GATE.json`
