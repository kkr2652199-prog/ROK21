# K-POOL-RESIDUAL — 단계② review/stat pool 잔여

시각: 2026-08-12 KST · **양산前** · **1237아님** · ge3미클레임

## 요지
단계① 합동smoke SMOKE_OK 이후, pool 잔여 2노브(뇌별 1개씩) 스윕.

| 단계 | 노브 | 판정 | chosen |
|------|------|------|--------|
| ②a | review `BLEND_STRENGTH` | **NO_IMPROVE_HOLD** | **0.85** |
| ②b | stat `HINT_WEIGHT` | **NO_IMPROVE_HOLD** | **0.15** |

## ②a review BLEND
- 후보 {0.85, 0.90, 0.95, 1.00} · pool nums prize
- b=1.0 prize 0.010907→0.009763 (Δ−0.00114 ≪ thr0.005) · prefer iso0
- 근거: `docs/benchmarks/20260812_KPOOL_RESIDUAL_REVIEW_BLEND.json`

## ②b stat HINT_WEIGHT
- 후보 {0.0, 0.15, 0.30, 0.45} · pool best |∩|/6
- base hit 0.335556 최선 · 전후보 improve 미달
- SCORE 스윕은 pool생성 무관 → **기각·미실행**
- 근거: `docs/benchmarks/20260812_KPOOL_RESIDUAL_STAT_HINT.json`

## 다음
③ 강제 BT 100회 재적재(모니터 · ge3 클레임 금지)
