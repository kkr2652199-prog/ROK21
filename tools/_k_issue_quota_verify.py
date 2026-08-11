# -*- coding: utf-8 -*-
"""K-ISSUE-QUOTA-VERIFY — 단계⑪ 발권 5장에 3뇌 ≥1 실측.

run_coordinated_prediction(target) 결과 lotto_predictions 뇌별 장수 확인.
min_each=1 전제. ge3미클레임 · 1237 아님(target≤1236).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KISSUE_QUOTA_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260812_KISSUE_QUOTA_VERIFY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

TARGETS = [1234, 1235, 1236]


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _count_brains(target: int) -> dict[str, Any]:
    from app.testlotto.brains.coordinator import (
        QUOTA_ADAPTIVE_MIN_EACH,
        _compute_dynamic_quota,
        _get_quota_weights,
        run_coordinated_prediction,
    )
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db

    set_learn_as_of(target)
    planned = _compute_dynamic_quota(_get_quota_weights(), total=5)
    out = run_coordinated_prediction(target)
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT brain_tag FROM lotto_predictions WHERE target_draw_no=?",
            (target,),
        ).fetchall()
    finally:
        conn.close()
    cnt = Counter(str(r["brain_tag"]) for r in rows)
    by = {t: int(cnt.get(t, 0)) for t in ("stat", "markov", "review")}
    return {
        "target": target,
        "min_each": int(QUOTA_ADAPTIVE_MIN_EACH),
        "planned_quota": planned,
        "issued_by_brain": by,
        "issued_total": sum(by.values()),
        "all_ge1": all(v >= 1 for v in by.values()),
        "error": out.get("error") if isinstance(out, dict) else None,
        "brain_errors": (out.get("brain_errors") if isinstance(out, dict) else None),
        "status": (out.get("status") if isinstance(out, dict) else None),
    }


def main() -> None:
    rows = [_count_brains(t) for t in TARGETS]
    ok = all(r["all_ge1"] and r["issued_total"] == 5 and not r["error"] for r in rows)
    verdict = "VERIFY_OK" if ok else "VERIFY_FAIL"
    out = {
        "id": "K-ISSUE-QUOTA-VERIFY",
        "ts": _now(),
        "targets": TARGETS,
        "rows": rows,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "note": "단계⑪ · min_each=1 · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-ISSUE-QUOTA-VERIFY",
        "",
        f"시각: {out['ts']} · 단계⑪",
        "",
        f"## 판정 **{verdict}**",
        "",
        "| target | planned | issued | all≥1 |",
        "|--------|---------|--------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['target']} | `{r['planned_quota']}` | `{r['issued_by_brain']}` | {r['all_ge1']} |"
        )
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", verdict)
    for r in rows:
        print(r["target"], r["planned_quota"], r["issued_by_brain"])
    print("WROTE", OUT_JSON)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
