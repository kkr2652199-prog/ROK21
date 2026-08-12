# K-SKILL-HOMEWORK-PERSIST — LIST_V3 L9c

판정: **WIRE_OK** · as_of=1236 · read_target=1237(검증만)

## HARD

- `write_ok`: **True**
- `write_3brains`: **True**
- `rows_3`: **True**
- `kind_stat`: **True**
- `kind_markov`: **True**
- `kind_review`: **True**
- `load_3`: **True**
- `no_peek`: **True**
- `payload_eq_recompute`: **True**
- `consume_wired`: **True**
- `consume_matches_stored`: **True**
- `wired_click`: **True**
- `wired_auto`: **True**

- max_abs vs recompute: `0.0`

## 스키마

- 테이블 `testlotto_skill_homework` PK(as_of_draw, brain_tag, skill_kind)
- 모듈: 결과확정 후 click/`_auto_feedback`
- 읽기: `build_hint_by_brain` ← `SKILL_HOMEWORK_CONSUME`

벤치: `docs/benchmarks/20260812_KSKILL_HOMEWORK_PERSIST.json`

다음: **L9d** K-EMA-OR-LEDGER-SSOT 문서결정
