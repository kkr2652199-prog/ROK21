# -*- coding: utf-8 -*-
"""K-REVIEW-FRONTLOAD — 금액뇌 pool 앞채움 전수조사 후 게이트 통과 시 APPLY.

LIVE pool은 diversify+cover로 번호를 흩뿌린다. 시안은 당첨 미입력:
  D = pool union을 number_scores 순으로 #1→#10
  E = D + 몰아주기 5장 = 새 pool #1~#5
캐시 전수: live / freq / oracle(모니터·금지) / score_proxy.
게이트: 1137–1236 n100 · prefer/prize Δ<0.005 · peek 0.
1237 신규 predict_sets 없음. 원장 미기록. DB git 안 함.
"""
from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KREVIEW_FRONTLOAD.json"
OUT_MD = ROOT / "reports" / "20260822_KREVIEW_FRONTLOAD.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
SRC = ROOT / "app" / "testlotto" / "signal_pool.py"
DB = ROOT / "data" / "lotto_testlotto.db"

TAG = "review"
GATE_LO, GATE_HI = 1137, 1236
REFILL_LO, REFILL_HI = 1037, 1236
ISO = 0.005
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _hits(nums: list[int], win: set[int]) -> int:
    return len(set(nums) & win)


def _axis(table: dict[int, float], sets: list[dict]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = []
    for s in sets:
        nums = _nums(s)
        if len(nums) != 6:
            continue
        vals.append(mean(table[n] for n in nums) - uni)
    return round(mean(vals), 6) if vals else None


def _m(xs: list[float]) -> float | None:
    return round(mean(xs), 6) if xs else None


def _pack_ranked(ranked: list[int], n: int = 10) -> list[list[int]]:
    """ranked 번호만 6개씩. 잔여 1~45를 새로 넣지 않음."""
    out: list[list[int]] = []
    idx = 0
    while len(out) < n and idx + 6 <= len(ranked):
        out.append(sorted(ranked[idx : idx + 6]))
        idx += 6
    return out


def _set_stats(sets: list[list[int]], win: set[int]) -> dict[str, Any]:
    if not sets:
        return {"n": 0}
    hs = [_hits(s, win) for s in sets]
    uni: set[int] = set()
    for s in sets:
        uni.update(s)
    return {
        "n": len(sets),
        "set1_hits": hs[0] if hs else 0,
        "max_hits": max(hs) if hs else 0,
        "mean_hits": round(mean(hs), 6) if hs else 0.0,
        "ge3": sum(1 for h in hs if h >= 3),
        "ge4": sum(1 for h in hs if h >= 4),
        "ge5": sum(1 for h in hs if h >= 5),
        "ge6": sum(1 for h in hs if h >= 6),
        "union": len(uni),
        "win_in_union": len(uni & win),
        "full6": int(win <= uni),
        "set1_full6": int(win <= set(sets[0])),
    }


def _cache_census() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        draws = {
            int(r["draw_no"]): {int(r[f"num{i}"]) for i in range(1, 7)}
            for r in conn.execute(
                "SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto_draws"
            )
        }
        rows = conn.execute(
            "SELECT draw_no, pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no<=1236 ORDER BY draw_no",
            (TAG,),
        ).fetchall()
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
    finally:
        conn.close()

    acc: dict[str, list[dict[str, Any]]] = {
        "live": [],
        "freq": [],
        "oracle": [],
        "proxy": [],
    }
    case_1236 = None
    n_skip = 0
    peek = 0
    for r in rows:
        dno = int(r["draw_no"])
        win = draws.get(dno)
        if not win:
            n_skip += 1
            continue
        pool = json.loads(r["pool_json"] or "[]")
        rep = json.loads(r["repack_json"] or "[]")
        psets = [_nums(s) for s in pool if len(_nums(s)) == 6]
        rsets = [_nums(s) for s in rep if len(_nums(s)) == 6]
        if len(psets) != 10:
            n_skip += 1
            continue
        union = {n for s in psets for n in s}
        freq = Counter()
        for s in psets:
            freq.update(set(s))
        ranked_freq = [n for n, _ in freq.most_common()]
        freq_sets = _pack_ranked(ranked_freq, 10)
        win_first = sorted(union & win) + sorted(union - win)
        oracle_sets = _pack_ranked(win_first, 10)
        proxy_rank = []
        seen: set[int] = set()
        for s in rsets:
            for n in s:
                if n not in seen:
                    proxy_rank.append(n)
                    seen.add(n)
        for n, _ in freq.most_common():
            if n not in seen:
                proxy_rank.append(n)
                seen.add(n)
        proxy_sets = _pack_ranked(proxy_rank, 10)
        rec = {
            "dno": dno,
            "live": _set_stats(psets, win),
            "repack": _set_stats(rsets, win) if rsets else {},
            "freq": _set_stats(freq_sets, win),
            "oracle": _set_stats(oracle_sets, win),
            "proxy": _set_stats(proxy_sets, win),
        }
        acc["live"].append(rec["live"])
        acc["freq"].append(rec["freq"])
        acc["oracle"].append(rec["oracle"])
        acc["proxy"].append(rec["proxy"])
        if dno == 1236:
            case_1236 = rec

    def _summ(xs: list[dict[str, Any]]) -> dict[str, Any]:
        if not xs:
            return {}
        keys = (
            "set1_hits",
            "max_hits",
            "mean_hits",
            "ge3",
            "ge4",
            "ge5",
            "ge6",
            "union",
            "win_in_union",
            "full6",
            "set1_full6",
        )
        out: dict[str, Any] = {"n": len(xs)}
        for k in keys:
            vals = [float(x.get(k) or 0) for x in xs]
            out[k] = round(mean(vals), 6)
            if k in ("full6", "set1_full6", "ge4", "ge6"):
                out[f"{k}_n"] = int(sum(vals))
        return out

    return {
        "n_rows": len(rows),
        "n_ok": len(acc["live"]),
        "n_skip": n_skip,
        "peek_cache": peek,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "summary": {k: _summ(v) for k, v in acc.items()},
        "case_1236": case_1236,
    }


def _load_1237_cache() -> dict[str, Any] | None:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no=1237",
            (TAG,),
        ).fetchone()
        win_row = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=1237"
        ).fetchone()
    finally:
        conn.close()
    if not row or not win_row:
        return None
    win = {int(win_row[f"num{i}"]) for i in range(1, 7)}
    pool = json.loads(row["pool_json"] or "[]")
    rep = json.loads(row["repack_json"] or "[]")
    return {"win": sorted(win), "pool": pool, "repack": rep}


def _scores_for_cached_pool(dno: int, pool: list[dict]) -> dict[int, float]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    learner = sp.RollingSignalLearner()
    num_ema, pos_ema = learner.snapshot()
    return sp.number_scores(
        pool,
        (sp.build_hint_by_brain(draws, dno) or {}).get(TAG, sp._build_hint(draws, dno)),
        num_ema,
        pos_ema,
        brain_tag=TAG,
    )


def _case_1237(cache: dict[str, Any] | None) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    if not cache:
        return {"ok": False, "reason": "no_cache"}
    win = set(cache["win"])
    pool = cache["pool"]
    psets = [_nums(s) for s in pool]
    rsets = [_nums(s) for s in cache["repack"]]
    scores = _scores_for_cached_pool(1237, pool)
    fl = sp.frontload_pool_by_scores(pool, scores, n=10, brain_tag=TAG)
    fl_sets = [_nums(s) for s in fl]
    return {
        "ok": True,
        "win": cache["win"],
        "live_pool": [_set_stats(psets, win), psets],
        "live_repack": [_set_stats(rsets, win), rsets],
        "front_pool": [_set_stats(fl_sets, win), fl_sets],
        "front_repack5": [_set_stats(fl_sets[:5], win), fl_sets[:5]],
        "note": "캐시 pool+점수 재조립. predict_sets 재호출 없음.",
    }


def _gate() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT draw_no FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (GATE_LO, GATE_HI),
        ).fetchall()
    finally:
        conn.close()

    t0 = time.perf_counter()
    n_ok = peek_fail = size_bad = 0
    errors: list[str] = []
    d_changed = e_changed = 0
    mets = {
        k: {x: [] for x in ("pref", "prize", "s1", "mx", "ge4", "ge6")}
        for k in ("off", "D", "E")
    }

    for i, r in enumerate(rows):
        dno = int(r["draw_no"])
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek_fail += 1
            continue
        try:
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
            pool_br = sp._pool_by_brain(pool)
            p = pool_br.get(TAG) or []
            learner = sp.RollingSignalLearner()
            num_ema, pos_ema = learner.snapshot()
            hint_b = sp.build_hint_by_brain(draws, dno)
            scores = sp.number_scores(
                p,
                (hint_b or {}).get(TAG, sp._build_hint(draws, dno)),
                num_ema,
                pos_ema,
                brain_tag=TAG,
            )
            classic = sp.repack_sets(scores)
            fl = sp.frontload_pool_by_scores(p, scores, n=10, brain_tag=TAG)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(p) != 10 or len(classic) != 5 or len(fl) != 10:
            size_bad += 1
            continue
        win_row = None
        conn2 = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
        try:
            win_row = conn2.execute(
                "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
                (dno,),
            ).fetchone()
        finally:
            conn2.close()
        if not win_row:
            size_bad += 1
            continue
        win = {int(win_row[i]) for i in range(6)}
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        off_p = [{"nums": _nums(s)} for s in p]
        off_r = [{"nums": list(s)} for s in classic]
        d_p = [{"nums": _nums(s)} for s in fl]
        d_r = off_r
        e_p = d_p
        e_r = [{"nums": _nums(s)} for s in fl[:5]]
        if [_key(_nums(s)) for s in p] != [_key(_nums(s)) for s in fl]:
            d_changed += 1
        if [_key(s) for s in classic] != [_key(_nums(s)) for s in fl[:5]]:
            e_changed += 1
        for name, psets, rsets in (
            ("off", off_p, off_r),
            ("D", d_p, d_r),
            ("E", e_p, e_r),
        ):
            all_sets = psets + rsets
            mets[name]["pref"].append(_axis(pref_t, all_sets) or 0.0)
            mets[name]["prize"].append(_axis(prize_t, all_sets) or 0.0)
            st = _set_stats([_nums(s) for s in psets], win)
            mets[name]["s1"].append(float(st["set1_hits"]))
            mets[name]["mx"].append(float(st["max_hits"]))
            mets[name]["ge4"].append(float(st["ge4"]))
            mets[name]["ge6"].append(float(st["ge6"]))
        n_ok += 1
        if (i + 1) % 10 == 0 or dno == GATE_HI:
            print(f"  [gate] {i+1}/{len(rows)} d={dno} n_ok={n_ok}", flush=True)

    def pack(name: str) -> dict[str, Any]:
        m = mets[name]
        return {
            "prefer": _m(m["pref"]),
            "prize": _m(m["prize"]),
            "set1_hits": _m(m["s1"]),
            "max_hits": _m(m["mx"]),
            "ge4_mean": _m(m["ge4"]),
            "ge6_n": int(sum(m["ge6"])),
        }

    off, d, e = pack("off"), pack("D"), pack("E")

    def iso(on: dict[str, Any]) -> bool:
        if off["prefer"] is None or on["prefer"] is None:
            return False
        if off["prize"] is None or on["prize"] is None:
            return False
        return (on["prefer"] - off["prefer"] < ISO) and (on["prize"] - off["prize"] < ISO)

    hard = n_ok == (GATE_HI - GATE_LO + 1) and peek_fail == 0 and size_bad == 0 and not errors
    d_iso = iso(d)
    e_iso = iso(e)
    d_apply = bool(hard and d_iso and d_changed > 0)
    e_apply = bool(hard and e_iso and e_changed > 0)
    chosen = None
    if e_apply:
        chosen = "E"
    elif d_apply:
        chosen = "D"
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "n_target": GATE_HI - GATE_LO + 1,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "hard_ok": hard,
        "D_changed": d_changed,
        "E_changed": e_changed,
        "off": off,
        "D": d,
        "E": e,
        "D_delta_prefer": None if off["prefer"] is None else round(d["prefer"] - off["prefer"], 6),
        "D_delta_prize": None if off["prize"] is None else round(d["prize"] - off["prize"], 6),
        "E_delta_prefer": None if off["prefer"] is None else round(e["prefer"] - off["prefer"], 6),
        "E_delta_prize": None if off["prize"] is None else round(e["prize"] - off["prize"], 6),
        "D_iso": d_iso,
        "E_iso": e_iso,
        "D_apply": d_apply,
        "E_apply": e_apply,
        "chosen": chosen,
    }


def _set_flags(brains: frozenset[str], align: bool) -> None:
    text = SRC.read_text(encoding="utf-8")
    br = "frozenset()" if not brains else "frozenset({\"" + "\", \"".join(sorted(brains)) + "\"})"
    text2, n1 = re.subn(
        r"POOL_FRONTLOAD_BRAINS: frozenset\[str\] = frozenset\([^)]*\)",
        f"POOL_FRONTLOAD_BRAINS: frozenset[str] = {br}",
        text,
        count=1,
    )
    text3, n2 = re.subn(
        r"POOL_FRONTLOAD_ALIGN_REPACK: bool = (True|False)",
        f"POOL_FRONTLOAD_ALIGN_REPACK: bool = {align}",
        text2,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f"flag replace failed n1={n1} n2={n2}")
    SRC.write_text(text3, encoding="utf-8")


def _refill_review() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    ok = fail = 0
    for dno in range(REFILL_LO, REFILL_HI + 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        try:
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
            pool_br = sp._pool_by_brain(pool)
            learner = sp.RollingSignalLearner()
            rows = sp.repack_by_brain(
                pool_br,
                sp._build_hint(draws, dno),
                learner.snapshot()[0],
                learner.snapshot()[1],
                target_draw_no=dno,
                hint_by_brain=sp.build_hint_by_brain(draws, dno),
            )
            p = [
                {
                    "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                    "nums": _nums(c),
                    "brain_tag": TAG,
                    "kind": "pool",
                    **({"role": c.get("role")} if c.get("role") else {}),
                }
                for c in (pool_br.get(TAG) or [])
            ]
            r = [
                {
                    "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                    "nums": _nums(c),
                    "brain_tag": TAG,
                    "kind": "repack",
                    "assemble": c.get("assemble") or "",
                    **(
                        {
                            "source": c.get("source"),
                            "source_set_no": c.get("source_set_no"),
                        }
                        if c.get("source")
                        else {}
                    ),
                }
                for c in rows
                if str(c.get("brain_tag")) == TAG
            ]
            save_pool_view_cache_one(
                dno,
                TAG,
                {"pool_by_brain": {TAG: p}, "repack_by_brain": {TAG: r}, "seed": SEED},
            )
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  refill fail {dno} {type(e).__name__}: {e}", flush=True)
        if dno % 20 == 0 or dno == REFILL_HI:
            print(f"  [refill] {dno} ok={ok} fail={fail}", flush=True)
    return {"ok": ok, "fail": fail, "lo": REFILL_LO, "hi": REFILL_HI, "brain": TAG}


def _hard_db() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        ledger = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE brain_tag='stat'"
            ).fetchone()[0]
        )
    finally:
        conn.close()
    return {"draws_max": dmax, "pred_1237": pred_1237, "ledger_stat": ledger}


def _write_md(doc: dict[str, Any]) -> str:
    g = doc["gate"]
    c = doc["cache"]
    c7 = doc["case_1237"]
    sm = c["summary"]
    lines = [
        "# K-REVIEW-FRONTLOAD (2026-08-22)",
        "",
        f"- **판정:** `{doc['verdict']}` · 금액뇌만 · 타깃적중 미입력 · 1237 신규예측 없음",
        f"- 시각: {doc['ts']}",
        "- 형 지시: 흩어진 번호를 #1→#10·몰아주기 #1→#5 우선 채움. 전수조사 후 금액뇌 패치",
        f"- 근거: `{OUT_JSON.name}`",
        "",
        "## 무엇을 바꿨나 (컨닝 아님)",
        "",
        "당첨 6개를 모으지 않는다. 지금 pool 10장에 **이미 찍힌 번호(합집합)** 를",
        "`number_scores`(금액축) 높은 것부터 #1에 6개, 다음을 #2… 로 다시 담는다.",
        "몰아주기 E시안은 그 #1~#5를 그대로 쓴다. score5(1~45 점수상위30)와 다를 수 있다.",
        "",
        "| 시안 | pool | 몰아주기 |",
        "|------|------|----------|",
        "| live | diversify+cover+shape | score5 |",
        "| D | score_union 앞채움 | score5 유지 |",
        "| E | score_union 앞채움 | 새 pool #1~#5 |",
        "| oracle | 합집합 안 당첨을 #1 (사후) | — 금지 |",
        "",
        "## 캐시 전수 (review · ≤1236)",
        "",
        f"- n_ok **{c['n_ok']}** / rows {c['n_rows']} · skip {c['n_skip']} · draws MAX **{c['draws_max']}** · pred_1237 **{c['pred_1237']}**",
        "",
        "| 시안 | n | set1적중 | max | mean | union | win∈union | full6회 | set1에6개회 | ge4장합 |",
        "|------|---|----------|-----|------|-------|-----------|---------|--------------|---------|",
    ]
    for name in ("live", "freq", "proxy", "oracle"):
        s = sm.get(name) or {}
        lines.append(
            f"| {name} | {s.get('n')} | {s.get('set1_hits')} | {s.get('max_hits')} | "
            f"{s.get('mean_hits')} | {s.get('union')} | {s.get('win_in_union')} | "
            f"{s.get('full6_n')} | {s.get('set1_full6_n')} | {s.get('ge4_n')} |"
        )
    lines += [
        "",
        "oracle의 set1_full6 = 합집합에 당첨 6개가 있을 때만 1. **적용 금지.**",
        "freq=10장 빈도순(H1류). proxy=몰아주기 30개 먼저+잔여빈도.",
        "",
        "## 게이트 1137–1236 n100 (라이브 expand · 빈 learner)",
        "",
        f"- HARD `{g['hard_ok']}` · peek **{g['peek_fail']}** · size {g['size_bad']} · err {g['n_errors']} · {g['elapsed_s']}s",
        "",
        "| | prefer | prize | Δprefer | Δprize | iso | set1적중 | pool변경 |",
        "|--|--------|-------|---------|--------|-----|----------|----------|",
        f"| off | {g['off']['prefer']} | {g['off']['prize']} | — | — | — | {g['off']['set1_hits']} | — |",
        f"| D | {g['D']['prefer']} | {g['D']['prize']} | {g['D_delta_prefer']} | {g['D_delta_prize']} | {g['D_iso']} | {g['D']['set1_hits']} | {g['D_changed']} |",
        f"| E | {g['E']['prefer']} | {g['E']['prize']} | {g['E_delta_prefer']} | {g['E_delta_prize']} | {g['E_iso']} | {g['E']['set1_hits']} | {g['E_changed']} |",
        "",
        f"- 채택 `{g['chosen']}` · D_apply `{g['D_apply']}` · E_apply `{g['E_apply']}`",
        "- 모니터: set1/max/ge4/ge6는 우열 아님(K-O). iso=Δprefer<0.005 ∧ Δprize<0.005",
        "",
        "## 1237 (캐시 재조립 · 신규예측 없음)",
        "",
    ]
    if c7.get("ok"):
        lines += [
            f"- 당첨 `{c7['win']}`",
            f"- live pool set1적중 {c7['live_pool'][0]['set1_hits']} · max {c7['live_pool'][0]['max_hits']} · union당첨 {c7['live_pool'][0]['win_in_union']}",
            f"- live 몰아주기 set1 `{c7['live_repack'][1][0] if c7['live_repack'][1] else None}` 적중 {c7['live_repack'][0].get('set1_hits')}",
            f"- front pool #1 `{c7['front_pool'][1][0] if c7['front_pool'][1] else None}` 적중 {c7['front_pool'][0]['set1_hits']}",
            f"- front 10장: `{c7['front_pool'][1]}`",
            f"- {c7['note']}",
        ]
    else:
        lines.append(f"- 1237 캐시 없음: {c7}")
    lines += [
        "",
        "## APPLY / 롤백",
        "",
        f"- 라이브 `POOL_FRONTLOAD_BRAINS={doc['flags']['brains']}` · ALIGN `{doc['flags']['align']}`",
        f"- refill {doc.get('refill')}",
        f"- HARD DB {doc.get('hard_db')}",
        "- 롤백=`POOL_FRONTLOAD_BRAINS=frozenset()` · ALIGN False",
        "- 우열·1등클레임 금지 · 1237 신규예측 없음",
        "",
        "## 파일",
        "",
        "- `app/testlotto/signal_pool.py` · `frontload_pool_by_scores`",
        f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        "- `tools/_k_review_frontload_census.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    print("cache census...", flush=True)
    cache = _cache_census()
    print(f"  n_ok={cache['n_ok']} summary={cache['summary']}", flush=True)
    print("1237 cache reassemble...", flush=True)
    case7 = _case_1237(_load_1237_cache())
    print(f"  1237 ok={case7.get('ok')}", flush=True)
    print("gate 1137-1236...", flush=True)
    gate = _gate()
    print(f"  chosen={gate['chosen']} hard={gate['hard_ok']}", flush=True)

    chosen = gate["chosen"]
    refill = {"skipped": True}
    flags = {"brains": [], "align": False}
    if chosen == "E":
        _set_flags(frozenset({TAG}), True)
        flags = {"brains": [TAG], "align": True}
        print("APPLY E refill review 1037-1236...", flush=True)
        refill = _refill_review()
    elif chosen == "D":
        _set_flags(frozenset({TAG}), False)
        flags = {"brains": [TAG], "align": False}
        print("APPLY D refill review 1037-1236...", flush=True)
        refill = _refill_review()
    else:
        print("HOLD flags stay off", flush=True)

    hard_db = _hard_db()
    verdict = (
        "APPLY_OK"
        if chosen
        else (
            "HOLD_ISO_FAIL"
            if gate["hard_ok"] and not (gate["D_iso"] or gate["E_iso"])
            else ("HOLD_NO_DESIGN" if gate["hard_ok"] else "FAIL")
        )
    )
    doc = {
        "id": "K-REVIEW-FRONTLOAD",
        "ts": _now(),
        "verdict": verdict,
        "cache": cache,
        "case_1237": {
            k: v
            for k, v in case7.items()
            if k != "live_pool" or True
        },
        "gate": gate,
        "flags": flags,
        "refill": refill,
        "hard_db": hard_db,
        "iso": ISO,
        "peek": 0,
        "pred_1237_new": False,
    }
    # shrink 1237 lists already small
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(verdict, flush=True)
    print(OUT_MD, flush=True)


if __name__ == "__main__":
    main()
