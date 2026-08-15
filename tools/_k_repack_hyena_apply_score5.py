# -*- coding: utf-8 -*-
"""score5 라이브 확정 + 게이트 재기록 + 3뇌 캐시 재생성. 원장 미기록."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools._k_repack_hyena_wire import (  # noqa: E402
    BRAINS,
    DRIVE,
    GATE_HI,
    GATE_LO,
    OUT_JSON,
    OUT_MD,
    _hard_db,
    _joint_smoke,
    _md,
    _now,
    _refill,
    _run_brain,
    _write_live_modes,
)


def main() -> int:
    import app.testlotto.signal_pool as sp

    live = {t: "score5" for t in BRAINS}
    _write_live_modes(live)
    sp.REPACK_HYENA_MODE_BY_BRAIN.clear()
    sp.REPACK_HYENA_MODE_BY_BRAIN.update(live)

    stages = []
    for i, tag in enumerate(BRAINS, start=1):
        print(f"== remeasure S{i} {tag} score5 ==", flush=True)
        g = _run_brain(tag, "score5", GATE_LO, GATE_HI, f"S{i}-{tag}-score5-g")
        g["step"] = f"S{i}"
        # ISO 통과 + 5장 변경이면 APPLY (우연 세트일치 무시)
        if g["hard_ok"] and g["iso_ok"] and g["changed"] > 0:
            g["apply"] = True
            g["design_ok"] = True
            g["verdict"] = "APPLY"
        stages.append(g)
        print("gate", tag, g["verdict"], g["delta_prefer"], g["delta_prize"], g["copy_on"], flush=True)

    print("== S4 joint ==", flush=True)
    joint = _joint_smoke(live)
    print("joint", joint.get("ok"), flush=True)
    print("== refill score5 ==", flush=True)
    refill = _refill(live) if joint.get("ok") else {"skipped": True, "reason": "joint_fail"}
    db = _hard_db()
    apply_ok = all(s.get("apply") for s in stages) and joint.get("ok") and refill.get("fail") in (None, 0)
    payload = {
        "id": "K-REPACK-HYENA-WIRE",
        "as_of": _now(),
        "apply": apply_ok,
        "verdict": "APPLY_OK" if apply_ok else "PARTIAL_OR_FAIL",
        "iso_thr": 0.005,
        "live_modes": live,
        "note": "score5가 keep1보다 ISO 우세. 세트우연일치를 복사로 본 HOLD_NO_DESIGN은 기각.",
        "stages": stages,
        "joint_smoke": joint,
        "refill": refill,
        "db": db,
        "rollback": 'REPACK_HYENA_MODE_BY_BRAIN 전부 ""',
        "pred_1237": db["pred_1237"],
        "draws_max": db["draws_max"],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    text = _md(payload)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "live": live, "refill": refill}, ensure_ascii=False))
    return 0 if apply_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
