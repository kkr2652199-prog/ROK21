# PINNED_PLAN — 형계획 메타선별 (ROK21)

> **핀 선언**: 변경 시 형 승인 필요. 2026-07-26 확정.

## 목표
뇌당 5세트 × N뇌 예측 풀에서, 과거 빅데이터만으로 **6수(+보너스 후보)를 재조립**하는 메타선별기.

## 금지
- 컷닝: `_get_draws_before` / 메타·유사검색도 `draw_no < target`만
- `random.choices` 동결 (B단계 전)
- 원본 `D:\3kweon` 미접촉 · SSOT = ROK21

## 성공(1차)
walk-forward에서 메타 avg_match가 **동일 회차 best 단일세트(~2.22)** 를 상회.  
cover&lt;6 → 「풀 부족」 분리 리포트 (선별 실패와 혼동 금지).

## 고정 사실
| 사실 | 값 |
|------|-----|
| 3뇌 합집합 cover6 | ~27.9% |
| avg 풀 cover / best세트 | 4.87 / 2.22 |
| Vote≥2 단독 | 0.79 → **기각** |

## Phase (건너뛰기 금지)
| Phase | 내용 | 상태 |
|-------|------|------|
| P0 | 핀 문서화 | DONE — PINNED_PLAN · roadmap · external_methods_pin |
| P1 | 보조4뇌 시드 + Vote 하이브리드 WF | DONE — pass_p1=false (seed/meta 0.80 vs oracle 2.22) |
| P2 | cover=6 규칙 마이닝 | DONE — cover6_rule_candidates · hist_only best on cover6 |
| P3 | 유사과거 렌즈 5종 swarm | DONE — KEEP=L_ending · 나머지 REJECT |
| P4 | 다양성 KPI (뇌 추가 게이트) | DONE — diversity_kpi · gate_pass=true |
| P5 | meta_assemble_sets 앱 레벨 | DONE — meta_picker + /api/testlotto/meta/* · UI deferred |

### P1 실측 메모
- 그리드 최적: min_vote=2, replace_slots=0 (슬롯 교체는 평균 악화)
- 보조4뇌 시드 ↔ 오라클 best 괴리 큼 → 시드 재설계는 **형 승인(핀 변경)**

## 운영용 시드 (오라클 아님)
보조4뇌(miss/pattern/balance/referee) 합산 최고 세트 1개 → Vote≥2/≥3 후보로 0~2슬롯 교체.

## Track A
튜닝은 병행 유지·핀의 주인공 아님. ending_digit 수정 완료. 전구간 재WF는 메타 1차 통과 후.

## 산출
- `docs/benchmarks/20260726_형계획_세트합집합_메타선별/`
- `tools/run_meta_*.py`, `tools/run_cover6_*.py`, `tools/run_similar_*.py`, `tools/run_diversity_*.py`
- 매 Phase 종료: 보고서 + STATUS + BOOT + push(ROK21)
