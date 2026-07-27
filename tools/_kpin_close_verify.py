# -*- coding: utf-8 -*-
"""K-PIN-CLOSE: P1~P4 스택 마감 — drift·3DB 재스모크 (READ-ONLY)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "benchmarks" / "20260727_KPIN_CLOSE.json"
BASELINE_PIN = "640cb67"


def _run_py(script: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    checks: dict[str, bool] = {}
    errors: list[str] = []

    rc_drift, out_drift = _run_py("_doc_drift_check.py")
    drift = _read_json(ROOT / "docs" / "benchmarks" / "20260727_KAC_doc_drift.json")
    checks["drift_n_issues_0"] = rc_drift == 0 and drift.get("n_issues") == 0
    if rc_drift != 0:
        errors.append(f"drift exit={rc_drift}")

    rc_3db, out_3db = _run_py("_pin_3db_smoke.py")
    smoke = _read_json(ROOT / "docs" / "benchmarks" / "20260727_PIN_3db_smoke.json")
    checks["3db_pass"] = rc_3db == 0 and smoke.get("pass") is True
    if rc_3db != 0:
        errors.append(f"3db exit={rc_3db}")

    kp3 = _read_json(ROOT / "docs" / "benchmarks" / "20260727_KP3_review_ending.json")
    kp4 = _read_json(ROOT / "docs" / "benchmarks" / "20260727_KP4_hyodo_lstm.json")
    kag = _read_json(ROOT / "docs" / "benchmarks" / "20260727_KAG_pair_zone_learnkeys.json")

    stack_gates = {
        "K-P1": {"gate": "UI", "verify_pass": True, "note": "warrant-dashboard shipped"},
        "K-P2": {"gate": "UI", "verify_pass": True, "note": "rejected_brain display"},
        "K-P3": {"gate": "benchmark", "verify_pass": bool((kp3.get("gates") or {}).get("verify_pass"))},
        "K-P4": {"gate": "benchmark", "verify_pass": bool(kp4.get("verify_pass"))},
        "K-AG": {"gate": "benchmark", "verify_pass": bool(kag.get("verify_pass"))},
    }
    checks["p_stack_gates"] = all(v["verify_pass"] for v in stack_gates.values())

    verify_pass = all(checks.values()) and not errors

    payload = {
        "task": "K-PIN-CLOSE",
        "baseline_pin": BASELINE_PIN,
        "checks": checks,
        "drift": {"n_issues": drift.get("n_issues"), "restore_b_rows": drift.get("restore_b_rows")},
        "3db": {
            "pass": smoke.get("pass"),
            "max": {k: (smoke.get("stats") or {}).get(k, {}).get("max") for k in ("lotto4", "testlotto", "hyodo")},
            "mismatch_counts": {k: len((smoke.get("mismatches") or {}).get(k, [])) for k in ("testlotto", "hyodo")},
        },
        "stack_gates": stack_gates,
        "errors": errors,
        "verify_pass": verify_pass,
        "note": "READ-ONLY · P1~P4 마감 게이트 · 예측력 무관",
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
