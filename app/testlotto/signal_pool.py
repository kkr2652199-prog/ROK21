"""10세트 pool + 신호 몰아주기(repack) — survey 도구와 UI 공용 (coordinator 미수정)."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Any

from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state_cutoff import set_learn_as_of

# bench_quick_gate / survey 와 동일 상수
MC_SEED = 42
POOL_SETS_PER_BRAIN = 10
REPACK_SETS_PER_BRAIN = 5
WINDOW_WEEKS = 4
WINDOW_SIGNAL = "zone_mix"
BRAIN_TAGS = ["markov", "stat", "review"]
LEARN_EMA = 0.15
W_HINT = 0.40
W_FREQ = 0.25
W_LEARN = 0.35

# K-REPACK-HYBRID-WIRE — ablation 20260804: stat/review hy_p45_r123 · markov baseline
# pool set 4+5 + score-몰아주기 rank1~3 → 발권 5장 (중복 시 rank4/5·다른 pool로 보충)
HYBRID_P45_R123_BRAINS: frozenset[str] = frozenset({"stat", "review"})
HYBRID_ASSEMBLE_MODE: str = "p45_r123"  # "" 이면 전원 baseline 몰아주기

# K-EVOLVE-FEAT-LAM-WIRE — SIGNAL PartB: review λ=0.3 only
FEATURE_LAMBDA_WIRE: bool = True


class RollingSignalLearner:
    """Walk-forward: target draw 이전 회차만으로 번호·세트위치 기여도 EMA."""

    def __init__(self) -> None:
        self.num_hit_ema: dict[int, float] = {n: 0.0 for n in range(1, 46)}
        self.pos_hit_ema: dict[int, float] = {n: 0.0 for n in range(1, POOL_SETS_PER_BRAIN + 1)}

    def snapshot(self) -> tuple[dict[int, float], dict[int, float]]:
        return dict(self.num_hit_ema), dict(self.pos_hit_ema)

    def update_from_pool(
        self,
        pool_by_brain: dict[str, list[dict]],
        actual: set[int],
    ) -> None:
        for _tag, pool in pool_by_brain.items():
            for c in pool:
                sn = int(c.get("pred_set_no") or c.get("set_no") or 1)
                nums = [int(x) for x in c["nums"]]
                mc = len(set(nums) & actual)
                if mc <= 0:
                    continue
                pos_credit = mc / 6.0
                old_p = self.pos_hit_ema.get(sn, 0.0)
                self.pos_hit_ema[sn] = (1 - LEARN_EMA) * old_p + LEARN_EMA * pos_credit
                per_num = mc / 6.0
                for n in nums:
                    if n in actual:
                        old = self.num_hit_ema.get(n, 0.0)
                        self.num_hit_ema[n] = (1 - LEARN_EMA) * old + LEARN_EMA * per_num


def _live_candidates(draws: list[dict], draw_no: int) -> list[dict]:
    """Coordinator live WF — survey _k_window_signal_survey._live_candidates 와 동일."""
    from tools._k_window_signal_survey import _live_candidates as _lc

    return _lc(draws, draw_no)


def expand_pool(draws: list[dict], draw_no: int, *, seed: int = MC_SEED) -> list[dict]:
    """Survey-only 10-set/brain: 2× predict_sets (seed offset on pass 2)."""
    pool: list[dict] = []
    for pass_idx in range(2):
        if pass_idx == 0:
            random.seed(seed)
        else:
            random.seed(seed + 10000 + draw_no)
        batch = _live_candidates(draws, draw_no)
        for c in batch:
            base_sn = int(c.get("pred_set_no") or c.get("set_no") or 1)
            c = {**c, "pred_set_no": base_sn + pass_idx * SETS_PER_PREDICT_BRAIN}
            c["set_no"] = c["pred_set_no"]
            pool.append(c)
    return pool


def _pool_by_brain(pool: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in pool:
        tag = c.get("brain_tag", "")
        if tag in out:
            out[tag].append(c)
    return out


def _pool_freq(pool: list[dict]) -> dict[int, float]:
    cnt: Counter[int] = Counter()
    for c in pool:
        for n in c["nums"]:
            cnt[int(n)] += 1
    mx = max(cnt.values()) if cnt else 1
    return {n: cnt.get(n, 0) / mx for n in range(1, 46)}


def number_scores(
    pool: list[dict],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_scores: bool = False,
) -> dict[int, float]:
    freq = _pool_freq(pool)
    pos_boost: dict[int, float] = defaultdict(float)
    for c in pool:
        sn = int(c.get("pred_set_no") or 1)
        pw = pos_ema.get(sn, 0.0)
        for n in c["nums"]:
            pos_boost[int(n)] = max(pos_boost[int(n)], pw)

    scores: dict[int, float] = {}
    for n in range(1, 46):
        if random_scores:
            scores[n] = random.random()
        elif hint_only:
            scores[n] = max(0.0, hint.get(n, 0.0))
        else:
            scores[n] = (
                W_HINT * max(0.0, hint.get(n, 0.0))
                + W_FREQ * freq.get(n, 0.0)
                + W_LEARN * (num_ema.get(n, 0.0) + 0.5 * pos_boost.get(n, 0.0))
            )
    return scores


def repack_sets(scores: dict[int, float], n_sets: int = REPACK_SETS_PER_BRAIN) -> list[list[int]]:
    ranked = sorted(range(1, 46), key=lambda x: (-scores[x], x))
    sets: list[list[int]] = []
    idx = 0
    for _ in range(n_sets):
        chunk = ranked[idx : idx + 6]
        idx += 6
        sets.append(sorted(chunk))
    return sets


def _nums_key(nums: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def assemble_hybrid_p45_r123(
    pool: list[dict],
    classic_repack: list[list[int]],
    *,
    n_sets: int = REPACK_SETS_PER_BRAIN,
) -> list[dict]:
    """pool set_no 4·5 + 점수몰아주기 rank1~3 조립 (K-REPACK-HYBRID).

    Returns list of {nums, source, source_set_no} length ≤ n_sets.
    """
    p_by = {
        int(c.get("pred_set_no") or c.get("set_no") or 0): [int(x) for x in c["nums"]]
        for c in pool
    }
    primary: list[tuple[list[int], str, int]] = []
    for sn in (4, 5):
        if sn in p_by:
            primary.append((p_by[sn], "pool", sn))
    for i, nums in enumerate(classic_repack[:3]):
        primary.append((list(nums), "score_repack", i + 1))
    fillers: list[tuple[list[int], str, int]] = []
    for i, nums in enumerate(classic_repack[3:], start=4):
        fillers.append((list(nums), "score_repack", i))
    for sn in sorted(p_by):
        if sn not in (4, 5):
            fillers.append((p_by[sn], "pool", sn))

    out: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for nums, src, ssn in primary + fillers:
        key = _nums_key(nums)
        if key in seen or len(nums) != 6:
            continue
        seen.add(key)
        out.append({"nums": sorted(nums), "source": src, "source_set_no": ssn})
        if len(out) >= n_sets:
            break
    return out


def repack_by_brain(
    pool_by_brain: dict[str, list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_repack: bool = False,
    target_draw_no: int | None = None,
) -> list[dict]:
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN, apply_feature_lambda

    out: list[dict] = []
    for tag in BRAIN_TAGS:
        pool = pool_by_brain.get(tag, [])
        if not pool:
            continue
        scores = number_scores(
            pool,
            hint,
            num_ema,
            pos_ema,
            hint_only=hint_only,
            random_scores=random_repack,
        )
        classic = repack_sets(scores)
        use_hybrid = (
            HYBRID_ASSEMBLE_MODE == "p45_r123" and tag in HYBRID_P45_R123_BRAINS
        )
        assembled_rows: list[dict] = []
        if use_hybrid:
            assembled = assemble_hybrid_p45_r123(pool, classic)
            for i, item in enumerate(assembled):
                assembled_rows.append(
                    {
                        "nums": item["nums"],
                        "brain_tag": tag,
                        "pred_set_no": i + 1,
                        "set_no": i + 1,
                        "repack_rank": i + 1,
                        "kind": "repack",
                        "assemble": "hy_p45_r123",
                        "source": item["source"],
                        "source_set_no": item["source_set_no"],
                    }
                )
        else:
            for i, nums in enumerate(classic):
                assembled_rows.append(
                    {
                        "nums": nums,
                        "brain_tag": tag,
                        "pred_set_no": i + 1,
                        "set_no": i + 1,
                        "repack_rank": i + 1,
                        "kind": "repack",
                        "assemble": "baseline_repack",
                    }
                )

        if (
            FEATURE_LAMBDA_WIRE
            and target_draw_no is not None
            and tag in FEATURE_LAMBDA_BY_BRAIN
        ):
            lam_rows = apply_feature_lambda(
                tag, pool, assembled_rows, int(target_draw_no)
            )
            if lam_rows:
                out.extend(lam_rows)
                continue
        out.extend(assembled_rows)
    return out


def _build_hint(draws: list[dict], draw_no: int) -> dict[int, float]:
    from tools._k_window_signal_survey import _build_hint as _bh

    return _bh(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)


def warm_learner_to_draw(
    learner: RollingSignalLearner,
    draw_start: int,
    before_draw: int,
    *,
    seed: int = MC_SEED,
) -> None:
    """draw_start .. before_draw-1 까지 WF로 learner EMA 갱신 (컨닝 없음)."""
    from app.testlotto.models import get_lotto_db

    if before_draw <= draw_start:
        return
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no >= ? AND draw_no < ? ORDER BY draw_no",
            (draw_start, before_draw),
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        row = dict(row)
        dno = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue
        random.seed(seed)
        pool = expand_pool(draws, dno, seed=seed)
        pool_br = _pool_by_brain(pool)
        learner.update_from_pool(pool_br, actual)


def build_pool_and_repack(
    target_draw_no: int,
    *,
    seed: int = MC_SEED,
    learner_warm_start: int | None = None,
) -> dict[str, Any]:
    """단일 회차 10세트 pool + 5 몰아주기 세트 (뇌별). walk-forward only."""
    set_learn_as_of(target_draw_no)
    draws = _get_draws_before(target_draw_no)
    if not draws:
        return {"ok": False, "error": f"{target_draw_no}회 이전 데이터 없음"}

    warm_from = learner_warm_start if learner_warm_start is not None else max(1, target_draw_no - 200)
    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, warm_from, target_draw_no, seed=seed)
    num_ema, pos_ema = learner.snapshot()

    random.seed(seed)
    pool = expand_pool(draws, target_draw_no, seed=seed)
    pool_br = _pool_by_brain(pool)
    hint = _build_hint(draws, target_draw_no)
    repacked = repack_by_brain(
        pool_br, hint, num_ema, pos_ema, target_draw_no=target_draw_no
    )

    by_brain_pool: dict[str, list[dict]] = {}
    for tag in BRAIN_TAGS:
        sets = sorted(pool_br.get(tag, []), key=lambda x: int(x.get("pred_set_no") or 0))
        by_brain_pool[tag] = [
            {
                "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                "nums": [int(x) for x in c["nums"]],
                "brain_tag": tag,
                "kind": "pool",
            }
            for c in sets
        ]

    by_brain_repack: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in repacked:
        tag = str(c["brain_tag"])
        entry: dict[str, Any] = {
            "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
            "nums": [int(x) for x in c["nums"]],
            "brain_tag": tag,
            "kind": "repack",
            "assemble": c.get("assemble") or "baseline_repack",
        }
        if c.get("source"):
            entry["source"] = c["source"]
            entry["source_set_no"] = c.get("source_set_no")
        by_brain_repack.setdefault(tag, []).append(entry)

    return {
        "ok": True,
        "target_draw_no": target_draw_no,
        "no_peek": True,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "repack_sets_per_brain": REPACK_SETS_PER_BRAIN,
        "seed": seed,
        "window_hint": {"weeks": WINDOW_WEEKS, "signal": WINDOW_SIGNAL},
        "hybrid": {
            "mode": HYBRID_ASSEMBLE_MODE,
            "brains": sorted(HYBRID_P45_R123_BRAINS),
            "markov": "baseline_repack",
        },
        "feature_lambda": _feature_lambda_meta(),
        "pool_by_brain": by_brain_pool,
        "repack_by_brain": by_brain_repack,
    }


def _feature_lambda_meta() -> dict[str, Any]:
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN

    return {"wired": FEATURE_LAMBDA_WIRE, "by_brain": dict(FEATURE_LAMBDA_BY_BRAIN)}
