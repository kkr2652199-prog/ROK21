# K-PAST-LEARN-WIRE — 과거학습 구조 패치 (2026-08-08)

- **판정:** `PASS` · wire 구조 ON
- flags: `{'PAST_LEARN_WIRE': True, 'PAST_LEARN_ENGINE_V2': True, 'PAST_LEARN_ASSOC_HINT': False, 'SOFT_WEIGHT': 0.12, 'SOFT_CONF_CAP': 3.0, 'rollback': 'K_PAST_LEARN=0 · K_STAT_ENGINE_V2=0 · K_PAST_LEARN_ASSOC=0'}`
- TRANSITION_V1_WIRE=`False` (OFF 유지)
- smoke_ok=`True` · methods=`['과거학습', '과거학습', '과거학습', '과거학습', '과거학습']`
- solo n50: mean_best=**1.58** · ge3=**0.14**
- sample: `과거학습: 빈도가중+끝수[1, 2, 5, 6, 9]+이월1개[15]+미출30+없음 [과거학습:1yHot[9, 15] Δ0.2] [학습조정 이월×1.00 끝수×1.00]`

## 구조

1. engine v2 (장·단 윈도우) via past_learn
2. aux_hint
3. past_learn soft(미출/1yHot·Cold) · ASSOC 기본 OFF
4. diversity.pick · method=`과거학습`

## 롤백

- `K_PAST_LEARN=0` · `K_STAT_ENGINE_V2=0`

- tool: `tools/_k_past_learn_wire.py`
