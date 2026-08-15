# -*- coding: utf-8 -*-
"""K-STAT-EVOLVE-DIAG-LOG APPLY 검증 — 1037~1236 n200. 원장·예측 미기록."""
from __future__ import annotations

import json
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
from app.testlotto.evolve_diag_stat import write_evolve_diag_stat
from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_EVOLVE_DIAG_LOG_APPLY.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_EVOLVE_DIAG_LOG_APPLY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
CENSUS0 = ROOT / "backups" / "20260815_EVOLVE전_DB전체" / "census.json"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _census() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
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
    peek_bad = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no"
        ).fetchone()[0]
    )
    ev_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0])
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    pred_1237 = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
        ).fetchone()[0]
    )
    dmax = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
    conn.close()
    return {
        "evolve_n": ev_n,
        "evolve_by": ev,
        "ledger_by": led,
        "cache_by": cache,
        "peek_as_of_ge_draw": peek_bad,
        "pred_n": pred_n,
        "pred_1237": pred_1237,
        "draws_max": int(dmax) if dmax else None,
    }


def _axis_from_cache() -> dict[str, float | None]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    prefs: list[float] = []
    prizes: list[float] = []
    for r in conn.execute(
        """
        SELECT draw_no, repack_json FROM testlotto_pool_view_cache
        WHERE brain='stat' AND draw_no BETWEEN ? AND ?
        ORDER BY draw_no
        """,
        (LO, HI),
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
    conn.close()
    return {
        "prefer_repack": round(mean(prefs), 6) if prefs else None,
        "prize_repack": round(mean(prizes), 6) if prizes else None,
        "n": len(prefs),
    }


def _md(o: dict[str, Any]) -> str:
    h = o.get("hard") or {}
    g = o.get("gate") or {}
    w = o.get("write") or {}
    c0 = o.get("census_before") or {}
    c1 = o.get("census_after") or {}
    return "\n".join(
        [
            "# K-STAT-EVOLVE-DIAG-LOG APPLY",
            "",
            f"시각: {o['as_of']} · **{o.get('verdict')}** · stat만 · 1237아님 · hits/tier 클레임 금지",
            "목적=캐시 채점 append. 예측 불변. EVOLVE_AUTO/FEATURE_LAMBDA OFF.",
            "",
            f"HARD={'통과' if o.get('hard_ok') else '실패'}. "
            f"write ok={w.get('n_ok')} skip={w.get('n_skip')} fail={w.get('n_fail')}.",
            "",
            "## 1) census",
            "",
            f"| 항목 | 전 | 후 |",
            f"|------|----|----|",
            f"| evolve 행 | {c0.get('evolve_n')} | {c1.get('evolve_n')} |",
            f"| evolve 뇌 | {c0.get('evolve_by')} | {c1.get('evolve_by')} |",
            f"| 원장 | {c0.get('ledger_by')} | {c1.get('ledger_by')} |",
            f"| 캐시 | {c0.get('cache_by')} | {c1.get('cache_by')} |",
            f"| predictions | {c0.get('pred_n')} | {c1.get('pred_n')} |",
            f"| pred_1237 | {c0.get('pred_1237')} | {c1.get('pred_1237')} |",
            f"| draws MAX | {c0.get('draws_max')} | {c1.get('draws_max')} |",
            "",
            "## 2) HARD",
            "",
            f"| 항 | 값 |",
            f"|----|-----|",
            f"| peek as_of>=draw | {h.get('peek')} |",
            f"| brain 전부 stat | {h.get('all_stat')} |",
            f"| markov/review 행 | {h.get('other_brains')} |",
            f"| 원장 3000 불변 | {h.get('ledger_unchanged')} |",
            f"| predictions 불변 | {h.get('pred_unchanged')} |",
            f"| pred_1237 | {h.get('pred_1237')} |",
            f"| draws MAX | {h.get('draws_max')} |",
            f"| EVOLVE_AUTO | {h.get('evolve_auto')} |",
            f"| FEATURE_LAMBDA | {h.get('feature_lambda')} |",
            "",
            "## 3) prefer/prize (캐시 불변 증명 · 모니터)",
            "",
            f"| 축 | 전 | 후 | Δ |",
            f"|----|----|----|---|",
            f"| prefer | {g.get('prefer_before')} | {g.get('prefer_after')} | {g.get('d_prefer')} |",
            f"| prize | {g.get('prize_before')} | {g.get('prize_after')} | {g.get('d_prize')} |",
            "",
            "예측 세트를 다시 뽑지 않음. Δ≠0이면 캐시가 바뀐 것(실패).",
            "",
            "## 4) 롤백",
            "",
            "`write_evolve_diag_stat` 호출 제거 + `DELETE FROM testlotto_evolve_log WHERE brain_tag='stat'`. 원장·예측 불변.",
            "",
        ]
    )


def main() -> int:
    before = json.loads(CENSUS0.read_text(encoding="utf-8")) if CENSUS0.exists() else _census()
    live_before = _census()
    axis_before = _axis_from_cache()

    n_ok = n_skip = n_fail = 0
    skips: dict[str, int] = {}
    fails: list[str] = []
    for dno in range(LO, HI + 1):
        r = write_evolve_diag_stat(dno)
        if r.get("ok") and r.get("inserted"):
            n_ok += 1
        elif r.get("skipped"):
            n_skip += 1
            sk = str(r["skipped"])
            skips[sk] = skips.get(sk, 0) + 1
        else:
            n_fail += 1
            fails.append(f"{dno}:{r}")
            break

    after = _census()
    axis_after = _axis_from_cache()
    d_pref = None
    d_prize = None
    if axis_before["prefer_repack"] is not None and axis_after["prefer_repack"] is not None:
        d_pref = round(axis_after["prefer_repack"] - axis_before["prefer_repack"], 6)
    if axis_before["prize_repack"] is not None and axis_after["prize_repack"] is not None:
        d_prize = round(axis_after["prize_repack"] - axis_before["prize_repack"], 6)

    ev_by = after.get("evolve_by") or {}
    hard = {
        "peek": int(after.get("peek_as_of_ge_draw") or 0),
        "all_stat": ev_by.get("stat", 0) == after.get("evolve_n") and ev_by.get("stat", 0) == n_ok,
        "other_brains": int(ev_by.get("markov") or 0) + int(ev_by.get("review") or 0),
        "ledger_unchanged": after.get("ledger_by") == live_before.get("ledger_by"),
        "pred_unchanged": after.get("pred_n") == live_before.get("pred_n"),
        "pred_1237": int(after.get("pred_1237") or 0),
        "draws_max": after.get("draws_max"),
        "evolve_auto": bool(evolve_auto_enabled()),
        "feature_lambda": bool(FEATURE_LAMBDA_WIRE),
    }
    hard_ok = (
        hard["peek"] == 0
        and hard["all_stat"]
        and hard["other_brains"] == 0
        and hard["ledger_unchanged"]
        and hard["pred_unchanged"]
        and hard["pred_1237"] == 0
        and hard["draws_max"] == 1236
        and hard["evolve_auto"] is False
        and hard["feature_lambda"] is False
        and n_fail == 0
        and d_pref == 0.0
        and d_prize == 0.0
    )
    out = {
        "id": "K-STAT-EVOLVE-DIAG-LOG-APPLY",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "verdict": "APPLY_OK" if hard_ok else "APPLY_FAIL",
        "hard_ok": hard_ok,
        "hard": hard,
        "write": {"n_ok": n_ok, "n_skip": n_skip, "n_fail": n_fail, "skips": skips, "fails": fails[:5]},
        "census_before": before,
        "census_live_before": live_before,
        "census_after": after,
        "gate": {
            "prefer_before": axis_before["prefer_repack"],
            "prefer_after": axis_after["prefer_repack"],
            "d_prefer": d_pref,
            "prize_before": axis_before["prize_repack"],
            "prize_after": axis_after["prize_repack"],
            "d_prize": d_prize,
            "monitor_only": True,
        },
        "flags": {
            "EVOLVE_AUTO": bool(evolve_auto_enabled()),
            "FEATURE_LAMBDA_WIRE": bool(FEATURE_LAMBDA_WIRE),
        },
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "hard_ok": hard_ok,
        "n_ok": n_ok,
        "n_skip": n_skip,
        "n_fail": n_fail,
        "peek": hard["peek"],
        "other": hard["other_brains"],
        "d_prefer": d_pref,
        "d_prize": d_prize,
        "evolve_by": ev_by,
    }, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
