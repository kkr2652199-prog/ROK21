"""효도로또(app/hyodo) → 테스트로또(app/testlotto) 격리 복제."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "app" / "hyodo"
DST = ROOT / "app" / "testlotto"

REPLACEMENTS = [
    ("app.hyodo", "app.testlotto"),
    ("lotto_hyodo.db", "lotto_testlotto.db"),
    ("lotto_patterns_hyodo.db", "lotto_patterns_testlotto.db"),
    ("lstm_hyodo.pt", "lstm_testlotto.pt"),
    ("hyodo_brain_weights", "testlotto_brain_weights"),
    ("init_hyodo_db", "init_testlotto_db"),
    ('prefix="/api/hyodo"', 'prefix="/api/testlotto"'),
    ('tags=["hyodo"]', 'tags=["testlotto"]'),
    ("효도로또", "테스트로또"),
    ("app.hyodo 독립 패키지", "app.testlotto 독립 패키지 (테스트용)"),
]


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    for src in sorted(SRC.glob("*.py")):
        text = src.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        (DST / src.name).write_text(text, encoding="utf-8")
        print(f"copied: {src.name}")

    (DST / "__init__.py").write_text(
        '"""테스트로또 — 효도로또 복제·격리 테스트 패키지."""\n',
        encoding="utf-8",
    )
    print("done:", DST)


if __name__ == "__main__":
    main()
