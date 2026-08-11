# -*- coding: utf-8 -*-
"""K-I-BRAIN-FALLBACK-WIRE — 단일 뇌 예외 시 타뇌 계속 검증.

mock으로 markov.predict_sets 를 깨뜨린 뒤 expand_pool / coordinator 경로가
stat·review 를 남기는지 확인. DB 영구쓰기 최소(predict 호출 시 발생 가능) —
대상회차는 기존 예측 삭제 후 필터로 markov만 깨짐 재현.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KI_BRAIN_FALLBACK_WIRE.json"
OUT_MD = ROOT / "reports" / "20260812_KI_BRAIN_FALLBACK_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

TARGET = 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _boom(*_a, **_k):
    raise RuntimeError("K-I mock brain failure")


def main() -> None:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains import coordinator as coord
    from app.testlotto.brains.markov_brain import predict as mk
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(TARGET)
    draws = _get_draws_before(TARGET)
    saved_mk = mk.predict_sets
    saved_coord = coord.PREDICT_MODULES["markov"].predict_sets

    checks: dict[str, Any] = {}
    try:
        mk.predict_sets = _boom  # type: ignore[assignment]
        # signal_pool 은 tools PREDICT_MODULES 를 쓰므로 그쪽도 패치
        from tools._k_window_signal_survey import PREDICT_MODULES as SPM

        saved_spm = SPM["markov"].predict_sets
        SPM["markov"].predict_sets = _boom  # type: ignore[method-assign]
        coord.PREDICT_MODULES["markov"].predict_sets = _boom  # type: ignore[method-assign]

        pool = sp.expand_pool(draws, TARGET, seed=42)
        by = sp._pool_by_brain(pool)
        tags = {t: len(by.get(t, [])) for t in sp.BRAIN_TAGS}
        checks["expand_pool"] = {
            "tags": tags,
            "markov_zero": tags.get("markov", 0) == 0,
            "others_ok": tags.get("stat", 0) > 0 and tags.get("review", 0) > 0,
            "no_raise": True,
        }

        # coordinator: brain_filter로 3뇌 모두 돌리되 markov만 boom
        out = coord.run_coordinated_prediction(TARGET, brain_filter=None)
        err = out.get("error")
        be = out.get("brain_errors") or {}
        # 응답에 predictions / sets 가 있으면 생존
        n_pred = 0
        if isinstance(out, dict) and not err:
            preds = out.get("predictions") or out.get("sets") or []
            if isinstance(preds, list):
                n_pred = len(preds)
            # cached shape
            for k in ("by_brain", "predict_by_brain", "results"):
                if isinstance(out.get(k), dict):
                    n_pred = max(n_pred, sum(len(v or []) for v in out[k].values()))
        checks["coordinator"] = {
            "error": err,
            "brain_errors": be,
            "markov_in_errors": "markov" in be,
            "survived": err is None and "markov" in be,
            "n_pred_hint": n_pred,
            "status": out.get("status") if isinstance(out, dict) else None,
        }
        SPM["markov"].predict_sets = saved_spm
    finally:
        mk.predict_sets = saved_mk
        coord.PREDICT_MODULES["markov"].predict_sets = saved_coord

    ok = (
        checks["expand_pool"]["markov_zero"]
        and checks["expand_pool"]["others_ok"]
        and checks["coordinator"]["survived"]
    )
    verdict = "WIRE_OK" if ok else "WIRE_FAIL"

    out = {
        "id": "K-I-BRAIN-FALLBACK-WIRE",
        "ts": _now(),
        "target": TARGET,
        "checks": checks,
        "verdict": verdict,
        "wire": True,
        "note": "K-I · 1237아님 · ge3미사용",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-I-BRAIN-FALLBACK-WIRE

시각: {out['ts']} · target={TARGET}

## 판정 **{verdict}**

### expand_pool
`{checks['expand_pool']}`

### coordinator
`{checks['coordinator']}`

## 패치
- `coordinator.run_coordinated_prediction` 뇌별 try/except · `brain_errors`
- `signal_pool.expand_pool` 뇌별 try/except
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print("WROTE", OUT_JSON)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
