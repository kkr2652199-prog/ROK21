# -*- coding: utf-8 -*-
"""K-TICKET-POOL-UNIFY-WIRE — LIST_V3 L12b 옵션 E 검증.

생성 1회(pool) · quota5 발권 · 같은 회차 pool 캐시 동기.
병합 아님 · pool10/repack15 발권 아님 · BT 경로 미수정 · 1237아님.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260813_KTICKET_POOL_UNIFY_WIRE.json"
OUT_MD = ROOT / "reports" / "20260813_KTICKET_POOL_UNIFY_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SAMPLE = 1236
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: list) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    from app.testlotto.brains.coordinator import (
        BRAIN_RNG_SEED_BASE,
        PREDICT_MODULES,
        _seed_independent_brain,
        run_coordinated_prediction,
    )
    from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import get_cached_pool_view
    from app.testlotto.ticket_pool_sync import (
        OPTION_ID,
        TICKET_POOL_SYNC,
        run_live_issue_with_pool_sync,
        skill_candidates_from_raw,
    )
    import app.testlotto.signal_pool as sp

    init_testlotto_db()
    set_learn_as_of(SAMPLE)
    draws = _get_draws_before(SAMPLE)
    checks: dict[str, Any] = {}

    routes_src = _src("app/testlotto/routes.py")
    engine_src = _src("app/testlotto/engine.py")
    coord_src = _src("app/testlotto/brains/coordinator.py")
    checks["ticket_pool_sync_on"] = TICKET_POOL_SYNC is True
    checks["api_predict_wired"] = "run_live_issue_with_pool_sync" in routes_src
    checks["engine_bt_unwired"] = "ticket_pool_sync" not in engine_src
    checks["prebuilt_param"] = "prebuilt_candidates" in coord_src
    checks["option_e"] = OPTION_ID == "E_same_gen_dual_write"

    # C8: expand_pool skill1~5 == predict_sets(5) (warm 없이)
    pool = sp.expand_pool(draws, SAMPLE, seed=SEED)
    pool_br = sp._pool_by_brain(pool)
    skill = skill_candidates_from_raw(pool_br)
    checks["skill_n"] = len(skill)
    checks["skill_is_15"] = len(skill) == 15
    c8: dict[str, bool] = {}
    for tag in sp.BRAIN_TAGS:
        _seed_independent_brain(SAMPLE)
        issued = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        issue_keys = [_key(c["nums"]) for c in issued]
        pool5 = [
            _key(c["nums"])
            for c in sorted(pool_br.get(tag) or [], key=lambda x: int(x.get("set_no") or 0))
            if int(c.get("set_no") or 0) <= 5
        ]
        c8[tag] = issue_keys == pool5
    checks["c8_pool1to5_eq_predict5"] = c8
    checks["c8_all"] = all(c8.values())
    checks["pass0_eq_coord_seed"] = sp._pass_seed(SEED, SAMPLE, 0) == (
        BRAIN_RNG_SEED_BASE + SAMPLE
    )

    conn = get_lotto_db()
    try:
        bak_pred = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM lotto_predictions WHERE target_draw_no=?",
                (SAMPLE,),
            ).fetchall()
        ]
        bak_cache = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM testlotto_pool_view_cache WHERE draw_no=?",
                (SAMPLE,),
            ).fetchall()
        ]
        conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no=?", (SAMPLE,))
        conn.execute(
            "DELETE FROM testlotto_pool_view_cache WHERE draw_no=?", (SAMPLE,)
        )
        conn.commit()
    finally:
        conn.close()

    live = run_live_issue_with_pool_sync(SAMPLE)
    ps = live.get("pool_sync") or {}
    checks["live_no_error"] = "error" not in live or live.get("error") in (None, "")
    checks["pool_sync_ok"] = bool(ps.get("ok"))
    checks["wrote_cache"] = bool(ps.get("wrote_cache"))
    checks["live_skill_n"] = int(ps.get("skill_n") or 0)
    checks["live_skill_is_15"] = checks["live_skill_n"] == 15

    conn = get_lotto_db()
    try:
        n_pred = conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=?",
            (SAMPLE,),
        ).fetchone()[0]
        by_tag = dict(
            conn.execute(
                "SELECT brain_tag, COUNT(*) FROM lotto_predictions "
                "WHERE target_draw_no=? GROUP BY brain_tag",
                (SAMPLE,),
            ).fetchall()
        )
        n_cache = conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_view_cache WHERE draw_no=?",
            (SAMPLE,),
        ).fetchone()[0]
    finally:
        conn.close()

    cached = get_cached_pool_view(SAMPLE)
    n_pool = {
        t: len((cached or {}).get("pool_by_brain", {}).get(t) or [])
        for t in sp.BRAIN_TAGS
    }
    n_repack = {
        t: len((cached or {}).get("repack_by_brain", {}).get(t) or [])
        for t in sp.BRAIN_TAGS
    }
    checks["issued_n"] = int(n_pred)
    checks["issued_by_tag"] = by_tag
    checks["issued_is_5"] = int(n_pred) == 5
    checks["issued_ne_pool10"] = int(n_pred) != 30
    checks["issued_ne_repack15"] = int(n_pred) != 15
    checks["issued_ne_all45"] = int(n_pred) != 45
    checks["cache_rows_3"] = int(n_cache) == 3
    checks["pool_sizes"] = n_pool
    checks["repack_sizes"] = n_repack
    checks["pool10"] = all(v == 10 for v in n_pool.values())
    checks["repack5"] = all(v == 5 for v in n_repack.values())
    checks["min_each_brain"] = set(by_tag) == {"stat", "markov", "review"} and all(
        v >= 1 for v in by_tag.values()
    )

    # restore
    conn = get_lotto_db()
    try:
        conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no=?", (SAMPLE,))
        conn.execute(
            "DELETE FROM testlotto_pool_view_cache WHERE draw_no=?", (SAMPLE,)
        )
        if bak_pred:
            cols = list(bak_pred[0].keys())
            ph = ",".join("?" * len(cols))
            cn = ",".join(cols)
            for row in bak_pred:
                conn.execute(
                    f"INSERT INTO lotto_predictions ({cn}) VALUES ({ph})",
                    [row[c] for c in cols],
                )
        if bak_cache:
            cols = list(bak_cache[0].keys())
            ph = ",".join("?" * len(cols))
            cn = ",".join(cols)
            for row in bak_cache:
                conn.execute(
                    f"INSERT INTO testlotto_pool_view_cache ({cn}) VALUES ({ph})",
                    [row[c] for c in cols],
                )
        conn.commit()
    finally:
        conn.close()
    checks["restored"] = True

    hard = [
        "ticket_pool_sync_on",
        "api_predict_wired",
        "engine_bt_unwired",
        "prebuilt_param",
        "skill_is_15",
        "c8_all",
        "pass0_eq_coord_seed",
        "live_no_error",
        "pool_sync_ok",
        "wrote_cache",
        "live_skill_is_15",
        "issued_is_5",
        "issued_ne_pool10",
        "issued_ne_repack15",
        "issued_ne_all45",
        "cache_rows_3",
        "pool10",
        "repack5",
        "min_each_brain",
        "restored",
    ]
    hard_ok = all(bool(checks.get(k)) for k in hard)
    verdict = "WIRE_OK" if hard_ok else "FAIL"

    payload = {
        "id": "K-TICKET-POOL-UNIFY-WIRE",
        "list": "LIST_V3 L12b",
        "status": verdict,
        "ts": _now(),
        "wire": True,
        "apply": True,
        "option": "E",
        "force_merge": False,
        "ge3_used_as_claim": False,
        "sample_draw": SAMPLE,
        "checks": checks,
        "hard_keys": hard,
        "note": "옵션E · quota5유지 · pool캐시동기 · BT경로불변 · 1237아님",
        "force_bt": False,
        "s1": False,
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# K-TICKET-POOL-UNIFY-WIRE — LIST_V3 L12b 옵션 E",
        "",
        f"시각: {payload['ts']} · **{verdict}** · wire=**True** · apply=**True** · 옵션=**E**",
        f"샘플: {SAMPLE} · seed={SEED} · **1237아님** · ge3미클레임 · 강제병합 안 함",
        "",
        "## 이번 턴 작업",
        "",
        "형 권고 **E**: 클릭 시 pool을 **한 번** 생성하고, skill1~5만 quota **5장** 발권하며,",
        "같은 회차 `testlotto_pool_view_cache`에 10+5를 같이 기록한다.",
        "pool10/repack15를 발권 테이블에 넣지 않는다. BT/`run_prediction`은 기존 경로.",
        "",
        "## HARD",
        "",
    ]
    for k in hard:
        lines.append(f"- `{k}`: **{checks.get(k)}**")
    lines += [
        "",
        f"- issued: n={checks['issued_n']} by_tag={checks['issued_by_tag']}",
        f"- pool sizes: {n_pool} · repack: {n_repack}",
        f"- C8: {c8}",
        f"- pool_sync: {ps}",
        "",
        "## 배선",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        "| 플래그 | `TICKET_POOL_SYNC=True` (`ticket_pool_sync.py`) |",
        "| 클릭 | `POST /predict/{N}` → `run_live_issue_with_pool_sync` |",
        "| 생성 | `build_pool_and_repack(..., return_raw=True)` 1회 |",
        "| 발권 | skill1~5 → `prebuilt_candidates` → quota5 → `lotto_predictions` |",
        "| 캐시 | 같은 회차 `save_pool_view_cache` |",
        "| BT | `engine.run_prediction` → coordinator (동기 없음) |",
        "| 롤백 | `TICKET_POOL_SYNC=False` (옵션 A 분리) |",
        "",
        "벤치: `docs/benchmarks/20260813_KTICKET_POOL_UNIFY_WIRE.json`",
        "도구: `tools/_k_ticket_pool_unify_wire.py`",
        "",
        "다음: LIST_V3 L0~L12b 완료 · 형 다음 1건",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "issued": checks.get("issued_by_tag"),
                "c8": c8,
                "pool_sync": ps,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
