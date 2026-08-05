# K-TRANSITION-STEP2-VERIFY — 수집 데이터 재검증 (2026-08-05)

> **작성:** Cursor · wire=`False` · 발권/뇌 미접촉

- **판정:** `PASS` · table_ok=`True`
- alignment: 지시서=STEP2 재검증 · 방향성 COLLECT→VERIFY → **일치**

## [1] table
- rows=1134 · dup=0 · missing=[]

## [2] collect (N→N+1)
- mean=1.998236 · std=1.08379 · within_band=True
- hit_dist={'0': 84, '1': 294, '2': 404, '3': 257, '4': 82, '5': 13, '6': 0}

## [3] FULL recheck (hit@N)
- mean=2.171806 · delta=0.171806 · match=**True**
- note: hit@N · lotto_draws 재계산. transition_log.hit_count는 N→N+1이라 FULL 재현에 직접 쓰지 않음 (Cursor 커버).

## [4] by_period
- {'early': 1.944737, 'mid': 2.074271, 'late': 1.976127, 'max_gap': 0.129534, 'stable': True, 'n_early': 380, 'n_mid': 377, 'n_late': 377}

## [5] spot_check 1230~1234
- 1230: hit=3 top15=`[13, 30, 12, 34, 45, 17, 3, 14, 19, 28, 4, 7, 33, 6, 36]`
- 1231: hit=1 top15=`[45, 24, 29, 18, 14, 8, 26, 27, 39, 11, 13, 17, 21, 37, 38]`
- 1232: hit=1 top15=`[28, 6, 12, 3, 43, 45, 8, 27, 34, 13, 14, 25, 19, 29, 38]`
- 1233: hit=2 top15=`[10, 43, 33, 37, 17, 40, 2, 15, 6, 22, 32, 3, 38, 39, 7]`
- 1234: hit=2 top15=`[34, 37, 38, 3, 44, 13, 15, 33, 1, 12, 17, 21, 45, 7, 19]`

- prior: `docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json`
- tool: `tools/_k_transition_step2_verify.py`
