# -*- coding: utf-8 -*-
"""K-H verify: 미등록 AUX 격리 · 3예측+4보조 유지 · import 0."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "benchmarks" / "20260728_KH_unused_aux.json"
BRAINS = ROOT / "app" / "testlotto" / "brains"
UNUSED = BRAINS / "_unused"
DEAD = ("aux_gap_scout.py", "aux_structure_guard.py")
LIVE_AUX = (
    "aux_miss_detective.py",
    "aux_pattern_spotlight.py",
    "aux_balance_keeper.py",
    "aux_referee.py",
)


def _py_files_under(app: Path) -> list[Path]:
    return [p for p in app.rglob("*.py") if "_unused" not in p.parts]


def _imports_name(path: Path, names: set[str]) -> list[str]:
    hits: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return hits
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if any(n in a.name for n in names):
                    hits.append(f"{path.name}:import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(n in mod for n in names):
                hits.append(f"{path.name}:from {mod}")
            for a in node.names:
                if a.name in names:
                    hits.append(f"{path.name}:from … import {a.name}")
    return hits


def main() -> int:
    names = {"aux_gap_scout", "aux_structure_guard", "gap_scout", "structure_guard"}
    import_hits: list[str] = []
    for p in _py_files_under(ROOT / "app"):
        import_hits.extend(_imports_name(p, names))

    from app.testlotto.brains.registry import AUX_BRAINS, PREDICT_BRAINS

    aux_tags = [b["tag"] for b in AUX_BRAINS]
    expected_aux = ["miss_aux", "pattern_aux", "balance_aux", "referee_aux"]
    checks = {
        "unused_dir_exists": UNUSED.is_dir(),
        "dead_files_in_unused": all((UNUSED / f).is_file() for f in DEAD),
        "dead_absent_from_brains_root": all(not (BRAINS / f).is_file() for f in DEAD),
        "live_aux_present": all((BRAINS / f).is_file() for f in LIVE_AUX),
        "predict_3": len(PREDICT_BRAINS) == 3,
        "aux_4": len(AUX_BRAINS) == 4,
        "aux_tags_ok": aux_tags == expected_aux,
        "no_live_imports": len(import_hits) == 0,
    }
    verify_pass = all(checks.values())

    payload = {
        "task": "K-H",
        "moved_to": str(UNUSED.relative_to(ROOT)).replace("\\", "/"),
        "files": list(DEAD),
        "import_hits_live_app": import_hits,
        "registry": {
            "predict": [b["tag"] for b in PREDICT_BRAINS],
            "aux": aux_tags,
        },
        "checks": checks,
        "verify_pass": verify_pass,
        "note": "재배선 금지 기본 · 3+4 구조 유지 · 예측력 무관",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "checks": checks, "out": str(OUT)}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
