# -*- coding: utf-8 -*-
"""K-STAT-EVOLVE-DIAG-READ — evolve_log stat 200행 모니터 집계. READ-ONLY."""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_EVOLVE_DIAG_READ.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_EVOLVE_DIAG_READ.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
E_HITS = 0.80
ROLES = ("skill", "cover", "shape", "focus")
HITS_KEYS = tuple(range(0, 7))


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _role_family(raw: str | None) -> str:
    r = str(raw or "").strip().lower()
    if r.startswith("skill"):
        return "skill"
    if r.startswith("cover"):
        return "cover"
    if r.startswith("shape"):
        return "shape"
    if r.startswith("focus"):
        return "focus"
    return "other"


def _blank_role() -> dict[str, Any]:
    return {
        "n_sets": 0,
        "n_draws_present": 0,
        "hits_sum": 0,
        "mean_hits": None,
        "delta_vs_080": None,
        "hits_hist": {str(k): 0 for k in HITS_KEYS},
        "tier_hist": {},
        "n_draws_ge3": 0,
        "cover_rate_ge3": None,
    }


def _ro() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _census(conn: sqlite3.Connection) -> dict[str, Any]:
    ev = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    led = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    cache = {
        str(r["brain"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache GROUP BY brain"
        )
    }
    peek_stat = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log "
            "WHERE brain_tag='stat' AND as_of >= draw_no"
        ).fetchone()[0]
    )
    peek_all = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no"
        ).fetchone()[0]
    )
    dmax = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])
    pred_1237 = int(
        conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
        ).fetchone()[0]
    )
    return {
        "evolve_n": sum(ev.values()),
        "evolve_by": ev,
        "ledger_by": led,
        "cache_by": cache,
        "peek_stat": peek_stat,
        "peek_all": peek_all,
        "pred_n": pred_n,
        "pred_1237": pred_1237,
        "draws_max": int(dmax) if dmax else None,
    }


def main() -> int:
    conn = _ro()
    census = _census(conn)
    rows = conn.execute(
        """
        SELECT draw_no, brain_tag, as_of, pool_hits_json, repack_hits_json,
               best_hits, mean_hits
        FROM testlotto_evolve_log
        WHERE brain_tag = 'stat'
        ORDER BY draw_no
        """
    ).fetchall()
    conn.close()

    n = len(rows)
    draw_nos = [int(r["draw_no"]) for r in rows]
    peek_rows = [int(r["draw_no"]) for r in rows if int(r["as_of"]) >= int(r["draw_no"])]
    other_tag = [str(r["brain_tag"]) for r in rows if str(r["brain_tag"]) != "stat"]

    by_role: dict[str, dict[str, Any]] = {k: _blank_role() for k in ROLES}
    by_role["other"] = _blank_role()
    by_kind: dict[str, dict[str, dict[str, Any]]] = {
        "pool": {k: _blank_role() for k in (*ROLES, "other")},
        "repack": {k: _blank_role() for k in (*ROLES, "other")},
    }
    ge3_draws: dict[str, set[int]] = defaultdict(set)
    present_draws: dict[str, set[int]] = defaultdict(set)
    ge3_any: set[int] = set()
    raw_roles = Counter()
    row_mean: list[float] = []
    row_best: list[int] = []

    def _acc(bucket: dict[str, Any], fam: str, hits: int, tier: str) -> None:
        b = bucket[fam]
        b["n_sets"] += 1
        b["hits_sum"] += hits
        key = str(hits) if hits in HITS_KEYS else "other"
        if key not in b["hits_hist"]:
            b["hits_hist"][key] = 0
        b["hits_hist"][key] += 1
        t = tier or "none"
        b["tier_hist"][t] = int(b["tier_hist"].get(t, 0)) + 1

    for r in rows:
        dno = int(r["draw_no"])
        row_mean.append(float(r["mean_hits"] or 0))
        row_best.append(int(r["best_hits"] or 0))
        pool = json.loads(r["pool_hits_json"] or "[]")
        repack = json.loads(r["repack_hits_json"] or "[]")
        draw_ge3_role: dict[str, bool] = defaultdict(bool)
        for item, kind in ((x, "pool") for x in pool):
            fam = _role_family(item.get("role"))
            raw_roles[str(item.get("role") or "")] += 1
            hits = int(item.get("hits") or 0)
            tier = str(item.get("tier") or "")
            _acc(by_role, fam, hits, tier)
            _acc(by_kind[kind], fam, hits, tier)
            present_draws[fam].add(dno)
            if hits >= 3:
                draw_ge3_role[fam] = True
                ge3_any.add(dno)
        for item in repack:
            fam = _role_family(item.get("role"))
            raw_roles[str(item.get("role") or "")] += 1
            hits = int(item.get("hits") or 0)
            tier = str(item.get("tier") or "")
            _acc(by_role, fam, hits, tier)
            _acc(by_kind["repack"], fam, hits, tier)
            present_draws[fam].add(dno)
            if hits >= 3:
                draw_ge3_role[fam] = True
                ge3_any.add(dno)
        for fam, flag in draw_ge3_role.items():
            if flag:
                ge3_draws[fam].add(dno)

    def _finalize(bucket: dict[str, Any], fam: str) -> None:
        b = bucket[fam]
        n_sets = int(b["n_sets"])
        n_pres = len(present_draws.get(fam, set())) if bucket is by_role else None
        if bucket is by_role:
            b["n_draws_present"] = n_pres
            b["n_draws_ge3"] = len(ge3_draws.get(fam, set()))
            b["cover_rate_ge3"] = (
                round(b["n_draws_ge3"] / n_pres, 4) if n_pres else None
            )
        if n_sets:
            mh = b["hits_sum"] / n_sets
            b["mean_hits"] = round(mh, 6)
            b["delta_vs_080"] = round(mh - E_HITS, 6)
        b["hits_hist"] = {k: int(b["hits_hist"][k]) for k in sorted(b["hits_hist"], key=lambda x: (x != "other", int(x) if x.isdigit() else 99))}
        b["tier_hist"] = dict(sorted(b["tier_hist"].items(), key=lambda kv: (-kv[1], kv[0])))

    for fam in (*ROLES, "other"):
        _finalize(by_role, fam)
        for kind in ("pool", "repack"):
            b = by_kind[kind][fam]
            if b["n_sets"]:
                mh = b["hits_sum"] / b["n_sets"]
                b["mean_hits"] = round(mh, 6)
                b["delta_vs_080"] = round(mh - E_HITS, 6)
            b["hits_hist"] = {k: int(v) for k, v in b["hits_hist"].items()}
            b["tier_hist"] = dict(sorted(b["tier_hist"].items(), key=lambda kv: (-kv[1], kv[0])))

    # drop empty other
    if by_role["other"]["n_sets"] == 0:
        del by_role["other"]
    for kind in ("pool", "repack"):
        if by_kind[kind]["other"]["n_sets"] == 0:
            del by_kind[kind]["other"]

    hard = {
        "n_stat": n,
        "all_stat": n == 200 and not other_tag,
        "peek": len(peek_rows),
        "peek_ok": len(peek_rows) == 0,
        "window": [min(draw_nos), max(draw_nos)] if draw_nos else None,
        "window_ok": draw_nos[:1] == [1037] and draw_nos[-1:] == [1236] and n == 200,
        "other_brains": int(census["evolve_by"].get("markov", 0))
        + int(census["evolve_by"].get("review", 0)),
        "pred_1237": census["pred_1237"],
        "draws_max": census["draws_max"],
        "read_only": True,
        "three_brain_sum": False,
    }
    hard_ok = (
        hard["all_stat"]
        and hard["peek_ok"]
        and hard["window_ok"]
        and hard["other_brains"] == 0
        and hard["pred_1237"] == 0
        and hard["draws_max"] == 1236
    )

    payload = {
        "id": "K-STAT-EVOLVE-DIAG-READ",
        "as_of": _now(),
        "verdict": "READ_OK" if hard_ok else "READ_FAIL",
        "ge3_claim": False,
        "draw_1237": False,
        "part2_expand": "AWAIT_HYUNG_GO",
        "e_hits": E_HITS,
        "note": "모니터 집계만. hits/tier/ge3 우열·성능 클레임 금지. 이론 0.80 대비 편차만.",
        "hard_ok": hard_ok,
        "hard": hard,
        "census": census,
        "row_monitor": {
            "n": n,
            "repack5_mean_hits": round(mean(row_mean), 6) if row_mean else None,
            "repack5_mean_hits_delta_vs_080": (
                round(mean(row_mean) - E_HITS, 6) if row_mean else None
            ),
            "repack5_best_hist": {str(k): row_best.count(k) for k in HITS_KEYS},
        },
        "raw_roles": dict(raw_roles),
        "by_role": {k: by_role[k] for k in ROLES if k in by_role},
        "by_kind": by_kind,
        "n_draws_any_ge3": len(ge3_any),
        "n_draws_any_ge3_note": "stat 세트 중 hits>=3 이 1장 이상인 회차수. 성적 아님.",
    }

    lines = [
        "# K-STAT-EVOLVE-DIAG-READ",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · stat만 · 1237아님 · hits/tier 클레임 금지",
        "목적=evolve_log stat 200행 모니터 집계. 예측·원장·캐시·learn 미접촉. 파트2 확장 없음.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. n={n} · peek={hard['peek']} · 타뇌행={hard['other_brains']} · pred_1237={hard['pred_1237']} · MAX={hard['draws_max']}.",
        "",
        "## 0) 읽는 법",
        "",
        f"- E[hits]=**{E_HITS}**(K-O). 아래 Δ는 이론 대비 편차. **누가 낫다 금지**.",
        "- ge3 회차수=그 역할 세트 중 hits≥3이 1장 이상인 회차. 커버율 모니터. 성적 아님.",
        "- 3뇌 합산 없음. `WHERE brain_tag='stat'`만.",
        "- 파트2 markov/review 확장=**형 GO 후**. 이번 턴 write 없음.",
        "",
        "## 1) HARD / census",
        "",
        "| 항 | 값 |",
        "|----|-----|",
        f"| n_stat | {n} |",
        f"| window | {hard['window']} |",
        f"| peek as_of≥draw | {hard['peek']} |",
        f"| evolve 뇌 | {census['evolve_by']} |",
        f"| markov/review 행 | {hard['other_brains']} |",
        f"| 원장 | {census['ledger_by']} |",
        f"| 캐시 | {census['cache_by']} |",
        f"| predictions | {census['pred_n']} |",
        f"| pred_1237 | {census['pred_1237']} |",
        f"| draws MAX | {census['draws_max']} |",
        "",
        "## 2) role별 세트 집계 (pool+repack, stat만)",
        "",
        "| role | n_sets | n_draws | mean_hits | Δ vs 0.80 | ge3회차 | ge3율 |",
        "|------|--------|---------|-----------|-----------|--------|------|",
    ]
    for fam in ROLES:
        b = by_role[fam]
        lines.append(
            f"| {fam} | {b['n_sets']} | {b['n_draws_present']} | {b['mean_hits']} | {b['delta_vs_080']} | {b['n_draws_ge3']} | {b['cover_rate_ge3']} |"
        )
    lines += [
        "",
        "행 mean(repack5 모니터)="
        f"{payload['row_monitor']['repack5_mean_hits']} · Δ vs 0.80="
        f"{payload['row_monitor']['repack5_mean_hits_delta_vs_080']} · 성적 아님.",
        "",
        "## 3) role별 hits 히스토그램 (세트수, 0~6)",
        "",
        "| role | 0 | 1 | 2 | 3 | 4 | 5 | 6 |",
        "|------|---|---|---|---|---|---|---|",
    ]
    for fam in ROLES:
        h = by_role[fam]["hits_hist"]
        lines.append(
            "| "
            + " | ".join(
                [fam] + [str(h.get(str(k), 0)) for k in HITS_KEYS]
            )
            + " |"
        )
    lines += [
        "",
        "## 4) role별 tier 분포 (세트수 · 모니터)",
        "",
    ]
    for fam in ROLES:
        th = by_role[fam]["tier_hist"]
        if not th:
            lines.append(f"- {fam}: (없음)")
            continue
        parts = ", ".join(f"{k}={v}" for k, v in th.items())
        lines.append(f"- {fam}: {parts}")
    lines += [
        "",
        f"## 5) ge3 회차 (커버율 관점 · n_draws={n})",
        "",
        f"- 아무 역할이든 hits≥3 1장 이상인 회차: **{len(ge3_any)}** / {n} (성적 아님).",
        "- 역할별 ge3회차=위 표. 역할 간 우열 문장 없음.",
        "",
        "## 6) kind 분리 (참고 · 합산 서열 아님)",
        "",
        "| kind | role | n_sets | mean_hits | Δ vs 0.80 |",
        "|------|------|--------|-----------|-----------|",
    ]
    for kind in ("pool", "repack"):
        for fam in ROLES:
            b = by_kind[kind].get(fam)
            if not b or not b["n_sets"]:
                continue
            lines.append(
                f"| {kind} | {fam} | {b['n_sets']} | {b['mean_hits']} | {b['delta_vs_080']} |"
            )
    lines += [
        "",
        f"원 role 라벨: `{dict(raw_roles)}`.",
        "",
        "## 7) 파트2 (미실행)",
        "",
        "markov/review 확장 · lotto_predictions 리셋 · 3뇌 write = **형 GO 후**.",
        "이번 턴 DB write 0. EVOLVE_AUTO/FEATURE_LAMBDA 미변경.",
        "",
        "## 8) 금지 확인",
        "",
        "3뇌 SUM 뷰 없음. 원장 미접촉. hits/tier로 APPLY·서열·성능 클레임 없음. 1237 아님.",
    ]

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "hard_ok": hard_ok, "n": n, "peek": hard["peek"], "by_role": {k: {"mean": by_role[k]["mean_hits"], "d": by_role[k]["delta_vs_080"], "ge3": by_role[k]["n_draws_ge3"]} for k in ROLES}}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
