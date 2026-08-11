# -*- coding: utf-8 -*-
"""K-F 재정의 — markov learn 재료 채움 + prefer_delta 효과 검증.

젠스파크답+형GO (20260811):
  Q1=B 재료+효과 · Q2=A prefer_delta 1차·mean_hits모니터 · Q3=C 재료후만
  Q4=A FINDINGS PATCHED/CLOSED · LEARN_WIRED 이미 ON(배선 아님)

순서: 백업확인 → markov-only feedback fill 1137~1236 → A/B LEARN_WIRED
게이트: prefer(on)>prefer(off) AND |Δprefer|≥ABS · prize_iso(비악화)
ge3 클레임금지 · 1237아님 · 동결 준수.
"""
from __future__ import annotations

import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KF_재정의_판정.json"
OUT_MD = ROOT / "reports" / "20260811_KF_재정의_판정.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
BACKUP_DIR = ROOT / "backups" / "20260811_KF전_DB전체"

LO, HI = 1137, 1236
SEEDS_AB = [0, 42, 123]
WARM_BACK = 80
ABS_THR = 0.005
PRIZE_ISO_THR = 0.005
SEED_BASE = 20260725
SEED_MULT = 9973


def _draw_seed(draw_no: int) -> int:
    return SEED_BASE + int(draw_no) * SEED_MULT


def _verify_backup() -> dict[str, Any]:
    meta_p = BACKUP_DIR / "pre_backup_meta.json"
    if not meta_p.exists():
        raise RuntimeError(f"backup meta missing: {meta_p}")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    if int(meta.get("total_bytes") or 0) < 1_000_000:
        raise RuntimeError("backup too small")
    return meta


def _fill_markov_learn() -> dict[str, Any]:
    """markov만 feedback — CUTOFF 재구성용 brain_review 행도 기록.

    load_learn_state(CUTOFF ON) = brain_review 재생. 글로벌 행만 쓰면 A/B가 빈 재료를 봄.
    """
    import json as _json

    from app.testlotto.brains.markov_brain import predict as markov_predict
    from app.testlotto.draw_analysis import detect_missed_patterns
    from app.testlotto.learn_state import apply_feedback, _load_global_learn_state
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import _get_draws_before
    from app.testlotto.walkforward import _learn_match_from_sets

    init_testlotto_db()
    clear_history_cache()
    conn = get_lotto_db()
    rows = conn.execute(
        "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws "
        "WHERE draw_no BETWEEN ? AND ? ORDER BY draw_no",
        (LO, HI),
    ).fetchall()
    # 구간 markov 복습만 교체 (다른 뇌 행 보존)
    conn.execute(
        "DELETE FROM testlotto_brain_review WHERE brain_tag='markov' AND draw_no BETWEEN ? AND ?",
        (LO, HI),
    )
    conn.commit()
    conn.close()

    n_ok = 0
    peek_ok = 0
    for row in rows:
        dno = int(row["draw_no"])
        actual = [int(row[f"num{k}"]) for k in range(1, 7)]
        bonus = int(row["bonus"] or 0)
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            raise RuntimeError(f"PEEK draw={dno} max_mat={max_mat}")
        peek_ok += 1
        if len(draws) < 50:
            continue
        random.seed(_draw_seed(dno))
        sets = markov_predict.predict_sets(draws, 5)
        scored = []
        act_set = set(actual)
        for i, s in enumerate(sets):
            nums = [int(x) for x in s["nums"]]
            scored.append(
                {
                    "nums": nums,
                    "matched_count": len(set(nums) & act_set),
                    "set_no": i + 1,
                    "bonus_matched": 1 if bonus in nums else 0,
                }
            )
        learn_matched, learn_nums, learn_set_no = _learn_match_from_sets(scored)
        missed = detect_missed_patterns(learn_nums, actual, draws)
        state = apply_feedback("markov", dno, learn_matched, missed)
        # CUTOFF 소스
        conn = get_lotto_db()
        try:
            conn.execute(
                """
                INSERT INTO testlotto_brain_review (
                    draw_no, brain_tag, predicted_nums, predicted_sets_json, best_set_no,
                    matched_count, bonus_matched, missed_patterns, feedback_json, weight_snapshot
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    dno,
                    "markov",
                    _json.dumps(learn_nums, ensure_ascii=False),
                    _json.dumps(scored, ensure_ascii=False),
                    int(learn_set_no or 0),
                    int(learn_matched),
                    0,
                    _json.dumps(missed, ensure_ascii=False),
                    _json.dumps(
                        {
                            "missed_patterns": missed,
                            "adjustments": state.get("adjustments", {}),
                            "feedback_mode": "mean",
                            "source": "K-F-REDEFINE",
                        },
                        ensure_ascii=False,
                    ),
                    _json.dumps({"markov": state}, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        n_ok += 1

    clear_history_cache()
    set_learn_as_of(HI + 1)  # load all filled events < 1237
    from app.testlotto.learn_state import load_learn_state

    st = load_learn_state("markov")
    st_s = load_learn_state("stat")
    st_r = load_learn_state("review")
    g_markov = _load_global_learn_state("markov")
    conn = get_lotto_db()
    rev_m = conn.execute(
        "SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag='markov' AND draw_no BETWEEN ? AND ?",
        (LO, HI),
    ).fetchone()[0]
    rev_other = conn.execute(
        "SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag!='markov' AND draw_no BETWEEN ? AND ?",
        (LO, HI),
    ).fetchone()[0]
    conn.close()
    return {
        "n_filled": n_ok,
        "peek_checks": peek_ok,
        "brain_review_markov": rev_m,
        "brain_review_other_in_range": rev_other,
        "markov_state_as_of": {
            "review_count": st.get("review_count"),
            "last_draw_no": st.get("last_draw_no"),
            "recent_avg_match": st.get("recent_avg_match"),
            "adjustments": st.get("adjustments"),
            "miss_counts": st.get("miss_counts"),
        },
        "markov_global": {
            "review_count": g_markov.get("review_count"),
            "adjustments": g_markov.get("adjustments"),
            "miss_counts": g_markov.get("miss_counts"),
        },
        "stat_review_count": st_s.get("review_count"),
        "review_review_count": st_r.get("review_count"),
        "independence_ok": int(st_s.get("review_count") or 0) == 0
        and int(st_r.get("review_count") or 0) == 0
        and int(rev_other) == 0,
        "materials_nonzero": any(
            float(v or 0) > 0 for v in (st.get("adjustments") or {}).values()
        )
        or any(int(v or 0) > 0 for v in (st.get("miss_counts") or {}).values()),
    }


def _run_ab(seed: int, wired: bool) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.markov_brain import learn as markov_learn
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _top15

    saved = bool(markov_learn.LEARN_WIRED)
    markov_learn.LEARN_WIRED = bool(wired)
    try:
        learner = sp.RollingSignalLearner()
        sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
        prefer: list[float] = []
        prize: list[float] = []
        hits: list[float] = []
        for dno in range(LO, HI + 1):
            sp.set_learn_as_of(dno)
            draws = sp._get_draws_before(dno)
            if len(draws) < 50:
                continue
            fw = _fw_proxy(draws)
            all_mean = mean(fw[n] for n in range(1, 46))
            if all_mean <= 1e-12:
                continue
            random.seed(seed)
            pool = sp.expand_pool(draws, dno, seed=seed)
            pool_br = sp._pool_by_brain(pool)
            num_ema, pos_ema = learner.snapshot()
            hint_by = sp.build_hint_by_brain(draws, dno)
            fallback = sp._build_hint(draws, dno)
            scores = {
                tag: sp.number_scores(
                    pool_br.get(tag, []),
                    hint_by.get(tag, fallback),
                    num_ema,
                    pos_ema,
                    brain_tag=tag,
                )
                for tag in sp.BRAIN_TAGS
            }
            t15m = _top15(scores["markov"])
            t15r = _top15(scores["review"])
            prefer.append(mean(fw[n] for n in t15m) - all_mean)
            prize.append(mean(fw[n] for n in t15r) - all_mean)
            # mean_hits monitor: markov pool sets mean hit vs actual
            act = _actual(dno)
            msets = pool_br.get("markov") or []
            if msets:
                hs = [len(set(int(x) for x in c["nums"]) & act) for c in msets]
                hits.append(mean(hs))
            learner.update_from_pool(pool_br, act)
        return {
            "seed": seed,
            "wired": wired,
            "n": len(prefer),
            "prefer": round(mean(prefer), 6) if prefer else None,
            "prize": round(mean(prize), 6) if prize else None,
            "mean_hits": round(mean(hits), 6) if hits else None,
        }
    finally:
        markov_learn.LEARN_WIRED = saved


def _decide(off: dict[str, Any], on: dict[str, Any]) -> dict[str, Any]:
    dpref = on["prefer"] - off["prefer"]
    dprize = on["prize"] - off["prize"]
    prefer_improve = on["prefer"] > off["prefer"] and abs(dpref) >= ABS_THR
    prize_ok = dprize >= -PRIZE_ISO_THR  # 비악화 (더 음수=개선도 OK, 양수악화만 차단)
    keep = bool(prefer_improve and prize_ok)
    return {
        "prefer_off": off["prefer"],
        "prefer_on": on["prefer"],
        "prize_off": off["prize"],
        "prize_on": on["prize"],
        "mean_hits_off": off["mean_hits"],
        "mean_hits_on": on["mean_hits"],
        "dprefer": round(dpref, 6),
        "dprize": round(dprize, 6),
        "prefer_improve": prefer_improve,
        "prize_non_worsen": prize_ok,
        "keep_learn_effect": keep,
        "abs_thr": ABS_THR,
        "prize_iso_thr": PRIZE_ISO_THR,
    }


def _patch_findings(verdict_line: str) -> None:
    path = ROOT / "My_Drive_Sync" / "SUMMARY" / "FINDINGS.md"
    text = path.read_text(encoding="utf-8")
    old = (
        "| K-F | OPEN | markov가 learn_state 미소비 | `brains/predict_flow_shaman.py:9` | boost 미적용. 3뇌 중 유일 |"
    )
    new = (
        f"| K-F | PATCHED | markov learn 재정의(재료+효과) · live=`markov_brain` 이미 소비 · "
        f"predict_flow_shaman DEPRECATED | `markov_brain/learn.py` · `20260811_KF_재정의_판정` | {verdict_line} |"
    )
    if old not in text:
        # already patched?
        if "K-F | PATCHED" in text or "K-F | CLOSED" in text:
            return
        raise RuntimeError("FINDINGS K-F row not found for patch")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    print("== backup ==")
    backup = _verify_backup()
    print("backup_ok", backup["n_files"], backup["total_bytes"])

    print("== fill markov learn 1137-1236 ==")
    fill = _fill_markov_learn()
    print(
        "fill",
        {
            k: fill[k]
            for k in (
                "n_filled",
                "materials_nonzero",
                "independence_ok",
                "brain_review_markov",
                "markov_state_as_of",
            )
        },
    )
    if int(fill["markov_state_as_of"].get("review_count") or 0) < 1:
        raise RuntimeError("materials still empty after fill")
    if not fill["independence_ok"]:
        raise RuntimeError("stat/review learn touched — abort")

    from app.testlotto.learn_state_cutoff import clear_history_cache

    clear_history_cache()
    print("== A/B LEARN_WIRED ==")
    off_runs = [_run_ab(s, False) for s in SEEDS_AB]
    on_runs = [_run_ab(s, True) for s in SEEDS_AB]
    off_agg = {
        "prefer": mean(r["prefer"] for r in off_runs),
        "prize": mean(r["prize"] for r in off_runs),
        "mean_hits": mean(r["mean_hits"] for r in off_runs),
    }
    on_agg = {
        "prefer": mean(r["prefer"] for r in on_runs),
        "prize": mean(r["prize"] for r in on_runs),
        "mean_hits": mean(r["mean_hits"] for r in on_runs),
    }
    decision = _decide(off_agg, on_agg)
    print("decision", decision)

    # LEARN_WIRED stays True (production default). If no effect → CLOSE note, still leave ON (already wired)
    if decision["keep_learn_effect"]:
        verdict = "KEEP_EFFECT"
        findings_note = "재료채움후 prefer↑·prize비악화 → LEARN_WIRED=True 유지"
    else:
        verdict = "NO_EFFECT_CLOSE"
        findings_note = "재료채움후 효과미달 → 배선사실 PATCHED·효과없음 CLOSE기록 · LEARN_WIRED=True유지(경로정상)"

    _patch_findings(findings_note)

    payload = {
        "id": "K-F-REDEFINE-JUDGE",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "genspark_answers": {"Q1": "B", "Q2": "A", "Q3": "C", "Q4": "A"},
        "backup": backup,
        "fill": fill,
        "ab": {
            "seeds": SEEDS_AB,
            "off_per_seed": off_runs,
            "on_per_seed": on_runs,
            "off_agg": {k: round(v, 6) for k, v in off_agg.items()},
            "on_agg": {k: round(v, 6) for k, v in on_agg.items()},
            "decision": decision,
        },
        "LEARN_WIRED_final": True,
        "verdict": verdict,
        "ge3_used_as_claim": False,
        "findings_k_f": "PATCHED",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = f"""# K-F 재정의 판정

📅 2026-08-11 KST · 젠스파크답+형GO · **재료+prefer_delta 효과**

## 재정의
- 배선(ON) 아님 → live `markov_brain` 이미 `apply_learn_boost`
- 본질 = **재료 공급 + 효과 검증**
- 판정축 = **prefer_delta 1차** · mean_hits 모니터 · ge3 클레임금지

## 1) 백업
- `{BACKUP_DIR.as_posix()}` · files={backup['n_files']} · bytes={backup['total_bytes']}

## 2) 재료 채움 (markov only · 1137~1236)
- n={fill['n_filled']} · brain_review_markov={fill['brain_review_markov']} · independence_ok={fill['independence_ok']}
- as_of review_count={fill['markov_state_as_of']['review_count']} · last={fill['markov_state_as_of']['last_draw_no']}
- adjustments={fill['markov_state_as_of']['adjustments']}
- miss_counts={fill['markov_state_as_of']['miss_counts']}
- materials_nonzero={fill['materials_nonzero']}
- seed=20260725+draw×9973 · `_get_draws_before` peek가드 · CUTOFF=`brain_review`

## 3) A/B LEARN_WIRED (재료 고정)
| | prefer | prize | mean_hits(모니터) |
|--|--------|-------|-------------------|
| OFF | {decision['prefer_off']:.6f} | {decision['prize_off']:.6f} | {decision['mean_hits_off']:.6f} |
| ON | {decision['prefer_on']:.6f} | {decision['prize_on']:.6f} | {decision['mean_hits_on']:.6f} |
| Δ | {decision['dprefer']:.6f} | {decision['dprize']:.6f} | — |

- prefer_improve={decision['prefer_improve']} · prize_non_worsen={decision['prize_non_worsen']}

## 4) 판정 **{verdict}**
- LEARN_WIRED_final=**True** (경로 정상 유지)
- FINDINGS K-F → **PATCHED** · {findings_note}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print("VERDICT", verdict)
    print("WROTE", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
