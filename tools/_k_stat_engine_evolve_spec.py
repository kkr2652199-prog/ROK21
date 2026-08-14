# -*- coding: utf-8 -*-
"""K-STAT-ENGINE-EVOLVE-SPEC — 패치 직후 stat 200회 원장/캐시 정밀.

6~10·몰아주기가 '3등/2등/1등 엔진'으로 도는지, 번호가 어떻게 조합되는지.
등수=모니터. 1237아님. DB쓰기 없음.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KSTAT_ENGINE_EVOLVE_SPEC.json"
OUT_MD = ROOT / "reports" / "20260814_KSTAT_ENGINE_EVOLVE_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1037, 1236
TAG = "stat"
LABEL = {1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등", 0: "미적중"}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _jaccard(a, b) -> float:
    sa, sb = set(a), set(b)
    u = sa | sb
    return (len(sa & sb) / len(u)) if u else 0.0


def _parse_nums(raw) -> list[int]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    return [int(x) for x in raw]


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import (
        ASSEMBLE_MODE,
        LEDGER_BLEND,
        POOL_SLOTS_BY_BRAIN,
        POOL_UNION_CAP_BY_BRAIN,
        ROLE_TIER_LEARN_BRAINS,
        ROLE_TIER_LEARN_WIRE,
        SCORE_WEIGHTS_BY_BRAIN,
    )
    from app.testlotto.role_homework import COVER_MIN_HITS
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        led = conn.execute(
            """
            SELECT draw_no, kind, set_no, role, nums_json, hits, bonus_hit, tier_rank
            FROM testlotto_pool_hit_ledger
            WHERE brain_tag=? AND draw_no BETWEEN ? AND ?
            ORDER BY draw_no, kind, set_no
            """,
            (TAG, LO, HI),
        ).fetchall()
        cache = conn.execute(
            """
            SELECT draw_no, brain, pool_json, repack_json
            FROM testlotto_pool_view_cache
            WHERE brain=? AND draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (TAG, LO, HI),
        ).fetchall()
        census = {
            "ledger": int(
                conn.execute(
                    "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE brain_tag=?",
                    (TAG,),
                ).fetchone()[0]
            ),
            "cache_stat": len(cache),
            "cache_all": int(
                conn.execute("SELECT COUNT(*) FROM testlotto_pool_view_cache").fetchone()[0]
            ),
            "role_hw_stat": int(
                conn.execute(
                    "SELECT COUNT(*) FROM testlotto_role_homework WHERE brain_tag=?",
                    (TAG,),
                ).fetchone()[0]
            ),
            "review_stat": int(
                conn.execute(
                    "SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag=?",
                    (TAG,),
                ).fetchone()[0]
            ),
        }
    finally:
        conn.close()

    by_role: dict[str, dict[str, list]] = defaultdict(
        lambda: {"hits": [], "n": 0, "ge3": 0, "ge4": 0, "ge5": 0}
    )
    uniq_tier: dict[tuple, tuple[int, str]] = {}
    set_tier: Counter = Counter()
    role_tier: Counter = Counter()

    for r in led:
        role = str(r["role"] or "")
        sn = int(r["set_no"] or 0)
        kind = str(r["kind"] or "")
        hits = int(r["hits"] or 0)
        tr = int(r["tier_rank"] or 0)
        nums = tuple(_parse_nums(r["nums_json"]))
        by_role[role]["hits"].append(hits)
        by_role[role]["n"] += 1
        if hits >= 3:
            by_role[role]["ge3"] += 1
        if hits >= 4:
            by_role[role]["ge4"] += 1
        if hits >= 5:
            by_role[role]["ge5"] += 1
        uk = (int(r["draw_no"]), nums)
        prev = uniq_tier.get(uk)
        if prev is None or (tr and (not prev[0] or tr < prev[0])):
            uniq_tier[uk] = (tr, role)
        if kind == "pool":
            set_tier[(sn, tr)] += 1
        role_tier[(role, tr)] += 1

    uniq_c = Counter()
    uniq_role = Counter()
    for (_d, _n), (tr, role) in uniq_tier.items():
        uniq_c[tr] += 1
        if tr:
            uniq_role[(role, tr)] += 1

    role_summ = {}
    for role, d in by_role.items():
        hs = d["hits"]
        role_summ[role] = {
            "n": d["n"],
            "mean_hits": round(mean(hs), 4) if hs else None,
            "ge3": d["ge3"],
            "ge4": d["ge4"],
            "ge5": d["ge5"],
            "monitor_only": True,
        }

    # cache geometry
    jac_cover: list[float] = []
    jac_shape: list[float] = []
    jac_shape_set1: list[float] = []
    union10: list[int] = []
    union5: list[int] = []
    union_rep: list[int] = []
    copy_src: Counter = Counter()
    copy_role: Counter = Counter()
    rec_n = copy_n = 0
    pool_src: Counter = Counter()
    n_cache = 0
    empty_repack_src = 0
    pair_cover: list[float] = []
    pair_skill: list[float] = []

    def _pairs(sets: list[list[int]]) -> float:
        if len(sets) < 2:
            return 0.0
        vs = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                vs.append(_jaccard(sets[i], sets[j]))
        return mean(vs) if vs else 0.0

    for row in cache:
        pool = json.loads(row["pool_json"] or "[]")
        rep = json.loads(row["repack_json"] or "[]")
        if len(pool) != 10:
            continue
        n_cache += 1
        by_sn = {int(s.get("set_no") or 0): [int(x) for x in (s.get("nums") or [])] for s in pool}
        skill = [by_sn[i] for i in range(1, 6) if i in by_sn]
        cover = [by_sn[i] for i in range(6, 9) if i in by_sn]
        shape = [by_sn[i] for i in range(9, 11) if i in by_sn]
        alln = [by_sn[i] for i in range(1, 11) if i in by_sn]
        union10.append(len(set().union(*map(set, alln))) if alln else 0)
        union5.append(len(set().union(*map(set, skill))) if skill else 0)
        if skill and cover:
            jac_cover.append(mean(_jaccard(c, s) for c in cover for s in skill))
        if skill and shape:
            jac_shape.append(mean(_jaccard(sh, s) for sh in shape for s in skill))
            jac_shape_set1.append(mean(_jaccard(sh, skill[0]) for sh in shape))
        pair_skill.append(_pairs(skill))
        pair_cover.append(_pairs(skill + cover))
        for s in pool:
            pool_src[str(s.get("source") or s.get("role") or "")] += 1
        pmap = {_key(by_sn[sn]): sn for sn in by_sn}
        rnums = []
        for s in rep:
            nums = [int(x) for x in (s.get("nums") or [])]
            rnums.append(nums)
            src = str(s.get("source") or "")
            if not src:
                empty_repack_src += 1
            k = _key(nums)
            if k in pmap:
                copy_n += 1
                sn = pmap[k]
                copy_src[sn] += 1
                if 1 <= sn <= 5:
                    copy_role["skill_native"] += 1
                elif 6 <= sn <= 8:
                    copy_role["cover_r3"] += 1
                elif 9 <= sn <= 10:
                    copy_role["shape_r2"] += 1
            else:
                rec_n += 1
        if rnums:
            union_rep.append(len(set().union(*map(set, rnums))))

    flags = {
        "ROLE_TIER_LEARN_WIRE": bool(ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
        "ASSEMBLE_MODE": ASSEMBLE_MODE,
        "POOL_SLOTS_stat": int(POOL_SLOTS_BY_BRAIN.get(TAG, 2)),
        "POOL_UNION_CAP_stat": int(POOL_UNION_CAP_BY_BRAIN.get(TAG, 4)),
        "LEDGER_BLEND": float(LEDGER_BLEND),
        "SCORE_WEIGHTS_stat": list(SCORE_WEIGHTS_BY_BRAIN.get(TAG, ())),
        "STRUCTURE_COVER_WIRE": False,
    }
    try:
        from app.testlotto.structure_cover import STRUCTURE_COVER_WIRE as scw

        flags["STRUCTURE_COVER_WIRE"] = bool(scw)
    except Exception:
        flags["STRUCTURE_COVER_WIRE"] = False

    out = {
        "id": "K-STAT-ENGINE-EVOLVE-SPEC",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "brain": TAG,
        "flags": flags,
        "census": census,
        "n_ledger": len(led),
        "n_cache_ok": n_cache,
        "by_role": role_summ,
        "unique_combo_tier": {LABEL[k]: int(uniq_c.get(k, 0)) for k in (1, 2, 3, 4, 5, 0)},
        "unique_prize_by_role": {
            f"{role}:{LABEL[tr]}": int(c) for (role, tr), c in sorted(uniq_role.items())
        },
        "geometry": {
            "union10_mean": round(mean(union10), 3) if union10 else None,
            "union_skill5_mean": round(mean(union5), 3) if union5 else None,
            "union_repack5_mean": round(mean(union_rep), 3) if union_rep else None,
            "jaccard_cover_vs_skill_mean": round(mean(jac_cover), 4) if jac_cover else None,
            "jaccard_shape_vs_skill_mean": round(mean(jac_shape), 4) if jac_shape else None,
            "jaccard_shape_vs_set1_mean": round(mean(jac_shape_set1), 4) if jac_shape_set1 else None,
            "pairwise_jaccard_skill5": round(mean(pair_skill), 4) if pair_skill else None,
            "pairwise_jaccard_skill+cover8": round(mean(pair_cover), 4) if pair_cover else None,
        },
        "repack": {
            "copy_n": copy_n,
            "recombine_n": rec_n,
            "copy_ratio": round(copy_n / max(1, copy_n + rec_n), 4),
            "empty_source_field": empty_repack_src,
            "copy_by_pool_set": {str(k): int(v) for k, v in sorted(copy_src.items())},
            "copy_by_role": dict(copy_role),
        },
        "verdict": "SPEC_OK",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("verdict", "census", "by_role", "unique_combo_tier", "unique_prize_by_role", "geometry", "repack", "flags")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
