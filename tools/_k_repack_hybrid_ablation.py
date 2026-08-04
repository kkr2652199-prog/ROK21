# -*- coding: utf-8 -*-
"""K-REPACK-HYBRID — pool+몰아주기 조립 ablation (READ-ONLY · wire 없음).

캐시된 pool_view(뇌당 pool10 + repack5)로 best_of_5 ge3 비교.
oracle은 상한 참조만 · 배포 가능 전략과 분리.

Usage:
  python tools/_k_repack_hybrid_ablation.py
  python tools/_k_repack_hybrid_ablation.py --start 1035 --end 1234
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KREPACK_HYBRID_survey.json"
OUT_MD = ROOT / "reports" / "20260804_KREPACK_HYBRID_SURVEY.md"
DRIVE_MD = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAIN_TAGS = ["stat", "markov", "review"]
BRAIN_KO = {"stat": "1뇌·통계요정", "markov": "2뇌·흐름술사", "review": "3뇌·복습왕"}
PIN = 0.1447
NULL5 = 0.1137


def _hits(nums: list[int], actual: set[int]) -> int:
    return len(set(int(x) for x in nums) & actual)


def _key(nums: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _load_draws(lo: int, hi: int) -> dict[int, dict]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no, num1,num2,num3,num4,num5,num6 FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (lo, hi),
    ).fetchall()
    conn.close()
    out: dict[int, dict] = {}
    for r in rows:
        d = dict(r)
        nums = [int(d[f"num{k}"]) for k in range(1, 7)]
        out[int(d["draw_no"])] = {"actual": set(nums), "nums": nums}
    return out


def _norm_pool(pool: list[dict]) -> list[dict]:
    return [
        {
            "set_no": int(p.get("set_no") or i + 1),
            "nums": [int(x) for x in p["nums"]],
            "kind": "pool",
        }
        for i, p in enumerate(sorted(pool, key=lambda x: int(x.get("set_no") or 0)))
    ]


def _norm_repack(repack: list[dict]) -> list[dict]:
    return [
        {
            "set_no": int(r.get("set_no") or i + 1),
            "nums": [int(x) for x in r["nums"]],
            "kind": "repack",
        }
        for i, r in enumerate(sorted(repack, key=lambda x: int(x.get("set_no") or 0)))
    ]


def _pool_freq(pool: list[dict]) -> Counter[int]:
    cnt: Counter[int] = Counter()
    for p in pool:
        for n in p["nums"]:
            cnt[int(n)] += 1
    return cnt


def _set_freq_score(pool: list[dict], nums: list[int]) -> float:
    freq = _pool_freq(pool)
    return float(sum(freq[int(n)] for n in nums))


def _by_set_nos(sets: list[dict], nos: list[int]) -> list[dict]:
    want = set(nos)
    return [s for s in sets if int(s["set_no"]) in want]


def _top_pool_by_freq(pool: list[dict], k: int) -> list[dict]:
    ranked = sorted(
        pool,
        key=lambda s: (-_set_freq_score(pool, s["nums"]), int(s["set_no"])),
    )
    return ranked[:k]


def _assemble(primary: list[dict], fillers: list[dict], n: int = 5) -> list[dict]:
    """순서대로 unique 세트 n장 조립."""
    out: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for s in list(primary) + list(fillers):
        k = _key(s["nums"])
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
        if len(out) >= n:
            break
    return out


def build_strategies(
    pool: list[dict], repack: list[dict], brain: str
) -> dict[str, list[dict]]:
    """전략명 → 최대 5세트 (배포가능 + oracle 참조)."""
    r_by = {int(r["set_no"]): r for r in repack}
    p_by = {int(p["set_no"]): p for p in pool}

    def R(*ranks: int) -> list[dict]:
        return [r_by[i] for i in ranks if i in r_by]

    def P(*nos: int) -> list[dict]:
        return [p_by[i] for i in nos if i in p_by]

    freq2 = _top_pool_by_freq(pool, 2)
    freq3 = _top_pool_by_freq(pool, 3)

    strategies: dict[str, list[dict]] = {
        "baseline_repack": _assemble(R(1, 2, 3, 4, 5), []),
        "pool_asc_1_5": _assemble(P(1, 2, 3, 4, 5), pool),
        "pool_late_6_10": _assemble(P(6, 7, 8, 9, 10), pool),
        "hy_freq2_r123": _assemble(freq2 + R(1, 2, 3), R(4, 5) + pool),
        "hy_freq2_r145": _assemble(freq2 + R(1, 4, 5), R(2, 3) + pool),
        "hy_freq2_r13_r2": _assemble(freq2 + R(1, 3, 2), R(4) + pool),  # skip r5
        "hy_p45_r123": _assemble(P(4, 5) + R(1, 2, 3), R(4, 5) + pool),
        "hy_p89_r145": _assemble(P(8, 9) + R(1, 4, 5), R(2, 3) + pool),
        "hy_freq3_r12": _assemble(freq3 + R(1, 2), R(3, 4, 5) + pool),
        # oracle upper bound (배포 금지)
        "oracle_best_pool1": [],  # filled below
    }

    # oracle: 실제 적중 최댓값 1세트 — 호출측에서 actual 넣어 채움
    # brain-tuned recommendation (데이터 근거 고정 규칙)
    if brain == "stat":
        # pool4+5 ge3 높음(DECOMPOSE) + 몰1~3
        strategies["hy_brain_rec"] = _assemble(P(4, 5) + R(1, 2, 3), R(4, 5) + pool)
    elif brain == "markov":
        # rank 역전 대비 몰1/4/5 + 후반 pool
        strategies["hy_brain_rec"] = _assemble(P(8, 9) + R(1, 4, 5), R(2, 3) + pool)
    else:
        # ablation: review는 freq2보다 p45+r123이 우세 → 동일 조립 채택
        strategies["hy_brain_rec"] = _assemble(P(4, 5) + R(1, 2, 3), R(4, 5) + pool)

    return strategies


def _oracle_best_pool(pool: list[dict], actual: set[int]) -> list[dict]:
    if not pool:
        return []
    best = max(pool, key=lambda s: (_hits(s["nums"], actual), -int(s["set_no"])))
    # pad with next-best for best_of_5 fairness? oracle = 1 ticket ceiling as ge3 of that one
    # For fair best_of_5 compare, use best 5 pool sets by hits (still oracle)
    ranked = sorted(pool, key=lambda s: (-_hits(s["nums"], actual), int(s["set_no"])))
    return _assemble(ranked[:5], [])


def _best_of(tickets: list[dict], actual: set[int]) -> int:
    if not tickets:
        return 0
    return max(_hits(t["nums"], actual) for t in tickets)


def run(lo: int, hi: int) -> dict[str, Any]:
    from app.testlotto.pool_view_cache import get_cached_pool_view
    from tools.bench_quick_gate import enrich_metrics, null_for_eval_mode

    draws = _load_draws(lo, hi)
    null_meta = null_for_eval_mode("best_of_5")

    # strategy -> brain -> list of best hits
    hits: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    missing: list[int] = []
    n_ok = 0
    composition_samples: dict[str, dict[str, Any]] = {}

    for dno in range(lo, hi + 1):
        if dno not in draws:
            continue
        pv = get_cached_pool_view(dno)
        if not pv or not pv.get("ok"):
            missing.append(dno)
            continue
        actual = draws[dno]["actual"]
        n_ok += 1
        for brain in BRAIN_TAGS:
            pool = _norm_pool(pv.get("pool_by_brain", {}).get(brain, []))
            repack = _norm_repack(pv.get("repack_by_brain", {}).get(brain, []))
            if len(pool) < 5 or len(repack) < 5:
                continue
            strats = build_strategies(pool, repack, brain)
            strats["oracle_best_pool5"] = _oracle_best_pool(pool, actual)
            for name, tickets in strats.items():
                if name == "oracle_best_pool1":
                    continue
                b = _best_of(tickets, actual)
                hits[name][brain].append(b)
                if dno == lo + 50 and brain == "markov" and name in (
                    "baseline_repack",
                    "hy_brain_rec",
                    "hy_freq2_r123",
                ):
                    composition_samples.setdefault(name, {})[brain] = {
                        "draw_no": dno,
                        "tickets": [
                            {
                                "kind": t["kind"],
                                "set_no": t["set_no"],
                                "nums": t["nums"],
                                "hits": _hits(t["nums"], actual),
                            }
                            for t in tickets
                        ],
                    }

    strategies_out: dict[str, Any] = {}
    for name, by_b in hits.items():
        row: dict[str, Any] = {
            "deployable": not name.startswith("oracle"),
            "by_brain": {},
        }
        for brain in BRAIN_TAGS:
            bests = by_b.get(brain, [])
            n = len(bests)
            if n == 0:
                continue
            ge3 = sum(1 for x in bests if x >= 3)
            m = mean(bests)
            gate = enrich_metrics(ge3, n, m, gate_mode="quick", eval_mode="best_of_5")
            row["by_brain"][brain] = {
                "label": BRAIN_KO[brain],
                "n_eval": n,
                "ge3_count": ge3,
                "ge3_rate": round(ge3 / n, 4),
                "mean": round(m, 4),
                "delta_vs_null": round(ge3 / n - NULL5, 4),
                "delta_vs_pin": round(ge3 / n - PIN, 4),
                "delta_vs_baseline": None,  # fill later
                "gate": gate,
            }
        strategies_out[name] = row

    # deltas vs baseline
    for name, row in strategies_out.items():
        for brain in BRAIN_TAGS:
            b = row["by_brain"].get(brain)
            base = strategies_out.get("baseline_repack", {}).get("by_brain", {}).get(brain)
            if b and base:
                b["delta_vs_baseline"] = round(b["ge3_rate"] - base["ge3_rate"], 4)

    # pick winners
    winners: dict[str, Any] = {}
    for brain in BRAIN_TAGS:
        ranked = []
        for name, row in strategies_out.items():
            if not row.get("deployable"):
                continue
            b = row["by_brain"].get(brain)
            if not b:
                continue
            ranked.append((name, b["ge3_rate"], b.get("delta_vs_baseline") or 0.0))
        ranked.sort(key=lambda x: (-x[1], -x[2], x[0]))
        winners[brain] = {
            "best_deployable": ranked[0][0] if ranked else None,
            "best_ge3": ranked[0][1] if ranked else None,
            "baseline_ge3": strategies_out["baseline_repack"]["by_brain"][brain]["ge3_rate"],
            "top3": [
                {"strategy": n, "ge3_rate": g, "delta_vs_baseline": d} for n, g, d in ranked[:3]
            ],
        }

    # recommended pack (brain_rec)
    rec = {
        "stat": "hy_p45_r123 (pool4+5 + 몰1~3)",
        "markov": "hy_p89_r145 또는 baseline_repack (동률·보수적으로 baseline 유지 가능)",
        "review": "hy_p45_r123 (pool4+5 + 몰1~3) — freq2보다 ablation 우세",
        "note": "1차 가설 후 ablation으로 review 권고 정정 · wire 전",
    }

    payload = {
        "id": "K-REPACK-HYBRID",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "cache_readonly_ablation",
        "wire": False,
        "eval_mode": "best_of_5",
        "draw_range": [lo, hi],
        "n_eval": n_ok,
        "missing_cache_n": len(missing),
        "missing_cache_sample": missing[:20],
        "null_ge3": NULL5,
        "wire_pin_ge3": PIN,
        "null_meta": null_meta,
        "strategy_defs": {
            "baseline_repack": "현행 몰아주기 rank1~5",
            "pool_asc_1_5": "pool set 1~5 그대로",
            "pool_late_6_10": "pool set 6~10 그대로",
            "hy_freq2_r123": "freq상위 pool2 + 몰1~3",
            "hy_freq2_r145": "freq상위 pool2 + 몰1/4/5",
            "hy_freq2_r13_r2": "freq상위 pool2 + 몰1/2/3 (몰5 제외)",
            "hy_p45_r123": "pool4+5 + 몰1~3",
            "hy_p89_r145": "pool8+9 + 몰1/4/5",
            "hy_freq3_r12": "freq상위 pool3 + 몰1~2",
            "hy_brain_rec": "뇌별 권고 조립(stat=p45+r123, markov=p89+r145, review=freq2+r123)",
            "oracle_best_pool5": "pool 적중순 상위5 (상한·배포금지)",
        },
        "brain_recommendation": rec,
        "winners": winners,
        "strategies": strategies_out,
        "composition_samples": composition_samples,
        "verdict": {
            "any_deployable_beats_baseline": any(
                (winners[b]["best_ge3"] or 0) > (winners[b]["baseline_ge3"] or 0)
                for b in BRAIN_TAGS
            ),
            "hy_brain_rec_vs_baseline": {
                b: strategies_out.get("hy_brain_rec", {})
                .get("by_brain", {})
                .get(b, {})
                .get("delta_vs_baseline")
                for b in BRAIN_TAGS
            },
        },
    }
    return payload


def write_report(payload: dict[str, Any]) -> str:
    lines = [
        "# K-REPACK-HYBRID — pool+몰아주기 조립 ablation",
        "",
        f"`{payload['ts']}` · n={payload['n_eval']} · {payload['draw_range'][0]}~{payload['draw_range'][1]} · **wire 없음**",
        "",
        "## 0. 한 줄",
        "",
    ]
    vs = payload["verdict"]["hy_brain_rec_vs_baseline"]
    lines.append(
        "뇌별 권고 hybrid(`hy_brain_rec`) vs 현행 몰아주기 Δge3: "
        + " · ".join(
            f"{BRAIN_KO[b]} **{vs.get(b):+.4f}**" if vs.get(b) is not None else f"{BRAIN_KO[b]} 미확인"
            for b in BRAIN_TAGS
        )
    )
    lines.extend(
        [
            "",
            f"- 배포가능 전략이 baseline을 이긴 뇌 존재: **{payload['verdict']['any_deployable_beats_baseline']}**",
            f"- null5={NULL5} · pin={PIN}",
            "",
            "## 1. 전략 정의",
            "",
            "| ID | 내용 | 배포 |",
            "|----|------|------|",
        ]
    )
    for k, v in payload["strategy_defs"].items():
        dep = "금지" if k.startswith("oracle") else "OK"
        lines.append(f"| `{k}` | {v} | {dep} |")

    lines.extend(["", "## 2. 뇌×전략 ge3_rate", ""])
    # table header
    strat_names = [
        "baseline_repack",
        "hy_brain_rec",
        "hy_freq2_r123",
        "hy_freq2_r145",
        "hy_p45_r123",
        "hy_p89_r145",
        "hy_freq3_r12",
        "pool_asc_1_5",
        "pool_late_6_10",
        "oracle_best_pool5",
    ]
    lines.append("| 전략 | stat | markov | review |")
    lines.append("|------|-----:|-------:|-------:|")
    for name in strat_names:
        row = payload["strategies"].get(name)
        if not row:
            continue
        cells = []
        for b in BRAIN_TAGS:
            bb = row["by_brain"].get(b, {})
            g = bb.get("ge3_rate")
            d = bb.get("delta_vs_baseline")
            if g is None:
                cells.append("—")
            elif name == "baseline_repack":
                cells.append(f"**{g:.4f}**")
            else:
                cells.append(f"{g:.4f} ({d:+.4f})" if d is not None else f"{g:.4f}")
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")

    lines.extend(["", "## 3. 뇌별 승자 (배포가능)", ""])
    for b in BRAIN_TAGS:
        w = payload["winners"][b]
        lines.append(f"### {BRAIN_KO[b]}")
        lines.append(
            f"- baseline **{w['baseline_ge3']}** → best `{w['best_deployable']}` **{w['best_ge3']}**"
        )
        for t in w["top3"]:
            lines.append(
                f"  - `{t['strategy']}` ge3={t['ge3_rate']} Δ={t['delta_vs_baseline']:+.4f}"
            )
        lines.append("")

    lines.extend(
        [
            "## 4. 해석 · 다음 wire 후보",
            "",
            "- oracle_best_pool5는 **상한** — 선택기 없이는 달성 불가",
            "- `hy_brain_rec`가 baseline 대비 양수면 해당 뇌 조립 패치 GO 가치",
            "- 전뇌 음수면 가중(W_*)·predict 측으로 축 이동",
            "- fusion(markov80%)은 markov 승자 전략을 FULL-first로 재검증",
            "",
            "## 근거",
            "",
            "- PER_BRAIN / DECOMPOSE / PIN-GAP 진단",
            "- pool_view_cache · coordinator wire 없음",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1035)
    ap.add_argument("--end", type=int, default=1234)
    args = ap.parse_args()

    print(f"K-REPACK-HYBRID {args.start}~{args.end} ...", flush=True)
    payload = run(args.start, args.end)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    DRIVE_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = write_report(payload)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE_MD.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_JSON}", flush=True)
    print(f"Wrote {OUT_MD}", flush=True)
    print("winners=", json.dumps(payload["winners"], ensure_ascii=False), flush=True)
    print("hy_brain_rec Δ=", payload["verdict"]["hy_brain_rec_vs_baseline"], flush=True)


if __name__ == "__main__":
    main()
