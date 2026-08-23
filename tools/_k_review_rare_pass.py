# -*- coding: utf-8 -*-
"""K-REVIEW-RARE-PASS — 814만 극소조합 저장 + 전체조합 표시 + 엔진 패스.

몰아주기 미접촉. 1239 예측 없음. part DB는 로컬만(git 안 함).
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_RARE_PASS.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_RARE_PASS.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _smoke() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    random.seed(SEED)
    pool = [
        tuple(int(x) for x in (c.get("nums") or []))
        for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
        if c.get("brain_tag") == "review"
    ]
    from app.testlotto.brains.review_brain.rare_pass_store import should_pass

    rare_n = sum(1 for t in pool if should_pass(list(t)))
    return {"dno": dno, "n": len(pool), "rare_in_pool": rare_n}


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
        n = int(conn.execute("SELECT COUNT(*) FROM testlotto_rare_pass_combos").fetchone()[0])
    finally:
        conn.close()
    return {"draws_max": dmax, "pred_1237": pred_1237, "pred_1239": pred_1239, "pass_n": n}


def _write_md(doc: dict[str, Any]) -> str:
    b = doc["rebuild"]
    tc = b.get("tag_counts") or {}
    return "\n".join(
        [
            "# K-REVIEW-RARE-PASS (2026-08-23)",
            "",
            f"- **판정:** `{doc['verdict']}` · 전체조합 반영 · 엔진 패스 · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 814만 동일확률. 얇은 형태는 패스. 당첨회 분석 저장을 조합·엔진이 읽게. 한 단계. 1238/1239 달력은 이번 작업 아님.",
            f"- 근거: `docs/benchmarks/{OUT_JSON.name}`",
            "- 선행: `20260823_KREVIEW_RARE_SLICE` (814만 전수+당첨1–1237 형태표)",
            "",
            "## 무엇을 저장했나",
            "",
            "개별 조합 확률은 모두 1/8,145,060. 갈라내는 것은 **얇은 형태 조각**(확률의 확률).",
            "예시 `1-2-3-4-5-6`은 클래스 중 하나일 뿐(run6). 사람+추첨기계가 극소 형태를 패스할 수 있게 목록을 저장.",
            "",
            "표=`testlotto_rare_pass_combos` · 엔진 `should_pass()` · 전체조합 탭 극소 열·「극소만 보기」가 **같은 목록**을 읽는다.",
            "",
            f"- unique `{b.get('ok')}` · tag합 `{sum(tc.values()) if tc else 0}` · stamp `{doc.get('stamp')}`",
            f"- 1236 pool rare `{doc['smoke']['rare_in_pool']}` / {doc['smoke']['n']}",
            f"- pred_1237 `{doc['hard']['pred_1237']}` · pred_1239 `{doc['hard']['pred_1239']}` · MAX `{doc['hard']['draws_max']}`",
            f"- tag `{tc}`",
            "- 추가아이디어 이중3연속 공간780·당첨1회 → 이번 패스 목록에 **안 넣음**",
            "",
            "## 롤백",
            "",
            "- `REVIEW_RARE_SLICE_WIRE=False`",
            "",
            "## 파일",
            "",
            "- `rare_pass_store.py` · `all_combos_service.py` · `engine.py` · 전체조합 UI",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    from app.lotto4.all_combos_service import stamp_rare_pass_on_parts
    from app.testlotto.brains.review_brain.rare_pass_store import TABLE, rebuild
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    print("rebuild pass catalog", flush=True)
    built = rebuild()
    print(built, flush=True)

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(f"SELECT combo_no, tags_json FROM {TABLE}").fetchall()
        entries = [{"combo_no": int(r[0]), "tags": json.loads(r[1])} for r in rows]
    finally:
        conn.close()
    print("stamp parts", len(entries), flush=True)
    stamp = stamp_rare_pass_on_parts(entries)
    print(stamp, flush=True)

    smoke = _smoke()
    hard = _hard()
    verdict = (
        "APPLY_OK"
        if built.get("ok", 0) > 0 and hard["pred_1237"] == 0 and hard["pred_1239"] == 0
        else "PARTIAL"
    )
    doc = {
        "id": "K-REVIEW-RARE-PASS",
        "ts": _now(),
        "verdict": verdict,
        "rebuild": built,
        "stamp": stamp,
        "smoke": smoke,
        "hard": hard,
        "repack": "untouched",
        "idea_dual3": {"space": 780, "draws": 1, "in_step1": False},
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "n", built.get("ok"), flush=True)


if __name__ == "__main__":
    main()
