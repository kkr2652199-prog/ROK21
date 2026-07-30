# -*- coding: utf-8 -*-
"""K-SIGNAL-REPACK-01 — 번호 몰아주기(repack) survey (READ-ONLY live WF).

뇌당 10세트 pool → 개별 번호 신호 점수 → 5 신호세트 재조립(몰아주기).
3뇌×5 = 15세트. K-SIGNAL-SELECT(통째 5장 고르기)와 구분.
coordinator·predict_* 원본 미수정 · QUICK tail-200 seed=42.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.bench_quick_gate import (  # noqa: E402
    DRAW_END,
    DRAW_START,
    FULL_N_EVAL,
    MC_SEED,
    NULL_GE3,
    QUICK_N_EVAL,
    WIRE_PIN_GE3,
    WIRE_PIN_MEAN,
    enrich_metrics,
    filter_draw_rows,
    gate_criteria_doc,
    resolve_eval_window,
)
from tools._k_signal_select_survey import (  # noqa: E402
    POOL_SETS_PER_BRAIN,
    SELECT_N,
    WINDOW_ALPHA,
    WINDOW_SIGNAL,
    WINDOW_WEEKS,
    _bin_match_score,
    _expand_pool,
    _expected_bins,
    _hint_overlap_score,
    _jaccard,
    _pick_set_no_asc,
    _pick_top_greedy,
)
from tools._k_window_signal_survey import (  # noqa: E402
    _build_hint,
    _empty_tier,
    _live_candidates,
    _prediction_rank_tier,
    _record_tier,
)

random.seed(MC_SEED)

from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.learn_state_cutoff import clear_history_cache  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402
from app.testlotto.tier_utils import score_predicted_set  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260730_KSIGNAL_REPACK_survey.json"
OUT_MD = ROOT / "reports" / "20260730_KSIGNAL_REPACK_SURVEY.md"

BRAIN_TAGS = ["markov", "stat", "review"]
REPACK_SETS_PER_BRAIN = 5
LEARN_EMA = 0.15
W_HINT = 0.40
W_FREQ = 0.25
W_LEARN = 0.35

STRATEGIES = [
    "signal_repack",
    "hint_only_repack",
    "random_repack",
    "set_no_asc",
    "k_signal_select_combined",
]


class RollingSignalLearner:
    """Walk-forward: target draw 이전 회차만으로 번호·세트위치 기여도 EMA."""

    def __init__(self) -> None:
        self.num_hit_ema: dict[int, float] = {n: 0.0 for n in range(1, 46)}
        self.pos_hit_ema: dict[int, float] = {n: 0.0 for n in range(1, POOL_SETS_PER_BRAIN + 1)}

    def snapshot(self) -> tuple[dict[int, float], dict[int, float]]:
        return dict(self.num_hit_ema), dict(self.pos_hit_ema)

    def update_from_pool(
        self,
        pool_by_brain: dict[str, list[dict]],
        actual: set[int],
    ) -> None:
        """10세트 pool partial hit → 번호·set_no 위치 EMA 갱신."""
        for _tag, pool in pool_by_brain.items():
            for c in pool:
                sn = int(c.get("pred_set_no") or c.get("set_no") or 1)
                nums = [int(x) for x in c["nums"]]
                mc = len(set(nums) & actual)
                if mc <= 0:
                    continue
                pos_credit = mc / 6.0
                old_p = self.pos_hit_ema.get(sn, 0.0)
                self.pos_hit_ema[sn] = (1 - LEARN_EMA) * old_p + LEARN_EMA * pos_credit
                per_num = mc / 6.0
                for n in nums:
                    if n in actual:
                        old = self.num_hit_ema.get(n, 0.0)
                        self.num_hit_ema[n] = (1 - LEARN_EMA) * old + LEARN_EMA * per_num


def _pool_by_brain(pool: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in pool:
        tag = c.get("brain_tag", "")
        if tag in out:
            out[tag].append(c)
    return out


def _pool_freq(pool: list[dict]) -> dict[int, float]:
    cnt: Counter[int] = Counter()
    for c in pool:
        for n in c["nums"]:
            cnt[int(n)] += 1
    mx = max(cnt.values()) if cnt else 1
    return {n: cnt.get(n, 0) / mx for n in range(1, 46)}


def _number_scores(
    pool: list[dict],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_scores: bool = False,
) -> dict[int, float]:
    freq = _pool_freq(pool)
    pos_boost: dict[int, float] = defaultdict(float)
    for c in pool:
        sn = int(c.get("pred_set_no") or 1)
        pw = pos_ema.get(sn, 0.0)
        for n in c["nums"]:
            pos_boost[int(n)] = max(pos_boost[int(n)], pw)

    scores: dict[int, float] = {}
    for n in range(1, 46):
        if random_scores:
            scores[n] = random.random()
        elif hint_only:
            scores[n] = max(0.0, hint.get(n, 0.0))
        else:
            scores[n] = (
                W_HINT * max(0.0, hint.get(n, 0.0))
                + W_FREQ * freq.get(n, 0.0)
                + W_LEARN * (num_ema.get(n, 0.0) + 0.5 * pos_boost.get(n, 0.0))
            )
    return scores


def _repack_sets(scores: dict[int, float], n_sets: int = REPACK_SETS_PER_BRAIN) -> list[list[int]]:
    """신호 강한 번호부터 set1→set5 순으로 6개씩 몰아주기."""
    ranked = sorted(range(1, 46), key=lambda x: (-scores[x], x))
    sets: list[list[int]] = []
    idx = 0
    for _ in range(n_sets):
        chunk = ranked[idx : idx + 6]
        idx += 6
        sets.append(sorted(chunk))
    return sets


def _repack_by_brain(
    pool_by_brain: dict[str, list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_repack: bool = False,
) -> list[dict]:
    """뇌당 5 신호세트 → brain_tag 포함 flat list."""
    out: list[dict] = []
    for tag in BRAIN_TAGS:
        pool = pool_by_brain.get(tag, [])
        if not pool:
            continue
        scores = _number_scores(
            pool,
            hint,
            num_ema,
            pos_ema,
            hint_only=hint_only,
            random_scores=random_repack,
        )
        for i, nums in enumerate(_repack_sets(scores)):
            out.append(
                {
                    "nums": nums,
                    "brain_tag": tag,
                    "pred_set_no": i + 1,
                    "set_no": i + 1,
                    "repack_rank": i + 1,
                }
            )
    return out


def _top5_from_15(repacked: list[dict]) -> list[dict]:
    """15세트 → 뇌별 1번 세트 3장 + 신호 set_no 2·3 중 상위 2장 = 5장."""
    by_brain: dict[str, list[dict]] = defaultdict(list)
    for c in repacked:
        by_brain[c["brain_tag"]].append(c)
    selected: list[dict] = []
    extras: list[dict] = []
    for tag in BRAIN_TAGS:
        sets = sorted(by_brain.get(tag, []), key=lambda x: int(x["pred_set_no"]))
        if sets:
            selected.append(sets[0])
            extras.extend(sets[1:])
    extras.sort(key=lambda x: (int(x["pred_set_no"]), x["brain_tag"]))
    selected.extend(extras[: max(0, SELECT_N - len(selected))])
    return selected[:SELECT_N]


def _best_match(sets: list[dict], actual: set[int]) -> int:
    if not sets:
        return 0
    return max(len(set(int(x) for x in c["nums"]) & actual) for c in sets)


def _best_tier(
    sets: list[dict], actual_list: list[int], bonus: int
) -> tuple[int, dict[str, int]]:
    tier_acc = _empty_tier()
    best_tr = 0
    for c in sets:
        scored = score_predicted_set(c["nums"], actual_list, bonus)
        tr = int(scored["tier_rank"])
        _record_tier(tier_acc, tr)
        if tr > 0 and (best_tr == 0 or tr < best_tr):
            best_tr = tr
    return best_tr, tier_acc


def _reset_predictions_for_eval(draw_start: int, draw_end: int) -> dict[str, Any]:
    """eval 구간 lotto_predictions 삭제 — cached 예측 간섭 방지."""
    init_lotto_db()
    conn = get_lotto_db()
    try:
        before = conn.execute(
            "SELECT COUNT(*) AS c FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            (draw_start, draw_end),
        ).fetchone()["c"]
        conn.execute(
            "DELETE FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            (draw_start, draw_end),
        )
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) AS c FROM lotto_predictions WHERE target_draw_no BETWEEN ? AND ?",
            (draw_start, draw_end),
        ).fetchone()["c"]
    finally:
        conn.close()
    clear_history_cache()
    return {
        "table": "lotto_predictions",
        "draw_range": [draw_start, draw_end],
        "deleted_rows": int(before),
        "remaining_in_range": int(after),
        "learn_state_reset": False,
        "note": "eval 구간 cached prediction만 삭제 · live WF 생성 · learn_state/coordinator 미건드림",
    }


def run_survey(eval_window) -> tuple[int, dict[str, Any], dict[str, Any]]:
    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    rows = filter_draw_rows(rows, eval_window)

    db_reset = _reset_predictions_for_eval(eval_window.draw_start, eval_window.draw_end)

    learner = RollingSignalLearner()
    acc: dict[str, list[int]] = {s: [] for s in STRATEGIES}
    acc_top5: dict[str, list[int]] = {s: [] for s in ("signal_repack", "hint_only_repack")}
    means: dict[str, list[float]] = {s: [] for s in STRATEGIES}
    tiers: dict[str, dict[str, int]] = {s: _empty_tier() for s in STRATEGIES}

    for ri, row in enumerate(rows):
        if ri % 50 == 0:
            print(f"  progress {ri}/{len(rows)} draw_no={row['draw_no']}", flush=True)
        row = dict(row)
        draw_no = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        actual_list = sorted(actual)
        bonus = int(row.get("bonus") or 0)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        num_ema, pos_ema = learner.snapshot()

        random.seed(MC_SEED)
        std_candidates = _live_candidates(draws, draw_no)
        pool = _expand_pool(draws, draw_no)
        pool_br = _pool_by_brain(pool)

        hint = _build_hint(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)
        expected_bins = _expected_bins(draws)

        repack_main = _repack_by_brain(pool_br, hint, num_ema, pos_ema)
        repack_hint = _repack_by_brain(
            pool_br, hint, num_ema, pos_ema, hint_only=True
        )
        repack_rand = _repack_by_brain(
            pool_br, hint, num_ema, pos_ema, random_repack=True
        )
        select_combined = _pick_top_greedy(
            pool,
            lambda nums: (
                0.5 * _hint_overlap_score(nums, hint)
                + 0.35 * _bin_match_score(nums, expected_bins)
            ),
            diversity_weight=0.15,
        )
        control = _pick_set_no_asc(std_candidates)

        picks: dict[str, list[dict]] = {
            "signal_repack": repack_main,
            "hint_only_repack": repack_hint,
            "random_repack": repack_rand,
            "set_no_asc": control,
            "k_signal_select_combined": select_combined,
        }

        for sid, selected in picks.items():
            best = _best_match(selected, actual)
            acc[sid].append(best)
            means[sid].append(float(best))
            _tr, tacc = _best_tier(selected, actual_list, bonus)
            for k, v in tacc.items():
                tiers[sid][k] += v

        acc_top5["signal_repack"].append(_best_match(_top5_from_15(repack_main), actual))
        acc_top5["hint_only_repack"].append(
            _best_match(_top5_from_15(repack_hint), actual)
        )

        learner.update_from_pool(pool_br, actual)

    n_eval = len(acc["set_no_asc"])
    mean_by = {
        s: round(sum(means[s]) / len(means[s]), 4) if means[s] else 0.0 for s in STRATEGIES
    }
    meta = {
        "eval_modes": {
            "primary": "best_of_15 — 3뇌×5 repack 세트 중 최대 적중",
            "secondary_top5": "top5_from_15 — 뇌별1번+잔여2장 → 5장 best",
        },
        "repack_weights": {"hint": W_HINT, "freq": W_FREQ, "learn": W_LEARN, "ema": LEARN_EMA},
        "db_reset": db_reset,
        "tiers": tiers,
        "top5_eval": {
            sid: {
                "ge3_rate": round(sum(1 for x in acc_top5[sid] if x >= 3) / n_eval, 4)
                if n_eval
                else 0.0,
                "mean": round(sum(acc_top5[sid]) / n_eval, 4) if n_eval else 0.0,
            }
            for sid in acc_top5
        },
    }
    return n_eval, acc, mean_by, meta


def _summarize_strategy(
    strategy_id: str, bests: list[int], mean: float, gate_mode: str, tiers: dict[str, int]
) -> dict[str, Any]:
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    n = len(bests)
    base = enrich_metrics(ge3_c, n, mean, gate_mode=gate_mode)
    return {
        "strategy_id": strategy_id,
        "label": strategy_id,
        "eval_mode": "best_of_15"
        if strategy_id in ("signal_repack", "hint_only_repack", "random_repack")
        else ("best_of_5" if strategy_id == "set_no_asc" else "best_of_5_from_30"),
        "repack_sets_per_brain": REPACK_SETS_PER_BRAIN if "repack" in strategy_id else None,
        **base,
        "ge4_rate": round(ge4_c / n, 4) if n else 0.0,
        "ge4_count": ge4_c,
        "tiers": dict(tiers),
    }


def _write_report(out: dict[str, Any]) -> None:
    results = out["strategies"]
    best = out["best_strategy"]
    baseline = out["baseline_control"]
    n = out["n_eval"]
    gate_mode = out["gate_mode"]
    pass_gate = out.get("pass_gate", False)
    db_reset = out.get("db_reset", {})

    lines: list[str] = []
    lines.append("# K-SIGNAL-REPACK-01 — 번호 몰아주기(repack) survey (READ-ONLY live WF)")
    lines.append(
        f"\n날짜 {out['ts'][:10]} · elapsed {out['elapsed_sec']}s · "
        f"**{'PASS' if pass_gate else 'FAIL'}** · seed={MC_SEED} · n={n} · gate={gate_mode}"
    )
    lines.append(
        f"\n개념: 뇌당 10세트 pool → **번호 단위** 신호 점수 → 5세트 몰아주기 ×3뇌=**15세트**. "
        f"K-SIGNAL-SELECT(30장 중 5장 통째 선택)과 **다름**."
    )
    lines.append(
        f"\n평가: primary=**best_of_15** · secondary=top5_from_15(JSON `top5_eval`). "
        f"hint=w{WINDOW_WEEKS}_{WINDOW_SIGNAL}@α={WINDOW_ALPHA}."
    )

    lines.append("\n## 1. 📋 선생님이 준 숙제")
    lines.append("| 항목 | 내용 |")
    lines.append("|------|------|")
    lines.append("| **ID** | `K-SIGNAL-REPACK-01` |")
    lines.append(
        "| **질문** | 10세트 pool 번호를 신호 점수로 재조립(몰아주기)하면 set_no_asc·K-SIGNAL-SELECT combined 대비 ge3↑? |"
    )
    lines.append("| **PASS (QUICK)** | any repack strategy ge3>null AND p<0.15 |")
    lines.append("| **금지** | coordinator·predict_* 수정 · wire · frozen path |")

    lines.append("\n## 2. 🔧 학생이 한 일")
    lines.append("| 항목 | Y/N |")
    lines.append("|------|-----|")
    lines.append("| coordinator 수정 | **N** |")
    lines.append(f"| DB reset | **Y** | `{db_reset.get('table')}` {db_reset.get('deleted_rows', 0)}행 삭제 |")
    lines.append("| pipeline | **WF live** |")

    lines.append("\n## 3. 📊 풀이 (결과표)")
    lines.append("\n### SUMMARY")
    lines.append(
        "| label | pipeline | mean | ge3_rate | Δnull | Δpin | p | verdict |"
    )
    lines.append("|-------|----------|-----:|---------:|------:|-----:|--:|---------|")
    lines.append("| **theory null** | — | 0.8000 | 0.1137 | — | — | — | — |")
    lines.append(f"| **WIRE-V2 pin** | stored | {WIRE_PIN_MEAN} | {WIRE_PIN_GE3} | +0.0310 | — | — | pin |")
    lines.append(
        f"| **set_no_asc (control)** | WF | {baseline['mean']} | {baseline['ge3_rate']} | "
        f"{baseline['delta_ge3_vs_null']:+.4f} | {baseline['delta_ge3_vs_pin']:+.4f} | "
        f"{baseline['p_value']} | {baseline['verdict']} |"
    )
    lines.append(
        f"| **best repack** | WF | **{best['mean']}** | **{best['ge3_rate']}** | "
        f"{best['delta_ge3_vs_null']:+.4f} | {best['delta_ge3_vs_pin']:+.4f} | "
        f"{best['p_value']} | **{best['verdict']}** |"
    )

    lines.append("\n### strategies (ge3 내림)")
    lines.append("| strategy | eval | mean | ge3 | ge3_cnt | Δpin | p | verdict |")
    lines.append("|----------|------|-----:|----:|--------:|-----:|--:|---------|")
    for r in sorted(results, key=lambda x: (-x["ge3_rate"], -x["mean"])):
        ev = r.get("eval_mode") or "—"
        lines.append(
            f"| {r['strategy_id']} | {ev} | {r['mean']} | {r['ge3_rate']} | {r['ge3_count']} | "
            f"{r['delta_ge3_vs_pin']:+.4f} | {r['p_value']} | {r['verdict']} |"
        )

    lines.append("\n### tier 1~5 (회차별 best 세트 등수 누적)")
    lines.append("| strategy | r1 | r2 | r3 | r4 | r5 |")
    lines.append("|----------|---:|---:|---:|---:|---:|")
    for r in sorted(results, key=lambda x: x["strategy_id"]):
        t = r.get("tiers") or {}
        lines.append(
            f"| {r['strategy_id']} | {t.get('r1', 0)} | {t.get('r2', 0)} | "
            f"{t.get('r3', 0)} | {t.get('r4', 0)} | {t.get('r5', 0)} |"
        )

    top5 = out.get("top5_eval") or {}
    if top5:
        lines.append("\n### top5_from_15 (보조)")
        lines.append("| strategy | mean | ge3_rate |")
        lines.append("|----------|-----:|---------:|")
        for sid, tv in top5.items():
            lines.append(f"| {sid} | {tv['mean']} | {tv['ge3_rate']} |")

    lines.append("\n## 4. ✅/❌ 판정")
    lines.append(f"- **gate:** {'PASS' if pass_gate else 'FAIL'} · best=`{best['strategy_id']}` ge3={best['ge3_rate']}")
    sel_ref = next((r for r in results if r["strategy_id"] == "k_signal_select_combined"), None)
    if sel_ref:
        lines.append(
            f"- vs K-SIGNAL-SELECT combined: ge3={sel_ref['ge3_rate']} "
            f"(repack best {best['ge3_rate']})"
        )

    lines.append("\n## 5. 📝 복습")
    lines.append(f"- **recommended_next:** {out['recommended_next']}")
    lines.append(f"- **verdict:** {out['verdict']}")

    lines.append("\n## 6. 📎 근거")
    lines.append(f"- JSON: `docs/benchmarks/20260730_KSIGNAL_REPACK_survey.json`")
    lines.append(f"- script: `tools/_k_signal_repack_survey.py`")
    lines.append(f"- db_reset: {json.dumps(db_reset, ensure_ascii=False)}")

    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    drive = ROOT / "My_Drive_Sync" / "커서보고서" / "20260730_KSIGNAL_REPACK_SURVEY.md"
    drive.parent.mkdir(parents=True, exist_ok=True)
    drive.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_MD}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="K-SIGNAL-REPACK-01 survey")
    ap.add_argument("--n-eval", type=int, default=QUICK_N_EVAL)
    ap.add_argument("--sample", choices=["tail", "full"], default="tail")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    n_eval_arg = FULL_N_EVAL if args.full else args.n_eval
    sample_mode = "full" if args.full else args.sample
    eval_window = resolve_eval_window(n_eval_arg, sample_mode=sample_mode)
    gate_mode = "full" if not eval_window.quick_gate else "quick"

    t0 = time.time()
    print(
        f"K-SIGNAL-REPACK-01 live WF {eval_window.draw_start}~{eval_window.draw_end} "
        f"n={eval_window.n_eval_target} gate={gate_mode} seed={MC_SEED}",
        flush=True,
    )

    n_eval, acc, mean_by, meta = run_survey(eval_window)

    results = [
        _summarize_strategy(s, acc[s], mean_by[s], gate_mode, meta["tiers"][s])
        for s in STRATEGIES
    ]
    results.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))

    baseline = next(r for r in results if r["strategy_id"] == "set_no_asc")
    repack_strats = [r for r in results if "repack" in r["strategy_id"]]
    best = max(results, key=lambda x: (x["ge3_rate"], x["mean"]))
    best_repack = max(repack_strats, key=lambda x: (x["ge3_rate"], x["mean"])) if repack_strats else best

    if gate_mode == "full":
        criterion = "any repack ge3>pin AND p<0.05"
        pass_gate = any(r["verdict"] == "PASS" for r in repack_strats)
    else:
        criterion = "any repack ge3>null AND p<0.15"
        pass_gate = any(r["verdict"] == "PASS" for r in repack_strats)

    if pass_gate:
        recommended = "K-SIGNAL-REPACK-FULL" if gate_mode == "quick" else "K-SIGNAL-REPACK-WIRE-HOLD"
        verdict = f"QUICK PASS: {best_repack['strategy_id']} ge3={best_repack['ge3_rate']} p={best_repack['p_value']}"
    else:
        recommended = "K-SIGNAL-SELECT-FULL (repack FAIL → 선별축 우선)"
        verdict = (
            f"FAIL: best repack {best_repack['strategy_id']} ge3={best_repack['ge3_rate']} "
            f"p={best_repack['p_value']}"
        )

    out: dict[str, Any] = {
        "id": "K-SIGNAL-REPACK-01",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": n_eval,
        "draw_range": [eval_window.draw_start, eval_window.draw_end],
        "eval_window": {
            "n_eval_target": eval_window.n_eval_target,
            "sample_mode": eval_window.sample_mode,
            "quick_gate": eval_window.quick_gate,
        },
        "gate_mode": gate_mode,
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": MC_SEED,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "repack_sets_per_brain": REPACK_SETS_PER_BRAIN,
        "total_repack_sets": REPACK_SETS_PER_BRAIN * len(BRAIN_TAGS),
        "window_hint": {"weeks": WINDOW_WEEKS, "signal": WINDOW_SIGNAL, "alpha_ref": WINDOW_ALPHA},
        "strategies": results,
        "baseline_control": baseline,
        "best_strategy": best,
        "best_repack_strategy": best_repack,
        "k_signal_select_combined_ref": next(
            (r for r in results if r["strategy_id"] == "k_signal_select_combined"), None
        ),
        "eval_modes": meta["eval_modes"],
        "repack_weights": meta["repack_weights"],
        "top5_eval": meta["top5_eval"],
        "db_reset": meta["db_reset"],
        "gates": gate_criteria_doc(),
        "pass_gate": pass_gate,
        "gates_eval": {"pass": pass_gate, "criterion": criterion},
        "recommended_next": recommended,
        "verdict": verdict,
        "db_code_write": True,
        "db_code_write_scope": "lotto_predictions eval range DELETE only",
        "coordinator_modified": False,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON}", flush=True)
    _write_report(out)
    print(f"verdict={verdict}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
