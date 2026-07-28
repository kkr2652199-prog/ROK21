# K-REFEREE-WINDOW — referee 슬라이딩 윈도우

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KREFEREE_WINDOW.json`  
📌 패치: `learn_state.py` + `learn_state_cutoff.py`  
📌 검증: `tools/_k_referee_window_verify.py` (matched 재생 · cutoff 동기)

---

## 0) 검토

NEXT=`K-REFEREE-WINDOW` 정합 · learn_state+cutoff 동시 · 동결 토큰·가중 공식 미수정.

---

## 1) 변경

| 항목 | 내용 |
|------|------|
| `REFEREE_WINDOW` | **30** |
| `recent_match_window` | state_json 키 추가 (스키마 불변) |
| `recent_avg_match` | 누적평균 → 창 mean |
| `get_referee_weights` | `1.0 + avg*0.15` **유지** |

---

## 2) before / after (2~1234 · n_events=3698)

| 뇌 | 누적평균(구공식 재현) | 슬라이딩 W=30 |
|----|----------------------|---------------|
| stat | 1.7186 | **1.6667** |
| markov | 1.7167 | **1.5333** |
| review | 1.6975 | **1.6667** |

| 지표 | 값 |
|------|-----|
| before max_gap | 0.0211 |
| **after max_gap** | **0.1334** |
| cutoff≡global | **true** |
| **pass** (≥0.01) | **true** |

참고: 외부AI 메모의「≈0.80」은 1장 null mean. 본 벤치의 `matched_count`는 best_set 기준이라 누적도 ≈1.7. 패치 효과는 **뇌간 격차 확대**(0.02→0.13).

---

## 3) 검증 방법

- 기본: 기존 `brain_review` matched 시계열 → `apply_feedback_pure` 재생 → 전역 저장 + cutoff rebuild  
- 풀 `review_single_draw` 재예측은 `--full-wf` (≈50분·예측 SSOT 변경) — 이번 턴 미실행

---

## 4) 다음

`K-ATTACK-CONF-CAL` 복귀 (ARCHIVE → NEXT).  
referee 배선은 이미 공식 유지 · 창 반영은 다음 예측/복습부터 유효.
