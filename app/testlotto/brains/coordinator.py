"""테스트로또 3+4 뇌 코디네이터 — 예측3뇌 생성 → 보조4뇌 채점 → DB저장.

K-D: 클릭/백테의 **실제 융합 경로**. `fusion._vector_fusion_predict` 미사용.
AUX 점수는 `AUX_WEIGHTS`(균등 0.25×4) + referee brain 가중.
"""

from __future__ import annotations

import logging

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

# K-MARKOV-WIRE: markov 배합 가중 (E_markov3mix2 실력 p=0.0007)
# 생성은 SETS_PER_PREDICT_BRAIN×3=15 유지 · 발권 선택만 쿼터 적용
MARKOV_WIRE_BRAIN_QUOTA: dict[str, int] = {
    "markov": 3,
    "stat": 1,
    "review": 1,
}
MARKOV_WIRE_ENABLED: bool = True  # K-MARKOV-WIRE-V2: set_no 쿼터


def apply_markov_wire_quota(candidates: list[dict]) -> list[dict]:
    """뇌별 set_no/pred_set_no 오름차순으로 쿼터만큼 선택 (confidence 정렬 없음)."""
    if not MARKOV_WIRE_ENABLED or not candidates:
        return candidates
    from collections import defaultdict

    quota = MARKOV_WIRE_BRAIN_QUOTA
    target_n = sum(quota.values())
    brain_buckets: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        tag = str(c.get("brain_tag", "") or "")
        if tag in quota:
            brain_buckets[tag].append(c)

    selected: list[dict] = []
    for tag, cap in quota.items():
        bucket = sorted(
            brain_buckets.get(tag) or [],
            key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or x.get("rank") or 0),
        )
        selected.extend(bucket[:cap])

    if len(selected) < target_n:
        used = {id(c) for c in selected}
        remainder = sorted(
            [c for c in candidates if id(c) not in used],
            key=lambda x: float(x.get("confidence") or 0),
            reverse=True,
        )
        for c in remainder:
            selected.append(c)
            if len(selected) >= target_n:
                break
    return selected[:target_n]


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
        return

    draws_before = _get_draws_before(prev_draw_no)

    by_brain: dict[str, list[dict]] = {}
    for row in pred_rows:
        tag = str(dict(row).get("brain_tag") or "")
        if tag not in PREDICT_TAGS:
            continue
        by_brain.setdefault(tag, []).append(dict(row))

    for tag in PREDICT_TAGS:
        rows = by_brain.get(tag)
        if not rows:
            continue

        state = _load_global_learn_state(tag)
        if int(state.get("last_draw_no", 0) or 0) >= prev_draw_no:
            logger.debug(
                "[K-HIGHWAY-FEEDBACK] skip %s draw=%d (last_draw_no=%s)",
                tag,
                prev_draw_no,
                state.get("last_draw_no"),
            )
            continue

        best_row = max(
            rows,
            key=lambda r: (
                int(r.get("matched_count") if r.get("matched_count") is not None else -1),
                float(r.get("confidence") or 0),
            ),
        )
        pred_nums = _prediction_row_nums(best_row)
        matched_count = len(set(pred_nums) & actual_set)
        if int(best_row.get("matched_count") or -1) >= 0:
            matched_count = int(best_row["matched_count"])

        missed = _detect_missed_patterns(pred_nums, actual_nums, draws_before)
        apply_feedback(tag, prev_draw_no, matched_count, missed)
        logger.info(
            "[K-HIGHWAY-FEEDBACK] %s draw=%d matched=%d missed=%s",
            tag,
            prev_draw_no,
            matched_count,
            missed,
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
    ref_weights = get_referee_weights()
    out: list[dict] = []
    for c in candidates:
        tag = c.get("brain_tag", "") or None
        aux_score = _aux_composite_score(c["nums"], draws, target_draw_no, brain_tag=tag)
        base = float(c.get("confidence", 60))
        brain_w = ref_weights.get(c.get("brain_tag", ""), 1.0 / 3)
        final_conf = min(99.5, base * 0.5 * brain_w + aux_score * 40 + base * 0.1)
        aux_notes = _aux_notes(c["nums"], draws, target_draw_no, tag)
        out.append(
            {
                **c,
                "confidence": round(final_conf, 1),
                "reasoning": f"{c.get('reasoning', '')} [보조4뇌:{aux_score:.2f}] {aux_notes}",
            }
        )
    return out


def run_coordinated_prediction(target_draw_no: int, brain_filter: tuple[str, ...] = ()) -> dict:
    """3 미래예측 뇌 × 5세트 + 4 보조 뇌 채점."""
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
    for brain in PREDICT_BRAINS:
        tag = brain["tag"]
        if not run(tag):
            continue
        mod = PREDICT_MODULES[tag]
        _delete_predictions_for_brain(conn, target_draw_no, tag)
        sets = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
            candidates.append({**s, "pred_set_no": sn, "set_no": sn})
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
            # 같은 뇌·같은 draws 조건으로 1세트 재요청
            raw = mod.predict_sets(draws, 1)
            if not raw:
                return None
            return _apply_aux_scoring(raw, draws, target_draw_no)[0]

        scored, dedup_stats = dedup_ticket_list(scored, regenerate=_regen)
        scored.sort(key=lambda x: x["confidence"], reverse=True)

    # K-MARKOV-WIRE-V2: 생성 15 → set_no 쿼터 발권(markov3+stat1+review1)
    scored = apply_markov_wire_quota(scored)
    if MARKOV_WIRE_ENABLED:
        dedup_stats = {
            **dedup_stats,
            "markov_wire": True,
            "markov_wire_method": "set_no_asc",
            "wire_quota": dict(MARKOV_WIRE_BRAIN_QUOTA),
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
