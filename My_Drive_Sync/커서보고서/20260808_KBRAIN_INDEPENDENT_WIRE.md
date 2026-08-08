# K-BRAIN-INDEPENDENT-WIRE

📅 2026-08-08 KST · **WIRE_CONFORMS** · wire_checks **5/5** · EV=`MARGINAL` (consistent)

형 지시: 3뇌 독립 · 공유=lotto_draws만 · hint 분리 · 몰아주기=뇌별 특성 번호 · EV프록시 게이트(ge3 금지)

## [A] hint 뇌별 분리

| 뇌 | HINT_SPEC | top5 (probe 1235) |
|----|-----------|-------------------|
| stat | `(26, miss_pattern)` | 15, 28, 31, 13, 19 |
| markov | `(None, crowd_prefer)` | 12, 7, 3, 13, 18 |
| review | `(None, crowd_prize)` | 40, 37, 45, 39, 34 |

- `hint_shared_across_brains()=False`
- top5 3쌍 전부 상이 (`all_different=True`)
- pool/몰아주기는 **실뇌 패키지** (`stat_brain`/`markov_brain`/`review_brain`) — deprecated 래퍼 경로 제거
- `_build_hint`(zone_mix4)는 **fallback 호환**만 유지

### wire_checks

| check | pass | 요지 |
|-------|------|------|
| V1_hint_separated | ✅ | 3뇌 hint top5 분리 |
| V2_dead_wire_clear | ✅ | HINT_SPEC 변경→몰아주기 지문 변경 |
| V3_signal_top_per_brain | ✅ | 뇌별 score 번호가 자기 hint와 더 겹침 |
| V4_rng_independent | ✅ | C7 재확인 (단독=합동) |
| V5_draws_shared | ✅ | lotto_draws 공유·no_peek 유지 |

## [B] EV 프록시 소구간 게이트 (금액뇌)

- 구간 **1100~1235** · n=136 · **ge3 미사용**
- 지표: review hint top15 번호의 과거 `first_winners` 평균 − 전체45 평균
- `prize_proxy_delta=**-0.092741**` → 판정 **MARGINAL** (−0.5~0)
- 구간: early/mid/late **전부 음수** → `consistent=True`
- 의미: 금액뇌 hint가 인기 반대(비인기) 방향을 가리킴. STRONG(|Δ|>0.5)은 아님 → 과장 클레임 금지

## 롤백

`K_CROWD_PREFER=0` · `K_PRIZE_EV=0`

## 금지 준수

coordinator / `random.choices` / `_get_draws_before` / lotto_draws공유제거 / ge3-as-EV — **미접촉**

## 파일

- `app/testlotto/signal_pool.py` — HINT_SPEC 분리 · crowd_* hint
- `tools/_k_window_signal_survey.py` — PREDICT_MODULES→실뇌
- `tools/_k_brain_independent_wire.py`
- `docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json`
