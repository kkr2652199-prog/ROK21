# -*- coding: utf-8 -*-
"""K-POOL-HIT-LEDGER-WIRE — L3 검증.

샘플 회차(기본 1236) 원장 기록 · no_peek · 스키마 카운트 · 벤치 JSON.
역할슬롯 생성/몰아주기 소비는 L4·L4b (본 도구 범위 밖).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLE_DRAW = 1236
BENCH = ROOT / "docs" / "benchmarks" / "20260812_KPOOL_HIT_LEDGER_WIRE.json"
REPORT = ROOT / "reports" / "20260812_KPOOL_HIT_LEDGER_WIRE.md"


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_hit_ledger import (
        LEDGER_TABLE,
        SCATTER_TABLE,
        assert_no_peek_read,
        ledger_counts,
        write_pool_hit_ledger,
    )

    init_testlotto_db()
    dno = SAMPLE_DRAW

    # 테이블 존재
    conn = get_lotto_db()
    try:
        names = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        tables_ok = LEDGER_TABLE in names and SCATTER_TABLE in names
        draw_row = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=?",
            (dno,),
        ).fetchone()
    finally:
        conn.close()

    if not tables_ok:
        print("FAIL: tables missing")
        return 1
    if not draw_row:
        print(f"FAIL: draw {dno} missing")
        return 1

    wr = write_pool_hit_ledger(dno, note="L3_WIRE_VERIFY")
    print("write:", json.dumps(wr, ensure_ascii=False))
    if not wr.get("ok"):
        return 1

    # 샘플 요약
    conn = get_lotto_db()
    try:
        n_ledger = conn.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE draw_no=?", (dno,)
        ).fetchone()[0]
        n_scatter = conn.execute(
            f"SELECT COUNT(*) FROM {SCATTER_TABLE} WHERE draw_no=?", (dno,)
        ).fetchone()[0]
        by_kind = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT kind, COUNT(*) AS n, MAX(hits) AS max_hits, SUM(hits) AS sum_hits
                FROM {LEDGER_TABLE} WHERE draw_no=? GROUP BY kind
                """,
                (dno,),
            ).fetchall()
        ]
        sample_rows = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT brain_tag, kind, set_no, hits, bonus_hit, tier_rank, role
                FROM {LEDGER_TABLE}
                WHERE draw_no=? AND kind='pool'
                ORDER BY brain_tag, set_no
                LIMIT 6
                """,
                (dno,),
            ).fetchall()
        ]
        scatter_sample = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT brain_tag, kind, union_hit_nums_json, dup_hit_nums_json,
                       sets_with_hits, max_hits_in_set, sum_hits, bonus_hit_set_count
                FROM {SCATTER_TABLE} WHERE draw_no=? AND kind='pool'
                """,
                (dno,),
            ).fetchall()
        ]
    finally:
        conn.close()

    # no_peek: target=1237 → draw 1236 포함 OK · target=1236 → 1236 제외
    peek_ok_incl = assert_no_peek_read(1237)
    peek_excl = assert_no_peek_read(1236)
    # 1236을 target으로 읽으면 1236행이 없어야 함
    has_1236_when_target_1236 = any(
        True
        for r in __import__(
            "app.testlotto.pool_hit_ledger", fromlist=["read_ledger_before"]
        ).read_ledger_before(1236, kind=None, limit=5000)
        if int(r["draw_no"]) >= 1236
    )
    no_peek = {
        "read_lt_1237": peek_ok_incl,
        "read_lt_1236": peek_excl,
        "target_1236_excludes_1236": not has_1236_when_target_1236,
        "ok": bool(peek_ok_incl.get("ok"))
        and bool(peek_excl.get("ok"))
        and (not has_1236_when_target_1236),
    }

    # predict reset 목록에 포함
    from tools._k_predict_reset import DELETE_TABLES

    reset_ok = LEDGER_TABLE in DELETE_TABLES and SCATTER_TABLE in DELETE_TABLES

    counts = ledger_counts()
    expected_ledger = 3 * (10 + 5)  # 3뇌 × (pool10+repack5)
    structure_ok = int(n_ledger) == expected_ledger and int(n_scatter) == 6  # 3×2 kind

    bench = {
        "id": "K-POOL-HIT-LEDGER-WIRE",
        "list": "LIST_V3",
        "step": "L3",
        "status": "WIRE_OK" if (wr.get("ok") and no_peek["ok"] and reset_ok and structure_ok) else "WIRE_FAIL",
        "ts_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sample_draw": dno,
        "actual": wr.get("actual"),
        "bonus": wr.get("bonus"),
        "seed": wr.get("seed"),
        "n_ledger_sample": int(n_ledger),
        "n_scatter_sample": int(n_scatter),
        "expected_ledger": expected_ledger,
        "expected_scatter": 6,
        "structure_ok": structure_ok,
        "by_kind": by_kind,
        "sample_pool_rows": sample_rows,
        "scatter_pool": [
            {
                **{k: v for k, v in s.items() if k != "union_hit_nums_json"},
                "union_hit_nums": json.loads(s["union_hit_nums_json"]),
                "dup_hit_nums": json.loads(s["dup_hit_nums_json"]),
            }
            for s in scatter_sample
        ],
        "no_peek": no_peek,
        "predict_reset_listed": reset_ok,
        "counts_global": counts,
        "role_wire": False,
        "note": "역할슬롯 코드는 L4b · repack 원장 소비는 L4 · 강제BT보류 · 1237아님",
        "gates": "prefer/prize 미실행(원장 wire만)",
    }

    BENCH.parent.mkdir(parents=True, exist_ok=True)
    BENCH.write_text(json.dumps(bench, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# K-POOL-HIT-LEDGER-WIRE — LIST_V3 L3",
        "",
        f"시각: {bench['ts_kst']} KST · **{bench['status']}** · wire=**True** · **1237아님** · ge3미클레임",
        "선행: L2 SPEC DOC_OK · L2b 역할SPEC DOC_OK",
        "다음: **L4** 몰아주기 원장 SSOT 읽기 (역할코드는 L4b)",
        "",
        "---",
        "",
        "## 실측",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| sample_draw | {dno} |",
        f"| actual | {bench['actual']} · bonus={bench['bonus']} |",
        f"| n_ledger | {n_ledger} (기대 {expected_ledger}) |",
        f"| n_scatter | {n_scatter} (기대 6) |",
        f"| structure_ok | {structure_ok} |",
        f"| no_peek | {no_peek['ok']} |",
        f"| predict_reset | {reset_ok} |",
        f"| role_wire | False (L4b) |",
        "",
        "## by_kind",
        "",
        "```json",
        json.dumps(by_kind, ensure_ascii=False, indent=2),
        "```",
        "",
        "## no_peek",
        "",
        "```json",
        json.dumps(no_peek, ensure_ascii=False, indent=2),
        "```",
        "",
        f"벤치: `{BENCH.relative_to(ROOT).as_posix()}`",
        "",
        "## 비범위",
        "",
        "- focus_r1 소비(L4) · 역할슬롯 생성(L4b) · 강제BT",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("bench:", BENCH)
    print("report:", REPORT)
    print("status:", bench["status"])
    return 0 if bench["status"] == "WIRE_OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
