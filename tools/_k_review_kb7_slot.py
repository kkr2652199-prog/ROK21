# -*- coding: utf-8 -*-
"""K-REVIEW-KB7-SLOT — 4·5·6 묶음 7번 자리. 기어 OFF.

1·2·3 불변. 몰아주기 없음. 예측 없음. 자동화 아님.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260823_KREVIEW_KB7_SLOT.json"
OUT_MD = ROOT / "reports" / "20260823_KREVIEW_KB7_SLOT.md"
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
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
    finally:
        conn.close()
    from app.testlotto.brains.review_brain.kb7_future import REVIEW_KB7_WIRE

    return {
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "wire": bool(REVIEW_KB7_WIRE),
    }


def _smoke() -> dict[str, Any]:
    import app.testlotto.brains.review_brain.kb7_future as kb7
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    dno = 1236
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    old = bool(kb7.REVIEW_KB7_WIRE)
    try:
        kb7.REVIEW_KB7_WIRE = False
        random.seed(SEED)
        a = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
        bundle = kb7.collect_before(draws)
        kb7.REVIEW_KB7_WIRE = True
        random.seed(SEED)
        b = [
            tuple(int(x) for x in (c.get("nums") or []))
            for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            if c.get("brain_tag") == "review"
        ]
    finally:
        kb7.REVIEW_KB7_WIRE = old
    return {
        "dno": dno,
        "same_off_on": a == b,
        "n": len(a),
        "bundle_as_of": bundle.get("as_of"),
        "has_shape": bool(bundle.get("shape")),
        "has_consec": bool(bundle.get("consec")),
        "has_assoc": bool(bundle.get("assoc")),
        "shape_n": (bundle.get("shape") or {}).get("n"),
        "assoc_n": (bundle.get("assoc") or {}).get("n"),
        "consec_as_of": (bundle.get("consec") or {}).get("as_of"),
    }


def _write_md(doc: dict[str, Any]) -> str:
    s = doc["smoke"]
    h = doc["hard"]
    return "\n".join(
        [
            "# K-REVIEW-KB7-SLOT (2026-08-23)",
            "",
            f"- **판정:** `{doc['verdict']}` · 7번 자리 · 기어 OFF · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 1·2·3 패스. 4·5·6은 엔진이 읽고 7번으로 미래장 참고. 단계 튜닝 필요. 아이디어 요청.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 이번 패치",
            "",
            "- `kb7_future.collect_before` = 4형태 + 5연속 + 6연관 한 묶음",
            "- `REVIEW_KB7_WIRE=False` · apply/skip 빈 자리",
            f"- 1236 발권 OFF==ON 동일 `{s['same_off_on']}` n `{s['n']}`",
            f"- 묶음 as_of `{s['bundle_as_of']}` · shape `{s['has_shape']}` n `{s['shape_n']}` · consec `{s['has_consec']}` · assoc `{s['has_assoc']}` n `{s['assoc_n']}`",
            f"- pred_1237 `{h['pred_1237']}` · pred_1239 `{h['pred_1239']}` · MAX `{h['draws_max']}` · wire `{h['wire']}`",
            "",
            "## 다음 단계(형 1건)",
            "",
            "- 4상세 / 5상세 / 6상세 중 하나, 또는 7번 한 소스만 기어 시험",
            "- 자동화 시동 아직 아님",
            "",
            "## 아이디어(성적 클레임 아님)",
            "",
            "- 4: 최근 회 보통 홀수·폭만 참고. 극단은 이미 3번이 자름",
            "- 5: PASS_WIRE 켜면 1600은 3번과 중복. 서명 flatten은 별 GO+게이트",
            "- 6: 핫쌍 가중이 아니라 한 장에 핫쌍 과다하면 패스(몰림 방지). 1238 표 추가는 별 오더",
            "- 7: 스위치 하나. 4만/5만/6만 켜서 단계 튜닝. prefer 0.005 게이트",
            "",
            "## 롤백",
            "",
            "- `REVIEW_KB7_WIRE=False`(이미) · 엔진 collect 호출 제거",
            "",
            "## 파일",
            "",
            "- `kb7_future.py` · `engine.py`",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    smoke = _smoke()
    hard = _hard()
    verdict = (
        "APPLY_OK"
        if smoke["same_off_on"]
        and smoke["has_shape"]
        and smoke["has_consec"]
        and smoke["has_assoc"]
        and hard["pred_1237"] == 0
        and hard["wire"] is False
        else "PARTIAL"
    )
    doc = {
        "id": "K-REVIEW-KB7-SLOT",
        "ts": _now(),
        "verdict": verdict,
        "pass_123": True,
        "smoke": smoke,
        "hard": hard,
        "repack": "untouched",
        "predict": False,
        "automation": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "same", smoke["same_off_on"], "as_of", smoke["bundle_as_of"], flush=True)


if __name__ == "__main__":
    main()
