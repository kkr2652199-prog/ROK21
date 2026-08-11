# -*- coding: utf-8 -*-
"""K-TIER45-SOURCE-AUDIT — BTv5 4등/5등 출처 분해 (READ-ONLY).

목적: 상위등수↑ 패치 전, r4/r5가 어느 뇌·pool/repack에서 났는지 실측.
주의: force BT best는 pool+repack 경로(장수 많음) · 발권5장과 동일하지 않음.
ge3/등수 = 모니터만 · 성적클레임 금지 · 1237아님.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KTIER45_SOURCE_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260812_KTIER45_SOURCE_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
BRAINS = ("stat", "markov", "review")


def _hits(nums: list[int], actual: set[int]) -> int:
    return len(set(nums) & actual)


def _load_actuals(conn: sqlite3.Connection) -> dict[int, tuple[set[int], int]]:
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
        "WHERE draw_no BETWEEN 1137 AND 1236"
    ).fetchall()
    out: dict[int, tuple[set[int], int]] = {}
    for r in rows:
        d = int(r[0])
        out[d] = ({int(r[i]) for i in range(1, 7)}, int(r[7] or 0))
    return out


def _best_in_sets(sets: list[dict], actual: set[int]) -> dict[str, Any]:
    best_h = -1
    best_set = None
    for s in sets or []:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        h = _hits(nums, actual)
        if h > best_h:
            best_h = h
            best_set = {"set_no": s.get("set_no"), "nums": nums, "hits": h, "meta": {
                k: s.get(k) for k in ("assemble", "source", "source_set_no", "kind") if k in s
            }}
    return {"best_hits": max(0, best_h), "best": best_set}


def audit() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        run = conn.execute(
            "SELECT run_id,n_draws,draw_start,draw_end,mean_hits,ge3_rate,"
            "tier_r1,tier_r2,tier_r3,tier_r4,tier_r5,survey_id,strategy_id "
            "FROM testlotto_backtest_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()
        if not run:
            raise SystemExit("no backtest run")
        run_id = int(run[0])
        bt_rows = conn.execute(
            "SELECT draw_no,best_hits,best_tier FROM testlotto_backtest_draw_results "
            "WHERE run_id=? ORDER BY draw_no",
            (run_id,),
        ).fetchall()
        actuals = _load_actuals(conn)
        cache = conn.execute(
            "SELECT draw_no,brain,pool_json,repack_json FROM testlotto_pool_view_cache "
            "WHERE draw_no BETWEEN 1137 AND 1236"
        ).fetchall()
    finally:
        conn.close()

    by_draw: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for dno, brain, pj, rj in cache:
        by_draw[int(dno)][str(brain)] = {
            "pool": json.loads(pj or "[]"),
            "repack": json.loads(rj or "[]"),
        }

    # 발권5장 경로 샘플: r4 회차만 coordinator → lotto_predictions 채점 후 해당 회차 행 삭제
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.models import get_lotto_db
    from app.testlotto.tier_utils import score_predicted_set

    r4_draws = [int(r[0]) for r in bt_rows if int(r[2]) == 4]
    r5_draws = [int(r[0]) for r in bt_rows if int(r[2]) == 5]

    per_r4: list[dict[str, Any]] = []
    brain_pool_r4 = Counter()
    brain_repack_r4 = Counter()
    pool_gt_repack_r4 = 0
    repack_eq_pool_r4 = 0
    issue_ge4 = 0
    issue_ge3 = 0

    for dno in r4_draws:
        actual, bonus = actuals[dno]
        row: dict[str, Any] = {"draw_no": dno, "actual": sorted(actual), "brains": {}}
        pool_best_h = -1
        repack_best_h = -1
        pool_winners: list[str] = []
        repack_winners: list[str] = []
        for b in BRAINS:
            blob = by_draw.get(dno, {}).get(b) or {}
            pb = _best_in_sets(blob.get("pool") or [], actual)
            rb = _best_in_sets(blob.get("repack") or [], actual)
            row["brains"][b] = {"pool": pb, "repack": rb}
            if pb["best_hits"] > pool_best_h:
                pool_best_h = pb["best_hits"]
                pool_winners = [b]
            elif pb["best_hits"] == pool_best_h:
                pool_winners.append(b)
            if rb["best_hits"] > repack_best_h:
                repack_best_h = rb["best_hits"]
                repack_winners = [b]
            elif rb["best_hits"] == repack_best_h:
                repack_winners.append(b)
        for b in pool_winners:
            if pool_best_h >= 4:
                brain_pool_r4[b] += 1
        for b in repack_winners:
            if repack_best_h >= 4:
                brain_repack_r4[b] += 1
        if pool_best_h > repack_best_h:
            pool_gt_repack_r4 += 1
        if pool_best_h == repack_best_h:
            repack_eq_pool_r4 += 1
        row["pool_best_hits"] = pool_best_h
        row["repack_best_hits"] = repack_best_h
        row["pool_winners"] = pool_winners
        row["repack_winners"] = repack_winners

        out = run_coordinated_prediction(dno)
        wconn = get_lotto_db()
        try:
            pred_rows = wconn.execute(
                "SELECT brain_tag,num1,num2,num3,num4,num5,num6 FROM lotto_predictions "
                "WHERE target_draw_no=?",
                (dno,),
            ).fetchall()
        finally:
            wconn.close()
        best_issue = 0
        issue_detail = []
        for pr in pred_rows:
            tag = str(pr["brain_tag"] if hasattr(pr, "keys") else pr[0])
            nums = [int(pr[f"num{i}"] if hasattr(pr, "keys") else pr[i]) for i in range(1, 7)]
            h = _hits(nums, actual)
            tr = score_predicted_set(nums, sorted(actual), bonus)
            tier = int(tr.get("tier_rank") or 0) if isinstance(tr, dict) else 0
            issue_detail.append({"brain": tag, "nums": nums, "hits": h, "tier": tier})
            best_issue = max(best_issue, h)
        row["issue_best_hits"] = best_issue
        row["issue"] = issue_detail
        row["coord_error"] = out.get("error") if isinstance(out, dict) else None
        if best_issue >= 4:
            issue_ge4 += 1
        if best_issue >= 3:
            issue_ge3 += 1
        # 로컬 오염 최소화: 감사 대상 회차 예측행 삭제(draws·BT·pool캐시 보존)
        dconn = get_lotto_db()
        try:
            dconn.execute("DELETE FROM lotto_predictions WHERE target_draw_no=?", (dno,))
            dconn.commit()
        finally:
            dconn.close()
        per_r4.append(row)

    # r5 집계(발권 재실행 없이 캐시만)
    brain_pool_r5 = Counter()
    brain_repack_r5 = Counter()
    pool_gt_repack_r5 = 0
    hits_hist = Counter()
    for dno in r5_draws:
        actual, _ = actuals[dno]
        pool_best_h = -1
        repack_best_h = -1
        pool_winners: list[str] = []
        repack_winners: list[str] = []
        for b in BRAINS:
            blob = by_draw.get(dno, {}).get(b) or {}
            pb = _best_in_sets(blob.get("pool") or [], actual)
            rb = _best_in_sets(blob.get("repack") or [], actual)
            if pb["best_hits"] > pool_best_h:
                pool_best_h = pb["best_hits"]
                pool_winners = [b]
            elif pb["best_hits"] == pool_best_h:
                pool_winners.append(b)
            if rb["best_hits"] > repack_best_h:
                repack_best_h = rb["best_hits"]
                repack_winners = [b]
            elif rb["best_hits"] == repack_best_h:
                repack_winners.append(b)
        for b in pool_winners:
            if pool_best_h >= 3:
                brain_pool_r5[b] += 1
        for b in repack_winners:
            if repack_best_h >= 3:
                brain_repack_r5[b] += 1
        if pool_best_h > repack_best_h:
            pool_gt_repack_r5 += 1
        hits_hist[(pool_best_h, repack_best_h)] += 1

    # 전구간: pool best>=4 인데 repack best<4 손실
    loss_ge4 = 0
    loss_ge3 = 0
    n_ok = 0
    for dno, bh, bt in bt_rows:
        dno = int(dno)
        actual, _ = actuals[dno]
        pool_best_h = max(
            (_best_in_sets((by_draw.get(dno, {}).get(b) or {}).get("pool") or [], actual)["best_hits"]
             for b in BRAINS),
            default=0,
        )
        repack_best_h = max(
            (_best_in_sets((by_draw.get(dno, {}).get(b) or {}).get("repack") or [], actual)["best_hits"]
             for b in BRAINS),
            default=0,
        )
        n_ok += 1
        if pool_best_h >= 4 and repack_best_h < 4:
            loss_ge4 += 1
        if pool_best_h >= 3 and repack_best_h < 3:
            loss_ge3 += 1

    verdict = "AUDIT_OK"
    # 핵심 결론 플래그
    flags = {
        "bt_best_is_pool_repack_path": True,
        "issue_path_r4_ge4_count": issue_ge4,
        "issue_path_r4_sample_n": len(r4_draws),
        "pool_ge4_lost_in_repack": loss_ge4,
        "pool_ge3_lost_in_repack": loss_ge3,
    }
    if issue_ge4 == 0 and len(r4_draws) > 0:
        flags["note"] = "UI/BT 4등이 발권5장 경로에서는 재현되지 않을 수 있음(장수효과)"
    if loss_ge4 > 0:
        flags["next_patch_hint"] = "pool→repack 보존(상위 hit 손실) 우선 후보"

    out = {
        "id": "K-TIER45-SOURCE-AUDIT",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        "wire": False,
        "ge3_used_as_claim": False,
        "run": {
            "run_id": run_id,
            "n": int(run[1]),
            "range": [int(run[2]), int(run[3])],
            "mean_hits": run[4],
            "ge3_rate": run[5],
            "tiers": {"r1": run[6], "r2": run[7], "r3": run[8], "r4": run[9], "r5": run[10]},
            "survey_id": run[11],
            "strategy_id": run[12],
        },
        "r4": {
            "draws": r4_draws,
            "brain_pool_winners": dict(brain_pool_r4),
            "brain_repack_winners": dict(brain_repack_r4),
            "pool_gt_repack": pool_gt_repack_r4,
            "repack_eq_pool": repack_eq_pool_r4,
            "issue_best_ge4": issue_ge4,
            "issue_best_ge3": issue_ge3,
            "detail": per_r4,
        },
        "r5": {
            "n": len(r5_draws),
            "brain_pool_winners": dict(brain_pool_r5),
            "brain_repack_winners": dict(brain_repack_r5),
            "pool_gt_repack": pool_gt_repack_r5,
            "pool_vs_repack_hits_hist_top": {
                f"pool{a}_repack{b}": n for (a, b), n in hits_hist.most_common(8)
            },
        },
        "all100": {
            "n": n_ok,
            "pool_ge4_lost_in_repack": loss_ge4,
            "pool_ge3_lost_in_repack": loss_ge3,
        },
        "flags": flags,
        "frame": "양산前·1237아님·등수모니터·성적클레임금지",
    }
    return out


def write_md(d: dict[str, Any]) -> str:
    r4 = d["r4"]
    lines = [
        "# K-TIER45-SOURCE-AUDIT",
        "",
        f"시각: {d['ts']} · **READ-ONLY** · wire=**False** · ge3미클레임 · **1237아님**",
        "",
        "## 판정",
        f"**{d['verdict']}**",
        "",
        "## 전제 (중요)",
        "- BTv5 `best_hits/tier` 는 **pool10+repack5 ×3뇌** 경로의 최고치(장수 많음).",
        "- **발권 5장** 경로와 동일하지 않음 → 4등 관측 ≠ 양산 발권 4등.",
        "",
        "## BTv5 요약",
        f"- run_id **{d['run']['run_id']}** · mean_hits **{d['run']['mean_hits']}**(모니터)",
        f"- tiers r1~r5 = {d['run']['tiers']}",
        "",
        "## 4등(r4) 분해",
        f"- 회차: `{r4['draws']}`",
        f"- pool≥4 기여뇌: `{r4['brain_pool_winners']}`",
        f"- repack≥4 기여뇌: `{r4['brain_repack_winners']}`",
        f"- pool>repack(hit): **{r4['pool_gt_repack']}**/4 · 동률: {r4['repack_eq_pool']}/4",
        f"- 발권5장 재실행 best≥4: **{r4['issue_best_ge4']}**/4 · best≥3: {r4['issue_best_ge3']}/4",
        "",
        "## 5등(r5) 분해(캐시)",
        f"- n={d['r5']['n']} · pool≥3 기여뇌 `{d['r5']['brain_pool_winners']}` · "
        f"repack≥3 `{d['r5']['brain_repack_winners']}` · pool>repack **{d['r5']['pool_gt_repack']}**",
        "",
        "## 전구간 손실",
        f"- pool≥4 & repack<4: **{d['all100']['pool_ge4_lost_in_repack']}**/100",
        f"- pool≥3 & repack<3: **{d['all100']['pool_ge3_lost_in_repack']}**/100",
        "",
        "## flags",
        "```json",
        json.dumps(d["flags"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## 다음(리스트① 완료 → ②)",
        "- 발권경로에서 r4가 안 나오면: **장수효과 정정 문서화** + 상위적중 목표를 prefer/prize·pool보존으로 재정의",
        "- pool≥4 손실>0 이면: **repack 보존 패치**가 다음 코드 후보",
        "",
        "## 근거",
        f"- `{OUT_JSON.as_posix()}`",
        f"- `{OUT_MD.as_posix()}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    d = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(d)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", d["verdict"])
    print("r4", d["r4"]["draws"])
    print("pool_winners", d["r4"]["brain_pool_winners"])
    print("repack_winners", d["r4"]["brain_repack_winners"])
    print("issue_ge4", d["r4"]["issue_best_ge4"], "/", len(d["r4"]["draws"]))
    print("loss_ge4", d["all100"]["pool_ge4_lost_in_repack"], "loss_ge3", d["all100"]["pool_ge3_lost_in_repack"])
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
