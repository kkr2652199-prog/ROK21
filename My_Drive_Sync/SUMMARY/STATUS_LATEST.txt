# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-COVER-SURVEY FAIL · NEXT=HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| COVER | wheel/pool **ge3≤RR** · WIRE금지 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-COVER-SURVEY** | F1 wheel·pool 격자 | FAIL (ge3≤RR) |
| **K-HISIM-SURVEY** | 13D 구조우선 analog | 관측종료 |
| **K-STRUCT-SURVEY** | 4보조·analog | 관측종료 |

---

## 2) COVER 핵심

| 항목 | 값 |
|------|-----|
| baseline union | 25.85 |
| baseline mean / ge3 | 1.7614 / 0.1277 |
| best_combo | B (ge3 동일) |
| best_pool | **40** · mean **1.797** · ge3 **0.132** |
| spearman union↔best | **0.0253** (≤0.03) |
| vs RR ge3 | **미달** (0.132 < 0.1337) |
| vs RR mean | **상회** (추가 표기) |

근거: `docs/benchmarks/20260729_KCOVER_survey.json`

---

## 3) 다음

`K-ATTACK-HOLD` — 새 축 재선정 (승인 필요) · COVER-WIRE 금지

---

## 4) 산출물

- `tools/_k_cover_survey.py`
- `docs/benchmarks/20260729_KCOVER_survey.json`
- `reports/20260729_KCOVER_SURVEY.md`
