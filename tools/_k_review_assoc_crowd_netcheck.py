# -*- coding: utf-8 -*-
"""K-REVIEW-ASSOC-CROWD-NETCHECK — 6번 핫쌍몰림 순수증분.

S0 READ-ONLY. 핫쌍 가중 없음. 보너스 미사용. peek=as_of 이전만.
PASS 켜지 않음. 1237예측 없음. 몰아주기 없음.
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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260827_KREVIEW_ASSOC_CROWD_NETCHECK.json"
OUT_MD = ROOT / "reports" / "20260827_KREVIEW_ASSOC_CROWD_NETCHECK.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42
GATE_LO, GATE_HI = 1137, 1236
HOT_NS = (10, 20, 30)
THRESH_KS = (2, 3, 4, 5)
# S1 주정의: 상위 20쌍 중 한 장에 3개 이상. 거의없음 = 출력 2% 미만.
PRIMARY_N = 20
PRIMARY_K = 3
ALMOST_NONE = 0.02


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _pairs15(nums: list[int]) -> list[tuple[int, int]]:
    s = sorted(int(x) for x in nums)
    return [(s[i], s[j]) for i in range(6) for j in range(i + 1, 6)]


def _hot_set(draws: list[dict], n: int) -> set[tuple[int, int]]:
    c: Counter[tuple[int, int]] = Counter()
    for d in draws:
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        if len(nums) != 6:
            continue
        for p in _pairs15(nums):
            c[p] += 1
    return {p for p, _ in c.most_common(int(n))}


def _crowd(nums: list[int], hot: set[tuple[int, int]]) -> int:
    return sum(1 for p in _pairs15(nums) if p in hot)


def _hist(xs: list[int]) -> dict[str, int]:
    h: Counter[int] = Counter(xs)
    return {str(k): h[k] for k in sorted(h)}


def _s0() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.review_brain.draw_assoc import (
        PREDICT_USE_BONUS_LINKS,
        REVIEW_ASSOC_KB_READ,
    )
    from app.testlotto.brains.review_brain.rare_consec import REVIEW_CONSEC_PASS_WIRE
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
        assoc_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_draw_assoc").fetchone()[0])
    finally:
        conn.close()

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
    n_ok = peek_fail = size_bad = bonus_in = 0
    errors: list[str] = []
    crowds: dict[int, list[int]] = {n: [] for n in HOT_NS}
    win_crowds: dict[int, list[int]] = {n: [] for n in HOT_NS}
    n_sets = 0
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            as_of = max((int(d["draw_no"]) for d in draws), default=0)
            if as_of >= dno:
                peek_fail += 1
                continue
            hots = {n: _hot_set(draws, n) for n in HOT_NS}
            try:
                random.seed(SEED)
                pool = [
                    c
                    for c in sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
                    if str(c.get("brain_tag")) == "review"
                ]
            except Exception as e:  # noqa: BLE001
                errors.append(f"{dno} {type(e).__name__}: {e}")
                continue
            if len(pool) != 10:
                size_bad += 1
                continue
            actual = None
            conn2 = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
            try:
                ar = conn2.execute(
                    "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?",
                    (dno,),
                ).fetchone()
            finally:
                conn2.close()
            if ar:
                actual = sorted(int(x) for x in ar)
            for c in pool:
                nums = [int(x) for x in (c.get("nums") or [])]
                if len(nums) != 6:
                    bonus_in += 1
                    continue
                n_sets += 1
                for n in HOT_NS:
                    crowds[n].append(_crowd(nums, hots[n]))
            if actual and len(actual) == 6:
                for n in HOT_NS:
                    win_crowds[n].append(_crowd(actual, hots[n]))
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [s0] {i+1}/{len(rows)} d={dno} n_ok={n_ok}", flush=True)
    finally:
        pass

    def pack(xs: list[int]) -> dict[str, Any]:
        if not xs:
            return {}
        rates = {}
        for k in THRESH_KS:
            rates[str(k)] = round(sum(1 for x in xs if x >= k) / len(xs), 6)
        return {
            "n": len(xs),
            "mean": round(sum(xs) / len(xs), 6),
            "hist": _hist(xs),
            "p_ge_k": rates,
        }

    by_n = {str(n): pack(crowds[n]) for n in HOT_NS}
    win_by_n = {str(n): pack(win_crowds[n]) for n in HOT_NS}
    prim = by_n[str(PRIMARY_N)]
    p_ge = float((prim.get("p_ge_k") or {}).get(str(PRIMARY_K) or 0) or 0)
    net_n = int(round(p_ge * n_sets)) if n_sets else 0
    return {
        "def": {
            "crowd_pair_count": "한 장 15쌍 중 as_of이전 상위N 본번호쌍에 든 개수",
            "hot_n_primary": PRIMARY_N,
            "k_primary": PRIMARY_K,
            "almost_none": ALMOST_NONE,
            "mains_only": True,
            "bonus_used": False,
        },
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "assoc_n": assoc_n,
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "bonus_in": bonus_in,
        "n_errors": len(errors),
        "n_sets": n_sets,
        "review_by_hot_n": by_n,
        "actual_by_hot_n": win_by_n,
        "primary_p_ge_k": p_ge,
        "primary_net_n": net_n,
        "flags": {
            "REVIEW_ASSOC_KB_READ": bool(REVIEW_ASSOC_KB_READ),
            "PREDICT_USE_BONUS_LINKS": bool(PREDICT_USE_BONUS_LINKS),
            "REVIEW_CONSEC_PASS_WIRE": bool(REVIEW_CONSEC_PASS_WIRE),
        },
    }


def _write_md(doc: dict[str, Any]) -> str:
    s0 = doc["s0"]
    prim = s0["review_by_hot_n"][str(PRIMARY_N)]
    win = s0["actual_by_hot_n"].get(str(PRIMARY_N) or {}) or {}
    return "\n".join(
        [
            "# K-REVIEW-ASSOC-CROWD-NETCHECK (2026-08-27)",
            "",
            f"- **판정:** `{doc['verdict']}` · S0 READ-ONLY · 핫쌍 가중 없음 · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 6번 한 장 핫쌍 과다 패스. net 확인 후 배선 여부. 유사도 아이디어 제외.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## 정의",
            "",
            f"- crowd_pair_count = 본번호 6개의 15쌍 중, as_of 이전 당첨에서 빈도 상위 **N={PRIMARY_N}** 쌍에 든 개수",
            f"- 몰림 임계 **K={PRIMARY_K}** (한 장에 핫쌍 {PRIMARY_K}개 이상)",
            "- 보너스 쌍 미사용. peek=draw_no < target.",
            f"- net = 이미 1·2·3번을 통과한 출력 장 중 crowd≥K 인 비율(추가 패스 후보)",
            "",
            "## S0 1137–1236 n100",
            "",
            f"- peek `{s0['peek_fail']}` n_ok `{s0['n_ok']}` sets `{s0['n_sets']}` bonus_in `{s0['bonus_in']}`",
            f"- review N=20 평균 `{prim.get('mean')}` hist `{prim.get('hist')}`",
            f"- review p(≥2/3/4/5) `{prim.get('p_ge_k')}`",
            f"- 당첨회(모니터) N=20 평균 `{win.get('mean')}` p_ge `{win.get('p_ge_k')}`",
            f"- 주정의 net `{s0['primary_net_n']}` / `{s0['n_sets']}` = `{s0['primary_p_ge_k']}`",
            f"- pred_1237 `{s0['pred_1237']}` · pred_1239 `{s0['pred_1239']}` · MAX `{s0['dmax']}` · assoc `{s0['assoc_n']}`",
            f"- elapsed `{s0['elapsed_s']}`s",
            "",
            "## 감도 N=10/30",
            "",
            f"- N10 `{s0['review_by_hot_n']['10'].get('p_ge_k')}` mean `{s0['review_by_hot_n']['10'].get('mean')}`",
            f"- N30 `{s0['review_by_hot_n']['30'].get('p_ge_k')}` mean `{s0['review_by_hot_n']['30'].get('mean')}`",
            "",
            "## S1 판정",
            "",
            f"- `{doc['s1']}`",
            f"- 사유: {doc['reason']}",
            f"- S2 `{doc['s2']}`",
            "- `REVIEW_ASSOC_KB_READ=True` 유지. CROWD_PASS 신설·라이브 **안 함**.",
            "",
            "## 롤백",
            "",
            "- READ: `REVIEW_ASSOC_KB_READ=False`",
            "",
            "## 파일",
            "",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    print("S0 crowd", flush=True)
    s0 = _s0()
    p = float(s0["primary_p_ge_k"] or 0)
    net_n = int(s0["primary_net_n"] or 0)
    if s0["peek_fail"] != 0 or s0["pred_1237"] != 0:
        s1 = "HOLD_HARD"
        reason = "peek 또는 pred_1237 이상."
        verdict = "HOLD_HARD"
        s2 = "skipped"
    elif net_n > 0 and p >= ALMOST_NONE:
        s1 = "WIRE_CANDIDATE"
        reason = (
            f"출력 {s0['n_sets']}장 중 crowd≥{PRIMARY_K} 가 {net_n} ({p}). "
            "1·2·3 통과 뒤에도 몰림 장이 남음. S2는 형 GO 후에만. 이번 턴 라이브 안 켬."
        )
        verdict = "DISCUSS_OK"
        s2 = "deferred_need_hyung_go"
    else:
        s1 = "HOLD_NO_WIRE"
        reason = (
            f"주정의 N={PRIMARY_N} K={PRIMARY_K} net_n={net_n} p={p} "
            f"(거의없음 기준 {ALMOST_NONE}). 라이브 배선 금지. 읽기만 유지."
        )
        verdict = "HOLD_NO_WIRE"
        s2 = "skipped"
    doc = {
        "id": "K-REVIEW-ASSOC-CROWD-NETCHECK",
        "ts": _now(),
        "verdict": verdict,
        "s0": s0,
        "s1": s1,
        "reason": reason,
        "s2": s2,
        "apply": False,
        "live_pass": False,
        "repack": "untouched",
        "all_combos": "untouched",
        "automation": False,
        "predict": False,
        "similarity_idea": "excluded",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "p", p, "net", net_n, flush=True)


if __name__ == "__main__":
    main()
