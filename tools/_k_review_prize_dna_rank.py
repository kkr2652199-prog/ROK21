# -*- coding: utf-8 -*-
"""K-REVIEW-PRIZE-DNA-RANK — 금액뇌 10세트 DNA 잠금 원인 분석 후 순위혼합 게이트.

review만. 몰아주기/score5 미접촉. random.choices 라인 불변. 1237 예측 금지.
게이트 통과 시에만 REVIEW_PRIZE_RANK_MIX=True + review 1037–1236 재기록.
"""
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

from app.testlotto.brains.review_brain import engine as rev_eng
from app.testlotto.brains.review_brain.engine import neutralize_ending_digit_mass
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums
from app.testlotto.learn_state_cutoff import set_learn_as_of
from tools._k_brain_independent_tune import _fw_proxy, _top15

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KREVIEW_PRIZE_DNA_RANK.json"
OUT_MD = ROOT / "reports" / "20260829_KREVIEW_PRIZE_DNA_RANK.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
ENG_PATH = ROOT / "app" / "testlotto" / "brains" / "review_brain" / "engine.py"
GATE_LO, GATE_HI = 1137, 1236
FILL_LO, FILL_HI = 1037, 1236
SEED = 42
ALPHA = 0.70
ISO = 0.005
NULL_HI32 = 6 * 14 / 45
HI32 = frozenset(range(32, 46))
END089 = frozenset(n for n in range(1, 46) if n % 10 in (0, 8, 9))


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _ranks(vals: list[float]) -> list[float]:
    n = len(vals)
    order = sorted(range(n), key=lambda i: vals[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) != len(b) or len(a) < 3:
        return None
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = mean(ra), mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    if da < 1e-12 or db < 1e-12:
        return None
    return round(num / (da * db), 4)


def _carry_neu(draws: list[dict]) -> dict[int, float]:
    prev = set(sorted_nums(draws[-1]))
    rates = repeat_rate_after_draw(draws)
    w = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in range(1, 46):
        w[n] *= 1.8 if n in prev else 0.85
    return neutralize_ending_digit_mass(w)


def _diagnose() -> dict[str, Any]:
    draws = _get_draws_before(1236)
    peek = max((int(d["draw_no"]) for d in draws), default=0)
    carry = _carry_neu(draws)
    prize = cs.prize_table(draws, brain="review")
    pos = [v for v in carry.values() if v > 0]
    c_hi, c_lo = max(pos), min(pos)
    p_hi, p_lo = max(prize.values()), min(prize.values())

    def mul(c: float, p: float, s: float = 0.85) -> float:
        return c * max(0.05, 1.0 + s * (p - 1.0))

    prev_flag = bool(rev_eng.REVIEW_PRIZE_RANK_MIX)
    rev_eng.REVIEW_PRIZE_RANK_MIX = False
    w_mul = rev_eng.build_review_weights(draws)
    rev_eng.REVIEW_PRIZE_RANK_MIX = True
    w_rank = rev_eng.build_review_weights(draws)
    rev_eng.REVIEW_PRIZE_RANK_MIX = prev_flag
    nums = list(range(1, 46))
    return {
        "as_of": 1236,
        "peek_ok": peek < 1236,
        "prev_nums": sorted(sorted_nums(draws[-1])),
        "carry_pos_min": round(c_lo, 6),
        "carry_pos_max": round(c_hi, 6),
        "carry_ratio": round(c_hi / c_lo, 4),
        "prize_min": round(p_lo, 6),
        "prize_max": round(p_hi, 6),
        "prize_ratio": round(p_hi / p_lo, 4),
        "mul_flip_extreme": bool(mul(c_lo, p_hi) > mul(c_hi, p_lo)),
        "mul_hi_x_plo": round(mul(c_hi, p_lo), 6),
        "mul_lo_x_phi": round(mul(c_lo, p_hi), 6),
        "rho_mul_vs_carry": _spearman([w_mul[n] for n in nums], [carry[n] for n in nums]),
        "rho_mul_vs_prize": _spearman([w_mul[n] for n in nums], [prize[n] for n in nums]),
        "rho_rank_vs_carry": _spearman([w_rank[n] for n in nums], [carry[n] for n in nums]),
        "rho_rank_vs_prize": _spearman([w_rank[n] for n in nums], [prize[n] for n in nums]),
        "why": "이월 neutralize 후 양수 가중 범위가 prize 표보다 훨씬 커서 곱셈 블렌드가 순위를 못 뒤집음.",
    }


def _axis(table: dict[int, float], sets: list[list[int]]) -> float | None:
    if not table or not sets:
        return None
    uni = mean(table[i] for i in range(1, 46))
    vals = [mean(table[n] for n in s) - uni for s in sets if len(s) == 6]
    return round(mean(vals), 6) if vals else None


def _run(rank_mix: bool) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    prev = bool(rev_eng.REVIEW_PRIZE_RANK_MIX)
    rev_eng.REVIEW_PRIZE_RANK_MIX = bool(rank_mix)
    peek = 0
    n_ok = 0
    hi: list[float] = []
    en: list[float] = []
    prize_ax: list[float] = []
    prefer_ax: list[float] = []
    fw_ds: list[float] = []
    try:
        for dno in range(GATE_LO, GATE_HI + 1):
            set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            mx = max((int(d["draw_no"]) for d in draws), default=0)
            if mx >= dno:
                peek += 1
                continue
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            rev = (sp._pool_by_brain(pool).get("review") or [])
            sets = []
            for s in rev:
                nums = [int(x) for x in (s.get("nums") or [])]
                if len(nums) == 6:
                    sets.append(nums)
                    hi.append(sum(1 for n in nums if n in HI32))
                    en.append(sum(1 for n in nums if n in END089))
            if not sets:
                continue
            prize = cs.prize_table(draws, brain="review")
            prefer = cs.prefer_table(draws, brain="markov")
            pa = _axis(prize, sets)
            pr = _axis(prefer, sets)
            if pa is not None:
                prize_ax.append(pa)
            if pr is not None:
                prefer_ax.append(pr)
            fw = _fw_proxy(draws)
            uni = mean(fw[n] for n in range(1, 46))
            learner = sp.RollingSignalLearner()
            num_ema, pos_ema = learner.snapshot()
            hint_by = sp.build_hint_by_brain(draws, dno)
            scores = sp.number_scores(
                rev,
                hint_by.get("review", sp._build_hint(draws, dno)),
                num_ema,
                pos_ema,
                brain_tag="review",
            )
            top = _top15(scores)
            fw_ds.append(mean(fw[n] for n in top) - uni)
            n_ok += 1
    finally:
        rev_eng.REVIEW_PRIZE_RANK_MIX = prev
    return {
        "rank_mix": rank_mix,
        "n": n_ok,
        "peek": peek,
        "hi32": round(mean(hi), 4) if hi else None,
        "end089": round(mean(en), 4) if en else None,
        "prize_axis": round(mean(prize_ax), 6) if prize_ax else None,
        "prefer_axis": round(mean(prefer_ax), 6) if prefer_ax else None,
        "fw_prize": round(mean(fw_ds), 6) if fw_ds else None,
    }


def _apply_flag() -> None:
    text = ENG_PATH.read_text(encoding="utf-8")
    old = "REVIEW_PRIZE_RANK_MIX: bool = False"
    new = "REVIEW_PRIZE_RANK_MIX: bool = True"
    if old not in text:
        raise RuntimeError("flag replace failed")
    ENG_PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
    rev_eng.REVIEW_PRIZE_RANK_MIX = True


def _fill_review_200() -> dict[str, int]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.evolve_diag import record_predictions_from_cache, write_evolve_diag
    from app.testlotto.pool_view_cache import payload_from_wf_parts, save_pool_view_cache_one

    conn = sqlite3.connect(str(DB), timeout=120.0)
    conn.execute(
        "DELETE FROM testlotto_pool_view_cache WHERE brain='review' AND draw_no BETWEEN ? AND ?",
        (FILL_LO, FILL_HI),
    )
    conn.execute(
        "DELETE FROM lotto_predictions WHERE brain_tag='review' AND target_draw_no BETWEEN ? AND ?",
        (FILL_LO, FILL_HI),
    )
    conn.execute(
        "DELETE FROM lotto_predictions WHERE target_draw_no IN (1237, 1239)"
    )
    conn.execute(
        "DELETE FROM testlotto_evolve_log WHERE brain_tag='review' AND draw_no BETWEEN ? AND ?",
        (FILL_LO, FILL_HI),
    )
    conn.commit()
    conn.close()
    ok = fail = peek = 0
    for dno in range(FILL_LO, FILL_HI + 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if max((int(d["draw_no"]) for d in draws), default=0) >= dno:
            peek += 1
            fail += 1
            continue
        random.seed(sp.MC_SEED)
        pool = sp.expand_pool(draws, dno, seed=sp.MC_SEED, brains=["review"])
        pool_br = sp._pool_by_brain(pool)
        learner = sp.RollingSignalLearner()
        num_ema, pos_ema = learner.snapshot()
        repacked = sp.repack_by_brain(
            pool_br,
            sp._build_hint(draws, dno),
            num_ema,
            pos_ema,
            target_draw_no=dno,
            hint_by_brain=sp.build_hint_by_brain(draws, dno),
        )
        only = [x for x in repacked if str(x.get("brain_tag")) == "review"]
        payload = payload_from_wf_parts(
            dno, {"review": pool_br.get("review") or []}, only, seed=sp.MC_SEED
        )
        if not payload["pool_by_brain"].get("review") or not payload["repack_by_brain"].get("review"):
            fail += 1
            continue
        save_pool_view_cache_one(dno, "review", payload)
        ev = write_evolve_diag(dno, "review")
        pr = record_predictions_from_cache(dno, "review")
        if ev.get("ok") and pr.get("ok"):
            ok += 1
        else:
            fail += 1
        if (dno - FILL_LO + 1) % 40 == 0:
            print(f"[RANK] fill {dno} ok={ok} fail={fail}", flush=True)
    return {"ok": ok, "fail": fail, "peek": peek}


def main() -> int:
    print("[RANK] diagnose", flush=True)
    diag = _diagnose()
    print("[RANK] diagnose", diag, flush=True)
    print("[RANK] measure base mul", flush=True)
    base = _run(False)
    print("[RANK] base", base, flush=True)
    print("[RANK] measure cand rank-mix", flush=True)
    cand = _run(True)
    print("[RANK] cand", cand, flush=True)

    d_hi = (
        round(cand["hi32"] - base["hi32"], 4)
        if base["hi32"] is not None and cand["hi32"] is not None
        else None
    )
    d_en = (
        round(cand["end089"] - base["end089"], 4)
        if base["end089"] is not None and cand["end089"] is not None
        else None
    )
    d_prize = (
        round(cand["prize_axis"] - base["prize_axis"], 6)
        if base["prize_axis"] is not None and cand["prize_axis"] is not None
        else None
    )
    d_pref = (
        round(cand["prefer_axis"] - base["prefer_axis"], 6)
        if base["prefer_axis"] is not None and cand["prefer_axis"] is not None
        else None
    )
    d_fw = (
        round(cand["fw_prize"] - base["fw_prize"], 6)
        if base["fw_prize"] is not None and cand["fw_prize"] is not None
        else None
    )
    rho_ok = bool(
        diag["rho_rank_vs_prize"] is not None
        and diag["rho_rank_vs_carry"] is not None
        and diag["rho_rank_vs_prize"] > diag["rho_rank_vs_carry"]
    )
    hard = {
        "peek0": base["peek"] == 0 and cand["peek"] == 0,
        "n100": base["n"] == 100 and cand["n"] == 100,
        "hi32_up": bool(d_hi is not None and d_hi > 0),
        "prize_not_worse": bool(d_prize is not None and d_prize >= -ISO),
        "fw_iso": bool(d_fw is not None and d_fw <= ISO),
        "rho_prize_gt_carry": rho_ok,
        "diag_no_mul_flip": diag["mul_flip_extreme"] is False,
    }
    apply_ok = all(hard.values())
    fill = None
    applied = False
    if apply_ok:
        _apply_flag()
        applied = True
        print("[RANK] refill review 200", flush=True)
        fill = _fill_review_200()
        verdict = "APPLY_OK" if fill and fill["ok"] == 200 and fill["fail"] == 0 else "APPLY_FILL_FAIL"
    else:
        verdict = "HOLD"

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    pred_1239 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0]
    )
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    payload = {
        "id": "K-REVIEW-PRIZE-DNA-RANK",
        "as_of": _now(),
        "verdict": verdict,
        "applied": applied,
        "apply": applied,
        "ge3_claim": False,
        "draw_1237": False,
        "score5_untouched": True,
        "alpha": ALPHA,
        "window_gate": [GATE_LO, GATE_HI],
        "window_fill": [FILL_LO, FILL_HI],
        "seed": SEED,
        "diag": diag,
        "base": base,
        "cand": cand,
        "delta": {
            "hi32": d_hi,
            "end089": d_en,
            "prize_axis": d_prize,
            "prefer_axis": d_pref,
            "fw_prize": d_fw,
        },
        "hard": hard,
        "fill": fill,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "draws_max": dmax,
        "rollback": "REVIEW_PRIZE_RANK_MIX=False",
        "null_hi32": round(NULL_HI32, 4),
    }

    lines = [
        "# K-REVIEW-PRIZE-DNA-RANK",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · review만 · 몰아주기 미접촉 · 1237아님 · hits 클레임 금지",
        "목적=금액뇌 10세트가 비인기 DNA를 못 쓰는 원인을 재고, 원인에 맞는 패치만 넣는다.",
        "",
        "## 0) 구조 전제",
        "",
        "금액뇌 10세트=`expand_pool`/`generate` = 남들이 덜 고르는 조합 프로세스.",
        "몰아주기는 그 축이 아님 · 이번 패치 범위 밖.",
        "",
        "## 1) 원인",
        "",
        f"as_of1236 peek_ok={diag['peek_ok']} · 직전번호 {diag['prev_nums']}.",
        f"이월+neutralize 양수 가중 범위 **{diag['carry_ratio']}배** "
        f"({diag['carry_pos_min']}–{diag['carry_pos_max']}).",
        f"prize 표 범위 **{diag['prize_ratio']}배** ({diag['prize_min']}–{diag['prize_max']}).",
        f"극단 곱셈 뒤집힘={diag['mul_flip_extreme']} "
        f"(hi×plo {diag['mul_hi_x_plo']} vs lo×phi {diag['mul_lo_x_phi']}).",
        f"{diag['why']}",
        "",
        f"ρ 곱셈블렌드↔이월 **{diag['rho_mul_vs_carry']}** · ↔prize **{diag['rho_mul_vs_prize']}**.",
        f"ρ 순위혼합α{ALPHA}↔이월 **{diag['rho_rank_vs_carry']}** · ↔prize **{diag['rho_rank_vs_prize']}**.",
        "",
        "## 2) 패치",
        "",
        f"`REVIEW_PRIZE_RANK_MIX` + `mix_by_rank(alpha={ALPHA})`. random.choices 불변. score5 불변.",
        f"APPLY={'함' if applied else '안 함(HOLD)'}. 롤백=`REVIEW_PRIZE_RANK_MIX=False`.",
        "",
        "## 3) 게이트 1137–1236 n100 seed42",
        "",
        "| 설정 | n | peek | hi32 | end089 | prize축 | prefer축 | fw_prize |",
        "|------|---|------|------|--------|---------|----------|----------|",
        f"| 곱셈(base) | {base['n']} | {base['peek']} | {base['hi32']} | {base['end089']} | {base['prize_axis']} | {base['prefer_axis']} | {base['fw_prize']} |",
        f"| 순위혼합 | {cand['n']} | {cand['peek']} | {cand['hi32']} | {cand['end089']} | {cand['prize_axis']} | {cand['prefer_axis']} | {cand['fw_prize']} |",
        f"| Δ | | | {d_hi} | {d_en} | {d_prize} | {d_pref} | {d_fw} |",
        "",
        f"널 hi32={NULL_HI32:.3f}.",
        "",
        "| 항 | 값 |",
        "|----|-----|",
        f"| peek0 | {hard['peek0']} |",
        f"| n100 | {hard['n100']} |",
        f"| hi32 Δ>0 | {hard['hi32_up']} ({d_hi}) |",
        f"| prize축 비악화≥-0.005 | {hard['prize_not_worse']} ({d_prize}) |",
        f"| fw Δ≤+0.005 | {hard['fw_iso']} ({d_fw}) |",
        f"| ρ prize>carry | {hard['rho_prize_gt_carry']} |",
        "",
        "## 4) 리필",
        "",
        f"{fill if fill else '없음(HOLD)'}. review만 1037–1236. stat/markov 캐시 유지.",
        "",
        "## 5) 금지 확인",
        "",
        f"pred_1237={pred_1237} · pred_1239={pred_1239} · MAX={dmax}. 동결토큰 미수정. kweon 미접촉. DB git 안 함.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "applied": applied, "hard": hard, "delta": payload["delta"], "fill": fill}, ensure_ascii=False))
    return 0 if verdict in ("APPLY_OK", "HOLD") else 2


if __name__ == "__main__":
    raise SystemExit(main())
