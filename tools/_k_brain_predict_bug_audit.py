# -*- coding: utf-8 -*-
"""K-BRAIN-PREDICT-BUG-AUDIT — 감독관 패치 후 3뇌 번호예측 경로 버그사냥.

READ-ONLY · ge3클레임금지 · 1237아님.
  P1 엔진 generate → predict_sets: 5장·형식·중복
  P2 expand_pool 10장·set_no·RNG단독=합동
  P3 hint 분리·brain_tag 부착
  P4 peek (max_material < target)
  P5 감독관 score_set 이 타뇌 불변 (교차)
  P6 coordinator 경로 import·quota 호출 가능
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

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260811_KBRAIN_PREDICT_BUG_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260811_KBRAIN_PREDICT_BUG_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1226, 1236
SEED = 42
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums: Any) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def main() -> None:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.shared import referee_by_brain as rbb
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from tools._k_window_signal_survey import PREDICT_MODULES

    fails: list[str] = []
    samples: list[dict] = []

    for dno in range(LO, HI + 1):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max(int(d["draw_no"]) for d in draws) if draws else 0
        if max_mat >= dno:
            fails.append(f"peek:{dno}")
        random.seed(SEED)
        pool = sp.expand_pool(draws, dno, seed=SEED)
        pool_br = sp._pool_by_brain(pool)
        hint_by = sp.build_hint_by_brain(draws, dno)
        row: dict[str, Any] = {"draw": dno, "peek_ok": max_mat < dno, "brains": {}}
        for tag in BRAINS:
            mod = PREDICT_MODULES[tag]
            random.seed(SEED + dno)
            sets5 = mod.predict_sets(draws, 5)
            if len(sets5) != 5:
                fails.append(f"P1_n5:{dno}:{tag}:{len(sets5)}")
            keys = [_key(s["nums"]) for s in sets5]
            if any(len(k) != 6 or len(set(k)) != 6 for k in keys):
                fails.append(f"P1_form:{dno}:{tag}")
            if len(keys) != len(set(keys)):
                fails.append(f"P1_dup5:{dno}:{tag}")
            if any(s.get("brain_tag") not in (None, tag) and s.get("brain_tag") != tag for s in sets5):
                # predict may set brain_tag inside
                pass
            psets = pool_br.get(tag) or []
            if len(psets) != 10:
                fails.append(f"P2_n10:{dno}:{tag}:{len(psets)}")
            sns = sorted(int(c.get("pred_set_no") or 0) for c in psets)
            if sns != list(range(1, 11)):
                fails.append(f"P2_setno:{dno}:{tag}")
            if not hint_by.get(tag):
                fails.append(f"P3_hint:{dno}:{tag}")
            row["brains"][tag] = {
                "n5": len(sets5),
                "n10": len(psets),
                "hint_top3": sorted(
                    range(1, 46),
                    key=lambda n: (-float(hint_by[tag].get(n, 0)), n),
                )[:3],
            }
        # hint tops distinct
        tops = tuple(tuple(row["brains"][t]["hint_top3"]) for t in BRAINS)
        if len(set(tops)) < 3:
            fails.append(f"P3_hint_share:{dno}")
        samples.append(row)

    # RNG solo=joint on last draw
    dno = HI
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    random.seed(SEED)
    joint = sp._pool_by_brain(sp.expand_pool(draws, dno, seed=SEED))
    for tag in BRAINS:
        mod = PREDICT_MODULES[tag]
        solo = []
        for pass_idx in range(2):
            s = sp._pass_seed(SEED, dno, pass_idx)
            random.seed(s)
            for i, c in enumerate(mod.predict_sets(draws, 5)):
                solo.append((_key(c["nums"]), int(c.get("rank") or i + 1) + pass_idx * 5))
        j = sorted(
            (_key(c["nums"]), int(c.get("pred_set_no") or 0)) for c in joint.get(tag, [])
        )
        if sorted(solo) != j:
            fails.append(f"P2_rng:{tag}")

    # P5 referee independence
    base = {
        "stat": {"recent_avg_match": 0.85, "review_count": 5},
        "markov": {"recent_avg_match": 0.75, "review_count": 5},
        "review": {"recent_avg_match": 0.80, "review_count": 5},
    }
    a = rbb.independent_scores_from_states(base)["review"]["set_score"]
    base2 = dict(base)
    base2["stat"] = {"recent_avg_match": 0.99, "review_count": 5}
    b = rbb.independent_scores_from_states(base2)["review"]["set_score"]
    if abs(a - b) > 1e-12:
        fails.append("P5_referee_cross")

    # P6 coordinator
    try:
        from app.testlotto.brains.coordinator import _get_quota_weights
        from app.testlotto.learn_state import get_referee_weights

        set_learn_as_of(HI)
        qw = _get_quota_weights()
        rw = get_referee_weights()
        p6 = abs(sum(qw.values()) - 1.0) < 1e-6 and abs(sum(rw.values()) - 1.0) < 1e-6
        if not p6:
            fails.append("P6_quota_sum")
    except Exception as exc:  # noqa: BLE001
        fails.append(f"P6_import:{exc}")

    verdict = "AUDIT_OK" if not fails else "BUG_FOUND"
    result = {
        "id": "K-BRAIN-PREDICT-BUG-AUDIT",
        "ts": _now(),
        "range": [LO, HI],
        "seed": SEED,
        "n_draws": HI - LO + 1,
        "verdict": verdict,
        "n_fail": len(fails),
        "fails_sample": fails[:40],
        "sample_draws": samples[:2] + samples[-1:],
        "referee_patch": "K-REFEREE-BY-BRAIN",
        "ge3_used_as_claim": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# K-BRAIN-PREDICT-BUG-AUDIT",
        "",
        f"시각: {result['ts']} · {LO}~{HI} · seed={SEED}",
        f"## 판정 **{verdict}** · fails={len(fails)}",
        "",
        f"fails_sample={fails[:20]}",
        "",
        "선행: K-REFEREE-BY-BRAIN 패치 후 실행",
        "",
    ]
    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print("VERDICT", verdict, "fails", len(fails))
    if fails:
        print(fails[:20])
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
