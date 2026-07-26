# -*- coding: utf-8 -*-
"""D 하이브리드 EV 리랭커 — 메타 조립 *이후* 후보 재정렬만.

활성: 환경변수 ROK21_EV_RERANK=1
기본: OFF (호출부에서 미진입 시 현행 A 경로 불변)

학습: draws_before 만 사용 (target 미만 — 호출자가 _get_draws_before 로 전달).
실패 시: None 반환 → 호출부가 A 결과 유지.
"""
from __future__ import annotations

import math
import os
from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# 생존 피처 (단변량 유의만)
FEATURE_NAMES = ("n_le31", "n_le12", "sum_nums", "carry_from_prev")


def ev_rerank_enabled() -> bool:
    return os.environ.get("ROK21_EV_RERANK", "").strip() == "1"


def _sorted_nums(d: dict) -> list[int]:
    return sorted(int(d[f"num{i}"]) for i in range(1, 7))


def _feat(nums: list[int], prev: list[int] | None) -> np.ndarray:
    s = sorted(int(x) for x in nums)
    return np.array(
        [
            sum(1 for x in s if x <= 31),
            sum(1 for x in s if x <= 12),
            float(sum(s)),
            0.0 if prev is None else float(len(set(s) & set(prev))),
        ],
        dtype=float,
    )


def _train_popularity(
    draws_before: list[dict],
    *,
    min_rows: int = 50,
) -> tuple[Any, Any] | None:
    """draw_no < target 인 draws_before 만으로 Ridge 학습.

    컨닝 차단 지점: 이 함수는 draws_before 외 DB를 읽지 않는다.
    prize tiers는 선택 — 없으면 total_sales+first 근사 불가 시 None.
    """
    from app.testlotto.models import get_lotto_db

    if len(draws_before) < min_rows:
        return None
    max_dn = max(int(d["draw_no"]) for d in draws_before)
    conn = get_lotto_db()
    try:
        tiers = {
            int(r["draw_no"]): dict(r)
            for r in conn.execute(
                """
                SELECT draw_no, winner_count, prize_per_game
                FROM testlotto_draw_prize_tiers
                WHERE tier_rank = 3 AND draw_no <= ?
                """,
                (max_dn,),
            )
        }
    finally:
        conn.close()

    xs, ys = [], []
    prev = None
    for d in draws_before:
        dn = int(d["draw_no"])
        t = tiers.get(dn)
        sales = float(d.get("total_sales") or 0)
        nums = _sorted_nums(d)
        if t and sales > 0 and int(t.get("winner_count") or 0) > 0:
            y = math.log(int(t["winner_count"]) / sales)
            xs.append(_feat(nums, prev))
            ys.append(y)
        prev = nums
    if len(xs) < min_rows:
        return None
    X = np.vstack(xs)
    y = np.array(ys, dtype=float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = Ridge(alpha=10.0, random_state=20260726)
    model.fit(Xs, y)
    return model, scaler


def _popularity_hat(model, scaler, nums: list[int], prev: list[int] | None) -> float:
    x = _feat(nums, prev).reshape(1, -1)
    return float(model.predict(scaler.transform(x))[0])


def pick_d_hybrid(
    pool_sets: list[list[int]],
    draws_before: list[dict],
    *,
    k: int = 3,
) -> list[list[int]] | None:
    """D = 0.5*norm(EV) + 0.5*norm(marginal coverage), greedy K.

    Returns None on any failure (caller keeps A).
    """
    try:
        if not pool_sets or k < 1:
            return None
        trained = _train_popularity(draws_before)
        if trained is None:
            return None
        model, scaler = trained
        prev = _sorted_nums(draws_before[-1]) if draws_before else None
        pops = [_popularity_hat(model, scaler, list(s), prev) for s in pool_sets]
        evs = np.array([-p for p in pops], dtype=float)
        span = max(1e-9, float(evs.max() - evs.min()))
        ev_n = (evs - evs.min()) / span

        remaining = list(range(len(pool_sets)))
        picked: list[list[int]] = []
        covered: set[int] = set()
        kk = min(k, len(pool_sets))
        while len(picked) < kk and remaining:
            best_i, best_sc = None, -1e9
            for i in remaining:
                s = set(int(x) for x in pool_sets[i])
                sc = 0.5 * float(ev_n[i]) + 0.5 * (len(s - covered) / 6.0)
                if sc > best_sc:
                    best_sc, best_i = sc, i
            assert best_i is not None
            remaining.remove(best_i)
            nums = sorted(int(x) for x in pool_sets[best_i])
            picked.append(nums)
            covered |= set(nums)
        return picked
    except Exception:
        return None


def maybe_apply_d_rerank(
    pool_sets: list[list[int]],
    draws_before: list[dict],
    a_assembled: list[dict[str, Any]],
    *,
    k: int = 3,
    ending_hook: Any | None = None,
) -> list[dict[str, Any]]:
    """메타 A 결과 위에 D 적용. OFF/실패 시 a_assembled 그대로 반환."""
    if not ev_rerank_enabled():
        return a_assembled
    picked = pick_d_hybrid(pool_sets, draws_before, k=k)
    if not picked:
        return a_assembled

    out: list[dict[str, Any]] = []
    for i, nums in enumerate(picked):
        meta_extra: dict[str, Any] = {"ev_rerank": "D_hybrid_0.5_0.5", "k09": "미해결전제"}
        final_nums = list(nums)
        n_replaced = 0
        if i == 0 and ending_hook is not None:
            try:
                hy = ending_hook(final_nums)
                if isinstance(hy, dict) and "nums" in hy:
                    final_nums = list(hy["nums"])
                    n_replaced = int(hy.get("n_replaced") or 0)
                    meta_extra["ending"] = hy
            except Exception:
                pass
        out.append(
            {
                "nums": final_nums,
                "method": "ev_d_hybrid" + ("_ending_r1" if n_replaced else ""),
                "n_replaced": n_replaced,
                "portfolio_index": i,
                "meta": meta_extra,
            }
        )
    return out[:k]
