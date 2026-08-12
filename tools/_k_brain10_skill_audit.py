# -*- coding: utf-8 -*-
"""K-BRAIN10-SKILL-AUDIT — LIST_V3 L5 (READ).

역할 도입 전/후 정합 + 뇌별 10세트 스킬 감사.
성적(ge3) 클레임 금지 · 1237아님 · 강제BT/S1 미포함.
결함 있으면 L6~L8 후보만 · 없으면 L9.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KBRAIN10_SKILL_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260812_KBRAIN10_SKILL_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1216, 1236
SEED = 42
BRAINS = ("stat", "markov", "review")
SAMPLE_C8 = (1234, 1235, 1236)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: Any) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _jaccard(a: list[int], b: list[int]) -> float:
    sa, sb = set(a), set(b)
    u = sa | sb
    return len(sa & sb) / len(u) if u else 0.0


def _pool_on_off(dno: int, seed: int) -> dict[str, Any]:
    """역할 ON/OFF 각각 expand · pass0(1~5) 동일성."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.role_slots import validate_pool_roles

    sp.set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    max_mat = max(int(d["draw_no"]) for d in draws) if draws else 0

    saved = bool(sp.ROLE_SLOTS_WIRE)
    try:
        sp.ROLE_SLOTS_WIRE = True
        random.seed(seed)
        on = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
        roles = validate_pool_roles(on)

        sp.ROLE_SLOTS_WIRE = False
        random.seed(seed)
        off = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    finally:
        sp.ROLE_SLOTS_WIRE = saved

    pass0_match: dict[str, bool] = {}
    for tag in BRAINS:
        on5 = [
            _key(c["nums"])
            for c in sorted(on.get(tag) or [], key=lambda x: int(x.get("set_no") or 0))
            if int(c.get("set_no") or 0) <= 5
        ]
        off5 = [
            _key(c["nums"])
            for c in sorted(off.get(tag) or [], key=lambda x: int(x.get("set_no") or 0))
            if int(c.get("set_no") or 0) <= 5
        ]
        pass0_match[tag] = on5 == off5 and len(on5) == 5

    # cover vs skill diversity
    cover_div: dict[str, float | None] = {}
    for tag in BRAINS:
        rows = on.get(tag) or []
        skill = [c for c in rows if c.get("role") == "skill_native"]
        cover = [c for c in rows if c.get("role") == "cover_r3"]
        if not skill or not cover:
            cover_div[tag] = None
            continue
        vals = [
            min(_jaccard(c["nums"], s["nums"]) for s in skill) for c in cover
        ]
        cover_div[tag] = round(mean(vals), 4) if vals else None

    cross = 0
    tags = list(BRAINS)
    for i, a in enumerate(tags):
        for b in tags[i + 1 :]:
            cross += len(
                {_key(c["nums"]) for c in on.get(a, [])}
                & {_key(c["nums"]) for c in on.get(b, [])}
            )

    return {
        "draw": dno,
        "peek_ok": max_mat < dno,
        "roles_ok": bool(roles.get("ok")),
        "role_issues": roles.get("issues") or [],
        "pass0_match_off": pass0_match,
        "pass0_all_match": all(pass0_match.values()),
        "cover_min_jaccard_vs_skill": cover_div,
        "cross_identical_pool": cross,
        "n_pool": {t: len(on.get(t) or []) for t in BRAINS},
    }


def _c8_pool_vs_issue(dno: int, seed: int = 42) -> dict[str, Any]:
    """pool set1~5 == 발권 predict_sets(5) (뇌별 시드)."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.coordinator import _seed_independent_brain
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from tools._k_window_signal_survey import PREDICT_MODULES

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    saved = bool(sp.ROLE_SLOTS_WIRE)
    try:
        sp.ROLE_SLOTS_WIRE = True
        random.seed(seed)
        pool = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    finally:
        sp.ROLE_SLOTS_WIRE = saved

    out: dict[str, Any] = {"draw": dno, "brains": {}}
    all_ok = True
    for tag in BRAINS:
        mod = PREDICT_MODULES.get(tag)
        if mod is None:
            out["brains"][tag] = {"ok": False, "error": "no_mod"}
            all_ok = False
            continue
        _seed_independent_brain(dno)
        try:
            issued = mod.predict_sets(draws, 5)
        except Exception as e:  # noqa: BLE001
            out["brains"][tag] = {"ok": False, "error": str(e)}
            all_ok = False
            continue
        issue_keys = [_key(c["nums"]) for c in issued]
        pool5 = [
            _key(c["nums"])
            for c in sorted(pool.get(tag) or [], key=lambda x: int(x.get("set_no") or 0))
            if int(c.get("set_no") or 0) <= 5
        ]
        ok = issue_keys == pool5
        out["brains"][tag] = {
            "ok": ok,
            "n_issue": len(issue_keys),
            "n_pool5": len(pool5),
        }
        if not ok:
            all_ok = False
    out["ok"] = all_ok
    return out


def _skill_axis_monitor(dno: int, seed: int) -> dict[str, Any]:
    """스킬축 모니터(클레임 아님): markov prefer↑ · review prize↓ 방향."""
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before

    sp.set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    prefer = cs.prefer_table(draws, brain="markov")
    prize = cs.prize_table(draws, brain="review")
    saved = bool(sp.ROLE_SLOTS_WIRE)
    try:
        sp.ROLE_SLOTS_WIRE = True
        random.seed(seed)
        pool = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))
    finally:
        sp.ROLE_SLOTS_WIRE = saved

    def avg_w(tag: str, table: dict[int, float]) -> float:
        rows = [c for c in pool.get(tag) or [] if c.get("role") == "skill_native"]
        nums = [n for c in rows for n in c["nums"]]
        if not nums:
            return 0.0
        return mean(float(table.get(int(n), 1.0)) for n in nums)

    m_pref = avg_w("markov", prefer)
    r_pref = avg_w("review", prefer)
    s_pref = avg_w("stat", prefer)
    m_prize = avg_w("markov", prize)
    r_prize = avg_w("review", prize)
    s_prize = avg_w("stat", prize)
    # 방향: markov prefer 가중 ≥ review · review prize 가중 ≤ markov (기대)
    return {
        "draw": dno,
        "prefer_avg": {"markov": round(m_pref, 4), "review": round(r_pref, 4), "stat": round(s_pref, 4)},
        "prize_avg": {"markov": round(m_prize, 4), "review": round(r_prize, 4), "stat": round(s_prize, 4)},
        "markov_prefer_ge_review": m_pref >= r_pref - 1e-9,
        "review_prize_le_markov": r_prize <= m_prize + 1e-9,
    }


def _hint_separation(dno: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before

    sp.set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    hint_by = sp.build_hint_by_brain(draws, dno)
    tops = {
        t: tuple(
            sorted(range(1, 46), key=lambda n: (-float(hint_by.get(t, {}).get(n, 0.0)), n))[:5]
        )
        for t in BRAINS
    }
    return {
        "hint_shared_flag": sp.hint_shared_across_brains(),
        "tops_distinct": len(set(tops.values())) == 3,
        "tops": {t: list(v) for t, v in tops.items()},
    }


def main() -> int:
    import app.testlotto.signal_pool as sp

    # 전 구간 구조 감사
    rows = []
    for dno in range(LO, HI + 1):
        rows.append(_pool_on_off(dno, SEED))

    n = len(rows)
    hard = {
        "pool10_complete": all(all(r["n_pool"][t] == 10 for t in BRAINS) for r in rows),
        "roles_ok_all": all(r["roles_ok"] for r in rows),
        "pass0_match_all": all(r["pass0_all_match"] for r in rows),
        "cross_identical_0": all(r["cross_identical_pool"] == 0 for r in rows),
        "peek_ok_all": all(r["peek_ok"] for r in rows),
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "LEDGER_SIGNAL_WIRE": bool(sp.LEDGER_SIGNAL_WIRE),
        "LEDGER_BLEND": float(sp.LEDGER_BLEND),
    }

    c8 = [_c8_pool_vs_issue(d, SEED) for d in SAMPLE_C8]
    hard["c8_pool1to5_eq_issue"] = all(x.get("ok") for x in c8)

    hint = _hint_separation(HI)
    hard["hint_not_shared"] = hint["hint_shared_flag"] is False
    hard["hint_tops_distinct"] = bool(hint["tops_distinct"])

    axis_rows = [_skill_axis_monitor(d, SEED) for d in range(LO, HI + 1)]
    m_ge_r = mean(1.0 if a["markov_prefer_ge_review"] else 0.0 for a in axis_rows)
    r_le_m = mean(1.0 if a["review_prize_le_markov"] else 0.0 for a in axis_rows)
    soft = {
        "markov_prefer_ge_review_rate": round(m_ge_r, 4),
        "review_prize_le_markov_rate": round(r_le_m, 4),
        # 소프트 결함 임계: 과반 미만이면 해당 뇌 L6~L8 후보
        "markov_axis_soft_fail": m_ge_r < 0.5,
        "review_axis_soft_fail": r_le_m < 0.5,
        "stat_axis": "homework/pattern via HINT_SPEC — structural only (no soft gate)",
    }

    cover_means = {
        t: round(
            mean(
                r["cover_min_jaccard_vs_skill"][t]
                for r in rows
                if r["cover_min_jaccard_vs_skill"].get(t) is not None
            ),
            4,
        )
        for t in BRAINS
    }

    defects: list[dict[str, str]] = []
    if soft["markov_axis_soft_fail"]:
        defects.append(
            {
                "brain": "markov",
                "id": "L7",
                "issue": "skill_native prefer축이 review 대비 우세율 과반 미만",
                "rate": str(soft["markov_prefer_ge_review_rate"]),
            }
        )
    if soft["review_axis_soft_fail"]:
        defects.append(
            {
                "brain": "review",
                "id": "L8",
                "issue": "skill_native prize축이 markov 대비 저가중 과반 미만",
                "rate": str(soft["review_prize_le_markov_rate"]),
            }
        )

    hard_ok = all(hard.values()) if isinstance(hard["ROLE_SLOTS_WIRE"], bool) else False
    # ROLE_SLOTS_WIRE True 필수
    hard_ok = all(
        [
            hard["pool10_complete"],
            hard["roles_ok_all"],
            hard["pass0_match_all"],
            hard["cross_identical_0"],
            hard["peek_ok_all"],
            hard["c8_pool1to5_eq_issue"],
            hard["hint_not_shared"],
            hard["hint_tops_distinct"],
            hard["ROLE_SLOTS_WIRE"] is True,
            abs(hard["LEDGER_BLEND"] - 0.5) < 1e-12,
        ]
    )

    if hard_ok and not defects:
        verdict = "AUDIT_OK"
        next_id = "K-REPACK-PRESERVE-PROBE"
        next_step = "L9"
    elif hard_ok and defects:
        verdict = "AUDIT_OK_SOFT"
        # 첫 결함 뇌 패치
        next_id = {
            "L6": "K-STAT-10SET-SKILL",
            "L7": "K-MARKOV-10SET-SKILL",
            "L8": "K-REVIEW-10SET-SKILL",
        }.get(defects[0]["id"], "K-MARKOV-10SET-SKILL")
        next_step = defects[0]["id"]
    else:
        verdict = "AUDIT_FAIL"
        next_id = "K-BRAIN10-SKILL-AUDIT"
        next_step = "L5_FIX"

    payload = {
        "id": "K-BRAIN10-SKILL-AUDIT",
        "list": "LIST_V3",
        "step": "L5",
        "status": verdict,
        "ts": _now(),
        "wire": False,
        "ge3_used_as_claim": False,
        "range": [LO, HI],
        "n_draws": n,
        "seed": SEED,
        "hard": hard,
        "hard_ok": hard_ok,
        "soft": soft,
        "cover_mean_min_jaccard_vs_skill": cover_means,
        "c8_samples": c8,
        "hint": hint,
        "axis_sample_last": axis_rows[-1] if axis_rows else None,
        "defects_for_L6_L8": defects,
        "next": {"step": next_step, "id": next_id},
        "force_bt": False,
        "s1": False,
        "note": "역할 ON vs OFF pass0 동일 · C8 pool1~5=발권 · 스킬축 모니터 · 1237아님",
        "fail_draws_pass0": [r["draw"] for r in rows if not r["pass0_all_match"]][:10],
        "fail_draws_roles": [r["draw"] for r in rows if not r["roles_ok"]][:10],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-BRAIN10-SKILL-AUDIT — LIST_V3 L5",
        "",
        f"시각: {payload['ts']} · **{verdict}** · wire=**False**(감사) · **1237아님** · ge3미클레임",
        f"구간: {LO}~{HI} n={n} seed={SEED}",
        f"다음: **{next_step}** `{next_id}`",
        "",
        "## HARD",
        "",
        f"```json\n{json.dumps(hard, ensure_ascii=False, indent=2)}\n```",
        "",
        f"hard_ok={hard_ok}",
        "",
        "## SOFT (스킬축 모니터)",
        "",
        f"```json\n{json.dumps(soft, ensure_ascii=False, indent=2)}\n```",
        "",
        "## defects → L6~L8",
        "",
        f"```json\n{json.dumps(defects, ensure_ascii=False, indent=2)}\n```",
        "",
        f"cover mean min-Jaccard vs skill: {cover_means}",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"status": verdict, "hard_ok": hard_ok, "defects": defects, "next": payload["next"]}, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
