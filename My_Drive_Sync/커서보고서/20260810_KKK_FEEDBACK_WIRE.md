# K-KK-FEEDBACK-WIRE

📅 2026-08-10 KST · wire=**True** · ge3=미사용  
도구: `tools/_k_kk_feedback_wire.py`

## 판정: **PATCHED**

## STEP0 진단
```json
{
  "routes_feedback_connected": true,
  "routes_feedback_line": 412,
  "coordinator_feedback_location": "both",
  "coordinator_note": "run_coordinated_prediction 진입 시 _auto_feedback(prev) 호출 기존 존재. 이번 패치는 routes 명시 + evolve_log 마크.",
  "apply_feedback_signature": "apply_feedback(brain_tag: 'str', draw_no: 'int', matched_count: 'int', missed_patterns: 'list[str]', *, window: 'int' = 20) -> 'dict[str, Any]'",
  "evolve_log_columns": [
    "draw_no",
    "brain_tag",
    "as_of",
    "schema_version",
    "weight_applied",
    "actual_nums_json",
    "pool_json",
    "repack_json",
    "pool_hits_json",
    "repack_hits_json",
    "best_hits",
    "mean_hits",
    "best_set_kind",
    "best_set_no",
    "features_json",
    "miss_tags_json",
    "assemble_mode",
    "note",
    "created_at",
    "updated_at"
  ],
  "weight_applied_write_path_exists": true,
  "apply_feedback_writes_evolve_log": false
}
```

## STEP1 설계
```json
{
  "trigger_point": "① POST /predict/{target} 후 apply_feedback_after_predict(target) → draw=target-1 · ② POST /fetch-latest 성공 시 해당 draw_no",
  "guard_duplicate": "evolve_log.note 에 K-KK-FEEDBACK 있으면 뇌별 SKIP · learn 은 last_draw_no>=draw 이면 apply_feedback 생략",
  "guard_future": "lotto_draws 에 해당 draw_no 없으면 SKIP(guard_future_no_draw)",
  "files_to_modify": [
    "app/testlotto/click_feedback.py (신규)",
    "app/testlotto/routes.py",
    "My_Drive_Sync/SUMMARY/FINDINGS.md (K-K)"
  ],
  "lines_to_add_approx": 220,
  "risk": "coordinator._auto_feedback 와 이중 호출 가능하나 last_draw/evolve 마크로 멱등. smoke 시 이미 학습된 회차는 learn SKIP·evolve 마크만."
}
```

## STEP2 패치
- 신규: `app/testlotto/click_feedback.py`
- 수정: `app/testlotto/routes.py` (`/predict`, `/fetch-latest`)
- coordinator/engine/random.choices/SCORE_WEIGHTS/**미수정**
- weight_applied **0.0 고정**

## STEP3 검증
| 항목 | 결과 |
|------|------|
| smoke 1230~1235 마크 | True (draws=6, rows=18) |
| evolve_log count | 60 → 60 |
| weight_applied=0 | True |
| 중복 SKIP | True |
| 미래 9999 SKIP | True |
| predict 무결성 | True |

## FINDINGS
- K-K → **PATCHED**
- K-M → HOLD 유지
- K-N → HOLD 유지

## 커서 의견
K-K 경로 연결 완료(routes 명시 + evolve 마크 + weight=0). 단 referee는 여전히 균등(K-M HOLD)이라 **학습 입력이 발권 가중으로 전달되지 않음**. K-M 착수 가능하나, 입력 지표가 best 오인(K-N)이면 가중 조정 전에 mean 입력 정합을 먼저 보는 편이 안전. 지금 당장 K-M GO는 **조건부 가능**(경로 살아 있음 · 실효격차 설계는 별도).
