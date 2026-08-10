# K-BRAIN-INDEPENDENCE-BY-BRAIN

📅 2026-08-10 KST · **PATCHED** · 형 「권장진행 · 뇌별 과정 독립 · 공유=과거결과 data만」

## 원칙 (고정)
| 공유 허용 | 공유 금지 |
|-----------|-----------|
| `lotto_draws` (과거 당첨·fw·sales 등 **결과값**) | 뇌별 예측 과정·가중 혼합·hint 스펙·BLEND/W_* 계수 |
| `_get_draws_before(target)` 재료 컷 | markov↔review 동일 스칼라로 동시 튜닝 |

## 이번 패치
`app/testlotto/brains/shared/crowd_signal.py`
- `W_CROWD_BY_BRAIN` / `W_STRUCT_BY_BRAIN` / `BLEND_STRENGTH_BY_BRAIN`
- `prefer_table(..., brain="markov")` · `prize_table(..., brain="review")`
- `blend_weights(..., brain=...)`

호출부: `markov_brain/engine.py` · `review_brain/engine.py` · `signal_pool.py` hint 경로.

## 독립성 실측 (BLEND 스윕 부수)
| 튜닝 | 모니터 축 drift | 판정 |
|------|-----------------|------|
| markov BLEND만 | prize_drift **0.000** 전원 | 독립 OK |
| review BLEND만 | (동 도구 prefer_iso) | 벤치 JSON |

## 튜닝 순서 (권장)
① markov prefer → ② review prize → ③ stat pattern → ④ 합동 smoke만  
ge3 성적클레임 금지 · 1236=마지막 · 1237 양산아님.
