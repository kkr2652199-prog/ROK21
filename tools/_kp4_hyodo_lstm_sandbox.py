# -*- coding: utf-8 -*-
"""K-P4 verify: hyodo LSTM 재학습 샌드박스 — 프로덕션 ckpt 미침범 · as_of 컷오프."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "benchmarks" / "20260727_KP4_hyodo_lstm.json"
AS_OF = 1235
SANDBOX_EPOCHS = 8


def _get_draws_before(target_draw_no: int) -> list[dict]:
    from app.hyodo.data_service import _get_draws_before

    return _get_draws_before(target_draw_no)


def _pmf_stats(pmf: dict[int, float]) -> dict:
    vals = list(pmf.values())
    u = 1.0 / 45.0
    spread = max(vals) - min(vals)
    chi2 = sum((v - u) ** 2 / u for v in vals)
    top3 = sorted(pmf.items(), key=lambda x: -x[1])[:3]
    return {
        "sum": round(sum(vals), 9),
        "min": round(min(vals), 9),
        "max": round(max(vals), 9),
        "spread": round(spread, 9),
        "chi2_vs_uniform": round(chi2, 6),
        "top3": [{"num": int(k), "p": round(float(v), 6)} for k, v in top3],
    }


def _run_once(draws: list[dict]) -> tuple[dict[int, float], dict]:
    from app.hyodo.predict_lstm import get_lstm_prob_vector, lstm_runtime_status, reset_lstm_runtime

    reset_lstm_runtime()
    pmf = get_lstm_prob_vector(draws)
    status = lstm_runtime_status()
    return pmf, status


def main() -> int:
    os.environ["ROK21_HYODO_LSTM_SANDBOX"] = "1"
    os.environ["ROK21_LSTM_EPOCHS"] = str(SANDBOX_EPOCHS)

    from app.hyodo.predict_lstm import SANDBOX_CKPT_PATH, SEQ_LEN, resolve_ckpt_path

    prod_ckpt = ROOT / "models" / "lstm_hyodo.pt"
    draws_full = _get_draws_before(AS_OF)
    n_full = len(draws_full)

    checks: dict[str, bool | str] = {}
    errors: list[str] = []

    if n_full < SEQ_LEN + 1:
        errors.append(f"draws<{SEQ_LEN + 1}: n={n_full}")
        checks["enough_draws"] = False
    else:
        checks["enough_draws"] = True

    # 프로덕션 ckpt mtime 스냅샷 (있을 때만)
    prod_mtime_before = prod_ckpt.stat().st_mtime if prod_ckpt.is_file() else None

    if SANDBOX_CKPT_PATH.is_file():
        SANDBOX_CKPT_PATH.unlink()

    pmf_full, st_full = _run_once(draws_full)
    stats_full = _pmf_stats(pmf_full)

    checks["torch_ok"] = bool(st_full.get("torch_ok"))
    checks["sandbox_flag"] = bool(st_full.get("sandbox"))
    checks["sandbox_ckpt_written"] = bool(st_full.get("ckpt_exists"))
    checks["pmf_sum_ok"] = abs(stats_full["sum"] - 1.0) < 1e-5
    checks["pmf_non_uniform"] = stats_full["spread"] > 1e-4
    checks["trained_len_match"] = int(st_full.get("last_trained_len") or 0) == n_full

    # as_of 누수 스모크: 짧은 창 vs 전체 → top1 번호 또는 spread 차이
    cut = min(n_full, SEQ_LEN + 80)
    draws_short = draws_full[:cut]
    pmf_short, _ = _run_once(draws_short)
    stats_short = _pmf_stats(pmf_short)
    top_full = stats_full["top3"][0]["num"] if stats_full["top3"] else 0
    top_short = stats_short["top3"][0]["num"] if stats_short["top3"] else 0
    checks["cutoff_changes_pmf"] = (
        top_full != top_short or abs(stats_full["spread"] - stats_short["spread"]) > 1e-5
    )

    prod_mtime_after = prod_ckpt.stat().st_mtime if prod_ckpt.is_file() else None
    if prod_mtime_before is None and prod_mtime_after is None:
        checks["prod_ckpt_untouched"] = True
    elif prod_mtime_before is not None and prod_mtime_after is not None:
        checks["prod_ckpt_untouched"] = abs(prod_mtime_after - prod_mtime_before) < 1e-6
    else:
        checks["prod_ckpt_untouched"] = False

    verify_pass = all(v is True for v in checks.values()) and not errors

    payload = {
        "task": "K-P4",
        "as_of": AS_OF,
        "draw_count": n_full,
        "seq_len": SEQ_LEN,
        "sandbox_epochs": SANDBOX_EPOCHS,
        "sandbox_ckpt": str(resolve_ckpt_path()),
        "prod_ckpt": str(prod_ckpt),
        "runtime_after_full": st_full,
        "pmf_full": stats_full,
        "pmf_short_window": {"draw_count": len(draws_short), **stats_short},
        "checks": checks,
        "errors": errors,
        "verify_pass": verify_pass,
        "note": "적중↑ 목표 아님 · PMF·컷오프·ckpt 격리 검증만",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "out": str(OUT), "checks": checks}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
