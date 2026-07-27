#!/usr/bin/env python3
"""beforeSubmitPrompt: ROK21 컨텍스트 7줄 주입 (continue=true)."""
from __future__ import annotations

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CONTEXT_LINES = """[ROK21] SSOT=kkr2652199-prog/ROK21 main · D:\\ROK21 · 7021 / 4군·테스트로또·효도로또만
[R34] 1~3군·memoy·My_Library 내용 ROK21 기록 금지
[충돌방지] 원본 kweon(D:\\3kweon·6124·264de3c 동결) 미접촉 · 작업은 ROK21만
[동결] random.choices = B단계 전 수정 금지
[동결] 백테 컨닝 금지 (_get_draws_before: target 이전만)
[시작] SUMMARY/BOOT.md + FINDINGS.md 확인
[종료] 보고서+STATUS+BOOT 3줄+push(ROK21)"""


def main() -> None:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass
    out = {"continue": True, "additional_context": CONTEXT_LINES}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stderr.write(f"[guard_boot] {CONTEXT_LINES}\n")


if __name__ == "__main__":
    main()
