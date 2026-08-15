# -*- coding: utf-8 -*-
"""K-LOTTO4-DASH-RECORD — 4군 두뇌예측 적중이 대시보드에 회차마다 남는지. READ-ONLY."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.lotto4.v13_weights_v2 import V13_V2_PREDICT_ORDER, SETS_PER_BRAIN_V2, V13_V2_HIDDEN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KLOTTO4_DASH_RECORD.json"
OUT_MD = ROOT / "reports" / "20260815_KLOTTO4_DASH_RECORD.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto4.db"
NEED = len(V13_V2_PREDICT_ORDER) * SETS_PER_BRAIN_V2  # 7*5=35


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0] or 0)
    dmin = int(conn.execute("SELECT MIN(draw_no) FROM lotto_draws").fetchone()[0] or 0)
    n_draws = int(conn.execute("SELECT COUNT(*) FROM lotto_draws").fetchone()[0] or 0)
    pred_1237 = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions_army4 WHERE target_draw_no=1237"
        ).fetchone()[0]
    )
    brains = [
        str(r[0])
        for r in conn.execute(
            "SELECT DISTINCT brain_tag FROM lotto_predictions_army4 WHERE brain_tag LIKE 'v13_%' ORDER BY 1"
        )
    ]
    by_brain = {
        str(r["brain_tag"]): {
            "n": int(r["n"]),
            "scored": int(r["scored"]),
            "unscored": int(r["unscored"]),
            "draws": int(r["draws"]),
        }
        for r in conn.execute(
            """
            SELECT brain_tag,
                   COUNT(*) n,
                   SUM(CASE WHEN matched_count >= 0 THEN 1 ELSE 0 END) scored,
                   SUM(CASE WHEN matched_count < 0 THEN 1 ELSE 0 END) unscored,
                   COUNT(DISTINCT target_draw_no) draws
            FROM lotto_predictions_army4
            WHERE brain_tag LIKE 'v13_%'
            GROUP BY brain_tag
            """
        )
    }
    # 회차 커버: 당첨이 있는 회차에 예측이 있는가
    cover_rows = list(
        conn.execute(
            """
            SELECT d.draw_no,
                   COUNT(p.id) AS n_pred,
                   SUM(CASE WHEN p.matched_count >= 0 THEN 1 ELSE 0 END) AS n_scored,
                   SUM(CASE WHEN p.matched_count < 0 THEN 1 ELSE 0 END) AS n_unscored,
                   COUNT(DISTINCT p.brain_tag) AS n_brains
            FROM lotto_draws d
            LEFT JOIN lotto_predictions_army4 p
              ON p.target_draw_no = d.draw_no AND p.brain_tag LIKE 'v13_%'
            WHERE d.draw_no BETWEEN ? AND ?
            GROUP BY d.draw_no
            ORDER BY d.draw_no
            """,
            (max(1, dmax - 199), dmax),
        )
    )
    recent = [dict(r) for r in cover_rows]
    n_recent = len(recent)
    full = sum(1 for r in recent if int(r["n_pred"] or 0) >= NEED)
    some = sum(1 for r in recent if 0 < int(r["n_pred"] or 0) < NEED)
    none = sum(1 for r in recent if int(r["n_pred"] or 0) == 0)
    unscored_has_draw = sum(1 for r in recent if int(r["n_unscored"] or 0) > 0)
    missing_recent = [int(r["draw_no"]) for r in recent if int(r["n_pred"] or 0) == 0]
    thin_recent = [int(r["draw_no"]) for r in recent if 0 < int(r["n_pred"] or 0) < NEED]

    # 1100-1131 (화면 두뇌예측 스테퍼)
    ui = list(
        conn.execute(
            """
            SELECT d.draw_no, COUNT(p.id) n_pred,
                   SUM(CASE WHEN p.matched_count >= 0 THEN 1 ELSE 0 END) n_scored,
                   COUNT(DISTINCT p.brain_tag) n_brains
            FROM lotto_draws d
            LEFT JOIN lotto_predictions_army4 p
              ON p.target_draw_no = d.draw_no AND p.brain_tag LIKE 'v13_%'
            WHERE d.draw_no BETWEEN 1100 AND 1131
            GROUP BY d.draw_no ORDER BY d.draw_no
            """
        )
    )
    ui_full = sum(1 for r in ui if int(r["n_pred"] or 0) >= NEED)
    ui_none = sum(1 for r in ui if int(r["n_pred"] or 0) == 0)

    # 전구간 갭
    all_miss = [
        int(r[0])
        for r in conn.execute(
            """
            SELECT d.draw_no FROM lotto_draws d
            LEFT JOIN lotto_predictions_army4 p
              ON p.target_draw_no = d.draw_no AND p.brain_tag LIKE 'v13_%'
            GROUP BY d.draw_no
            HAVING COUNT(p.id) = 0
            ORDER BY d.draw_no
            """
        )
    ]
    # 당첨 있는데 미채점
    stale = [
        int(r[0])
        for r in conn.execute(
            """
            SELECT DISTINCT p.target_draw_no
            FROM lotto_predictions_army4 p
            JOIN lotto_draws d ON d.draw_no = p.target_draw_no
            WHERE p.brain_tag LIKE 'v13_%' AND p.matched_count < 0
            ORDER BY 1
            """
        )
    ]
    weights = [
        dict(r)
        for r in conn.execute(
            """
            SELECT brain_tag, current_weight, last_updated_draw
            FROM lotto_brain_weights_army4
            WHERE brain_tag LIKE 'v13_%'
            ORDER BY current_weight DESC
            """
        )
    ]
    w_max = max((int(w.get("last_updated_draw") or 0) for w in weights), default=0)
    # 대시보드 brain_power와 같은 집계
    power = [
        dict(r)
        for r in conn.execute(
            """
            SELECT brain_tag,
                   SUM(CASE WHEN matched_count=6 THEN 1 ELSE 0 END) r1,
                   SUM(CASE WHEN matched_count=5 AND bonus_matched=1 THEN 1 ELSE 0 END) r2,
                   SUM(CASE WHEN matched_count=5 AND IFNULL(bonus_matched,0)=0 THEN 1 ELSE 0 END) r3,
                   SUM(CASE WHEN matched_count=4 THEN 1 ELSE 0 END) r4,
                   SUM(CASE WHEN matched_count=3 THEN 1 ELSE 0 END) r5,
                   COUNT(*) n
            FROM lotto_predictions_army4
            WHERE brain_tag LIKE 'v13_%' AND matched_count >= 0
            GROUP BY brain_tag
            """
        )
    ]
    conn.close()

    auto = {
        "score_on_collect": True,
        "predict_on_collect": False,
        "predict_trigger": "두뇌 예측 실행 버튼 / API",
        "hidden_not_predicted": sorted(V13_V2_HIDDEN_BRAINS),
        "predict_brains": list(V13_V2_PREDICT_ORDER),
        "rows_per_draw_expected": NEED,
    }
    hard_ok = dmax == 1236 and pred_1237 == 0
    payload = {
        "id": "K-LOTTO4-DASH-RECORD",
        "as_of": _now(),
        "verdict": "READ_OK" if hard_ok else "READ_FAIL",
        "apply": False,
        "draws_max": dmax,
        "draws_min": dmin,
        "n_draws": n_draws,
        "pred_1237": pred_1237,
        "brains_in_pred": brains,
        "by_brain": by_brain,
        "recent200": {
            "lo": max(1, dmax - 199),
            "hi": dmax,
            "n": n_recent,
            "full35": full,
            "thin": some,
            "none": none,
            "unscored_draws": unscored_has_draw,
            "missing": missing_recent[:40],
            "thin_draws": thin_recent[:40],
        },
        "ui_1100_1131": {
            "n": len(ui),
            "full35": ui_full,
            "none": ui_none,
            "rows": [dict(r) for r in ui],
        },
        "all_miss_n": len(all_miss),
        "all_miss_head": all_miss[:20],
        "all_miss_tail": all_miss[-20:],
        "stale_unscored_with_draw": stale,
        "weights": weights,
        "weight_last_draw": w_max,
        "brain_power": power,
        "auto": auto,
        "hard_ok": hard_ok,
    }

    r200 = payload["recent200"]
    lines = [
        "# K-LOTTO4-DASH-RECORD",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=4군 두뇌예측 적중이 대시보드에 회차마다 자동 기록되는지 실측.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. draws MAX={dmax} · pred_1237={pred_1237}.",
        "",
        "## 0) 한 줄",
        "",
        "대시보드 숫자는 `lotto_predictions_army4` **이미 있는 행의 합**이다. "
        "당첨 수집 후 적중 칸(`matched_count`)은 **자동 갱신**된다. "
        "다만 **예측 자체는 매회 자동 생성이 아니다.** 「두뇌 예측 실행」을 누른 회차만 행이 생긴다. "
        f"최근200회 중 35장(7뇌×5) 가득 **{full}** · 없음 **{none}** · 미채점(당첨있는데 -1) **{len(stale)}**회.",
        "",
        "## 1) 자동 vs 수동",
        "",
        "| 단계 | 자동? | 트리거 |",
        "|------|-------|--------|",
        "| 당첨 수집 | 스케줄/fetch-latest | `collect_latest_forward` |",
        "| 적중 채점 | **예** | 수집 직후 `refresh_army4_predictions_for_draw` |",
        "| 예측 생성 | **아니오** | 화면 「두뇌 예측 실행」 |",
        "| 대시보드 표시 | 읽기 | `/dashboard-summary` 가 채점된 행을 합산 |",
        "",
        f"predict 루프 뇌={list(V13_V2_PREDICT_ORDER)} (회당 {NEED}행). "
        f"HIDDEN(예측 안 함)={sorted(V13_V2_HIDDEN_BRAINS)}. "
        "화면 순위 #2 `v13_cond_prob` 는 Hidden — 가중치 표에만 있을 수 있고 신규 예측은 안 쌓인다.",
        "",
        "## 2) 최근 200회 커버 (당첨 있는 회차)",
        "",
        f"| 가득({NEED}행) | 부족 | 예측0 | 미채점회 |",
        f"|---|---|---|---|",
        f"| {full} | {some} | {none} | {unscored_has_draw} |",
        "",
        f"예측0 회차(앞): {missing_recent[:25]}",
        f"부족 회차(앞): {thin_recent[:25]}",
        f"전구간 예측0: {len(all_miss)}회 · 끝={all_miss[-10:] if all_miss else []}",
        f"당첨있는데 미채점: {stale}",
        "",
        "## 3) 화면 1100–1131",
        "",
        f"32회 중 가득 {ui_full} · 예측0 {ui_none}.",
        "",
        "| 회 | 행 | 채점 | 뇌수 |",
        "|----|----|------|------|",
    ]
    for r in ui:
        lines.append(f"| {r['draw_no']} | {r['n_pred']} | {r['n_scored']} | {r['n_brains']} |")
    lines += [
        "",
        "## 4) 뇌별 예측 행",
        "",
        "| 뇌 | 행 | 채점 | 미채점 | 회차수 |",
        "|----|----|------|--------|--------|",
    ]
    for t in brains:
        b = by_brain[t]
        lines.append(f"| {t} | {b['n']} | {b['scored']} | {b['unscored']} | {b['draws']} |")
    lines += [
        "",
        "## 5) 대시보드 가중치 last_updated_draw",
        "",
        f"최대 last_updated_draw=**{w_max}** (당첨 MAX {dmax}). 가중치가 매회 안 따라가면 여기가 멈춘 것.",
        "",
        "| 뇌 | weight | last_updated_draw |",
        "|----|--------|-------------------|",
    ]
    for w in weights:
        lines.append(f"| {w['brain_tag']} | {w['current_weight']} | {w.get('last_updated_draw')} |")
    lines += [
        "",
        "## 6) 대시보드 적중 누적 (채점행 합 · 성적 클레임 아님)",
        "",
        "| 뇌 | n | 1등 | 2등 | 3등 | 4등 | 5등 |",
        "|----|---|-----|-----|-----|-----|-----|",
    ]
    for p in power:
        lines.append(
            f"| {p['brain_tag']} | {p['n']} | {p['r1']} | {p['r2']} | {p['r3']} | {p['r4']} | {p['r5']} |"
        )
    lines += [
        "",
        "## 7) 판정",
        "",
        "READ_OK. 「매회 자동으로 모두 기록」은 **반은 맞고 반은 아니다.** "
        "채점은 자동, 예측 생성은 수동. 예측 없는 회차는 대시보드 누적에 안 들어간다.",
        "코드/DB 쓰기 없음. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": payload["verdict"],
                "dmax": dmax,
                "recent_full": full,
                "recent_none": none,
                "stale": stale,
                "all_miss_n": len(all_miss),
                "ui_full": ui_full,
                "w_max": w_max,
                "pred_1237": pred_1237,
            },
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
