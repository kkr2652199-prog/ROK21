# -*- coding: utf-8 -*-
"""K-BT-ISSUE-PATH-METRIC — 강제BT 구간에서 발권5장 best를 병기 측정.

BTv5 pool/repack 등수 ≠ 양산 발권. 1137~1236 각 회차
run_coordinated_prediction → lotto_predictions 채점 → 해당 회차 행 삭제.

ge3/등수 모니터만 · 1237아님 · wire=False(측정·문서 패치).
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KBT_ISSUE_PATH_METRIC.json"
OUT_MD = ROOT / "reports" / "20260812_KBT_ISSUE_PATH_METRIC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
LO, HI = 1137, 1236


def _hits(nums: list[int], actual: set[int]) -> int:
    return len(set(nums) & actual)


def main() -> None:
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.tier_utils import score_predicted_set

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        draws = conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (LO, HI),
        ).fetchall()
        bt = {
            int(r["draw_no"]): (int(r["best_hits"]), int(r["best_tier"] or 0))
            for r in conn.execute(
                "SELECT d.draw_no,d.best_hits,d.best_tier "
                "FROM testlotto_backtest_draw_results d "
                "JOIN testlotto_backtest_runs r ON r.run_id=d.run_id "
                "ORDER BY r.run_id DESC"
            ).fetchall()
        }
    finally:
        conn.close()

    # bt dict may have duplicates from join — rebuild clean
    conn = get_lotto_db()
    try:
        run_id = conn.execute(
            "SELECT run_id FROM testlotto_backtest_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()[0]
        bt = {
            int(r[0]): (int(r[1]), int(r[2] or 0))
            for r in conn.execute(
                "SELECT draw_no,best_hits,best_tier FROM testlotto_backtest_draw_results "
                "WHERE run_id=?",
                (run_id,),
            ).fetchall()
        }
    finally:
        conn.close()

    per: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for i, row in enumerate(draws):
        dno = int(row["draw_no"] if hasattr(row, "keys") else row[0])
        actual = {int(row[f"num{k}"] if hasattr(row, "keys") else row[k]) for k in range(1, 7)}
        bonus = int((row["bonus"] if hasattr(row, "keys") else row[7]) or 0)
        out = run_coordinated_prediction(dno)
        wconn = get_lotto_db()
        try:
            preds = wconn.execute(
                "SELECT brain_tag,num1,num2,num3,num4,num5,num6 FROM lotto_predictions "
                "WHERE target_draw_no=?",
                (dno,),
            ).fetchall()
            wconn.execute("DELETE FROM lotto_predictions WHERE target_draw_no=?", (dno,))
            wconn.commit()
        finally:
            wconn.close()

        best_h = 0
        best_tier = 0
        by_brain: Counter = Counter()
        for pr in preds:
            tag = str(pr["brain_tag"] if hasattr(pr, "keys") else pr[0])
            nums = [int(pr[f"num{j}"] if hasattr(pr, "keys") else pr[j]) for j in range(1, 7)]
            by_brain[tag] += 1
            h = _hits(nums, actual)
            tr = score_predicted_set(nums, sorted(actual), bonus)
            tier = int(tr.get("tier_rank") or 0) if isinstance(tr, dict) else 0
            if h > best_h or (h == best_h and tier and (not best_tier or tier < best_tier)):
                best_h = h
                best_tier = tier
        bt_h, bt_t = bt.get(dno, (-1, 0))
        per.append(
            {
                "draw_no": dno,
                "issue_best_hits": best_h,
                "issue_best_tier": best_tier,
                "pool_path_best_hits": bt_h,
                "pool_path_best_tier": bt_t,
                "issued_n": sum(by_brain.values()),
                "issued_by_brain": dict(by_brain),
                "coord_error": out.get("error") if isinstance(out, dict) else None,
            }
        )
        if (i + 1) % 10 == 0:
            print(f"  issue {i+1}/{len(draws)} draw={dno} h={best_h}", flush=True)

    n = len(per)
    issue_ge3 = sum(1 for r in per if r["issue_best_hits"] >= 3)
    issue_ge4 = sum(1 for r in per if r["issue_best_hits"] >= 4)
    pool_ge3 = sum(1 for r in per if r["pool_path_best_hits"] >= 3)
    pool_ge4 = sum(1 for r in per if r["pool_path_best_hits"] >= 4)
    issue_mean = sum(r["issue_best_hits"] for r in per) / n if n else 0.0
    pool_mean = sum(r["pool_path_best_hits"] for r in per) / n if n else 0.0
    issue_tiers = Counter(r["issue_best_tier"] for r in per if r["issue_best_tier"])
    pool_tiers = Counter(r["pool_path_best_tier"] for r in per if r["pool_path_best_tier"])
    gap_ge3 = pool_ge3 - issue_ge3
    gap_ge4 = pool_ge4 - issue_ge4

    verdict = "METRIC_OK"
    if any(r.get("coord_error") for r in per) or any(r["issued_n"] != 5 for r in per):
        verdict = "METRIC_WARN"

    out = {
        "id": "K-BT-ISSUE-PATH-METRIC",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        "wire": False,
        "ge3_used_as_claim": False,
        "range": [LO, HI],
        "n": n,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "bt_run_id": int(run_id),
        "pool_path": {
            "mean_hits": round(pool_mean, 4),
            "ge3_count": pool_ge3,
            "ge4_count": pool_ge4,
            "tiers": {f"r{k}": int(v) for k, v in sorted(pool_tiers.items())},
            "note": "BTv5 best_of pool10+repack5×3",
        },
        "issue_path": {
            "mean_hits": round(issue_mean, 4),
            "ge3_count": issue_ge3,
            "ge4_count": issue_ge4,
            "tiers": {f"r{k}": int(v) for k, v in sorted(issue_tiers.items())},
            "note": "run_coordinated_prediction 발권5장",
        },
        "gap_pool_minus_issue": {"ge3": gap_ge3, "ge4": gap_ge4, "mean_hits": round(pool_mean - issue_mean, 4)},
        "frame": "양산前·1237아님·등수모니터·성적클레임금지·BT≠발권",
        "per_draw": per,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = "\n".join(
        [
            "# K-BT-ISSUE-PATH-METRIC",
            "",
            f"시각: {out['ts']} · wire=**False** · ge3미클레임 · **1237아님**",
            "",
            "## 판정",
            f"**{verdict}**",
            "",
            "## 요지",
            "- 목적: 강제BT **pool경로 등수**와 **발권5장 등수**를 같은 구간에 병기",
            f"- 구간 {LO}~{HI} n={n} · bt_run_id **{run_id}** · {out['elapsed_s']}s",
            "",
            "## 비교 (모니터만)",
            "| 경로 | mean_hits | ≥3 | ≥4 | tiers |",
            "|------|-----------|----|----|-------|",
            f"| pool/repack(BT) | **{out['pool_path']['mean_hits']}** | {pool_ge3} | {pool_ge4} | {out['pool_path']['tiers']} |",
            f"| **발권5장** | **{out['issue_path']['mean_hits']}** | {issue_ge3} | {issue_ge4} | {out['issue_path']['tiers']} |",
            f"| gap(pool−issue) | {out['gap_pool_minus_issue']['mean_hits']} | {gap_ge3} | {gap_ge4} | — |",
            "",
            "## 결론",
            "- 상위적중 튜닝의 **SSOT 지표 = 발권경로**(또는 prefer/prize).",
            "- pool경로 4·5등은 **장수효과**를 포함 → APPLY 근거로 쓰지 않음.",
            "",
            "## 근거",
            f"- `{OUT_JSON.as_posix()}`",
            f"- `{OUT_MD.as_posix()}`",
            "- 도구: `tools/_k_bt_issue_path_metric.py`",
            "",
        ]
    )
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print("pool", out["pool_path"])
    print("issue", out["issue_path"])
    print("gap", out["gap_pool_minus_issue"])
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
