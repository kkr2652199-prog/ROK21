# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-ATTACK-SLICE · 구간승격 보류 · NEXT=BAYES

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| BASELINE_PIN | **`640cb67`** |
| 3DB MAX | **1234** |
| GATHER | 관측고정 (아이디어 OK · WIRE 보류) |
| SLICE | 관측유지 · 배선 보류 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-ATTACK-SLICE** | LMH 승격 정책 비교 · live conf proxy | 배선 보류 |
| **K-GATHER-V2** | V축소 covering | 회수0 · 관측고정 |
| **K-GATHER-V1** | oracle 찢김 | 회수0 |

---

## 2) SLICE 핵심

| 항목 | 값 |
|------|-----|
| conf_only mean | 0.826 |
| conf top2→222 | 0.823 (무이득) |
| conf top2 oracle | **1.226** (정렬 개선 여지) |

---

## 3) 다음

`K-ATTACK-BAYES` — 3뇌 동적가중  
근거: `reports/20260729_KATTACK_SLICE.md`

---

## 4) 산출물

- `docs/benchmarks/20260729_KATTACK_slice.json`
- `reports/20260729_KATTACK_SLICE.md`
