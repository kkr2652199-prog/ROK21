# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-ATTACK-CONF-CAL 보류 · NEXT=OPEN

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| REFEREE | W=30 PASS |
| CONF-CAL | **보류** · max-conf≈null · ≪tier · WIRE 금지 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-ATTACK-CONF-CAL** | isotonic conf 세트순위 | 보류 (Δ+0.002 · ≪tier) |
| **K-REFEREE-WINDOW** | 슬라이딩 W=30 | PASS |
| **K-ATTACK-BAYES** | inv-corr | soft null |

---

## 2) CONF-CAL 핵심 (n_eval=1182)

| 정책 | mean |
|------|------|
| max conf / conf_cal | 0.825 / **0.827** |
| tier best_set | **1.708** |
| RR+tier | **1.743** |

근거: `docs/benchmarks/20260729_KCONFCAL_results.json`

---

## 3) 다음

`K-ATTACK-OPEN` — 다음 공격 레버 1건 선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_attack_conf_cal.py`
- `docs/benchmarks/20260729_KCONFCAL_results.json`
- `reports/20260729_KATTACK_CONF_CAL.md`
