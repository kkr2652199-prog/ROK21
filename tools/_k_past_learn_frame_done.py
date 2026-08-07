# -*- coding: utf-8 -*-
"""K-PAST-LEARN-FRAME-DONE — 과거학습 기본 틀 잠금 (세부 튜닝 전).

Usage:
  python tools/_k_past_learn_frame_done.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_FRAME_DONE.json"
OUT_MD = ROOT / "reports" / "20260808_KPAST_LEARN_FRAME_DONE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name


def main() -> int:
    for k in (
        "K_STAT_ENG_SHORT_WIN",
        "K_STAT_ENG_SHORT_MIX",
        "K_STAT_ENGINE_V2",
        "K_PAST_LEARN_ASSOC",
        "K_STAT_TRANSITION_V1",
    ):
        os.environ.pop(k, None)
    os.environ["K_PAST_LEARN_ASSOC"] = "0"

    from app.testlotto.brains.stat_brain import past_learn
    from app.testlotto.brains.stat_brain.predict import run
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    fw = past_learn.framework_snapshot()
    set_learn_as_of(1235)
    sets = run(_get_draws_before(1235), 5)
    smoke_ok = (
        len(sets) == 5
        and all(s.get("method") == "과거학습" for s in sets)
        and fw["engine_defaults"]["V2_SHORT_WIN"] == 26
        and abs(float(fw["engine_defaults"]["V2_SHORT_MIX"]) - 0.8) < 1e-9
        and fw["flags"]["PAST_LEARN_WIRE"]
        and fw["flags"]["PAST_LEARN_ENGINE_V2"]
        and not fw["fixed_off"]["TRANSITION_V1_WIRE"]
        and not fw["fixed_off"]["ASSOC_HINT"]
    )
    payload = {
        "id": "K-PAST-LEARN-FRAME-DONE",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "FRAME_LOCKED" if smoke_ok else "FAIL",
        "smoke_ok": smoke_ok,
        "framework": fw,
        "sample_methods": [s.get("method") for s in sets],
        "sample_nums": sets[0].get("nums") if sets else [],
        "meaning_for_beginner": {
            "done": "과거학습 뇌 기본 파이프·엔진 기본값(26/0.8) 잠금",
            "not_yet": "decay·세부 가중 같은 미세 튜닝은 다음 단계",
            "other_brains": "markov/review 미변경",
            "fusion": "n200 ge3=0.135 유지(APPLY 근거)",
        },
        "next_detail": "K-PAST-LEARN-DETAIL-TUNE (decay 등) · 형 GO",
        "tool": "tools/_k_past_learn_frame_done.py",
        "priors": fw["evidence"],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# K-PAST-LEARN-FRAME-DONE — 기본 틀 잠금 (2026-08-08)",
        "",
        f"- **판정:** `{payload['verdict']}` · smoke_ok=`{smoke_ok}`",
        "",
        "## 초보용 요약",
        "",
        "1. **끝난 것(틀):** 과거학습 뇌가 돌아가는 길 + 엔진 기본값 win**26**/mix**0.8**",
        "2. **아직 안 함(세부):** decay·더 미세한 가중 조절",
        "3. **안 건드림:** markov / review · transition OFF · ASSOC OFF",
        "4. **전체 발권:** fusion ge3 **0.135** 그대로(APPLY 때 확인)",
        "",
        "## 잠긴 기본값",
        "",
        f"- engine: `{fw['engine_defaults']}`",
        f"- pipe: `{fw['pipe']}`",
        f"- 롤백 win/mix: `{fw['engine_defaults']['rollback_win_mix']}`",
        "",
        f"- 다음: `{payload['next_detail']}`",
        f"- tool: `{payload['tool']}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "smoke_ok": smoke_ok}, ensure_ascii=False), flush=True)
    return 0 if smoke_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
