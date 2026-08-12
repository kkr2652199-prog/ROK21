# -*- coding: utf-8 -*-
"""K-SKILL-HOMEWORK-PERSIST — LIST_V3 L9c 검증."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLE_ASOF = 1236
TARGET = 1237  # 예측 타깃(양산 아님 · 읽기 no_peek만)
BENCH = ROOT / "docs" / "benchmarks" / "20260812_KSKILL_HOMEWORK_PERSIST.json"
REPORT = ROOT / "reports" / "20260812_KSKILL_HOMEWORK_PERSIST.md"


def main() -> int:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import (
        HINT_SPEC_BY_BRAIN,
        _build_hint_for_spec,
        build_hint_by_brain,
    )
    from app.testlotto import skill_homework as hw

    init_testlotto_db()
    hw.ensure_skill_homework_table()
    checks: dict[str, bool] = {}

    wr = hw.write_skill_homework(SAMPLE_ASOF, note="L9c_WIRE_VERIFY")
    checks["write_ok"] = bool(wr.get("ok"))
    checks["write_3brains"] = set(wr.get("brains") or {}) == {"stat", "markov", "review"}

    conn = get_lotto_db()
    try:
        n = conn.execute(
            f"SELECT COUNT(*) FROM {hw.TABLE} WHERE as_of_draw=?",
            (SAMPLE_ASOF,),
        ).fetchone()[0]
        kinds = dict(
            conn.execute(
                f"SELECT brain_tag, skill_kind FROM {hw.TABLE} WHERE as_of_draw=?",
                (SAMPLE_ASOF,),
            ).fetchall()
        )
    finally:
        conn.close()
    checks["rows_3"] = n == 3
    checks["kind_stat"] = kinds.get("stat") == "miss_pattern"
    checks["kind_markov"] = kinds.get("markov") == "crowd_prefer"
    checks["kind_review"] = kinds.get("review") == "crowd_prize"

    loaded = hw.load_skill_homework_before(TARGET)
    checks["load_3"] = set(loaded) == {"stat", "markov", "review"}
    checks["no_peek"] = hw.assert_no_peek_homework(TARGET)

    # stored == live recompute (as_of=1236 → target 1237 draws)
    draws = _get_draws_before(TARGET)
    max_abs = 0.0
    for tag in ("stat", "markov", "review"):
        weeks, signal = HINT_SPEC_BY_BRAIN[tag]
        live = _build_hint_for_spec(draws, weeks, signal, TARGET)
        st = loaded[tag]
        for i in range(1, 46):
            max_abs = max(max_abs, abs(float(live[i]) - float(st[i])))
    checks["payload_eq_recompute"] = max_abs < 1e-9

    # build_hint_by_brain consume path
    old = hw.SKILL_HOMEWORK_CONSUME
    try:
        hw.SKILL_HOMEWORK_CONSUME = True
        via = build_hint_by_brain(draws, TARGET)
        checks["consume_wired"] = set(via) == {"stat", "markov", "review"}
        cons_abs = 0.0
        for tag in via:
            for i in range(1, 46):
                cons_abs = max(cons_abs, abs(float(via[tag][i]) - float(loaded[tag][i])))
        checks["consume_matches_stored"] = cons_abs < 1e-9
    finally:
        hw.SKILL_HOMEWORK_CONSUME = old

    import inspect
    from app.testlotto import click_feedback as cf
    from app.testlotto.brains import coordinator as coord

    checks["wired_click"] = "write_skill_homework" in inspect.getsource(
        cf.apply_draw_result_feedback
    ) or "skill_homework" in inspect.getsource(cf.apply_draw_result_feedback)
    checks["wired_auto"] = "write_skill_homework" in inspect.getsource(coord._auto_feedback)

    hard = [
        "write_ok",
        "write_3brains",
        "rows_3",
        "kind_stat",
        "kind_markov",
        "kind_review",
        "load_3",
        "no_peek",
        "payload_eq_recompute",
        "consume_wired",
        "consume_matches_stored",
        "wired_click",
        "wired_auto",
    ]
    hard_ok = all(checks.get(k) for k in hard)
    verdict = "WIRE_OK" if hard_ok else "FAIL"

    payload = {
        "id": "K-SKILL-HOMEWORK-PERSIST",
        "list": "LIST_V3 L9c",
        "verdict": verdict,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "as_of": SAMPLE_ASOF,
        "target_read": TARGET,
        "max_abs_vs_recompute": max_abs,
        "checks": checks,
        "write": wr,
        "notes": [
            "skill별 저장: stat=miss_pattern(52) · markov=crowd_prefer · review=crowd_prize",
            "읽기 as_of < target · 1237은 양산 아님(no_peek 검증용)",
            "ge3 미클레임 · 강제BT 보류",
        ],
    }
    BENCH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-SKILL-HOMEWORK-PERSIST — LIST_V3 L9c",
        "",
        f"판정: **{verdict}** · as_of={SAMPLE_ASOF} · read_target={TARGET}(검증만)",
        "",
        "## HARD",
        "",
    ]
    for k in hard:
        lines.append(f"- `{k}`: **{checks.get(k)}**")
    lines += [
        "",
        f"- max_abs vs recompute: `{max_abs}`",
        "",
        "## 스키마",
        "",
        "- 테이블 `testlotto_skill_homework` PK(as_of_draw, brain_tag, skill_kind)",
        "- 모듈: 결과확정 후 click/`_auto_feedback`",
        "- 읽기: `build_hint_by_brain` ← `SKILL_HOMEWORK_CONSUME`",
        "",
        f"벤치: `{BENCH.relative_to(ROOT).as_posix()}`",
        "",
        "다음: **L9d** K-EMA-OR-LEDGER-SSOT 문서결정",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "checks": checks, "max_abs": max_abs}, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
