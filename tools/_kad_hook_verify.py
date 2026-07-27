# -*- coding: utf-8 -*-
"""K-AD verify: inject dump · BOOT corruption resilience · drift · light regression."""
from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "benchmarks" / "20260727_KAD_hook_inject.json"
BOOT = ROOT / "My_Drive_Sync" / "SUMMARY" / "BOOT.md"
SEED = 20260727
AS_OF = 1234


def run_hook(stdin_obj: dict | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(
        [sys.executable, str(ROOT / ".cursor" / "hooks" / "guard_boot.py")],
        input=json.dumps(stdin_obj or {}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        env=env,
        check=False,
    )
    try:
        out = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        out = {"parse_error": True, "stdout": p.stdout}
    return {
        "returncode": p.returncode,
        "stdout_json": out,
        "stderr": (p.stderr or "")[-2000:],
        "continue": out.get("continue"),
        "additional_context": out.get("additional_context"),
        "n_lines": len((out.get("additional_context") or "").splitlines()),
    }


def main() -> int:
    from rok21_inject import build_inject_text, sync_restore_header, short_head

    # update NEXT hash placeholder
    na = ROOT / "My_Drive_Sync" / "SUMMARY" / "NEXT_ACTIONS.md"
    text = na.read_text(encoding="utf-8")
    head = short_head()
    text2 = text.replace("- 최종갱신: pending", f"- 최종갱신: {head}")
    if text2 != text:
        na.write_text(text2, encoding="utf-8")
    sync_restore_header()

    normal = run_hook({})
    inject_text = normal.get("additional_context") or build_inject_text()

    # 5-2 corruption: backup BOOT, break section 1, run hook, restore
    bak = BOOT.read_text(encoding="utf-8")
    broken_ok = False
    try:
        BOOT.write_text("# BOOT broken\n## 1) 현재 스레드\n(no dashes)\n", encoding="utf-8")
        broken = run_hook({})
        broken_ok = broken.get("continue") is True and broken.get("returncode") == 0
    finally:
        BOOT.write_text(bak, encoding="utf-8")

    # drift
    drift = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "_doc_drift_check.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    drift_json = ROOT / "docs" / "benchmarks" / "20260727_KAC_doc_drift.json"
    n_issues = None
    if drift_json.exists():
        n_issues = json.loads(drift_json.read_text(encoding="utf-8")).get("n_issues")

    # light regression (same as K-AB style)
    reg = {"skipped": False}
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
            "dedup_enabled": dedup_enabled(),
            "E_k": ek,
            "unresolved_total": unresolved,
            "k_all_100": all(k == 100 for k in ks),
            "sha_ok": h1 == h2,
            "sha256": h1,
            "cutoff_on": True,
            "gate_pass": ek == 100.0 and unresolved == 0 and h1 == h2,
        }
    except Exception as e:
        reg = {"error": str(e), "gate_pass": False}

    # resync after boot restore
    sync_restore_header()
    final_inject = build_inject_text()

    result = {
        "meta": {
            "disclaimer": "이 작업은 예측력과 무관하다. 압축 후 즉시 복귀를 위한 운영 인프라다.",
            "head": head,
        },
        "inject_text_full": final_inject,
        "inject_n_lines": len(final_inject.splitlines()),
        "hook_normal": {
            "continue": normal.get("continue"),
            "n_lines": normal.get("n_lines"),
            "returncode": normal.get("returncode"),
        },
        "hook_broken_boot": {
            "continue_true": broken_ok,
            "detail": "BOOT §1 broken temporarily; hook must continue:true",
        },
        "drift": {
            "exit_code": drift.returncode,
            "n_issues": n_issues,
            "stdout_tail": (drift.stdout or "")[-500:],
        },
        "regression": reg,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("INJECT:\n", final_inject)
    print("broken_ok", broken_ok, "drift_n", n_issues, "reg", reg.get("gate_pass"))
    print("WROTE", OUT)
    ok = (
        broken_ok
        and n_issues == 0
        and reg.get("gate_pass")
        and result["inject_n_lines"] <= 15
        and normal.get("continue") is True
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
