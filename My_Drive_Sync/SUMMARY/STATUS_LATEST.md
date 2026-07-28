# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-REFEREE-WINDOW PASS · NEXT=CONF-CAL 복귀

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| 3DB MAX | **1234** |
| REFEREE | **W=30 슬라이딩** · max_gap **0.1334** PASS |
| GATHER/SLICE/BAYES | 배선 보류 유지 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-REFEREE-WINDOW** | recent_avg_match 누적→창30 · cutoff 동시 | PASS |
| **K-ATTACK-BAYES** | inv-corr 동적가중 | soft null · vs RR 패배 |
| **K-ATTACK-SLICE** | LMH 승격 | 배선 보류 |

---

## 2) REFEREE 핵심

| 뇌 | 누적(구) | W=30 |
|----|----------|------|
| stat | 1.7186 | 1.6667 |
| markov | 1.7167 | **1.5333** |
| review | 1.6975 | 1.6667 |

근거: `docs/benchmarks/20260729_KREFEREE_WINDOW.json`

---

## 3) 다음

`K-ATTACK-CONF-CAL` — 뇌내 conf 보정·세트순위 (READ-ONLY)

---

## 4) 산출물

- `app/testlotto/learn_state.py` · `learn_state_cutoff.py`
- `tools/_k_referee_window_verify.py`
- `docs/benchmarks/20260729_KREFEREE_WINDOW.json`
- `reports/20260729_KREFEREE_WINDOW.md`
