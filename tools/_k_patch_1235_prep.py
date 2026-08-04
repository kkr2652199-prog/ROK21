# -*- coding: utf-8 -*-
"""K-PATCH-1235-PREP — 1235 기반 패치 후보 진단 (wire 없음 · READ-ONLY).

SELECT-ONLY: lotto_draws / lotto_predictions / testlotto_pool_view_cache
Usage:
  python tools/_k_patch_1235_prep.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KPATCH_1235_PREP.json"
OUT_MD = ROOT / "reports" / "20260805_KPATCH_1235_PREP.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1036, 1235
TOP20 = [
    (11, 21),
    (1, 28),
    (10, 31),
    (6, 38),
    (33, 40),
    (25, 36),
    (6, 28),
    (12, 24),
    (34, 42),
    (10, 22),
    (19, 21),
    (5, 11),
    (8, 39),
    (3, 24),
    (2, 25),
    (3, 22),
    (37, 40),
    (5, 20),
    (14, 15),
    (3, 20),
]

# BC-MEASURE와 동일 정의
SUM_LOW = 116
SUM_HIGH = 160
SUM_TIER_P90 = 3  # BC-MEASURE sum_tier transition_threshold_p90


def sum_tier(s: int) -> str:
    if s < SUM_LOW:
        return "low"
    if s > SUM_HIGH:
        return "high"
    return "mid"


def hits(nums: list[int], actual: set[int]) -> int:
    return len(set(nums) & actual)


def ge3_rate(bests: list[int]) -> float:
    if not bests:
        return 0.0
    return round(sum(1 for b in bests if b >= 3) / len(bests), 6)


def signal_from_delta(delta: float) -> str:
    if delta >= 0.03:
        return "STRONG"
    if delta >= 0.01:
        return "MODERATE"
    if delta > 0:
        return "WEAK"
    return "WEAK"


def hamilton_counts(pct: dict[str, float], n: int = 5) -> dict[str, int]:
    """Largest remainder · 동률 시 stat > review > markov."""
    tags = ("stat", "markov", "review")
    priority = {"stat": 3, "review": 2, "markov": 1}
    raw = {t: n * float(pct[t]) / 100.0 for t in tags}
    floors = {t: int(raw[t]) for t in tags}
    rem = n - sum(floors.values())
    order = sorted(
        tags,
        key=lambda t: (raw[t] - floors[t], priority[t]),
        reverse=True,
    )
    out = dict(floors)
    for i in range(rem):
        out[order[i % len(order)]] += 1
    return out


def load_draws_all() -> list[dict[str, Any]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT draw_no, num1,num2,num3,num4,num5,num6
        FROM lotto_draws WHERE draw_no BETWEEN 1 AND 1235
        ORDER BY draw_no
        """
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        nums = sorted(int(d[f"num{k}"]) for k in range(1, 7))
        out.append(
            {
                "draw_no": int(d["draw_no"]),
                "nums": nums,
                "set": set(nums),
                "sum": sum(nums),
                "sum_tier": sum_tier(sum(nums)),
                "odd": sum(1 for x in nums if x % 2),
                "zone_low": sum(1 for x in nums if 1 <= x <= 15),
            }
        )
    return out


def load_fusion_preds(lo: int, hi: int) -> dict[int, list[dict[str, Any]]]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        """
        SELECT target_draw_no, brain_tag, num1,num2,num3,num4,num5,num6, matched_count
        FROM lotto_predictions
        WHERE target_draw_no BETWEEN ? AND ?
        ORDER BY target_draw_no, id
        """,
        (lo, hi),
    ).fetchall()
    conn.close()
    by: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        d = dict(r)
        dno = int(d["target_draw_no"])
        nums = [int(d[f"num{k}"]) for k in range(1, 7)]
        by.setdefault(dno, []).append(
            {
                "brain_tag": str(d.get("brain_tag") or ""),
                "nums": nums,
                "matched_count": d.get("matched_count"),
            }
        )
    return by


def load_repack_cache(lo: int, hi: int) -> dict[int, dict[str, list[list[int]]]]:
    from app.testlotto.pool_view_cache import get_cached_pool_view

    out: dict[int, dict[str, list[list[int]]]] = {}
    for dno in range(lo, hi + 1):
        pv = get_cached_pool_view(dno)
        if not pv:
            continue
        brains: dict[str, list[list[int]]] = {}
        for tag in ("stat", "markov", "review"):
            rep = pv.get("repack_by_brain", {}).get(tag) or []
            brains[tag] = [list(map(int, s["nums"])) for s in rep]
        out[dno] = brains
    return out


def cluster_count(nums: list[int]) -> int:
    s = set(nums)
    return sum(1 for a, b in TOP20 if a in s and b in s)


def run_len_before(tiers: list[str], idx: int) -> int:
    """tiers[idx] 직전( idx-1 끝) 동일 런 길이. idx=0 → 0."""
    if idx <= 0:
        return 0
    last = tiers[idx - 1]
    n = 0
    j = idx - 1
    while j >= 0 and tiers[j] == last:
        n += 1
        j -= 1
    return n


def measure_quota(
    draws_eval: list[dict],
    fusion: dict[int, list[dict]],
    cache: dict[int, dict[str, list[list[int]]]],
) -> dict[str, Any]:
    scenarios = {
        "A_stat0_markov80_review20": {"stat": 0, "markov": 80, "review": 20},
        "B_stat10_markov80_review10": {"stat": 10, "markov": 80, "review": 10},
        "C_stat20_markov70_review10": {"stat": 20, "markov": 70, "review": 10},
        "D_stat30_markov60_review10": {"stat": 30, "markov": 60, "review": 10},
    }
    slots = {k: hamilton_counts(v) for k, v in scenarios.items()}

    # A live = lotto_predictions fusion
    live_bests: list[int] = []
    for d in draws_eval:
        dno = d["draw_no"]
        actual = d["set"]
        preds = fusion.get(dno) or []
        if not preds:
            continue
        best = 0
        for p in preds:
            if p.get("matched_count") is not None and int(p["matched_count"]) >= 0:
                mc = int(p["matched_count"])
            else:
                mc = hits(p["nums"], actual)
            best = max(best, mc)
        live_bests.append(best)

    sim_ge3: dict[str, float] = {}
    sim_detail: dict[str, Any] = {}
    for key, pct in scenarios.items():
        caps = slots[key]
        bests: list[int] = []
        used_counts = Counter()
        for d in draws_eval:
            dno = d["draw_no"]
            actual = d["set"]
            brains = cache.get(dno)
            if not brains:
                continue
            selected: list[list[int]] = []
            for tag in ("stat", "markov", "review"):
                take = caps[tag]
                pool = brains.get(tag) or []
                selected.extend(pool[:take])
                used_counts[tag] += min(take, len(pool))
            if len(selected) < 5:
                # fill from markov then review then stat
                for tag in ("markov", "review", "stat"):
                    for nums in brains.get(tag) or []:
                        if len(selected) >= 5:
                            break
                        if nums not in selected:
                            selected.append(nums)
                    if len(selected) >= 5:
                        break
            best = max((hits(s, actual) for s in selected[:5]), default=0)
            bests.append(best)
        sim_ge3[key] = ge3_rate(bests)
        sim_detail[key] = {
            "slots": caps,
            "pct": pct,
            "n_draws": len(bests),
            "ge3_rate": sim_ge3[key],
            "mean_slots_used": {
                t: round(used_counts[t] / max(1, len(bests)), 4) for t in ("stat", "markov", "review")
            },
        }

    a_live = ge3_rate(live_bests)
    return {
        "quota_sim": {
            "A_stat0_markov80_review20": a_live,  # 현행 fusion DB SSOT
            "B_stat10_markov80_review10": sim_ge3["B_stat10_markov80_review10"],
            "C_stat20_markov70_review10": sim_ge3["C_stat20_markov70_review10"],
            "D_stat30_markov60_review10": sim_ge3["D_stat30_markov60_review10"],
        },
        "quota_sim_meta": {
            "A_source": "lotto_predictions fusion (brain_tag markov80/review20)",
            "A_live_ge3": a_live,
            "A_cache_sim_ge3": sim_ge3["A_stat0_markov80_review20"],
            "BCD_source": "testlotto_pool_view_cache repack_by_brain SELECT-ONLY",
            "slots": slots,
            "detail": sim_detail,
            "note": (
                "A는 발권 fusion DB. B/C/D는 캐시 뇌별 repack에서 슬롯 재조합 시뮬 "
                "(predictions에 stat=0이라 재할당 불가)"
            ),
        },
    }


def measure_pmi(draws_eval: list[dict], fusion: dict[int, list[dict]]) -> dict[str, Any]:
    buckets = {"0": [], "1": [], "ge2": []}
    for d in draws_eval:
        actual = d["set"]
        for p in fusion.get(d["draw_no"]) or []:
            cc = cluster_count(p["nums"])
            if p.get("matched_count") is not None and int(p["matched_count"]) >= 0:
                mc = int(p["matched_count"])
            else:
                mc = hits(p["nums"], actual)
            ge3 = 1 if mc >= 3 else 0
            if cc <= 0:
                buckets["0"].append(ge3)
            elif cc == 1:
                buckets["1"].append(ge3)
            else:
                buckets["ge2"].append(ge3)

    def pack(xs: list[int]) -> dict[str, Any]:
        n = len(xs)
        return {"n_sets": n, "ge3_rate": round(sum(xs) / n, 6) if n else 0.0}

    c0, c1, cg = pack(buckets["0"]), pack(buckets["1"]), pack(buckets["ge2"])
    delta = round(cg["ge3_rate"] - c0["ge3_rate"], 6)
    return {
        "cluster_0": c0,
        "cluster_1": c1,
        "cluster_ge2": cg,
        "delta_ge2_minus_0": delta,
        "signal": signal_from_delta(delta),
    }


def measure_sum_tier(
    draws_all: list[dict], draws_eval: list[dict], fusion: dict[int, list[dict]]
) -> dict[str, Any]:
    tiers = [d["sum_tier"] for d in draws_all]
    idx_by = {d["draw_no"]: i for i, d in enumerate(draws_all)}
    imm_bests: list[int] = []
    nor_bests: list[int] = []
    for d in draws_eval:
        i = idx_by[d["draw_no"]]
        run_before = run_len_before(tiers, i)
        preds = fusion.get(d["draw_no"]) or []
        if not preds:
            continue
        best = 0
        for p in preds:
            if p.get("matched_count") is not None and int(p["matched_count"]) >= 0:
                mc = int(p["matched_count"])
            else:
                mc = hits(p["nums"], d["set"])
            best = max(best, mc)
        if run_before >= SUM_TIER_P90:
            imm_bests.append(best)
        else:
            nor_bests.append(best)
    imm_g = ge3_rate(imm_bests)
    nor_g = ge3_rate(nor_bests)
    delta = round(imm_g - nor_g, 6)
    return {
        "imminent_n_draws": len(imm_bests),
        "imminent_ge3": imm_g,
        "normal_n_draws": len(nor_bests),
        "normal_ge3": nor_g,
        "delta": delta,
        "threshold_run": SUM_TIER_P90,
        "signal": signal_from_delta(delta),
    }


def dynamic_slot_top3(window: list[list[int]]) -> list[set[int]]:
    hist = [Counter() for _ in range(6)]
    for nums in window:
        for i, n in enumerate(nums):
            hist[i][n] += 1
    tops: list[set[int]] = []
    for c in hist:
        tops.append({n for n, _ in c.most_common(3)})
    return tops


def d_signal(nums: list[int], tops: list[set[int]]) -> int:
    sn = sorted(nums)
    return sum(1 for i, n in enumerate(sn) if n in tops[i])


def measure_d_dynamic(
    draws_all: list[dict], draws_eval: list[dict], fusion: dict[int, list[dict]]
) -> dict[str, Any]:
    by_no = {d["draw_no"]: d for d in draws_all}
    ge4: list[int] = []
    lt4: list[int] = []
    for d in draws_eval:
        dno = d["draw_no"]
        window_nums = []
        for prev in range(dno - 10, dno):
            pd = by_no.get(prev)
            if pd:
                window_nums.append(pd["nums"])
        if len(window_nums) < 10:
            continue
        tops = dynamic_slot_top3(window_nums)
        for p in fusion.get(dno) or []:
            score = d_signal(p["nums"], tops)
            if p.get("matched_count") is not None and int(p["matched_count"]) >= 0:
                mc = int(p["matched_count"])
            else:
                mc = hits(p["nums"], d["set"])
            ge3 = 1 if mc >= 3 else 0
            if score >= 4:
                ge4.append(ge3)
            else:
                lt4.append(ge3)
    g4 = round(sum(ge4) / len(ge4), 6) if ge4 else 0.0
    l4 = round(sum(lt4) / len(lt4), 6) if lt4 else 0.0
    delta = round(g4 - l4, 6)
    return {
        "d_ge4_n_sets": len(ge4),
        "d_ge4_ge3": g4,
        "d_lt4_n_sets": len(lt4),
        "d_lt4_ge3": l4,
        "d_delta": delta,
        "signal": signal_from_delta(delta),
    }


def build_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    base = payload["quota_sim"]["A_stat0_markov80_review20"]
    for key, ge3 in payload["quota_sim"].items():
        if key.startswith("A_"):
            continue
        delta = round(float(ge3) - float(base), 6)
        if delta >= 0.01:
            cands.append(
                {
                    "id": f"quota_{key}",
                    "axis": "quota_sim",
                    "delta_ge3": delta,
                    "ge3": ge3,
                    "base_ge3": base,
                    "wire_GO_required": True,
                    "note": "wire GO 필요 · quota 실변경 금지(현 측정만)",
                }
            )
    pmi = payload["pmi_cluster_ge3"]
    d_pmi = pmi.get("delta_ge2_minus_0", 0.0)
    if d_pmi >= 0.01:
        cands.append(
            {
                "id": "C_pmi_cluster_prefer_ge2",
                "axis": "pmi_cluster",
                "delta_ge3": d_pmi,
                "ge3_ge2": pmi["cluster_ge2"]["ge3_rate"],
                "ge3_0": pmi["cluster_0"]["ge3_rate"],
                "wire_GO_required": True,
                "note": "wire GO 필요 · cluster≥2 선호 필터 후보",
            }
        )
    st = payload["sum_tier_transition"]
    if st["delta"] >= 0.01:
        cands.append(
            {
                "id": "B_sum_tier_imminent",
                "axis": "sum_tier_transition",
                "delta_ge3": st["delta"],
                "imminent_ge3": st["imminent_ge3"],
                "normal_ge3": st["normal_ge3"],
                "wire_GO_required": True,
                "note": "wire GO 필요 · 전환임박 회차 정책 후보",
            }
        )
    dd = payload["D_dynamic"]
    if dd["d_delta"] >= 0.01:
        cands.append(
            {
                "id": "D_dynamic_slot_ge4",
                "axis": "D_dynamic",
                "delta_ge3": dd["d_delta"],
                "d_ge4_ge3": dd["d_ge4_ge3"],
                "d_lt4_ge3": dd["d_lt4_ge3"],
                "wire_GO_required": True,
                "note": "wire GO 필요 · 동적 슬롯 top3≥4 선호 후보",
            }
        )
    return cands


def write_md(p: dict[str, Any]) -> str:
    qs = p["quota_sim"]
    meta = p["quota_sim_meta"]
    lines = [
        "# K-PATCH-1235-PREP — 1235 기반 패치 준비 (2026-08-05)",
        "",
        f"- **판정:** `{p['verdict']}` · wire=`{p['wire']}` · n={p['n_draws']} ({p['draw_range'][0]}~{p['draw_range'][1]})",
        "- **금지:** engine/quota 실변경 · 발권 ge3 약속 · wire 무단",
        "",
        "## base_1235",
        "",
        f"```json\n{json.dumps(p['base_1235'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## 1) quota 시뮬",
        "",
        f"| 시나리오 | ge3 | Δ vs A |",
        f"|----------|-----|--------|",
    ]
    a = qs["A_stat0_markov80_review20"]
    for k, v in qs.items():
        lines.append(f"| {k} | **{v}** | {round(v - a, 6):+} |")
    lines += [
        "",
        f"- A 출처: {meta['A_source']} (live={meta['A_live_ge3']} · cache_sim={meta['A_cache_sim_ge3']})",
        f"- B/C/D 출처: {meta['BCD_source']}",
        f"- 슬롯: `{meta['slots']}`",
        f"- 메모: {meta['note']}",
        "",
        "## 2) C-PMI 클러스터 × 발권 ge3",
        "",
        f"```json\n{json.dumps(p['pmi_cluster_ge3'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## 3) B-sum_tier 전환임박",
        "",
        f"```json\n{json.dumps(p['sum_tier_transition'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## 4) D-동적 슬롯",
        "",
        f"```json\n{json.dumps(p['D_dynamic'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## patch_candidates (Δge3≥+0.01만)",
        "",
    ]
    if not p["patch_candidates"]:
        lines.append("_없음 — 전원 delta<+0.01 또는 역방향_")
    else:
        for c in p["patch_candidates"]:
            lines.append(
                f"- **{c['id']}** · Δ={c['delta_ge3']} · wire GO 필요 · {c.get('note','')}"
            )
    lines += [
        "",
        "## 산출물",
        "",
        f"- JSON: `docs/benchmarks/{OUT_JSON.name}`",
        f"- tool: `tools/_k_patch_1235_prep.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    draws_all = load_draws_all()
    draws_eval = [d for d in draws_all if LO <= d["draw_no"] <= HI]
    fusion = load_fusion_preds(LO, HI)
    cache = load_repack_cache(LO, HI)

    d1235 = next(d for d in draws_all if d["draw_no"] == 1235)
    idx = next(i for i, d in enumerate(draws_all) if d["draw_no"] == 1235)
    tiers = [d["sum_tier"] for d in draws_all]
    run_before = run_len_before(tiers, idx)
    prev_tier = tiers[idx - 1] if idx > 0 else None
    transition = prev_tier is not None and prev_tier != d1235["sum_tier"]

    q = measure_quota(draws_eval, fusion, cache)
    pmi = measure_pmi(draws_eval, fusion)
    st = measure_sum_tier(draws_all, draws_eval, fusion)
    dd = measure_d_dynamic(draws_all, draws_eval, fusion)

    payload: dict[str, Any] = {
        "id": "K-PATCH-1235-PREP",
        "ts": datetime.now(timezone.utc).isoformat(),
        "verdict": "MEASURED",
        "wire": False,
        "draw_range": [LO, HI],
        "n_draws": len(draws_eval),
        "base_1235": {
            "actual": d1235["nums"],
            "sum": d1235["sum"],
            "sum_tier": d1235["sum_tier"],
            "sum_tier_def": f"low<{SUM_LOW} / high>{SUM_HIGH} / else mid (BC-MEASURE)",
            "odd": d1235["odd"],
            "zone_low": d1235["zone_low"],
            "B_sum_tier_run_before": run_before,
            "B_transition_occurred": transition,
            "prev_sum_tier": prev_tier,
            "note_bg": "배경문구 sum=121(low)는 정의상 mid(116~160) — 실측 레이블 mid",
        },
        "quota_sim": q["quota_sim"],
        "quota_sim_meta": q["quota_sim_meta"],
        "pmi_cluster_ge3": pmi,
        "sum_tier_transition": st,
        "D_dynamic": dd,
        "patch_candidates": [],
        "forbid": [
            "random.choices",
            "_get_draws_before mutate",
            "engine.py",
            "auto-tune",
            "wire",
            "quota 실제 변경",
        ],
        "pass": True,
        "tool": "tools/_k_patch_1235_prep.py",
    }
    payload["patch_candidates"] = build_candidates(payload)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = write_md(payload)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        DRIVE.parent.mkdir(parents=True, exist_ok=True)
        DRIVE.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"drive copy skip: {e}", file=sys.stderr)

    print(
        json.dumps(
            {
                "ok": True,
                "quota_sim": payload["quota_sim"],
                "pmi": {
                    "0": pmi["cluster_0"]["ge3_rate"],
                    "1": pmi["cluster_1"]["ge3_rate"],
                    "ge2": pmi["cluster_ge2"]["ge3_rate"],
                    "signal": pmi["signal"],
                },
                "sum_tier": {
                    "imm": st["imminent_ge3"],
                    "nor": st["normal_ge3"],
                    "delta": st["delta"],
                },
                "D": {"ge4": dd["d_ge4_ge3"], "lt4": dd["d_lt4_ge3"], "delta": dd["d_delta"]},
                "candidates": [c["id"] for c in payload["patch_candidates"]],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
