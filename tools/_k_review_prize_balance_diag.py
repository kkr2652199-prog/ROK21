# -*- coding: utf-8 -*-
"""K-REVIEW-PRIZE-BALANCE-DIAG — 4번 저울 vs prize 축 밸런스. READ-ONLY · APPLY 금지."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.testlotto.brains.review_brain.draw_shape_kb as kb
from app.testlotto.brains.review_brain.kb7_future import collect_before
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import consecutive_pairs
from app.testlotto.learn_state_cutoff import set_learn_as_of

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260828_KREVIEW_PRIZE_BALANCE_DIAG.json"
OUT_MD = ROOT / "reports" / "20260828_KREVIEW_PRIZE_BALANCE_DIAG.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1137, 1236
SEED = 42
HI32 = frozenset(range(32, 46))
SRC = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "draw_shape_kb.py"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _axis(table: dict[int, float], sets: list[list[int]]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = [mean(table[n] for n in nums) - uni for nums in sets if len(nums) == 6]
    return round(mean(vals), 6) if vals else None


def _run3_count(nums: list[int]) -> int:
    s = sorted(nums)
    if len(s) < 3:
        return 0
    n = 0
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        if j - i + 1 >= 3:
            n += 1
        i = j + 1
    return n


def _shape(sets: list[list[int]]) -> dict[str, float | None]:
    if not sets:
        return {"run2": None, "run3": None, "hi32": None, "n_sets": 0}
    r2 = [consecutive_pairs(s) for s in sets]
    r3 = [_run3_count(s) for s in sets]
    hi = [sum(1 for n in s if n in HI32) for s in sets]
    return {
        "run2": round(mean(r2), 6),
        "run3": round(mean(r3), 6),
        "hi32": round(mean(hi), 6),
        "n_sets": len(sets),
    }


def _pool_sets(dno: int, draws: list[dict], wire: bool) -> list[list[int]]:
    import app.testlotto.signal_pool as sp

    prev = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = bool(wire)
    try:
        set_learn_as_of(dno)
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
    finally:
        kb.REVIEW_SHAPE_KB_WEIGHT_WIRE = prev
    out = []
    for s in pool:
        nums = _nums(s)
        if len(nums) == 6:
            out.append(nums)
    return out


def main() -> int:
    live_wire = bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE)
    src = SRC.read_text(encoding="utf-8")
    knobs = {
        "W_CROWD_review": cs.W_CROWD_BY_BRAIN.get("review"),
        "W_STRUCT_review": cs.W_STRUCT_BY_BRAIN.get("review"),
        "BLEND_review": cs.BLEND_STRENGTH_BY_BRAIN.get("review"),
        "PRIZE_WIRE": cs.prize_on(),
        "REVIEW_SHAPE_KB_WEIGHT_WIRE_live": live_wire,
        "src_wire_true": "REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = True" in src,
        "REVIEW_PRIZE_RANK_MIX": __import__(
            "app.testlotto.brains.review_brain.engine", fromlist=["REVIEW_PRIZE_RANK_MIX"]
        ).REVIEW_PRIZE_RANK_MIX,
    }

    peek = 0
    n_ok = 0
    acc: dict[str, dict[str, list[float]]] = {
        "off": {"prefer": [], "prize": [], "struct": [], "run2": [], "run3": [], "hi32": []},
        "on": {"prefer": [], "prize": [], "struct": [], "run2": [], "run3": [], "hi32": []},
    }
    s2_d_prize: list[float] = []
    s2_keep_n: list[int] = []
    s2_skip = 0

    for dno in range(LO, HI + 1):
        draws = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in draws), default=0)
        if mx >= dno:
            peek += 1
            continue
        prize = cs.prize_table(draws, brain="review")
        prefer = cs.prefer_table(draws, brain="markov")
        struct = cs.structural_unpopular_prior()
        off_sets = _pool_sets(dno, draws, False)
        on_sets = _pool_sets(dno, draws, True)
        if len(off_sets) < 10 or len(on_sets) < 10:
            continue
        for tag, sets in (("off", off_sets), ("on", on_sets)):
            pa = _axis(prize, sets)
            pr = _axis(prefer, sets)
            st = _axis(struct, sets)
            sh = _shape(sets)
            if pa is not None:
                acc[tag]["prize"].append(pa)
            if pr is not None:
                acc[tag]["prefer"].append(pr)
            if st is not None:
                acc[tag]["struct"].append(st)
            if sh["run2"] is not None:
                acc[tag]["run2"].append(float(sh["run2"]))
            if sh["run3"] is not None:
                acc[tag]["run3"].append(float(sh["run3"]))
            if sh["hi32"] is not None:
                acc[tag]["hi32"].append(float(sh["hi32"]))

        hist = (collect_before(draws) or {}).get("shape")
        state = random.getstate()
        random.seed(SEED * 100000 + dno)
        kept = [s for s in off_sets if kb.keep_set_by_hist(s, hist)]
        random.setstate(state)
        if not kept:
            s2_skip += 1
        else:
            a_all = _axis(prize, off_sets)
            a_kept = _axis(prize, kept)
            if a_all is not None and a_kept is not None:
                s2_d_prize.append(a_kept - a_all)
                s2_keep_n.append(len(kept))
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"[BAL] {dno} n={n_ok} peek={peek}", flush=True)

    def _summ(tag: str) -> dict[str, Any]:
        out: dict[str, Any] = {"n": n_ok}
        for k, vs in acc[tag].items():
            out[k] = round(mean(vs), 6) if vs else None
        return out

    off = _summ("off")
    on = _summ("on")

    def _d(key: str) -> float | None:
        a, b = off.get(key), on.get(key)
        if a is None or b is None:
            return None
        return round(float(b) - float(a), 6)

    delta = {
        "prefer": _d("prefer"),
        "prize": _d("prize"),
        "struct": _d("struct"),
        "run2": _d("run2"),
        "run3": _d("run3"),
        "hi32": _d("hi32"),
    }
    s2 = {
        "n": len(s2_d_prize),
        "skip_empty": s2_skip,
        "keep_mean": round(mean(s2_keep_n), 4) if s2_keep_n else None,
        "d_prize_mean": round(mean(s2_d_prize), 6) if s2_d_prize else None,
        "d_prize_abs_mean": round(mean(abs(x) for x in s2_d_prize), 6) if s2_d_prize else None,
        "near0_005": bool(s2_d_prize and abs(mean(s2_d_prize)) < 0.005),
    }

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0])
    pred_1239 = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    hard = {
        "peek0": peek == 0,
        "n100": n_ok == 100,
        "wire_restored": bool(kb.REVIEW_SHAPE_KB_WEIGHT_WIRE) == live_wire,
        "pred_1237_0": pred_1237 == 0,
        "pred_1239_0": pred_1239 == 0,
        "src_unchanged_true": "REVIEW_SHAPE_KB_WEIGHT_WIRE: bool = True" in SRC.read_text(encoding="utf-8"),
    }
    verdict = "SPEC_OK" if all(hard.values()) else "DISCUSS_OK"

    payload = {
        "id": "K-REVIEW-PRIZE-BALANCE-DIAG",
        "as_of": _now(),
        "verdict": verdict,
        "apply": False,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "seed": SEED,
        "n": n_ok,
        "peek": peek,
        "knobs": knobs,
        "off": off,
        "on": on,
        "delta_on_minus_off": delta,
        "s2_isolate_filter_on_frozen_off_sets": s2,
        "hard": hard,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "note": "ON-OFF 발권은 저울 RNG가 choices 시드를 갈라 Δ에 섞일 수 있음. S2는 OFF 10장을 고정하고 저울만 후필터.",
    }

    prize_cut = bool(delta["prize"] is not None and delta["prize"] < 0)
    run_up = bool(delta["run2"] is not None and delta["run2"] > 0)
    hi_up = bool(delta["hi32"] is not None and delta["hi32"] > 0)

    lines = [
        "# K-REVIEW-PRIZE-BALANCE-DIAG",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · READ-ONLY · APPLY **없음** · 1237아님 · hits 클레임 금지",
        "목적=금액뇌 1순위 prize_table vs 패치(1·2·3·4) 밸런스. 특히 4번 저울이 prize를 깎는지·연속쌍을 늘리는지.",
        "",
        "## S0) prize_table 구성",
        "",
        f"W_CROWD review=**{knobs['W_CROWD_review']}** · W_STRUCT review=**{knobs['W_STRUCT_review']}** · "
        f"BLEND review=**{knobs['BLEND_review']}** · PRIZE_WIRE={knobs['PRIZE_WIRE']}.",
        "표 = 0.80×crowd_unpopular(1/√first_winners) + 0.20×structural_unpopular(고번호·끝 0/8/9).",
        f"라이브 4번 WIRE={live_wire} (파일 True, 측정 중 메모리만 토글 후 복원).",
        f"게이트 {LO}–{HI} n={n_ok} peek={peek} seed={SEED}.",
        "",
        "| 축 | OFF | ON | Δ(ON−OFF) |",
        "|----|-----|-----|-----------|",
        f"| prefer | {off['prefer']} | {on['prefer']} | {delta['prefer']} |",
        f"| prize | {off['prize']} | {on['prize']} | {delta['prize']} |",
        f"| struct | {off['struct']} | {on['struct']} | {delta['struct']} |",
        "",
        f"4번이 prize를 깎나: **{'예(Δprize<0)' if prize_cut else '아니오(Δprize≥0 또는 없음)'}**.",
        "",
        "## S1) 연속쌍·고번호 (장당 평균)",
        "",
        "| 지표 | OFF | ON | Δ(ON−OFF) |",
        "|------|-----|-----|-----------|",
        f"| run2 연속쌍 | {off['run2']} | {on['run2']} | {delta['run2']} |",
        f"| run3 줄 수 | {off['run3']} | {on['run3']} | {delta['run3']} |",
        f"| hi32(32+) | {off['hi32']} | {on['hi32']} | {delta['hi32']} |",
        "",
        f"4번 ON이 연속쌍을 늘리나: **{'예' if run_up else '아니오'}**. 고번호를 늘리나: **{'예' if hi_up else '아니오'}**.",
        "",
        "## S2) 격리 시뮬 (미적용)",
        "",
        "OFF로 만든 10장을 고정한 뒤 `keep_set_by_hist`만 후필터. 발권 RNG 재분기 없음.",
        f"n={s2['n']} · 전량탈락 skip={s2['skip_empty']} · 생존장 평균={s2['keep_mean']}.",
        f"Δprize(kept−all) 평균={s2['d_prize_mean']} · |Δ|평균={s2['d_prize_abs_mean']} · |평균|<0.005={s2['near0_005']}.",
        "0 수렴이면 저울은 같은 장 묶음 안에서 prize를 거의 안 고른다. 발권 ON−OFF Δ는 시드 갈라짐이 섞일 수 있음.",
        "",
        "## 판정",
        "",
        f"**{verdict}**. APPLY 없음. 몰아주기 미접촉. 동결토큰 미수정. pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax}.",
        "",
        "## 금지 확인",
        "",
        "코드/플래그/DB write 없음. kweon 미접촉. 1237/1239 예측 없음.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {"verdict": verdict, "delta": delta, "s2": s2, "hard": hard, "n": n_ok, "peek": peek},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
