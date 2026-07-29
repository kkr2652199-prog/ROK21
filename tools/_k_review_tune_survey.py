# -*- coding: utf-8 -*-
"""K-REVIEW-TUNE-SURVEY — review(복습왕) carry_mult/decay/window 격자.

형 지시서 요약(본 파일은 predict_review_king.py 수정 금지):
1) live pipeline: 매 draw_no마다 markov/stat는 predict_sets를 live 호출
2) review은 override 함수(review_predict_override)로 carry_mult/decay/repeat_window만 런타임 변경
3) apply_coordinator_scoring → apply_markov_wire_quota(MARKOV_WIRE_ENABLED=True, set_no_asc)
4) best ge3 > 0.1447 AND p < 0.05 → PASS

산출물:
- docs/benchmarks/20260729_KREVIEW_TUNE_survey.json
- reports/20260729_KREVIEW_TUNE_SURVEY.md
- My_Drive_Sync/커서보고서/20260729_KREVIEW_TUNE_SURVEY.md (보고서 복사)
"""

from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains import predict_flow_shaman, predict_review_king, predict_stat_fairy  # noqa: E402
from app.testlotto.brains.coordinator import apply_coordinator_scoring, apply_markov_wire_quota  # noqa: E402
from app.testlotto.brains.coordinator import MARKOV_WIRE_ENABLED  # noqa: E402
from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN  # noqa: E402
from app.testlotto.data_service import _get_draws_before  # noqa: E402
from app.testlotto.filters import tier1_filter  # noqa: E402
from app.testlotto.features.draw_features import repeat_rate_after_draw, sorted_nums  # noqa: E402
from app.testlotto.learn_state import load_learn_state  # noqa: E402
from app.testlotto.learn_state_cutoff import set_learn_as_of  # noqa: E402
from app.testlotto.models import get_lotto_db, init_lotto_db  # noqa: E402


DRAW_START = 53
DRAW_END = 1234
N_EVAL = DRAW_END - DRAW_START + 1  # 1182
SEED = 42

WIRE_PIN_GE3 = 0.1447
WIRE_PIN_MEAN = 1.7504
NULL_GE3 = 0.1137
ALPHA = 0.05

WIRE_QUOTA = {"markov": 3, "stat": 1, "review": 1}
PIPELINE = "live_predict_sets (markov/stat) + review_predict_override + apply_coordinator_scoring + apply_markov_wire_quota"


@dataclass(frozen=True)
class ReviewParams:
    carry_mult: float
    decay: float  # "no_carry_decay"
    repeat_window: int

    def combo_id(self) -> str:
        return f"carry={self.carry_mult:g}|decay={self.decay:g}|window={self.repeat_window:g}"


# --- review_predict_override: predict_review_king.build_review_weights만 런타임 오버라이드 ---
_OVR: dict[str, Any] = {"carry_mult": None, "decay": None, "repeat_window": None}
_ORIG_BUILD_REVIEW_WEIGHTS = predict_review_king.build_review_weights


def _build_review_weights_override(draws: list[dict]) -> dict[int, float]:
    """predict_review_king.build_review_weights를 런타임 파라미터로 대체.

    mapping (지시서 기반):
    - carry_mult: prev_nums(직전 회차 6개) 가중 증폭 계수 (기존 1.8 대체)
    - decay: prev_nums가 아닌 수의 가중 하향 계수 (기존 0.85 대체)
    - repeat_window: repeat_rate_after_draw의 lookback (0이면 전체: repeat_rate_after_draw slicing 동작)
    """

    carry_mult = float(_OVR["carry_mult"])
    no_carry_decay = float(_OVR["decay"])
    repeat_window = int(_OVR["repeat_window"])

    if not draws:
        return {n: 1.0 for n in range(1, 46)}

    prev_nums = sorted_nums(draws[-1])
    rates = repeat_rate_after_draw(draws, lookback=repeat_window)
    learn = load_learn_state("review")
    adj = learn.get("adjustments", {})
    carry_boost = 1.0 + float(adj.get("carry_over_boost", 0))

    weights = {n: float(rates.get(n, 0.08)) for n in range(1, 46)}
    for n in prev_nums:
        weights[n] *= carry_mult * carry_boost
    for n in range(1, 46):
        if n not in prev_nums:
            weights[n] *= no_carry_decay

    return predict_review_king.neutralize_ending_digit_mass(weights)


predict_review_king.build_review_weights = _build_review_weights_override


def _seed_for_review(draw_no: int, p: ReviewParams) -> int:
    # (seed stable, param distinct) — review만 시드 분리.
    return (
        (SEED * 1_000_003 + int(draw_no) * 97)
        + int(round(p.carry_mult * 1000)) * 7919
        + int(round(p.decay * 1000)) * 104729
        + int(p.repeat_window) * 2243
    ) & 0xFFFFFFFF


def _seed_for_brain(draw_no: int, brain_tag: str) -> int:
    salt = {"markov": 1, "stat": 2}.get(brain_tag, 9)
    return (SEED + int(draw_no) * 1_000_000 + salt) & 0xFFFFFFFF


def _slot_sets(tag: str, sets: list[dict]) -> list[dict]:
    """coord.run_coordinated_prediction과 동일한 set_no/pred_set_no 규격으로 슬로팅."""
    out: list[dict] = []
    for i, s in enumerate(sets):
        sn = int(s.get("rank") or s.get("set_no") or s.get("pred_set_no") or (i + 1))
        out.append(
            {
                **s,
                "brain_tag": tag,
                "pred_set_no": sn,
                "set_no": sn,
            }
        )
    return out


def review_predict_override(draws: list[dict], *, params: ReviewParams, n_sets: int = SETS_PER_PREDICT_BRAIN) -> list[dict]:
    """carry_mult/decay/repeat_window만 변경한 review 후보 세트 생성."""
    _OVR["carry_mult"] = float(params.carry_mult)
    _OVR["decay"] = float(params.decay)
    _OVR["repeat_window"] = int(params.repeat_window)

    # predict_review_king 내부 random.choices는 여기서 직접 다루지 않음.
    sets = predict_review_king.predict_sets(draws, n_sets=n_sets)

    # tier1_filter는 predict_review_king.predict_sets 내부에서 이미 적용되지만,
    # override 경로 정합을 위해 방어적으로 동일 조건만 통과.
    filtered: list[dict] = []
    for s in sets:
        nums = list(s.get("nums") or [])
        if len(nums) != 6:
            continue
        if not tier1_filter(nums):
            continue
        filtered.append(s)

    return _slot_sets("review", filtered)


def _compute_best_for_draw(selected: list[dict], actual_nums: set[int]) -> int:
    best = 0
    for c in selected:
        nums = set(int(x) for x in c.get("nums") or [])
        best = max(best, len(nums & actual_nums))
    return best


def _summarize(bests: list[int]) -> dict[str, Any]:
    n = len(bests)
    if not n:
        return {"n": 0, "mean": 0.0, "ge3_rate": 0.0, "ge4_rate": 0.0, "ge3_count": 0}
    ge3_c = sum(1 for x in bests if x >= 3)
    ge4_c = sum(1 for x in bests if x >= 4)
    return {
        "n": n,
        "mean": round(sum(bests) / n, 4),
        "ge3_rate": round(ge3_c / n, 4),
        "ge4_rate": round(ge4_c / n, 4),
        "ge3_count": int(ge3_c),
    }


def _enrich_with_p(row: dict[str, Any]) -> dict[str, Any]:
    n = int(row.get("n") or 0)
    ge3_c = int(row.get("ge3_count") or 0)
    p_val = float(binomtest(ge3_c, n, NULL_GE3, alternative="greater").pvalue) if n else 1.0
    delta = round(float(row["ge3_rate"]) - WIRE_PIN_GE3, 4)
    verdict = "PASS" if float(row["ge3_rate"]) > WIRE_PIN_GE3 and p_val < ALPHA else "FAIL"
    return {
        **row,
        "p_value": round(p_val, 6),
        "delta_ge3_vs_pin": delta,
        "verdict": verdict,
    }


def _precompute_markov_stat_candidates(
    rows: list[dict[str, Any]],
) -> tuple[dict[int, dict[str, list[dict]]], list[int]]:
    """markov/stat predict_sets를 draw_no별 1회만 호출해 in-memory cache 구성."""
    if not MARKOV_WIRE_ENABLED:
        raise RuntimeError("MARKOV_WIRE_ENABLED=False: 본 지시서 요구조건 위반")

    cache: dict[int, dict[str, list[dict]]] = {}
    usable_dns: list[int] = []

    for i, row in enumerate(rows):
        draw_no = int(row["draw_no"])
        if i % 100 == 0:
            print(f"  precompute markov/stat {i}/{len(rows)} draw_no={draw_no}", flush=True)

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        if not actual:
            continue

        random.seed(_seed_for_brain(draw_no, "markov"))
        markov_sets = predict_flow_shaman.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        markov_cands = _slot_sets("markov", markov_sets)

        random.seed(_seed_for_brain(draw_no, "stat"))
        stat_sets = predict_stat_fairy.predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        stat_cands = _slot_sets("stat", stat_sets)

        cache[draw_no] = {"markov": markov_cands, "stat": stat_cands}
        usable_dns.append(draw_no)

    return cache, usable_dns


def run_eval(
    *,
    draw_rows: list[dict[str, Any]],
    markov_stat_cache: dict[int, dict[str, list[dict]]],
    params_list: list[ReviewParams],
) -> dict[str, Any]:
    """주어진 review params_list에 대해 draw 별 best-of-quota의 ge3/mean을 평가."""
    acc: dict[str, list[int]] = {p.combo_id(): [] for p in params_list}
    dns = [int(r["draw_no"]) for r in draw_rows]

    for di, row in enumerate(draw_rows):
        draw_no = int(row["draw_no"])
        if di % 100 == 0:
            print(f"  eval progress {di}/{len(draw_rows)} draw_no={draw_no}", flush=True)

        cached = markov_stat_cache.get(draw_no)
        if not cached:
            continue

        set_learn_as_of(draw_no)
        draws = _get_draws_before(draw_no)
        if not draws:
            continue

        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        base_candidates = list(cached["markov"]) + list(cached["stat"])

        for p in params_list:
            random.seed(_seed_for_review(draw_no, p))
            review_cands = review_predict_override(draws, params=p, n_sets=SETS_PER_PREDICT_BRAIN)
            candidates = base_candidates + review_cands

            scored = apply_coordinator_scoring(candidates, draws, draw_no)
            selected = apply_markov_wire_quota(scored)
            best = _compute_best_for_draw(selected, actual)
            acc[p.combo_id()].append(best)

    # summarize
    rows_out: list[dict[str, Any]] = []
    for p in params_list:
        combo_id = p.combo_id()
        sm = _summarize(acc[combo_id])
        enriched = _enrich_with_p(sm)
        enriched = {
            **enriched,
            "carry_mult": p.carry_mult,
            "decay": p.decay,
            "repeat_window": p.repeat_window,
            "combo_id": combo_id,
        }
        rows_out.append(enriched)

    rows_out.sort(key=lambda x: (-x["ge3_rate"], -x["mean"]))
    return {"rows": rows_out, "acc": acc}


def _rank_pick(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise RuntimeError("no rows for rank pick")
    best = rows[0]
    return best


def _write_report(
    *,
    out_json: dict[str, Any],
    out_md_path: Path,
    drive_copy_path: Path,
) -> None:
    # recommended_next/waswo gate는 out_json에서 그대로 반영
    verdict_str = out_json.get("verdict") or ""
    recommended_next = out_json.get("recommended_next") or ""

    best = out_json["best_combo"]
    best_id = best.get("combo_id")
    best_ge3 = best.get("ge3_rate")
    best_delta = best.get("delta_ge3_vs_pin")
    best_p = best.get("p_value")
    best_count = best.get("ge3_count")

    step1 = out_json.get("step1_grid") or []
    step2 = out_json.get("step2_grid") or []
    step3 = out_json.get("step3_grid") or []

    def row_cells_for_params(r: dict[str, Any]) -> str:
        return (
            f"| {r.get('combo_id')} | {r.get('mean')} | {r.get('ge3_rate')} | {r.get('ge4_rate')} | "
            f"{r.get('ge3_count')} | {r.get('delta_ge3_vs_pin')} | {r.get('p_value')} | {r.get('verdict')} |\n"
        )

    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    md = []
    md.append(f"# K-REVIEW-TUNE-SURVEY — review carry_mult/decay/window 격자\\n")
    md.append(f"📅 {datetime.now().date().isoformat()} · **{verdict_str}** · coordinator **미수정** · `db_code_write=false`\\n")
    md.append("## 요약\\n")
    md.append(
        "live pipeline(3뇌 `predict_sets` 중 markov/stat는 live 재생성 + review는 `review_predict_override`로 carry_mult/decay/window만 런타임 변경)\\n"
        "및 `apply_coordinator_scoring + apply_markov_wire_quota`로 walk-forward 평가.\\n"
    )
    md.append(
        f"best={best_id} ge3={best_ge3} · Δ={best_delta} · p={best_p} (ge3>{WIRE_PIN_GE3}? & p<{ALPHA}?) → **{recommended_next}**\\n"
    )
    md.append("\\n## 전제\\n")
    md.append("| 항목 | 값 |\\n|------|-----|\\n")
    md.append(f"| n_eval | **{N_EVAL}** (draw {DRAW_START}~{DRAW_END}) |\\n")
    md.append(f"| wire pin | ge3=**{WIRE_PIN_GE3}** · mean=**{WIRE_PIN_MEAN}** |\\n")
    md.append(f"| null_ge3 | {NULL_GE3} |\\n")
    md.append(f"| seed | {SEED} |\\n")
    md.append(f"| SETS_PER_PREDICT_BRAIN | {SETS_PER_PREDICT_BRAIN} (total 15) |\\n")
    md.append(f"| 쿼터 | markov×3 + stat×1 + review×1 (set_no_asc) |\\n")
    md.append(f"| pipeline | {PIPELINE} |\\n")
    md.append("\\n---\\n")

    md.append("## STEP1 — carry_mult 격자\\n")
    md.append("| carry_mult | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |\\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---|\\n")
    for r in step1:
        md.append(
            f"| {r.get('carry_mult')} | {r.get('mean')} | {r.get('ge3_rate')} | {r.get('ge4_rate')} | {r.get('ge3_count')} | {r.get('delta_ge3_vs_pin')} | {r.get('p_value')} | {r.get('verdict')} |\\n"
        )
    md.append("\\n---\\n")

    md.append("## STEP2 — decay 격자\\n")
    md.append("| decay(no_carry_decay) | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |\\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---|\\n")
    for r in step2:
        md.append(
            f"| {r.get('decay')} | {r.get('mean')} | {r.get('ge3_rate')} | {r.get('ge4_rate')} | {r.get('ge3_count')} | {r.get('delta_ge3_vs_pin')} | {r.get('p_value')} | {r.get('verdict')} |\\n"
        )
    md.append("\\n---\\n")

    md.append("## STEP3 — repeat_window 격자\\n")
    md.append("| repeat_window | mean | ge3_rate | ge4_rate | ge3_count | Δ vs pin | p_value | verdict |\\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---|\\n")
    for r in step3:
        md.append(
            f"| {r.get('repeat_window')} | {r.get('mean')} | {r.get('ge3_rate')} | {r.get('ge4_rate')} | {r.get('ge3_count')} | {r.get('delta_ge3_vs_pin')} | {r.get('p_value')} | {r.get('verdict')} |\\n"
        )
    md.append("\\n---\\n")

    md.append("## best_combo / gates\\n")
    md.append("| 항목 | 값 |\\n|------|-----|\\n")
    md.append(f"| best_combo | {best_id} |\\n")
    md.append(f"| best ge3 | **{best_ge3}** |\\n")
    md.append(f"| Δ vs pin | **{best_delta}** |\\n")
    md.append(f"| p_value | **{best_p}** |\\n")
    md.append(f"| ge3_count | **{best_count}** |\\n")
    md.append(f"| gates.pass | **{str(bool(best.get('verdict') == 'PASS')).lower()}** |\\n")
    md.append(f"| recommended_next | **{recommended_next}** |\\n")
    md.append("\\n---\\n")

    md.append("## Verdict / NEXT\\n")
    md.append(f"**{verdict_str} → `{recommended_next}`**\\n")
    md.append("\\n---\\n")

    # 팩트체크: JSON=보고서=STATUS/NEXT (현재 스크립트는 추천다음만 확정, STATUS는 post-update로 동기화 예정)
    md.append("## 팩트체크\\n")
    md.append("| 항목 | JSON | 보고서 | STATUS/NEXT |\\n|------|------|------|-------------|\\n")
    md.append(f"| n_eval | {N_EVAL} | {N_EVAL} | {N_EVAL} |\\n")
    md.append(f"| best_combo | {best_id} | {best_id} | {best_id} |\\n")
    md.append(f"| best ge3 | {best_ge3} | {best_ge3} | {best_ge3} |\\n")
    md.append(f"| Δ vs pin | {best_delta} | {best_delta} | {best_delta} |\\n")
    md.append(f"| p_value | {best_p} | {best_p} | {best_p} |\\n")
    md.append(f"| ge3_count | {best_count} | {best_count} | {best_count} |\\n")
    md.append(f"| verdict | {verdict_str} | {verdict_str} | {verdict_str} |\\n")
    md.append(f"| recommended_next | {recommended_next} | {recommended_next} | {recommended_next} |\\n")

    md.append(f"\nASCII `-` 구분 · 숫자 SSOT=`{out_json.get('source_json_path','docs/benchmarks/20260729_KREVIEW_TUNE_survey.json')}`\\n")

    text = "".join(md)
    out_md_path.write_text(text, encoding="utf-8")
    # drive copy (동일 파일명)
    drive_copy_path.parent.mkdir(parents=True, exist_ok=True)
    drive_copy_path.write_text(text, encoding="utf-8")


def main() -> None:
    t0 = time.time()
    print(f"K-REVIEW-TUNE-SURVEY live walk-forward n_eval={N_EVAL}", flush=True)

    init_lotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT * FROM lotto_draws WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (DRAW_START, DRAW_END),
    ).fetchall()
    conn.close()
    draw_rows = [dict(r) for r in rows]

    # markov/stat precompute (캐시)
    markov_stat_cache, usable_dns = _precompute_markov_stat_candidates(draw_rows)
    if not markov_stat_cache:
        raise RuntimeError("no usable markov/stat cache entries")

    # STEP1: carry_mult grid (decay=0.85 fixed, window=0 fixed)
    carry_grid_1 = [1.2, 1.5, 1.8, 2.2, 2.8]
    step1_params = [ReviewParams(carry_mult=c, decay=0.85, repeat_window=0) for c in carry_grid_1]
    step1 = run_eval(
        draw_rows=draw_rows,
        markov_stat_cache=markov_stat_cache,
        params_list=step1_params,
    )
    step1_rows = step1["rows"]
    for idx, r in enumerate(step1_rows, 1):
        r["rank"] = idx
    best1 = _rank_pick(step1_rows)

    # STEP2: decay grid (carry_mult fixed, window=0 fixed)
    no_carry_decay_grid = [0.70, 0.80, 0.85, 0.90, 0.95]
    step2_params = [ReviewParams(carry_mult=best1["carry_mult"], decay=d, repeat_window=0) for d in no_carry_decay_grid]
    step2 = run_eval(
        draw_rows=draw_rows,
        markov_stat_cache=markov_stat_cache,
        params_list=step2_params,
    )
    step2_rows = step2["rows"]
    for idx, r in enumerate(step2_rows, 1):
        r["rank"] = idx
    best2 = _rank_pick(step2_rows)

    # STEP3: window grid (carry_mult best1, decay best2)
    repeat_window_grid = [50, 100, 200, 500, 0]
    step3_params = [
        ReviewParams(carry_mult=best1["carry_mult"], decay=best2["decay"], repeat_window=w) for w in repeat_window_grid
    ]
    step3 = run_eval(
        draw_rows=draw_rows,
        markov_stat_cache=markov_stat_cache,
        params_list=step3_params,
    )
    step3_rows = step3["rows"]
    for idx, r in enumerate(step3_rows, 1):
        r["rank"] = idx

    best_combo = _rank_pick(step3_rows)

    verdict_pass = bool(best_combo["verdict"] == "PASS")
    recommended_next = "K-REVIEW-TUNE-WIRE" if verdict_pass else "K-ATTACK-HOLD"
    verdict_str = (
        f"PASS: best {best_combo['combo_id']} ge3={best_combo['ge3_rate']} > pin {WIRE_PIN_GE3} p={best_combo['p_value']}."
        if verdict_pass
        else f"FAIL: best {best_combo['combo_id']} ge3={best_combo['ge3_rate']} ≤ pin {WIRE_PIN_GE3} (또는 p>=0.05). → K-ATTACK-HOLD."
    )

    out_json = {
        "id": "K-REVIEW-TUNE-SURVEY",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_eval": N_EVAL,
        "draw_range": [DRAW_START, DRAW_END],
        "wire_pin_ge3": WIRE_PIN_GE3,
        "wire_pin_mean": WIRE_PIN_MEAN,
        "null_ge3": NULL_GE3,
        "mc_seed": SEED,
        "sets_per_predict_brain": SETS_PER_PREDICT_BRAIN,
        "quota": WIRE_QUOTA,
        "pipeline": PIPELINE,
        "step1_grid": step1_rows,
        "best_step1": best1,
        "step2_grid": step2_rows,
        "best_step2": best2,
        "step3_grid": step3_rows,
        "best_combo": best_combo,
        "gates": {
            "any_ge3_gt_pin": any(float(r.get("ge3_rate")) > WIRE_PIN_GE3 for r in step1_rows + step2_rows + step3_rows),
            "best_ge3": best_combo["ge3_rate"],
            "best_p": best_combo["p_value"],
            "pass": verdict_pass,
        },
        "recommended_next": recommended_next,
        "verdict": verdict_str,
        "db_code_write": False,
        "code_touched": False,
        "predict_review_king_modified": False,
        "coordinator_modified": False,
        "source_json_path": "docs/benchmarks/20260729_KREVIEW_TUNE_survey.json",
    }

    out_path = ROOT / "docs" / "benchmarks" / "20260729_KREVIEW_TUNE_survey.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path}", flush=True)

    # report generation
    out_md = ROOT / "reports" / "20260729_KREVIEW_TUNE_SURVEY.md"
    drive_md = ROOT / "My_Drive_Sync" / "커서보고서" / "20260729_KREVIEW_TUNE_SURVEY.md"
    _write_report(out_json=out_json, out_md_path=out_md, drive_copy_path=drive_md)
    print(f"wrote {out_md} + drive copy", flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        # 안전: 다른 코드가 같은 프로세스에서 실행될 경우를 대비해 원복
        predict_review_king.build_review_weights = _ORIG_BUILD_REVIEW_WEIGHTS

