# K-PIN-GAP-DIAG — FUTURE-WIRE FULL pin갭 진단

HEAD 시점 진단 · `2026-08-04T02:45:16+00:00` · **READ-ONLY 1차(JSON)** · seed 스윕 포함

## 0. 한 줄

FULL ge3 **0.1184** vs pin **0.1447** (Δ**-0.0263**). 주원인은 **early 구간 약세(n=394)** + **n100→FULL 붕괴** + **markov80% 고착(solo도 pin 미달)**. **mid 붕괴 아님** · **K-M≈0 기여** · **K-N 주성분 미입증**.

## 1. 기간별 분해 (FULL thirds · n=각 394)

| 구간 | n | ge3 | vs pin | vs null5 |
|------|---|-----|--------|----------|
| early | 394 | **0.099** | -0.0457 | -0.0147 |
| mid | 394 | **0.132** | -0.0127 | +0.0183 |
| late | 394 | **0.1244** | -0.0203 | +0.0107 |

- pin 대비 최악: **early** (Δ-0.0457)
- mid−early ge3 = **+0.0330** → mid 붕괴 주장 **기각**
- 보조 N100(25/25/50): late가 pin 최약 — FULL과 창이 다름

## 2. 뇌·쿼터 기여 (markov 80% 고착)

| 항목 | 값 |
|------|-----|
| quota FULL | markov 80.0% · review 20.0% · stat 0.0% |
| solo ge3 ref | markov 0.13 · review 0.11 · stat 0.09 |
| 선형혼합 기대 | **0.126** |
| FULL fused | **0.1184** |
| vs markov solo | **-0.0116** |
| markov solo vs pin | **-0.0147** |

quota 고착으로 fused≈markov 지배. 단 markov solo 0.13 자체도 pin 0.1447 미달(Δ−0.0147)이므로 pin갭 전량이 희석만으로 설명되지 않음.

## 3. seed=42 고정 영향

- 창: N100 1135~1234 · seeds=[42, 0, 7]
- ge3 min/max/range: **0.1** / **0.15** / **0.05**
- seed42 ge3(재측정): **0.15**
- 민감(≥0.02): **True**

| seed | ge3 | vs pin | vs ref0.15 |
|------|-----|--------|------------|
| 42 | **0.15** | +0.0053 | +0.0000 |
| 0 | **0.1** | -0.0447 | -0.0500 |
| 7 | **0.1** | -0.0447 | -0.0500 |

N100에서 seed에 따라 ge3가 크게 변함(0.15↔0.10, range 0.05). n100 PASS·소표본은 seed=42 운에 민감. FULL pin갭(Δ−0.0263)은 seed=42 고정 FULL 결과 — 다른 seed로 pin 회복은 미검증(FULL multi-seed 별도 GO).

## 4. K-M / K-N → pin갭 기여

| ID | 판정 | 근거 |
|----|------|------|
| K-M | **negligible (~0)** | wΔ≈0.0018 · top5 멤버십 불일치 5% |
| K-N | **low_indirect** | early≪late로 누적오인 주원인 불일치 · 직접계수 미분리 |

## 5. 드라이버 순위 · 다음 패치 후보

1. **FULL_early_period_weakness** — early ge3=0.099 Δpin=-0.0457 (n=394) (기간 중 pin 대비 최악 · mid 붕괴 아님)
2. **n100_seed42_luck_and_full_collapse** — N100 seed42=0.15 vs 0/7=0.10 (range 0.05); FULL 0.1184 Δn100=-0.0316
3. **markov80_quota_lock_plus_solo_below_pin** — quota markov80% · fused=0.1184 · blend≈0.126 · markov_solo=0.13 vs pin=0.1447 (희석(−0.0116 vs solo) + solo자체 pin미달(−0.0147))
4. **K-M_referee** — membership mismatch 5% · wΔ≈0.0018 (pin갭 기여 ≈0)
5. **K-N_best_feedback** — early≪late → 누적오인 주원인 불일치 (직접 기여 미입증(low_indirect))

### next_patch_candidates
- early-period 안정화 조사(윈도/학습 warm-up)
- FULL-first 게이트(I2) · n100 단독 PASS→wire 금지
- N100 multi-seed 게이트 또는 seed-robust 지표
- quota/stat0% A/B는 I1 후(I7) — solo markov도 pin 미달 전제
- I3 B1 feature 로그(가중0) 병행

## 근거 파일

- `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json`
- `docs/benchmarks/20260803_KFUTURE_WIRE_N100.json`
- `docs/benchmarks/20260803_KFUTURE_WIRE_QUICK200.json`
- `reports/20260727_KM_KN_분산검정.md`
- `docs/benchmarks/20260801_KHIGHWAY_BACKTEST_100.json` (solo ge3)

## 금지 준수

engine.py·coordinator wire 없음 · auto-tune 없음 · FINDINGS 무단 갱신 없음
