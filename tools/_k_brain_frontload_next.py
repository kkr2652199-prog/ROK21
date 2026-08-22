# -*- coding: utf-8 -*-
"""K-BRAIN-FRONTLOAD-NEXT — 금액뇌 다음. markov·stat 엔진점수 앞채움.

공식/당첨입력 없음. 각 뇌 number_scores(엔진)로 합집합을 #1→#10.
E = 몰아주기=새 pool #1~#5. 게이트 통과 뇌만 플래그에 추가(review 유지).
1237 신규 predict 없음. 통과 뇌 캐시 1037–1236 리필 + 1237은 캐시재조립만.
"""
from __future__ import annotations

import json
import random
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

from tools._k_review_frontload_census import (  # noqa: E402
    DB,
    GATE_HI,
    GATE_LO,
    ISO,
    REFILL_HI,
    REFILL_LO,
    SEED,
    SRC,
    _axis,
    _key,
    _m,
    _nums,
    _pack_ranked,
    _set_flags,
    _set_stats,
)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KBRAIN_FRONTLOAD_NEXT.json"
OUT_MD = ROOT / "reports" / "20260822_KBRAIN_FRONTLOAD_NEXT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
TAGS = ("markov", "stat")
KEEP = {"review"}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _cache_census(tag: str) -> dict[str, Any]:
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
            (tag,),
        ).fetchall()
    finally:
        conn.close()
    acc: dict[str, list[dict[str, Any]]] = {"live": [], "freq": [], "oracle": [], "proxy": []}
    n_skip = 0
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
        proxy_rank: list[int] = []
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
        acc["live"].append(_set_stats(psets, win))
        acc["freq"].append(_set_stats(freq_sets, win))
        acc["oracle"].append(_set_stats(oracle_sets, win))
        acc["proxy"].append(_set_stats(proxy_sets, win))

    def _summ(xs: list[dict[str, Any]]) -> dict[str, Any]:
        if not xs:
            return {}
        keys = (
            "set1_hits",
            "max_hits",
            "mean_hits",
            "ge4",
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
        "summary": {k: _summ(v) for k, v in acc.items()},
    }


def _gate(tag: str) -> dict[str, Any]:
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
    hit_sc: list[float] = []
    miss_sc: list[float] = []

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
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
            p = (sp._pool_by_brain(pool).get(tag) or [])
            learner = sp.RollingSignalLearner()
            num_ema, pos_ema = learner.snapshot()
            hint_b = sp.build_hint_by_brain(draws, dno)
            scores = sp.number_scores(
                p,
                (hint_b or {}).get(tag, sp._build_hint(draws, dno)),
                num_ema,
                pos_ema,
                brain_tag=tag,
            )
            classic = sp.repack_sets(scores)
            fl = sp.frontload_pool_by_scores(p, scores, n=10, brain_tag=tag)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{dno} {type(e).__name__}: {e}")
            continue
        if len(p) != 10 or len(classic) != 5 or len(fl) != 10:
            size_bad += 1
            continue
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
        win = {int(win_row[j]) for j in range(6)}
        union = {n for s in p for n in _nums(s)}
        for n in union:
            (hit_sc if n in win else miss_sc).append(float(scores.get(n, 0.0)))
        pref_t = cs.prefer_table(draws, brain="markov")
        prize_t = cs.prize_table(draws, brain="review")
        off_p = [{"nums": _nums(s)} for s in p]
        off_r = [{"nums": list(s)} for s in classic]
        d_p = [{"nums": _nums(s)} for s in fl]
        e_r = [{"nums": _nums(s)} for s in fl[:5]]
        if [_key(_nums(s)) for s in p] != [_key(_nums(s)) for s in fl]:
            d_changed += 1
        if [_key(s) for s in classic] != [_key(_nums(s)) for s in fl[:5]]:
            e_changed += 1
        for name, psets, rsets in (
            ("off", off_p, off_r),
            ("D", d_p, off_r),
            ("E", d_p, e_r),
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
        if (i + 1) % 20 == 0 or dno == GATE_HI:
            print(f"  [gate {tag}] {i+1}/{len(rows)} d={dno} n_ok={n_ok}", flush=True)

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
        if None in (off["prefer"], on["prefer"], off["prize"], on["prize"]):
            return False
        return (on["prefer"] - off["prefer"] < ISO) and (on["prize"] - off["prize"] < ISO)

    hard = n_ok == (GATE_HI - GATE_LO + 1) and peek_fail == 0 and size_bad == 0 and not errors
    d_iso, e_iso = iso(d), iso(e)
    d_apply = bool(hard and d_iso and d_changed > 0)
    e_apply = bool(hard and e_iso and e_changed > 0)
    chosen = "E" if e_apply else ("D" if d_apply else None)
    return {
        "tag": tag,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
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
        "engine_union": {
            "hit_score": _m(hit_sc),
            "miss_score": _m(miss_sc),
            "delta": None
            if not hit_sc or not miss_sc
            else round(mean(hit_sc) - mean(miss_sc), 6),
            "note": "합집합 안 번호의 엔진점수. 당첨>비당첨이면 핸들. 우열아님.",
        },
    }


def _refill(tag: str) -> dict[str, Any]:
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
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=[tag])
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
                    "brain_tag": tag,
                    "kind": "pool",
                    **({"role": c.get("role")} if c.get("role") else {}),
                }
                for c in (pool_br.get(tag) or [])
            ]
            r = [
                {
                    "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
                    "nums": _nums(c),
                    "brain_tag": tag,
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
                if str(c.get("brain_tag")) == tag
            ]
            save_pool_view_cache_one(
                dno,
                tag,
                {"pool_by_brain": {tag: p}, "repack_by_brain": {tag: r}, "seed": SEED},
            )
            ok += 1
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"  refill fail {tag} {dno} {type(e).__name__}: {e}", flush=True)
        if dno % 40 == 0 or dno == REFILL_HI:
            print(f"  [refill {tag}] {dno} ok={ok} fail={fail}", flush=True)
    return {"tag": tag, "ok": ok, "fail": fail, "lo": REFILL_LO, "hi": REFILL_HI}


def _rewrite_1237(tag: str) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.pool_view_cache import save_pool_view_cache_one

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no=1237",
            (tag,),
        ).fetchone()
        win_row = conn.execute(
            "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=1237"
        ).fetchone()
    finally:
        conn.close()
    if not row or not win_row:
        return {"ok": False, "tag": tag, "reason": "no_cache"}
    pool = json.loads(row["pool_json"] or "[]")
    win = {int(win_row[f"num{i}"]) for i in range(1, 7)}
    set_learn_as_of(1237)
    draws = _get_draws_before(1237)
    learner = sp.RollingSignalLearner()
    scores = sp.number_scores(
        pool,
        (sp.build_hint_by_brain(draws, 1237) or {}).get(tag, sp._build_hint(draws, 1237)),
        learner.snapshot()[0],
        learner.snapshot()[1],
        brain_tag=tag,
    )
    fl = sp.frontload_pool_by_scores(pool, scores, n=10, brain_tag=tag)
    p = [
        {
            "set_no": i + 1,
            "nums": [int(x) for x in c["nums"]],
            "brain_tag": tag,
            "kind": "pool",
            "role": c.get("role"),
        }
        for i, c in enumerate(fl)
    ]
    r = [
        {
            "set_no": i + 1,
            "nums": [int(x) for x in c["nums"]],
            "brain_tag": tag,
            "kind": "repack",
            "assemble": "frontload_align",
            "source": "pool",
            "source_set_no": i + 1,
        }
        for i, c in enumerate(fl[:5])
    ]
    save_pool_view_cache_one(
        1237,
        tag,
        {"pool_by_brain": {tag: p}, "repack_by_brain": {tag: r}, "seed": SEED},
    )
    return {
        "ok": True,
        "tag": tag,
        "win": sorted(win),
        "set1": p[0]["nums"] if p else [],
        "set1_hits": len(set(p[0]["nums"]) & win) if p else 0,
        "note": "캐시재조립. predict_sets 없음",
    }


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
    lines = [
        "# K-BRAIN-FRONTLOAD-NEXT (2026-08-22)",
        "",
        f"- **판정:** `{doc['verdict']}` · 공식없음 · 엔진 `number_scores` · 당첨미입력",
        f"- 시각: {doc['ts']}",
        "- 이어서: 금액뇌 APPLY 다음 markov·stat. 통과 뇌만 추가",
        f"- 근거: `{OUT_JSON.name}`",
        "",
        "## 방법",
        "",
        "당첨 6개를 모으는 공식 없음. 각 뇌가 이미 가진 `number_scores`로",
        "그 뇌 pool 합집합을 #1부터 채운다. 몰아주기 E = 새 #1~#5.",
        "oracle(사후 당첨모음)은 모니터·금지.",
        "",
        f"- 유지 review · 추가 `{doc['applied']}` · HOLD `{doc['held']}`",
        f"- 라이브 BRAINS `{doc['flags']['brains']}` · ALIGN `{doc['flags']['align']}`",
        "",
    ]
    for tag in TAGS:
        c = doc["by_brain"][tag]["cache"]
        g = doc["by_brain"][tag]["gate"]
        sm = c["summary"]
        lines += [
            f"## {tag}",
            "",
            f"- 캐시 n_ok **{c['n_ok']}** / {c['n_rows']} · skip {c['n_skip']}",
            "",
            "| 시안 | set1 | max | union | win∈union | full6회 | set1에6 | ge4장 |",
            "|------|------|-----|-------|-----------|---------|---------|-------|",
        ]
        for name in ("live", "freq", "proxy", "oracle"):
            s = sm.get(name) or {}
            lines.append(
                f"| {name} | {s.get('set1_hits')} | {s.get('max_hits')} | {s.get('union')} | "
                f"{s.get('win_in_union')} | {s.get('full6_n')} | {s.get('set1_full6_n')} | {s.get('ge4_n')} |"
            )
        eu = g.get("engine_union") or {}
        lines += [
            "",
            f"- 게이트 HARD `{g['hard_ok']}` peek **{g['peek_fail']}** size {g['size_bad']} err {g['n_errors']} {g['elapsed_s']}s",
            f"- off prefer/prize `{g['off']['prefer']}` / `{g['off']['prize']}` set1 `{g['off']['set1_hits']}`",
            f"- E Δprefer `{g['E_delta_prefer']}` Δprize `{g['E_delta_prize']}` iso `{g['E_iso']}` set1 `{g['E']['set1_hits']}`",
            f"- D Δprefer `{g['D_delta_prefer']}` Δprize `{g['D_delta_prize']}` iso `{g['D_iso']}`",
            f"- 채택 `{g['chosen']}` · 엔진합집합 점수 당첨 `{eu.get('hit_score')}` 비당첨 `{eu.get('miss_score')}` Δ `{eu.get('delta')}`",
            "",
        ]
        c7 = doc["by_brain"][tag].get("case_1237")
        if c7:
            lines += [f"- 1237 재조립 `{c7}`", ""]
    lines += [
        "## APPLY / 롤백",
        "",
        f"- refill {doc.get('refill')}",
        f"- HARD DB {doc.get('hard_db')}",
        "- 롤백=`POOL_FRONTLOAD_BRAINS=frozenset({\"review\"})` (금액뇌만) 또는 전부 off",
        "- 우열·1등클레임 금지 · 1237 신규예측 없음",
        "",
        "## 파일",
        "",
        "- `app/testlotto/signal_pool.py`",
        f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        "- `tools/_k_brain_frontload_next.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    by: dict[str, Any] = {}
    applied: list[str] = []
    held: list[str] = []
    for tag in TAGS:
        print(f"cache {tag}...", flush=True)
        cache = _cache_census(tag)
        print(f"  n_ok={cache['n_ok']}", flush=True)
        print(f"gate {tag}...", flush=True)
        gate = _gate(tag)
        print(f"  chosen={gate['chosen']} hard={gate['hard_ok']}", flush=True)
        by[tag] = {"cache": cache, "gate": gate}
        if gate["chosen"]:
            applied.append(tag)
        else:
            held.append(tag)

    brains = frozenset(KEEP | set(applied))
    align = True
    _set_flags(brains, align)
    print(f"flags brains={sorted(brains)} align={align}", flush=True)

    refill = []
    for tag in applied:
        print(f"refill {tag}...", flush=True)
        refill.append(_refill(tag))
        print(f"1237 rewrite {tag}...", flush=True)
        by[tag]["case_1237"] = _rewrite_1237(tag)

    hard_db = _hard_db()
    if applied and not held:
        verdict = "APPLY_OK"
    elif applied:
        verdict = "APPLY_PARTIAL"
    elif all(by[t]["gate"]["hard_ok"] for t in TAGS):
        verdict = "HOLD_ISO_FAIL"
    else:
        verdict = "FAIL"
    doc = {
        "id": "K-BRAIN-FRONTLOAD-NEXT",
        "ts": _now(),
        "verdict": verdict,
        "applied": applied,
        "held": held,
        "flags": {"brains": sorted(brains), "align": align},
        "by_brain": by,
        "refill": refill,
        "hard_db": hard_db,
        "iso": ISO,
        "pred_1237_new": False,
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(verdict, flush=True)


if __name__ == "__main__":
    main()
