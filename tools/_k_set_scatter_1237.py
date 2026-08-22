# -*- coding: utf-8 -*-
"""K-SET-SCATTER-1237 — 1237회 세트별 번호 선택·적중 분산 READ-ONLY."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lotto_testlotto.db"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KSET_SCATTER_1237.json"
OUT_MD = ROOT / "reports" / "20260822_KSET_SCATTER_1237.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
BRAINS = ("stat", "markov", "review")
ROLE = {
    1: "skill_native",
    2: "skill_native",
    3: "skill_native",
    4: "skill_native",
    5: "skill_native",
    6: "cover_r3",
    7: "cover_r3",
    8: "cover_r3",
    9: "shape_r2",
    10: "shape_r2",
}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s) -> list[int]:
    if isinstance(s, dict) and s.get("nums"):
        return [int(x) for x in s["nums"]]
    return []


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dr = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=1237"
    ).fetchone()
    actual = [int(dr[i]) for i in range(6)] if dr else []
    bonus = int(dr[6]) if dr else 0
    win = set(actual)
    by: dict = {}
    for tag in BRAINS:
        row = conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache WHERE brain=? AND draw_no=1237",
            (tag,),
        ).fetchone()
        if not row:
            by[tag] = None
            continue
        pool = json.loads(row["pool_json"] or "[]")
        repack = json.loads(row["repack_json"] or "[]")
        pool_rows = []
        hit_union: set[int] = set()
        for i, s in enumerate(pool):
            nums = _nums(s)
            hits = sorted(set(nums) & win)
            hit_union.update(hits)
            sn = int(s.get("set_no") or s.get("pred_set_no") or i + 1)
            pool_rows.append(
                {
                    "set_no": sn,
                    "role": s.get("role") or ROLE.get(sn, "?"),
                    "nums": nums,
                    "hits": hits,
                    "n_hit": len(hits),
                }
            )
        repack_rows = []
        rh_union: set[int] = set()
        for i, s in enumerate(repack):
            nums = _nums(s)
            hits = sorted(set(nums) & win)
            rh_union.update(hits)
            repack_rows.append(
                {
                    "set_no": i + 1,
                    "source": s.get("source"),
                    "nums": nums,
                    "hits": hits,
                    "n_hit": len(hits),
                }
            )
        by[tag] = {
            "pool": pool_rows,
            "repack": repack_rows,
            "pool_hit_union": sorted(hit_union),
            "pool_hit_union_n": len(hit_union),
            "repack_hit_union": sorted(rh_union),
            "repack_hit_union_n": len(rh_union),
            "repack1_is_6": bool(repack_rows and set(repack_rows[0]["nums"]) == win),
        }
    conn.close()

    payload = {
        "id": "K-SET-SCATTER-1237",
        "as_of": _now(),
        "read_only": True,
        "draw_no": 1237,
        "actual": actual,
        "bonus": bonus,
        "ui_brain_accordion_2": "review",
        "ui_sets_cited": "pool #2/#3/#4/#5/#8 (10장 pool, 몰아주기5 아님)",
        "by_brain": by,
        "mechanism": {
            "pool_1_5": "predict_sets → random.choices(weights) 6개 ×5 · diversify_pick로 세트 간 겹침 줄임",
            "pool_6_8": "cover_r3 · stat만 outside_union(스킬합 밖) · review/markov는 jaccard 분리",
            "pool_9_10": "shape_r2 · 형태 1칸 교체",
            "repack_score5": "number_scores 상위30을 6개씩 5장 · 1장이 점수 1~6위(최고점 6개 한 장)",
            "hindsight_gather_forbidden": "이번 회 당첨을 모아 1장 만드는 것은 peek/컨닝",
        },
        "verdict": (
            "분산은 버그 아님. pool 10장은 역할이 서로 다른 샘플이라 당첨이 장마다 흩어짐. "
            "한 장으로 모으면 1등이라는 관찰은 사후(정답을 본 뒤). "
            "몰아주기 score5는 점수 상위6을 1장에 모음 — 당첨 6개가 아님."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# K-SET-SCATTER-1237 (2026-08-22)",
        "",
        "- **판정:** `DISCUSS_OK` · READ-ONLY · APPLY **없음**",
        "- 형 질문: 1237 당첨 6개가 세트마다 흩어짐 · 한 장으로 모으면 1등 · 세트별 예측 정밀분석",
        f"- 근거: `{OUT_JSON.name}`",
        "",
        "## 화면이 가리킨 것",
        "",
        f"- 당첨 **1237** `{actual}` +{bonus}",
        "- 아코디언 `[2]` = **금액뇌(review)** (순서: 과거학습→선호번호→금액뇌)",
        "- 카드 #2 #3 #4 #5 #8 = **pool 10장** (몰아주기 5장 아님)",
        "",
        "## 각 세트는 어떻게 번호를 고르나",
        "",
        "| 세트 | 역할 | 고르는 방법 |",
        "|------|------|-------------|",
        "| 1~5 | skill_native | 그 뇌 `predict_sets`. review는 이월가중(직전×1.8·나머지×0.85)·prize축 후 `random.choices`로 6개. 5장을 **서로 덜 겹치게** `diversify_pick` |",
        "| 6~8 | cover_r3 | 1~5 **합집합 밖/다른 방향**. stat만 outside_union. review는 Jaccard로 1~5와 떨어짐 |",
        "| 9~10 | shape_r2 | 1번 세트 형태에서 1칸 교체(보너스/당첨 미사용) |",
        "| 몰아주기 1~5 | score5 | 뇌별 `number_scores` 상위 30개를 6개씩 자름. **1장 = 점수 1~6위** |",
        "",
        "즉 1~5는 같은 가중치에서 **5번 따로 뽑고**, 6~8은 **일부러 다른 번호**를 갑니다. 당첨이 장마다 흩어지는 게 설계입니다.",
        "",
    ]
    for tag, lab in (("stat", "과거학습"), ("markov", "선호번호"), ("review", "금액뇌")):
        b = by.get(tag)
        lines.append(f"## {lab} (`{tag}`) 1237 실측")
        lines.append("")
        if not b:
            lines.append("- 캐시 **없음** (미확인)")
            lines.append("")
            continue
        lines.append("| pool# | 역할 | 번호 | 맞음 |")
        lines.append("|-------|------|------|------|")
        for r in b["pool"]:
            lines.append(
                f"| {r['set_no']} | {r['role']} | {r['nums']} | {r['hits']} ({r['n_hit']}) |"
            )
        lines.append("")
        lines.append(
            f"- pool 10장 적중번호 합집합 **{b['pool_hit_union']}** (n={b['pool_hit_union_n']}/6)"
        )
        lines.append("| 몰아주기# | source | 번호 | 맞음 |")
        lines.append("|-----------|--------|------|------|")
        for r in b["repack"]:
            lines.append(
                f"| {r['set_no']} | {r['source']} | {r['nums']} | {r['hits']} ({r['n_hit']}) |"
            )
        lines.append(
            f"- 몰아주기 합집합 **{b['repack_hit_union']}** (n={b['repack_hit_union_n']}) · 1장이 당첨6개? **{b['repack1_is_6']}**"
        )
        lines.append("")

    lines += [
        "## 「한 장으로 모으면 1등」",
        "",
        "맞다. **정답을 본 뒤** 10장에 찍힌 당첨번호를 한 장에 모으면 6개다. 그건 발권기가 할 수 있는 신호가 아니다. 타깃 회 당첨을 몰아주기 입력으로 쓰면 **컨닝**이다 (동결·금지).",
        "",
        "몰아주기가 모으는 것은 **점수 상위 번호**이지 이번 회 당첨이 아니다. 점수가 당첨 6개와 같으면 1장에 모인다. 지금 score5는 그 기기다.",
        "",
        "- APPLY 없음 · 1237 신규예측 없음 · 우열 클레임 금지",
        "",
        "## 파일",
        "",
        "- `tools/_k_set_scatter_1237.py`",
        f"- `{OUT_JSON.name}`",
        "- `app/testlotto/signal_pool.py` · `role_slots.py` · `set_diversity.py` · `brains/predict_review_king.py`",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"actual": actual, "review": by.get("review") is not None, "stat": by.get("stat") is not None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
