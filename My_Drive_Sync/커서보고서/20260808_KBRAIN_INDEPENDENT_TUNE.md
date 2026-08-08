# K-BRAIN-INDEPENDENT-TUNE

📅 2026-08-08 KST · **APPLY** · applied=True · ge3 미사용

형 GO (WIRE_CONFORMS 승인) → 뇌별 몰아주기 점수축(`SCORE_WEIGHTS_BY_BRAIN`) 1노브.

## 후보

| 뇌 | base (h,f,l) | cand_A | 의도 |
|----|-------------:|-------:|------|
| stat | 0.40/0.25/0.35 | **0.25/0.35/0.40** | 패턴·학습 쪽 |
| markov | 0.40/0.25/0.35 | **0.55/0.20/0.25** | 선호 hint↑ |
| review | 0.40/0.25/0.35 | **0.55/0.20/0.25** | 금액 hint↑ |

## 축 지표 (1100~1235 · n=136 · seed=42)

| 축 | base | cand | Δ | 판정 |
|----|-----:|-----:|--:|------|
| markov prefer_delta | +0.226051 | **+0.249387** | +0.023336 | OK(↑) |
| review prize_delta | −0.027791 | **−0.054918** | −0.027127 | OK(더 음수) |
| stat top15_hit | 0.300245 | **0.305147** | +0.004902 | OK |

- review 3구간 cand: early/mid/late **전부 음수** → `consistent_neg=True` (base는 early 양수였음)
- **ge3 미사용** · 적중확률↑ 클레임 없음

## 적용

`app/testlotto/signal_pool.py` → `SCORE_WEIGHTS_BY_BRAIN=cand_A`

롤백: 3뇌 모두 `(0.40, 0.25, 0.35)`

## 후속

hint 분리(V1)는 스펙 불변으로 유지. 다음=뇌별 엔진 내부 노브(군중 BLEND 등)는 별도 GO.

## 파일

- `docs/benchmarks/20260808_KBRAIN_INDEPENDENT_TUNE.json`
- `tools/_k_brain_independent_tune.py`
