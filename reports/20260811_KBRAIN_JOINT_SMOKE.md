# K-BRAIN-JOINT-SMOKE

📅 2026-08-11 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_brain_joint_smoke.py`

## 배선 사전확인
- markov BLEND=0.55 (기대 0.55)
- review BLEND=0.85 (기대 0.85)
- stat HINT=[52, 'miss_pattern'] (기대 [52, miss_pattern])
- precheck → OK

## 합동 축지표 (1137~1236 · seeds [0, 42, 123])
| 축 | 값 | 건강 |
|----|---:|:----:|
| markov preferΔ | **+0.244449** | Y |
| review prizeΔ | **-0.074379** | Y |
| stat top15_hit | **0.319444** | (모니터) |
| prefer split rate | 1.00 | |
| cn_rate | 1.00 | |

## 단독튜닝 대비 drift (클레임 아님)
- prefer: -0.000000
- prize: +0.000000
- hit: +0.000000

## 판정
- **verdict** = **SMOKE_OK**
- 3축 건강 조건 충족. 뇌별 단독튜닝 값이 합동에서도 유지. ge3로 성적 주장 금지. 1237 양산 아님 — 형 다음 지시 대기.
