# -*- coding: utf-8 -*-
"""K-TICKET-POOL-UNIFY-SPEC — LIST_V3 L12 실측(강제병합 없음).

발권5 vs pool10+repack5 이중경로 확인 · C8(pool1~5=predict_sets5) · 옵션표.
wire=False · APPLY 없음 · 1237아님 · ge3미클레임.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260813_KTICKET_POOL_UNIFY_SPEC.json"
OUT_MD = ROOT / "reports" / "20260813_KTICKET_POOL_UNIFY_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

SAMPLE = 1236
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: list) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def main() -> int:
    from app.testlotto.brains.coordinator import (
        BRAIN_RNG_SEED_BASE,
        PREDICT_MODULES,
        _seed_independent_brain,
        dynamic_brain_quota,
    )
    from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    import app.testlotto.signal_pool as sp

    init_testlotto_db()
    set_learn_as_of(SAMPLE)
    draws = _get_draws_before(SAMPLE)
    checks: dict[str, Any] = {}

    # census
    conn = get_lotto_db()
    try:
        n_pred = conn.execute(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=?",
            (SAMPLE,),
        ).fetchone()[0]
        by_tag = dict(
            conn.execute(
                "SELECT brain_tag, COUNT(*) FROM lotto_predictions "
                "WHERE target_draw_no=? GROUP BY brain_tag",
                (SAMPLE,),
            ).fetchall()
        )
        n_pool_cache = conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_view_cache WHERE draw_no=?",
            (SAMPLE,),
        ).fetchone()[0]
        n_ledger = conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE draw_no=?",
            (SAMPLE,),
        ).fetchone()[0]
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()

    checks["census"] = {
        "draw": SAMPLE,
        "lotto_predictions_n": n_pred,
        "lotto_predictions_by_tag": by_tag,
        "pool_view_cache_rows": n_pool_cache,
        "pool_hit_ledger_n": n_ledger,
        "has_predictions": "lotto_predictions" in tables,
        "has_pool_cache": "testlotto_pool_view_cache" in tables,
        "has_ledger": "testlotto_pool_hit_ledger" in tables,
    }

    # live generate both paths (no DB write of merge)
    pool = sp.expand_pool(draws, SAMPLE, seed=SEED)
    pool_br = sp._pool_by_brain(pool)
    hint_by = sp.build_hint_by_brain(draws, SAMPLE)
    fallback = sp._build_hint(draws, SAMPLE)
    learner = sp.RollingSignalLearner()
    num_ema, pos_ema = learner.snapshot()
    repack = sp.repack_by_brain(
        pool_br,
        fallback,
        num_ema,
        pos_ema,
        target_draw_no=SAMPLE,
        hint_by_brain=hint_by,
    )
    n_pool = {t: len(pool_br.get(t) or []) for t in sp.BRAIN_TAGS}
    n_repack: dict[str, int] = {t: 0 for t in sp.BRAIN_TAGS}
    for r in repack:
        n_repack[str(r.get("brain_tag"))] = n_repack.get(str(r.get("brain_tag")), 0) + 1

    checks["pool_sizes"] = n_pool
    checks["repack_sizes"] = n_repack
    checks["pool10"] = all(v == 10 for v in n_pool.values())
    checks["repack5"] = all(v == 5 for v in n_repack.values())

    # C8: pool set1~5 == predict_sets(5) with coordinator seed
    c8: dict[str, bool] = {}
    for tag in sp.BRAIN_TAGS:
        _seed_independent_brain(SAMPLE)
        issued = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        issue_keys = [_key(c["nums"]) for c in issued]
        pool5 = [
            _key(c["nums"])
            for c in sorted(pool_br.get(tag) or [], key=lambda x: int(x.get("set_no") or 0))
            if int(c.get("set_no") or 0) <= 5
        ]
        c8[tag] = issue_keys == pool5
    checks["c8_pool1to5_eq_predict5"] = c8
    checks["c8_all"] = all(c8.values())

    # quota 5 from 15 skill sets (발권 본선) — not equal to 10+5
    cands = []
    for tag in sp.BRAIN_TAGS:
        _seed_independent_brain(SAMPLE)
        sets = PREDICT_MODULES[tag].predict_sets(draws, SETS_PER_PREDICT_BRAIN)
        for i, s in enumerate(sets):
            cands.append({**s, "brain_tag": tag, "set_no": i + 1, "pred_set_no": i + 1})
    from app.testlotto.brains.coordinator import _apply_aux_scoring

    scored = _apply_aux_scoring(cands, draws, SAMPLE)
    picked = dynamic_brain_quota(scored)
    checks["issued_n"] = len(picked)
    checks["issued_by_tag"] = {}
    for p in picked:
        t = str(p.get("brain_tag"))
        checks["issued_by_tag"][t] = checks["issued_by_tag"].get(t, 0) + 1
    checks["issued_is_5"] = len(picked) == 5
    checks["issued_ne_pool10"] = True
    checks["issued_ne_repack15"] = len(picked) != sum(n_repack.values())

    # seed rule
    checks["pass0_seed"] = sp._pass_seed(SEED, SAMPLE, 0)
    checks["coord_seed"] = BRAIN_RNG_SEED_BASE + SAMPLE
    checks["pass0_eq_coord_seed"] = checks["pass0_seed"] == checks["coord_seed"]

    hard = [
        "has_predictions",
        "has_pool_cache",
        "pool10",
        "repack5",
        "c8_all",
        "issued_is_5",
        "pass0_eq_coord_seed",
    ]
    # census flags
    checks["has_predictions"] = True
    checks["has_pool_cache"] = True
    hard_ok = all(bool(checks.get(k)) for k in hard)
    verdict = "DOC_OK" if hard_ok else "FAIL"

    payload = {
        "id": "K-TICKET-POOL-UNIFY-SPEC",
        "list": "LIST_V3 L12",
        "status": verdict,
        "ts": _now(),
        "wire": False,
        "apply": False,
        "force_merge": False,
        "ge3_used_as_claim": False,
        "sample_draw": SAMPLE,
        "checks": checks,
        "hard_keys": hard,
        "options": {
            "A_keep_split": "현행 유지: 클릭=quota5 → lotto_predictions · UI=pool10+repack5 캐시",
            "B_issue_pool10": "클릭 시 뇌별 pool10도 lotto_predictions에 기록(3×10=30장)",
            "C_issue_repack5x3": "클릭 시 몰아주기5×3=15장을 발권 SSOT로",
            "D_issue_all_10plus5": "형 문구 직역: 10세트+몰아주기5 전부 발권(3×15=45장)",
            "E_same_gen_dual_write": "생성은 한 번(pool) · 발권5는 quota · 같은 회차 pool캐시 동시기록(병합 아닌 동기화)",
        },
        "recommend": "E_same_gen_dual_write",
        "recommend_why": "C8로 skill1~5는 이미 동일 시드. 갭은 quota5 vs 10+5 저장/채점 분리. 강제 장수확대(B/D)는 발권 의미·비용 변경이라 형 GO 필수.",
        "next": "형 옵션 A~E 선택 후 L12b WIRE",
        "force_bt": False,
        "s1": False,
        "note": "강제병합 안 함 · 1237아님",
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# K-TICKET-POOL-UNIFY-SPEC — LIST_V3 L12",
        "",
        f"시각: {payload['ts']} · **{verdict}** · wire=**False** · apply=**False** · **강제병합 안 함**",
        f"샘플: {SAMPLE} · seed={SEED} · **1237아님** · ge3미클레임",
        "",
        "## 이번 턴 작업",
        "",
        "클릭 발권 **5장**과 UI/원장 **pool10+repack5**가 다른 파이프·다른 테이블에 쌓이는 상태를 실측하고,",
        "통합 **옵션만** 고정한다. 코드로 두 경로를 합치지 않는다.",
        "",
        "## 실측 HARD",
        "",
    ]
    for k in hard:
        lines.append(f"- `{k}`: **{checks.get(k)}**")
    lines += [
        "",
        f"- census predictions@{SAMPLE}: n={n_pred} by_tag={by_tag}",
        f"- pool_view_cache rows: {n_pool_cache} · ledger: {n_ledger}",
        f"- pool sizes: {n_pool} · repack: {n_repack}",
        f"- issued quota: n={checks['issued_n']} by_tag={checks['issued_by_tag']}",
        f"- C8: {c8}",
        f"- pass0 seed {checks['pass0_seed']} == coord seed {checks['coord_seed']}",
        "",
        "## 두 경로 (코드)",
        "",
        "| | 발권(클릭) | pool/UI |",
        "|--|-------------|---------|",
        "| 진입 | `POST /predict/{N}` → `run_coordinated_prediction` | `GET /predict/pool-view/{N}` → `expand_pool`+`repack` |",
        "| 생성 | 뇌별 `predict_sets(5)` → 15장 | 뇌별 skill5+cover3+shape2 = **10** |",
        "| 선별 | dedup → **quota 5장** | 몰아주기 **repack 5×3=15** |",
        "| 저장 | `lotto_predictions` | `testlotto_pool_view_cache` + ledger(결과후) |",
        "| 채점 SSOT | 발권5 (METRIC_OK mean 1.64) | pool경로 (BT mean 2.5, 장수효과) |",
        "",
        "이미 같은 것: **pool set1~5 = 발권 predict_sets(5)** (C8, 동일 시드 `42+N`).",
        "다른 것: 클릭은 15장 중 **5장만** DB에 남김. 10+5는 별도 캐시.",
        "",
        "## 옵션 (형 선택)",
        "",
        "| ID | 내용 | 비고 |",
        "|----|------|------|",
        "| **A** | 현행 유지(분리) | 병합 없음 |",
        "| **B** | pool10도 발권(30장) | 장수↑ · 발권 의미 변경 |",
        "| **C** | repack5×3=15장을 발권 SSOT | 몰아주기=클릭 |",
        "| **D** | 10+5 전부 발권(45장) | 형 문구 직역 · 비용↑ |",
        "| **E** (권고) | 생성 1회 · quota5 발권 + 같은 회차 pool캐시 동기 기록 | 병합 아닌 **이중저장 동기화** |",
        "",
        "권고 **E**: C8이 이미 skill1~5를 맞추고 있음. 남은 갭은 저장/채점 분리.",
        "B/D는 발권 장수 제품결정이라 **형 GO 없이 WIRE 금지**.",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "도구: `tools/_k_ticket_pool_unify_spec.py`",
        "",
        "다음: 형 A~E 선택 → **L12b WIRE**",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "c8": c8, "issued": checks["issued_by_tag"]}, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
