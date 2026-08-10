# K-N-MEAN-INPUT-FIX

📅 2026-08-10 KST · **3뇌 테스트/개발 단계** · ge3 미사용

## 판정: **PATCHED**

## 이해 (형)
지금은 개발·테스트. 1237 개발 완료 후 양산 준비. 이번은 3뇌 학습입력 정합.

## 패치
- `walkforward.py`: `_learn_match_from_sets` · `apply_feedback`에 **mean** 입력
- best/tier는 표시·`best_matched` 참고만
- `FEEDBACK_MATCH_MODE` = `mean` (coordinator와 공유)
- click_feedback / coordinator `_auto_feedback` 이미 mean — 정렬 확인

## 검증
- unit: best=3 vs learn_mean=1 (고분산 best 오인 사례) → `{'learn_matched': 1, 'learn_set_no': 5, 'best_would_be_matched': 3, 'best_would_be_set': 3, 'unit_ok': True}`
- smoke review 1235: `{'draw_no': 1235, 'skipped': None, 'n_rows': 3, 'feedback_modes': ['mean', 'mean', 'mean'], 'matched_counts_learn': [0, 1, 1], 'best_matcheds': [1, 2, 2], 'all_mode_mean': True, 'ok': True}`

## FINDINGS
- K-N → **PATCHED**
- K-M → HOLD (다음)

## 커서 의견
walkforward 학습입력을 coordinator/click_feedback과 동일 mean으로 정합. best는 tier/표시만. K-M(referee 균등)이 다음 — 학습 신호가 mean으로 들어가도 referee가 평탄하면 발권 비중은 안 움직임.
