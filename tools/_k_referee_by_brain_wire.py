# -*- coding: utf-8 -*-
"""K-REFEREE-BY-BRAIN-WIRE — 뇌별 독립 감독관 검증.

검사
  1) 엔진 모듈 3개 import
  2) 타뇌 avg 변경 → 이 뇌 set_score 불변 (교차의존 0)
  3) quota 가중은 뇌별 raw 후 정규화
  4) DB 미러 sync (K-J)
  5) knobs snapshot
성적클레임 금지 · 1237아님.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KREFEREE_BY_BRAIN_WIRE.json"
OUT_MD = ROOT / "reports" / "20260811_KREFEREE_BY_BRAIN_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> None:
    from app.testlotto.brains.markov_brain import referee as mk_ref
    from app.testlotto.brains.review_brain import referee as rv_ref
    from app.testlotto.brains.stat_brain import referee as st_ref
    from app.testlotto.brains.shared import referee_by_brain as rbb
    from app.testlotto.brains import aux_referee
    from app.testlotto.learn_state import sync_brain_weights_from_referee
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    checks: dict[str, Any] = {}

    checks["engines_import"] = {
        "pass": (
            st_ref.BRAIN_TAG == "stat"
            and mk_ref.BRAIN_TAG == "markov"
            and rv_ref.BRAIN_TAG == "review"
        ),
        "tags": [st_ref.BRAIN_TAG, mk_ref.BRAIN_TAG, rv_ref.BRAIN_TAG],
    }

    # 교차의존: markov avg만 바꿔도 stat set_score 동일
    base_states = {
        "stat": {"recent_avg_match": 0.90, "review_count": 10},
        "markov": {"recent_avg_match": 0.70, "review_count": 10},
        "review": {"recent_avg_match": 0.80, "review_count": 10},
    }
    s0 = rbb.independent_scores_from_states(base_states)["stat"]["set_score"]
    altered = {
        "stat": dict(base_states["stat"]),
        "markov": {"recent_avg_match": 0.99, "review_count": 10},
        "review": dict(base_states["review"]),
    }
    s1 = rbb.independent_scores_from_states(altered)["stat"]["set_score"]
    checks["cross_brain_independence"] = {
        "pass": abs(s0 - s1) < 1e-12,
        "stat_score_before": s0,
        "stat_score_after_markov_change": s1,
    }

    # 구식 상대가중 경로가 아님: aux score uses local (mock via engine)
    st_local = st_ref.set_score_from_state(base_states["stat"])
    checks["stat_engine_local"] = {
        "pass": abs(st_local - s0) < 1e-12,
        "score": st_local,
    }

    q0 = rbb.quota_weights_from_states(base_states)
    q1 = rbb.quota_weights_from_states(altered)
    checks["quota_reacts_to_peer"] = {
        "pass": abs(q0["stat"] - q1["stat"]) > 1e-6,  # 배분만 상대화됨
        "q0": q0,
        "q1": q1,
        "note": "quota는 상대화 OK · set_score는 불변이어야 함",
    }

    # empty → equal
    empty = {t: {"recent_avg_match": 0.0, "review_count": 0} for t in rbb.PREDICT_TAGS}
    qe = rbb.quota_weights_from_states(empty)
    checks["empty_equal"] = {
        "pass": all(abs(qe[t] - 1 / 3) < 1e-9 for t in qe),
        "weights": qe,
    }

    init_testlotto_db()
    set_learn_as_of(1236)
    sync = sync_brain_weights_from_referee()
    conn = get_lotto_db()
    db = {
        str(r["brain_tag"]): float(r["current_weight"])
        for r in conn.execute(
            "SELECT brain_tag, current_weight FROM testlotto_brain_weights "
            "WHERE brain_tag IN ('stat','markov','review')"
        )
    }
    conn.close()
    mirror_ok = all(abs(db.get(t, -1) - sync.get(t, -2)) < 1e-9 for t in sync)
    checks["kj_mirror_sync"] = {"pass": mirror_ok, "live": sync, "db": db}

    # aux_referee.score_set with as_of (learn may be empty → 0.5)
    sc = aux_referee.score_set([1, 2, 3, 4, 5, 6], [], 1236, brain_tag="stat")
    checks["aux_score_set_range"] = {"pass": 0.0 <= sc <= 1.0, "score": sc}

    fails = [k for k, v in checks.items() if not v.get("pass")]
    result = {
        "id": "K-REFEREE-BY-BRAIN-WIRE",
        "ts": _now(),
        "knobs": rbb.knobs_snapshot(),
        "checks": checks,
        "verdict": "WIRE_OK" if not fails else "WIRE_FAIL",
        "failed": fails,
        "ge3_used_as_claim": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-REFEREE-BY-BRAIN-WIRE",
        "",
        f"시각: {result['ts']}",
        f"## 판정 **{result['verdict']}**",
        "",
        f"failed={fails}",
        "",
        "## knobs",
        "```json",
        json.dumps(result["knobs"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## checks",
        "```json",
        json.dumps(checks, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", result["verdict"], "failed", fails)
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
