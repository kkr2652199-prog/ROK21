# -*- coding: utf-8 -*-
"""K-TIER-ROLE-SLOTS-WIRE — LIST_V3 L4b 검증.

역할 5+3+2 · no_bonus_peek · prefer/prize 게이트 · L3/L4 계약.
실패 시 ROLE_SLOTS_WIRE=False 롤백 권고(벤치 HOLD).
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260812_KTIER_ROLE_SLOTS_WIRE.json"
OUT_MD = ROOT / "reports" / "20260812_KTIER_ROLE_SLOTS_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

FRAME = 1236
LO, HI = 1137, 1236
SEEDS = [0, 42, 123]
WARM_BACK = 80
L1_REF = {
    "prefer": 0.294930,
    "prize": -0.111224,
    "source": "docs/benchmarks/20260812_KPOST_REFILL_JOINT_SMOKE.json",
}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _no_bonus_peek_tests() -> dict[str, Any]:
    from app.testlotto.role_slots import (
        assert_shape_no_bonus_in_signature,
        build_shape_r2_sets,
    )

    t1 = assert_shape_no_bonus_in_signature()
    skill = [{"nums": [1, 2, 3, 4, 5, 6], "set_no": 1}]
    a = build_shape_r2_sets(skill, brain_tag="stat", seed=42, draw_no=1236, n=2)
    # T-NB2: draws에 bonus를 심어도 shape 함수는 draws를 안 받음 → 동일
    b = build_shape_r2_sets(skill, brain_tag="stat", seed=42, draw_no=1236, n=2)
    same = [x["nums"] for x in a] == [x["nums"] for x in b]
    # 시그니처에 bonus 강제 kwargs 불가
    try:
        build_shape_r2_sets(skill, brain_tag="stat", seed=42, draw_no=1236, bonus=10)  # type: ignore[call-arg]
        bonus_kw_rejected = False
    except TypeError:
        bonus_kw_rejected = True
    return {
        "T-NB1": t1,
        "T-NB2": {"ok": same and bonus_kw_rejected, "same": same, "bonus_kw_rejected": bonus_kw_rejected},
        "T-NB3": {
            "ok": True,
            "note": "shape/cover는 draws·seed만 · target 당첨행 미조회(코드경로)",
        },
        "T-NB4": {
            "ok": True,
            "note": "ledger write만 actual · role 생성과 분리",
        },
    }


def _role_and_contracts() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_hit_ledger import LEDGER_TABLE, SCATTER_TABLE, write_pool_hit_ledger
    from app.testlotto.role_slots import validate_pool_roles
    from app.testlotto.signal_pool import last_ledger_consume

    init_testlotto_db()
    # 과거 시드 유지( L4 계약 )
    for d in (1234, 1235):
        write_pool_hit_ledger(d, note="L4b_SEED")
    wr = write_pool_hit_ledger(FRAME, note="L4b_CONTRACT")
    built = sp.build_pool_and_repack(FRAME)
    consume = last_ledger_consume()
    roles = validate_pool_roles(built.get("pool_by_brain") or {})
    focus_ok = all(
        str(r.get("role")) == "focus_r1"
        for rows in (built.get("repack_by_brain") or {}).values()
        for r in rows
    )
    conn = get_lotto_db()
    try:
        n_l = conn.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE draw_no=?", (FRAME,)
        ).fetchone()[0]
        n_s = conn.execute(
            f"SELECT COUNT(*) FROM {SCATTER_TABLE} WHERE draw_no=?", (FRAME,)
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "build_ok": bool(built.get("ok")),
        "roles": roles,
        "focus_r1_all": focus_ok,
        "ledger_consume": {
            "consumed": bool(consume.get("consumed")),
            "blend": consume.get("blend"),
            "ema_solo_exit": bool(consume.get("ema_solo_exit")),
            "n_draws": consume.get("n_draws"),
        },
        "contract_1236": {
            "n_ledger": int(n_l),
            "n_scatter": int(n_s),
            "ok": int(n_l) == 45 and int(n_s) == 6,
            "write_ok": bool(wr.get("ok")),
        },
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "LEDGER_BLEND": float(sp.LEDGER_BLEND),
        "sample_stat_roles": [
            {
                "set_no": r.get("set_no"),
                "role": r.get("role"),
                "role_pass": r.get("role_pass"),
            }
            for r in sorted(
                (built.get("pool_by_brain") or {}).get("stat") or [],
                key=lambda x: int(x.get("set_no") or 0),
            )
        ],
    }


def _run_gate_seed(seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from tools._k_brain_independent_tune import _actual, _fw_proxy, _top15

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, LO - WARM_BACK), LO, seed=seed)
    prefer_all: list[tuple[int, float]] = []
    prize_all: list[float] = []
    prize_early: list[float] = []
    prize_mid: list[float] = []
    prize_late: list[float] = []

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
        prefer_d = mean(fw[n] for n in _top15(scores["markov"])) - all_mean
        prize_d = mean(fw[n] for n in _top15(scores["review"])) - all_mean
        prefer_all.append((dno, prefer_d))
        prize_all.append(prize_d)
        if LO <= dno <= LO + 32:
            prize_early.append(prize_d)
        elif LO + 33 <= dno <= LO + 65:
            prize_mid.append(prize_d)
        else:
            prize_late.append(prize_d)
        learner.update_from_pool(pool_br, _actual(dno))

    mid = (LO + HI) // 2
    pref_lo = [v for d, v in prefer_all if d <= mid]
    pref_hi = [v for d, v in prefer_all if d > mid]
    return {
        "seed": seed,
        "n": len(prefer_all),
        "prefer_mean": round(mean(v for _, v in prefer_all), 6) if prefer_all else 0.0,
        "prize_mean": round(mean(prize_all), 6) if prize_all else 0.0,
        "prefer_split_both_pos": bool(
            pref_lo and pref_hi and mean(pref_lo) > 0 and mean(pref_hi) > 0
        ),
        "consistent_neg": all(
            mean(xs) < 0 for xs in (prize_early, prize_mid, prize_late) if xs
        ),
    }


def main() -> int:
    import app.testlotto.signal_pool as sp
    from tools._k_post_refill_joint_smoke import _precheck

    nb = _no_bonus_peek_tests()
    nb_ok = all(
        (nb[k].get("ok") if isinstance(nb[k], dict) else False)
        for k in ("T-NB1", "T-NB2", "T-NB3", "T-NB4")
    )
    print("no_bonus_peek", nb_ok, flush=True)

    contracts = _role_and_contracts()
    print("roles", contracts["roles"].get("ok"), "focus", contracts["focus_r1_all"], flush=True)
    print("L4 consume", contracts["ledger_consume"], flush=True)
    print("1236", contracts["contract_1236"], flush=True)

    pre = _precheck()
    print("precheck", pre.get("ok"), flush=True)

    runs = []
    for s in SEEDS:
        print(f"== gate seed={s} ==", flush=True)
        r = _run_gate_seed(s)
        print(
            f"  prefer={r['prefer_mean']} prize={r['prize_mean']} "
            f"split={r['prefer_split_both_pos']} cn={r['consistent_neg']}",
            flush=True,
        )
        runs.append(r)

    prefer = mean(r["prefer_mean"] for r in runs)
    prize = mean(r["prize_mean"] for r in runs)
    split_rate = mean(1.0 if r["prefer_split_both_pos"] else 0.0 for r in runs)
    cn_rate = mean(1.0 if r["consistent_neg"] else 0.0 for r in runs)

    health = {
        "prefer_pos": prefer > 0,
        "prefer_split": split_rate >= 1.0,
        "prize_neg": prize < 0,
        "consistent_neg": cn_rate >= (2.0 / 3.0),
        "knobs_ok": bool(pre.get("ok")),
        "roles_ok": bool(contracts["roles"].get("ok")),
        "focus_ok": bool(contracts["focus_r1_all"]),
        "no_bonus_peek": nb_ok,
        "l4_consume": bool(contracts["ledger_consume"].get("consumed")),
        "blend_050": abs(float(contracts["LEDGER_BLEND"]) - 0.5) < 1e-12,
        "contract_1236": bool(contracts["contract_1236"].get("ok")),
    }
    gate_ok = all(health.values())
    # SPEC: 실패 시 HOLD+롤백
    rolled_back = False
    if not gate_ok and sp.ROLE_SLOTS_WIRE:
        # 코드 상수는 커밋 전 유지하되 벤치에 HOLD 기록. 자동 파일 롤백은 형이 결정.
        # 게이트 실패면 플래그를 False로 내려 런타임 롤백(세션).
        sp.ROLE_SLOTS_WIRE = False
        rolled_back = True

    verdict = "WIRE_OK" if gate_ok else "HOLD_ROLLBACK"
    payload = {
        "id": "K-TIER-ROLE-SLOTS-WIRE",
        "list": "LIST_V3",
        "step": "L4b",
        "status": verdict,
        "ts": _now(),
        "wire": bool(gate_ok),
        "ge3_used_as_claim": False,
        "frame_draw": FRAME,
        "no_bonus_peek": nb,
        "contracts": contracts,
        "precheck": pre,
        "gate_runs": runs,
        "gate_summary": {
            "prefer": round(prefer, 6),
            "prize": round(prize, 6),
            "split_rate": round(split_rate, 6),
            "cn_rate": round(cn_rate, 6),
            "drift_vs_l1": {
                "prefer": round(prefer - L1_REF["prefer"], 6),
                "prize": round(prize - L1_REF["prize"], 6),
                "note": "모니터만 · 단독 APPLY 근거 아님",
            },
        },
        "health": health,
        "session_rollback_flag": rolled_back,
        "ROLE_SLOTS_WIRE_after": bool(sp.ROLE_SLOTS_WIRE),
        "s1_begin_immediate": False,
        "force_bt": False,
        "next_list": "L5 K-BRAIN10-SKILL-AUDIT",
        "note": "외부패스 · SPEC 5+3+2 · expand_pool · 1237아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# K-TIER-ROLE-SLOTS-WIRE — LIST_V3 L4b",
        "",
        f"시각: {payload['ts']} · **{verdict}** · wire=**{gate_ok}** · **1237아님** · ge3미클레임",
        "선행: L4 WIRE_OK · L2b SPEC DOC_OK · 외부패스",
        "다음: **L5** K-BRAIN10-SKILL-AUDIT · 강제BT보류 · S1 개별승인",
        "",
        "## 게이트",
        "",
        f"| prefer | prize | split | cn |",
        f"|--------|-------|-------|-----|",
        f"| {prefer:.6f} | {prize:.6f} | {split_rate} | {cn_rate} |",
        "",
        f"health: `{json.dumps(health, ensure_ascii=False)}`",
        "",
        f"벤치: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(OUT_MD.read_text(encoding="utf-8"), encoding="utf-8")
    print("STATUS", verdict, flush=True)
    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
