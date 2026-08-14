# K-ROLE-TIER-LEARN-WIRE — 6~8/9~10 원장복습 (stat만)

시각: 2026-08-14T20:24:37+09:00 · **WIRE_OK** · 1~5 불변 · ge3미클레임 · 1237아님

## 0) 형이 시킨 것

- 3뇌 동시 튜닝 안 함 → **첫 뇌=과거학습(stat)**
- 1~5 = 현행 엔진 유지
- 6~8 = 3등 지향 **과거 원장 복습** (이 뇌 4~5맞 번호)
- 9~10 = 2등 지향 **과거 보너스·5맞 복습** (타깃 보너스 입력 금지)
- 학습/복습 = 결과 확정 후 저장, 다음 예측은 `as_of < target` 만 읽음 (스킬 숙제와 같은 뼈대)

## 1) 배선

| 항목 | 값 |
|------|-----|
| `ROLE_TIER_LEARN_WIRE` | True |
| 소비 뇌 | ['stat'] |
| 테이블 | `testlotto_role_homework` |
| 쓰기 | click_feedback / `_auto_feedback` (원장 다음) |
| 롤백 | 플래그 False 또는 BRAINS 비우기 |

markov·review 6~10은 **구 Jaccard/랜덤 6번째** 유지.

## 2) 검증

hard_ok=**True**

```json
{
  "write_ok": true,
  "load_before_target_has_stat": true,
  "load_asof_not_self": true,
  "peek_draws": true,
  "roles_ok": true,
  "tnb1": true,
  "stat_cover_hw": true,
  "markov_cover_jaccard": true,
  "stat_shape_hw": true,
  "markov_shape_classic": true,
  "skill_5_each": true,
  "reset_lists_table": true,
  "wired_click": true,
  "wired_auto": true,
  "wire_flag": true,
  "brains_stat_only": true,
  "no_peek_load": true
}
```

stat cover source: ['cover_r3_role_hw', 'cover_r3_role_hw', 'cover_r3_role_hw']
markov cover source: ['cover_r3_jaccard', 'cover_r3_jaccard', 'cover_r3_jaccard']

등수 횟수로 APPLY하지 않음. 다음 뇌(markov)는 형 1건.

## 3) 금지 지킨 것

- 타깃 보너스/당첨 미입력 (T-NB1 True)
- `_get_draws_before` 미수정 · random.choices 미수정 · boost 상한 미수정
- 1~5 predict_sets 경로 미수정
