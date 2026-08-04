# -*- coding: utf-8 -*-
"""Feature-bucket λ 재선정 — K-EVOLVE-SIGNAL Part B.

as_of 절단: draw < before_draw 로그만 사용 (컨닝 금지).
WIRE: review λ=0.3 only · stat/markov HOLD.
"""
from __future__ import annotations

import json
from collections import defaultdict
from statistics import mean
from typing import Any

from app.testlotto.evolve_log import set_features

# K-EVOLVE-FEAT-LAM-REVAL 20260804: full 53~1234에서 review λ0.3 Δ−0.0025
# (SIGNAL n200 +0.01은 희소히스토리 과적합) → wire HOLD
FEATURE_LAMBDA_BY_BRAIN: dict[str, float] = {}
MARKOV_LAMBDA_SCALE = 0.5  # survey 표기용 · wire 대상 아님
# 참고(HOLD): 직전 live 후보였던 값
_HOLD_CANDIDATE_LAMBDA: dict[str, float] = {"review": 0.3}


def feat_key(features: dict | None) -> tuple:
    if not features:
        return ("empty",)
    return (
        int(features.get("odd", -1)),
        int(features.get("zone_low", -1)),
        int(features.get("zone_mid", -1)),
        int(features.get("zone_high", -1)),
        int(features.get("max_run", -1)),
        int(round(float(features.get("sum", 0)) / 20.0)),
    )


def select_top5(
    candidates: list[dict],
    bucket_stats: dict[tuple, dict[str, float]],
    lam: float,
    global_mean: float,
) -> list[dict]:
    scored: list[tuple[float, tuple[int, ...], dict]] = []
    for s in candidates:
        nums = tuple(sorted(int(x) for x in s.get("nums") or []))
        if len(nums) != 6:
            continue
        feats = s.get("features") or set_features(list(nums))
        fk = feat_key(feats)
        hist = bucket_stats.get(fk, {}).get("mean_hits", global_mean)
        base = 1.0 / (1.0 + int(s.get("set_no") or 1))
        score = (1.0 - lam) * base + lam * float(hist)
        scored.append((score, nums, s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for _sc, nums, s in scored:
        if nums in seen:
            continue
        seen.add(nums)
        out.append(s)
        if len(out) >= 5:
            break
    return out


def load_bucket_stats_from_evolve(
    tag: str, before_draw: int
) -> tuple[dict[tuple, dict[str, float]], float]:
    """evolve_log (draw < before_draw) → bucket mean_hits + global mean."""
    from app.testlotto.evolve_log import ensure_evolve_log_table
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            """
            SELECT pool_json, repack_json, repack_hits_json, actual_nums_json
            FROM testlotto_evolve_log
            WHERE brain_tag = ? AND draw_no < ?
            ORDER BY draw_no
            """,
            (tag, before_draw),
        ).fetchall()
    finally:
        conn.close()

    buckets: dict[tuple, list[int]] = defaultdict(list)
    all_hits: list[int] = []
    for r in rows:
        d = dict(r)
        actual = set(json.loads(d["actual_nums_json"] or "[]"))
        rh = {int(x["set_no"]): x for x in json.loads(d["repack_hits_json"] or "[]")}
        for s in json.loads(d["repack_json"] or "[]"):
            sn = int(s.get("set_no") or 0)
            if sn in rh:
                hits = int(rh[sn].get("hits") or 0)
                feats = rh[sn].get("features") or {}
            else:
                nums = [int(x) for x in s.get("nums") or []]
                hits = len(set(nums) & actual)
                feats = set_features(nums) if len(nums) == 6 else {}
            all_hits.append(hits)
            buckets[feat_key(feats)].append(hits)
        for s in json.loads(d["pool_json"] or "[]"):
            nums = [int(x) for x in s.get("nums") or []]
            hits = len(set(nums) & actual)
            feats = set_features(nums) if len(nums) == 6 else {}
            all_hits.append(hits)
            buckets[feat_key(feats)].append(hits)

    stats = {k: {"n": len(xs), "mean_hits": mean(xs)} for k, xs in buckets.items()}
    gmean = mean(all_hits) if all_hits else 0.8
    return stats, float(gmean)


def candidates_from_pool_repack(
    pool: list[dict], repack: list[dict]
) -> list[dict]:
    """pool+repack → λ 후보 (features 부착)."""
    out: list[dict] = []
    for s in list(pool) + list(repack):
        nums = [int(x) for x in s.get("nums") or []]
        if len(nums) != 6:
            continue
        item = dict(s)
        item["nums"] = nums
        item["set_no"] = int(s.get("set_no") or s.get("pred_set_no") or 1)
        if not item.get("features"):
            item["features"] = set_features(nums)
        out.append(item)
    return out


def apply_feature_lambda(
    tag: str,
    pool: list[dict],
    assembled_repack: list[dict],
    before_draw: int,
) -> list[dict] | None:
    """brain별 λ wire. 대상 아니면 None → 호출측이 assembled 유지."""
    if tag not in FEATURE_LAMBDA_BY_BRAIN:
        return None
    lam = float(FEATURE_LAMBDA_BY_BRAIN[tag])
    if lam <= 0:
        return None
    buckets, gmean = load_bucket_stats_from_evolve(tag, before_draw)
    cands = candidates_from_pool_repack(pool, assembled_repack)
    if not cands:
        return None
    picked = select_top5(cands, buckets, lam, gmean)
    if len(picked) < 1:
        return None
    mode = f"feat_lam_{lam:g}"
    out: list[dict[str, Any]] = []
    for i, s in enumerate(picked):
        nums = sorted(int(x) for x in s["nums"])
        entry: dict[str, Any] = {
            "nums": nums,
            "brain_tag": tag,
            "pred_set_no": i + 1,
            "set_no": i + 1,
            "repack_rank": i + 1,
            "kind": "repack",
            "assemble": mode,
        }
        if s.get("source"):
            entry["source"] = s["source"]
            entry["source_set_no"] = s.get("source_set_no")
        elif s.get("kind") == "pool":
            entry["source"] = "pool"
            entry["source_set_no"] = int(s.get("set_no") or 0)
        out.append(entry)
    return out
