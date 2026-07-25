# stat boost 최적값 역산 (READ-ONLY)

- **일시**: 2026-07-25 (KST)
- **데이터**: `testlotto_brain_review` stat **1,230**행 (draw **2~1231**)
- **방법**: 3축 그리드 × 오프라인 재채점 — **DB·learn_state 쓰기 0건**

---

## 시뮬레이션 규칙

| 항목 | 내용 |
|------|------|
| boost 후보 | carry / ending / overdue 각 `{0.0, 0.1, 0.2, 0.3, 0.5}` → **125**조합 |
| draws | `_get_draws_before(draw_no)` — target **미포함** (`data_service.py:684`) |
| miss_counts | `weight_snapshot` stat at **draw_no−1** (walk-forward) |
| 샘플링 | `predict_statistical.py:187-188` 동일 `random.choices`, `seed=20260725+draw_no×9973` |
| base weights | 피드백(`get_feedback_summary`)까지 — learn boost만 그리드값으로 치환 |

**컨닝 없음 근거**: 회차 N 예측에 N 당첨·N 이후 review 미사용. miss_counts는 N−1 스냅샷만.

---

## 상위 3조합

| 순위 | carry | ending | overdue | avg match | match_sum | reviewed |
|------|-------|--------|---------|-----------|-----------|----------|
| **1** | **0.2** | **0.3** | **0.2** | **1.7171** | 2112 | 1230 |
| 2 | 0.2 | 0.3 | 0.1 | 1.7138 | 2108 | 1230 |
| 2 | 0.2 | 0.3 | 0.3 | 1.7138 | 2108 | 1230 |

**추천 조합 (1위)**: `carry=0.2, ending=0.3, overdue=0.2`

---

## 현재값(전부 0.5) vs 최적

| 항목 | carry | ending | overdue | avg match | **순위** |
|------|-------|--------|---------|-----------|----------|
| **현재(production 상한)** | 0.5 | 0.5 | 0.5 | **1.6724** | **124 / 125** |
| **추천(1위)** | 0.2 | 0.3 | 0.2 | **1.7171** | **1 / 125** |
| **최하위** | 0.3 | 0.5 | 0.5 | 1.6659 | 125 / 125 |

- 현재 0.5³ vs 1위: **−0.0447** (−2.6%p) — **과보정 가설 지지**
- boost **0** (`0,0,0`): avg **1.6862**, 순위 **90 / 125** — 적정 boost는 0.1~0.3대

---

## 전체 125조합

전수표: `backups/20260725_boost_grid.json` → `all_combos` (avg_match 내림차순)

---

## 소견

1. **DB 역산 결과**, 최적은 **0.5가 아니라 0.2/0.3/0.2** — ending만 0.3으로 상대적으로 큼.
2. **현재 0.5 상한은 125개 중 124위** — 거의 최악. A배선 후 1132~1231 하락(1.70→1.63)과 정합.
3. **적용 시 주의**: `apply_feedback` 상한 0.5는 **튜닝 대상** — 역산 추천은 **초기값**이며, 적용 후 동일 프로토콜 WF 재측정 필수.
4. 역산은 **random 시드 고정** 오프라인 재채점; 실제 learn_state 동적 누적과 100% 동일하지 않을 수 있음.
5. **다음**: 추천 boost를 `apply_feedback` cap 또는 `_statistical_predict` 배선에 반영 → 1132~1231 재측정.

---

*스크립트*: `tools/_reverse_stat_boost_grid.py` · elapsed **103.6s**
