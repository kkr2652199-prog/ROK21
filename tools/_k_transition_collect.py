# -*- coding: utf-8 -*-
"""K-TRANSITION-COLLECT-DESIGN — transition_log 수집 (wire/coordinator 미접촉).

Usage:
  python tools/_k_transition_collect.py --ensure-table
  python tools/_k_transition_collect.py --backfill
  python tools/_k_transition_collect.py --collect-latest
  python tools/_k_transition_collect.py --verify
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_COLLECT_DESIGN.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_COLLECT_DESIGN.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

PRIOR_MEAN = 2.171806
PRIOR_DELTA = 0.171806
BASELINE = 2.0
ROLL_START = 101
TOP_M = 15
# FULL 재현용 (hit@N · next-of-similar must be before N)
FULL_MIN_SIMILAR = 10


def _conn():
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    return get_lotto_db()


def ensure_table(conn=None) -> None:
    own = conn is None
    if own:
        conn = _conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS transition_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_no       INTEGER NOT NULL,
            anchor_nums   TEXT NOT NULL,
            similar_count INTEGER NOT NULL,
            sim_k         INTEGER NOT NULL,
            freq_table    TEXT NOT NULL,
            top15         TEXT NOT NULL,
            next_actual   TEXT NOT NULL,
            hit_count     INTEGER NOT NULL,
            created_at    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_transition_draw
            ON transition_log(draw_no);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transition_draw_simk
            ON transition_log(draw_no, sim_k);
        """
    )
    conn.commit()
    if own:
        conn.close()


def load_draws(conn) -> dict[int, list[int]]:
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws ORDER BY draw_no
        """
    ).fetchall()
    out: dict[int, list[int]] = {}
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        out[int(d["draw_no"])] = nums
    return out


def _masks(draws_by_no: dict[int, list[int]], max_no: int) -> np.ndarray:
    masks = np.zeros(max_no, dtype=np.uint64)
    for dn, nums in draws_by_no.items():
        if dn < 1 or dn > max_no:
            continue
        m = np.uint64(0)
        for x in nums:
            m |= np.uint64(1) << np.uint64(x - 1)
        masks[dn - 1] = m
    return masks


def _popcount_and(past: np.ndarray, target: np.uint64) -> np.ndarray:
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(past & target)
    return np.array(
        [int(bin(int(past[j] & target)).count("1")) for j in range(len(past))],
        dtype=np.int8,
    )


def compute_row(
    draws_by_no: dict[int, list[int]],
    masks: np.ndarray,
    draw_no: int,
    sim_k: int = 2,
) -> dict[str, Any] | None:
    """Anchor=N → similar in 1..N-1 → freq of (similar+1) → hit vs N+1."""
    if draw_no not in draws_by_no:
        return None
    next_no = draw_no + 1
    if next_no not in draws_by_no:
        return None
    if draw_no < 2:
        return None

    ni = draw_no - 1
    target = masks[ni]
    past = masks[:ni]
    commons = _popcount_and(past, target)
    cand = np.flatnonzero(commons >= sim_k)
    n_sim = int(cand.size)

    freq = np.zeros(45, dtype=np.int32)
    for j in cand:
        nxt_idx = int(j) + 1  # draw_no j+2? j is 0-based index of draw j+1; next index j+1 = draw j+2
        # j = index of similar draw (draw_no = j+1). Next draw index = j+1 (draw_no = j+2).
        # Max j = ni-1 → next index = ni = draw_no N. OK.
        nxt_nums = draws_by_no.get(j + 2)  # draw_no of next = (j+1)+1 = j+2
        if nxt_nums is None:
            continue
        for x in nxt_nums:
            freq[x - 1] += 1

    order = np.lexsort((np.arange(45), -freq))
    top15 = [int(i + 1) for i in order[:TOP_M]]
    next_actual = draws_by_no[next_no]
    hit = len(set(top15) & set(next_actual))
    freq_table = {str(i + 1): int(freq[i]) for i in range(45)}

    return {
        "draw_no": draw_no,
        "anchor_nums": draws_by_no[draw_no],
        "similar_count": n_sim,
        "sim_k": sim_k,
        "freq_table": freq_table,
        "top15": top15,
        "next_actual": next_actual,
        "hit_count": hit,
    }


def compute_row_full_style(
    draws_by_no: dict[int, list[int]],
    masks: np.ndarray,
    draw_no: int,
    sim_k: int = 2,
    min_similar: int = FULL_MIN_SIMILAR,
) -> dict[str, Any] | None:
    """K-TRANSITION-FULL 동치: hit vs N · similar next must be before N."""
    if draw_no not in draws_by_no or draw_no < 2:
        return None
    ni = draw_no - 1
    target = masks[ni]
    past = masks[:ni]
    commons = _popcount_and(past, target)
    # j in 0..ni-2 so next index j+1 <= ni-1
    if ni < 2:
        return None
    cand = np.flatnonzero(commons[: ni - 1] >= sim_k)
    n_sim = int(cand.size)
    if n_sim < min_similar:
        return None
    freq = np.zeros(45, dtype=np.int32)
    for j in cand:
        nxt_nums = draws_by_no.get(int(j) + 2)
        if not nxt_nums:
            continue
        for x in nxt_nums:
            freq[x - 1] += 1
    order = np.lexsort((np.arange(45), -freq))
    top15 = [int(i + 1) for i in order[:TOP_M]]
    hit = len(set(top15) & set(draws_by_no[draw_no]))
    return {
        "draw_no": draw_no,
        "similar_count": n_sim,
        "hit_count": hit,
        "top15": top15,
    }


def row_exists(conn, draw_no: int, sim_k: int) -> bool:
    r = conn.execute(
        "SELECT 1 FROM transition_log WHERE draw_no=? AND sim_k=? LIMIT 1",
        (draw_no, sim_k),
    ).fetchone()
    return r is not None


def insert_row(conn, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO transition_log (
            draw_no, anchor_nums, similar_count, sim_k,
            freq_table, top15, next_actual, hit_count, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            row["draw_no"],
            json.dumps(row["anchor_nums"], ensure_ascii=False),
            row["similar_count"],
            row["sim_k"],
            json.dumps(row["freq_table"], ensure_ascii=False),
            json.dumps(row["top15"], ensure_ascii=False),
            json.dumps(row["next_actual"], ensure_ascii=False),
            row["hit_count"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def build_transition_row(draw_no: int, sim_k: int = 2) -> dict[str, Any]:
    """Build + INSERT one row. Skip if exists or missing next."""
    conn = _conn()
    try:
        ensure_table(conn)
        if row_exists(conn, draw_no, sim_k):
            return {"ok": True, "skipped": True, "draw_no": draw_no, "reason": "exists"}
        draws = load_draws(conn)
        if not draws:
            return {"ok": False, "error": "no draws"}
        max_no = max(draws)
        masks = _masks(draws, max_no)
        row = compute_row(draws, masks, draw_no, sim_k)
        if row is None:
            return {
                "ok": True,
                "skipped": True,
                "draw_no": draw_no,
                "reason": "no_next_or_missing",
            }
        insert_row(conn, row)
        # HIT-WARRANT 학습로그 (발권 미접촉)
        try:
            from app.testlotto.hit_warrant import label_pair, upsert_hit_warrant_log

            cat = label_pair(row["anchor_nums"], row["next_actual"], row["top15"])
            upsert_hit_warrant_log(
                int(row["draw_no"]) + 1,
                int(row["draw_no"]),
                cat,
                sim_k=sim_k,
                conn=conn,
            )
        except Exception:
            pass
        conn.commit()
        return {
            "ok": True,
            "skipped": False,
            "draw_no": draw_no,
            "similar_count": row["similar_count"],
            "hit_count": row["hit_count"],
            "top15": row["top15"],
        }
    finally:
        conn.close()


def backfill_all(sim_k: int = 2, lo: int = ROLL_START, hi: int = 1234) -> dict[str, Any]:
    conn = _conn()
    try:
        ensure_table(conn)
        draws = load_draws(conn)
        max_no = max(draws) if draws else 0
        masks = _masks(draws, max_no)
        inserted = 0
        skipped = 0
        hits: list[int] = []
        for dn in range(lo, hi + 1):
            if row_exists(conn, dn, sim_k):
                skipped += 1
                r = conn.execute(
                    "SELECT hit_count FROM transition_log WHERE draw_no=? AND sim_k=?",
                    (dn, sim_k),
                ).fetchone()
                if r:
                    hits.append(int(r["hit_count"]))
                continue
            row = compute_row(draws, masks, dn, sim_k)
            if row is None:
                skipped += 1
                continue
            insert_row(conn, row)
            inserted += 1
            hits.append(row["hit_count"])
            if inserted % 200 == 0:
                conn.commit()
                print(f"[backfill] inserted={inserted} at draw={dn}", flush=True)
        conn.commit()
        mean_hit = float(np.mean(hits)) if hits else 0.0
        return {
            "draw_range": [lo, hi],
            "total_inserted": inserted,
            "total_skipped": skipped,
            "n_rows_scored": len(hits),
            "mean_hit": round(mean_hit, 6),
            "delta": round(mean_hit - BASELINE, 6),
            "sim_k": sim_k,
        }
    finally:
        conn.close()


def collect_latest(sim_k: int = 2) -> dict[str, Any]:
    conn = _conn()
    try:
        ensure_table(conn)
        r = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
        latest = int(r["m"] or 0)
        # Prefer latest that has next_actual; else latest-1
        r2 = conn.execute(
            "SELECT MAX(draw_no) AS m FROM lotto_draws WHERE draw_no < ?",
            (latest,),
        ).fetchone()
        # If latest has no next, build for latest-1
        draws = load_draws(conn)
        target = latest if (latest + 1) in draws else latest - 1
        if target < ROLL_START:
            return {"ok": True, "skipped": True, "reason": "below_roll_start", "latest": latest}
    finally:
        conn.close()
    return build_transition_row(target, sim_k=sim_k)


def verify_query(sim_k: int = 2) -> dict[str, Any]:
    conn = _conn()
    try:
        ensure_table(conn)
        r = conn.execute(
            """
            SELECT
              COUNT(*) as total_rows,
              AVG(hit_count) as mean_hit,
              AVG(hit_count) - 2.0 as delta,
              SUM(CASE WHEN hit_count >= 3 THEN 1 ELSE 0 END) as hit_ge3_count
            FROM transition_log WHERE sim_k=?
            """,
            (sim_k,),
        ).fetchone()
        mean_hit = float(r["mean_hit"] or 0.0)
        delta = float(r["delta"] or 0.0)
        return {
            "total_rows": int(r["total_rows"] or 0),
            "mean_hit": round(mean_hit, 6),
            "delta": round(delta, 6),
            "hit_ge3_count": int(r["hit_ge3_count"] or 0),
        }
    finally:
        conn.close()


def full_style_recheck(sim_k: int = 2, lo: int = 101, hi: int = 1235) -> dict[str, Any]:
    """Reproduce K-TRANSITION-FULL sim_k2 mean without writing."""
    conn = _conn()
    try:
        draws = load_draws(conn)
        max_no = max(draws)
        masks = _masks(draws, max_no)
        hits: list[int] = []
        skipped = 0
        for dn in range(lo, hi + 1):
            row = compute_row_full_style(draws, masks, dn, sim_k=sim_k)
            if row is None:
                skipped += 1
                continue
            hits.append(row["hit_count"])
        mean_hit = float(np.mean(hits)) if hits else 0.0
        delta = mean_hit - BASELINE
        match = abs(mean_hit - PRIOR_MEAN) < 0.005
        return {
            "draw_range": [lo, hi],
            "n_valid": len(hits),
            "n_skipped": skipped,
            "mean_hit": round(mean_hit, 6),
            "delta": round(delta, 6),
            "prior_mean": PRIOR_MEAN,
            "prior_delta": PRIOR_DELTA,
            "match_prior_json": match,
            "note": "hit@N · similar next before N · min_similar=10 (FULL 동치)",
        }
    finally:
        conn.close()


def write_artifacts(
    backfill: dict[str, Any],
    verify: dict[str, Any],
    full_chk: dict[str, Any],
    hook_registered: bool,
) -> dict[str, Any]:
    # collect metric ≠ FULL metric (N+1 vs N) — document honestly
    match_collect_to_prior = abs(verify["mean_hit"] - PRIOR_MEAN) < 0.02
    verdict = "PASS" if (
        verify["total_rows"] > 0
        and full_chk.get("match_prior_json")
        and hook_registered
    ) else "FAIL"

    payload = {
        "id": "K-TRANSITION-COLLECT-DESIGN",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "wire": False,
        "table_created": True,
        "table_name": "transition_log",
        "db": "data/lotto_testlotto.db",
        "metric_note": (
            "transition_log.hit_count = |top15 ∩ D_{N+1}| (수집·학습용). "
            "K-TRANSITION-FULL mean 2.172 = |top15 ∩ D_N| (FULL 동치 재현은 full_style_recheck)."
        ),
        "backfill": {
            "draw_range": backfill["draw_range"],
            "total_inserted": backfill["total_inserted"],
            "total_skipped": backfill["total_skipped"],
            "sim_k2": {
                "mean_hit": verify["mean_hit"],
                "delta": verify["delta"],
                "hit_ge3_count": verify["hit_ge3_count"],
                "total_rows": verify["total_rows"],
                "match_prior_json": match_collect_to_prior,
                "match_prior_note": (
                    "collect(N→N+1) vs FULL(hit@N) 지표 상이 — "
                    f"abs(mean-prior)<0.02 → {match_collect_to_prior}"
                ),
            },
        },
        "full_style_recheck": full_chk,
        "hook_registered": hook_registered,
        "hook_file": ".cursor/hooks/transition_collect_hook.py",
        "next_step": "STEP2 — 수집 데이터 재검증 (데이터 쌓인 후)",
        "forbid": [
            "random.choices",
            "engine.py",
            "auto-tune",
            "wire",
            "coordinator 접촉",
            "기존 발권 테이블 수정",
            "신호 과장",
        ],
        "pass": verdict == "PASS",
        "tool": "tools/_k_transition_collect.py",
        "prior": "docs/benchmarks/20260805_KTRANSITION_FULL.json",
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# K-TRANSITION-COLLECT-DESIGN — transition_log 수집 구조 (2026-08-05)",
        "",
        "> **작성:** Cursor · wire=`False` · coordinator/발권 **미접촉**",
        "",
        f"- **판정:** `{verdict}` · table=`transition_log`",
        f"- backfill range: `{backfill['draw_range']}` · "
        f"inserted={backfill['total_inserted']} · skipped={backfill['total_skipped']}",
        "",
        "## collect 검증 (hit vs N+1)",
        f"- total_rows={verify['total_rows']} · mean_hit={verify['mean_hit']} · "
        f"delta={verify['delta']} · hit_ge3={verify['hit_ge3_count']}",
        f"- match_prior_json(collect≈FULL): **{match_collect_to_prior}** "
        f"(지표 상이 시 False 정상)",
        "",
        "## FULL 동치 재현 (hit vs N)",
        f"- mean_hit={full_chk['mean_hit']} · delta={full_chk['delta']} · "
        f"match_prior=**{full_chk['match_prior_json']}** · n={full_chk['n_valid']}",
        "",
        f"- hook_registered: **{hook_registered}**",
        f"- next_step: {payload['next_step']}",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensure-table", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--collect-latest", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--write-artifacts", action="store_true")
    ap.add_argument("--sim-k", type=int, default=2)
    ap.add_argument("--hook-registered", action="store_true", default=False)
    args = ap.parse_args()

    if args.ensure_table:
        ensure_table()
        print(json.dumps({"ok": True, "table": "transition_log"}), flush=True)

    if args.collect_latest:
        print(json.dumps(collect_latest(args.sim_k), ensure_ascii=False), flush=True)

    backfill_stat = None
    if args.backfill:
        print("[backfill] start", flush=True)
        backfill_stat = backfill_all(sim_k=args.sim_k)
        print(json.dumps({"backfill": backfill_stat}, ensure_ascii=False), flush=True)

    if args.verify or args.write_artifacts or args.backfill:
        v = verify_query(args.sim_k)
        fchk = full_style_recheck(args.sim_k)
        print(json.dumps({"verify": v, "full_style_recheck": fchk}, ensure_ascii=False), flush=True)
        if args.write_artifacts or args.backfill:
            if backfill_stat is None:
                backfill_stat = {
                    "draw_range": [ROLL_START, 1234],
                    "total_inserted": 0,
                    "total_skipped": v["total_rows"],
                }
            payload = write_artifacts(
                backfill_stat, v, fchk, hook_registered=args.hook_registered
            )
            print(json.dumps({"artifacts": {"verdict": payload["verdict"], "pass": payload["pass"]}}, ensure_ascii=False), flush=True)

    if not any(
        [args.ensure_table, args.backfill, args.collect_latest, args.verify, args.write_artifacts]
    ):
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
