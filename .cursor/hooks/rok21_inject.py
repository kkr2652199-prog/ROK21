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
FLOW_BRIEF = SUMMARY / "FLOW_BRIEF.md"
FINDINGS = SUMMARY / "FINDINGS.md"
EXTERNAL_START = ROOT / "EXTERNAL_START.md"
EXTERNAL_BOOTSTRAP = SUMMARY / "EXTERNAL_AI_BOOTSTRAP.md"
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
        "> 큐: **동생, EXTERNAL_START.md(또는 RESTORE) 읽고 시작해. GitHub 404면 형이 붙여준 LIVE 블록만 써.**",
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


def _findings_open_sample(limit: int = 3) -> str:
    raw = _safe_read(FINDINGS)
    opens: list[str] = []
    for m in re.finditer(
        r"\|\s*(K-[A-Z0-9]+)\s*\|\s*OPEN\s*\|",
        raw,
    ):
        opens.append(m.group(1))
        if len(opens) >= limit:
            break
    return ", ".join(opens) if opens else "(OPEN 없음/미확인)"


def build_flow_brief() -> str:
    """외부 AI 압축 대비 매턴 요약본 (≤15줄). GitHub이 살아 있는 전원."""
    head = short_head()
    boot = parse_boot_section1()
    nxt = parse_next_block()
    work = parse_workstate()

    def _strip(ln: str) -> str:
        s = ln.lstrip("- ").strip()
        for pref in ("지금:", "직전:", "다음:"):
            if s.startswith(pref):
                return s[len(pref) :].strip()
        return s

    lines = [
        "# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)",
        "",
        f"- HEAD: `{head}` · WORK=`{work}`",
        f"- 지금: {_strip(boot[0])}",
        f"- 직전: {_strip(boot[1])}",
        f"- BOOT다음: {_strip(boot[2])}",
        f"- NEXT1: {nxt['id']} — {nxt['todo']} (승인={nxt['need_approval']})",
        f"- OPEN샘플: {_findings_open_sample()}",
        "- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT",
        "- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축",
        "- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF",
        "- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.",
        "",
    ]
    return "\n".join(lines)


def read_baseline_pin() -> str:
    """PINNED_BASELINE.md 의 BASELINE_PIN — 없으면 HEAD."""
    path = SUMMARY / "PINNED_BASELINE.md"
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r"BASELINE_PIN:\s*`([^`]+)`", text)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return short_head()


def build_live_flow_block() -> str:
    """외부AI가 한 블록으로 흐름을 잡기 위한 LIVE 스냅샷."""
    head = short_head()
    boot = parse_boot_section1()
    nxt = parse_next_block()
    work = parse_workstate()

    def _strip(ln: str) -> str:
        s = ln.lstrip("- ").strip()
        for pref in ("지금:", "직전:", "다음:"):
            if s.startswith(pref):
                return s[len(pref) :].strip()
        return s

    now = _strip(boot[0])
    prev = _strip(boot[1])
    boot_next = _strip(boot[2])
    pin = read_baseline_pin()
    lines = [
        "<!-- ROK21_LIVE_FLOW -->",
        "## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)",
        "",
        f"| 키 | 값 |",
        f"|----|-----|",
        f"| HEAD(실측) | `{head}` |",
        f"| BASELINE_PIN | `{pin}` |",
        f"| WORK | `{work}` |",
        f"| 지금 | {now} |",
        f"| 직전 | {prev} |",
        f"| BOOT다음 | {boot_next} |",
        f"| NEXT1 ID | **{nxt['id']}** |",
        f"| NEXT1 할일 | {nxt['todo']} |",
        f"| 승인필요 | {nxt['need_approval']} |",
        f"| 선행 | {nxt['precond']} |",
        f"| OPEN샘플 | {_findings_open_sample()} |",
        "",
        "### 역할",
        "- 형=결정 · 동생(너)=판단·짧은 지시서 · 커서=실행·commit·push",
        "- 너는 D:\\ROK21 / 비공개 GitHub를 못 열 수 있다 → **이 LIVE 블록이 SSOT**",
        "- 404 = 권한 없음(경로 오류 아님). D:\\3kweon·memoy·1~3군 미접촉",
        "",
        "### 본선 vs 인프라",
        "- 테스트로또 **3예측+4보조 유지** (구조 해체 없음)",
        "- K-AB~AF = 수집/문서/훅(예측력 무관) · 인프라 지시 남발 금지",
        "- 형 방향 = 전제 실증·쓸모 (적중↑ 랜덤앱 아님)",
        "",
        "### 네가 할 일",
        f"1. 첫줄 `[복귀] HEAD={head} · 지금={now} · 다음={nxt['id']}`",
        "2. 승인 없으면 장문 지시서 금지 · 형에게 질문 1개",
        "3. 추가 파일 필요 시: `형, SUMMARY/○○.md 붙여줘`",
        "<!-- /ROK21_LIVE_FLOW -->",
    ]
    return "\n".join(lines)


def build_external_start() -> str:
    """레포 루트 EXTERNAL_START.md — 외부AI가 제일 먼저 볼 파일."""
    live = build_live_flow_block()
    # strip HTML comments for cleaner paste, keep content
    body = re.sub(r"<!--.*?-->\n?", "", live).strip()
    return "\n".join(
        [
            "# EXTERNAL_START — 외부 에이전트 작업 흐름 진입점",
            "",
            "> **이 파일 하나면 흐름 복구.** GitHub 404 / 로컬 미접근이면 형이 이 파일 전체를 채팅에 붙여넣는다.",
            "> 상세 복사용 프롬프트: `My_Drive_Sync/SUMMARY/EXTERNAL_AI_BOOTSTRAP.md`",
            "> **핀 베이스라인:** `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md`",
            "> 동생 큐(권한 있을 때): `My_Drive_Sync/SUMMARY/RESTORE.md`",
            "",
            body,
            "",
            "## 파일 지도 (권한 있을 때만)",
            "| 용도 | 경로 |",
            "|------|------|",
            "| 복귀5줄 | `My_Drive_Sync/SUMMARY/RESTORE.md` |",
            "| NEXT 1건 | `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |",
            "| 매턴요약 | `My_Drive_Sync/SUMMARY/FLOW_BRIEF.md` |",
            "| 결함 | `My_Drive_Sync/SUMMARY/FINDINGS.md` |",
            "| 명분 | `My_Drive_Sync/SUMMARY/WARRANT.md` |",
            "| 핀 베이스라인 | `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md` |",
            "| 수치 | `docs/benchmarks/*.json` |",
            "",
            f"_generated: {short_head()}_",
            "",
        ]
    )


def sync_flow_brief() -> bool:
    """FLOW_BRIEF.md 갱신. 실패 시 False."""
    try:
        FLOW_BRIEF.write_text(build_flow_brief(), encoding="utf-8")
        return True
    except OSError:
        return False


def sync_external_start() -> bool:
    try:
        EXTERNAL_START.write_text(build_external_start(), encoding="utf-8")
        return True
    except OSError:
        return False


def sync_external_bootstrap_live() -> bool:
    """EXTERNAL_AI_BOOTSTRAP.md 안의 LIVE 블록만 교체."""
    path = EXTERNAL_BOOTSTRAP
    block = build_live_flow_block()
    try:
        if not path.exists():
            path.write_text(
                "# EXTERNAL_AI_BOOTSTRAP\n\n" + block + "\n",
                encoding="utf-8",
            )
            return True
        text = path.read_text(encoding="utf-8")
        if "<!-- ROK21_LIVE_FLOW -->" in text and "<!-- /ROK21_LIVE_FLOW -->" in text:
            new = re.sub(
                r"<!-- ROK21_LIVE_FLOW -->.*?<!-- /ROK21_LIVE_FLOW -->",
                lambda _m: block,
                text,
                count=1,
                flags=re.S,
            )
        else:
            # insert after title
            parts = text.split("\n", 1)
            new = parts[0] + "\n\n" + block + "\n\n" + (parts[1] if len(parts) > 1 else "")
        path.write_text(new, encoding="utf-8")
        return True
    except OSError:
        return False


def sync_all_resume_docs() -> dict[str, bool]:
    """종료루틴: RESTORE + FLOW_BRIEF + EXTERNAL_START + BOOTSTRAP LIVE."""
    return {
        "restore": sync_restore_header(),
        "flow_brief": sync_flow_brief(),
        "external_start": sync_external_start(),
        "external_bootstrap": sync_external_bootstrap_live(),
    }
