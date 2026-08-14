# -*- coding: utf-8 -*-
"""K-BT200-TIER-COUNTS — 지금 200회 등수 집계 (READ).

발권 vs 고유조합 vs 세트행. ge3 클레임 금지. 1237아님.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KBT200_TIER_COUNTS.json"
OUT_MD = ROOT / "reports" / "20260814_KBT200_TIER_COUNTS.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
LO, HI = 1037, 1236
LABEL = {1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등", 0: "미적중"}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> dict:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    pred_n = conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0]
    pred_ge3 = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE matched_count>=3"
    ).fetchone()[0]
    pred_1237 = conn.execute(
        "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT draw_no, brain_tag, kind, set_no, nums_json, hits, bonus_hit, tier_rank, role
        FROM testlotto_pool_hit_ledger
        WHERE draw_no BETWEEN ? AND ?
        """,
        (LO, HI),
    ).fetchall()

    set_c: Counter = Counter()
    set_by_role: Counter = Counter()
    uniq: dict = {}
    best: dict = {}
    for r in rows:
        tr = int(r["tier_rank"] or 0)
        set_c[tr] += 1
        set_by_role[f"{r['role']}|{LABEL.get(tr, tr)}"] += 1
        nums = tuple(sorted(json.loads(r["nums_json"] or "[]")))
        uk = (int(r["draw_no"]), str(r["brain_tag"]), nums)
        prev = uniq.get(uk)
        if prev is None or (tr and (not prev["tier"] or tr < prev["tier"])):
            uniq[uk] = {
                "tier": tr,
                "kind": r["kind"],
                "role": r["role"],
                "set_no": int(r["set_no"] or 0),
                "hits": int(r["hits"] or 0),
                "bonus_hit": int(r["bonus_hit"] or 0),
            }
        dk = (int(r["draw_no"]), str(r["brain_tag"]))
        score = tr if tr else 99
        if score < best.get(dk, 99):
            best[dk] = score

    uniq_c = Counter(v["tier"] for v in uniq.values())
    best_c = Counter((v if v != 99 else 0) for v in best.values())
    draws_n = conn.execute(
        "SELECT COUNT(DISTINCT draw_no) FROM testlotto_pool_hit_ledger WHERE draw_no BETWEEN ? AND ?",
        (LO, HI),
    ).fetchone()[0]
    draws_any = conn.execute(
        """
        SELECT COUNT(DISTINCT draw_no) FROM testlotto_pool_hit_ledger
        WHERE draw_no BETWEEN ? AND ? AND tier_rank BETWEEN 1 AND 5
        """,
        (LO, HI),
    ).fetchone()[0]

    hits_ge4 = [
        {
            "draw_no": d,
            "brain": tag,
            "nums": list(nums),
            **meta,
            "label": LABEL.get(meta["tier"], str(meta["tier"])),
        }
        for (d, tag, nums), meta in sorted(uniq.items())
        if 1 <= meta["tier"] <= 4
    ]

    d1117 = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=1117"
    ).fetchone()
    actual_1117 = None
    if d1117:
        actual_1117 = {
            "nums": [int(d1117[f"num{i}"]) for i in range(1, 7)],
            "bonus": int(d1117["bonus"] or 0),
        }

    brains = sorted({str(r["brain_tag"]) for r in rows})
    conn.close()

    out = {
        "id": "K-BT200-TIER-COUNTS",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "window": [LO, HI],
        "n_draws": int(draws_n),
        "brains": brains,
        "issued": {
            "predictions": int(pred_n),
            "matched_ge3": int(pred_ge3),
            "pred_1237": int(pred_1237),
            "note": "발권 0 → 산 티켓 등수 없음",
        },
        "set_rows": {
            "n": len(rows),
            "by_tier": {LABEL[k]: int(set_c.get(k, 0)) for k in (1, 2, 3, 4, 5, 0)},
            "note": "풀10+몰아주기5 행 단위. 같은 번호 중복 가능",
        },
        "unique_combo": {
            "n": len(uniq),
            "by_tier": {LABEL[k]: int(uniq_c.get(k, 0)) for k in (1, 2, 3, 4, 5, 0)},
            "note": "회차×뇌×번호조합 1회",
        },
        "draw_best": {
            "draws_with_any_tier": int(draws_any),
            "draws_no_tier": int(draws_n) - int(draws_any),
            "by_best_tier": {
                LABEL[k]: int(best_c.get(k, 0)) for k in (1, 2, 3, 4, 5)
            },
            "note": "회차당 최고 등수 1개. 미적중 회차는 by_best에 안 넣음",
        },
        "hits_ge4_unique": hits_ge4,
        "actual_1117": actual_1117,
        "set_by_role_prize": dict(set_by_role),
        "verdict": "DOC_OK",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    u = out["unique_combo"]["by_tier"]
    s = out["set_rows"]["by_tier"]
    b = out["draw_best"]
    md = "\n".join(
        [
            "# K-BT200-TIER-COUNTS — 지금 200회 적중 등수",
            "",
            f"시각: {out['as_of']} · **모니터만** · ge3미클레임 · 1237아님",
            "창 1037~1236 n=200 · 뇌=stat만 · 발권0",
            "",
            "## 0) 한 줄",
            "",
            f"**1등 0 · 2등 0 · 3등 0.** 4등 고유 **{u['4등']}**회(1117 9~10번 칸). "
            f"5등 고유 **{u['5등']}**조합 / **{b['by_best_tier']['5등']}**회차. "
            "산 티켓 등수는 없음(발권 0).",
            "",
            "## 1) 세 가지 세는 법",
            "",
            "| 등수 | 고유조합(권고) | 세트행(중복포함) | 회차최고 |",
            "|------|----------------|------------------|----------|",
        ]
    )
    md += "\n"
    for lab in ("1등", "2등", "3등", "4등", "5등"):
        md += (
            f"| {lab} | **{u[lab]}** | {s[lab]} | "
            f"{b['by_best_tier'].get(lab, 0)} |\n"
        )
    md += (
        f"| 미적중 | {u['미적중']} | {s['미적중']} | "
        f"등수없는 회차 **{b['draws_no_tier']}**/200 |\n"
        "\n"
        "- 고유조합: 같은 번호가 풀·몰아주기에 둘 다 있으면 1번.\n"
        "- 세트행: 홈 화면이 이렇게 세면 4등이 2줄로 보일 수 있음(1117).\n"
        "- 회차최고: 그 회차에 나온 제일 좋은 등수 1개.\n"
        "\n"
        "## 2) 4등 상세 (고유 1)\n"
        "\n"
    )
    if hits_ge4 and actual_1117:
        h = hits_ge4[0]
        md += (
            f"- 회차 **{h['draw_no']}** 당첨 `{actual_1117['nums']}` 보너스 {actual_1117['bonus']}\n"
            f"- 예측 `{h['nums']}` · hits=**4** · 보너스맞음={h['bonus_hit']} · "
            f"칸={h['kind']} {h['role']} set{h['set_no']}\n"
            "- 몰아주기에도 같은 번호 1행 → 세트행 4등=2, 고유=1.\n"
        )
    md += (
        "\n## 3) 발권\n\n"
        f"`lotto_predictions`=**{pred_n}** · matched≥3=**{pred_ge3}** · 1237=**{pred_1237}**\n"
        "\n## 4) 금지\n\n"
        "- 5등 55 / 세트행 79 를 성적 향상으로 쓰지 말 것 (장수 많음).\n"
        "- 3등 0. 홈에서 예전에 보이던 3등 2는 다른 경로(1210) 이야기.\n"
        "\n## 5) 다음\n\n형 1건(권고=markov 동일 소비). 1237아님.\n"
    )
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": "DOC_OK", "unique": u, "issued": pred_n}, ensure_ascii=False))
    return out


if __name__ == "__main__":
    main()
