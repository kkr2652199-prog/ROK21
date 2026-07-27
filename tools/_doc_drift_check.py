# -*- coding: utf-8 -*-
"""K-AC 문서 드리프트 검사 (READ-ONLY · 자동수정 금지 · 보고만)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "My_Drive_Sync" / "SUMMARY"
OUT = ROOT / "docs" / "benchmarks" / "20260727_KAC_doc_drift.json"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def findings_status() -> dict[str, list[str]]:
    text = read(SUMMARY / "FINDINGS.md")
    rows = re.findall(r"^\| (K-[\w]+) \| (\w+) \|", text, re.M)
    out: dict[str, list[str]] = {}
    for kid, st in rows:
        out.setdefault(st, []).append(kid)
    return out


def restore_e_buckets(text: str) -> dict[str, set[str]]:
    m = re.search(r"## E\) 열린 결함(.*?)(?=\n## |\Z)", text, re.S)
    block = m.group(1) if m else ""
    buckets: dict[str, set[str]] = {"OPEN": set(), "HOLD": set(), "PATCHED": set(), "CLOSED": set()}
    for label in buckets:
        lm = re.search(rf"\*\*{label}[^*]*\*\*:?\s*(.*)", block)
        if lm:
            buckets[label] = set(re.findall(r"K-[\w]+", lm.group(1)))
    return buckets


def boot_section3(text: str) -> str:
    m = re.search(r"## 3\) 열린 과제.*?\n(.*?)(?=\n## |\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def restore_b_rows(text: str) -> int:
    m = re.search(r"## B\) 턴 로그.*?\n\|[^\n]+\n\|[^\n]+\n(.*?)(?=\n## |\Z)", text, re.S)
    if not m:
        return 0
    return len([ln for ln in m.group(1).splitlines() if ln.strip().startswith("|")])


def check_hyodo_max(restore: str, boot: str) -> list[dict]:
    issues: list[dict] = []
    try:
        import sqlite3

        p = ROOT / "data" / "lotto_hyodo.db"
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        mx = con.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
        con.close()
    except Exception as e:
        return [{"id": "DB_HYODO", "severity": "error", "detail": str(e)}]
    if mx != 1234:
        issues.append(
            {
                "id": "DB_HYODO_MAX",
                "severity": "unexpected",
                "detail": f"expected 1234 got {mx}",
            }
        )
    return issues


def main() -> int:
    findings = findings_status()
    open_hold = set(findings.get("OPEN", []) + findings.get("HOLD", []))
    patched = set(findings.get("PATCHED", []) + findings.get("CLOSED", []))
    restore = read(SUMMARY / "RESTORE.md")
    boot = read(SUMMARY / "BOOT.md")
    status = read(SUMMARY / "STATUS_LATEST.md")

    issues: list[dict] = []
    e_buckets = restore_e_buckets(restore)
    e_open = e_buckets["OPEN"]

    # PATCHED/CLOSED must not appear in E OPEN list
    for kid in sorted(e_open & patched):
        issues.append(
            {
                "id": f"E_STALE_OPEN_{kid}",
                "severity": "status_mismatch",
                "detail": f"{kid} in RESTORE E OPEN but FINDINGS={ 'PATCHED' if kid in findings.get('PATCHED', []) else 'CLOSED' }",
            }
        )

    # Critical OPEN missing from E OPEN (optional warn for subset starting K-0 and K-A single letter? keep soft)
    # Require K-06 present in OPEN if FINDINGS OPEN
    for must in ("K-06",):
        if must in findings.get("OPEN", []) and must not in e_open:
            issues.append(
                {
                    "id": f"E_MISSING_{must}",
                    "severity": "status_mismatch",
                    "detail": f"{must} OPEN in FINDINGS but missing from RESTORE E OPEN",
                }
            )

    b3 = boot_section3(boot)
    if re.search(r"K-07\s*=\s*\*\*OPEN\*\*", b3):
        issues.append(
            {
                "id": "BOOT3_K07",
                "severity": "status_mismatch",
                "detail": "BOOT §3 marks K-07 OPEN",
            }
        )

    nrows = restore_b_rows(restore)
    if nrows > 12:
        issues.append(
            {
                "id": "RESTORE_B_ROWS",
                "severity": "format",
                "detail": f"B절 {nrows}행 > 최대 12",
            }
        )

    issues.extend(check_hyodo_max(restore, boot))

    # F: obsolete exclusive pattern as the recommended glob
    fm = re.search(r"## F\) 더 읽을 파일(.*?)(?=\n## |\Z)", restore, re.S)
    fblock = fm.group(1) if fm else ""
    if re.search(r"최신 `reports/YYYYMMDD_ROK21_\*\.md`", fblock) or re.search(
        r"1\.\s*`?reports/YYYYMMDD_ROK21_", fblock
    ):
        issues.append(
            {
                "id": "RESTORE_F_PATTERN",
                "severity": "stale_pattern",
                "detail": "F절이 권장 글로브로 YYYYMMDD_ROK21_*.md 만 제시",
            }
        )

    cm = re.search(r"## C\) 확정 사실.*?\n(\|[^\n]+)", restore, re.S)
    if cm and "커밋" not in cm.group(1):
        issues.append(
            {
                "id": "RESTORE_C_HASH_COL",
                "severity": "missing_column",
                "detail": "C절에 최종확인 커밋해시 열 없음",
            }
        )

    gap = ROOT / "docs" / "benchmarks" / "20260727_KAB_draw_gap.json"
    if gap.exists():
        data = json.loads(gap.read_text(encoding="utf-8"))
        post = (data.get("step3") or {}).get("post_stats") or {}
        hy = post.get("hyodo") or {}
        if hy.get("max") == 1234:
            for ln in restore.splitlines():
                if "hyodo" in ln.lower() and "1231" in ln and "1234" not in ln:
                    issues.append(
                        {
                            "id": "RESTORE_HYODO_1231_LINE",
                            "severity": "stale_number",
                            "detail": ln.strip()[:120],
                        }
                    )

    if "K-06" in findings.get("OPEN", []) and re.search(r"K-06[^\n]*\*\*PATCHED\*\*", status):
        issues.append(
            {
                "id": "STATUS_K06",
                "severity": "status_mismatch",
                "detail": "STATUS marks K-06 PATCHED but FINDINGS OPEN",
            }
        )

    result = {
        "meta": {
            "read_only": True,
            "auto_fix": False,
            "disclaimer": "이 작업은 예측력과 무관하다. 압축으로 인한 방향 상실 방지다.",
        },
        "findings_counts": {k: len(v) for k, v in findings.items()},
        "findings_open_hold": sorted(open_hold),
        "restore_e_open": sorted(e_open),
        "restore_e_hold": sorted(e_buckets["HOLD"]),
        "restore_b_rows": nrows,
        "boot_section3": b3[:300],
        "issues": issues,
        "n_issues": len(issues),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("n_issues", len(issues))
    for i in issues:
        print("-", i["id"], i["severity"], str(i.get("detail", ""))[:100])
    print("WROTE", OUT)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
