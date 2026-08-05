# K-TRANSITION-STEP4-WIRE — transition_v1 배선 (2026-08-05)

- **판정:** `PASS` · wire=`True` (형 A GO)
- flag ON 기본 · 롤백: `K_STAT_TRANSITION_V1=0` 또는 `TRANSITION_V1_WIRE=False`
- smoke: `{'smoke_ok': True, 'wire_default': True, 'on_methods': ['전이패턴v1', '전이패턴v1', '전이패턴v1', '전이패턴v1', '전이패턴v1'], 'off_methods': ['통계요정', '통계요정', '통계요정', '통계요정', '통계요정'], 'on_sample': [3, 13, 15, 34, 37, 38], 'rollback_env': 'K_STAT_TRANSITION_V1=0'}`
- mini_wf n50: ge3_rate=**0.06** mean_best=**1.22**
- prior HOLD note: STEP3 DESIGN_HOLD(nopeek≈2.007) 상태에서 형 A=STEP4 GO. solo n50는 참고 · fusion n200 재검증 권고.

- tool: `tools/_k_transition_step4_wire.py`
