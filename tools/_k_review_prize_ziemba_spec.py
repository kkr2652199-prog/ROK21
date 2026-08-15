# -*- coding: utf-8 -*-
"""K-REVIEW-PRIZE-ZIEMBA-SPEC — prize_table vs Ziemba 비인기 규칙. READ-ONLY."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREVIEW_PRIZE_ZIEMBA_SPEC.json"
OUT_MD = ROOT / "reports" / "20260815_KREVIEW_PRIZE_ZIEMBA_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
AS_OF = 1236
BRAINS = ("review", "stat", "markov")

# Ziemba et al. 1986 캐나다 6/49 비인기 12개 중 6/45에 있는 것 (48 제외)
ZIEMBA_CA = frozenset({10, 12, 18, 29, 30, 32, 38, 39, 40, 41, 42})
END089 = frozenset(n for n in range(1, 46) if n % 10 in (0, 8, 9))
HI32 = frozenset(n for n in range(32, 46))
HI40 = frozenset(n for n in range(40, 46))
BDAY = frozenset(n for n in range(1, 32))
NULL = {
    "hi32": 6 * 14 / 45,
    "hi40": 6 * 6 / 45,
    "end089": 6 * 12 / 45,
    "bday": 6 * 31 / 45,
    "ziemba_ca": 6 * 11 / 45,
}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _ranks(vals: list[float]) -> list[float]:
    n = len(vals)
    order = sorted(range(n), key=lambda i: vals[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) != len(b) or len(a) < 3:
        return None
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = mean(ra), mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    if da < 1e-12 or db < 1e-12:
        return None
    return round(num / (da * db), 4)


def _occ(nums: list[int]) -> dict[str, int]:
    s = set(nums)
    return {
        "hi32": sum(1 for n in s if n in HI32),
        "hi40": sum(1 for n in s if n in HI40),
        "end089": sum(1 for n in s if n in END089),
        "bday": sum(1 for n in s if n in BDAY),
        "ziemba_ca": sum(1 for n in s if n in ZIEMBA_CA),
    }


def _brain_occ(conn: sqlite3.Connection, brain: str, kind: str) -> dict[str, Any]:
    col = "pool_json" if kind == "pool" else "repack_json"
    acc = {k: [] for k in NULL}
    n_sets = 0
    for r in conn.execute(
        f"SELECT {col} FROM testlotto_pool_view_cache WHERE brain=? AND draw_no BETWEEN ? AND ?",
        (brain, LO, HI),
    ):
        for s in json.loads(r[0] or "[]"):
            nums = [int(x) for x in (s.get("nums") or [])]
            if len(nums) != 6:
                continue
            o = _occ(nums)
            n_sets += 1
            for k in acc:
                acc[k].append(o[k])
    out: dict[str, Any] = {"n_sets": n_sets}
    for k, vs in acc.items():
        m = mean(vs) if vs else None
        out[k] = round(m, 4) if m is not None else None
        out[f"d_{k}"] = round(m - NULL[k], 4) if m is not None else None
    return out


def main() -> int:
    draws = _get_draws_before(AS_OF)
    peek = max((int(d["draw_no"]) for d in draws), default=0)
    fw_pos = sum(1 for d in draws if int(d.get("first_winners") or 0) > 0)
    fw_zero = sum(1 for d in draws if int(d.get("first_winners") or 0) == 0)

    crowd = cs.crowd_unpopular_from_draws(draws)
    struct = cs.structural_unpopular_prior()
    prize = cs.prize_table(draws, brain="review")
    nums = list(range(1, 46))
    pv = [prize[n] for n in nums]
    cv = [crowd[n] for n in nums]
    sv = [struct[n] for n in nums]
    ziemba_bin = [1.0 if n in ZIEMBA_CA else 0.0 for n in nums]
    hi32_bin = [1.0 if n in HI32 else 0.0 for n in nums]
    end_bin = [1.0 if n in END089 else 0.0 for n in nums]

    rho = {
        "prize_vs_struct": _spearman(pv, sv),
        "prize_vs_crowd": _spearman(pv, cv),
        "crowd_vs_struct": _spearman(cv, sv),
        "prize_vs_ziemba_ca": _spearman(pv, ziemba_bin),
        "prize_vs_hi32": _spearman(pv, hi32_bin),
        "prize_vs_end089": _spearman(pv, end_bin),
        "struct_vs_ziemba_ca": _spearman(sv, ziemba_bin),
    }

    def topk(table: dict[int, float], k: int = 12) -> list[int]:
        return [n for n, _ in sorted(table.items(), key=lambda x: (-x[1], x[0]))[:k]]

    top_prize = topk(prize, 12)
    top_struct = topk(struct, 12)
    top_crowd = topk(crowd, 12)
    overlap_ps = len(set(top_prize) & set(top_struct))
    overlap_pc = len(set(top_prize) & set(top_crowd))
    overlap_pz = len(set(top_prize) & ZIEMBA_CA)

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    occ: dict[str, Any] = {}
    for tag in BRAINS:
        occ[tag] = {
            "pool": _brain_occ(conn, tag, "pool"),
            "repack": _brain_occ(conn, tag, "repack"),
        }
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    conn.close()

    # 이미 배선됨. 갭= crowd 0.90이 struct를 얼마나 덮나.
    already = True
    rec = "HOLD"
    reason = (
        "prize_table = 0.90*crowd_unpopular(first_winners) + 0.10*structural_unpopular_prior "
        "(고번호·끝 0/8/9). Ziemba 규칙은 struct에 이미 있음. 이번 APPLY 없음."
    )

    payload = {
        "id": "K-REVIEW-PRIZE-ZIEMBA-SPEC",
        "as_of": _now(),
        "verdict": "SPEC_OK",
        "apply": False,
        "recommend": rec,
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "as_of_draw": AS_OF,
        "peek_ok": peek < AS_OF,
        "peek_max": peek,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "fw_used": fw_pos,
        "fw_zero_skip": fw_zero,
        "n_draws_before": len(draws),
        "knobs": {
            "W_CROWD_review": cs.W_CROWD_BY_BRAIN.get("review"),
            "W_STRUCT_review": cs.W_STRUCT_BY_BRAIN.get("review"),
            "BLEND_review": cs.BLEND_STRENGTH_BY_BRAIN.get("review"),
            "PRIZE_SHAPE_STRENGTH": cs.PRIZE_SHAPE_STRENGTH,
            "PRIZE_WIRE": cs.prize_on(),
        },
        "already_wired": already,
        "rho": rho,
        "top12": {
            "prize": top_prize,
            "struct": top_struct,
            "crowd": top_crowd,
            "overlap_prize_struct": overlap_ps,
            "overlap_prize_crowd": overlap_pc,
            "overlap_prize_ziemba_ca": overlap_pz,
        },
        "ziemba_ca_645": sorted(ZIEMBA_CA),
        "null_per_set": {k: round(v, 4) for k, v in NULL.items()},
        "occupancy": occ,
        "reason": reason,
        "next_apply": "형 GO 전 금지. 후보=W_STRUCT↑는 prize 게이트 필요. apply_learn_boost 복사 금지.",
    }

    def _row(tag: str, kind: str) -> str:
        o = occ[tag][kind]
        return (
            f"| {tag} {kind} | {o['n_sets']} | {o['hi32']} ({o['d_hi32']:+}) | "
            f"{o['end089']} ({o['d_end089']:+}) | {o['bday']} ({o['d_bday']:+}) | "
            f"{o['ziemba_ca']} ({o['d_ziemba_ca']:+}) |"
        )

    lines = [
        "# K-REVIEW-PRIZE-ZIEMBA-SPEC",
        "",
        f"시각: {payload['as_of']} · **SPEC_OK** · READ-ONLY · APPLY **없음** · 1237아님 · hits 클레임 금지",
        "목적=review `prize_table`이 Ziemba/Chernoff 비인기 규칙과 얼마나 같은지 실측. 예측 불변.",
        "",
        f"권고=**{rec}**. {reason}",
        "",
        "## 0) 이미 있는 배선",
        "",
        "`structural_unpopular_prior`: n≥40 ×1.40 · n≥32 ×1.25 · n≤12 ×0.80 · 끝 0/8/9 ×1.15.",
        f"`prize_table` = W_CROWD **{cs.W_CROWD_BY_BRAIN.get('review')}** × crowd(1/√first_winners) + "
        f"W_STRUCT **{cs.W_STRUCT_BY_BRAIN.get('review')}** × 위 사전. blend review **{cs.BLEND_STRENGTH_BY_BRAIN.get('review')}**.",
        f"as_of={AS_OF} 이전 draws={len(draws)} · first_winners>0 사용={fw_pos} · 0스킵={fw_zero} · peek_max={peek} (<{AS_OF}={peek < AS_OF}).",
        "조합별 판매수 없음 → 1등 당첨자수 프록시. 당첨P 불변 · 몫 EV만.",
        "",
        "## 1) 표 정렬 (Spearman ρ, n=45)",
        "",
        "| 쌍 | ρ |",
        "|----|---|",
        f"| prize vs struct(Ziemba형 사전) | {rho['prize_vs_struct']} |",
        f"| prize vs crowd(당첨자수) | {rho['prize_vs_crowd']} |",
        f"| crowd vs struct | {rho['crowd_vs_struct']} |",
        f"| prize vs hi32 더미 | {rho['prize_vs_hi32']} |",
        f"| prize vs 끝0/8/9 더미 | {rho['prize_vs_end089']} |",
        f"| prize vs 캐나다12(48제외) 더미 | {rho['prize_vs_ziemba_ca']} |",
        f"| struct vs 캐나다12 더미 | {rho['struct_vs_ziemba_ca']} |",
        "",
        f"prize top12={top_prize} · struct top12={top_struct} · crowd top12={top_crowd}.",
        f"top12 교집합 prize∩struct=**{overlap_ps}** · prize∩crowd=**{overlap_pc}** · prize∩캐나다11=**{overlap_pz}**.",
        "",
        "## 2) 캐시 세트 점유 (1037–1236 · 모니터 · 널=비복원 6×k/45)",
        "",
        f"널 1장: hi32={NULL['hi32']:.3f} · end089={NULL['end089']:.3f} · bday={NULL['bday']:.3f} · 캐나다11={NULL['ziemba_ca']:.3f}.",
        "",
        "| 뇌 kind | n | hi32 (Δ널) | end089 (Δ널) | bday (Δ널) | 캐나다11 (Δ널) |",
        "|---------|---|-------------|--------------|------------|----------------|",
        _row("review", "pool"),
        _row("review", "repack"),
        _row("stat", "repack"),
        _row("markov", "repack"),
        "",
        "Δ는 이론 대비 편차. **누가 낫다 금지**. review가 고번호·끝수에서 널보다 크면 prize축이 세트에 보임.",
        "",
        "## 3) 채택 / 기각",
        "",
        "| 항 | 판정 |",
        "|----|------|",
        "| 문헌 규칙을 prize_table에 **새로** 넣기 | **기각(이미 있음)** |",
        "| W_STRUCT를 이번 턴에 올리기 | **HOLD** · 군중 0.90이 표를 지배(ρ prize-crowd). 올리려면 prize 게이트+별 GO |",
        "| review에 apply_learn_boost 복사 | **기각** · 축 붕괴 |",
        "| 캐나다 12를 한국 6/45에 그대로 고정 | **기각** · 48 없음·시장 다름. 구조 사전(고번호·끝수)이 이식분 |",
        "| hits/ge3로 품질 점수 | **기각** |",
        "| 숙제 ON / covering / S2 / 1237 | **기각** |",
        "",
        "## 4) 다음 APPLY (형 GO 후만)",
        "",
        "후보 A: `W_STRUCT_BY_BRAIN['review']`만 소폭↑ (crowd↓). 게이트=review prize 축 비악화 · stat/markov 캐시 불변 · peek0.",
        "후보 B: 없음(모니터 유지). 권고는 **B=HOLD** — 규칙은 이미 들어가 있고, 이번은 대조 SPEC.",
        "",
        "## 5) 금지 확인",
        "",
        "DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": "SPEC_OK",
                "recommend": rec,
                "rho": rho,
                "overlap_ps": overlap_ps,
                "overlap_pc": overlap_pc,
                "review_repack": occ["review"]["repack"],
                "peek_ok": peek < AS_OF,
                "fw_pos": fw_pos,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
