# K-EXCLUDE-SURVEY — combined + 배제 λ sweep (빠른 검증(200회) · READ-ONLY live WF)

날짜 2026-08-01 · elapsed 14.0s · **FAIL** · seed=42 · n=200 · gate=quick

개념: 3뇌×10 pool → **배제 필터(λ)** → combined 5선별 · 패턴: 3연속+ · 합 p05-p95 밖 · zone 4+ skew · per-draw `build_exclude_catalog(as_of=T)`.

## 1. 📋 숙제
| 항목 | 내용 |
|------|------|
| **ID** | `K-EXCLUDE-SURVEY` |
| **질문** | combined 선별에 WF-safe 배제(λ)를 얹으면 ge3가 baseline(0.145 quick / 0.1218 full)을 이기는가? |
| **PASS** | exclude ON variant > combined baseline **AND** p<0.15(quick)/0.05(full) **AND** 과배제≤90% |
| **금지** | coordinator wire · `_get_draws_before` 수정 · catalog 미래누수 |

## 2. SUMMARY
| label | λ | mean | ge3_rate | ge3_cnt | Δpin | Δcombined | p(vs null) | kill% | verdict |
|-------|--:|-----:|---------:|--------:|-----:|----------:|-----------:|------:|---------|
| **theory_baseline** | — | 0.8000 | 0.1137 | — | — | — | — | — | — |
| **WIRE-V2 pin** | — | 1.7504 | 0.1447 | — | — | — | — | — | stored |
| **combined ref** | — | — | **0.145** | — | — | — | — | — | K-SIGNAL-SELECT |
| combined_baseline | OFF | 1.715 | 0.145 | 29 | +0.0003 | +0.0000 | 0.102441 | 0.0% | PASS |
| combined_exclude_l0.5 | 0.5 | 1.715 | 0.145 | 29 | +0.0003 | +0.0000 | 0.102441 | 2.8% | PASS |
| combined_exclude_l0.75 | 0.75 | 1.715 | 0.145 | 29 | +0.0003 | +0.0000 | 0.102441 | 0.5% | PASS |
| combined_exclude_l1 | 1 | 1.715 | 0.145 | 29 | +0.0003 | +0.0000 | 0.102441 | 0.5% | PASS |
| combined_exclude_l0.25 | 0.25 | 1.725 | 0.135 | 27 | -0.0097 | -0.0100 | 0.198612 | 10.9% | FAIL |

## 3. variants (ge3 내림)
| variant | λ | ge3_rate | ge3_cnt | Δcombined | p(null) | avg_kill | over_exclude |
|---------|--:|---------:|--------:|----------:|--------:|---------:|:------------:|
| combined_baseline | 0.0 | 0.145 | 29 | +0.0000 | 0.102441 | 0.0% | OK |
| combined_exclude_l0.5 | 0.5 | 0.145 | 29 | +0.0000 | 0.102441 | 2.8% | OK |
| combined_exclude_l0.75 | 0.75 | 0.145 | 29 | +0.0000 | 0.102441 | 0.5% | OK |
| combined_exclude_l1 | 1.0 | 0.145 | 29 | +0.0000 | 0.102441 | 0.5% | OK |
| combined_exclude_l0.25 | 0.25 | 0.135 | 27 | -0.0100 | 0.198612 | 10.9% | OK |

## 4. Verdict
- **gate (quick):** exclude ON beats combined baseline AND p<0.15 AND avg_kill<=90% → **FAIL**
- **baseline (λ=0):** ge3=0.145 · ref=0.145
- **best exclude ON:** `combined_exclude_l0.5` ge3=0.145 Δcombined=+0.0000 p=0.102441 kill=2.8%
- **recommended_next:** K-ATTACK-HOLD · SELECT-WIRE HOLD

## 5. 팩트체크
| 항목 | JSON | 보고서 |
|------|------|--------|
| n_eval | 200 | 200 |
| baseline ge3 | 0.145 | 0.145 |
| best ge3 | 0.145 | 0.145 |
| pass_gate | False | False |
| no_peek | True | True |
| coordinator_modified | False | False |
