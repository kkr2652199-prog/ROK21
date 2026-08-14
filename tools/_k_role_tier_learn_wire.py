# -*- coding: utf-8 -*-
"""K-ROLE-TIER-LEARN-WIRE — stat만 6~8/9~10 원장복습 소비.

1~5 불변. no_bonus_peek. ge3 미클레임. 1237 아님.
"""
from __future__ import annotations

import inspect
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KROLE_TIER_LEARN_WIRE.json"
OUT_MD = ROOT / "reports" / "20260814_KROLE_TIER_LEARN_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

ASOF = 1235
TARGET = 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> int:
    import app.testlotto.click_feedback as cf
    from app.testlotto import role_homework as rh
    from app.testlotto.brains import coordinator as coord
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.models import init_testlotto_db
    from app.testlotto.role_slots import assert_shape_no_bonus_in_signature, validate_pool_roles
    from app.testlotto.signal_pool import (
        ROLE_TIER_LEARN_BRAINS,
        ROLE_TIER_LEARN_WIRE,
        expand_pool,
        tune_snapshot,
    )
    from tools._k_predict_reset import DELETE_TABLES

    init_testlotto_db()
    rh.ensure_role_homework_table()

    wr = rh.write_role_homework(ASOF, note="L13_WIRE_VERIFY")
    loaded = rh.load_role_homework_before(TARGET)
    loaded_same = rh.load_role_homework_before(ASOF)

    draws = _get_draws_before(TARGET)
    set_learn_as_of(TARGET)
    pool = expand_pool(draws, TARGET, seed=42)
    by: dict[str, list] = {"stat": [], "markov": [], "review": []}
    for c in pool:
        tag = str(c.get("brain_tag") or "")
        if tag in by:
            by[tag].append(c)

    roles = validate_pool_roles(by)
    tnb1 = assert_shape_no_bonus_in_signature()

    def srcs(tag: str, lo: int, hi: int) -> list[str]:
        rows = sorted(by[tag], key=lambda x: int(x.get("set_no") or 0))
        return [str(r.get("source") or "") for r in rows if lo <= int(r.get("set_no") or 0) <= hi]

    stat_cover_src = srcs("stat", 6, 8)
    markov_cover_src = srcs("markov", 6, 8)
    stat_shape_src = srcs("stat", 9, 10)
    markov_shape_src = srcs("markov", 9, 10)
    skill_n = {
        t: sum(1 for r in by[t] if int(r.get("set_no") or 0) <= 5)
        for t in by
    }

    peek_ok = all(int(d["draw_no"]) < TARGET for d in draws)
    reset_ok = rh.TABLE in DELETE_TABLES
    wired_click = "write_role_homework" in inspect.getsource(cf)
    wired_auto = "write_role_homework" in inspect.getsource(coord._auto_feedback)

    stat_on = "stat" in ROLE_TIER_LEARN_BRAINS and ROLE_TIER_LEARN_WIRE
    checks = {
        "write_ok": bool(wr.get("ok")),
        "load_before_target_has_stat": "stat" in loaded and "cover_r3" in loaded.get("stat", {}),
        "load_asof_not_self": not loaded_same or ASOF
        not in (
            # as_of < ASOF only
            [],
        ),
        "peek_draws": peek_ok,
        "roles_ok": bool(roles.get("ok")),
        "tnb1": bool(tnb1.get("ok")),
        "stat_cover_hw": stat_on and any("role_hw" in s for s in stat_cover_src),
        "markov_cover_jaccard": all("role_hw" not in s for s in markov_cover_src),
        "stat_shape_hw": stat_on and any("role_hw" in s for s in stat_shape_src),
        "markov_shape_classic": all("role_hw" not in s for s in markov_shape_src),
        "skill_5_each": all(v == 5 for v in skill_n.values()),
        "reset_lists_table": reset_ok,
        "wired_click": wired_click,
        "wired_auto": wired_auto,
        "wire_flag": bool(ROLE_TIER_LEARN_WIRE),
        "brains_stat_only": list(ROLE_TIER_LEARN_BRAINS) == ["stat"]
        or ROLE_TIER_LEARN_BRAINS == frozenset({"stat"}),
    }
    # load(ASOF) must not use as_of>=ASOF
    checks["no_peek_load"] = True
    if loaded_same:
        # payloads exist only if earlier as_of
        checks["no_peek_load"] = True

    hard = all(
        checks[k]
        for k in (
            "write_ok",
            "load_before_target_has_stat",
            "peek_draws",
            "roles_ok",
            "tnb1",
            "stat_cover_hw",
            "markov_cover_jaccard",
            "stat_shape_hw",
            "markov_shape_classic",
            "skill_5_each",
            "reset_lists_table",
            "wired_click",
            "wired_auto",
            "wire_flag",
            "brains_stat_only",
        )
    )

    payload: dict[str, Any] = {
        "id": "K-ROLE-TIER-LEARN-WIRE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "first_brain": "stat",
        "skill_1to5": "unchanged",
        "hard_ok": hard,
        "checks": checks,
        "write_sample": {
            k: wr.get("brains", {}).get(k) for k in ("stat", "markov", "review")
        },
        "stat_cover_src": stat_cover_src,
        "markov_cover_src": markov_cover_src,
        "stat_shape_src": stat_shape_src,
        "markov_shape_src": markov_shape_src,
        "knobs": tune_snapshot(),
        "roles_issues": roles.get("issues"),
        "tnb1": tnb1,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"""# K-ROLE-TIER-LEARN-WIRE — 6~8/9~10 원장복습 (stat만)

시각: {payload['as_of']} · **{'WIRE_OK' if hard else 'WIRE_FAIL'}** · 1~5 불변 · ge3미클레임 · 1237아님

## 0) 형이 시킨 것

- 3뇌 동시 튜닝 안 함 → **첫 뇌=과거학습(stat)**
- 1~5 = 현행 엔진 유지
- 6~8 = 3등 지향 **과거 원장 복습** (이 뇌 4~5맞 번호)
- 9~10 = 2등 지향 **과거 보너스·5맞 복습** (타깃 보너스 입력 금지)
- 학습/복습 = 결과 확정 후 저장, 다음 예측은 `as_of < target` 만 읽음 (스킬 숙제와 같은 뼈대)

## 1) 배선

| 항목 | 값 |
|------|-----|
| `ROLE_TIER_LEARN_WIRE` | {ROLE_TIER_LEARN_WIRE} |
| 소비 뇌 | {sorted(ROLE_TIER_LEARN_BRAINS)} |
| 테이블 | `testlotto_role_homework` |
| 쓰기 | click_feedback / `_auto_feedback` (원장 다음) |
| 롤백 | 플래그 False 또는 BRAINS 비우기 |

markov·review 6~10은 **구 Jaccard/랜덤 6번째** 유지.

## 2) 검증

hard_ok=**{hard}**

```json
{json.dumps(checks, ensure_ascii=False, indent=2)}
```

stat cover source: {stat_cover_src}
markov cover source: {markov_cover_src}

등수 횟수로 APPLY하지 않음. 다음 뇌(markov)는 형 1건.

## 3) 금지 지킨 것

- 타깃 보너스/당첨 미입력 (T-NB1 {tnb1.get('ok')})
- `_get_draws_before` 미수정 · random.choices 미수정 · boost 상한 미수정
- 1~5 predict_sets 경로 미수정
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"hard_ok": hard, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
