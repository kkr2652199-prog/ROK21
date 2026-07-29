# K-STAT-TUNE-WIRE — stat gap20/hot10 배선 verify

📅 2026-07-29 · **FAIL** · `predict_statistical.py` **롤백완료** (gap30/50 · hot5)

## 요약

형 GO 승인 후 gap_threshold=20 · hot_window=10 리터럴 배선 → live walk-forward verify.  
ge3=**0.1176** < pin **0.1447** · Δ=**-0.0271** · p=**0.349617** → **FAIL**.  
`predict_statistical.py` 원복(gap 30/50 · hot 5). NEXT=**K-ATTACK-HOLD**.

근거: `docs/benchmarks/20260729_KSTAT_WIRE_verify.json`

---

## 배선 (시도 · 롤백됨)

| 파라미터 | 이전 | 시도 | 현재(롤백) |
|----------|------|------|------------|
| gap mid/hi | 30/50 | **20/40** | 30/50 |
| hot_window | 5 | **10** | 5 |
| recency_decay | 0.02 | 0.02 | 0.02 |
| top_pairs | 30 | 30 | 30 |
| pair_bonus_cap | 0.5 | 0.5 | 0.5 |

---

## Verify 결과

| 항목 | 값 |
|------|-----|
| n_eval | **1182** (draw 53~1234) |
| ge3_rate | **0.1176** |
| ge4_rate | 0.0085 |
| ge3_count | 139 |
| wire pin ge3 | 0.1447 |
| null_ge3 | 0.1137 |
| Δ vs pin | **-0.0271** |
| p_value | **0.349617** |
| verdict | **FAIL** |
| recommended_next | ROLLBACK → **K-ATTACK-HOLD** |

방법: 3뇌 live predict_sets + coordinator scoring + markov wire quota (지시서 `_k_stat_wire_verify.py`).

---

## STAT-TUNE survey vs WIRE verify

| 구분 | ge3 | 방법 |
|------|-----|------|
| STAT-TUNE best (격자) | 0.1523 | stored markov/review + stat 재생성 |
| **WIRE verify (live)** | **0.1176** | 3뇌 전부 live 재생성 |

격자 PASS ≠ live pipeline PASS — 배선 채택 불가.

---

## Verdict / NEXT

**FAIL → 롤백완료 → `K-ATTACK-HOLD`**  
다음 공격축 형 결정 대기 · 승인필요=**예**.

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| ge3_rate | 0.1176 | 0.1176 | 0.1176 |
| Δ vs pin | -0.0271 | -0.0271 | -0.0271 |
| p_value | 0.349617 | 0.349617 | 0.349617 |
| verdict | FAIL | FAIL | FAIL |
| rollback | true | true | true |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |

ASCII `-` 구분 · 숫자 SSOT=`docs/benchmarks/20260729_KSTAT_WIRE_verify.json`
