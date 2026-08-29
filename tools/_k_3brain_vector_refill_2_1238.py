# -*- coding: utf-8 -*-
"""K-3BRAIN-VECTOR-REFILL-2-1238 — 예측 기록 초기화 후 2–1238 3뇌 재백필.

1회는 draws_before 없음 → 스킵. 1239 예측 없음.
원장·숙제·learn·lotto_draws 보존. data/*.db git 안 함.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.data_service import _get_draws_before
from app.testlotto.evolve_diag import record_predictions_from_cache, write_evolve_diag
from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_K3BRAIN_VECTOR_REFILL_2_1238.json"
OUT_MD = ROOT / "reports" / "20260829_K3BRAIN_VECTOR_REFILL_2_1238.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
BAK_DIR = ROOT / "backups" / "20260829_VECTOR전_1_1238"
LO, HI = 2, 1238
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


def _census() -> dict[str, Any]:
    conn = _connect(False)
    cache = {
        str(r["brain"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache GROUP BY brain"
        )
    }
    ev = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    led = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    pred_by = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM lotto_predictions GROUP BY brain_tag"
        )
    }
    pred_win = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM lotto_predictions "
            "WHERE target_draw_no BETWEEN ? AND ? GROUP BY brain_tag",
            (LO, HI),
        )
    }
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1238 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1238").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    dmin = int(conn.execute("SELECT MIN(draw_no) FROM lotto_draws").fetchone()[0])
    learn = int(conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0])
    skill_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_skill_homework").fetchone()[0])
    role_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_role_homework").fetchone()[0])
    nonempty: dict[str, int] = {}
    for tag in BRAINS:
        n = 0
        for r in conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache WHERE brain=?",
            (tag,),
        ):
            p = json.loads(r["pool_json"] or "[]")
            q = json.loads(r["repack_json"] or "[]")
            if len(p) >= 10 and len(q) >= 5:
                n += 1
        nonempty[tag] = n
    tmin = conn.execute("SELECT MIN(target_draw_no) FROM lotto_predictions").fetchone()[0]
    tmax = conn.execute("SELECT MAX(target_draw_no) FROM lotto_predictions").fetchone()[0]
    conn.close()
    return {
        "cache_by": cache,
        "cache_nonempty": nonempty,
        "evolve_by": ev,
        "ledger_by": led,
        "pred_n": pred_n,
        "pred_by": pred_by,
        "pred_win": pred_win,
        "pred_min": tmin,
        "pred_max": tmax,
        "peek": peek,
        "pred_1237": pred_1237,
        "pred_1238": pred_1238,
        "pred_1239": pred_1239,
        "draws_min": dmin,
        "draws_max": dmax,
        "learn_n": learn,
        "skill_hw": skill_hw,
        "role_hw": role_hw,
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
    n_cache = int(conn.execute("SELECT COUNT(*) FROM testlotto_pool_view_cache").fetchone()[0])
    n_pred = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    n_ev = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0])
    conn.execute("DELETE FROM testlotto_pool_view_cache")
    conn.execute("DELETE FROM lotto_predictions")
    conn.execute("DELETE FROM testlotto_evolve_log")
    conn.commit()
    conn.close()
    return {"cache": n_cache, "pred": n_pred, "evolve": n_ev}


def _fill_one(dno: int, tag: str) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import payload_from_wf_parts, save_pool_view_cache_one

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    max_mat = max((int(d["draw_no"]) for d in draws), default=0)
    if max_mat >= dno:
        return {"ok": False, "error": "peek"}
    if not draws:
        return {"ok": False, "error": "no_history"}
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
    n_pool = len(payload["pool_by_brain"].get(tag) or [])
    n_repack = len(payload["repack_by_brain"].get(tag) or [])
    if n_pool < 10 or n_repack < 5:
        return {"ok": False, "error": "empty_build", "n_pool": n_pool, "n_repack": n_repack}
    save_pool_view_cache_one(dno, tag, payload)
    ev = write_evolve_diag(dno, tag)
    pr = record_predictions_from_cache(dno, tag)
    pred_n = int(pr.get("n") or 0)
    return {
        "ok": bool(pr.get("ok") and pred_n >= 5),
        "n_pool": n_pool,
        "n_repack": n_repack,
        "evolve_ok": bool(ev.get("ok")),
        "pred_n": pred_n,
        "error": None if pr.get("ok") else (ev.get("skipped") or pr.get("skipped")),
    }


def main() -> int:
    print("[VECTOR] backup", flush=True)
    _backup()
    before = _census()
    print("[VECTOR] reset", before.get("pred_n"), flush=True)
    deleted = _reset()
    mid = _census()
    print("[VECTOR] after reset pred=", mid["pred_n"], "cache=", mid["cache_by"], flush=True)

    fill: dict[str, dict[str, int]] = {t: {"ok": 0, "fail": 0} for t in BRAINS}
    peek_fill = 0
    no_hist = 0
    for dno in range(LO, HI + 1):
        for tag in BRAINS:
            r = _fill_one(dno, tag)
            if r.get("error") == "peek":
                peek_fill += 1
                fill[tag]["fail"] += 1
            elif r.get("error") == "no_history":
                no_hist += 1
                fill[tag]["fail"] += 1
            elif r.get("ok"):
                fill[tag]["ok"] += 1
            else:
                fill[tag]["fail"] += 1
        if dno % 50 == 0 or dno in (LO, HI, 3, 10, 100, 1236, 1237, 1238):
            print(f"[VECTOR] {dno} {fill} peek={peek_fill}", flush=True)

    after = _census()
    want = HI - LO + 1
    ledger_same = before["ledger_by"] == after["ledger_by"]
    hw_same = (
        before["learn_n"] == after["learn_n"]
        and before["skill_hw"] == after["skill_hw"]
        and before["role_hw"] == after["role_hw"]
    )
    hard_ok = (
        after["peek"] == 0
        and peek_fill == 0
        and after["pred_1239"] == 0
        and after["draws_max"] == 1238
        and after["pred_min"] == LO
        and after["pred_max"] == HI
        and all(after["cache_nonempty"].get(t, 0) >= want - 2 for t in BRAINS)
        and all(after["pred_win"].get(t, 0) >= 5 * (want - 2) for t in BRAINS)
        and ledger_same
        and hw_same
        and sorted(ROLE_TIER_LEARN_BRAINS) == ["stat"]
    )
    payload = {
        "id": "K-3BRAIN-VECTOR-REFILL-2-1238",
        "as_of": _now(),
        "verdict": "REFILL_OK" if hard_ok else "REFILL_PARTIAL",
        "apply": True,
        "db_git": False,
        "ge3_claim": False,
        "draw_1239": False,
        "window": [LO, HI],
        "skip_draw_1": "no_history",
        "hard_ok": hard_ok,
        "deleted": deleted,
        "fill": fill,
        "peek_fill": peek_fill,
        "no_hist": no_hist,
        "census_before": before,
        "census_mid": mid,
        "census_after": after,
        "ledger_unchanged": ledger_same,
        "homework_unchanged": hw_same,
        "backup": str(BAK_DIR),
        "ui": "테스트로또 회차 전환 · /api/testlotto/predictions/draw/{n} · pool-view 캐시",
    }
    lines = [
        "# K-3BRAIN-VECTOR-REFILL-2-1238",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · 예측기록 초기화 후 2–1238 3뇌 재백필 · hits 클레임 금지",
        "목적=브라우저에서 회차별 벡터 확인. 1회는 이전회 없음 스킵. 1239 예측 없음.",
        "원장·숙제·learn·lotto_draws 보존. DB git 안 함.",
        "",
        f"HARD={'통과' if hard_ok else '부분'}. peek={after['peek']} · pred_1237={after['pred_1237']} · pred_1238={after['pred_1238']} · pred_1239={after['pred_1239']} · MAX={after['draws_max']}.",
        "",
        "## 1) 리셋",
        "",
        f"| 표 | 삭제 |",
        f"|----|------|",
        f"| pool_view_cache 전체 | {deleted['cache']} |",
        f"| lotto_predictions 전체 | {deleted['pred']} |",
        f"| evolve_log 전체 | {deleted['evolve']} |",
        "",
        "보존: lotto_draws · pool_hit_ledger · skill_homework · role_homework · learn_state.",
        "",
        "## 2) 백필 2–1238",
        "",
        f"| 뇌 | expand ok | fail | cache nonempty | evolve | pred |",
        f"|----|-----------|------|----------------|--------|------|",
    ]
    for tag in BRAINS:
        lines.append(
            f"| {tag} | {fill[tag]['ok']} | {fill[tag]['fail']} | "
            f"{after['cache_nonempty'].get(tag)} | {after['evolve_by'].get(tag)} | "
            f"{after['pred_by'].get(tag)} |"
        )
    lines += [
        "",
        f"예측 구간 min={after['pred_min']} max={after['pred_max']}. 브라우저=테스트로또 회차전환.",
        "",
        "## 3) census",
        "",
        f"| 항 | 전 | 후 |",
        f"|----|----|----|",
        f"| 원장 | {before['ledger_by']} | {after['ledger_by']} |",
        f"| learn/skill/role | {before['learn_n']}/{before['skill_hw']}/{before['role_hw']} | {after['learn_n']}/{after['skill_hw']}/{after['role_hw']} |",
        "",
        "## 4) 판정",
        "",
        "성적 아님. 롤백=`backups/20260829_VECTOR전_1_1238/`.",
        "",
        "## 5) 금지 확인",
        "",
        "1239 없음. kweon 미접촉. 동결토큰 미수정. DB git 안 함.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {"verdict": payload["verdict"], "hard_ok": hard_ok, "fill": fill, "after": {
                "pred": after["pred_by"], "cache": after["cache_nonempty"],
                "pred_1237": after["pred_1237"], "pred_1238": after["pred_1238"], "pred_1239": after["pred_1239"],
            }},
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
