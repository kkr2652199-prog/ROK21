# -*- coding: utf-8 -*-
"""READ-ONLY 3DB MAX + overlap mismatch smoke for pin baseline."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUM_KEY = ("num1", "num2", "num3", "num4", "num5", "num6", "bonus")


def load_map(path: Path) -> dict[int, tuple]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    q = f"SELECT draw_no,{','.join(NUM_KEY)} FROM lotto_draws"
    out = {int(r[0]): tuple(r[1:]) for r in con.execute(q)}
    con.close()
    return out


def main() -> int:
    paths = {
        "lotto4": ROOT / "data" / "lotto4.db",
        "testlotto": ROOT / "data" / "lotto_testlotto.db",
        "hyodo": ROOT / "data" / "lotto_hyodo.db",
    }
    stats = {}
    for k, p in paths.items():
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        mn, mx, cnt = con.execute(
            "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM lotto_draws"
        ).fetchone()
        con.close()
        stats[k] = {"min": mn, "max": mx, "count": cnt}
    src = load_map(paths["lotto4"])
    mism = {}
    for label in ("testlotto", "hyodo"):
        dst = load_map(paths[label])
        mism[label] = sorted(n for n in set(src) & set(dst) if src[n] != dst[n])
    ok = all(s["max"] == 1234 for s in stats.values()) and all(
        len(v) == 0 for v in mism.values()
    )
    out = {"stats": stats, "mismatches": mism, "pass": ok}
    p = ROOT / "docs" / "benchmarks" / "20260727_PIN_3db_smoke.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("pass", ok, "WROTE", p)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
