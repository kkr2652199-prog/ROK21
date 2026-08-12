# -*- coding: utf-8 -*-
"""K-REPACK-READ-LEDGER — LIST_V3 L4 검증.

원장 SSOT 소비 · no_peek · EMA 단독 탈피 · 1236 계약 재검증.
역할슬롯/강제BT/S1 IMMEDIATE = 범위 밖.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FRAME_DRAW = 1236  # 마지막 확정 · 1237아님
SEED_DRAWS = (1234, 1235)  # target=1236 읽기용 (draw_no < 1236)
BENCH = ROOT / "docs" / "benchmarks" / "20260812_KREPACK_READ_LEDGER.json"
REPORT = ROOT / "reports" / "20260812_KREPACK_READ_LEDGER.md"


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_hit_ledger import (
        LEDGER_TABLE,
        SCATTER_TABLE,
        assert_no_peek_read,
        write_pool_hit_ledger,
    )
    from app.testlotto.signal_pool import (
        LEDGER_BLEND,
        LEDGER_SIGNAL_WIRE,
        build_pool_and_repack,
        last_ledger_consume,
        tune_snapshot,
    )

    init_testlotto_db()

    # 선행: target=1236이 읽을 과거 원장 시드 (1236 자체는 유지·재기록 OK)
    seed_writes = []
    for d in SEED_DRAWS:
        wr = write_pool_hit_ledger(d, note="L4_SEED")
        seed_writes.append({"draw_no": d, "ok": wr.get("ok"), "n_ledger": wr.get("n_ledger")})
        if not wr.get("ok"):
            print("FAIL seed", wr)
            return 1

    wr1236 = write_pool_hit_ledger(FRAME_DRAW, note="L4_CONTRACT_RECHECK")
    if not wr1236.get("ok"):
        print("FAIL 1236 rewrite", wr1236)
        return 1

    conn = get_lotto_db()
    try:
        n_ledger_1236 = conn.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE draw_no=?", (FRAME_DRAW,)
        ).fetchone()[0]
        n_scatter_1236 = conn.execute(
            f"SELECT COUNT(*) FROM {SCATTER_TABLE} WHERE draw_no=?", (FRAME_DRAW,)
        ).fetchone()[0]
        n_lt = conn.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE draw_no < ?", (FRAME_DRAW,)
        ).fetchone()[0]
    finally:
        conn.close()

    contract_ok = int(n_ledger_1236) == 45 and int(n_scatter_1236) == 6

    # 몰아주기 경로: target=1236 → draw_no<1236 원장 소비
    built = build_pool_and_repack(FRAME_DRAW)
    consume = last_ledger_consume()
    peek = assert_no_peek_read(FRAME_DRAW)

    # 원장 OFF vs ON 비교용 플래그 스냅 (실제 켜진 상태만 주장)
    knobs = tune_snapshot()
    repack_n = sum(len(v) for v in (built.get("repack_by_brain") or {}).values())

    checks = {
        "wire_flag": bool(LEDGER_SIGNAL_WIRE),
        "blend": float(LEDGER_BLEND),
        "build_ok": bool(built.get("ok")),
        "repack_sets_total": int(repack_n),
        "consumed": bool(consume.get("consumed")),
        "ema_solo_exit": bool(consume.get("ema_solo_exit")),
        "no_peek_consume": consume.get("no_peek_ok"),
        "no_peek_assert": bool(peek.get("ok")),
        "consume_n_draws": int(consume.get("n_draws") or 0),
        "consume_draw_range": consume.get("draw_range"),
        "contract_1236_ledger45": int(n_ledger_1236) == 45,
        "contract_1236_scatter6": int(n_scatter_1236) == 6,
        "ledger_rows_lt_1236": int(n_lt),
        "source": consume.get("source"),
        "skipped": consume.get("skipped"),
    }
    ok = (
        checks["wire_flag"]
        and checks["build_ok"]
        and checks["consumed"]
        and checks["ema_solo_exit"]
        and checks["no_peek_consume"]
        and checks["no_peek_assert"]
        and checks["contract_1236_ledger45"]
        and checks["contract_1236_scatter6"]
        and checks["repack_sets_total"] == 15
        and checks["consume_n_draws"] >= 1
    )

    bench = {
        "id": "K-REPACK-READ-LEDGER",
        "list": "LIST_V3",
        "step": "L4",
        "status": "WIRE_OK" if ok else "WIRE_FAIL",
        "ts_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "frame_draw": FRAME_DRAW,
        "seed_draws": list(SEED_DRAWS),
        "seed_writes": seed_writes,
        "contract_1236": {
            "n_ledger": int(n_ledger_1236),
            "n_scatter": int(n_scatter_1236),
            "ok": contract_ok,
            "actual": wr1236.get("actual"),
            "bonus": wr1236.get("bonus"),
        },
        "consume": consume,
        "checks": checks,
        "knobs": {
            "LEDGER_SIGNAL_WIRE": knobs.get("LEDGER_SIGNAL_WIRE"),
            "LEDGER_BLEND": knobs.get("LEDGER_BLEND"),
            "LEDGER_WINDOW_DRAWS": knobs.get("LEDGER_WINDOW_DRAWS"),
            "ASSEMBLE_MODE": knobs.get("ASSEMBLE_MODE"),
        },
        "role_wire": False,
        "s1_begin_immediate": False,
        "force_bt": False,
        "note": "focus_r1 경로=repack_by_brain 원장 블렌드 · 역할라벨 L4b · 1237아님 · ge3미클레임",
    }

    BENCH.parent.mkdir(parents=True, exist_ok=True)
    BENCH.write_text(json.dumps(bench, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# K-REPACK-READ-LEDGER — LIST_V3 L4",
        "",
        f"시각: {bench['ts_kst']} KST · **{bench['status']}** · wire=**True** · **1237아님** · ge3미클레임",
        "선행: L3 WIRE_OK · 형 L4 GO",
        "다음: **L4b** 역할슬롯 WIRE (게이트 후) · S1 IMMEDIATE는 L4 후 개별승인",
        "",
        "---",
        "",
        "## 실측",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| frame | {FRAME_DRAW} |",
        f"| seed_draws | {list(SEED_DRAWS)} |",
        f"| consumed | {checks['consumed']} |",
        f"| ema_solo_exit | {checks['ema_solo_exit']} |",
        f"| no_peek | {checks['no_peek_assert']} |",
        f"| consume_n_draws | {checks['consume_n_draws']} · range={checks['consume_draw_range']} |",
        f"| blend | {LEDGER_BLEND} |",
        f"| 1236 ledger/scatter | {n_ledger_1236}/{n_scatter_1236} |",
        f"| repack sets | {checks['repack_sets_total']} |",
        "",
        "## consume 로그",
        "",
        "```json",
        json.dumps(consume, ensure_ascii=False, indent=2),
        "```",
        "",
        f"벤치: `{BENCH.relative_to(ROOT).as_posix()}`",
        "",
        "## 비범위",
        "",
        "- 역할슬롯(L4b) · S1 BEGIN IMMEDIATE · 강제BT · prefer/prize 게이트",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": bench["status"], "checks": checks}, ensure_ascii=False, indent=2))
    print("bench:", BENCH)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
