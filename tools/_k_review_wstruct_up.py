# -*- coding: utf-8 -*-
"""K-REVIEW-WSTRUCT-UP — review W_STRUCT 0.10→0.20 측정 후 게이트 통과 시만 APPLY.

review만. markov 0.90/0.10 불변. 숙제/covering/S2/1237 금지.
게이트: hi32 Δ>0(Ziemba 축) · fw prize Δ≤+0.005(군중락 비악화) · peek0.
실패=HOLD · 노브 미변경.
"""
from __future__ import annotations

import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from tools._k_brain_independent_tune import _fw_proxy, _top15

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREVIEW_WSTRUCT_UP.json"
OUT_MD = ROOT / "reports" / "20260815_KREVIEW_WSTRUCT_UP.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
CS_PATH = ROOT / "app" / "testlotto" / "brains" / "shared" / "crowd_signal.py"

LO, HI = 1137, 1236
SEED = 42
BASE_C, BASE_S = 0.90, 0.10
CAND_C, CAND_S = 0.80, 0.20
FW_ISO = 0.005
HI32 = frozenset(range(32, 46))
END089 = frozenset(n for n in range(1, 46) if n % 10 in (0, 8, 9))


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _patch(wc: float, ws: float):
    saved_c = dict(cs.W_CROWD_BY_BRAIN)
    saved_s = dict(cs.W_STRUCT_BY_BRAIN)
    cs.W_CROWD_BY_BRAIN["review"] = float(wc)
    cs.W_STRUCT_BY_BRAIN["review"] = float(ws)
    # markov 고정
    cs.W_CROWD_BY_BRAIN["markov"] = float(saved_c.get("markov", 0.90))
    cs.W_STRUCT_BY_BRAIN["markov"] = float(saved_s.get("markov", 0.10))

    def restore() -> None:
        cs.W_CROWD_BY_BRAIN.clear()
        cs.W_CROWD_BY_BRAIN.update(saved_c)
        cs.W_STRUCT_BY_BRAIN.clear()
        cs.W_STRUCT_BY_BRAIN.update(saved_s)

    return restore


def _run(wc: float, ws: float) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    restore = _patch(wc, ws)
    peek = 0
    fw_ds: list[float] = []
    hi: list[float] = []
    en: list[float] = []
    n_ok = 0
    try:
        for dno in range(LO, HI + 1):
            sp.set_learn_as_of(dno)
            draws = _get_draws_before(dno)
            mx = max((int(d["draw_no"]) for d in draws), default=0)
            if mx >= dno:
                peek += 1
                continue
            fw = _fw_proxy(draws)
            uni = mean(fw[n] for n in range(1, 46))
            random.seed(SEED)
            pool = sp.expand_pool(draws, dno, seed=SEED, brains=["review"])
            pool_br = sp._pool_by_brain(pool)
            rev = pool_br.get("review") or []
            if not rev:
                continue
            learner = sp.RollingSignalLearner()
            num_ema, pos_ema = learner.snapshot()
            hint_by = sp.build_hint_by_brain(draws, dno)
            scores = sp.number_scores(
                rev,
                hint_by.get("review", sp._build_hint(draws, dno)),
                num_ema,
                pos_ema,
                brain_tag="review",
            )
            top = _top15(scores)
            fw_ds.append(mean(fw[n] for n in top) - uni)
            for s in rev:
                nums = [int(x) for x in (s.get("nums") or [])]
                if len(nums) != 6:
                    continue
                hi.append(sum(1 for n in nums if n in HI32))
                en.append(sum(1 for n in nums if n in END089))
            n_ok += 1
    finally:
        restore()
    return {
        "wc": wc,
        "ws": ws,
        "n": n_ok,
        "peek": peek,
        "fw_prize": round(mean(fw_ds), 6) if fw_ds else None,
        "hi32": round(mean(hi), 4) if hi else None,
        "end089": round(mean(en), 4) if en else None,
    }


def _apply_knobs() -> None:
    text = CS_PATH.read_text(encoding="utf-8")
    text2 = re.sub(
        r'W_CROWD_BY_BRAIN: dict\[str, float\] = \{"markov": 0\.90, "review": 0\.90\}',
        'W_CROWD_BY_BRAIN: dict[str, float] = {"markov": 0.90, "review": 0.80}',
        text,
        count=1,
    )
    text2 = re.sub(
        r'W_STRUCT_BY_BRAIN: dict\[str, float\] = \{"markov": 0\.10, "review": 0\.10\}',
        'W_STRUCT_BY_BRAIN: dict[str, float] = {"markov": 0.10, "review": 0.20}',
        text2,
        count=1,
    )
    if text2 == text:
        raise RuntimeError("knob replace failed")
    note = "# review W_STRUCT=0.20: K-REVIEW-WSTRUCT-UP APPLY (markov 0.10 불변)\n"
    if "K-REVIEW-WSTRUCT-UP" not in text2:
        text2 = text2.replace(
            "W_CROWD_BY_BRAIN: dict[str, float]",
            note + "W_CROWD_BY_BRAIN: dict[str, float]",
            1,
        )
    CS_PATH.write_text(text2, encoding="utf-8")
    cs.W_CROWD_BY_BRAIN["review"] = 0.80
    cs.W_STRUCT_BY_BRAIN["review"] = 0.20


def main() -> int:
    pre = {
        "review_c": cs.W_CROWD_BY_BRAIN.get("review"),
        "review_s": cs.W_STRUCT_BY_BRAIN.get("review"),
        "markov_c": cs.W_CROWD_BY_BRAIN.get("markov"),
        "markov_s": cs.W_STRUCT_BY_BRAIN.get("markov"),
    }
    lock_ok = (
        abs(float(pre["review_c"]) - BASE_C) < 1e-12
        and abs(float(pre["review_s"]) - BASE_S) < 1e-12
        and abs(float(pre["markov_c"]) - 0.90) < 1e-12
    )
    print("[WSTRUCT] measure base", flush=True)
    base = _run(BASE_C, BASE_S)
    print("[WSTRUCT] measure cand", base, flush=True)
    cand = _run(CAND_C, CAND_S)
    print("[WSTRUCT] cand", cand, flush=True)

    d_fw = None
    d_hi = None
    d_en = None
    if base["fw_prize"] is not None and cand["fw_prize"] is not None:
        d_fw = round(cand["fw_prize"] - base["fw_prize"], 6)
    if base["hi32"] is not None and cand["hi32"] is not None:
        d_hi = round(cand["hi32"] - base["hi32"], 4)
    if base["end089"] is not None and cand["end089"] is not None:
        d_en = round(cand["end089"] - base["end089"], 4)

    hard = {
        "lock_ok": lock_ok,
        "peek_base": base["peek"],
        "peek_cand": cand["peek"],
        "n_base": base["n"],
        "n_cand": cand["n"],
        "d_fw": d_fw,
        "d_hi32": d_hi,
        "d_end089": d_en,
        "hi32_up": bool(d_hi is not None and d_hi > 0),
        "fw_iso": bool(d_fw is not None and d_fw <= FW_ISO),
        "markov_untouched": True,
    }
    apply_ok = (
        lock_ok
        and base["peek"] == 0
        and cand["peek"] == 0
        and base["n"] == 100
        and cand["n"] == 100
        and hard["hi32_up"]
        and hard["fw_iso"]
    )
    applied = False
    if apply_ok:
        _apply_knobs()
        applied = True
        verdict = "APPLY_OK"
    else:
        verdict = "HOLD"

    payload = {
        "id": "K-REVIEW-WSTRUCT-UP",
        "as_of": _now(),
        "verdict": verdict,
        "applied": applied,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "seed": SEED,
        "base": base,
        "cand": cand,
        "delta": {"fw_prize": d_fw, "hi32": d_hi, "end089": d_en},
        "hard": hard,
        "pre": pre,
        "gate": {
            "hi32_up": hard["hi32_up"],
            "fw_d_le_005": hard["fw_iso"],
            "peek0": base["peek"] == 0 and cand["peek"] == 0,
        },
        "rollback": "W_CROWD review=0.90 · W_STRUCT review=0.10",
    }

    lines = [
        "# K-REVIEW-WSTRUCT-UP",
        "",
        f"시각: {payload['as_of']} · **{verdict}** · review만 · 1237아님 · hits 클레임 금지",
        f"후보=W_CROWD 0.90→0.80 · W_STRUCT 0.10→0.20 (합1). markov 0.90/0.10 불변. seed={SEED} · {LO}–{HI} n100.",
        "",
        f"APPLY={'함' if applied else '안 함(HOLD)'}.",
        "",
        "## 1) 측정",
        "",
        "| 설정 | n | peek | fw_prize | hi32 | end089 |",
        "|------|---|------|----------|------|--------|",
        f"| base 0.90/0.10 | {base['n']} | {base['peek']} | {base['fw_prize']} | {base['hi32']} | {base['end089']} |",
        f"| cand 0.80/0.20 | {cand['n']} | {cand['peek']} | {cand['fw_prize']} | {cand['hi32']} | {cand['end089']} |",
        f"| Δ | | | {d_fw} | {d_hi} | {d_en} |",
        "",
        "fw_prize=top15 번호의 first_winners편차(음수=군중 비인기). hi32=세트당 고번호 개수(Ziemba).",
        "",
        "## 2) 게이트",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| peek | {base['peek']}/{cand['peek']} |",
        f"| hi32 Δ>0 | {hard['hi32_up']} ({d_hi}) |",
        f"| fw Δ≤+0.005 | {hard['fw_iso']} ({d_fw}) |",
        f"| markov 노브 | 불변 |",
        "",
        "## 3) 판정",
        "",
        "통과 시에만 코드 노브 변경. 캐시 재생성은 이번 도구에 없음(측정 전용 경로).",
        "실패=HOLD · 이전 K-W-CROWD 0.90 락 유지.",
        "",
        "## 4) 금지 확인",
        "",
        "숙제ON·covering·S2·apply_learn_boost복사·1237 없음. 동결 토큰 미수정.",
        "",
    ]
    text = "\n".join(lines)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "applied": applied, "d_fw": d_fw, "d_hi": d_hi, "d_en": d_en}, ensure_ascii=False))
    return 0 if verdict in ("APPLY_OK", "HOLD") else 1


if __name__ == "__main__":
    raise SystemExit(main())
