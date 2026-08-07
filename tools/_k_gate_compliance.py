# -*- coding: utf-8 -*-
"""K-GATE-COMPLIANCE — R38 판정 게이트 준수 검사 (READ-ONLY).

두 가지를 한다.

1. **자기검증** — `tools/k_gate` 가 확정 수치를 재현하는지 확인한다.
   실패하면 게이트 자체를 신뢰할 수 없으므로 즉시 비정상 종료한다.

2. **준수 검사** — `docs/benchmarks/*.json` 을 훑어, 비교·선택 주장을 담은 벤치가
   `decision_gate` 블록을 기록했는지 본다.

   오늘 이전에 만들어진 벤치는 **legacy** 로 한 번 스냅샷하고 면제한다(기록물이므로
   소급 수정하지 않는다). 스냅샷 이후 새로 생기거나 legacy 목록에 없는 벤치가
   비교 주장을 하면서 게이트를 빼먹으면 **FAIL** 로 잡는다.

Usage:
  python tools/_k_gate_compliance.py

정책: READ-ONLY (자기 산출물 2개만 씀) · DB 미접촉 · 벤치 원본 무수정.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.k_gate import GATE_KEY, GATE_RULE, self_test  # noqa: E402

BENCH_DIR = ROOT / "docs" / "benchmarks"
OUT_JSON = BENCH_DIR / "20260808_KGATE_COMPLIANCE.json"
OUT_MD = ROOT / "reports" / "20260808_KGATE_COMPLIANCE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BENCH_ID = "K-GATE-COMPLIANCE"

# 비교·선택 주장의 흔적이 되는 키 이름 조각
CLAIM_HINTS = (
    "delta",
    "vs_base",
    "vs_null",
    "vs_baseline",
    "vs_pin",
    "best",
    "candidate",
    "grid",
    "n_cells",
    "sweep",
    "holdout",
    "tune_",
    "improve",
)
# 게이트가 필요 없는 순수 기록물 표식
RECORD_ONLY_VERDICTS = ("CATALOG", "DESIGN_HOLD", "SNAPSHOT", "MEASURED_ONLY")

MAX_DEPTH = 6


def walk_keys(obj: Any, depth: int = 0) -> list[str]:
    """중첩 dict/list 의 키 이름을 모은다 (깊이 제한)."""
    if depth > MAX_DEPTH:
        return []
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.append(str(k))
            found.extend(walk_keys(v, depth + 1))
    elif isinstance(obj, list):
        for v in obj[:50]:
            found.extend(walk_keys(v, depth + 1))
    return found


def looks_comparative(obj: dict[str, Any]) -> tuple[bool, list[str]]:
    keys = [k.lower() for k in walk_keys(obj)]
    hits = sorted({h for h in CLAIM_HINTS if any(h in k for k in keys)})
    return (len(hits) > 0, hits)


def has_gate(obj: dict[str, Any]) -> bool:
    return GATE_KEY in set(walk_keys(obj))


def load_prev_legacy() -> list[str] | None:
    if not OUT_JSON.exists():
        return None
    try:
        prev = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    legacy = prev.get("legacy_exempt")
    return list(legacy) if isinstance(legacy, list) else None


def scan() -> dict[str, Any]:
    files = sorted(p.name for p in BENCH_DIR.glob("*.json"))
    rows: list[dict[str, Any]] = []
    unreadable: list[str] = []

    for name in files:
        try:
            obj = json.loads((BENCH_DIR / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            unreadable.append(f"{name}: {type(e).__name__}")
            continue
        if not isinstance(obj, dict):
            continue
        comparative, hints = looks_comparative(obj)
        verdict_val = str(obj.get("verdict") or "")
        rows.append(
            {
                "file": name,
                "comparative": comparative,
                "hints": hints,
                "has_gate": has_gate(obj),
                "record_only": any(v in verdict_val for v in RECORD_ONLY_VERDICTS),
            }
        )

    prev_legacy = load_prev_legacy()
    first_run = prev_legacy is None
    if first_run:
        legacy = [r["file"] for r in rows if r["comparative"] and not r["has_gate"]]
    else:
        legacy = prev_legacy

    legacy_set = set(legacy)
    violations = [
        r
        for r in rows
        if r["comparative"]
        and not r["has_gate"]
        and not r["record_only"]
        and r["file"] not in legacy_set
    ]
    compliant = [r for r in rows if r["has_gate"]]

    return {
        "n_files": len(files),
        "n_readable": len(rows),
        "unreadable": unreadable,
        "rows": rows,
        "first_run": first_run,
        "legacy_exempt": sorted(legacy),
        "violations": violations,
        "compliant": [r["file"] for r in compliant],
    }


def build_report(p: dict[str, Any]) -> str:
    st = p["module_self_test"]
    sc = p["scan"]
    lines = [
        f"# {BENCH_ID} — R38 판정 게이트 준수 검사",
        "",
        f"- 날짜: {p['date']} · **판정: {p['verdict']['code']}**",
        f"- {p['verdict']['headline_ko']}",
        "- 정책: READ-ONLY · 벤치 원본 무수정 · DB 미접촉",
        "",
        "## 1. 게이트 모듈 자기검증",
        "",
        f"**{'전부 통과' if st['all_pass'] else '실패'}** ({st['n_checks']}개 검사)",
        "",
        "| 검사 | 계산값 | 기대값 | 통과 |",
        "|---|---|---|---|",
    ]
    for c in st["checks"]:
        lines.append(f"| {c['name']} | {c['got']} | {c['want']} | {'O' if c['pass'] else '**X**'} |")

    lines += [
        "",
        "자기검증이 하는 일: null 을 초기하분포로 계산한 값이 2026-07-30 몬테카를로",
        "측정치와 일치하는지, 눈금 수치가 재현되는지, 그리고 **적용상수 win26/mix0.8 이",
        "다시 넣어도 `NOISE_SELECTION_CONFIRMED` 로 판정되는지** 확인한다.",
        "이 중 하나라도 깨지면 게이트를 쓰는 모든 판정을 신뢰할 수 없다.",
        "",
        "## 2. 벤치마크 준수 현황",
        "",
        f"- 검사 파일: **{sc['n_files']}**개 (읽기 성공 {sc['n_readable']})",
        f"- 비교·선택 주장 포함: **{p['counts']['comparative']}**개",
        f"- `{GATE_KEY}` 기록됨: **{p['counts']['with_gate']}**개",
        f"- legacy 면제(오늘 스냅샷): **{len(sc['legacy_exempt'])}**개",
        f"- **위반: {len(sc['violations'])}개**",
        "",
    ]
    if sc["first_run"]:
        lines += [
            "이번이 최초 실행이므로, 현재 존재하는 비교성 벤치는 전부 **legacy 로 스냅샷**하고",
            "면제했다. 기록물을 소급 수정하지 않는다는 원칙 때문이다.",
            "다음 실행부터는 이 목록에 없는 새 벤치가 게이트를 빼먹으면 위반으로 잡힌다.",
            "",
        ]
    if sc["violations"]:
        lines += ["### 위반 목록", "", "| 파일 | 주장 흔적 |", "|---|---|"]
        for v in sc["violations"]:
            lines.append(f"| `{v['file']}` | {', '.join(v['hints'])} |")
        lines.append("")
    else:
        lines += ["위반 없음.", ""]

    if sc["unreadable"]:
        lines += ["### 읽기 실패", ""] + [f"- {u}" for u in sc["unreadable"]] + [""]

    lines += [
        "## 3. R38 요약",
        "",
        "모든 튜닝·비교 도구는 판정 전에 다음을 호출하고 결과를 벤치 JSON 의",
        f"`{GATE_KEY}` 키에 넣는다.",
        "",
        "```python",
        "from tools.k_gate import gate_block",
        "",
        'payload["decision_gate"] = gate_block(',
        "    n=200, k_cells=9, delta=0.012, metric=\"ge3\",",
        "    holdout_value=0.118, label=\"short_decay 스윕\",",
        ")",
        "```",
        "",
        "`actionable` 이 False 면 그 판정은 **차이 없음**으로 보고한다. 등급은 네 가지다.",
        "",
        "| 등급 | 뜻 |",
        "|---|---|",
        "| DECIDABLE | 선택보정 임계를 넘음 → 차이 주장 가능 |",
        "| SELECTION_SUSPECT | K셀 탐색 잡음 범위 안 → 근거 불충분 |",
        "| UNDECIDABLE | 단일비교 최소검출차 미달 → 주장 불가 |",
        "| NOISE_SELECTION_CONFIRMED | 홀드아웃이 null 구간으로 붕괴 → 폐기 |",
        "",
        "## 4. 한계",
        "",
        "- 비교성 판정은 **키 이름 기반 휴리스틱**이다. 이름이 특이한 벤치는 놓칠 수 있다.",
        f"  현재 탐지 단서: {', '.join(CLAIM_HINTS)}",
        "- legacy 면제는 최초 실행 시점의 스냅샷이다. 면제된 벤치의 과거 주장은",
        "  `reports/20260808_KSTAT_DECISION_GATE.md` 의 소급감사를 참고하라.",
        "- 이 도구는 게이트 기록 **유무**만 본다. 기록된 `n`·`k_cells` 가 정직한지는",
        "  검증하지 않는다. 특히 `k_cells` 를 실제 탐색량보다 작게 적으면 임계가 느슨해진다.",
        "",
        f"근거 원본: `docs/benchmarks/{OUT_JSON.name}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    st = self_test()
    sc = scan()

    counts = {
        "comparative": sum(1 for r in sc["rows"] if r["comparative"]),
        "with_gate": sum(1 for r in sc["rows"] if r["has_gate"]),
        "violations": len(sc["violations"]),
    }

    if not st["all_pass"]:
        code = "MODULE_SELF_TEST_FAIL"
        head = "게이트 모듈이 확정 수치를 재현하지 못함 — 모든 게이트 판정 보류"
    elif sc["violations"]:
        code = "VIOLATIONS_FOUND"
        head = f"게이트 미기록 벤치 {len(sc['violations'])}건 — 해당 판정은 차이 없음으로 취급"
    elif sc["first_run"]:
        code = "BASELINE_SET"
        head = (
            f"자기검증 {st['n_checks']}/{st['n_checks']} 통과 · "
            f"legacy {len(sc['legacy_exempt'])}건 스냅샷 · 이후 신규 벤치부터 강제"
        )
    else:
        code = "COMPLIANT"
        head = f"자기검증 통과 · 위반 없음 (게이트 기록 {counts['with_gate']}건)"

    payload: dict[str, Any] = {
        "bench_id": BENCH_ID,
        "date": "2026-08-08",
        "rule": GATE_RULE,
        "gate_key": GATE_KEY,
        "wire": False,
        "policy": {"read_only": True, "db_write": False, "bench_mutation": False},
        "module_self_test": st,
        "counts": counts,
        "scan": sc,
        "legacy_exempt": sc["legacy_exempt"],
        "verdict": {"code": code, "headline_ko": head},
        "prior": "docs/benchmarks/20260808_KSTAT_DECISION_GATE.json",
        "tool": "tools/_k_gate_compliance.py",
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = build_report(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(f"[{BENCH_ID}] {code} — {head}")
    print(f"  self_test {st['n_checks']}건 all_pass={st['all_pass']}")
    print(
        f"  파일 {sc['n_files']} · 비교성 {counts['comparative']} · 게이트기록 "
        f"{counts['with_gate']} · legacy {len(sc['legacy_exempt'])} · 위반 {counts['violations']}"
    )
    for v in sc["violations"]:
        print(f"  VIOLATION {v['file']}  hints={','.join(v['hints'])}")
    print(f"  bench  -> {OUT_JSON}")
    print(f"  report -> {OUT_MD}")
    return 0 if st["all_pass"] and not sc["violations"] else 1


if __name__ == "__main__":
    sys.exit(main())
