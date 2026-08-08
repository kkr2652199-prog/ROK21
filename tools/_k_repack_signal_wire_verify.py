# -*- coding: utf-8 -*-
"""K-REPACK-SIGNAL-WIRE-VERIFY — 몰아주기 배선 3건이 설계대로 동작하는지 검증.

이 도구는 **성적을 재지 않는다.** 「설계 의도와 코드가 일치하는가」만 본다.
적중률이 오르든 말든 통과해야 하는 항목들이다.

수정한 배선 (K-REPACK-SIGNAL-WIRE · 20260808)
  ① 성적표를 뇌별로 분리 — 이전엔 3뇌가 pos/num EMA 한 장을 공유
  ② pool 슬롯을 신호 상위로 선택 — 이전엔 set_no 4·5 하드코딩
  ③ 3뇌 동일 배선 — 이전엔 markov 만 pool 슬롯 0개

검사 항목
  C1 뇌별 성적표가 실제로 분리됐나 (3뇌 표가 서로 다른가)
  C2 고른 pool 세트가 정말 신호 최상위인가 · 4·5 고정에서 벗어났나
  C3 3뇌 모두 같은 조립을 쓰고 pool 슬롯 수가 설계값과 같은가
  C4 통째 보존이 실제로 되는가 (발권 세트가 pool 세트와 번호까지 같은가)
  C5 같은 seed 로 두 번 돌리면 완전히 같은가 (결정성)
  C6 미래참조가 없는가 (N회 신호가 N회 정답을 안 보는가)
  C7 뇌 간 RNG 독립인가 (한 뇌만 돌려도 같은 세트가 나오는가)
  C8 pool 1~5 가 실제 발권 경로의 5세트와 일치하는가

Usage
  python tools/_k_repack_signal_wire_verify.py
  K_WV_LO=1176 K_WV_HI=1235 python tools/_k_repack_signal_wire_verify.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

VERIFY_ID = "K-REPACK-SIGNAL-WIRE-VERIFY"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KREPACK_SIGNAL_WIRE_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260808_KREPACK_SIGNAL_WIRE_VERIFY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

DEFAULT_LO = 1176
WARM_BACK = 200


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    return int(v) if v else default


def _max_draw_no() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    row = conn.execute("SELECT MAX(draw_no) AS m FROM lotto_draws").fetchone()
    conn.close()
    return int(dict(row)["m"])


def _actual(dno: int) -> set[int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    row = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6 FROM lotto_draws WHERE draw_no=?", (dno,)
    ).fetchone()
    conn.close()
    d = dict(row)
    return {int(d[f"num{k}"]) for k in range(1, 7)}


def _state_at(dno: int, seed: int) -> dict[str, Any]:
    """dno 시점의 뇌별 신호표 + pool + 몰아주기 결과. walk-forward only."""
    import app.testlotto.signal_pool as sp

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, dno - WARM_BACK), dno, seed=seed)
    num_all, pos_all = learner.snapshot()

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    random.seed(seed)
    pool = sp.expand_pool(draws, dno, seed=seed)
    pool_br = sp._pool_by_brain(pool)
    hint = sp._build_hint(draws, dno)
    rows = sp.repack_by_brain(pool_br, hint, num_all, pos_all, target_draw_no=dno)
    return {
        "num_all": num_all,
        "pos_all": pos_all,
        "pool_br": pool_br,
        "rows": rows,
    }


def _tables_distinct(pos_all: dict[str, dict[int, float]]) -> dict[str, Any]:
    """C1 — 뇌별 표가 실제로 다른가. 공유 표였다면 전부 동일하게 나온다."""
    import app.testlotto.signal_pool as sp

    tags = list(sp.BRAIN_TAGS)
    pairs = {}
    for i, a in enumerate(tags):
        for b in tags[i + 1 :]:
            same = pos_all.get(a) == pos_all.get(b)
            pairs[f"{a}|{b}"] = {"identical": bool(same)}
    nonzero = {t: sum(1 for v in (pos_all.get(t) or {}).values() if v > 0) for t in tags}
    return {
        "pairs": pairs,
        "any_pair_identical": any(v["identical"] for v in pairs.values()),
        "nonzero_slots_per_brain": nonzero,
    }


def _picked_pool_sets(rows: list[dict], tag: str) -> list[int]:
    return [
        int(r["source_set_no"])
        for r in rows
        if r.get("brain_tag") == tag and r.get("source") == "pool"
    ]


def _check_one_draw(dno: int, st: dict[str, Any]) -> dict[str, Any]:
    """회차 1건에 대한 C2·C3·C4 원자료."""
    import app.testlotto.signal_pool as sp

    per_brain: dict[str, Any] = {}
    for tag in sp.BRAIN_TAGS:
        pool = st["pool_br"].get(tag, [])
        if not pool:
            continue
        pos_t = sp.brain_signal(st["pos_all"], tag)
        expect = list(sp.signal_top_set_nos(pool, pos_t))
        picked = _picked_pool_sets(st["rows"], tag)
        labels = {
            r.get("assemble")
            for r in st["rows"]
            if r.get("brain_tag") == tag
        }
        pool_nums = {
            int(c.get("pred_set_no") or 0): sorted(int(x) for x in c["nums"])
            for c in pool
        }
        preserved = all(
            sorted(int(x) for x in r["nums"]) == pool_nums.get(int(r["source_set_no"]))
            for r in st["rows"]
            if r.get("brain_tag") == tag and r.get("source") == "pool"
        )
        signal_all_zero = all(v <= 0 for v in pos_t.values())
        per_brain[tag] = {
            "expected_top": expect,
            "picked": picked,
            # 중복 제거로 슬롯이 밀릴 수 있으므로 '기대 상위에 포함'을 본다
            "picked_subset_of_expected": set(picked).issubset(set(expect)),
            "is_legacy_45": sorted(picked) == [4, 5],
            "labels": sorted(labels),
            "n_pool_slots": len(picked),
            "sets_preserved": bool(preserved),
            "signal_all_zero": bool(signal_all_zero),
        }
    return {"draw_no": dno, "by_brain": per_brain}


def check_determinism(dno: int, seed: int) -> dict[str, Any]:
    """C5 — 같은 seed 두 번이 완전히 같은가."""
    a = _state_at(dno, seed)
    b = _state_at(dno, seed)
    same_rows = [
        (r["brain_tag"], sorted(r["nums"]), r.get("source"), r.get("source_set_no"))
        for r in a["rows"]
    ] == [
        (r["brain_tag"], sorted(r["nums"]), r.get("source"), r.get("source_set_no"))
        for r in b["rows"]
    ]
    return {
        "draw_no": dno,
        "rows_identical": bool(same_rows),
        "pos_tables_identical": a["pos_all"] == b["pos_all"],
    }


def check_no_peek(dno: int, seed: int) -> dict[str, Any]:
    """C6 — dno 시점 신호표가 dno 정답을 반영하지 않는가.

    warm 은 dno 미만까지만 돌아야 한다. dno 정답을 추가로 먹인 표와 다르면 정상.
    """
    import app.testlotto.signal_pool as sp

    st = _state_at(dno, seed)
    before = {t: dict(v) for t, v in st["pos_all"].items()}

    learner = sp.RollingSignalLearner()
    sp.warm_learner_to_draw(learner, max(1, dno - WARM_BACK), dno, seed=seed)
    learner.update_from_pool(st["pool_br"], _actual(dno))
    _, after = learner.snapshot()

    return {
        "draw_no": dno,
        "state_changes_when_actual_fed": bool(before != after),
        "meaning_ko": (
            "True = dno 시점 표에 dno 정답이 안 들어가 있다(정상). "
            "False 면 이미 반영됐다는 뜻이므로 컨닝"
        ),
    }


def check_rng_independent(dno: int, seed: int) -> dict[str, Any]:
    """C7 — 한 뇌만 단독으로 돌려도 같은 세트가 나오는가.

    3뇌를 한 난수 흐름으로 돌리면 앞 뇌의 뽑기 횟수가 뒤 뇌를 바꾼다. 뇌마다
    시드를 리셋하면 「단독 실행」과 「3뇌 함께 실행」의 결과가 같아야 한다.
    """
    import app.testlotto.signal_pool as sp
    from tools._k_window_signal_survey import PREDICT_MODULES

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    together = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))

    per_brain: dict[str, Any] = {}
    for tag in sp.BRAIN_TAGS:
        mod = PREDICT_MODULES.get(tag)
        if mod is None:
            continue
        solo: list[list[int]] = []
        for pass_idx in range(2):
            random.seed(sp._pass_seed(seed, dno, pass_idx))
            solo += [
                sorted(int(x) for x in c["nums"])
                for c in mod.predict_sets(draws, sp.SETS_PER_PREDICT_BRAIN)
            ]
        joint = [
            sorted(int(x) for x in c["nums"])
            for c in sorted(
                together.get(tag, []), key=lambda x: int(x.get("pred_set_no") or 0)
            )
        ]
        per_brain[tag] = {"solo_equals_joint": solo == joint, "n_sets": len(joint)}
    return {
        "draw_no": dno,
        "by_brain": per_brain,
        "all_independent": all(v["solo_equals_joint"] for v in per_brain.values()),
    }


def check_pool_matches_live(dno: int, seed: int) -> dict[str, Any]:
    """C8 — pool 1~5 가 발권 경로(`coordinator`)의 5세트와 같은가.

    `_pass_seed(pass 0)` 은 `coordinator._seed_independent_brain` 과 같은 규칙이므로
    pool 앞 5세트는 실제 티켓 후보와 일치해야 한다. 분석과 발권이 어긋나지 않는지 본다.
    """
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.coordinator import _seed_independent_brain
    from tools._k_window_signal_survey import PREDICT_MODULES

    sp.set_learn_as_of(dno)
    draws = sp._get_draws_before(dno)
    pool_br = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=seed))

    per_brain: dict[str, Any] = {}
    for tag in sp.BRAIN_TAGS:
        mod = PREDICT_MODULES.get(tag)
        if mod is None:
            continue
        _seed_independent_brain(dno)
        live = [
            sorted(int(x) for x in c["nums"])
            for c in mod.predict_sets(draws, sp.SETS_PER_PREDICT_BRAIN)
        ]
        first5 = [
            sorted(int(x) for x in c["nums"])
            for c in sorted(
                pool_br.get(tag, []), key=lambda x: int(x.get("pred_set_no") or 0)
            )[: sp.SETS_PER_PREDICT_BRAIN]
        ]
        per_brain[tag] = {"pool_first5_equals_live": live == first5}
    return {
        "draw_no": dno,
        "by_brain": per_brain,
        "all_match": all(v["pool_first5_equals_live"] for v in per_brain.values()),
        "note_ko": "coordinator 시드 규칙 = MC_SEED(42) + draw_no 여야 성립",
    }


def run(lo: int, hi: int, seed: int) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    per_draw: list[dict[str, Any]] = []
    c1: dict[str, Any] = {}
    for dno in range(lo, hi + 1):
        st = _state_at(dno, seed)
        if not c1:
            c1 = _tables_distinct(st["pos_all"])
        per_draw.append(_check_one_draw(dno, st))
        print(f"  {dno} ok", flush=True)

    tags = list(sp.BRAIN_TAGS)
    agg: dict[str, Any] = {}
    for tag in tags:
        recs = [d["by_brain"][tag] for d in per_draw if tag in d["by_brain"]]
        if not recs:
            continue
        picks: Counter[str] = Counter()
        for r in recs:
            picks[",".join(str(x) for x in sorted(r["picked"]))] += 1
        agg[tag] = {
            "n_draws": len(recs),
            "subset_of_expected_all": all(r["picked_subset_of_expected"] for r in recs),
            "legacy_45_count": sum(1 for r in recs if r["is_legacy_45"]),
            "escaped_45_rate": round(
                sum(1 for r in recs if not r["is_legacy_45"]) / len(recs), 6
            ),
            "labels_seen": sorted({lb for r in recs for lb in r["labels"]}),
            "n_pool_slots_seen": sorted({r["n_pool_slots"] for r in recs}),
            "sets_preserved_all": all(r["sets_preserved"] for r in recs),
            "signal_all_zero_count": sum(1 for r in recs if r["signal_all_zero"]),
            "top_pick_patterns": picks.most_common(5),
        }

    return {
        "c1_tables_separated": c1,
        "c2_c3_c4_by_brain": agg,
        "c5_determinism": check_determinism(hi, seed),
        "c6_no_peek": check_no_peek(hi, seed),
        "c7_rng_independent": check_rng_independent(hi, seed),
        "c8_pool_matches_live": check_pool_matches_live(hi, seed),
        "per_draw": per_draw,
    }


def verdict(res: dict[str, Any], n_slots: int, tags: list[str]) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}

    c1 = res["c1_tables_separated"]
    checks["C1_성적표_뇌별분리"] = {
        "pass": not c1["any_pair_identical"],
        "detail_ko": (
            "3뇌 위치신호표가 서로 다르다 (공유였다면 동일하게 나옴)"
            if not c1["any_pair_identical"]
            else "동일한 뇌 쌍이 있다 → 아직 공유 중"
        ),
    }

    agg = res["c2_c3_c4_by_brain"]
    checks["C2_신호상위_선택"] = {
        "pass": all(v["subset_of_expected_all"] for v in agg.values()),
        "detail_ko": "고른 pool 세트가 전부 신호 상위 집합 안에 있다",
    }
    checks["C2b_4·5고정_이탈"] = {
        "pass": all(v["escaped_45_rate"] > 0 for v in agg.values()),
        "detail_ko": "회차별로 4·5 이외 세트도 골랐다 (고정 아님)",
        "escaped_rate": {t: agg[t]["escaped_45_rate"] for t in agg},
    }
    checks["C3_3뇌_동일배선"] = {
        "pass": (
            sorted(agg.keys()) == sorted(tags)
            and all(v["labels_seen"] == ["signal_top"] for v in agg.values())
            and all(v["n_pool_slots_seen"] == [n_slots] for v in agg.values())
        ),
        "detail_ko": f"3뇌 모두 signal_top · pool 슬롯 {n_slots}개",
        "labels": {t: agg[t]["labels_seen"] for t in agg},
        "slots": {t: agg[t]["n_pool_slots_seen"] for t in agg},
    }
    checks["C4_세트_통째보존"] = {
        "pass": all(v["sets_preserved_all"] for v in agg.values()),
        "detail_ko": "pool 출처 발권 세트의 번호가 pool 세트와 완전히 일치",
    }
    checks["C5_결정성"] = {
        "pass": bool(
            res["c5_determinism"]["rows_identical"]
            and res["c5_determinism"]["pos_tables_identical"]
        ),
        "detail_ko": "같은 seed 두 번이 완전히 동일",
    }
    checks["C6_미래참조_없음"] = {
        "pass": bool(res["c6_no_peek"]["state_changes_when_actual_fed"]),
        "detail_ko": "해당 회차 정답이 그 회차 신호표에 안 들어가 있다",
    }
    checks["C7_뇌간_RNG독립"] = {
        "pass": bool(res["c7_rng_independent"]["all_independent"]),
        "detail_ko": "한 뇌만 단독 실행해도 3뇌 함께 실행과 같은 세트가 나온다",
        "by_brain": res["c7_rng_independent"]["by_brain"],
    }
    checks["C8_pool1~5＝발권세트"] = {
        "pass": bool(res["c8_pool_matches_live"]["all_match"]),
        "detail_ko": "pool 앞 5세트가 발권 경로(coordinator)의 5세트와 일치",
        "by_brain": res["c8_pool_matches_live"]["by_brain"],
    }

    all_pass = all(v["pass"] for v in checks.values())
    return {
        "checks": checks,
        "n_pass": sum(1 for v in checks.values() if v["pass"]),
        "n_total": len(checks),
        "all_pass": all_pass,
        "code": "WIRE_CONFORMS" if all_pass else "WIRE_DEFECT_REMAINS",
    }


def build_md(p: dict[str, Any]) -> str:
    v = p["verdict"]
    agg = p["result"]["c2_c3_c4_by_brain"]
    L = [
        f"# {VERIFY_ID} — 몰아주기 배선 설계일치 검증",
        "",
        f"- 생성 {p['generated_at']} · 회차 {p['range'][0]}~{p['range'][1]} · seed {p['seed']}",
        f"- **{v['code']}** · {v['n_pass']}/{v['n_total']} 통과",
        "",
        "## 0. 이 검증은 성적을 재지 않는다",
        "",
        "「설계 의도와 코드가 일치하는가」만 본다. 적중률이 오르든 말든 통과해야",
        "하는 항목들이며, 그래서 R38 게이트 대상이 아니다.",
        "",
        "## 1. 검사 결과",
        "",
        "|검사|통과|내용|",
        "|---|---|---|",
    ]
    for k, c in v["checks"].items():
        L.append(f"|{k}|{'O' if c['pass'] else 'X'}|{c['detail_ko']}|")

    L += [
        "",
        "## 2. 뇌별 상세",
        "",
        "|뇌|회차|4·5 이탈률|조립 라벨|pool 슬롯|세트 보존|신호0 회차|",
        "|---|---|---|---|---|---|---|",
    ]
    for t, a in agg.items():
        L.append(
            f"|{t}|{a['n_draws']}|{a['escaped_45_rate']:.4f}|"
            f"{','.join(a['labels_seen'])}|{a['n_pool_slots_seen']}|"
            f"{'O' if a['sets_preserved_all'] else 'X'}|{a['signal_all_zero_count']}|"
        )
    L += [
        "",
        "가장 많이 고른 pool 세트 조합:",
        "",
    ]
    for t, a in agg.items():
        pats = " · ".join(f"({k})×{n}" for k, n in a["top_pick_patterns"])
        L.append(f"- **{t}**: {pats}")

    L += [
        "",
        "## 3. 수정 전과 무엇이 달라졌나",
        "",
        "|항목|수정 전|수정 후|",
        "|---|---|---|",
        "|성적표|3뇌가 한 장 공유 (`for _tag`)|뇌별 분리|",
        "|pool 슬롯 선택|`for sn in (4, 5)` 고정|위치 EMA 상위|",
        "|대상 뇌|stat·review 만|3뇌 전부|",
        "|RNG|3뇌를 한 난수 흐름으로 순차 호출|뇌마다 시드 리셋|",
        "|pool pass0 시드|`seed` (발권과 불일치)|`seed+draw_no` (발권과 동일)|",
        "|뇌별 상수|단일 상수|뇌별 dict (**값은 전부 동일** = 성적 무변화)|",
        "",
        "아직 공유 중인 것 (튜닝 과제 · 이번 범위 밖):",
        "",
        f"- **hint 는 3뇌 공유** (`HINT_SHARED_ACROSS_BRAINS={p['config'].get('HINT_SHARED_ACROSS_BRAINS')}`)."
        " 가중치가 가장 크므로 영향이 크지만, 「어느 신호가 어느 뇌에 맞는가」는"
        " 데이터로 정해야 하는 성적 주장이다",
        "",
        "## 4. 한계",
        "",
        "- 이 검증은 **배선 일치**만 본다. 적중률 향상 주장은 별도 판정이 필요하다",
        "- 발권 경로(`coordinator`)는 이번에 건드리지 않았다 —",
        "  실제 티켓은 여전히 3뇌×5세트 → 동적쿼터 5장 경로다",
        f"- 검증 회차 {p['range'][1] - p['range'][0] + 1}건. 초기 회차(신호 전부 0)는 set_no 순서와 같아진다",
        "",
    ]
    return "\n".join(L)


def main() -> None:
    import app.testlotto.signal_pool as sp

    hi = _env_int("K_WV_HI", 0) or _max_draw_no()
    lo = _env_int("K_WV_LO", 0) or DEFAULT_LO
    seed = _env_int("K_WV_SEED", sp.MC_SEED)

    print(f"[{VERIFY_ID}] {lo}~{hi} · seed {seed}", flush=True)
    print(
        f"  ASSEMBLE_MODE={sp.ASSEMBLE_MODE} · POOL_SLOTS={sp.POOL_SLOTS_PER_BRAIN} "
        f"· BRAINS={sorted(sp.SIGNAL_TOP_BRAINS)}",
        flush=True,
    )
    res = run(lo, hi, seed)
    v = verdict(res, sp.POOL_SLOTS_PER_BRAIN, list(sp.BRAIN_TAGS))

    payload = {
        "id": VERIFY_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "range": [lo, hi],
        "seed": seed,
        "config": {
            "ASSEMBLE_MODE": sp.ASSEMBLE_MODE,
            "POOL_SLOTS_BY_BRAIN": dict(sp.POOL_SLOTS_BY_BRAIN),
            "SIGNAL_TOP_BRAINS": sorted(sp.SIGNAL_TOP_BRAINS),
            "SCORE_WEIGHTS_BY_BRAIN": {
                k: list(v) for k, v in sp.SCORE_WEIGHTS_BY_BRAIN.items()
            },
            "LEARN_EMA_BY_BRAIN": dict(sp.LEARN_EMA_BY_BRAIN),
            "HINT_SPEC_BY_BRAIN": {t: list(v) for t, v in sp.HINT_SPEC_BY_BRAIN.items()},
            "HINT_SHARED_ACROSS_BRAINS": sp.hint_shared_across_brains(),
        },
        "policy": {
            "measures_performance": False,
            "note": "설계일치 검증 · R38 게이트 대상 아님",
            "coordinator_touched": False,
        },
        "verdict": v,
        "result": {k: val for k, val in res.items() if k != "per_draw"},
        "per_draw": res["per_draw"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")

    print(f"\n=== {VERIFY_ID} ===")
    for k, c in v["checks"].items():
        print(f"  [{'O' if c['pass'] else 'X'}] {k} — {c['detail_ko']}")
    for t, a in res["c2_c3_c4_by_brain"].items():
        print(
            f"  {t:7s} 4·5이탈 {a['escaped_45_rate']:.4f} · 라벨 {a['labels_seen']} "
            f"· 슬롯 {a['n_pool_slots_seen']} · 보존 {a['sets_preserved_all']}"
        )
    print(f"\n{v['code']} · {v['n_pass']}/{v['n_total']}")
    print(f"-> {OUT_JSON.relative_to(ROOT)}\n-> {OUT_MD.relative_to(ROOT)}")
    sys.exit(0 if v["all_pass"] else 1)


if __name__ == "__main__":
    main()
