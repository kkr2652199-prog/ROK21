# -*- coding: utf-8 -*-
"""K-STAT-HOMEWORK-FILL — 회차 숙제 기록 채우기 (형 권장 ①).

확정 길:
  예측 = N 숙제 · 재료 = 1..(N-1) · 채점 = N 정답 · 깊은 패턴은 재료

하는 일 (회차마다):
  1) coordinator.run_coordinated_prediction(N)
     → lotto_predictions 기록 · 직전회 피드백(learn_state)
  2) engine.refresh_prediction_scores_for_target_draw(N)
     → matched_count / bonus_matched
  3) evolve_auto.predict_and_cache(N) + score_draw_from_cache(N)
     → pool_view_cache · evolve_log (몰아주기 분석 경로)

Usage
  python tools/_k_stat_homework_fill.py
  K_HF_LO=1216 K_HF_HI=1235 python tools/_k_stat_homework_fill.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FILL_ID = "K-STAT-HOMEWORK-FILL"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KSTAT_HOMEWORK_FILL.json"
OUT_MD = ROOT / "reports" / "20260808_KSTAT_HOMEWORK_FILL.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DEFAULT_LO = 1216


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def _max_draw() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    m = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()
    return m


def _census() -> dict[str, int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    tabs = [
        "lotto_predictions",
        "testlotto_brain_learn_state",
        "hit_warrant_log",
        "testlotto_evolve_log",
        "testlotto_pool_view_cache",
        "lotto_analysis",
    ]
    out = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tabs}
    # matched 채워진 예측
    out["predictions_scored"] = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE matched_count >= 0"
    ).fetchone()[0]
    out["predictions_stat"] = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE brain_tag='stat'"
    ).fetchone()[0]
    conn.close()
    return out


def _sample_stat_reasoning(draw_no: int) -> list[dict[str, Any]]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT id, num1,num2,num3,num4,num5,num6,
               matched_count, confidence, reasoning
        FROM lotto_predictions
        WHERE target_draw_no=? AND brain_tag='stat'
        ORDER BY id
        """,
        (draw_no,),
    ).fetchall()
    conn.close()
    out = []
    for i, r in enumerate(rows, 1):
        d = dict(r)
        out.append(
            {
                "set": i,
                "nums": [d[f"num{k}"] for k in range(1, 7)],
                "matched": d["matched_count"],
                "conf": d["confidence"],
                "reasoning": (d.get("reasoning") or "")[:220],
            }
        )
    return out


def _clear_range(lo: int, hi: int) -> dict[str, int]:
    """채우기 구간만 지운다 (원천 lotto_draws 보존)."""
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    deleted: dict[str, int] = {}
    for sql, key in [
        (
            "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            "lotto_predictions",
        ),
        (
            "DELETE FROM testlotto_pool_view_cache WHERE draw_no BETWEEN ? AND ?",
            "pool_view_cache",
        ),
        (
            "DELETE FROM testlotto_evolve_log WHERE draw_no BETWEEN ? AND ?",
            "evolve_log",
        ),
    ]:
        cur = conn.execute(sql, (lo, hi))
        deleted[key] = cur.rowcount
    # learn_state 는 회차 피드백 누적이라 구간 채우기 전 비움(3뇌)
    cur = conn.execute("DELETE FROM testlotto_brain_learn_state")
    deleted["learn_state"] = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def _count_brain(dno: int, tag: str) -> int:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    n = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=? AND brain_tag=?",
        (dno, tag),
    ).fetchone()[0]
    conn.close()
    return int(n)


def fill_one(dno: int) -> dict[str, Any]:
    """1) 발권경로 전체(쿼터 5장) 2) 과거학습 숙제 전용(stat 5장) 3) 채점 4) pool/evolve."""
    from app.testlotto.brains.coordinator import run_coordinated_prediction
    from app.testlotto.engine import refresh_prediction_scores_for_target_draw
    from app.testlotto.evolve_auto import predict_and_cache, score_draw_from_cache

    t0 = time.perf_counter()
    # 발권 경로: 쿼터 때문에 stat 이 0장이 될 수 있음 → 시스템 기록용
    live = run_coordinated_prediction(int(dno))
    live_ok = "error" not in live
    # 과거학습 숙제: brain_filter=stat 로 5장 강제 기록 (다른 뇌 행은 유지)
    stat = run_coordinated_prediction(int(dno), brain_filter=("stat",))
    stat_ok = "error" not in stat
    n_stat = _count_brain(dno, "stat")
    scored = bool(refresh_prediction_scores_for_target_draw(int(dno)))
    cache = predict_and_cache(int(dno))
    evol = (
        score_draw_from_cache(int(dno))
        if cache.get("ok")
        else {"ok": False, "error": "cache skip"}
    )
    return {
        "draw_no": dno,
        "predict_ok": live_ok and stat_ok and n_stat > 0,
        "predict_error": live.get("error") or stat.get("error"),
        "n_stat_sets": n_stat,
        "scores_refreshed": scored,
        "pool_cache_ok": bool(cache.get("ok")),
        "evolve_ok": bool(evol.get("ok")),
        "evolve_error": evol.get("error"),
        "sec": round(time.perf_counter() - t0, 2),
    }


def build_md(p: dict[str, Any]) -> str:
    L = [
        f"# {FILL_ID} — 회차 숙제 기록 채우기",
        "",
        f"- 생성 {p['generated_at']} · 회차 {p['lo']}~{p['hi']} · HEAD 참고용",
        f"- 경과 {p['elapsed_sec']}초 · 성공 {p['n_ok']}/{p['n_total']}",
        "",
        "## 0. 확정 길",
        "",
        "예측=N 숙제 · 재료=1..(N-1) · 채점=N 정답 · 깊은 패턴은 재료.",
        "빈 DB로 숫자 튜닝하지 않기 위해 **기록부터** 채웠다.",
        "",
        "## 1. 전후 행수",
        "",
        "|테이블|전|후|",
        "|---|---|---|",
    ]
    for k in sorted(p["before"]):
        L.append(f"|`{k}`|{p['before'][k]}|{p['after'].get(k, '?')}|")
    L += [
        "",
        "## 2. 회차별",
        "",
        "|회차|예측|stat장수|채점|pool캐시|evolve|초|",
        "|---|---|---|---|---|---|---|",
    ]
    for r in p["rows"]:
        L.append(
            f"|{r['draw_no']}|{'O' if r['predict_ok'] else 'X'}|"
            f"{r.get('n_stat_sets', 0)}|"
            f"{'O' if r['scores_refreshed'] else 'X'}|"
            f"{'O' if r['pool_cache_ok'] else 'X'}|"
            f"{'O' if r['evolve_ok'] else 'X'}|{r['sec']}|"
        )
    L += [
        "",
        f"## 3. 명분 샘플 (stat · {p['sample_draw']}회)",
        "",
    ]
    for s in p.get("sample_stat") or []:
        L.append(
            f"- set{s['set']} {s['nums']} · 적중 {s['matched']} · conf {s['conf']}"
        )
        L.append(f"  - {s['reasoning']}")
    L += [
        "",
        "## 4. 다음",
        "",
        "기록이 채워졌으므로 형이 한 회차 명분을 읽거나, 그다음 재료 튜닝(게이트)으로 갈 수 있다.",
        "",
    ]
    return "\n".join(L)


def main() -> None:
    hi = _env_int("K_HF_HI", 0) or _max_draw()
    lo = _env_int("K_HF_LO", DEFAULT_LO)
    print(f"[{FILL_ID}] {lo}~{hi}", flush=True)
    before = _census()
    print("before", before, flush=True)
    cleared = _clear_range(lo, hi)
    print("cleared", cleared, flush=True)

    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for dno in range(lo, hi + 1):
        try:
            r = fill_one(dno)
        except Exception as e:  # noqa: BLE001
            r = {
                "draw_no": dno,
                "predict_ok": False,
                "predict_error": str(e),
                "scores_refreshed": False,
                "pool_cache_ok": False,
                "evolve_ok": False,
                "evolve_error": str(e),
                "sec": 0.0,
                "n_stat_sets": 0,
            }
        rows.append(r)
        mark = "OK" if r["predict_ok"] and r["evolve_ok"] else "!!"
        print(
            f"  {dno} {mark} pred={r['predict_ok']} stat={r.get('n_stat_sets', 0)} "
            f"score={r['scores_refreshed']} cache={r['pool_cache_ok']} "
            f"evol={r['evolve_ok']} {r['sec']}s",
            flush=True,
        )

    after = _census()
    sample_draw = hi
    sample = _sample_stat_reasoning(sample_draw)
    n_ok = sum(1 for r in rows if r["predict_ok"] and r["evolve_ok"] and r["scores_refreshed"])
    payload = {
        "id": FILL_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lo": lo,
        "hi": hi,
        "elapsed_sec": round(time.perf_counter() - t0, 1),
        "n_total": len(rows),
        "n_ok": n_ok,
        "cleared": cleared,
        "before": before,
        "after": after,
        "rows": rows,
        "sample_draw": sample_draw,
        "sample_stat": sample,
        "policy": {
            "path": "N homework ← 1..N-1 · score with N actual",
            "includes": [
                "lotto_predictions",
                "learn_state via _auto_feedback",
                "matched_count refresh",
                "pool_view_cache",
                "evolve_log",
            ],
            "tuning": False,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(f"\nafter {after}")
    print(f"OK {n_ok}/{len(rows)} · {payload['elapsed_sec']}s")
    print(f"-> {OUT_JSON.relative_to(ROOT)}\n-> {OUT_MD.relative_to(ROOT)}")
    sys.exit(0 if n_ok == len(rows) else 1)


if __name__ == "__main__":
    main()
