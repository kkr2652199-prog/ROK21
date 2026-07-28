# -*- coding: utf-8 -*-
"""K-PIPE-A — walk-forward에 coordinator AUX scoring 적용 검증."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260728_KPIPE_unify.json"


def main() -> int:
    from app.testlotto.brains.coordinator import PREDICT_MODULES, apply_coordinator_scoring
    from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    draw_no = 1234
    checks: dict[str, bool] = {}
    samples: dict[str, object] = {}

    set_learn_as_of(draw_no)
    draws = _get_draws_before(draw_no)
    checks["draws_before_1234"] = len(draws) > 0

    mod = PREDICT_MODULES["stat"]
    raw = mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
    checks["stat_raw_sets"] = len(raw) >= 1

    scored = apply_coordinator_scoring(copy.deepcopy(raw), draws, draw_no)
    checks["stat_scored_sets"] = len(scored) == len(raw)

    nums_unchanged = all(
        list(r.get("nums") or []) == list(s.get("nums") or []) for r, s in zip(raw, scored)
    )
    checks["nums_unchanged_after_aux"] = nums_unchanged

    conf_changed = any(
        float(r.get("confidence") or 0) != float(s.get("confidence") or 0) for r, s in zip(raw, scored)
    )
    checks["confidence_adjusted"] = conf_changed

    aux_marker = all("[보조4뇌:" in (s.get("reasoning") or "") for s in scored)
    checks["reasoning_has_aux_marker"] = aux_marker

    # walkforward 모듈이 apply_coordinator_scoring import
    import app.testlotto.walkforward as wf

    checks["walkforward_imports_pipe"] = hasattr(wf, "apply_coordinator_scoring") or (
        "apply_coordinator_scoring" in open(wf.__file__, encoding="utf-8").read()
    )

    samples["stat_set1"] = {
        "raw_conf": raw[0].get("confidence") if raw else None,
        "scored_conf": scored[0].get("confidence") if scored else None,
        "nums": list(scored[0].get("nums") or []) if scored else [],
        "reasoning_prefix": (scored[0].get("reasoning") or "")[:120] if scored else "",
    }

    verify_pass = all(checks.values())
    payload = {
        "task": "K-PIPE-A",
        "fix": "walkforward review_single_draw uses apply_coordinator_scoring + clear_history_cache",
        "checks": checks,
        "samples": samples,
        "verify_pass": verify_pass,
        "note": "기존 brain_review 행은 재복습 전까지 구 reasoning 유지",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
