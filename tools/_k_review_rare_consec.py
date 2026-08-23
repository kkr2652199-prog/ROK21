# -*- coding: utf-8 -*-
"""K-REVIEW-RARE-CONSEC — 연속 run 서명 표 저장. 기어 중립.

몰아주기 미접촉. 1237/1239 예측 없음. 가중·flatten 불변.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_RARE_CONSEC.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_RARE_CONSEC.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _pool() -> list[tuple[int, ...]]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    random.seed(SEED)
    return [
        tuple(int(x) for x in (c.get("nums") or []))
        for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
        if c.get("brain_tag") == "review"
    ]


def _hard() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
        n_cls = int(conn.execute("SELECT COUNT(*) FROM testlotto_rare_consec_classes").fetchone()[0])
        n_cmb = int(conn.execute("SELECT COUNT(*) FROM testlotto_rare_consec_combos").fetchone()[0])
    finally:
        conn.close()
    return {
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "classes": n_cls,
        "combos": n_cmb,
    }


def _write_md(doc: dict[str, Any]) -> str:
    b = doc["rebuild"]
    rows = doc.get("table", {}).get("rows") or []
    lines = [
        "# K-REVIEW-RARE-CONSEC (2026-08-23)",
        "",
        f"- **판정:** `{doc['verdict']}` · 연속 세분화 표 · 기어 중립 · 몰아주기 미접촉",
        f"- 시각: {doc['ts']}",
        "- 형: 극소조합 다음 단계=극소 연속. 분석·저장·예측전 읽기. 금액뇌 특성 패치 아님.",
        f"- 근거: `docs/benchmarks/{OUT_JSON.name}`",
        "- 선행: `20260823_KREVIEW_RARE_PASS` · `20260822_KREVIEW_SHAPE_CONSEC`",
        "",
        "## 틀 (중립)",
        "",
        "개별 확률은 1/8,145,060. 여기는 **연속 run 서명**(붙는 덩어리 길이).",
        "기어 중립=`REVIEW_CONSEC_PASS_WIRE=False` · 가중/flatten/`random.choices` **불변**.",
        "엔진은 `summarize_before(draws)` 만 읽음. 거절은 기존 rare_pass+tier1(run≥4).",
        "",
        f"- 클래스 `{b.get('classes')}` · STEP1 조합 `{b.get('combos')}` · sig `{b.get('sig_counts')}`",
        f"- 1236 pool 동일 `{doc['smoke']['same']}` · n `{doc['smoke']['n']}`",
        f"- pred_1237 `{doc['hard']['pred_1237']}` · pred_1239 `{doc['hard']['pred_1239']}` · MAX `{doc['hard']['draws_max']}`",
        "",
        "## 814만 × 당첨 1–1238",
        "",
        "| 서명 | 814만 | 당첨 | 널E | STEP1 |",
        "|------|------:|-----:|-----:|:------:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['sig']} | {r['space']} | {r['draws']} | {r['null_e']} | {'Y' if r['step1'] else ''} |"
        )
    lines.extend(
        [
            "",
            "## STEP1 (0회·얇음)",
            "",
            "- `6` 40 · `5+1` 1560. 합 **1600** (기존 rare_pass run5/6과 동일 집합)",
            "- `4+2` 당첨 1(292회 `17-18-31-32-33-34`) · `3+3` 당첨 1(1152회 `30-31-32-35-36-37`) → **목록 제외**",
            "- `2+2+2` 당첨 6 · `4+1+1` 당첨 5 → 제외",
            "",
            "## 롤백",
            "",
            "- `REVIEW_CONSEC_KB_READ=False`",
            "",
            "## 파일",
            "",
            "- `rare_consec.py` · `rare_consec_store.py` · `engine.py`(읽기) · 전체조합 연속열",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    from app.testlotto.brains.review_brain.rare_consec import summarize
    from app.testlotto.brains.review_brain.rare_consec_store import rebuild

    before = _pool()
    print("rebuild consec", flush=True)
    built = rebuild()
    print(built, flush=True)
    after = _pool()
    smoke = {
        "dno": 1236,
        "n": len(after),
        "same": before == after,
        "first": list(after[0]) if after else None,
    }
    hard = _hard()
    table = summarize()
    verdict = (
        "APPLY_OK"
        if built.get("combos", 0) == 1600
        and hard["pred_1237"] == 0
        and hard["pred_1239"] == 0
        and smoke["same"]
        else "PARTIAL"
    )
    doc = {
        "id": "K-REVIEW-RARE-CONSEC",
        "ts": _now(),
        "verdict": verdict,
        "rebuild": built,
        "smoke": smoke,
        "hard": hard,
        "table": table,
        "repack": "untouched",
        "gear": "neutral",
        "pass_wire": False,
        "flatten_untouched": True,
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "combos", built.get("combos"), "same", smoke["same"], flush=True)


if __name__ == "__main__":
    main()
