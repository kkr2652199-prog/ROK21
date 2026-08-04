# -*- coding: utf-8 -*-
"""K-PAIR-COVER — 저출현쌍 covering survey (wire 없음 · as_of).

Usage:
  python tools/_k_pair_cover_survey.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260805_KPAIR_COVER_survey.json"
OUT_MD = ROOT / "reports" / "20260805_KPAIR_COVER_SURVEY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
LO, HI = 1035, 1234
NULL5 = 0.1137
PIN = 0.1447


def _hits(nums, actual) -> int:
    return len(set(int(x) for x in nums) & actual)


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pair_cover import PAIR_COVER_WIRE, select_pair_cover
    from app.testlotto.pool_view_cache import get_cached_pool_view_any_schema

    init_testlotto_db()
    conn = get_lotto_db()
    draws = {
        int(r["draw_no"]): {int(r[f"num{k}"]) for k in range(1, 7)}
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        )
    }
    conn.close()

    from itertools import combinations

    from app.testlotto.pair_cover import _pair_key, load_pair_freq_before

    # as_of 시작: LO 이전 히스토리 1회 로드 후 증분
    freq, _exp0, n_hist = load_pair_freq_before(LO)
    import math

    base_bests = {b: [] for b in BRAINS}
    cover_bests = {b: [] for b in BRAINS}
    rare_means = {b: [] for b in BRAINS}
    n_ok = 0

    for dno in range(LO, HI + 1):
        if dno not in draws:
            continue
        pv = get_cached_pool_view_any_schema(dno)
        if not pv or not pv.get("ok"):
            continue
        actual = draws[dno]
        exp = (n_hist * math.comb(6, 2) / math.comb(45, 2)) if n_hist else 0.0
        n_ok += 1
        for tag in BRAINS:
            pool = pv.get("pool_by_brain", {}).get(tag) or []
            repack = pv.get("repack_by_brain", {}).get(tag) or []
            if not pool or not repack:
                continue
            base_bests[tag].append(
                max((_hits(s["nums"], actual) for s in repack), default=0)
            )
            cands = [{**s, "kind": "pool"} for s in pool] + [
                {**s, "kind": "repack"} for s in repack
            ]
            picked = select_pair_cover(
                cands, dno, n_sets=5, freq=freq, exp=exp, n_hist=n_hist
            )
            cover_bests[tag].append(
                max((_hits(s["nums"], actual) for s in picked), default=0)
            )
            rare_means[tag].append(
                mean(float(s.get("pair_cover", {}).get("n_rare") or 0) for s in picked)
                if picked
                else 0.0
            )
        # 현재 회차를 다음 as_of에 반영
        nums = sorted(actual)
        for a, b in combinations(nums, 2):
            freq[_pair_key(a, b)] += 1
        n_hist += 1

    def pack(bests):
        n = len(bests)
        g = sum(1 for x in bests if x >= 3)
        rate = round(g / n, 4) if n else 0.0
        return {
            "n": n,
            "ge3_count": g,
            "ge3_rate": rate,
            "mean_best": round(mean(bests), 4) if bests else 0.0,
            "delta_vs_null": round(rate - NULL5, 4),
            "delta_vs_pin": round(rate - PIN, 4),
        }

    by_brain = {}
    for tag in BRAINS:
        b = pack(base_bests[tag])
        c = pack(cover_bests[tag])
        by_brain[tag] = {
            "baseline_repack": b,
            "pair_cover": c,
            "delta_ge3": round(c["ge3_rate"] - b["ge3_rate"], 4),
            "mean_n_rare_in_picked": round(mean(rare_means[tag]), 4)
            if rare_means[tag]
            else 0.0,
        }

    wire_brains = [t for t in BRAINS if by_brain[t]["delta_ge3"] >= 0.01]
    if wire_brains:
        verdict = "GO-WAIT"
    elif all(by_brain[t]["delta_ge3"] <= 0 for t in BRAINS):
        verdict = "HOLD"
    else:
        verdict = "WATCH"

    payload = {
        "id": "K-PAIR-COVER",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": "survey",
        "wire": False,
        "PAIR_COVER_WIRE_live": PAIR_COVER_WIRE,
        "draw_range": [LO, HI],
        "n_draws": n_ok,
        "axis": "low-frequency pair covering (as_of)",
        "warrant_ref": "20260805_KMATH_PATTERN_WARRANT.json#W-PAIR-COVERING",
        "by_brain": by_brain,
        "verdict": {
            "label": verdict,
            "wire_brains": wire_brains,
            "next": (
                f"pair_cover wire GO-WAIT ({','.join(wire_brains)}) · 형 GO"
                if wire_brains
                else "PAIR_COVER HOLD · AUTO설계문서 또는 다른축 · 형 GO"
            ),
        },
        "pass": True,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-PAIR-COVER — 저출현쌍 covering survey",
        "",
        f"📅 {payload['ts'][:10]} · **{verdict}** · wire=**False** · n=**{n_ok}** ({LO}~{HI})",
        "",
        "## 0) 한 줄",
        "",
        "as_of 쌍빈도로 희소쌍을 많이·다양하게 담는 5장 재선정. "
        "컨닝 없음 · 1등확률 보증 아님.",
        "",
        "## 1) 결과",
        "",
        "| 뇌 | baseline | pair_cover | Δ | mean n_rare |",
        "|----|----------:|-----------:|---:|------------:|",
    ]
    for tag in BRAINS:
        r = by_brain[tag]
        lines.append(
            f"| {tag} | {r['baseline_repack']['ge3_rate']:.4f} | "
            f"{r['pair_cover']['ge3_rate']:.4f} | {r['delta_ge3']:+.4f} | "
            f"{r['mean_n_rare_in_picked']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## 2) 설계 (`pair_cover.py`)",
            "",
            "- 쌍빈도: `draw < target` only",
            "- rare = 기대출현 대비 deficit 상위 80쌍",
            "- 탐욕: 새 희소쌍 커버 + 세트 희소점수",
            "- `PAIR_COVER_WIRE=False`",
            "",
            f"## 3) 판정 **{verdict}**",
            "",
            f"- wire 후보: {wire_brains or '없음'}",
            f"- 다음: {payload['verdict']['next']}",
            "",
            f"근거: `{OUT_JSON.name}`",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n": n_ok,
                "by_brain": {
                    t: {
                        "base": by_brain[t]["baseline_repack"]["ge3_rate"],
                        "cover": by_brain[t]["pair_cover"]["ge3_rate"],
                        "d": by_brain[t]["delta_ge3"],
                    }
                    for t in BRAINS
                },
                "wire_brains": wire_brains,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
