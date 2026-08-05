# -*- coding: utf-8 -*-
"""HIT warrant — D_N → D_{N+1} 번호별 명분 라벨 (로그·설명 전용).

발권 confidence / quota / WIRE / engine 미접촉.
당첨확률↑ 클레임 금지.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

# 로그 부착 ON · 가중/발권과 무관
HIT_WARRANT_ATTACH: bool = True


def zone_of(n: int) -> str:
    if n <= 15:
        return "L"
    if n <= 30:
        return "M"
    return "H"


def consec_members(nums: list[int]) -> set[int]:
    s = set(int(x) for x in nums)
    hit: set[int] = set()
    for x in nums:
        xi = int(x)
        if (xi - 1) in s or (xi + 1) in s:
            hit.add(xi)
    return hit


def label_number(
    num: int,
    d_n: set[int],
    top15: list[int],
    consec: set[int],
) -> dict[str, Any]:
    labels: list[str] = []
    if num in d_n:
        labels.append("carry")
    rank: int | None = None
    if num in top15:
        labels.append("trans_top15")
        rank = top15.index(num) + 1
    if num in consec:
        labels.append("struct_consec")
    labels.append(f"struct_zone_{zone_of(num)}")
    labels.append("struct_odd" if num % 2 else "struct_even")
    primary = {"carry", "trans_top15", "struct_consec"}
    has_primary = bool(primary & set(labels))
    if not has_primary:
        labels.append("unexplained")
    return {
        "num": int(num),
        "labels": labels,
        "trans_top15_rank": rank,
        "explained": has_primary,
    }


def label_pair(
    d_n: list[int],
    d_n1: list[int],
    top15: list[int] | None = None,
) -> dict[str, Any]:
    """D_N → D_{N+1} 명분 카탈로그 1건."""
    top = [int(x) for x in (top15 or [])]
    dn = set(int(x) for x in d_n)
    dn1 = [int(x) for x in d_n1]
    consec = consec_members(dn1)
    numbers = [label_number(x, dn, top, consec) for x in dn1]
    carry = sorted(dn & set(dn1))
    return {
        "D_N": sorted(dn),
        "D_N1": dn1,
        "carry": carry,
        "top15": top,
        "numbers": numbers,
        "n_explained": sum(1 for x in numbers if x["explained"]),
        "n_unexplained": sum(1 for x in numbers if not x["explained"]),
    }


def format_note_summary(catalog: dict[str, Any]) -> str:
    """evolve_log.note / 설명용 짧은 문자열 (가중 입력 금지)."""
    parts: list[str] = []
    for lab in catalog.get("numbers") or []:
        prim = [
            L
            for L in lab.get("labels") or []
            if L in ("carry", "trans_top15", "struct_consec", "unexplained")
        ]
        rank = lab.get("trans_top15_rank")
        extra = f"@{rank}" if rank else ""
        parts.append(f"{lab['num']}:{'+'.join(prim) or '?'}{extra}")
    carry = catalog.get("carry") or []
    return (
        f"HIT-WARRANT carry={carry} "
        f"exp={catalog.get('n_explained', 0)}/6 "
        f"[{'; '.join(parts)}]"
    )


def ensure_hit_warrant_log_table(conn=None) -> None:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hit_warrant_log (
            draw_no        INTEGER NOT NULL,
            anchor_draw    INTEGER NOT NULL,
            sim_k          INTEGER NOT NULL DEFAULT 2,
            labels_json    TEXT NOT NULL,
            summary_text   TEXT NOT NULL,
            n_explained    INTEGER NOT NULL DEFAULT 0,
            n_unexplained  INTEGER NOT NULL DEFAULT 0,
            created_at     TEXT NOT NULL,
            PRIMARY KEY (draw_no, sim_k)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_hit_warrant_anchor ON hit_warrant_log(anchor_draw)"
    )
    if own:
        conn.commit()
        conn.close()


def upsert_hit_warrant_log(
    draw_no: int,
    anchor_draw: int,
    catalog: dict[str, Any],
    *,
    sim_k: int = 2,
    conn=None,
) -> None:
    """draw_no = N+1 (당첨 확정 회차), anchor_draw = N."""
    if not HIT_WARRANT_ATTACH:
        return
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    ensure_hit_warrant_log_table(conn)
    summary = format_note_summary(catalog)
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO hit_warrant_log (
            draw_no, anchor_draw, sim_k, labels_json, summary_text,
            n_explained, n_unexplained, created_at
        ) VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(draw_no, sim_k) DO UPDATE SET
            anchor_draw=excluded.anchor_draw,
            labels_json=excluded.labels_json,
            summary_text=excluded.summary_text,
            n_explained=excluded.n_explained,
            n_unexplained=excluded.n_unexplained,
            created_at=excluded.created_at
        """,
        (
            int(draw_no),
            int(anchor_draw),
            int(sim_k),
            json.dumps(catalog, ensure_ascii=False),
            summary,
            int(catalog.get("n_explained") or 0),
            int(catalog.get("n_unexplained") or 0),
            ts,
        ),
    )
    if own:
        conn.commit()
        conn.close()


def load_top15_for_anchor(anchor_draw: int, *, sim_k: int = 2, conn=None) -> list[int]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    own = conn is None
    if own:
        init_testlotto_db()
        conn = get_lotto_db()
    row = conn.execute(
        "SELECT top15 FROM transition_log WHERE draw_no=? AND sim_k=? LIMIT 1",
        (int(anchor_draw), int(sim_k)),
    ).fetchone()
    if own:
        conn.close()
    if not row:
        return []
    return [int(x) for x in json.loads(dict(row)["top15"])]


def catalog_for_draws(
    draws_by_no: dict[int, list[int]],
    n1: int,
    *,
    top15: list[int] | None = None,
    sim_k: int = 2,
    conn=None,
) -> dict[str, Any] | None:
    """N+1=n1 기준 · N=n1-1."""
    n = n1 - 1
    if n not in draws_by_no or n1 not in draws_by_no:
        return None
    top = top15
    if top is None:
        top = load_top15_for_anchor(n, sim_k=sim_k, conn=conn)
    return label_pair(draws_by_no[n], draws_by_no[n1], top)


def attach_summary_for_evolve_note(draw_no: int, base_note: str) -> str:
    """evolve_log note에 HIT-WARRANT 요약 부착 · 가중 불변."""
    if not HIT_WARRANT_ATTACH:
        return base_note
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        conn.execute("PRAGMA busy_timeout=60000")
        ensure_hit_warrant_log_table(conn)
        row = conn.execute(
            "SELECT summary_text FROM hit_warrant_log WHERE draw_no=? AND sim_k=2",
            (int(draw_no),),
        ).fetchone()
        if row:
            summary = dict(row)["summary_text"]
            if summary and summary not in (base_note or ""):
                return f"{base_note} · {summary}" if base_note else summary
            return base_note
        # 로그 없으면 즉석 계산
        rows = conn.execute(
            """
            SELECT draw_no,num1,num2,num3,num4,num5,num6
            FROM lotto_draws WHERE draw_no IN (?,?)
            """,
            (draw_no - 1, draw_no),
        ).fetchall()
        by = {
            int(dict(r)["draw_no"]): sorted(
                int(dict(r)[f"num{k}"]) for k in range(1, 7)
            )
            for r in rows
        }
        cat = catalog_for_draws(by, int(draw_no), conn=conn)
        if not cat:
            return base_note
        summary = format_note_summary(cat)
        upsert_hit_warrant_log(int(draw_no), int(draw_no) - 1, cat, conn=conn)
        conn.commit()
        return f"{base_note} · {summary}" if base_note else summary
    finally:
        conn.close()
