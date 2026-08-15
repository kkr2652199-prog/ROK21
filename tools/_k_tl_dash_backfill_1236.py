# -*- coding: utf-8 -*-
"""K-TL-DASH-BACKFILL-1236 — 테스트로또 예측 초기화 후 1–1236 3뇌 백필."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.data_service import _get_draws_before
from app.testlotto.evolve_diag import record_predictions_from_cache, write_evolve_diag

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KTL_DASH_BACKFILL_1236.json"
OUT_MD = ROOT / "reports" / "20260815_KTL_DASH_BACKFILL_1236.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PROGRESS = ROOT / "docs" / "benchmarks" / "_k_tl_dash_backfill_progress.json"
DB = ROOT / "data" / "lotto_testlotto.db"
BAK_DIR = ROOT / "backups" / "20260815_TLDASH전_DB전체"
LO, HI = 1, 1236
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _connect(rw: bool = False) -> sqlite3.Connection:
    if rw:
        conn = sqlite3.connect(str(DB), timeout=180.0)
    else:
        conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _write_progress(payload: dict[str, Any]) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    tmp = dict(payload)
    tmp["as_of"] = _now()
    PROGRESS.write_text(json.dumps(tmp, ensure_ascii=False, indent=2), encoding="utf-8")


def _census() -> dict[str, Any]:
    conn = _connect(False)
    pred_by = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM lotto_predictions "
            "WHERE brain_tag IN ('stat','markov','review') GROUP BY brain_tag"
        )
    }
    pred_range = conn.execute(
        "SELECT MIN(target_draw_no), MAX(target_draw_no), COUNT(*) "
        "FROM lotto_predictions WHERE brain_tag IN ('stat','markov','review')"
    ).fetchone()
    cache = conn.execute(
        "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM testlotto_pool_view_cache"
    ).fetchone()
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0] or 0)
    ledger = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    conn.close()
    return {
        "pred_by": pred_by,
        "pred_n": int(pred_range[2] or 0),
        "pred_min": int(pred_range[0] or 0),
        "pred_max": int(pred_range[1] or 0),
        "cache_min": int(cache[0] or 0),
        "cache_max": int(cache[1] or 0),
        "cache_n": int(cache[2] or 0),
        "pred_1237": pred_1237,
        "draws_max": dmax,
        "ledger_by": ledger,
    }


def _backup() -> None:
    BAK_DIR.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(DB))
    dst = sqlite3.connect(str(BAK_DIR / "lotto_testlotto.db"))
    src.backup(dst)
    dst.close()
    src.close()
    (BAK_DIR / "census.json").write_text(
        json.dumps(_census(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _reset() -> dict[str, int]:
    conn = _connect(True)
    n_pred = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE brain_tag IN ('stat','markov','review')"
        ).fetchone()[0]
    )
    n_cache = int(conn.execute("SELECT COUNT(*) FROM testlotto_pool_view_cache").fetchone()[0])
    n_ev = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        ).fetchone()[0]
    )
    conn.execute("DELETE FROM lotto_predictions WHERE brain_tag IN ('stat','markov','review')")
    conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no=1237")
    conn.execute("DELETE FROM testlotto_pool_view_cache")
    conn.execute("DELETE FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?", (LO, HI))
    conn.commit()
    conn.close()
    return {"pred": n_pred, "cache": n_cache, "evolve": n_ev}


def _fill_one(dno: int, tag: str) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import payload_from_wf_parts, save_pool_view_cache_one

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    max_mat = max((int(d["draw_no"]) for d in draws), default=0)
    if max_mat >= dno:
        return {"ok": False, "error": "peek"}
    random.seed(sp.MC_SEED)
    pool = sp.expand_pool(draws, dno, seed=sp.MC_SEED, brains=[tag])
    pool_br = sp._pool_by_brain(pool)
    learner = sp.RollingSignalLearner()
    num_ema, pos_ema = learner.snapshot()
    repacked = sp.repack_by_brain(
        pool_br,
        sp._build_hint(draws, dno),
        num_ema,
        pos_ema,
        target_draw_no=dno,
        hint_by_brain=sp.build_hint_by_brain(draws, dno),
    )
    only = [x for x in repacked if str(x.get("brain_tag")) == tag]
    payload = payload_from_wf_parts(dno, {tag: pool_br.get(tag) or []}, only, seed=sp.MC_SEED)
    if not payload["pool_by_brain"].get(tag) or not payload["repack_by_brain"].get(tag):
        return {"ok": False, "error": "empty_build"}
    save_pool_view_cache_one(dno, tag, payload)
    ev = write_evolve_diag(dno, tag)
    pr = record_predictions_from_cache(dno, tag)
    return {
        "ok": bool(pr.get("ok")),
        "pred_n": int(pr.get("n") or 0),
        "evolve_ok": bool(ev.get("ok")),
        "error": ev.get("skipped") or pr.get("skipped"),
    }


def main() -> int:
    print("[TLDASH] backup", flush=True)
    _write_progress({"status": "backup", "start": LO, "end": HI, "ok": 0, "fail": 0})
    _backup()
    before = _census()
    print("[TLDASH] reset", before, flush=True)
    deleted = _reset()
    mid = _census()
    print("[TLDASH] after reset", mid, deleted, flush=True)
    _write_progress(
        {
            "status": "running",
            "start": LO,
            "end": HI,
            "draw_no": 0,
            "ok": 0,
            "fail": 0,
            "deleted": deleted,
        }
    )

    fill = {t: {"ok": 0, "fail": 0} for t in BRAINS}
    peek_fill = 0
    ok_n = 0
    fail_n = 0
    for dno in range(LO, HI + 1):
        for tag in BRAINS:
            try:
                r = _fill_one(dno, tag)
            except Exception as e:  # noqa: BLE001
                r = {"ok": False, "error": f"exc:{type(e).__name__}:{e}"}
                traceback.print_exc()
            if r.get("error") == "peek":
                peek_fill += 1
                fill[tag]["fail"] += 1
                fail_n += 1
            elif r.get("ok"):
                fill[tag]["ok"] += 1
                ok_n += 1
            else:
                fill[tag]["fail"] += 1
                fail_n += 1
        if dno % 20 == 0 or dno == LO or dno == HI:
            print(f"[TLDASH] {dno} ok={ok_n} fail={fail_n} {fill}", flush=True)
            _write_progress(
                {
                    "status": "running",
                    "start": LO,
                    "end": HI,
                    "draw_no": dno,
                    "ok": ok_n,
                    "fail": fail_n,
                    "fill": fill,
                    "peek": peek_fill,
                }
            )

    after = _census()
    ledger_same = before["ledger_by"] == after["ledger_by"]
    hard_ok = (
        after["pred_1237"] == 0
        and after["draws_max"] == 1236
        and peek_fill == 0
        and ledger_same
        and after["pred_min"] == 1
        and after["pred_max"] == 1236
    )
    payload = {
        "id": "K-TL-DASH-BACKFILL-1236",
        "as_of": _now(),
        "lo": LO,
        "hi": HI,
        "deleted": deleted,
        "fill": fill,
        "ok": ok_n,
        "fail": fail_n,
        "peek": peek_fill,
        "before": before,
        "after": after,
        "ledger_same": ledger_same,
        "hard_ok": hard_ok,
        "pred_1237": after["pred_1237"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-TL-DASH-BACKFILL-1236 (2026-08-15)",
        "",
        f"- **판정:** `{'BACKFILL_OK' if hard_ok else 'BACKFILL_PARTIAL'}`",
        "- 형 요청: 예측 초기화 + 테스트 대시보드 탭 + 1–1236 백필",
        "",
        "## 실측",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 삭제 pred/cache/evolve | {deleted['pred']} / {deleted['cache']} / {deleted['evolve']} |",
        f"| fill ok / fail | {ok_n} / {fail_n} |",
        f"| peek | {peek_fill} |",
        f"| pred 후 | {after['pred_n']} · {after['pred_min']}–{after['pred_max']} · by={after['pred_by']} |",
        f"| cache 후 | {after['cache_n']} · {after['cache_min']}–{after['cache_max']} |",
        f"| pred_1237 | {after['pred_1237']} |",
        f"| ledger 보존 | {ledger_same} · {after['ledger_by']} |",
        f"| MAX | {after['draws_max']} |",
        "",
        "- 우열/hits 클레임 금지. 대시보드 숫자는 기록.",
        "- 롤백=`backups/20260815_TLDASH전_DB전체/`",
        "- 1237아님.",
        "",
        "## 파일",
        "",
        "- `tools/_k_tl_dash_backfill_1236.py`",
        "- `app/testlotto/routes.py` · `app/static/index.html` · `app/static/js/lotto4.js`",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    _write_progress(
        {
            "status": "done",
            "start": LO,
            "end": HI,
            "draw_no": HI,
            "ok": ok_n,
            "fail": fail_n,
            "pred_n": after["pred_n"],
            "hard_ok": hard_ok,
        }
    )
    print("[TLDASH] done", payload["hard_ok"], after, flush=True)
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
