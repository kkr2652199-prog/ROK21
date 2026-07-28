# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-ATTACK-OPEN 서베이 · 3레버 FAIL · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| OPEN | A/B/C **전부 관측종료** · recommended=**없음** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-ATTACK-OPEN** | analog·markov tune·conf rebuild 서베이 | 추천없음 |
| **K-ATTACK-CONF-CAL** | conf 보정 | 보류 |
| **K-REFEREE-WINDOW** | W=30 | PASS |

---

## 2) OPEN 핵심

| 레버 | 지표 | verdict |
|------|------|---------|
| A | spearman −0.0023 | 관측종료 |
| B | best mean 0.8176 | 관측종료 |
| C | sp≈0.024 · spread5 | 관측종료 |

근거: `docs/benchmarks/20260729_KOPEN_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — 다음 공격 축 재선정 (승인 필요)

---

## 4) 산출물

- `tools/_k_attack_open_survey.py`
- `docs/benchmarks/20260729_KOPEN_survey.json`
- `reports/20260729_KATTACK_OPEN.md`
