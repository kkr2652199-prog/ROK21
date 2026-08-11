# K-POST-REFILL-JOINT-SMOKE

📅 2026-08-12 KST · **LIST_V3 L1** · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_post_refill_joint_smoke.py`

## 배선 사전확인
- markov BLEND=0.55 (기대 0.55)
- review BLEND=0.85 (기대 0.85)
- W_CROWD={'markov': 0.9, 'review': 0.9} (기대 0.90/0.90)
- SCORE={'stat': [0.25, 0.35, 0.4], 'markov': [0.65, 0.15, 0.2], 'review': [0.65, 0.15, 0.2]} (cand_B)
- ASSEMBLE=signal_union · oversample={'stat': 3, 'markov': 5, 'review': 3}
- precheck → OK

## 합동 축지표 (1137~1236 · seeds [0, 42, 123])
| 축 | 값 | 건강 |
|----|---:|:----:|
| markov preferΔ | **+0.294930** | Y |
| review prizeΔ | **-0.111224** | Y |
| stat top15_hit | **0.313333** | (모니터) |
| prefer split rate | 1.00 | |
| cn_rate | 1.00 | |

## V2 대비 drift (모니터 · 클레임 아님)
- prefer: +0.000833
- prize: +0.000000
- hit: -0.002222
- refs: `docs/benchmarks/20260812_KBRAIN_JOINT_SMOKE_V2.json`

## 판정
- **verdict** = **SMOKE_OK**
- LIST_V3 L1: refill_v2 후 합동 건강조건 충족. 원장·역할슬롯 코드 미적용(의도). ge3클레임금지·1237아님. 다음=L2 원장SPEC.
