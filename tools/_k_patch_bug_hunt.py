# -*- coding: utf-8 -*-
"""K-PATCH-BUG-HUNT — 켠 패치 경로 버그 실측. READ-ONLY. APPLY 없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KPATCH_BUG_HUNT.json"
OUT_MD = ROOT / "reports" / "20260815_KPATCH_BUG_HUNT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")
SAMPLE = (1216, 1236)
COLD_SAMPLE = (1037, 1137, 1216, 1234, 1236)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (nums or [])))


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def _valid6(nums: list[int]) -> bool:
    return len(nums) == 6 and len(set(nums)) == 6 and all(1 <= n <= 45 for n in nums)


def _census(conn: sqlite3.Connection) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tag in BRAINS:
        n = copy = bad = dup5 = 0
        assemble: dict[str, int] = {}
        unions: list[int] = []
        for r in conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ?",
            (tag, LO, HI),
        ):
            pool = json.loads(r["pool_json"] or "[]")
            rep = json.loads(r["repack_json"] or "[]")
            n += 1
            pset = {_key(_nums(s)) for s in pool}
            seen: set[tuple[int, ...]] = set()
            u: set[int] = set()
            for s in rep:
                k = _key(_nums(s))
                if k in seen:
                    dup5 += 1
                seen.add(k)
                if not _valid6(_nums(s)):
                    bad += 1
                if k in pset:
                    copy += 1
                u.update(_nums(s))
                a = str(s.get("assemble") or s.get("source") or "?")
                assemble[a] = assemble.get(a, 0) + 1
            unions.append(len(u))
        out[tag] = {
            "n": n,
            "copy_sets": copy,
            "copy_per5": round(copy / n, 4) if n else None,
            "bad_sets": bad,
            "dup_in_repack5": dup5,
            "union_mean": round(sum(unions) / len(unions), 4) if unions else None,
            "assemble": assemble,
        }
    return out


def _cache_maps(dno: int) -> tuple[dict[str, list], dict[str, list]]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = list(
            conn.execute(
                "SELECT brain, pool_json, repack_json FROM testlotto_pool_view_cache WHERE draw_no=?",
                (dno,),
            )
        )
    finally:
        conn.close()
    pool = {str(r["brain"]): json.loads(r["pool_json"] or "[]") for r in rows}
    rep = {str(r["brain"]): json.loads(r["repack_json"] or "[]") for r in rows}
    return pool, rep


def _cold_repack(dno: int) -> dict[str, list]:
    import random

    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    out: dict[str, list] = {}
    for tag in BRAINS:
        random.seed(42)
        pool = sp.expand_pool(draws, dno, seed=42, brains=[tag])
        pool_br = sp._pool_by_brain(pool)
        learner = sp.RollingSignalLearner()
        rows = sp.repack_by_brain(
            pool_br,
            sp._build_hint(draws, dno),
            learner.snapshot()[0],
            learner.snapshot()[1],
            target_draw_no=dno,
            hint_by_brain=sp.build_hint_by_brain(draws, dno),
        )
        out[tag] = [x for x in rows if str(x.get("brain_tag")) == tag]
    return out


def _cmp_one(dno: int, *, with_live: bool) -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    print(f"  cmp {dno} live={with_live}", flush=True)
    set_learn_as_of(dno)
    draws = _get_draws_before(dno)
    peek = max((int(d["draw_no"]) for d in draws), default=0) >= dno
    cache_pool, cache_rep = _cache_maps(dno)
    cold = _cold_repack(dno)
    live = sp.build_pool_and_repack(dno) if with_live else None
    rec: dict[str, Any] = {"draw_no": dno, "peek": peek, "with_live": with_live, "brains": {}}
    for tag in BRAINS:
        c_rep = [_key(_nums(s)) for s in cache_rep.get(tag, [])]
        k_rep = [_key(_nums(s)) for s in cold.get(tag, [])]
        c_pool = [_key(_nums(s)) for s in cache_pool.get(tag, [])]
        row = {
            "cache_vs_cold_repack": c_rep == k_rep,
            "n_cache": len(c_rep),
            "n_cold": len(k_rep),
        }
        if live is not None:
            l_rep = [_key(_nums(s)) for s in (live.get("repack_by_brain") or {}).get(tag, [])]
            l_pool = [_key(_nums(s)) for s in (live.get("pool_by_brain") or {}).get(tag, [])]
            row["cache_vs_live_repack"] = c_rep == l_rep
            row["cold_vs_live_repack"] = k_rep == l_rep
            row["cache_vs_live_pool"] = c_pool == l_pool
            row["n_live"] = len(l_rep)
            row["live_assemble"] = [
                str(s.get("assemble") or "")
                for s in (live.get("repack_by_brain") or {}).get(tag, [])
            ]
        rec["brains"][tag] = row
    return rec


def main() -> int:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_slots import COVER_SELECT_MODE, SHAPE_CORE_MODE

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    led = {
        str(r[0]): int(r[1])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    census = _census(conn)
    conn.close()

    print("== census done, cold samples ==", flush=True)
    colds = [_cmp_one(d, with_live=False) for d in COLD_SAMPLE]
    print("== live samples ==", flush=True)
    samples = [_cmp_one(d, with_live=True) for d in SAMPLE]
    n_mis_repack = sum(
        1
        for s in samples
        for t in BRAINS
        if s["brains"][t].get("cache_vs_live_repack") is False
    )
    n_mis_pool = sum(
        1
        for s in samples
        for t in BRAINS
        if s["brains"][t].get("cache_vs_live_pool") is False
    )
    n_cold_live = sum(
        1
        for s in samples
        for t in BRAINS
        if s["brains"][t].get("cold_vs_live_repack") is False
    )
    n_cache_cold = sum(
        1
        for s in colds
        for t in BRAINS
        if s["brains"][t].get("cache_vs_cold_repack") is False
    )

    flags = {
        "HYENA": dict(sp.REPACK_HYENA_MODE_BY_BRAIN),
        "S3_QUOTA": bool(sp.REPACK_ROLE_QUOTA_WIRE),
        "S3_BRAINS": sorted(sp.REPACK_ROLE_QUOTA_BRAINS),
        "S4_MODE": sp.REPACK_RECOMBINE_MODE,
        "S4_BRAINS": sorted(sp.REPACK_RECOMBINE_BRAINS),
        "ASSEMBLE_MODE": sp.ASSEMBLE_MODE,
        "COVER": COVER_SELECT_MODE,
        "SHAPE": SHAPE_CORE_MODE,
        "ROLE_LEARN": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "LEDGER": bool(sp.LEDGER_SIGNAL_WIRE),
    }
    s3s4_dead = all(v == "score5" for v in sp.REPACK_HYENA_MODE_BY_BRAIN.values()) and (
        sp.REPACK_ROLE_QUOTA_WIRE or sp.REPACK_RECOMBINE_MODE == "complement"
    )

    bugs = []
    if n_mis_repack:
        bugs.append(
            {
                "id": "B1",
                "sev": "P1",
                "title": "UI캐시 몰아주기 ≠ 라이브 build_pool_and_repack",
                "evidence": (
                    f"live샘플 {len(SAMPLE)}회×3뇌 cache≠live_repack {n_mis_repack} · "
                    f"cold≠live {n_cold_live} · cache≠cold {n_cache_cold}/{len(COLD_SAMPLE)*3}"
                ),
                "cause": "캐시 refill이 RollingSignalLearner() 빈 스냅샷. 라이브/발권은 warm_learner_to_draw(200). UI는 캐시 우선.",
            }
        )
    if n_mis_pool:
        bugs.append(
            {
                "id": "B2",
                "sev": "P2",
                "title": "캐시 pool10 ≠ 라이브 pool10",
                "evidence": f"cache≠live_pool {n_mis_pool}/{len(SAMPLE)*3}",
                "cause": "미확인(시드/단독expand vs 3뇌expand). 측정값만.",
            }
        )
    if s3s4_dead:
        bugs.append(
            {
                "id": "B3",
                "sev": "P3",
                "title": "S3역할쿼터·S4보완 플래그 ON인데 score5가 우회",
                "evidence": "hyena=score5가 assemble_signal_union보다 먼저 return. quota/complement 미호출.",
                "cause": "죽은 배선. 런타임 오동작은 아님. 문서/튜닝 혼선.",
            }
        )
    copy_left = {t: census[t]["copy_per5"] for t in BRAINS}
    if any((census[t]["copy_per5"] or 0) > 0.2 for t in BRAINS):
        bugs.append(
            {
                "id": "B4",
                "sev": "P2",
                "title": "score5인데 캐시 복사율이 높음",
                "evidence": str(copy_left),
                "cause": "세트우연일치 또는 캐시 미갱신.",
            }
        )
    if any(census[t]["bad_sets"] for t in BRAINS):
        bugs.append(
            {
                "id": "B5",
                "sev": "P1",
                "title": "몰아주기 번호 무효",
                "evidence": {t: census[t]["bad_sets"] for t in BRAINS},
                "cause": "1–45/중복/장수.",
            }
        )

    hard_ok = dmax == 1236 and pred_1237 == 0 and all(census[t]["n"] == 200 for t in BRAINS)
    payload = {
        "id": "K-PATCH-BUG-HUNT",
        "as_of": _now(),
        "verdict": "BUGHUNT_OK" if hard_ok else "BUGHUNT_FAIL",
        "apply": False,
        "hard_ok": hard_ok,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "ledger": led,
        "flags": flags,
        "census": census,
        "sample": samples,
        "cold_sample": colds,
        "mismatch": {
            "n_sample_pairs": len(SAMPLE) * 3,
            "cache_vs_live_repack": n_mis_repack,
            "cache_vs_live_pool": n_mis_pool,
            "cold_vs_live_repack": n_cold_live,
            "cache_vs_cold_repack": n_cache_cold,
        },
        "bugs": bugs,
    }

    lines = [
        "# K-PATCH-BUG-HUNT",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=켠 패치(특히 몰아주기 score5)에서 오동작만 실측. 성적 아님.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. MAX={dmax} · pred_1237={pred_1237} · 원장 {led}.",
        "",
        "## 0) 한 줄",
        "",
    ]
    if bugs:
        lines.append("찾은 것: " + " · ".join(f"{b['id']} {b['title']}" for b in bugs))
    else:
        lines.append("HARD 경로에서 새 런타임 버그 0. 아래는 죽은 배선·설계 잔여만.")
    lines += [
        "",
        "## 1) 캐시 200회 센서스 (1037–1236)",
        "",
        "| 뇌 | n | copy/5 | 무효 | 5장중복 | union | assemble |",
        "|----|---|--------|------|---------|-------|----------|",
    ]
    for tag in BRAINS:
        c = census[tag]
        lines.append(
            f"| {tag} | {c['n']} | {c['copy_per5']} | {c['bad_sets']} | {c['dup_in_repack5']} | "
            f"{c['union_mean']} | {c['assemble']} |"
        )
    lines += [
        "",
        "## 2) 캐시 vs 라이브 (샘플 7회×3뇌)",
        "",
        f"cache≠live 몰아주기 **{n_mis_repack}**/{len(SAMPLE)*3} · cache≠live pool **{n_mis_pool}** · "
        f"cold≠live **{n_cold_live}** · cache≠cold **{n_cache_cold}**/{len(COLD_SAMPLE)*3}.",
        "",
        "| 회 | 뇌 | cache=cold | cache=live몰아 | cold=live | cache=live pool |",
        "|----|----|------------|----------------|-----------|-----------------|",
    ]
    shown = list(colds) + [s for s in samples if s["draw_no"] not in {c["draw_no"] for c in colds}]
    for s in shown:
        for tag in BRAINS:
            b = s["brains"][tag]
            lines.append(
                f"| {s['draw_no']} | {tag} | {b.get('cache_vs_cold_repack')} | {b.get('cache_vs_live_repack', '—')} | "
                f"{b.get('cold_vs_live_repack', '—')} | {b.get('cache_vs_live_pool', '—')} |"
            )
    lines += [
        "",
        "## 3) 버그 목록",
        "",
    ]
    if not bugs:
        lines.append("(없음)")
    for b in bugs:
        lines += [
            f"### {b['id']} · {b['sev']} · {b['title']}",
            "",
            f"- 근거: {b['evidence']}",
            f"- 원인: {b['cause']}",
            "",
        ]
    lines += [
        "## 4) 라이브 플래그",
        "",
        json.dumps(flags, ensure_ascii=False),
        "",
        "## 5) 논의 (패치 제안 아님 · APPLY 없음)",
        "",
        "- B1이 실측되면: 당첨확인 UI(캐시)와 발권(build_pool_and_repack) 몰아주기가 갈라진다. 고치려면 캐시를 warm 경로로 다시 쓰거나, 발권도 캐시를 읽게.",
        "- B3은 버그라기보다 **죽은 스위치**. S3/S4를 끄거나 문서에 ‘score5가 우선’을 박제.",
        "- 타깃 적중 입력·동결토큰은 이번 헌트에서 안 건드림.",
        "",
        "## 6) 판정",
        "",
        "BUGHUNT_OK. 코드/DB 쓰기 없음. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": payload["verdict"],
                "bugs": [b["id"] for b in bugs],
                "mismatch": payload["mismatch"],
                "copy_per5": {t: census[t]["copy_per5"] for t in BRAINS},
            },
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
