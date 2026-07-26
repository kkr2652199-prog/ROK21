#!/usr/bin/env python3
"""afterFileEdit: ROK21 동결 토큰·R34 역방향 차단 (exit 2)."""
from __future__ import annotations

import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# R34 역방향: ROK21 기록에 1~3군 내용 금지
R34_KEYWORDS = ("1군", "2군", "3군", "memoy", "My_Library", "MONEY lol")
STATUS_MARKERS = (
    "my_drive_sync/summary/status_latest.md",
    "my_drive_sync/summary/status_latest.txt",
    "my_drive_sync/summary/boot.md",
    "my_drive_sync/summary/resume_here.md",
)
# 동결: KWEON_ALLOW_FROZEN=1 없이는 수정 차단
FROZEN_SUFFIX = ("predict_statistical.py",)
FROZEN_TOKENS = ("random.choices", "_get_draws_before")
# 소속 미확인 — 차단 대신 경고
WARN_SEGMENTS = ("app/lotto/", "app/lotto2/")
WARN_MSG = "[미확인영역] app/lotto·lotto2 소속 불명. MAP.md 확정 전 신중히."


def _norm(p: str) -> str:
    return p.replace("\\", "/").lower()


def _edit_text(edits: list) -> str:
    return "".join(e.get("new_string") or "" for e in (edits or []) if isinstance(e, dict))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.stderr.write("[guard_paths] stdin JSON 파싱 실패\n")
        sys.exit(0)

    allow = os.environ.get("KWEON_ALLOW_FROZEN") == "1"
    path_norm = _norm(payload.get("file_path") or "")
    combined = _edit_text(payload.get("edits") or [])

    if not allow and any(path_norm.endswith(s) for s in FROZEN_SUFFIX):
        if any(tok in combined for tok in FROZEN_TOKENS):
            sys.stderr.write("동결영역(random.choices / 백테 컨닝방지). 형 승인 필요\n")
            sys.exit(2)

    if any(m in path_norm for m in STATUS_MARKERS):
        hit = [k for k in R34_KEYWORDS if k in combined]
        if hit:
            sys.stderr.write(f"R34 위반: ROK21 기록에 1~3군 내용 금지 ({', '.join(hit)})\n")
            sys.exit(2)

    if any(seg in path_norm for seg in WARN_SEGMENTS):
        sys.stderr.write(f"{WARN_MSG}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
