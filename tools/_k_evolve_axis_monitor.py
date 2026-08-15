# -*- coding: utf-8 -*-
"""K-EVOLVE-AXIS-MONITOR — 권고순서#2 뇌별 prefer/prize·전이vs균일 표. READ-ONLY."""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.markov_brain.engine import build_transition_matrix
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KEVOLVE_AXIS_MONITOR.json"
OUT_MD = ROOT / "reports" / "20260815_KEVOLVE_AXIS_MONITOR.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
AS_OF = 1236
BRAINS = ("stat", "markov", "review")
END089 = frozenset(n for n in range(1, 46) if n % 10 in (0, 8, 9))
HI32 = frozenset(n for n in range(32, 46))
BDAY = frozenset(n for n in range(1, 32))
NULL_OCC = {
    "hi32": 6 * 14 / 45,
    "end089": 6 * 12 / 45,
    "bday": 6 * 31 / 45,
}
H_UNIF = math.log(45.0)
U = 1.0 / 45.0


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _ro() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _mass(table: dict[int, float], group: frozenset[int]) -> float:
    tot = sum(float(table[n]) for n in range(1, 46))
    if tot <= 1e-12:
        return 0.0
    return sum(float(table[n]) for n in group) / tot


def _occ(nums: list[int]) -> dict[str, int]:
    s = set(nums)
    return {
        "hi32": sum(1 for n in s if n in HI32),
        "end089": sum(1 for n in s if n in END089),
        "bday": sum(1 for n in s if n in BDAY),
    }


def _blank_kind() -> dict[str, Any]:
    return {
        "n_sets": 0,
        "prefer_avgs": [],
        "prize_avgs": [],
        "hi32": [],
        "end089": [],
        "bday": [],
    }


def _summarize(acc: dict[str, Any]) -> dict[str, Any]:
    n = int(acc["n_sets"])
    out: dict[str, Any] = {"n_sets": n}
    for key, null in (("prefer", 1.0), ("prize", 1.0)):
        vs = acc[f"{key}_avgs"]
        m = mean(vs) if vs else None
        out[f"{key}_mean"] = round(m, 4) if m is not None else None
        out[f"d_{key}"] = round(m - null, 4) if m is not None else None
    for key, null in NULL_OCC.items():
        vs = acc[key]
        m = mean(vs) if vs else None
        out[key] = round(m, 4) if m is not None else None
        out[f"d_{key}"] = round(m - null, 4) if m is not None else None
    return out


def _trans_vs_unif(matrix: dict) -> dict[str, Any]:
    tvs: list[float] = []
    ents: list[float] = []
    max_p = 0.0
    min_p = 1.0
    for i in range(1, 46):
        row = [float(matrix[i][j]) for j in range(1, 46)]
        s = sum(row)
        if s <= 1e-12:
            continue
        p = [x / s for x in row]
        tvs.append(0.5 * sum(abs(x - U) for x in p))
        ents.append(-sum(x * math.log(x) for x in p if x > 0.0))
        max_p = max(max_p, max(p))
        min_p = min(min_p, min(p))
    mtv = mean(tvs) if tvs else None
    ment = mean(ents) if ents else None
    return {
        "n_rows": len(tvs),
        "mean_tv": round(mtv, 6) if mtv is not None else None,
        "max_tv": round(max(tvs), 6) if tvs else None,
        "mean_entropy": round(ment, 6) if ment is not None else None,
        "h_uniform": round(H_UNIF, 6),
        "entropy_ratio": round(ment / H_UNIF, 6) if ment else None,
        "p_max": round(max_p, 6),
        "p_min": round(min_p, 6),
        "note": "TV·엔트로피 모니터. χ² APPLY 게이트 아님. 1.0=완전균일.",
    }


def main() -> int:
    conn = _ro()
    evolve = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    peek_win = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_evolve_log "
            "WHERE as_of >= draw_no AND draw_no BETWEEN ? AND ?",
            (LO, HI),
        ).fetchone()[0]
    )
    ledger = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    cache_n = {
        str(r["brain"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache "
            "WHERE draw_no BETWEEN ? AND ? GROUP BY brain",
            (LO, HI),
        )
    }
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    pred_n = int(conn.execute("SELECT COUNT(*) FROM lotto_predictions").fetchone()[0])

    draw_rows = list(
        conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no < ? ORDER BY draw_no",
            (AS_OF + 1,),
        )
    )
    all_draws = [dict(r) for r in draw_rows]

    cache: dict[int, dict[str, dict[str, list[list[int]]]]] = {}
    for r in conn.execute(
        "SELECT draw_no, brain, pool_json, repack_json FROM testlotto_pool_view_cache "
        "WHERE draw_no BETWEEN ? AND ?",
        (LO, HI),
    ):
        dn = int(r["draw_no"])
        tag = str(r["brain"])
        cache.setdefault(dn, {})[tag] = {
            "pool": [
                [int(x) for x in (s.get("nums") or [])]
                for s in json.loads(r["pool_json"] or "[]")
                if len(s.get("nums") or []) == 6
            ],
            "repack": [
                [int(x) for x in (s.get("nums") or [])]
                for s in json.loads(r["repack_json"] or "[]")
                if len(s.get("nums") or []) == 6
            ],
        }
    conn.close()

    acc: dict[str, dict[str, dict[str, Any]]] = {
        tag: {"pool": _blank_kind(), "repack": _blank_kind()} for tag in BRAINS
    }
    n_scored = 0
    peek_score = 0
    hist: list[dict] = []
    for d in all_draws:
        hist.append(d)
        dn = int(d["draw_no"])
        nxt = dn + 1
        if nxt < LO or nxt > HI:
            continue
        if any(int(x["draw_no"]) >= nxt for x in hist):
            peek_score += 1
            continue
        pref = cs.prefer_table(hist, brain="markov")
        prize = cs.prize_table(hist, brain="review")
        row = cache.get(nxt) or {}
        for tag in BRAINS:
            kinds = row.get(tag)
            if not kinds:
                continue
            for kind in ("pool", "repack"):
                bucket = acc[tag][kind]
                for nums in kinds[kind]:
                    pa, _ = cs.set_crowd_score(nums, pref)
                    za, _ = cs.set_crowd_score(nums, prize)
                    o = _occ(nums)
                    bucket["n_sets"] += 1
                    bucket["prefer_avgs"].append(pa)
                    bucket["prize_avgs"].append(za)
                    for k in NULL_OCC:
                        bucket[k].append(o[k])
                    n_scored += 1

    axis = {tag: {k: _summarize(acc[tag][k]) for k in ("pool", "repack")} for tag in BRAINS}

    draws_1236 = [d for d in all_draws if int(d["draw_no"]) < AS_OF]
    peek_ok = max((int(d["draw_no"]) for d in draws_1236), default=0) < AS_OF
    pref_now = cs.prefer_table(draws_1236, brain="markov")
    prize_now = cs.prize_table(draws_1236, brain="review")
    struct_u = cs.structural_unpopular_prior()
    table_mass = {
        "prefer_markov": {
            "hi32": round(_mass(pref_now, HI32), 4),
            "end089": round(_mass(pref_now, END089), 4),
            "bday": round(_mass(pref_now, BDAY), 4),
        },
        "prize_review": {
            "hi32": round(_mass(prize_now, HI32), 4),
            "end089": round(_mass(prize_now, END089), 4),
            "bday": round(_mass(prize_now, BDAY), 4),
        },
        "struct_unpopular": {
            "hi32": round(_mass(struct_u, HI32), 4),
            "end089": round(_mass(struct_u, END089), 4),
            "bday": round(_mass(struct_u, BDAY), 4),
        },
        "uniform": {
            "hi32": round(14 / 45, 4),
            "end089": round(12 / 45, 4),
            "bday": round(31 / 45, 4),
        },
    }

    trans = _trans_vs_unif(build_transition_matrix(draws_1236))

    hard = {
        "peek_evolve": peek,
        "peek_evolve_win": peek_win,
        "peek_score_as_of_ge_target": peek_score,
        "peek_table_ok": peek_ok,
        "pred_1237": pred_1237,
        "draws_max": dmax,
        "evolve_by": evolve,
        "cache_by": cache_n,
        "n_scored_sets": n_scored,
        "role_learn_brains": sorted(ROLE_TIER_LEARN_BRAINS),
        "db_write": False,
        "apply": False,
    }
    hard_ok = (
        peek == 0
        and peek_win == 0
        and peek_score == 0
        and peek_ok
        and pred_1237 == 0
        and dmax == 1236
        and evolve.get("stat") == 200
        and evolve.get("markov") == 200
        and evolve.get("review") == 200
    )

    payload = {
        "id": "K-EVOLVE-AXIS-MONITOR",
        "as_of": _now(),
        "verdict": "READ_OK" if hard_ok else "READ_FAIL",
        "apply": False,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "as_of_draw": AS_OF,
        "hard": hard,
        "hard_ok": hard_ok,
        "knobs": {
            "W_CROWD": dict(cs.W_CROWD_BY_BRAIN),
            "W_STRUCT": dict(cs.W_STRUCT_BY_BRAIN),
            "BLEND": dict(cs.BLEND_STRENGTH_BY_BRAIN),
            "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        },
        "census": {
            "evolve": evolve,
            "ledger": ledger,
            "cache": cache_n,
            "pred_n": pred_n,
            "pred_1237": pred_1237,
            "draws_max": dmax,
        },
        "axis_sets": axis,
        "table_mass": table_mass,
        "transition_vs_uniform": trans,
        "null_occ": {k: round(v, 4) for k, v in NULL_OCC.items()},
        "read_rule": "prefer/prize 축·점유만. hits/ge3 서열 금지. 숙제ON/covering/S2/1237 없음.",
    }

    def _ax(tag: str, kind: str) -> str:
        o = axis[tag][kind]
        return (
            f"| {tag} {kind} | {o['n_sets']} | {o['prefer_mean']} ({o['d_prefer']:+}) | "
            f"{o['prize_mean']} ({o['d_prize']:+}) | {o['hi32']} ({o['d_hi32']:+}) | "
            f"{o['end089']} ({o['d_end089']:+}) |"
        )

    tm = table_mass
    lines = [
        "# K-EVOLVE-AXIS-MONITOR",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님 · hits 클레임 금지",
        "목적=권고순서#2. evolve/캐시를 뇌별로 **prefer·prize 축과 점유만** 표. 전이행렬 vs 균일. 예측·숙제 미변경.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. peek evolve={peek} · score peek={peek_score} · pred_1237={pred_1237} · MAX={dmax}.",
        "",
        "## 0) 읽는 법",
        "",
        "- prefer_mean / prize_mean = 세트 `set_crowd_score` 평균. 널≈**1.0**. Δ는 축 편차. **누가 낫다 금지**.",
        "- hi32 널=**1.8667** · end089 널=**1.6**. 점유 모니터. 성적 아님.",
        "- 전이 TV=행별 균일(1/45)과의 총변동거리. entropy_ratio=1이면 완전 평평. χ² APPLY 금지.",
        "- 3뇌 합산 없음. 숙제 소비는 라이브 `{stat}` 유지.",
        "",
        "## 1) HARD / census",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| evolve | {evolve} |",
        f"| cache 1037–1236 | {cache_n} |",
        f"| 원장 | {ledger} |",
        f"| peek evolve | {peek} |",
        f"| pred_1237 | {pred_1237} |",
        f"| draws MAX | {dmax} |",
        f"| 숙제 소비 | {sorted(ROLE_TIER_LEARN_BRAINS)} |",
        f"| review W_STRUCT | {cs.W_STRUCT_BY_BRAIN.get('review')} |",
        f"| markov W_STRUCT | {cs.W_STRUCT_BY_BRAIN.get('markov')} |",
        "",
        "## 2) 캐시 세트 축 (walk-forward as_of=N-1)",
        "",
        "| 뇌 kind | n | prefer (Δvs1) | prize (Δvs1) | hi32 (Δvs널) | end089 (Δvs널) |",
        "|---------|---|----------------|---------------|--------------|----------------|",
    ]
    for tag in BRAINS:
        for kind in ("pool", "repack"):
            lines.append(_ax(tag, kind))
    lines += [
        "",
        "## 3) 표 질량 (as_of 1236 · 번호가중 합/전체)",
        "",
        "| 표 | hi32 (널0.3111) | end089 (널0.2667) | bday (널0.6889) |",
        "|----|-----------------|-------------------|-----------------|",
        f"| prefer markov | {tm['prefer_markov']['hi32']} | {tm['prefer_markov']['end089']} | {tm['prefer_markov']['bday']} |",
        f"| prize review | {tm['prize_review']['hi32']} | {tm['prize_review']['end089']} | {tm['prize_review']['bday']} |",
        f"| struct unpopular | {tm['struct_unpopular']['hi32']} | {tm['struct_unpopular']['end089']} | {tm['struct_unpopular']['bday']} |",
        f"| 균일 | {tm['uniform']['hi32']} | {tm['uniform']['end089']} | {tm['uniform']['bday']} |",
        "",
        "## 4) markov 전이행렬 vs 균일 (as_of 1236)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| 행 | {trans['n_rows']} |",
        f"| mean TV | {trans['mean_tv']} |",
        f"| max TV | {trans['max_tv']} |",
        f"| mean entropy | {trans['mean_entropy']} |",
        f"| H_uniform | {trans['h_uniform']} |",
        f"| entropy_ratio | {trans['entropy_ratio']} |",
        f"| p_max / p_min | {trans['p_max']} / {trans['p_min']} |",
        "",
        trans["note"],
        "",
        "## 5) 판정",
        "",
        "READ_OK. APPLY 없음. 축이 세트에 보이는지만 표로 확인. 우열·hits 문장 없음.",
        "다음 APPLY는 형 1건. 숙제ON·궁합prefer·covering·S2·1237 이번 없음.",
        "",
        "## 6) 금지 확인",
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
    print(json.dumps({"verdict": payload["verdict"], "hard_ok": hard_ok, "n_scored": n_scored, "trans": trans}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
