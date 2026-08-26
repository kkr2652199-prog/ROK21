# -*- coding: utf-8 -*-
"""K-REVIEW-RARE-CONSEC-NETCHECK — 5-세분 vs 5-바탕 순수증분.

S0 READ-ONLY. PASS_WIRE 켜지 않음. 1237예측 없음. 몰아주기 없음.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260827_KREVIEW_RARE_CONSEC_NETCHECK.json"
OUT_MD = ROOT / "reports" / "20260827_KREVIEW_RARE_CONSEC_NETCHECK.md"
DB = ROOT / "data" / "lotto_testlotto.db"
SEED = 42
GATE_LO, GATE_HI = 1137, 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _load_sets() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        pass_nos = {
            int(r[0])
            for r in conn.execute("SELECT combo_no FROM testlotto_rare_pass_combos")
        }
        consec_rows = conn.execute(
            "SELECT combo_no, nums_json, sig FROM testlotto_rare_consec_combos"
        ).fetchall()
        consec_nos = {int(r[0]) for r in consec_rows}
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
        draws = conn.execute(
            "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN 1 AND 1238 ORDER BY draw_no"
        ).fetchall()
        n_cls = int(conn.execute("SELECT COUNT(*) FROM testlotto_rare_consec_classes").fetchone()[0])
        sigs = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                "SELECT sig, COUNT(*) FROM testlotto_rare_consec_combos GROUP BY sig"
            )
        }
    finally:
        conn.close()
    overlap = pass_nos & consec_nos
    net = consec_nos - pass_nos
    only_pass = pass_nos - consec_nos
    net_rows = [r for r in consec_rows if int(r[0]) in net]
    hit_net: list[dict[str, Any]] = []
    draw_keys = {
        int(r[0]): tuple(sorted(int(r[i]) for i in range(1, 7))) for r in draws
    }
    net_tuples = {int(r[0]): tuple(json.loads(r[1])) for r in net_rows}
    for dno, six in draw_keys.items():
        for cno, t in net_tuples.items():
            if six == t:
                hit_net.append({"draw_no": dno, "combo_no": cno, "nums": list(t)})
    return {
        "pass_n": len(pass_nos),
        "consec_n": len(consec_nos),
        "overlap_n": len(overlap),
        "net_n": len(net),
        "only_pass_n": len(only_pass),
        "equal_sets": consec_nos == pass_nos,
        "consec_subset_of_pass": consec_nos <= pass_nos,
        "net_hits_1_1238": hit_net,
        "net_hit_n": len(hit_net),
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "n_draws_1238": len(draws),
        "n_cls": n_cls,
        "consec_sig_counts": sigs,
    }


def _virtual_extra() -> dict[str, Any]:
    """현재 라이브(rare_pass ON, consec PASS OFF) 발권에서 가상 추가 패스 측정."""
    import app.testlotto.brains.review_brain.rare_consec as rc
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.review_brain.rare_consec import is_step1_consec
    from app.testlotto.brains.review_brain.rare_pass_store import should_pass
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
    n_ok = peek_fail = size_bad = bonus_in = 0
    n_sets = 0
    n_rare = 0
    n_consec = 0
    n_both = 0
    n_extra = 0
    errors: list[str] = []
    pass_wire = bool(rc.REVIEW_CONSEC_PASS_WIRE)
    try:
        for i, r in enumerate(rows):
            dno = int(r["draw_no"])
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
                peek_fail += 1
                continue
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
            for c in pool:
                nums = [int(x) for x in (c.get("nums") or [])]
                if len(nums) != 6:
                    bonus_in += 1
                    continue
                n_sets += 1
                rp = bool(should_pass(nums))
                cs = bool(is_step1_consec(nums))
                if rp:
                    n_rare += 1
                if cs:
                    n_consec += 1
                if rp and cs:
                    n_both += 1
                if cs and not rp:
                    n_extra += 1
            n_ok += 1
            if (i + 1) % 20 == 0 or dno == GATE_HI:
                print(f"  [virt] {i+1}/{len(rows)} d={dno} n_ok={n_ok} extra={n_extra}", flush=True)
    finally:
        pass
    extra_rate = round(n_extra / n_sets, 6) if n_sets else None
    return {
        "elapsed_s": round(time.perf_counter() - t0, 1),
        "n_ok": n_ok,
        "peek_fail": peek_fail,
        "size_bad": size_bad,
        "bonus_in": bonus_in,
        "n_errors": len(errors),
        "errors_head": errors[:6],
        "n_sets": n_sets,
        "n_rare_pass_in_output": n_rare,
        "n_consec_step1_in_output": n_consec,
        "n_both": n_both,
        "n_extra_consec_not_rare": n_extra,
        "extra_pass_rate": extra_rate,
        "live_consec_pass_wire": pass_wire,
        "meaningful_extra": bool(n_extra > 0),
    }


def _write_md(doc: dict[str, Any]) -> str:
    s0 = doc["s0"]
    v = doc["virtual"]
    return "\n".join(
        [
            "# K-REVIEW-RARE-CONSEC-NETCHECK (2026-08-27)",
            "",
            f"- **판정:** `{doc['verdict']}` · S0 READ-ONLY · PASS_WIRE 켜지 않음 · 몰아주기 미접촉",
            f"- 시각: {doc['ts']}",
            "- 형: 5-세분 STEP1이 5-바탕과 동일 집합인지 net 확인 후 배선 여부.",
            f"- 근거: `{OUT_JSON.name}`",
            "",
            "## S0 순수증분",
            "",
            f"- 5-바탕(rare_pass) `{s0['pass_n']}` · 5-세분 STEP1 `{s0['consec_n']}` · 클래스 `{s0['n_cls']}` · sig `{s0['consec_sig_counts']}`",
            f"- 겹침(이미 포함) `{s0['overlap_n']}` · net(세분-바탕) `{s0['net_n']}` · 바탕만 `{s0['only_pass_n']}`",
            f"- 세분 ⊆ 바탕 `{s0['consec_subset_of_pass']}`",
            f"- net 당첨 1–1238 `{s0['net_hit_n']}` (net=0이면 공집합)",
            f"- pred_1237 `{s0['pred_1237']}` · pred_1239 `{s0['pred_1239']}` · MAX `{s0['dmax']}`",
            "",
            "## S0 가상 추가 패스 1137–1236 n100",
            "",
            f"- peek `{v['peek_fail']}` n_ok `{v['n_ok']}` sets `{v['n_sets']}` bonus_in `{v['bonus_in']}`",
            f"- 출력에 rare_pass `{v['n_rare_pass_in_output']}` · consec STEP1 `{v['n_consec_step1_in_output']}` · 둘다 `{v['n_both']}`",
            f"- **추가 패스**(consec이고 rare_pass 아님) `{v['n_extra_consec_not_rare']}` · 비율 `{v['extra_pass_rate']}`",
            f"- 라이브 PASS_WIRE `{v['live_consec_pass_wire']}`",
            f"- elapsed `{v['elapsed_s']}`s",
            "",
            "## S1 판정",
            "",
            f"- `{doc['s1']}`",
            f"- 사유: {doc['reason']}",
            "- S2 배선 **안 함**. `REVIEW_CONSEC_PASS_WIRE` 유지 False. `REVIEW_CONSEC_KB_READ` 유지 True(모니터).",
            "",
            "## 롤백",
            "",
            "- PASS: 이미 False · READ: `REVIEW_CONSEC_KB_READ=False`",
            "",
            "## 파일",
            "",
            f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
        ]
    )


def main() -> None:
    from app.testlotto.brains.review_brain.rare_consec import (
        REVIEW_CONSEC_KB_READ,
        REVIEW_CONSEC_PASS_WIRE,
    )

    print("S0 sets", flush=True)
    s0 = _load_sets()
    print(
        {"pass": s0["pass_n"], "consec": s0["consec_n"], "net": s0["net_n"], "overlap": s0["overlap_n"]},
        flush=True,
    )
    print("S0 virtual extra", flush=True)
    virt = _virtual_extra()
    net = int(s0["net_n"])
    extra = int(virt["n_extra_consec_not_rare"])
    if net > 0 and s0["net_hit_n"] == 0 and extra > 0:
        s1 = "WIRE_CANDIDATE"
        reason = "net>0 이고 당첨0 이고 추가패스>0. S2는 형 GO 후에만."
        verdict = "DISCUSS_OK"
    else:
        s1 = "HOLD_NO_WIRE"
        bits = []
        if net == 0:
            bits.append("net=0 (STEP1 1600이 rare_pass에 전부 포함)")
        if extra == 0:
            bits.append("추가 패스 0")
        if s0["net_hit_n"] > 0:
            bits.append(f"net 당첨 {s0['net_hit_n']}회")
        reason = " · ".join(bits) + ". 라이브 배선 금지. 읽기(세분 라벨)만 유지."
        verdict = "HOLD_NO_WIRE"
    if REVIEW_CONSEC_PASS_WIRE:
        verdict = "HOLD_HARD"
        reason = "측정 중 PASS_WIRE가 True였음. 라이브 확정 아님."
    if s0["pred_1237"] != 0:
        verdict = "HOLD_HARD"
    doc = {
        "id": "K-REVIEW-RARE-CONSEC-NETCHECK",
        "ts": _now(),
        "verdict": verdict,
        "s0": s0,
        "virtual": virt,
        "s1": s1,
        "reason": reason,
        "s2": "skipped",
        "flags": {
            "REVIEW_RARE_SLICE_WIRE": True,
            "REVIEW_CONSEC_KB_READ": bool(REVIEW_CONSEC_KB_READ),
            "REVIEW_CONSEC_PASS_WIRE": bool(REVIEW_CONSEC_PASS_WIRE),
        },
        "apply": False,
        "live_pass": False,
        "repack": "untouched",
        "all_combos": "untouched",
        "automation": False,
        "predict": False,
    }
    # drop hit list if huge
    if len(s0["net_hits_1_1238"]) > 20:
        s0["net_hits_1_1238"] = s0["net_hits_1_1238"][:20]
        s0["net_hits_truncated"] = True
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    print(verdict, "net", net, "extra", extra, flush=True)


if __name__ == "__main__":
    main()
