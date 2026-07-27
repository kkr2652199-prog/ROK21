# BENCH_PROTOCOL — 테스트로또 성적 비교 프로토콜 (K-B 고정)

📅 제정: 2026-07-27 · SSOT=`kkr2652199-prog/ROK21`  
📌 충돌 시 이 문서가 성적 수치의 우선순위.

---

## 1) 성적 SSOT (mean · K-08)

| 항목 | 값 |
|------|-----|
| 소스 | `testlotto_brain_review.predicted_sets_json` |
| 집계 | **전세트 mean** (회차×뇌당 5세트 전부) |
| 창 | **최근 100회차** 고정 (현재 실측 기준 1135–1234) |
| 적중 | 본번호 교집합 크기 (보너스는 mean에 미포함 · 별도 표기) |

이것이 STATUS·보고서·뇌 비교의 **유일한 성적 SSOT**.

---

## 2) 운영 / UI (성적 비교 금지)

| 항목 | 값 |
|------|-----|
| 소스 | `lotto_predictions` |
| 용도 | 클릭 캐시 · UI 표시 |
| 금지 | **뇌 실력·벤치 비교에 사용 금지** |
| 알려진 갭 | **1149–1179** (31회) — 2026-07-25 재기록 구멍 |

---

## 3) 학습 입력 (K-N 재검토)

| 항목 | 값 |
|------|-----|
| 경로 | `walkforward.review_single_draw` → `apply_feedback(best)` |
| 지표 | 회차당 **best 세트** `matched_count` |
| 저장 | `testlotto_brain_learn_state.recent_avg_match` (창 없는 누적) |
| 비고 | 성적 SSOT(mean)와 **다름**. K-N: best→분산 오인 가능성 · 재검토 대상 |

---

## 4) best 인용 규칙

- best / best-of-N / `recent_avg_match`를 쓸 때 **천장 ≈2.27** 병기 필수.
- best를 mean 대체 실력 지표로 쓰지 말 것 (K-08).

---

## 5) 표 작성 금지

- **표본이 다른 두 수치**(`review` JSON mean vs `lotto_predictions` mean 등)를 **같은 표에 나란히** 두지 말 것.
- 부득이 언급 시 출처·회차수·집계(전세트/best)를 칸마다 명시.

---

## 6) 관련 FINDINGS

K-B(표본충돌) · K-08(mean) · K-N(best 학습) · K-M(가중 실효≈0)
