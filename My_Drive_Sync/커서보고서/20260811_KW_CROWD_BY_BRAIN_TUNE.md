# K-W-CROWD-BY-BRAIN-TUNE

📅 2026-08-11 KST · **W_CROWD/STRUCT 뇌별 스윕** · 확정 BLEND 유지

## 잠금 전제
- markovBLEND **0.55** · reviewBLEND **0.85** · SCORE cand_A · statHINT52
- 구간 1137~1236 · seed [0, 42, 123] · ABS≥0.01 · ISO&lt;0.005
- ge3 미사용

## markov (prefer↑ · prize iso)
| w_crowd | prefer | prize | gate |
|---------|--------|-------|------|
| 0.70 | 0.243358 | -0.074379 | True |
| 0.50 | 0.252778 | -0.074379 | False |
| 0.60 | 0.244259 | -0.074379 | False |
| 0.80 | 0.263517 | -0.074379 | True |
| 0.90 | 0.282167 | -0.074379 | True |

best=0.9 · prefer최대 w=0.9 prefer=0.282167

## review (prize↓ · prefer iso)
| w_crowd | prefer | prize | gate |
|---------|--------|-------|------|
| 0.70 | 0.243358 | -0.074379 | True |
| 0.50 | 0.243358 | -0.087086 | True |
| 0.60 | 0.243358 | -0.068802 | False |
| 0.80 | 0.243358 | -0.078716 | False |
| 0.90 | 0.243358 | -0.095253 | True |

best=0.9 · prize최음수 w=0.9 prize=-0.095253

## 판정
- **APPLY** · applied={'markov': 0.9, 'review': 0.9}
