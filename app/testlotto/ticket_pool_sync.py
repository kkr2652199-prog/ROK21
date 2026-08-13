"""L12b K-TICKET-POOL-UNIFY-WIRE — 옵션 E (생성 1회 + quota5 발권 + pool 캐시 동기).

클릭(POST /predict)만. BT·run_prediction·run_coordinated_prediction 기본경로는 불변.
발권 장수는 quota 5 유지 (pool10/repack15 발권 아님 · 병합 아님).
롤백: TICKET_POOL_SYNC=False → 분리유지(옵션 A).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# L12b E. False = 클릭 시 캐시 동기 안 함 (L12 옵션 A).
TICKET_POOL_SYNC: bool = True
OPTION_ID = "E_same_gen_dual_write"

SKILL_SET_MAX = 5
BRAIN_TAGS = ("stat", "markov", "review")


def skill_candidates_from_raw(pool_br: dict[str, list[dict]]) -> list[dict]:
    """pool 원본에서 skill_native(set 1~5)만. cover/shape는 발권에 넣지 않는다."""
    out: list[dict] = []
    for tag in BRAIN_TAGS:
        rows = pool_br.get(tag) or []
        for c in rows:
            sn = int(c.get("set_no") or c.get("pred_set_no") or 0)
            role = str(c.get("role") or "")
            if sn < 1 or sn > SKILL_SET_MAX:
                continue
            if role and role != "skill_native":
                continue
            out.append({**c, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})
    return out


def _cache_payload(built: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in built.items() if k not in ("raw_pool_by_brain", "raw_repack")}


def _pred_count(target_draw_no: int) -> int:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    try:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=?",
                (int(target_draw_no),),
            ).fetchone()[0]
        )
    finally:
        conn.close()


def run_live_issue_with_pool_sync(target_draw_no: int) -> dict[str, Any]:
    """클릭 발권: pool 생성 1회 → quota5 → 같은 회차 pool_view_cache.

    이미 발권·캐시가 있으면 재생성하지 않는다.
    발권만 있으면 캐시만 채운다 (장수 변경 없음).
    """
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.pool_view_cache import get_cached_pool_view, save_pool_view_cache
    from app.testlotto.signal_pool import build_pool_and_repack

    dno = int(target_draw_no)
    if not TICKET_POOL_SYNC:
        return run_coordinated_prediction(dno)

    cache_hit = get_cached_pool_view(dno) is not None
    n_pred = _pred_count(dno)

    if n_pred > 0 and cache_hit:
        out = dict(run_coordinated_prediction(dno))
        out["pool_sync"] = {
            "ok": True,
            "option": OPTION_ID,
            "skipped": "both_warm",
        }
        return out

    if n_pred > 0 and not cache_hit:
        built = build_pool_and_repack(dno, return_raw=True)
        wrote = False
        if built.get("ok"):
            save_pool_view_cache(dno, _cache_payload(built))
            wrote = True
        out = dict(run_coordinated_prediction(dno))
        out["pool_sync"] = {
            "ok": wrote,
            "option": OPTION_ID,
            "wrote_cache": wrote,
            "issued_unchanged": True,
            "error": None if wrote else built.get("error"),
        }
        return out

    built = build_pool_and_repack(dno, return_raw=True)
    if not built.get("ok"):
        out = dict(run_coordinated_prediction(dno))
        out["pool_sync"] = {
            "ok": False,
            "option": OPTION_ID,
            "fallback": "coordinator_generate",
            "error": built.get("error"),
        }
        return out

    skill = skill_candidates_from_raw(built.get("raw_pool_by_brain") or {})
    out = dict(
        run_coordinated_prediction(dno, prebuilt_candidates=skill)
    )
    wrote = False
    if not out.get("error"):
        save_pool_view_cache(dno, _cache_payload(built))
        wrote = True
    out["pool_sync"] = {
        "ok": wrote and not out.get("error"),
        "option": OPTION_ID,
        "wrote_cache": wrote,
        "skill_n": len(skill),
        "issued_is_quota": True,
    }
    return out
