#!/usr/bin/env python3
"""beforeSubmitPrompt: ROK21 동적 컨텍스트 주입 (continue=true · 최대 15줄)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 동일 디렉터리 모듈
sys.path.insert(0, str(Path(__file__).resolve().parent))

FALLBACK = """[ROK21] HEAD=unknown · SSOT=ROK21/7021 · kweon=264de3c동결
[지금] 미확인
[직전] 미확인
[BOOT다음] 미확인
[NEXT] 미확인
[WORK] IDLE
[경고] 동결: random.choices / _get_draws_before / boost상한
[경고] 원본 kweon 쓰기·push 금지
[경고] 수치 원본=docs/benchmarks/*.json
[규칙] 수치를 기억으로 쓰지 마라. 근거파일 없으면 '미확인'으로 중단하고 물어라."""


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    ctx = FALLBACK
    try:
        from rok21_inject import build_inject_text

        ctx = build_inject_text() or FALLBACK
    except Exception as exc:
        sys.stderr.write(f"[guard_boot] inject fallback: {exc}\n")
        ctx = FALLBACK

    # 줄 수 상한
    lines = [ln for ln in ctx.splitlines() if ln.strip()]
    if len(lines) > 15:
        lines = lines[:15]
        ctx = "\n".join(lines)

    out = {"continue": True, "additional_context": ctx}
    try:
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception:
        sys.stdout.write('{"continue": true, "additional_context": "[ROK21] inject-error"}')
    try:
        sys.stderr.write(f"[guard_boot]\n{ctx}\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
