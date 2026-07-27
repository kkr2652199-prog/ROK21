#!/usr/bin/env python3
"""stop: ROK21 SSOT — 미커밋·당일 보고서 미작성 시 followup_message만 (절대 exit 2 금지)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
# 당일 보고서 검사 경로 (ROK21 SSOT)
REPORT_DIRS = (ROOT / "My_Drive_Sync" / "커서보고서", ROOT / "reports")
# 종료체크 dirty 스코프 — ROK21 작업 경로만 (kweon/memoy 제외)
ROK21_SCOPE = ("My_Drive_Sync/SUMMARY", "My_Drive_Sync/커서보고서",
               "reports", ".cursor", "app")


def _git_lines(args: list[str]) -> list[str]:
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", check=False)
    return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]


def _is_noise(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return (
        "/__pycache__/" in f"/{p}/"
        or p.endswith(".pyc")
        or p.endswith(".pyo")
        or p.endswith(".pyd")
    )


def _dirty() -> list[str]:
    out: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only", "HEAD", "--", *ROK21_SCOPE],
        ["git", "diff", "--cached", "--name-only", "--", *ROK21_SCOPE],
    ):
        out.update(x for x in _git_lines(cmd) if not _is_noise(x))
    return sorted(out)


def main() -> None:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass

    issues: list[str] = []
    try:
        d = _dirty()
        if d:
            issues.append("ROK21 경로 미커밋 변경: " + ", ".join(d[:5])
                          + (" ..." if len(d) > 5 else "") + " — commit+push 완료하세요.")
    except OSError as exc:
        issues.append(f"git diff 실행 실패: {exc}")

    today = datetime.now().strftime("%Y%m%d")
    if not any(p.exists() and list(p.glob(f"{today}_*.md")) for p in REPORT_DIRS):
        issues.append(f"{today}_*.md 보고서가 reports/ · 커서보고서/ 어디에도 없습니다.")

    if issues:
        sys.stdout.write(json.dumps(
            {"followup_message": "[ROK21 종료체크] " + " / ".join(issues)},
            ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
