# -*- coding: utf-8 -*-
"""K-REPACK-HYENA-SCATTER — 10장에 1등6개 분산 vs 몰아주기. READ-ONLY.

캐시 1037~1236 3뇌. 타깃 적중은 모니터만(예측 입력 금지).
APPLY 없음. 1237아님. DB 쓰기 없음.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREPACK_HYENA_SCATTER.json"
OUT_MD = ROOT / "reports" / "20260815_KREPACK_HYENA_SCATTER.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return sorted(int(x) for x in (s.get("nums") or []))


def _hits(nums: list[int], win: set[int]) -> int:
    return sum(1 for n in nums if n in win)


def _comb(n: int, k: int) -> int:
    if k < 0 or n < k:
        return 0
    return math.comb(n, k)


def hyena_freq_chunk(pool: list[list[int]], n_sets: int = 5) -> list[list[int]]:
    cnt: Counter[int] = Counter()
    for s in pool:
        cnt.update(s)
    ranked = sorted(range(1, 46), key=lambda n: (-cnt[n], n))
    out: list[list[int]] = []
    idx = 0
    for _ in range(n_sets):
        chunk = ranked[idx : idx + 6]
        idx += 6
        if len(chunk) == 6:
            out.append(sorted(chunk))
    return out


def hyena_core_decay(pool: list[list[int]], core_n: int = 10, n_sets: int = 5) -> list[list[int]]:
    cnt: Counter[int] = Counter()
    for s in pool:
        cnt.update(s)
    core = sorted(range(1, 46), key=lambda n: (-cnt[n], n))[:core_n]
    w = {n: float(cnt[n]) for n in core}
    tickets: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for _ in range(n_sets):
        pick = sorted(core, key=lambda n: (-w[n], n))[:6]
        key = tuple(sorted(pick))
        if key in seen:
            for n in pick:
                w[n] *= 0.15
            pick = sorted(core, key=lambda n: (-w[n], n))[:6]
            key = tuple(sorted(pick))
        seen.add(key)
        tickets.append(sorted(pick))
        for n in pick:
            w[n] *= 0.35
    return tickets


def _pack_stats(tickets: list[list[int]], win: set[int]) -> dict[str, Any]:
    unions: set[int] = set()
    hit_list = []
    for t in tickets:
        unions.update(t)
        hit_list.append(_hits(t, win))
    return {
        "union": len(unions),
        "win_in_union": len(unions & win),
        "max_hits": max(hit_list) if hit_list else 0,
        "ge3": sum(1 for h in hit_list if h >= 3),
        "ge4": sum(1 for h in hit_list if h >= 4),
        "ge5": sum(1 for h in hit_list if h >= 5),
        "ge6": sum(1 for h in hit_list if h >= 6),
        "mean_hits": round(mean(hit_list), 4) if hit_list else 0.0,
    }


def _one_draw(pool_rows: list[dict], rep_rows: list[dict], win: set[int]) -> dict[str, Any]:
    pool = [_nums(s) for s in pool_rows]
    rep = [_nums(s) for s in rep_rows]
    p_union: set[int] = set()
    for s in pool:
        p_union.update(s)
    r_union: set[int] = set()
    for s in rep:
        r_union.update(s)
    p_hits = [_hits(s, win) for s in pool]
    r_hits = [_hits(s, win) for s in rep]
    cnt: Counter[int] = Counter()
    for s in pool:
        cnt.update(s)
    win_f = [cnt[n] for n in win]
    other = [cnt[n] for n in p_union if n not in win]
    copies = 0
    copy_win: set[int] = set()
    reco_win: set[int] = set()
    pset = {tuple(s) for s in pool}
    for i, s in enumerate(rep):
        is_c = tuple(s) in pset or (rep_rows[i].get("source") == "pool")
        if is_c:
            copies += 1
            copy_win.update(n for n in s if n in win)
        else:
            reco_win.update(n for n in s if n in win)
    full6 = len(p_union & win) == 6
    scatter = full6 and (max(p_hits) if p_hits else 0) <= 3
    cluster = full6 and (max(p_hits) if p_hits else 0) >= 4
    return {
        "u10": len(p_union),
        "win10": len(p_union & win),
        "max10": max(p_hits) if p_hits else 0,
        "ge3_10": sum(1 for h in p_hits if h >= 3),
        "ge4_10": sum(1 for h in p_hits if h >= 4),
        "u5": len(r_union),
        "win5": len(r_union & win),
        "max5": max(r_hits) if r_hits else 0,
        "ge3_5": sum(1 for h in r_hits if h >= 3),
        "ge4_5": sum(1 for h in r_hits if h >= 4),
        "copies": copies,
        "copy_win": len(copy_win),
        "reco_win": len(reco_win),
        "win_freq_mean": round(mean(win_f), 4) if win_f else 0.0,
        "other_freq_mean": round(mean(other), 4) if other else 0.0,
        "full6": full6,
        "scatter": scatter,
        "cluster": cluster,
        "hyena_chunk": _pack_stats(hyena_freq_chunk(pool), win),
        "hyena_core10": _pack_stats(hyena_core_decay(pool, 10), win),
        "hyena_core8": _pack_stats(hyena_core_decay(pool, 8), win),
        "live": _pack_stats(rep, win),
    }


def _agg(rows: list[dict[str, Any]], key: str | None = None) -> dict[str, Any]:
    xs = rows if key is None else [r for r in rows if r.get(key)]
    n = len(xs)
    if not n:
        return {"n": 0}
    def avg(k: str) -> float:
        return round(mean(r[k] for r in xs), 4)

    def pack_avg(name: str) -> dict[str, Any]:
        return {
            "union": round(mean(r[name]["union"] for r in xs), 4),
            "win_in_union": round(mean(r[name]["win_in_union"] for r in xs), 4),
            "max_hits": round(mean(r[name]["max_hits"] for r in xs), 4),
            "ge3_sets": int(sum(r[name]["ge3"] for r in xs)),
            "ge4_sets": int(sum(r[name]["ge4"] for r in xs)),
            "ge5_sets": int(sum(r[name]["ge5"] for r in xs)),
            "ge6_sets": int(sum(r[name]["ge6"] for r in xs)),
            "draws_ge3": int(sum(1 for r in xs if r[name]["max_hits"] >= 3)),
            "draws_ge4": int(sum(1 for r in xs if r[name]["max_hits"] >= 4)),
            "mean_hits": round(mean(r[name]["mean_hits"] for r in xs), 4),
        }

    win10_hist = Counter(r["win10"] for r in xs)
    return {
        "n": n,
        "u10": avg("u10"),
        "win10": avg("win10"),
        "max10": avg("max10"),
        "u5": avg("u5"),
        "win5": avg("win5"),
        "max5": avg("max5"),
        "copies": avg("copies"),
        "copy_win": avg("copy_win"),
        "reco_win": avg("reco_win"),
        "win_freq_mean": avg("win_freq_mean"),
        "other_freq_mean": avg("other_freq_mean"),
        "freq_delta": round(avg("win_freq_mean") - avg("other_freq_mean"), 4),
        "full6": int(sum(1 for r in xs if r["full6"])),
        "scatter": int(sum(1 for r in xs if r["scatter"])),
        "cluster": int(sum(1 for r in xs if r["cluster"])),
        "win10_hist": {str(k): win10_hist[k] for k in range(0, 7)},
        "live": pack_avg("live"),
        "hyena_chunk": pack_avg("hyena_chunk"),
        "hyena_core10": pack_avg("hyena_core10"),
        "hyena_core8": pack_avg("hyena_core8"),
    }


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    draws = {
        int(r["draw_no"]): {int(r[f"num{i}"]) for i in range(1, 7)}
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        )
    }
    by_brain: dict[str, Any] = {}
    lists: dict[str, dict[str, list[int]]] = {}
    snap_1216: dict[str, Any] = {}
    for tag in BRAINS:
        rows_out: list[dict[str, Any]] = []
        full6_nos: list[int] = []
        scatter_nos: list[int] = []
        cluster_nos: list[int] = []
        n_cache = 0
        for r in conn.execute(
            "SELECT draw_no, pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (tag, LO, HI),
        ):
            dn = int(r["draw_no"])
            win = draws.get(dn)
            if not win:
                continue
            pool = json.loads(r["pool_json"] or "[]")
            rep = json.loads(r["repack_json"] or "[]")
            if len(pool) != 10 or len(rep) != 5:
                continue
            n_cache += 1
            m = _one_draw(pool, rep, win)
            m["draw_no"] = dn
            rows_out.append(m)
            if m["full6"]:
                full6_nos.append(dn)
            if m["scatter"]:
                scatter_nos.append(dn)
            if m["cluster"]:
                cluster_nos.append(dn)
            if dn == 1216:
                pnums = [_nums(s) for s in pool]
                rnums = [_nums(s) for s in rep]
                cnt: Counter[int] = Counter()
                for s in pnums:
                    cnt.update(s)
                snap_1216[tag] = {
                    "win": sorted(win),
                    "win_in_10": sorted(set().union(*pnums) & win),
                    "missing": sorted(win - set().union(*pnums)),
                    "pool_hits": [_hits(s, win) for s in pnums],
                    "repack_hits": [_hits(s, win) for s in rnums],
                    "freq_winners": {str(n): cnt[n] for n in sorted(win)},
                    "live": m["live"],
                    "hyena_chunk": m["hyena_chunk"],
                    "hyena_core10": m["hyena_core10"],
                    "hyena_core8": m["hyena_core8"],
                }
        by_brain[tag] = {
            "n_cache": n_cache,
            "all": _agg(rows_out),
            "on_full6": _agg(rows_out, "full6"),
            "on_scatter": _agg(rows_out, "scatter"),
            "on_cluster": _agg(rows_out, "cluster"),
        }
        lists[tag] = {
            "full6": full6_nos,
            "scatter": scatter_nos,
            "cluster": cluster_nos,
        }
    conn.close()

    # random-union null: P(all 6 in a random U-subset)
    u_stat = by_brain["stat"]["all"]["u10"]
    u_i = int(round(u_stat))
    p_full6_null = _comb(45 - 6, u_i - 6) / _comb(45, u_i) if u_i >= 6 else 0.0
    e_win10_null = round(6 * u_stat / 45, 4)

    hard_ok = (
        dmax == 1236
        and pred_1237 == 0
        and all(by_brain[t]["n_cache"] == 200 for t in BRAINS)
    )
    payload = {
        "id": "K-REPACK-HYENA-SCATTER",
        "as_of": _now(),
        "verdict": "DISCUSS_OK" if hard_ok else "DISCUSS_FAIL",
        "apply": False,
        "window": [LO, HI],
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "hard_ok": hard_ok,
        "null": {
            "u10_stat": u_stat,
            "e_win10": e_win10_null,
            "p_full6_random_subset": round(p_full6_null, 6),
            "e_full6_per200": round(200 * p_full6_null, 3),
        },
        "brains": by_brain,
        "draw_lists": lists,
        "snap_1216": snap_1216,
        "note": (
            "full6=10장 union에 본번호6개 전부. scatter=full6이고 10장 최댓값≤3. "
            "cluster=full6이고 최댓값≥4. hyena는 이번 pool 빈도만(당첨번호 미입력). "
            "hits/tier는 모니터·성적 아님."
        ),
    }

    st = by_brain["stat"]
    lines = [
        "# K-REPACK-HYENA-SCATTER",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=10장에 1등 6개가 흩어진 회차를 200캐시에서 세고, 지금 몰아주기(복사4) vs 하이에나(번호훔침·0복사) 시안을 대조.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. MAX={dmax} · pred_1237={pred_1237} · 캐시 3뇌 각 {by_brain['stat']['n_cache']}.",
        "",
        "## 0) 한 줄 의견",
        "",
        "형의 그림(10장에 1등 번호가 흩어져 미당첨 → 몰아주기가 번호를 모아 새 5장)은 **스킬 정의로는 맞다.**",
        "지금 코드는 그 스킬이 아니다. **세트 복사**라서 같은 번호가 두 칸에 보이고, union은 31→22로만 줄어든다.",
        "하이에나(빈도 상위 번호를 훔쳐 새 티켓)는 복사를 없앤다. 다만 **이번 회 당첨을 보고 모으는 것은 컨닝**이고,",
        "예측 시점에 할 수 있는 일은 ‘10장이 자주 찍은 번호’를 코어로 줄인 뒤 5장을 새로 짜는 것까지다.",
        "코어를 8~10개로 줄이지 않으면 5장으로 흩어진 6개를 한 장에 모을 조합이 사실상 없다.",
        "",
        "## 1) 형의 가설을 숫자로",
        "",
        f"stat 10장 union 평균 **{st['all']['u10']}**. 무작위 {int(round(u_stat))}개 부분집합에 본번호 6개가 모두 들어갈 확률 "
        f"**{p_full6_null:.4f}** → 200회 기대 **{200 * p_full6_null:.2f}**회.",
        f"E[10장에 들어온 본번호 개수] 널 ≈ **{e_win10_null}** (=6×U/45).",
        "",
        "정의:",
        "- **full6**: 10장 번호합에 당첨 본번호 6개가 **모두** 있음 (1등이 10장에 분포).",
        "- **scatter**: full6 이면서 10장 중 최다 적중 **≤3** (한 장에 4등 이상이 없음 · 형이 말한 미당첨 분산).",
        "- **cluster**: full6 이면서 최다 적중 **≥4** (이미 한 장이 4등 이상 · 복사하면 그 장이 몰아주기에도 남음).",
        "",
        "## 2) 200회 실측 — 10장에 본번호가 몇 개 들어왔나",
        "",
        "| 뇌 | n | union10 | win10평균 | full6 | scatter(≤3) | cluster(≥4) | win10=0..6 |",
        "|----|---|---------|-----------|-------|-------------|-------------|------------|",
    ]
    for tag in BRAINS:
        a = by_brain[tag]["all"]
        hist = "·".join(str(a["win10_hist"][str(k)]) for k in range(7))
        lines.append(
            f"| {tag} | {a['n']} | {a['u10']} | {a['win10']} | {a['full6']} | {a['scatter']} | {a['cluster']} | {hist} |"
        )
    lines += [
        "",
        f"stat full6 회차: {lists['stat']['full6']}",
        f"stat scatter 회차: {lists['stat']['scatter']}",
        f"stat cluster 회차: {lists['stat']['cluster']}",
        "",
        "## 3) full6 회차에서 지금 몰아주기는 6개를 모았나",
        "",
        "모니터. 성적 클레임 금지. live=캐시 몰아주기(복사4+1).",
        "",
        "| 뇌 | n | 10장 win | 5장 win | 5장 union | 복사4가 담은 win | 재조합1이 담은 win | live max | live 4등+장 |",
        "|----|---|----------|---------|-----------|------------------|---------------------|----------|-------------|",
    ]
    for tag in BRAINS:
        f6 = by_brain[tag]["on_full6"]
        if f6["n"] == 0:
            lines.append(f"| {tag} | 0 | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {tag} | {f6['n']} | {f6['win10']} | {f6['win5']} | {f6['u5']} | {f6['copy_win']} | {f6['reco_win']} | "
            f"{f6['live']['max_hits']} | {f6['live']['ge4_sets']} |"
        )
    lines += [
        "",
        "## 4) scatter vs cluster (stat)",
        "",
        "| 부분집합 | n | 10장max | 5장 win | live max | live ge4장 | hyena_chunk win | hyena_core10 win | hyena_core8 win |",
        "|----------|---|---------|---------|----------|------------|-----------------|------------------|-----------------|",
    ]
    for key, lab in (("on_scatter", "scatter≤3"), ("on_cluster", "cluster≥4"), ("on_full6", "full6전체"), ("all", "200전체")):
        a = st[key]
        if a["n"] == 0:
            lines.append(f"| {lab} | 0 | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {lab} | {a['n']} | {a.get('max10', '—')} | {a['win5']} | {a['live']['max_hits']} | {a['live']['ge4_sets']} | "
            f"{a['hyena_chunk']['win_in_union']} | {a['hyena_core10']['win_in_union']} | {a['hyena_core8']['win_in_union']} |"
        )
    lines += [
        "",
        "## 5) 하이에나가 당첨 번호를 더 자주 훔치는가 (빈도 신호)",
        "",
        "win_freq = 당첨번호가 10장 중 몇 장에 나왔는지. other_freq = union 안 비당첨 번호의 같은 값.",
        "Δ>0 이면 당첨번호가 10장에서 더 반복 → 빈도훔침이 핸들을 가짐. Δ≈0 이면 큰 union에 우연히 들어간 것.",
        "",
        "| 뇌 | 범위 | win_freq | other_freq | Δ |",
        "|----|------|----------|------------|---|",
    ]
    for tag in BRAINS:
        for key, lab in (("all", "200"), ("on_full6", "full6"), ("on_scatter", "scatter")):
            a = by_brain[tag][key]
            if a["n"] == 0:
                continue
            lines.append(
                f"| {tag} | {lab} n={a['n']} | {a['win_freq_mean']} | {a['other_freq_mean']} | {a['freq_delta']} |"
            )
    lines += [
        "",
        "## 6) 시안 대조 (stat · 모니터 · 성적아님)",
        "",
        "hyena_chunk = 빈도순 30개를 6개씩 5장 (복사 0). hyena_core10/8 = 빈도 상위 10·8만 남기고 감쇠로 5장.",
        "live = 지금 복사4+보완1.",
        "",
        "| 시안 | 범위 | union | win_in_5 | max | ge3회 | ge4장 | ge5장 | ge6장 | mean_hits |",
        "|------|------|-------|----------|-----|-------|-------|-------|-------|-----------|",
    ]
    for scope, sl in (("all", "200"), ("on_full6", "full6"), ("on_scatter", "scatter")):
        a = st[scope]
        if a["n"] == 0:
            continue
        for name, lab in (("live", "live복사"), ("hyena_chunk", "chunk0복사"), ("hyena_core10", "core10"), ("hyena_core8", "core8")):
            p = a[name]
            lines.append(
                f"| {lab} | {sl} n={a['n']} | {p['union']} | {p['win_in_union']} | {p['max_hits']} | "
                f"{p['draws_ge3']} | {p['ge4_sets']} | {p['ge5_sets']} | {p['ge6_sets']} | {p['mean_hits']} |"
            )
    s16 = snap_1216.get("stat") or {}
    lines += [
        "",
        "## 7) 화면 예 1216 (stat) — full6가 아님",
        "",
    ]
    if s16:
        lines += [
            f"당첨 {s16['win']}. 10장에 들어온 것 {s16['win_in_10']} · **빠진 번호 {s16['missing']}**.",
            f"10장 적중 {s16['pool_hits']} · 몰아주기 적중 {s16['repack_hits']}.",
            f"당첨번호의 10장 출현횟수 {s16['freq_winners']}.",
            f"live {s16['live']} · chunk {s16['hyena_chunk']} · core10 {s16['hyena_core10']} · core8 {s16['hyena_core8']}.",
            "1216의 4등은 pool#4가 이미 4개(3·15·23·24)를 한 장에 가진 **cluster형**이다. 복사가 그 장을 살린 것이지, 흩어진 번호를 모은 것이 아니다. 14는 10장에 없음.",
            "",
        ]
    lines += [
        "## 8) 엔진을 어떻게 손볼지 (APPLY 아님 · 브리핑)",
        "",
        "### 왜 복사가 하이에나가 아닌가",
        "",
        "- 복사 4장 = 10장과 **완전 동일 티켓** → 중복. 새 조합이 생기지 않음.",
        "- 5장 union ≈22, 10장 union ≈31. 번호는 조금 줄지만 **같은 6묶음이 두 번** 나온다.",
        "- 보완 1장(stat complement)만 복사 밖 고점수 6개. 하이에나 역할은 이 1장뿐.",
        "",
        "### 예측 시점에 할 수 있는 일 / 없는 일",
        "",
        "| | 가능 | 금지 |",
        "|---|------|------|",
        "| 재료 | 이번 10장의 **번호 빈도·점수·역할** | 이번 회 **당첨/적중** |",
        "| 동작 | 자주 나온 번호를 코어로 줄여 **새 5장** | 적중 잘된 장을 결과 보고 고르기 |",
        "| 목표 | 분산된 **합의 번호**를 소수 티켓에 재배치 | 1등 P 상승 클레임 |",
        "",
        "결과 본 뒤 ‘적중된 번호를 모은다’는 원장 학습(이미 있는 ledger/숙제)의 일이지, **그 회 몰아주기 입력**이 될 수 없다.",
        "",
        "### 문헌·벤치 (웹)",
        "",
        "- Lottery wheeling / covering: 풀 V를 정한 뒤 티켓으로 t-묶음을 덮는다. 복사가 아니라 **새 블록**이다. (Wikipedia Lottery wheeling; La Jolla C(v,6,t))",
        "- Abbreviated wheel: 1등 보장이 아니라 ‘V에 m개가 들어오면 t맞 1장’ 보장. 한국 3등=5맞이라 C(v,6,5)는 v=10만 해도 50장. **5장으로 1등/3등 보장 불가**.",
        "- 5장으로 완전 3-cover가 되는 V 크기: C(8,6,3)=**4** ≤5. C(9,6,3)=7>5. **코어를 8 이하로 줄여야** 5장이 t=3 보장권.",
        "- Key-number wheel: 확신 번호를 모든 장에 고정. 하이에나 해석=10장에서 5회 이상 나온 번호를 키로.",
        "- Smart Coverage (Lucky Picks): 예산(5장) 안에서 pair/triple 덮기 최대화. 보장 실패 시 greedy fallback.",
        "- Thaler & Ziemba 1988: 당첨 P는 티켓 배치로 안 바뀜. 바꾸는 것은 **중복 제거와 하위등수 형태 덮기**뿐.",
        "",
        "이미 레포: K-STAT-TIER3-COVERING-DISCUSS — cover_r3는 휠이 아님. 휠을 몰아주기에 얹으면 S3/S4(복사쿼터·보완)와 충돌.",
        "",
        "### 개선안 3개 (별 GO + prefer/prize 게이트)",
        "",
        "| ID | 손볼 곳 | 동작 | 기대(설계) | 위험 |",
        "|----|---------|------|------------|------|",
        "| **H1 권고** | `assemble_signal_union` 교체 · cap=0 | 10장 빈도 상위 8~10을 코어 → 감쇠/키휠로 **새 5장** · 복사 0 | 중복 제거 · union 22→8~12 · scatter에서 한 장에 3묶음 모일 여지 | cluster(이미 4등 장)를 **분해**할 수 있음 · prefer 쏠림 |",
        "| H2 절충 | cap=1 | 점수 최상위 **1장만 보존** + 하이에나 4장 | 1216형 4등 장을 살릴 수 있음 | 여전히 1장 중복 |",
        "| H3 유지 | 지금 | 복사4+보완1 | cluster 보존 | 형 스킬과 불일치 · 중복 |",
        "",
        "H1 끼움점=`assemble_signal_union` / `_assembled_for_brain`. 플래그 예: `REPACK_HYENA_MODE=core8` · 롤백=`signal_union`. **stat만** 먼저(뇌독립). markov/review는 별 GO.",
        "게이트: prefer/prize 비악화 · peek0 · 1~10 pool HARD 불변 · 몰아주기 5장만 변경. hits/ge3/등수 **게이트 아님**(K-O).",
        "타깃 적중 입력 금지. 원장 EMA는 이미 `number_scores`에 있음 — 그걸 ‘지난 회 흩어진 번호’ 학습으로 쓰는 것은 유지.",
        "",
        "### 내 생각 (커서)",
        "",
        "하이에나 비유는 맞다. 다만 훔칠 대상은 ‘나중에 당첨된 번호’가 아니라 **지금 10장이 서로 동의하는 번호**다.",
        "200회에서 full6 자체가 드물고(널과 비슷한 규모여야 정상), 그때도 5장으로 6개를 한 장에 넣는 것은 코어≤8이 아니면 조합이 안 된다.",
        "그래서 1등 회수기가 아니라 **중복 제거 + 합의 코어 재배치**로 이름을 고정하는 편이 맞다.",
        "지금 바로 APPLY 하지 말 것. 형이 H1/H2/H3 중 하나를 고르면 SPEC→stat 단독 게이트.",
        "",
        "## 9) 판정",
        "",
        "DISCUSS_OK. 코드/DB 쓰기 없음. 1237 아님. 동결 토큰 미수정.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": payload["verdict"],
                "stat_full6": st["all"]["full6"],
                "stat_scatter": st["all"]["scatter"],
                "stat_cluster": st["all"]["cluster"],
                "stat_win10": st["all"]["win10"],
                "null_e_full6": payload["null"]["e_full6_per200"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
