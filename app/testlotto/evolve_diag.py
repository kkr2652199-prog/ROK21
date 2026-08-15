# -*- coding: utf-8 -*-
"""K-EVOLVE-DIAG — 뇌별 캐시 채점 append.

예측 재실행 없음. apply_feedback / 숙제 / get_feedback_summary / predict_sets /
get_or_build / allow_compute 금지.
소스 = testlotto_pool_view_cache 의 해당 brain 행만. 타뇌 미접촉.
as_of = draw_no-1. peek면 INSERT 안 함.
review 는 apply_learn_boost 없음(carry만) — 기록 note/features에만 표기.
롤백: 호출 제거 + DELETE FROM testlotto_evolve_log WHERE brain_tag IN (...)
"""
from __future__ import annotations

import json
import logging
from statistics import mean
from typing import Any

from app.testlotto.evolve_log import WEIGHT_APPLIED, ensure_evolve_log_table
from app.testlotto.models import get_lotto_db, init_testlotto_db
from app.testlotto.tier_utils import score_predicted_set

logger = logging.getLogger(__name__)

BRAINS = ("stat", "markov", "review")
HAS_APPLY_LEARN_BOOST = {"stat": True, "markov": True, "review": False}
SCHEMA_VERSION = 1
METHOD_BY_BRAIN = {"stat": "과거학습", "markov": "선호번호", "review": "금액뇌"}


def _note(brain: str) -> str:
    boost = "learn_boost=on" if HAS_APPLY_LEARN_BOOST.get(brain) else "learn_boost=none(carry_only)"
    return f"K-EVOLVE-DIAG · weight=0 · brain={brain} · as_of=N-1 · {boost}"


def _role_of(s: dict[str, Any], *, kind: str) -> str:
    role = s.get("role")
    if role:
        return str(role)
    if kind == "repack":
        return "focus_r1"
    sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
    if 1 <= sn <= 5:
        return "skill_native"
    if 6 <= sn <= 8:
        return "cover_r3"
    if 9 <= sn <= 10:
        return "shape_r2"
    return "unknown"


def _score_list(
    sets: list[dict[str, Any]],
    actual: list[int],
    bonus: int,
    *,
    kind: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in sets:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        sc = score_predicted_set(nums, actual, bonus)
        sn = int(s.get("set_no") or s.get("pred_set_no") or s.get("repack_rank") or 0)
        out.append(
            {
                "set_no": sn,
                "nums": nums,
                "hits": int(sc["matched_count"]),
                "kind": kind,
                "role": _role_of(s, kind=kind),
                "tier": sc["tier_label"],
                "tier_rank": int(sc["tier_rank"]),
            }
        )
    return out


def _load_brain_cache(draw_no: int, brain: str) -> dict[str, Any] | None:
    """해당 뇌 캐시 행만. get_or_build / 3뇌 묶음 조회 금지."""
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT pool_json, repack_json
            FROM testlotto_pool_view_cache
            WHERE draw_no=? AND brain=?
            ORDER BY schema_version DESC
            LIMIT 1
            """,
            (int(draw_no), str(brain)),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    pool = json.loads(row["pool_json"] or "[]")
    repack = json.loads(row["repack_json"] or "[]")
    if not pool or not repack:
        return None
    return {"pool": pool, "repack": repack}


def _load_actual(draw_no: int) -> tuple[list[int], int] | None:
    init_testlotto_db()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT num1,num2,num3,num4,num5,num6,bonus
            FROM lotto_draws WHERE draw_no=?
            """,
            (int(draw_no),),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    nums = [int(row[f"num{k}"]) for k in range(1, 7)]
    bonus = int(row["bonus"] or 0)
    return nums, bonus


def write_evolve_diag(draw_no: int, brain: str) -> dict[str, Any]:
    """회차 N 확정 후 해당 뇌 캐시만 채점 append. 타뇌·예측로직·원장·숙제 불변."""
    tag = str(brain or "").strip().lower()
    dno = int(draw_no)
    as_of = dno - 1
    out: dict[str, Any] = {
        "ok": False,
        "draw_no": dno,
        "brain_tag": tag,
        "as_of": as_of,
        "inserted": False,
        "skipped": None,
    }
    if tag not in BRAINS:
        out["skipped"] = "bad_brain"
        return out
    if as_of >= dno:
        out["skipped"] = "hard_peek_as_of"
        logger.error("[EVOLVE-DIAG] peek as_of=%s draw_no=%s brain=%s", as_of, dno, tag)
        return out

    actual_pack = _load_actual(dno)
    if actual_pack is None:
        out["skipped"] = "no_draw"
        return out
    actual, bonus = actual_pack

    cache = _load_brain_cache(dno, tag)
    if cache is None:
        out["skipped"] = f"no_{tag}_cache"
        return out

    pool_scored = _score_list(cache["pool"], actual, bonus, kind="pool")
    repack_scored = _score_list(cache["repack"], actual, bonus, kind="repack")
    if not pool_scored or not repack_scored:
        out["skipped"] = "empty_scored"
        return out

    best_hits = max(x["hits"] for x in repack_scored)
    mean_hits = round(mean(x["hits"] for x in repack_scored), 4)
    best_row = max(repack_scored, key=lambda x: (x["hits"], -int(x["set_no"])))
    assemble_modes = {
        str(s.get("assemble") or "") for s in cache["repack"] if s.get("assemble")
    }
    assemble_mode = ",".join(sorted(m for m in assemble_modes if m)) or "unknown"

    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        conn.execute(
            """
            INSERT INTO testlotto_evolve_log (
                draw_no, brain_tag, as_of, schema_version, weight_applied,
                actual_nums_json, pool_json, repack_json,
                pool_hits_json, repack_hits_json,
                best_hits, mean_hits, best_set_kind, best_set_no,
                features_json, miss_tags_json, assemble_mode, note,
                updated_at
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                datetime('now','localtime')
            )
            ON CONFLICT(draw_no, brain_tag) DO UPDATE SET
                as_of=excluded.as_of,
                schema_version=excluded.schema_version,
                weight_applied=excluded.weight_applied,
                actual_nums_json=excluded.actual_nums_json,
                pool_json=excluded.pool_json,
                repack_json=excluded.repack_json,
                pool_hits_json=excluded.pool_hits_json,
                repack_hits_json=excluded.repack_hits_json,
                best_hits=excluded.best_hits,
                mean_hits=excluded.mean_hits,
                best_set_kind=excluded.best_set_kind,
                best_set_no=excluded.best_set_no,
                features_json=excluded.features_json,
                miss_tags_json=excluded.miss_tags_json,
                assemble_mode=excluded.assemble_mode,
                note=excluded.note,
                updated_at=datetime('now','localtime')
            """,
            (
                dno,
                tag,
                as_of,
                SCHEMA_VERSION,
                WEIGHT_APPLIED,
                json.dumps(actual, ensure_ascii=False),
                json.dumps(
                    [
                        {"set_no": p["set_no"], "nums": p["nums"], "kind": p["kind"], "role": p["role"]}
                        for p in pool_scored
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(
                    [
                        {"set_no": r["set_no"], "nums": r["nums"], "kind": r["kind"], "role": r["role"]}
                        for r in repack_scored
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(pool_scored, ensure_ascii=False),
                json.dumps(repack_scored, ensure_ascii=False),
                int(best_hits),
                float(mean_hits),
                "repack",
                int(best_row["set_no"]),
                json.dumps(
                    {
                        "weight_applied": WEIGHT_APPLIED,
                        "n_repack": len(repack_scored),
                        "n_pool": len(pool_scored),
                        "has_apply_learn_boost": bool(HAS_APPLY_LEARN_BOOST[tag]),
                    },
                    ensure_ascii=False,
                ),
                "[]",
                assemble_mode,
                _note(tag),
            ),
        )
        conn.commit()
    except Exception as e:  # noqa: BLE001
        logger.exception("[EVOLVE-DIAG] write failed draw=%s brain=%s", dno, tag)
        out["skipped"] = f"write_error:{e}"
        return out
    finally:
        conn.close()

    out.update(
        {
            "ok": True,
            "inserted": True,
            "best_hits": int(best_hits),
            "mean_hits": mean_hits,
            "n_pool": len(pool_scored),
            "n_repack": len(repack_scored),
            "has_apply_learn_boost": bool(HAS_APPLY_LEARN_BOOST[tag]),
        }
    )
    return out


def write_evolve_diag_confirmed(draw_no: int) -> dict[str, Any]:
    """회차 확정 후 뇌별 독립 write 3회. 합산 필드 없음."""
    dno = int(draw_no)
    by: dict[str, Any] = {}
    for tag in BRAINS:
        by[tag] = write_evolve_diag(dno, tag)
    return {"ok": all(v.get("ok") for v in by.values()), "draw_no": dno, "by_brain": by}


def get_evolve_diag(draw_no: int, brain: str) -> dict[str, Any] | None:
    """읽기: WHERE brain_tag=해당뇌 필수. 3뇌 합산 없음."""
    tag = str(brain or "").strip().lower()
    if tag not in BRAINS:
        return None
    ensure_evolve_log_table()
    conn = get_lotto_db()
    try:
        row = conn.execute(
            """
            SELECT * FROM testlotto_evolve_log
            WHERE draw_no=? AND brain_tag=?
            """,
            (int(draw_no), tag),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    return {
        "ok": True,
        "draw_no": int(d["draw_no"]),
        "brain_tag": d["brain_tag"],
        "as_of": int(d["as_of"]),
        "weight_applied": d["weight_applied"],
        "actual_nums": json.loads(d["actual_nums_json"] or "[]"),
        "pool": json.loads(d["pool_json"] or "[]"),
        "repack": json.loads(d["repack_json"] or "[]"),
        "pool_hits": json.loads(d["pool_hits_json"] or "[]"),
        "repack_hits": json.loads(d["repack_hits_json"] or "[]"),
        "best_hits": d["best_hits"],
        "mean_hits": d["mean_hits"],
        "assemble_mode": d["assemble_mode"],
        "note": d["note"],
        "updated_at": d["updated_at"],
        "has_apply_learn_boost": bool(HAS_APPLY_LEARN_BOOST[tag]),
    }


def record_predictions_from_cache(draw_no: int, brain: str) -> dict[str, Any]:
    """해당 뇌 캐시 repack5만 lotto_predictions에 기록. predict_sets 금지."""
    tag = str(brain or "").strip().lower()
    dno = int(draw_no)
    out: dict[str, Any] = {"ok": False, "draw_no": dno, "brain_tag": tag, "n": 0}
    if tag not in BRAINS:
        out["skipped"] = "bad_brain"
        return out
    cache = _load_brain_cache(dno, tag)
    if cache is None:
        out["skipped"] = f"no_{tag}_cache"
        return out
    actual_pack = _load_actual(dno)
    actual_set: set[int] = set()
    bonus = 0
    if actual_pack:
        actual_set = set(actual_pack[0])
        bonus = int(actual_pack[1])
    init_testlotto_db()
    conn = get_lotto_db()
    n = 0
    try:
        conn.execute(
            "DELETE FROM lotto_predictions WHERE target_draw_no=? AND brain_tag=?",
            (dno, tag),
        )
        for s in cache["repack"]:
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            matched = len(set(nums) & actual_set) if actual_set else -1
            bonus_matched = 1 if actual_set and bonus in set(nums) else 0
            conn.execute(
                """
                INSERT INTO lotto_predictions
                (target_draw_no, method, brain_tag, num1, num2, num3, num4, num5, num6,
                 confidence, reasoning, matched_count, bonus_matched)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    dno,
                    METHOD_BY_BRAIN[tag],
                    tag,
                    nums[0],
                    nums[1],
                    nums[2],
                    nums[3],
                    nums[4],
                    nums[5],
                    0.0,
                    f"evolve-diag cache repack brain={tag} as_of={dno-1}",
                    matched,
                    bonus_matched,
                ),
            )
            n += 1
        conn.commit()
    except Exception as e:  # noqa: BLE001
        logger.exception("[EVOLVE-DIAG] pred record failed draw=%s brain=%s", dno, tag)
        out["skipped"] = f"pred_write_error:{e}"
        return out
    finally:
        conn.close()
    out.update({"ok": True, "n": n})
    return out
