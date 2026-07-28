# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-ATTACK-BAYES · inv-corr 무력 · NEXT=CONF-CAL

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| 3DB MAX | **1234** |
| GATHER | 관측고정 (아이디어 OK · WIRE 보류) |
| SLICE | 관측유지 · 배선 보류 |
| BAYES | soft≈null · pick_invcorr < RR · **배선 보류** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-ATTACK-BAYES** | 창50 inv-corr 동적가중 | soft null · vs RR 패배 |
| **K-ATTACK-SLICE** | LMH 승격 정책 비교 · live conf proxy | 배선 보류 |
| **K-GATHER-V2** | V축소 covering | 회수0 · 관측고정 |
| **EXTERNAL_AI_JOIN** | GitHub 합류 읽기순서 프롬프트 | DOCS |

---

## 2) BAYES 핵심 (n_eval=1182)

| 항목 | 값 |
|------|-----|
| soft Δmean | **−0.001** (null) |
| pick_invcorr vs RR Δmean | **−0.047** |
| pick_invcorr vs max_conf Δmean | +0.025 (conf 약함) |
| mean pair corr | markov–review **0.059** |

근거: `docs/benchmarks/20260729_KBAYES_dyn_weight.json`

---

## 3) 다음

`K-ATTACK-CONF-CAL` — 뇌 **내부** conf 보정·세트순위 (READ-ONLY)  
근거: `reports/20260729_KATTACK_BAYES.md`

---

## 4) 산출물

- `docs/benchmarks/20260729_KBAYES_dyn_weight.json`
- `reports/20260729_KATTACK_BAYES.md`
- `tools/_k_attack_bayes.py`
