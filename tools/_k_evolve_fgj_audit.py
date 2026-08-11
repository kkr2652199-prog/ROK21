# -*- coding: utf-8 -*-
"""K-EVOLVE-REFEREE + K-F/G/J 잔여 감사 (READ · wire=False).

리스트 4·5: evolve weight_applied / referee 실효 · markov learn(K-F) · ending(K-G) · 가중이중(K-J).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KEVOLVE_FGJ_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260811_KEVOLVE_FGJ_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"


def _db() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    return c


def audit() -> dict[str, Any]:
    from app.testlotto.learn_state import get_referee_weights, load_learn_state
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    import app.testlotto.brains.predict_flow_shaman as markov_mod

    conn = _db()
    try:
        tabs = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        evolve_n = (
            conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]
            if "testlotto_evolve_log" in tabs
            else -1
        )
        wa = {"n": 0, "nonzero": 0, "distinct": [], "sample": []}
        if evolve_n > 0:
            rows = conn.execute(
                "SELECT weight_applied, COUNT(*) c FROM testlotto_evolve_log GROUP BY weight_applied ORDER BY c DESC"
            ).fetchall()
            wa["distinct"] = [{"weight_applied": r[0], "count": r[1]} for r in rows]
            wa["n"] = evolve_n
            wa["nonzero"] = sum(r[1] for r in rows if float(r[0] or 0) != 0.0)
        bw = []
        if "testlotto_brain_weights" in tabs:
            bw = [dict(r) for r in conn.execute("SELECT * FROM testlotto_brain_weights").fetchall()]
        learn_n = (
            conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0]
            if "testlotto_brain_learn_state" in tabs
            else 0
        )
    finally:
        conn.close()

    set_learn_as_of(1236)
    referee = get_referee_weights()
    spreads = max(referee.values()) - min(referee.values()) if referee else None

    # K-F: markov engine consumes learn boost?
    src = Path(markov_mod.__file__).read_text(encoding="utf-8") if hasattr(markov_mod, "__file__") else ""
    # also package engine
    eng = ROOT / "app" / "testlotto" / "brains" / "markov_brain" / "engine.py"
    eng_src = eng.read_text(encoding="utf-8") if eng.exists() else ""
    kf = {
        "finding": "K-F",
        "markov_imports_learn": ("load_learn_state" in src) or ("load_learn_state" in eng_src) or ("get_boost" in eng_src),
        "predict_flow_shaman_path": getattr(markov_mod, "__file__", None),
        "engine_has_boost": ("boost" in eng_src.lower()) and ("learn" in eng_src.lower()),
        "status": "OPEN_LIKELY" if not (
            ("load_learn_state" in eng_src) or ("apply_boost" in eng_src)
        ) else "CHECK_MANUAL",
    }

    # K-G ending
    st = load_learn_state("review")
    kg = {
        "finding": "K-G",
        "ending_digit_boost_in_state": st.get("ending_digit_boost"),
        "path_exists_learn_state": True,
        "status": "DORMANT" if float(st.get("ending_digit_boost") or 0) == 0.0 else "ACTIVE",
    }

    # K-J dual weights
    live = referee
    db_w = {r.get("brain_tag") or r.get("brain"): r.get("current_weight") for r in bw}
    kj = {
        "finding": "K-J",
        "live_referee": live,
        "db_brain_weights": db_w,
        "spread_live": spreads,
        "status": "DUAL_OPEN" if db_w and live else "PARTIAL",
        "note": "DB current_weight vs live referee — SSOT 불명 유지",
    }

    evolve = {
        "evolve_rows": evolve_n,
        "weight_applied": wa,
        "phase1_fixed_zero": wa["n"] == 0 or wa["nonzero"] == 0,
        "recommendation": "weight_applied Phase1=0 유지 중이면 엔진 노브만 더 돌려도 학습루프 귀속 불가 → 배선 설계 후 튜닝",
    }

    return {
        "id": "K-EVOLVE-FGJ-AUDIT",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "wire": False,
        "evolve_referee": evolve,
        "referee_live": {"weights": live, "spread": spreads, "learn_state_rows": learn_n},
        "K-F": kf,
        "K-G": kg,
        "K-J": kj,
        "verdict": "AUDIT_DONE",
        "next_patch_suggestions": [
            "K-F: markov engine에 learn boost 소비 배선(형승인·동결주의)",
            "K-G: ending_digit_boost 활성화는 성적게이트 필요·지금은 DORMANT 기록",
            "K-J: referee live를 SSOT로 문서화하거나 DB sync 패치",
            "evolve: weight_applied≠0 설계는 별도 지시서",
        ],
    }


def main() -> int:
    payload = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = f"""# K-EVOLVE-FGJ-AUDIT

📅 2026-08-11 · READ · wire=False

## evolve / referee
- evolve_rows={payload['evolve_referee']['evolve_rows']}
- weight_applied nonzero={payload['evolve_referee']['weight_applied'].get('nonzero')}
- phase1_fixed_zero={payload['evolve_referee']['phase1_fixed_zero']}
- live referee={payload['referee_live']['weights']} spread={payload['referee_live']['spread']}

## K-F markov learn
- {payload['K-F']}

## K-G ending
- {payload['K-G']}

## K-J dual
- {payload['K-J']}

## 다음 패치 제안
""" + "\n".join(f"- {x}" for x in payload["next_patch_suggestions"])
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", payload["verdict"])
    print(json.dumps({k: payload[k] for k in ("evolve_referee", "referee_live", "K-F", "K-G", "K-J")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
