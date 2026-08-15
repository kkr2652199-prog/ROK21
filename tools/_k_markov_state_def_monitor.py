# -*- coding: utf-8 -*-
"""K-MARKOV-STATE-DEF-MONITOR — 권고4A 전이 상태정의 vs 균일. READ-ONLY."""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from math import exp
from pathlib import Path
from statistics import mean
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KMARKOV_STATE_DEF_MONITOR.json"
OUT_MD = ROOT / "reports" / "20260815_KMARKOV_STATE_DEF_MONITOR.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
AS_OF = 1236
DECAY = 0.02
LAPLACE = 0.5


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(d: dict) -> list[int]:
    return [int(d[f"num{k}"]) for k in range(1, 7)]


def _end(n: int) -> int:
    return n % 10


def _band15(n: int) -> int:
    if n <= 15:
        return 0
    if n <= 30:
        return 1
    return 2


def _decade(n: int) -> int:
    if n <= 10:
        return 0
    if n <= 20:
        return 1
    if n <= 30:
        return 2
    if n <= 40:
        return 3
    return 4


def _odd_count(nums: list[int]) -> int:
    return sum(1 for n in nums if n % 2 == 1)


def _sum_mod10(nums: list[int]) -> int:
    return sum(nums) % 10


def _build(
    draws: list[dict],
    states: list[Any],
    proj: Callable[[int], Any] | None,
    set_proj: Callable[[list[int]], Any] | None,
) -> dict[Any, dict[Any, float]]:
    matrix = {a: {b: LAPLACE for b in states} for a in states}
    n = len(draws)
    for idx in range(n - 1):
        cur = _nums(draws[idx])
        nxt = _nums(draws[idx + 1])
        w = exp(-DECAY * (n - 1 - idx))
        if set_proj is not None:
            matrix[set_proj(cur)][set_proj(nxt)] += w
        else:
            assert proj is not None
            for a in cur:
                for b in nxt:
                    matrix[proj(a)][proj(b)] += w
    return matrix


def _stats(matrix: dict[Any, dict[Any, float]], states: list[Any]) -> dict[str, Any]:
    k = len(states)
    u = 1.0 / k
    h_u = math.log(k)
    tvs: list[float] = []
    ents: list[float] = []
    pmax = 0.0
    pmin = 1.0
    for a in states:
        row = [float(matrix[a][b]) for b in states]
        s = sum(row)
        if s <= 1e-12:
            continue
        p = [x / s for x in row]
        tvs.append(0.5 * sum(abs(x - u) for x in p))
        ents.append(-sum(x * math.log(x) for x in p if x > 0.0))
        pmax = max(pmax, max(p))
        pmin = min(pmin, min(p))
    mtv = mean(tvs) if tvs else None
    ment = mean(ents) if ents else None
    return {
        "n_states": k,
        "n_rows": len(tvs),
        "mean_tv": round(mtv, 6) if mtv is not None else None,
        "max_tv": round(max(tvs), 6) if tvs else None,
        "mean_entropy": round(ment, 6) if ment is not None else None,
        "h_uniform": round(h_u, 6),
        "entropy_ratio": round(ment / h_u, 6) if ment else None,
        "p_max": round(pmax, 6),
        "p_min": round(pmin, 6),
    }


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute("SELECT * FROM lotto_draws WHERE draw_no < ? ORDER BY draw_no", (AS_OF,)))
    draws = [dict(r) for r in rows]
    peek_max = max((int(d["draw_no"]) for d in draws), default=0)
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    evolve = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    conn.close()

    defs: list[tuple[str, list[Any], Callable[[int], Any] | None, Callable[[list[int]], Any] | None, str]] = [
        ("number_1to45", list(range(1, 46)), lambda n: n, None, "현행 엔진. 번호→번호 45×45"),
        ("end_digit", list(range(10)), _end, None, "끝수 0–9. Chernoff 자리 선호와 같은 칸"),
        ("band15", [0, 1, 2], _band15, None, "1–15 / 16–30 / 31–45"),
        ("decade", [0, 1, 2, 3, 4], _decade, None, "10단위. 41–45는 한 칸"),
        ("odd_count", list(range(7)), None, _odd_count, "세트 홀수개수 0–6. 세트해시 粗"),
        ("sum_mod10", list(range(10)), None, _sum_mod10, "세트 합 mod 10. 세트해시 粗"),
    ]

    out_defs: dict[str, Any] = {}
    for name, states, proj, set_proj, note in defs:
        mat = _build(draws, states, proj, set_proj)
        st = _stats(mat, states)
        st["unit"] = "set" if set_proj is not None else "number_pair"
        st["note"] = note
        out_defs[name] = st

    peek_ok = peek_max < AS_OF
    hard_ok = peek_ok and pred_1237 == 0 and dmax == 1236 and len(draws) == AS_OF - 1

    payload = {
        "id": "K-MARKOV-STATE-DEF-MONITOR",
        "as_of": _now(),
        "verdict": "READ_OK" if hard_ok else "READ_FAIL",
        "apply": False,
        "recommend": "HOLD",
        "ge3_claim": False,
        "draw_1237": False,
        "as_of_draw": AS_OF,
        "n_draws_before": len(draws),
        "peek_max": peek_max,
        "peek_ok": peek_ok,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "evolve": evolve,
        "role_learn_brains": sorted(ROLE_TIER_LEARN_BRAINS),
        "decay": DECAY,
        "laplace": LAPLACE,
        "defs": out_defs,
        "read_rule": "상태정의 모니터. χ²·entropy를 APPLY 게이트로 쓰지 않음. 당첨P 아님.",
        "reason": (
            "번호→번호가 거의 평평해도 끝수/대역이 더 구조적이면 상태 재정의 후보. "
            "이번은 표만. 엔진 상태 교체 APPLY 없음."
        ),
    }

    def _row(name: str) -> str:
        d = out_defs[name]
        return (
            f"| {name} | {d['n_states']} | {d['unit']} | {d['mean_tv']} | "
            f"{d['entropy_ratio']} | {d['p_max']} / {d['p_min']} |"
        )

    lines = [
        "# K-MARKOV-STATE-DEF-MONITOR",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=권고4A. markov 전이 **상태 정의**를 균일과 표로만 비교. 엔진·숙제 미변경.",
        "",
        f"권고=**HOLD**. {payload['reason']}",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. as_of={AS_OF} · peek_max={peek_max} · n_draws={len(draws)} · pred_1237={pred_1237} · MAX={dmax}.",
        "",
        "## 0) 읽는 법",
        "",
        "- entropy_ratio=1이면 그 상태공간에서 완전 균일. **작을수록 구조가 보임**. 누가 낫다·당첨P 금지.",
        "- 상태 수가 다르면 TV를 가로로 서열화하지 말 것. 같은 표 안에서만 본다.",
        "- 현행 엔진은 `number_1to45`만 씀. 나머지=대조.",
        "- χ²를 APPLY 게이트로 쓰지 않음 (Joe 검정은 당첨공 균일성용).",
        "",
        "## 1) 상태 정의 vs 균일 (as_of 1236 · decay 0.02 · Laplace 0.5)",
        "",
        "| 정의 | 상태수 | 단위 | mean TV | entropy_ratio | p_max / p_min |",
        "|------|--------|------|---------|---------------|---------------|",
    ]
    for name, *_rest in defs:
        lines.append(_row(name))
    lines += [
        "",
        "## 2) 정의 메모",
        "",
    ]
    for name, _s, _p, _sp, note in defs:
        er = out_defs[name]["entropy_ratio"]
        lines.append(f"- `{name}`: {note} · entropy_ratio **{er}**")
    lines += [
        "",
        "## 3) 판정",
        "",
        "READ_OK. 상태 교체 APPLY 없음. 숙제ON·궁합prefer·covering·S2·1237 없음.",
        "다음 APPLY는 형 1건.",
        "",
        "## 4) 금지 확인",
        "",
        "DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": payload["verdict"],
                "hard_ok": hard_ok,
                "ratios": {k: v["entropy_ratio"] for k, v in out_defs.items()},
            },
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
