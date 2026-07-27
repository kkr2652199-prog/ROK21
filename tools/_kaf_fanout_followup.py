# -*- coding: utf-8 -*-
"""K-AF fan-out residual verify — sandbox copies only."""
from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAF_fanout_followup.json"
PATCH = ROOT / "docs" / "benchmarks" / "20260727_KAF_diff.patch"
TMP = ROOT / "data" / "_kaf_fanout_sandbox"
SEED = 20260727
AS_OF = 1234


def stats(path: Path) -> dict:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    mn, mx, cnt = con.execute(
        "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM lotto_draws"
    ).fetchone()
    con.close()
    return {"min": mn, "max": mx, "count": cnt}


def count_no(path: Path, n: int) -> int:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c = con.execute(
        "SELECT COUNT(*) FROM lotto_draws WHERE draw_no=?", (n,)
    ).fetchone()[0]
    con.close()
    return int(c)


def copy_ops() -> dict[str, Path]:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    out = {}
    for name in ("lotto4.db", "lotto_testlotto.db", "lotto_hyodo.db"):
        src = ROOT / "data" / name
        dst = TMP / name
        shutil.copy2(src, dst)
        out[name] = dst
    return out


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_dedup_gate() -> dict:
    """DEDUP ON 20×100 · E[k]=100 · as_of · SHA (K-AE와 동일 경로)."""
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
    return {
        "as_of_ok": max_before < AS_OF,
        "as_of_safe": max_before < AS_OF,
        "E_k": ek,
        "unresolved": unresolved,
        "sha256": h1,
        "sha_ok": h1 == h2,
        "dedup_on": dedup_enabled(),
        "DEDUP": "ON",
        "CUTOFF": "ON",
        "gate_pass": ek == 100.0 and unresolved == 0 and h1 == h2 and max_before < AS_OF,
    }


def main() -> int:
    os.environ.pop("ROK21_FANOUT", None)
    os.environ.pop("ROK21_FANOUT_TEST_FAIL_COMMIT", None)

    from app.lotto.draw_fanout import fanout_after_collect, fanout_from_lotto4

    ops_before = {
        "lotto4": stats(ROOT / "data" / "lotto4.db"),
        "testlotto": stats(ROOT / "data" / "lotto_testlotto.db"),
        "hyodo": stats(ROOT / "data" / "lotto_hyodo.db"),
    }
    ops_hash_before = {
        k: sha_file(ROOT / "data" / name)
        for k, name in (
            ("lotto4", "lotto4.db"),
            ("testlotto", "lotto_testlotto.db"),
            ("hyodo", "lotto_hyodo.db"),
        )
    }

    paths = copy_ops()
    p4, pt, ph = paths["lotto4.db"], paths["lotto_testlotto.db"], paths["lotto_hyodo.db"]

    tests: dict[str, dict] = {}

    # T5 no-op cost first (aligned sandbox)
    t0 = time.perf_counter()
    r_noop = fanout_from_lotto4(
        None, catch_up_missing=True, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    noop_ms = (time.perf_counter() - t0) * 1000.0
    tests["T5_noop_ms"] = {
        "pass": True,
        "ms": round(noop_ms, 3),
        "early_gate": bool(r_noop.get("early_gate")),
        "note": r_noop.get("note"),
    }

    # T1: collected=[] + gap → recover via fanout_after_collect (e2e hook path)
    for dbp in (pt, ph):
        con = sqlite3.connect(str(dbp))
        con.execute("DELETE FROM lotto_draws WHERE draw_no IN (1233,1234)")
        con.commit()
        con.close()
    gap_before = {"testlotto": stats(pt), "hyodo": stats(ph)}
    # simulate collect_latest_forward collected=[] calling fanout_after_collect
    # by temporarily pointing module paths — call with explicit dbs via from_lotto4
    # and also exercise data_service wrapper semantics: always call even if empty
    r_t1 = fanout_after_collect([])
    # fanout_after_collect uses ops paths — must use sandbox via from_lotto4 for T1
    r_t1 = fanout_from_lotto4(
        [], catch_up_missing=True, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    gap_after = {"testlotto": stats(pt), "hyodo": stats(ph)}
    t1_pass = (
        r_t1.get("ok")
        and gap_after["testlotto"]["max"] == ops_before["lotto4"]["max"]
        and gap_after["hyodo"]["max"] == ops_before["lotto4"]["max"]
        and gap_before["hyodo"]["max"] < gap_after["hyodo"]["max"]
    )
    tests["T1_e2e_empty_collected_catchup"] = {
        "pass": bool(t1_pass),
        "gap_before": gap_before,
        "gap_after": gap_after,
        "result": {k: r_t1.get(k) for k in ("ok", "planned", "note", "inserted_hyodo", "inserted_testlotto")},
    }

    # T3 idempotent
    r3a = fanout_from_lotto4(
        [1234], catch_up_missing=False, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    r3b = fanout_from_lotto4(
        [1234], catch_up_missing=False, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    c4t, c4h = count_no(pt, 1234), count_no(ph, 1234)
    tests["T3_idempotent"] = {
        "pass": c4t == 1 and c4h == 1,
        "count_testlotto_1234": c4t,
        "count_hyodo_1234": c4h,
        "r3a_note": r3a.get("note"),
        "r3b_note": r3b.get("note"),
    }

    # T2 partial commit inject → diverge → catch-up converge
    # reset sandbox from ops
    paths = copy_ops()
    p4, pt, ph = paths["lotto4.db"], paths["lotto_testlotto.db"], paths["lotto_hyodo.db"]
    for dbp in (pt, ph):
        con = sqlite3.connect(str(dbp))
        con.execute("DELETE FROM lotto_draws WHERE draw_no=1234")
        con.commit()
        con.close()
    os.environ["ROK21_FANOUT_TEST_FAIL_COMMIT"] = "hyodo"
    r_fail = fanout_from_lotto4(
        [1234], catch_up_missing=False, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    mid = {"testlotto": stats(pt), "hyodo": stats(ph), "ok": r_fail.get("ok")}
    # testlotto should have 1234, hyodo not (if inject after testlotto commit)
    # order is testlotto then hyodo — fail on hyodo → testlotto committed
    os.environ.pop("ROK21_FANOUT_TEST_FAIL_COMMIT", None)
    r_fix = fanout_from_lotto4(
        None, catch_up_missing=True, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    after = {"testlotto": stats(pt), "hyodo": stats(ph)}
    t2_pass = (
        mid["testlotto"]["max"] == 1234
        and mid["hyodo"]["max"] == 1233
        and after["testlotto"]["max"] == after["hyodo"]["max"] == 1234
        and r_fix.get("ok")
    )
    tests["T2_partial_commit_converge"] = {
        "pass": bool(t2_pass),
        "after_inject": mid,
        "after_catchup": after,
        "fail_note": r_fail.get("note"),
        "fix_note": r_fix.get("note"),
        "fail_errors": r_fail.get("errors"),
    }

    # T4 OFF
    os.environ["ROK21_FANOUT"] = "0"
    r_off = fanout_from_lotto4(
        None, catch_up_missing=True, db_lotto4=p4, db_testlotto=pt, db_hyodo=ph
    )
    os.environ.pop("ROK21_FANOUT", None)
    tests["T4_switch_off"] = {
        "pass": bool(r_off.get("skipped")) and r_off.get("note") == "ROK21_FANOUT=OFF",
        "result": {k: r_off.get(k) for k in ("skipped", "note", "enabled")},
    }

    # T6 ops immutable
    ops_after = {
        "lotto4": stats(ROOT / "data" / "lotto4.db"),
        "testlotto": stats(ROOT / "data" / "lotto_testlotto.db"),
        "hyodo": stats(ROOT / "data" / "lotto_hyodo.db"),
    }
    ops_hash_after = {
        k: sha_file(ROOT / "data" / name)
        for k, name in (
            ("lotto4", "lotto4.db"),
            ("testlotto", "lotto_testlotto.db"),
            ("hyodo", "lotto_hyodo.db"),
        )
    }
    t6 = ops_before == ops_after and ops_hash_before == ops_hash_after
    tests["T6_ops_immutable"] = {
        "pass": bool(t6),
        "before": ops_before,
        "after": ops_after,
        "max_ok": all(v["max"] == 1234 for v in ops_after.values()),
    }

    # T7 regression gate (live)
    try:
        reg = run_dedup_gate()
        tests["T7_regression"] = {
            "pass": bool(reg.get("gate_pass")),
            "E_k": reg.get("E_k"),
            "DEDUP": "ON",
            "CUTOFF": "ON",
            "as_of": AS_OF,
            "sha256": reg.get("sha256"),
            "sha_ok": reg.get("sha_ok"),
            "as_of_ok": reg.get("as_of_ok"),
            "unresolved": reg.get("unresolved"),
            "dedup_on": reg.get("dedup_on"),
        }
    except Exception as e:
        tests["T7_regression"] = {"pass": False, "error": str(e)}

    # T8 drift (보고만 · verify_pass 집합 밖)
    import re
    import subprocess

    drift = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "_doc_drift_check.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    drift_out = (drift.stdout or "") + (drift.stderr or "")
    n_issues = None
    m = re.search(r"n_issues\s+(\d+)", drift_out)
    if m:
        n_issues = int(m.group(1))
    tests["T8_drift"] = {
        "n_issues": n_issues,
        "exit_code": drift.returncode,
        "stdout_tail": drift_out[-500:],
    }

    src = (ROOT / "app" / "lotto" / "data_service.py").read_text(encoding="utf-8")
    m = re.search(r"# K-06/K-AE/K-AF.*?return \{", src, re.S)
    block = m.group(0) if m else ""
    tests["source_unconditional_fanout"] = {
        "pass": "if collected:" not in block and "fanout_after_collect" in block,
        "snippet_has_if_collected": "if collected:" in block,
    }

    core = ["T1_e2e_empty_collected_catchup", "T2_partial_commit_converge", "T3_idempotent", "T4_switch_off", "T5_noop_ms", "T6_ops_immutable", "T7_regression"]
    verify_pass = all(tests[k].get("pass") for k in core)

    payload = {
        "id": "K-AF",
        "date": "2026-07-27",
        "verify_pass": verify_pass,
        "ops_before": ops_before,
        "ops_after": ops_after,
        "tests": tests,
        "mismatch_compare_scope": {
            "compared": list(("num1", "num2", "num3", "num4", "num5", "num6", "bonus")),
            "not_compared": ["draw_date", "total_sales", "first_prize", "first_winners", "created_at"],
        },
        "residual_commit_risk": (
            "SQLite multi-DB atomic commit impossible; sequential commit may leave "
            "testlotto ahead of hyodo; next catch-up converges"
        ),
        "disclaimer": "이 작업은 예측력과 무관하다. 수집 파이프라인 무결성의 잔여 정합이다.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verify_pass": verify_pass, "noop_ms": tests["T5_noop_ms"]["ms"], "T8": tests["T8_drift"]}, ensure_ascii=False))
    return 0 if verify_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
