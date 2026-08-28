# -*- coding: utf-8 -*-
"""K-REVIEW-VECTOR-REFILL-200 — 20260828 벡터 200 리셋 후 3뇌 재백필. 원장/숙제 보존. 1237 예측 금지."""
from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.review_brain.kb7_future import REVIEW_KB7_WIRE
from app.testlotto.data_service import _get_draws_before
from app.testlotto.evolve_auto import evolve_auto_enabled
from app.testlotto.evolve_diag import record_predictions_from_cache, write_evolve_diag
from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE, ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260828_KREVIEW_VECTOR_REFILL_200.json"
OUT_MD = ROOT / "reports" / "20260828_KREVIEW_VECTOR_REFILL_200.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
BAK_DIR = ROOT / "backups" / "20260828_VECTOR전_DB전체"
LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _connect(rw: bool = False) -> sqlite3.Connection:
    if rw:
        conn = sqlite3.connect(str(DB), timeout=120.0)
    else:
        conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _census() -> dict[str, Any]:
    conn = _connect(False)
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
    cache = {
        str(r["brain"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache "
            "WHERE draw_no BETWEEN ? AND ? GROUP BY brain",
            (LO, HI),
        )
    }
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    ev_win = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log "
            "WHERE draw_no BETWEEN ? AND ? GROUP BY brain_tag",
            (LO, HI),
        )
    }
    pred_by = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM lotto_predictions "
            "WHERE target_draw_no BETWEEN ? AND ? GROUP BY brain_tag",
            (LO, HI),
        )
    }
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    pred_1238 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1238").fetchone()[0]
    )
    pred_1239 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0]
    )
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    learn = int(conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0])
    skill_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_skill_homework").fetchone()[0])
    role_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_role_homework").fetchone()[0])
    nonempty = {}
    for tag in BRAINS:
        n = 0
        for r in conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ?",
            (tag, LO, HI),
        ):
            p = json.loads(r["pool_json"] or "[]")
            q = json.loads(r["repack_json"] or "[]")
            if len(p) >= 10 and len(q) >= 5:
                n += 1
        nonempty[tag] = n
    conn.close()
    return {
        "evolve_by": ev,
        "evolve_window": ev_win,
        "ledger_by": led,
        "cache_by": cache,
        "cache_nonempty": nonempty,
        "peek": peek,
        "pred_n": pred_n,
        "pred_by": pred_by,
        "pred_1237": pred_1237,
        "pred_1238": pred_1238,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "learn_n": learn,
        "skill_hw": skill_hw,
        "role_hw": role_hw,
    }


def _fp() -> dict[str, str]:
    conn = _connect(False)
    out: dict[str, str] = {}
    for tag in BRAINS:
        h = hashlib.sha256()
        for r in conn.execute(
            "SELECT draw_no, pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (tag, LO, HI),
        ):
            h.update(str(r["draw_no"]).encode())
            h.update((r["pool_json"] or "").encode())
            h.update((r["repack_json"] or "").encode())
        out[tag] = h.hexdigest()[:16]
    conn.close()
    return out


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


def _reset_vectors() -> dict[str, int]:
    conn = _connect(True)
    n_cache = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_view_cache WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        ).fetchone()[0]
    )
    n_pred = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            (LO, HI),
        ).fetchone()[0]
    )
    n_ev = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        ).fetchone()[0]
    )
    conn.execute("DELETE FROM testlotto_pool_view_cache WHERE draw_no BETWEEN ? AND ?", (LO, HI))
    conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?", (LO, HI))
    conn.execute("DELETE FROM lotto_predictions WHERE target_draw_no IN (1237, 1239)")
    conn.execute("DELETE FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?", (LO, HI))
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
        "ok": bool(ev.get("ok") and pr.get("ok")),
        "n_pool": len(payload["pool_by_brain"][tag]),
        "n_repack": len(payload["repack_by_brain"][tag]),
        "evolve_ok": bool(ev.get("ok")),
        "pred_n": int(pr.get("n") or 0),
        "error": ev.get("skipped") or pr.get("skipped"),
    }


def main() -> int:
    print("[VECTOR] backup", flush=True)
    _backup()
    before = _census()
    fp0 = _fp()
    print("[VECTOR] reset", before, flush=True)
    deleted = _reset_vectors()
    mid = _census()
    print("[VECTOR] after reset", mid, flush=True)

    fill: dict[str, dict[str, int]] = {t: {"ok": 0, "fail": 0} for t in BRAINS}
    peek_fill = 0
    for dno in range(LO, HI + 1):
        for tag in BRAINS:
            r = _fill_one(dno, tag)
            if r.get("error") == "peek":
                peek_fill += 1
                fill[tag]["fail"] += 1
            elif r.get("ok"):
                fill[tag]["ok"] += 1
            else:
                fill[tag]["fail"] += 1
        if (dno - LO + 1) % 40 == 0:
            print(f"[VECTOR] {dno} {fill}", flush=True)

    after = _census()
    fp1 = _fp()
    ledger_same = before["ledger_by"] == after["ledger_by"]
    hw_same = (
        before["learn_n"] == after["learn_n"]
        and before["skill_hw"] == after["skill_hw"]
        and before["role_hw"] == after["role_hw"]
    )
    hard_ok = (
        after["peek"] == 0
        and peek_fill == 0
        and after["pred_1237"] == 0
        and after["pred_1239"] == 0
        and after["draws_max"] == 1238
        and after["evolve_window"].get("stat") == 200
        and after["evolve_window"].get("markov") == 200
        and after["evolve_window"].get("review") == 200
        and after["cache_nonempty"].get("stat") == 200
        and after["cache_nonempty"].get("markov") == 200
        and after["cache_nonempty"].get("review") == 200
        and after["pred_by"].get("stat") == 1000
        and after["pred_by"].get("markov") == 1000
        and after["pred_by"].get("review") == 1000
        and ledger_same
        and hw_same
        and FEATURE_LAMBDA_WIRE is False
        and REVIEW_KB7_WIRE is False
        and evolve_auto_enabled() is False
        and sorted(ROLE_TIER_LEARN_BRAINS) == ["stat"]
        and all(fill[t]["ok"] == 200 and fill[t]["fail"] == 0 for t in BRAINS)
    )

    payload = {
        "id": "K-REVIEW-VECTOR-REFILL-200",
        "as_of": _now(),
        "verdict": "REFILL_OK" if hard_ok else "REFILL_FAIL",
        "apply": True,
        "db_git": False,
        "ge3_claim": False,
        "draw_1237": False,
        "draw_1239": False,
        "window": [LO, HI],
        "hard_ok": hard_ok,
        "deleted": deleted,
        "fill": fill,
        "peek_fill": peek_fill,
        "fp_before": fp0,
        "fp_after": fp1,
        "census_before": before,
        "census_mid": mid,
        "census_after": after,
        "ledger_unchanged": ledger_same,
        "homework_unchanged": hw_same,
        "knobs": {
            "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
            "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
            "REVIEW_KB7_WIRE": REVIEW_KB7_WIRE,
            "EVOLVE_AUTO": evolve_auto_enabled(),
        },
        "backup": str(BAK_DIR),
    }

    lines = [
        "# K-REVIEW-VECTOR-REFILL-200",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · 3뇌 벡터 리셋+재백필 · 1237/1239아님 · hits 클레임 금지",
        "목적=금액뇌 튜닝 후 1037–1236 캐시·예측·evolve를 지우고 3뇌 각각 `expand_pool(brains=[tag])` 200회 재생성.",
        "원장·숙제·learn 보존. DB 파일 커밋 안 함. 7번 WIRE False.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. peek={after['peek']} · pred_1237={after['pred_1237']} · pred_1239={after['pred_1239']} · MAX={after['draws_max']}.",
        "",
        "## 1) 리셋",
        "",
        f"| 표 | 삭제 |",
        f"|----|------|",
        f"| pool_view_cache {LO}–{HI} | {deleted['cache']} |",
        f"| lotto_predictions {LO}–{HI} | {deleted['pred']} |",
        f"| evolve_log {LO}–{HI} | {deleted['evolve']} |",
        "",
        "보존: lotto_draws · pool_hit_ledger · skill_homework · role_homework · learn_state.",
        "",
        "## 2) 백필",
        "",
        f"| 뇌 | expand ok | fail | cache nonempty | evolve | pred(repack5) | fp 전→후 |",
        f"|----|-----------|------|----------------|--------|---------------|----------|",
    ]
    for tag in BRAINS:
        lines.append(
            f"| {tag} | {fill[tag]['ok']} | {fill[tag]['fail']} | "
            f"{after['cache_nonempty'].get(tag)} | {after['evolve_window'].get(tag)} | "
            f"{after['pred_by'].get(tag)} | {fp0.get(tag)}→{fp1.get(tag)} |"
        )
    lines += [
        "",
        "## 3) census",
        "",
        f"| 항 | 전 | 후 |",
        f"|----|----|----|",
        f"| 원장 | {before['ledger_by']} | {after['ledger_by']} |",
        f"| learn/skill/role | {before['learn_n']}/{before['skill_hw']}/{before['role_hw']} | {after['learn_n']}/{after['skill_hw']}/{after['role_hw']} |",
        f"| 숙제 소비 | {sorted(ROLE_TIER_LEARN_BRAINS)} | 동일 |",
        "",
        "## 4) 판정",
        "",
        "REFILL_OK면 3뇌 벡터가 지금 노브(합리장·3연속·극소형태·형태지식 저울·7번 WIRE False)로 다시 채워진 것. 성적 아님.",
        "롤백=백업 `backups/20260828_VECTOR전_DB전체/`.",
        "",
        "## 5) 금지 확인",
        "",
        "1237 없음. 숙제ON/covering휠/S2/궁합 APPLY 없음. 동결 토큰 미수정. kweon 미접촉. DB git 안 함.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "hard_ok": hard_ok, "fill": fill, "fp": fp1}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
