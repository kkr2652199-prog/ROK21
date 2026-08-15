# -*- coding: utf-8 -*-
"""K-STAT-ONLY-CONSUME-RESTORE — 역할숙제 소비를 과거학습(stat)만으로 되돌림.

형 정정: 지금 진행=과거학습 뇌만. markov/review 숙제 200회는 하지 않음.
HARD: stat 1~10 이 3뇌소비 vs stat만소비에서 동일.
1237아님. DB쓰기 없음.
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_ONLY_CONSUME_RESTORE.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_ONLY_CONSUME_RESTORE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SMOKE_LO, SMOKE_HI = 1234, 1236
GATE_LO, GATE_HI = 1137, 1236
SEED = 42
WIDE = frozenset({"stat", "markov", "review"})
STAT = frozenset({"stat"})


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _pool_stat(draws, dno: int, *, brains: frozenset[str]) -> list[tuple[int, ...]]:
    import app.testlotto.signal_pool as sp

    old = sp.ROLE_TIER_LEARN_BRAINS
    sp.ROLE_TIER_LEARN_BRAINS = frozenset(brains)
    try:
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=["stat"])
        rows = sorted(
            [s for s in pool if str(s.get("brain_tag")) == "stat"],
            key=lambda s: int(s.get("set_no") or 0),
        )
        return [_key(s.get("nums") or []) for s in rows]
    finally:
        sp.ROLE_TIER_LEARN_BRAINS = old


def _run(lo: int, hi: int, label: str) -> dict[str, Any]:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (lo, hi),
        ).fetchall()
    finally:
        conn.close()

    t0 = time.perf_counter()
    n_ok = peek_fail = size_bad = stat_same = 0
    errors: list[str] = []
    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek_fail += 1
            continue
        try:
            wide = _pool_stat(draws, dno, brains=WIDE)
            only = _pool_stat(draws, dno, brains=STAT)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(wide) != 10 or len(only) != 10:
            size_bad += 1
            continue
        if wide == only:
            stat_same += 1
        n_ok += 1
        if (i + 1) % 20 == 0 or dno == hi:
            print(f"  [{label}] {i+1}/{len(rows)} d={dno} same={stat_same}", flush=True)
    return {
        "label": label,
        "lo": lo,
        "hi": hi,
        "n_ok": n_ok,
        "n_target": hi - lo + 1,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:8],
        "stat_same": stat_same,
    }


def main() -> int:
    import app.testlotto.signal_pool as sp

    print("== SMOKE ==", flush=True)
    smoke = _run(SMOKE_LO, SMOKE_HI, "smoke")
    smoke_hard = (
        smoke["n_ok"] == 3
        and smoke["peek_fail"] == 0
        and smoke["size_bad"] == 0
        and smoke["n_errors"] == 0
        and smoke["stat_same"] == 3
    )
    print("smoke_hard", smoke_hard, flush=True)
    gate = None
    if smoke_hard:
        print("== GATE n100 ==", flush=True)
        gate = _run(GATE_LO, GATE_HI, "gate100")
    hard = bool(
        smoke_hard
        and gate
        and gate["n_ok"] == 100
        and gate["peek_fail"] == 0
        and gate["size_bad"] == 0
        and gate["n_errors"] == 0
        and gate["stat_same"] == 100
    )
    if hard:
        verdict = "RESTORE_OK"
        sp.ROLE_TIER_LEARN_BRAINS = STAT
    else:
        verdict = "FAIL"
        sp.ROLE_TIER_LEARN_BRAINS = STAT
    out = {
        "id": "K-STAT-ONLY-CONSUME-RESTORE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "review_bt200_ran": False,
        "live_brains_after": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "smoke": smoke,
        "smoke_hard": smoke_hard,
        "gate100": gate,
        "hard_ok": hard,
        "verdict": verdict,
        "note": "형 정정: 진행=과거학습만. markov/review WIRE 보고서는 보존·라이브 소비에서 제외.",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = "\n".join([
        "# K-STAT-ONLY-CONSUME-RESTORE — 역할숙제 소비를 과거학습만으로",
        "",
        f"시각: {out['as_of']} · **{verdict}** · ge3미클레임 · 1237아님",
        "",
        "## 0) 한 줄",
        "",
        "형이 「과거학습 뇌만」이라고 정정했다. review 200회는 **실행하지 않았다**. "
        "라이브 소비를 `{stat}` 만으로 되돌렸다. markov/review 숙제 배선 코드·보고서는 남긴다.",
        "",
        "## 1) HARD",
        "",
        f"- 스모크 1234~1236 stat동일 {smoke.get('stat_same')}/3",
        f"- 게이트 1137~1236 stat동일 {(gate or {}).get('stat_same')}/{(gate or {}).get('n_ok')}",
        f"- peek={(gate or {}).get('peek_fail')} err={(gate or {}).get('n_errors')} size={(gate or {}).get('size_bad')}",
        f"- 라이브 BRAINS=`{out['live_brains_after']}`",
        "",
        "## 2) 하지 않은 것",
        "",
        "- K-REVIEW-ROLE-LEARN-BT200 리셋+200회",
        "- markov/review S1~S4 복사",
        "",
        "## 3) 다음",
        "",
        "과거학습 다음 1건은 형 지시. 1237아님.",
        "",
    ])
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "hard": hard,
        "live": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "stat_same": (gate or {}).get("stat_same"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
