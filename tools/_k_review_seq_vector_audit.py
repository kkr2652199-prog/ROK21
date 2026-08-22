# -*- coding: utf-8 -*-
"""K-REVIEW-SEQ-VECTOR-AUDIT — 금액뇌 소진벡터 결과 정밀확인.

캐시 1037–1236 review vs 라이브 expand(빈 learner) · 기하 · 리셋겹침 ·
발권1~5=pool1~5 · 1237캐시 상태. 버그/아이디어만. 당첨 미입력 APPLY 없음.
1237 신규 predict 없음.
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KREVIEW_SEQ_VECTOR_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260822_KREVIEW_SEQ_VECTOR_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
TAG = "review"
LO, HI = 1037, 1236
SEED = 42
SAMPLE_LIVE = (1137, 1186, 1236)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _key(xs) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in xs))


def _m(xs: list[float]) -> float | None:
    return round(mean(xs), 6) if xs else None


def _geom(sets: list[list[int]]) -> dict[str, Any]:
    skill = sets[:5]
    rest = sets[5:]
    u5: set[int] = set()
    for s in skill:
        u5.update(s)
    u10: set[int] = set(u5)
    for s in rest:
        u10.update(s)
    u7: set[int] = set()
    for s in sets[:7]:
        u7.update(s)
    wrap = sets[7:]
    wrap_u: set[int] = set()
    for s in wrap:
        wrap_u.update(s)
    cnt: Counter[int] = Counter()
    for s in skill:
        cnt.update(set(s))
    bad6 = sum(1 for s in sets if len(s) != 6 or len(set(s)) != 6)
    return {
        "n": len(sets),
        "union5": len(u5),
        "union7": len(u7),
        "union10": len(u10),
        "s1_s2": len(set(skill[0]) & set(skill[1])) if len(skill) > 1 else 0,
        "multi5": sum(1 for v in cnt.values() if v >= 2),
        "wrap_n": len(wrap),
        "wrap_overlap7": len(wrap_u & u7),
        "bad6": bad6,
        "roles": [],
    }


def _cache_audit() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT draw_no, pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ? ORDER BY draw_no",
            (TAG, LO, HI),
        ).fetchall()
        row1237 = conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no=1237",
            (TAG,),
        ).fetchone()
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
        draws = {
            int(r["draw_no"]): {int(r[f"num{i}"]) for i in range(1, 7)}
            for r in conn.execute(
                "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws "
                "WHERE draw_no BETWEEN ? AND ?",
                (LO, HI),
            )
        }
    finally:
        conn.close()

    size_bad = 0
    src = Counter()
    roles = Counter()
    geoms: list[dict[str, Any]] = []
    set1_hits: list[int] = []
    max_hits: list[int] = []
    samples = {}
    for r in rows:
        dno = int(r["draw_no"])
        pool = json.loads(r["pool_json"] or "[]")
        psets = [_nums(s) for s in sorted(pool, key=lambda x: int(x.get("set_no") or 0))]
        if len(psets) != 10:
            size_bad += 1
            continue
        g = _geom(psets)
        geoms.append(g)
        for s in pool:
            roles[str(s.get("role") or "")] += 1
            src[str(s.get("source") or s.get("role") or "")] += 1
        win = draws.get(dno)
        if win:
            hs = [len(set(s) & win) for s in psets]
            set1_hits.append(hs[0])
            max_hits.append(max(hs))
        if dno in (1137, 1186, 1236):
            samples[str(dno)] = {
                "sets": psets,
                "geom": g,
                "roles": [s.get("role") for s in sorted(pool, key=lambda x: int(x.get("set_no") or 0))],
                "sources": [s.get("source") for s in sorted(pool, key=lambda x: int(x.get("set_no") or 0))],
            }

    c1237: dict[str, Any] = {"ok": False}
    if row1237:
        p = json.loads(row1237["pool_json"] or "[]")
        psets = [_nums(s) for s in sorted(p, key=lambda x: int(x.get("set_no") or 0))]
        srcs = [s.get("source") or s.get("role") for s in p]
        g = _geom(psets) if psets else {}
        c1237 = {
            "ok": True,
            "n": len(psets),
            "geom": g,
            "set1": psets[0] if psets else [],
            "sources": srcs,
            "looks_seq": bool(g.get("union5") == 30 and g.get("s1_s2") == 0),
            "looks_frontload": psets[0] == [15, 18, 27, 34, 37, 40] if psets else False,
        }

    def col(k: str) -> list[float]:
        return [float(x.get(k) or 0) for x in geoms]

    return {
        "n_rows": len(rows),
        "n_ok": len(geoms),
        "size_bad": size_bad,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "ledger_stat": ledger,
        "roles": dict(roles),
        "sources": dict(src),
        "union5": _m(col("union5")),
        "union5_n30": sum(1 for x in geoms if x["union5"] == 30),
        "union7": _m(col("union7")),
        "union10": _m(col("union10")),
        "s1_s2": _m(col("s1_s2")),
        "s1_s2_n0": sum(1 for x in geoms if x["s1_s2"] == 0),
        "multi5": _m(col("multi5")),
        "multi5_n0": sum(1 for x in geoms if x["multi5"] == 0),
        "wrap_overlap7": _m(col("wrap_overlap7")),
        "bad6_sum": int(sum(x["bad6"] for x in geoms)),
        "set1_hits": _m([float(x) for x in set1_hits]),
        "max_hits": _m([float(x) for x in max_hits]),
        "samples": samples,
        "cache_1237": c1237,
    }


def _live_match() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.coordinator import PREDICT_MODULES
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cached = {
            int(r["draw_no"]): json.loads(r["pool_json"] or "[]")
            for r in conn.execute(
                "SELECT draw_no, pool_json FROM testlotto_pool_view_cache "
                "WHERE brain=? AND draw_no IN (1137,1186,1236)",
                (TAG,),
            )
        }
    finally:
        conn.close()

    out = []
    for dno in SAMPLE_LIVE:
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        peek = max((int(d["draw_no"]) for d in draws), default=0) >= dno
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
        live = [
            _key(_nums(s))
            for s in sorted(pool, key=lambda x: int(x.get("pred_set_no") or x.get("set_no") or 0))
        ]
        ch = [
            _key(_nums(s))
            for s in sorted(cached.get(dno) or [], key=lambda x: int(x.get("set_no") or 0))
        ]
        random.seed(sp._pass_seed(SEED, dno, 0))
        tickets = PREDICT_MODULES[TAG].predict_sets(draws, 5)
        tkeys = [_key(_nums(s)) for s in tickets]
        out.append(
            {
                "dno": dno,
                "peek": peek,
                "live_n": len(live),
                "cache_n": len(ch),
                "cache_eq_live": live == ch,
                "ticket5_eq_pool5": tkeys == live[:5],
                "live_set1": list(live[0]) if live else [],
                "cache_set1": list(ch[0]) if ch else [],
                "ticket_set1": list(tkeys[0]) if tkeys else [],
            }
        )
    return {"samples": out, "all_cache_eq_live": all(x["cache_eq_live"] for x in out),
            "all_ticket_eq_pool5": all(x["ticket5_eq_pool5"] for x in out)}


def _write_md(doc: dict[str, Any]) -> str:
    c = doc["cache"]
    lv = doc["live"]
    bugs = doc["bugs"]
    ideas = doc["ideas"]
    lines = [
        "# K-REVIEW-SEQ-VECTOR-AUDIT (2026-08-22)",
        "",
        f"- **판정:** `{doc['verdict']}` · READ-ONLY · APPLY **없음**",
        f"- 시각: {doc['ts']}",
        "- 형: 금액뇌 벡터 결과물 정밀분석 · 버그 · 아이디어",
        f"- 근거: `{OUT_JSON.name}` · 선행 `{doc['prior']}`",
        "",
        "## 벡터가 뭔가",
        "",
        "정식 `backtest_runs` 등수표가 아니다. 금액뇌 `expand_pool` 소진분포를",
        f"캐시 **{c['n_ok']}**/200 (1037–1236)에 쓴 것 + 게이트 n100 기하.",
        "",
        "## 캐시 전수 (review 1037–1236)",
        "",
        f"- rows {c['n_rows']} · size≠10 **{c['size_bad']}** · bad6(중복/길이) **{c['bad6_sum']}**",
        f"- skill5합 평균 **{c['union5']}** · 정확히30 **{c['union5_n30']}**/{c['n_ok']}",
        f"- #1∩#2 평균 **{c['s1_s2']}** · 0인회 **{c['s1_s2_n0']}**",
        f"- 1~5에서 2장이상 번호 평균 **{c['multi5']}** · 0인회 **{c['multi5_n0']}**",
        f"- 1~7합 **{c['union7']}** · 10장합 **{c['union10']}** · #8~10∩(1~7) **{c['wrap_overlap7']}**",
        f"- 모니터 set1적중 **{c['set1_hits']}** · max **{c['max_hits']}** (우열아님)",
        f"- roles `{c['roles']}`",
        f"- sources `{c['sources']}`",
        "",
        "## 라이브 대조 (빈 learner · seed42 · 1137/1186/1236)",
        "",
        f"- 캐시=라이브 pool **{lv['all_cache_eq_live']}**",
        f"- 발권 predict_sets(5)=pool #1~#5 **{lv['all_ticket_eq_pool5']}**",
        "",
    ]
    for s in lv["samples"]:
        lines.append(
            f"- {s['dno']}: cache=live `{s['cache_eq_live']}` · ticket=pool1-5 `{s['ticket5_eq_pool5']}` "
            f"peek `{s['peek']}` set1 live `{s['live_set1']}`"
        )
    c7 = c["cache_1237"]
    lines += [
        "",
        "## 1237 캐시 (신규예측 없음)",
        "",
        f"- `{c7}`",
        "",
        "## 버그",
        "",
    ]
    for b in bugs:
        lines.append(f"- **{b['id']}** · {b['sev']} · {b['text']}")
    lines += ["", "## 아이디어 (APPLY 아님 · 형 선택)", ""]
    for i, idea in enumerate(ideas, 1):
        lines.append(f"{i}. {idea}")
    lines += [
        "",
        f"- HARD DB MAX `{c['draws_max']}` · pred_1237 **{c['pred_1237']}** · 원장 stat `{c['ledger_stat']}`",
        "- 우열금지 · 1237 신규예측 없음",
        "",
        "## 파일",
        "",
        f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        "- `tools/_k_review_seq_vector_audit.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    t0 = time.perf_counter()
    print("cache audit...", flush=True)
    cache = _cache_audit()
    print(f"  n_ok={cache['n_ok']} union5={cache['union5']}", flush=True)
    print("live match...", flush=True)
    live = _live_match()
    print(live, flush=True)

    bugs: list[dict[str, Any]] = []
    if cache["size_bad"] or cache["bad6_sum"]:
        bugs.append(
            {
                "id": "B-SIZE",
                "sev": "P1",
                "text": f"size≠10 {cache['size_bad']} · bad6 {cache['bad6_sum']}",
            }
        )
    if cache["union5_n30"] != cache["n_ok"]:
        bugs.append(
            {
                "id": "B-TIER1-HOLE",
                "sev": "P2",
                "text": (
                    f"skill5합=30이 아닌 회 {cache['n_ok']-cache['union5_n30']}/{cache['n_ok']}. "
                    "tier1 탈락해도 번호는 풀에서 빠짐 → 구멍. 평균 "
                    f"{cache['union5']}."
                ),
            }
        )
    if (cache["wrap_overlap7"] or 0) > 0:
        bugs.append(
            {
                "id": "B-RESET-WRAP",
                "sev": "P2",
                "text": (
                    f"#8~10이 1~7과 평균 {cache['wrap_overlap7']}개 겹침. "
                    "45소진 후 풀 리셋(2바퀴). cover/shape 라벨이지만 실제는 재추출."
                ),
            }
        )
    if not live["all_cache_eq_live"]:
        bugs.append(
            {
                "id": "B-CACHE-LIVE",
                "sev": "P1",
                "text": f"캐시≠라이브 샘플 {live['samples']}",
            }
        )
    if not live["all_ticket_eq_pool5"]:
        bugs.append(
            {
                "id": "B-TICKET-POOL",
                "sev": "P1",
                "text": "발권5 ≠ pool1~5. 시드/경로 불일치.",
            }
        )
    if cache["cache_1237"].get("ok") and not cache["cache_1237"].get("looks_seq"):
        bugs.append(
            {
                "id": "B-1237-STALE",
                "sev": "P3",
                "text": "1237 review 캐시가 소진벡터가 아님(이전 앞채움 재조립 잔존). 신규예측은 안 함.",
            }
        )
    if cache["sources"] and "review_seq_deplete" not in json.dumps(cache["sources"]):
        bugs.append(
            {
                "id": "B-SOURCE",
                "sev": "P3",
                "text": f"source에 review_seq_deplete 적음. `{cache['sources']}`",
            }
        )

    ideas = [
        "리셋 금지: 45개만 7장+나머지3은 패딩 없이 멈추거나, 8~10은 빈칸/원본 미사용. 2바퀴 겹침 제거.",
        "tier1 탈락 시 뽑은 6개를 풀에 되돌리거나, 필터를 소진 후에만 적용. 구멍(union5<30) 방지.",
        "6~10 라벨 cover/shape는 허위. seq면 전부 skill_seq 또는 #6=2순위 엔진장으로 문서화.",
        "발권5와 pool1~5가 같으면(이번 실측) 몰아주기 score5와 #1 정렬은 별 GO.",
        "1237은 예측 재실행 없이 캐시만 소진재조립할지 형이 결정.",
    ]

    if not bugs:
        verdict = "AUDIT_OK"
    elif any(b["sev"] == "P1" for b in bugs):
        verdict = "AUDIT_BUGS"
    else:
        verdict = "AUDIT_NOTES"

    doc = {
        "id": "K-REVIEW-SEQ-VECTOR-AUDIT",
        "ts": _now(),
        "verdict": verdict,
        "prior": "20260822_KREVIEW_SEQ_DISTRIBUTE.json",
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "cache": cache,
        "live": live,
        "bugs": bugs,
        "ideas": ideas,
        "pred_1237_new": False,
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(verdict, json.dumps(bugs, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
