# -*- coding: utf-8 -*-
"""K-AB STEP1 READ-ONLY: draw gap audit across lotto4/testlotto/hyodo."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "benchmarks" / "20260727_KAB_draw_gap.json"

DBS = {
    "lotto4": ROOT / "data" / "lotto4.db",
    "testlotto": ROOT / "data" / "lotto_testlotto.db",
    "hyodo": ROOT / "data" / "lotto_hyodo.db",
}

NUM_COLS = ["num1", "num2", "num3", "num4", "num5", "num6", "bonus"]


def find_draws_table(con: sqlite3.Connection) -> str | None:
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1"
    )]
    for cand in ("lotto_draws", "draws", "draw_results"):
        if cand in tables:
            return cand
    for t in tables:
        if "draw" in t.lower():
            return t
    return None


def schema_info(con: sqlite3.Connection, table: str) -> list[dict]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    # cid, name, type, notnull, dflt_value, pk
    return [
        {
            "cid": r[0],
            "name": r[1],
            "type": r[2],
            "notnull": r[3],
            "dflt": r[4],
            "pk": r[5],
        }
        for r in rows
    ]


def load_draws(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    table = find_draws_table(con)
    if not table:
        con.close()
        return {"exists": True, "path": str(path), "error": "no draws table"}
    cols = schema_info(con, table)
    col_names = [c["name"] for c in cols]
    # indexes
    idx = con.execute(f"PRAGMA index_list({table})").fetchall()
    mn, mx, cnt = con.execute(
        f"SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM {table}"
    ).fetchone()
    nos = [int(r[0]) for r in con.execute(
        f"SELECT draw_no FROM {table} ORDER BY draw_no"
    )]
    holes = []
    if nos:
        s = set(nos)
        for n in range(min(nos), max(nos) + 1):
            if n not in s:
                holes.append(n)
    # load number map
    select_cols = ["draw_no"] + [c for c in NUM_COLS if c in col_names]
    q = f"SELECT {','.join(select_cols)} FROM {table} ORDER BY draw_no"
    num_map = {}
    for row in con.execute(q):
        d = dict(zip(select_cols, row))
        nums = tuple(int(d[c]) for c in NUM_COLS if c in d and d[c] is not None)
        num_map[int(d["draw_no"])] = {
            "nums": nums,
            "raw": {c: d.get(c) for c in select_cols},
        }
    con.close()
    trailing_missing_vs_global = None  # filled later
    return {
        "exists": True,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "table": table,
        "schema": cols,
        "indexes": [{"seq": i[0], "name": i[1], "unique": i[2]} for i in idx],
        "min": mn,
        "max": mx,
        "count": cnt,
        "holes_internal": holes,
        "n_holes_internal": len(holes),
        "num_map": num_map,
        "col_names": col_names,
    }


def compare_overlap(a_name, a, b_name, b):
    if not a.get("num_map") or not b.get("num_map"):
        return {"pair": f"{a_name}vs{b_name}", "error": "missing"}
    ka, kb = set(a["num_map"]), set(b["num_map"])
    common = sorted(ka & kb)
    mismatches = []
    for n in common:
        na = a["num_map"][n]["nums"]
        nb = b["num_map"][n]["nums"]
        # compare shared length prefix (both should have 6+bonus if present)
        # normalize: first 6 main numbers sorted? keep as stored order
        if na[:6] != nb[:6] or (
            len(na) > 6 and len(nb) > 6 and na[6] != nb[6]
        ):
            mismatches.append(
                {
                    "draw_no": n,
                    a_name: list(na),
                    b_name: list(nb),
                }
            )
        elif len(na) != len(nb):
            # bonus missing on one side — flag if main match
            if na[:6] == nb[:6]:
                mismatches.append(
                    {
                        "draw_no": n,
                        "note": "main_ok_bonus_len_diff",
                        a_name: list(na),
                        b_name: list(nb),
                    }
                )
    only_a = sorted(ka - kb)
    only_b = sorted(kb - ka)
    return {
        "pair": f"{a_name}_vs_{b_name}",
        "n_common": len(common),
        "common_min": common[0] if common else None,
        "common_max": common[-1] if common else None,
        "n_mismatch": len(mismatches),
        "mismatches": mismatches,
        "only_in_first": only_a,
        "only_in_second": only_b,
        "n_only_first": len(only_a),
        "n_only_second": len(only_b),
    }


def main():
    data = {}
    for name, path in DBS.items():
        print("loading", name, flush=True)
        data[name] = load_draws(path)
        d = data[name]
        if d.get("exists") and "min" in d:
            print(
                f"  {name}: min={d['min']} max={d['max']} count={d['count']} "
                f"holes={d['n_holes_internal']} table={d['table']}",
                flush=True,
            )

    # strip heavy num_map from final but keep for compare
    pairs = []
    names = [n for n in ("lotto4", "testlotto", "hyodo") if data[n].get("num_map")]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            cmp = compare_overlap(names[i], data[names[i]], names[j], data[names[j]])
            pairs.append(cmp)
            print(
                f"compare {cmp['pair']}: common={cmp['n_common']} "
                f"mismatch={cmp['n_mismatch']} "
                f"only1={cmp['n_only_first']} only2={cmp['n_only_second']}",
                flush=True,
            )

    # trailing gap vs max of lotto4
    global_max = max(
        (data[n]["max"] for n in names if data[n].get("max") is not None),
        default=None,
    )
    trailing = {}
    for n in names:
        mx = data[n]["max"]
        missing = list(range(mx + 1, global_max + 1)) if mx is not None and global_max else []
        trailing[n] = {
            "max": mx,
            "global_max": global_max,
            "trailing_missing": missing,
            "gap_kind": (
                "trailing_only"
                if data[n]["n_holes_internal"] == 0 and missing
                else (
                    "internal_holes"
                    if data[n]["n_holes_internal"]
                    else ("complete" if not missing else "mixed")
                )
            ),
        }

    # schema diff
    schemas = {n: data[n].get("schema") for n in names}
    schema_diff = {}
    if len(names) >= 2:
        base = names[0]
        base_cols = {c["name"]: c for c in schemas[base] or []}
        for n in names[1:]:
            other = {c["name"]: c for c in schemas[n] or []}
            only_base = sorted(set(base_cols) - set(other))
            only_other = sorted(set(other) - set(base_cols))
            type_diff = []
            for k in sorted(set(base_cols) & set(other)):
                if (base_cols[k]["type"], base_cols[k]["notnull"], base_cols[k]["pk"]) != (
                    other[k]["type"],
                    other[k]["notnull"],
                    other[k]["pk"],
                ):
                    type_diff.append({"col": k, base: base_cols[k], n: other[k]})
            schema_diff[f"{base}_vs_{n}"] = {
                "only_in_" + base: only_base,
                "only_in_" + n: only_other,
                "type_constraint_diff": type_diff,
            }

    halt = any(p["n_mismatch"] > 0 for p in pairs)
    # missing draws for fan-out candidates
    missing_for = {}
    if "lotto4" in data and data["lotto4"].get("num_map"):
        src = set(data["lotto4"]["num_map"])
        for n in ("testlotto", "hyodo"):
            if data[n].get("num_map") is not None:
                missing_for[n] = sorted(src - set(data[n]["num_map"]))

    # compact export (drop num_map bodies)
    export_dbs = {}
    for n, d in data.items():
        export_dbs[n] = {
            k: v
            for k, v in d.items()
            if k != "num_map"
        }

    out = {
        "meta": {
            "read_only": True,
            "halt_on_mismatch": halt,
            "disclaimer": "이 정합은 예측력과 무관하다. 분석 기반 데이터의 무결성 확보다.",
        },
        "dbs": export_dbs,
        "trailing": trailing,
        "overlap_compare": [
            {k: v for k, v in p.items() if k not in ("only_in_first", "only_in_second")
             or len(v) <= 50}
            for p in pairs
        ],
        # keep full only_* if short
        "overlap_only_full": {
            p["pair"]: {
                "only_in_first": p["only_in_first"],
                "only_in_second": p["only_in_second"],
            }
            for p in pairs
        },
        "schema_diff": schema_diff,
        "missing_vs_lotto4": missing_for,
        "step3_allowed": (not halt) and bool(missing_for),
    }
    # enrich overlap with truncated only lists always in compare
    for p, ep in zip(pairs, out["overlap_compare"]):
        ep["only_in_first_head"] = p["only_in_first"][:20]
        ep["only_in_second_head"] = p["only_in_second"][:20]
        ep["only_in_first_all_if_le20"] = (
            p["only_in_first"] if len(p["only_in_first"]) <= 20 else None
        )
        ep["only_in_second_all_if_le20"] = (
            p["only_in_second"] if len(p["only_in_second"]) <= 20 else None
        )

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("HALT_MISMATCH", halt)
    print("step3_allowed", out["step3_allowed"])
    print("missing_vs_lotto4", {k: (v[:10], len(v)) for k, v in missing_for.items()})
    return 0 if not halt else 2


if __name__ == "__main__":
    raise SystemExit(main())
