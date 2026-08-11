# K-BRAIN-JOINT-SMOKE-V2

📅 2026-08-12 KST · **wire=False** · ge3=미사용 · DB쓰기=없음  
도구: `tools/_k_brain_joint_smoke_v2.py` · 단계①

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
| markov preferΔ | **+0.294097** | Y |
| review prizeΔ | **-0.111224** | Y |
| stat top15_hit | **0.315555** | (모니터) |
| prefer split rate | 1.00 | |
| cn_rate | 1.00 | |

## 직전 합동(v1) 대비 drift (클레임 아님)
- prefer: +0.049648
- prize: -0.036845
- hit: -0.003889

## 판정
- **verdict** = **SMOKE_OK**
- 3축 건강 조건 충족. markov oversample×5·cand_B·union 포함 live knobs 합동 OK. ge3 성적 주장 금지. 1237 아님 — 다음=② review/stat pool 잔여.
