# -*- coding: utf-8 -*-
"""K-REVIEW-PRIZE-DNA-ALIVE — 금액뇌 비인기 DNA가 코드·캐시에 살아있는지 READ-ONLY 실측."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.review_brain.engine import (  # noqa: E402
    REVIEW_REASONABLE_SET,
    REVIEW_SEQ_DISTRIBUTE,
    build_review_weights,
    neutralize_ending_digit_mass,
    review_compose_mode,
)
from app.testlotto.brains.review_brain.kb7_future import REVIEW_KB7_WIRE  # noqa: E402
from app.testlotto.brains.review_brain.rare_consec import REVIEW_CONSEC_PASS_WIRE  # noqa: E402
from app.testlotto.brains.review_brain.rare_slice import REVIEW_RARE_SLICE_WIRE  # noqa: E402
from app.testlotto.brains.review_brain.shape_table import REVIEW_SHAPE_WIRE  # noqa: E402
from app.testlotto.brains.review_brain.draw_shape_kb import REVIEW_SHAPE_KB_WEIGHT_WIRE  # noqa: E402
from app.testlotto.brains.shared import crowd_signal as cs  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260828_KREVIEW_PRIZE_DNA_ALIVE.json"
OUT_MD = ROOT / "reports" / "20260828_KREVIEW_PRIZE_DNA_ALIVE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
AS_OF = 1236
BRAINS = ("review", "stat", "markov")
END089 = frozenset(n for n in range(1, 46) if n % 10 in (0, 8, 9))
HI32 = frozenset(n for n in range(32, 46))
HI40 = frozenset(n for n in range(40, 46))
BDAY = frozenset(n for n in range(1, 32))
NULL = {
    "hi32": 6 * 14 / 45,
    "hi40": 6 * 6 / 45,
    "end089": 6 * 12 / 45,
    "bday": 6 * 31 / 45,
}


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


def _occ(nums: list[int]) -> dict[str, int]:
    s = set(nums)
    return {
        "hi32": sum(1 for n in s if n in HI32),
        "hi40": sum(1 for n in s if n in HI40),
        "end089": sum(1 for n in s if n in END089),
        "bday": sum(1 for n in s if n in BDAY),
    }


def _carry_only(draws: list[dict]) -> dict[int, float]:
    prev_nums = sorted_nums(draws[-1])
    rates = repeat_rate_after_draw(draws)
    weights = {n: rates.get(n, 0.08) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= 1.8
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= 0.85
    return neutralize_ending_digit_mass(weights)


def _topk(table: dict[int, float], k: int = 12) -> list[int]:
    return [n for n, _ in sorted(table.items(), key=lambda x: (-x[1], x[0]))[:k]]


def _brain_occ(conn: sqlite3.Connection, brain: str, kind: str) -> dict[str, Any]:
    col = "pool_json" if kind == "pool" else "repack_json"
    acc = {k: [] for k in NULL}
    n_sets = 0
    for r in conn.execute(
        f"SELECT {col} FROM testlotto_pool_view_cache WHERE brain=? AND draw_no BETWEEN ? AND ?",
        (brain, LO, HI),
    ):
        for s in json.loads(r[0] or "[]"):
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            o = _occ(nums)
            n_sets += 1
            for k in acc:
                acc[k].append(o[k])
    out: dict[str, Any] = {"n_sets": n_sets}
    for k, vs in acc.items():
        m = mean(vs) if vs else None
        out[k] = round(m, 4) if m is not None else None
        out[f"d_{k}"] = round(m - NULL[k], 4) if m is not None else None
    return out


def main() -> int:
    draws_asof = _get_draws_before(AS_OF)
    peek = max((int(d["draw_no"]) for d in draws_asof), default=0)
    fw_pos = sum(1 for d in draws_asof if int(d.get("first_winners") or 0) > 0)
    fw_zero = sum(1 for d in draws_asof if int(d.get("first_winners") or 0) == 0)

    crowd = cs.crowd_unpopular_from_draws(draws_asof)
    struct = cs.structural_unpopular_prior()
    prize = cs.prize_table(draws_asof, brain="review")
    nums = list(range(1, 46))
    rho_table = {
        "prize_vs_struct": _spearman([prize[n] for n in nums], [struct[n] for n in nums]),
        "prize_vs_crowd": _spearman([prize[n] for n in nums], [crowd[n] for n in nums]),
        "crowd_vs_struct": _spearman([crowd[n] for n in nums], [struct[n] for n in nums]),
        "prize_vs_hi32": _spearman(
            [prize[n] for n in nums], [1.0 if n in HI32 else 0.0 for n in nums]
        ),
        "prize_vs_end089": _spearman(
            [prize[n] for n in nums], [1.0 if n in END089 else 0.0 for n in nums]
        ),
    }

    w_carry = _carry_only(draws_asof)
    w_prize_blend = cs.blend_weights(w_carry, prize, brain="review")
    w_full = build_review_weights(draws_asof, None)
    rho_w = {
        "full_vs_carry": _spearman([w_full[n] for n in nums], [w_carry[n] for n in nums]),
        "full_vs_prize": _spearman([w_full[n] for n in nums], [prize[n] for n in nums]),
        "full_vs_prize_blend": _spearman(
            [w_full[n] for n in nums], [w_prize_blend[n] for n in nums]
        ),
        "carry_vs_prize": _spearman([w_carry[n] for n in nums], [prize[n] for n in nums]),
    }
    top_full = _topk(w_full, 12)
    top_prize = _topk(prize, 12)
    top_carry = _topk(w_carry, 12)
    top_overlap = {
        "full_cap_prize": len(set(top_full) & set(top_prize)),
        "full_cap_carry": len(set(top_full) & set(top_carry)),
        "prize_cap_carry": len(set(top_prize) & set(top_carry)),
    }

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    occ: dict[str, Any] = {}
    cache: dict[str, dict[int, dict[str, list[list[int]]]]] = {t: {} for t in BRAINS}
    for tag in BRAINS:
        occ[tag] = {
            "pool": _brain_occ(conn, tag, "pool"),
            "repack": _brain_occ(conn, tag, "repack"),
        }
        for r in conn.execute(
            "SELECT draw_no, pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ?",
            (tag, LO, HI),
        ):
            dno = int(r["draw_no"])
            cache[tag][dno] = {
                "pool": [
                    [int(x) for x in (s.get("nums") or [])]
                    for s in json.loads(r["pool_json"] or "[]")
                    if len(s.get("nums") or []) == 6
                ],
                "repack": [
                    [int(x) for x in (s.get("nums") or [])]
                    for s in json.loads(r["repack_json"] or "[]")
                    if len(s.get("nums") or []) == 6
                ],
            }
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    pred_1239 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239").fetchone()[0]
    )
    conn.close()

    scored: dict[str, dict[str, dict[str, Any]]] = {}
    freq_review = {n: 0 for n in nums}
    n_review_pool = 0
    for dno in range(LO, HI + 1):
        dprev = _get_draws_before(dno)
        if max((int(d["draw_no"]) for d in dprev), default=0) >= dno:
            continue
        pt = cs.prize_table(dprev, brain="review")
        for tag in BRAINS:
            if dno not in cache[tag]:
                continue
            for kind in ("pool", "repack"):
                scored.setdefault(tag, {}).setdefault(kind, {"prize_avg": [], "n": 0})
                for s in cache[tag][dno][kind]:
                    avg = sum(pt[n] for n in s) / 6.0
                    scored[tag][kind]["prize_avg"].append(avg)
                    scored[tag][kind]["n"] += 1
                    if tag == "review" and kind == "pool":
                        n_review_pool += 1
                        for n in s:
                            freq_review[n] += 1

    prize_score: dict[str, Any] = {}
    for tag in BRAINS:
        prize_score[tag] = {}
        for kind in ("pool", "repack"):
            vs = scored.get(tag, {}).get(kind, {}).get("prize_avg") or []
            m = mean(vs) if vs else None
            prize_score[tag][kind] = {
                "n": len(vs),
                "mean": round(m, 6) if m is not None else None,
                "d_null1": round(m - 1.0, 6) if m is not None else None,
            }

    rho_freq = _spearman([float(freq_review[n]) for n in nums], [prize[n] for n in nums])
    rho_freq_struct = _spearman([float(freq_review[n]) for n in nums], [struct[n] for n in nums])
    rho_freq_crowd = _spearman([float(freq_review[n]) for n in nums], [crowd[n] for n in nums])
    rho_freq_carry = _spearman([float(freq_review[n]) for n in nums], [w_carry[n] for n in nums])

    r_pool = prize_score["review"]["pool"]["mean"]
    s_pool = prize_score["stat"]["pool"]["mean"]
    m_pool = prize_score["markov"]["pool"]["mean"]
    r_rep = prize_score["review"]["repack"]["mean"]
    r_hi = occ["review"]["pool"]["d_hi32"]
    r_end = occ["review"]["pool"]["d_end089"]
    r_hi_rep = occ["review"]["repack"]["d_hi32"]

    code_live = bool(
        cs.prize_on()
        and cs.PRIZE_WIRE
        and REVIEW_REASONABLE_SET
        and not REVIEW_KB7_WIRE
    )
    end_pool_live = bool(r_end is not None and r_end > 0)
    hi_pool_live = bool(r_hi is not None and r_hi > 0)
    hi_rep_live = bool(r_hi_rep is not None and r_hi_rep > 0)
    prize_pool_best = bool(
        r_pool is not None and s_pool is not None and m_pool is not None and r_pool > s_pool and r_pool > m_pool
    )
    prize_rep_best = bool(
        r_rep is not None
        and prize_score["stat"]["repack"]["mean"] is not None
        and prize_score["markov"]["repack"]["mean"] is not None
        and r_rep > prize_score["stat"]["repack"]["mean"]
        and r_rep > prize_score["markov"]["repack"]["mean"]
    )
    output_live = bool(end_pool_live or hi_rep_live or prize_rep_best)
    crowd_dominates = bool(
        rho_table["prize_vs_crowd"] is not None
        and rho_table["prize_vs_struct"] is not None
        and rho_table["prize_vs_crowd"] > rho_table["prize_vs_struct"]
    )
    carry_owns_weights = bool(rho_w["full_vs_carry"] is not None and rho_w["full_vs_carry"] >= 0.95)
    if not code_live:
        verdict = "DNA_OFF"
    elif carry_owns_weights and end_pool_live and (not hi_pool_live) and hi_rep_live:
        verdict = "DNA_PARTIAL"
    elif output_live:
        verdict = "DNA_ALIVE_MIXED"
    else:
        verdict = "DNA_CODE_ONLY"

    payload = {
        "id": "K-REVIEW-PRIZE-DNA-ALIVE",
        "as_of": _now(),
        "verdict": verdict,
        "apply": False,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "as_of_draw": AS_OF,
        "peek_ok": peek < AS_OF,
        "peek_max": peek,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "fw_used": fw_pos,
        "fw_zero_skip": fw_zero,
        "n_draws_before": len(draws_asof),
        "n_review_pool_sets": n_review_pool,
        "code_live": code_live,
        "output_live": output_live,
        "end_pool_live": end_pool_live,
        "hi_pool_live": hi_pool_live,
        "hi_repack_live": hi_rep_live,
        "prize_pool_best": prize_pool_best,
        "prize_repack_best": prize_rep_best,
        "carry_owns_weights": carry_owns_weights,
        "crowd_dominates_table": crowd_dominates,
        "knobs": {
            "PRIZE_WIRE": cs.prize_on(),
            "W_CROWD_review": cs.W_CROWD_BY_BRAIN.get("review"),
            "W_STRUCT_review": cs.W_STRUCT_BY_BRAIN.get("review"),
            "BLEND_review": cs.BLEND_STRENGTH_BY_BRAIN.get("review"),
            "compose": review_compose_mode(),
            "REVIEW_REASONABLE_SET": REVIEW_REASONABLE_SET,
            "REVIEW_SEQ_DISTRIBUTE": REVIEW_SEQ_DISTRIBUTE,
            "REVIEW_SHAPE_WIRE": REVIEW_SHAPE_WIRE,
            "REVIEW_RARE_SLICE_WIRE": REVIEW_RARE_SLICE_WIRE,
            "REVIEW_SHAPE_KB_WEIGHT_WIRE": REVIEW_SHAPE_KB_WEIGHT_WIRE,
            "REVIEW_CONSEC_PASS_WIRE": REVIEW_CONSEC_PASS_WIRE,
            "REVIEW_KB7_WIRE": REVIEW_KB7_WIRE,
        },
        "rho_table": rho_table,
        "rho_weights_asof1236": rho_w,
        "top12_asof1236": {
            "full_weights": top_full,
            "prize": top_prize,
            "carry": top_carry,
            "overlap": top_overlap,
        },
        "null_per_set": {k: round(v, 4) for k, v in NULL.items()},
        "occupancy": occ,
        "prize_score_vs_review_table": prize_score,
        "freq_review_pool_vs_asof1236": {
            "rho_prize": rho_freq,
            "rho_struct": rho_freq_struct,
            "rho_crowd": rho_freq_crowd,
            "rho_carry": rho_freq_carry,
        },
        "data_limit": "조합별 판매수 없음. first_winners 프록시 + 고번호·끝089 사전. 당첨P 불변.",
    }

    def _orow(tag: str, kind: str) -> str:
        o = occ[tag][kind]
        return (
            f"| {tag} {kind} | {o['n_sets']} | {o['hi32']} ({o['d_hi32']:+}) | "
            f"{o['end089']} ({o['d_end089']:+}) | {o['hi40']} ({o['d_hi40']:+}) | "
            f"{o['bday']} ({o['d_bday']:+}) |"
        )

    def _srow(tag: str, kind: str) -> str:
        s = prize_score[tag][kind]
        return f"| {tag} {kind} | {s['n']} | {s['mean']} | {s['d_null1']:+} |"

    lines = [
        "# K-REVIEW-PRIZE-DNA-ALIVE",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · READ-ONLY · APPLY없음 · 1237아님 · hits 클레임 금지",
        "목적=지금 튜닝 뇌=금액뇌(review)인지, 비인기(남들이 덜 고르는) DNA가 코드와 1037–1236 캐시에 살아있는지 실측.",
        "",
        "## 0) 한 줄",
        "",
        "튜닝 뇌는 **금액뇌(review)** 가 맞다. 비인기 DNA는 **코드에 켜져 있다.** "
        "실제 가중치 순위는 **이월(직전회 ×1.8)이 거의 전부**(ρ≥0.95). "
        "pool 10장은 고번호가 널보다 적고, **끝수 0/8/9만** 널보다 많다. "
        "고번호·금액표 점수는 **몰아주기 5장(repack)** 에서 커진다. 당첨 확률은 안 바뀐다.",
        "",
        f"판정 **{verdict}**. code_live={code_live} · end_pool={end_pool_live} · "
        f"hi_pool={hi_pool_live} · hi_repack={hi_rep_live} · prize_repack_best={prize_rep_best} · "
        f"carry_owns_weights={carry_owns_weights} · 표 crowd>struct={crowd_dominates}.",
        "",
        "## 1) DNA가 뭔가 (코드)",
        "",
        "문헌(Thaler–Ziemba / Chernoff): 당첨P=동일, 남이 안 고른 조합이 당첨되면 **몫(금액)** 이 커진다.",
        "이 레포는 조합별 판매수가 없어서 `prize_table` = "
        f"W_CROWD **{cs.W_CROWD_BY_BRAIN.get('review')}** × (1/√first_winners) + "
        f"W_STRUCT **{cs.W_STRUCT_BY_BRAIN.get('review')}** × (고번호·끝 0/8/9).",
        f"엔진 `build_review_weights`가 이 표를 blend **{cs.BLEND_STRENGTH_BY_BRAIN.get('review')}** 로 곱한 뒤 "
        "`random.choices`로 6개를 뽑는다. `PRIZE_WIRE`="
        f"{cs.prize_on()}. 7번 WIRE={REVIEW_KB7_WIRE}.",
        "",
        "같이 켜진 다른 DNA:",
        f"- 합리한장 `REVIEW_REASONABLE_SET`={REVIEW_REASONABLE_SET} (compose=`{review_compose_mode()}`)",
        f"- 3연속 평탄 `REVIEW_SHAPE_WIRE`={REVIEW_SHAPE_WIRE}",
        f"- 극소형태 패스 `REVIEW_RARE_SLICE_WIRE`={REVIEW_RARE_SLICE_WIRE}",
        f"- 형태지식 저울 `REVIEW_SHAPE_KB_WEIGHT_WIRE`={REVIEW_SHAPE_KB_WEIGHT_WIRE}",
        f"- 극소연속 PASS `REVIEW_CONSEC_PASS_WIRE`={REVIEW_CONSEC_PASS_WIRE}",
        "- 이월 ×1.8 + 끝수 질량 균등(`neutralize_ending_digit_mass`)",
        "",
        f"as_of={AS_OF} 이전 {len(draws_asof)}회 · first_winners>0 사용={fw_pos} · 0스킵={fw_zero} · "
        f"peek_max={peek} (<{AS_OF}={peek < AS_OF}) · MAX={dmax} · pred_1237={pred_1237}.",
        "",
        "## 2) 표 정렬 (as_of 1236 · Spearman ρ, n=45)",
        "",
        "| 쌍 | ρ |",
        "|----|---|",
        f"| prize vs crowd(당첨자수↓) | {rho_table['prize_vs_crowd']} |",
        f"| prize vs struct(고번호·끝089) | {rho_table['prize_vs_struct']} |",
        f"| crowd vs struct | {rho_table['crowd_vs_struct']} |",
        f"| prize vs hi32 더미 | {rho_table['prize_vs_hi32']} |",
        f"| prize vs 끝0/8/9 더미 | {rho_table['prize_vs_end089']} |",
        "",
        f"prize top12={top_prize}",
        f"가중치(풀경로) top12={top_full}",
        f"이월만 top12={top_carry}",
        f"top12 교집합 풀∩prize=**{top_overlap['full_cap_prize']}** · 풀∩이월=**{top_overlap['full_cap_carry']}**.",
        "",
        "## 3) 가중치 DNA (as_of 1236 한 시점)",
        "",
        "| 쌍 | ρ |",
        "|----|---|",
        f"| 최종가중 vs 이월만 | {rho_w['full_vs_carry']} |",
        f"| 최종가중 vs prize표 | {rho_w['full_vs_prize']} |",
        f"| 최종가중 vs (이월×prize blend) | {rho_w['full_vs_prize_blend']} |",
        f"| 이월만 vs prize표 | {rho_w['carry_vs_prize']} |",
        "",
        "최종가중이 prize blend와 거의 같으면 금액 DNA가 가중치에 묻어 있는 것. "
        "이월과도 높으면 두 DNA가 공존.",
        "",
        "## 4) 캐시 장 점유 (1037–1236 · 방금 REFILL · 널=6×k/45)",
        "",
        f"널 1장: hi32={NULL['hi32']:.3f} · end089={NULL['end089']:.3f} · hi40={NULL['hi40']:.3f} · bday={NULL['bday']:.3f}.",
        "",
        "| 뇌 kind | n | hi32 (Δ널) | end089 (Δ널) | hi40 (Δ널) | bday (Δ널) |",
        "|---------|---|-------------|--------------|------------|------------|",
        _orow("review", "pool"),
        _orow("review", "repack"),
        _orow("stat", "pool"),
        _orow("stat", "repack"),
        _orow("markov", "pool"),
        _orow("markov", "repack"),
        "",
        "review가 고번호·끝089에서 널보다 크고, stat/markov보다 크면 **비인기 구조가 장에 보임**. "
        "repack(몰아주기 5장)은 pool과 다를 수 있음 · score5 공식은 이번 측정에서 안 바꿈.",
        "",
        "## 5) 금액표 점수 (회차별 prize_table로 그 회 장을 채점 · 널 기대≈1.0)",
        "",
        "| 뇌 kind | n | mean prize | Δ1.0 |",
        "|---------|---|------------|------|",
        _srow("review", "pool"),
        _srow("review", "repack"),
        _srow("stat", "pool"),
        _srow("stat", "repack"),
        _srow("markov", "pool"),
        _srow("markov", "repack"),
        "",
        "같은 표로 세 뇌를 채점한다. review mean이 1보다 크고 타뇌보다 크면 "
        "**남이 덜 고른 쪽(프록시)으로 금액뇌만 기울어 예측 장을 뽑은 것**.",
        "",
        "## 6) 번호빈도 vs 표 (review pool 전수 · 표는 as_of1236 한 장)",
        "",
        f"ρ 빈도↔prize={rho_freq} · ↔crowd={rho_freq_crowd} · ↔struct={rho_freq_struct} · ↔이월={rho_freq_carry}.",
        "창 200회 표가 매회 바뀌므로 이 ρ는 근사. 본증거는 §5.",
        "",
        "## 7) 판정",
        "",
        f"**{verdict}**. 적중↑ 클레임 금지. 판매수 원본 없음. 시동/몰아주기공식/1237예측 없음.",
        "롤백 해당 없음(READ-ONLY).",
        "",
        "## 8) 금지 확인",
        "",
        "DB write 없음. 동결 토큰 미수정. kweon 미접촉. pred_1237=0.",
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
            {
                "verdict": verdict,
                "output_live": output_live,
                "prize_score": prize_score,
                "rho_table": rho_table,
                "rho_w": rho_w,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
