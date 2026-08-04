# -*- coding: utf-8 -*-
"""K-REPACK-HYBRID-WIRE — v1 캐시→hybrid v2 마이그레이션 + ge3 검증.

- v1 repack = baseline 점수몰아주기 (ablation과 동일 전제)
- stat/review → assemble_hybrid_p45_r123 · markov 유지
- wire 없음 재계산 없이 schema=2 저장 후 ge3 대조

Usage:
  python tools/_k_repack_hybrid_wire_verify.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260804_KREPACK_HYBRID_WIRE.json"
OUT_MD = ROOT / "reports" / "20260804_KREPACK_HYBRID_WIRE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

BRAINS = ("stat", "markov", "review")
REF = {"stat": 0.165, "markov": 0.130, "review": 0.135}
NULL5 = 0.1137
PIN = 0.1447


def _hits(nums, actual):
    return len(set(int(x) for x in nums) & actual)


def main() -> None:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.pool_view_cache import CACHE_SCHEMA_VERSION, save_pool_view_cache
    from app.testlotto.signal_pool import (
        HYBRID_ASSEMBLE_MODE,
        HYBRID_P45_R123_BRAINS,
        assemble_hybrid_p45_r123,
        build_pool_and_repack,
    )

    init_testlotto_db()
    conn = get_lotto_db()
    draws = {
        int(r["draw_no"]): {int(r[f"num{k}"]) for k in range(1, 7)}
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN 1035 AND 1234"
        )
    }
    rows = conn.execute(
        """
        SELECT draw_no, brain, pool_json, repack_json, seed, schema_version
        FROM testlotto_pool_view_cache
        WHERE draw_no BETWEEN 1035 AND 1234
        ORDER BY draw_no, brain
        """
    ).fetchall()
    conn.close()

    by_draw: dict[int, dict] = defaultdict(dict)
    for r in rows:
        d = dict(r)
        by_draw[int(d["draw_no"])][str(d["brain"])] = d

    bests: dict[str, list[int]] = {b: [] for b in BRAINS}
    migrated = 0
    for dno in range(1035, 1235):
        if dno not in draws or dno not in by_draw or len(by_draw[dno]) < 3:
            continue
        actual = draws[dno]
        pool_by = {}
        repack_by = {}
        for tag in BRAINS:
            row = by_draw[dno][tag]
            pool = json.loads(row["pool_json"] or "[]")
            old_repack = json.loads(row["repack_json"] or "[]")
            pool_by[tag] = pool
            classic = [
                [int(x) for x in sorted(s["nums"], key=int)]
                for s in sorted(old_repack, key=lambda x: int(x.get("set_no") or 0))
            ]
            # v1이 이미 hybrid면 classic이 오염 — schema 1만 신뢰
            if int(row.get("schema_version") or 1) >= 2 and tag in HYBRID_P45_R123_BRAINS:
                # already v2: use as-is for scoring after save skip
                new_tickets = old_repack
            elif tag in HYBRID_P45_R123_BRAINS and HYBRID_ASSEMBLE_MODE == "p45_r123":
                assembled = assemble_hybrid_p45_r123(pool, classic)
                new_tickets = [
                    {
                        "set_no": i + 1,
                        "nums": item["nums"],
                        "brain_tag": tag,
                        "kind": "repack",
                        "assemble": "hy_p45_r123",
                        "source": item["source"],
                        "source_set_no": item["source_set_no"],
                    }
                    for i, item in enumerate(assembled)
                ]
            else:
                new_tickets = [
                    {
                        "set_no": i + 1,
                        "nums": [int(x) for x in classic[i]],
                        "brain_tag": tag,
                        "kind": "repack",
                        "assemble": "baseline_repack",
                    }
                    for i in range(min(5, len(classic)))
                ]
            repack_by[tag] = new_tickets
            bests[tag].append(max((_hits(t["nums"], actual) for t in new_tickets), default=0))

        save_pool_view_cache(
            dno,
            {
                "seed": 42,
                "pool_by_brain": pool_by,
                "repack_by_brain": repack_by,
            },
        )
        migrated += 1

    # smoke live build
    smoke = build_pool_and_repack(1230)
    smoke_ok = bool(smoke.get("ok"))
    smoke_asm = {
        b: (smoke.get("repack_by_brain") or {}).get(b, [{}])[0].get("assemble")
        for b in BRAINS
    } if smoke_ok else {}

    summary = {}
    for b in BRAINS:
        xs = bests[b]
        n = len(xs)
        ge3 = sum(1 for x in xs if x >= 3)
        rate = round(ge3 / n, 4) if n else 0.0
        summary[b] = {
            "n_eval": n,
            "ge3_count": ge3,
            "ge3_rate": rate,
            "mean": round(mean(xs), 4) if xs else 0.0,
            "ref_ablation_ge3": REF[b],
            "delta_vs_ref": round(rate - REF[b], 4),
            "delta_vs_null": round(rate - NULL5, 4),
            "delta_vs_pin": round(rate - PIN, 4),
            "match_ref": abs(rate - REF[b]) < 1e-9,
        }

    payload = {
        "id": "K-REPACK-HYBRID-WIRE",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wire": True,
        "scope": {
            "hybrid_brains": sorted(HYBRID_P45_R123_BRAINS),
            "mode": HYBRID_ASSEMBLE_MODE,
            "markov": "baseline_repack",
            "cache_schema_version": CACHE_SCHEMA_VERSION,
        },
        "migrated_draws": migrated,
        "by_brain": summary,
        "smoke_build_1230": {"ok": smoke_ok, "assemble": smoke_asm, "hybrid_meta": smoke.get("hybrid")},
        "pass": all(summary[b]["match_ref"] for b in BRAINS) and smoke_ok,
        "references": {
            "ablation": "docs/benchmarks/20260804_KREPACK_HYBRID_survey.json",
            "null_ge3": NULL5,
            "pin_ge3": PIN,
        },
    }

    lines = [
        "# K-REPACK-HYBRID-WIRE — stat/review hy_p45_r123 배선",
        "",
        f"`{payload['ts']}` · migrated={migrated} · schema={CACHE_SCHEMA_VERSION}",
        "",
        "## 0. 한 줄",
        "",
        f"stat/review **pool4+5+몰1~3** wire · markov baseline 유지 · "
        f"검증 PASS=**{payload['pass']}**",
        "",
        "## 1. ge3 vs ablation 참조",
        "",
        "| 뇌 | wire ge3 | ablation ref | Δ | vs null |",
        "|----|---------:|-------------:|---|--------:|",
    ]
    for b in BRAINS:
        s = summary[b]
        lines.append(
            f"| {b} | **{s['ge3_rate']:.4f}** | {s['ref_ablation_ge3']:.4f} | "
            f"{s['delta_vs_ref']:+.4f} | {s['delta_vs_null']:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## 2. smoke build_pool_and_repack(1230)",
            "",
            f"- ok: {smoke_ok}",
            f"- assemble: {smoke_asm}",
            f"- hybrid meta: {smoke.get('hybrid')}",
            "",
            "## 3. 변경 파일",
            "",
            "- `app/testlotto/signal_pool.py` — assemble_hybrid_p45_r123 · HYBRID_P45_R123_BRAINS",
            "- `app/testlotto/pool_view_cache.py` — CACHE_SCHEMA_VERSION=2 · schema 필터",
            "",
            "## 금지 준수",
            "",
            "coordinator/quota 미수정 · random.choices/_get_draws_before/boost상한 미손 · engine 미수정",
            "",
        ]
    )
    text = "\n".join(lines)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps(payload["by_brain"], ensure_ascii=False, indent=2))
    print("pass=", payload["pass"], "smoke=", smoke_asm)


if __name__ == "__main__":
    main()
