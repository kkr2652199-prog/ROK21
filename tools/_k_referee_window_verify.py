# -*- coding: utf-8 -*-
"""K-REFEREE-WINDOW verify — 슬라이딩 윈도우 recent_avg_match.

기본: brain_review matched 시계열을 apply_feedback_pure 로 재생 후
      전역 learn_state 1회 저장 + cutoff history rebuild.
옵션: --full-wf → review_single_draw 2~1234 (느림·예측 SSOT 변경)

Usage:
  python tools/_k_referee_window_verify.py
  python tools/_k_referee_window_verify.py --full-wf
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260729_KREFEREE_WINDOW.json"
BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 2, 1234


def _cumulative_avgs(events: list[tuple[int, str, int]]) -> dict[str, float]:
    rc = {b: 0 for b in BRAINS}
    avg = {b: 0.0 for b in BRAINS}
    for _dn, tag, matched in events:
        if tag not in avg:
            continue
        rc[tag] += 1
        prev = avg[tag]
        avg[tag] = ((prev * (rc[tag] - 1)) + matched) / rc[tag]
    return {b: round(avg[b], 4) for b in BRAINS}


def _load_events() -> list[tuple[int, str, int, list[str]]]:
    from app.testlotto.learn_state_cutoff import _load_feedback_events

    return [
        (dn, tag, matched, missed)
        for dn, tag, matched, missed in _load_feedback_events()
        if D_LO <= dn <= D_HI and tag in BRAINS
    ]


def _replay_pure(
    events: list[tuple[int, str, int, list[str]]],
) -> dict[str, dict[str, Any]]:
    from app.testlotto.learn_state import PREDICT_BRAIN_TAGS, _empty_state, save_learn_state
    from app.testlotto.learn_state_cutoff import apply_feedback_pure
    from app.testlotto.models import init_testlotto_db
    from app.testlotto.learn_state import reset_learn_states

    init_testlotto_db()
    reset_learn_states()
    states = {tag: _empty_state() for tag in PREDICT_BRAIN_TAGS}
    for dn, tag, matched, missed in events:
        if tag not in states:
            continue
        states[tag] = apply_feedback_pure(states[tag], dn, matched, missed)

    for tag, st in states.items():
        save_learn_state(tag, st)

    out: dict[str, dict[str, Any]] = {}
    for tag in PREDICT_BRAIN_TAGS:
        st = states[tag]
        out[tag] = {
            "recent_avg_match": float(st.get("recent_avg_match") or 0),
            "review_count": int(st.get("review_count") or 0),
            "window_len": len(st.get("recent_match_window") or []),
            "last_draw_no": int(st.get("last_draw_no") or 0),
        }
    return out


def _cutoff_as_of() -> dict[str, dict[str, Any]]:
    from app.testlotto.learn_state import PREDICT_BRAIN_TAGS, REFEREE_WINDOW
    from app.testlotto.learn_state_cutoff import (
        clear_history_cache,
        ensure_history_built,
        rebuild_state_as_of,
    )

    clear_history_cache()
    ensure_history_built()
    out = {}
    for tag in PREDICT_BRAIN_TAGS:
        st = rebuild_state_as_of(tag, D_HI + 1)
        out[tag] = {
            "recent_avg_match": float(st.get("recent_avg_match") or 0),
            "review_count": int(st.get("review_count") or 0),
            "window_len": len(st.get("recent_match_window") or []),
            "last_draw_no": int(st.get("last_draw_no") or 0),
            "referee_window": REFEREE_WINDOW,
        }
    return out


def _run_full_wf() -> dict[str, Any]:
    from app.testlotto.learn_state import (
        PREDICT_BRAIN_TAGS,
        reset_learn_states,
        _load_global_learn_state,
    )
    from app.testlotto.learn_state_cutoff import clear_history_cache
    from app.testlotto.models import init_testlotto_db
    from app.testlotto.walkforward import run_review_loop

    init_testlotto_db()
    clear_history_cache()
    reset_learn_states()
    os.environ.setdefault("ROK21_LEARN_CUTOFF", "1")
    t0 = time.perf_counter()
    summary = run_review_loop(D_LO, D_HI, progress_every=50)
    elapsed = round(time.perf_counter() - t0, 1)
    finals = {}
    for tag in PREDICT_BRAIN_TAGS:
        st = _load_global_learn_state(tag)
        finals[tag] = {
            "recent_avg_match": float(st.get("recent_avg_match") or 0),
            "review_count": int(st.get("review_count") or 0),
            "window_len": len(st.get("recent_match_window") or []),
        }
    return {
        "reviewed": summary.get("reviewed"),
        "skipped": summary.get("skipped"),
        "elapsed_sec": elapsed,
        "finals": finals,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-wf", action="store_true")
    args = ap.parse_args()

    from app.testlotto.learn_state import REFEREE_WINDOW
    from app.testlotto.learn_state_cutoff import clear_history_cache

    clear_history_cache()
    events = _load_events()
    flat = [(dn, tag, m) for dn, tag, m, _ in events]
    before = _cumulative_avgs(flat)

    t0 = time.perf_counter()
    global_after = _replay_pure(events)
    cutoff_after = _cutoff_as_of()
    replay_sec = round(time.perf_counter() - t0, 2)

    avgs = {b: global_after[b]["recent_avg_match"] for b in BRAINS}
    cutoff_avgs = {b: cutoff_after[b]["recent_avg_match"] for b in BRAINS}
    cutoff_sync = all(abs(avgs[b] - cutoff_avgs[b]) < 1e-6 for b in BRAINS)

    vals = list(avgs.values())
    max_gap = round(max(vals) - min(vals), 4) if vals else 0.0
    passed = max_gap >= 0.01

    full_wf_block: dict[str, Any] | None = None
    if args.full_wf:
        full_wf_block = _run_full_wf()
        avgs = {b: full_wf_block["finals"][b]["recent_avg_match"] for b in BRAINS}
        vals = list(avgs.values())
        max_gap = round(max(vals) - min(vals), 4)
        passed = max_gap >= 0.01

    out = {
        "id": "K-REFEREE-WINDOW",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "window_size": REFEREE_WINDOW,
        "method": (
            "full_wf_review_single_draw"
            if args.full_wf
            else "feedback_replay_pure_then_save"
        ),
        "draw_range": [D_LO, D_HI],
        "n_events": len(events),
        "before_cumulative_avg": before,
        "final_recent_avg_match": avgs,
        "cutoff_final_recent_avg_match": cutoff_avgs,
        "global_detail": global_after,
        "cutoff_detail": cutoff_after,
        "cutoff_matches_global": cutoff_sync,
        "max_gap": max_gap,
        "pass": bool(passed and (cutoff_sync or args.full_wf)),
        "replay_elapsed_sec": replay_sec,
        "full_wf": full_wf_block,
        "note": (
            "누적평균이면 셋 다 ≈0.80 · 패치 후 뇌간 격차 ≥0.01 이상. "
            "기본=matched 재생(공식). --full-wf=예측 SSOT 재기록."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "before": before,
                "after": avgs,
                "max_gap": max_gap,
                "pass": out["pass"],
                "cutoff_sync": cutoff_sync,
                "method": out["method"],
                "sec": replay_sec,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
