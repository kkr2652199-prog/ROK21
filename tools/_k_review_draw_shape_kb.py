# -*- coding: utf-8 -*-
"""K-REVIEW-DRAW-SHAPE-KB — 당첨 회차별 형태 지식 저장.

1번째 오더: 로또조회 당첨 회만 분석·저장. 전체조합 반영 없음. 몰아주기 없음.
예측 가중/거절 변경 없음(읽기 배선만). 1237 신규예측 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_DRAW_SHAPE_KB.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_DRAW_SHAPE_KB.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _hard() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        kb_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_draw_shape_kb").fetchone()[0])
        kb_min, kb_max = conn.execute(
            "SELECT MIN(draw_no), MAX(draw_no) FROM testlotto_draw_shape_kb"
        ).fetchone()
        feat_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_draw_features").fetchone()[0])
    finally:
        conn.close()
    return {
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "kb_n": kb_n,
        "kb_min": kb_min,
        "kb_max": kb_max,
        "feat_n": feat_n,
    }


def _smoke_same() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.draw_shape_kb as kb
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    old = bool(kb.REVIEW_SHAPE_KB_READ)
    try:
        kb.REVIEW_SHAPE_KB_READ = False
        random.seed(SEED)
        a = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
        kb.REVIEW_SHAPE_KB_READ = True
        random.seed(SEED)
        b = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
    finally:
        kb.REVIEW_SHAPE_KB_READ = old
    return {"dno": dno, "same": a == b, "n": len(a)}


def _write_md(doc: dict[str, Any]) -> str:
    s = doc["summary"]
    return "\n".join(
        [
            "# K-REVIEW-DRAW-SHAPE-KB (2026-08-23)",
            "",
            f"- **판정:** `{doc['verdict']}` · 금액뇌 읽기만 · 전체조합 미반영 · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 로또조회 1회~당첨회 특징을 회차마다 저장. 전체조합은 다음. 패치적용 전 지식.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 1번째 오더",
            "",
            f"- 저장 `{s.get('ok')}` / fail `{s.get('fail')}` · 구간 {s.get('lo')}–{s.get('hi')} · src `{s.get('n_src')}`",
            f"- DB draws_max `{doc['hard']['draws_max']}` · kb `{doc['hard']['kb_n']}` ({doc['hard']['kb_min']}–{doc['hard']['kb_max']})",
            f"- 구 draw_features `{doc['hard']['feat_n']}` (1237·1238 빈칸 채움)",
            f"- 읽기 요약 as_of `{doc['read'].get('as_of')}` n `{doc['read'].get('n')}` span평균 `{doc['read'].get('span_mean')}`",
            f"- 1236 발권 동일 `{doc['smoke']['same']}` (가중·거절 변경 없음)",
            f"- pred_1237 `{doc['hard']['pred_1237']}`",
            "",
            "## 엔진",
            "",
            "- `summarize_before(draws)` · as_of=타깃 이전",
            "- `REVIEW_SHAPE_KB_READ=True` · 생성 공식 불변",
            "- 전체조합 탭 코드 불변",
            "",
            "## 파일",
            "",
            "- `app/testlotto/brains/review_brain/draw_shape_kb.py` · `engine.py` · `models.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    from app.testlotto.brains.review_brain.draw_shape_kb import rebuild, summarize_before
    from app.testlotto.draw_analysis import upsert_draw_features
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    finally:
        conn.close()

    print(f"rebuild kb 1-{dmax}", flush=True)
    built = rebuild(lo=1, hi=dmax)
    print(built, flush=True)

    feat_ok = 0
    for dno in range(1, dmax + 1):
        if upsert_draw_features(dno):
            feat_ok += 1
        if dno % 200 == 0 or dno == dmax:
            print(f"  feat {dno} ok={feat_ok}", flush=True)

    from app.testlotto.data_service import _get_draws_before

    draws = _get_draws_before(dmax + 1)
    read = summarize_before(draws)
    smoke = _smoke_same()
    hard = _hard()
    verdict = (
        "APPLY_OK"
        if built.get("fail") == 0
        and hard["kb_n"] == built["n_src"]
        and smoke["same"]
        and hard["pred_1237"] == 0
        else "PARTIAL"
    )
    doc = {
        "id": "K-REVIEW-DRAW-SHAPE-KB",
        "ts": _now(),
        "verdict": verdict,
        "summary": built,
        "feat_upsert": feat_ok,
        "read": read,
        "smoke": smoke,
        "hard": hard,
        "all_combos": "untouched",
        "repack": "untouched",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "kb", hard["kb_n"], "same", smoke["same"], "pred_1237", hard["pred_1237"], flush=True)


if __name__ == "__main__":
    main()
