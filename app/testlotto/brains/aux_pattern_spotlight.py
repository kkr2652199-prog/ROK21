"""패턴돋보기 — 쌍수·연속수·AC값 (SELMA consecutive + pair 벤치마킹).

[명분] 실증 · K-T 형태지표 이론부합 p≥0.13 · K-Z/K-AA 이론상수(AC최빈=8·consec PMF) · 출처 K-T·K-Z·K-AA
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


def score_set(nums: list[int], draws: list[dict], target_draw_no: int) -> float:
    feats = combo_features(nums, draws)
    pair_freq = build_pair_freq(draws)
    pairs = pair_set(nums)
    pair_score = sum(pair_freq.get(p, 0) for p in pairs)
    pair_norm = min(1.0, pair_score / 30.0)
    consec = feats["consecutive"]
    ac = feats["ac"]
    ac_score = 1.0 - min(1.0, abs(ac - AC_TARGET) / 10.0)
    consec_score = _CONSEC_SCORE.get(int(consec), 0.3)
    return max(0.1, min(1.0, 0.4 * pair_norm + 0.35 * ac_score + 0.25 * consec_score))


def describe(nums: list[int], draws: list[dict], target_draw_no: int) -> str:
    feats = combo_features(nums, draws)
    return f"패턴돋보기:AC{feats['ac']} 연속{feats['consecutive']} 점수{score_set(nums, draws, target_draw_no):.2f}"
