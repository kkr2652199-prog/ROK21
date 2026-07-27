# -*- coding: utf-8 -*-
"""K-D verify: 클릭 경로=coordinator only · fusion 미배선 · 3+4 유지."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "benchmarks" / "20260728_KD_fusion_path.json"
ENGINE = ROOT / "app" / "testlotto" / "engine.py"
COORD = ROOT / "app" / "testlotto" / "brains" / "coordinator.py"
FUSION = ROOT / "app" / "testlotto" / "fusion.py"


def _fn_calls(path: Path, fn_name: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            names: list[str] = []
            for n in ast.walk(node):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Name):
                        names.append(f.id)
                    elif isinstance(f, ast.Attribute):
                        names.append(f.attr)
            return names
    return []


def _imports_from(path: Path, module_substr: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and module_substr in node.module:
            for a in node.names:
                hits.append(a.name)
        if isinstance(node, ast.Import):
            for a in node.names:
                if module_substr in a.name:
                    hits.append(a.name)
    return hits


def main() -> int:
    calls = _fn_calls(ENGINE, "run_prediction")
    eng_fusion_imports = _imports_from(ENGINE, "fusion")
    src_e = ENGINE.read_text(encoding="utf-8")
    src_f = FUSION.read_text(encoding="utf-8")
    src_c = COORD.read_text(encoding="utf-8")

    from app.testlotto.brains.coordinator import AUX_WEIGHTS, AUX_MODULES, PREDICT_MODULES
    from app.testlotto.brains.registry import AUX_BRAINS, PREDICT_BRAINS

    checks = {
        "run_prediction_calls_coordinator": "run_coordinated_prediction" in calls,
        "run_prediction_no_vector_fusion": "_vector_fusion_predict" not in calls,
        "engine_no_fusion_import": len(eng_fusion_imports) == 0,
        "engine_doc_mentions_KD": "K-D" in src_e[:800],
        "fusion_doc_mentions_unwired": "미배선" in src_f[:600] or "K-D" in src_f[:600],
        "coordinator_doc_mentions_KD": "K-D" in src_c[:400],
        "predict_3": len(PREDICT_BRAINS) == 3 and len(PREDICT_MODULES) == 3,
        "aux_4": len(AUX_BRAINS) == 4 and len(AUX_MODULES) == 4,
        "aux_weights_equal": AUX_WEIGHTS == [0.25, 0.25, 0.25, 0.25],
    }
    verify_pass = all(checks.values())
    payload = {
        "task": "K-D",
        "run_prediction_calls": calls,
        "engine_fusion_imports": eng_fusion_imports,
        "active_path": "engine.run_prediction → coordinator.run_coordinated_prediction",
        "fusion_status": "present_file_unwired_from_click_path",
        "registry": {
            "predict": [b["tag"] for b in PREDICT_BRAINS],
            "aux": [b["tag"] for b in AUX_BRAINS],
            "AUX_WEIGHTS": AUX_WEIGHTS,
        },
        "checks": checks,
        "verify_pass": verify_pass,
        "note": "재배선(fusion 연결) 금지 · 3+4 유지 · 예측력 무관 · 문서/기대흐름 정합",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
