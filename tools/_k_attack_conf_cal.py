# -*- coding: utf-8 -*-
"""K-ATTACK-CONF-CAL — 뇌 내부 conf 보정·세트순위 시뮬 (READ-ONLY).

데이터: testlotto_brain_review.predicted_sets_json (set별 confidence·matched_count)
  ※ lotto_predictions 대신 review 사용 — 세트별 matched 이미 저장·기존 ATTACK 벤치와 동일 SSOT

평가: walk-forward isotonic (target 이전 회만 fit · 컨닝 금지)
산출: docs/benchmarks/20260729_KCONFCAL_results.json
"""
from __future__ import annotations

import json
import math
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT = ROOT / "docs" / "benchmarks" / "20260729_KCONFCAL_results.json"

BRAINS = ("stat", "markov", "review")
D_LO, D_HI = 2, 1234
MIN_TRAIN = 50  # BAYES와 동일 워밍 → n_eval≈1182
# BAYES pick_round_robin 참조 상수
RR_REF = {"mean": 1.7428, "ge3_rate": 0.1337, "n": 1182, "source": "K-ATTACK-BAYES"}


def pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 2 or n != len(b):
        return 0.0
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da < 1e-12 or db < 1e-12:
        return 0.0
    return num / (da * db)


def ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    return round(pearson(ranks(xs), ranks(ys)), 4)


def summarize(ms: list[int]) -> dict[str, Any]:
    n = len(ms)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3": 0, "ge3_rate": 0.0}
    ge3 = sum(1 for x in ms if x >= 3)
    ge4 = sum(1 for x in ms if x >= 4)
    return {
        "n": n,
        "mean": round(sum(ms) / n, 4),
        "ge3": ge3,
        "ge3_rate": round(ge3 / n, 4),
        "ge4": ge4,
        "ge4_rate": round(ge4 / n, 4),
    }


def delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    if not a.get("n") or not b.get("n"):
        return {"mean": 0.0, "ge3_rate": 0.0}
    return {
        "mean": round(a["mean"] - b["mean"], 4),
        "ge3_rate": round(a["ge3_rate"] - b["ge3_rate"], 4),
    }


def bin_index(conf: float) -> int:
    return max(0, min(9, int(conf // 10)))


def make_bin_calibrator(
    confs: list[float], matches: list[int]
) -> Callable[[float], float]:
    buckets: list[list[int]] = [[] for _ in range(10)]
    for c, m in zip(confs, matches):
        buckets[bin_index(c)].append(int(m))
    means = [
        (sum(b) / len(b) if b else float("nan")) for b in buckets
    ]
    # fill empty bins by neighbor
    for i in range(10):
        if means[i] == means[i] and not math.isnan(means[i]):
            continue
        left = next((means[j] for j in range(i - 1, -1, -1) if means[j] == means[j]), None)
        right = next((means[j] for j in range(i + 1, 10) if means[j] == means[j]), None)
        if left is not None and right is not None:
            means[i] = (left + right) / 2
        elif left is not None:
            means[i] = left
        elif right is not None:
            means[i] = right
        else:
            means[i] = 0.8

    def cal(c: float) -> float:
        return float(means[bin_index(c)])

    return cal


def make_isotonic_calibrator(
    confs: list[float], matches: list[int]
) -> Callable[[float], float]:
    if len(confs) < 10:
        return make_bin_calibrator(confs, matches)
    try:
        from sklearn.isotonic import IsotonicRegression

        ir = IsotonicRegression(out_of_bounds="clip")
        ir.fit(confs, matches)

        def cal(c: float) -> float:
            return float(ir.predict([c])[0])

        return cal
    except Exception:
        return make_bin_calibrator(confs, matches)


def calibration_bins(confs: list[float], matches: list[int]) -> list[dict[str, Any]]:
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(10)]
    for c, m in zip(confs, matches):
        buckets[bin_index(c)].append((c, int(m)))
    out = []
    for i, b in enumerate(buckets):
        lo, hi = i * 10, i * 10 + 9
        if not b:
            out.append({"bin": f"{lo}-{hi}", "n": 0, "mean_matched": None, "mean_conf": None})
            continue
        out.append(
            {
                "bin": f"{lo}-{hi}",
                "n": len(b),
                "mean_matched": round(sum(m for _, m in b) / len(b), 4),
                "mean_conf": round(sum(c for c, _ in b) / len(b), 2),
            }
        )
    return out


def load_rows() -> dict[int, dict[str, dict[str, Any]]]:
    """draw -> brain -> {sets: [...], best_set_no}"""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT draw_no, brain_tag, predicted_sets_json, best_set_no, matched_count
        FROM testlotto_brain_review
        WHERE draw_no BETWEEN ? AND ? AND brain_tag IN ('stat','markov','review')
        ORDER BY draw_no
        """,
        (D_LO, D_HI),
    ).fetchall()
    con.close()

    by: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        tag = r["brain_tag"]
        d = int(r["draw_no"])
        try:
            sets = json.loads(r["predicted_sets_json"] or "[]")
        except Exception:
            sets = []
        parsed = []
        for s in sets:
            conf = float(s.get("confidence") or 0)
            m = int(s["matched_count"]) if s.get("matched_count") is not None else 0
            parsed.append(
                {
                    "set_no": int(s.get("set_no") or 0),
                    "conf": conf,
                    "match": m,
                }
            )
        if parsed:
            by[d][tag] = {
                "sets": parsed,
                "best_set_no": int(r["best_set_no"] or 1),
                "best_match": int(r["matched_count"] or 0),
            }
    return by


def pick_best_set_row(entry: dict[str, Any]) -> dict[str, Any]:
    sets = entry["sets"]
    bno = entry["best_set_no"]
    for s in sets:
        if s["set_no"] == bno:
            return s
    return max(sets, key=lambda s: s["match"])


def main() -> None:
    by = load_rows()
    complete = sorted(d for d, br in by.items() if all(b in br for b in BRAINS))

    cal_report: dict[str, Any] = {}
    for tag in BRAINS:
        confs: list[float] = []
        matches: list[int] = []
        for d in complete:
            for s in by[d][tag]["sets"]:
                confs.append(s["conf"])
                matches.append(s["match"])
        cal_report[tag] = {
            "n_sets": len(confs),
            "spearman_r": spearman(confs, [float(m) for m in matches]),
            "conf_mean": round(sum(confs) / len(confs), 2) if confs else 0,
            "match_mean": round(sum(matches) / len(matches), 4) if matches else 0,
            "bins": calibration_bins(confs, matches),
        }

    hist_conf: dict[str, list[float]] = {b: [] for b in BRAINS}
    hist_match: dict[str, list[int]] = {b: [] for b in BRAINS}

    # within-brain set policies (3 tickets/draw)
    w_orig: list[int] = []
    w_cal: list[int] = []
    w_tier: list[int] = []  # current best_set
    by_brain: dict[str, dict[str, list[int]]] = {
        b: {"orig": [], "cal": [], "tier": []} for b in BRAINS
    }

    # cross-brain one ticket (BAYES-comparable)
    cross_orig: list[int] = []
    cross_cal: list[int] = []
    cross_tier_rr: list[int] = []  # RR over brains using tier best_set

    eval_i = 0
    n_eval_draws = 0
    method_note = "isotonic"

    for d in complete:
        ready = all(len(hist_conf[b]) >= MIN_TRAIN * 5 for b in BRAINS)
        if not ready:
            for tag in BRAINS:
                for s in by[d][tag]["sets"]:
                    hist_conf[tag].append(s["conf"])
                    hist_match[tag].append(s["match"])
            continue

        n_eval_draws += 1
        calibrators = {
            tag: make_isotonic_calibrator(hist_conf[tag], hist_match[tag])
            for tag in BRAINS
        }
        if eval_i == 0:
            try:
                from sklearn.isotonic import IsotonicRegression  # noqa: F401
            except Exception:
                method_note = "bin_mean_fallback"

        brain_score_orig: dict[str, tuple[float, int]] = {}
        brain_score_cal: dict[str, tuple[float, int]] = {}

        for tag in BRAINS:
            sets = by[d][tag]["sets"]
            s_orig = max(sets, key=lambda s: (s["conf"], -s["set_no"]))
            s_cal = max(
                sets,
                key=lambda s: (calibrators[tag](s["conf"]), -s["set_no"]),
            )
            s_tier = pick_best_set_row(by[d][tag])

            w_orig.append(s_orig["match"])
            w_cal.append(s_cal["match"])
            w_tier.append(s_tier["match"])
            by_brain[tag]["orig"].append(s_orig["match"])
            by_brain[tag]["cal"].append(s_cal["match"])
            by_brain[tag]["tier"].append(s_tier["match"])

            brain_score_orig[tag] = (s_orig["conf"], s_orig["match"])
            brain_score_cal[tag] = (calibrators[tag](s_cal["conf"]), s_cal["match"])

        tag_o = max(BRAINS, key=lambda t: (brain_score_orig[t][0], -BRAINS.index(t)))
        tag_c = max(BRAINS, key=lambda t: (brain_score_cal[t][0], -BRAINS.index(t)))
        cross_orig.append(brain_score_orig[tag_o][1])
        cross_cal.append(brain_score_cal[tag_c][1])

        rr_tag = BRAINS[eval_i % 3]
        cross_tier_rr.append(by[d][rr_tag]["best_match"])

        for tag in BRAINS:
            for s in by[d][tag]["sets"]:
                hist_conf[tag].append(s["conf"])
                hist_match[tag].append(s["match"])
        eval_i += 1

    s_orig = summarize(w_orig)
    s_cal = summarize(w_cal)
    s_tier = summarize(w_tier)
    s_cross_o = summarize(cross_orig)
    s_cross_c = summarize(cross_cal)
    s_rr = summarize(cross_tier_rr)

    spearman_pos = sum(1 for t in BRAINS if cal_report[t]["spearman_r"] > 0)
    d_cal_orig = delta(s_cal, s_orig)
    d_cal_tier = delta(s_cal, s_tier)
    d_cal_rr = delta(s_cross_c, s_rr)  # cross cal vs RR(tier)
    d_cross = delta(s_cross_c, s_cross_o)
    # primary instruction deltas (within pool + vs RR ref mean)
    d_vs_rr_ref = {
        "mean": round(s_cross_c["mean"] - RR_REF["mean"], 4),
        "ge3_rate": round(s_cross_c["ge3_rate"] - RR_REF["ge3_rate"], 4),
    }

    gates = {
        "spearman_pos_ge2": spearman_pos >= 2,
        "conf_cal_vs_orig_mean_gt0": d_cal_orig["mean"] > 0,
        "conf_cal_vs_rr_mean_gt0": d_vs_rr_ref["mean"] > 0,
        "cross_cal_vs_orig_mean_gt0": d_cross["mean"] > 0,
        "conf_cal_beats_tier_mean": d_cal_tier["mean"] > 0,
    }

    if (
        gates["spearman_pos_ge2"]
        and gates["conf_cal_vs_orig_mean_gt0"]
        and gates["conf_cal_vs_rr_mean_gt0"]
    ):
        verdict = "GO"
        next_id = "K-ATTACK-CONF-WIRE"
    elif gates["spearman_pos_ge2"] and (
        gates["conf_cal_vs_orig_mean_gt0"] or gates["cross_cal_vs_orig_mean_gt0"]
    ):
        verdict = "보류"
        next_id = "K-ATTACK-NEXT-OPEN"
    elif not gates["spearman_pos_ge2"]:
        verdict = "관측종료"
        next_id = "K-ATTACK-NEXT-OPEN"
    else:
        verdict = "보류"
        next_id = "K-ATTACK-NEXT-OPEN"

    out = {
        "id": "K-ATTACK-CONF-CAL",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "n_eval": n_eval_draws,
        "n_set_picks": len(w_orig),
        "method": {
            "data": "testlotto_brain_review.predicted_sets_json",
            "calibrator": method_note,
            "fit": f"walk-forward expanding · min_train_draws≈{MIN_TRAIN}",
            "db_code_write": False,
            "note": (
                "within=뇌별 5세트 중 max conf/cal/tier. "
                "cross=3뇌 중 max score 1장. RR=뇌 cycle + best_set(tier)."
            ),
        },
        "calibration": cal_report,
        "set_rank_comparison": {
            "orig_conf": s_orig,
            "conf_cal": s_cal,
            "tier_best_set": s_tier,
            "round_robin": {
                "mean": s_rr["mean"],
                "ge3_rate": s_rr["ge3_rate"],
                "n": s_rr["n"],
            },
            "round_robin_bayes_ref": RR_REF,
            "cross_brain_pick": {
                "orig_conf": s_cross_o,
                "conf_cal": s_cross_c,
            },
            "by_brain": {
                tag: {
                    "orig_conf": summarize(by_brain[tag]["orig"]),
                    "conf_cal": summarize(by_brain[tag]["cal"]),
                    "tier_best_set": summarize(by_brain[tag]["tier"]),
                    "delta_cal_minus_orig_mean": round(
                        summarize(by_brain[tag]["cal"])["mean"]
                        - summarize(by_brain[tag]["orig"])["mean"],
                        4,
                    ),
                }
                for tag in BRAINS
            },
        },
        "delta": {
            "conf_cal_vs_orig": d_cal_orig,
            "conf_cal_vs_tier": d_cal_tier,
            "conf_cal_vs_rr": d_vs_rr_ref,
            "conf_cal_vs_rr_replay": delta(s_cross_c, s_rr),
            "cross_cal_vs_cross_orig": d_cross,
        },
        "gates": gates,
        "verdict": verdict,
        "suggested_next": next_id,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(OUT),
                "n_eval": n_eval_draws,
                "spearman": {t: cal_report[t]["spearman_r"] for t in BRAINS},
                "within": {"orig": s_orig, "cal": s_cal, "tier": s_tier},
                "cross": {"orig": s_cross_o, "cal": s_cross_c, "rr": s_rr},
                "delta": out["delta"],
                "gates": gates,
                "verdict": verdict,
                "next": next_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
