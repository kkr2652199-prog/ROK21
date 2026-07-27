# -*- coding: utf-8 -*-
"""K-AB STEP3+4: backup, INSERT missing draws lotto4→hyodo, reverify, regression."""
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

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BACKUP_DIR = ROOT / "data" / "_backup_20260727"
HASH_FILE = ROOT / "docs" / "benchmarks" / "20260727_KAB_backup_hashes.txt"
GAP_JSON = ROOT / "docs" / "benchmarks" / "20260727_KAB_draw_gap.json"
DBS = {
    "lotto4": ROOT / "data" / "lotto4.db",
    "testlotto": ROOT / "data" / "lotto_testlotto.db",
    "hyodo": ROOT / "data" / "lotto_hyodo.db",
}
SEED = 20260727
AS_OF = 1234
COLS = (
    "draw_no",
    "draw_date",
    "num1",
    "num2",
    "num3",
    "num4",
    "num5",
    "num6",
    "bonus",
    "total_sales",
    "first_prize",
    "first_winners",
    "created_at",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_all() -> dict[str, str]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    hashes = {}
    lines = [f"# K-AB backup {BACKUP_DIR}", f"# created before INSERT"]
    for name, src in DBS.items():
        if not src.exists():
            lines.append(f"MISSING {name} {src}")
            continue
        dst = BACKUP_DIR / src.name
        shutil.copy2(src, dst)
        dig = sha256_file(dst)
        hashes[name] = dig
        lines.append(f"{name}\t{src.name}\t{dst.stat().st_size}\t{dig}")
        print("backed up", name, dig[:16], flush=True)
    HASH_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return hashes


def insert_missing_hyodo() -> dict:
    src = sqlite3.connect(str(DBS["lotto4"]))
    dst = sqlite3.connect(str(DBS["hyodo"]))
    src_nos = {r[0] for r in src.execute("SELECT draw_no FROM lotto_draws")}
    dst_nos = {r[0] for r in dst.execute("SELECT draw_no FROM lotto_draws")}
    missing = sorted(src_nos - dst_nos)
    inserted = []
    skipped_existing = []
    for n in missing:
        row = src.execute(
            f"SELECT {','.join(COLS)} FROM lotto_draws WHERE draw_no=?", (n,)
        ).fetchone()
        if row is None:
            continue
        # refuse UPDATE — only INSERT OR IGNORE
        cur = dst.execute(
            f"INSERT OR IGNORE INTO lotto_draws ({','.join(COLS)}) "
            f"VALUES ({','.join('?' for _ in COLS)})",
            row,
        )
        if cur.rowcount == 1:
            inserted.append(n)
        else:
            skipped_existing.append(n)
    dst.commit()
    # verify no updates to prior rows: check 1231 still same as backup
    bak = sqlite3.connect(str(BACKUP_DIR / "lotto_hyodo.db"))
    before_1231 = bak.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=1231"
    ).fetchone()
    after_1231 = dst.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=1231"
    ).fetchone()
    bak.close()
    src.close()
    dst.close()
    return {
        "missing_planned": missing,
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "prior_row_1231_unchanged": before_1231 == after_1231,
    }


def stats(path: Path) -> dict:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    mn, mx, cnt = con.execute(
        "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM lotto_draws"
    ).fetchone()
    nos = [r[0] for r in con.execute("SELECT draw_no FROM lotto_draws ORDER BY 1")]
    holes = [n for n in range(mn, mx + 1) if n not in set(nos)] if nos else []
    con.close()
    return {"min": mn, "max": mx, "count": cnt, "holes": holes}


def recompare() -> dict:
    maps = {}
    for name, path in DBS.items():
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        m = {}
        for r in con.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws"
        ):
            m[int(r[0])] = tuple(r[1:])
        con.close()
        maps[name] = m
    out = {}
    for a, b in (("lotto4", "testlotto"), ("lotto4", "hyodo"), ("testlotto", "hyodo")):
        common = sorted(set(maps[a]) & set(maps[b]))
        mism = [
            n for n in common if maps[a][n] != maps[b][n]
        ]
        out[f"{a}_vs_{b}"] = {
            "n_common": len(common),
            "n_mismatch": len(mism),
            "mismatches": mism,
            "only_a": sorted(set(maps[a]) - set(maps[b])),
            "only_b": sorted(set(maps[b]) - set(maps[a])),
        }
    return out


def rollback_hyodo():
    src = BACKUP_DIR / "lotto_hyodo.db"
    dst = DBS["hyodo"]
    shutil.copy2(src, dst)
    print("ROLLED BACK hyodo from backup", flush=True)


def step4_regression() -> dict:
    """K-S/K-V style gates on testlotto (hyodo draws sync does not change testlotto code path)."""
    from app.testlotto.brains.coordinator import PREDICT_MODULES, _apply_aux_scoring
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import clear_history_cache, set_learn_as_of
    from app.testlotto.ticket_dedup import combo_key, dedup_enabled, dedup_ticket_list

    os.environ["ROK21_DEDUP"] = "1"
    os.environ.pop("ROK21_LEARN_CUTOFF", None)
    clear_history_cache()
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    # as_of path: draws must be all < AS_OF
    max_before = max(int(d["draw_no"]) for d in draws) if draws else None
    as_of_ok = max_before is not None and max_before < AS_OF

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
    ks = []
    unresolved = 0
    regen = make_regen(AS_OF)
    t0 = time.perf_counter()
    for _ in range(20):
        batch = [dict(t) for t in rng.sample(base, min(100, len(base)))]
        while len(batch) < 100:
            batch.append(dict(batch[len(batch) % len(batch)]))
        for j in range(3):
            batch[90 + j] = dict(batch[j])
        batch, st = dedup_ticket_list(batch, regenerate=regen)
        ks.append(len({combo_key(t["nums"]) for t in batch}))
        unresolved += int(st["unresolved_count"])
    dedup_sec = time.perf_counter() - t0
    ek = float(np.mean(ks))
    dedup_ok = dedup_enabled() and ek == 100.0 and unresolved == 0 and all(k == 100 for k in ks)

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
    sha_ok = h1 == h2
    cutoff_on = "ROK21_LEARN_CUTOFF" not in os.environ or os.environ.get(
        "ROK21_LEARN_CUTOFF"
    ) not in ("0", "false", "OFF", "off")

    # BENCH path safety: recent-100 window still well-defined at MAX=1234
    con = sqlite3.connect(f"file:{DBS['testlotto']}?mode=ro", uri=True)
    tmax = con.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
    n100 = con.execute(
        "SELECT COUNT(*) FROM lotto_draws WHERE draw_no BETWEEN ? AND ?",
        (tmax - 99, tmax),
    ).fetchone()[0]
    con.close()
    bench_ok = int(n100) == 100 and int(tmax) == 1234

    # hyodo as_of readiness: MAX now 1234
    hy = stats(DBS["hyodo"])
    hyodo_ok = hy["max"] == 1234 and hy["count"] == 1234 and not hy["holes"]

    gate = as_of_ok and dedup_ok and sha_ok and cutoff_on and bench_ok and hyodo_ok
    return {
        "as_of": AS_OF,
        "draws_before_max": max_before,
        "as_of_ok": as_of_ok,
        "cutoff_default_on": cutoff_on,
        "E_k": ek,
        "unresolved_total": unresolved,
        "dedup_ok": dedup_ok,
        "dedup_seconds": dedup_sec,
        "sha256_run1": h1,
        "sha256_run2": h2,
        "sha_ok": sha_ok,
        "bench_window_n100": n100,
        "bench_ok": bench_ok,
        "hyodo_stats": hy,
        "hyodo_aligned": hyodo_ok,
        "gate_pass": gate,
    }


def main():
    gap = json.loads(GAP_JSON.read_text(encoding="utf-8"))
    if gap["meta"].get("halt_on_mismatch"):
        print("ABORT: mismatch in STEP1")
        return 2
    if not gap.get("step3_allowed"):
        print("ABORT: step3 not allowed")
        return 2

    print("STEP3 backup...", flush=True)
    hashes = backup_all()
    print("STEP3 insert hyodo...", flush=True)
    ins = insert_missing_hyodo()
    print(ins, flush=True)
    if not ins["prior_row_1231_unchanged"]:
        rollback_hyodo()
        return 3

    post_stats = {n: stats(p) for n, p in DBS.items()}
    cmp = recompare()
    print("post_stats", post_stats, flush=True)
    print("recompare mismatches", {k: v["n_mismatch"] for k, v in cmp.items()}, flush=True)
    if any(v["n_mismatch"] for v in cmp.values()):
        rollback_hyodo()
        return 4

    print("STEP4 regression...", flush=True)
    reg = step4_regression()
    print("gate", reg["gate_pass"], "Ek", reg["E_k"], "sha", reg["sha_ok"], flush=True)
    if not reg["gate_pass"]:
        rollback_hyodo()
        return 5

    # merge into gap json
    gap["step3"] = {
        "backup_dir": str(BACKUP_DIR),
        "backup_hashes_file": str(HASH_FILE),
        "backup_sha256": hashes,
        "insert": ins,
        "post_stats": post_stats,
        "recompare": cmp,
    }
    gap["step4_regression"] = reg
    gap["meta"]["read_only"] = False
    gap["meta"]["corrected"] = True
    GAP_JSON.write_text(json.dumps(gap, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", GAP_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
