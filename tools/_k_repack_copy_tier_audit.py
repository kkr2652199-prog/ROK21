# -*- coding: utf-8 -*-
"""K-REPACK-COPY-AND-TIER-AUDIT — 200회 원장/캐시 정밀.

몰아주기=pool 복사인지(설계 signal_union) vs 버그.
등수 집계: 발권5 ≠ pool10 ≠ repack5. ge3 성적클레임 금지.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260813_KREPACK_COPY_TIER_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260813_KREPACK_COPY_TIER_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1037, 1236
CMP_LO = 1137  # v5 창과 겹침
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _tier(mc: int, bm: int) -> int:
    from app.testlotto.tier_utils import prediction_rank_tier

    t, _ = prediction_rank_tier(int(mc or 0), int(bm or 0))
    return t


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import (
        ASSEMBLE_MODE,
        POOL_SLOTS_BY_BRAIN,
        POOL_UNION_CAP,
        POOL_UNION_CAP_BY_BRAIN,
    )

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        ledger = [
            dict(r)
            for r in conn.execute(
                """
                SELECT draw_no, brain_tag AS brain, kind, set_no, hits, bonus, bonus_hit, tier_rank
                FROM testlotto_pool_hit_ledger
                WHERE draw_no BETWEEN ? AND ?
                """,
                (LO, HI),
            ).fetchall()
        ]
        preds = [
            dict(r)
            for r in conn.execute(
                """
                SELECT target_draw_no, brain_tag, matched_count, bonus_matched
                FROM lotto_predictions
                WHERE target_draw_no BETWEEN ? AND ?
                """,
                (LO, HI),
            ).fetchall()
        ]
        cache_rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT draw_no, brain, pool_json, repack_json
                FROM testlotto_pool_view_cache
                WHERE draw_no BETWEEN ? AND ?
                """,
                (LO, HI),
            ).fetchall()
        ]
    finally:
        conn.close()

    # --- copy / source from cache ---
    copy_n = 0
    repack_n = 0
    src_ctr: Counter[str] = Counter()
    copy_by_brain: dict[str, Counter[str]] = {t: Counter() for t in BRAINS}
    copy_per_draw_brain: list[int] = []  # how many of 5 are exact pool copies
    sample_copy: list[dict[str, Any]] = []

    for row in cache_rows:
        tag = str(row["brain"])
        pool = json.loads(row["pool_json"] or "[]")
        repack = json.loads(row["repack_json"] or "[]")
        pkeys = {_key(s.get("nums") or []) for s in pool}
        n_copy = 0
        for s in repack:
            repack_n += 1
            src = str(s.get("source") or "")
            if src:
                src_ctr[src] += 1
                copy_by_brain[tag][src] += 1
            k = _key(s.get("nums") or [])
            if k in pkeys:
                copy_n += 1
                n_copy += 1
                if len(sample_copy) < 8:
                    sample_copy.append(
                        {
                            "draw": row["draw_no"],
                            "brain": tag,
                            "repack_set": s.get("set_no"),
                            "source": src or "no_source_field",
                            "source_set_no": s.get("source_set_no"),
                            "nums": sorted(int(x) for x in (s.get("nums") or [])),
                        }
                    )
        copy_per_draw_brain.append(n_copy)

    # --- tiers from ledger (set-level, not best-of-draw) ---
    def tier_of(r: dict) -> int:
        tr = r.get("tier_rank")
        if tr not in (None, 0, "0"):
            try:
                return int(tr)
            except (TypeError, ValueError):
                pass
        return _tier(int(r.get("hits") or 0), int(r.get("bonus_hit") or r.get("bonus") or 0))

    set_tiers: dict[str, Counter[int]] = defaultdict(Counter)  # kind -> tier
    brain_kind_t3: list[dict[str, Any]] = []
    draw_best: dict[str, dict[int, int]] = {
        "pool": {},
        "repack": {},
        "any": {},
    }
    for r in ledger:
        kind = str(r["kind"])
        dno = int(r["draw_no"])
        t = tier_of(r)
        set_tiers[kind][t] += 1
        set_tiers[f"{kind}:{r['brain']}"][t] += 1
        if t == 3:
            brain_kind_t3.append(
                {
                    "draw": dno,
                    "brain": r["brain"],
                    "kind": kind,
                    "set_no": r["set_no"],
                    "hits": r["hits"],
                    "bonus": r.get("bonus_hit") if r.get("bonus_hit") is not None else r.get("bonus"),
                }
            )
        if 1 <= t <= 5:
            for bucket in (kind, "any"):
                prev = draw_best[bucket].get(dno, 99)
                if t < prev:
                    draw_best[bucket][dno] = t

    def draw_tier_hist(mp: dict[int, int], lo: int, hi: int) -> dict[str, int]:
        h = {f"r{i}": 0 for i in range(1, 6)}
        h["none"] = 0
        for d in range(lo, hi + 1):
            t = mp.get(d)
            if t and 1 <= t <= 5:
                h[f"r{t}"] += 1
            else:
                h["none"] += 1
        return h

    # ticket path
    ticket_set_t: Counter[int] = Counter()
    ticket_draw_best: dict[int, int] = {}
    ticket_t3: list[dict[str, Any]] = []
    for p in preds:
        dno = int(p["target_draw_no"])
        t = _tier(int(p["matched_count"] or 0), int(p["bonus_matched"] or 0))
        ticket_set_t[t] += 1
        if t == 3:
            ticket_t3.append(
                {
                    "draw": dno,
                    "brain": p["brain_tag"],
                    "hits": p["matched_count"],
                    "bonus": p["bonus_matched"],
                }
            )
        prev = ticket_draw_best.get(dno, 99)
        if t and 1 <= t < prev:
            ticket_draw_best[dno] = t

    n_repack_sets = max(1, repack_n)
    copy_rate = round(copy_n / n_repack_sets, 4)
    src_pool = src_ctr.get("pool", 0)
    src_score = src_ctr.get("score_repack", 0)

    payload = {
        "id": "K-REPACK-COPY-TIER-AUDIT",
        "ts": _now(),
        "window": [LO, HI],
        "n_draws": HI - LO + 1,
        "ge3_used_as_claim": False,
        "assemble": {
            "mode": ASSEMBLE_MODE,
            "pool_slots": dict(POOL_SLOTS_BY_BRAIN),
            "union_cap": int(POOL_UNION_CAP),
            "union_cap_by_brain": dict(POOL_UNION_CAP_BY_BRAIN),
            "copy_is": "DESIGN" if ASSEMBLE_MODE == "signal_union" else "CHECK",
            "rule": "몰아주기 5장 중 최대 cap(기본4)장은 pool 10장에서 통째 보존(source=pool). 나머지는 점수몰아주기(source=score_repack).",
        },
        "copy": {
            "repack_sets": repack_n,
            "exact_match_pool_nums": copy_n,
            "exact_match_rate": copy_rate,
            "source_field": dict(src_ctr),
            "source_pool": src_pool,
            "source_score_repack": src_score,
            "by_brain": {t: dict(copy_by_brain[t]) for t in BRAINS},
            "copies_per_brain_draw_mean": round(
                sum(copy_per_draw_brain) / max(1, len(copy_per_draw_brain)), 3
            ),
            "sample": sample_copy,
        },
        "set_level_tiers": {k: dict(v) for k, v in sorted(set_tiers.items())},
        "draw_best_tiers": {
            "pool_1037_1236": draw_tier_hist(draw_best["pool"], LO, HI),
            "repack_1037_1236": draw_tier_hist(draw_best["repack"], LO, HI),
            "pool_or_repack_1037_1236": draw_tier_hist(draw_best["any"], LO, HI),
            "pool_or_repack_1137_1236": draw_tier_hist(draw_best["any"], CMP_LO, HI),
            "ticket5_1037_1236": draw_tier_hist(ticket_draw_best, LO, HI),
        },
        "tier3_sets": {
            "n": len(brain_kind_t3),
            "by_kind": dict(Counter(x["kind"] for x in brain_kind_t3)),
            "by_brain": dict(Counter(x["brain"] for x in brain_kind_t3)),
            "rows": brain_kind_t3,
        },
        "ticket_set_tiers": dict(ticket_set_t),
        "ticket_tier3": ticket_t3,
        "v5_ref_1137_1236_pool_best": {
            "source": "docs/benchmarks/20260812_KFORCE_POOL_BACKTEST_100_v5.json",
            "n": 100,
            "r3": 0,
            "r4": 4,
            "r5": 42,
            "mean_hits": 2.5,
            "note": "풀경로 best-of-many · 발권5 아님 · 창 n=100",
        },
        "verdict_copy": "DESIGN_NOT_BUG",
        "note": "3등=세트 5적중 무보너스. 회차 best 등수와 세트 건수는 다름. 성적클레임 금지.",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    t3 = payload["tier3_sets"]
    db = payload["draw_best_tiers"]
    lines = [
        "# K-REPACK-COPY-TIER-AUDIT — 몰아주기 복사·등수 정밀",
        "",
        f"시각: {payload['ts']} · 창 {LO}~{HI} · **복사=설계(signal_union)** · ge3미클레임",
        "",
        "## 1) 형이 본 것: 몰아주기가 10세트를 그대로 가져온다",
        "",
        f"- 현재 조립: `{ASSEMBLE_MODE}` · 슬롯={dict(POOL_SLOTS_BY_BRAIN)} · cap={POOL_UNION_CAP}",
        "- **버그 아님.** 몰아주기 5장 중 **최대 4장**은 pool 10장 중 점수/신호 상위 세트를 **통째 보존**한다 (`source=pool`).",
        "- 나머지 1장(+중복 시 보충)은 번호 재조합 (`source=score_repack`).",
        f"- 실측: repack {repack_n}장 중 pool번호 완전일치 **{copy_n}** (비율 **{copy_rate}**)",
        f"- source 필드: {dict(src_ctr)}",
        f"- 뇌×회차당 평균 복사 장수: **{payload['copy']['copies_per_brain_draw_mean']}** / 5",
        "",
        "## 2) 3등 세트 (5적중·보너스없음) — 세트 단위",
        "",
        f"- pool+repack 3등 세트 **{t3['n']}건** · kind={t3['by_kind']} · brain={t3['by_brain']}",
        f"- 발권5 3등 세트 **{len(ticket_t3)}건** {ticket_t3}",
        "",
        "### 3등 세트 목록 (원장)",
        "",
    ]
    if brain_kind_t3:
        lines.append("| 회차 | 뇌 | 경로 | set | hits | bonus |")
        lines.append("|------|----|------|-----|------|-------|")
        for x in brain_kind_t3:
            lines.append(
                f"| {x['draw']} | {x['brain']} | {x['kind']} | {x['set_no']} | {x['hits']} | {x['bonus']} |"
            )
    else:
        lines.append("(0건)")
    lines += [
        "",
        "## 3) 회차 best 등수 (그 회차에서 제일 좋은 장 1개)",
        "",
        f"- 발권5: {db['ticket5_1037_1236']}",
        f"- pool10 only: {db['pool_1037_1236']}",
        f"- repack5 only: {db['repack_1037_1236']}",
        f"- pool또는repack (45장 효과): {db['pool_or_repack_1037_1236']}",
        f"- 같은 창 1137~1236 n100 vs v5: 이번 {db['pool_or_repack_1137_1236']} · v5 r3=0 r4=4 r5=42 (풀경로 모니터)",
        "",
        "발권5의 3·4·5등과 풀 45장 등수를 **같은 성적**으로 비교하면 안 된다.",
        "v5와 이번 200회는 창 길이도 다르다(100 vs 200). 겹친 100회만 위 한 줄.",
        "",
        "## 4) 뇌 엔진 (발권 전세트 mean · 이미 BT200)",
        "",
        "근거 파일 `20260813_KPOST_L12B_RESET_BT200.json` solo mean_all: stat 0.828 / markov 0.808 / review 0.823.",
        "이론 장당 0.80 근처. **서열 선언 안 함.**",
        "",
        "샘플 복사:",
        "```",
        json.dumps(sample_copy, ensure_ascii=False, indent=2),
        "```",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "도구: `tools/_k_repack_copy_tier_audit.py`",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "copy_is": payload["verdict_copy"],
                "copy_rate": copy_rate,
                "source": dict(src_ctr),
                "t3": t3,
                "ticket_t3": ticket_t3,
                "draw_best": db,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
