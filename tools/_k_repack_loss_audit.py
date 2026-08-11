# -*- coding: utf-8 -*-
"""K-REPACK-LOSS — pool>repack 손실 정밀 조사 (cand_B·W0.9 강제100 캐시).

목적: 몰아주기(repack)가 pool 최선보다 못한 회차의 원인 분해 · 개선안(게이트).
ge3 클레임 금지 · 1237아님 · 읽기전용(캐시 재채점).
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KREPACK_LOSS_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260811_KREPACK_LOSS_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _score_sets(sets: list[dict], actual: list[int], bonus: int) -> list[dict[str, Any]]:
    from app.testlotto.tier_utils import prediction_rank_tier, score_predicted_set

    out: list[dict[str, Any]] = []
    for s in sets or []:
        nums = [int(x) for x in (s.get("nums") or [])]
        scored = score_predicted_set(nums, actual, bonus)
        hits = int(scored.get("matched_count") or scored.get("hits") or 0)
        bhit = bool(scored.get("bonus_matched") or scored.get("bonus_hit"))
        if "matched_count" not in scored and "hits" not in scored:
            hits = len(set(nums) & set(actual))
            bhit = bonus in set(nums)
        tr, _ = prediction_rank_tier(hits, 1 if bhit else 0)
        out.append(
            {
                "nums": nums,
                "hits": hits,
                "bonus_hit": bhit,
                "tier": int(tr),
                "set_no": s.get("set_no") or s.get("repack_rank"),
                "source": s.get("source"),
                "source_set_no": s.get("source_set_no"),
                "assemble": s.get("assemble"),
            }
        )
    return out


def _best(scored: list[dict]) -> dict[str, Any]:
    if not scored:
        return {"hits": -1, "tier": 0, "set_no": None, "nums": []}

    def key(s: dict) -> tuple:
        t = int(s["tier"] or 0)
        return (int(s["hits"]), 0 if t == 0 else -t)

    return max(scored, key=key)


def audit() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import get_cached_pool_view
    import app.testlotto.signal_pool as sp

    init_testlotto_db()
    conn = get_lotto_db()
    draws = {
        int(r["draw_no"]): dict(r)
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
            "WHERE draw_no BETWEEN ? AND ?",
            (LO, HI),
        )
    }
    conn.close()

    loss_n = Counter()
    win_n = Counter()
    tie_n = Counter()
    delta_hist: dict[str, Counter] = {b: Counter() for b in BRAINS}
    # pool 최선 set이 repack에 포함됐는지
    pool_best_in_repack = Counter()
    pool_best_not_in_repack = Counter()
    pool_best_set_no_dist: dict[str, Counter] = {b: Counter() for b in BRAINS}
    assemble_labels: dict[str, Counter] = {b: Counter() for b in BRAINS}
    # 손실 시: pool 최선 hits vs repack 최선 · 티어 손실
    loss_samples: list[dict] = []
    tier_loss = Counter()  # e.g. "4->5", "5->0"
    total_loss_hits = 0
    n_scored = 0

    for dno in range(LO, HI + 1):
        row = draws.get(dno)
        if not row:
            continue
        actual = [int(row[f"num{k}"]) for k in range(1, 7)]
        bonus = int(row.get("bonus") or 0)
        payload = get_cached_pool_view(dno)
        if not payload:
            continue
        n_scored += 1
        for b in BRAINS:
            ps = _score_sets(payload.get("pool_by_brain", {}).get(b) or [], actual, bonus)
            rs = _score_sets(payload.get("repack_by_brain", {}).get(b) or [], actual, bonus)
            pb = _best(ps)
            rb = _best(rs)
            ph, rh = int(pb["hits"]), int(rb["hits"])
            if ph < 0:
                continue
            if ph > rh:
                loss_n[b] += 1
                delta_hist[b][ph - rh] += 1
                total_loss_hits += ph - rh
                pt, rt = int(pb.get("tier") or 0), int(rb.get("tier") or 0)
                if pt and (not rt or rt > pt):
                    tier_loss[f"{pt}->{rt or 0}"] += 1
                # membership
                pnums = tuple(sorted(pb.get("nums") or []))
                in_rep = any(tuple(sorted(s["nums"])) == pnums for s in rs)
                if in_rep:
                    pool_best_in_repack[b] += 1
                else:
                    pool_best_not_in_repack[b] += 1
                sn = pb.get("set_no")
                pool_best_set_no_dist[b][str(sn)] += 1
                for s in rs[:1]:
                    assemble_labels[b][str(s.get("assemble") or "?")] += 1
                if len(loss_samples) < 24:
                    loss_samples.append(
                        {
                            "draw": dno,
                            "brain": b,
                            "pool_hits": ph,
                            "repack_hits": rh,
                            "delta": ph - rh,
                            "pool_set_no": sn,
                            "pool_tier": pt,
                            "repack_tier": rt,
                            "pool_best_in_repack": in_rep,
                            "assemble": (rs[0].get("assemble") if rs else None),
                        }
                    )
            elif rh > ph:
                win_n[b] += 1
            else:
                tie_n[b] += 1

    # 개선안 (게이트 제안 — 코드 미적용)
    proposals = [
        {
            "id": "P1-PRESERVE-POOL-TOP-K",
            "gate": "prefer/prize 축 iso · seed≥3 · |Δ|≥0.01",
            "idea": "signal_top n_slots↑ 또는 pool 신호상위 K개를 repack 슬롯에 강제보존",
            "rationale": "손실의 대부분이 pool_best ∉ repack — 신호순위≠사후히트",
            "risk": "다양성↓ · classic score_repack 비중↓",
            "status": "PROPOSE",
        },
        {
            "id": "P2-ORACLE-FREE-UNION",
            "gate": "동일 · 발권세트수 고정(5) 유지",
            "idea": "repack = signal_top(pool) ∪ classic_repack 상위 재순위(중복제거 후 5)",
            "rationale": "pool 보존과 번호점수몰아주기 절충",
            "risk": "세트 중복·근친 증가",
            "status": "PROPOSE",
        },
        {
            "id": "P3-NO-CODE-HOLD",
            "gate": "형 승인 전",
            "idea": "손실은 사후정보(당첨) 기준 — live 신호로는 완전제거 불가. 측정만 유지",
            "rationale": "pool>repack 은 실패라기보다 선택편향 모니터",
            "risk": "없음",
            "status": "HOLD_DEFAULT",
        },
    ]

    by_brain = {}
    for b in BRAINS:
        by_brain[b] = {
            "pool_gt_repack": int(loss_n[b]),
            "repack_gt_pool": int(win_n[b]),
            "tie": int(tie_n[b]),
            "delta_hist": {str(k): int(v) for k, v in sorted(delta_hist[b].items())},
            "pool_best_in_repack_when_loss": int(pool_best_in_repack[b]),
            "pool_best_not_in_repack_when_loss": int(pool_best_not_in_repack[b]),
            "pool_best_set_no_dist_loss": dict(pool_best_set_no_dist[b]),
            "assemble_on_loss": dict(assemble_labels[b]),
        }

    # 지배 원인
    not_in = sum(pool_best_not_in_repack.values())
    in_rep = sum(pool_best_in_repack.values())
    dominant = (
        "POOL_BEST_DROPPED_FROM_REPACK"
        if not_in > in_rep
        else "POOL_BEST_KEPT_BUT_REPACK_OTHER_WORSE"
        if in_rep
        else "NO_LOSS"
    )

    return {
        "id": "K-REPACK-LOSS-AUDIT",
        "ts": _now(),
        "range": [LO, HI],
        "n_draws_scored": n_scored,
        "live_assemble": {
            "ASSEMBLE_MODE": getattr(sp, "ASSEMBLE_MODE", None),
            "SIGNAL_TOP_BRAINS": sorted(getattr(sp, "SIGNAL_TOP_BRAINS", []) or []),
            "POOL_SLOTS_BY_BRAIN": dict(getattr(sp, "POOL_SLOTS_BY_BRAIN", {}) or {}),
            "REPACK_SETS_PER_BRAIN": getattr(sp, "REPACK_SETS_PER_BRAIN", None),
        },
        "totals": {
            "pool_gt_repack": dict(loss_n),
            "repack_gt_pool": dict(win_n),
            "tie": dict(tie_n),
            "sum_hit_delta_on_loss": total_loss_hits,
            "tier_downgrade_on_loss": dict(tier_loss),
        },
        "by_brain": by_brain,
        "dominant_cause": dominant,
        "loss_samples": loss_samples,
        "proposals": proposals,
        "code_changed": False,
        "verdict": "AUDIT_DONE_PROPOSE_HOLD",
        "ge3_used_as_claim": False,
        "note": "개선코드는 형 승인 후 P1/P2 게이트. 기본=P3 HOLD",
    }


def write_md(r: dict[str, Any]) -> str:
    lines = [
        "# K-REPACK-LOSS-AUDIT — pool>repack 손실 조사",
        "",
        f"시각: {r['ts']} · 범위 {r['range']} · n={r['n_draws_scored']}",
        "",
        f"## 판정 **{r['verdict']}**",
        f"- dominant_cause=`{r['dominant_cause']}`",
        f"- code_changed={r['code_changed']} · ge3클레임금지 · 1237아님",
        "",
        "## 조립 설정",
        f"- `{r['live_assemble']}`",
        "",
        "## 뇌별 요약",
    ]
    for b, d in r["by_brain"].items():
        lines.append(
            f"- **{b}**: pool>repack={d['pool_gt_repack']} · "
            f"repack>pool={d['repack_gt_pool']} · tie={d['tie']} · "
            f"loss시 pool_best∉repack={d['pool_best_not_in_repack_when_loss']} / "
            f"∈repack={d['pool_best_in_repack_when_loss']}"
        )
    lines += [
        "",
        f"## 티어 하락(손실회) `{r['totals']['tier_downgrade_on_loss']}`",
        f"- sum_hit_delta_on_loss={r['totals']['sum_hit_delta_on_loss']}",
        "",
        "## 개선안 (미적용)",
    ]
    for p in r["proposals"]:
        lines.append(f"- **{p['id']}** [{p['status']}] {p['idea']} · gate={p['gate']}")
    lines += ["", "## 샘플(최대24)", "```json", json.dumps(r["loss_samples"][:12], ensure_ascii=False, indent=2), "```", ""]
    text = "\n".join(lines)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    r = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(r)
    print("VERDICT", r["verdict"], "cause", r["dominant_cause"])
    print("totals", r["totals"]["pool_gt_repack"])
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
