"""review_brain.engine — 금액뇌 생성 엔진 (이월·neutralize + 비선호 혼합)."""

from __future__ import annotations

import random

# K-REVIEW-SEQ-DISTRIBUTE (20260822) — 45소진 찌꺼기장. 롤백용 잔존.
REVIEW_SEQ_DISTRIBUTE: bool = False
# K-REVIEW-REASONABLE-SET (20260822)
# 장마다 1~45 리셋 후 합리한 장(tier1). Jaccard멀리·45소진 없음. #1=먼저 완성된 장.
# 장끼리 같은 번호 겹침 허용. random.choices 라인 동결. 롤백: False.
REVIEW_REASONABLE_SET: bool = True


def review_compose_mode() -> str:
    if REVIEW_REASONABLE_SET:
        return "reasonable"
    if REVIEW_SEQ_DISTRIBUTE:
        return "seq"
    return "legacy"

from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
from app.testlotto.filters import tier1_filter


def build_review_weights(draws: list[dict], adj: dict | None = None) -> dict[int, float]:
    """review 가중치 구성 (K-X 경로). random.choices 직전까지."""
    if not draws:
        return {n: 1.0 for n in range(1, 46)}
    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    carry_boost = 1.0 + float((adj or {}).get("carry_over_boost", 0))
    weights = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= 1.8 * carry_boost
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= 0.85
    weights = neutralize_ending_digit_mass(weights)
    # 금액뇌: 저당첨자수 회차·고번호 비선호 신호를 가중치에만 혼합
    # random.choices 라인은 그대로
    try:
        from app.testlotto.brains.shared import crowd_signal

        if crowd_signal.prize_on():
            weights = crowd_signal.blend_weights(
                weights,
                crowd_signal.prize_table(draws, brain="review"),
                brain="review",
            )
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.testlotto.brains.review_brain.shape_table import (
            REVIEW_SHAPE_WIRE,
            apply_consec_flatten,
        )

        if REVIEW_SHAPE_WIRE:
            weights = apply_consec_flatten(weights)
    except Exception:  # noqa: BLE001
        pass
    return weights


def neutralize_ending_digit_mass(weights: dict[int, float]) -> dict[int, float]:
    """K-P3: 끝수별 총 질량을 균등화해 repeat_rate 끝수 투영 완화.

    random.choices 라인은 건드리지 않음. 가중치만 조정.
    """
    end_sum: dict[int, float] = {d: 0.0 for d in range(10)}
    for n, w in weights.items():
        end_sum[n % 10] += max(float(w), 0.0)
    total = sum(end_sum.values()) or 1.0
    target_per_end = total / 10.0
    out: dict[int, float] = {}
    for n, w in weights.items():
        e = n % 10
        factor = target_per_end / max(end_sum[e], 1e-12)
        out[n] = max(float(w), 0.0) * factor
    return out


def generate(draws: list[dict], n_sets: int = 5, adj: dict | None = None) -> list[dict]:
    if not draws:
        return []

    prev = draws[-1]
    prev_nums = sorted_nums(prev)
    rates = repeat_rate_after_draw(draws)
    weights = build_review_weights(draws, adj)
    kb7: dict = {}
    try:
        from app.testlotto.brains.review_brain.kb7_future import (
            REVIEW_KB7_WIRE,
            apply_kb7_weights,
            collect_before,
        )

        kb7 = collect_before(draws)
        if REVIEW_KB7_WIRE:
            weights = apply_kb7_weights(weights, kb7)
    except Exception:  # noqa: BLE001
        kb7 = {}

    results: list[dict] = []
    used: set[tuple[int, ...]] = set()
    attempts = 0
    seq = review_compose_mode() == "seq"
    pool = list(range(1, 46))
    w = [weights[n] for n in pool]
    while len(results) < n_sets and attempts < 3000:
        attempts += 1
        if not seq:
            pool = list(range(1, 46))
            w = [weights[n] for n in pool]
        elif len(pool) < 6:
            pool = list(range(1, 46))
            w = [weights[n] for n in pool]
        pick: list[int] = []
        for _ in range(6):
            if not pool:
                break
            chosen = random.choices(pool, weights=w, k=1)[0]
            pick.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)
        pick = sorted(pick)
        if len(pick) != 6:
            continue
        key = tuple(pick)
        if key in used:
            continue
        if not tier1_filter(pick):
            continue
        try:
            from app.testlotto.brains.review_brain.rare_pass_store import should_pass
            from app.testlotto.brains.review_brain.rare_slice import REVIEW_RARE_SLICE_WIRE

            if REVIEW_RARE_SLICE_WIRE and should_pass(pick):
                continue
        except Exception:  # noqa: BLE001
            pass
        try:
            from app.testlotto.brains.review_brain.draw_shape_kb import (
                REVIEW_SHAPE_KB_WEIGHT_WIRE,
                keep_set_by_hist,
            )

            if REVIEW_SHAPE_KB_WEIGHT_WIRE:
                hist = (kb7 or {}).get("shape")
                if hist is None:
                    from app.testlotto.brains.review_brain.draw_shape_kb import last_read

                    hist = last_read()
                if not keep_set_by_hist(pick, hist):
                    continue
        except Exception:  # noqa: BLE001
            pass
        try:
            from app.testlotto.brains.review_brain.kb7_future import (
                REVIEW_KB7_WIRE,
                should_skip_kb7,
            )

            if REVIEW_KB7_WIRE and should_skip_kb7(pick, kb7):
                continue
        except Exception:  # noqa: BLE001
            pass
        used.add(key)
        repeat_hits = [n for n in pick if n in prev_nums]
        conf = 60 + len(repeat_hits) * 5 + sum(rates.get(n, 0) for n in repeat_hits) * 20
        results.append(
            {
                "nums": pick,
                "confidence": min(95, conf),
            }
        )
    return results
