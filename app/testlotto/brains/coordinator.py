"""테스트로또 3+4 뇌 코디네이터 — 독립 예측3뇌 → 전용aux hint → 발권 → DB저장.

K-D: 클릭/백테의 **실제 융합 경로**. `fusion._vector_fusion_predict` 미사용.
K-FUTURE-WIRE: 각 독립뇌가 다음회(미래) 후보를 만들고, 뇌내 발권은
`aux_hint_score`(+ native_confidence)로 고른다. set_no_asc(과거 순서) 폐기.
표시용 AUX confidence 재작성은 유지하되 발권 키와 분리.
"""

from __future__ import annotations

import logging
import random

from app.testlotto.brains import aux_balance_keeper, aux_miss_detective, aux_pattern_spotlight, aux_referee
from app.testlotto.brains.stat_brain import aux as stat_brain_aux
from app.testlotto.brains.stat_brain import predict as stat_brain_predict
from app.testlotto.brains.markov_brain import aux as markov_brain_aux
from app.testlotto.brains.markov_brain import predict as markov_brain_predict
from app.testlotto.brains.review_brain import aux as review_brain_aux
from app.testlotto.brains.review_brain import predict as review_brain_predict
from app.testlotto.brains.shared import referee as shared_referee
from app.testlotto.brains.registry import AUX_BRAINS, PREDICT_BRAINS, SETS_PER_PREDICT_BRAIN
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state import get_referee_weights
from app.testlotto.models import get_lotto_db, init_lotto_db

logger = logging.getLogger(__name__)

PREDICT_MODULES = {
    "stat": stat_brain_predict,
    "markov": markov_brain_predict,
    "review": review_brain_predict,
}

AUX_MODULES = [
    aux_miss_detective,
    aux_pattern_spotlight,
    aux_balance_keeper,
    aux_referee,
]

AUX_WEIGHTS = [0.25, 0.25, 0.25, 0.25]
PREDICT_TAGS = [b["tag"] for b in PREDICT_BRAINS]

# K-BRAIN-PACKAGE-PHASE7: 뇌별 전용 aux 1:1 (False=4×0.25 전역 baseline)
AUX_1TO1_ENABLED: bool = True

BRAIN_DEDICATED_AUX = {
    "stat": stat_brain_aux,
    "markov": markov_brain_aux,
    "review": review_brain_aux,
}

# K-HIGHWAY-QUOTA: referee 가중 동적 5장 배분 · MARKOV_WIRE_ENABLED=False → conf top5
MARKOV_WIRE_ENABLED: bool = True
# K-FUSION-QUOTA-FIX: legacy pin (fallback only — 벤치 pin·롤백 참조)
DEFAULT_QUOTA_WEIGHTS: dict[str, float] = {"stat": 0.25, "markov": 0.60, "review": 0.15}
# K-FUSION-DYNAMIC-V2: 3뇌 solo ge3 — K-HIGHWAY-BACKTEST-100 by_brain (1135~1234)
SOLO_GE3_PRIORS: dict[str, float] = {"stat": 0.09, "markov": 0.13, "review": 0.11}
# K-QUOTA-MIN-EACH (20260812): 3뇌 독립 발권 — 뇌당 최소 1장 (total≥3)
# 구값 0: dominance 시 3번째 뇌 0장(예: m4/r1/s0) 허용 → 과거학습 발권 누락
QUOTA_ADAPTIVE_MIN_EACH: int = 1
# solo prior 기준 markov 1위(0.39) vs review 2위(0.33) ≈ 1.18 → 1.15로 floor 허용
# (min_each=1 이면 dominance 후에도 3뇌 ≥1 로 보정)
QUOTA_DOMINANCE_FLOOR: float = 1.15
# K-FUTURE-WIRE: 뇌 버킷 내 선별 — aux_hint_native | set_no_asc(legacy)
BUCKET_SELECT_MODE: str = "aux_hint_native"
# 독립뇌 RNG — 벤치 MC_SEED(42)와 동일 · 뇌마다 시드 리셋 → solo와 동치
BRAIN_RNG_SEED_BASE: int = 42


def _seed_independent_brain(target_draw_no: int) -> None:
    """각 예측뇌 generate 직전 시드 — 선행 뇌 RNG 오염 제거(미래예측 독립성)."""
    random.seed(BRAIN_RNG_SEED_BASE + int(target_draw_no))
# 벤치 pin 참조용 (production은 dynamic_brain_quota 사용)
MARKOV_WIRE_BRAIN_QUOTA: dict[str, int] = {"markov": 3, "stat": 1, "review": 1}
# K-QUOTA-D-WIRE (형 GO): 고정 슬롯 stat2/markov3/review0 (=30/60/10 · 5세트)
# None=production dynamic(구 0/4/1). 롤백 시 None 복원.
BENCH_FIXED_QUOTA: dict[str, int] | None = None

# K-TICKET-COVER-LITE (LIST_V3 L10): 발권5 선별 시 이미 고른 장과의 Jaccard 패널티.
# buy-the-pot/전수커버 아님 · 부분당첨 기회 분산(겹침↓)만. 기본 OFF(프로브 HOLD 시 유지).
TICKET_COVER_LITE: bool = False
TICKET_COVER_JACCARD_PENALTY: float = 1.0


def _cover_lite_pick(
    bucket: list[dict],
    k: int,
    already: list[dict],
    *,
    penalty: float,
) -> list[dict]:
    """버킷에서 k장 · 이미 선택된 장과의 평균 Jaccard 를 깎아 탐욕 선택."""
    from app.testlotto.set_diversity import jaccard

    if k <= 0 or not bucket:
        return []
    remaining = list(bucket)
    picked: list[dict] = []
    context = list(already)

    def _score(item: dict) -> float:
        conf = float(item.get("aux_hint_score") or 0.0) * 50.0 + float(
            item.get("native_confidence") or item.get("confidence") or 0.0
        )
        if not context:
            return conf
        nums = {int(x) for x in item["nums"]}
        avg_j = sum(jaccard(nums, {int(x) for x in p["nums"]}) for p in context) / len(
            context
        )
        return conf - float(penalty) * avg_j * 40.0

    while len(picked) < k and remaining:
        best = max(remaining, key=_score)
        remaining.remove(best)
        picked.append(best)
        context.append(best)
    return picked


def _get_quota_weights() -> dict[str, float]:
    """K-FUSION-DYNAMIC-V2: referee × solo_ge3_prior (고정 DEFAULT 미사용).

    3뇌 교체 후 solo 성적(K-HIGHWAY by_brain)을 prior로 · walk-forward referee가 미세조정.
    """
    ref = get_referee_weights()
    combined = {
        t: float(ref.get(t, 1.0 / len(PREDICT_TAGS)))
        * float(SOLO_GE3_PRIORS.get(t, 1.0 / len(PREDICT_TAGS)))
        for t in PREDICT_TAGS
    }
    total = sum(combined.values()) or 1.0
    if total <= 0:
        return {t: SOLO_GE3_PRIORS.get(t, 1.0 / len(PREDICT_TAGS)) for t in PREDICT_TAGS}
    return {k: v / total for k, v in combined.items()}


def _compute_dynamic_quota(
    referee_weights: dict[str, float],
    total: int = 5,
    min_each: int | None = None,
) -> dict[str, int]:
    """referee 가중 비례 배분 · adaptive min_each · dominance floor."""
    if min_each is None:
        min_each = QUOTA_ADAPTIVE_MIN_EACH

    tags_list = list(PREDICT_TAGS)
    n = len(tags_list)

    def _w(tag: str) -> float:
        return float(referee_weights.get(tag, 1.0 / n))

    # K-FUSION-DYNAMIC-V2: 성적 1위 뇌가 압도적이면 floor (total-1)/1 (예: 4/5)
    ranked = sorted(tags_list, key=_w, reverse=True)
    top, second = ranked[0], ranked[1]
    w_top, w_second = _w(top), _w(second)
    if (
        total >= 4
        and w_top >= 0.38
        and w_second > 0
        and w_top >= QUOTA_DOMINANCE_FLOOR * w_second
    ):
        others = [t for t in tags_list if t != top]
        winner = max(others, key=_w)
        quota: dict[str, int] = {t: 0 for t in tags_list}
        quota[top] = total - 1
        quota[winner] = 1
        # min_each>0: dominance가 3번째 뇌를 0으로 두지 않음 (top 초과분에서 이체)
        if min_each > 0 and total >= n * min_each:
            for t in tags_list:
                while quota[t] < min_each and quota[top] > min_each:
                    quota[top] -= 1
                    quota[t] += 1
        return quota

    floor_min = min_each * n
    if total < floor_min:
        each = max(1, total // n)
        return {t: each for t in tags_list}

    wsum = sum(_w(t) for t in tags_list) or 1.0
    raw = {t: total * _w(t) / wsum for t in tags_list}
    floor_slots = {t: max(min_each, int(raw[t])) for t in tags_list}

    while sum(floor_slots.values()) > total:
        trim_candidates = [t for t in tags_list if floor_slots[t] > min_each]
        if not trim_candidates:
            break
        drop = max(trim_candidates, key=lambda t: floor_slots[t] - raw[t])
        floor_slots[drop] -= 1

    deficit = total - sum(floor_slots.values())
    if deficit > 0:
        order = sorted(
            tags_list, key=lambda t: raw[t] - int(raw[t]), reverse=True
        )
        for i in range(deficit):
            floor_slots[order[i % len(order)]] += 1
    return floor_slots


def _sort_brain_bucket(bucket: list[dict]) -> list[dict]:
    """뇌 버킷 내 선별 — aux_hint_native(미래신호) 또는 set_no_asc(legacy)."""
    if BUCKET_SELECT_MODE == "aux_hint_native":
        return sorted(
            bucket,
            key=lambda x: (
                float(x.get("aux_hint_score") or 0.0),
                float(x.get("native_confidence") or x.get("confidence") or 0.0),
            ),
            reverse=True,
        )
    return sorted(
        bucket,
        key=lambda x: int(
            x.get("pred_set_no") or x.get("set_no") or x.get("rank") or 0
        ),
    )


def _ensure_brain_future_signals(
    candidates: list[dict], draws: list[dict], target_draw_no: int
) -> list[dict]:
    """독립뇌 미래예측 신호 보강 — native_confidence · aux_hint_score."""
    out: list[dict] = []
    for c in candidates:
        row = dict(c)
        if "native_confidence" not in row:
            row["native_confidence"] = float(row.get("confidence") or 60)
        if "aux_hint_score" not in row:
            tag = str(row.get("brain_tag") or "")
            dedicated = BRAIN_DEDICATED_AUX.get(tag)
            if dedicated is not None:
                try:
                    row["aux_hint_score"] = float(
                        dedicated.score_set(
                            row["nums"], draws, target_draw_no, brain_tag=tag or None
                        )
                    )
                except Exception:
                    row["aux_hint_score"] = 0.5
            else:
                row["aux_hint_score"] = 0.5
        out.append(row)
    return out


def dynamic_brain_quota(candidates: list[dict]) -> list[dict]:
    """K-FUTURE-WIRE: referee 동적 쿼터 · 뇌내 aux_hint_native 선별."""
    target_n = 5
    if not candidates:
        return candidates

    if not MARKOV_WIRE_ENABLED:
        return sorted(
            candidates,
            key=lambda x: (
                float(x.get("aux_hint_score") or 0),
                float(x.get("native_confidence") or x.get("confidence") or 0),
            ),
            reverse=True,
        )[:target_n]

    from collections import defaultdict

    quota = (
        dict(BENCH_FIXED_QUOTA)
        if BENCH_FIXED_QUOTA is not None
        else _compute_dynamic_quota(_get_quota_weights(), total=target_n)
    )
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in quota:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in quota.items():
        bucket = _sort_brain_bucket(brain_buckets.get(tag) or [])
        if TICKET_COVER_LITE and int(cap) > 0:
            selected.extend(
                _cover_lite_pick(
                    bucket,
                    int(cap),
                    selected,
                    penalty=TICKET_COVER_JACCARD_PENALTY,
                )
            )
        else:
            selected.extend(bucket[:cap])

    if len(selected) < target_n:
        used = {id(c) for c in selected}
        remainder = [
            c for c in candidates if id(c) not in used
        ]
        if TICKET_COVER_LITE:
            need = target_n - len(selected)
            selected.extend(
                _cover_lite_pick(
                    _sort_brain_bucket(remainder),
                    need,
                    selected,
                    penalty=TICKET_COVER_JACCARD_PENALTY,
                )
            )
        else:
            remainder = sorted(
                remainder,
                key=lambda x: (
                    float(x.get("aux_hint_score") or 0),
                    float(x.get("native_confidence") or x.get("confidence") or 0),
                ),
                reverse=True,
            )
            for c in remainder:
                selected.append(c)
                if len(selected) >= target_n:
                    break
    return selected[:target_n]


def apply_markov_wire_quota(candidates: list[dict]) -> list[dict]:
    """벤치 도구 호환 alias → dynamic_brain_quota."""
    return dynamic_brain_quota(candidates)


def _detect_missed_patterns(
    pred_nums: list[int],
    actual_nums: list[int],
    draws_before: list[dict] | None = None,
) -> list[str]:
    """K-HIGHWAY-FEEDBACK: 예측 vs 정답 오답 패턴 태그 (apply_feedback 호환)."""
    from app.testlotto.features.draw_features import build_number_gaps, sorted_nums

    pred_set = set(int(n) for n in pred_nums)
    actual_set = set(int(n) for n in actual_nums)
    missed: list[str] = []

    if draws_before:
        prev = draws_before[-1]
        prev_nums = set(sorted_nums(prev))
        actual_carry = prev_nums & actual_set
        if actual_carry and not (actual_carry & pred_set):
            missed.append("carry_over")

        gaps = build_number_gaps(draws_before)
        actual_overdue = [n for n in actual_set if gaps.get(n, 0) >= 30]
        if actual_overdue and not any(n in pred_set for n in actual_overdue):
            missed.append("overdue")

    actual_endings = {n % 10 for n in actual_set}
    pred_endings = {n % 10 for n in pred_set}
    if len(actual_endings.symmetric_difference(pred_endings)) >= 3:
        missed.append("ending_digit")

    return missed


def _prediction_row_nums(row: dict) -> list[int]:
    return [
        int(row["num1"]),
        int(row["num2"]),
        int(row["num3"]),
        int(row["num4"]),
        int(row["num5"]),
        int(row["num6"]),
    ]


# K-EVOLVE-SIGNAL / K-N: best 단독 학습 오인 차단 → 뇌 내 세트 mean 사용
# "best" = 구경로(비권고) · "mean" = Phase2 기본
FEEDBACK_MATCH_MODE: str = "mean"


def _auto_feedback(target_draw_no: int, conn) -> None:
    """직전 회차 예측·정답으로 learn_state 피드백 (중복 apply 방지)."""
    from app.testlotto.learn_state import _load_global_learn_state, apply_feedback

    prev_draw_no = int(target_draw_no) - 1
    if prev_draw_no < 1:
        return

    actual_row = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no = ?", (prev_draw_no,)
    ).fetchone()
    if not actual_row:
        return

    actual = dict(actual_row)
    actual_nums = [
        actual["num1"],
        actual["num2"],
        actual["num3"],
        actual["num4"],
        actual["num5"],
        actual["num6"],
    ]
    actual_set = set(actual_nums)

    pred_rows = conn.execute(
        "SELECT * FROM lotto_predictions WHERE target_draw_no = ?",
        (prev_draw_no,),
    ).fetchall()
    if not pred_rows:
        try:
            from app.testlotto.pool_hit_ledger import write_pool_hit_ledger

            write_pool_hit_ledger(prev_draw_no, note="auto_feedback_no_pred")
        except Exception:
            logger.exception(
                "[K-POOL-HIT-LEDGER] auto_feedback write failed draw=%s",
                prev_draw_no,
            )
        try:
            from app.testlotto.skill_homework import write_skill_homework

            write_skill_homework(prev_draw_no, note="auto_feedback_no_pred")
        except Exception:
            logger.exception(
                "[L9c-SKILL-HW] auto_feedback write failed draw=%s", prev_draw_no
            )
        return

    draws_before = _get_draws_before(prev_draw_no)

    by_brain: dict[str, list[dict]] = {}
    for row in pred_rows:
        tag = str(dict(row).get("brain_tag") or "")
        if tag not in PREDICT_TAGS:
            continue
        by_brain.setdefault(tag, []).append(dict(row))

    from app.testlotto.brain_review_mirror import upsert_brain_review_feedback

    for tag in PREDICT_TAGS:
        rows = by_brain.get(tag)
        if not rows:
            continue

        scored: list[tuple[int, list[int], dict]] = []
        for row in rows:
            pred_nums = _prediction_row_nums(row)
            mc = len(set(pred_nums) & actual_set)
            if int(row.get("matched_count") or -1) >= 0:
                mc = int(row["matched_count"])
            scored.append((mc, pred_nums, row))

        if FEEDBACK_MATCH_MODE == "best":
            pick = max(scored, key=lambda s: (s[0], float(s[2].get("confidence") or 0)))
            matched_count = int(pick[0])
            pred_nums = pick[1]
            best_set_no = int(pick[2].get("set_no") or pick[2].get("pred_set_no") or 1)
        else:
            # mean: 실력 지표 · miss 태그는 mean에 가장 가까운 세트에서 추출
            mean_mc = sum(s[0] for s in scored) / len(scored)
            matched_count = int(round(mean_mc))
            pick = min(scored, key=lambda s: (abs(s[0] - mean_mc), -s[0]))
            pred_nums = pick[1]
            best_set_no = int(pick[2].get("set_no") or pick[2].get("pred_set_no") or 1)

        missed = _detect_missed_patterns(pred_nums, actual_nums, draws_before)
        # L9b: learn 중복이어도 CUTOFF SSOT(brain_review)는 항상 미러
        upsert_brain_review_feedback(
            prev_draw_no,
            tag,
            predicted_nums=pred_nums,
            matched_count=matched_count,
            missed=missed,
            best_set_no=best_set_no,
            source="auto_feedback",
        )

        state = _load_global_learn_state(tag)
        if int(state.get("last_draw_no", 0) or 0) >= prev_draw_no:
            logger.debug(
                "[K-HIGHWAY-FEEDBACK] learn-skip %s draw=%d (last_draw_no=%s) review=upserted",
                tag,
                prev_draw_no,
                state.get("last_draw_no"),
            )
            continue

        apply_feedback(tag, prev_draw_no, matched_count, missed)
        logger.info(
            "[K-HIGHWAY-FEEDBACK] %s draw=%d mode=%s matched=%d missed=%s",
            tag,
            prev_draw_no,
            FEEDBACK_MATCH_MODE,
            matched_count,
            missed,
        )

    # L3: 직전 회차 원장 (예측 피드백과 독립 · 실패 무시)
    try:
        from app.testlotto.pool_hit_ledger import write_pool_hit_ledger

        wr = write_pool_hit_ledger(prev_draw_no, note="auto_feedback")
        if not wr.get("ok"):
            logger.warning(
                "[K-POOL-HIT-LEDGER] auto_feedback write skip draw=%s %s",
                prev_draw_no,
                wr,
            )
    except Exception:
        logger.exception(
            "[K-POOL-HIT-LEDGER] auto_feedback write failed draw=%s", prev_draw_no
        )

    # L9c: 뇌별 스킬 hint 숙제 (원장과 독립 · 실패 무시)
    try:
        from app.testlotto.skill_homework import write_skill_homework

        hw = write_skill_homework(prev_draw_no, note="auto_feedback")
        if not hw.get("ok"):
            logger.warning(
                "[L9c-SKILL-HW] auto_feedback write skip draw=%s %s",
                prev_draw_no,
                hw,
            )
    except Exception:
        logger.exception(
            "[L9c-SKILL-HW] auto_feedback write failed draw=%s", prev_draw_no
        )


def _delete_predictions_for_brain(conn, target_draw_no: int, brain_tag: str) -> None:
    conn.execute(
        "DELETE FROM lotto_predictions WHERE target_draw_no = ? AND brain_tag = ?",
        (target_draw_no, brain_tag),
    )


def _aux_composite_score(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    if AUX_1TO1_ENABLED and brain_tag:
        dedicated = BRAIN_DEDICATED_AUX.get(brain_tag)
        if dedicated is not None:
            return dedicated.score_set(
                nums, draws, target_draw_no, brain_tag=brain_tag
            )
    total = 0.0
    for mod, w in zip(AUX_MODULES, AUX_WEIGHTS):
        total += w * mod.score_set(nums, draws, target_draw_no, brain_tag=brain_tag)
    return total


def _aux_notes(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None,
) -> str:
    if AUX_1TO1_ENABLED and brain_tag:
        dedicated = BRAIN_DEDICATED_AUX.get(brain_tag)
        if dedicated is not None:
            return " | ".join(
                [
                    dedicated.describe(
                        nums, draws, target_draw_no, brain_tag=brain_tag
                    ),
                    shared_referee.describe(
                        nums, draws, target_draw_no, brain_tag=brain_tag
                    ),
                ]
            )
    return " | ".join(
        m.describe(nums, draws, target_draw_no, brain_tag=brain_tag)
        for m in AUX_MODULES
    )


def apply_coordinator_scoring(
    candidates: list[dict], draws: list[dict], target_draw_no: int
) -> list[dict]:
    """K-PIPE-A: walk-forward·live predict 공통 4보조+referee confidence (nums 불변)."""
    return _apply_aux_scoring(candidates, draws, target_draw_no)


def _apply_aux_scoring(candidates: list[dict], draws: list[dict], target_draw_no: int) -> list[dict]:
    """표시용 confidence 재작성 · 발권 키(native/aux_hint)는 보존."""
    candidates = _ensure_brain_future_signals(candidates, draws, target_draw_no)
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_score = _aux_composite_score(c["nums"], draws, target_draw_no, brain_tag=tag)
        native = float(c.get("native_confidence") or c.get("confidence") or 60)
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, native * 0.5 * brain_w + aux_score * 40 + native * 0.1)
        aux_notes = _aux_notes(c["nums"], draws, target_draw_no, tag)
        out.append(
            {
                **c,
                "native_confidence": native,
                "confidence": round(final_conf, 1),
                "reasoning": f"{c.get('reasoning', '')} [보조4뇌:{aux_score:.2f}] {aux_notes}",
            }
        )
    return out


def run_coordinated_prediction(
    target_draw_no: int,
    brain_filter: tuple[str, ...] = (),
    *,
    prebuilt_candidates: list[dict] | None = None,
) -> dict:
    """3 미래예측 뇌 × 5세트 + 4 보조 뇌 채점.

    prebuilt_candidates: L12b E 전용. pool 생성1회에서 뽑은 skill1~5.
    있으면 predict_sets를 다시 돌리지 않는다. quota5·BT 기본경로는 불변.
    """
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    init_lotto_db()
    conn = get_lotto_db()
    _auto_feedback(target_draw_no, conn)
    bf = brain_filter
    # 학습/심판 가중: target 미만만 (CUTOFF 기본 ON)
    set_learn_as_of(int(target_draw_no))

    def run(tag: str) -> bool:
        return (not bf) or (tag in bf)

    existing = conn.execute(
        "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no = ?",
        (target_draw_no,),
    ).fetchall()
    tags_in_db = {r[0] for r in existing}
    if existing and (not bf) and all(t in tags_in_db for t in PREDICT_TAGS):
        conn.close()
        from app.testlotto.brains.warrant import get_brain_warrant
        from app.testlotto.engine import _build_cached_response

        cached = _build_cached_response(target_draw_no)
        cached["brain_warrant"] = get_brain_warrant()
        return cached

    draws = _get_draws_before(target_draw_no)
    if not draws:
        conn.close()
        return {"error": f"이전 당첨 데이터가 없습니다. {target_draw_no}회차 이전 회차를 먼저 수집하세요."}

    candidates: list[dict] = []
    brain_errors: dict[str, str] = {}
    if prebuilt_candidates is not None:
        # L12b E: pool skill1~5를 발권 후보로. predict_sets 재실행 없음.
        for brain in PREDICT_BRAINS:
            tag = brain["tag"]
            if run(tag):
                _delete_predictions_for_brain(conn, target_draw_no, tag)
        for s in prebuilt_candidates:
            tag = str(s.get("brain_tag") or "")
            if not run(tag):
                continue
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or 1)
            conf = float(s.get("confidence", 60))
            candidates.append(
                {**s, "confidence": conf, "pred_set_no": sn, "set_no": sn}
            )
        logger.info("[테스트로또] prebuilt skill 후보 %d장 (L12b E)", len(candidates))
    else:
        for brain in PREDICT_BRAINS:
            tag = brain["tag"]
            if not run(tag):
                continue
            mod = PREDICT_MODULES[tag]
            _delete_predictions_for_brain(conn, target_draw_no, tag)
            # 독립뇌: 뇌마다 동일 회차 시드로 재시작 (stat RNG가 markov를 오염시키던 구조 제거)
            # K-I: 단일 뇌 예외가 전체 실패로 전파되지 않게 try 보호
            _seed_independent_brain(target_draw_no)
            try:
                sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
            except Exception as exc:  # noqa: BLE001
                brain_errors[tag] = f"{type(exc).__name__}: {exc}"
                logger.exception("[테스트로또] %s 생성 실패 — 타뇌 계속", brain["name"])
                continue
            for i, s in enumerate(sets):
                sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
                conf = float(s.get("confidence", 60))
                candidates.append(
                    {**s, "confidence": conf, "pred_set_no": sn, "set_no": sn}
                )
            logger.info("[테스트로또] %s %d세트", brain["name"], len(sets))

    if not candidates:
        conn.rollback()
        conn.close()
        return {"error": "생성할 예측이 없습니다 (brain_filter·이전 데이터 확인)."}

    scored = _apply_aux_scoring(candidates, draws, target_draw_no)
    scored.sort(key=lambda x: x["confidence"], reverse=True)

    # ── K-V 발권 후처리 dedup (뇌/fusion/referee 미수정) ──
    from app.testlotto.ticket_dedup import dedup_enabled, dedup_ticket_list

    dedup_stats: dict = {"dedup_enabled": False, "unresolved_count": 0}
    if dedup_enabled():

        def _regen(
            brain_tag: str,
            seen: set[tuple[int, ...]],
            replace_of: dict | None = None,
        ):
            mod = PREDICT_MODULES.get(brain_tag)
            if mod is None:
                return None
            # 같은 뇌·같은 draws · 독립 시드로 1세트 재요청
            _seed_independent_brain(target_draw_no)
            try:
                raw = mod.predict_sets(draws, 1)
            except Exception as exc:  # noqa: BLE001
                logger.warning("[테스트로또] dedup regen %s 실패: %s", brain_tag, exc)
                return None
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, target_draw_no)[0]

        scored, dedup_stats = dedup_ticket_list(scored, regenerate=_regen)
        scored.sort(key=lambda x: x["confidence"], reverse=True)

    # K-FUTURE-WIRE: 생성 15 → solo×ref 쿼터 5장 (뇌내 aux_hint_native)
    wire_quota = _compute_dynamic_quota(_get_quota_weights()) if MARKOV_WIRE_ENABLED else {}
    scored = dynamic_brain_quota(scored)
    if MARKOV_WIRE_ENABLED:
        dedup_stats = {
            **dedup_stats,
            "markov_wire": True,
            "markov_wire_method": "dynamic_referee_quota",
            "bucket_select_mode": BUCKET_SELECT_MODE,
            "wire_quota": dict(wire_quota),
            "issued_sets": len(scored),
        }

    actual_row = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no = ?", (target_draw_no,)
    ).fetchone()
    actual_nums: set[int] | None = None
    actual_bonus = 0
    if actual_row:
        actual = dict(actual_row)
        actual_nums = {
            actual["num1"],
            actual["num2"],
            actual["num3"],
            actual["num4"],
            actual["num5"],
            actual["num6"],
        }
        actual_bonus = actual["bonus"]

    for pred in scored:
        matched = -1
        bonus_matched = 0
        if actual_nums:
            pred_set = set(pred["nums"])
            matched = len(pred_set & actual_nums)
            bonus_matched = 1 if actual_bonus in pred_set else 0
        conn.execute(
            """INSERT INTO lotto_predictions
               (target_draw_no, method, brain_tag, num1, num2, num3, num4, num5, num6,
                confidence, reasoning, matched_count, bonus_matched)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                target_draw_no,
                pred["method"],
                pred.get("brain_tag", "legacy"),
                pred["nums"][0],
                pred["nums"][1],
                pred["nums"][2],
                pred["nums"][3],
                pred["nums"][4],
                pred["nums"][5],
                pred["confidence"],
                pred["reasoning"],
                matched,
                bonus_matched,
            ),
        )

    conn.commit()
    conn.close()

    from app.testlotto.engine import _build_cached_response

    out = _build_cached_response(target_draw_no)
    out["status"] = "예측 완료 (3+4뇌 체계)"
    out["brain_system"] = "testlotto_3predict_4aux"
    out["dedup"] = dedup_stats
    if brain_errors:
        out["brain_errors"] = dict(brain_errors)
        out["status"] = f"예측 완료 (일부뇌 스킵: {','.join(brain_errors)})"
    # 명분 라벨 데이터만 적재 (UI 노출 금지 · 산출/dedup 로직 무관)
    from app.testlotto.brains.warrant import get_brain_warrant

    out["brain_warrant"] = get_brain_warrant()
    if len(draws) < 10:
        out["warning"] = f"데이터 부족 (이전 {len(draws)}회)"
    return out


def get_brain_status_summary() -> dict:
    """두뇌 상태 API용 3+4 체계 요약."""
    return {
        "system": "testlotto_3predict_4aux",
        "predict_brains": PREDICT_BRAINS,
        "aux_brains": AUX_BRAINS,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "total_predict_sets": SETS_PER_PREDICT_BRAIN * len(PREDICT_BRAINS),
    }
