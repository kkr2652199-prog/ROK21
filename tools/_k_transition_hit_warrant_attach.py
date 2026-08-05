# -*- coding: utf-8 -*-
"""K-TRANSITION-HIT-WARRANT-ATTACH — 명분 라벨 → hit_warrant_log + evolve note.

발권가중·WIRE·engine·coordinator 산출 경로 금지.
Usage:
  python tools/_k_transition_hit_warrant_attach.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_HIT_WARRANT_ATTACH.json"
OUT_MD = ROOT / "reports" / "20260805_KTRANSITION_HIT_WARRANT_ATTACH.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
PRIOR = ROOT / "docs" / "benchmarks" / "20260805_KTRANSITION_HIT_WARRANT.json"


def backfill_hit_warrant_log() -> dict[str, Any]:
    from app.testlotto.hit_warrant import (
        HIT_WARRANT_ATTACH,
        ensure_hit_warrant_log_table,
        label_pair,
        upsert_hit_warrant_log,
    )
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    conn.execute("PRAGMA busy_timeout=60000")
    ensure_hit_warrant_log_table(conn)
    rows = conn.execute(
        """
        SELECT draw_no, anchor_nums, top15, next_actual
        FROM transition_log WHERE sim_k=2 ORDER BY draw_no
        """
    ).fetchall()
    inserted = 0
    for r in rows:
        d = dict(r)
        n = int(d["draw_no"])
        cat = label_pair(
            json.loads(d["anchor_nums"]),
            json.loads(d["next_actual"]),
            json.loads(d["top15"]),
        )
        upsert_hit_warrant_log(n + 1, n, cat, sim_k=2, conn=conn)
        inserted += 1
        if inserted % 300 == 0:
            conn.commit()
    conn.commit()
    n_log = int(
        conn.execute("SELECT COUNT(*) AS c FROM hit_warrant_log").fetchone()["c"]
    )
    spot = conn.execute(
        "SELECT draw_no, summary_text, n_explained, n_unexplained "
        "FROM hit_warrant_log WHERE draw_no=1235 AND sim_k=2"
    ).fetchone()
    conn.close()
    return {
        "HIT_WARRANT_ATTACH": HIT_WARRANT_ATTACH,
        "transition_rows": len(rows),
        "upserted": inserted,
        "hit_warrant_log_rows": n_log,
        "spot_1235": dict(spot) if spot else None,
    }


def patch_evolve_notes_sample(limit: int = 30) -> dict[str, Any]:
    """기존 evolve_log note에 요약 부착 (weight 불변). hit_warrant_log만 참조."""
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        conn.execute("PRAGMA busy_timeout=60000")
        rows = conn.execute(
            """
            SELECT draw_no, brain_tag, note, weight_applied
            FROM testlotto_evolve_log
            ORDER BY draw_no DESC
            """
        ).fetchall()
        updated = 0
        weight_ok = True
        samples: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            if float(d["weight_applied"] or 0) != 0.0:
                weight_ok = False
            old = d["note"] or ""
            if "HIT-WARRANT" in old:
                continue
            wr = conn.execute(
                "SELECT summary_text FROM hit_warrant_log WHERE draw_no=? AND sim_k=2",
                (int(d["draw_no"]),),
            ).fetchone()
            if not wr:
                continue
            summary = dict(wr)["summary_text"]
            new = f"{old} · {summary}" if old else summary
            if new == old:
                continue
            conn.execute(
                """
                UPDATE testlotto_evolve_log
                SET note=?, updated_at=datetime('now','localtime')
                WHERE draw_no=? AND brain_tag=?
                """,
                (new, int(d["draw_no"]), d["brain_tag"]),
            )
            updated += 1
            if len(samples) < limit:
                samples.append(
                    {
                        "draw_no": int(d["draw_no"]),
                        "brain_tag": d["brain_tag"],
                        "note_tail": new[-160:],
                    }
                )
        conn.commit()
        bad = conn.execute(
            "SELECT COUNT(*) AS c FROM testlotto_evolve_log WHERE weight_applied != 0"
        ).fetchone()["c"]
        return {
            "evolve_rows_scanned": len(rows),
            "notes_updated": updated,
            "weight_all_zero": weight_ok and int(bad) == 0,
            "samples": samples,
        }
    finally:
        conn.close()


def smoke_no_wire() -> dict[str, Any]:
    from app.testlotto.brains.stat_brain import transition_v1
    from app.testlotto.hit_warrant import HIT_WARRANT_ATTACH

    return {
        "TRANSITION_V1_WIRE": bool(transition_v1.TRANSITION_V1_WIRE),
        "HIT_WARRANT_ATTACH": HIT_WARRANT_ATTACH,
        "wire_must_be_false": transition_v1.TRANSITION_V1_WIRE is False,
    }


def main() -> int:
    bf = backfill_hit_warrant_log()
    ev = patch_evolve_notes_sample()
    sm = smoke_no_wire()
    prior_rates = None
    if PRIOR.exists():
        prior_rates = json.loads(PRIOR.read_text(encoding="utf-8")).get("rates")

    ok = (
        bf["hit_warrant_log_rows"] >= 1134
        and sm["wire_must_be_false"]
        and ev["weight_all_zero"]
    )
    payload = {
        "id": "K-TRANSITION-HIT-WARRANT-ATTACH",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if ok else "FAIL",
        "wire": False,
        "pass": ok,
        "backfill": bf,
        "evolve_note_patch": ev,
        "smoke": sm,
        "prior_catalog_rates": prior_rates,
        "claim": "로그·설명 부착만 · 발권가중/WIRE/confidence 미변경 · 당첨P↑금지",
        "tool": "tools/_k_transition_hit_warrant_attach.py",
        "module": "app/testlotto/hit_warrant.py",
        "prior": "docs/benchmarks/20260805_KTRANSITION_HIT_WARRANT.json",
        "forbid": [
            "engine.py",
            "random.choices",
            "발권 INSERT 경로 가중",
            "coordinator 산출 수정",
            "TRANSITION_V1_WIRE ON",
            "당첨확률↑ 클레임",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# K-TRANSITION-HIT-WARRANT-ATTACH (2026-08-05)",
        "",
        f"- **판정:** `{payload['verdict']}` · wire=`False`",
        f"- hit_warrant_log rows=**{bf['hit_warrant_log_rows']}** "
        f"(transition upsert={bf['upserted']})",
        f"- evolve notes updated=**{ev['notes_updated']}** · "
        f"weight_all_zero=**{ev['weight_all_zero']}**",
        f"- TRANSITION_V1_WIRE=**{sm['TRANSITION_V1_WIRE']}** · "
        f"HIT_WARRANT_ATTACH=**{sm['HIT_WARRANT_ATTACH']}**",
        "",
        "## spot 1235",
        f"- `{bf.get('spot_1235')}`",
        "",
        "## 해석",
        "- 명분 라벨을 **학습/설명 로그**에만 부착.",
        "- 발권 confidence·quota·WIRE 변경 없음.",
        "- 카탈로그 비율 SSOT는 prior HIT-WARRANT JSON.",
        "",
        f"- tool: `{payload['tool']}` · module: `{payload['module']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": ok,
                "verdict": payload["verdict"],
                "rows": bf["hit_warrant_log_rows"],
                "notes_updated": ev["notes_updated"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
