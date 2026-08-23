# -*- coding: utf-8 -*-
"""K-REVIEW-DRAW-ASSOC — 1–1237 당첨 6+보너스 연관 저장.

통작업 세부. 조사·저장·엔진 읽기. 예측 없음. 자동화 시동 아님.
비슷한 조합=본번호 겹침(순서 무관). 몰아주기 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_DRAW_ASSOC.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_DRAW_ASSOC.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42
HI = 1237


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
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
        n = int(conn.execute("SELECT COUNT(*) FROM testlotto_draw_assoc").fetchone()[0])
        amin, amax = conn.execute(
            "SELECT MIN(draw_no), MAX(draw_no) FROM testlotto_draw_assoc"
        ).fetchone()
        n5 = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_draw_assoc WHERE similar5_json != '[]'"
            ).fetchone()[0]
        )
        n4 = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_draw_assoc WHERE similar4_json != '[]'"
            ).fetchone()[0]
        )
        d1237 = conn.execute(
            """
            SELECT nums_json, bonus, similar4_json, similar5_json, pairs_json,
                   bonus_links_json, share3_count
            FROM testlotto_draw_assoc WHERE draw_no=1237
            """
        ).fetchone()
    finally:
        conn.close()
    row1237 = None
    if d1237:
        row1237 = {
            "nums": json.loads(d1237[0] or "[]"),
            "bonus": int(d1237[1] or 0),
            "similar4_n": len(json.loads(d1237[2] or "[]")),
            "similar5_n": len(json.loads(d1237[3] or "[]")),
            "pairs_n": len(json.loads(d1237[4] or "[]")),
            "bonus_links_n": len(json.loads(d1237[5] or "[]")),
            "share3_count": int(d1237[6] or 0),
        }
    return {
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "assoc_n": n,
        "assoc_min": amin,
        "assoc_max": amax,
        "n_similar4_draws": n4,
        "n_similar5_draws": n5,
        "row_1237": row1237,
    }


def _smoke_same() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.draw_assoc as kb
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    old = bool(kb.REVIEW_ASSOC_KB_READ)
    try:
        kb.REVIEW_ASSOC_KB_READ = False
        random.seed(SEED)
        a = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
        kb.REVIEW_ASSOC_KB_READ = True
        random.seed(SEED)
        b = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
    finally:
        kb.REVIEW_ASSOC_KB_READ = old
    return {"dno": dno, "same": a == b, "n": len(a)}


def _write_md(doc: dict[str, Any]) -> str:
    s = doc["summary"]
    r = doc["read"]
    h = doc["hard"]
    row = h.get("row_1237") or {}
    tops = r.get("top_pairs") or []
    tops_s = ", ".join(f"{p['pair'][0]}-{p['pair'][1]}×{p['n']}" for p in tops[:8])
    ex5 = r.get("similar5_examples") or []
    ex5_s = "; ".join(
        f"{e['a']}↔{e['b']} share{e['share']} {e.get('overlap')}" for e in ex5[:8]
    )
    return "\n".join(
        [
            "# K-REVIEW-DRAW-ASSOC (2026-08-23)",
            "",
            f"- **판정:** `{doc['verdict']}` · 금액뇌 읽기만 · 자동화 아님 · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 통작업 세부. 이전 회 조사. 1–1237 비슷한 조합(본번호 겹침). 6+보너스 연관 저장. 예측 바로 안 함.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 구간·저장",
            "",
            f"- 저장 `{s.get('ok')}` / fail `{s.get('fail')}` · 구간 {s.get('lo')}–{s.get('hi')} · src `{s.get('n_src')}`",
            f"- DB draws_max `{h['draws_max']}` (1238 있음 · 이번 표는 **1237까지**)",
            f"- 표 `testlotto_draw_assoc` `{h['assoc_n']}` ({h['assoc_min']}–{h['assoc_max']})",
            f"- 1237 본번호 `{row.get('nums')}` +보너스 `{row.get('bonus')}` · 쌍 `{row.get('pairs_n')}` · 보너슬ink `{row.get('bonus_links_n')}`",
            "",
            "## 비슷한 조합 (본번호 겹침 · 순서 무관)",
            "",
            f"- 4개 이상 겹친 회 `{h['n_similar4_draws']}` · 무방향쌍 `{s.get('n_similar4_undirected')}`",
            f"- 5개 이상 겹친 회 `{h['n_similar5_draws']}` · 무방향쌍 `{s.get('n_similar5_undirected')}`",
            f"- 예(5겹): {ex5_s or '없음'}",
            f"- 3겹 회당 평균 `{r.get('share3_mean')}` (목록 비저장·건수만)",
            f"- 1237의 4겹상대 `{row.get('similar4_n')}` · 5겹 `{row.get('similar5_n')}` · 3겹건수 `{row.get('share3_count')}`",
            "",
            "## 번호 연관 (1–1237 집계 · as_of 필터)",
            "",
            f"- 본번호 쌍 종류 `{r.get('pair_kinds')}` · 보너스연결 종류 `{r.get('bonus_link_kinds')}`",
            f"- 상위 본번호쌍: {tops_s}",
            f"- 연번쌍 회평균 `{r.get('consec_pair_mean')}` · 이월 회평균 `{r.get('carry_mean')}`",
            f"- 읽기 as_of `{r.get('as_of')}` n `{r.get('n')}`",
            "",
            "## 엔진",
            "",
            "- `summarize_before(draws)` · as_of=타깃 이전 · 비슷한상대도 as_of 이하만",
            "- `REVIEW_ASSOC_KB_READ=True` · 생성 공식 불변",
            f"- 1236 발권 동일 `{doc['smoke']['same']}` n `{doc['smoke']['n']}`",
            f"- pred_1237 `{h['pred_1237']}` · pred_1239 `{h['pred_1239']}`",
            "- 자동화(시동=전부 회전) **아직 아님**. 수동 패치.",
            "",
            "## 롤백",
            "",
            "- `REVIEW_ASSOC_KB_READ=False`",
            "",
            "## 파일",
            "",
            "- `app/testlotto/brains/review_brain/draw_assoc.py` · `engine.py` · `models.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    from app.testlotto.brains.review_brain.draw_assoc import rebuild, summarize_before
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.models import init_testlotto_db

    init_testlotto_db()
    print(f"rebuild assoc 1-{HI}", flush=True)
    built = rebuild(lo=1, hi=HI)
    print(built, flush=True)

    draws = _get_draws_before(HI + 1)
    read = summarize_before(draws)
    smoke = _smoke_same()
    hard = _hard()
    verdict = (
        "APPLY_OK"
        if built.get("fail") == 0
        and hard["assoc_n"] == built["n_src"]
        and hard["assoc_max"] == HI
        and smoke["same"]
        and hard["pred_1237"] == 0
        else "PARTIAL"
    )
    doc = {
        "id": "K-REVIEW-DRAW-ASSOC",
        "ts": _now(),
        "verdict": verdict,
        "window": {"lo": 1, "hi": HI, "note": "형 지정 1–1237. DB MAX는 별도."},
        "summary": built,
        "read": read,
        "smoke": smoke,
        "hard": hard,
        "automation": False,
        "repack": "untouched",
        "predict": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(
        verdict,
        "assoc",
        hard["assoc_n"],
        "same",
        smoke["same"],
        "pred_1237",
        hard["pred_1237"],
        flush=True,
    )


if __name__ == "__main__":
    main()
