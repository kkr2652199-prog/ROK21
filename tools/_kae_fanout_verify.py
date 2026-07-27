# -*- coding: utf-8 -*-
"""K-AE fan-out verify on backup copies — never mutate ops DBs for experiments."""
from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAE_fanout_verify.json"
PATCH = ROOT / "docs" / "benchmarks" / "20260727_KAE_fanout_diff.patch"
TMP = ROOT / "data" / "_kae_fanout_sandbox"
SEED = 20260727
AS_OF = 1234
COLS = (
    "draw_no", "draw_date", "num1", "num2", "num3", "num4", "num5", "num6",
    "bonus", "total_sales", "first_prize", "first_winners", "created_at",
)


def stats(path: Path) -> dict:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    mn, mx, cnt = con.execute(
        "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM lotto_draws"
    ).fetchone()
    con.close()
    return {"min": mn, "max": mx, "count": cnt}


def copy_ops_to_sandbox() -> dict[str, Path]:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    paths = {}
    for name in ("lotto4.db", "lotto_testlotto.db", "lotto_hyodo.db"):
        src = ROOT / "data" / name
        dst = TMP / name
        shutil.copy2(src, dst)
        paths[name] = dst
    return paths


def main() -> int:
    from app.lotto.draw_fanout import fanout_enabled, fanout_from_lotto4

    # --- ops snapshot ---
    ops = {
        "lotto4": stats(ROOT / "data" / "lotto4.db"),
        "testlotto": stats(ROOT / "data" / "lotto_testlotto.db"),
        "hyodo": stats(ROOT / "data" / "lotto_hyodo.db"),
    }

    paths = copy_ops_to_sandbox()
    p4, pt, ph = paths["lotto4.db"], paths["lotto_testlotto.db"], paths["lotto_hyodo.db"]

    # 1) no-op on aligned
    r1 = fanout_from_lotto4(
        None,
        catch_up_missing=True,
        db_lotto4=p4,
        db_testlotto=pt,
        db_hyodo=ph,
    )
    # 2) idempotent second run
    r2 = fanout_from_lotto4(
        None,
        catch_up_missing=True,
        db_lotto4=p4,
        db_testlotto=pt,
        db_hyodo=ph,
    )

    # 3) simulate multi-gap: delete 1233-1234 from hyodo+test copies, fanout catch-up
    for dbp in (pt, ph):
        con = sqlite3.connect(str(dbp))
        con.execute("DELETE FROM lotto_draws WHERE draw_no IN (1233,1234)")
        con.commit()
        con.close()
    gap_before = {"testlotto": stats(pt), "hyodo": stats(ph), "lotto4": stats(p4)}
    r3 = fanout_from_lotto4(
        None,
        catch_up_missing=True,
        db_lotto4=p4,
        db_testlotto=pt,
        db_hyodo=ph,
    )
    gap_after = {"testlotto": stats(pt), "hyodo": stats(ph), "lotto4": stats(p4)}

    # 4) double fanout same draws
    r4a = fanout_from_lotto4(
        [1234],
        catch_up_missing=False,
        db_lotto4=p4,
        db_testlotto=pt,
        db_hyodo=ph,
    )
    r4b = fanout_from_lotto4(
        [1234],
        catch_up_missing=False,
        db_lotto4=p4,
        db_testlotto=pt,
        db_hyodo=ph,
    )
    # uniqueness: count rows for 1234
    def count_no(path, n):
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        c = con.execute("SELECT COUNT(*) FROM lotto_draws WHERE draw_no=?", (n,)).fetchone()[0]
        con.close()
        return c

    # OFF switch
    os.environ["ROK21_FANOUT"] = "0"
    r_off = fanout_from_lotto4(None, catch_up_missing=True, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph)
    os.environ.pop("ROK21_FANOUT", None)

    # regression on real testlotto (read path only for predict)
    reg = {}
    try:
        from app.testlotto.brains.coordinator import PREDICT_MODULES, _apply_aux_scoring
        from app.testlotto.data_service import _get_draws_before
        from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
        from app.testlotto.ticket_dedup import combo_key, dedup_enabled, dedup_ticket_list
        import numpy as np

        os.environ["ROK21_DEDUP"] = "1"
        os.environ.pop("ROK21_LEARN_CUTOFF", None)
        clear_history_cache()
        set_learn_as_of(AS_OF)
        draws = _get_draws_before(AS_OF)
        max_before = max(int(d["draw_no"]) for d in draws)

        def tag_seed(tag: str) -> int:
            return SEED + int(hashlib.md5(tag.encode()).hexdigest()[:8], 16) % 10007

        def make_regen(target):
            def regen(brain_tag, seen, replace_of=None):
                mod = PREDICT_MODULES.get(brain_tag)
                if not mod:
                    return None
                raw = mod.predict_sets(draws, 1)
                if not raw:
                    return None
                return _apply_aux_scoring(raw, draws, target)[0]

            return regen

        random.seed(SEED)
        base = []
        for tag, mod in PREDICT_MODULES.items():
            random.seed(tag_seed(tag))
            base.extend(mod.predict_sets(draws, 40))
        base = _apply_aux_scoring(base[:120], draws, AS_OF)
        rng = random.Random(SEED)
        ks, unresolved = [], 0
        regen = make_regen(AS_OF)
        for _ in range(20):
            batch = [dict(t) for t in rng.sample(base, min(100, len(base)))]
            while len(batch) < 100:
                batch.append(dict(batch[len(batch) % len(batch)]))
            for j in range(3):
                batch[90 + j] = dict(batch[j])
            batch, st = dedup_ticket_list(batch, regenerate=regen)
            ks.append(len({combo_key(t["nums"]) for t in batch}))
            unresolved += int(st["unresolved_count"])
        ek = float(np.mean(ks))

        def run_hash():
            clear_history_cache()
            set_learn_as_of(AS_OF)
            random.seed(SEED)
            cands = []
            for tag, mod in PREDICT_MODULES.items():
                random.seed(tag_seed(tag))
                cands.extend(mod.predict_sets(draws, 20))
            scored = _apply_aux_scoring(cands, draws, AS_OF)
            scored.sort(key=lambda x: -x["confidence"])
            top = [sorted(c["nums"]) for c in scored[:15]]
            return hashlib.sha256(json.dumps(top, separators=(",", ":")).encode()).hexdigest()

        h1, h2 = run_hash(), run_hash()
        reg = {
            "as_of_ok": max_before < AS_OF,
            "E_k": ek,
            "unresolved": unresolved,
            "sha_ok": h1 == h2,
            "dedup_on": dedup_enabled(),
            "gate_pass": ek == 100.0 and unresolved == 0 and h1 == h2 and max_before < AS_OF,
        }
    except Exception as e:
        reg = {"error": str(e), "gate_pass": False}

    # ops still aligned after tests (sandbox only)
    ops_after = {
        "lotto4": stats(ROOT / "data" / "lotto4.db"),
        "testlotto": stats(ROOT / "data" / "lotto_testlotto.db"),
        "hyodo": stats(ROOT / "data" / "lotto_hyodo.db"),
    }

    out = {
        "meta": {
            "disclaimer": "이 작업은 예측력과 무관하다. 수집 파이프라인의 데이터 무결성 확보다.",
            "sandbox": str(TMP),
            "fanout_default_on": fanout_enabled(),
        },
        "ops_before": ops,
        "ops_after_unchanged": ops == ops_after,
        "ops_after": ops_after,
        "noop_aligned": r1,
        "noop_second": r2,
        "multi_gap": {
            "before": gap_before,
            "result": r3,
            "after": gap_after,
            "filled": gap_after["hyodo"]["max"] == 1234 and gap_after["testlotto"]["max"] == 1234,
        },
        "idempotent_same_draw": {
            "first": r4a,
            "second": r4b,
            "count_1234_test": count_no(pt, 1234),
            "count_1234_hyodo": count_no(ph, 1234),
        },
        "switch_off": r_off,
        "regression": reg,
        "path_notes": {
            "hook": "collect_latest_forward → fanout_after_collect (스케줄·수동 공통, K-AB STEP5 옵션2)",
            "hyodo_separate_fetch": "app/hyodo/data_service.fetch_latest_draw 별도 경로 존재 — 팬아웃은 lotto4 소스 내부복사",
            "lotto4_on_fanout_fail": "롤백 안 함 (K-AB). 대상 DB만 트랜잭션 롤백",
        },
    }
    ok = (
        r1.get("note", "").startswith("no-op")
        and r2.get("note", "").startswith("no-op")
        and out["multi_gap"]["filled"]
        and count_no(pt, 1234) == 1
        and count_no(ph, 1234) == 1
        and r_off.get("skipped") is True
        and ops == ops_after
        and reg.get("gate_pass") is True
    )
    out["verify_pass"] = ok
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("verify_pass", ok)
    print("WROTE", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
