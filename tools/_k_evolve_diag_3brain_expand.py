# -*- coding: utf-8 -*-
"""K-EVOLVE-DIAG-3BRAIN-EXPAND — 캐시→evolve_log 3뇌 독립 write. 예측로직 미변경."""
from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.evolve_auto import evolve_auto_enabled
from app.testlotto.evolve_diag import (
    BRAINS,
    HAS_APPLY_LEARN_BOOST,
    record_predictions_from_cache,
    write_evolve_diag,
)
from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KEVOLVE_DIAG_3BRAIN_EXPAND.json"
OUT_MD = ROOT / "reports" / "20260815_KEVOLVE_DIAG_3BRAIN_EXPAND.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
BAK_DIR = ROOT / "backups" / "20260815_EXPAND전_DB전체"
CENSUS0 = BAK_DIR / "census.json"
LO, HI = 1037, 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _connect(rw: bool = False) -> sqlite3.Connection:
    if rw:
        conn = sqlite3.connect(str(DB), timeout=60.0)
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
            "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache GROUP BY brain"
        )
    }
    peek = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no"
        ).fetchone()[0]
    )
    pred_by = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM lotto_predictions GROUP BY brain_tag"
        )
    }
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    pred_1237 = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
        ).fetchone()[0]
    )
    dmax = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
    learn = int(conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0])
    skill_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_skill_homework").fetchone()[0])
    role_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_role_homework").fetchone()[0])
    conn.close()
    return {
        "evolve_n": sum(ev.values()),
        "evolve_by": ev,
        "ledger_by": led,
        "cache_by": cache,
        "peek_as_of_ge_draw": peek,
        "pred_n": pred_n,
        "pred_by": pred_by,
        "pred_1237": pred_1237,
        "draws_max": int(dmax) if dmax else None,
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


def _restore() -> None:
    bak = BAK_DIR / "lotto_testlotto.db"
    if not bak.exists():
        return
    src = sqlite3.connect(str(bak))
    dst = sqlite3.connect(str(DB))
    src.backup(dst)
    dst.close()
    src.close()


def _cache_fp() -> dict[str, str]:
    conn = _connect(False)
    out: dict[str, str] = {}
    for tag in BRAINS:
        h = hashlib.sha256()
        rows = conn.execute(
            """
            SELECT draw_no, pool_json, repack_json
            FROM testlotto_pool_view_cache
            WHERE brain=? AND draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (tag, LO, HI),
        ).fetchall()
        for r in rows:
            h.update(str(r["draw_no"]).encode())
            h.update((r["pool_json"] or "").encode())
            h.update((r["repack_json"] or "").encode())
        out[tag] = h.hexdigest()[:16]
    conn.close()
    return out


def _axis_from_cache() -> dict[str, Any]:
    conn = _connect(False)
    by: dict[str, dict[str, float | None]] = {}
    for tag in BRAINS:
        prefs: list[float] = []
        prizes: list[float] = []
        for r in conn.execute(
            """
            SELECT draw_no, repack_json FROM testlotto_pool_view_cache
            WHERE brain=? AND draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (tag, LO, HI),
        ):
            dno = int(r["draw_no"])
            rep = json.loads(r["repack_json"] or "[]")
            draws = _get_draws_before(dno)
            pref_t = cs.prefer_table(draws, brain="markov")
            prize_t = cs.prize_table(draws, brain="review")
            avgs_p: list[float] = []
            avgs_z: list[float] = []
            for s in rep:
                nums = [int(x) for x in (s.get("nums") or [])]
                if len(nums) != 6:
                    continue
                avgs_p.append(cs.set_crowd_score(nums, pref_t)[0])
                avgs_z.append(cs.set_crowd_score(nums, prize_t)[0])
            if avgs_p:
                prefs.append(mean(avgs_p))
            if avgs_z:
                prizes.append(mean(avgs_z))
        by[tag] = {
            "prefer": round(mean(prefs), 6) if prefs else None,
            "prize": round(mean(prizes), 6) if prizes else None,
            "n": len(prefs),
        }
    conn.close()
    return by


def _nums_key(items: list[dict[str, Any]]) -> tuple[tuple[int, ...], ...]:
    keys: list[tuple[int, ...]] = []
    for s in items:
        nums = tuple(int(x) for x in (s.get("nums") or []))
        if len(nums) == 6:
            keys.append(nums)
    return tuple(keys)


def _independence() -> dict[str, Any]:
    conn = _connect(False)
    drift = {t: 0 for t in BRAINS}
    n_ok = {t: 0 for t in BRAINS}
    cross = 0
    for dno in range(LO, HI + 1):
        cache_nums: dict[str, tuple] = {}
        evo_nums: dict[str, tuple] = {}
        for tag in BRAINS:
            c = conn.execute(
                "SELECT pool_json, repack_json FROM testlotto_pool_view_cache WHERE draw_no=? AND brain=?",
                (dno, tag),
            ).fetchone()
            e = conn.execute(
                "SELECT pool_json, repack_json FROM testlotto_evolve_log WHERE draw_no=? AND brain_tag=?",
                (dno, tag),
            ).fetchone()
            if not c or not e:
                drift[tag] += 1
                continue
            ck = _nums_key(json.loads(c["pool_json"] or "[]")) + _nums_key(
                json.loads(c["repack_json"] or "[]")
            )
            ek = _nums_key(json.loads(e["pool_json"] or "[]")) + _nums_key(
                json.loads(e["repack_json"] or "[]")
            )
            cache_nums[tag] = ck
            evo_nums[tag] = ek
            if ck != ek:
                drift[tag] += 1
            else:
                n_ok[tag] += 1
        for tag in BRAINS:
            others = [t for t in BRAINS if t != tag]
            if tag not in evo_nums:
                continue
            for ot in others:
                if ot in cache_nums and evo_nums[tag] == cache_nums[ot] and evo_nums[tag] != cache_nums.get(tag):
                    cross += 1
    conn.close()
    return {
        "drift_by": drift,
        "n_ok_by": n_ok,
        "drift": sum(drift.values()),
        "cross_source": cross,
    }


def _cache_nonempty(draw_no: int, brain: str) -> bool:
    conn = _connect(False)
    row = conn.execute(
        "SELECT pool_json, repack_json FROM testlotto_pool_view_cache WHERE draw_no=? AND brain=?",
        (int(draw_no), brain),
    ).fetchone()
    conn.close()
    if not row:
        return False
    pool = json.loads(row["pool_json"] or "[]")
    rep = json.loads(row["repack_json"] or "[]")
    return bool(pool) and bool(rep)


def _fill_brain_cache(dno: int, tag: str) -> dict[str, Any]:
    """빈 캐시만 해당 뇌 expand로 채움. stat 미접촉. 원장/숙제 미호출."""
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
    return {
        "ok": True,
        "n_pool": len(payload["pool_by_brain"][tag]),
        "n_repack": len(payload["repack_by_brain"][tag]),
    }


def _reset_predictions() -> int:
    conn = _connect(True)
    n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    conn.execute("DELETE FROM lotto_predictions")
    conn.commit()
    conn.close()
    return n


def _md(o: dict[str, Any]) -> str:
    h = o.get("hard") or {}
    g = o.get("gate") or {}
    w = o.get("write") or {}
    c0 = o.get("census_before") or {}
    c1 = o.get("census_after") or {}
    ind = o.get("independence") or {}
    lines = [
        "# K-EVOLVE-DIAG-3BRAIN-EXPAND",
        "",
        f"시각: {o['as_of']} · **{o.get('verdict')}** · 3뇌 독립 write · 1237아님 · hits/tier 클레임 금지",
        "목적=캐시 채점 append를 markov/review로 확장. 예측로직 미변경. EVOLVE_AUTO/FEATURE_LAMBDA OFF.",
        "",
        f"HARD={'통과' if o.get('hard_ok') else '실패'}. "
        f"write ok={w.get('n_ok')} skip={w.get('n_skip')} fail={w.get('n_fail')}. "
        f"pred_reset={o.get('pred_deleted')} pred_after={c1.get('pred_n')}.",
        "",
        "## 1) census",
        "",
        "| 항목 | 전 | 후 |",
        "|------|----|----|",
        f"| evolve 행 | {c0.get('evolve_n')} | {c1.get('evolve_n')} |",
        f"| evolve 뇌 | {c0.get('evolve_by')} | {c1.get('evolve_by')} |",
        f"| 원장 | {c0.get('ledger_by')} | {c1.get('ledger_by')} |",
        f"| 캐시 | {c0.get('cache_by')} | {c1.get('cache_by')} |",
        f"| predictions | {c0.get('pred_n')} | {c1.get('pred_n')} |",
        f"| pred 뇌 | {c0.get('pred_by')} | {c1.get('pred_by')} |",
        f"| pred_1237 | {c0.get('pred_1237')} | {c1.get('pred_1237')} |",
        f"| draws MAX | {c0.get('draws_max')} | {c1.get('draws_max')} |",
        f"| learn/skill_hw/role_hw | {c0.get('learn_n')}/{c0.get('skill_hw')}/{c0.get('role_hw')} | {c1.get('learn_n')}/{c1.get('skill_hw')}/{c1.get('role_hw')} |",
        "",
        "## 2) HARD",
        "",
        "| 항 | 값 |",
        "|----|-----|",
        f"| peek as_of>=draw | {h.get('peek')} |",
        f"| evolve 뇌별 | {h.get('evolve_by')} |",
        f"| 합산뷰 | 없음 |",
        f"| 원장 불변 | {h.get('ledger_unchanged')} |",
        f"| learn/숙제 불변 | {h.get('learn_unchanged')} |",
        f"| stat 캐시 fp 불변 | {h.get('stat_fp_unchanged')} |",
        f"| markov/review 캐시 채움 | {h.get('filled_ok')} |",
        f"| drift | {h.get('drift')} |",
        f"| cross_source | {h.get('cross_source')} |",
        f"| pred_1237 | {h.get('pred_1237')} |",
        f"| draws MAX | {h.get('draws_max')} |",
        f"| EVOLVE_AUTO | {h.get('evolve_auto')} |",
        f"| FEATURE_LAMBDA | {h.get('feature_lambda')} |",
        f"| review learn_boost | {h.get('review_learn_boost')} |",
        "",
        "## 3) prefer/prize (캐시 불변 증명 · 모니터)",
        "",
        "| 뇌 | prefer전 | prefer후 | Δprefer | prize전 | prize후 | Δprize |",
        "|----|----------|----------|---------|---------|---------|--------|",
    ]
    for tag in BRAINS:
        gg = (g.get("by_brain") or {}).get(tag) or {}
        lines.append(
            f"| {tag} | {gg.get('prefer_before')} | {gg.get('prefer_after')} | {gg.get('d_prefer')} | "
            f"{gg.get('prize_before')} | {gg.get('prize_after')} | {gg.get('d_prize')} |"
        )
    lines += [
        "",
        "예측 세트를 다시 뽑지 않음(캐시→로그/발권 복사). Δ≠0이면 캐시가 바뀐 것(실패).",
        "",
        "## 4) 독립",
        "",
        f"- evolve nums == 해당뇌 캐시: ok={ind.get('n_ok_by')} drift={ind.get('drift_by')}",
        f"- 타뇌 캐시 소스로 기록: {ind.get('cross_source')}",
        f"- review apply_learn_boost 함수: **없음**(carry만). 기록 features.has_apply_learn_boost=false.",
        "",
        "## 5) 롤백",
        "",
        "`write_evolve_diag_confirmed` 호출 제거 + `DELETE FROM testlotto_evolve_log WHERE brain_tag IN ('markov','review')` "
        "+ `backups/20260815_EXPAND전_DB전체` 복원. 원장 불변.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    _backup()
    before = _census()
    CENSUS0.write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    fp_before = _cache_fp()
    axis_before = _axis_from_cache()

    pred_deleted = _reset_predictions()

    n_ok = n_skip = n_fail = 0
    n_fill = 0
    skips: dict[str, int] = {}
    fails: list[str] = []
    pred_n = 0
    for dno in range(LO, HI + 1):
        if (dno - LO) % 20 == 0:
            print(f"[EXPAND] draw={dno} fill={n_fill} write={n_ok}", flush=True)
        for tag in ("markov", "review"):
            if _cache_nonempty(dno, tag):
                continue
            fr = _fill_brain_cache(dno, tag)
            if not fr.get("ok"):
                n_fail += 1
                fails.append(f"{dno}:{tag}:fill:{fr}")
                after_fail = _census()
                _fail_out(before, after_fail, axis_before, fp_before, pred_deleted, n_ok, n_skip, n_fail, skips, fails)
                _restore()
                print(json.dumps({"verdict": "EXPAND_FAIL", "fail": fails[-1]}, ensure_ascii=False))
                return 1
            n_fill += 1
        for tag in BRAINS:
            r = write_evolve_diag(dno, tag)
            if r.get("ok") and r.get("inserted"):
                n_ok += 1
            elif r.get("skipped"):
                n_skip += 1
                sk = str(r["skipped"])
                skips[sk] = skips.get(sk, 0) + 1
                fails.append(f"{dno}:{tag}:{sk}")
                after_fail = _census()
                _fail_out(before, after_fail, axis_before, fp_before, pred_deleted, n_ok, n_skip, n_fail + 1, skips, fails)
                _restore()
                print(json.dumps({"verdict": "EXPAND_FAIL", "fail": fails[-1]}, ensure_ascii=False))
                return 1
            else:
                n_fail += 1
                fails.append(f"{dno}:{tag}:{r}")
                _restore()
                print(json.dumps({"verdict": "EXPAND_FAIL", "fail": fails[-1]}, ensure_ascii=False))
                return 1
            pr = record_predictions_from_cache(dno, tag)
            if not pr.get("ok"):
                n_fail += 1
                fails.append(f"{dno}:{tag}:pred:{pr}")
                _restore()
                print(json.dumps({"verdict": "EXPAND_FAIL", "fail": fails[-1]}, ensure_ascii=False))
                return 1
            pred_n += int(pr.get("n") or 0)

    after = _census()
    fp_after = _cache_fp()
    axis_after = _axis_from_cache()
    ind = _independence()

    gate_by: dict[str, Any] = {}
    d_all_zero = True
    for tag in BRAINS:
        pb = axis_before[tag]["prefer"]
        pa = axis_after[tag]["prefer"]
        zb = axis_before[tag]["prize"]
        za = axis_after[tag]["prize"]
        dp = round(pa - pb, 6) if pb is not None and pa is not None else None
        dz = round(za - zb, 6) if zb is not None and za is not None else None
        gate_by[tag] = {
            "prefer_before": pb,
            "prefer_after": pa,
            "d_prefer": dp,
            "prize_before": zb,
            "prize_after": za,
            "d_prize": dz,
        }
        if tag == "stat" and (dp != 0.0 or dz != 0.0):
            d_all_zero = False

    ev_by = after.get("evolve_by") or {}
    hard = {
        "peek": int(after.get("peek_as_of_ge_draw") or 0),
        "evolve_by": ev_by,
        "evolve_split_ok": ev_by.get("stat") == 200
        and ev_by.get("markov") == 200
        and ev_by.get("review") == 200
        and after.get("evolve_n") == 600,
        "ledger_unchanged": after.get("ledger_by") == before.get("ledger_by"),
        "learn_unchanged": after.get("learn_n") == before.get("learn_n")
        and after.get("skill_hw") == before.get("skill_hw")
        and after.get("role_hw") == before.get("role_hw"),
        "stat_fp_unchanged": fp_before.get("stat") == fp_after.get("stat"),
        "filled_ok": n_fill == 400,
        "cache_by_unchanged": after.get("cache_by") == before.get("cache_by"),
        "drift": ind["drift"],
        "cross_source": ind["cross_source"],
        "pred_1237": int(after.get("pred_1237") or 0),
        "pred_n": after.get("pred_n"),
        "draws_max": after.get("draws_max"),
        "evolve_auto": bool(evolve_auto_enabled()),
        "feature_lambda": bool(FEATURE_LAMBDA_WIRE),
        "review_learn_boost": bool(HAS_APPLY_LEARN_BOOST["review"]),
        "n_fill": n_fill,
    }
    hard_ok = (
        hard["peek"] == 0
        and hard["evolve_split_ok"]
        and hard["ledger_unchanged"]
        and hard["learn_unchanged"]
        and hard["stat_fp_unchanged"]
        and hard["filled_ok"]
        and hard["cache_by_unchanged"]
        and hard["drift"] == 0
        and hard["cross_source"] == 0
        and hard["pred_1237"] == 0
        and hard["draws_max"] == 1236
        and hard["evolve_auto"] is False
        and hard["feature_lambda"] is False
        and hard["review_learn_boost"] is False
        and n_fail == 0
        and n_skip == 0
        and n_ok == 600
        and d_all_zero
        and after.get("pred_n") == 3000
    )
    out = {
        "id": "K-EVOLVE-DIAG-3BRAIN-EXPAND",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "verdict": "EXPAND_OK" if hard_ok else "EXPAND_FAIL",
        "hard_ok": hard_ok,
        "hard": hard,
        "write": {"n_ok": n_ok, "n_skip": n_skip, "n_fail": n_fail, "skips": skips, "fails": fails[:8]},
        "pred_deleted": pred_deleted,
        "pred_recorded": pred_n,
        "n_fill": n_fill,
        "census_before": before,
        "census_after": after,
        "cache_fp_before": fp_before,
        "cache_fp_after": fp_after,
        "independence": ind,
        "gate": {"by_brain": gate_by, "all_delta_zero": d_all_zero, "monitor_only": True},
        "review_structure": {
            "apply_learn_boost": False,
            "carry_only": True,
            "note": "review_brain/learn.py 에 apply_learn_boost 없음. engine은 carry_over_boost만.",
        },
        "flags": {
            "EVOLVE_AUTO": bool(evolve_auto_enabled()),
            "FEATURE_LAMBDA_WIRE": bool(FEATURE_LAMBDA_WIRE),
        },
    }
    if not hard_ok:
        _restore()
        out["rolled_back"] = True
        out["verdict"] = "EXPAND_FAIL"
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": out["verdict"],
                "hard_ok": hard_ok,
                "n_ok": n_ok,
                "n_skip": n_skip,
                "n_fail": n_fail,
                "peek": hard["peek"],
                "evolve_by": ev_by,
                "drift": hard["drift"],
                "pred_n": after.get("pred_n"),
                "d_all_zero": d_all_zero,
                "rolled_back": out.get("rolled_back", False),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if hard_ok else 1


def _fail_out(before, after, axis_before, fp_before, pred_deleted, n_ok, n_skip, n_fail, skips, fails) -> None:
    out = {
        "id": "K-EVOLVE-DIAG-3BRAIN-EXPAND",
        "as_of": _now(),
        "verdict": "EXPAND_FAIL",
        "hard_ok": False,
        "write": {"n_ok": n_ok, "n_skip": n_skip, "n_fail": n_fail, "skips": skips, "fails": fails[:8]},
        "pred_deleted": pred_deleted,
        "census_before": before,
        "census_after": after,
        "cache_fp_before": fp_before,
        "gate": {"by_brain": {t: {"prefer_before": axis_before[t]["prefer"]} for t in BRAINS}},
        "rolled_back": True,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text("# K-EVOLVE-DIAG-3BRAIN-EXPAND\n\n**EXPAND_FAIL** · 중단·롤백.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
