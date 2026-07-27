"""패턴돋보기 — 쌍수·연속수·AC값 (SELMA consecutive + pair 벤치마킹).

[명분] 실증 · K-T 형태지표 이론부합 p≥0.13 · K-Z/K-AA 이론상수(AC최빈=8·consec PMF) · 출처 K-T·K-Z·K-AA
[K-AG] pair 정규화 = window100 null_q95(32.0) · pair_boost/consecutive_boost 소비
"""

from __future__ import annotations

from app.testlotto.features.draw_features import ac_value, build_pair_freq, combo_features, consecutive_pairs, pair_set

# C(45,6) 연속쌍 개수 PMF (K-Z 전수) → 점수 ∈ [0.3, 0.7], 순위=확률순위, 0≠1 동점 해소
# score = 0.3 + 0.4 * (p / p_mode), p_mode=p(0)≈0.4713
_CONSEC_SCORE: dict[int, float] = {
    0: 0.7,
    1: 0.6428,  # p≈0.4039
    2: 0.3952,  # p≈0.1122
    3: 0.3103,  # p≈0.0121
    4: 0.3004,  # p≈0.0005
    5: 0.3,  # p≈4.91e-6
}

AC_TARGET = 8  # C(45,6) AC 최빈 (K-Z)

# K-AG STEP0: pair_score null(5000) q95 @ window=100, as_of=1234
# docs/benchmarks/20260727_KAG_step0_measure.json → pair.null_5000.q95
# 고빈도쌍=당첨유리 해석 금지(K-U FDR0). 구 /30 은 출처 없는 상수.
PAIR_NORM_DIVISOR = 32.0


def _learn_boosts(brain_tag: str | None) -> tuple[float, float]:
    if not brain_tag:
        return 0.0, 0.0
    try:
        from app.testlotto.learn_state import load_learn_state

        adj = load_learn_state(brain_tag).get("adjustments") or {}
    except (ValueError, Exception):
        return 0.0, 0.0
    return (
        float(adj.get("pair_boost", 0) or 0),
        float(adj.get("consecutive_boost", 0) or 0),
    )


def score_set(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> float:
    feats = combo_features(nums, draws)
    pair_freq = build_pair_freq(draws)
    pairs = pair_set(nums)
    pair_score = sum(pair_freq.get(p, 0) for p in pairs)
    pair_norm = min(1.0, pair_score / PAIR_NORM_DIVISOR)
    consec = feats["consecutive"]
    ac = feats["ac"]
    ac_score = 1.0 - min(1.0, abs(ac - AC_TARGET) / 10.0)
    consec_score = _CONSEC_SCORE.get(int(consec), 0.3)

    pair_b, consec_b = _learn_boosts(brain_tag)
    # 키=0이면 기존과 항등: *(1+0)
    pair_term = min(1.0, pair_norm * (1.0 + pair_b))
    consec_term = min(1.0, consec_score * (1.0 + consec_b))

    return max(0.1, min(1.0, 0.4 * pair_term + 0.35 * ac_score + 0.25 * consec_term))


def describe(
    nums: list[int],
    draws: list[dict],
    target_draw_no: int,
    brain_tag: str | None = None,
) -> str:
    feats = combo_features(nums, draws)
    return (
        f"패턴돋보기:AC{feats['ac']} 연속{feats['consecutive']} "
        f"점수{score_set(nums, draws, target_draw_no, brain_tag=brain_tag):.2f}"
    )
