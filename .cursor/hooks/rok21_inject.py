# -*- coding: utf-8 -*-
"""ROK21 압축복귀 컨텍스트 빌더 — guard_boot / RESTORE 헤더 공통 소스.

읽기 전용. 예외를 밖으로 던지지 않고 안전한 기본값 반환.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
ROOT = HOOKS_DIR.parents[1]
SUMMARY = ROOT / "My_Drive_Sync" / "SUMMARY"
BOOT = SUMMARY / "BOOT.md"
NEXT_ACTIONS = SUMMARY / "NEXT_ACTIONS.md"
MAX_LINES = 15


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def short_head() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        h = (r.stdout or "").strip()
        return h or "unknown"
    except OSError:
        return "unknown"


def parse_boot_section1(text: str | None = None) -> list[str]:
    raw = text if text is not None else _safe_read(BOOT)
    m = re.search(
        r"## 1\) 현재 스레드[^\n]*\n((?:- .*\n){1,5})",
        raw,
    )
    if not m:
        return ["- 지금: 미확인", "- 직전: 미확인", "- 다음: 미확인"]
    lines = [ln.rstrip() for ln in m.group(1).splitlines() if ln.strip().startswith("-")]
    while len(lines) < 3:
        lines.append("- (미확인)")
    return lines[:3]


def parse_next_block(text: str | None = None) -> dict[str, str]:
    raw = text if text is not None else _safe_read(NEXT_ACTIONS)
    out = {
        "id": "미확인",
        "todo": "미확인",
        "precond": "없음",
        "need_approval": "미확인",
        "updated": "미확인",
    }
    m = re.search(r"## NEXT \(1건\)\s*\n(.*?)(?=\n## |\Z)", raw, re.S)
    if not m:
        return out
    block = m.group(1)
    for key, pat in (
        ("id", r"-\s*ID:\s*(.+)"),
        ("todo", r"-\s*할일:\s*(.+)"),
        ("precond", r"-\s*선행조건:\s*(.+)"),
        ("need_approval", r"-\s*승인필요:\s*(.+)"),
        ("updated", r"-\s*최종갱신:\s*(.+)"),
    ):
        mm = re.search(pat, block)
        if mm:
            out[key] = mm.group(1).strip()
    return out


def parse_workstate(text: str | None = None) -> str:
    raw = text if text is not None else _safe_read(NEXT_ACTIONS)
    m = re.search(r"## WORKSTATE\s*\n([^\n#]+)", raw)
    if not m:
        return "IDLE"
    s = m.group(1).strip()
    return s or "IDLE"


def build_inject_lines() -> list[str]:
    head = short_head()
    boot_lines = parse_boot_section1()
    nxt = parse_next_block()
    work = parse_workstate()
    next_one = f"{nxt['id']}: {nxt['todo']}"

    def _strip_label(ln: str) -> str:
        s = ln.lstrip("- ").strip()
        for pref in ("지금:", "직전:", "다음:"):
            if s.startswith(pref):
                return s[len(pref) :].strip()
        return s

    lines = [
        f"[ROK21] HEAD={head} · SSOT=ROK21/7021 · kweon=264de3c동결",
        f"[지금] {_strip_label(boot_lines[0])}",
        f"[직전] {_strip_label(boot_lines[1])}",
        f"[BOOT다음] {_strip_label(boot_lines[2])}",
        f"[NEXT] {next_one}",
        f"[WORK] {work}",
        "[경고] 동결: random.choices / _get_draws_before / boost상한",
        "[경고] 원본 kweon(D:\\3kweon) 쓰기·push·신규작업 금지",
        "[경고] 수치 원본=docs/benchmarks/*.json (BOOT/STATUS는 사본)",
        "[규칙] 수치를 기억으로 쓰지 마라. 근거파일 없으면 '미확인'으로 중단하고 물어라.",
    ]
    return lines[:MAX_LINES]


def build_inject_text() -> str:
    return "\n".join(build_inject_lines())


def build_restore_resume_block() -> str:
    """RESTORE 상단 「동생 복귀 5줄」 — inject와 동일 소스."""
    head = short_head()
    boot_lines = parse_boot_section1()
    nxt = parse_next_block()
    work = parse_workstate()

    def _strip_label(ln: str) -> str:
        s = ln.lstrip("- ").strip()
        for pref in ("지금:", "직전:", "다음:"):
            if s.startswith(pref):
                return s[len(pref) :].strip()
        return s

    now = _strip_label(boot_lines[0])
    next_one = f"{nxt['id']} — {nxt['todo']}"
    lines = [
        "<!-- ROK21_RESUME_BLOCK -->",
        "## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)",
        "",
        f"1. **HEAD:** `{head}` · WORK=`{work}`",
        f"2. **지금:** {now}",
        f"3. **다음1건:** {next_one} (승인필요={nxt['need_approval']} · 선행={nxt['precond']})",
        "4. **SSOT충돌:** 수치=`docs/benchmarks/*.json` · 결함=`FINDINGS.md` · 라벨=`WARRANT.md` 가 원본. BOOT/STATUS/RESTORE는 사본.",
        "5. **금지요약:** 동결토큰·kweon미접촉·컨닝금지·DB전체초기화금지·1~3군기록금지·채팅간략≠문서압축.",
        "",
        "> 큐: **동생, ROK21 RESTORE.md 읽고 시작해.**",
        "<!-- /ROK21_RESUME_BLOCK -->",
    ]
    return "\n".join(lines)


def sync_restore_header() -> bool:
    """RESTORE.md 상단 마커 블록을 공통 소스로 갱신. 실패 시 False."""
    path = SUMMARY / "RESTORE.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    block = build_restore_resume_block()
    if "<!-- ROK21_RESUME_BLOCK -->" in text and "<!-- /ROK21_RESUME_BLOCK -->" in text:
        new = re.sub(
            r"<!-- ROK21_RESUME_BLOCK -->.*?<!-- /ROK21_RESUME_BLOCK -->",
            block,
            text,
            count=1,
            flags=re.S,
        )
    else:
        # insert after title line
        parts = text.split("\n", 1)
        if len(parts) == 2:
            new = parts[0] + "\n\n" + block + "\n\n" + parts[1]
        else:
            new = block + "\n\n" + text
    try:
        path.write_text(new, encoding="utf-8")
        return True
    except OSError:
        return False
