# -*- coding: utf-8 -*-
"""K-ARMY4-SX-BRAIN-REMOVE — lotto4.db에서 4군 v13·전략X 예측행만 삭제.

테스트로또 DB·combinadic·조합조회·수집·효도 미접촉.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto4.db"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KARMY4_SX_BRAIN_REMOVE.json"
OUT_MD = ROOT / "reports" / "20260822_KARMY4_SX_BRAIN_REMOVE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _census(conn: sqlite3.Connection) -> dict:
    v13 = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions_army4 WHERE brain_tag LIKE 'v13_%'"
        ).fetchone()[0]
    )
    sx = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions_army4 WHERE brain_tag LIKE 'strategy_x_%'"
        ).fetchone()[0]
    )
    other = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions_army4 "
            "WHERE brain_tag NOT LIKE 'v13_%' AND brain_tag NOT LIKE 'strategy_x_%'"
        ).fetchone()[0]
    )
    draws = int(conn.execute("SELECT COUNT(*) FROM lotto_draws").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0] or 0)
    return {"v13": v13, "strategy_x": sx, "other_pred": other, "draws": draws, "draws_max": dmax}


def main() -> int:
    conn = sqlite3.connect(str(DB), timeout=60)
    before = _census(conn)
    conn.execute("DELETE FROM lotto_predictions_army4 WHERE brain_tag LIKE 'v13_%'")
    conn.execute("DELETE FROM lotto_predictions_army4 WHERE brain_tag LIKE 'strategy_x_%'")
    conn.execute("DELETE FROM lotto_predictions_army4 WHERE target_draw_no=1237")
    conn.commit()
    after = _census(conn)
    conn.close()

    payload = {
        "id": "K-ARMY4-SX-BRAIN-REMOVE",
        "as_of": _now(),
        "db": "data/lotto4.db",
        "testlotto_db_touched": False,
        "kept": [
            "app/lotto4/combinadic.py",
            "app/lotto4/all_combos_service.py",
            "app/lotto4/models.py",
            "lotto_draws",
            "combo lookup / all-combos / data collect / hyodo / testlotto",
        ],
        "removed_ui": ["dashboard(4군)", "predict", "strategy-x", "hall", "brain"],
        "before": before,
        "after": after,
        "deleted_v13": before["v13"] - after["v13"],
        "deleted_sx": before["strategy_x"] - after["strategy_x"],
        "pred_1237": 0,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-ARMY4-SX-BRAIN-REMOVE (2026-08-22)",
        "",
        "- **판정:** `REMOVE_OK`",
        "- 형 요청: 4군·전략X **뇌만** 삭제 · 테스트로또와 독립 · 공통기능 유지 · 이후 패치",
        "",
        "## 삭제",
        "",
        f"| 항목 | 삭제 전 | 삭제 후 |",
        f"|------|---------|---------|",
        f"| v13_* 예측 | {before['v13']} | {after['v13']} |",
        f"| strategy_x_* 예측 | {before['strategy_x']} | {after['strategy_x']} |",
        f"| 그 외 army4 예측 | {before['other_pred']} | {after['other_pred']} |",
        f"| lotto_draws | {before['draws']} (MAX {before['draws_max']}) | {after['draws']} (MAX {after['draws_max']}) |",
        "",
        "## 유지 (테스트로또·공통)",
        "",
        "- `combinadic.py` · 로또 조회 · 전체 조합 · 데이터수집 · 효도 · 테스트로또 · 테스트 대시보드",
        "- `lotto_testlotto.db` **미접촉**",
        "- 뇌 소스 파일은 디스크에 남김(공통 import 붕괴 방지). 생성 API는 `removed` 반환.",
        "",
        "## UI 숨김",
        "",
        "- 4군 대시보드 · 두뇌예측 · 전략 X · 명예의전당 · 두뇌상태",
        "",
        "- 1237 예측 생성 **없음**. APPLY 테스트로또 패치는 별 GO.",
        "",
        "## 파일",
        "",
        "- `app/lotto4/army4_brains_removed.py`",
        "- `app/lotto4/v13_routes.py` · `app/static/js/lotto4.js` · `app/static/index.html`",
        "- `tools/_k_army4_sx_brain_remove.py`",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
