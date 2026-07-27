# -*- coding: utf-8 -*-
"""lotto4 → testlotto/hyodo draws 팬아웃 (K-06 / K-AE).

INSERT OR IGNORE only. 기존 행 UPDATE/DELETE 없음.
스위치: ROK21_FANOUT 기본 ON (0/false/off/no 만 OFF).
"""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
LOTTO4_DB = ROOT / "data" / "lotto4.db"
TESTLOTTO_DB = ROOT / "data" / "lotto_testlotto.db"
HYODO_DB = ROOT / "data" / "lotto_hyodo.db"

COLS = (
    "draw_no",
    "draw_date",
    "num1",
    "num2",
    "num3",
    "num4",
    "num5",
    "num6",
    "bonus",
    "total_sales",
    "first_prize",
    "first_winners",
    "created_at",
)
NUM_KEY = ("num1", "num2", "num3", "num4", "num5", "num6", "bonus")


def fanout_enabled() -> bool:
    raw = os.environ.get("ROK21_FANOUT")
    if raw is None or str(raw).strip() == "":
        return True
    v = str(raw).strip().lower()
    if v in ("0", "false", "off", "no"):
        return False
    return True


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def _load_num_map(con: sqlite3.Connection) -> dict[int, tuple]:
    q = f"SELECT draw_no,{','.join(NUM_KEY)} FROM lotto_draws"
    out: dict[int, tuple] = {}
    for r in con.execute(q):
        out[int(r["draw_no"])] = tuple(r[k] for k in NUM_KEY)
    return out


def _max_count(con: sqlite3.Connection) -> tuple[int | None, int]:
    row = con.execute(
        "SELECT MAX(draw_no), COUNT(*) FROM lotto_draws"
    ).fetchone()
    return (row[0], int(row[1] or 0))


def check_overlap_mismatch(
    src: dict[int, tuple], dst: dict[int, tuple]
) -> list[int]:
    mism: list[int] = []
    for n in set(src) & set(dst):
        if src[n] != dst[n]:
            mism.append(n)
    return sorted(mism)


def _fetch_rows(con: sqlite3.Connection, draw_nos: list[int]) -> list[tuple]:
    rows = []
    for n in draw_nos:
        r = con.execute(
            f"SELECT {','.join(COLS)} FROM lotto_draws WHERE draw_no=?", (n,)
        ).fetchone()
        if r is not None:
            rows.append(tuple(r[c] for c in COLS))
    return rows


def fanout_from_lotto4(
    draw_nos: list[int] | None = None,
    *,
    catch_up_missing: bool = True,
    db_lotto4: Path | None = None,
    db_testlotto: Path | None = None,
    db_hyodo: Path | None = None,
) -> dict[str, Any]:
    """lotto4 행을 testlotto·hyodo에 INSERT OR IGNORE.

    INSERT는 양쪽 일괄(BEGIN 후 실행). commit은 DB별 순차.
    순차 commit 중 후행 실패 시 이미 commit된 선행 DB는 rollback으로
    되돌리지 못함(SQLite 다중DB 원자성 불가). 잔여는 다음 catch-up이 수렴.
    lotto4는 수정·롤백하지 않음 (K-AB STEP5).
    """
    result: dict[str, Any] = {
        "enabled": fanout_enabled(),
        "ok": True,
        "skipped": False,
        "early_gate": False,
        "inserted_testlotto": [],
        "inserted_hyodo": [],
        "planned": [],
        "mismatches": {},
        "errors": [],
        "note": "",
    }
    if not fanout_enabled():
        result["skipped"] = True
        result["note"] = "ROK21_FANOUT=OFF"
        return result

    p4 = db_lotto4 or LOTTO4_DB
    pt = db_testlotto or TESTLOTTO_DB
    ph = db_hyodo or HYODO_DB
    if not p4.exists():
        result["ok"] = False
        result["errors"].append(f"missing source {p4}")
        return result

    src = None
    targets: list[tuple[str, Path, sqlite3.Connection]] = []
    try:
        src = _connect(p4)
        for path, label in ((pt, "testlotto"), (ph, "hyodo")):
            if not path.exists():
                result["errors"].append(f"missing target {label}:{path}")
                result["ok"] = False
                return result
            targets.append((label, path, _connect(path)))

        # 비용 게이트: MAX·COUNT 일치 + 강제 draw_nos 없으면 전량 로드 생략
        src_mc = _max_count(src)
        tgt_mcs = {label: _max_count(con) for label, _path, con in targets}
        force_nos = [int(x) for x in (draw_nos or [])]
        if (
            catch_up_missing
            and not force_nos
            and all(mc == src_mc for mc in tgt_mcs.values())
        ):
            result["early_gate"] = True
            result["planned"] = []
            result["note"] = "no-op early gate (MAX/COUNT match)"
            return result

        src_map = _load_num_map(src)
        mism_all: dict[str, list[int]] = {}
        for label, path, con in targets:
            mism = check_overlap_mismatch(src_map, _load_num_map(con))
            if mism:
                mism_all[label] = mism
        if mism_all:
            result["ok"] = False
            result["mismatches"] = mism_all
            result["errors"].append("overlap mismatch — fanout aborted")
            result["note"] = "INSERT 금지 (불일치)"
            return result

        missing_union: set[int] = set()
        for label, path, con in targets:
            missing_union |= set(src_map) - set(_load_num_map(con))
        if draw_nos is not None:
            planned = sorted(set(int(x) for x in draw_nos) & set(src_map))
            if catch_up_missing:
                planned = sorted(set(planned) | missing_union)
        else:
            planned = sorted(missing_union) if catch_up_missing else []

        result["planned"] = planned
        if not planned:
            result["note"] = "no-op (already aligned or empty plan)"
            return result

        rows = _fetch_rows(src, planned)
        placeholders = ",".join("?" for _ in COLS)
        sql = (
            f"INSERT OR IGNORE INTO lotto_draws ({','.join(COLS)}) "
            f"VALUES ({placeholders})"
        )

        inserted: dict[str, list[int]] = {"testlotto": [], "hyodo": []}
        befores: dict[str, set[int]] = {}
        # 샌드박스 전용: ROK21_FANOUT_TEST_FAIL_COMMIT=hyodo|testlotto
        fail_label = os.environ.get("ROK21_FANOUT_TEST_FAIL_COMMIT", "").strip().lower()
        try:
            for label, path, con in targets:
                befores[label] = set(_load_num_map(con))
                con.execute("BEGIN")
                for row in rows:
                    con.execute(sql, row)
            # commit은 DB별 순차 — 완전 원자성 불가 (잔여위험)
            for label, path, con in targets:
                if fail_label and label == fail_label:
                    raise RuntimeError(f"test inject fail commit:{label}")
                con.commit()
                after = set(_load_num_map(con))
                inserted[label] = sorted(after - befores[label])
        except Exception as e:
            for label, path, con in targets:
                try:
                    con.rollback()
                except Exception:
                    pass
            result["ok"] = False
            result["errors"].append(f"fanout txn failed: {e}")
            result["note"] = (
                "순차 commit 잔여위험: 이미 commit된 DB는 rollback 불가. "
                "미commit DB만 rollback. lotto4 미변경"
            )
            logger.warning("fanout failed: %s", e)
            return result

        result["inserted_testlotto"] = inserted["testlotto"]
        result["inserted_hyodo"] = inserted["hyodo"]
        result["note"] = "ok"
        return result
    finally:
        if src is not None:
            try:
                src.close()
            except Exception:
                pass
        for label, path, con in targets:
            try:
                con.close()
            except Exception:
                pass


def fanout_after_collect(collected: list[int]) -> dict[str, Any]:
    """수집 직후 호출: collected + 누락 catch-up. 예외는 삼키고 dict 반환."""
    try:
        return fanout_from_lotto4(list(collected or []), catch_up_missing=True)
    except Exception as e:
        logger.warning("fanout_after_collect error: %s", e)
        return {
            "ok": False,
            "enabled": fanout_enabled(),
            "errors": [str(e)],
            "note": "exception swallowed — collect pipeline continues",
        }
