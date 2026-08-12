# -*- coding: utf-8 -*-
"""K-TIER-ROLE-SLOTS — LIST_V3 L4b 역할 슬롯 생성.

pool10 = skill_native×5 + cover_r3×3 + shape_r2×2
repack5 = focus_r1 라벨
shape_r2: bonus/actual 인자 금지 (no_bonus_peek).
"""
from __future__ import annotations

import inspect
import random
from typing import Any, Callable

ROLE_SKILL = "skill_native"
ROLE_COVER = "cover_r3"
ROLE_SHAPE = "shape_r2"
ROLE_FOCUS = "focus_r1"

ROLE_BY_POOL_SET: dict[int, tuple[str, str]] = {
    1: (ROLE_SKILL, "pass0"),
    2: (ROLE_SKILL, "pass0"),
    3: (ROLE_SKILL, "pass0"),
    4: (ROLE_SKILL, "pass0"),
    5: (ROLE_SKILL, "pass0"),
    6: (ROLE_COVER, "pass1a"),
    7: (ROLE_COVER, "pass1a"),
    8: (ROLE_COVER, "pass1a"),
    9: (ROLE_SHAPE, "pass1b"),
    10: (ROLE_SHAPE, "pass1b"),
}


def _nums_key(nums: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _jaccard(a: list[int], b: list[int]) -> float:
    sa, sb = set(a), set(b)
    u = sa | sb
    if not u:
        return 0.0
    return len(sa & sb) / len(u)


def label_skill_sets(
    sets: list[dict[str, Any]], *, brain_tag: str
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, c in enumerate(sets):
        sn = i + 1
        role, rpass = ROLE_BY_POOL_SET[sn]
        row = {
            **c,
            "brain_tag": brain_tag,
            "pred_set_no": sn,
            "set_no": sn,
            "kind": "pool",
            "role": role,
            "role_pass": rpass,
            "nums": [int(x) for x in c["nums"]],
        }
        out.append(row)
    return out


def build_cover_r3_sets(
    predict_sets_fn: Callable[..., list[dict]],
    draws: list[dict],
    *,
    brain_tag: str,
    skill_sets: list[dict[str, Any]],
    seed: int,
    draw_no: int,
    n: int = 3,
) -> list[dict[str, Any]]:
    """pass1a: 시드 오프셋 predict 후보에서 skill 대비 Jaccard 낮은 3장.

    SPEC 후보 (A). 타깃 정답·bonus 미사용.
    """
    from app.testlotto.signal_pool import _pass_seed

    random.seed(_pass_seed(seed, draw_no, 1))
    try:
        cands = predict_sets_fn(draws, 5)
    except Exception:  # noqa: BLE001
        cands = []

    skill_keys = {_nums_key(s["nums"]) for s in skill_sets}
    skill_nums = [list(s["nums"]) for s in skill_sets]

    def cover_key(c: dict) -> tuple:
        nums = [int(x) for x in c.get("nums") or []]
        if len(nums) != 6:
            return (9.0, _nums_key(nums))
        jac = (
            min(_jaccard(nums, sk) for sk in skill_nums) if skill_nums else 0.0
        )
        return (jac, _nums_key(nums))

    ranked = sorted(cands, key=cover_key)
    picked: list[dict[str, Any]] = []
    picked_keys: set[tuple[int, ...]] = set()
    for c in ranked:
        nums = [int(x) for x in c.get("nums") or []]
        if len(nums) != 6:
            continue
        key = _nums_key(nums)
        if key in skill_keys or key in picked_keys:
            continue
        # 이미 고른 cover와도 너무 겹치면 스킵
        if picked and min(_jaccard(nums, p["nums"]) for p in picked) > 0.85:
            continue
        sn = 6 + len(picked)
        picked.append(
            {
                **c,
                "nums": sorted(nums),
                "brain_tag": brain_tag,
                "pred_set_no": sn,
                "set_no": sn,
                "kind": "pool",
                "role": ROLE_COVER,
                "role_pass": "pass1a",
            }
        )
        picked_keys.add(key)
        if len(picked) >= n:
            break

    # 부족 시: skill 변형(번호 1개 교체)으로 채움 — bonus 미사용
    rng = random.Random(_pass_seed(seed, draw_no, 1) + 777)
    while len(picked) < n and skill_sets:
        base = [int(x) for x in skill_sets[len(picked) % len(skill_sets)]["nums"]]
        if len(base) != 6:
            break
        drop = rng.randrange(6)
        core = [base[j] for j in range(6) if j != drop]
        cands_n = [x for x in range(1, 46) if x not in set(base)]
        rng.shuffle(cands_n)
        nums = sorted(core + [cands_n[0]])
        key = _nums_key(nums)
        if key in skill_keys or key in picked_keys:
            if len(cands_n) > 1:
                nums = sorted(core + [cands_n[1]])
                key = _nums_key(nums)
            if key in skill_keys or key in picked_keys:
                break
        sn = 6 + len(picked)
        picked.append(
            {
                "nums": nums,
                "brain_tag": brain_tag,
                "pred_set_no": sn,
                "set_no": sn,
                "kind": "pool",
                "role": ROLE_COVER,
                "role_pass": "pass1a",
                "source": "cover_fill_morph",
            }
        )
        picked_keys.add(key)
    return picked


def build_shape_r2_sets(
    skill_sets: list[dict[str, Any]],
    *,
    brain_tag: str,
    seed: int,
    draw_no: int,
    n: int = 2,
) -> list[dict[str, Any]]:
    """pass1b: 핵심5 + 6번째 가변. bonus/actual 파라미터 없음 (T-NB1)."""
    from app.testlotto.signal_pool import _pass_seed

    if not skill_sets:
        return []
    base = [int(x) for x in skill_sets[0]["nums"]]
    if len(base) != 6:
        return []
    rng = random.Random(_pass_seed(seed, draw_no, 2) + 90001)
    out: list[dict[str, Any]] = []
    for i in range(n):
        drop_idx = i % 6
        core5 = [base[j] for j in range(6) if j != drop_idx]
        used = set(base)
        cands = [x for x in range(1, 46) if x not in used]
        rng.shuffle(cands)
        # i번째 shape는 서로 다른 6번째
        sixth = cands[min(i, len(cands) - 1)]
        nums = sorted(core5 + [sixth])
        sn = 9 + i
        out.append(
            {
                "nums": nums,
                "brain_tag": brain_tag,
                "pred_set_no": sn,
                "set_no": sn,
                "kind": "pool",
                "role": ROLE_SHAPE,
                "role_pass": "pass1b",
                "source": "shape_core5_vary6",
            }
        )
    return out


def label_repack_focus(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """repack 결과에 role=focus_r1 부착."""
    out: list[dict[str, Any]] = []
    for c in rows:
        row = dict(c)
        row["role"] = ROLE_FOCUS
        row["role_pass"] = "repack"
        out.append(row)
    return out


def assert_shape_no_bonus_in_signature() -> dict[str, Any]:
    """T-NB1: shape 생성 시그니처에 bonus/actual 없음."""
    sig = inspect.signature(build_shape_r2_sets)
    names = set(sig.parameters)
    bad = sorted(names & {"bonus", "actual", "actual_nums", "bonus_num"})
    return {"ok": len(bad) == 0, "params": sorted(names), "bad": bad}


def role_counts_for_brain(pool_rows: list[dict[str, Any]]) -> dict[str, int]:
    cnt: dict[str, int] = {}
    for r in pool_rows:
        role = str(r.get("role") or "")
        cnt[role] = cnt.get(role, 0) + 1
    return cnt


def validate_pool_roles(pool_by_brain: dict[str, list[dict]]) -> dict[str, Any]:
    """set_no↔role 표 일치 · 뇌별 5+3+2."""
    issues: list[str] = []
    for tag, rows in pool_by_brain.items():
        by_sn = {int(r.get("set_no") or 0): r for r in rows}
        if len(rows) != 10:
            issues.append(f"{tag}:n={len(rows)}!=10")
        for sn, (role, rpass) in ROLE_BY_POOL_SET.items():
            r = by_sn.get(sn)
            if not r:
                issues.append(f"{tag}:missing set_no={sn}")
                continue
            if str(r.get("role")) != role:
                issues.append(f"{tag}:set{sn} role={r.get('role')}!={role}")
            if str(r.get("role_pass")) != rpass:
                issues.append(f"{tag}:set{sn} pass={r.get('role_pass')}!={rpass}")
    return {"ok": len(issues) == 0, "issues": issues[:20]}
