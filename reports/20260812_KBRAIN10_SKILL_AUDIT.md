# K-BRAIN10-SKILL-AUDIT — LIST_V3 L5

시각: 2026-08-12T10:04:04+09:00 · **AUDIT_OK** · wire=**False**(감사) · **1237아님** · ge3미클레임
구간: 1216~1236 n=21 seed=42
다음: **L9** `K-REPACK-PRESERVE-PROBE`

## HARD

```json
{
  "pool10_complete": true,
  "roles_ok_all": true,
  "pass0_match_all": true,
  "cross_identical_0": true,
  "peek_ok_all": true,
  "ROLE_SLOTS_WIRE": true,
  "LEDGER_SIGNAL_WIRE": true,
  "LEDGER_BLEND": 0.5,
  "c8_pool1to5_eq_issue": true,
  "hint_not_shared": true,
  "hint_tops_distinct": true
}
```

hard_ok=True

## SOFT (스킬축 모니터)

```json
{
  "markov_prefer_ge_review_rate": 0.6667,
  "review_prize_le_markov_rate": 0.5714,
  "markov_axis_soft_fail": false,
  "review_axis_soft_fail": false,
  "stat_axis": "homework/pattern via HINT_SPEC — structural only (no soft gate)"
}
```

## defects → L6~L8

```json
[]
```

cover mean min-Jaccard vs skill: {'stat': 0.0, 'markov': 0.0014, 'review': 0.0219}

벤치: `docs/benchmarks/20260812_KBRAIN10_SKILL_AUDIT.json`
