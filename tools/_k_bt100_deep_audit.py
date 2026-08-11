# -*- coding: utf-8 -*-
"""K-BT100-DEEP-AUDIT — 강제100회 pool 백테 캐시 재채점 + 뇌진/부품 개선 후보.

목적: 4·5등 확인 · 뇌별 몰아주기 확인 · 버그후보·개선점 교차분석.
ge3 성적클레임 금지 · 1237아님 · 컨닝 샘플검증.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KBT100_DEEP_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260811_KBT100_DEEP_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1137, 1236
BRAINS = ("stat", "markov", "review")
FORCE_JSON = ROOT / "docs" / "benchmarks" / "20260811_KFORCE_POOL_BACKTEST_100.json"


def _now_kst_iso() -> str:
    # KST = UTC+9 (고정 오프셋; 로컬 TZ 의존 최소화)
    from datetime import timedelta

    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _score_sets(sets: list[dict], actual_nums: list[int], bonus: int) -> list[dict[str, Any]]:
    from app.testlotto.tier_utils import prediction_rank_tier, score_predicted_set

    out: list[dict[str, Any]] = []
    for s in sets or []:
        nums = [int(x) for x in (s.get("nums") or [])]
        bad: list[str] = []
        if len(nums) != 6:
            bad.append("len!=6")
        if len(set(nums)) != len(nums):
            bad.append("dup")
        if any(n < 1 or n > 45 for n in nums):
            bad.append("oor")
        scored = score_predicted_set(nums, actual_nums, bonus)
        hits = int(scored.get("matched_count") or scored.get("hits") or 0)
        bhit = bool(scored.get("bonus_matched") or scored.get("bonus_hit"))
        # score_predicted_set 필드명 호환
        if "matched_count" not in scored and "hits" not in scored:
            hits = len(set(nums) & set(actual_nums))
            bhit = bonus in set(nums)
        tr, _ = prediction_rank_tier(hits, 1 if bhit else 0)
        out.append(
            {
                "nums": nums,
                "hits": hits,
                "bonus_hit": bhit,
                "tier": int(tr),
                "bad": bad,
                "set_no": s.get("set_no") or s.get("repack_rank"),
            }
        )
    return out


def _best(scored: list[dict]) -> dict[str, Any]:
    if not scored:
        return {"hits": 0, "tier": 0, "bonus_hit": False}

    def key(s: dict) -> tuple:
        t = int(s["tier"] or 0)
        return (int(s["hits"]), 0 if t == 0 else -t)

    b = max(scored, key=key)
    return {"hits": b["hits"], "tier": b["tier"], "bonus_hit": b["bonus_hit"]}


def _mean(xs: list[int]) -> float:
    return round(sum(xs) / len(xs), 6) if xs else 0.0


def _norm_weights(obj: Any) -> Any:
    """튜플/리스트 혼용 비교용."""
    if isinstance(obj, dict):
        return {str(k): _norm_weights(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_norm_weights(x) for x in obj]
    return obj


def audit() -> dict[str, Any]:
    from app.testlotto.brains.shared import crowd_signal as cs
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import CACHE_SCHEMA_VERSION, get_cached_pool_view
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
    bt_rows = {
        int(r["draw_no"]): dict(r)
        for r in conn.execute(
            "SELECT draw_no,best_hits,best_tier FROM testlotto_backtest_draw_results "
            "WHERE run_id=(SELECT MAX(run_id) FROM testlotto_backtest_runs)"
        )
    }
    run = conn.execute(
        "SELECT * FROM testlotto_backtest_runs ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    pool_n = int(conn.execute("SELECT COUNT(*) c FROM testlotto_pool_view_cache").fetchone()["c"])
    schema_dist = [
        dict(r)
        for r in conn.execute(
            "SELECT schema_version, COUNT(*) AS c FROM testlotto_pool_view_cache "
            "GROUP BY schema_version"
        )
    ]
    # 강제100 구간 캐시 tune_json 보존 여부
    tune_fill = conn.execute(
        """
        SELECT
          SUM(CASE WHEN tune_json IS NOT NULL AND length(tune_json)>2 THEN 1 ELSE 0 END) AS filled,
          COUNT(*) AS total
        FROM testlotto_pool_view_cache
        WHERE draw_no BETWEEN ? AND ?
        """,
        (LO, HI),
    ).fetchone()
    conn.close()

    live_knobs = {
        "BLEND": dict(cs.BLEND_STRENGTH_BY_BRAIN),
        "W_CROWD": dict(cs.W_CROWD_BY_BRAIN),
        "W_STRUCT": dict(cs.W_STRUCT_BY_BRAIN),
        "SCORE": {k: list(v) for k, v in sp.SCORE_WEIGHTS_BY_BRAIN.items()},
        "HINT": {k: list(v) for k, v in sp.HINT_SPEC_BY_BRAIN.items()},
        "FEATURE_LAMBDA_WIRE": bool(getattr(sp, "FEATURE_LAMBDA_WIRE", False)),
        "CACHE_SCHEMA": CACHE_SCHEMA_VERSION,
    }

    per_brain_pool: dict[str, Counter] = {b: Counter() for b in BRAINS}
    per_brain_repack: dict[str, Counter] = {b: Counter() for b in BRAINS}
    per_brain_pool_hits: dict[str, list[int]] = {b: [] for b in BRAINS}
    per_brain_repack_hits: dict[str, list[int]] = {b: [] for b in BRAINS}
    pool_beats_repack: Counter = Counter()
    repack_beats_pool: Counter = Counter()
    tie: Counter = Counter()
    bad_sets: list[dict] = []
    cache_miss: list[int] = []
    bt_mismatch: list[dict] = []
    tier4_draws: list[dict] = []
    tier4_by_brain_repack: dict[str, list[int]] = {b: [] for b in BRAINS}
    tier5_by_brain_repack: dict[str, list[int]] = {b: [] for b in BRAINS}
    recompute_best_hits: list[int] = []
    recompute_best_tier: list[int] = []

    tune_from_cache_n = 0
    tune_live_overlay_n = 0
    sample_tune: dict[str, Any] | None = None
    sample_tune_from_cache: bool | None = None

    for dno in range(LO, HI + 1):
        row = draws.get(dno)
        if not row:
            continue
        actual_nums = [int(row[f"num{k}"]) for k in range(1, 7)]
        bonus = int(row.get("bonus") or 0)
        payload = get_cached_pool_view(dno)
        if not payload:
            cache_miss.append(dno)
            continue

        if payload.get("tune_from_cache"):
            tune_from_cache_n += 1
        else:
            tune_live_overlay_n += 1
        if sample_tune is None:
            sample_tune = payload.get("tune_snapshot")
            sample_tune_from_cache = bool(payload.get("tune_from_cache"))

        all_scored: list[dict] = []
        for b in BRAINS:
            ps = _score_sets(payload.get("pool_by_brain", {}).get(b) or [], actual_nums, bonus)
            rs = _score_sets(payload.get("repack_by_brain", {}).get(b) or [], actual_nums, bonus)
            for s in ps + rs:
                if s["bad"]:
                    bad_sets.append(
                        {"draw": dno, "brain": b, "bad": s["bad"], "nums": s["nums"]}
                    )
            bp, br = _best(ps), _best(rs)
            per_brain_pool[b][bp["tier"]] += 1
            per_brain_repack[b][br["tier"]] += 1
            per_brain_pool_hits[b].append(int(bp["hits"]))
            per_brain_repack_hits[b].append(int(br["hits"]))
            if bp["hits"] > br["hits"]:
                pool_beats_repack[b] += 1
            elif br["hits"] > bp["hits"]:
                repack_beats_pool[b] += 1
            else:
                tie[b] += 1
            if br["tier"] == 4:
                tier4_by_brain_repack[b].append(dno)
            if br["tier"] == 5:
                tier5_by_brain_repack[b].append(dno)
            all_scored.extend(ps + rs)

        glob = _best(all_scored)
        recompute_best_hits.append(int(glob["hits"]))
        recompute_best_tier.append(int(glob["tier"]))
        if glob["tier"] == 4:
            tier4_draws.append({"draw": dno, "hits": glob["hits"], "bonus": bonus})

        stored = bt_rows.get(dno)
        if stored and (
            int(stored["best_hits"]) != int(glob["hits"])
            or int(stored.get("best_tier") or 0) != int(glob["tier"])
        ):
            bt_mismatch.append(
                {
                    "draw": dno,
                    "stored": {"hits": stored["best_hits"], "tier": stored["best_tier"]},
                    "recompute": {"hits": glob["hits"], "tier": glob["tier"]},
                }
            )

    # 컨닝 샘플: set_learn_as_of + _get_draws_before
    peek: list[dict[str, Any]] = []
    for dno in (LO, LO + 50, HI):
        set_learn_as_of(dno)
        mat = _get_draws_before(dno)
        mx = max((int(d["draw_no"]) for d in mat), default=0)
        peek.append({"draw": dno, "max_material": mx, "ok": mx < dno})
    set_learn_as_of(None)
    peek_ok = all(p["ok"] for p in peek)

    brain_summary: dict[str, Any] = {}
    for b in BRAINS:
        brain_summary[b] = {
            "pool_tier_counts": {str(k): int(per_brain_pool[b][k]) for k in range(0, 6)},
            "repack_tier_counts": {str(k): int(per_brain_repack[b][k]) for k in range(0, 6)},
            "pool_mean_best_hits": _mean(per_brain_pool_hits[b]),
            "repack_mean_best_hits": _mean(per_brain_repack_hits[b]),
            "pool_beats_repack": int(pool_beats_repack[b]),
            "repack_beats_pool": int(repack_beats_pool[b]),
            "tie": int(tie[b]),
            "repack_r4_draws": tier4_by_brain_repack[b],
            "repack_r4_n": len(tier4_by_brain_repack[b]),
            "repack_r5_n": len(tier5_by_brain_repack[b]),
        }

    build_snap: dict[str, Any] = {}
    if FORCE_JSON.exists():
        build_snap = (json.loads(FORCE_JSON.read_text(encoding="utf-8")).get("wf") or {}).get(
            "tune_snapshot"
        ) or {}
    build_score = _norm_weights(build_snap.get("SCORE_WEIGHTS_BY_BRAIN") or {})
    live_score = _norm_weights(live_knobs["SCORE"])
    build_blend = _norm_weights(build_snap.get("BLEND_STRENGTH_BY_BRAIN") or {})
    live_blend = _norm_weights(live_knobs["BLEND"])

    drift = {
        "score_build_vs_live": build_score != live_score,
        "blend_build_vs_live": build_blend != live_blend,
        "build_SCORE": build_score,
        "live_SCORE": live_score,
        "live_W_CROWD": live_knobs["W_CROWD"],
        "build_BLEND": build_blend,
        "live_BLEND": live_blend,
        "tune_from_cache_draws": tune_from_cache_n,
        "tune_live_overlay_draws": tune_live_overlay_n,
        "tune_json_filled_rows": int(tune_fill["filled"] or 0) if tune_fill else 0,
        "tune_json_total_rows": int(tune_fill["total"] or 0) if tune_fill else 0,
        "api_overlays_live_when_tune_json_null": True,
        "note": (
            "강제100회 빌드 시점 SCORE=cand_A · 이후 cand_B·W0.9 적용. "
            "구행은 tune_json NULL이라 get_cached_pool_view가 live tune_snapshot으로 폴백할 수 있음."
        ),
    }

    cache_tune_snapshot = {
        "sample_draw_tune_snapshot": sample_tune,
        "sample_tune_from_cache": sample_tune_from_cache,
        "warning": (
            "stored tune_json 우선; NULL이면 live tune_snapshot 폴백 "
            "(I-TUNE-SNAPSHOT-OVERLAY 코드패치 후 동작)"
        ),
    }

    improvements: list[dict[str, Any]] = []

    for b in BRAINS:
        s = brain_summary[b]
        if s["pool_mean_best_hits"] > s["repack_mean_best_hits"] + 0.05:
            improvements.append(
                {
                    "id": f"I-REPACK-LOSS-{b}",
                    "hypothesis": f"{b} 몰아주기가 pool 최고히트보다 낮아 손실",
                    "evidence": {
                        "pool_mean": s["pool_mean_best_hits"],
                        "repack_mean": s["repack_mean_best_hits"],
                        "pool_beats": s["pool_beats_repack"],
                        "repack_beats": s["repack_beats_pool"],
                    },
                    "suggestion": (
                        "signal_top 슬롯·SCORE/HINT 재튜닝 또는 몰아주기 선별 특성 점검"
                        "(기존 K-REPACK-SELECT-DIAG 참고)"
                    ),
                    "severity": "medium",
                    "status": "OPEN",
                }
            )

    if drift["score_build_vs_live"] or tune_live_overlay_n > 0:
        improvements.append(
            {
                "id": "I-CACHE-STALE-KNOBS",
                "hypothesis": "UI 100회 숫자가 옛 knobs(cand_A) 기반 · live는 cand_B·W0.9",
                "evidence": drift,
                "suggestion": "강제 리셋+`_k_force_pool_backtest_100` 재실행으로 캐시 갱신 후 UI 재확인",
                "severity": "high",
                "status": "OPEN",
            }
        )

    improvements.append(
        {
            "id": "I-TUNE-SNAPSHOT-OVERLAY",
            "hypothesis": "get_cached_pool_view가 tune_snapshot을 live로 덮어씀",
            "evidence": {
                "code": "pool_view_cache._rows_to_pool_payload: stored tune_json 우선",
                "tune_json_filled_rows": drift["tune_json_filled_rows"],
                "tune_live_overlay_draws": tune_live_overlay_n,
                "note": "코드는 패치됨. 강제100 구간 구행은 tune_json 비어 live 폴백 가능",
            },
            "suggestion": "tune_json 컬럼+저장/서빙 패치 유지(구행 NULL→live폴백). 신규 강제BT 시 시점보존.",
            "severity": "high",
            "status": "PATCHED_THIS_TURN",
        }
    )

    improvements.append(
        {
            "id": "I-MARKOV-LEARN-NO-EFFECT",
            "hypothesis": "markov learn 경로가 히트에 실질 영향 없음",
            "evidence": "20260811_KF_재정립판정 NO_EFFECT_CLOSE",
            "suggestion": (
                "learn boost·visit_count 경로 포함한 overdue/carry 조건 축소 · "
                "선호번호 blend가 지배적인지 확인 후 boost 설계 재검토(동결상한 준수)"
            ),
            "severity": "medium",
            "status": "OPEN",
        }
    )

    engine_v2 = False
    try:
        from app.testlotto.brains.stat_brain import engine as stat_engine

        engine_v2 = bool(getattr(stat_engine, "ENGINE_V2", False))
    except Exception as exc:  # noqa: BLE001
        engine_v2 = f"import_error:{exc}"  # type: ignore[assignment]

    improvements.append(
        {
            "id": "I-STAT-ENGINE-V2-FLAG",
            "hypothesis": "stat ENGINE_V2 플래그/ past_learn 이중경로 혼선",
            "evidence": {"ENGINE_V2": engine_v2, "file": "stat_brain/engine.py"},
            "suggestion": "엔진 v2 vs past_learn soft 이중경로 문서화·어느 쪽이 live 지배인지 측정",
            "severity": "low",
            "status": "OPEN",
        }
    )

    improvements.append(
        {
            "id": "I-FEATURE-LAMBDA-OFF",
            "hypothesis": "feature lambda 와이어 OFF로 보조축 미사용",
            "evidence": {
                "FEATURE_LAMBDA_WIRE": live_knobs["FEATURE_LAMBDA_WIRE"],
                "ref": "K-EVOLVE-FEAT-LAM-REVAL HOLD",
            },
            "suggestion": "몰아주기 보조축으로 재개하려면 뇌별 λ 소규모 게이트(ge3금지·축분리)",
            "severity": "low",
            "status": "OPEN",
        }
    )

    improvements.append(
        {
            "id": "I-KJ-DUAL-WEIGHT",
            "hypothesis": "발권 가중 SSOT 이중화(문서 vs live)",
            "evidence": "K-EVOLVE-FGJ-AUDIT DUAL_OPEN",
            "suggestion": "발권 SSOT=live referee로 문서·코드화 일치(K-J)",
            "severity": "medium",
            "status": "OPEN",
        }
    )

    hint_w = None
    try:
        from app.testlotto.brains.markov_brain import predict as mk_predict

        hint_w = getattr(mk_predict, "HINT_WEIGHT", None)
    except Exception as exc:  # noqa: BLE001
        hint_w = f"import_error:{exc}"

    improvements.append(
        {
            "id": "I-AUX-HINT-WEIGHT",
            "hypothesis": "aux hint 가중 고정으로 뇌별 힌트 기여 과소/과다",
            "evidence": {"HINT_WEIGHT": hint_w, "file": "markov_brain/predict.py"},
            "suggestion": "HINT_WEIGHT_BY_BRAIN 스윕(축=prefer/prize/hit · iso)",
            "severity": "medium",
            "status": "OPEN",
        }
    )

    # 전역 best-of (풀+리팩 전 세트)
    tier_counts = Counter(recompute_best_tier)
    n_scored = len(recompute_best_hits)
    global_best = {
        "mean_hits": _mean(recompute_best_hits),
        "tier_counts": {str(k): int(tier_counts[k]) for k in range(0, 6)},
        "r4_n": int(tier_counts[4]),
        "r5_n": int(tier_counts[5]),
        "r4_draws": tier4_draws,
    }

    hard_bugs = bool(bad_sets or bt_mismatch or cache_miss or (not peek_ok))
    verdict = "AUDIT_DONE_HARD_BUG" if hard_bugs else "AUDIT_DONE_NO_HARD_BUG"

    run_dict = dict(run) if run else {}
    # sqlite Row → 직렬화 가능
    for k, v in list(run_dict.items()):
        if hasattr(v, "isoformat"):
            run_dict[k] = v.isoformat()

    return {
        "id": "K-BT100-DEEP-AUDIT",
        "ts": _now_kst_iso(),
        "range": [LO, HI],
        "n_draws_scored": n_scored,
        "run": run_dict,
        "pool_cache_rows": pool_n,
        "schema_dist": schema_dist,
        "live_knobs": live_knobs,
        "cache_tune_snapshot": cache_tune_snapshot,
        "knob_drift": drift,
        "global_best": global_best,
        "by_brain": brain_summary,
        "bugs": {
            "cache_miss_draws": cache_miss,
            "bad_sets_n": len(bad_sets),
            "bad_sets_sample": bad_sets[:20],
            "bt_mismatch_n": len(bt_mismatch),
            "bt_mismatch_sample": bt_mismatch[:20],
            "peek_ok": peek_ok,
            "peek": peek,
            "hard_bugs_found": hard_bugs,
        },
        "improvements": improvements,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "user_note": "형 UI에서 4·5등·뇌별 몰아주기 확인 — 본 감사가 재집계로 교차검증",
        "overlay_patch": {
            "tune_json_column": True,
            "serve_stored_first": True,
            "schema_kept": CACHE_SCHEMA_VERSION,
            "force100_rows_may_lack_tune_json": drift["tune_json_filled_rows"] == 0,
        },
    }


def write_md(result: dict[str, Any]) -> str:
    gb = result["global_best"]
    bugs = result["bugs"]
    drift = result["knob_drift"]
    lines: list[str] = []
    lines.append("# K-BT100-DEEP-AUDIT — 100회 강제풀 심층감사")
    lines.append("")
    lines.append(f"시각: {result['ts']} · 범위 {result['range']} · 4·5등·뇌별 몰아주기 확인 · 버그/개선 교차분석")
    lines.append("")
    lines.append(f"## 판정 **{result['verdict']}**")
    lines.append(
        f"- hard_bugs={bugs['hard_bugs_found']} · peek_ok={bugs['peek_ok']} · "
        f"bad_sets={bugs['bad_sets_n']} · bt_mismatch={bugs['bt_mismatch_n']} · "
        f"cache_miss={len(bugs['cache_miss_draws'])}"
    )
    lines.append("- ge3 클레임 금지 · 1237아님")
    lines.append("")
    lines.append("## 형 UI 교차검증 (전체 best-of)")
    lines.append(
        f"- mean_best_hits={gb['mean_hits']} · **4등={gb['r4_n']}** · **5등={gb['r5_n']}**"
    )
    lines.append(f"- tier_counts={gb['tier_counts']}")
    lines.append(f"- 4등 회차={gb['r4_draws']}")
    lines.append("")
    lines.append("## 뇌별 몰아주기(repack) 성적")
    for b in BRAINS:
        s = result["by_brain"][b]
        lines.append(
            f"- **{b}**: repack **r4={s['repack_r4_n']}** · **r5={s['repack_r5_n']}** · "
            f"mean_hits pool={s['pool_mean_best_hits']} / repack={s['repack_mean_best_hits']} · "
            f"pool>repack={s['pool_beats_repack']} / repack>pool={s['repack_beats_pool']}"
        )
        lines.append(
            f"  - pool_tiers={s['pool_tier_counts']} · repack_tiers={s['repack_tier_counts']}"
        )
        if s["repack_r4_draws"]:
            lines.append(f"  - repack 4등 회차={s['repack_r4_draws']}")
    lines.append("")
    lines.append("## 캐시 vs live knobs (중요)")
    lines.append(f"- score_build_vs_live={drift['score_build_vs_live']}")
    lines.append(f"- build SCORE={drift['build_SCORE']}")
    lines.append(f"- live SCORE={drift['live_SCORE']}")
    lines.append(f"- live W_CROWD={drift['live_W_CROWD']}")
    lines.append(
        f"- tune_json filled={drift['tune_json_filled_rows']}/{drift['tune_json_total_rows']} · "
        f"live_overlay_draws={drift['tune_live_overlay_draws']}"
    )
    lines.append(f"- note: {drift['note']}")
    lines.append("")
    lines.append("## 이미 된 패치")
    lines.append(
        "- **I-TUNE-SNAPSHOT-OVERLAY PATCHED**: `tune_json` 컬럼 · 저장/서빙 시 배출 knobs 우선"
    )
    lines.append(
        "- **I-CACHE-STALE-KNOBS 잔여**: UI 숫자는 옛 knobs(cand_A) 가능 → 강제100회 재실행 권장"
    )
    lines.append("")
    lines.append("## 개선 후보 (우선순위)")
    for imp in result["improvements"]:
        lines.append(
            f"### {imp['id']} · {imp.get('severity')} · {imp.get('status', 'OPEN')}"
        )
        lines.append(f"- 가설: {imp.get('hypothesis', '')}")
        lines.append(f"- 제안: {imp.get('suggestion', '')}")
        lines.append("")
    lines.append("## 부품 맵")
    lines.append("- 엔진: stat/markov/review `engine.py`")
    lines.append("- 학습: `learn.py` · learn_state · CUTOFF")
    lines.append("- 군중: crowd_signal W/BLEND")
    lines.append("- 몰아주기: signal_pool.repack · assemble_signal_top")
    lines.append("- 보조: aux hint · feature_lambda · past_learn")
    lines.append("")
    lines.append("JSON: `docs/benchmarks/20260811_KBT100_DEEP_AUDIT.json`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    result = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.parent.mkdir(parents=True, exist_ok=True)

    OUT_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md = write_md(result)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")

    print("OUT_JSON", OUT_JSON)
    print("OUT_MD", OUT_MD)
    print("DRIVE", DRIVE)
    print("verdict", result["verdict"])
    print("n_draws_scored", result["n_draws_scored"])
    print("global_best", result["global_best"])
    print("bugs", {k: result["bugs"][k] for k in (
        "bad_sets_n", "bt_mismatch_n", "peek_ok", "hard_bugs_found"
    )})
    print("improvements", [i["id"] for i in result["improvements"]])
    print("ge3_used_as_claim", result["ge3_used_as_claim"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
