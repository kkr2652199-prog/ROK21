# -*- coding: utf-8 -*-
"""K-TRANSITION-STEP2-VERIFY — transition_log 재검증 (wire 없음).

Usage:
  python tools/_k_transition_step2_verify.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_STEP2_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_STEP2_VERIFY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PRIOR = "docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json"
PRIOR_MEAN = 2.171806
COLLECT_MEAN_REF = 1.998236
EXPECTED_ROWS = 1134


def _conn():
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    return get_lotto_db()


def check_table(conn) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT draw_no, sim_k, hit_count, top15, next_actual FROM transition_log WHERE sim_k=2 ORDER BY draw_no"
    ).fetchall()
    n = len(rows)
    draw_nos = [int(r["draw_no"]) for r in rows]
    null_hit = sum(1 for r in rows if r["hit_count"] is None)
    null_top = sum(1 for r in rows if not r["top15"])
    dup = len(draw_nos) - len(set(draw_nos))
    # expected contiguous 101..1234
    expected = list(range(101, 1235))
    missing = sorted(set(expected) - set(draw_nos))
    extra = sorted(set(draw_nos) - set(expected))
    table_ok = (
        n == EXPECTED_ROWS
        and dup == 0
        and null_hit == 0
        and null_top == 0
        and not missing
        and not extra
    )
    return {
        "table_ok": table_ok,
        "total_rows": n,
        "expected_rows": EXPECTED_ROWS,
        "skipped_implied": EXPECTED_ROWS - n if n <= EXPECTED_ROWS else 0,
        "duplicate_draw_no": dup,
        "null_hit_count": null_hit,
        "null_top15": null_top,
        "missing_draw_nos_sample": missing[:10],
        "extra_draw_nos_sample": extra[:10],
        "rows": rows,
    }


def collect_stats(rows) -> dict[str, Any]:
    hits = [int(r["hit_count"]) for r in rows]
    dist = Counter(hits)
    mean_hit = float(np.mean(hits)) if hits else 0.0
    std_hit = float(np.std(hits, ddof=0)) if hits else 0.0
    hit_dist = {str(k): int(dist.get(k, 0)) for k in range(7)}
    within = abs(mean_hit - COLLECT_MEAN_REF) <= 0.05
    return {
        "mean_hit": round(mean_hit, 6),
        "std_hit": round(std_hit, 6),
        "hit_dist": hit_dist,
        "within_ref_band": within,
        "ref_mean": COLLECT_MEAN_REF,
    }


def full_recheck() -> dict[str, Any]:
    """FULL 동치: lotto_draws 재계산 (transition_log.hit는 N+1용이라 직접 사용 불가)."""
    from tools._k_transition_collect import full_style_recheck

    r = full_style_recheck(sim_k=2, lo=101, hi=1235)
    return {
        "mean_hit": r["mean_hit"],
        "delta": r["delta"],
        "match_prior_json": r["match_prior_json"],
        "n_valid": r["n_valid"],
        "note": (
            "hit@N · lotto_draws 재계산. "
            "transition_log.hit_count는 N→N+1이라 FULL 재현에 직접 쓰지 않음 (Cursor 커버)."
        ),
        "prior_mean": PRIOR_MEAN,
    }


def by_period(rows) -> dict[str, Any]:
    bands = {
        "early": (101, 480),
        "mid": (481, 857),
        "late": (858, 1234),
    }
    means: dict[str, float] = {}
    for name, (lo, hi) in bands.items():
        hs = [int(r["hit_count"]) for r in rows if lo <= int(r["draw_no"]) <= hi]
        means[name] = round(float(np.mean(hs)), 6) if hs else 0.0
    vals = list(means.values())
    gap = max(vals) - min(vals) if vals else 0.0
    stable = gap < 0.15
    return {
        "early": means["early"],
        "mid": means["mid"],
        "late": means["late"],
        "max_gap": round(gap, 6),
        "stable": stable,
        "n_early": sum(1 for r in rows if 101 <= int(r["draw_no"]) <= 480),
        "n_mid": sum(1 for r in rows if 481 <= int(r["draw_no"]) <= 857),
        "n_late": sum(1 for r in rows if 858 <= int(r["draw_no"]) <= 1234),
    }


def spot_check(rows) -> list[dict[str, Any]]:
    want = {1230, 1231, 1232, 1233, 1234}
    out = []
    by = {int(r["draw_no"]): r for r in rows}
    for dn in sorted(want):
        r = by.get(dn)
        if not r:
            out.append({"draw_no": dn, "top15": [], "hit_count": None, "missing": True})
            continue
        top15 = json.loads(r["top15"])
        out.append(
            {
                "draw_no": dn,
                "top15": top15,
                "hit_count": int(r["hit_count"]),
                "next_actual": json.loads(r["next_actual"]),
            }
        )
    return out


def verdict(
    table_ok: bool,
    collect: dict,
    full: dict,
    period: dict,
) -> str:
    c1 = table_ok
    c2 = bool(collect.get("within_ref_band"))
    c3 = bool(full.get("match_prior_json")) and abs(full["mean_hit"] - PRIOR_MEAN) <= 0.01
    c4 = bool(period.get("stable"))
    if not c1 or not c3:
        return "FAIL"
    ok123 = c1 and c2 and c3
    if ok123 and c4:
        return "PASS"
    # 1 of [1]-[3] fail already handled; if c2 fail or not stable → MARGINAL
    n_fail = sum(1 for x in (c1, c2, c3) if not x)
    if n_fail >= 1 or not c4:
        return "MARGINAL"
    return "PASS"


def write_md(p: dict[str, Any]) -> None:
    lines = [
        "# K-TRANSITION-STEP2-VERIFY — 수집 데이터 재검증 (2026-08-05)",
        "",
        "> **작성:** Cursor · wire=`False` · 발권/뇌 미접촉",
        "",
        f"- **판정:** `{p['verdict']}` · table_ok=`{p['table_ok']}`",
        f"- alignment: 지시서=STEP2 재검증 · 방향성 COLLECT→VERIFY → **일치**",
        "",
        "## [1] table",
        f"- rows={p['table']['total_rows']} · dup={p['table']['duplicate_draw_no']} · "
        f"missing={p['table']['missing_draw_nos_sample']}",
        "",
        "## [2] collect (N→N+1)",
        f"- mean={p['collect']['mean_hit']} · std={p['collect']['std_hit']} · "
        f"within_band={p['collect']['within_ref_band']}",
        f"- hit_dist={p['collect']['hit_dist']}",
        "",
        "## [3] FULL recheck (hit@N)",
        f"- mean={p['full_recheck']['mean_hit']} · delta={p['full_recheck']['delta']} · "
        f"match=**{p['full_recheck']['match_prior_json']}**",
        f"- note: {p['full_recheck']['note']}",
        "",
        "## [4] by_period",
        f"- {p['by_period']}",
        "",
        "## [5] spot_check 1230~1234",
    ]
    for s in p["spot_check"]:
        lines.append(
            f"- {s['draw_no']}: hit={s.get('hit_count')} top15=`{s.get('top15')}`"
        )
    lines += ["", f"- prior: `{p['prior']}`", f"- tool: `{p['tool']}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    conn = _conn()
    try:
        t = check_table(conn)
        rows = t["rows"]
        collect = collect_stats(rows)
        full = full_recheck()
        period = by_period(rows)
        spots = spot_check(rows)
        v = verdict(t["table_ok"], collect, full, period)
        table_meta = {k: t[k] for k in t if k != "rows"}

        payload = {
            "id": "K-TRANSITION-STEP2-VERIFY",
            "ts": datetime.now(timezone.utc).isoformat(),
            "verdict": v,
            "wire": False,
            "alignment_check": {
                "direction": "COLLECT_FIRST → STEP2 verify → STEP3 later",
                "instruction_match": True,
                "cursor_cover": [
                    "FULL recheck uses lotto_draws (not transition_log.hit_count)",
                    "FINDINGS.md HEAD-only via R37; no FINDINGS ID patch",
                ],
                "hard_stop": False,
            },
            "table_ok": t["table_ok"],
            "table": table_meta,
            "collect": collect,
            "full_recheck": full,
            "by_period": period,
            "spot_check": spots,
            "forbid": [
                "wire",
                "engine.py 수정",
                "auto-tune",
                "random.choices",
                "stat 즉시 교체",
                "발권 테이블 INSERT/UPDATE",
                "신호 과장 클레임",
            ],
            "pass": v == "PASS",
            "tool": "tools/_k_transition_step2_verify.py",
            "prior": PRIOR,
        }

        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_md(payload)
        print(
            json.dumps(
                {
                    "ok": True,
                    "verdict": v,
                    "table_ok": t["table_ok"],
                    "collect_mean": collect["mean_hit"],
                    "full_mean": full["mean_hit"],
                    "match": full["match_prior_json"],
                    "stable": period["stable"],
                    "period": {
                        "e": period["early"],
                        "m": period["mid"],
                        "l": period["late"],
                    },
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
